# QA-NEG-001 — PASS

URL: http://localhost:3000/pipeline/crawling

UTC time: 2026-10-20 07:41:30Z

Browser: isolated headed Chrome, Playwright MCP; dispatch01a1583f-bc1a-7ba2-af7a-590ba8288a20. See preflight.md for server substitutions and integrity failure.

## Steps

Enter invalid min/max; inspect buttons; direct invalid PUT; GET before/after.

## Expected

- "저장" 버튼과 "목록 수집 시작" 버튼이 비활성화된다
  - PUT /crawl/{sid}/config에 `youtube_vlog: {"min_duration_s": 1800, "max_duration_s": 600}`을 직접 보내면 422 응답과 `error.code: "invalid_request"`가 온다
  - GET /session/{sid}의 `crawlConfig.youtube_vlog`는 이전 저장값 그대로다

## Actual

30/10 disables Save and list start. PUT422 invalid_request; saved config remains5/120/1800 before and after.

## Evidence

- [settings-data.json](settings-data.json) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/settings-data.json`
- [QA-NEG-001.png](QA-NEG-001.png) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-NEG-001.png`

Console/network: [console-main.log](console-main.log), [network-main.log](network-main.log). Case JSON contains DOM/API output; blocked and sample cases include dedicated network/console arrays. Screenshots saved to explicit absolute paths and visually inspected; fullPage may capture only the internal scroll-container viewport. DOM/API records support offscreen values. No inherited verdict used.
