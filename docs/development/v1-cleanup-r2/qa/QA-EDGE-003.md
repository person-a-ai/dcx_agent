# QA-EDGE-003 — PASS

- URL: http://localhost:3411/pipeline/clustering
- Tested HEAD: `5de8f30bbb05986afa4b5ccf579d3d0442302857`
- Executor: codex / browser-qa; thread `01a15844-a762-7910-97e2-9d33167a6188`.
- Recorded UTC interval: 2026-10-20T07:54:11.174Z → 2026-10-20T07:56:17.731Z.

## Expected

Stage3 restart v2 locks stages 6–9 and shows prep banner; reselecting completed v1 consistently opens sidebar and clustering/personas pages (DV-5).

## Steps

1. Run last, after the other 18 active cases.
2. From completed session preprocess click 3단계부터 다시 → 새 버전 만들기.
3. Observe POST from=v1/restartFrom=stage3 creating v2.
4. Directly open clustering and inspect v2 gate/session.
5. Open version list and select v1; inspect clustering, then click personas.

## Actual

v2 stale prep locked all four stages and showed banner. v1 restored ten links; clustering read-only view and persona screen opened without prep gates.

- PASS — created v2 from stage3
- PASS — v2 invalid prep
- PASS — v2 four locked
- PASS — v2 prep banner
- PASS — v1 completed
- PASS — v1 clustering open
- PASS — v1 personas open

## Evidence

- [version-success.json](version-success.json)
- [all-events.json](all-events.json)
- [QA-EDGE-003-v2.png](QA-EDGE-003-v2.png) — absolute-path capture, existence verified, visually inspected.
- [QA-EDGE-003-v1-clustering.png](QA-EDGE-003-v1-clustering.png) — absolute-path capture, existence verified, visually inspected.
- [QA-EDGE-003-v1-personas.png](QA-EDGE-003-v1-personas.png) — absolute-path capture, existence verified, visually inspected.

## Console / network / API

Page errors: 0; console error messages: 23.

Complete timestamped request/response bodies and console locations are in the linked JSON. Relevant observed HTTP/error entries:

