# QA-REG-002 — PASS

Updated: 2026-10-20T13:32:23.423661+00:00

URL: http://localhost:3010/pipeline/crawling

Approved steps and expected:
```
QA-REG-002
Priority: P1
Type: Regression
Given: 설정 화면
When: "유튜브 댓글"을 켜고 고급 설정을 연다
Then:
  - "키워드당 영상 수", "영상당 최대 댓글" 칸이 기존대로 보인다
  - 기존 채널(네이버 카페 · 블로그 · 뽐뿌 · 클리앙)의 동시성 · 요청 간격 기본값이 바뀌지 않았다(블로그 1 · 0.5)
```

Actual execution and observations:
Enabled 유튜브 댓글 and old channels; expanded advanced settings. YouTube fields 키워드당 영상 수20 and 영상당 최대 댓글500 visible. Cafe/blog/ppomppu/clien default concurrency1 and interval0.5 each (blog1/0.5 as specified). Changes discarded before empty-case run.

Evidence:
- [QA-REG-002-browser.json](QA-REG-002-browser.json)
- [QA-REG-002.png](QA-REG-002.png)

Shared seed/API evidence: [seed-output.json](seed-output.json). Browser console/network: files prefixed with scenario ID or final-console/final-network.

Execution-integrity caveat: this scenario’s observed assertions passed, but overall verdict is FAIL because the worktree HEAD/fingerprint changed externally. See [integrity-check.json](integrity-check.json).

Shared runtime evidence: [timestamped network](browser-network-timestamped.json), [timestamped console](browser-console-timestamped.json), [full MCP network](final-network.log), [full MCP console](final-console.log).
