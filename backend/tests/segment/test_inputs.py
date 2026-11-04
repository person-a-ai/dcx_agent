import json
from collections import Counter
from types import SimpleNamespace

import numpy as np
import pytest

from app.context import store
from app.context.versions import version_dir
from app.model.infer import documents, prepared_root
from app.prep import tokens as prep_tokens
from app.segment.inputs import load_input
from tests.fixtures.segment_synth import make_segment_session


@pytest.fixture
def session(data_dir):
    return make_segment_session(data_dir, clusters=1, personas=(2,), contexts=(2, 2), docs_per_context=4)


def snapshot(session):
    return store.read_json(version_dir(session.sid, session.version) / 'session.json')


def write_rows(path, rows):
    store.atomic_write(path, ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))


def test_input_exclusions_float16_normalization_and_truncation(session):
    data = snapshot(session)
    root = prepared_root(session.sid, data)
    docs = documents(session.sid, data)
    docs['d000003']['body'] = '가' * 2001
    docs['d000004']['comments'] = [{'text': '나' * 2001}]
    for path in (root / 'docs').glob('*.jsonl'):
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        write_rows(path, [docs[r['doc_id']] for r in rows])
    result = load_input(session.sid, session.version)
    assert len(result.ids) == session.expected['documents'] - 3
    assert not set(result.ids) & set(session.expected['zero_vector_ids'] + session.expected['no_token_ids'])
    assert set(result.ids) == set(result.tokens) == set(result.nouns) == set(result.docs)
    assert result.vectors.dtype == np.float16
    np.testing.assert_allclose(np.linalg.norm(result.vectors.astype(np.float32), axis=1), 1, atol=.001)
    assert result.report == dict(relevant=16, zero_vector=2, no_tokens=1, truncated=2,
                                by_channel=dict(Counter(docs[i]['source'] for i in result.ids)))
    for doc_id in result.ids:
        assert result.nouns[doc_id] == result.tokens[doc_id]
        assert all(isinstance(t, str) for t in result.tokens[doc_id])


def test_channel_from_derived_not_export(session):
    data = snapshot(session)
    prepared = documents(session.sid, data)
    path = version_dir(session.sid, session.version).parents[3] / data['training']['exportRef']
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    for row in rows:
        row['source'] = 'agreed'
        for key in ('author_hash', 'comments', 'date'):
            row.pop(key, None)
    write_rows(path, rows)
    result = load_input(session.sid, session.version)
    assert 'agreed' not in result.report['by_channel']
    assert sum(result.report['by_channel'].values()) == len(result.ids)
    for doc_id, doc in result.docs.items():
        for key in ('source', 'author_hash', 'date'):
            assert doc[key] == prepared[doc_id][key]
        assert doc['comments'] == [{'text': (c.get('text') or '')[:300]}
                                   for c in prepared[doc_id]['comments'][:1]]
        assert doc['evidence_level_pred'] in {'core', 'supporting'}


def test_load_input_does_not_take_session_lock(session, monkeypatch, data_dir):
    data = snapshot(session)
    root = prepared_root(session.sid, data)
    manifest = store.read_json(root / 'manifest.json')
    manifest['config']['tokenPos'] = ['NNG', 'NNP', 'VV', 'VA', 'XR']
    store.write_json(root / 'manifest.json', manifest)
    export_path = data_dir / data['training']['exportRef']
    export_rows = [json.loads(line) for line in export_path.read_text().splitlines()]
    write_rows(export_path, export_rows[3:5])
    calls = []

    def kiwi():
        calls.append(1)
        return SimpleNamespace(tokenize=lambda text: [SimpleNamespace(form='냉방', tag='NNG')])

    def unexpected_lock(sid):
        pytest.fail('load_input must not acquire the shared session lock')

    monkeypatch.setattr(prep_tokens, '_kiwi', kiwi)
    monkeypatch.setattr(store, 'locked', unexpected_lock)
    first = load_input(session.sid, session.version)
    assert first.ids == ['d000003', 'd000004']
    assert len(calls) == session.expected['documents']
    calls.clear()
    assert load_input(session.sid, session.version).nouns == first.nouns
    # Another version can select previously irrelevant docs without rebuilding.
    expanded_ref = f'classified/{session.sid}/v2/gen-synth/relevant.jsonl'
    write_rows(data_dir / expanded_ref, export_rows)
    store.write_json(version_dir(session.sid, 'v2') / 'session.json', {
        **data, 'training': {**data['training'], 'exportRef': expanded_ref},
    })
    expanded = load_input(session.sid, 'v2')
    assert len(expanded.ids) == session.expected['documents'] - 3
    assert all(words == ['냉방'] for words in expanded.nouns.values())
    assert not calls


