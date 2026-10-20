"""Assemble QA reports from this worker's recorded browser observations; no app writes."""
import json
from pathlib import Path
from urllib.parse import urlparse

Q = Path(__file__).resolve().parent
REL = "docs/development/v1-cleanup-r2/qa/"
HEAD = "5de8f30bbb05986afa4b5ccf579d3d0442302857"
BASE = "http://localhost:3411"
API = "http://127.0.0.1:8411"
SID = "s3bee57561d744ff8a5cf63fc5bff34f9"
load = lambda n: json.loads((Q / (n + ".json")).read_text())
events = load("all-events")["events"]
g = load("gates")
p = load("prep-success")
running = load("prep-running")["running"]
files = load("prep-files-done")
c = load("completed-screens")
im = load("insights-mobile")
kk = load("keyboard-keywords")
leg = load("legacy")
neg = load("negative")
chat = load("chat-success")
v = load("version-success")
scenarios = []
assertions = {}


def clean(x):
    if isinstance(x, dict):
        return {k: clean(a) for k, a in x.items() if k != "events"}
    if isinstance(x, list):
        return [clean(a) for a in x]
    return x


def no_requests(es, prefixes):
    return not any(e["type"] == "request" and
                   any(urlparse(e["url"]).path == s or
                       urlparse(e["url"]).path.startswith(s + "/")
                       for s in prefixes) for e in es)


def errors(es):
    return [e for e in es if e["type"] == "pageerror" or
            e["type"] == "console" and e["level"] == "error"]


def locked(nav):
    return len(nav) == 10 and all(x["aria"] == "true" and x["href"] is None
                                  for x in nav[6:])


def opened(nav):
    return len(nav) == 10 and all(x["href"] and x["aria"] is None for x in nav)


def report(id, route, expected, actual, steps, data, checks, sources, shots=(), marks=None, notes=""):
    result = "PASS" if all(checks.values()) else "FAIL"
    assertions[id] = checks
    url = route if route.startswith("http") else BASE + route
    scenarios.append(dict(id=id, url=url, result=result, expected=expected,
                          actual=actual, evidence=REL + id + ".md"))
    es = [e for e in events if any(e["mark"].startswith(m) for m in (marks or [id]))]
    times = [e["time"] for e in es]

    def collect_times(obj):
        if isinstance(obj, dict):
            if "time" in obj:
                times.append(obj["time"])
            for value in obj.values():
                collect_times(value)
        elif isinstance(obj, list):
            for value in obj:
                collect_times(value)
    collect_times(data)
    text = f"# {id} — {result}\n\n"
    text += f"- URL: {url}\n- Tested HEAD: `{HEAD}`\n"
    text += "- Executor: codex / browser-qa; thread `01a15844-a762-7910-97e2-9d33167a6188`.\n"
    if times:
        text += f"- Recorded UTC interval: {min(times)} → {max(times)}.\n"
    text += f"\n## Expected\n\n{expected}\n\n## Steps\n\n"
    text += "\n".join(f"{i}. {s}" for i, s in enumerate(steps, 1))
    text += f"\n\n## Actual\n\n{actual}\n\n"
    text += "\n".join(f"- {'PASS' if ok else 'FAIL'} — {name}" for name, ok in checks.items())
    text += "\n\n## Evidence\n\n"
    for name in sources + ["all-events.json"]:
        assert (Q / name).is_file(), name
        text += f"- [{name}]({name})\n"
    for name in shots:
        assert (Q / name).is_file() and (Q / name).stat().st_size > 0, name
        text += f"- [{name}]({name}) — absolute-path capture, existence verified, visually inspected.\n"
    if not shots:
        text += "- API/file assertions use response or filesystem records; no screenshot substituted for data proof.\n"
    text += "\n## Console / network / API\n\n"
    text += f"Page errors: {sum(e['type'] == 'pageerror' for e in es)}; console error messages: {sum(e['type'] == 'console' and e['level'] == 'error' for e in es)}.\n\n"
    text += "Complete timestamped request/response bodies and console locations are in the linked JSON. Relevant observed HTTP/error entries:\n\n```text\n"
    for e in es:
        if e["type"] == "response" and ":8411/" in e["url"]:
            text += f"{e['time']} HTTP {e['status']} {e['url']}\n"
        elif e["type"] == "pageerror" or e["type"] == "console" and e["level"] == "error":
            text += f"{e['time']} {e['type']} {e.get('text')} {e.get('location', {}).get('url', '')}\n"
    text += "```\n\n## Captured state / API output\n\n```json\n"
    text += json.dumps(clean(data), ensure_ascii=False, indent=2) + "\n```\n"
    if notes:
        text += "\n## Execution notes\n\n" + notes + "\n"
    (Q / (id + ".md")).write_text(text)


