# QA-REG-003 — PASS

- URL: http://localhost:3411/pipeline/preprocess
- Tested HEAD: `5de8f30bbb05986afa4b5ccf579d3d0442302857`
- Executor: codex / browser-qa; thread `01a15844-a762-7910-97e2-9d33167a6188`.
- Recorded UTC interval: 2026-10-20T07:49:36.001863+00:00 → 2026-10-20T07:49:36.001863+00:00.

## Expected

Each derived JSONL row contains desc/cafe/link and desc length <=4000.

## Steps

1. Immediately after first prep/reuse checks, read all derived docs/*.jsonl rows.
2. Record filenames, row numbers, keys and desc lengths without changing data.

## Actual

All six rows contain the three fields; every desc is 44 characters.

- PASS — six rows inspected
- PASS — all keys
- PASS — desc maximum

## Evidence

- [prep-files-done.json](prep-files-done.json)
- [all-events.json](all-events.json)
- API/file assertions use response or filesystem records; no screenshot substituted for data proof.

## Console / network / API

Page errors: 0; console error messages: 0.

Complete timestamped request/response bodies and console locations are in the linked JSON. Relevant observed HTTP/error entries:

```text
```

## Captured state / API output

```json
{
  "time": "2026-10-20T07:49:36.001863+00:00",
  "preprocessedExists": false,
  "manifests": [
    {
      "path": ".harness/qa-data/derived/s3bee57561d744ff8a5cf63fc5bff34f9/c1/p_8d4420d74b0b/manifest.json",
      "data": {
        "collectionId": "c1",
        "prepKey": "p_8d4420d74b0b",
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
        "collectionFinalized": true,
        "embedder": {
          "name": "fake",
          "model": "voyage-4",
          "dim": 1024
        },
        "analyzer": "kiwi-0.24.0",
        "createdAt": "2026-10-20T07:49:06.776604+00:00",
        "counts": {
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
        "progress": {
          "done_shards": 1,
          "total_shards": 1,
          "docs_written": 6,
          "tokens_written": 6,
          "vectors_written": 6
        },
        "embedderName": "fake",
        "status": "done"
      }
    }
  ],
  "rows": [
    {
      "file": ".harness/qa-data/derived/s3bee57561d744ff8a5cf63fc5bff34f9/c1/p_8d4420d74b0b/docs/part-00001.jsonl",
      "line": 1,
      "keys": [
        "body",
        "cafe",
        "comments",
        "desc",
        "doc_id",
        "fetch_level",
        "idx",
        "link",
        "source",
        "src_meta",
        "title",
        "url"
      ],
      "descLength": 44,
      "desc": "에어컨 냉방 사용 경험이 충분히 긴 본문입니다 0. 여름에 시원했습니다.\n좋아요",
      "cafe": "QA카페",
      "link": "https://example.test/qa0"
    },
    {
      "file": ".harness/qa-data/derived/s3bee57561d744ff8a5cf63fc5bff34f9/c1/p_8d4420d74b0b/docs/part-00001.jsonl",
      "line": 2,
      "keys": [
        "body",
        "cafe",
        "comments",
        "desc",
        "doc_id",
        "fetch_level",
        "idx",
        "link",
        "source",
        "src_meta",
        "title",
        "url"
      ],
      "descLength": 44,
      "desc": "에어컨 냉방 사용 경험이 충분히 긴 본문입니다 1. 여름에 시원했습니다.\n좋아요",
      "cafe": "QA카페",
      "link": "https://example.test/qa1"
    },
    {
      "file": ".harness/qa-data/derived/s3bee57561d744ff8a5cf63fc5bff34f9/c1/p_8d4420d74b0b/docs/part-00001.jsonl",
      "line": 3,
      "keys": [
        "body",
        "cafe",
        "comments",
        "desc",
        "doc_id",
        "fetch_level",
        "idx",
        "link",
        "source",
        "src_meta",
        "title",
        "url"
      ],
      "descLength": 44,
      "desc": "에어컨 냉방 사용 경험이 충분히 긴 본문입니다 2. 여름에 시원했습니다.\n좋아요",
      "cafe": "QA카페",
      "link": "https://example.test/qa2"
    },
    {
      "file": ".harness/qa-data/derived/s3bee57561d744ff8a5cf63fc5bff34f9/c1/p_8d4420d74b0b/docs/part-00001.jsonl",
      "line": 4,
      "keys": [
        "body",
        "cafe",
        "comments",
        "desc",
        "doc_id",
        "fetch_level",
        "idx",
        "link",
        "source",
        "src_meta",
        "title",
        "url"
      ],
      "descLength": 44,
      "desc": "에어컨 냉방 사용 경험이 충분히 긴 본문입니다 3. 여름에 시원했습니다.\n좋아요",
      "cafe": "QA카페",
      "link": "https://example.test/qa3"
    },
    {
      "file": ".harness/qa-data/derived/s3bee57561d744ff8a5cf63fc5bff34f9/c1/p_8d4420d74b0b/docs/part-00001.jsonl",
      "line": 5,
      "keys": [
        "body",
        "cafe",
        "comments",
        "desc",
        "doc_id",
        "fetch_level",
        "idx",
        "link",
        "source",
        "src_meta",
        "title",
        "url"
      ],
      "descLength": 44,
      "desc": "에어컨 냉방 사용 경험이 충분히 긴 본문입니다 4. 여름에 시원했습니다.\n좋아요",
      "cafe": "QA카페",
      "link": "https://example.test/qa4"
    },
    {
      "file": ".harness/qa-data/derived/s3bee57561d744ff8a5cf63fc5bff34f9/c1/p_8d4420d74b0b/docs/part-00001.jsonl",
      "line": 6,
      "keys": [
        "body",
        "cafe",
        "comments",
        "desc",
        "doc_id",
        "fetch_level",
        "idx",
        "link",
        "source",
        "src_meta",
        "title",
        "url"
      ],
      "descLength": 44,
      "desc": "에어컨 냉방 사용 경험이 충분히 긴 본문입니다 5. 여름에 시원했습니다.\n좋아요",
      "cafe": "QA카페",
      "link": "https://example.test/qa5"
    }
  ]
}
```
