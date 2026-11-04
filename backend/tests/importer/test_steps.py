import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.config import settings
from app.context import store, versions
from app.crawl.control import phase_state
from app.importer import read, steps
from app.prep import pipeline
from app.work import runner
from tests.importer.conftest import row, write_csv


@pytest.fixture
def env(data_dir, salt, monkeypatch, tmp_path):
    """runner.start only records the launch (start_prep holds the session lock);
    the injected sleep runs the prepared worker outside that lock, like a detached child."""
    monkeypatch.setattr(settings, 'embed_backend', 'fake')
    runs, pending = {}, []

    class Ctx:
        def __init__(self, sid, version, args):
            self.sid, self.version, self.args, self.run_id = sid, version, args, 'prep-1'
        def heartbeat(self, *a): pass
        def should_stop(self): return False
        def should_pause(self): return False

    def start(sid, version, kind, args):
        assert kind == 'prep'
        pending.append((sid, version, args))
        runs[sid] = {'runId': 'prep-1', 'kind': 'prep', 'state': 'running', 'progress': 0, 'detail': {}, 'error': None}
        return dict(runs[sid])

    def sleep(_seconds):
        while pending:
            sid, version, args = pending.pop()
            pipeline.run_prep(Ctx(sid, version, args), sid, version)
            runs[sid].update(state='done', progress=1)

    monkeypatch.setattr(runner, 'start', start)
    monkeypatch.setattr(runner, 'status', lambda sid: [dict(runs[sid])] if sid in runs else [])
    rows = [row(i) for i in range(6)] + [row(6, status='skipped', evidence_level=''), row(7, site='티스토리')]
    rows[1].update(anchor='0', sense='0', feel='0', think='0', act='0', relate='0', outcome='0', situation='0',
                   evidence_level='non', reason_code='ad', signal='')
    return SimpleNamespace(path=write_csv(tmp_path / 'r.csv', rows), logs=[], runs=runs, sleep=sleep)


def run(env, **kw):
    return steps.run_import(env.path, log=env.logs.append, poll_s=0, sleep=env.sleep, **kw)


def test_full_import_reaches_stage6(env, data_dir):
    summary = run(env)
    sid = summary['sid']
    assert sid == 'imp-' + read.open_source(env.path).sha256[:12]
    data = store.load_session(sid)
    ctx = data['projectContext']
    assert (ctx['bk'], ctx['oneLiner'], ctx['researchQuestion']['text'], ctx['taskMode']) == ('.', '.', '.', 'explore')
    assert [k['kw'] for k in data['keywords']] == ['건강 키워드0', '건강 키워드1']
    assert phase_state(sid, 'c1') == 'done'
    assert data['prep']['status'] == 'done'
    assert data['labeling'] == {**data['labeling'], 'started': True, 'status': 'done', 'labelerMode': 'imported'}
    assert data['step'] == 'cluster-start'
    assert summary['counts']['labeled'] == 6 and summary['counts']['unlabeled'] == 0
    from app.known.filter import read_export
    relevant = read_export(sid, data)
    assert len(relevant) == 5 and all(r['source'] == 'imported' for r in relevant)
    from app.routers.sessions import _completion
    done = _completion(sid, data)
    assert done['crawlDone'] and done['prepDone'] and done['labelingDone'] and done['exportDone']
    assert any('0단계' in line for line in env.logs)


def test_rerun_is_noop(env):
    first = run(env)
    before = store.load_session(first['sid'])
    second = run(env)
    after = store.load_session(first['sid'])
    assert second['sid'] == first['sid']
    assert after['training']['exportRef'] == before['training']['exportRef']


