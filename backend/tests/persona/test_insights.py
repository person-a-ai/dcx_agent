import json
import sqlite3

import numpy as np
import pytest

from app.context import store as sessions
from app.context.versions import version_dir
from app.llm import registry
from app.llm.fake import FakeBackend
from app.persona.insights import InsightError, confirm, derive, opportunity_bars
from app.persona.package import load_package
from app.persona.store import PersonaStore
from tests.fixtures.evidence_package import write_session_with_package, fake_persona_backend


class Embedder:
    def embed(self, texts, input_type=None):
        assert input_type == 'query'
        return np.eye(3)


@pytest.fixture
def env(data_dir):
    session = write_session_with_package(data_dir)
    store = PersonaStore.open(session.sid, session.version)
    cards = {'items': [{'persona_id': 'CL0-P0', 'summary': {'intent': {'text': 'カード要約'}}}]}
    store.write('cards', cards)
    package = load_package(session.sid, session.version)
    with sqlite3.connect(version_dir(session.sid, session.version) / 'segment/segment.sqlite') as db:
        for n, context in enumerate(c for b in package.personas for c in b.context_evidence):
            db.execute('UPDATE contexts SET centroid=? WHERE context_id=?',
                       (np.eye(3, dtype=np.float32)[n % 3].tobytes(), context.context_id))
    backend = fake_persona_backend(package)
    rows = json.loads(backend.responses['insight.derive'])['items']
    for row in rows:
        row.update(headline=row['title'], statements=['편안한 냉방을 원한다', row['pain_point']],
                   hashtags=['냉방', '조절'],
                   flow=[dict(context_id=cid, text=row['pain_point']) for cid in row['context_ids']])
    return session, store, rows, cards


def runner(monkeypatch, responses):
    pending = iter(responses)
    calls = []
    class Backend:
        def run(self, task):
            calls.append(task)
            return FakeBackend(responses={task.task: json.dumps({'items': next(pending)})}).run(task)
    monkeypatch.setattr(registry, 'get_backend', lambda name: Backend())
    return calls


@pytest.mark.parametrize('count', [0, 2, 9])
def test_range_regenerates_once_then_fails(env, monkeypatch, count):
    session, store, rows, _ = env
    invalid = [{**rows[n % 3], 'id': f'I{n}'} for n in range(count)]
    calls = runner(monkeypatch, [invalid, invalid])
    with pytest.raises(InsightError, match='^인사이트를 만들지 못했습니다. 다시 시도하세요.$'):
        derive(session.sid, session.version, embedder=Embedder())
    assert len(calls) == 2
    assert store.read('insights') is None


@pytest.mark.parametrize('count', [3, 8])
def test_range_recovery_revision_and_cards_input(env, monkeypatch, count):
    session, store, rows, cards = env
    valid = [{**rows[n % 3], 'id': f'I{n}'} for n in range(count)]
    calls = runner(monkeypatch, [[], valid, valid])
    assert derive(session.sid, session.version, embedder=Embedder()) == 1
    first = store.read('insights')
    assert derive(session.sid, session.version, embedder=Embedder()) == 2
    assert store.read('insights')['history'][0]['items'] == first['items']
    assert json.loads(calls[0].attachments[0].body)['cards'] == cards
    assert calls[0].task == 'insight.derive'


def test_known_badge(env, monkeypatch):
    session, store, rows, _ = env
    rows[0]['known_ki_id'] = 'k1'
    sessions.update_session(session.sid, {'knownInsights': [{'id': 'k1', 'text': '알려진 내용'}]})
    calls = runner(monkeypatch, [rows])
    derive(session.sid, session.version, embedder=Embedder())
    items = store.read('insights')['items']
    assert items[0]['known_badge'] == 'Known Insight #k1와 같은 내용'
    assert items[1]['known_badge'] is None
    assert json.loads(calls[0].attachments[0].body)['known_insights'][0]['id'] == 'k1'


