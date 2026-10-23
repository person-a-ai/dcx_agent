# QA-NEG-003 — PASS

Updated: 2026-10-20T13:32:23.421614+00:00

URL: http://localhost:3012/pipeline/crawling

Approved steps and expected:
```
QA-NEG-003
Priority: P0
Type: Negative / Failure injection
Given: 서버를 `QA_THREADS_MODE=blocked`로 다시 띄웠고, Threads만 켠 세션에서 목록 수집이 끝난 게이트 화면이다
When: "상세 수집 시작"을 누르고 멈출 때까지 기다린 뒤 "여기까지로 마치기"를 누르고 확인한다
Then:
  - 멈춤 배너 "수집이 멈췄습니다"가 보인다
  - 배너에 "Threads" 배지가 보인다
  - 배너에 "Threads가 로그인 화면을 보여 주어 멈췄습니다. 로그인은 시도하지 않습니다." 문구가 보인다
  - "여기까지로 마치기" 후 결과 화면 "건너뛴 항목" 표에 "Threads · 차단으로 여기까지 마침" 행이 있다
  - 서버 로그와 네트워크 기록에 threads.com 로그인 주소 요청이 없다
```

Actual execution and observations:
Used prestarted blocked environment3012→8012. Threads-only list finished; detail paused after20 blocked attempts. Banner 수집이 멈췄습니다, Threads badge and exact no-login-attempt sentence visible. Clicked 여기까지로 마치기 and accepted confirmation (50 URLs); result skip row Threads 차단으로 여기까지 마침50건. Browser network has no threads.com login requests. Copied worker list/detail logs (detail empty), queue read-only backup/dump, report and worker_state; no login URL in those records. QA hook inspection confirms synthetic AdapterBlocked without external requests. See logs-blocked/ and qa-hook-inspected.py; scoped to approved synthetic environment.

Evidence:
- [QA-NEG-003-paused.json](QA-NEG-003-paused.json)
- [QA-NEG-003-paused.png](QA-NEG-003-paused.png)
- [QA-NEG-003-result.json](QA-NEG-003-result.json)
- [QA-NEG-003-result.png](QA-NEG-003-result.png)

Shared seed/API evidence: [seed-output.json](seed-output.json). Browser console/network: files prefixed with scenario ID or final-console/final-network.

Execution-integrity caveat: this scenario’s observed assertions passed, but overall verdict is FAIL because the worktree HEAD/fingerprint changed externally. See [integrity-check.json](integrity-check.json).

Shared runtime evidence: [timestamped network](browser-network-timestamped.json), [timestamped console](browser-console-timestamped.json), [full MCP network](final-network.log), [full MCP console](final-console.log).

Copied read-only server evidence: [list.log](logs-blocked/list.log), [detail.log](logs-blocked/detail.log), [queue dump](logs-blocked/queue-dump.json), [queue SQLite backup](logs-blocked/queue.sqlite), [report](logs-blocked/report.json), [worker state](logs-blocked/worker_state.json), [inspected hook](qa-hook-inspected.py). detail.log is empty; list.log contains the snapshot ID. No claim of external packet capture is made; absence assertion uses these approved records plus browser requests and the network-free QA hook.
