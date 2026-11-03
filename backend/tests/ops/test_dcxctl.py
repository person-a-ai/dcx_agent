"""Manual commands reuse the isolated T2 harness."""
import subprocess
import pytest
from .conftest import SCRIPTS


def ctl(m, *args, **env):
    return subprocess.run([m.env['DCX_BASH'], str(SCRIPTS/'dcxctl'), *args],
                          env=dict(m.env, **env), text=True, capture_output=True, timeout=45)


def test_status_prints(macmini):
    m = macmini
    (m.root/'shared/last-failed-sha').write_text(m.b)
    m.lib('sha=test; log error')
    r = ctl(m, 'status')
    assert r.returncode == 0, r.stderr
    for text in ('current', m.a, 'release', 'last-failed-sha', m.b, 'deploy-history', 'deploy.log', 'error'):
        assert text in r.stdout


@pytest.mark.parametrize('explicit', [True, False])
def test_deploy_explicit_sha_clears_failed(macmini, explicit):
    m = macmini
    (m.root/'shared/last-failed-sha').write_text(m.b)
    r = ctl(m, 'deploy', *([m.b[:12]] if explicit else []))
    assert r.returncode == 0, r.stderr
    assert m.current == m.b
    assert not (m.root/'shared/last-failed-sha').exists()


def test_rollback(macmini):
    m = macmini
    assert m.run_deploy()[0] == 0
    (m.root/'shared/data/sessions/value').write_text('after')
    (m.root/'shared/data/work/runs.sqlite').write_text('work-after')
    (m.root/'events').write_text('')
    r = ctl(m, 'rollback')
    assert r.returncode == 0, r.stderr
    assert m.current == m.a
    assert (m.root/'shared/data/sessions/value').read_text() == 'original'
    assert (m.root/'shared/data/work/runs.sqlite').read_text() == 'work-before'
    assert (m.root/'shared/last-failed-sha').read_text().strip() == m.b
    assert m.logs[-1]['decision'] == 'rolled-back'
    assert (m.root/'events').read_text().splitlines() == ['stop', 'start']
    assert (m.root/'shared/deploy-history').read_text().splitlines() == [f'{m.a} -']
    assert ctl(m, 'rollback').returncode != 0


@pytest.mark.parametrize('missing', ['history', 'release', 'snapshot'])
def test_rollback_without_previous(macmini, missing):
    m = macmini
    if missing != 'history':
        assert m.run_deploy()[0] == 0
        import shutil
        if missing == 'release':
            shutil.rmtree(m.root/'releases'/m.a)
        else:
            shutil.rmtree(m.root/'shared/snapshots')
    before = (m.current, (m.root/'shared/deploy-history').read_text(), len(m.logs))
    r = ctl(m, 'rollback')
    assert r.returncode != 0
    assert '되돌릴 버전이 없습니다' in r.stderr
    assert before == (m.current, (m.root/'shared/deploy-history').read_text(), len(m.logs))
    assert not (m.root/'shared/last-failed-sha').exists()


def test_busy_lock_does_not_clear_failed(macmini):
    m = macmini
    import os
    lock = m.root/'shared/deploy.lock'
    lock.mkdir()
    (lock/'pid').write_text(str(os.getpid()))
    (m.root/'shared/last-failed-sha').write_text(m.b)
    assert ctl(m, 'deploy', m.b).returncode != 0
    assert (m.root/'shared/last-failed-sha').read_text() == m.b


def test_rollback_unhealthy(macmini):
    m = macmini
    assert m.run_deploy()[0] == 0
    r = ctl(m, 'rollback', DCX_FORCE_UNHEALTHY_SHA=m.a)
    assert r.returncode != 0
    assert m.logs[-1]['decision'] == 'unhealthy-both'
    assert (m.root/'shared/last-failed-sha').read_text().strip() == m.b


def test_manual_rollback_recovers_after_kill(macmini):
    m = macmini
    assert m.run_deploy()[0] == 0
    (m.root/'shared/data/sessions/value').write_text('after')
    history = (m.root/'shared/deploy-history').read_text()
    # switch_to runs after restoration and before history finalization.
    (m.bin/'mv').unlink()
    m.command('mv', '''import os,signal,sys
if sys.argv[-2].endswith('/current.tmp'):
    os.kill(os.getppid(), signal.SIGKILL)
    sys.exit(0)
os.execv('/bin/mv', ['/bin/mv']+sys.argv[1:])
''')
    r = ctl(m, 'rollback')
    assert r.returncode == -9
    assert (m.root/'shared/data/sessions/value').read_text() == 'original'
    assert (m.root/'shared/deploy-history').read_text() == history
    state = m.root/'shared/deploy-state'
    saved = state.read_text()
    assert saved.startswith(f'rolling-back {m.b} {m.a} ')
    (m.bin/'mv').unlink(); (m.bin/'mv').symlink_to('/bin/mv')
    assert m.run_deploy()[0] == 0, m.output
    assert m.current == m.a
    assert (m.root/'shared/last-failed-sha').read_text().strip() == m.b
    assert (m.root/'shared/deploy-history').read_text() == f'{m.a} -\n'
    assert m.logs[-1]['decision'] == 'rolled-back'
    assert not state.exists()
    assert not (m.root/'shared/maintenance').exists()
    backups = list((m.root/'shared/snapshots').glob('*-failed/sessions/value'))
    assert len(backups) == 1 and backups[0].read_text() == 'after'
    # Replay a crash after history rename: never remove another history row.
    state.write_text(saved)
    assert m.run_deploy()[0] == 0, m.output
    assert (m.root/'shared/deploy-history').read_text() == f'{m.a} -\n'
    assert not state.exists()


