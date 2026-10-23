# QA-EDGE-003 — BLOCKED

Recorded: 2026-10-20T06:29:08.569101+00:00
Shared preflight interval: 2026-10-20T06:26:59.366893+00:00 – 2026-10-20T06:27:05.061306+00:00.
Intended URL: http://localhost:3000/pipeline/crawling
Session: unavailable (seed failed); no scenario actions were performed.

## Approved scenario (unmodified)

Priority: P2
Type: Edge / Viewport
Given: 브라우저 폭 375px
When: 설정 화면과 결과 화면을 연다
Then:
  - 문서 가로 스크롤 폭(`document.documentElement.scrollWidth`)이 화면 폭과 같다(표만 자체 가로 스크롤)
  - 새 채널 네 행과 "건너뛴 항목" 표의 모든 열 이름을 가로 스크롤로 볼 수 있다

## Attempted steps and actual result

1. Confirmed immutable HEAD and source fingerprint; read the full approved plan.
2. Started mandatory backend using QA adapter/fake embedding environment.
3. Observed startup followed by EPERM on localhost:8000 and process shutdown.
4. Opened the crawling URL in the actual isolated Chrome browser; observed connection refused.
5. Executed seed.py against the real POST /context endpoint; connection was denied.
6. Stopped at the unmet Given preconditions. No Then assertion is marked passed.

BLOCKED by environment before scenario execution. Uvicorn initialized but exited with code 3: [Errno 1] binding 127.0.0.1:8000: operation not permitted. A second captured attempt with fresh LOCAL_DATA_DIR reproduced the error. Playwright navigation to http://localhost:3000/pipeline/crawling returned net::ERR_CONNECTION_REFUSED. Seed POST /context failed with PermissionError (operation not permitted). No session ID or application DOM was available. Final HEAD also changed externally from f22e495fa7946d5d5d18b6283049b62de95bf71a to 4e29b449cb00ff6f942b84efedf52154762a040a; source fingerprint is unchanged. No 375px application DOM exists; scrollWidth and table scrolling were not tested.

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
