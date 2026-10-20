# QA-NEG-001 — PASS

- URL: http://127.0.0.1:8411
- Tested HEAD: `5de8f30bbb05986afa4b5ccf579d3d0442302857`
- Executor: codex / browser-qa; thread `01a15844-a762-7910-97e2-9d33167a6188`.
- Recorded UTC interval: 2026-10-20T07:53:28.374Z → 2026-10-20T07:53:28.480Z.

## Expected

Thirteen removed API paths return 404 or 405 without Python Traceback.

## Steps

1. Use browser APIRequestContext against the running backend.
2. Send all 13 plan method/path pairs with JSON {sid:x}.
3. Capture each status and raw response body.

## Actual

All 13 returned HTTP 404 with no Traceback.

- PASS — all 13 tested
- PASS — all removed
- PASS — no Traceback

## Evidence

- [negative.json](negative.json)
- [all-events.json](all-events.json)
- API/file assertions use response or filesystem records; no screenshot substituted for data proof.

## Console / network / API

Page errors: 0; console error messages: 0.

Complete timestamped request/response bodies and console locations are in the linked JSON. Relevant observed HTTP/error entries:

```text
2026-10-20T07:53:28.425Z HTTP 200 http://localhost:8411/sessions
2026-10-20T07:53:28.465Z HTTP 200 http://localhost:8411/sessions
```

## Captured state / API output

```json
[
  {
    "time": "2026-10-20T07:53:28.377Z",
    "method": "POST",
    "url": "http://127.0.0.1:8411/preprocess",
    "request": {
      "sid": "x"
    },
    "status": 404,
    "body": "{\"detail\":\"Not Found\"}"
  },
  {
    "time": "2026-10-20T07:53:28.381Z",
    "method": "GET",
    "url": "http://127.0.0.1:8411/preprocess-status/x",
    "request": {
      "sid": "x"
    },
    "status": 404,
    "body": "{\"detail\":\"Not Found\"}"
  },
  {
    "time": "2026-10-20T07:53:28.390Z",
    "method": "GET",
    "url": "http://127.0.0.1:8411/sample/x",
    "request": {
      "sid": "x"
    },
    "status": 404,
    "body": "{\"detail\":\"Not Found\"}"
  },
  {
    "time": "2026-10-20T07:53:28.412Z",
    "method": "POST",
    "url": "http://127.0.0.1:8411/train",
    "request": {
      "sid": "x"
    },
    "status": 404,
    "body": "{\"detail\":\"Not Found\"}"
  },
  {
    "time": "2026-10-20T07:53:28.416Z",
    "method": "GET",
    "url": "http://127.0.0.1:8411/train-status/x",
    "request": {
      "sid": "x"
    },
    "status": 404,
    "body": "{\"detail\":\"Not Found\"}"
  },
  {
    "time": "2026-10-20T07:53:28.420Z",
    "method": "POST",
    "url": "http://127.0.0.1:8411/cluster",
    "request": {
      "sid": "x"
    },
    "status": 404,
    "body": "{\"detail\":\"Not Found\"}"
  },
  {
    "time": "2026-10-20T07:53:28.425Z",
    "method": "GET",
    "url": "http://127.0.0.1:8411/cluster-status/x",
    "request": {
      "sid": "x"
    },
    "status": 404,
    "body": "{\"detail\":\"Not Found\"}"
  },
  {
    "time": "2026-10-20T07:53:28.444Z",
    "method": "POST",
    "url": "http://127.0.0.1:8411/cluster-refine",
    "request": {
      "sid": "x"
    },
    "status": 404,
    "body": "{\"detail\":\"Not Found\"}"
  },
  {
    "time": "2026-10-20T07:53:28.450Z",
    "method": "POST",
    "url": "http://127.0.0.1:8411/embed",
    "request": {
      "sid": "x"
    },
    "status": 404,
    "body": "{\"detail\":\"Not Found\"}"
  },
  {
    "time": "2026-10-20T07:53:28.469Z",
    "method": "GET",
    "url": "http://127.0.0.1:8411/embed-status/x",
    "request": {
      "sid": "x"
    },
    "status": 404,
    "body": "{\"detail\":\"Not Found\"}"
  },
  {
    "time": "2026-10-20T07:53:28.473Z",
    "method": "POST",
    "url": "http://127.0.0.1:8411/persona",
    "request": {
      "sid": "x"
    },
    "status": 404,
    "body": "{\"detail\":\"Not Found\"}"
  },
  {
    "time": "2026-10-20T07:53:28.477Z",
    "method": "GET",
    "url": "http://127.0.0.1:8411/persona-status/x",
    "request": {
      "sid": "x"
    },
    "status": 404,
    "body": "{\"detail\":\"Not Found\"}"
  },
  {
    "time": "2026-10-20T07:53:28.480Z",
    "method": "GET",
    "url": "http://127.0.0.1:8411/sna-data/x",
    "request": {
      "sid": "x"
    },
    "status": 404,
    "body": "{\"detail\":\"Not Found\"}"
  }
]
```
