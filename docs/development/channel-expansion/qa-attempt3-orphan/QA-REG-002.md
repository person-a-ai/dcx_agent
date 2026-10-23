# QA-REG-002 — PASS

URL: http://localhost:3000/pipeline/crawling

UTC time: 2026-10-20 07:41:30Z

Browser: isolated headed Chrome, Playwright MCP; dispatch01a1583f-bc1a-7ba2-af7a-590ba8288a20. See preflight.md for server substitutions and integrity failure.

## Steps

Enable old channels, inspect advanced settings/default values; reload without saving toggles.

## Expected

- "키워드당 영상 수", "영상당 최대 댓글" 칸이 기존대로 보인다
  - 기존 채널(네이버 카페 · 블로그 · 뽐뿌 · 클리앙)의 동시성 · 요청 간격 기본값이 바뀌지 않았다(블로그 1 · 0.5)

## Actual

Comments video-count/max-comments fields20/500. Cafe/blog/ppomppu/clien concurrency1 and interval0.5; blog1/0.5.

## Evidence

- [settings-data.json](settings-data.json) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/settings-data.json`
- [QA-REG-002.png](QA-REG-002.png) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-REG-002.png`

Console/network: [console-main.log](console-main.log), [network-main.log](network-main.log). Case JSON contains DOM/API output; blocked and sample cases include dedicated network/console arrays. Screenshots saved to explicit absolute paths and visually inspected; fullPage may capture only the internal scroll-container viewport. DOM/API records support offscreen values. No inherited verdict used.
