# QA-NEG-004 — PASS

UTC: 2026-10-20T13:39:32.265Z

URL: http://localhost:3010/pipeline/crawling

Steps: Direct PUT videos_per_keyword=0.

Expected: 422 invalid_request.

Actual: {"http":422,"body":{"status":"error","error":{"kind":"validation","code":"invalid_request","message":"Invalid crawl request"}}}

Evidence: [settings-negative-boundary.json](settings-negative-boundary.json)

Screenshots: /Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/neg001.png, /Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/edge004.png

DOM, API responses, console and network details are retained in the evidence JSON. Screenshots inspected separately before final acceptance.

Approved plan (verbatim):

```
QA-NEG-004
Priority: P2
Type: Negative / API
Given: QA 세션
When: PUT /crawl/{sid}/config에 `youtube_vlog: {"videos_per_keyword": 0}`을 보낸다
Then:
  - 422 응답과 `error.code: "invalid_request"`가 온다
```

Additional evidence:

- [Browser console](browser-console.log): no errors; CSS preload and logo aspect-ratio warnings observed.
- [Accumulated browser requests and console](browser-final-audit.json)
- [Final source integrity](integrity-after.json)
- [Screenshot inspection record](visual-inspection.md)
