import json
import random

import numpy as np
import pytest

from app.config import settings
from app.context import store as sessions
from app.context.models import PersonaCard, ProjectContext
from app.context.versions import version_dir
from app.llm import registry
from app.llm.base import LLMResult
from app.llm.fake import FakeBackend
from app.segment import params, pipeline, target
from app.segment.store import SegmentStore
from tests.fixtures.segment_synth import make_segment_session, fake_dims_backend


CARD = dict(desire='푹 자고 싶음', context='남편과 같은 방에서 잠', pain='코골이 때문에 각방', unmet='각방 없이 숙면',
            keywords=['코골이', '각방'], quotes=['코고는 소리 때문에 잠을 못 자요'])


def persona(**card):
    return dict(id='T1', name='잠자리 협상가', card={**CARD, **card})


def test_card_model_strips_and_limits():
    card = PersonaCard(desire=' 숙면 ', keywords=[' 코골이 ', ''], quotes=['  각방  '])
    assert (card.desire, card.keywords, card.quotes) == ('숙면', ['코골이'], ['각방'])
    assert card.filled() and not PersonaCard().filled()
    with pytest.raises(ValueError):
        PersonaCard(quotes=['가' * 301])


def test_cards_number_only_filled_seeds():
    context = {'personaSeeds': {'items': [{'text': '빈 시드'}, {'text': '잠자리 협상가', 'card': CARD},
                                          {'text': '빈 카드', 'card': {'keywords': []}}]}}
    assert [(p['id'], p['name']) for p in target.cards(context)] == [('T1', '잠자리 협상가')]
    assert target.cards({}) == []


def test_anchor_texts_cover_card_slices_and_quotes():
    texts = target.anchor_texts(persona())
    assert texts[0].startswith('이름: 잠자리 협상가')
    assert '푹 자고 싶음. 남편과 같은 방에서 잠. 코골이 때문에 각방' in texts
    assert '코골이, 각방' in texts and '코고는 소리 때문에 잠을 못 자요' in texts
    assert len(texts) == len(set(texts))


def test_score_is_max_cosine_per_persona():
    vectors = np.eye(3, dtype=np.float32)
    personas = [persona(), dict(persona(), id='T2')]
    def embed(texts):
        # First persona's anchors point at axis 0, the second's at axis 1.
        half = len(texts) // 2
        return np.asarray([[1, 0, 0]] * half + [[0, 1, 0]] * (len(texts) - half), dtype=np.float32)
    scores = target.score(vectors, personas, embed, chunk=2)
    assert scores.shape == (3, 2)
    np.testing.assert_allclose(scores, [[1, 0], [0, 1], [0, 0]], atol=1e-6)


class _Result:
    def __init__(self, data):
        self.ok, self.data = data is not None, data


def test_calibrate_picks_lowest_band_with_passing_bands_above():
    rng = np.random.default_rng(0)
    top = np.concatenate([rng.uniform(.45, .55, 40), rng.uniform(.60, .75, 40)])
    scores = np.stack([top, np.zeros_like(top)], axis=1).astype(np.float32)
    ids = [f'd{i}' for i in range(len(top))]
    docs = {i: {'title': i, 'body': f'score {s:.3f}'} for i, s in zip(ids, top)}
    def run_task(task):
        value = float(task.attachments[1].body.split()[-1])
        return _Result(target.JudgeOut(match='yes' if value >= .6 else 'no'))
    result = target.calibrate('sid', scores, ids, docs, [persona(), dict(persona(), id='T2')], run_task, random.Random(1))
    assert result['T1']['threshold'] == .60
    assert result['T2']['threshold'] is None
    assert sum(b['docs'] for b in result['T1']['bands']) == len(top)


def test_calibrate_stops_at_a_failing_band_even_if_lower_bands_pass():
    top = np.array([.46] * 10 + [.52] * 10 + [.71] * 10, dtype=np.float32)
    scores = top[:, None]
    ids = [str(i) for i in range(len(top))]
    docs = {i: {'body': str(s)} for i, s in zip(ids, top)}
    def run_task(task):
        return _Result(target.JudgeOut(match='no' if task.attachments[1].body.startswith('0.52') else 'yes'))
    result = target.calibrate('sid', scores, ids, docs, [persona()], run_task)
    assert result['T1']['threshold'] == .70


