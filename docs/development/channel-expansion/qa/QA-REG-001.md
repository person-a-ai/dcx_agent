# QA-REG-001 — PASS

UTC: 2026-10-20T13:52:08.988Z

URL: http://localhost:3013/pipeline/crawling

Steps: Controller fixture env3013/8013; corpus-confirmed 에어컨 seeded and approved; fixture-only list→gate→detail→result using UI. Initial count locator used inaccessible term name; corrected to observed text filter.

Expected: Collected docs >0; exact no-skipped message; preprocess button.

Actual: 2,000 documents; 건너뛴 항목이 없습니다.; preprocess button visible. See sample-session.json, reg001-gate.json, reg001-start.json and logs-sample/.

Evidence: [reg001-verified.json](reg001-verified.json)

Screenshots: /Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/reg001-result.png, /Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/reg001-preprocess-button.png

DOM, API responses, console and network details are retained in the evidence JSON. Screenshots inspected separately before final acceptance.

Approved plan (verbatim):

```
QA-REG-001
Priority: P0
Type: Regression
Given: 개발용 샘플(fixture) 채널만 켠 세션(`ENABLE_FIXTURE_CHANNEL=true`)
When: 목록 수집 → 게이트 → 상세 수집 → 결과까지 진행한다
Then:
  - 결과 화면 "수집 문서"가 0보다 크다
  - "건너뛴 항목이 없습니다." 문구가 보인다
  - "전처리로 이동하기" 버튼이 보인다
```

Additional evidence:

- [sample-seed.js](sample-seed.js)
- [sample-session.json](sample-session.json)
- [reg001-gate.json](reg001-gate.json)
- [reg001-start.json](reg001-start.json)
- [logs-sample/report.json](logs-sample/report.json)
- [logs-sample/worker_state.json](logs-sample/worker_state.json)
- [logs-sample/queue-dump.json](logs-sample/queue-dump.json)
- [Browser console](browser-console.log): no errors; CSS preload and logo aspect-ratio warnings observed.
- [Accumulated browser requests and console](browser-final-audit.json)
- [Final source integrity](integrity-after.json)
- [Screenshot inspection record](visual-inspection.md)
