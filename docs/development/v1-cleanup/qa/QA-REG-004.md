# QA-REG-004

```json
{
  "id": "QA-REG-004",
  "url": "http://localhost:3411/pipeline/keywords",
  "result": "PASS",
  "expected": "Keyword page opens with zero error-level console messages.",
  "actual": "{\"body\":\"이 단계부터 다시\\n1단계 · 키워드\\nR1 초기 발산 결과 0개를 검토합니다\\n\\n거절할 키워드를 누르고 사유를 남기면 다음 라운드에 반영됩니다. 드래그하거나 M 키로 하위 카테고리를 옮길 수 있습니다.\\n\\nR1 · 현재\\n초기 발산\\n5W1H · JTBD\\nR2\\n인접 확장\\nSCAMPER 대체·결합·응용\\nR3\\n수렴 · 균형\\n분포 · 거절 · 커버리지\\nR4\\n재발산\\n역발상 · 제거 · 부정 공간\\n최종\\n최종 검토\\n크롤링으로 전달\\n검토할 라운드\\nR1\\n다음 라운드 방향 지시 (선택)\\n지시 저장하기\\n전체0\\n물리0\\n심리0\\n행동0\\n전체 0\\n판단 필요 0\\nLLM 단독 0\\n검색량 적음 0\\n미연결 0\\n거절됨 0\\n수동 0\\n키워드 검색\\n키보드 도움말 보기\\n모두 접기\\n조건에 맞는 키워드가 없습니다. 필터를 해제하세요.\\n물리 › 시간 접기\\n0\\n직접 추가하기\\n물리 › 공간 접기\\n0\\n직접 추가하기\\n물리 › 사회적 환경 접기\\n0\\n직접 추가하기\\n물리 › 감각 접기\\n0\\n직접 추가하기\\n물리 › 신체 상태 접기\\n0\\n직접 추가하기\\n물리 › 제품·물리 상호작용 접기\\n0\\n직접 추가하기\\n새 하위 카테고리 축\\n축 선택\\n물리\\n심리\\n행동\\n새 하위 카테고리 이름\\n하위 카테고리 추가하기\\n축 분포\\n\\n승인 예정 포함 0개 기준 · 부족한 축은 다음 라운드가 채웁니다.\\n\\n물리\\n0개 · 0%\\n심리\\n0개 · 0%\\n행동\\n0개 · 0%\\n커버리지\\nR1 확정 후 계산\\nkeyword_feedback.md 미리보기 내부용\\n\\n승인 예정 0 · 거절 0\\n\\n변경 사항 없음\\n임시 저장\\n저장\\n생성하기\\n다음 라운드 생성\",\"errorCount\":0}",
  "evidence": "docs/development/v1-cleanup/qa/QA-REG-004.md",
  "time": "2026-10-20T04:23:41.248Z",
  "steps": [
    "Opened /pipeline/keywords with completed session",
    "Waited for loading indicator to disappear",
    "Inspected rendered page and console"
  ],
  "screenshot": "/Users/yunho/Documents/dcx_agent-v1-cleanup/docs/development/v1-cleanup/qa/QA-REG-004.png",
  "console": [
    {
      "time": "2026-10-20T04:23:27.935Z",
      "type": "log",
      "text": "[Fast Refresh] rebuilding"
    },
    {
      "time": "2026-10-20T04:23:28.196Z",
      "type": "info",
      "text": "%cDownload the React DevTools for a better development experience: https://react.dev/link/react-devtools font-weight:bold"
    },
    {
      "time": "2026-10-20T04:23:28.210Z",
      "type": "log",
      "text": "[HMR] connected"
    },
    {
      "time": "2026-10-20T04:23:28.224Z",
      "type": "warning",
      "text": "Image with src \"/person-a-logo.png\" has either width or height modified, but not the other. If you use CSS to change the size of your image, also include the styles 'width: \"auto\"' or 'height: \"auto\"' to maintain the aspect ratio."
    }
  ],
  "network": [
    {
      "time": "2026-10-20T04:23:28.224Z",
      "method": "GET",
      "url": "http://localhost:8411/integrations",
      "body": null
    },
    {
      "time": "2026-10-20T04:23:28.224Z",
      "method": "GET",
      "url": "http://localhost:8411/session/sf7d9d6897a31472895cf5fdeafb9cea1",
      "body": null
    },
    {
      "time": "2026-10-20T04:23:28.227Z",
      "status": 200,
      "url": "http://localhost:8411/integrations",
      "body": "[{\"name\":\"openai\",\"connected\":false,\"env_vars\":[\"OPENAI_API_KEY\",\"OPENAI_MODEL\"],\"affects\":[\"llm\"],\"last_error\":null},{\"name\":\"claude\",\"connected\":false,\"env_vars\":[\"CLAUDE_API_KEY\"],\"affects\":[\"llm\"],\"last_error\":null}]"
    },
    {
      "time": "2026-10-20T04:23:28.243Z",
      "method": "GET",
      "url": "http://localhost:8411/sessions",
      "body": null
    },
    {
      "time": "2026-10-20T04:23:28.244Z",
      "method": "GET",
      "url": "http://localhost:8411/integrations",
      "body": null
    },
    {
      "time": "2026-10-20T04:23:28.244Z",
      "method": "GET",
      "url": "http://localhost:8411/known/sf7d9d6897a31472895cf5fdeafb9cea1",
      "body": null
    },
    {
      "time": "2026-10-20T04:23:28.244Z",
      "method": "GET",
      "url": "http://localhost:8411/sessions/sf7d9d6897a31472895cf5fdeafb9cea1/versions",
      "body": null
    },
    {
      "time": "2026-10-20T04:23:28.244Z",
      "method": "GET",
      "url": "http://localhost:8411/sessions",
      "body": null
    },
    {
      "time": "2026-10-20T04:23:28.244Z",
      "method": "GET",
      "url": "http://localhost:8411/integrations",
      "body": null
    },
    {
      "time": "2026-10-20T04:23:28.245Z",
      "method": "GET",
      "url": "http://localhost:8411/known/sf7d9d6897a31472895cf5fdeafb9cea1",
      "body": null
    },
    {
      "time": "2026-10-20T04:23:28.230Z",
      "status": 200,
      "url": "http://localhost:8411/session/sf7d9d6897a31472895cf5fdeafb9cea1",
      "body": "{\"status\":\"ok\",\"data\":{\"schemaVersion\":2,\"sid\":\"sf7d9d6897a31472895cf5fdeafb9cea1\",\"step\":\"start\",\"drafts\":{\"prep\":null},\"projectContext\":{\"bk\":\"QA 전처리 실행\",\"oneLiner\":\"QA용 세션\",\"researchQuestion\":{\"text\":\"냉방 경험은?\",\"template\":null},\"projectType\":{\"choice\":\"new\",\"note\":\"\"},\"taskMode\":null,\"analysisGoal\":{\"choice\":\"needs\",\"note\":\"\"},\"keyMetrics\":[{\"name\":\"만족\",\"source\":\"\",\"item\":\"\"}],\"constraints\":[],\"positioning\":{\"price\":\"value\",\"market\":\"new\",\"priceText\":\"\",\"marketText\":\"\"},\"personaSeeds\":null,\"channels\":[\"fixture\"],\"knownInsights\":[],\"productCategory\":{\"l1\":\"가전\",\"l2\":null,\"l3\":null,\"source\":\"user\"},\"targetScope\":null,\"futureCustomer\":null,\"schemaVersion\":1},\"knownInsights\":[],\"version\":\"v1\",\"updatedAt\":\"2026-10-20T04:21:42.270428+00:00\",\"collectionId\":\"c1\",\"prep\":{\"config\":{\"adFilter\":[],\"excludeSources\":[],\"excludeChannels\":[],\"minBodyChars\":10,\"boilerplate\":{\"naver_cafe\":[\"카페 회원이 되시면 전체 내용을 볼 수 있습니다.\",\"카페 가입하기\"],\"naver_blog\":[\"공감\",\"이웃추가\"],\"clien\":[],\"ppomppu\":[],\"youtube\":[]},\"analyzer\":\"kiwi\",\"tokenPos\":[\"NNG\",\"NNP\",\"VV\",\"VA\",\"XR\"],\"embedder\":\"fake\",\"embedModel\":\"voyage-4\",\"embedDim\":1024},\"derivedRef\":{\"collectionId\":\"c1\",\"prepKey\":\"p_8d4420d74b0b\"},\"status\":\"done\",\"savedAt\":\"2026-10-20T04:21:42.261446+00:00\",\"reused\":true,\"runId\":null},\"completion\":{\"crawlDone\":true,\"prepDone\":true,\"labelingDone\":false,\"exportDone\":false,\"clustersDone\":false,\"segmentDone\":false,\"personaDone\":false,\"insightDone\":false,\"evidenceDone\":false}}}"
    },
    {
      "time": "2026-10-20T04:23:28.255Z",
      "method": "GET",
      "url": "http://localhost:8411/session/sf7d9d6897a31472895cf5fdeafb9cea1?version=v1",
      "body": null
    },
    {
      "time": "2026-10-20T04:23:28.253Z",
      "status": 200,
      "url": "http://localhost:8411/integrations",
      "body": "[{\"name\":\"openai\",\"connected\":false,\"env_vars\":[\"OPENAI_API_KEY\",\"OPENAI_MODEL\"],\"affects\":[\"llm\"],\"last_error\":null},{\"name\":\"claude\",\"connected\":false,\"env_vars\":[\"CLAUDE_API_KEY\"],\"affects\":[\"llm\"],\"last_error\":null}]"
    },
    {
      "time": "2026-10-20T04:23:28.253Z",
      "status": 200,
      "url": "http://localhost:8411/known/sf7d9d6897a31472895cf5fdeafb9cea1",
      "body": "{\"items\":[]}"
    },
    {
      "time": "2026-10-20T04:23:28.254Z",
      "status": 200,
      "url": "http://localhost:8411/sessions/sf7d9d6897a31472895cf5fdeafb9cea1/versions",
      "body": "{\"activeVersion\":\"v1\",\"versions\":[{\"id\":\"v1\",\"parent\":null,\"restartFrom\":\"stage0\",\"createdAt\":\"2026-10-20T04:15:20.626738+00:00\",\"note\":\"\",\"readonly\":false,\"collectionId\":\"c1\"}]}"
    },
    {
      "time": "2026-10-20T04:23:28.254Z",
      "status": 200,
      "url": "http://localhost:8411/known/sf7d9d6897a31472895cf5fdeafb9cea1",
      "body": "{\"items\":[]}"
    },
    {
      "time": "2026-10-20T04:23:28.255Z",
      "status": 200,
      "url": "http://localhost:8411/sessions",
      "body": "{\"status\":\"ok\",\"sessions\":[{\"sid\":\"sf7d9d6897a31472895cf5fdeafb9cea1\",\"bk\":\"QA 전처리 실행\",\"step\":\"start\",\"schemaVersion\":2,\"legacy\":false,\"activity\":null,\"updatedAt\":\"2026-10-20T04:21:42.270428+00:00\"},{\"sid\":\"qaold\",\"bk\":\"QA 옛 세션\",\"step\":\"clustering\",\"schemaVersion\":null,\"legacy\":true,\"activity\":null,\"updatedAt\":\"2026-10-20T04:15:20.634998+00:00\"},{\"sid\":\"s044bfc25b18847d6a3f7679e41f1d0cb\",\"bk\":\"QA 전처리 전\",\"step\":\"start\",\"schemaVersion\":2,\"legacy\":false,\"activity\":null,\"updatedAt\":\"2026-10-20T04:15:20.624132+00:00\"}]}"
    },
    {
      "time": "2026-10-20T04:23:28.260Z",
      "status": 200,
      "url": "http://localhost:8411/sessions",
      "body": "{\"status\":\"ok\",\"sessions\":[{\"sid\":\"sf7d9d6897a31472895cf5fdeafb9cea1\",\"bk\":\"QA 전처리 실행\",\"step\":\"start\",\"schemaVersion\":2,\"legacy\":false,\"activity\":null,\"updatedAt\":\"2026-10-20T04:21:42.270428+00:00\"},{\"sid\":\"qaold\",\"bk\":\"QA 옛 세션\",\"step\":\"clustering\",\"schemaVersion\":null,\"legacy\":true,\"activity\":null,\"updatedAt\":\"2026-10-20T04:15:20.634998+00:00\"},{\"sid\":\"s044bfc25b18847d6a3f7679e41f1d0cb\",\"bk\":\"QA 전처리 전\",\"step\":\"start\",\"schemaVersion\":2,\"legacy\":false,\"activity\":null,\"updatedAt\":\"2026-10-20T04:15:20.624132+00:00\"}]}"
    },
    {
      "time": "2026-10-20T04:23:28.260Z",
      "status": 200,
      "url": "http://localhost:8411/session/sf7d9d6897a31472895cf5fdeafb9cea1?version=v1",
      "body": "{\"status\":\"ok\",\"data\":{\"schemaVersion\":2,\"sid\":\"sf7d9d6897a31472895cf5fdeafb9cea1\",\"step\":\"start\",\"drafts\":{\"prep\":null},\"projectContext\":{\"bk\":\"QA 전처리 실행\",\"oneLiner\":\"QA용 세션\",\"researchQuestion\":{\"text\":\"냉방 경험은?\",\"template\":null},\"projectType\":{\"choice\":\"new\",\"note\":\"\"},\"taskMode\":null,\"analysisGoal\":{\"choice\":\"needs\",\"note\":\"\"},\"keyMetrics\":[{\"name\":\"만족\",\"source\":\"\",\"item\":\"\"}],\"constraints\":[],\"positioning\":{\"price\":\"value\",\"market\":\"new\",\"priceText\":\"\",\"marketText\":\"\"},\"personaSeeds\":null,\"channels\":[\"fixture\"],\"knownInsights\":[],\"productCategory\":{\"l1\":\"가전\",\"l2\":null,\"l3\":null,\"source\":\"user\"},\"targetScope\":null,\"futureCustomer\":null,\"schemaVersion\":1},\"knownInsights\":[],\"version\":\"v1\",\"updatedAt\":\"2026-10-20T04:21:42.270428+00:00\",\"collectionId\":\"c1\",\"prep\":{\"config\":{\"adFilter\":[],\"excludeSources\":[],\"excludeChannels\":[],\"minBodyChars\":10,\"boilerplate\":{\"naver_cafe\":[\"카페 회원이 되시면 전체 내용을 볼 수 있습니다.\",\"카페 가입하기\"],\"naver_blog\":[\"공감\",\"이웃추가\"],\"clien\":[],\"ppomppu\":[],\"youtube\":[]},\"analyzer\":\"kiwi\",\"tokenPos\":[\"NNG\",\"NNP\",\"VV\",\"VA\",\"XR\"],\"embedder\":\"fake\",\"embedModel\":\"voyage-4\",\"embedDim\":1024},\"derivedRef\":{\"collectionId\":\"c1\",\"prepKey\":\"p_8d4420d74b0b\"},\"status\":\"done\",\"savedAt\":\"2026-10-20T04:21:42.261446+00:00\",\"reused\":true,\"runId\":null},\"completion\":{\"crawlDone\":true,\"prepDone\":true,\"labelingDone\":false,\"exportDone\":false,\"clustersDone\":false,\"segmentDone\":false,\"personaDone\":false,\"insightDone\":false,\"evidenceDone\":false}}}"
    },
    {
      "time": "2026-10-20T04:23:28.271Z",
      "method": "GET",
      "url": "http://localhost:8411/keywords/sf7d9d6897a31472895cf5fdeafb9cea1?version=v1",
      "body": null
    },
    {
      "time": "2026-10-20T04:23:28.271Z",
      "method": "GET",
      "url": "http://localhost:8411/session/sf7d9d6897a31472895cf5fdeafb9cea1?version=v1",
      "body": null
    },
    {
      "time": "2026-10-20T04:23:28.271Z",
      "method": "GET",
      "url": "http://localhost:8411/known/sf7d9d6897a31472895cf5fdeafb9cea1?version=v1",
      "body": null
    },
    {
      "time": "2026-10-20T04:23:28.271Z",
      "method": "GET",
      "url": "http://localhost:8411/sessions/sf7d9d6897a31472895cf5fdeafb9cea1/versions",
      "body": null
    },
    {
      "time": "2026-10-20T04:23:28.272Z",
      "method": "GET",
      "url": "http://localhost:8411/keywords/sf7d9d6897a31472895cf5fdeafb9cea1?version=v1",
      "body": null
    },
    {
      "time": "2026-10-20T04:23:28.272Z",
      "method": "GET",
      "url": "http://localhost:8411/session/sf7d9d6897a31472895cf5fdeafb9cea1?version=v1",
      "body": null
    },
    {
      "time": "2026-10-20T04:23:28.272Z",
      "status": 200,
      "url": "http://localhost:8411/known/sf7d9d6897a31472895cf5fdeafb9cea1?version=v1",
      "body": "{\"items\":[]}"
    },
    {
      "time": "2026-10-20T04:23:28.279Z",
      "method": "GET",
      "url": "http://localhost:8411/session/sf7d9d6897a31472895cf5fdeafb9cea1?version=v1",
      "body": null
    },
    {
      "time": "2026-10-20T04:23:28.277Z",
      "status": 200,
      "url": "http://localhost:8411/keywords/sf7d9d6897a31472895cf5fdeafb9cea1?version=v1",
      "body": "{\"keywordRounds\":{},\"coverage\":{},\"keywords\":[],\"feedback_md\":\"\"}"
    },
    {
      "time": "2026-10-20T04:23:28.278Z",
      "status": 200,
      "url": "http://localhost:8411/sessions/sf7d9d6897a31472895cf5fdeafb9cea1/versions",
      "body": "{\"activeVersion\":\"v1\",\"versions\":[{\"id\":\"v1\",\"parent\":null,\"restartFrom\":\"stage0\",\"createdAt\":\"2026-10-20T04:15:20.626738+00:00\",\"note\":\"\",\"readonly\":false,\"collectionId\":\"c1\"}]}"
    },
    {
      "time": "2026-10-20T04:23:28.278Z",
      "status": 200,
      "url": "http://localhost:8411/keywords/sf7d9d6897a31472895cf5fdeafb9cea1?version=v1",
      "body": "{\"keywordRounds\":{},\"coverage\":{},\"keywords\":[],\"feedback_md\":\"\"}"
    },
    {
      "time": "2026-10-20T04:23:28.278Z",
      "status": 200,
      "url": "http://localhost:8411/session/sf7d9d6897a31472895cf5fdeafb9cea1?version=v1",
      "body": "{\"status\":\"ok\",\"data\":{\"schemaVersion\":2,\"sid\":\"sf7d9d6897a31472895cf5fdeafb9cea1\",\"step\":\"start\",\"drafts\":{\"prep\":null},\"projectContext\":{\"bk\":\"QA 전처리 실행\",\"oneLiner\":\"QA용 세션\",\"researchQuestion\":{\"text\":\"냉방 경험은?\",\"template\":null},\"projectType\":{\"choice\":\"new\",\"note\":\"\"},\"taskMode\":null,\"analysisGoal\":{\"choice\":\"needs\",\"note\":\"\"},\"keyMetrics\":[{\"name\":\"만족\",\"source\":\"\",\"item\":\"\"}],\"constraints\":[],\"positioning\":{\"price\":\"value\",\"market\":\"new\",\"priceText\":\"\",\"marketText\":\"\"},\"personaSeeds\":null,\"channels\":[\"fixture\"],\"knownInsights\":[],\"productCategory\":{\"l1\":\"가전\",\"l2\":null,\"l3\":null,\"source\":\"user\"},\"targetScope\":null,\"futureCustomer\":null,\"schemaVersion\":1},\"knownInsights\":[],\"version\":\"v1\",\"updatedAt\":\"2026-10-20T04:21:42.270428+00:00\",\"collectionId\":\"c1\",\"prep\":{\"config\":{\"adFilter\":[],\"excludeSources\":[],\"excludeChannels\":[],\"minBodyChars\":10,\"boilerplate\":{\"naver_cafe\":[\"카페 회원이 되시면 전체 내용을 볼 수 있습니다.\",\"카페 가입하기\"],\"naver_blog\":[\"공감\",\"이웃추가\"],\"clien\":[],\"ppomppu\":[],\"youtube\":[]},\"analyzer\":\"kiwi\",\"tokenPos\":[\"NNG\",\"NNP\",\"VV\",\"VA\",\"XR\"],\"embedder\":\"fake\",\"embedModel\":\"voyage-4\",\"embedDim\":1024},\"derivedRef\":{\"collectionId\":\"c1\",\"prepKey\":\"p_8d4420d74b0b\"},\"status\":\"done\",\"savedAt\":\"2026-10-20T04:21:42.261446+00:00\",\"reused\":true,\"runId\":null},\"completion\":{\"crawlDone\":true,\"prepDone\":true,\"labelingDone\":false,\"exportDone\":false,\"clustersDone\":false,\"segmentDone\":false,\"personaDone\":false,\"insightDone\":false,\"evidenceDone\":false}}}"
    },
    {
      "time": "2026-10-20T04:23:28.279Z",
      "status": 200,
      "url": "http://localhost:8411/session/sf7d9d6897a31472895cf5fdeafb9cea1?version=v1",
      "body": "{\"status\":\"ok\",\"data\":{\"schemaVersion\":2,\"sid\":\"sf7d9d6897a31472895cf5fdeafb9cea1\",\"step\":\"start\",\"drafts\":{\"prep\":null},\"projectContext\":{\"bk\":\"QA 전처리 실행\",\"oneLiner\":\"QA용 세션\",\"researchQuestion\":{\"text\":\"냉방 경험은?\",\"template\":null},\"projectType\":{\"choice\":\"new\",\"note\":\"\"},\"taskMode\":null,\"analysisGoal\":{\"choice\":\"needs\",\"note\":\"\"},\"keyMetrics\":[{\"name\":\"만족\",\"source\":\"\",\"item\":\"\"}],\"constraints\":[],\"positioning\":{\"price\":\"value\",\"market\":\"new\",\"priceText\":\"\",\"marketText\":\"\"},\"personaSeeds\":null,\"channels\":[\"fixture\"],\"knownInsights\":[],\"productCategory\":{\"l1\":\"가전\",\"l2\":null,\"l3\":null,\"source\":\"user\"},\"targetScope\":null,\"futureCustomer\":null,\"schemaVersion\":1},\"knownInsights\":[],\"version\":\"v1\",\"updatedAt\":\"2026-10-20T04:21:42.270428+00:00\",\"collectionId\":\"c1\",\"prep\":{\"config\":{\"adFilter\":[],\"excludeSources\":[],\"excludeChannels\":[],\"minBodyChars\":10,\"boilerplate\":{\"naver_cafe\":[\"카페 회원이 되시면 전체 내용을 볼 수 있습니다.\",\"카페 가입하기\"],\"naver_blog\":[\"공감\",\"이웃추가\"],\"clien\":[],\"ppomppu\":[],\"youtube\":[]},\"analyzer\":\"kiwi\",\"tokenPos\":[\"NNG\",\"NNP\",\"VV\",\"VA\",\"XR\"],\"embedder\":\"fake\",\"embedModel\":\"voyage-4\",\"embedDim\":1024},\"derivedRef\":{\"collectionId\":\"c1\",\"prepKey\":\"p_8d4420d74b0b\"},\"status\":\"done\",\"savedAt\":\"2026-10-20T04:21:42.261446+00:00\",\"reused\":true,\"runId\":null},\"completion\":{\"crawlDone\":true,\"prepDone\":true,\"labelingDone\":false,\"exportDone\":false,\"clustersDone\":false,\"segmentDone\":false,\"personaDone\":false,\"insightDone\":false,\"evidenceDone\":false}}}"
    },
    {
      "time": "2026-10-20T04:23:28.298Z",
      "status": 200,
      "url": "http://localhost:8411/session/sf7d9d6897a31472895cf5fdeafb9cea1?version=v1",
      "body": "{\"status\":\"ok\",\"data\":{\"schemaVersion\":2,\"sid\":\"sf7d9d6897a31472895cf5fdeafb9cea1\",\"step\":\"start\",\"drafts\":{\"prep\":null},\"projectContext\":{\"bk\":\"QA 전처리 실행\",\"oneLiner\":\"QA용 세션\",\"researchQuestion\":{\"text\":\"냉방 경험은?\",\"template\":null},\"projectType\":{\"choice\":\"new\",\"note\":\"\"},\"taskMode\":null,\"analysisGoal\":{\"choice\":\"needs\",\"note\":\"\"},\"keyMetrics\":[{\"name\":\"만족\",\"source\":\"\",\"item\":\"\"}],\"constraints\":[],\"positioning\":{\"price\":\"value\",\"market\":\"new\",\"priceText\":\"\",\"marketText\":\"\"},\"personaSeeds\":null,\"channels\":[\"fixture\"],\"knownInsights\":[],\"productCategory\":{\"l1\":\"가전\",\"l2\":null,\"l3\":null,\"source\":\"user\"},\"targetScope\":null,\"futureCustomer\":null,\"schemaVersion\":1},\"knownInsights\":[],\"version\":\"v1\",\"updatedAt\":\"2026-10-20T04:21:42.270428+00:00\",\"collectionId\":\"c1\",\"prep\":{\"config\":{\"adFilter\":[],\"excludeSources\":[],\"excludeChannels\":[],\"minBodyChars\":10,\"boilerplate\":{\"naver_cafe\":[\"카페 회원이 되시면 전체 내용을 볼 수 있습니다.\",\"카페 가입하기\"],\"naver_blog\":[\"공감\",\"이웃추가\"],\"clien\":[],\"ppomppu\":[],\"youtube\":[]},\"analyzer\":\"kiwi\",\"tokenPos\":[\"NNG\",\"NNP\",\"VV\",\"VA\",\"XR\"],\"embedder\":\"fake\",\"embedModel\":\"voyage-4\",\"embedDim\":1024},\"derivedRef\":{\"collectionId\":\"c1\",\"prepKey\":\"p_8d4420d74b0b\"},\"status\":\"done\",\"savedAt\":\"2026-10-20T04:21:42.261446+00:00\",\"reused\":true,\"runId\":null},\"completion\":{\"crawlDone\":true,\"prepDone\":true,\"labelingDone\":false,\"exportDone\":false,\"clustersDone\":false,\"segmentDone\":false,\"personaDone\":false,\"insightDone\":false,\"evidenceDone\":false}}}"
    },
    {
      "time": "2026-10-20T04:23:38.256Z",
      "method": "GET",
      "url": "http://localhost:8411/sessions",
      "body": null
    },
    {
      "time": "2026-10-20T04:23:38.272Z",
      "method": "GET",
      "url": "http://localhost:8411/sessions/sf7d9d6897a31472895cf5fdeafb9cea1/versions",
      "body": null
    },
    {
      "time": "2026-10-20T04:23:38.279Z",
      "method": "GET",
      "url": "http://localhost:8411/session/sf7d9d6897a31472895cf5fdeafb9cea1?version=v1",
      "body": null
    },
    {
      "time": "2026-10-20T04:23:38.274Z",
      "status": 200,
      "url": "http://localhost:8411/sessions",
      "body": "{\"status\":\"ok\",\"sessions\":[{\"sid\":\"sf7d9d6897a31472895cf5fdeafb9cea1\",\"bk\":\"QA 전처리 실행\",\"step\":\"start\",\"schemaVersion\":2,\"legacy\":false,\"activity\":null,\"updatedAt\":\"2026-10-20T04:21:42.270428+00:00\"},{\"sid\":\"qaold\",\"bk\":\"QA 옛 세션\",\"step\":\"clustering\",\"schemaVersion\":null,\"legacy\":true,\"activity\":null,\"updatedAt\":\"2026-10-20T04:15:20.634998+00:00\"},{\"sid\":\"s044bfc25b18847d6a3f7679e41f1d0cb\",\"bk\":\"QA 전처리 전\",\"step\":\"start\",\"schemaVersion\":2,\"legacy\":false,\"activity\":null,\"updatedAt\":\"2026-10-20T04:15:20.624132+00:00\"}]}"
    },
    {
      "time": "2026-10-20T04:23:38.279Z",
      "status": 200,
      "url": "http://localhost:8411/sessions/sf7d9d6897a31472895cf5fdeafb9cea1/versions",
      "body": "{\"activeVersion\":\"v1\",\"versions\":[{\"id\":\"v1\",\"parent\":null,\"restartFrom\":\"stage0\",\"createdAt\":\"2026-10-20T04:15:20.626738+00:00\",\"note\":\"\",\"readonly\":false,\"collectionId\":\"c1\"}]}"
    },
    {
      "time": "2026-10-20T04:23:38.287Z",
      "status": 200,
      "url": "http://localhost:8411/session/sf7d9d6897a31472895cf5fdeafb9cea1?version=v1",
      "body": "{\"status\":\"ok\",\"data\":{\"schemaVersion\":2,\"sid\":\"sf7d9d6897a31472895cf5fdeafb9cea1\",\"step\":\"start\",\"drafts\":{\"prep\":null},\"projectContext\":{\"bk\":\"QA 전처리 실행\",\"oneLiner\":\"QA용 세션\",\"researchQuestion\":{\"text\":\"냉방 경험은?\",\"template\":null},\"projectType\":{\"choice\":\"new\",\"note\":\"\"},\"taskMode\":null,\"analysisGoal\":{\"choice\":\"needs\",\"note\":\"\"},\"keyMetrics\":[{\"name\":\"만족\",\"source\":\"\",\"item\":\"\"}],\"constraints\":[],\"positioning\":{\"price\":\"value\",\"market\":\"new\",\"priceText\":\"\",\"marketText\":\"\"},\"personaSeeds\":null,\"channels\":[\"fixture\"],\"knownInsights\":[],\"productCategory\":{\"l1\":\"가전\",\"l2\":null,\"l3\":null,\"source\":\"user\"},\"targetScope\":null,\"futureCustomer\":null,\"schemaVersion\":1},\"knownInsights\":[],\"version\":\"v1\",\"updatedAt\":\"2026-10-20T04:21:42.270428+00:00\",\"collectionId\":\"c1\",\"prep\":{\"config\":{\"adFilter\":[],\"excludeSources\":[],\"excludeChannels\":[],\"minBodyChars\":10,\"boilerplate\":{\"naver_cafe\":[\"카페 회원이 되시면 전체 내용을 볼 수 있습니다.\",\"카페 가입하기\"],\"naver_blog\":[\"공감\",\"이웃추가\"],\"clien\":[],\"ppomppu\":[],\"youtube\":[]},\"analyzer\":\"kiwi\",\"tokenPos\":[\"NNG\",\"NNP\",\"VV\",\"VA\",\"XR\"],\"embedder\":\"fake\",\"embedModel\":\"voyage-4\",\"embedDim\":1024},\"derivedRef\":{\"collectionId\":\"c1\",\"prepKey\":\"p_8d4420d74b0b\"},\"status\":\"done\",\"savedAt\":\"2026-10-20T04:21:42.261446+00:00\",\"reused\":true,\"runId\":null},\"completion\":{\"crawlDone\":true,\"prepDone\":true,\"labelingDone\":false,\"exportDone\":false,\"clustersDone\":false,\"segmentDone\":false,\"personaDone\":false,\"insightDone\":false,\"evidenceDone\":false}}}"
    }
  ]
}
```

