# QA-NEG-002 — PASS

- URL: http://127.0.0.1:8411
- Tested HEAD: `5de8f30bbb05986afa4b5ccf579d3d0442302857`
- Executor: codex / browser-qa; thread `01a15844-a762-7910-97e2-9d33167a6188`.
- Recorded UTC interval: 2026-10-20T07:50:48.752Z → 2026-10-20T07:50:48.771Z.

## Expected

Persona, train and prep v2 status endpoints do not return 404.

## Steps

1. After QA-E2E-009, GET persona/{sid}/status, train/{sid}/status and prep/{sid}/status.
2. Record statuses and JSON.

## Actual

All three returned HTTP 200 for the completed session.

- PASS — three calls
- PASS — none 404

## Evidence

- [completed-screens.json](completed-screens.json)
- [all-events.json](all-events.json)
- API/file assertions use response or filesystem records; no screenshot substituted for data proof.

## Console / network / API

Page errors: 0; console error messages: 0.

Complete timestamped request/response bodies and console locations are in the linked JSON. Relevant observed HTTP/error entries:

```text
```

## Captured state / API output

```json
[
  {
    "time": "2026-10-20T07:50:48.752Z",
    "url": "http://127.0.0.1:8411/persona/s3bee57561d744ff8a5cf63fc5bff34f9/status",
    "status": 200,
    "body": {
      "package": false,
      "evidence_required": true,
      "status": "none",
      "run": null,
      "progress": 0,
      "personas": []
    }
  },
  {
    "time": "2026-10-20T07:50:48.765Z",
    "url": "http://127.0.0.1:8411/train/s3bee57561d744ff8a5cf63fc5bff34f9/status",
    "status": 200,
    "body": {
      "training": {},
      "workers": [],
      "monitor": null,
      "stage5": null
    }
  },
  {
    "time": "2026-10-20T07:50:48.771Z",
    "url": "http://127.0.0.1:8411/prep/s3bee57561d744ff8a5cf63fc5bff34f9/status",
    "status": 200,
    "body": {
      "status": "done",
      "progress": 1,
      "detail": {},
      "runId": null,
      "derivedRef": {
        "collectionId": "c1",
        "prepKey": "p_8d4420d74b0b"
      },
      "stage3": {
        "original": 6,
        "after": 6,
        "removed": {
          "ad": 0,
          "excluded_source": 0,
          "duplicate": 0,
          "too_short": 0,
          "excluded_channel": 0
        },
        "boilerplate_replaced": {},
        "tokens_written": 6,
        "embedded": 6,
        "embed_failed_zero_vector": 0,
        "prepKey": "p_8d4420d74b0b",
        "embedder": "fake",
        "analyzer": "kiwi-0.24.0",
        "at": "2026-10-20T07:49:09.457330+00:00"
      },
      "error": null,
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
      "reused": true
    }
  }
]
```
