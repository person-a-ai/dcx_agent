"""Write factual blocked QA reports from the approved plan and captured evidence."""
import datetime
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

QA = Path(__file__).resolve().parent
ROOT = QA.parents[3]
REL = "docs/development/channel-expansion/qa"
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
runtime = json.loads((QA / "runtime.json").read_text())
def command(*args):
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()

# Playwright's initial about:blank navigation emitted this automatic snapshot.
# Preserve it under the approved QA directory and remove its newly created folder.
automatic = ROOT / ".playwright-mcp"
if automatic.exists():
    destination = QA / "playwright-generated"
    destination.mkdir(exist_ok=True)
    for path in automatic.iterdir():
        shutil.move(str(path), destination / path.name)
    automatic.rmdir()

head = command("git", "rev-parse", "HEAD")
requested_head = "f22e495fa7946d5d5d18b6283049b62de95bf71a"
head_changes = command("git", "diff", "--name-only", requested_head, "HEAD")
fingerprint = command("/Users/yunho/.local/bin/development-harness", "fingerprint")
tracked = command("git", "diff", "--name-only", "HEAD")
status = command("git", "status", "--porcelain=v1")
assert fingerprint == "3e1e169979028b3760d3a23b12305431c54955f07f6ad5064931dc51690e902f"
assert not tracked
assert all("docs/development/channel-expansion/qa" in line for line in status.splitlines())
dispatch = os.environ["CODEX_THREAD_ID"]
verification = {
    "timestamp": now, "head": head, "fingerprint": fingerprint,
    "trackedDiff": tracked, "gitStatus": status,
    "dispatch": dispatch, "backendProcessesExited": [6049, runtime["pid"]],
    "browserTabClosed": True,
    "requestedHead": requested_head, "headMatchesRequested": head == requested_head,
    "committedChangesDuringQa": head_changes,
}
(QA / "postflight.json").write_text(json.dumps(verification, indent=2))
common = (
    "BLOCKED by environment before scenario execution. Uvicorn initialized but exited "
    "with code 3: [Errno 1] binding 127.0.0.1:8000: operation not permitted. "
    "A second captured attempt with fresh LOCAL_DATA_DIR reproduced the error. "
    "Playwright navigation to http://localhost:3000/pipeline/crawling returned "
    "net::ERR_CONNECTION_REFUSED. Seed POST /context failed with PermissionError "
    "(operation not permitted). No session ID or application DOM was available."
)
if head != requested_head:
    common += f" Final HEAD also changed externally from {requested_head} to {head}; source fingerprint is unchanged."
