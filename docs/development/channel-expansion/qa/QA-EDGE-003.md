# QA-EDGE-003 — PASS

UTC: 2026-10-20T13:50:46.790Z

URL: http://localhost:3012/pipeline/crawling

Steps: At 375px inspect settings and both completed past/active results; horizontally scroll tables left/middle/right; vertically expose all four new rows. Repeat width measurements/screenshots at 1100/1200/1300.

Expected: Document scrollWidth equals viewport; new channel rows and all skipped-table column labels reachable through table scrolling.

Actual: Document widths 375/1100/1200/1300 exactly match viewport. At 375px table clientWidth206, scrollWidth600; scrollLeft 0/200/394 exposes 채널/사유/건수. Four new settings rows present and viewed. See edge003-settings.json, edge003-result.json, edge003-mobile-new-rows.json and screenshots.

Evidence: [edge003-complete.json](edge003-complete.json)

Screenshots: /Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/edge003-active-result-375-0.png, /Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/edge003-active-result-375-200.png, /Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/edge003-active-result-375-1000.png, /Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/edge003-active-result-1100-0.png, /Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/edge003-active-result-1100-200.png, /Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/edge003-active-result-1100-1000.png, /Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/edge003-active-result-1200-0.png, /Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/edge003-active-result-1200-200.png, /Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/edge003-active-result-1200-1000.png, /Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/edge003-active-result-1300-0.png, /Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/edge003-active-result-1300-200.png, /Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/edge003-active-result-1300-1000.png

DOM, API responses, console and network details are retained in the evidence JSON. Screenshots inspected separately before final acceptance.

Approved plan (verbatim):

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

Additional evidence:

- [edge003-settings.json](edge003-settings.json)
- [edge003-result.json](edge003-result.json)
- [edge003-mobile-new-rows.json](edge003-mobile-new-rows.json)
- [edge003-mobile-four-rows.png](edge003-mobile-four-rows.png)
- [edge003-settings-375-left.png](edge003-settings-375-left.png)
- [edge003-settings-375-right.png](edge003-settings-375-right.png)
- [edge003-active-result-375-0.png](edge003-active-result-375-0.png)
- [edge003-active-result-375-200.png](edge003-active-result-375-200.png)
- [edge003-active-result-375-1000.png](edge003-active-result-375-1000.png)
- [edge003-settings-1100-left.png](edge003-settings-1100-left.png)
- [edge003-settings-1200-left.png](edge003-settings-1200-left.png)
- [edge003-settings-1300-left.png](edge003-settings-1300-left.png)
- [Browser console](browser-console.log): no errors; CSS preload and logo aspect-ratio warnings observed.
- [Accumulated browser requests and console](browser-final-audit.json)
- [Final source integrity](integrity-after.json)
- [Screenshot inspection record](visual-inspection.md)