def test_bars_mean_and_targets():
    result = opportunity_bars([{'id': 'a', 'context_ids': ['x', 'y']},
        {'id': 'b', 'context_ids': ['y']}, {'id': 'c', 'context_ids': ['z']}],
        {'x': 0, 'y': 2, 'z': 3})
    assert result == {'bars': [{'id': 'a', 'odi': 1}, {'id': 'b', 'odi': 2},
                               {'id': 'c', 'odi': 3}], 'mean': 2, 'targets': ['b', 'c']}


def test_llm_numbers_ignored(env, monkeypatch):
    session, store, rows, _ = env
    for row in rows:
        row.update(radar={'raw': 999}, odi=999, percentile=999, default_target=True)
    runner(monkeypatch, [rows])
    derive(session.sid, session.version, embedder=Embedder())
    items = store.read('insights')['items']
    assert items[0]['radar']['raw'] == dict(Computed=1, Connected=0, Shared=0)
    assert items[0]['radar']['percentile']['Computed'] == pytest.approx(100 * 2.5 / 3)
    assert [i['odi'] for i in items] == pytest.approx([.05, .75, 1.36])
    assert [i['default_target'] for i in items] == [False, True, True]
    assert 'percentile' not in items[0]


def test_confirm_sets_session(env, monkeypatch):
    session, store, rows, _ = env
    runner(monkeypatch, [rows])
    derive(session.sid, session.version, embedder=Embedder())
    sessions.update_session(session.sid, {'persona': {'status': 'done'}})
    assert confirm(session.sid, session.version, ['I1', 'I3']) == ['I1', 'I3']
    assert sessions.load_session(session.sid)['insight']['confirmed'] == ['I1', 'I3']
    with pytest.raises(sessions.StoreError):
        confirm(session.sid, session.version, ['missing'])
    assert confirm(session.sid, session.version, []) == []


def test_unknown_context_rejected_without_revision(env, monkeypatch):
    session, store, rows, _ = env
    rows[0]['context_ids'] = ['missing']
    runner(monkeypatch, [rows, rows])
    with pytest.raises(InsightError):
        derive(session.sid, session.version, embedder=Embedder())
    assert store.read('insights') is None


def test_derive_weights_context_cosines_by_document_count(env, monkeypatch):
    session, store, rows, _ = env
    path = version_dir(session.sid, session.version) / 'evidence/package.json'
    package = json.loads(path.read_text())
    contexts = package['personas'][0]['context_evidence']
    contexts[0]['metrics']['doc_count'] = 1
    contexts[1]['metrics']['doc_count'] = 3
    path.write_text(json.dumps(package), encoding='utf-8')
    rows[0]['context_ids'] = [contexts[0]['context_id'], contexts[1]['context_id']]
    rows[0]['flow'] = [dict(context_id=cid, text='온도를 조절한다') for cid in rows[0]['context_ids']]
    runner(monkeypatch, [rows])
    derive(session.sid, session.version, embedder=Embedder())
    first = store.read('insights')['items'][0]
    assert first['radar']['raw'] == pytest.approx(dict(Computed=.25, Connected=.75, Shared=0))
    # ODI remains the unweighted mean even though the radar is weighted.
    assert first['odi'] == pytest.approx(.4)


def test_missing_centroid_preserves_previous_revision(env, monkeypatch):
    session, store, rows, _ = env
    runner(monkeypatch, [rows, rows])
    derive(session.sid, session.version, embedder=Embedder())
    previous = store.read('insights')
    with sqlite3.connect(version_dir(session.sid, session.version) / 'segment/segment.sqlite') as db:
        db.execute('UPDATE contexts SET centroid=NULL WHERE context_id=?', (rows[0]['context_ids'][0],))
    with pytest.raises(InsightError):
        derive(session.sid, session.version, embedder=Embedder())
    assert store.read('insights') == previous


NEW_FIELDS = ('headline', 'statements', 'hashtags', 'flow')


def modern_items():
    return [dict(id=f'I{i}', title='제목', pain_point='불편', known_ki_id=None,
                 context_ids=['a'], headline='짧은 제목', statements=['원한다', '해결해 줘'],
                 hashtags=['심박', '수면'], flow=[dict(context_id='a', text='불편하다')])
            for i in range(3)]


