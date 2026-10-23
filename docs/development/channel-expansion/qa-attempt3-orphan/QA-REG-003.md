# QA-REG-003 — BLOCKED

URL: http://localhost:3000/pipeline/start

UTC time: 2026-10-20 07:48Z–07:49Z

Browser: isolated headed Chrome, Playwright MCP; dispatch01a1583f-bc1a-7ba2-af7a-590ba8288a20. See preflight.md for server substitutions and integrity failure.

## Steps

Open fresh isolated start context; inspect form/channel choices. Stop dependent save when immutable source and server prerequisites fail.

## Expected

- 기존 채널 선택지가 그대로 있다
  - 새 채널 4개가 선택지에 보이고, 하나를 골라 저장하면 GET /session/{sid}의 `projectContext.channels`에 그 값이 들어간다

## Actual

Fresh project form exposes all existing and four new choices. Navigation load wait timed out but DOM rendered. Source drift and backend connection refusal prevented channel-selection/save/GET verification.

## Evidence

- [environment-interruption.json](environment-interruption.json) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/environment-interruption.json`
- [QA-REG-003-before-save.png](QA-REG-003-before-save.png) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-REG-003-before-save.png`
- [integrity-final.json](integrity-final.json) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/integrity-final.json`

Console/network: [console-main.log](console-main.log), [network-main.log](network-main.log). Case JSON contains DOM/API output; blocked and sample cases include dedicated network/console arrays. Screenshots saved to explicit absolute paths and visually inspected; fullPage may capture only the internal scroll-container viewport. DOM/API records support offscreen values. No inherited verdict used.
