"""Display labels are projections; historical reports are immutable reads."""
from contextlib import closing
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.context import store, versions
from app.crawl import control
from app.crawl.queue import CrawlQueue
from app.keywords import display
from app.main import app


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, 'local_data_dir', str(tmp_path))
    monkeypatch.setattr(control, 'available_sources', lambda: ['youtube_vlog'])
    session = dict(schemaVersion=2, sid='S', collectionId='c1',
                   keywords=[dict(kw='에어컨청소', status='approved')])
    store.update_session('S', session)
    root = control.collection_dir('S')
    root.mkdir(parents=True)
    store.write_json(root / 'meta.json', dict(keywords=[dict(kw='수집키워드')], parent=None))
    store.write_json(root / 'manifest.json', dict(channels=['youtube_vlog']))
    with closing(CrawlQueue(root / 'queue.sqlite')):
        pass
    store.write_json(root / 'gate.json', dict(rows=[dict(kw='게이트키워드')]))
    report = dict(matrix={'보고서키워드': {}}, counts={'집계키워드': {}},
                  channels={'youtube_vlog': dict(docs=7, urls_done=2, share=1,
                      skip_reasons={'no_ko_captions': 3})}, totals=dict(doc_count=7))
    store.write_json(root / 'report.json', report)
    return SimpleNamespace(root=root, base=tmp_path, report=report, client=TestClient(app))


def test_status_labels_cover_session_collection_gate_and_report(env):
    response = env.client.get('/crawl/S/status')
    assert response.status_code == 200
    data = response.json()
    assert data['keywordDisplay']['에어컨청소'] == '에어컨 청소'
    assert set(data['keywordDisplay']) == {'에어컨청소', '수집키워드', '게이트키워드', '보고서키워드', '집계키워드'}
    assert data['gate'][0]['kw'] == '게이트키워드'
    assert data['report'] == env.report
    assert data['collection_keywords'] == ['수집키워드']
    assert store.load_session('S')['keywords'][0]['kw'] == '에어컨청소'
    assert store.read_json(env.root / 'report.json') == env.report


def test_idle_status_labels_fall_back_to_raw_keyword(env, monkeypatch):
    store.update_session('S', {'collectionId': None})
    monkeypatch.setattr(display, 'display_form', lambda kw: kw)
    data = env.client.get('/crawl/S/status').json()
    assert data['status'] == 'idle'
    assert data['keywordDisplay'] == {'에어컨청소': '에어컨청소'}


def snapshot(base):
    return {str(p.relative_to(base)): (p.read_bytes(), p.stat().st_mtime_ns)
            for p in base.rglob('*') if p.is_file()}


def forbid_writes(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('Historical report must not write, lock, or inspect live state')
    for module, names in [(store, ['write_json', 'locked', 'load_session']),
                          (control, ['collection_lock', 'status', 'latest_run'])]:
        for name in names:
            monkeypatch.setattr(module, name, forbidden)


def test_history_reads_own_collection_with_another_version_active_without_writes(env, monkeypatch):
    # The active collection deliberately lacks a queue: history must not inspect it.
    active = dict(versions._data('S', 'v1'), version='v2', collectionId='c2', keywords=[dict(kw='현재키워드')])
    store.write_json(versions.version_dir('S', 'v2') / 'session.json', active)
    versions._activate_link(store.root_dir('S'), 'v2')
    meta = versions._meta('S')
    store.write_json(store.root_dir('S') / 'meta.json', dict(meta, activeVersion='v2'))
    store.write_json(env.root.parent / 'c2' / 'report.json', dict(totals=dict(doc_count=999)))
    before = snapshot(env.base)
    forbid_writes(monkeypatch)
    response = env.client.get('/crawl/S/report?version=v1')
    assert response.status_code == 200
    data = response.json()
    assert set(data) == {'version', 'collectionId', 'report', 'keywordDisplay'}
    assert data['version'] == 'v1'
    assert data['collectionId'] == 'c1'
    assert data['report'] == env.report
    assert data['keywordDisplay']['에어컨청소'] == '에어컨 청소'
    assert {'보고서키워드', '집계키워드'} <= data['keywordDisplay'].keys()
    assert '현재키워드' not in data['keywordDisplay']
    assert snapshot(env.base) == before


@pytest.mark.parametrize('version,cid,has_report,expected,code', [
    ('v99', 'c1', True, 404, 'version_not_found'),
    ('v0', 'c1', True, 400, 'invalid_version'),
    ('v1', None, True, 409, 'no_collection'),
    ('v1', '../c2', True, 409, 'no_collection'),
    ('v1', 'c0', True, 409, 'no_collection'),
    ('v1', 'c1', False, 404, 'report_not_found'),
])
def test_history_errors_are_readonly(env, monkeypatch, version, cid, has_report, expected, code):
    store.update_session('S', dict(collectionId=cid))
    if not has_report:
        (env.root / 'report.json').unlink()
    before = snapshot(env.base)
    forbid_writes(monkeypatch)
    response = env.client.get('/crawl/S/report', params=dict(version=version))
    assert response.status_code == expected
    assert response.json()['error']['code'] == code
    assert snapshot(env.base) == before


def test_history_requires_explicit_version(env):
    assert env.client.get('/crawl/S/report').status_code == 422
