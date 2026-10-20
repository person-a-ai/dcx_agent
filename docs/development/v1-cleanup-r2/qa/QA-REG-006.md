# QA-REG-006 — PASS

- URL: http://localhost:3411/pipeline/insights
- Tested HEAD: `5de8f30bbb05986afa4b5ccf579d3d0442302857`
- Executor: codex / browser-qa; thread `01a15844-a762-7910-97e2-9d33167a6188`.
- Recorded UTC interval: 2026-10-20T07:51:00.874Z → 2026-10-20T07:54:00.490Z.

## Expected

Pipeline chat panel sends POST /chat, not 404, and displays answer/error; API-only POST /insight-chat is not 404.

## Steps

1. Open pipeline chatbot on the completed session.
2. Enter 현재 전처리 상태를 알려주세요. and click 전송.
3. Capture POST /chat response and actual panel text.
4. Read OpenAPI request schema; call /insight-chat with sid/query/bk/novel through APIRequestContext only.

## Actual

POST /chat and /insight-chat returned 200; panel displayed the no-model fallback answer.

- PASS — chat route alive
- PASS — panel displays response
- PASS — insight route alive

## Evidence

- [chat-success.json](chat-success.json)
- [all-events.json](all-events.json)
- [QA-REG-006.png](QA-REG-006.png) — absolute-path capture, existence verified, visually inspected.

## Console / network / API

Page errors: 0; console error messages: 0.

Complete timestamped request/response bodies and console locations are in the linked JSON. Relevant observed HTTP/error entries:

```text
2026-10-20T07:51:11.684Z HTTP 200 http://localhost:8411/sessions
2026-10-20T07:51:11.701Z HTTP 200 http://localhost:8411/sessions/s3bee57561d744ff8a5cf63fc5bff34f9/versions
2026-10-20T07:51:11.705Z HTTP 200 http://localhost:8411/session/s3bee57561d744ff8a5cf63fc5bff34f9?version=v1
2026-10-20T07:51:21.681Z HTTP 200 http://localhost:8411/sessions
2026-10-20T07:51:21.700Z HTTP 200 http://localhost:8411/sessions/s3bee57561d744ff8a5cf63fc5bff34f9/versions
2026-10-20T07:51:21.704Z HTTP 200 http://localhost:8411/session/s3bee57561d744ff8a5cf63fc5bff34f9?version=v1
2026-10-20T07:51:27.189Z HTTP 200 http://localhost:8411/chat
2026-10-20T07:51:27.848Z HTTP 200 http://localhost:8411/integrations
2026-10-20T07:51:27.854Z HTTP 200 http://localhost:8411/session/s3bee57561d744ff8a5cf63fc5bff34f9
2026-10-20T07:51:27.888Z HTTP 200 http://localhost:8411/integrations
2026-10-20T07:51:27.893Z HTTP 200 http://localhost:8411/known/s3bee57561d744ff8a5cf63fc5bff34f9
2026-10-20T07:51:27.900Z HTTP 200 http://localhost:8411/sessions/s3bee57561d744ff8a5cf63fc5bff34f9/versions
2026-10-20T07:51:27.901Z HTTP 200 http://localhost:8411/known/s3bee57561d744ff8a5cf63fc5bff34f9
2026-10-20T07:51:27.924Z HTTP 200 http://localhost:8411/sessions
2026-10-20T07:51:27.937Z HTTP 200 http://localhost:8411/session/s3bee57561d744ff8a5cf63fc5bff34f9?version=v1
2026-10-20T07:51:27.966Z HTTP 200 http://localhost:8411/sessions
2026-10-20T07:51:27.982Z HTTP 200 http://localhost:8411/context/s3bee57561d744ff8a5cf63fc5bff34f9?version=v1
2026-10-20T07:51:27.983Z HTTP 200 http://localhost:8411/known/s3bee57561d744ff8a5cf63fc5bff34f9?version=v1
2026-10-20T07:51:27.984Z HTTP 200 http://localhost:8411/sessions/s3bee57561d744ff8a5cf63fc5bff34f9/versions
2026-10-20T07:51:27.984Z HTTP 200 http://localhost:8411/context/s3bee57561d744ff8a5cf63fc5bff34f9?version=v1
2026-10-20T07:51:27.985Z HTTP 200 http://localhost:8411/sessions
2026-10-20T07:51:27.986Z HTTP 200 http://localhost:8411/sessions
2026-10-20T07:51:28.017Z HTTP 200 http://localhost:8411/session/s3bee57561d744ff8a5cf63fc5bff34f9?version=v1
2026-10-20T07:51:28.170Z HTTP 200 http://localhost:8411/session/sa0e61b32fcd940bebff92bc1e0189a8f
2026-10-20T07:51:28.196Z HTTP 200 http://localhost:8411/integrations
2026-10-20T07:51:28.196Z HTTP 200 http://localhost:8411/known/sa0e61b32fcd940bebff92bc1e0189a8f
2026-10-20T07:51:28.202Z HTTP 200 http://localhost:8411/sessions/sa0e61b32fcd940bebff92bc1e0189a8f/versions
2026-10-20T07:53:59.976Z HTTP 200 http://localhost:8411/chat
2026-10-20T07:54:00.097Z HTTP 200 http://localhost:8411/sessions
2026-10-20T07:54:00.236Z HTTP 200 http://localhost:8411/sessions/s3bee57561d744ff8a5cf63fc5bff34f9/versions
2026-10-20T07:54:00.241Z HTTP 200 http://localhost:8411/session/s3bee57561d744ff8a5cf63fc5bff34f9?version=v1
```

