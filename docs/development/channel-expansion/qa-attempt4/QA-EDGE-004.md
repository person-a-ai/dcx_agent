# QA-EDGE-004 — PASS

Tested HEAD: `8d99f5323e800a0860f363751c783a4551b69714`. Source fingerprint: `3bae4a00deb67d67b3ed5f9ab6c8a9907a2795857b93e93c8e9ab9700c5731fc`.

URL: http://localhost:3010/pipeline/crawling

Session: `s33a213de835b40fb8085e04e41d7e104`. Capture timestamps (UTC): 2026-10-20T09:18:32.756Z.

## Approved Given / When / Then

```text
Priority: P2
Type: Edge / Boundary
Given: 설정 화면에서 "유튜브 브이로그"가 켜져 있다
When: 최소 길이 0, 최대 길이 1을 입력해 저장한다
Then:
  - 저장에 성공한다
  - GET /session/{sid}의 `crawlConfig.youtube_vlog`가 `min_duration_s: 0`, `max_duration_s: 60`이다
```

## Executed steps

In enabled vlog settings enter minimum 0 and maximum 1, save through the UI, inspect PUT response and GET session.

## Expected versus actual

| Expected (unchanged plan) | Actual |
|---|---|
| 저장에 성공한다 | Save succeeds with HTTP 200 and unchanged/clean UI state. |
| GET /session/{sid}의 `crawlConfig.youtube_vlog`가 `min_duration_s: 0`, `max_duration_s: 60`이다 | Saved min_duration_s=0 and max_duration_s=60. |

## Evidence

- [QA-EDGE-004-final.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-004-final.json) — DOM, API output, timestamps and/or recorded tool result.
- [QA-EDGE-004-final.png](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-004-final.png) — screenshot saved at the explicit absolute path shown in this link.

Console/network: [console-network.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/console-network.json); original per-capture `events` arrays are retained. No captured console error or pageerror; development warnings include logo aspect ratio and unused CSS preload. Direct API validations are preserved in the listed response JSONs (browser page request events do not include every APIRequestContext call).

Preserved tool-error captures: [QA-EDGE-004-verified.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-004-verified.json), [QA-EDGE-004.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-004.json). These are not treated as passing assertions.