@pytest.mark.parametrize('partial', [False, True])
def test_interrupted_labels_completion_is_reinserted(env, monkeypatch, partial):
    from app.model import export

    real_iter = steps.iter_records
    def records(source, crawled_at):
        for i, record in enumerate(real_iter(source, crawled_at)):
            if partial and crawled_at == '' and i == 0:
                continue
            yield record
    monkeypatch.setattr(steps, 'iter_records', records)
    insert = Mock(wraps=steps.insert_labels)
    write_export = Mock(wraps=export.write)
    monkeypatch.setattr(steps, 'insert_labels', insert)
    monkeypatch.setattr(export, 'write', write_export)
    real_write = store.write_json
    interrupted = False
    def write(path, data):
        nonlocal interrupted
        if (path.name == 'session.json' and 'labels' in data.get('imported', {}).get('steps', {})
                and not interrupted):
            interrupted = True
            raise KeyboardInterrupt
        return real_write(path, data)
    monkeypatch.setattr(store, 'write_json', write)

    with pytest.raises(KeyboardInterrupt):
        run(env)
    sid = steps.default_sid(read.open_source(env.path))
    pending = store.load_session(sid)
    assert pending['labeling']['status'] == 'running'
    assert 'labels' not in pending['imported']['steps']
    assert pending['imported']['counts'] == {}

    summary = run(env)
    data = store.load_session(sid)
    assert insert.call_count == 2
    assert summary['counts'] == dict(labeled=5 if partial else 6, unlabeled=int(partial), droppedByPrep=0)
    assert data['version'] == pending['version'] == 'v1'
    assert data['step'] == 'cluster-start'
    assert data['labeling']['status'] == 'done'
    assert 'labels' in data['imported']['steps']
    assert write_export.call_args.kwargs['partial'] is partial
    assert data['training']['exportPartial'] is partial


@pytest.mark.parametrize('missing', ['labeled', 'unlabeled', 'droppedByPrep'])
def test_labels_done_without_complete_counts_is_reinserted(env, monkeypatch, missing):
    with monkeypatch.context() as patch:
        patch.setattr(steps, 'export_step', Mock(side_effect=KeyboardInterrupt))
        with pytest.raises(KeyboardInterrupt):
            run(env)
    sid = steps.default_sid(read.open_source(env.path))
    with store.locked(sid):
        data = store.load_session(sid)
        del data['imported']['counts'][missing]
        store.write_json(store.session_dir(sid) / 'session.json', data)
    insert = Mock(wraps=steps.insert_labels)
    monkeypatch.setattr(steps, 'insert_labels', insert)

    summary = run(env)
    assert insert.call_count == 1
    assert summary['counts'] == dict(labeled=6, unlabeled=0, droppedByPrep=0)
    assert store.load_session(sid)['step'] == 'cluster-start'


@pytest.mark.parametrize('when', ['after_export', 'completion_write'])
def test_interrupted_export_completion_is_redone(env, monkeypatch, when):
    from app.model import export

    real_export = export.write
    calls = []
    def write_export(*args, **kwargs):
        result = real_export(*args, **kwargs)
        calls.append(result['exportRef'])
        if when == 'after_export' and len(calls) == 1:
            raise KeyboardInterrupt
        return result
    monkeypatch.setattr(export, 'write', write_export)
    real_write = store.write_json
    interrupted = False
    def write(path, data):
        nonlocal interrupted
        if (when == 'completion_write' and path.name == 'session.json'
                and 'export' in data.get('imported', {}).get('steps', {}) and not interrupted):
            interrupted = True
            raise KeyboardInterrupt
        return real_write(path, data)
    monkeypatch.setattr(store, 'write_json', write)

    with pytest.raises(KeyboardInterrupt):
        run(env)
    sid = steps.default_sid(read.open_source(env.path))
    pending = store.load_session(sid)
    assert pending['training']['exportRef'] == calls[0]
    assert pending['training'].get('status') != 'done'
    assert pending['step'] == 'train-start'
    assert 'export' not in pending['imported']['steps']

    summary = run(env)
    data = store.load_session(sid)
    assert len(calls) == 2
    assert summary['exportRef'] == calls[1] != calls[0]
    assert data['version'] == pending['version'] == 'v1'
    assert data['step'] == 'cluster-start'
    assert data['training']['status'] == 'done'
    assert 'export' in data['imported']['steps']


