# QA-EDGE-002 — PASS

URL: http://localhost:3000/pipeline/crawling

Tested commit: c597b2a678231016e51b0d3644f3d6df921810c2; observed HEAD: c597b2a678231016e51b0d3644f3d6df921810c2.

## Approved scenario (unchanged)

```text
QA-EDGE-002
Priority: P1
Type: Edge / Permission (read-only)
Given: QA-E2E-005가 끝난 세션에서 새 버전을 만들어, 끝난 버전이 과거 버전(열람 전용)이 됐다
When: 과거 버전의 크롤링 화면을 연다
Then:
  - 결과 화면의 "건너뛴 항목" 표가 보인다
  - "일시 정지하기" · "다시 수집" 등 쓰기 버튼이 보이지 않거나 비활성화돼 있다
```

## Executed steps

1. 완료 세션에서 POST versions(from=v1,restartFrom=stage2)→201 v2
2. v1을 유지한 브라우저가 읽기 전용으로 갱신될 때까지 관찰
3. 버전 API, 표, 쓰기 제어 확인

## Actual / verdict

v2 생성 후 v1 readonly=true. v1 결과 및 건너뛴 사유 표 유지. 일시 정지하기/다시 수집 없음, 자동 연쇄 체크박스 disabled.

새 버전을 만드는 이 버전에서 새로 시작하기/이 단계부터 다시는 존재한다. 과거 수집본을 직접 변경하는 버튼과 구별하여 기록했다.

## Timestamped DOM / API evidence