def test_truncated_counts_only_final_target_docs(session):
    data = snapshot(session)
    root = prepared_root(session.sid, data)
    docs = documents(session.sid, data)
    excluded = session.expected['zero_vector_ids'] + session.expected['no_token_ids']
    for doc_id in excluded + ['d000003']:
        docs[doc_id]['body'] = '가' * 2001
    docs['d000004']['comments'] = [{'text': '나' * 2001}]
    for path in (root / 'docs').glob('*.jsonl'):
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        write_rows(path, [docs[row['doc_id']] for row in rows])

    result = load_input(session.sid, session.version)
    assert not set(result.ids) & set(excluded)
    assert {'d000003', 'd000004'} <= set(result.ids)
    assert result.report['truncated'] == 2


def test_nouns_cached_next_to_derived(session, monkeypatch):
    data = snapshot(session)
    root = prepared_root(session.sid, data)
    manifest = store.read_json(root / 'manifest.json')
    manifest['config']['tokenPos'] = ['NNG', 'NNP', 'VV']
    store.write_json(root / 'manifest.json', manifest)
    calls = []
    def kiwi():
        calls.append(1)
        return SimpleNamespace(tokenize=lambda text: [SimpleNamespace(form='냉방', tag='NNG'),
                                                       SimpleNamespace(form='하다', tag='VV')])
    monkeypatch.setattr(prep_tokens, '_kiwi', kiwi)
    writes = []
    original = store.atomic_write
    def atomic(path, text):
        writes.append(path)
        original(path, text)
    monkeypatch.setattr(store, 'atomic_write', atomic)
    result = load_input(session.sid, session.version)
    assert calls
    assert all(n == ['냉방'] for n in result.nouns.values())
    assert list((root / 'nouns').glob('part-*.jsonl'))
    assert any(p.parent == root / 'nouns' and p.name.startswith('part-') for p in writes)
    calls.clear()
    assert load_input(session.sid, session.version).nouns == result.nouns
    assert not calls
    store.write_json(version_dir(session.sid, 'v2') / 'session.json', data)
    assert load_input(session.sid, 'v2').nouns == result.nouns
    assert not calls
    # A partial generation is not a cache, regardless of plausible row contents.
    (root / 'nouns/manifest.json').unlink()
    write_rows(root / 'nouns/part-99999.jsonl', [{'doc_id': result.ids[0], 'nouns': ['partial']}])
    assert load_input(session.sid, 'v2').nouns == result.nouns
    assert calls
    assert not (root / 'nouns/part-99999.jsonl').exists()


def test_missing_tokens_requires_reprep(session):
    root = prepared_root(session.sid, snapshot(session))
    for path in (root / 'tokens').glob('*.jsonl'):
        path.unlink()
    with pytest.raises(store.StoreError, match='토큰'):
        load_input(session.sid, session.version)


def test_noun_only_tokens_need_no_kiwi(session, monkeypatch):
    def unexpected():
        pytest.fail('Noun-only preparation should not invoke Kiwi')
    monkeypatch.setattr(prep_tokens, '_kiwi', unexpected)
    first = load_input(session.sid, session.version)
    second = load_input(session.sid, session.version)
    assert first.nouns == first.tokens == second.nouns


def test_damaged_completed_cache_is_rebuilt(session):
    first = load_input(session.sid, session.version)
    root = prepared_root(session.sid, snapshot(session))
    part = next((root / 'nouns').glob('part-*.jsonl'))
    store.atomic_write(part, '{broken json')
    assert load_input(session.sid, session.version).nouns == first.nouns
    part.unlink()
    assert load_input(session.sid, session.version).nouns == first.nouns


