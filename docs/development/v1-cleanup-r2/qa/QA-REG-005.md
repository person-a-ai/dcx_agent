# QA-REG-005 — PASS

- URL: http://localhost:3411/pipeline/crawling
- Tested HEAD: `5de8f30bbb05986afa4b5ccf579d3d0442302857`
- Executor: codex / browser-qa; thread `01a15844-a762-7910-97e2-9d33167a6188`.
- Recorded UTC interval: 2026-10-20T07:53:10.272Z → 2026-10-20T07:53:13.239Z.

## Expected

Legacy crawling retains the existing 0–2-stage editing restriction banner.

## Steps

1. Keep QA 옛 세션 selected after legacy gate cases.
2. Directly navigate to crawling and inspect rendered banner.

## Actual

Exact legacy editing restriction remained visible.

- PASS — existing banner

## Evidence

- [legacy.json](legacy.json)
- [all-events.json](all-events.json)
- [QA-REG-005.png](QA-REG-005.png) — absolute-path capture, existence verified, visually inspected.

## Console / network / API

Page errors: 0; console error messages: 0.

Complete timestamped request/response bodies and console locations are in the linked JSON. Relevant observed HTTP/error entries:

```text
2026-10-20T07:53:10.318Z HTTP 200 http://localhost:8411/sessions
2026-10-20T07:53:10.327Z HTTP 200 http://localhost:8411/sessions
2026-10-20T07:53:12.942Z HTTP 200 http://localhost:8411/integrations
2026-10-20T07:53:12.951Z HTTP 200 http://localhost:8411/session/qaold
2026-10-20T07:53:13.071Z HTTP 200 http://localhost:8411/known/qaold
2026-10-20T07:53:13.073Z HTTP 200 http://localhost:8411/integrations
2026-10-20T07:53:13.094Z HTTP 200 http://localhost:8411/known/qaold
2026-10-20T07:53:13.101Z HTTP 200 http://localhost:8411/sessions
2026-10-20T07:53:13.122Z HTTP 200 http://localhost:8411/sessions
```

## Captured state / API output

```json
{
  "time": "2026-10-20T07:53:13.239Z",
  "url": "http://localhost:3411/pipeline/crawling",
  "body": "구버전 세션은 0~2단계를 편집할 수 없습니다. 3단계 이후 화면에서 결과를 확인하세요.\n전처리 화면으로"
}
```
