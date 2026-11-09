import json
import sqlite3

from app.label import judge, overview


def _db(tmp_path, n):
    path = tmp_path / 'labels.sqlite'
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE documents (doc_id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
        db.executemany('INSERT INTO documents VALUES (?,?)',
                       [(f'd{i}', json.dumps({'doc_id': f'd{i}', 'title': '제목', 'body': '본문 ' * 20})) for i in range(n)])
    return str(path)


def test_estimate_skips_the_corpus_when_nothing_is_pending(tmp_path, monkeypatch):
    path = _db(tmp_path, 3)
    overview._estimate.cache_clear()
    monkeypatch.setattr(judge, 'estimate', lambda *a, **k: (_ for _ in ()).throw(AssertionError('corpus read')))
    assert overview._estimate(path, 'jev', (0, 3, 0), 'ctx', ('s',)) == dict(seconds=0, jevTokens=0)


def test_estimate_streams_documents_with_the_same_result(tmp_path):
    path = _db(tmp_path, 25)
    overview._estimate.cache_clear()
    with sqlite3.connect(path) as db:
        docs = [json.loads(row[0]) for row in db.execute('SELECT payload FROM documents')]
    expected = judge.estimate(docs, 'ctx', 'jev')
    if expected['seconds'] is not None:
        expected['seconds'] *= 10 / 25
    streamed = overview._IndexedDocuments(path)
    assert len(streamed) == 25 and not isinstance(streamed, list)
    assert overview._estimate(path, 'jev', (10, 15, 0), 'ctx', ('s',)) == expected


def test_estimate_before_judging_starts_reads_the_corpus(tmp_path):
    path = _db(tmp_path, 4)
    overview._estimate.cache_clear()
    with sqlite3.connect(path) as db:
        docs = [json.loads(row[0]) for row in db.execute('SELECT payload FROM documents')]
    assert overview._estimate(path, 'jev', (0, 0, 0), 'ctx', ('s',)) == judge.estimate(docs, 'ctx', 'jev')


def test_streamed_documents_are_read_in_chunks_without_holding_a_lock(tmp_path, monkeypatch):
    path = _db(tmp_path, 7)
    monkeypatch.setattr(overview._IndexedDocuments, 'chunk', 3)
    seen = []
    for doc in overview._IndexedDocuments(path):
        seen.append(doc['doc_id'])
        # A writer must not wait on the reader between rows.
        with sqlite3.connect(path, timeout=0) as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('UPDATE documents SET payload=payload WHERE doc_id=?', (doc['doc_id'],))
    assert seen == [f'd{i}' for i in range(7)]