def test_empty_relevant_input(session, data_dir):
    data = snapshot(session)
    store.atomic_write(data_dir / data['training']['exportRef'], '')
    result = load_input(session.sid, session.version)
    assert result.ids == []
    assert result.vectors.shape == (0, 1024)
    assert result.vectors.dtype == np.float16
    assert result.report == dict(relevant=0, zero_vector=0, no_tokens=0, truncated=0, by_channel={})


def test_failed_cache_publication_is_rebuilt(session, monkeypatch):
    root = prepared_root(session.sid, snapshot(session))
    original = store.atomic_write
    def interrupted(path, text):
        if path == root / 'nouns/manifest.json':
            raise OSError('simulated interruption')
        original(path, text)
    with monkeypatch.context() as patch:
        patch.setattr(store, 'atomic_write', interrupted)
        with pytest.raises(OSError, match='simulated interruption'):
            load_input(session.sid, session.version)
    assert list((root / 'nouns').glob('part-*.jsonl'))
    assert not (root / 'nouns/manifest.json').exists()
    assert len(load_input(session.sid, session.version).ids) == 13
    assert store.read_json(root / 'nouns/manifest.json')['status'] == 'done'


def test_sparse_collection_memory_and_noun_pulse(session, data_dir, monkeypatch):
    import gc
    import tracemalloc
    from app.segment import inputs
    data = snapshot(session)
    root = prepared_root(session.sid, data)
    export = data_dir / data['training']['exportRef']
    rows = [json.loads(line) for line in export.read_text().splitlines()]
    write_rows(export, rows[3:5])
    monkeypatch.setattr(inputs, '_SHARD_ROWS', 100)
    def measure(extra):
        import shutil
        shutil.rmtree(root / 'nouns', ignore_errors=True)
        with (root / 'docs/extra.jsonl').open('w') as docs, (root / 'tokens/extra.jsonl').open('w') as tokens:
            for i in range(extra):
                docs.write(json.dumps({'doc_id': f'extra{i}', 'body': 'x'*8000})+'\n')
                tokens.write(json.dumps({'doc_id': f'extra{i}', 'tokens': ['noun']*20})+'\n')
        manifest = store.read_json(root / 'manifest.json')
        manifest['counts']['after'] = extra + 16
        store.write_json(root / 'manifest.json', manifest)
        gc.collect()
        tracemalloc.start()
        result = load_input(session.sid, 'v1')
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        assert result.ids == ['d000003', 'd000004']
        assert store.read_json(root / 'nouns/manifest.json')['count'] == extra + 16
        return peak
    small = measure(200)
    large = measure(4000)
    assert large < small * 3 + 2_000_000


def test_noun_build_pulses_and_stops(session, monkeypatch):
    from app.segment import inputs
    root = prepared_root(session.sid, snapshot(session))
    manifest = store.read_json(root / 'manifest.json')
    manifest['config']['tokenPos'] = ['VV']
    store.write_json(root / 'manifest.json', manifest)
    monkeypatch.setattr(inputs, 'tokenize', lambda *a: ['noun'])
    events = []
    class Stopped(BaseException):
        pass
    def pulse(**detail):
        events.append(detail)
        if detail['docs'] >= 2:
            raise Stopped
    with pytest.raises(Stopped):
        load_input(session.sid, 'v1', pulse=pulse)
    assert events[0] == {'docs': 0, 'total': 16}
    assert not (root / 'nouns/manifest.json').exists()
    assert load_input(session.sid, 'v1').ids


def test_sparse_vectors_do_not_materialize_collection_index(session, monkeypatch):
    from app.vectors.store import VectorStore
    monkeypatch.setattr(VectorStore, '_records', lambda self: pytest.fail('whole collection vector index loaded'))
    result = load_input(session.sid, 'v1')
    assert len(result.ids) == 13
    np.testing.assert_allclose(np.linalg.norm(result.vectors.astype(np.float32), axis=1), 1, atol=.001)


