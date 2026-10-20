"""Assemble the independent QA report from recorded evidence; no product writes."""
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path("/Users/yunho/Documents/dcx_agent-v1-cleanup")
OUT = ROOT / "docs/development/v1-cleanup/qa"
HEAD = "c15ea7fa22e3641078939a524f5a5581b2689127"
summaries = {
    "QA-E2E-001": ("Four stages disabled with required titles/no href; six earlier links work; locked click stays put.", "All DOM attributes matched; clicking clustering left URL unchanged."),
    "QA-E2E-002": ("Clustering prep banner/action; no cluster-status, cluster, cluster-refine, save-session requests.", "Exact banner; no prohibited requests; action opened /pipeline/preprocess."),
    "QA-E2E-003": ("Persona prep banner, no old Start button or prohibited requests; session step unchanged.", "Exact banner; no Start button or prohibited requests; step remained start."),
    "QA-E2E-004": ("Insight prep banner; no /sessions, persona-status, cluster-status, sna-data requests.", "Banner matched, but GET /sessions occurred twice."),
    "QA-E2E-005": ("Ten enabled links; three new screens; no gate banners; zero console errors.", "Screens and links matched; persona endpoint returned 409 and produced three console errors."),
    "QA-E2E-006": ("Prep done; no preprocessed directory/compatRef; same-settings rerun reused=true; clustering linked.", "Six docs completed; no compatibility artifacts; second POST reused=true; link enabled."),
    "QA-E2E-007": ("All three legacy banners; action to start; no prohibited legacy requests.", "Exact banners and destinations matched on all three pages; prohibited requests absent."),
    "QA-NEG-001": ("Thirteen removed endpoints return 404/405 without Traceback.", "All thirteen returned 404; no Traceback."),
    "QA-NEG-002": ("Persona/train/prep v2 status routes do not return 404.", "All three returned 200."),
    "QA-NEG-003": ("Empty storage shows project-selection banner; action to start; zero console errors.", "Storage empty; banner/action matched; zero console errors."),
    "QA-EDGE-001": ("375x812: 72px number-only sidebar, unclipped banner/action, no horizontal overflow.", "Sidebar 72px; scrollWidth 375; action below message and clickable; screenshot inspected."),
    "QA-EDGE-002": ("Locked during initial prep; linked after completion without refresh; link survives reload.", "Link survived completion/reload, but unlocked at 04:21:11.411Z while prep remained running through 04:21:13.979Z."),
    "QA-EDGE-003": ("Stage3 restart creates v2 without prep, locks later stages and shows prep banner.", "v2 retained stale derivedRef with prepDone=false; all later links stayed enabled; no prep banner."),
    "QA-EDGE-004": ("Tab skips four locked entries; unlocked entries have visible 2px focus outlines.", "Six links received 2px solid focus outlines; next Tab skipped to version button."),
    "QA-REG-001": ("Chat panels send to /chat and /insight-chat without 404 and show answer/error.", "Pipeline panel sent /chat:200 and displayed fallback. Direct /insight-chat probe:200, but its UI path was unreachable after /insights redirected; UI integration unverified."),
    "QA-REG-002": ("/insights redirects to /pipeline/insights.", "Redirect and final rendered screen confirmed."),
    "QA-REG-003": ("Every derived document has desc/cafe/link; desc length <=4000.", "All six rows have required keys; each desc is 44 characters."),
    "QA-REG-004": ("Keyword screen opens with zero console errors.", "Rendered keyword screen; zero console errors."),
    "QA-REG-005": ("Legacy crawling preserves the 0-2-stage editing restriction banner.", "Exact existing restriction message displayed."),
}
details = {}
scenarios = []
for scenario_id, (expected, actual) in summaries.items():
    file = OUT / f"{scenario_id}.md"
    d = json.loads(file.read_text().split("```json\n", 1)[1].split("\n```", 1)[0])
    details[scenario_id] = d
    assert Path(d["screenshot"]).is_file(), d["screenshot"]
    url = d.get("testedURL", d["url"])
    if scenario_id in ("QA-EDGE-001",):
        url = "http://localhost:3411/pipeline/personas"
    if scenario_id == "QA-NEG-003":
        url = "http://localhost:3411/pipeline/clustering"
    if scenario_id == "QA-REG-002":
        url = "http://localhost:3411/insights"
    if scenario_id.startswith("QA-NEG-00") and scenario_id != "QA-NEG-003":
        url = "http://127.0.0.1:8411"
    scenarios.append(dict(id=scenario_id, url=url, result=d["result"],
                          expected=expected, actual=actual, evidence=d["evidence"]))

