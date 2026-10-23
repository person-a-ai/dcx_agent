# QA-NEG-002 — PASS

Updated: 2026-10-20T13:32:23.421172+00:00

URL: http://localhost:3011/pipeline/crawling

Approved steps and expected:
```
QA-NEG-002
Priority: P1
Type: Negative
Given: 서버를 `PLAYWRIGHT_BROWSERS_PATH=<빈 임시 폴더>`로 다시 띄웠다(Chromium 없음)
When: 설정 화면을 연다
Then:
  - "Threads" 행에 "사용 불가" 배지가 보인다
  - "Threads" 행에 "Crawl4AI 브라우저가 설치돼 있지 않아 사용할 수 없습니다." 문구가 보인다
  - "Threads" 스위치가 비활성화돼 있다
  - GET /crawl/{sid}/status의 `available_sources`에 `threads`가 없다
  - `threads`를 포함한 설정을 PUT /crawl/{sid}/config로 보내면 422와 `error.code: "sources_unavailable"`이 온다
```

Actual execution and observations:
Used controller prestarted 3011→8011 empty-browser-path environment instead of restart. Threads row has 사용 불가 and exact Crawl4AI browser-not-installed copy; switch disabled. API available_sources excludes threads; PUT channels threads returned422 sources_unavailable.

Evidence:
- [QA-NEG-002-browser.json](QA-NEG-002-browser.json)
- [QA-NEG-002.png](QA-NEG-002.png)

Shared seed/API evidence: [seed-output.json](seed-output.json). Browser console/network: files prefixed with scenario ID or final-console/final-network.

Execution-integrity caveat: this scenario’s observed assertions passed, but overall verdict is FAIL because the worktree HEAD/fingerprint changed externally. See [integrity-check.json](integrity-check.json).

Shared runtime evidence: [timestamped network](browser-network-timestamped.json), [timestamped console](browser-console-timestamped.json), [full MCP network](final-network.log), [full MCP console](final-console.log).
