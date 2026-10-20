# QA-REG-003 — PASS

Updated: 2026-10-20T13:32:23.423904+00:00

URL: http://localhost:3010/pipeline/start

Approved steps and expected:
```
QA-REG-003
Priority: P1
Type: Regression
Given: 새 프로젝트를 0단계(입력)에서 만든다
When: 수집 채널 선택 칸을 연다
Then:
  - 기존 채널 선택지가 그대로 있다
  - 새 채널 4개가 선택지에 보이고, 하나를 골라 저장하면 GET /session/{sid}의 `projectContext.channels`에 그 값이 들어간다
```

Actual execution and observations:
Created brand-new project through stage0 UI: filled product/definition/question, selected 신규기획 and Threads, clicked 저장. Channel chooser contains all old options and four new options. POST context succeeded and GET session confirms projectContext.channels=[threads]. Initial screenshot scroll target detached during post-save rerender; stable group recaptured successfully.

Evidence:
- [QA-REG-003-browser.json](QA-REG-003-browser.json)
- [QA-REG-003-result.json](QA-REG-003-result.json)
- [QA-REG-003.png](QA-REG-003.png)

Shared seed/API evidence: [seed-output.json](seed-output.json). Browser console/network: files prefixed with scenario ID or final-console/final-network.

Execution-integrity caveat: this scenario’s observed assertions passed, but overall verdict is FAIL because the worktree HEAD/fingerprint changed externally. See [integrity-check.json](integrity-check.json).

Shared runtime evidence: [timestamped network](browser-network-timestamped.json), [timestamped console](browser-console-timestamped.json), [full MCP network](final-network.log), [full MCP console](final-console.log).
