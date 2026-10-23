# QA-EDGE-003 — BLOCKED

URL: http://localhost:3000/pipeline/crawling

UTC time: 2026-10-20 07:41:31Z–07:46:05Z

Browser: isolated headed Chrome, Playwright MCP; dispatch01a1583f-bc1a-7ba2-af7a-590ba8288a20. See preflight.md for server substitutions and integrity failure.

## Steps

Resize375×812; measure document/table; scroll target tables and capture endpoints/headers. Earlier screenshots and later sweep are separately timestamped.

## Expected

- 문서 가로 스크롤 폭(`document.documentElement.scrollWidth`)이 화면 폭과 같다(표만 자체 가로 스크롤)
  - 새 채널 네 행과 "건너뛴 항목" 표의 모든 열 이름을 가로 스크롤로 볼 수 있다

## Actual

Before drift, settings/results both document scrollWidth=innerWidth=375; table overflow:auto, scrollWidth600/clientWidth206, actual scrollLeft394. Result headers exposed by horizontal scrolling. Comprehensive settings-header sweep occurred only after drift, so full exact-commit assertion incomplete.

## Evidence

- [settings-data.json](settings-data.json) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/settings-data.json`
- [mobile-result.json](mobile-result.json) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/mobile-result.json`
- [empty-mobile.json](empty-mobile.json) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/empty-mobile.json`
- [QA-EDGE-003-settings.png](QA-EDGE-003-settings.png) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-003-settings.png`
- [QA-EDGE-003-settings-scrolled.png](QA-EDGE-003-settings-scrolled.png) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-003-settings-scrolled.png`
- [QA-EDGE-003-result-0.png](QA-EDGE-003-result-0.png) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-003-result-0.png`
- [QA-EDGE-003-result-150.png](QA-EDGE-003-result-150.png) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-003-result-150.png`
- [QA-EDGE-003-result-1000.png](QA-EDGE-003-result-1000.png) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-003-result-1000.png`
- [QA-EDGE-003-settings-0.png](QA-EDGE-003-settings-0.png) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-003-settings-0.png`
- [QA-EDGE-003-settings-150.png](QA-EDGE-003-settings-150.png) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-003-settings-150.png`
- [QA-EDGE-003-settings-300.png](QA-EDGE-003-settings-300.png) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-003-settings-300.png`
- [QA-EDGE-003-settings-1000.png](QA-EDGE-003-settings-1000.png) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-003-settings-1000.png`

Console/network: [console-main.log](console-main.log), [network-main.log](network-main.log). Case JSON contains DOM/API output; blocked and sample cases include dedicated network/console arrays. Screenshots saved to explicit absolute paths and visually inspected; fullPage may capture only the internal scroll-container viewport. DOM/API records support offscreen values. No inherited verdict used.
