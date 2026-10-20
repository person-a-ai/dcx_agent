# QA-REG-001 — PASS

URL: http://localhost:3003/pipeline/crawling

UTC time: 2026-10-20 07:45:01Z–07:45:31Z

Browser: isolated headed Chrome, Playwright MCP; dispatch01a1583f-bc1a-7ba2-af7a-590ba8288a20. See preflight.md for server substitutions and integrity failure.

## Steps

Create fixture-only session on8003 with keyword에어컨; browser3003 list→gate→detail→result. Copied frontend separate from main-worktree edits.

## Expected

- 결과 화면 "수집 문서"가 0보다 크다
  - "건너뛴 항목이 없습니다." 문구가 보인다
  - "전처리로 이동하기" 버튼이 보인다

## Actual

Separate copied-frontend environment completed2000 documents; no-skipped message and preprocessing button; API report matches.

## Evidence

- [sample-data.json](sample-data.json) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/sample-data.json`
- [QA-REG-001-gate-matched.png](QA-REG-001-gate-matched.png) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-REG-001-gate-matched.png`
- [QA-REG-001-success-matched.png](QA-REG-001-success-matched.png) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-REG-001-success-matched.png`

Console/network: [console-main.log](console-main.log), [network-main.log](network-main.log). Case JSON contains DOM/API output; blocked and sample cases include dedicated network/console arrays. Screenshots saved to explicit absolute paths and visually inspected; fullPage may capture only the internal scroll-container viewport. DOM/API records support offscreen values. No inherited verdict used.