preflight = f"""# Independent browser QA preflight — BLOCKED

Recorded: {now}
Runtime dispatch: `{dispatch}` (CODEX_THREAD_ID / CODEX_SESSION_ID).
Executor: codex; role: browser-qa; fresh session: true.
Skill: `/Users/yunho/.codex/skills/harness-browser-qa/SKILL.md`, read first.
Worktree: `{ROOT}`; branch: `feature/channel-expansion`.
HEAD before: `{requested_head}` (matched requested commit).
HEAD after: `{head}` (changed externally during QA; does not match).
Committed changes during QA: `{head_changes}`.
The QA worker issued no Git mutation commands. The external change adds a review
document only; product fingerprint remains identical. Immutable HEAD requirement
nevertheless fails and is a separate environment finding.
Fingerprint before and after: `{fingerprint}`.
Initial Git status was empty; postflight tracked diff is empty.
All 17 scenario IDs are active. There are no `[withdrawn]` ID lines.

## Browser verification

Tool: Playwright MCP (`mcp__playwright__browser_navigate`, snapshot, screenshot,
run_code_unsafe, network_requests, console_messages, close).
Tool discovery via tool_search returned an unsupported-call error; live tool
metadata in functions.exec exposed the tools and their schemas. Actual navigation
to about:blank succeeded at 2026-10-20T06:25:23.559Z.
Session: new isolated Chrome context created in this dispatch at that time.
Configured launch: `--browser chrome --isolated`; headed (no headless option).
Observed user agent: Chrome/155.0.0.0 on macOS. No headless fallback was used.

Target: http://localhost:3000/pipeline/crawling
Actual page after failed navigation: `chrome-error://chromewebdata/`, title localhost.
Read saved DOM before selecting the error page's Details button. Clicking Details
changed it to Hide details and expanded Chrome troubleshooting text. This verifies
browser control only; no harmless **application** interaction was possible.

Screenshot saved with explicit absolute path:
`{QA / 'preflight-browser.png'}`.
File existence checked and image opened/visually inspected: Chrome displays
“This site can’t be reached”, localhost refused to connect, ERR_CONNECTION_REFUSED.
This screenshot does not substantiate any product assertion.

## Server and seed

{common}

Captured attempt: {runtime['startedAt']} through {runtime['finishedAt']}.
Command: `backend/.venv/bin/python -m uvicorn app.main:app --port 8000`,
cwd backend. Fresh data directory: `{runtime['localDataDir']}`.
STORAGE=local, EMBED_BACKEND=fake, ENABLE_FIXTURE_CHANNEL=true,
REAL_CHANNELS_ENABLED=true, CORS_ORIGINS=http://localhost:3000,
DCX_TEST_ADAPTER_MODULE=channel_expansion_qa, PYTHONPATH includes backend/tests/qa_hooks
and backend. VOYAGE_API_KEY unset; PYTHONDONTWRITEBYTECODE=1.

Ports 3000/8000 had no listeners before or after. Error was EPERM, not a busy port.
Frontend was not started after the mandatory backend failed to bind. Variant
restarts, all product interactions, mobile rendering, and status/report assertions
remain blocked. No variant result is inferred from source inspection.

The required seed script was written and executed. It uses POST /context then
the real app store update_session to populate approved keywords, writing only
inside the QA directory. Its first POST failed; **zero sessions were seeded**.
No real channel site was requested by the app.

## Evidence and cleanup

- `backend-preflight.log`: captured server startup/bind failure/shutdown.
- `runtime.json`: timestamps, command, fresh data directory, PID and exit codes.
- `seed.py`, `seed-attempt.log`: seeding implementation and failed execution.
- `preflight-browser.md`, `preflight-browser.png`: actual DOM and inspected screenshot.
- `preflight-network.log`: three failed localhost navigation requests.
- `preflight-console.log`: no console messages; not evidence of application correctness.
- `postflight.json`: final commit/fingerprint and tracked-file verification, including HEAD drift.

Both started backend processes exited (6049 and {runtime['pid']}); the owned
browser tab was closed. No frontend or crawl worker was started.
The first Playwright navigation automatically created `.playwright-mcp/page-*.yml`
outside the requested evidence directory. It was moved into `qa/playwright-generated/`
and the generated folder removed; final untracked files are confined to QA paths.
No product code, staging, commits, harness complete, or harness decide changes occurred.

Result: preflight FAIL / execution BLOCKED. The required JSON verdict vocabulary
contains only PASS or FAIL, so qa.json records FAIL with all scenario results BLOCKED.
This is an environment finding, not an observed product defect.
"""
(QA / "preflight.md").write_text(preflight)
plan = (QA.parent / "QA_PLAN-channel-expansion.md").read_text()
scenarios = []
for match in re.finditer(r"```\n(QA-(?:E2E|NEG|EDGE|REG)-\d+)([^\n]*)\n(.*?)```", plan, re.S):
    sid, marker, body = match.groups()
    if "[withdrawn]" in marker:
        continue
    expected = body.split("Then:", 1)[1].strip()
    url = "http://localhost:3000/pipeline/preprocess" if sid == "QA-E2E-006" else (
        "http://localhost:3000/pipeline/start" if sid == "QA-REG-003" else
        "http://localhost:3000/pipeline/crawling")
    actual = common
    if sid == "QA-EDGE-003":
        actual += " No 375px application DOM exists; scrollWidth and table scrolling were not tested."
    if sid in ("QA-NEG-002", "QA-NEG-003"):
        actual += " Variant server was not started after the baseline bind failure; variant-specific assertions are untested."
    evidence = f"{REL}/{sid}.md"
    report = f"""# {sid} — BLOCKED

Recorded: {now}
Shared preflight interval: {runtime['startedAt']} – {runtime['finishedAt']}.
Intended URL: {url}
Session: unavailable (seed failed); no scenario actions were performed.

## Approved scenario (unmodified)

{body.strip()}

## Attempted steps and actual result

1. Confirmed immutable HEAD and source fingerprint; read the full approved plan.
2. Started mandatory backend using QA adapter/fake embedding environment.
3. Observed startup followed by EPERM on localhost:8000 and process shutdown.
4. Opened the crawling URL in the actual isolated Chrome browser; observed connection refused.
5. Executed seed.py against the real POST /context endpoint; connection was denied.
6. Stopped at the unmet Given preconditions. No Then assertion is marked passed.

{actual}

## Evidence

Common preflight: [preflight.md](preflight.md).
Startup/API: [backend-preflight.log](backend-preflight.log),
[runtime.json](runtime.json), [seed-attempt.log](seed-attempt.log).
Browser DOM: [preflight-browser.md](preflight-browser.md).
Screenshot: `{QA / 'preflight-browser.png'}` (saved and inspected).
Network/console: [preflight-network.log](preflight-network.log),
[preflight-console.log](preflight-console.log).

The shared screenshot shows a connection error, not this scenario's product state.
No scenario-specific screenshot or API response could be produced.
"""
    (QA / f"{sid}.md").write_text(report)
    scenarios.append(dict(id=sid, url=url, result="BLOCKED", expected=expected,
                          actual=actual, evidence=evidence))
assert len(scenarios) == 17
report = {
    "verdict": "FAIL", "head": head, "fingerprint": fingerprint,
    "requestedHead": requested_head, "initialHead": requested_head,
    "executor": "codex", "role": "browser-qa", "freshSession": True,
    "dispatch": dispatch,
    "browser": {"tool": "Playwright MCP / Chrome (headed, isolated)",
                "session": f"{dispatch}; isolated context opened 2026-10-20T06:25:23.559Z",
                "preflight": "FAIL", "evidence": f"{REL}/preflight.md"},
    "scenarios": scenarios,
    "findings": [{
        "id": "QA-ENV-001", "severity": "BLOCKER", "scenario": "ALL_ACTIVE_IDS",
        "issue": "Sandbox forbids localhost server binding and API connection; application preflight blocked.",
        "reproduction": "Run the approved uvicorn command in this sandbox with the QA environment. It initializes, fails binding 127.0.0.1:8000 with Errno 1, and exits 3. Open localhost:3000/pipeline/crawling in Playwright: ERR_CONNECTION_REFUSED.",
        "evidence": f"{REL}/preflight.md",
    }],
}
if head != requested_head:
    report["findings"].append({
        "id": "QA-ENV-002", "severity": "BLOCKER", "scenario": "ALL_ACTIVE_IDS",
        "issue": "HEAD changed externally during QA; immutable tested-commit requirement failed.",
        "reproduction": f"Initial HEAD {requested_head}; final HEAD {head}. Changed committed file: {head_changes}. Product fingerprint unchanged. No worker Git mutations.",
        "evidence": f"{REL}/postflight.json",
    })
(QA.parent / "qa.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(json.dumps({"verdict": report["verdict"], "counts": {"BLOCKED": len(scenarios)},
                  "head": head, "fingerprint": fingerprint}, indent=2))
