# QA-NEG-004 — PASS

URL: http://localhost:8000/crawl/s0645b66274364a7688b9ee4ae84d78e6/config

Tested commit: c597b2a678231016e51b0d3644f3d6df921810c2; observed HEAD: c597b2a678231016e51b0d3644f3d6df921810c2.

## Approved scenario (unchanged)

```text
QA-NEG-004
Priority: P2
Type: Negative / API
Given: QA 세션
When: PUT /crawl/{sid}/config에 `youtube_vlog: {"videos_per_keyword": 0}`을 보낸다
Then:
  - 422 응답과 `error.code: "invalid_request"`가 온다
```

## Executed steps

1. 채널 youtube_vlog 및 videos_per_keyword=0 PUT

## Actual / verdict

videos_per_keyword=0 직접 PUT이 422 invalid_request 반환.



## Timestamped DOM / API evidence

```json
{
  "time": "2026-10-20T06:55:33.516Z",
  "url": "http://localhost:8000/crawl/s0645b66274364a7688b9ee4ae84d78e6/config",
  "status": 422,
  "body": {
    "status": "error",
    "error": {
      "kind": "validation",
      "code": "invalid_request",
      "message": "Invalid crawl request"
    }
  }
}
```

## Evidence files

- [settings-results-retry.json](settings-results-retry.json)

Screenshots were saved using explicit absolute paths and inspected for relevant states:



Shared main browser console/network: [console-main.log](console-main.log), [network-main.log](network-main.log). Main console: no errors; logo aspect-ratio warning. Scenario-specific API responses and variant network records are in the JSON above or linked raw evidence. Screenshots supplement DOM/API evidence, not replace it.
