# QA-NEG-001 — PASS

Updated: 2026-10-20T13:32:23.420895+00:00

URL: http://localhost:3010/pipeline/crawling

Approved steps and expected:
```
QA-NEG-001
Priority: P1
Type: Negative
Given: 설정 화면에서 "유튜브 브이로그"가 켜져 있다
When: 최소 길이 30, 최대 길이 10을 입력한다
Then:
  - "저장" 버튼과 "목록 수집 시작" 버튼이 비활성화된다
  - PUT /crawl/{sid}/config에 `youtube_vlog: {"min_duration_s": 1800, "max_duration_s": 600}`을 직접 보내면 422 응답과 `error.code: "invalid_request"`가 온다
  - GET /session/{sid}의 `crawlConfig.youtube_vlog`는 이전 저장값 그대로다
```

Actual execution and observations:
Entered min=30,max=10. Save and list-start disabled. Direct PUT returned HTTP422 invalid_request. GET youtube_vlog before/after identical (5,120,1800).

Evidence:
- [QA-NEG-001-browser.json](QA-NEG-001-browser.json)
- [QA-NEG-001.png](QA-NEG-001.png)

Shared seed/API evidence: [seed-output.json](seed-output.json). Browser console/network: files prefixed with scenario ID or final-console/final-network.

Execution-integrity caveat: this scenario’s observed assertions passed, but overall verdict is FAIL because the worktree HEAD/fingerprint changed externally. See [integrity-check.json](integrity-check.json).

Shared runtime evidence: [timestamped network](browser-network-timestamped.json), [timestamped console](browser-console-timestamped.json), [full MCP network](final-network.log), [full MCP console](final-console.log).
