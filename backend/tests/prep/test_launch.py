from contextlib import closing
from importlib.util import find_spec

from app.config import settings
from app.context import store
from app.crawl.queue import CrawlQueue
from app.work import runner


def _ready(data_dir, sid='launch'):
    root = data_dir / 'crawl' / sid / 'collections/c1'
    store.write_json(root / 'manifest.json', {'parent': None})
    with closing(CrawlQueue(root / 'queue.sqlite')) as queue:
        queue.finish_run(queue.register_run('detail'), 'done')
    store.update_session(sid, {'schemaVersion': 2, 'collectionId': 'c1'})
    return sid


def test_start_prep_launches_worker_and_saves_run(data_dir, monkeypatch):
    monkeypatch.setattr(settings, 'embed_backend', 'fake')
    launched = []
    monkeypatch.setattr(runner, 'start', lambda sid, v, kind, args: launched.append((kind, args)) or
                        {'runId': 'r1', 'state': 'running', 'progress': 0})
    assert find_spec('app.prep.launch') is not None, 'Shared preparation launcher must exist'
    from app.prep.launch import start_prep
    sid = _ready(data_dir)
    result = start_prep(sid)
    assert result['runId'] == 'r1' and result['status'] == 'running'
    assert launched[0][0] == 'prep'
    prep = store.load_session(sid)['prep']
    assert prep['runId'] == 'r1' and prep['derivedRef']['collectionId'] == 'c1'


def test_router_uses_start_prep(client, data_dir, monkeypatch):
    monkeypatch.setattr(settings, 'embed_backend', 'fake')
    monkeypatch.setattr(runner, 'start', lambda *a: {'runId': 'r2', 'state': 'running', 'progress': 0})
    sid = _ready(data_dir, 'launch2')
    response = client.post(f'/prep/{sid}/run')
    assert response.status_code == 200 and response.json()['runId'] == 'r2'


def test_router_delegates_session_and_version(client, monkeypatch):
    assert find_spec('app.prep.launch') is not None, 'Shared preparation launcher must exist'
    from app.prep import launch
    calls = []
    result = {'status': 'running', 'runId': 'r3', 'progress': 0, 'reused': False}

    def start(sid, version=None):
        calls.append((sid, version))
        return result

    monkeypatch.setattr(launch, 'start_prep', start)
    response = client.post('/prep/delegated/run?version=v2')
    assert response.status_code == 200
    assert response.json() == result
    assert calls == [('delegated', 'v2')]
