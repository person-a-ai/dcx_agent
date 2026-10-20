# QA-EDGE-002 — PASS

Updated: 2026-10-20T13:32:23.422567+00:00

URL: http://localhost:3010/pipeline/crawling

Approved steps and expected:
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

Actual execution and observations:
Used exact completed E2E005 session s4ba0a06a93c4421ead4816e9a01b2b75. From crawling clicked 이 단계부터 다시 → 새 버전 만들기, created v2 from v1, then opened v1 using version picker. Read-only v1 displays 건너뛴 항목 and both saved skip rows, 90 docs. No pause/recollect/save/start collection controls. API versions marks v1 readonly and v2 active; network report?version=v1 recorded.

Evidence:
- [QA-EDGE-002-browser.json](QA-EDGE-002-browser.json)
- [QA-EDGE-002-saved-result-table.png](QA-EDGE-002-saved-result-table.png)
- [QA-EDGE-002.png](QA-EDGE-002.png)

Shared seed/API evidence: [seed-output.json](seed-output.json). Browser console/network: files prefixed with scenario ID or final-console/final-network.

Execution-integrity caveat: this scenario’s observed assertions passed, but overall verdict is FAIL because the worktree HEAD/fingerprint changed externally. See [integrity-check.json](integrity-check.json).

Shared runtime evidence: [timestamped network](browser-network-timestamped.json), [timestamped console](browser-console-timestamped.json), [full MCP network](final-network.log), [full MCP console](final-console.log).