def validate(items, **kwargs):
    from app.persona.insights import validate_items
    return validate_items(items, {'a', 'b', 'c'}, **kwargs)


def test_validate_ok():
    items = modern_items()
    assert validate(items) == items
    assert validate(items) is not items


@pytest.mark.parametrize('count', [1, 3])
def test_validate_statements_count(count):
    items = modern_items()
    items[0]['statements'] = ['문장'] * count
    with pytest.raises(ValueError):
        validate(items)


def test_validate_flow_outside_context_ids():
    items = modern_items()
    items[0]['flow'][0]['context_id'] = 'b'
    with pytest.raises(ValueError):
        validate(items)


@pytest.mark.parametrize('ids,ok', [(['a'], False), (['a', 'b'], True),
                                     (['a', 'b', 'c'], True), (['a', 'a'], False)])
def test_validate_flow_count(ids, ok):
    items = modern_items()
    items[0]['context_ids'] = ['a', 'b', 'c']
    items[0]['flow'] = [dict(context_id=cid, text='문장') for cid in ids]
    if ok:
        assert validate(items) == items
    else:
        with pytest.raises(ValueError):
            validate(items)


def test_validate_flow_single_context():
    assert validate(modern_items()) == modern_items()


@pytest.mark.parametrize('field,limit', [('headline', 30), ('statements', 70)])
def test_validate_length_caps(field, limit):
    items = modern_items()
    def set_text(text):
        items[0][field] = text if field == 'headline' else [text, '문장']
    set_text(' ' + '가' * limit + ' ')
    assert validate(items)[0][field] == ('가' * limit if field == 'headline' else ['가' * limit, '문장'])
    set_text('가' * (limit + 1))
    with pytest.raises(ValueError):
        validate(items)


def test_validate_cleans_hashtag_and_quotes():
    items = modern_items()
    items[0].update(headline='“귀로 재는 컨디션”', hashtags=['#심박', ' 수면 '])
    cleaned = validate(items)
    assert cleaned[0]['headline'] == '귀로 재는 컨디션'
    assert cleaned[0]['hashtags'] == ['심박', '수면']
    assert items[0]['hashtags'] == ['#심박', ' 수면 ']
    for tags in (['#', '수면'], ['#수면', ' 수면 ']):
        items[0]['hashtags'] = tags
        with pytest.raises(ValueError):
            validate(items)


def test_validate_edit_all_or_none():
    from app.persona.insights import EditOut
    items = modern_items()
    legacy = [{k: v for k, v in row.items() if k not in NEW_FIELDS} for row in items]
    assert validate(legacy, require_new=False) == legacy
    assert validate(items, require_new=False) == items
    assert EditOut.model_validate({'items': legacy}).items[0].headline is None
    nullable = EditOut.model_validate({'items': legacy}).model_dump()['items']
    assert validate(nullable, require_new=False) == legacy
    legacy[0]['headline'] = '일부만'
    with pytest.raises(ValueError):
        validate(legacy, require_new=False)
    items[0]['flow'][0]['context_id'] = 'b'
    with pytest.raises(ValueError):
        validate(items, require_new=False)


def test_validate_edit_no_regression():
    previous = modern_items()
    legacy = [{k: v for k, v in row.items() if k not in NEW_FIELDS} for row in previous]
    with pytest.raises(ValueError):
        validate(legacy, require_new=False, previous=previous)


@pytest.mark.parametrize('case', ['range', 'id', 'unknown', 'duplicate'])
def test_validate_keeps_existing_rules(case):
    items = modern_items()
    if case == 'range':
        items = items[:2]
    elif case == 'id':
        items[0]['id'] = items[1]['id']
    elif case == 'unknown':
        items[0]['context_ids'] = ['missing']
    else:
        items[0]['context_ids'] = ['a', 'a']
    with pytest.raises(ValueError):
        validate(items)


def test_derive_retries_once_on_invalid_flow(env, monkeypatch):
    from copy import deepcopy
    session, _, rows, _ = env
    invalid = deepcopy(rows)
    invalid[0]['flow'][0]['context_id'] = 'missing'
    calls = runner(monkeypatch, [invalid, rows])
    assert derive(session.sid, session.version, embedder=Embedder()) == 1
    assert len(calls) == 2
    assert 'flow' in json.loads(calls[1].attachments[0].body)['retry']


