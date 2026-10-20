# QA-EDGE-004 — PASS

Updated: 2026-10-20T13:32:23.423152+00:00

URL: http://localhost:3010/pipeline/crawling

Approved steps and expected:
```
QA-EDGE-004
Priority: P2
Type: Edge / Boundary
Given: 설정 화면에서 "유튜브 브이로그"가 켜져 있다
When: 최소 길이 0, 최대 길이 1을 입력해 저장한다
Then:
  - 저장에 성공한다
  - GET /session/{sid}의 `crawlConfig.youtube_vlog`가 `min_duration_s: 0`, `max_duration_s: 60`이다
```

Actual execution and observations:
Entered 0/1 minutes through UI, saved successfully. GET returned min_duration_s=0,max_duration_s=60. Restored 2/30 and saved before E2E list flow.

Evidence:
- [QA-EDGE-004-browser.json](QA-EDGE-004-browser.json)
- [QA-EDGE-004.png](QA-EDGE-004.png)

Shared seed/API evidence: [seed-output.json](seed-output.json). Browser console/network: files prefixed with scenario ID or final-console/final-network.

Execution-integrity caveat: this scenario’s observed assertions passed, but overall verdict is FAIL because the worktree HEAD/fingerprint changed externally. See [integrity-check.json](integrity-check.json).

Shared runtime evidence: [timestamped network](browser-network-timestamped.json), [timestamped console](browser-console-timestamped.json), [full MCP network](final-network.log), [full MCP console](final-console.log).