@pytest.mark.parametrize('restart_from, repeated', [
    ('stage3', ['prep', 'labels', 'export']),
    ('stage4', ['labels', 'export']),
    ('stage5', ['export']),
])
def test_completed_import_resumes_active_version(env, monkeypatch, restart_from, repeated):
    from app.label.overview import labels_for

    first = run(env)
    sid = first['sid']
    assert versions.create_version(sid, 'v1', restart_from, 'test') == 'v2'
    restarted = store.load_session(sid)
    assert set(restarted['imported']['steps']) == set(steps.ORDER)
    if restart_from != 'stage5':
        assert restarted['labeling']['started'] is False
        assert restarted['labeling']['mode'] == 'imported'
        assert 'labelerMode' not in restarted['labeling']
        with labels_for(sid, restarted)._db() as db:
            assert db.execute('SELECT count(*) FROM final').fetchone()[0] == 0
    calls = {}
    for step, name in steps.STEP_FUNCTIONS.items():
        calls[step] = Mock(wraps=getattr(steps, name))
        monkeypatch.setattr(steps, name, calls[step])

    summary = run(env)
    assert [step for step, call in calls.items() if call.called] == repeated
    data = store.load_session(sid)
    assert data['version'] == 'v2'
    assert data['prep']['status'] == 'done'
    assert data['labeling']['status'] == 'done'
    assert data['labeling']['labelerMode'] == 'imported'
    assert data['training']['exportRef'] == summary['exportRef']
    assert summary['exportRef'] and summary['exportRef'] != first['exportRef']
    assert data['training']['status'] != 'stale'
    assert 'stage5' not in data.get('stale', {})
    assert data['step'] == 'cluster-start'
    with labels_for(sid, data)._db() as db:
        assert db.execute('SELECT count(*) FROM final').fetchone()[0] == 6
        assert {r[0] for r in db.execute('SELECT source FROM final')} == {'imported'}

    for call in calls.values():
        call.reset_mock()
    assert run(env)['exportRef'] == summary['exportRef']
    for call in calls.values():
        call.assert_not_called()


def test_export_interrupted_by_stage4_restart_resumes(env, monkeypatch):
    from app.label.overview import labels_for
    from app.model import export

    real_write = export.write
    def write(sid, *args, **kwargs):
        result = real_write(sid, *args, **kwargs)
        assert versions.create_version(sid, 'v1', 'stage4', 'test') == 'v2'
        return result
    with monkeypatch.context() as patch:
        patch.setattr(export, 'write', write)
        with pytest.raises(read.ImportError_, match='가져오는 동안 프로젝트 버전이 바뀌었습니다'):
            run(env)

    sid = steps.default_sid(read.open_source(env.path))
    restarted = store.load_session(sid)
    assert 'labels' in restarted['imported']['steps']
    assert 'export' not in restarted['imported']['steps']
    with labels_for(sid, restarted)._db() as db:
        assert db.execute('SELECT count(*) FROM final').fetchone()[0] == 0

    summary = run(env)
    data = store.load_session(sid)
    assert data['version'] == 'v2'
    assert data['labeling']['status'] == 'done'
    assert data['labeling']['labelerMode'] == 'imported'
    assert data['training']['exportRef'] == summary['exportRef']
    assert summary['exportRef'] and data['step'] == 'cluster-start'
    with labels_for(sid, data)._db() as db:
        assert db.execute('SELECT count(*) FROM final').fetchone()[0] == 6
        assert {r[0] for r in db.execute('SELECT source FROM final')} == {'imported'}


@pytest.mark.parametrize('blocked', ['register_collection', 'run_prep_step', 'insert_labels', 'export_step'])
def test_resume_after_interruption(env, monkeypatch, blocked):
    original = getattr(steps, blocked)
    def boom(*a, **k):
        raise KeyboardInterrupt
    monkeypatch.setattr(steps, blocked, boom)
    with pytest.raises(KeyboardInterrupt):
        run(env)
    monkeypatch.setattr(steps, blocked, original)
    summary = run(env)
    data = store.load_session(summary['sid'])
    assert data['step'] == 'cluster-start' and data['training']['exportRef']


