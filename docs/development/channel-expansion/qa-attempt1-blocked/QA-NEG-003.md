# QA-NEG-003 — BLOCKED

Recorded: 2026-10-20T06:29:08.569101+00:00
Shared preflight interval: 2026-10-20T06:26:59.366893+00:00 – 2026-10-20T06:27:05.061306+00:00.
Intended URL: http://localhost:3000/pipeline/crawling
Session: unavailable (seed failed); no scenario actions were performed.

## Approved scenario (unmodified)

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

## Attempted steps and actual result

1. Confirmed immutable HEAD and source fingerprint; read the full approved plan.
2. Started mandatory backend using QA adapter/fake embedding environment.
3. Observed startup followed by EPERM on localhost:8000 and process shutdown.
4. Opened the crawling URL in the actual isolated Chrome browser; observed connection refused.
5. Executed seed.py against the real POST /context endpoint; connection was denied.
6. Stopped at the unmet Given preconditions. No Then assertion is marked passed.

BLOCKED by environment before scenario execution. Uvicorn initialized but exited with code 3: [Errno 1] binding 127.0.0.1:8000: operation not permitted. A second captured attempt with fresh LOCAL_DATA_DIR reproduced the error. Playwright navigation to http://localhost:3000/pipeline/crawling returned net::ERR_CONNECTION_REFUSED. Seed POST /context failed with PermissionError (operation not permitted). No session ID or application DOM was available. Final HEAD also changed externally from f22e495fa7946d5d5d18b6283049b62de95bf71a to 4e29b449cb00ff6f942b84efedf52154762a040a; source fingerprint is unchanged. Variant server was not started after the baseline bind failure; variant-specific assertions are untested.

## Evidence

Common preflight: [preflight.md](preflight.md).
Startup/API: [backend-preflight.log](backend-preflight.log),
[runtime.json](runtime.json), [seed-attempt.log](seed-attempt.log).
Browser DOM: [preflight-browser.md](preflight-browser.md).
Screenshot: `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/preflight-browser.png` (saved and inspected).
Network/console: [preflight-network.log](preflight-network.log),
[preflight-console.log](preflight-console.log).

The shared screenshot shows a connection error, not this scenario's product state.
No scenario-specific screenshot or API response could be produced.
