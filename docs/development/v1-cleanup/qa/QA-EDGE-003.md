# QA-EDGE-003

```json
{
  "id": "QA-EDGE-003",
  "url": "http://localhost:3411/pipeline/clustering",
  "result": "FAIL",
  "expected": "Restart stage3 in v2: no preprocessing result, four later stages locked, clustering preprocessing-required banner.",
  "actual": "{\"version\":\"v2\",\"prepStatus\":\"stale\",\"derivedRef\":{\"collectionId\":\"c1\",\"prepKey\":\"p_8d4420d74b0b\"},\"prepDone\":false,\"nav\":[{\"text\":\"7클러스터링진행 중\",\"href\":\"/pipeline/clustering\",\"disabled\":null},{\"text\":\"8근거 탐색\",\"href\":\"/pipeline/evidence\",\"disabled\":null},{\"text\":\"9페르소나\",\"href\":\"/pipeline/personas\",\"disabled\":null},{\"text\":\"10인사이트\",\"href\":\"/pipeline/insights\",\"disabled\":null}],\"bannerPresent\":false,\"actualScreen\":\"이 결과는 v1의 6단계 기준입니다. 이 단계를 다시 하거나 그대로 쓰세요.\\n이 단계부터 다시\\n\\n6단계 · 클러스터링\\n\\nTouch Point를 확정합니다\\n\\nCluster → Persona → Context 순서로 초안을 확인하고 확정하세요.\\n\\n잠정\\n6-A · Cluster\\n클러스터 이름\\n0/0 확정\\n6-B · Persona\\nDesire · Goal\\n잠김 · 6-A 확정 후\\n6-C · Context\\nContext 이름 · 행동\\n잠김 · 6-B 확정 후\\n\\n학습 결과의 Core · Supporting 문서를 나눕니다.\\n\\n블로그 · 카페로 구조 만들기 (유튜브 댓글은 가까운 Context의 보조 근거)\\n클러스터링 실행\\n근거 탐색 실행\"}",
  "evidence": "docs/development/v1-cleanup/qa/QA-EDGE-003.md",
  "time": "2026-10-20T04:25:29.477Z",
  "steps": [
    "Executed last after other 18 scenarios",
    "Selected completed session via start UI",
    "Clicked 3단계부터 다시 and 새 버전 만들기",
    "Observed POST versions with from=v1/restartFrom=stage3 and active v2",
    "Opened clustering directly",
    "Expected banner wait timed out after 30 seconds; captured actual unlocked screen",
    "Read v2 session and version list"
  ],
  "screenshot": "/Users/yunho/Documents/dcx_agent-v1-cleanup/docs/development/v1-cleanup/qa/QA-EDGE-003.png",
  "session": {
    "status": "ok",
    "data": {
      "schemaVersion": 2,
      "sid": "sf7d9d6897a31472895cf5fdeafb9cea1",
      "step": "start",
      "drafts": {
        "prep": null
      },
      "projectContext": {
        "bk": "QA 전처리 실행",
        "oneLiner": "QA용 세션",
        "researchQuestion": {
          "text": "냉방 경험은?",
          "template": null
        },
        "projectType": {
          "choice": "new",
          "note": ""
        },
        "taskMode": null,
        "analysisGoal": {
          "choice": "needs",
          "note": ""
        },
        "keyMetrics": [
          {
            "name": "만족",
            "source": "",
            "item": ""
          }
        ],
        "constraints": [],
        "positioning": {
          "price": "value",
          "market": "new",
          "priceText": "",
          "marketText": ""
        },
        "personaSeeds": null,
        "channels": [
          "fixture"
        ],
        "knownInsights": [],
        "productCategory": {
          "l1": "가전",
          "l2": null,
          "l3": null,
          "source": "user"
        },
        "targetScope": null,
        "futureCustomer": null,
        "schemaVersion": 1
      },
      "knownInsights": [],
      "version": "v2",
      "updatedAt": "2026-10-20T04:24:37.072170+00:00",
      "collectionId": "c1",
      "prep": {
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
        "derivedRef": {
          "collectionId": "c1",
          "prepKey": "p_8d4420d74b0b"
        },
        "status": "stale",
        "savedAt": "2026-10-20T04:21:42.261446+00:00",
        "reused": true,
        "runId": null
      },
      "parentVersion": "v1",
      "restartFrom": "stage3",
      "stale": {
        "stage3": "stage3 changed in v2",
        "stage4": "stage3 changed in v2",
        "stage5": "stage3 changed in v2",
        "stage6": "stage3 changed in v2",
        "stage7": "stage3 changed in v2",
        "stage8": "stage3 changed in v2"
      },
      "segment": {
        "status": "stale"
      },
      "completion": {
        "crawlDone": true,
        "prepDone": false,
        "labelingDone": false,
        "exportDone": false,
        "clustersDone": false,
        "segmentDone": false,
        "personaDone": false,
        "insightDone": false,
        "evidenceDone": false
      }
    }
  },
  "versions": {
    "activeVersion": "v2",
    "versions": [
      {
        "id": "v1",
        "parent": null,
        "restartFrom": "stage0",
        "createdAt": "2026-10-20T04:15:20.626738+00:00",
        "note": "",
        "readonly": true,
        "collectionId": "c1"
      },
      {
        "id": "v2",
        "parent": "v1",
        "restartFrom": "stage3",
        "createdAt": "2026-10-20T04:24:37.076624+00:00",
        "note": "",
        "readonly": false,
        "collectionId": "c1"
      }
    ]
  },
  "network": [
    {
      "time": "2026-10-20T04:24:36.975Z",
      "method": "POST",
      "url": "http://localhost:8411/sessions/sf7d9d6897a31472895cf5fdeafb9cea1/versions",
      "body": "{\"from\":\"v1\",\"restartFrom\":\"stage3\",\"note\":\"\"}"
    },
    {
      "time": "2026-10-20T04:24:37.122Z",
      "status": 201,
      "url": "http://localhost:8411/sessions/sf7d9d6897a31472895cf5fdeafb9cea1/versions",
      "body": "{\"version\":\"v2\"}"
    },
    {
      "time": "2026-10-20T04:24:37.269Z",
      "method": "GET",
      "url": "http://localhost:8411/sessions/sf7d9d6897a31472895cf5fdeafb9cea1/versions",
      "body": null
    },
    {
      "time": "2026-10-20T04:24:37.279Z",
      "status": 200,
      "url": "http://localhost:8411/sessions/sf7d9d6897a31472895cf5fdeafb9cea1/versions",
      "body": "{\"activeVersion\":\"v2\",\"versions\":[{\"id\":\"v1\",\"parent\":null,\"restartFrom\":\"stage0\",\"createdAt\":\"2026-10-20T04:15:20.626738+00:00\",\"note\":\"\",\"readonly\":true,\"collectionId\":\"c1\"},{\"id\":\"v2\",\"parent\":\"v1\",\"restartFrom\":\"stage3\",\"createdAt\":\"2026-10-20T04:24:37.076624+00:00\",\"note\":\"\",\"readonly\":false,\"collectionId\":\"c1\"}]}"
    },
    {
      "time": "2026-10-20T04:24:37.714Z",
      "method": "GET",
      "url": "http://localhost:8411/sessions/sf7d9d6897a31472895cf5fdeafb9cea1/versions",
      "body": null
    },
    {
      "time": "2026-10-20T04:24:37.722Z",
      "status": 200,
      "url": "http://localhost:8411/sessions/sf7d9d6897a31472895cf5fdeafb9cea1/versions",
      "body": "{\"activeVersion\":\"v2\",\"versions\":[{\"id\":\"v1\",\"parent\":null,\"restartFrom\":\"stage0\",\"createdAt\":\"2026-10-20T04:15:20.626738+00:00\",\"note\":\"\",\"readonly\":true,\"collectionId\":\"c1\"},{\"id\":\"v2\",\"parent\":\"v1\",\"restartFrom\":\"stage3\",\"createdAt\":\"2026-10-20T04:24:37.076624+00:00\",\"note\":\"\",\"readonly\":false,\"collectionId\":\"c1\"}]}"
    },
    {
      "time": "2026-10-20T04:24:37.746Z",
      "method": "GET",
      "url": "http://localhost:8411/sessions/sf7d9d6897a31472895cf5fdeafb9cea1/versions",
      "body": null
    },
    {
      "time": "2026-10-20T04:24:37.752Z",
      "status": 200,
      "url": "http://localhost:8411/sessions/sf7d9d6897a31472895cf5fdeafb9cea1/versions",
      "body": "{\"activeVersion\":\"v2\",\"versions\":[{\"id\":\"v1\",\"parent\":null,\"restartFrom\":\"stage0\",\"createdAt\":\"2026-10-20T04:15:20.626738+00:00\",\"note\":\"\",\"readonly\":true,\"collectionId\":\"c1\"},{\"id\":\"v2\",\"parent\":\"v1\",\"restartFrom\":\"stage3\",\"createdAt\":\"2026-10-20T04:24:37.076624+00:00\",\"note\":\"\",\"readonly\":false,\"collectionId\":\"c1\"}]}"
    },
    {
      "time": "2026-10-20T04:24:47.746Z",
      "method": "GET",
      "url": "http://localhost:8411/sessions/sf7d9d6897a31472895cf5fdeafb9cea1/versions",
      "body": null
    },
    {
      "time": "2026-10-20T04:24:47.748Z",
      "status": 200,
      "url": "http://localhost:8411/sessions/sf7d9d6897a31472895cf5fdeafb9cea1/versions",
      "body": "{\"activeVersion\":\"v2\",\"versions\":[{\"id\":\"v1\",\"parent\":null,\"restartFrom\":\"stage0\",\"createdAt\":\"2026-10-20T04:15:20.626738+00:00\",\"note\":\"\",\"readonly\":true,\"collectionId\":\"c1\"},{\"id\":\"v2\",\"parent\":\"v1\",\"restartFrom\":\"stage3\",\"createdAt\":\"2026-10-20T04:24:37.076624+00:00\",\"note\":\"\",\"readonly\":false,\"collectionId\":\"c1\"}]}"
    },
    {
      "time": "2026-10-20T04:24:57.745Z",
      "method": "GET",
      "url": "http://localhost:8411/sessions/sf7d9d6897a31472895cf5fdeafb9cea1/versions",
      "body": null
    },
    {
      "time": "2026-10-20T04:24:57.748Z",
      "status": 200,
      "url": "http://localhost:8411/sessions/sf7d9d6897a31472895cf5fdeafb9cea1/versions",
      "body": "{\"activeVersion\":\"v2\",\"versions\":[{\"id\":\"v1\",\"parent\":null,\"restartFrom\":\"stage0\",\"createdAt\":\"2026-10-20T04:15:20.626738+00:00\",\"note\":\"\",\"readonly\":true,\"collectionId\":\"c1\"},{\"id\":\"v2\",\"parent\":\"v1\",\"restartFrom\":\"stage3\",\"createdAt\":\"2026-10-20T04:24:37.076624+00:00\",\"note\":\"\",\"readonly\":false,\"collectionId\":\"c1\"}]}"
    },
    {
      "time": "2026-10-20T04:25:07.744Z",
      "method": "GET",
      "url": "http://localhost:8411/sessions/sf7d9d6897a31472895cf5fdeafb9cea1/versions",
      "body": null
    },
    {
      "time": "2026-10-20T04:25:07.748Z",
      "status": 200,
      "url": "http://localhost:8411/sessions/sf7d9d6897a31472895cf5fdeafb9cea1/versions",
      "body": "{\"activeVersion\":\"v2\",\"versions\":[{\"id\":\"v1\",\"parent\":null,\"restartFrom\":\"stage0\",\"createdAt\":\"2026-10-20T04:15:20.626738+00:00\",\"note\":\"\",\"readonly\":true,\"collectionId\":\"c1\"},{\"id\":\"v2\",\"parent\":\"v1\",\"restartFrom\":\"stage3\",\"createdAt\":\"2026-10-20T04:24:37.076624+00:00\",\"note\":\"\",\"readonly\":false,\"collectionId\":\"c1\"}]}"
    },
    {
      "time": "2026-10-20T04:25:17.746Z",
      "method": "GET",
      "url": "http://localhost:8411/sessions/sf7d9d6897a31472895cf5fdeafb9cea1/versions",
      "body": null
    },
    {
      "time": "2026-10-20T04:25:17.749Z",
      "status": 200,
      "url": "http://localhost:8411/sessions/sf7d9d6897a31472895cf5fdeafb9cea1/versions",
      "body": "{\"activeVersion\":\"v2\",\"versions\":[{\"id\":\"v1\",\"parent\":null,\"restartFrom\":\"stage0\",\"createdAt\":\"2026-10-20T04:15:20.626738+00:00\",\"note\":\"\",\"readonly\":true,\"collectionId\":\"c1\"},{\"id\":\"v2\",\"parent\":\"v1\",\"restartFrom\":\"stage3\",\"createdAt\":\"2026-10-20T04:24:37.076624+00:00\",\"note\":\"\",\"readonly\":false,\"collectionId\":\"c1\"}]}"
    },
    {
      "time": "2026-10-20T04:25:27.747Z",
      "method": "GET",
      "url": "http://localhost:8411/sessions/sf7d9d6897a31472895cf5fdeafb9cea1/versions",
      "body": null
    },
    {
      "time": "2026-10-20T04:25:27.752Z",
      "status": 200,
      "url": "http://localhost:8411/sessions/sf7d9d6897a31472895cf5fdeafb9cea1/versions",
      "body": "{\"activeVersion\":\"v2\",\"versions\":[{\"id\":\"v1\",\"parent\":null,\"restartFrom\":\"stage0\",\"createdAt\":\"2026-10-20T04:15:20.626738+00:00\",\"note\":\"\",\"readonly\":true,\"collectionId\":\"c1\"},{\"id\":\"v2\",\"parent\":\"v1\",\"restartFrom\":\"stage3\",\"createdAt\":\"2026-10-20T04:24:37.076624+00:00\",\"note\":\"\",\"readonly\":false,\"collectionId\":\"c1\"}]}"
    }
  ],
  "console": [
    {
      "time": "2026-10-20T04:24:37.344Z",
      "type": "error",
      "text": "Failed to load resource: the server responded with a status of 404 (Not Found)"
    },
    {
      "time": "2026-10-20T04:24:37.346Z",
      "type": "error",
      "text": "Failed to load resource: the server responded with a status of 404 (Not Found)"
    },
    {
      "time": "2026-10-20T04:24:37.381Z",
      "type": "log",
      "text": "[Fast Refresh] rebuilding"
    },
    {
      "time": "2026-10-20T04:24:37.434Z",
      "type": "log",
      "text": "[Fast Refresh] done in 154ms"
    },
    {
      "time": "2026-10-20T04:24:37.642Z",
      "type": "info",
      "text": "%cDownload the React DevTools for a better development experience: https://react.dev/link/react-devtools font-weight:bold"
    },
    {
      "time": "2026-10-20T04:24:37.676Z",
      "type": "log",
      "text": "[HMR] connected"
    },
    {
      "time": "2026-10-20T04:24:37.687Z",
      "type": "warning",
      "text": "Image with src \"/person-a-logo.png\" has either width or height modified, but not the other. If you use CSS to change the size of your image, also include the styles 'width: \"auto\"' or 'height: \"auto\"' to maintain the aspect ratio."
    }
  ]
}
```

