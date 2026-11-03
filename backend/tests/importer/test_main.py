import pytest

from app.importer import __main__ as cli
from app.importer import read, steps


def test_main_success(monkeypatch, capsys):
    monkeypatch.setattr(steps, 'run_import', lambda path, sid=None, log=print: log('ok') or {'sid': 'imp-x'})
    assert cli.main(['some.zip']) == 0
    assert 'ok' in capsys.readouterr().out


def test_main_import_error(monkeypatch, capsys):
    def fail(*a, **k):
        raise read.ImportError_('필수 컬럼이 없습니다: url')
    monkeypatch.setattr(steps, 'run_import', fail)
    assert cli.main(['x.csv']) == 1
    assert '필수 컬럼' in capsys.readouterr().err


def test_main_interrupt(monkeypatch, capsys):
    def stop(*a, **k):
        raise KeyboardInterrupt
    monkeypatch.setattr(steps, 'run_import', stop)
    assert cli.main(['x.csv', '--sid', 'imp-a']) == 130
    assert '다시 실행' in capsys.readouterr().err


def test_main_forwards_path_and_sid(monkeypatch):
    calls = []

    def run(path, *, sid=None, log=print):
        calls.append((path, sid))

    monkeypatch.setattr(steps, 'run_import', run)
    assert cli.main(['네이버 카페.zip', '--sid', 'imp-a']) == 0
    assert calls == [('네이버 카페.zip', 'imp-a')]


def test_main_requires_file():
    with pytest.raises(SystemExit) as exc:
        cli.main([])
    assert exc.value.code == 2
