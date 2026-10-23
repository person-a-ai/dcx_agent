# QA-REG-003 — PASS

Tested HEAD: `8d99f5323e800a0860f363751c783a4551b69714`. Source fingerprint: `3bae4a00deb67d67b3ed5f9ab6c8a9907a2795857b93e93c8e9ab9700c5731fc`.

URL: http://localhost:3010/pipeline/start

Session: `s34aa9438fe6e422680df508378cc6b79`. Capture timestamps (UTC): 2026-10-20T09:12:54.460Z, 2026-10-20T09:13:26.847Z.

## Approved Given / When / Then

```text
Priority: P1
Type: Regression
Given: 새 프로젝트를 0단계(입력)에서 만든다
When: 수집 채널 선택 칸을 연다
Then:
  - 기존 채널 선택지가 그대로 있다
  - 새 채널 4개가 선택지에 보이고, 하나를 골라 저장하면 GET /session/{sid}의 `projectContext.channels`에 그 값이 들어간다
```

## Executed steps

Create a new project through stage0. Inspect channel choices, select 유튜브 브이로그, save, then GET the resulting session.

## Expected versus actual

| Expected (unchanged plan) | Actual |
|---|---|
| 기존 채널 선택지가 그대로 있다 | Existing choices remain (cafe, blog, YouTube, ppomppu, clien; fixture also visible). |
| 새 채널 4개가 선택지에 보이고, 하나를 골라 저장하면 GET /session/{sid}의 `projectContext.channels`에 그 값이 들어간다 | All four new choices appear; saved projectContext.channels contains youtube_vlog. |

## Evidence

- [QA-REG-003-input.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-REG-003-input.json) — DOM, API output, timestamps and/or recorded tool result.
- [QA-REG-003.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-REG-003.json) — DOM, API output, timestamps and/or recorded tool result.
- [QA-REG-003-input.png](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-REG-003-input.png) — screenshot saved at the explicit absolute path shown in this link.
- [QA-REG-003.png](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-REG-003.png) — screenshot saved at the explicit absolute path shown in this link.

Console/network: [console-network.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/console-network.json); original per-capture `events` arrays are retained. No captured console error or pageerror; development warnings include logo aspect ratio and unused CSS preload. Direct API validations are preserved in the listed response JSONs (browser page request events do not include every APIRequestContext call).
