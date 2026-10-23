# QA-REG-003 — PASS

UTC: 2026-10-20T13:49:47.172Z

URL: http://localhost:3010/pipeline/start

Steps: Start page → new project; fill mandatory fields, inspect channel options, choose vlog, save; GET newly created session.

Expected: Existing and four new options; chosen new channel stored in projectContext.channels.

Actual: {"options":["네이버 카페","네이버 블로그","유튜브","뽐뿌","클리앙","개발용 샘플","유튜브 브이로그","Threads","지식iN","82쿡"],"sid":"s613cb442a2d44c028b33677e27c36556","channels":["youtube_vlog"]}

Evidence: [reg003.json](reg003.json)

Screenshots: /Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/reg003-selected.png

DOM, API responses, console and network details are retained in the evidence JSON. Screenshots inspected separately before final acceptance.

Approved plan (verbatim):

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

Additional evidence:

- [Browser console](browser-console.log): no errors; CSS preload and logo aspect-ratio warnings observed.
- [Accumulated browser requests and console](browser-final-audit.json)
- [Final source integrity](integrity-after.json)
- [Screenshot inspection record](visual-inspection.md)
