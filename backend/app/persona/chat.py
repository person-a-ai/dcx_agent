"""Validated text edits and append-only reverts for stage-eight insights."""
import json
from pathlib import Path

from pydantic import BaseModel

from app.context import store as sessions
from app.known import store as known
from app.persona.source import Source, require_persona
from app.llm.base import Attachment, LLMTask
from app.persona import concepts, insights, prescribe
from app.persona.insight_pipeline import serialized, publish_status
from app.persona.package import load_package, PackageMissing
from app.persona.store import PersonaStore
from app.vectors.embedder import get_embedder

FAILURE_COPY = '요청을 반영하지 못했습니다. 다르게 말해 주세요.'


def _target(target):
    if target == 'insights':
        return 'insights', None, 'list'
    if isinstance(target, str) and target.startswith('concept:') and target[8:]:
        return 'concepts', target[8:], 'concept'
    if isinstance(target, str) and target.startswith('insight:') and target[8:]:
        return 'insights', target[8:], 'item'
    raise ValueError('Invalid chat target')


class ItemOut(BaseModel):
    item: insights.EditItem


def _concept_draft(item):
    return dict(persona_profile=item['persona_profile']['text'],
        pain_points=[p['evidence_number'] for p in item['pain_points']],
        journey=[{key: row[key] for key in concepts.JourneyRow.model_fields} for row in item['journey']])


def edit(sid, version, target: str, message: str, *, focus_id: str | None = None, run_task=None) -> dict:
    require_persona(sessions.assert_writable(sid, version))
    with serialized(sid):
        source = Source(sid, version)
        source.check()
        store = PersonaStore.open(sid, version)
        store.guard = source.check
        if run_task is None:
            from app.persona.pipeline import _Calls
            run_task = _Calls(store.path, lambda: None).run_task
        try:
            name, insight_id, mode = _target(target)
            current = store.read(name)
            if mode == 'item' and not any(row['id'] == insight_id for row in (current or {}).get('items', [])):
                raise sessions.StoreError('Unknown insight target', 400, 'validation')
            if not current or not isinstance(message, str) or not message.strip():
                raise ValueError('Missing input')
            try:
                package = load_package(sid, version)
            except PackageMissing:
                package = None
            payload = dict(current=current, message=message, target=target)
            schema = insights.EditOut
            if name == 'insights':
                context_ids = [c.context_id for b in package.personas for c in b.context_evidence] if package else []
                payload['contexts'] = [{key: row[key] for key in ('context_id', 'context_name', 'pain_point')}
                    for row in insights.context_view(package, store.read('cards'), {'context_ids': context_ids})]
                if mode == 'item':
                    payload['item_id'] = insight_id
                    schema = ItemOut
                elif focus_id in {row['id'] for row in current['items']}:
                    payload['focus_id'] = focus_id
            if mode == 'concept':
                item = next(row for row in current['items'] if row['id'] == insight_id)
                insight = next(row for row in store.read('insights')['items'] if row['id'] == insight_id)
                contexts, _, refs, owners = concepts._inputs(package, insight)
                payload.update(editable=_concept_draft(item), insight=insight,
                    evidence={n: ref.model_dump() for n, ref in refs.items()})
                schema = concepts.ConceptOut
            task = LLMTask(task='insight.edit', sid=sid,
                instructions=Path(__file__).with_name('prompts').joinpath('edit.v2.md').read_text(encoding='utf-8'),
                attachments=[Attachment(title='현재 판과 수정 요청', body=json.dumps(payload, ensure_ascii=False))],
                output_schema=schema)
            result = run_task(task)
            if not result.ok or not isinstance(result.data, schema):
                raise ValueError('Invalid edit schema')
            draft = result.data.model_dump()
            if name == 'insights':
                if mode == 'item':
                    draft['item']['id'] = insight_id
                    items = [draft['item'] if row['id'] == insight_id else row for row in current['items']]
                else:
                    items = draft['items']
                available = {c.context_id for b in package.personas for c in b.context_evidence} if package else set()
                items = insights.validate_items(items, available, require_new=False, previous=current['items'])
                embedder = known.session_embedder(sid, sessions.assert_writable(sid, version), get_embedder)
                insights.recompute(sid, version, items, package=package, embedder=embedder)
                if mode == 'item':
                    items = [row if row['id'] == insight_id else old
                             for row, old in zip(items, current['items'])]
            else:
                if (any(n not in refs for n in draft['pain_points']) or
                        any(row['context_id'] not in insight['context_ids'] for row in draft['journey'])):
                    raise ValueError('Invalid concept references')
                concept = concepts._hydrate(draft, insight_id,
                    concepts._basis(sid, version, contexts), refs, owners)
                project = sessions.load_session(sid).get('projectContext', {})
                checked = prescribe.check_constraints(sid, concept, project, run_task=run_task)
                violations = [row for row in checked if row['verdict'] == 'violates']
                concept.update(insight_revision=store.read('insights')['revision'],
                               context_ids=list(insight['context_ids']), outdated=False,
                               constraint_check=checked, blocked=bool(violations),
                               represcribed=False, regenerated=False)
                if violations:
                    concept['message'] = '\n'.join(
                        f"사내 제약 '{row['constraint']}'를 지키는 처방을 만들지 못했습니다." for row in violations)
                items = [concept if row['id'] == insight_id else row for row in current['items']]
            source.check()
            revision = store.new_revision(name, items, by='chat', message=message)
            publish_status(sid, version, 'done', before_publish=source.check)
            outcome = {'ok': True, 'revision': revision}
        except sessions.StoreError:
            raise
        except Exception:
            outcome = {'ok': False, 'message': FAILURE_COPY}
        store.append_chat(dict(at=sessions.now(), target=target, message=message,
                               **{k: v for k, v in outcome.items() if k != 'message'},
                               **({'reason': FAILURE_COPY} if not outcome['ok'] else {})))
        return outcome


def revert(sid, version, target: str, revision: int) -> dict:
    require_persona(sessions.assert_writable(sid, version))
    with serialized(sid):
        source = Source(sid, version)
        source.check()
        store = PersonaStore.open(sid, version)
        store.guard = source.check
        name, insight_id, mode = _target(target)
        if name == 'insights':
            number = store.revert(name, revision)
        else:
            current = store.read(name) or {}
            snapshot = next((h for h in current.get('history', []) if h['revision'] == revision), {})
            item = next((row for row in snapshot.get('items', []) if row['id'] == insight_id), None)
            if item is None:
                raise sessions.StoreError('Revision not found', 404, 'not_found')
            items = [row for row in current.get('items', []) if row['id'] != insight_id]
            number = store.new_revision(name, [*items, item], by='revert', message=None)
        publish_status(sid, version, 'done', before_publish=source.check)
        return {'revision': number}
