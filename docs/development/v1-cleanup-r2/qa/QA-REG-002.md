# QA-REG-002 — PASS

- URL: http://localhost:3411/insights
- Tested HEAD: `5de8f30bbb05986afa4b5ccf579d3d0442302857`
- Executor: codex / browser-qa; thread `01a15844-a762-7910-97e2-9d33167a6188`.
- Recorded UTC interval: 2026-10-20T07:51:00.874Z → 2026-10-20T07:51:01.847Z.

## Expected

/insights redirects to /pipeline/insights.

## Steps

1. With completed session selected, navigate directly to /insights.
2. Wait for redirected URL and insight empty-state text.

## Actual

HTTP 307 redirect reached the rendered /pipeline/insights screen.

- PASS — redirect destination
- PASS — rendered

## Evidence

- [chat-success.json](chat-success.json)
- [all-events.json](all-events.json)
- [QA-REG-002.png](QA-REG-002.png) — absolute-path capture, existence verified, visually inspected.

## Console / network / API

Page errors: 0; console error messages: 0.

Complete timestamped request/response bodies and console locations are in the linked JSON. Relevant observed HTTP/error entries:

```text
2026-10-20T07:51:01.644Z HTTP 200 http://localhost:8411/integrations
2026-10-20T07:51:01.653Z HTTP 200 http://localhost:8411/session/s3bee57561d744ff8a5cf63fc5bff34f9
2026-10-20T07:51:01.678Z HTTP 200 http://localhost:8411/integrations
2026-10-20T07:51:01.678Z HTTP 200 http://localhost:8411/known/s3bee57561d744ff8a5cf63fc5bff34f9
2026-10-20T07:51:01.678Z HTTP 200 http://localhost:8411/sessions/s3bee57561d744ff8a5cf63fc5bff34f9/versions
2026-10-20T07:51:01.678Z HTTP 200 http://localhost:8411/known/s3bee57561d744ff8a5cf63fc5bff34f9
2026-10-20T07:51:01.682Z HTTP 200 http://localhost:8411/sessions
2026-10-20T07:51:01.685Z HTTP 200 http://localhost:8411/sessions
2026-10-20T07:51:01.686Z HTTP 200 http://localhost:8411/session/s3bee57561d744ff8a5cf63fc5bff34f9?version=v1
2026-10-20T07:51:01.705Z HTTP 200 http://localhost:8411/known/s3bee57561d744ff8a5cf63fc5bff34f9?version=v1
2026-10-20T07:51:01.705Z HTTP 200 http://localhost:8411/sessions/s3bee57561d744ff8a5cf63fc5bff34f9/versions
2026-10-20T07:51:01.709Z HTTP 200 http://localhost:8411/insight/s3bee57561d744ff8a5cf63fc5bff34f9?version=v1
2026-10-20T07:51:01.710Z HTTP 200 http://localhost:8411/insight/s3bee57561d744ff8a5cf63fc5bff34f9?version=v1
2026-10-20T07:51:01.710Z HTTP 200 http://localhost:8411/session/s3bee57561d744ff8a5cf63fc5bff34f9?version=v1
2026-10-20T07:51:01.715Z HTTP 200 http://localhost:8411/session/s3bee57561d744ff8a5cf63fc5bff34f9?version=v1
2026-10-20T07:51:01.718Z HTTP 200 http://localhost:8411/session/s3bee57561d744ff8a5cf63fc5bff34f9?version=v1
```

## Captured state / API output

```json
{
  "time": "2026-10-20T07:51:01.847Z",
  "url": "http://localhost:3411/pipeline/insights",
  "body": "8-E 인사이트 도출 › 인사이트별 Pain Point\n인사이트 0개 · 대화형\n인사이트 도출\n\n페르소나를 바탕으로 인사이트를 도출하세요."
}
```