findings = [
    dict(id="F-01", severity="P0", scenario="QA-EDGE-002",
         title="Later-stage navigation unlocks while preprocessing is running",
         detail="MutationObserver recorded all four hrefs at 04:21:11.411Z. Status responses at 04:21:10.958Z and 04:21:13.979Z were running, stage3=null. Post-completion and reload assertions passed; the stipulated locked-running state did not.",
         evidence=details["QA-EDGE-002"]["evidence"]),
    dict(id="F-02", severity="P1", scenario="QA-E2E-004",
         title="Direct insights navigation issues prohibited /sessions requests",
         detail="GET http://localhost:8411/sessions occurred at 04:20:16.327Z and 04:20:16.328Z. The banner was correct. No exemption was made for requests possibly originating in the shared shell.",
         evidence=details["QA-E2E-004"]["evidence"]),
    dict(id="F-03", severity="P1", scenario="QA-E2E-005",
         title="Completed-prep persona screen violates zero-error-console criterion",
         detail="GET /segment/sf7d9d6897a31472895cf5fdeafb9cea1/personas?version=v1 returned 409 three times, with the message that earlier layers must be confirmed. All ten links and all three new screens were present.",
         evidence=details["QA-E2E-005"]["evidence"]),
    dict(id="F-04", severity="P2", scenario="QA-EDGE-003",
         title="Stage3 restart keeps stale prep reference and leaves later stages open",
         detail="UI POST versions from=v1/restartFrom=stage3 created active v2. Session retained prep.derivedRef, prep.status=stale and completion.prepDone=false. The clustering screen remained open; required gate banner never appeared.",
         evidence=details["QA-EDGE-003"]["evidence"]),
    dict(id="F-05", severity="P1", scenario="QA-REG-001",
         title="Insight chatbot UI integration could not be verified",
         detail="The visible chatbot on /pipeline/insights uses /chat and displayed a valid no-model fallback. /insights immediately redirects. Direct /insight-chat returned 200, proving route survival only; it does not prove the requested insight chatbot UI request path.",
         evidence=details["QA-REG-001"]["evidence"]),
]
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
status = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True)
assert head == HEAD
assert all(line.startswith("?? docs/development/v1-cleanup/") for line in status.splitlines())
fingerprint = subprocess.check_output(
    [str(Path.home() / ".local/bin/development-harness"), "fingerprint"],
    cwd=ROOT, text=True).strip()
report = dict(
    verdict="PASS" if all(s["result"] == "PASS" for s in scenarios) else "FAIL",
    head=head, fingerprint=fingerprint, findings=findings,
    executor="codex", role="browser-qa", freshSession=True,
    dispatch="01a15786-12bc-7fa3-a3ca-65e3d7d2f1d0",
    browser=dict(tool="playwright-mcp",
                 session="Fresh isolated Chrome/Chromium 155.0.8059.85 context; initially one page and empty localStorage; worker-owned page closed after QA",
                 preflight="PASS", evidence="docs/development/v1-cleanup/qa/preflight.md"),
    scenarios=scenarios,
)
(OUT / "qa.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
(OUT / "final-integrity.json").write_text(json.dumps(dict(
    checkedAt=datetime.now(timezone.utc).isoformat(), head=head, status=status,
    initialFingerprint="a89512faf2eacae1e240d660ab0707ad5043d4e09f028b5a79b7fc68da8044e8",
    finalFingerprint=fingerprint, productChanges=False, stagedChanges=False,
    scenarioCount=len(scenarios),
    counts={r: sum(s["result"] == r for s in scenarios) for r in ["PASS", "FAIL", "BLOCKED", "NOT_RUN"]},
), indent=2) + "\n")
assert len(scenarios) == 19
print(json.dumps(report, ensure_ascii=False, indent=2))