def test_calibrate_skips_thinly_judged_top_bands():
    top = np.array([.66] * 20 + [.72] * 20 + [.85] * 3, dtype=np.float32)
    ids = [str(i) for i in range(len(top))]
    docs = {i: {'body': f'{s:.2f}'} for i, s in zip(ids, top)}
    def run_task(task):
        return _Result(target.JudgeOut(match='no' if task.attachments[1].body in ('0.66', '0.85') else 'yes'))
    result = target.calibrate('sid', top[:, None], ids, docs, [persona()], run_task)
    assert result['T1']['threshold'] == .70
    assert [b['judged'] for b in result['T1']['bands'] if b['docs']] == [20, 20, 3]


def test_calibrate_finds_a_narrow_core_above_seventy():
    top = np.array([.71] * 20 + [.76] * 20 + [.82] * 20, dtype=np.float32)
    ids = [str(i) for i in range(len(top))]
    docs = {i: {'body': f'{s:.2f}'} for i, s in zip(ids, top)}
    def run_task(task):
        return _Result(target.JudgeOut(match='no' if task.attachments[1].body == '0.71' else 'yes'))
    assert target.calibrate('sid', top[:, None], ids, docs, [persona()], run_task)['T1']['threshold'] == .75


def test_calibrate_judges_borderline_bands_again_on_more_documents():
    # .70 band: 21 of 40 documents fit, so twenty samples land near .5 either way.
    top = np.array([.71] * 40 + [.76] * 60, dtype=np.float32)
    ids = [str(i) for i in range(len(top))]
    docs = {i: {'body': 'yes' if int(i) < 21 or int(i) >= 40 else 'no'} for i in ids}
    calls = []
    def run_task(task):
        calls.append(task.attachments[1].body)
        return _Result(target.JudgeOut(match=task.attachments[1].body))
    result = target.calibrate('sid', top[:, None], ids, docs, [persona()], run_task, random.Random(0))
    bands = {b['start']: b for b in result['T1']['bands']}
    assert bands[.70]['judged'] == 40 and bands[.70]['precision'] == .525
    assert bands[.75]['judged'] == 20  # a clear pass is not judged again
    assert result['T1']['threshold'] == .70
    assert len(calls) == 60


def test_calibrate_rechecks_a_lower_band_reached_only_after_a_recheck():
    # .65 band fits 19 of 40 (fails on the full count); .70 band fits 22 of 40 (passes).
    top = np.array([.66] * 40 + [.71] * 40 + [.81] * 20, dtype=np.float32)
    ids = [str(i) for i in range(len(top))]
    fits = set(range(19)) | set(range(40, 62)) | set(range(80, 100))
    docs = {i: {'body': 'yes' if int(i) in fits else 'no'} for i in ids}
    def run_task(task):
        return _Result(target.JudgeOut(match=task.attachments[1].body))
    result = target.calibrate('sid', top[:, None], ids, docs, [persona()], run_task, random.Random(3))
    bands = {b['start']: b for b in result['T1']['bands']}
    assert bands[.70]['judged'] == 40 and bands[.70]['precision'] == .55
    assert bands[.65]['judged'] == 40 and bands[.65]['precision'] == .475
    assert result['T1']['threshold'] == .70


def test_calibrate_judges_fetched_originals_over_short_previews():
    top = np.array([.71] * 4, dtype=np.float32)
    ids = [f'd{i}' for i in range(4)]
    docs = {i: {'body': 'preview'} for i in ids}
    seen, asked = [], []
    def fetch(wanted):
        asked.append(set(wanted))
        return {i: 'long original ' * 50 for i in wanted if i != 'd3'}
    def run_task(task):
        seen.append(task.attachments[1].body)
        return _Result(target.JudgeOut(match='yes'))
    target.calibrate('sid', top[:, None], ids, docs, [persona()], run_task, fetch=fetch)
    assert asked == [set(ids)]
    assert sorted(seen) == ['long original ' * 50] * 3 + ['preview']