## Captured state / API output

```json
{
  "time": "2026-10-20T07:54:00.490Z",
  "redirect": {
    "time": "2026-10-20T07:51:01.847Z",
    "url": "http://localhost:3411/pipeline/insights",
    "body": "8-E 인사이트 도출 › 인사이트별 Pain Point\n인사이트 0개 · 대화형\n인사이트 도출\n\n페르소나를 바탕으로 인사이트를 도출하세요."
  },
  "chat": {
    "url": "http://localhost:8411/chat",
    "status": 200,
    "request": "{\"sid\":\"s3bee57561d744ff8a5cf63fc5bff34f9\",\"query\":\"현재 전처리 상태를 알려주세요.\",\"pipeline_context\":\"제품:QA 전처리 실행, 세션:s3bee57561d744ff8a5cf63fc5bff34f9, 현재단계:시작, 키워드:0개\",\"novel\":true}",
    "body": {
      "status": "ok",
      "answer": "답변 모델이 연결되지 않아 근거 원문만 보여 줍니다.",
      "sources": [],
      "reason": "no_labels"
    }
  },
  "panel": "파이프라인 챗봇\n\n파이프라인 진행이나 결과에 대해 물어보세요.\n\n현재 전처리 상태를 알려주세요.\n\n답변 모델이 연결되지 않아 근거 원문만 보여 줍니다.\n\n근거 원문 0건\n새 발견 찾기\n\n검색할 근거 원문이 없습니다. 라벨 판정을 먼저 완료하세요.\n\n새 발견 찾기\n전송",
  "insight": {
    "url": "http://127.0.0.1:8411/insight-chat",
    "status": 200,
    "request": {
      "sid": "s3bee57561d744ff8a5cf63fc5bff34f9",
      "query": "현재 전처리 상태를 알려주세요.",
      "bk": "QA 전처리 실행",
      "novel": true
    },
    "body": "{\"status\":\"ok\",\"answer\":\"답변 모델이 연결되지 않아 근거 원문만 보여 줍니다.\",\"sources\":[],\"reason\":\"no_labels\",\"modified\":false}"
  }
}
```

## Execution notes

First response waiter used URL, unavailable in this tool's VM; actual first POST still returned 200. Retry used the observed URL string and verified panel text. The failed tool attempt is retained in chat-redirect-tool.json. Insight chat UI is deliberately not asserted because D-306 makes it unreachable. No answer-quality assertion or LLM-key requirement.
