# QA-NEG-001 — PASS

UTC: 2026-10-20T13:39:32.265Z

URL: http://localhost:3010/pipeline/crawling

Steps: Enter min30/max10; inspect disabled controls; PUT invalid config; GET session.

Expected: Save/start disabled; 422 invalid_request; prior stored vlog config unchanged.

Actual: {"disabled":{"save":true,"start":true},"invalid":{"http":422,"body":{"status":"error","error":{"kind":"validation","code":"invalid_request","message":"Invalid crawl request"}}},"same":true}

Evidence: [settings-negative-boundary.json](settings-negative-boundary.json)

Screenshots: /Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/neg001.png, /Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/edge004.png

DOM, API responses, console and network details are retained in the evidence JSON. Screenshots inspected separately before final acceptance.

Approved plan (verbatim):

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

Additional evidence:

- [Browser console](browser-console.log): no errors; CSS preload and logo aspect-ratio warnings observed.
- [Accumulated browser requests and console](browser-final-audit.json)
- [Final source integrity](integrity-after.json)
- [Screenshot inspection record](visual-inspection.md)