```json
{
  "time": "2026-10-20T07:04:19.833Z",
  "url": "http://localhost:3000/pipeline/crawling",
  "dom": "- main:\n  - status:\n    - text: v1 · 읽기 전용 ·\n    - button \"이 버전에서 새로 시작하기\"\n  - group:\n    - button \"이 단계부터 다시\" [disabled]\n    - text: 2단계 · 크롤링\n    - heading \"수집 결과를 확인합니다\" [level=1]\n    - checkbox \"크롤링이 끝나면 전처리 · 라벨링(GPT, 블로그 · 카페 먼저)까지 자동으로 시작\" [disabled]\n    - text: 크롤링이 끝나면 전처리 · 라벨링(GPT, 블로그 · 카페 먼저)까지 자동으로 시작\n    - heading \"P5 수집 요약\" [level=2]\n    - progressbar \"상세 수집 진행\"\n    - term: 완료 / 대상 URL\n    - definition: 82 / 82\n    - term: 원문 확보\n    - definition: 100.0%\n    - term: 분당 처리량\n    - definition: \"49.6\"\n    - term: 남은 시간\n    - definition: 약 0분\n    - paragraph: 스니펫 0.0% · 제한글 0.0%\n    - region \"채널별 수집 상태 스크롤\":\n      - table \"채널별 수집 상태\":\n        - rowgroup:\n          - row \"채널 상태 시도 차단 파싱 오류 건너뜀\":\n            - columnheader \"채널\"\n            - columnheader \"상태\"\n            - columnheader \"시도\"\n            - columnheader \"차단\"\n            - columnheader \"파싱 오류\"\n            - columnheader \"건너뜀\"\n        - rowgroup:\n          - row \"82쿡 완료 16 0 0 —\":\n            - rowheader \"82쿡\"\n            - cell \"완료\"\n            - cell \"16\"\n            - cell \"0\"\n            - cell \"0\"\n            - cell \"—\"\n          - row \"지식iN 완료 8 0 0 2 (삭제된 글)\":\n            - rowheader \"지식iN\"\n            - cell \"완료\"\n            - cell \"8\"\n            - cell \"0\"\n            - cell \"0\"\n            - cell \"2 (삭제된 글)\"\n          - row \"Threads 완료 50 0 0 —\":\n            - rowheader \"Threads\"\n            - cell \"완료\"\n            - cell \"50\"\n            - cell \"0\"\n            - cell \"0\"\n            - cell \"—\"\n          - row \"유튜브 브이로그 완료 8 0 0 2 (자막 없음)\":\n            - rowheader \"유튜브 브이로그\"\n            - cell \"완료\"\n            - cell \"8\"\n            - cell \"0\"\n            - cell \"0\"\n            - cell \"2 (자막 없음)\"\n    - term: 수집 문서\n    - definition: \"90\"\n    - term: 채널\n    - definition: \"4\"\n    - term: 목록 URL\n    - definition: \"86\"\n    - term: 완료 URL\n    - definition: \"82\"\n    - heading \"건너뛴 항목\" [level=2]\n    - table \"채널별 건너뛴 사유\":\n      - rowgroup:\n        - row \"채널 사유 건수\":\n          - columnheader \"채널\"\n          - columnheader \"사유\"\n          - columnheader \"건수\"\n      - rowgroup:\n        - row \"지식iN 삭제된 글 2건\":\n          - cell \"지식iN\"\n          - cell \"삭제된 글\"\n          - cell \"2건\"\n        - row \"유튜브 브이로그 한국어 자막 없음 2개 영상\":\n          - cell \"유튜브 브이로그\"\n          - cell \"한국어 자막 없음\"\n          - cell \"2개 영상\"\n    - heading \"채널 분포\" [level=2]\n    - text: 82쿡 16 · 17.8% 지식iN 8 · 8.9% Threads 50 · 55.6% 유튜브 브이로그 16 · 17.8% (영상 8개 → 구간 16)\n    - table \"키워드별 수집 결과\":\n      - rowgroup:\n        - row \"키워드 채널 수집 문서 목록 URL 완료 URL\":\n          - columnheader \"키워드\"\n          - columnheader \"채널\"\n          - columnheader \"수집 문서\"\n          - columnheader \"목록 URL\"\n          - columnheader \"완료 URL\"\n      - rowgroup:\n        - row \"qa-empty 82쿡 0 0 0\":\n          - cell \"qa-empty\"\n          - cell \"82쿡\"\n          - cell \"0\"\n          - cell \"0\"\n          - cell \"0\"\n        - row \"qa-empty 지식iN 0 0 0\":\n          - cell \"qa-empty\"\n          - cell \"지식iN\"\n          - cell \"0\"\n          - cell \"0\"\n          - cell \"0\"\n        - row \"qa-empty Threads 0 0 0\":\n          - cell \"qa-empty\"\n          - cell \"Threads\"\n          - cell \"0\"\n          - cell \"0\"\n          - cell \"0\"\n        - row \"qa-empty 유튜브 브이로그 0 0 0\":\n          - cell \"qa-empty\"\n          - cell \"유튜브 브이로그\"\n          - cell \"0\"\n          - cell \"0\"\n          - cell \"0\"\n        - row \"에어컨청소 82쿡 8 8 8\":\n          - cell \"에어컨청소\"\n          - cell \"82쿡\"\n          - cell \"8\"\n          - cell \"8\"\n          - cell \"8\"\n        - row \"에어컨청소 지식iN 4 5 4\":\n          - cell \"에어컨청소\"\n          - cell \"지식iN\"\n          - cell \"4\"\n          - cell \"5\"\n          - cell \"4\"\n        - row \"에어컨청소 Threads 25 25 25\":\n          - cell \"에어컨청소\"\n          - cell \"Threads\"\n          - cell \"25\"\n          - cell \"25\"\n          - cell \"25\"\n        - row \"에어컨청소 유튜브 브이로그 8 5 4\":\n          - cell \"에어컨청소\"\n          - cell \"유튜브 브이로그\"\n          - cell \"8\"\n          - cell \"5\"\n          - cell \"4\"\n        - row \"제습기 82쿡 8 8 8\":\n          - cell \"제습기\"\n          - cell \"82쿡\"\n          - cell \"8\"\n          - cell \"8\"\n          - cell \"8\"\n        - row \"제습기 지식iN 4 5 4\":\n          - cell \"제습기\"\n          - cell \"지식iN\"\n          - cell \"4\"\n          - cell \"5\"\n          - cell \"4\"\n        - row \"제습기 Threads 25 25 25\":\n          - cell \"제습기\"\n          - cell \"Threads\"\n          - cell \"25\"\n          - cell \"25\"\n          - cell \"25\"\n        - row \"제습기 유튜브 브이로그 8 5 4\":\n          - cell \"제습기\"\n          - cell \"유튜브 브이로그\"\n          - cell \"8\"\n          - cell \"5\"\n          - cell \"4\"\n    - heading \"키워드 상위\" [level=2]\n    - text: 에어컨청소 45 제습기 45 qa-empty 0\n    - heading \"키워드 하위\" [level=2]\n    - text: qa-empty 0 제습기 45 에어컨청소 45\n    - paragraph: 내부용 스냅샷 9281df2b8ef845d48214705ad3491294\n    - button \"전처리로 이동하기\" [disabled]",
  "versions": {
    "activeVersion": "v2",
    "versions": [
      {
        "id": "v1",
        "parent": null,
        "restartFrom": "stage0",
        "createdAt": "2026-10-20T06:52:17.926606+00:00",
        "note": "",
        "readonly": true,
        "collectionId": "c1"
      },
      {
        "id": "v2",
        "parent": "v1",
        "restartFrom": "stage2",
        "createdAt": "2026-10-20T07:03:19.620851+00:00",
        "note": "QA-EDGE-002 historical read-only verification",
        "readonly": false,
        "collectionId": "c1"
      }
    ]
  },
  "historical": {
    "status": "ok",
    "data": {
      "schemaVersion": 2,
      "sid": "s0b496d50fd7a4ec7884eb11611993f4c",
      "step": "crawl-done",
      "drafts": {
        "crawl": {
          "config": null
        },
        "prep": null
      },
      "projectContext": {
        "bk": "QA 채널 확장",
        "oneLiner": "생활 가전 사용 경험을 조사하는 QA 프로젝트",
        "researchQuestion": {
          "text": "생활 가전을 사용하는 경험은 어떠한가?",
          "template": null
        },
        "projectType": {
          "choice": "new",
          "note": ""
        },
        "taskMode": "explore",
        "analysisGoal": null,
        "keyMetrics": [],
        "constraints": [],
        "positioning": {
          "price": null,
          "market": null,
          "priceText": "",
          "marketText": ""
        },
        "personaSeeds": null,
        "channels": [
          "youtube_vlog",
          "threads",
          "naver_kin",
          "cook82"
        ],
        "knownInsights": [],
        "productCategory": {
          "l1": "생활가전",
          "l2": null,
          "l3": null,
          "source": "user"
        },
        "targetScope": null,
        "futureCustomer": null,
        "schemaVersion": 1
      },
      "knownInsights": [],
      "version": "v1",
      "updatedAt": "2026-10-20T06:57:44.157723+00:00",
      "keywords": [
        {
          "id": "manual-b80b6ee1a71748deb620e52c1eb6380f",
          "kw": "에어컨청소",
          "axis": "physical",
          "sub": "product_physical",
          "round": 1,
          "origin": "manual",
          "status": "approved",
          "reject": null,
          "volume": {
            "monthly": null,
            "source": "unconnected",
            "at": null
          },
          "badges": [],
          "crawlExcluded": false
        },
        {
          "id": "manual-3dd4a70fea614153ae60008af6bd6849",
          "kw": "제습기",
          "axis": "physical",
          "sub": "product_physical",
          "round": 1,
          "origin": "manual",
          "status": "approved",
          "reject": null,
          "volume": {
            "monthly": null,
            "source": "unconnected",
            "at": null
          },
          "badges": [],
          "crawlExcluded": false
        },
        {
          "id": "manual-aed6700e63f34bb780e6eaf457df646d",
          "kw": "qa-empty",
          "axis": "physical",
          "sub": "product_physical",
          "round": 1,
          "origin": "manual",
          "status": "approved",
          "reject": null,
          "volume": {
            "monthly": null,
            "source": "unconnected",
            "at": null
          },
          "badges": [],
          "crawlExcluded": false
        }
      ],
      "crawlConfig": {
        "channels": [
          "threads",
          "naver_kin",
          "cook82",
          "youtube_vlog"
        ],
        "dateFrom": "2025-10-20",
        "dateTo": "2026-10-20",
        "adWords": [
          "협찬",
          "광고",
          "제공받",
          "원고료",
          "체험단",
          "서포터즈",
          "중고",
          "판매",
          "거래",
          "체험단",
          "협찬",
          "원고료",
          "소정의",
          "제공받아",
          "서포터즈"
        ],
        "excludeSources": [
          "중고나라",
          "번개장터",
          "당근",
          "세컨웨어",
          "헬로마켓",
          "중고",
          "장터",
          "부동산",
          "판매",
          "팝니다",
          "삽니다",
          "택배",
          "무료배송",
          "할인코드",
          "쿠폰",
          "홍보",
          "광고",
          "업체",
          "시공",
          "인테리어업체",
          "이사",
          "용달",
          "대출",
          "보험설계사",
          "설계사모집",
          "모집"
        ],
        "includeSources": [],
        "product_name_filter": false,
        "perChannel": {
          "threads": {
            "concurrency": 1,
            "min_interval_s": 2,
            "max_per_keyword": 1000
          },
          "naver_kin": {
            "concurrency": 1,
            "min_interval_s": 0.5,
            "max_per_keyword": 1000
          },
          "cook82": {
            "concurrency": 1,
            "min_interval_s": 0.5,
            "max_per_keyword": 1000
          },
          "youtube_vlog": {
            "concurrency": 2,
            "min_interval_s": 0,
            "max_per_keyword": 1000
          }
        },
        "youtube": {
          "videos_per_keyword": 20,
          "max_comments": 500
        },
        "youtube_vlog": {
          "videos_per_keyword": 5,
          "min_duration_s": 120,
          "max_duration_s": 1800
        },
        "target_total": null,
        "gateExclusions": []
      },
      "collectionId": "c1",
      "prep": {
        "config": {
          "adFilter": [
            "협찬",
            "광고",
            "제공받",
            "원고료",
            "체험단",
            "서포터즈",
            "중고",
            "판매",
            "거래",
            "체험단",
            "협찬",
            "원고료",
            "소정의",
            "제공받아",
            "서포터즈"
          ],
          "excludeSources": [
            "중고나라",
            "번개장터",
            "당근",
            "세컨웨어",
            "헬로마켓",
            "중고",
            "장터",
            "부동산",
            "판매",
            "팝니다",
            "삽니다",
            "택배",
            "무료배송",
            "할인코드",
            "쿠폰",
            "홍보",
            "광고",
            "업체",
            "시공",
            "인테리어업체",
            "이사",
            "용달",
            "대출",
            "보험설계사",
            "설계사모집",
            "모집"
          ],
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
            "youtube": [],
            "youtube_vlog": [],
            "threads": [],
            "naver_kin": [],
            "cook82": []
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
          "prepKey": "p_82344a663550"
        },
        "status": "done",
        "savedAt": "2026-10-20T06:57:48.538421+00:00",
        "reused": false
      },
      "completion": {
        "crawlDone": true,
        "prepDone": true,
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
  "buttons": [
    {
      "text": "이 버전에서 새로 시작하기",
      "disabled": false
    },
    {
      "text": "이 단계부터 다시",
      "disabled": false
    },
    {
      "text": "전처리로 이동하기",
      "disabled": false
    }
  ]
}
```

## Evidence files

- [QA-EDGE-002-data.json](QA-EDGE-002-data.json)

Screenshots were saved using explicit absolute paths and inspected for relevant states:

- [QA-EDGE-002.png](QA-EDGE-002.png) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-002.png`

Shared main browser console/network: [console-main.log](console-main.log), [network-main.log](network-main.log). Main console: no errors; logo aspect-ratio warning. Scenario-specific API responses and variant network records are in the JSON above or linked raw evidence. Screenshots supplement DOM/API evidence, not replace it.