def test_full_texts_reads_title_and_body_from_preparation(tmp_path, monkeypatch):
    from app.segment import inputs
    (tmp_path / 'docs').mkdir()
    rows = [dict(doc_id='a', title='T', body='x' * 3000, comments=[{'text': 'c'}]),
            dict(doc_id='b', title='', body='short'), dict(doc_id='c', title='skip', body='me')]
    (tmp_path / 'docs' / 'part-0.jsonl').write_text('\n'.join(json.dumps(r) for r in rows), encoding='utf-8')
    monkeypatch.setattr(inputs.store, 'read_json', lambda path: {})
    monkeypatch.setattr(inputs, 'prepared_root', lambda sid, data: tmp_path)
    got = inputs.full_texts('sid', 'v1', ['a', 'b'], 1500)
    assert got == {'a': ('T\n' + 'x' * 3000)[:1500], 'b': 'short'}
    assert inputs.full_texts('sid', 'v1', [], 1500) == {}


def test_near_duplicates_flags_copy_paste_groups():
    rng = np.random.default_rng(0)
    base = rng.normal(size=8)
    copies = base + rng.normal(0, .01, (5, 8))
    unique = rng.normal(size=(5, 8))
    mask = target.near_duplicates(np.vstack([copies, unique]))
    assert mask[:5].all() and not mask[5:].any()


def test_assign_respects_threshold_and_exclusions():
    scores = np.array([[.8, .1], [.5, .2], [.2, .9], [.75, .1]], dtype=np.float32)
    personas = [persona(), dict(persona(), id='T2')]
    thresholds = {'T1': {'threshold': .6}, 'T2': {'threshold': None}}
    excluded = np.array([False, False, False, True])
    assert target.assign(scores, thresholds, personas, excluded).tolist() == [0, -1, -1, -1]


def test_need_sentences_and_quotes_skip_ads_and_repeated_titles():
    assert target.need_sentences('날씨가 좋네요. 코골이 때문에 잠을 못자서 너무 힘들어요. 남편이랑 각방을 써야 할까요?') == [
        '코골이 때문에 잠을 못자서 너무 힘들어요.', '남편이랑 각방을 써야 할까요?']
    docs = {'a': {'title': '각방 고민', 'body': '남편 코골이 때문에 너무 힘들어요.'},
            'b': {'title': '각방 고민', 'body': '같은 제목의 다른 글인데 너무 힘들어요.'},
            'c': {'title': '추천', 'body': '체험단으로 받은 제품인데 숙면 고민 해결했어요.'},
            'd': {'title': '일기', 'body': '오늘은 맑음.'}}
    assert [q['docId'] for q in target.quotes(['a', 'b', 'c', 'd'], docs)] == ['a']


def test_group_causes_folds_members_and_falls_back():
    causes = ['야근', '회사 스트레스', '아이 육아']
    out = target.CausesOut(groups=[{'label': '직장', 'members': [0, 1, 1]}, {'label': '중복', 'members': [0]}])
    groups = target.group_causes('sid', persona(), causes, lambda task: _Result(out))
    assert groups == [dict(label='직장', count=2), dict(label='기타', count=1)]
    fallback = target.group_causes('sid', persona(), causes + ['야근'], lambda task: _Result(None))
    assert fallback[0] == dict(label='야근', count=2)


def test_render_includes_card_without_changing_plain_seeds():
    from app.context.render import _personas
    from app.context.models import PersonaSeeds
    lines = _personas(PersonaSeeds(items=[{'text': '잠자리 협상가', 'card': CARD}, {'text': '보호자'}]))
    assert '- 잠자리 협상가' in lines and '  - Pain Point: 코골이 때문에 각방' in lines
    assert lines[lines.index('- 보호자') + 1] != '  - Desire: 푹 자고 싶음'


# --- pipeline: target mode end to end on the synthetic session -------------

class Context:
    def __init__(self, sid, version='v1', args=None):
        self.sid, self.version, self.args = sid, version, args or {}
        self.events = []

    def heartbeat(self, progress, detail):
        self.events.append((progress, detail))

    def should_stop(self):
        return False