a = g["e001"]
report("QA-E2E-001", "/pipeline/start",
       "Four later stages disabled with required titles and no href; six earlier links; locked click preserves URL.",
       "All ten DOM entries matched; clicking locked clustering kept /pipeline/start.",
       ["Select QA 전처리 전 through /pipeline/start.", "Read all sidebar attributes.", "Click the rendered locked clustering item with the mouse and compare URL."],
       a, {"four locked": locked(a["nav"]),
           "four exact titles": all(x["title"] == "전처리(3단계)를 먼저 완료하세요" for x in a["nav"][6:]),
           "six earlier hrefs": all(x["href"] for x in a["nav"][:6]),
           "URL unchanged": a["before"] == a["after"]},
       ["gates.json"], ["QA-E2E-001.png"])

a = g["e002"]
report("QA-E2E-002", "/pipeline/clustering",
       "Exact clustering prep banner and action; no cluster-status/cluster/cluster-refine/save-session requests.",
       "Exact banner rendered; prohibited requests absent; action reached /pipeline/preprocess.",
       ["Keep QA 전처리 전 selected; begin a fresh network observation.", "Directly navigate to clustering; inspect banner and requests.", "Click 전처리 화면으로 and await URL."],
       a, {"exact banner": "3단계(전처리)를 먼저 완료하세요. 전처리가 끝나야 클러스터링 화면을 열 수 있습니다." in a["body"],
           "no prohibited calls": no_requests(a["events"], ["/cluster-status", "/cluster", "/cluster-refine", "/save-session"]),
           "action destination": a["actionUrl"] == BASE + "/pipeline/preprocess"},
       ["gates.json"], ["QA-E2E-002.png"])

a = g["e003"]
report("QA-E2E-003", "/pipeline/personas",
       "Persona prep banner; no old Start button or embed/persona/persona-status/save-session calls; data.step unchanged.",
       "Banner matched; Start button count 0; prohibited requests 0; data.step stayed start.",
       ["GET session before navigation.", "Directly open personas with QA 전처리 전 selected.", "Inspect DOM and request trace, then GET the same session again."],
       a, {"persona banner": "전처리가 끝나야 페르소나 화면을 열 수 있습니다." in a["body"],
           "old Start absent": a["startButtons"] == 0,
           "no prohibited calls": no_requests(a["events"], ["/embed", "/persona", "/persona-status", "/save-session"]),
           "step unchanged": a["before"]["data"]["step"] == a["after"]["data"]["step"]},
       ["gates.json"], ["QA-E2E-003.png"])

report("QA-E2E-006", "/pipeline/preprocess",
       "First prep completes; no preprocessed directory or compatRef; identical rerun reused=true; clustering becomes linked.",
       "Six documents completed; no compatibility artifacts; second UI run returned reused=true; clustering linked.",
       ["Select QA 전처리 실행, confirm no prep and no preprocessed directory.", "Run preprocessing from UI, recording running state and sidebar mutations.", "Wait for done and automatic unlock without navigation.", "Click 다시 실행 with identical settings; inspect response.", "Read derived manifest and directory state."],
       {"before": load("prep-before"), "running": running, "completion": p, "files": files},
       {"initial no prep": "prep" not in load("prep-before")["session"],
        "first status done": p["done"]["status"]["status"] == "done",
        "no compatibility directory before or after": not load("prep-before")["preprocessedExists"] and not files["preprocessedExists"],
        "manifest exists without compatRef": bool(files["manifests"]) and all("compatRef" not in x["data"] for x in files["manifests"]),
        "reused true": p["reuse"]["reused"] is True,
        "clustering enabled": p["done"]["nav"][6]["href"] == "/pipeline/clustering"},
       ["prep-before.json", "prep-running.json", "prep-success.json", "prep-files-done.json", "prep-timeout.json"],
       ["QA-EDGE-002-running.png", "QA-E2E-006-done.png"],
       marks=["prep-first", "prep-reuse"],
       notes="Initial 30-second wait expired while actual prep remained running. Continued observing the same page with no reload; done arrived at 07:49:10.253Z. There is no plan time limit. Early filesystem inspection had no manifest yet; preserved as prep-files.json. Preprocess entry/reload emitted crawl/status 404 for the seeded fixture; this scenario has no zero-404 assertion, and these are not part of QA-E2E-009.")