def test_partial_collection_is_rebuilt(env, data_dir, monkeypatch):
    from app.crawl import writer
    real_close = writer.DocWriter.close
    def crash(self):
        real_close(self)
        raise KeyboardInterrupt
    monkeypatch.setattr(writer.DocWriter, 'close', crash)
    with pytest.raises(KeyboardInterrupt):
        run(env)
    sid = 'imp-' + read.open_source(env.path).sha256[:12]
    assert (data_dir / 'crawl' / sid / 'collections/c1.partial').exists()
    assert not (data_dir / 'crawl' / sid / 'collections/c1').exists()
    monkeypatch.setattr(writer.DocWriter, 'close', real_close)
    run(env)
    assert phase_state(sid, 'c1') == 'done'
    assert not (data_dir / 'crawl' / sid / 'collections/c1.partial').exists()


def test_short_body_dropped_by_prep_is_reported(env, tmp_path):
    rows = [row(i) for i in range(3)] + [row(9, contents='짧음')]
    env.path = write_csv(tmp_path / 'short.csv', rows)
    summary = run(env)
    assert summary['counts']['droppedByPrep'] == 1 and summary['counts']['labeled'] == 3
    from app.label.overview import labels_for
    data = store.load_session(summary['sid'])
    with labels_for(summary['sid'], data)._db() as db:
        assert db.execute('SELECT 1 FROM final WHERE doc_id=?', (row(9)['doc_id'],)).fetchone() is None
    assert any('전처리에서 빠짐 1' in line for line in env.logs)


def test_unlabeled_prepared_docs_use_partial_export(env, monkeypatch):
    from app.model import export
    calls = []
    real = export.write
    monkeypatch.setattr(export, 'write', lambda *a, **k: calls.append(k) or real(*a, **k))
    real_iter = steps.iter_records
    def drop_first_label(source, crawled_at):
        for i, record in enumerate(real_iter(source, crawled_at)):
            if crawled_at == '' and i == 0:
                continue  # insert_labels reads with crawled_at='': skip one label only there
            yield record
    monkeypatch.setattr(steps, 'iter_records', drop_first_label)
    summary = run(env)
    assert summary['counts']['unlabeled'] == 1
    assert summary['counts']['droppedByPrep'] == 0
    assert calls[-1]['partial'] is True
    assert store.load_session(summary['sid'])['training']['exportPartial'] is True


def test_concurrent_import_refused(env, data_dir):
    import fcntl
    sid = 'imp-' + read.open_source(env.path).sha256[:12]
    lock = data_dir / 'imports' / f'{sid}.lock'
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open('a') as held:
        fcntl.flock(held, fcntl.LOCK_EX)
        with pytest.raises(read.ImportError_, match='이미 실행 중'):
            run(env)
    assert not (data_dir / 'sessions' / sid).exists()


def test_same_sid_different_file_rejected(env, tmp_path):
    run(env, sid='imp-fixed')
    other = write_csv(tmp_path / 'other.csv', [row(20)])
    with pytest.raises(read.ImportError_, match='다른 파일'):
        steps.run_import(other, sid='imp-fixed', log=lambda s: None, poll_s=0, sleep=lambda s: None)


def test_invalid_file_creates_nothing(env, tmp_path, data_dir):
    bad = write_csv(tmp_path / 'bad.csv', [row(1, questions_version='q9')])
    with pytest.raises(read.ImportError_):
        steps.run_import(bad, log=lambda s: None, poll_s=0, sleep=lambda s: None)
    assert not (data_dir / 'sessions').exists() or not any((data_dir / 'sessions').iterdir())


def test_prep_failure_reported(env, monkeypatch):
    monkeypatch.setattr(runner, 'start', lambda *a: {'runId': 'x', 'kind': 'prep', 'state': 'failed',
                                                     'progress': 0, 'detail': {}, 'error': 'Boom'})
    monkeypatch.setattr(runner, 'status', lambda sid: [{'runId': 'x', 'kind': 'prep', 'state': 'failed',
                                                       'progress': 0, 'detail': {}, 'error': 'Boom'}])
    with pytest.raises(read.ImportError_, match='전처리'):
        run(env)


