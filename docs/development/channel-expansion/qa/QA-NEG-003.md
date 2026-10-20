# QA-NEG-003 — PASS

UTC: 2026-10-20T13:47:19.164Z

URL: http://localhost:3012/pipeline/crawling

Steps: Use 3012/8012 blocked environment instead of restart; Threads-only list then detail; wait for paused banner; finish partial and accept confirmation. Inspect copied worker logs/queue and network.

Expected: Paused banner with Threads badge and exact no-login sentence; finish yields Threads blocked-partial skip row; no threads.com login requests.

Actual: Paused after 20 blocked attempts; confirmed finish; Threads 차단으로 여기까지 마침 50건. Browser login requests zero; copied list.log/detail.log contain no login URLs, queue consists of qa.invalid URLs, network-free QA hook raises AdapterBlocked without login. See logs-blocked/ and qa-hook-inspected.py.

Evidence: [neg003-finished.json](neg003-finished.json)

Screenshots: /Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/neg003-paused.png, /Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/neg003-finish.png

DOM, API responses, console and network details are retained in the evidence JSON. Screenshots inspected separately before final acceptance.

Approved plan (verbatim):

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

Additional evidence:

- [neg003-gate.json](neg003-gate.json)
- [neg003-paused.json](neg003-paused.json)
- [neg003-finish.json](neg003-finish.json)
- [neg003-log-check.json](neg003-log-check.json)
- [logs-blocked/list.log](logs-blocked/list.log)
- [logs-blocked/detail.log](logs-blocked/detail.log)
- [logs-blocked/report.json](logs-blocked/report.json)
- [logs-blocked/worker_state.json](logs-blocked/worker_state.json)
- [logs-blocked/queue-dump.json](logs-blocked/queue-dump.json)
- [qa-hook-inspected.py](qa-hook-inspected.py)
- [Browser console](browser-console.log): no errors; CSS preload and logo aspect-ratio warnings observed.
- [Accumulated browser requests and console](browser-final-audit.json)
- [Final source integrity](integrity-after.json)
- [Screenshot inspection record](visual-inspection.md)
