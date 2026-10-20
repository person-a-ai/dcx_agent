# QA-NEG-003

```json
{
  "id": "QA-NEG-003",
  "url": "http://localhost:3411/pipeline/start",
  "result": "PASS",
  "expected": "Cleared browser storage: clustering shows select-project banner; action opens start; zero console errors.",
  "actual": "{\"storage\":{\"local\":{},\"session\":{}},\"destination\":\"http://localhost:3411/pipeline/start\",\"errorCount\":0}",
  "evidence": "docs/development/v1-cleanup/qa/QA-NEG-003.md",
  "time": "2026-10-20T04:24:14.680Z",
  "steps": [
    "Cleared local/session storage, CacheStorage, IndexedDB and cookies",
    "Directly opened clustering",
    "Waited for exact no-session banner",
    "Clicked 프로젝트 선택하기"
  ],
  "screenshot": "/Users/yunho/Documents/dcx_agent-v1-cleanup/docs/development/v1-cleanup/qa/QA-NEG-003.png",
  "console": [
    {
      "time": "2026-10-20T04:24:14.343Z",
      "type": "info",
      "text": "%cDownload the React DevTools for a better development experience: https://react.dev/link/react-devtools font-weight:bold"
    },
    {
      "time": "2026-10-20T04:24:14.358Z",
      "type": "log",
      "text": "[HMR] connected"
    },
    {
      "time": "2026-10-20T04:24:14.380Z",
      "type": "warning",
      "text": "Image with src \"/person-a-logo.png\" has either width or height modified, but not the other. If you use CSS to change the size of your image, also include the styles 'width: \"auto\"' or 'height: \"auto\"' to maintain the aspect ratio."
    }
  ],
  "noSessionScreenshot": "/Users/yunho/Documents/dcx_agent-v1-cleanup/docs/development/v1-cleanup/qa/QA-NEG-003-no-session.png",
  "network": [
    {
      "time": "2026-10-20T04:24:14.380Z",
      "method": "GET",
      "url": "http://localhost:8411/integrations",
      "body": null
    },
    {
      "time": "2026-10-20T04:24:14.381Z",
      "status": 200,
      "url": "http://localhost:8411/integrations",
      "body": "[{\"name\":\"openai\",\"connected\":false,\"env_vars\":[\"OPENAI_API_KEY\",\"OPENAI_MODEL\"],\"affects\":[\"llm\"],\"last_error\":null},{\"name\":\"claude\",\"connected\":false,\"env_vars\":[\"CLAUDE_API_KEY\"],\"affects\":[\"llm\"],\"last_error\":null}]"
    },
    {
      "time": "2026-10-20T04:24:14.604Z",
      "method": "GET",
      "url": "http://localhost:8411/sessions",
      "body": null
    },
    {
      "time": "2026-10-20T04:24:14.604Z",
      "method": "GET",
      "url": "http://localhost:8411/sessions",
      "body": null
    }
  ]
}
```