@pytest.fixture
def target_session(data_dir, monkeypatch):
    monkeypatch.setattr(settings, 'embed_backend', 'fake')
    monkeypatch.setattr(settings, 'llm_backend', 'fake')
    monkeypatch.setattr(params, 'DISCOVER_K', 3)
    tasks = []

    class Backend:
        def run(self, task):
            tasks.append(task.task)
            if task.task == 'segment.dims':
                return fake_dims_backend([a.title for a in task.attachments]).run(task)
            return FakeBackend().run(task)
    monkeypatch.setattr(registry, 'get_backend', lambda name: Backend())
    fixture = make_segment_session(data_dir, clusters=3, personas=(2, 2, 2), contexts=(2,) * 6, docs_per_context=30)
    path = version_dir(fixture.sid, fixture.version) / 'session.json'
    data = sessions.read_json(path)
    data.setdefault('projectContext', {})['personaSeeds'] = {'items': [
        {'text': '첫째 묶음', 'card': CARD}, {'text': '둘째 묶음', 'card': {**CARD, 'pain': '둘째'}}, {'text': '카드 없음'}]}
    data['projectContext'].setdefault('oneLiner', '집에서 건강하게')
    sessions.write_json(path, data)

    def fake_score(vectors, personas, embed, chunk=50_000):
        # Persona j points at a document of synthetic cluster j (120 documents per cluster, 3 dropped from the first).
        unit = target._unit(vectors)
        refs = unit[[10, 130]]
        return (unit @ refs.T).astype(np.float32)
    monkeypatch.setattr(pipeline.target, 'score', fake_score)
    return fixture, tasks


def test_target_mode_end_to_end(target_session):
    fixture, tasks = target_session
    pipeline.run(Context(fixture.sid, args={'mode': 'target'}))
    root = version_dir(fixture.sid, 'v1') / 'segment'
    assert sessions.read_json(root / 'checkpoint.json')['mode'] == 'target'
    assert sessions.read_json(root / 'checkpoint.json')['done'] == list(pipeline.TARGET_STEPS)
    store = SegmentStore.open(fixture.sid, 'v1')
    clusters = {row['cluster_id']: row for row in store.clusters()}
    assert set(clusters) == {'T1', 'T2'}
    assert {row['name_draft'] for row in clusters.values()} == {'첫째 묶음', '둘째 묶음'}
    expected = fixture.expected['assignments']
    docs = store.docs(limit=10000)
    by_cluster = {row['doc_id']: row['cluster_id'] for row in docs}
    # Each target collects exactly its synthetic cluster (minus zero-vector rows); the third cluster is 'other'.
    assert {expected[d]['cluster'] for d, c in by_cluster.items() if c == 'T1'} == {'CL0'}
    assert {expected[d]['cluster'] for d, c in by_cluster.items() if c == 'T2'} == {'CL1'}
    assert all(row['persona_id'].startswith(row['cluster_id'] + '-P') for row in docs)
    assert all(row['context_id'] and row['context_id'].startswith(row['persona_id']) for row in docs)
    report = sessions.read_json(root / 'target.json')
    assert report['assigned'] == len(docs) and report['assigned'] + report['other'] == report['total']
    first = report['personas'][0]
    # The 0.70-0.75 band holds too few docs to judge on its own, so it neither passes nor stops.
    assert first['threshold'] == .75 and first['docs'] > 0 and first['needs']['mine'] > 0
    assert first['needs']['tried'][0]['tried'] == '제품·기기'
    assert report['discovered'] and report['discovered'][0]['label']['name'] == '새 후보'
    assert 'segment.cluster_name' not in tasks
    assert {'segment.target_judge', 'segment.target_needs', 'segment.target_causes', 'segment.target_discover'} <= set(tasks)
    preview = sessions.read_json(root / 'preview.json')
    assert preview['mode'] == 'target' and {c['id'] for c in preview['clusters']} == {'T1', 'T2'}
    stage6 = sessions.read_json(root / 'stage_6.json')
    assert stage6['L1']['mode'] == 'target'


def test_target_mode_without_cards_fails_cleanly(target_session):
    fixture, _ = target_session
    path = version_dir(fixture.sid, fixture.version) / 'session.json'
    data = sessions.read_json(path)
    data['projectContext']['personaSeeds'] = {'items': [{'text': '카드 없음'}]}
    sessions.write_json(path, data)
    with pytest.raises(sessions.StoreError):
        pipeline.run(Context(fixture.sid, args={'mode': 'target'}))
    assert sessions.read_json(path)['segment']['status'] == 'failed'
