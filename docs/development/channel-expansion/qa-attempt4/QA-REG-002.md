# QA-REG-002 — PASS

Tested HEAD: `8d99f5323e800a0860f363751c783a4551b69714`. Source fingerprint: `3bae4a00deb67d67b3ed5f9ab6c8a9907a2795857b93e93c8e9ab9700c5731fc`.

URL: http://localhost:3010/pipeline/crawling

Session: `s33a213de835b40fb8085e04e41d7e104`. Capture timestamps (UTC): 2026-10-20T09:18:51.027Z.

## Approved Given / When / Then

```text
Priority: P1
Type: Regression
Given: 설정 화면
When: "유튜브 댓글"을 켜고 고급 설정을 연다
Then:
  - "키워드당 영상 수", "영상당 최대 댓글" 칸이 기존대로 보인다
  - 기존 채널(네이버 카페 · 블로그 · 뽐뿌 · 클리앙)의 동시성 · 요청 간격 기본값이 바뀌지 않았다(블로그 1 · 0.5)
```

## Executed steps

In settings enable YouTube comments and the four existing text channels. Expand advanced options and inspect the rendered fields/defaults without starting collection.

## Expected versus actual

| Expected (unchanged plan) | Actual |
|---|---|
| "키워드당 영상 수", "영상당 최대 댓글" 칸이 기존대로 보인다 | YouTube comments has 키워드당 영상 수=20 and 영상당 최대 댓글=500. |
| 기존 채널(네이버 카페 · 블로그 · 뽐뿌 · 클리앙)의 동시성 · 요청 간격 기본값이 바뀌지 않았다(블로그 1 · 0.5) | Cafe, blog, ppomppu and clien each display concurrency=1 and request interval=0.5 seconds, including blog 1 / 0.5. |

## Evidence

- [QA-REG-002.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-REG-002.json) — DOM, API output, timestamps and/or recorded tool result.
- [QA-REG-002.png](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-REG-002.png) — screenshot saved at the explicit absolute path shown in this link.

Console/network: [console-network.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/console-network.json); original per-capture `events` arrays are retained. No captured console error or pageerror; development warnings include logo aspect ratio and unused CSS preload. Direct API validations are preserved in the listed response JSONs (browser page request events do not include every APIRequestContext call).