```text
2026-10-20T07:54:11.333Z HTTP 404 http://localhost:8411/crawl/s3bee57561d744ff8a5cf63fc5bff34f9/status
2026-10-20T07:54:11.334Z console Failed to load resource: the server responded with a status of 404 (Not Found) http://localhost:8411/crawl/s3bee57561d744ff8a5cf63fc5bff34f9/status
2026-10-20T07:54:11.339Z HTTP 404 http://localhost:8411/crawl/s3bee57561d744ff8a5cf63fc5bff34f9/status
2026-10-20T07:54:11.339Z console Failed to load resource: the server responded with a status of 404 (Not Found) http://localhost:8411/crawl/s3bee57561d744ff8a5cf63fc5bff34f9/status
2026-10-20T07:54:11.341Z HTTP 200 http://localhost:8411/prep/s3bee57561d744ff8a5cf63fc5bff34f9/status?version=v1
2026-10-20T07:54:11.343Z HTTP 200 http://localhost:8411/session/s3bee57561d744ff8a5cf63fc5bff34f9?version=v1
2026-10-20T07:54:11.345Z HTTP 200 http://localhost:8411/prep/s3bee57561d744ff8a5cf63fc5bff34f9/status?version=v1
2026-10-20T07:54:11.350Z HTTP 200 http://localhost:8411/session/s3bee57561d744ff8a5cf63fc5bff34f9?version=v1
2026-10-20T07:54:20.300Z HTTP 200 http://localhost:8411/sessions/s3bee57561d744ff8a5cf63fc5bff34f9/versions
2026-10-20T07:54:20.324Z HTTP 200 http://localhost:8411/sessions
2026-10-20T07:54:20.343Z HTTP 200 http://localhost:8411/session/s3bee57561d744ff8a5cf63fc5bff34f9?version=v1
2026-10-20T07:54:23.669Z HTTP 201 http://localhost:8411/sessions/s3bee57561d744ff8a5cf63fc5bff34f9/versions
2026-10-20T07:54:23.688Z HTTP 200 http://localhost:8411/session/s3bee57561d744ff8a5cf63fc5bff34f9?version=v2
2026-10-20T07:54:23.724Z HTTP 200 http://localhost:8411/sessions/s3bee57561d744ff8a5cf63fc5bff34f9/versions
2026-10-20T07:54:23.748Z HTTP 200 http://localhost:8411/known/s3bee57561d744ff8a5cf63fc5bff34f9?version=v2
2026-10-20T07:54:23.767Z HTTP 200 http://localhost:8411/session/s3bee57561d744ff8a5cf63fc5bff34f9?version=v2
2026-10-20T07:54:23.843Z HTTP 404 http://localhost:8411/crawl/s3bee57561d744ff8a5cf63fc5bff34f9/status
2026-10-20T07:54:23.844Z console Failed to load resource: the server responded with a status of 404 (Not Found) http://localhost:8411/crawl/s3bee57561d744ff8a5cf63fc5bff34f9/status
2026-10-20T07:54:23.846Z HTTP 200 http://localhost:8411/prep/s3bee57561d744ff8a5cf63fc5bff34f9/status?version=v2
2026-10-20T07:54:23.850Z HTTP 200 http://localhost:8411/session/s3bee57561d744ff8a5cf63fc5bff34f9?version=v2
2026-10-20T07:54:23.874Z HTTP 404 http://localhost:8411/crawl/s3bee57561d744ff8a5cf63fc5bff34f9/status
2026-10-20T07:54:23.875Z console Failed to load resource: the server responded with a status of 404 (Not Found) http://localhost:8411/crawl/s3bee57561d744ff8a5cf63fc5bff34f9/status
2026-10-20T07:54:23.878Z HTTP 200 http://localhost:8411/prep/s3bee57561d744ff8a5cf63fc5bff34f9/status?version=v2
2026-10-20T07:54:23.910Z HTTP 200 http://localhost:8411/session/s3bee57561d744ff8a5cf63fc5bff34f9?version=v2
2026-10-20T07:54:24.887Z HTTP 200 http://localhost:8411/integrations
2026-10-20T07:54:24.888Z HTTP 200 http://localhost:8411/session/s3bee57561d744ff8a5cf63fc5bff34f9
2026-10-20T07:54:25.002Z HTTP 200 http://localhost:8411/integrations
2026-10-20T07:54:25.048Z HTTP 200 http://localhost:8411/sessions/s3bee57561d744ff8a5cf63fc5bff34f9/versions
2026-10-20T07:54:25.050Z HTTP 200 http://localhost:8411/known/s3bee57561d744ff8a5cf63fc5bff34f9
2026-10-20T07:54:25.051Z HTTP 200 http://localhost:8411/known/s3bee57561d744ff8a5cf63fc5bff34f9
2026-10-20T07:54:25.465Z HTTP 200 http://localhost:8411/sessions
2026-10-20T07:54:25.465Z HTTP 200 http://localhost:8411/session/s3bee57561d744ff8a5cf63fc5bff34f9?version=v2
2026-10-20T07:54:25.472Z HTTP 200 http://localhost:8411/known/s3bee57561d744ff8a5cf63fc5bff34f9?version=v2
2026-10-20T07:54:25.472Z HTTP 200 http://localhost:8411/sessions/s3bee57561d744ff8a5cf63fc5bff34f9/versions
2026-10-20T07:54:25.473Z HTTP 200 http://localhost:8411/session/s3bee57561d744ff8a5cf63fc5bff34f9?version=v2
2026-10-20T07:54:25.474Z HTTP 200 http://localhost:8411/sessions
2026-10-20T07:54:34.947Z HTTP 200 http://localhost:8411/sessions
2026-10-20T07:54:35.036Z HTTP 200 http://localhost:8411/sessions/s3bee57561d744ff8a5cf63fc5bff34f9/versions
2026-10-20T07:54:35.046Z HTTP 200 http://localhost:8411/session/s3bee57561d744ff8a5cf63fc5bff34f9?version=v2
2026-10-20T07:54:36.393Z HTTP 200 http://localhost:8411/known/s3bee57561d744ff8a5cf63fc5bff34f9?version=v1
2026-10-20T07:54:36.401Z HTTP 200 http://localhost:8411/sessions/s3bee57561d744ff8a5cf63fc5bff34f9/versions
2026-10-20T07:54:36.422Z HTTP 200 http://localhost:8411/session/s3bee57561d744ff8a5cf63fc5bff34f9?version=v1
2026-10-20T07:54:45.079Z HTTP 200 http://localhost:8411/sessions
2026-10-20T07:54:46.319Z HTTP 200 http://localhost:8411/sessions/s3bee57561d744ff8a5cf63fc5bff34f9/versions
2026-10-20T07:54:46.331Z HTTP 200 http://localhost:8411/session/s3bee57561d744ff8a5cf63fc5bff34f9?version=v1
2026-10-20T07:54:54.950Z HTTP 200 http://localhost:8411/sessions
2026-10-20T07:54:56.317Z HTTP 200 http://localhost:8411/sessions/s3bee57561d744ff8a5cf63fc5bff34f9/versions
2026-10-20T07:54:56.324Z HTTP 200 http://localhost:8411/session/s3bee57561d744ff8a5cf63fc5bff34f9?version=v1
2026-10-20T07:55:04.917Z HTTP 200 http://localhost:8411/sessions
2026-10-20T07:55:06.318Z HTTP 200 http://localhost:8411/sessions/s3bee57561d744ff8a5cf63fc5bff34f9/versions
2026-10-20T07:55:06.333Z HTTP 200 http://localhost:8411/session/s3bee57561d744ff8a5cf63fc5bff34f9?version=v1
2026-10-20T07:55:14.902Z HTTP 200 http://localhost:8411/sessions
2026-10-20T07:55:16.316Z HTTP 200 http://localhost:8411/sessions/s3bee57561d744ff8a5cf63fc5bff34f9/versions
2026-10-20T07:55:16.322Z HTTP 200 http://localhost:8411/session/s3bee57561d744ff8a5cf63fc5bff34f9?version=v1
2026-10-20T07:55:24.889Z HTTP 200 http://localhost:8411/sessions
2026-10-20T07:55:25.008Z HTTP 200 http://localhost:8411/persona/s3bee57561d744ff8a5cf63fc5bff34f9/status?version=v1
2026-10-20T07:55:25.018Z HTTP 200 http://localhost:8411/persona/s3bee57561d744ff8a5cf63fc5bff34f9/status?version=v1
2026-10-20T07:55:25.022Z HTTP 409 http://localhost:8411/segment/s3bee57561d744ff8a5cf63fc5bff34f9/personas?version=v1
2026-10-20T07:55:25.022Z console Failed to load resource: the server responded with a status of 409 (Conflict) http://localhost:8411/segment/s3bee57561d744ff8a5cf63fc5bff34f9/personas?version=v1
2026-10-20T07:55:25.029Z HTTP 409 http://localhost:8411/segment/s3bee57561d744ff8a5cf63fc5bff34f9/personas?version=v1
2026-10-20T07:55:25.029Z console Failed to load resource: the server responded with a status of 409 (Conflict) http://localhost:8411/segment/s3bee57561d744ff8a5cf63fc5bff34f9/personas?version=v1
2026-10-20T07:55:26.315Z HTTP 200 http://localhost:8411/sessions/s3bee57561d744ff8a5cf63fc5bff34f9/versions
2026-10-20T07:55:26.319Z HTTP 200 http://localhost:8411/session/s3bee57561d744ff8a5cf63fc5bff34f9?version=v1
2026-10-20T07:55:28.005Z HTTP 200 http://localhost:8411/persona/s3bee57561d744ff8a5cf63fc5bff34f9/status?version=v1
2026-10-20T07:55:28.018Z HTTP 409 http://localhost:8411/segment/s3bee57561d744ff8a5cf63fc5bff34f9/personas?version=v1
2026-10-20T07:55:28.018Z console Failed to load resource: the server responded with a status of 409 (Conflict) http://localhost:8411/segment/s3bee57561d744ff8a5cf63fc5bff34f9/personas?version=v1
2026-10-20T07:55:30.998Z HTTP 200 http://localhost:8411/persona/s3bee57561d744ff8a5cf63fc5bff34f9/status?version=v1
2026-10-20T07:55:31.009Z HTTP 409 http://localhost:8411/segment/s3bee57561d744ff8a5cf63fc5bff34f9/personas?version=v1
2026-10-20T07:55:31.009Z console Failed to load resource: the server responded with a status of 409 (Conflict) http://localhost:8411/segment/s3bee57561d744ff8a5cf63fc5bff34f9/personas?version=v1
2026-10-20T07:55:33.999Z HTTP 200 http://localhost:8411/persona/s3bee57561d744ff8a5cf63fc5bff34f9/status?version=v1
2026-10-20T07:55:34.010Z HTTP 409 http://localhost:8411/segment/s3bee57561d744ff8a5cf63fc5bff34f9/personas?version=v1
2026-10-20T07:55:34.010Z console Failed to load resource: the server responded with a status of 409 (Conflict) http://localhost:8411/segment/s3bee57561d744ff8a5cf63fc5bff34f9/personas?version=v1
2026-10-20T07:55:34.891Z HTTP 200 http://localhost:8411/sessions
2026-10-20T07:55:36.314Z HTTP 200 http://localhost:8411/sessions/s3bee57561d744ff8a5cf63fc5bff34f9/versions
2026-10-20T07:55:36.318Z HTTP 200 http://localhost:8411/session/s3bee57561d744ff8a5cf63fc5bff34f9?version=v1
2026-10-20T07:55:37.002Z HTTP 200 http://localhost:8411/persona/s3bee57561d744ff8a5cf63fc5bff34f9/status?version=v1
2026-10-20T07:55:37.017Z HTTP 409 http://localhost:8411/segment/s3bee57561d744ff8a5cf63fc5bff34f9/personas?version=v1
2026-10-20T07:55:37.018Z console Failed to load resource: the server responded with a status of 409 (Conflict) http://localhost:8411/segment/s3bee57561d744ff8a5cf63fc5bff34f9/personas?version=v1
2026-10-20T07:55:40.002Z HTTP 200 http://localhost:8411/persona/s3bee57561d744ff8a5cf63fc5bff34f9/status?version=v1
2026-10-20T07:55:40.012Z HTTP 409 http://localhost:8411/segment/s3bee57561d744ff8a5cf63fc5bff34f9/personas?version=v1
2026-10-20T07:55:40.012Z console Failed to load resource: the server responded with a status of 409 (Conflict) http://localhost:8411/segment/s3bee57561d744ff8a5cf63fc5bff34f9/personas?version=v1
2026-10-20T07:55:42.996Z HTTP 200 http://localhost:8411/persona/s3bee57561d744ff8a5cf63fc5bff34f9/status?version=v1
2026-10-20T07:55:43.005Z HTTP 409 http://localhost:8411/segment/s3bee57561d744ff8a5cf63fc5bff34f9/personas?version=v1
2026-10-20T07:55:43.005Z console Failed to load resource: the server responded with a status of 409 (Conflict) http://localhost:8411/segment/s3bee57561d744ff8a5cf63fc5bff34f9/personas?version=v1
2026-10-20T07:55:44.906Z HTTP 200 http://localhost:8411/sessions
2026-10-20T07:55:46.005Z HTTP 200 http://localhost:8411/persona/s3bee57561d744ff8a5cf63fc5bff34f9/status?version=v1
2026-10-20T07:55:46.016Z HTTP 409 http://localhost:8411/segment/s3bee57561d744ff8a5cf63fc5bff34f9/personas?version=v1
2026-10-20T07:55:46.016Z console Failed to load resource: the server responded with a status of 409 (Conflict) http://localhost:8411/segment/s3bee57561d744ff8a5cf63fc5bff34f9/personas?version=v1
2026-10-20T07:55:46.317Z HTTP 200 http://localhost:8411/sessions/s3bee57561d744ff8a5cf63fc5bff34f9/versions
2026-10-20T07:55:46.324Z HTTP 200 http://localhost:8411/session/s3bee57561d744ff8a5cf63fc5bff34f9?version=v1
2026-10-20T07:55:49.005Z HTTP 200 http://localhost:8411/persona/s3bee57561d744ff8a5cf63fc5bff34f9/status?version=v1
2026-10-20T07:55:49.016Z HTTP 409 http://localhost:8411/segment/s3bee57561d744ff8a5cf63fc5bff34f9/personas?version=v1
2026-10-20T07:55:49.017Z console Failed to load resource: the server responded with a status of 409 (Conflict) http://localhost:8411/segment/s3bee57561d744ff8a5cf63fc5bff34f9/personas?version=v1
2026-10-20T07:55:52.002Z HTTP 200 http://localhost:8411/persona/s3bee57561d744ff8a5cf63fc5bff34f9/status?version=v1
2026-10-20T07:55:52.013Z HTTP 409 http://localhost:8411/segment/s3bee57561d744ff8a5cf63fc5bff34f9/personas?version=v1
2026-10-20T07:55:52.013Z console Failed to load resource: the server responded with a status of 409 (Conflict) http://localhost:8411/segment/s3bee57561d744ff8a5cf63fc5bff34f9/personas?version=v1
2026-10-20T07:55:54.899Z HTTP 200 http://localhost:8411/sessions
2026-10-20T07:55:55.003Z HTTP 200 http://localhost:8411/persona/s3bee57561d744ff8a5cf63fc5bff34f9/status?version=v1
2026-10-20T07:55:55.014Z HTTP 409 http://localhost:8411/segment/s3bee57561d744ff8a5cf63fc5bff34f9/personas?version=v1
2026-10-20T07:55:55.014Z console Failed to load resource: the server responded with a status of 409 (Conflict) http://localhost:8411/segment/s3bee57561d744ff8a5cf63fc5bff34f9/personas?version=v1
2026-10-20T07:55:56.319Z HTTP 200 http://localhost:8411/sessions/s3bee57561d744ff8a5cf63fc5bff34f9/versions
2026-10-20T07:55:56.326Z HTTP 200 http://localhost:8411/session/s3bee57561d744ff8a5cf63fc5bff34f9?version=v1
2026-10-20T07:55:58.006Z HTTP 200 http://localhost:8411/persona/s3bee57561d744ff8a5cf63fc5bff34f9/status?version=v1
2026-10-20T07:55:58.015Z HTTP 409 http://localhost:8411/segment/s3bee57561d744ff8a5cf63fc5bff34f9/personas?version=v1
2026-10-20T07:55:58.015Z console Failed to load resource: the server responded with a status of 409 (Conflict) http://localhost:8411/segment/s3bee57561d744ff8a5cf63fc5bff34f9/personas?version=v1
2026-10-20T07:56:01.016Z HTTP 200 http://localhost:8411/persona/s3bee57561d744ff8a5cf63fc5bff34f9/status?version=v1
2026-10-20T07:56:01.026Z HTTP 409 http://localhost:8411/segment/s3bee57561d744ff8a5cf63fc5bff34f9/personas?version=v1
2026-10-20T07:56:01.028Z console Failed to load resource: the server responded with a status of 409 (Conflict) http://localhost:8411/segment/s3bee57561d744ff8a5cf63fc5bff34f9/personas?version=v1
2026-10-20T07:56:04.007Z HTTP 200 http://localhost:8411/persona/s3bee57561d744ff8a5cf63fc5bff34f9/status?version=v1
2026-10-20T07:56:04.021Z HTTP 409 http://localhost:8411/segment/s3bee57561d744ff8a5cf63fc5bff34f9/personas?version=v1
2026-10-20T07:56:04.021Z console Failed to load resource: the server responded with a status of 409 (Conflict) http://localhost:8411/segment/s3bee57561d744ff8a5cf63fc5bff34f9/personas?version=v1
2026-10-20T07:56:04.905Z HTTP 200 http://localhost:8411/sessions
2026-10-20T07:56:06.318Z HTTP 200 http://localhost:8411/sessions/s3bee57561d744ff8a5cf63fc5bff34f9/versions
2026-10-20T07:56:06.329Z HTTP 200 http://localhost:8411/session/s3bee57561d744ff8a5cf63fc5bff34f9?version=v1
2026-10-20T07:56:07.003Z HTTP 200 http://localhost:8411/persona/s3bee57561d744ff8a5cf63fc5bff34f9/status?version=v1
2026-10-20T07:56:07.014Z HTTP 409 http://localhost:8411/segment/s3bee57561d744ff8a5cf63fc5bff34f9/personas?version=v1
2026-10-20T07:56:07.015Z console Failed to load resource: the server responded with a status of 409 (Conflict) http://localhost:8411/segment/s3bee57561d744ff8a5cf63fc5bff34f9/personas?version=v1
2026-10-20T07:56:10.006Z HTTP 200 http://localhost:8411/persona/s3bee57561d744ff8a5cf63fc5bff34f9/status?version=v1
2026-10-20T07:56:10.018Z HTTP 409 http://localhost:8411/segment/s3bee57561d744ff8a5cf63fc5bff34f9/personas?version=v1
2026-10-20T07:56:10.018Z console Failed to load resource: the server responded with a status of 409 (Conflict) http://localhost:8411/segment/s3bee57561d744ff8a5cf63fc5bff34f9/personas?version=v1
2026-10-20T07:56:13.006Z HTTP 200 http://localhost:8411/persona/s3bee57561d744ff8a5cf63fc5bff34f9/status?version=v1
2026-10-20T07:56:13.017Z HTTP 409 http://localhost:8411/segment/s3bee57561d744ff8a5cf63fc5bff34f9/personas?version=v1
2026-10-20T07:56:13.017Z console Failed to load resource: the server responded with a status of 409 (Conflict) http://localhost:8411/segment/s3bee57561d744ff8a5cf63fc5bff34f9/personas?version=v1
2026-10-20T07:56:14.899Z HTTP 200 http://localhost:8411/sessions
2026-10-20T07:56:16.005Z HTTP 200 http://localhost:8411/persona/s3bee57561d744ff8a5cf63fc5bff34f9/status?version=v1
2026-10-20T07:56:16.019Z HTTP 409 http://localhost:8411/segment/s3bee57561d744ff8a5cf63fc5bff34f9/personas?version=v1
2026-10-20T07:56:16.020Z console Failed to load resource: the server responded with a status of 409 (Conflict) http://localhost:8411/segment/s3bee57561d744ff8a5cf63fc5bff34f9/personas?version=v1
2026-10-20T07:56:16.320Z HTTP 200 http://localhost:8411/sessions/s3bee57561d744ff8a5cf63fc5bff34f9/versions
2026-10-20T07:56:16.327Z HTTP 200 http://localhost:8411/session/s3bee57561d744ff8a5cf63fc5bff34f9?version=v1
```