def test_public_stage_api():
    names = ('default_sid', 'run_import', *steps.STEP_FUNCTIONS.values()) if hasattr(steps, 'STEP_FUNCTIONS') else ('run_import',)
    assert all(callable(getattr(steps, name, None)) for name in names)


@pytest.mark.parametrize('mode', ['cross', 'gpt_only', None])
def test_existing_labeling_is_not_overwritten(env, monkeypatch, mode):
    original = steps.insert_labels
    def started(sid, source):
        store.update_session(sid, {'labeling': {'started': True, 'labelerMode': mode}})
        return original(sid, source)
    monkeypatch.setattr(steps, 'insert_labels', started)
    with pytest.raises(read.ImportError_, match='이미 라벨링을 시작한 프로젝트입니다'):
        run(env)
    sid = steps.default_sid(read.open_source(env.path))
    assert store.load_session(sid)['labeling']['labelerMode'] == mode
    from app.label.overview import labels_for
    labels = labels_for(sid, store.load_session(sid))
    with labels._db() as db:
        assert db.execute('SELECT count(*) FROM final').fetchone()[0] == 0


def test_public_stages_work_independently(env):
    source = read.open_source(env.path)
    sid = steps.default_sid(source)
    steps.create_session(sid, source, read.scan(source))
    steps.register_collection(sid, source)
    steps.run_prep_step(sid, env.logs.append, 0, env.sleep)
    counts = steps.insert_labels(sid, source)
    exported = steps.export_step(sid, partial=counts['unlabeled'] > 0)
    assert counts == dict(labeled=6, unlabeled=0, droppedByPrep=0)
    assert exported['relevant'] == 5
    assert store.load_session(sid)['step'] == 'cluster-start'


def test_label_batches_resume_without_duplicates(env, monkeypatch):
    monkeypatch.setattr(steps, '_BATCH', 2)
    real_iter = steps.iter_records
    def interrupted(source, crawled_at):
        for i, record in enumerate(real_iter(source, crawled_at)):
            if crawled_at == '' and i == 2:
                raise KeyboardInterrupt
            yield record
    monkeypatch.setattr(steps, 'iter_records', interrupted)
    with pytest.raises(KeyboardInterrupt):
        run(env)
    monkeypatch.setattr(steps, 'iter_records', real_iter)
    summary = run(env)
    from app.label.overview import labels_for
    data = store.load_session(summary['sid'])
    with labels_for(summary['sid'], data)._db() as db:
        assert db.execute('SELECT count(*) FROM final').fetchone()[0] == 6
    assert summary['counts']['labeled'] == 6


@pytest.mark.parametrize('after_rows', [2, 6])
def test_version_change_during_label_insertion_stops_writes(env, monkeypatch, after_rows):
    from app.context import versions
    from app.label.overview import labels_for

    sid = steps.default_sid(read.open_source(env.path))
    monkeypatch.setattr(steps, '_BATCH', 2)
    real_iter = steps.iter_records
    switched = False
    def records(source, crawled_at):
        nonlocal switched
        for i, record in enumerate(real_iter(source, crawled_at), 1):
            yield record
            if crawled_at == '' and i == after_rows and not switched:
                switched = True
                assert versions.create_version(sid, 'v1', 'stage4', 'test') == 'v2'
    monkeypatch.setattr(steps, 'iter_records', records)

    with pytest.raises(read.ImportError_, match='가져오는 동안 프로젝트 버전이 바뀌었습니다. 같은 명령을 다시 실행하세요.'):
        run(env)
    old = versions._data(sid, 'v1')
    with labels_for(sid, old)._db() as db:
        assert db.execute('SELECT count(*) FROM final').fetchone()[0] == after_rows
    assert old['labeling']['status'] == 'running'
    assert 'labels' not in old['imported']['steps']
    assert 'labels' not in store.load_session(sid)['imported']['steps']

    summary = run(env)
    data = store.load_session(sid)
    assert data['version'] == 'v2' and data['labeling']['status'] == 'done'
    assert data['training']['exportRef'] == summary['exportRef']
    assert summary['counts']['labeled'] == 6
    with labels_for(sid, data)._db() as db:
        assert db.execute('SELECT count(*) FROM final').fetchone()[0] == 6
    with labels_for(sid, old)._db() as db:
        assert db.execute('SELECT count(*) FROM final').fetchone()[0] == after_rows


