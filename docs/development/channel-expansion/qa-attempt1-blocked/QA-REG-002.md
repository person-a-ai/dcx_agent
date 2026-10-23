# QA-REG-002 — BLOCKED

Recorded: 2026-10-20T06:29:08.569101+00:00
Shared preflight interval: 2026-10-20T06:26:59.366893+00:00 – 2026-10-20T06:27:05.061306+00:00.
Intended URL: http://localhost:3000/pipeline/crawling
Session: unavailable (seed failed); no scenario actions were performed.

## Approved scenario (unmodified)

Priority: P1
Type: Regression
Given: 설정 화면
When: "유튜브 댓글"을 켜고 고급 설정을 연다
Then:
  - "키워드당 영상 수", "영상당 최대 댓글" 칸이 기존대로 보인다
  - 기존 채널(네이버 카페 · 블로그 · 뽐뿌 · 클리앙)의 동시성 · 요청 간격 기본값이 바뀌지 않았다(블로그 1 · 0.5)

## Attempted steps and actual result

1. Confirmed immutable HEAD and source fingerprint; read the full approved plan.
2. Started mandatory backend using QA adapter/fake embedding environment.
3. Observed startup followed by EPERM on localhost:8000 and process shutdown.
4. Opened the crawling URL in the actual isolated Chrome browser; observed connection refused.
5. Executed seed.py against the real POST /context endpoint; connection was denied.
6. Stopped at the unmet Given preconditions. No Then assertion is marked passed.

BLOCKED by environment before scenario execution. Uvicorn initialized but exited with code 3: [Errno 1] binding 127.0.0.1:8000: operation not permitted. A second captured attempt with fresh LOCAL_DATA_DIR reproduced the error. Playwright navigation to http://localhost:3000/pipeline/crawling returned net::ERR_CONNECTION_REFUSED. Seed POST /context failed with PermissionError (operation not permitted). No session ID or application DOM was available. Final HEAD also changed externally from f22e495fa7946d5d5d18b6283049b62de95bf71a to 4e29b449cb00ff6f942b84efedf52154762a040a; source fingerprint is unchanged.

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