## Captured state / API output

```json
{
  "time": "2026-10-20T07:54:23.669Z",
  "status": 201,
  "request": "{\"from\":\"v1\",\"restartFrom\":\"stage3\",\"note\":\"\"}",
  "response": {
    "version": "v2"
  },
  "nav": [
    {
      "text": "시작",
      "aria": null,
      "href": "/pipeline/start",
      "title": null,
      "tabindex": null
    },
    {
      "text": "키워드",
      "aria": null,
      "href": "/pipeline/keywords",
      "title": null,
      "tabindex": null
    },
    {
      "text": "크롤링",
      "aria": null,
      "href": "/pipeline/crawling",
      "title": null,
      "tabindex": null
    },
    {
      "text": "4전처리진행 중",
      "aria": null,
      "href": "/pipeline/preprocess",
      "title": null,
      "tabindex": null
    },
    {
      "text": "5라벨링",
      "aria": null,
      "href": "/pipeline/labeling",
      "title": null,
      "tabindex": null
    },
    {
      "text": "6학습",
      "aria": null,
      "href": "/pipeline/training",
      "title": null,
      "tabindex": null
    },
    {
      "text": "7클러스터링",
      "aria": "true",
      "href": null,
      "title": "전처리(3단계)를 먼저 완료하세요",
      "tabindex": null
    },
    {
      "text": "8근거 탐색",
      "aria": "true",
      "href": null,
      "title": "전처리(3단계)를 먼저 완료하세요",
      "tabindex": null
    },
    {
      "text": "9페르소나",
      "aria": "true",
      "href": null,
      "title": "전처리(3단계)를 먼저 완료하세요",
      "tabindex": null
    },
    {
      "text": "10인사이트",
      "aria": "true",
      "href": null,
      "title": "전처리(3단계)를 먼저 완료하세요",
      "tabindex": null
    }
  ],
  "v2": {
    "time": "2026-10-20T07:54:25.488Z",
    "url": "http://localhost:3411/pipeline/clustering",
    "body": "이 결과는 v1의 6단계 기준입니다. 이 단계를 다시 하거나 그대로 쓰세요.\n3단계(전처리)를 먼저 완료하세요. 전처리가 끝나야 클러스터링 화면을 열 수 있습니다.\n전처리 화면으로",
    "nav": [
      {
        "text": "시작",
        "aria": null,
        "href": "/pipeline/start",
        "title": null,
        "tabindex": null
      },
      {
        "text": "키워드",
        "aria": null,
        "href": "/pipeline/keywords",
        "title": null,
        "tabindex": null
      },
      {
        "text": "크롤링",
        "aria": null,
        "href": "/pipeline/crawling",
        "title": null,
        "tabindex": null
      },
      {
        "text": "4전처리",
        "aria": null,
        "href": "/pipeline/preprocess",
        "title": null,
        "tabindex": null
      },
      {
        "text": "5라벨링",
        "aria": null,
        "href": "/pipeline/labeling",
        "title": null,
        "tabindex": null
      },
      {
        "text": "6학습",
        "aria": null,
        "href": "/pipeline/training",
        "title": null,
        "tabindex": null
      },
      {
        "text": "7클러스터링진행 중",
        "aria": "true",
        "href": null,
        "title": "전처리(3단계)를 먼저 완료하세요",
        "tabindex": null
      },
      {
        "text": "8근거 탐색",
        "aria": "true",
        "href": null,
        "title": "전처리(3단계)를 먼저 완료하세요",
        "tabindex": null
      },
      {
        "text": "9페르소나",
        "aria": "true",
        "href": null,
        "title": "전처리(3단계)를 먼저 완료하세요",
        "tabindex": null
      },
      {
        "text": "10인사이트",
        "aria": "true",
        "href": null,
        "title": "전처리(3단계)를 먼저 완료하세요",
        "tabindex": null
      }
    ],
    "session": {
      "status": "ok",
      "data": {
        "schemaVersion": 2,
        "sid": "s3bee57561d744ff8a5cf63fc5bff34f9",
        "step": "start",
        "drafts": {
          "prep": null
        },
        "projectContext": {
          "bk": "QA 전처리 실행",
          "oneLiner": "QA용 세션",
          "researchQuestion": {
            "text": "냉방 경험은?",
            "template": null
          },
          "projectType": {
            "choice": "new",
            "note": ""
          },
          "taskMode": null,
          "analysisGoal": {
            "choice": "needs",
            "note": ""
          },
          "keyMetrics": [
            {
              "name": "만족",
              "source": "",
              "item": ""
            }
          ],
          "constraints": [],
          "positioning": {
            "price": "value",
            "market": "new",
            "priceText": "",
            "marketText": ""
          },
          "personaSeeds": null,
          "channels": [
            "fixture"
          ],
          "knownInsights": [],
          "productCategory": {
            "l1": "가전",
            "l2": null,
            "l3": null,
            "source": "user"
          },
          "targetScope": null,
          "futureCustomer": null,
          "schemaVersion": 1
        },
        "knownInsights": [],
        "version": "v2",
        "updatedAt": "2026-10-20T07:54:23.652713+00:00",
        "collectionId": "c1",
        "prep": {
          "config": {
            "adFilter": [],
            "excludeSources": [],
            "excludeChannels": [],
            "minBodyChars": 10,
            "boilerplate": {
              "naver_cafe": [
                "카페 회원이 되시면 전체 내용을 볼 수 있습니다.",
                "카페 가입하기"
              ],
              "naver_blog": [
                "공감",
                "이웃추가"
              ],
              "clien": [],
              "ppomppu": [],
              "youtube": []
            },
            "analyzer": "kiwi",
            "tokenPos": [
              "NNG",
              "NNP",
              "VV",
              "VA",
              "XR"
            ],
            "embedder": "fake",
            "embedModel": "voyage-4",
            "embedDim": 1024
          },
          "derivedRef": {
            "collectionId": "c1",
            "prepKey": "p_8d4420d74b0b"
          },
          "status": "stale",
          "savedAt": "2026-10-20T07:49:34.574128+00:00",
          "reused": true,
          "runId": null
        },
        "parentVersion": "v1",
        "restartFrom": "stage3",
        "stale": {
          "stage3": "stage3 changed in v2",
          "stage4": "stage3 changed in v2",
          "stage5": "stage3 changed in v2",
          "stage6": "stage3 changed in v2",
          "stage7": "stage3 changed in v2",
          "stage8": "stage3 changed in v2"
        },
        "segment": {
          "status": "stale"
        },
        "completion": {
          "crawlDone": true,
          "prepDone": false,
          "labelingDone": false,
          "exportDone": false,
          "clustersDone": false,
          "segmentDone": false,
          "personaDone": false,
          "insightDone": false,
          "evidenceDone": false
        }
      }
    }
  },
  "v1cluster": {
    "time": "2026-10-20T07:55:24.822Z",
    "url": "http://localhost:3411/pipeline/clustering",
    "body": "v1 · 읽기 전용 · 이 버전에서 새로 시작하기\n6단계의 저장된 결과를 확인합니다\n\n이 버전의 결과 파일과 저장 시각은 버전 비교에서 확인하세요.",
    "nav": [
      {
        "text": "시작",
        "aria": null,
        "href": "/pipeline/start",
        "title": null,
        "tabindex": null
      },
      {
        "text": "키워드",
        "aria": null,
        "href": "/pipeline/keywords",
        "title": null,
        "tabindex": null
      },
      {
        "text": "크롤링",
        "aria": null,
        "href": "/pipeline/crawling",
        "title": null,
        "tabindex": null
      },
      {
        "text": "전처리",
        "aria": null,
        "href": "/pipeline/preprocess",
        "title": null,
        "tabindex": null
      },
      {
        "text": "5라벨링",
        "aria": null,
        "href": "/pipeline/labeling",
        "title": null,
        "tabindex": null
      },
      {
        "text": "6학습",
        "aria": null,
        "href": "/pipeline/training",
        "title": null,
        "tabindex": null
      },
      {
        "text": "7클러스터링진행 중",
        "aria": null,
        "href": "/pipeline/clustering",
        "title": null,
        "tabindex": null
      },
      {
        "text": "8근거 탐색",
        "aria": null,
        "href": "/pipeline/evidence",
        "title": null,
        "tabindex": null
      },
      {
        "text": "9페르소나",
        "aria": null,
        "href": "/pipeline/personas",
        "title": null,
        "tabindex": null
      },
      {
        "text": "10인사이트",
        "aria": null,
        "href": "/pipeline/insights",
        "title": null,
        "tabindex": null
      }
    ],
    "session": {
      "status": "ok",
      "data": {
        "schemaVersion": 2,
        "sid": "s3bee57561d744ff8a5cf63fc5bff34f9",
        "step": "start",
        "drafts": {
          "prep": null
        },
        "projectContext": {
          "bk": "QA 전처리 실행",
          "oneLiner": "QA용 세션",
          "researchQuestion": {
            "text": "냉방 경험은?",
            "template": null
          },
          "projectType": {
            "choice": "new",
            "note": ""
          },
          "taskMode": null,
          "analysisGoal": {
            "choice": "needs",
            "note": ""
          },
          "keyMetrics": [
            {
              "name": "만족",
              "source": "",
              "item": ""
            }
          ],
          "constraints": [],
          "positioning": {
            "price": "value",
            "market": "new",
            "priceText": "",
            "marketText": ""
          },
          "personaSeeds": null,
          "channels": [
            "fixture"
          ],
          "knownInsights": [],
          "productCategory": {
            "l1": "가전",
            "l2": null,
            "l3": null,
            "source": "user"
          },
          "targetScope": null,
          "futureCustomer": null,
          "schemaVersion": 1
        },
        "knownInsights": [],
        "version": "v1",
        "updatedAt": "2026-10-20T07:49:34.577924+00:00",
        "collectionId": "c1",
        "prep": {
          "config": {
            "adFilter": [],
            "excludeSources": [],
            "excludeChannels": [],
            "minBodyChars": 10,
            "boilerplate": {
              "naver_cafe": [
                "카페 회원이 되시면 전체 내용을 볼 수 있습니다.",
                "카페 가입하기"
              ],
              "naver_blog": [
                "공감",
                "이웃추가"
              ],
              "clien": [],
              "ppomppu": [],
              "youtube": []
            },
            "analyzer": "kiwi",
            "tokenPos": [
              "NNG",
              "NNP",
              "VV",
              "VA",
              "XR"
            ],
            "embedder": "fake",
            "embedModel": "voyage-4",
            "embedDim": 1024
          },
          "derivedRef": {
            "collectionId": "c1",
            "prepKey": "p_8d4420d74b0b"
          },
          "status": "done",
          "savedAt": "2026-10-20T07:49:34.574128+00:00",
          "reused": true,
          "runId": null
        },
        "completion": {
          "crawlDone": true,
          "prepDone": true,
          "labelingDone": false,
          "exportDone": false,
          "clustersDone": false,
          "segmentDone": false,
          "personaDone": false,
          "insightDone": false,
          "evidenceDone": false
        }
      }
    }
  },
  "v1personas": {
    "time": "2026-10-20T07:56:17.731Z",
    "url": "http://localhost:3411/pipeline/personas",
    "body": "8단계 · 페르소나\n\n세션 전체에서 어느 Context가 기회인가\n\nv1 · 읽기 전용\n\n페르소나 만들기\n앞 층을 모두 확정한 뒤 진행하세요. 다시 불러오기\n페르소나 목록\n전체 맵\nPersona 카드\nOpportunity Map · Context 0개 · 기회 잠정\n0\n0.25\n0.5\n0.75\n1\n0\n0.25\n0.5\n0.75\n1\n중요도\n만족도\nA Exciting\nB Experiencing\nC Competitive\nD Forgiven\nE Dangling\nF At-risk\n\n기회 지도를 만들 Context가 없습니다.\n\n속 빈 모양 · 반례 Context / ★ 몰랐고 기회도 큰 지점 · 겹친 점은 아래 Context 표에서 각각 확인할 수 있습니다.\n\n점을 가리키거나 아래 표에서 Context를 고르세요.\n\nContext 비교 표",
    "nav": [
      {
        "text": "시작",
        "aria": null,
        "href": "/pipeline/start",
        "title": null,
        "tabindex": null
      },
      {
        "text": "키워드",
        "aria": null,
        "href": "/pipeline/keywords",
        "title": null,
        "tabindex": null
      },
      {
        "text": "크롤링",
        "aria": null,
        "href": "/pipeline/crawling",
        "title": null,
        "tabindex": null
      },
      {
        "text": "전처리",
        "aria": null,
        "href": "/pipeline/preprocess",
        "title": null,
        "tabindex": null
      },
      {
        "text": "5라벨링",
        "aria": null,
        "href": "/pipeline/labeling",
        "title": null,
        "tabindex": null
      },
      {
        "text": "6학습",
        "aria": null,
        "href": "/pipeline/training",
        "title": null,
        "tabindex": null
      },
      {
        "text": "7클러스터링",
        "aria": null,
        "href": "/pipeline/clustering",
        "title": null,
        "tabindex": null
      },
      {
        "text": "8근거 탐색",
        "aria": null,
        "href": "/pipeline/evidence",
        "title": null,
        "tabindex": null
      },
      {
        "text": "9페르소나진행 중",
        "aria": null,
        "href": "/pipeline/personas",
        "title": null,
        "tabindex": null
      },
      {
        "text": "10인사이트",
        "aria": null,
        "href": "/pipeline/insights",
        "title": null,
        "tabindex": null
      }
    ]
  }
}
```

## Execution notes

Extra DV-5 observation: clustering's old version is its read-only stored-results view; personas displays the persona UI with v1 read-only label. Both pass the gate. Initial QA locator incorrectly waited for an active-version execution button on clustering, then for a generic saved-results heading on personas; those timeouts did not represent required assertions. Corrected after inspecting actual DOM. The v1 persona endpoint continues returning its existing 409; preprocess entry emits seeded crawl/status 404s. These are recorded, and QA-EDGE-003 does not impose the QA-E2E-009 console rule.
