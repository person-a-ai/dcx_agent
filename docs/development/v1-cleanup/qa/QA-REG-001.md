# QA-REG-001

```json
{
  "id": "QA-REG-001",
  "url": "http://localhost:3411/pipeline/insights",
  "result": "FAIL",
  "expected": "Pipeline chatbot opens, POST /chat not 404, panel shows answer/error; insight screen chatbot uses reachable POST /insight-chat.",
  "actual": "{\"chat\":{\"status\":200,\"body\":\"{\\\"status\\\":\\\"ok\\\",\\\"answer\\\":\\\"답변 모델이 연결되지 않아 근거 원문만 보여 줍니다.\\\",\\\"sources\\\":[],\\\"reason\\\":\\\"no_labels\\\"}\",\"request\":\"{\\\"sid\\\":\\\"sf7d9d6897a31472895cf5fdeafb9cea1\\\",\\\"query\\\":\\\"QA: 전처리 결과를 요약해 주세요.\\\",\\\"pipeline_context\\\":\\\"제품:QA 전처리 실행, 세션:sf7d9d6897a31472895cf5fdeafb9cea1, 현재단계:시작, 키워드:0개\\\",\\\"novel\\\":true}\"},\"chatPanelAnswer\":true,\"insightApiProbe\":{\"status\":200,\"body\":\"{\\\"status\\\":\\\"ok\\\",\\\"answer\\\":\\\"답변 모델이 연결되지 않아 근거 원문만 보여 줍니다.\\\",\\\"sources\\\":[],\\\"reason\\\":\\\"no_labels\\\",\\\"modified\\\":false}\"},\"insightUi\":\"On /pipeline/insights visible chatbot is 파이프라인 챗봇 and sends /chat. /insights redirects immediately; no reachable legacy insight chatbot observed.\"}",
  "evidence": "docs/development/v1-cleanup/qa/QA-REG-001.md",
  "time": "2026-10-20T04:23:17.780Z",
  "steps": [
    "Opened chatbot on insight page",
    "Sent real UI message and captured POST /chat plus displayed fallback answer",
    "Navigated /insights and observed redirect",
    "Inspected available UI; legacy insight chatbot is not reachable",
    "Supplemental direct POST /insight-chat to verify endpoint existence"
  ],
  "screenshot": "/Users/yunho/Documents/dcx_agent-v1-cleanup/docs/development/v1-cleanup/qa/QA-REG-001.png",
  "chatPanelScreenshot": "/Users/yunho/Documents/dcx_agent-v1-cleanup/docs/development/v1-cleanup/qa/QA-REG-001-chat.png",
  "chatPanelText": "파이프라인\n시작\n키워드\n크롤링\n전처리\n5\n라벨링\n6\n학습\n7\n클러스터링\n8\n근거 탐색\n9\n페르소나\n10\n인사이트\n진행 중\nQA 전처리 실행\nv1 · 활성 버전 목록 열기\n검토 대기\nKnown Insight · 0\n외부 API · 0/2 연결 열기\n내부용\n8-E 인사이트 도출 › 인사이트별 Pain Point\n인사이트 0개 · 대화형\n인사이트 도출\n\n페르소나를 바탕으로 인사이트를 도출하세요.\n\n파이프라인 챗봇\n\n파이프라인 진행이나 결과에 대해 물어보세요.\n\nQA: 전처리 결과를 요약해 주세요.\n\n답변 모델이 연결되지 않아 근거 원문만 보여 줍니다.\n\n근거 원문 0건\n새 발견 찾기\n\n검색할 근거 원문이 없습니다. 라벨 판정을 먼저 완료하세요.\n\n새 발견 찾기\n전송",
  "insightApiProbe": {
    "status": 200,
    "body": "{\"status\":\"ok\",\"answer\":\"답변 모델이 연결되지 않아 근거 원문만 보여 줍니다.\",\"sources\":[],\"reason\":\"no_labels\",\"modified\":false}"
  },
  "limitation": "Direct API probe proves route survival, but does not substitute for requested insight chatbot UI integration."
}
```