@pytest.mark.parametrize('step', ['labels', 'export'])
def test_version_change_before_checkpoint_does_not_mark_new_version(env, monkeypatch, step):
    from app.context import versions

    real_mark = steps._mark
    switched = False
    def mark(sid, name, **kwargs):
        nonlocal switched
        if name == step and not switched:
            switched = True
            versions.create_version(sid, 'v1', 'stage4' if step == 'labels' else 'stage5', 'test')
        return real_mark(sid, name, **kwargs)
    monkeypatch.setattr(steps, '_mark', mark)

    with pytest.raises(read.ImportError_, match='가져오는 동안 프로젝트 버전이 바뀌었습니다'):
        run(env)
    sid = steps.default_sid(read.open_source(env.path))
    assert step not in versions._data(sid, 'v1')['imported']['steps']
    assert step not in store.load_session(sid)['imported']['steps']
    summary = run(env)
    data = store.load_session(sid)
    assert data['version'] == 'v2' and data['labeling']['status'] == 'done'
    assert data['training']['exportRef'] == summary['exportRef']
    assert step in data['imported']['steps']


def test_version_change_before_export_close_does_not_update_new_version(env, monkeypatch):
    from app.context import versions
    from app.model import export

    real_write = export.write
    switched = False
    def write(sid, *args, **kwargs):
        nonlocal switched
        result = real_write(sid, *args, **kwargs)
        if not switched:
            switched = True
            versions.create_version(sid, 'v1', 'stage5', 'test')
        return result
    monkeypatch.setattr(export, 'write', write)

    with pytest.raises(read.ImportError_, match='가져오는 동안 프로젝트 버전이 바뀌었습니다'):
        run(env)
    sid = steps.default_sid(read.open_source(env.path))
    assert store.load_session(sid)['step'] == 'train-start'
    assert 'export' not in store.load_session(sid)['imported']['steps']
    assert run(env)['exportRef']


def test_invalid_sid_is_import_error_without_writes(env, data_dir):
    with pytest.raises(read.ImportError_, match='Invalid session id'):
        run(env, sid='../outside')
    assert not (data_dir / 'imports').exists()
    assert not (data_dir / 'sessions').exists()


@pytest.fixture
def prepared_import(env):
    source = read.open_source(env.path)
    sid = steps.default_sid(source)
    steps.create_session(sid, source, read.scan(source))
    steps.register_collection(sid, source)
    steps.run_prep_step(sid, env.logs.append, 0, env.sleep)
    return sid, source


def test_import_claim_blocks_api_start_during_and_after_insert(prepared_import, client, monkeypatch):
    from app.label.overview import labels_for

    sid, source = prepared_import
    labels = labels_for(sid, store.load_session(sid))
    launches, checkpoints = [], []
    def start(sid, version, kind, args):
        launches.append(kind)
        return {'runId': args['labeler'], 'state': 'running'}
    monkeypatch.setattr(runner, 'start', start)
    monkeypatch.setattr(steps, '_BATCH', 2)
    real_iter = steps.iter_records
    def records(source, crawled_at):
        for i, record in enumerate(real_iter(source, crawled_at)):
            if i in (0, 2):
                assert client.post(f'/label/{sid}/start').status_code == 409
                assert store.load_session(sid)['labeling'] == {
                    'started': True, 'mode': 'imported', 'labelerMode': 'imported', 'status': 'running'}
                with labels._db() as db:
                    assert db.execute('SELECT count(*) FROM final').fetchone()[0] == i
                    assert not db.execute("SELECT 1 FROM final WHERE source != 'imported'").fetchone()
                checkpoints.append(i)
            yield record
    monkeypatch.setattr(steps, 'iter_records', records)

    assert steps.insert_labels(sid, source)['labeled'] == 6
    assert checkpoints == [0, 2]
    assert client.post(f'/label/{sid}/start').status_code == 409
    assert launches == []
    data = store.load_session(sid)
    assert data['labeling']['status'] == 'done' and data['step'] == 'train-start'
    with labels._db() as db:
        assert db.execute('SELECT count(*) FROM final').fetchone()[0] == 6
        assert {r[0] for r in db.execute('SELECT source FROM final')} == {'imported'}


