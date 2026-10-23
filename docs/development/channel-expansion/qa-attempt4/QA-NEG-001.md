# QA-NEG-001 — PASS

Tested HEAD: `8d99f5323e800a0860f363751c783a4551b69714`. Source fingerprint: `3bae4a00deb67d67b3ed5f9ab6c8a9907a2795857b93e93c8e9ab9700c5731fc`.

URL: http://localhost:3010/pipeline/crawling

Session: `s33a213de835b40fb8085e04e41d7e104`. Capture timestamps (UTC): 2026-10-20T09:18:31.887Z.

## Approved Given / When / Then

```text
Priority: P1
Type: Negative
Given: 설정 화면에서 "유튜브 브이로그"가 켜져 있다
When: 최소 길이 30, 최대 길이 10을 입력한다
Then:
  - "저장" 버튼과 "목록 수집 시작" 버튼이 비활성화된다
  - PUT /crawl/{sid}/config에 `youtube_vlog: {"min_duration_s": 1800, "max_duration_s": 600}`을 직접 보내면 422 응답과 `error.code: "invalid_request"`가 온다
  - GET /session/{sid}의 `crawlConfig.youtube_vlog`는 이전 저장값 그대로다
```

## Executed steps

In enabled vlog settings set minimum 30 and maximum 10. Inspect disabled controls; directly PUT minimum 1800 / maximum 600; compare saved settings before and after.

## Expected versus actual

| Expected (unchanged plan) | Actual |
|---|---|
| "저장" 버튼과 "목록 수집 시작" 버튼이 비활성화된다 | saveDisabled=true and startDisabled=true. |
| PUT /crawl/{sid}/config에 `youtube_vlog: {"min_duration_s": 1800, "max_duration_s": 600}`을 직접 보내면 422 응답과 `error.code: "invalid_request"`가 온다 | PUT returns HTTP 422, error.code=invalid_request. |
| GET /session/{sid}의 `crawlConfig.youtube_vlog`는 이전 저장값 그대로다 | Before and after saved config both equal 5 / 120 / 1800. |

## Evidence

- [QA-NEG-001-final.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-NEG-001-final.json) — DOM, API output, timestamps and/or recorded tool result.
- [QA-NEG-001-final.png](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-NEG-001-final.png) — screenshot saved at the explicit absolute path shown in this link.

Console/network: [console-network.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/console-network.json); original per-capture `events` arrays are retained. No captured console error or pageerror; development warnings include logo aspect ratio and unused CSS preload. Direct API validations are preserved in the listed response JSONs (browser page request events do not include every APIRequestContext call).

Preserved tool-error captures: [QA-NEG-001-verified.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-NEG-001-verified.json), [QA-NEG-001.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-NEG-001.json). These are not treated as passing assertions.