def test_derive_uses_v2_prompt(env, monkeypatch):
    session, _, rows, _ = env
    calls = runner(monkeypatch, [rows])
    derive(session.sid, session.version, embedder=Embedder())
    instructions = calls[0].instructions
    assert 'headline' in instructions
    output_rule = instructions.split('각 인사이트는', 1)[1].split('반환하세요.', 1)[0]
    assert all(field in output_rule for field in NEW_FIELDS)
    assert 'known_ki_id(같은 내용의 Known Insight ID 또는 null)만 반환하세요.' not in instructions


@pytest.mark.parametrize('recover', [True, False])
@pytest.mark.parametrize('field,values', [('statements', ['하나', '둘', '셋']),
                                         ('hashtags', ['태그'])])
def test_derive_retries_once_on_schema_error(env, recover, field, values):
    from copy import deepcopy
    session, store, rows, _ = env
    invalid = deepcopy(rows)
    invalid[0][field] = values
    responses = iter([invalid, rows if recover else invalid])
    calls = []

    def run_task(task):
        calls.append(task)
        result = FakeBackend(responses={task.task: json.dumps({'items': next(responses)})}).run(task)
        if len(calls) == 1:
            assert not result.ok and result.error.kind == 'schema'
        return result

    if recover:
        assert derive(session.sid, session.version, run_task=run_task, embedder=Embedder()) == 1
    else:
        with pytest.raises(InsightError):
            derive(session.sid, session.version, run_task=run_task, embedder=Embedder())
        assert store.read('insights') is None
    assert len(calls) == 2
    assert json.loads(calls[1].attachments[0].body)['retry'] == (
        '인사이트를 3~8개 생성하고 고유 ID와 입력에 있는 Context ID만 사용하세요. '
        'headline은 30자 이하, statements는 정확히 2개이며 각 70자 이하, '
        'hashtags는 2~4개, flow는 그 인사이트 context_ids 안에서 고르세요.')


@pytest.mark.parametrize('recover', [True, False])
def test_derive_retries_once_on_wrong_result_model(env, recover):
    from app.llm.base import LLMResult
    from app.persona.insights import DeriveOut, EditOut
    session, _, rows, _ = env
    wrong = LLMResult(ok=True, data=EditOut.model_validate({'items': rows}))
    valid = LLMResult(ok=True, data=DeriveOut.model_validate({'items': rows}))
    responses = iter([wrong, valid if recover else wrong])
    calls = []

    def run_task(task):
        calls.append(task)
        return next(responses)

    if recover:
        assert derive(session.sid, session.version, run_task=run_task, embedder=Embedder()) == 1
    else:
        with pytest.raises(InsightError):
            derive(session.sid, session.version, run_task=run_task, embedder=Embedder())
    assert len(calls) == 2
    assert 'retry' in json.loads(calls[1].attachments[0].body)


@pytest.mark.parametrize('kind', ['backend', 'timeout', 'interrupted'])
def test_derive_does_not_retry_terminal_errors(env, kind):
    from app.llm.base import failure
    session, _, _, _ = env
    calls = []

    def run_task(task):
        calls.append(task)
        return failure(kind, 'terminal failure')

    with pytest.raises(InsightError):
        derive(session.sid, session.version, run_task=run_task, embedder=Embedder())
    assert len(calls) == 1


def test_dominant_dim_counts_support_only(env):
    from app.persona.insights import dominant_dim
    session, _, _, _ = env
    context = load_package(session.sid, session.version).personas[0].context_evidence[0]
    context.evidence[0].tags = ['think', 'act']
    context.evidence[1].tags = ['act']
    context.counter_evidence = [context.counter_evidence[0].model_copy(update={'tags': ['feel']})] * 5
    context.rare_evidence[0].tags = ['feel'] * 10
    assert dominant_dim(context) == 'Act'