@pytest.mark.parametrize('when', ['before_insert', 'before_claim_lock'])
def test_api_started_after_prep_refuses_import(prepared_import, client, monkeypatch, when):
    from contextlib import contextmanager
    from app.label.overview import labels_for

    sid, source = prepared_import
    monkeypatch.setattr(runner, 'start', lambda s, v, kind, args: {
        'runId': args['labeler'], 'state': 'running'})
    def api_start():
        assert client.post(f'/label/{sid}/start').status_code == 200
        labeling = store.load_session(sid)['labeling']
        assert labeling['started'] and labeling['labelerMode'] != 'imported'

    if when == 'before_insert':
        api_start()
    else:
        real_locked = store.locked
        pending = True
        @contextmanager
        def locked(session_id):
            nonlocal pending
            if session_id == sid and pending:
                pending = False
                # The API wins the lock immediately before the importer acquires it.
                api_start()
            with real_locked(session_id) as root:
                yield root
        monkeypatch.setattr(store, 'locked', locked)

    with pytest.raises(read.ImportError_, match='이미 라벨링을 시작한 프로젝트입니다'):
        steps.insert_labels(sid, source)
    with labels_for(sid, store.load_session(sid))._db() as db:
        assert db.execute('SELECT count(*) FROM final').fetchone()[0] == 0
    assert store.load_session(sid)['labeling']['labelerMode'] != 'imported'


def test_full_import_streams_prepared_ids(env, monkeypatch):
    from app.model import infer

    original = steps.insert_labels
    def forbidden(*args, **kwargs):
        pytest.fail('insert_labels must not load prepared document bodies with infer.documents')
    def insert(sid, source):
        # Stage-five export still uses infer.documents and is outside this fix.
        with monkeypatch.context() as patch:
            patch.setattr(infer, 'documents', forbidden)
            return original(sid, source)
    monkeypatch.setattr(steps, 'insert_labels', insert)

    summary = run(env)
    assert summary['counts'] == dict(labeled=6, unlabeled=0, droppedByPrep=0)
    assert summary['exportRef']
    assert store.load_session(summary['sid'])['step'] == 'cluster-start'


@pytest.mark.parametrize('invalid', ['missing', 'duplicate'])
def test_invalid_prepared_docs_write_no_labels(prepared_import, invalid):
    from app.label.overview import labels_for
    from app.model import infer

    sid, source = prepared_import
    data = store.load_session(sid)
    root = infer.prepared_root(sid, data) / 'docs'
    if invalid == 'missing':
        root.rename(root.with_name('docs-missing'))
        error, message = store.StoreError, '전처리 문서를 찾을 수 없습니다.'
    else:
        first = next(p for p in sorted(root.glob('*.jsonl')))
        with first.open(encoding='utf-8') as stream:
            doc = next(json.loads(line) for line in stream if line.strip())
        (root / 'duplicate.jsonl').write_text('\n' + json.dumps(doc) + '\n', encoding='utf-8')
        error, message = ValueError, 'Duplicate prepared document ID'
    with pytest.raises(error, match=message):
        steps.insert_labels(sid, source)
    with labels_for(sid, data)._db() as db:
        assert db.execute('SELECT count(*) FROM final').fetchone()[0] == 0
