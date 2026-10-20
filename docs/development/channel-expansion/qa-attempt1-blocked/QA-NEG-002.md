# QA-NEG-002 — BLOCKED

Recorded: 2026-10-20T06:29:08.569101+00:00
Shared preflight interval: 2026-10-20T06:26:59.366893+00:00 – 2026-10-20T06:27:05.061306+00:00.
Intended URL: http://localhost:3000/pipeline/crawling
Session: unavailable (seed failed); no scenario actions were performed.

## Approved scenario (unmodified)

Priority: P1
Type: Negative
Given: 서버를 `PLAYWRIGHT_BROWSERS_PATH=<빈 임시 폴더>`로 다시 띄웠다(Chromium 없음)
When: 설정 화면을 연다
Then:
  - "Threads" 행에 "사용 불가" 배지가 보인다
  - "Threads" 행에 "Crawl4AI 브라우저가 설치돼 있지 않아 사용할 수 없습니다." 문구가 보인다
  - "Threads" 스위치가 비활성화돼 있다
  - GET /crawl/{sid}/status의 `available_sources`에 `threads`가 없다
  - `threads`를 포함한 설정을 PUT /crawl/{sid}/config로 보내면 422와 `error.code: "sources_unavailable"`이 온다

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
