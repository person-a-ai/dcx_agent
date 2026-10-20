# QA-NEG-002 — PASS

URL: http://localhost:3001/pipeline/crawling

UTC time: 2026-10-20 07:42:46Z

Browser: isolated headed Chrome, Playwright MCP; dispatch01a1583f-bc1a-7ba2-af7a-590ba8288a20. See preflight.md for server substitutions and integrity failure.

## Steps

Use3001→8001 instead of restart; inspect UI/status; PUT threads config.

## Expected

- "Threads" 행에 "사용 불가" 배지가 보인다
  - "Threads" 행에 "Crawl4AI 브라우저가 설치돼 있지 않아 사용할 수 없습니다." 문구가 보인다
  - "Threads" 스위치가 비활성화돼 있다
  - GET /crawl/{sid}/status의 `available_sources`에 `threads`가 없다
  - `threads`를 포함한 설정을 PUT /crawl/{sid}/config로 보내면 422와 `error.code: "sources_unavailable"`이 온다

## Actual

Threads unavailable badge and exact Crawl4AI missing-browser sentence; switch disabled; available_sources excludes threads; PUT422 sources_unavailable.

## Evidence

- [unavailable-data.json](unavailable-data.json) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/unavailable-data.json`
- [QA-NEG-002.png](QA-NEG-002.png) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-NEG-002.png`

Console/network: [console-main.log](console-main.log), [network-main.log](network-main.log). Case JSON contains DOM/API output; blocked and sample cases include dedicated network/console arrays. Screenshots saved to explicit absolute paths and visually inspected; fullPage may capture only the internal scroll-container viewport. DOM/API records support offscreen values. No inherited verdict used.