legacy_message = "구버전 세션은 이 단계를 열 수 없습니다. 새 프로젝트를 만들어 진행하세요."
report("QA-E2E-007", "/pipeline/clustering",
       "Legacy session shows the exact banner on all three pages; selection action reaches start; no prohibited legacy requests.",
       "All three banners and return actions matched; prohibited requests absent.",
       ["Select seeded QA 옛 세션 through start.", "Directly open clustering, personas and insights separately.", "For each page capture banner/network and click 프로젝트 선택하기."],
       leg["legacy"],
       {"three pages": len(leg["legacy"]) == 3,
        "three exact banners": all(legacy_message in x["body"] for x in leg["legacy"]),
        "three return actions": all(x["actionUrl"] == BASE + "/pipeline/start" for x in leg["legacy"]),
        "no prohibited calls": all(no_requests(x["events"], ["/cluster-status", "/persona-status", "/sna-data", "/embed"]) for x in leg["legacy"])},
       ["legacy.json"], [f"QA-E2E-007-{r}.png" for r in ["clustering", "personas", "insights"]])

counts = [sum(e["type"] == "request" and urlparse(e["url"]).path == "/sessions" for e in x["events"]) for x in im["e008"]]
report("QA-E2E-008", "/pipeline/insights",
       "Insight prep banner; no persona-status/cluster-status/sna-data calls; /sessions count no greater than clustering control.",
       f"Exact banner; prohibited calls 0; /sessions requests: insights {counts[1]}, clustering control {counts[0]}.",
       ["Keep QA 전처리 전 selected for both pages.", "Directly open clustering as control with a fresh observation.", "Directly open insights with a fresh observation.", "Use the same rendered-action readiness and network-quiescence check on each, then compare exact /sessions paths."],
       {"pages": im["e008"], "controlSessions": counts[0], "insightsSessions": counts[1]},
       {"insight prep banner": "전처리가 끝나야 인사이트 화면을 열 수 있습니다." in im["e008"][1]["body"],
        "no prohibited calls": no_requests(im["e008"][1]["events"], ["/persona-status", "/cluster-status", "/sna-data"]),
        "insights <= control": counts[1] <= counts[0]},
       ["insights-mobile.json"], ["QA-E2E-008-clustering.png", "QA-E2E-008-insights.png"])

ce = errors(c["events"])
allowed = lambda e: (e["type"] == "console" and "status of 409" in e["text"] and
                      urlparse(e["location"]["url"]).path == f"/segment/{SID}/personas")
report("QA-E2E-009", "/pipeline/clustering",
       "Ten sidebar links; three new screens; zero pageerror/404; only HTTP 409 console errors from /segment/{sid}/personas allowed.",
       "All screens and ten links matched; pageerror 0, HTTP 404 0; four console errors, all allowed persona HTTP 409.",
       ["Use the completed v1 session.", "Begin error/network observation immediately before sidebar clustering click.", "Click clustering, personas and insights in order; await rendered states.", "Record all responses, pageerror and console error locations without filtering exceptions."],
       c, {"all ten links on all three pages": len(c["screens"]) == 3 and all(opened(x["nav"]) for x in c["screens"]),
           "clustering execution button": "클러스터링 실행" in c["screens"][0]["body"],
           "new persona screen without prep gate": "세션 전체에서 어느 Context가 기회인가" in c["screens"][1]["body"] and "전처리를 먼저 완료하세요" not in c["screens"][1]["body"],
           "new insight screen without legacy gate": "인사이트 도출" in c["screens"][2]["body"] and "구버전 세션" not in c["screens"][2]["body"],
           "zero pageerror": not any(e["type"] == "pageerror" for e in c["events"]),
           "zero 404": not any(e["type"] == "response" and e["status"] == 404 for e in c["events"]),
           "only exact allowed console errors": all(allowed(e) for e in ce)},
       ["completed-screens.json"], [f"QA-E2E-009-{r}.png" for r in ["clustering", "personas", "insights"]])

