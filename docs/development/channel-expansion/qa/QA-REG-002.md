# QA-REG-002 — PASS

UTC: 2026-10-20T13:39:54.906Z

URL: http://localhost:3010/pipeline/crawling

Steps: Enable YouTube comments and four existing channels; inspect advanced settings.

Expected: Videos per keyword and comments per video fields remain; old defaults unchanged, blog 1/0.5.

Actual: {"defaults":[{"name":"네이버 카페","values":["1","0.5","1000"]},{"name":"네이버 블로그","values":["1","0.5","1000"]},{"name":"뽐뿌","values":["1","0.5","1000"]},{"name":"클리앙","values":["1","0.5","1000"]}],"videos":"20","comments":"500"}

Evidence: [reg002.json](reg002.json)

Screenshots: /Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/reg002.png

DOM, API responses, console and network details are retained in the evidence JSON. Screenshots inspected separately before final acceptance.

Approved plan (verbatim):

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

Additional evidence:

- [Browser console](browser-console.log): no errors; CSS preload and logo aspect-ratio warnings observed.
- [Accumulated browser requests and console](browser-final-audit.json)
- [Final source integrity](integrity-after.json)
- [Screenshot inspection record](visual-inspection.md)
