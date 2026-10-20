# QA-EDGE-004 — PASS

URL: http://localhost:3000/pipeline/crawling

UTC time: 2026-10-20 07:41:30Z

Browser: isolated headed Chrome, Playwright MCP; dispatch01a1583f-bc1a-7ba2-af7a-590ba8288a20. See preflight.md for server substitutions and integrity failure.

## Steps

Fill5/0/1,save,await success,GET session; restore5/2/30.

## Expected

- 저장에 성공한다
  - GET /session/{sid}의 `crawlConfig.youtube_vlog`가 `min_duration_s: 0`, `max_duration_s: 60`이다

## Actual

Saved0/1 minute boundary successfully; GET min_duration_s0,max_duration_s60.

## Evidence

- [settings-data.json](settings-data.json) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/settings-data.json`
- [QA-EDGE-004.png](QA-EDGE-004.png) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-004.png`

Console/network: [console-main.log](console-main.log), [network-main.log](network-main.log). Case JSON contains DOM/API output; blocked and sample cases include dedicated network/console arrays. Screenshots saved to explicit absolute paths and visually inspected; fullPage may capture only the internal scroll-container viewport. DOM/API records support offscreen values. No inherited verdict used.
