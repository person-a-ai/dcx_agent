# QA-NEG-003 — PASS

URL: http://localhost:3002/pipeline/crawling

UTC time: 2026-10-20 07:42:46Z–07:44:07Z

Browser: isolated headed Chrome, Playwright MCP; dispatch01a1583f-bc1a-7ba2-af7a-590ba8288a20. See preflight.md for server substitutions and integrity failure.

## Steps

Use3002→8002 instead of restart; list→detail; preserve initial30-second timeout; wait for actual pause after20 blocked attempts; finish and accept confirm; inspect result/logs/network.

## Expected

- 멈춤 배너 "수집이 멈췄습니다"가 보인다
  - 배너에 "Threads" 배지가 보인다
  - 배너에 "Threads가 로그인 화면을 보여 주어 멈췄습니다. 로그인은 시도하지 않습니다." 문구가 보인다
  - "여기까지로 마치기" 후 결과 화면 "건너뛴 항목" 표에 "Threads · 차단으로 여기까지 마침" 행이 있다
  - 서버 로그와 네트워크 기록에 threads.com 로그인 주소 요청이 없다

## Actual

Required paused banner/Threads badge/no-login sentence. Accepted finish-partial confirm; result Threads/차단으로 여기까지 마침/50건. Browser network and copied worker logs contain no Threads login request. Logs are sparse(detail.log empty,list.log snapshot only); this is the approved network-free hook, not a real-site trace.

## Evidence

- [blocked-data.json](blocked-data.json) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/blocked-data.json`
- [blocked-paused.json](blocked-paused.json) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/blocked-paused.json`
- [blocked-final.json](blocked-final.json) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/blocked-final.json`
- [QA-NEG-003-paused.png](QA-NEG-003-paused.png) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-NEG-003-paused.png`
- [QA-NEG-003-result.png](QA-NEG-003-result.png) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-NEG-003-result.png`
- [server-logs/neg003/list.log](server-logs/neg003/list.log) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/server-logs/neg003/list.log`
- [server-logs/neg003/detail.log](server-logs/neg003/detail.log) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/server-logs/neg003/detail.log`
- [server-logs/neg003/queue-export.json](server-logs/neg003/queue-export.json) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/server-logs/neg003/queue-export.json`
- [server-logs/neg003/report.json](server-logs/neg003/report.json) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/server-logs/neg003/report.json`

Console/network: [console-main.log](console-main.log), [network-main.log](network-main.log). Case JSON contains DOM/API output; blocked and sample cases include dedicated network/console arrays. Screenshots saved to explicit absolute paths and visually inspected; fullPage may capture only the internal scroll-container viewport. DOM/API records support offscreen values. No inherited verdict used.