def test_status_reports_hold(macmini):
    m = macmini
    assert 'maintenance: clear' in ctl(m, 'status').stdout
    (m.root/'shared/maintenance').write_text('99999999 install\n')
    output = ctl(m, 'status').stdout
    assert 'maintenance: held' in output
    assert '99999999 install' in output


def _fake_python(m):
    backend = m.root / f'releases/{m.a}/backend'
    python = backend / '.venv/bin/python'
    python.parent.mkdir(parents=True, exist_ok=True)
    python.write_text('#!/bin/bash\nprintf "%s\\n" "$@" > "$(dirname "$0")/../../args.txt"\n')
    python.chmod(0o755)
    return backend / 'args.txt'


def test_import_labels_runs_release_importer(macmini, tmp_path):
    m = macmini
    args = _fake_python(m)
    data = tmp_path / 'data.zip'
    data.write_bytes(b'x')
    r = ctl(m, 'import-labels', str(data), '--sid', 'imp-a')
    assert r.returncode == 0, r.stderr
    text = args.read_text()
    assert str(data) in text and 'imp-a' in text and 'app.importer' in text


def test_import_labels_refused_in_maintenance(macmini, tmp_path):
    m = macmini
    args = _fake_python(m)
    (m.root / 'shared/maintenance').write_text('99999999 install\n')
    r = ctl(m, 'import-labels', str(tmp_path / 'x.zip'))
    assert r.returncode == 1 and '점검' in r.stderr
    assert not args.exists()


def test_import_labels_requires_file(macmini):
    r = ctl(macmini, 'import-labels')
    assert r.returncode == 2


def test_import_labels_requires_current_release(macmini):
    args = _fake_python(macmini)
    (macmini.root / 'current').unlink()
    r = ctl(macmini, 'import-labels', 'x.csv')
    assert r.returncode == 1 and 'current 릴리스가 없습니다' in r.stderr
    assert not args.exists()


@pytest.mark.parametrize('exit_code', [0, 1, 130])
def test_import_labels_loads_env_and_preserves_arguments(macmini, tmp_path, monkeypatch, exit_code):
    import json
    import shlex
    import sys

    m = macmini
    backend = m.root / f'releases/{m.a}/backend'
    python = backend / '.venv/bin/python'
    python.parent.mkdir(parents=True)
    # Preserve the test interpreter's virtualenv and installed python-dotenv.
    python.write_text(f'#!/bin/bash\nexec {shlex.quote(sys.executable)} "$@"\n')
    python.chmod(0o755)
    package = backend / 'app/importer'
    package.mkdir(parents=True)
    (backend / 'app/__init__.py').touch()
    (package / '__init__.py').touch()
    (package / '__main__.py').write_text('''import json, os, pathlib, sys
pathlib.Path('probe.json').write_text(json.dumps({
    'cwd': os.getcwd(), 'args': sys.argv[1:],
    'app': os.environ['IMPORT_APP'], 'value': os.environ['IMPORT_VALUE'],
    'literal': os.environ['IMPORT_LITERAL'], 'empty': os.environ['IMPORT_EMPTY'],
    'bare': os.environ['IMPORT_BARE'],
}))
sys.exit(int(os.environ['IMPORT_EXIT']))
''')
    (m.root / 'shared/app.env').write_text(
        'IMPORT_APP=app-value\nIMPORT_VALUE=app\nIMPORT_EMPTY=\nIMPORT_BARE\n'
    )
    (m.root / 'shared/runtime.env').write_text(
        'IMPORT_VALUE=runtime\nIMPORT_LITERAL="${IMPORT_APP} $(touch unexpected)"\n'
        f'IMPORT_EXIT={exit_code}\n'
    )
    data = tmp_path / '네이버 카페.zip'
    data.write_bytes(b'x')
    monkeypatch.chdir(tmp_path)
    r = ctl(m, 'import-labels', data.name, '--sid', 'imp-a',
            IMPORT_VALUE='inherited', IMPORT_BARE='inherited')
    assert r.returncode == exit_code, r.stderr
    assert json.loads((backend / 'probe.json').read_text()) == {
        'cwd': str(backend), 'args': [str(data), '--sid', 'imp-a'],
        'app': 'app-value', 'value': 'runtime',
        'literal': '${IMPORT_APP} $(touch unexpected)', 'empty': '', 'bare': 'inherited',
    }
    assert not (tmp_path / 'unexpected').exists()
    assert not (backend / 'unexpected').exists()