report("QA-NEG-001", API,
       "Thirteen removed API paths return 404 or 405 without Python Traceback.",
       "All 13 returned HTTP 404 with no Traceback.",
       ["Use browser APIRequestContext against the running backend.", "Send all 13 plan method/path pairs with JSON {sid:x}.", "Capture each status and raw response body."],
       neg["removed"], {"all 13 tested": len(neg["removed"]) == 13,
                         "all removed": all(x["status"] in (404, 405) for x in neg["removed"]),
                         "no Traceback": all("Traceback" not in x["body"] for x in neg["removed"])},
       ["negative.json"])
report("QA-NEG-002", API,
       "Persona, train and prep v2 status endpoints do not return 404.",
       "All three returned HTTP 200 for the completed session.",
       ["After QA-E2E-009, GET persona/{sid}/status, train/{sid}/status and prep/{sid}/status.", "Record statuses and JSON."],
       c["api"], {"three calls": len(c["api"]) == 3, "none 404": all(x["status"] != 404 for x in c["api"])},
       ["completed-screens.json"])
a = neg["empty"]
report("QA-NEG-003", "/pipeline/clustering",
       "Empty browser storage shows project-selection banner; action reaches start; zero console errors.",
       "Storage empty, exact banner displayed, action reached start; console errors 0.",
       ["Clear localStorage, sessionStorage and context cookies.", "Directly navigate to clustering.", "Check banner/error trace and click 프로젝트 선택하기."],
       a, {"empty storage": a["storage"] == {"local": {}, "session": {}},
           "exact banner": "프로젝트를 먼저 선택하세요." in a["body"],
           "action": a["actionUrl"] == BASE + "/pipeline/start", "zero errors": not errors(a["events"])},
       ["negative.json"], ["QA-NEG-003.png"])

a = im["mobile"]
l = a["layout"]
report("QA-EDGE-001", "/pipeline/personas",
       "375×812: 72px number-only sidebar; full unclipped banner; visible clickable action; scrollWidth <=375.",
       "Sidebar 72px, labels hidden, scrollWidth 375; banner and button fully visible; click reached preprocess.",
       ["Select QA 전처리 전 and resize browser viewport to 375×812.", "Directly open personas.", "Inspect screenshot and DOM rectangles; click 전처리 화면으로."],
       a, {"viewport": (l["width"], l["height"]) == (375, 812),
           "72px sidebar": l["side"]["width"] == 72,
           "text labels hidden": all(x["display"] == "none" for x in l["labels"]),
           "banner in viewport and visually unclipped": l["banner"]["right"] <= 375 and l["banner"]["bottom"] <= 812,
           "button in viewport": l["button"]["left"] >= 0 and l["button"]["right"] <= 375 and l["button"]["bottom"] <= 812,
           "button click": a["actionUrl"] == BASE + "/pipeline/preprocess",
           "no horizontal overflow": l["scrollWidth"] <= 375},
       ["insights-mobile.json"], ["QA-EDGE-001.png"])

transitions = p["done"]["transitions"]
done_events = [e for e in events if e["mark"] == "prep-first" and e["type"] == "response" and "/prep/" in e["url"] and "/status" in e["url"] and e.get("body") and json.loads(e["body"]).get("status") == "done"]
report("QA-EDGE-002", "/pipeline/preprocess",
       "Later stages stay locked during prep, unlock only after done without reload, and remain open after reload.",
       "Locked at running; first done response 07:49:10.253Z, automatic unlock 07:49:10.420Z; reload retained links.",
       ["Observe alongside the first QA-E2E-006 UI run.", "Install read-only DOM MutationObserver before clicking run.", "Correlate running/done HTTP responses with sidebar href changes.", "Capture done state, then reload and check the link."],
       {"running": running, "done": p["done"], "reloaded": p["reloaded"]},
       {"running is running": running["status"]["status"] == "running",
        "running derivedRef exists yet locked": bool(running["status"]["derivedRef"]) and locked(running["nav"]),
        "only locked then unlocked transition": len(transitions) == 2 and all(x["href"] is None for x in transitions[0]["items"]),
        "unlock after done": bool(done_events) and transitions[1]["time"] > done_events[0]["time"],
        "all four unlocked": all(x["href"] and x["disabled"] is None for x in transitions[1]["items"]),
        "no page navigation before unlock": not any(e["mark"] == "prep-first" and e["type"] == "request" and e["url"] == BASE + "/pipeline/preprocess" for e in events),
        "reload preserves link": p["reloaded"]["nav"][6]["href"] == "/pipeline/clustering"},
       ["prep-running.json", "prep-success.json", "prep-timeout.json"],
       ["QA-EDGE-002-running.png", "QA-E2E-006-done.png", "QA-EDGE-002-reload.png"],
       marks=["prep-first", "prep-reuse"])

