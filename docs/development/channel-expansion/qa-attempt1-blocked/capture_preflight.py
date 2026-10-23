"""Capture the authorized backend startup and seed attempt, without product edits."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import tempfile
import urllib.request

QA = Path(__file__).resolve().parent
ROOT = QA.parents[3]
data = tempfile.mkdtemp(prefix="local-data-", dir=QA)
env = dict(os.environ)
env.pop("VOYAGE_API_KEY", None)
env.update(
    STORAGE="local", LOCAL_DATA_DIR=data, EMBED_BACKEND="fake",
    ENABLE_FIXTURE_CHANNEL="true", REAL_CHANNELS_ENABLED="true",
    CORS_ORIGINS="http://localhost:3000",
    DCX_TEST_ADAPTER_MODULE="channel_expansion_qa",
    PYTHONPATH=str(ROOT / "backend/tests/qa_hooks") + ":" + str(ROOT / "backend"),
    PYTHONDONTWRITEBYTECODE="1",
)
env.pop("QA_THREADS_MODE", None)
env.pop("PLAYWRIGHT_BROWSERS_PATH", None)
command = [str(ROOT / "backend/.venv/bin/python"), "-m", "uvicorn",
           "app.main:app", "--port", "8000"]
record = {"startedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
          "command": command, "cwd": str(ROOT / "backend"),
          "localDataDir": data, "ports": {"frontend": 3000, "backend": 8000},
          "voyageApiKeyUnset": "VOYAGE_API_KEY" not in env}
with (QA / "backend-preflight.log").open("w") as log:
    process = subprocess.Popen(command, cwd=ROOT / "backend", env=env,
                               stdout=log, stderr=subprocess.STDOUT)
    record["pid"] = process.pid
    try:
        record["exitCode"] = process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        record["stillRunningAfter15Seconds"] = True
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)
        record["finalExitCode"] = process.returncode
with (QA / "seed-attempt.log").open("w") as log:
    seeded = subprocess.run([str(ROOT / "backend/.venv/bin/python"), str(QA / "seed.py")],
                            cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
                            timeout=20)
    record["seedExitCode"] = seeded.returncode
record["finishedAt"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
(QA / "runtime.json").write_text(json.dumps(record, indent=2))
print(json.dumps(record, indent=2))
