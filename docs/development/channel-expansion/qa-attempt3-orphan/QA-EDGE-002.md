# QA-EDGE-002 — FAIL

URL: http://localhost:3000/pipeline/crawling

UTC time: 2026-10-20 07:46:49Z–07:49:23Z

Browser: isolated headed Chrome, Playwright MCP; dispatch01a1583f-bc1a-7ba2-af7a-590ba8288a20. See preflight.md for server substitutions and integrity failure.

## Steps

Completedv1→이 단계부터 다시→새 버전 만들기→version picker→v1. Result-heading wait timed out; actual DOM shows 저장된 수집 설정을 확인합니다 and no skipped table.

## Expected

- 결과 화면의 "건너뛴 항목" 표가 보인다
  - "일시 정지하기" · "다시 수집" 등 쓰기 버튼이 보이지 않거나 비활성화돼 있다

## Actual

After creatingv2(201), opening read-onlyv1 shows saved-settings screen, not the result/skipped-items table. Writes absent/disabled. Required table assertion fails. Observation followed external source drift; attribution to exact commit requires clean rerun.

## Evidence

- [readonly-data.json](readonly-data.json) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/readonly-data.json`
- [environment-interruption.json](environment-interruption.json) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/environment-interruption.json`
- [QA-EDGE-002-observed.png](QA-EDGE-002-observed.png) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-002-observed.png`
- [integrity-final.json](integrity-final.json) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/integrity-final.json`

Console/network: [console-main.log](console-main.log), [network-main.log](network-main.log). Case JSON contains DOM/API output; blocked and sample cases include dedicated network/console arrays. Screenshots saved to explicit absolute paths and visually inspected; fullPage may capture only the internal scroll-container viewport. DOM/API records support offscreen values. No inherited verdict used.
