# QA-EDGE-004 — PASS

UTC: 2026-10-20T13:39:32.265Z

URL: http://localhost:3010/pipeline/crawling

Steps: Enter min0/max1; save through UI; GET session.

Expected: Save succeeds; min_duration_s 0 and max_duration_s 60.

Actual: {"videos_per_keyword":5,"min_duration_s":0,"max_duration_s":60}

Evidence: [settings-negative-boundary.json](settings-negative-boundary.json)

Screenshots: /Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/neg001.png, /Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/edge004.png

DOM, API responses, console and network details are retained in the evidence JSON. Screenshots inspected separately before final acceptance.

Approved plan (verbatim):

```
QA-EDGE-004
Priority: P2
Type: Edge / Boundary
Given: 설정 화면에서 "유튜브 브이로그"가 켜져 있다
When: 최소 길이 0, 최대 길이 1을 입력해 저장한다
Then:
  - 저장에 성공한다
  - GET /session/{sid}의 `crawlConfig.youtube_vlog`가 `min_duration_s: 0`, `max_duration_s: 60`이다
```

Additional evidence:

- [Browser console](browser-console.log): no errors; CSS preload and logo aspect-ratio warnings observed.
- [Accumulated browser requests and console](browser-final-audit.json)
- [Final source integrity](integrity-after.json)
- [Screenshot inspection record](visual-inspection.md)
