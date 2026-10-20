# QA-NEG-004 — PASS

URL: http://localhost:8000/crawl/s022667b4b6674eef9f3c2747db878043/config

UTC time: 2026-10-20 07:41:30Z

Browser: isolated headed Chrome, Playwright MCP; dispatch01a1583f-bc1a-7ba2-af7a-590ba8288a20. See preflight.md for server substitutions and integrity failure.

## Steps

Direct invalid PUT and inspect response.

## Expected

- 422 응답과 `error.code: "invalid_request"`가 온다

## Actual

PUT videos_per_keyword=0 returned422 invalid_request.

## Evidence

- [settings-data.json](settings-data.json) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/settings-data.json`

Console/network: [console-main.log](console-main.log), [network-main.log](network-main.log). Case JSON contains DOM/API output; blocked and sample cases include dedicated network/console arrays. Screenshots saved to explicit absolute paths and visually inspected; fullPage may capture only the internal scroll-container viewport. DOM/API records support offscreen values. No inherited verdict used.
