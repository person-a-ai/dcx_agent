# QA-NEG-002 — PASS

UTC: 2026-10-20T13:45:30.304Z

URL: http://localhost:3011/pipeline/crawling

Steps: Use controller missing-browser environment 3011/8011 instead of restart; open seeded settings; inspect Threads; GET status; PUT channels threads.

Expected: Unavailable badge and exact browser-not-installed message; disabled switch; no threads available; 422 sources_unavailable.

Actual: {"row":"Threads 새 채널 사용 불가\t검색 화면(로그인 없음) · 글 본문 · 키워드당 약 20건\n\nCrawl4AI 브라우저가 설치돼 있지 않아 사용할 수 없습니다.\n\n\t사용 불가\t\nThreads 사용하기","disabled":true,"available":["naver_blog","naver_cafe","naver_kin","cook82","youtube","youtube_vlog","clien","ppomppu"],"put":{"http":422,"body":{"status":"error","error":{"kind":"validation","code":"sources_unavailable","message":"Sources are unavailable"}}}}

Evidence: [neg002.json](neg002.json)

Screenshots: /Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/neg002.png

DOM, API responses, console and network details are retained in the evidence JSON. Screenshots inspected separately before final acceptance.

Approved plan (verbatim):

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

Additional evidence:

- [controller-launcher-inspected.sh](controller-launcher-inspected.sh)
- [Browser console](browser-console.log): no errors; CSS preload and logo aspect-ratio warnings observed.
- [Accumulated browser requests and console](browser-final-audit.json)
- [Final source integrity](integrity-after.json)
- [Screenshot inspection record](visual-inspection.md)
