# QA-NEG-004 — PASS

Updated: 2026-10-20T13:32:23.421905+00:00

URL: http://localhost:3010/pipeline/crawling

Approved steps and expected:
```
QA-NEG-004
Priority: P2
Type: Negative / API
Given: QA 세션
When: PUT /crawl/{sid}/config에 `youtube_vlog: {"videos_per_keyword": 0}`을 보낸다
Then:
  - 422 응답과 `error.code: "invalid_request"`가 온다
```

Actual execution and observations:
Direct PUT youtube_vlog videos_per_keyword=0 returned HTTP422 error.code invalid_request.

Evidence:
- [QA-NEG-004-browser.json](QA-NEG-004-browser.json)

Shared seed/API evidence: [seed-output.json](seed-output.json). Browser console/network: files prefixed with scenario ID or final-console/final-network.

Execution-integrity caveat: this scenario’s observed assertions passed, but overall verdict is FAIL because the worktree HEAD/fingerprint changed externally. See [integrity-check.json](integrity-check.json).

Shared runtime evidence: [timestamped network](browser-network-timestamped.json), [timestamped console](browser-console-timestamped.json), [full MCP network](final-network.log), [full MCP console](final-console.log).
