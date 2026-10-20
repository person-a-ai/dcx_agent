# QA-NEG-002

```json
{
  "id": "QA-NEG-002",
  "url": "http://localhost:3411/pipeline/insights",
  "result": "PASS",
  "expected": "GET persona/train/prep v2 status endpoints are not 404 for completed session.",
  "actual": "[{\"url\":\"http://127.0.0.1:8411/persona/sf7d9d6897a31472895cf5fdeafb9cea1/status\",\"status\":200},{\"url\":\"http://127.0.0.1:8411/train/sf7d9d6897a31472895cf5fdeafb9cea1/status\",\"status\":200},{\"url\":\"http://127.0.0.1:8411/prep/sf7d9d6897a31472895cf5fdeafb9cea1/status\",\"status\":200}]",
  "evidence": "docs/development/v1-cleanup/qa/QA-NEG-002.md",
  "time": "2026-10-20T04:22:37.733Z",
  "steps": [
    "Read all three v2 status endpoints after preprocessing completion"
  ],
  "screenshot": "/Users/yunho/Documents/dcx_agent-v1-cleanup/docs/development/v1-cleanup/qa/QA-NEG-002.png",
  "responses": [
    {
      "time": "2026-10-20T04:22:37.669Z",
      "url": "http://127.0.0.1:8411/persona/sf7d9d6897a31472895cf5fdeafb9cea1/status",
      "status": 200,
      "body": "{\"package\":false,\"evidence_required\":true,\"status\":\"none\",\"run\":null,\"progress\":0,\"personas\":[]}"
    },
    {
      "time": "2026-10-20T04:22:37.671Z",
      "url": "http://127.0.0.1:8411/train/sf7d9d6897a31472895cf5fdeafb9cea1/status",
      "status": 200,
      "body": "{\"training\":{},\"workers\":[],\"monitor\":null,\"stage5\":null}"
    },
    {
      "time": "2026-10-20T04:22:37.674Z",
      "url": "http://127.0.0.1:8411/prep/sf7d9d6897a31472895cf5fdeafb9cea1/status",
      "status": 200,
      "body": "{\"status\":\"done\",\"progress\":1,\"detail\":{},\"runId\":null,\"derivedRef\":{\"collectionId\":\"c1\",\"prepKey\":\"p_8d4420d74b0b\"},\"stage3\":{\"original\":6,\"after\":6,\"removed\":{\"ad\":0,\"excluded_source\":0,\"duplicate\":0,\"too_short\":0,\"excluded_channel\":0},\"boilerplate_replaced\":{},\"tokens_written\":6,\"embedded\":6,\"embed_failed_zero_vector\":0,\"prepKey\":\"p_8d4420d74b0b\",\"embedder\":\"fake\",\"analyzer\":\"kiwi-0.24.0\",\"at\":\"2026-10-20T04:21:14.539728+00:00\"},\"error\":null,\"config\":{\"adFilter\":[],\"excludeSources\":[],\"excludeChannels\":[],\"minBodyChars\":10,\"boilerplate\":{\"naver_cafe\":[\"카페 회원이 되시면 전체 내용을 볼 수 있습니다.\",\"카페 가입하기\"],\"naver_blog\":[\"공감\",\"이웃추가\"],\"clien\":[],\"ppomppu\":[],\"youtube\":[]},\"analyzer\":\"kiwi\",\"tokenPos\":[\"NNG\",\"NNP\",\"VV\",\"VA\",\"XR\"],\"embedder\":\"fake\",\"embedModel\":\"voyage-4\",\"embedDim\":1024},\"reused\":true}"
    }
  ]
}
```