def test_compact_input_and_resume_preserve_consumers(session, data_dir, monkeypatch):
    import sys
    from app.segment.inputs import SegmentInput, _join, restore_input
    from app.segment.pipeline import _reps
    from app.segment.signals import document_signals
    from app.segment.quality import channel_distribution
    data = snapshot(session)
    root = prepared_root(session.sid, data)
    prepared = documents(session.sid, data)
    for doc in prepared.values():
        doc.update(title='title' * 100, body='body' * 1000,
                   comments=[{'text': 'comment' * 100, 'unused': 'x'}, {'text': 'later'}],
                   unused='x' * 10000)
        if int(doc['doc_id'][1:]) % 3 != 2:
            doc['body'] = ''
        if int(doc['doc_id'][1:]) % 3 == 1:
            doc['title'] = ''
    for path in (root / 'docs').glob('*.jsonl'):
        write_rows(path, [prepared[r['doc_id']] for r in map(json.loads, path.read_text().splitlines())])
    export = data_dir / data['training']['exportRef']
    rows = list(map(json.loads, export.read_text().splitlines()))
    from app.segment import inputs
    with monkeypatch.context() as patch:
        patch.setattr(inputs, '_compact', _join)
        baseline = load_input(session.sid, session.version)
    result = load_input(session.sid, session.version)
    assert result.ids == baseline.ids
    np.testing.assert_array_equal(result.vectors, baseline.vectors)
    assert result.tokens == baseline.tokens
    assert result.nouns == baseline.nouns
    assert result.report == baseline.report
    full = SegmentInput(result.ids, result.vectors, result.tokens, result.nouns,
                        {r['doc_id']: _join(r, prepared[r['doc_id']]) for r in rows}, result.report)
    for source in (full, result):
        source.index = {i: n for n, i in enumerate(source.ids)}
    assert _reps(result, result.ids) == _reps(full, full.ids)
    for doc_id in result.ids:
        assert _reps(result, [doc_id]) == _reps(full, [doc_id])
    assert document_signals(result) == document_signals(full)
    assert channel_distribution(result.docs.values()) == channel_distribution(full.docs[i] for i in full.ids)
    allowed = {'doc_id', 'title', 'body', 'comments', 'source', 'author_hash', 'date',
               'evidence_level_pred', 'pred_entropy'}
    for doc in result.docs.values():
        assert set(doc) <= allowed
        original = prepared[doc['doc_id']]
        assert doc['body'] == original['body'][:300]
        assert doc['title'] == original['title'][:300]
        assert doc['comments'] == [{'text': ('comment' * 100)[:300]}]
        assert len(json.dumps(doc)) < 3000
    for words in [*result.tokens.values(), *result.nouns.values()]:
        assert all(w is sys.intern(w) for w in words)
    restored = restore_input(session.sid, session.version,
                             {'ids': result.ids, 'report': result.report}, result.vectors)
    assert restored.docs == result.docs
    assert restored.tokens == result.tokens
    assert restored.nouns == result.nouns
    write_rows(export, list(reversed(rows)))
    reordered = load_input(session.sid, session.version)
    assert reordered.ids == list(reversed(result.ids))
    assert reordered.docs == result.docs
    assert reordered.report == result.report
    np.testing.assert_array_equal(reordered.vectors, result.vectors[::-1])


def test_large_join_retains_only_compact_rows(tmp_path, monkeypatch):
    import tracemalloc
    from app.segment import inputs
    root = tmp_path
    (root / 'docs').mkdir()
    count = 3000
    with (root / 'docs/part-00001.jsonl').open('w') as stream:
        for i in range(count):
            stream.write(json.dumps({'doc_id': str(i), 'body': 'x' * 20000,
                                     'unused': 'y' * 20000}) + '\n')
    monkeypatch.setattr(inputs, '_exports', lambda *args: (
        {'doc_id': str(i), 'evidence_level_pred': 'core', 'unused': 'z' * 20000}
        for i in range(count)))
    selected = {str(i) for i in range(count)}
    tracemalloc.start()
    try:
        docs = dict((doc['doc_id'], doc) for doc, _ in inputs._joined_rows('', {}, root, selected))
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert len(docs) == count
    assert peak < 8_000_000
    assert all(len(doc['body']) == 300 and 'unused' not in doc for doc in docs.values())
