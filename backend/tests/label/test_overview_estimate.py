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
