# QA-EDGE-002

```json
{
  "id": "QA-EDGE-002",
  "url": "http://localhost:3411/pipeline/preprocess",
  "result": "FAIL",
  "expected": "Sidebar locked while initial prep runs, unlocks without refresh after completion, remains linked after reload.",
  "actual": "{\"before\":[{\"text\":\"7클러스터링\",\"href\":null,\"disabled\":\"true\"},{\"text\":\"8근거 탐색\",\"href\":null,\"disabled\":\"true\"},{\"text\":\"9페르소나\",\"href\":null,\"disabled\":\"true\"},{\"text\":\"10인사이트\",\"href\":null,\"disabled\":\"true\"}],\"unlockedBeforeReload\":\"/pipeline/clustering\",\"afterReload\":\"/pipeline/clustering\",\"unlockedWhileRunning\":true}",
  "evidence": "docs/development/v1-cleanup/qa/QA-EDGE-002.md",
  "time": "2026-10-20T04:21:42.778Z",
  "steps": [
    "Observed initial locked nav",
    "MutationObserver recorded nav transition during first run",
    "Observed completed state without reload",
    "Reloaded and checked link persisted"
  ],
  "screenshot": "/Users/yunho/Documents/dcx_agent-v1-cleanup/docs/development/v1-cleanup/qa/QA-EDGE-002.png",
  "transitions": [
    {
      "time": "2026-10-20T04:21:11.411Z",
      "nav": [
        {
          "text": "7클러스터링",
          "href": "/pipeline/clustering",
          "disabled": null
        },
        {
          "text": "8근거 탐색",
          "href": "/pipeline/evidence",
          "disabled": null
        },
        {
          "text": "9페르소나",
          "href": "/pipeline/personas",
          "disabled": null
        },
        {
          "text": "10인사이트",
          "href": "/pipeline/insights",
          "disabled": null
        }
      ],
      "main": " 중복 · 너무 짧은 글만 뺍니다. 대상과 관련 있는지는 4단계에서 판단합니다.\n\n3단계부터 다시\n임시 저장\n전처리 실행\n전처리 진행 중\n\n필터 → 토큰 → 임베딩 · 처리 중\n\n필터 → 토큰 → 임베딩 순서로 처리합니다. 완료된 작업은 이어서 사용합니다.\n\n규칙 필터\n\n본문 + 댓글 기준 · 0~2단계 설정을 그대로 가져왔습니다\n\n분석 채널\n네이버 카페\n네이버 블로그\n유튜브\n뽐뿌\n클리앙\n체크를 끈 채널은 수집본에 있어도 전처리 · 라벨링에서 통째로 뺍니다.\n광고어\n한 줄에 하나씩 입력하세요.\n제외 출처\n출처 이름을 한 줄에 하나씩 입력하세요.\n최소 본문*\n자 (스니펫 문서는 제목 5자 또는 요약 10자)\n채널 정형 문구\n\n본문 · 댓글에서 문자열만 지웁니다. 글은 남습니다.\n\n네이버 카페2\n네이버 블로그2\n유튜브0\n뽐뿌0\n클리앙0\n치환 건수는 채널별로 집계합니다. 문구별 집계는 제공되지 않습니다.\n문구\t출처\t치환 건수\t삭제\n카페 회원이 되시면 전체 내용을 볼 수 있습니다.\t기본\t실행 후 집계\t삭제\n카페 가입하기\t기본\t실행 후 집계\t삭제\n\n네이버 카페 치환 실행 후 집계\n\n네이버 카페에 지울 문구 추가\n추가\n내부용 · 임베더\nVoyage\n가짜 임베더 · 오프라인 시연\n만들어지는 것\n원문 정제본\n라벨러 · 임베딩 입력\n형태소 토큰\nKiwi · 문장부호 삭제\n임베딩\n가짜 임베더 · 전량 1회\n\n같은 수집본과 같은 규칙이면 새 버전에서도 다시 만들지 않습니다.\n\n예상\n\n수집 건수 확인 전\n\n통과 건수와 저장량은 실행 후 확인할 수 있습니다.\n\n임베딩 예상 시간은 아직 제공되지 않습니다.\n\n규칙을 확인하고 실행하세요"
    },
    {
      "time": "2026-10-20T04:21:17.044Z",
      "nav": [
        {
          "text": "7클러스터링",
          "href": "/pipeline/clustering",
          "disabled": null
        },
        {
          "text": "8근거 탐색",
          "href": "/pipeline/evidence",
          "disabled": null
        },
        {
          "text": "9페르소나",
          "href": "/pipeline/personas",
          "disabled": null
        },
        {
          "text": "10인사이트",
          "href": "/pipeline/insights",
          "disabled": null
        }
      ],
      "main": "3단계 · 전처리 · 임베딩\n\n라벨링에 쓸 문서와 벡터를 만듭니다\n\n규칙은 명백한 광고 · 중복 · 너무 짧은 글만 뺍니다. 대상과 관련 있는지는 4단계에서 판단합니다.\n\n3단계부터 다시\n임시 저장\n다시 실행\n전처리 결과\n6건이 라벨링으로 넘어갑니다.\n\n원본 6건 중 광고 0 · 너무 짧음 0 · 제외 출처 0 · 중복 0건을 뺐습니다.\n\n수집본 c1\n가짜 임베더\nKiwi\n생성 2026. 10. 20. 오후 1:21:14\nprepKey p_8d4420d74b0b\n다음 행동 · 라벨링을 시작하세요\n라벨링으로 →\n규칙별 제거\n제외 채널\n0\n광고어\n0\n짧음\n0\n제외 출처\n0\n중복\n0\n\n정형 문구 치환 0건 · 토큰 6건\n\n임베딩 완료 6건\n\n규칙 수정하고 다시 실행\n만들어지는 것\n원문 정제본\n라벨러 · 임베딩 입력\n형태소 토큰\nKiwi · 문장부호 삭제\n임베딩\n가짜 임베더 · 전량 1회\n\n같은 수집본과 같은 규칙이면 새 버전에서도 다시 만들지 않습니다.\n\n예상\n\n6건 → 약 6건\n\n직전 실행 기준 · 벡터 저장 약 0.00GB\n\n임베딩 예상 시간은 아직 제공되지 않습니다.\n\n규칙을 확인하고 실행하세요"
    }
  ],
  "firstStatus": {
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
      "at": "2026-10-20T04:21:14.539728+00:00"
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
    "reused": false
  },
  "network": [
    {
      "time": "2026-10-20T04:21:10.894Z",
      "method": "PUT",
      "url": "http://localhost:8411/prep/sf7d9d6897a31472895cf5fdeafb9cea1/config?version=v1",
      "body": "{\"adFilter\":[],\"excludeSources\":[],\"excludeChannels\":[],\"minBodyChars\":10,\"analyzer\":\"kiwi\",\"tokenPos\":[\"NNG\",\"NNP\",\"VV\",\"VA\",\"XR\"],\"embedder\":\"fake\",\"embedModel\":\"voyage-4\",\"embedDim\":1024,\"boilerplate\":{\"naver_cafe\":[\"카페 회원이 되시면 전체 내용을 볼 수 있습니다.\",\"카페 가입하기\"],\"naver_blog\":[\"공감\",\"이웃추가\"],\"clien\":[],\"ppomppu\":[],\"youtube\":[]}}"
    },
    {
      "time": "2026-10-20T04:21:10.918Z",
      "method": "POST",
      "url": "http://localhost:8411/prep/sf7d9d6897a31472895cf5fdeafb9cea1/run?version=v1",
      "body": null
    },
    {
      "time": "2026-10-20T04:21:10.915Z",
      "status": 200,
      "url": "http://localhost:8411/prep/sf7d9d6897a31472895cf5fdeafb9cea1/config?version=v1",
      "body": "{\"status\":\"ok\",\"prep\":{\"config\":{\"adFilter\":[],\"excludeSources\":[],\"excludeChannels\":[],\"minBodyChars\":10,\"boilerplate\":{\"naver_cafe\":[\"카페 회원이 되시면 전체 내용을 볼 수 있습니다.\",\"카페 가입하기\"],\"naver_blog\":[\"공감\",\"이웃추가\"],\"clien\":[],\"ppomppu\":[],\"youtube\":[]},\"analyzer\":\"kiwi\",\"tokenPos\":[\"NNG\",\"NNP\",\"VV\",\"VA\",\"XR\"],\"embedder\":\"fake\",\"embedModel\":\"voyage-4\",\"embedDim\":1024},\"status\":\"none\",\"derivedRef\":null,\"runId\":null,\"reused\":false,\"savedAt\":\"2026-10-20T04:21:10.890204+00:00\"}}"
    },
    {
      "time": "2026-10-20T04:21:10.944Z",
      "status": 200,
      "url": "http://localhost:8411/prep/sf7d9d6897a31472895cf5fdeafb9cea1/run?version=v1",
      "body": "{\"status\":\"running\",\"runId\":\"3c08d4e9c3db4ee3a55dc06087525203\",\"progress\":0.0,\"reused\":false}"
    },
    {
      "time": "2026-10-20T04:21:10.956Z",
      "method": "GET",
      "url": "http://localhost:8411/prep/sf7d9d6897a31472895cf5fdeafb9cea1/status?version=v1",
      "body": null
    },
    {
      "time": "2026-10-20T04:21:10.958Z",
      "status": 200,
      "url": "http://localhost:8411/prep/sf7d9d6897a31472895cf5fdeafb9cea1/status?version=v1",
      "body": "{\"status\":\"running\",\"progress\":0.0,\"detail\":{},\"runId\":\"3c08d4e9c3db4ee3a55dc06087525203\",\"derivedRef\":{\"collectionId\":\"c1\",\"prepKey\":\"p_8d4420d74b0b\"},\"stage3\":null,\"error\":null,\"config\":{\"adFilter\":[],\"excludeSources\":[],\"excludeChannels\":[],\"minBodyChars\":10,\"boilerplate\":{\"naver_cafe\":[\"카페 회원이 되시면 전체 내용을 볼 수 있습니다.\",\"카페 가입하기\"],\"naver_blog\":[\"공감\",\"이웃추가\"],\"clien\":[],\"ppomppu\":[],\"youtube\":[]},\"analyzer\":\"kiwi\",\"tokenPos\":[\"NNG\",\"NNP\",\"VV\",\"VA\",\"XR\"],\"embedder\":\"fake\",\"embedModel\":\"voyage-4\",\"embedDim\":1024},\"reused\":false}"
    },
    {
      "time": "2026-10-20T04:21:13.970Z",
      "method": "GET",
      "url": "http://localhost:8411/prep/sf7d9d6897a31472895cf5fdeafb9cea1/status?version=v1",
      "body": null
    },
    {
      "time": "2026-10-20T04:21:13.979Z",
      "status": 200,
      "url": "http://localhost:8411/prep/sf7d9d6897a31472895cf5fdeafb9cea1/status?version=v1",
      "body": "{\"status\":\"running\",\"progress\":0.0,\"detail\":{},\"runId\":\"3c08d4e9c3db4ee3a55dc06087525203\",\"derivedRef\":{\"collectionId\":\"c1\",\"prepKey\":\"p_8d4420d74b0b\"},\"stage3\":null,\"error\":null,\"config\":{\"adFilter\":[],\"excludeSources\":[],\"excludeChannels\":[],\"minBodyChars\":10,\"boilerplate\":{\"naver_cafe\":[\"카페 회원이 되시면 전체 내용을 볼 수 있습니다.\",\"카페 가입하기\"],\"naver_blog\":[\"공감\",\"이웃추가\"],\"clien\":[],\"ppomppu\":[],\"youtube\":[]},\"analyzer\":\"kiwi\",\"tokenPos\":[\"NNG\",\"NNP\",\"VV\",\"VA\",\"XR\"],\"embedder\":\"fake\",\"embedModel\":\"voyage-4\",\"embedDim\":1024},\"reused\":false}"
    },
    {
      "time": "2026-10-20T04:21:16.985Z",
      "method": "GET",
      "url": "http://localhost:8411/prep/sf7d9d6897a31472895cf5fdeafb9cea1/status?version=v1",
      "body": null
    },
    {
      "time": "2026-10-20T04:21:16.992Z",
      "status": 200,
      "url": "http://localhost:8411/prep/sf7d9d6897a31472895cf5fdeafb9cea1/status?version=v1",
      "body": "{\"status\":\"done\",\"progress\":1,\"detail\":{},\"runId\":null,\"derivedRef\":{\"collectionId\":\"c1\",\"prepKey\":\"p_8d4420d74b0b\"},\"stage3\":{\"original\":6,\"after\":6,\"removed\":{\"ad\":0,\"excluded_source\":0,\"duplicate\":0,\"too_short\":0,\"excluded_channel\":0},\"boilerplate_replaced\":{},\"tokens_written\":6,\"embedded\":6,\"embed_failed_zero_vector\":0,\"prepKey\":\"p_8d4420d74b0b\",\"embedder\":\"fake\",\"analyzer\":\"kiwi-0.24.0\",\"at\":\"2026-10-20T04:21:14.539728+00:00\"},\"error\":null,\"config\":{\"adFilter\":[],\"excludeSources\":[],\"excludeChannels\":[],\"minBodyChars\":10,\"boilerplate\":{\"naver_cafe\":[\"카페 회원이 되시면 전체 내용을 볼 수 있습니다.\",\"카페 가입하기\"],\"naver_blog\":[\"공감\",\"이웃추가\"],\"clien\":[],\"ppomppu\":[],\"youtube\":[]},\"analyzer\":\"kiwi\",\"tokenPos\":[\"NNG\",\"NNP\",\"VV\",\"VA\",\"XR\"],\"embedder\":\"fake\",\"embedModel\":\"voyage-4\",\"embedDim\":1024},\"reused\":false}"
    },
    {
      "time": "2026-10-20T04:21:42.230Z",
      "method": "PUT",
      "url": "http://localhost:8411/prep/sf7d9d6897a31472895cf5fdeafb9cea1/config?version=v1",
      "body": "{\"adFilter\":[],\"excludeSources\":[],\"excludeChannels\":[],\"minBodyChars\":10,\"analyzer\":\"kiwi\",\"tokenPos\":[\"NNG\",\"NNP\",\"VV\",\"VA\",\"XR\"],\"embedder\":\"fake\",\"embedModel\":\"voyage-4\",\"embedDim\":1024,\"boilerplate\":{\"naver_cafe\":[\"카페 회원이 되시면 전체 내용을 볼 수 있습니다.\",\"카페 가입하기\"],\"naver_blog\":[\"공감\",\"이웃추가\"],\"clien\":[],\"ppomppu\":[],\"youtube\":[]}}"
    },
    {
      "time": "2026-10-20T04:21:42.249Z",
      "method": "POST",
      "url": "http://localhost:8411/prep/sf7d9d6897a31472895cf5fdeafb9cea1/run?version=v1",
      "body": null
    },
    {
      "time": "2026-10-20T04:21:42.248Z",
      "status": 200,
      "url": "http://localhost:8411/prep/sf7d9d6897a31472895cf5fdeafb9cea1/config?version=v1",
      "body": "{\"status\":\"ok\",\"prep\":{\"config\":{\"adFilter\":[],\"excludeSources\":[],\"excludeChannels\":[],\"minBodyChars\":10,\"boilerplate\":{\"naver_cafe\":[\"카페 회원이 되시면 전체 내용을 볼 수 있습니다.\",\"카페 가입하기\"],\"naver_blog\":[\"공감\",\"이웃추가\"],\"clien\":[],\"ppomppu\":[],\"youtube\":[]},\"analyzer\":\"kiwi\",\"tokenPos\":[\"NNG\",\"NNP\",\"VV\",\"VA\",\"XR\"],\"embedder\":\"fake\",\"embedModel\":\"voyage-4\",\"embedDim\":1024},\"derivedRef\":null,\"status\":\"none\",\"savedAt\":\"2026-10-20T04:21:42.220031+00:00\",\"reused\":false,\"runId\":null}}"
    },
    {
      "time": "2026-10-20T04:21:42.266Z",
      "status": 200,
      "url": "http://localhost:8411/prep/sf7d9d6897a31472895cf5fdeafb9cea1/run?version=v1",
      "body": "{\"status\":\"done\",\"progress\":1,\"detail\":{},\"runId\":null,\"derivedRef\":{\"collectionId\":\"c1\",\"prepKey\":\"p_8d4420d74b0b\"},\"stage3\":{\"original\":6,\"after\":6,\"removed\":{\"ad\":0,\"excluded_source\":0,\"duplicate\":0,\"too_short\":0,\"excluded_channel\":0},\"boilerplate_replaced\":{},\"tokens_written\":6,\"embedded\":6,\"embed_failed_zero_vector\":0,\"prepKey\":\"p_8d4420d74b0b\",\"embedder\":\"fake\",\"analyzer\":\"kiwi-0.24.0\",\"at\":\"2026-10-20T04:21:14.539728+00:00\"},\"error\":null,\"config\":{\"adFilter\":[],\"excludeSources\":[],\"excludeChannels\":[],\"minBodyChars\":10,\"boilerplate\":{\"naver_cafe\":[\"카페 회원이 되시면 전체 내용을 볼 수 있습니다.\",\"카페 가입하기\"],\"naver_blog\":[\"공감\",\"이웃추가\"],\"clien\":[],\"ppomppu\":[],\"youtube\":[]},\"analyzer\":\"kiwi\",\"tokenPos\":[\"NNG\",\"NNP\",\"VV\",\"VA\",\"XR\"],\"embedder\":\"fake\",\"embedModel\":\"voyage-4\",\"embedDim\":1024},\"reused\":true}"
    }
  ]
}
```

