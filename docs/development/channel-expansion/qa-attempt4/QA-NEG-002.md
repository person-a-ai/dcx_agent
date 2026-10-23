# QA-NEG-002 — PASS

Tested HEAD: `8d99f5323e800a0860f363751c783a4551b69714`. Source fingerprint: `3bae4a00deb67d67b3ed5f9ab6c8a9907a2795857b93e93c8e9ab9700c5731fc`.

URL: http://localhost:3011/pipeline/crawling

Session: `s25961c210b644ce0bcab9aca5e3b459d`. Capture timestamps (UTC): 2026-10-20T09:20:49.823Z, 2026-10-20T09:20:50.630Z.

## Approved Given / When / Then

```text
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

## Executed steps

Use controller's 3011→8011 environment in place of the plan's restart (empty PLAYWRIGHT_BROWSERS_PATH). Open settings, inspect Threads, GET status, PUT a configuration containing threads.

## Expected versus actual

| Expected (unchanged plan) | Actual |
|---|---|
| "Threads" 행에 "사용 불가" 배지가 보인다 | Threads has 사용 불가. |
| "Threads" 행에 "Crawl4AI 브라우저가 설치돼 있지 않아 사용할 수 없습니다." 문구가 보인다 | The exact Crawl4AI browser-not-installed message is present. |
| "Threads" 스위치가 비활성화돼 있다 | Threads switch disabled=true. |
| GET /crawl/{sid}/status의 `available_sources`에 `threads`가 없다 | available_sources excludes threads. |
| `threads`를 포함한 설정을 PUT /crawl/{sid}/config로 보내면 422와 `error.code: "sources_unavailable"`이 온다 | PUT returns HTTP 422, error.code=sources_unavailable. |

## Evidence

- [QA-NEG-002-settings.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-NEG-002-settings.json) — DOM, API output, timestamps and/or recorded tool result.
- [QA-NEG-002.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-NEG-002.json) — DOM, API output, timestamps and/or recorded tool result.
- [QA-NEG-002-settings.png](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-NEG-002-settings.png) — screenshot saved at the explicit absolute path shown in this link.
- [QA-NEG-002.png](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-NEG-002.png) — screenshot saved at the explicit absolute path shown in this link.

Console/network: [console-network.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/console-network.json); original per-capture `events` arrays are retained. No captured console error or pageerror; development warnings include logo aspect ratio and unused CSS preload. Direct API validations are preserved in the listed response JSONs (browser page request events do not include every APIRequestContext call).