def test_dominant_dim_tie_and_empty(env):
    from app.persona.insights import dominant_dim
    session, _, _, _ = env
    context = load_package(session.sid, session.version).personas[0].context_evidence[0]
    context.evidence[0].tags = ['feel']
    context.evidence[1].tags = ['sense']
    assert dominant_dim(context) == 'Sense'
    context.evidence = []
    assert dominant_dim(context) is None


def test_dominant_dim_ignores_non_list_tags(env):
    from app.persona.insights import dominant_dim
    session, _, _, _ = env
    context = load_package(session.sid, session.version).personas[0].context_evidence[0]
    base = context.evidence[0]
    context.evidence = [base.model_copy(update={'tags': tags})
                        for tags in ({'think': 10}, None, 'think', ['unknown', {}, None])]
    assert dominant_dim(context) is None
    context.evidence.append(base.model_copy(update={'tags': ['think']}))
    assert dominant_dim(context) == 'Think'


def test_context_axis_max_and_zero():
    from app.persona.insights import context_axis
    from app.persona.params import RADAR_AXES
    axes = np.eye(3)
    names = list(RADAR_AXES)
    assert context_axis(axes[1], axes) == names[1]
    assert context_axis(np.zeros(3), axes) is None
    assert context_axis(np.array([1, 1, 0]), axes) == names[0]


def test_context_view_rows(env):
    from app.persona.insights import context_view
    session, _, _, _ = env
    package = load_package(session.sid, session.version)
    first = package.personas[0].context_evidence[1]
    counter = package.personas[1].context_evidence[0]
    first.evidence[0].tags = ['think']
    cards = {'personas': {'CL0-P0': {'card': {'contexts': [
        {'context_id': 'other', 'pain_points': [{'text': 'wrong'}]},
        {'context_id': first.context_id, 'pain_points': [{'text': '첫 불편', 'cite': ['E1']}, {'text': '둘째'}]}]}}}}
    item = {'context_ids': [first.context_id, counter.context_id]}
    rows = context_view(package, cards, item, {first.context_id: 'Shared'})
    assert rows[0] == dict(context_id=first.context_id, short='C1', persona_id='CL0-P0',
        persona_name=package.personas[0].persona_evidence.persona_name,
        context_name=first.context_name, odi=first.metrics.odi, axis='Shared', dim='Think',
        counter=False, pain_point='첫 불편')
    assert rows[1]['context_id'] == counter.context_id and rows[1]['counter'] is True
    assert rows[1]['pain_point'] is None and rows[1]['axis'] is None
    for old in ({}, {'pain_points': []}):
        cards['personas']['CL0-P0']['card']['contexts'][1] = {'context_id': first.context_id, **old}
        assert context_view(package, cards, item)[0]['pain_point'] is None
    assert context_view(None, cards, item)[0] == dict(context_id=first.context_id, short='C1',
        persona_id=None, persona_name=None, context_name=None, odi=None, axis=None, dim=None,
        counter=False, pain_point=None)


def test_recompute_stores_contexts_with_axis(env, monkeypatch):
    from app.persona.params import RADAR_AXES
    session, store, rows, _ = env
    runner(monkeypatch, [rows])
    derive(session.sid, session.version, embedder=Embedder())
    for item in store.read('insights')['items']:
        assert [c['context_id'] for c in item['contexts']] == item['context_ids']
        assert all(c['axis'] in RADAR_AXES for c in item['contexts'])


def test_summary_means(env):
    from app.persona.insights import summary
    from app.persona.params import RADAR_AXES
    session, _, _, _ = env
    package = load_package(session.sid, session.version)
    for n, context in enumerate(c for b in package.personas for c in b.context_evidence):
        context.metrics.odi = [1., None, 3.][n] if n < 3 else None
    items = [{'radar': {'raw': dict.fromkeys(RADAR_AXES, value)}} for value in (.2, .6)]
    assert summary(package, items) == {'context_odi_mean': 2., 'radar_mean': dict.fromkeys(RADAR_AXES, .4)}
    assert summary(None, []) == {'context_odi_mean': None, 'radar_mean': None}
    assert summary(package, []) == {'context_odi_mean': 2., 'radar_mean': None}
