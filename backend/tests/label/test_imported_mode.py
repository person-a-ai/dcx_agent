import json
import sqlite3

import pytest

from app.config import settings
from app.context import store
from app.context.stale import _judges_complete
from app.label import audit, route, rule
from app.label.overview import labels_for, overview
from app.label.questions import QVER
from app.label.votes import VoteCache
from app.work.status import database_path, transaction


def _imported_session(sid='imp-test'):
    store.update_session(sid, {'schemaVersion': 2})
    data = store.load_session(sid)
    data['labeling'] = {'started': True, 'status': 'done', 'mode': 'imported', 'labelerMode': 'imported'}
    data['prep'] = {'status': 'done', 'derivedRef': None}
    store.write_json(store.session_dir(sid) / 'session.json', data)
    labels = labels_for(sid, store.load_session(sid))
    route.schema(labels)
    tags = dict(anchor=True, situation=True, sem={k: 1 for k in rule.SEM}, reason_code=None, signal='pain')
    with labels._db() as db:
        for i in range(3):
            db.execute('INSERT INTO final VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
                       (f'nc_{i:016x}', 'core', None, 'imported', 'accepted', json.dumps(tags), None, 'pain',
                        'r0' if i == 0 else rule.RULE_VERSION, QVER, '{}', '[]', 0))
    return sid, labels


@pytest.mark.parametrize('with_caches', [False, True])
def test_rebuild_and_sync_keep_imported_rows(data_dir, tmp_path, monkeypatch, with_caches):
    _, labels = _imported_session()
    monkeypatch.setattr(settings, 'audit_first', 1)
    monkeypatch.setattr(settings, 'audit_size', 1)
    jev = VoteCache(tmp_path / 'jev') if with_caches else None
    gpt = VoteCache(tmp_path / 'gpt') if with_caches else None
    route.rebuild_queue(labels, jev, gpt, mode='imported')
    route.sync(labels, jev, gpt, mode='imported')
    with labels._db() as db:
        assert db.execute("SELECT count(*) FROM final WHERE source='imported'").fetchone()[0] == 3
        assert db.execute('SELECT count(*) FROM audit_set').fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM queue WHERE status='open'").fetchone()[0] == 0


def test_version_change_does_not_delete_imported_rows(data_dir, tmp_path):
    _, labels = _imported_session()
    gpt = VoteCache(tmp_path / 'gpt')
    route.rebuild_final(labels, None, gpt, mode='gpt_only')
    with labels._db() as db:
        assert db.execute("SELECT count(*) FROM final WHERE source='imported'").fetchone()[0] == 3
        db.execute("UPDATE route_sync SET identity='old:r0:q0' WHERE name='gpt'")
    route.rebuild_final(labels, None, gpt, mode='gpt_only')
    with labels._db() as db:
        assert db.execute("SELECT count(*) FROM final WHERE source='imported'").fetchone()[0] == 3


def test_imported_label_can_be_read(data_dir):
    _, labels = _imported_session()
    label = labels.get('nc_0000000000000000')
    assert label.source == 'imported'
    assert label.confidence is None


def test_judges_complete_without_runs():
    with sqlite3.connect(':memory:') as db:
        db.execute('CREATE TABLE runs (labeler TEXT, state TEXT, version TEXT, kind TEXT, started_at REAL)')
        assert _judges_complete(db, 'v1', mode='imported') is False
        assert _judges_complete(db, 'v1', mode='gpt_only') is False


@pytest.mark.parametrize('status', ['running', 'done'])
def test_session_read_preserves_imported_status_with_runs_database(client, data_dir, status):
    sid, _ = _imported_session()
    store.update_session(sid, {'labeling': {'status': status}})
    with transaction(sid):
        pass
    assert database_path(sid).exists()

    response = client.get(f'/session/{sid}')

    assert response.status_code == 200, response.text
    assert response.json()['data']['labeling']['status'] == status
    assert store.load_session(sid)['labeling']['status'] == status


def test_label_api_refuses_imported_audit(client, data_dir, monkeypatch):
    sid, labels = _imported_session()
    monkeypatch.setattr(settings, 'audit_size', 3)

    response = client.post(f'/label/{sid}/audit')

    assert response.status_code == 409, response.text
    assert '가져온 라벨' in response.text
    with labels._db() as db:
        assert db.execute('SELECT count(*) FROM audit_set').fetchone()[0] == 0


@pytest.mark.parametrize('mode', ['audit', 'reissue'])
def test_label_api_refuses_imported_review_submission(client, data_dir, monkeypatch, mode):
    sid, labels = _imported_session()
    monkeypatch.setattr(settings, 'audit_size', 3)
    # Reproduce a round created before imported sessions were guarded.
    round_id = audit.maybe_new_round(labels, 3, kind='manual')
    doc_id = 'nc_0000000000000000'
    with labels._db() as db:
        if mode == 'reissue':
            db.execute('INSERT INTO audit_reissue VALUES (?,?)', (round_id, doc_id))
        before = tuple(db.execute('SELECT * FROM final WHERE doc_id=?', (doc_id,)).fetchone())
    tags = dict(anchor=False, situation=True, sem={k: 1 for k in rule.SEM},
                reason_code=None, signal='pain')

    response = client.post(f'/label/{sid}/submit', json=dict(
        doc_id=doc_id, labeler='alice', mode=mode, round=round_id, tags=tags))

    assert response.status_code == 409, response.text
    assert '가져온 라벨' in response.text
    with labels._db() as db:
        after = db.execute('SELECT * FROM final WHERE doc_id=?', (doc_id,)).fetchone()
        assert after['source'] == 'imported'
        assert tuple(after) == before
        assert db.execute('SELECT count(*) FROM human').fetchone()[0] == 0


@pytest.mark.parametrize('derived_ref', [None, {'collectionId': 'c1', 'prepKey': 'p_0123456789ab'}])
def test_overview_reports_imported_totals(data_dir, derived_ref):
    sid, _ = _imported_session()
    store.update_session(sid, {'prep': {'derivedRef': derived_ref}})
    view = overview(sid, sync=True)
    assert view['labelerAccuracy']['jev'] is None and view['labelerAccuracy']['gpt'] is None
    assert view['levelDistribution']['core'] == 3


@pytest.mark.parametrize(('path', 'body'), [
    ('start', None),
    ('judge', None),
    ('mode', {'mode': 'llm'}),
    *[(f'judge/{labeler}/{action}', None)
      for labeler in ('jev', 'gpt', 'infer') for action in ('pause', 'resume', 'stop')],
])
def test_label_api_refuses_judging(client, data_dir, path, body):
    sid, _ = _imported_session()
    response = client.post(f'/label/{sid}/{path}', json=body)
    assert response.status_code == 409, (path, response.text)
    assert '가져온 라벨입니다. 새 버전에서 다시 하세요.' in response.text
