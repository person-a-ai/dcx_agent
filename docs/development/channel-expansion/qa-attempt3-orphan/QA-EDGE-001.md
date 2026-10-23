# QA-EDGE-001 — BLOCKED

URL: http://localhost:3000/pipeline/crawling

UTC time: 2026-10-20 07:46:15Z

Browser: isolated headed Chrome, Playwright MCP; dispatch01a1583f-bc1a-7ba2-af7a-590ba8288a20. See preflight.md for server substitutions and integrity failure.

## Steps

Open separate qa-empty-only session; start list; wait for gate and inspect DOM/status.

## Expected

- 게이트 화면 인사이트에 "수집된 목록이 없습니다"가 보인다
  - 상세 수집 예상 대상 URL이 0이다
  - 화면에 오류 배너가 없다

## Actual

Observed empty-list notice,0 estimated URLs,no error banner. Execution07:46Z occurred after external source modifications; cannot accept against immutable99606c7.

## Evidence

- [empty-mobile.json](empty-mobile.json) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/empty-mobile.json`
- [QA-EDGE-001.png](QA-EDGE-001.png) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-001.png`
- [integrity-final.json](integrity-final.json) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/integrity-final.json`

Console/network: [console-main.log](console-main.log), [network-main.log](network-main.log). Case JSON contains DOM/API output; blocked and sample cases include dedicated network/console arrays. Screenshots saved to explicit absolute paths and visually inspected; fullPage may capture only the internal scroll-container viewport. DOM/API records support offscreen values. No inherited verdict used.
