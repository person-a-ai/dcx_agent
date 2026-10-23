# QA-NEG-003 — PASS

URL: http://localhost:3002/pipeline/crawling

Tested commit: c597b2a678231016e51b0d3644f3d6df921810c2; observed HEAD: c597b2a678231016e51b0d3644f3d6df921810c2.

## Approved scenario (unchanged)

```text
QA-NEG-003
Priority: P0
Type: Negative / Failure injection
Given: 서버를 `QA_THREADS_MODE=blocked`로 다시 띄웠고, Threads만 켠 세션에서 목록 수집이 끝난 게이트 화면이다
When: "상세 수집 시작"을 누르고 멈출 때까지 기다린 뒤 "여기까지로 마치기"를 누르고 확인한다
Then:
  - 멈춤 배너 "수집이 멈췄습니다"가 보인다
  - 배너에 "Threads" 배지가 보인다
  - 배너에 "Threads가 로그인 화면을 보여 주어 멈췄습니다. 로그인은 시도하지 않습니다." 문구가 보인다
  - "여기까지로 마치기" 후 결과 화면 "건너뛴 항목" 표에 "Threads · 차단으로 여기까지 마침" 행이 있다
  - 서버 로그와 네트워크 기록에 threads.com 로그인 주소 요청이 없다
```

## Executed steps

1. 서버 재시작 대신 3002/8002 blocked 환경 사용
2. Threads만 목록→게이트→상세 수집
3. paused_blocked 실제 상태까지 기다림
4. 여기까지로 마치기 및 확인창 승인
5. 결과/상태 API/브라우저 네트워크/워커 로그 비교

## Actual / verdict

Threads 차단 후 멈춤 배너·Threads 배지·로그인 미시도 문구 확인. 확인창 승인 후 결과에 Threads 차단으로 여기까지 마침 50건. 브라우저 요청과 제공된 워커 로그에 threads.com 로그인 요청 없음.

초기 30초 대기는 20회 차단 임계치(간격2초)보다 짧아 timeout; 이후 실제 paused_blocked(시도20/차단20)를 관찰하고 계속했다. 서버 로그는 컨트롤러가 복사한 실제 list 1줄/detail 0줄을 독립적으로 읽었다. uvicorn stdout 원본은 파일이 없어 컨트롤러 관찰 메모로만 남는다. access log는 outbound를 기록하지 않으므로 이것만으로 외부 요청 부재를 증명한다고 주장하지 않는다. QA 훅 소스가 네트워크 호출 없이 AdapterBlocked를 발생시키는 점, 실제 blocked 상태, 워커 로그 및 브라우저 기록을 함께 확인했다. 실제 사이트 로그인 테스트는 범위 밖이다.

## Timestamped DOM / API evidence

