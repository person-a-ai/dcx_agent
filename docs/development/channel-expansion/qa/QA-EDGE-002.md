# QA-EDGE-002 — PASS

UTC: 2026-10-20T13:47:54.071Z

URL: http://localhost:3010/pipeline/crawling

Steps: Created v2 from E2E005-completed v1, opened v1 with version picker. Rechecked disabled state using Playwright isDisabled which includes aria-disabled.

Expected: Past completed version preserves skipped table; write controls absent/disabled.

Actual: Skipped table visible; restart isDisabled=true (aria-disabled=true); pause/recollect absent. Earlier evidence edge002-pass.json incorrectly tested only native .disabled and produced a false QA-script failure; preserved, corrected by live semantics and screenshot. Same actual completed session and version picker used.

Evidence: [edge002-verified.json](edge002-verified.json)

Screenshots: /Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/edge002-verified.png

DOM, API responses, console and network details are retained in the evidence JSON. Screenshots inspected separately before final acceptance.

Approved plan (verbatim):

```
QA-EDGE-002
Priority: P1
Type: Edge / Permission (read-only)
Given: QA-E2E-005가 끝난 세션에서 새 버전을 만들어, 끝난 버전이 과거 버전(열람 전용)이 됐다
When: 과거 버전의 크롤링 화면을 연다
Then:
  - 결과 화면의 "건너뛴 항목" 표가 보인다
  - "일시 정지하기" · "다시 수집" 등 쓰기 버튼이 보이지 않거나 비활성화돼 있다
```

Additional evidence:

- [edge002-create-dialog.json](edge002-create-dialog.json)
- [edge002-new-version.json](edge002-new-version.json)
- [edge002-observed.json](edge002-observed.json)
- [edge002-pass.json](edge002-pass.json)
- [edge002-verified.json](edge002-verified.json)
- [Browser console](browser-console.log): no errors; CSS preload and logo aspect-ratio warnings observed.
- [Accumulated browser requests and console](browser-final-audit.json)
- [Final source integrity](integrity-after.json)
- [Screenshot inspection record](visual-inspection.md)
