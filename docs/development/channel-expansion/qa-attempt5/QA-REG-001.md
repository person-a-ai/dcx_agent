# QA-REG-001 — PASS

Updated: 2026-10-20T13:32:23.423409+00:00

URL: http://localhost:3013/pipeline/crawling

Approved steps and expected:
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

Actual execution and observations:
Used controller sample3013→8013 (qa-data-r5reg001), fixture only. Read corpus and confirmed 에어컨 occurs in2000/2000 rows; created fresh confirmed 에어컨 seed. UI list→gate2000→detail→result succeeded; 수집 문서2000>0, exact 건너뛴 항목이 없습니다., 전처리로 이동하기 present. API docs2000 and no skips.

Evidence:
- [QA-REG-001-corpus-check.json](QA-REG-001-corpus-check.json)
- [QA-REG-001-result.json](QA-REG-001-result.json)
- [QA-REG-001-seed.json](QA-REG-001-seed.json)
- [QA-REG-001.png](QA-REG-001.png)

Shared seed/API evidence: [seed-output.json](seed-output.json). Browser console/network: files prefixed with scenario ID or final-console/final-network.

Execution-integrity caveat: this scenario’s observed assertions passed, but overall verdict is FAIL because the worktree HEAD/fingerprint changed externally. See [integrity-check.json](integrity-check.json).

Shared runtime evidence: [timestamped network](browser-network-timestamped.json), [timestamped console](browser-console-timestamped.json), [full MCP network](final-network.log), [full MCP console](final-console.log).

Collection evidence: [report](logs-sample/report.json), [worker state](logs-sample/worker_state.json), [queue dump](logs-sample/queue-dump.json).
