# QA-NEG-001

```json
{
  "id": "QA-NEG-001",
  "url": "http://localhost:3411/pipeline/insights",
  "result": "PASS",
  "expected": "All 13 removed endpoints respond 404 or 405 and no Python Traceback.",
  "actual": "[{\"method\":\"POST\",\"path\":\"/preprocess\",\"status\":404},{\"method\":\"GET\",\"path\":\"/preprocess-status/x\",\"status\":404},{\"method\":\"GET\",\"path\":\"/sample/x\",\"status\":404},{\"method\":\"POST\",\"path\":\"/train\",\"status\":404},{\"method\":\"GET\",\"path\":\"/train-status/x\",\"status\":404},{\"method\":\"POST\",\"path\":\"/cluster\",\"status\":404},{\"method\":\"GET\",\"path\":\"/cluster-status/x\",\"status\":404},{\"method\":\"POST\",\"path\":\"/cluster-refine\",\"status\":404},{\"method\":\"POST\",\"path\":\"/embed\",\"status\":404},{\"method\":\"GET\",\"path\":\"/embed-status/x\",\"status\":404},{\"method\":\"POST\",\"path\":\"/persona\",\"status\":404},{\"method\":\"GET\",\"path\":\"/persona-status/x\",\"status\":404},{\"method\":\"GET\",\"path\":\"/sna-data/x\",\"status\":404}]",
  "evidence": "docs/development/v1-cleanup/qa/QA-NEG-001.md",
  "time": "2026-10-20T04:22:37.666Z",
  "steps": [
    "Sent each approved removed-route HTTP request using Playwright APIRequestContext"
  ],
  "screenshot": "/Users/yunho/Documents/dcx_agent-v1-cleanup/docs/development/v1-cleanup/qa/QA-NEG-001.png",
  "responses": [
    {
      "time": "2026-10-20T04:22:37.516Z",
      "method": "POST",
      "path": "/preprocess",
      "status": 404,
      "body": "{\"detail\":\"Not Found\"}"
    },
    {
      "time": "2026-10-20T04:22:37.518Z",
      "method": "GET",
      "path": "/preprocess-status/x",
      "status": 404,
      "body": "{\"detail\":\"Not Found\"}"
    },
    {
      "time": "2026-10-20T04:22:37.520Z",
      "method": "GET",
      "path": "/sample/x",
      "status": 404,
      "body": "{\"detail\":\"Not Found\"}"
    },
    {
      "time": "2026-10-20T04:22:37.521Z",
      "method": "POST",
      "path": "/train",
      "status": 404,
      "body": "{\"detail\":\"Not Found\"}"
    },
    {
      "time": "2026-10-20T04:22:37.522Z",
      "method": "GET",
      "path": "/train-status/x",
      "status": 404,
      "body": "{\"detail\":\"Not Found\"}"
    },
    {
      "time": "2026-10-20T04:22:37.524Z",
      "method": "POST",
      "path": "/cluster",
      "status": 404,
      "body": "{\"detail\":\"Not Found\"}"
    },
    {
      "time": "2026-10-20T04:22:37.525Z",
      "method": "GET",
      "path": "/cluster-status/x",
      "status": 404,
      "body": "{\"detail\":\"Not Found\"}"
    },
    {
      "time": "2026-10-20T04:22:37.526Z",
      "method": "POST",
      "path": "/cluster-refine",
      "status": 404,
      "body": "{\"detail\":\"Not Found\"}"
    },
    {
      "time": "2026-10-20T04:22:37.527Z",
      "method": "POST",
      "path": "/embed",
      "status": 404,
      "body": "{\"detail\":\"Not Found\"}"
    },
    {
      "time": "2026-10-20T04:22:37.528Z",
      "method": "GET",
      "path": "/embed-status/x",
      "status": 404,
      "body": "{\"detail\":\"Not Found\"}"
    },
    {
      "time": "2026-10-20T04:22:37.530Z",
      "method": "POST",
      "path": "/persona",
      "status": 404,
      "body": "{\"detail\":\"Not Found\"}"
    },
    {
      "time": "2026-10-20T04:22:37.531Z",
      "method": "GET",
      "path": "/persona-status/x",
      "status": 404,
      "body": "{\"detail\":\"Not Found\"}"
    },
    {
      "time": "2026-10-20T04:22:37.532Z",
      "method": "GET",
      "path": "/sna-data/x",
      "status": 404,
      "body": "{\"detail\":\"Not Found\"}"
    }
  ]
}
```

