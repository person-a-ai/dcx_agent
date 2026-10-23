import os
from pathlib import Path
import pytest
from app.config import settings
from app.llm.codex_exec import run_many

@pytest.fixture(autouse=True)
def fake(monkeypatch, data_dir):
    monkeypatch.setattr(settings, "codex_bin", str(Path(__file__).resolve().parents[1] / "fakes/fake_codex.py"))
    monkeypatch.setattr(settings, "codex_timeout_s", 1)

def test_rerun_skips_answered_and_live(task, data_dir):
    root = data_dir / "llm_runs/reuse"
    (root / "answers").mkdir(parents=True)
    (root / "locks").mkdir()
    (root / "answers/task-0.json").write_text('{"value":7}')
    (root / "locks/task-1.pid").write_text(str(os.getpid()))
    results = run_many([task, task, task], "reuse", 2)
    assert results[0].data.value == 7
    assert results[1].error.kind == "interrupted"
    assert results[2].data.value == 1
    assert len((root / "invocations").read_text().splitlines()) == 1
    assert (root / "manifest.json").exists()
    assert task.attachments[0].body in (root / "prompts/task-2.txt").read_text()
    run_many([task, task, task], "reuse", 2)
    assert len((root / "invocations").read_text().splitlines()) == 1

def test_bad_answer_quarantined(task, data_dir):
    result = run_many([task.model_copy(update={"instructions":"BAD_MODE"})], "bad", 1)[0]
    assert result.error.kind == "schema"
    root = data_dir / "llm_runs/bad/answers/bad"
    assert (root / "task-0.json").exists()
    assert (root / "task-0.reason.txt").exists()

def test_timeout_kills_process(task, data_dir):
    result = run_many([task.model_copy(update={"instructions":"SLEEP_MODE"})], "sleep", 1)[0]
    assert result.error.kind == "timeout"
    root = data_dir / "llm_runs/sleep"
    for pid in [int((root / "child.pid").read_text()), int((root / "invocations").read_text())]:
        with pytest.raises(ProcessLookupError):
            os.kill(pid, 0)
    assert not (root / "locks/task-0.pid").exists()

def test_stale_lock_and_append_log(task, data_dir):
    root = data_dir / 'llm_runs/append'
    (root / 'locks').mkdir(parents=True)
    (root / 'locks/task-0.pid').write_text('0')
    bad_task = task.model_copy(update={'instructions': 'BAD_MODE'})
    assert run_many([bad_task], 'append', 1)[0].error.kind == 'schema'
    assert run_many([bad_task], 'append', 1)[0].error.kind == 'schema'
    assert (root / 'logs/worker-0.log').read_text().count('--- attempt ---') == 2
    assert len((root / 'invocations').read_text().splitlines()) == 2


def test_existing_parse_error_quarantined(task, data_dir):
    root = data_dir / 'llm_runs/parse'
    (root / 'answers').mkdir(parents=True)
    (root / 'answers/task-0.json').write_text('broken')
    assert run_many([task], 'parse', 1)[0].error.kind == 'parse'
    assert (root / 'answers/bad/task-0.json').read_text() == 'broken'
    assert not (root / 'invocations').exists()


def test_unrenamed_part_is_adopted(task, data_dir):
    result = run_many([task.model_copy(update={'instructions': 'NORENAME_MODE'})], 'unrenamed', 1)[0]
    assert result.ok
    assert result.data.value == 1
    root = data_dir / 'llm_runs/unrenamed/answers'
    assert (root / 'task-0.json').exists()
    assert not (root / 'task-0.json.part').exists()


def test_part_ignored_on_nonzero_exit(task, data_dir):
    result = run_many([task.model_copy(update={'instructions': 'NORENAME_FAIL_MODE'})], 'nonzero', 1)[0]
    assert result.error.kind == 'backend'
    root = data_dir / 'llm_runs/nonzero/answers'
    assert not (root / 'task-0.json').exists()
    assert (root / 'task-0.json.part').exists()


def test_truncated_part_quarantined(task, data_dir):
    result = run_many([task.model_copy(update={'instructions': 'TRUNCATED_MODE'})], 'truncated', 1)[0]
    assert result.error.kind == 'parse'
    root = data_dir / 'llm_runs/truncated/answers'
    assert (root / 'bad/task-0.json').read_text() == '{"value":'
    assert not (root / 'task-0.json.part').exists()


def test_instruction_names_final_file(task, data_dir):
    run_many([task], 'instruction', 1)
    first_line = (data_dir / 'llm_runs/instruction/prompts/task-0.txt').read_text().splitlines()[0]
    assert '`answers/task-0.json.part`' in first_line
    assert 'answers/task-0.json으로 이름을 바꿔라' in first_line


def test_stale_part_not_adopted(task, data_dir):
    root = data_dir / 'llm_runs/stale'
    (root / 'answers').mkdir(parents=True)
    stale = root / 'answers/task-0.json.part'
    stale.write_text('{"value":7}')
    result = run_many([task.model_copy(update={'instructions': 'SILENT_MODE'})], 'stale', 1)[0]
    assert result.error.kind == 'backend'
    quarantined = list((root / 'answers/bad').glob('task-0.json.part.*'))
    assert len(quarantined) == 1
    assert quarantined[0].read_text() == '{"value":7}'
    assert not stale.exists()
    assert not (root / 'answers/task-0.json').exists()
