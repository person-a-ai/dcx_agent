"""Generate an atomic Persona card from the stage-seven file contract.

Injected runners perform one attempt. The default registry already retries
parse/schema failures twice, so it is invoked once per logical call. Validation
of coverage and references lives in the task schema, including registry calls.
No storage writes occur here; callers persist only a successful CardResult.
"""
import json
import re
from dataclasses import dataclass
from math import isclose
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from app.llm import registry
from app.llm.base import Attachment, LLMTask
from app.persona.grade import grade_card
from app.persona.package import PersonaBlock, evidence_index
from app.persona.params import CARD_CHUNK

FIELDS = ('state', 'emotion', 'barrier')


class Output(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class Cell(Output):
    text: str | None
    cite: list[str]


class PainCell(Output):
    text: str
    cite: list[str] = Field(min_length=1)


class ContextOut(Output):
    context_id: str
    state: Cell
    emotion: Cell
    barrier: Cell
    pain_points: list[PainCell] = Field(default_factory=list, max_length=3)


class CardOut(Output):
    contexts: list[ContextOut] = Field(max_length=CARD_CHUNK)


class Intent(Output):
    text: str | None
    basis_context_ids: list[str]
    reserved_context_ids: list[str]


class Journey(Output):
    pre_purchase: float | None = Field(ge=0, le=1)
    purchase: float | None = Field(ge=0, le=1)
    post_purchase: float | None = Field(ge=0, le=1)

    @model_validator(mode='after')
    def total(self):
        values = (self.pre_purchase, self.purchase, self.post_purchase)
        if all(v is None for v in values):
            return self
        if any(v is None for v in values) or not isclose(sum(values), 1, abs_tol=1e-9):
            raise ValueError('Journey ratios must sum to one or all be null')
        return self


class Sensitivity(Output):
    price: Literal['상', '중', '하'] | None
    brand: Literal['상', '중', '하'] | None
    feature: Literal['상', '중', '하'] | None


class SummaryOut(Output):
    intent: Intent
    usage_context: Cell
    jtbd: Cell
    journey: Journey
    sensitivity: Sensitivity
    values: str | None
    decision_style: str | None


@dataclass(frozen=True)
class CardResult:
    status: Literal['done', 'failed']
    card: dict | None = None
    error: str | None = None


def _card_schema(context_ids, local_refs):
    class ChunkOut(CardOut):
        @model_validator(mode='after')
        def references(self):
            ids = [row.context_id for row in self.contexts]
            if len(ids) != len(context_ids) or set(ids) != set(context_ids):
                raise ValueError('Each requested Context must occur exactly once')
            for row in self.contexts:
                for cell in [getattr(row, field) for field in FIELDS] + row.pain_points:
                    for cite in cell.cite:
                        if cite not in local_refs or local_refs[cite].context_id != row.context_id:
                            raise ValueError('Citation must belong to this Context')
            return self
    return ChunkOut


def _summary_schema(context_ids, refs):
    class PersonaSummaryOut(SummaryOut):
        @model_validator(mode='after')
        def references(self):
            for cid in self.intent.basis_context_ids + self.intent.reserved_context_ids:
                if cid not in context_ids:
                    raise ValueError('Unknown intent Context')
            for cell in (self.usage_context, self.jtbd):
                if any(cite not in refs for cite in cell.cite):
                    raise ValueError('Unknown summary citation')
            return self
    return PersonaSummaryOut


def _call(sid, name, payload, schema, runner):
    prompt = (Path(__file__).with_name('prompts') / f'{name}.v1.md').read_text(encoding='utf-8')
    task = LLMTask(task=f'persona.{name}', sid=sid, instructions=prompt,
                   attachments=[Attachment(title='관찰 근거', body=json.dumps(payload, ensure_ascii=False))],
                   output_schema=schema)
    attempts = 1 if (runner is registry.run_task or
        getattr(getattr(runner, '__self__', runner), 'retries_schema', False)) else 2
    for _ in range(attempts):
        try:
            result = runner(task)
        except Exception:
            return None, 'backend'
        if not result.ok:
            kind = result.error.kind if result.error else 'backend'
            if kind not in ('parse', 'schema'):
                return None, kind
            continue
        try:
            data = result.data.model_dump() if isinstance(result.data, BaseModel) else result.data
            return schema.model_validate(data).model_dump(), None
        except (ValidationError, TypeError):
            pass
    return None, 'schema'


def _evidence_payload(ref):
    # Explicit projection prevents producer extras/project metadata leaking into prompts.
    return dict(context_id=ref.context_id, role=ref.role, doc_id=ref.doc_id,
                source=ref.source, pain_point=ref.pain_point['text'] if ref.pain_point else None, quote={key: getattr(ref.quote, key) for key in
                    ('field', 'idx', 'start', 'end', 'text', 'verified')} if ref.quote else None)


def _normalize_pain(text: str) -> str:
    return re.sub(r'[\s\W_]+', '', text)


def aggregate_pain_points(contexts: list[dict], context_docs: dict[str, int]) -> list[dict]:
    """Merge equivalent sentences, preserving first-seen text and citation order."""
    merged = {}
    for context in contexts:
        cid = context['context_id']
        for pain in context.get('pain_points', []):
            key = _normalize_pain(pain['text'])
            item = merged.setdefault(key, dict(text=pain['text'], grade='inferred',
                                               context_ids=[], cite=[]))
            if pain['grade'] == 'observed':
                item['grade'] = 'observed'
            if cid not in item['context_ids']:
                item['context_ids'].append(cid)
            item['cite'] = list(dict.fromkeys([*item['cite'], *pain['cite']]))
    return sorted(merged.values(), key=lambda item: (
        item['grade'] != 'observed', -len(item['cite']),
        -sum(context_docs.get(cid, 0) for cid in item['context_ids'])))[:5]


def generate_card(sid, block: PersonaBlock, *, run_task=None) -> CardResult:
    """At most four Contexts per card call, then one Persona-wide summary.

    Confirmed identity/action are copied from the package. Dims-derived
    situations retain LLM text; citations determine epistemic grades.
    """
    runner = registry.run_task if run_task is None else run_task
    refs = evidence_index(block)
    persona = block.persona_evidence
    identity = {key: getattr(persona, key) for key in
                ('cluster_id', 'persona_id', 'persona_name', 'desire', 'goal')}
    rows = []
    for offset in range(0, len(block.context_evidence), CARD_CHUNK):
        chunk = block.context_evidence[offset:offset + CARD_CHUNK]
        ids = [context.context_id for context in chunk]
        global_keys = [key for key, ref in refs.items() if ref.context_id in ids]
        mapping = {f'E{i+1}': key for i, key in enumerate(global_keys)}
        local_refs = {local: refs[global_id] for local, global_id in mapping.items()}
        payload = dict(**identity, context_ids=ids, context_evidence=[dict(
            context_id=c.context_id, context_name=c.context_name,
            situation={field: getattr(c.situation, field) for field in FIELDS},
            situation_origin=c.situation_origin,
            counter_context='counter_context' in c.flags) for c in chunk],
            evidence={key: _evidence_payload(ref) for key, ref in local_refs.items()})
        if local_refs:
            data, error = _call(sid, 'card', payload, _card_schema(ids, local_refs), runner)
        else:
            data = {'contexts': [dict(context_id=cid, **{field: dict(text=None, cite=[])
                                                       for field in FIELDS}) for cid in ids]}
            error = None
        if error:
            return CardResult('failed', error=error)
        generated = {row['context_id']: row for row in data['contexts']}
        for context in chunk:
            row = generated[context.context_id]
            has_evidence = any(ref.context_id == context.context_id for ref in local_refs.values())
            row['pain_points'] = row.get('pain_points', []) if has_evidence else []
            for pain in row['pain_points']:
                tagged = [local_refs[cite].pain_point for cite in pain['cite']
                          if local_refs[cite].pain_point]
                matched = next((tag for tag in tagged if tag.get('verified') is True
                    and _normalize_pain(pain['text']) == _normalize_pain(tag['text'])), None)
                pain['grade'] = 'observed' if matched else 'inferred'
                source = matched or next(iter(tagged), None)
                pain['source_pain'] = source['text'] if source else None
                pain['cite'] = [mapping[cite] for cite in pain['cite']]
            barrier_empty = row['barrier']['text'] is None
            for field in FIELDS:
                cell = row[field]
                if not has_evidence:
                    cell.update(text=None, cite=[])
                if cell['text'] is None:
                    cell['cite'] = []
                cell['cite'] = [mapping[cite] for cite in cell['cite']]
            if barrier_empty and row['pain_points']:
                first = row['pain_points'][0]
                row['barrier'] = dict(text=first['text'], cite=list(first['cite']))
            row.update(keywords=list(context.keywords), action=context.action, context_name=context.context_name,
                       situation_origin=context.situation_origin, metrics=context.metrics.model_dump())
            rows.append(row)
    ids = [c.context_id for c in block.context_evidence]
    # Metrics and confirmed Action are code-owned, so exclude them from synthesis.
    payload = dict(**identity, context_ids=ids,
        contexts=[{key: row[key] for key in ('context_id', *FIELDS)} for row in rows],
        counter_context_ids=[c.context_id for c in block.context_evidence if 'counter_context' in c.flags],
        evidence={key: _evidence_payload(ref) for key, ref in refs.items()})
    if refs:
        summary, error = _call(sid, 'summary', payload, _summary_schema(ids, refs), runner)
        if error:
            return CardResult('failed', error=error)
    else:
        summary = dict(intent=dict(text=None, basis_context_ids=[], reserved_context_ids=[]),
            usage_context=dict(text=None, cite=[]), jtbd=dict(text=None, cite=[]),
            journey=dict(pre_purchase=None, purchase=None, post_purchase=None),
            sensitivity=dict(price=None, brand=None, feature=None), values=None, decision_style=None)
    card = dict(**identity, artifacts=[a.model_dump() for a in persona.artifacts], contexts=rows, **summary, intent_warning='의도 ≠ 행동',
                metrics=persona.metrics.model_dump(), quality=persona.quality.model_dump())
    card['pain_points'] = aggregate_pain_points(rows,
        {c.context_id: c.metrics.doc_count for c in block.context_evidence})
    card.update(grade_card(card, refs))
    return CardResult('done', card=card)