```json
{
  "time": "2026-10-20T06:59:26.918Z",
  "before": "- main:\n  - group:\n    - button \"이 단계부터 다시\" [disabled]\n    - text: 2단계 · 크롤링\n    - heading \"본문과 댓글을 수집합니다\" [level=1]\n    - status:\n      - text: 수집이 멈췄습니다. 완료된 결과는 저장되어 있습니다. 이어서 진행하세요. Threads\n      - paragraph: Threads가 로그인 화면을 보여 주어 멈췄습니다. 로그인은 시도하지 않습니다. 간격을 늘리고 재개하거나 여기까지로 마치세요.\n      - paragraph: 간격을 늘리면 멈춘 채널의 요청 간격을 두 배로 늘립니다(최소 1초).\n      - button \"이어서 진행\"\n      - button \"간격을 늘리고 재개\"\n      - button \"여기까지로 마치기\"\n    - checkbox \"크롤링이 끝나면 전처리 · 라벨링(GPT, 블로그 · 카페 먼저)까지 자동으로 시작\"\n    - text: 크롤링이 끝나면 전처리 · 라벨링(GPT, 블로그 · 카페 먼저)까지 자동으로 시작\n    - heading \"P3 상세 수집\" [level=2]\n    - progressbar \"상세 수집 진행\"\n    - term: 완료 / 대상 URL\n    - definition: 0 / 50\n    - term: 원문 확보\n    - definition: —\n    - term: 분당 처리량\n    - definition: \"0\"\n    - term: 남은 시간\n    - definition: 계산 불가\n    - paragraph: 스니펫 — · 제한글 —\n    - region \"채널별 수집 상태 스크롤\":\n      - table \"채널별 수집 상태\":\n        - rowgroup:\n          - row \"채널 상태 시도 차단 파싱 오류 건너뜀\":\n            - columnheader \"채널\"\n            - columnheader \"상태\"\n            - columnheader \"시도\"\n            - columnheader \"차단\"\n            - columnheader \"파싱 오류\"\n            - columnheader \"건너뜀\"\n        - rowgroup:\n          - row \"Threads 차단으로 멈춤 20 20 0 —\":\n            - rowheader \"Threads\"\n            - cell \"차단으로 멈춤\"\n            - cell \"20\"\n            - cell \"20\"\n            - cell \"0\"\n            - cell \"—\"\n    - paragraph: 내부용 스냅샷 d1aa5c71278a4915bbcff1772f8dbdbc",
  "after": "- main:\n  - group:\n    - button \"이 단계부터 다시\"\n    - text: 2단계 · 크롤링\n    - heading \"수집 결과를 확인합니다\" [level=1]\n    - checkbox \"크롤링이 끝나면 전처리 · 라벨링(GPT, 블로그 · 카페 먼저)까지 자동으로 시작\"\n    - text: 크롤링이 끝나면 전처리 · 라벨링(GPT, 블로그 · 카페 먼저)까지 자동으로 시작\n    - heading \"P5 수집 요약\" [level=2]\n    - progressbar \"상세 수집 진행\"\n    - term: 완료 / 대상 URL\n    - definition: 0 / 0\n    - term: 원문 확보\n    - definition: —\n    - term: 분당 처리량\n    - definition: \"0\"\n    - term: 남은 시간\n    - definition: 계산 불가\n    - paragraph: 스니펫 — · 제한글 —\n    - region \"채널별 수집 상태 스크롤\":\n      - table \"채널별 수집 상태\":\n        - rowgroup:\n          - row \"채널 상태 시도 차단 파싱 오류 건너뜀\":\n            - columnheader \"채널\"\n            - columnheader \"상태\"\n            - columnheader \"시도\"\n            - columnheader \"차단\"\n            - columnheader \"파싱 오류\"\n            - columnheader \"건너뜀\"\n        - rowgroup:\n          - row \"Threads 완료 20 20 0 50 (차단으로 여기까지 마침)\":\n            - rowheader \"Threads\"\n            - cell \"완료\"\n            - cell \"20\"\n            - cell \"20\"\n            - cell \"0\"\n            - cell \"50 (차단으로 여기까지 마침)\"\n    - term: 수집 문서\n    - definition: \"0\"\n    - term: 채널\n    - definition: \"1\"\n    - term: 목록 URL\n    - definition: \"50\"\n    - term: 완료 URL\n    - definition: \"0\"\n    - heading \"건너뛴 항목\" [level=2]\n    - table \"채널별 건너뛴 사유\":\n      - rowgroup:\n        - row \"채널 사유 건수\":\n          - columnheader \"채널\"\n          - columnheader \"사유\"\n          - columnheader \"건수\"\n      - rowgroup:\n        - row \"Threads 차단으로 여기까지 마침 50건\":\n          - cell \"Threads\"\n          - cell \"차단으로 여기까지 마침\"\n          - cell \"50건\"\n    - heading \"채널 분포\" [level=2]\n    - text: Threads 0 · 0.0%\n    - table \"키워드별 수집 결과\":\n      - rowgroup:\n        - row \"키워드 채널 수집 문서 목록 URL 완료 URL\":\n          - columnheader \"키워드\"\n          - columnheader \"채널\"\n          - columnheader \"수집 문서\"\n          - columnheader \"목록 URL\"\n          - columnheader \"완료 URL\"\n      - rowgroup:\n        - row \"qa-empty Threads 0 0 0\":\n          - cell \"qa-empty\"\n          - cell \"Threads\"\n          - cell \"0\"\n          - cell \"0\"\n          - cell \"0\"\n        - row \"에어컨청소 Threads 0 25 0\":\n          - cell \"에어컨청소\"\n          - cell \"Threads\"\n          - cell \"0\"\n          - cell \"25\"\n          - cell \"0\"\n        - row \"제습기 Threads 0 25 0\":\n          - cell \"제습기\"\n          - cell \"Threads\"\n          - cell \"0\"\n          - cell \"25\"\n          - cell \"0\"\n    - heading \"키워드 상위\" [level=2]\n    - text: qa-empty 0 에어컨청소 0 제습기 0\n    - heading \"키워드 하위\" [level=2]\n    - text: 제습기 0 에어컨청소 0 qa-empty 0\n    - paragraph: 내부용 스냅샷 d1aa5c71278a4915bbcff1772f8dbdbc\n    - button \"전처리로 이동하기\"",
  "api": {
    "defaults": {
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
      ]
    },
    "available_sources": [
      "naver_blog",
      "naver_cafe",
      "naver_kin",
      "cook82",
      "threads",
      "youtube",
      "youtube_vlog",
      "clien",
      "ppomppu"
    ],
    "collection_keywords": [
      "에어컨청소",
      "제습기",
      "qa-empty"
    ],
    "collection_channels": [
      "threads"
    ],
    "min_interval_s": {
      "threads": 2
    },
    "added_keywords_count": 0,
    "status": "done",
    "resumable": false,
    "remaining_by_channel": {},
    "kind": "detail",
    "collectionId": "c1",
    "progress": {
      "done": 0,
      "target": 0,
      "full": 0,
      "snippet": 0,
      "restricted": 0,
      "per_minute": 0,
      "channels": {
        "threads": {
          "status": "done",
          "attempts": 20,
          "parse_errors": 0,
          "blocked": 20
        }
      },
      "list_tasks": {
        "threads": {
          "done": 3,
          "target": 3
        }
      },
      "skipped": {
        "threads": {
          "blocked": 50
        }
      }
    },
    "channels": {
      "threads": {
        "status": "done",
        "attempts": 20,
        "parse_errors": 0,
        "blocked": 20
      }
    },
    "paused_channels": [],
    "stopReason": "partial_finished",
    "snapshot_id": "d1aa5c71278a4915bbcff1772f8dbdbc",
    "gate": [
      {
        "kw": "qa-empty",
        "axis": "physical",
        "sub": "product_physical",
        "per_source": {
          "threads": {
            "listed": 0,
            "filtered": 0,
            "unique": 0
          }
        },
        "listed": 0,
        "after_filter": 0,
        "unique_ratio": 0,
        "badges": [
          "zero",
          "low"
        ],
        "count_unit": "urls"
      },
      {
        "kw": "에어컨청소",
        "axis": "physical",
        "sub": "product_physical",
        "per_source": {
          "threads": {
            "listed": 25,
            "filtered": 0,
            "unique": 25
          }
        },
        "listed": 25,
        "after_filter": 25,
        "unique_ratio": 1,
        "badges": [],
        "count_unit": "urls"
      },
      {
        "kw": "제습기",
        "axis": "physical",
        "sub": "product_physical",
        "per_source": {
          "threads": {
            "listed": 25,
            "filtered": 0,
            "unique": 25
          }
        },
        "listed": 25,
        "after_filter": 25,
        "unique_ratio": 1,
        "badges": [],
        "count_unit": "urls"
      }
    ],
    "estimate": {
      "urls": 50,
      "minutes": 0.8333333333333334
    },
    "report": {
      "matrix": {
        "qa-empty": {
          "threads": {
            "listed": 0,
            "filtered": 0,
            "excluded": 0,
            "full": 0,
            "snippet": 0,
            "restricted": 0,
            "unique": 0,
            "urls_listed": 0,
            "urls_done": 0
          }
        },
        "에어컨청소": {
          "threads": {
            "listed": 25,
            "filtered": 0,
            "excluded": 0,
            "full": 0,
            "snippet": 0,
            "restricted": 0,
            "unique": 25,
            "urls_listed": 25,
            "urls_done": 0
          }
        },
        "제습기": {
          "threads": {
            "listed": 25,
            "filtered": 0,
            "excluded": 0,
            "full": 0,
            "snippet": 0,
            "restricted": 0,
            "unique": 25,
            "urls_listed": 25,
            "urls_done": 0
          }
        }
      },
      "channels": {
        "threads": {
          "skipped": 50,
          "skip_reason": "blocked",
          "docs": 0,
          "urls_done": 0,
          "share": 0,
          "status": "done",
          "errors_top": [
            {
              "error": "crawl_error",
              "count": 50
            }
          ],
          "skip_reasons": {
            "blocked": 50
          }
        }
      },
      "totals": {
        "skipped": 50,
        "total": 50,
        "urls_listed": 50,
        "urls_done": 0,
        "doc_count": 0
      },
      "counts": {
        "qa-empty": {
          "threads": 0
        },
        "에어컨청소": {
          "threads": 0
        },
        "제습기": {
          "threads": 0
        }
      },
      "snapshot_id": "d1aa5c71278a4915bbcff1772f8dbdbc",
      "started_at": 1792479510.093529,
      "finished_at": 1792479566.3861918,
      "throughput_per_min": 0
    },
    "updatedAt": "2026-10-20T06:59:26.386192+00:00"
  },
  "dialog": {
    "type": "confirm",
    "message": "Threads 50건 미수집(차단)\n남은 URL을 건너뛰고 지금까지 모은 결과로 마치시겠습니까?"
  },
  "workerLogs": {
    "neg003-worker-list.log": "d1aa5c71278a4915bbcff1772f8dbdbc\n",
    "neg003-worker-detail.log": ""
  },
  "threadsBrowserRequests": []
}
```

## Evidence files

- [QA-NEG-003-data.json](QA-NEG-003-data.json)
- [blocked-prep-status.json](blocked-prep-status.json)
- [QA-NEG-003-finished-data.json](QA-NEG-003-finished-data.json)
- [server-logs/README.md](server-logs/README.md)
- [server-logs/neg003-worker-list.log](server-logs/neg003-worker-list.log)
- [server-logs/neg003-worker-detail.log](server-logs/neg003-worker-detail.log)

Screenshots were saved using explicit absolute paths and inspected for relevant states:

- [QA-NEG-003-paused.png](QA-NEG-003-paused.png) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-NEG-003-paused.png`
- [QA-NEG-003-result.png](QA-NEG-003-result.png) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-NEG-003-result.png`

Shared main browser console/network: [console-main.log](console-main.log), [network-main.log](network-main.log). Main console: no errors; logo aspect-ratio warning. Scenario-specific API responses and variant network records are in the JSON above or linked raw evidence. Screenshots supplement DOM/API evidence, not replace it.
