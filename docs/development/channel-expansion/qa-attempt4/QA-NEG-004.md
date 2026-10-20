# QA-NEG-004 — PASS

Tested HEAD: `8d99f5323e800a0860f363751c783a4551b69714`. Source fingerprint: `3bae4a00deb67d67b3ed5f9ab6c8a9907a2795857b93e93c8e9ab9700c5731fc`.

URL: http://localhost:3010/pipeline/crawling

Session: `s33a213de835b40fb8085e04e41d7e104`. Capture timestamps (UTC): 2026-10-20T09:17:38.929Z.

## Approved Given / When / Then

```text
Priority: P2
Type: Negative / API
Given: QA 세션
When: PUT /crawl/{sid}/config에 `youtube_vlog: {"videos_per_keyword": 0}`을 보낸다
Then:
  - 422 응답과 `error.code: "invalid_request"`가 온다
```

## Executed steps

Using the browser request client, directly PUT youtube_vlog.videos_per_keyword=0 to the main session's config API.

## Expected versus actual

| Expected (unchanged plan) | Actual |
|---|---|
| 422 응답과 `error.code: "invalid_request"`가 온다 | HTTP 422 with error.code=invalid_request. |

## Qualifications and preserved attempts

API-only case per the plan. Its response log is the primary evidence; no screenshot is required.

## Evidence

- [QA-NEG-004-verified.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-NEG-004-verified.json) — DOM, API output, timestamps and/or recorded tool result.

Console/network: [console-network.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/console-network.json); original per-capture `events` arrays are retained. No captured console error or pageerror; development warnings include logo aspect ratio and unused CSS preload. Direct API validations are preserved in the listed response JSONs (browser page request events do not include every APIRequestContext call).

Preserved tool-error captures: [QA-NEG-004.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-NEG-004.json). These are not treated as passing assertions.