report("QA-EDGE-003", "/pipeline/clustering",
       "Stage3 restart v2 locks stages 6–9 and shows prep banner; reselecting completed v1 consistently opens sidebar and clustering/personas pages (DV-5).",
       "v2 stale prep locked all four stages and showed banner. v1 restored ten links; clustering read-only view and persona screen opened without prep gates.",
       ["Run last, after the other 18 active cases.", "From completed session preprocess click 3단계부터 다시 → 새 버전 만들기.", "Observe POST from=v1/restartFrom=stage3 creating v2.", "Directly open clustering and inspect v2 gate/session.", "Open version list and select v1; inspect clustering, then click personas."],
       v, {"created v2 from stage3": v["status"] == 201 and v["response"]["version"] == "v2" and json.loads(v["request"])["restartFrom"] == "stage3",
           "v2 invalid prep": v["v2"]["session"]["data"]["prep"]["status"] == "stale" and not v["v2"]["session"]["data"]["completion"]["prepDone"],
           "v2 four locked": locked(v["v2"]["nav"]),
           "v2 prep banner": "3단계(전처리)를 먼저 완료하세요" in v["v2"]["body"],
           "v1 completed": v["v1cluster"]["session"]["data"]["prep"]["status"] == "done",
           "v1 clustering open": opened(v["v1cluster"]["nav"]) and "6단계의 저장된 결과를 확인합니다" in v["v1cluster"]["body"] and "전처리)를 먼저" not in v["v1cluster"]["body"],
           "v1 personas open": opened(v["v1personas"]["nav"]) and "세션 전체에서 어느 Context가 기회인가" in v["v1personas"]["body"] and "전처리)를 먼저" not in v["v1personas"]["body"]},
       ["version-success.json"], ["QA-EDGE-003-v2.png", "QA-EDGE-003-v1-clustering.png", "QA-EDGE-003-v1-personas.png"],
       notes="Extra DV-5 observation: clustering's old version is its read-only stored-results view; personas displays the persona UI with v1 read-only label. Both pass the gate. Initial QA locator incorrectly waited for an active-version execution button on clustering, then for a generic saved-results heading on personas; those timeouts did not represent required assertions. Corrected after inspecting actual DOM. The v1 persona endpoint continues returning its existing 409; preprocess entry emits seeded crawl/status 404s. These are recorded, and QA-EDGE-003 does not impose the QA-E2E-009 console rule.")

a = kk["keyboard"]
report("QA-EDGE-004", "/pipeline/personas",
       "Tab skips all four locked sidebar items; unlocked links show 2px focus outline.",
       "Six earlier links received 2px solid focus-visible outlines; next Tab skipped to version button.",
       ["Restore desktop viewport with QA 전처리 전 selected.", "Focus sidebar collapse control as a starting point.", "Press Tab seven times and record active element and computed outline; capture third link focus."],
       a, {"six links": len(a) == 7 and all(x["tag"] == "A" for x in a[:6]),
           "2px visible outlines": all(x["outlineWidth"] == "2px" and x["outlineStyle"] == "solid" and x["focusVisible"] for x in a[:6]),
           "locked items skipped": all(x["disabled"] != "true" for x in a) and a[6]["tag"] == "BUTTON" and "버전 목록" in a[6]["text"]},
       ["keyboard-keywords.json"], ["QA-EDGE-004.png"])

report("QA-REG-002", "/insights",
       "/insights redirects to /pipeline/insights.",
       "HTTP 307 redirect reached the rendered /pipeline/insights screen.",
       ["With completed session selected, navigate directly to /insights.", "Wait for redirected URL and insight empty-state text."],
       chat["redirect"], {"redirect destination": chat["redirect"]["url"] == BASE + "/pipeline/insights",
                           "rendered": "인사이트 도출" in chat["redirect"]["body"]},
       ["chat-success.json"], ["QA-REG-002.png"])
