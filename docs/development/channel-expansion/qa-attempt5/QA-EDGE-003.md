# QA-EDGE-003 — PASS

Updated: 2026-10-20T13:32:23.422902+00:00

URL: http://localhost:3010/pipeline/crawling

Approved steps and expected:
```
QA-EDGE-003
Priority: P2
Type: Edge / Viewport
Given: 브라우저 폭 375px
When: 설정 화면과 결과 화면을 연다
Then:
  - 문서 가로 스크롤 폭(`document.documentElement.scrollWidth`)이 화면 폭과 같다(표만 자체 가로 스크롤)
  - 새 채널 네 행과 "건너뛴 항목" 표의 모든 열 이름을 가로 스크롤로 볼 수 있다
```

Actual execution and observations:
At375px settings and completed-result document scrollWidth=innerWidth=375. New four rows visible; table region scrollWidth600/client206 scrolls horizontally. Active result on3012: individually scrolled each header 채널,사유,건수 into viewport (left0,193.5,394); all fully visible. Also checked completed E2E005 historical result and settings at1100/1200/1300: document widths equal viewport throughout. Screenshots inspected. A navigation load wait timed out once while rendered UI was ready; continued using DOM readiness.

Evidence:
- [QA-EDGE-003-live-result-375-건수.png](QA-EDGE-003-live-result-375-건수.png)
- [QA-EDGE-003-live-result-375-사유.png](QA-EDGE-003-live-result-375-사유.png)
- [QA-EDGE-003-live-result-375-채널.png](QA-EDGE-003-live-result-375-채널.png)
- [QA-EDGE-003-live-result.json](QA-EDGE-003-live-result.json)
- [QA-EDGE-003-result-1100-left.png](QA-EDGE-003-result-1100-left.png)
- [QA-EDGE-003-result-1100-right.png](QA-EDGE-003-result-1100-right.png)
- [QA-EDGE-003-result-1200-left.png](QA-EDGE-003-result-1200-left.png)
- [QA-EDGE-003-result-1200-right.png](QA-EDGE-003-result-1200-right.png)
- [QA-EDGE-003-result-1300-left.png](QA-EDGE-003-result-1300-left.png)
- [QA-EDGE-003-result-1300-right.png](QA-EDGE-003-result-1300-right.png)
- [QA-EDGE-003-result-375-left.png](QA-EDGE-003-result-375-left.png)
- [QA-EDGE-003-result-375-right.png](QA-EDGE-003-result-375-right.png)
- [QA-EDGE-003-results.json](QA-EDGE-003-results.json)
- [QA-EDGE-003-settings-1100-left.png](QA-EDGE-003-settings-1100-left.png)
- [QA-EDGE-003-settings-1100-right.png](QA-EDGE-003-settings-1100-right.png)
- [QA-EDGE-003-settings-1200-left.png](QA-EDGE-003-settings-1200-left.png)
- [QA-EDGE-003-settings-1200-right.png](QA-EDGE-003-settings-1200-right.png)
- [QA-EDGE-003-settings-1300-left.png](QA-EDGE-003-settings-1300-left.png)
- [QA-EDGE-003-settings-1300-right.png](QA-EDGE-003-settings-1300-right.png)
- [QA-EDGE-003-settings-375-82쿡.png](QA-EDGE-003-settings-375-82쿡.png)
- [QA-EDGE-003-settings-375-Threads.png](QA-EDGE-003-settings-375-Threads.png)
- [QA-EDGE-003-settings-375-left.png](QA-EDGE-003-settings-375-left.png)
- [QA-EDGE-003-settings-375-right.png](QA-EDGE-003-settings-375-right.png)
- [QA-EDGE-003-settings-375-유튜브 브이로그.png](QA-EDGE-003-settings-375-유튜브 브이로그.png)
- [QA-EDGE-003-settings-375-지식iN.png](QA-EDGE-003-settings-375-지식iN.png)
- [QA-EDGE-003-settings.json](QA-EDGE-003-settings.json)

Shared seed/API evidence: [seed-output.json](seed-output.json). Browser console/network: files prefixed with scenario ID or final-console/final-network.

Execution-integrity caveat: this scenario’s observed assertions passed, but overall verdict is FAIL because the worktree HEAD/fingerprint changed externally. See [integrity-check.json](integrity-check.json).

Shared runtime evidence: [timestamped network](browser-network-timestamped.json), [timestamped console](browser-console-timestamped.json), [full MCP network](final-network.log), [full MCP console](final-console.log).