report("QA-REG-003", "/pipeline/preprocess",
       "Each derived JSONL row contains desc/cafe/link and desc length <=4000.",
       "All six rows contain the three fields; every desc is 44 characters.",
       ["Immediately after first prep/reuse checks, read all derived docs/*.jsonl rows.", "Record filenames, row numbers, keys and desc lengths without changing data."],
       files, {"six rows inspected": len(files["rows"]) == 6,
               "all keys": all({"desc", "cafe", "link"}.issubset(x["keys"]) for x in files["rows"]),
               "desc maximum": all(x["descLength"] <= 4000 for x in files["rows"])},
       ["prep-files-done.json"])
a = kk["keywords"]
report("QA-REG-004", "/pipeline/keywords",
       "Keyword screen opens with zero console errors.",
       "R1 keyword screen rendered; console errors and pageerror both 0.",
       ["Select QA 전처리 전.", "Directly open keywords and await rendered UI/network readiness.", "Capture screen and all console/pageerror events."],
       a, {"keyword screen": "1단계 · 키워드" in a["body"] and "R1 초기 발산 결과" in a["body"],
           "zero console errors": not errors(a["events"])},
       ["keyboard-keywords.json"], ["QA-REG-004.png"])
a = leg["crawling"]
report("QA-REG-005", "/pipeline/crawling",
       "Legacy crawling retains the existing 0–2-stage editing restriction banner.",
       "Exact legacy editing restriction remained visible.",
       ["Keep QA 옛 세션 selected after legacy gate cases.", "Directly navigate to crawling and inspect rendered banner."],
       a, {"existing banner": "구버전 세션은 0~2단계를 편집할 수 없습니다." in a["body"]},
       ["legacy.json"], ["QA-REG-005.png"])
report("QA-REG-006", "/pipeline/insights",
       "Pipeline chat panel sends POST /chat, not 404, and displays answer/error; API-only POST /insight-chat is not 404.",
       "POST /chat and /insight-chat returned 200; panel displayed the no-model fallback answer.",
       ["Open pipeline chatbot on the completed session.", "Enter 현재 전처리 상태를 알려주세요. and click 전송.", "Capture POST /chat response and actual panel text.", "Read OpenAPI request schema; call /insight-chat with sid/query/bk/novel through APIRequestContext only."],
       chat, {"chat route alive": chat["chat"]["status"] != 404,
              "panel displays response": chat["chat"]["body"]["answer"] in chat["panel"],
              "insight route alive": chat["insight"]["status"] != 404},
       ["chat-success.json"], ["QA-REG-006.png"],
       notes="First response waiter used URL, unavailable in this tool's VM; actual first POST still returned 200. Retry used the observed URL string and verified panel text. The failed tool attempt is retained in chat-redirect-tool.json. Insight chat UI is deliberately not asserted because D-306 makes it unreachable. No answer-quality assertion or LLM-key requirement.")

scenarios.sort(key=lambda x: (["E2E", "NEG", "EDGE", "REG"].index(x["id"].split("-")[1]), x["id"]))
expected_ids = ([f"QA-E2E-{i:03d}" for i in [1, 2, 3, 6, 7, 8, 9]] +
                [f"QA-NEG-{i:03d}" for i in range(1, 4)] +
                [f"QA-EDGE-{i:03d}" for i in range(1, 5)] +
                [f"QA-REG-{i:03d}" for i in range(2, 7)])
assert [x["id"] for x in scenarios] == expected_ids
report_json = dict(
    verdict="PASS" if all(x["result"] == "PASS" for x in scenarios) else "FAIL",
    head=HEAD,
    fingerprint="782850ccbb537d9468d3457193dfee775ab5dd5105d031d0833a8e02fcbd49ad",
    findings=[{"scenario": x["id"], "title": "Acceptance assertion failed",
               "checks": [k for k, val in assertions[x["id"]].items() if not val],
               "evidence": x["evidence"]} for x in scenarios if x["result"] != "PASS"],
    executor="codex", role="browser-qa", freshSession=True,
    dispatch="01a15844-a762-7910-97e2-9d33167a6188",
    browser=dict(tool="playwright-mcp",
                 session="Fresh isolated visible Chrome 155.0.8059.85 context; one initial page, initial localStorage {}; worker-owned page closed after QA",
                 preflight="PASS", evidence=REL + "preflight.md"),
    scenarios=scenarios)
(Q / "qa.json").write_text(json.dumps(report_json, ensure_ascii=False, indent=2) + "\n")
(Q / "assertions.json").write_text(json.dumps(assertions, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"verdict": report_json["verdict"], "count": len(scenarios),
                  "findings": report_json["findings"]}, ensure_ascii=False))
