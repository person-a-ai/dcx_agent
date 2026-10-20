# QA-EDGE-001 — PASS

URL: http://localhost:3000/pipeline/crawling

Tested commit: c597b2a678231016e51b0d3644f3d6df921810c2; observed HEAD: c597b2a678231016e51b0d3644f3d6df921810c2.

## Approved scenario (unchanged)

```text
QA-EDGE-001
Priority: P1
Type: Edge / Empty
Given: 확정 키워드가 `qa-empty` 하나뿐인 세션
When: 네 새 채널로 목록 수집을 끝낸다
Then:
  - 게이트 화면 인사이트에 "수집된 목록이 없습니다"가 보인다
  - 상세 수집 예상 대상 URL이 0이다
  - 화면에 오류 배너가 없다
```

## Executed steps

1. QA 빈 결과 새 세션 열기
2. 네 새 채널 목록 수집 시작
3. 완료 게이트 UI와 상태 API 확인

## Actual / verdict

qa-empty 단일 키워드 목록 완료. 수집된 목록이 없습니다 안내, 대상 URL=0, 오류 배너 없음.

도구 선택자 strict 오류 및 재실행 중 다른 샘플 세션의 disabled 버튼 timeout은 empty-sample-data.json/empty-sample-retry-data.json에 보존. 완료된 QA 빈 결과의 정확한 sid=s3374891ec39441adb0ba71d0c579975a API와 그 세션을 연 tab4의 실제 게이트를 최종 검증했다.

## Timestamped DOM / API evidence

```json
{
  "time": "2026-10-20T07:03:14.316Z",
  "url": "http://localhost:3000/pipeline/crawling",
  "dom": "- main:\n  - group:\n    - button \"이 단계부터 다시\"\n    - text: 2단계 · 크롤링\n    - heading \"본문 수집 전에 키워드를 정리합니다\" [level=1]\n    - status: Threads는 로그인 없이 볼 수 있는 결과만 모아 키워드당 약 20건입니다. Threads 때문에 \"저수율\" 배지가 붙은 키워드는 다른 채널 수치를 함께 보고 판단하세요.\n    - text: 목록 신호\n    - heading \"키워드 1개를 검토하세요\" [level=2]\n    - text: 수집된 목록이 없습니다. 날짜 범위와 채널을 확인하고 목록을 다시 수집하세요. 키워드 1개\n    - button \"설정으로 돌아가기\"\n    - heading \"상세 수집 예상\" [level=2]\n    - term: 대상 URL\n    - definition: \"0\"\n    - term: 예상 소요\n    - definition: 약 0분\n    - paragraph: 저장된 제외 목록 기준입니다. 중간에 멈춰도 이어서 진행합니다.\n    - paragraph: 유튜브 브이로그는 영상마다 자막 구간을 나누므로 영상 1개가 문서 여러 건이 됩니다.\n    - button \"배지 있는 행 먼저 보기\" [pressed]\n    - button \"0건 보기\"\n    - button \"저수율 보기\"\n    - button \"고유 기여 낮음 보기\"\n    - button \"배지 행 모두 제외\"\n    - text: 0개 제외 선택\n    - table \"키워드별 목록 검토\":\n      - rowgroup:\n        - row \"제외 키워드 축 · 하위 목록 → 필터 후 고유 기여 채널 상태\":\n          - columnheader \"제외\"\n          - columnheader \"키워드\"\n          - columnheader \"축 · 하위\"\n          - columnheader \"목록 → 필터 후\"\n          - columnheader \"고유 기여\"\n          - columnheader \"채널\"\n          - columnheader \"상태\"\n      - rowgroup:\n        - row \"qa-empty 제외 qa-empty · 펼치기 physical · product_physical 0 → 0 — 82쿡 0, 0% 지식iN 0, 0% Threads 0, 0% 유튜브 브이로그 0, 0% 0건 저수율\":\n          - cell \"qa-empty 제외\":\n            - checkbox \"qa-empty 제외\"\n          - rowheader \"qa-empty · 펼치기\":\n            - button \"qa-empty · 펼치기\"\n          - cell \"physical · product_physical\"\n          - cell \"0 → 0\"\n          - cell \"—\"\n          - cell \"82쿡 0, 0% 지식iN 0, 0% Threads 0, 0% 유튜브 브이로그 0, 0%\"\n          - cell \"0건 저수율\"\n    - paragraph: 다른 키워드도 찾은 URL은 유지됩니다. 제외한 키워드는 다음 세션의 과거 0건 키워드 근거로 남습니다.\n    - paragraph: 내부용 스냅샷 99f697f7e163452a9a717fc8aeb09d19\n    - region \"저장 작업\":\n      - status: 변경 사항 없음\n      - button \"임시 저장\"\n      - button \"저장\"\n      - button \"상세 수집 시작\"\n    - paragraph: 설정과 제외 선택을 저장한 다음 수집을 시작하세요.",
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
      "qa-empty"
    ],
    "collection_channels": [
      "youtube_vlog",
      "threads",
      "naver_kin",
      "cook82"
    ],
    "min_interval_s": {
      "youtube_vlog": 0,
      "threads": 2,
      "naver_kin": 0.5,
      "cook82": 0.5
    },
    "added_keywords_count": 0,
    "status": "done",
    "resumable": false,
    "remaining_by_channel": {},
    "kind": "list",
    "collectionId": "c1",
    "progress": {
      "done": 0,
      "target": 0,
      "full": 0,
      "snippet": 0,
      "restricted": 0,
      "per_minute": 0,
      "channels": {
        "youtube_vlog": {
          "status": "done",
          "attempts": 1,
          "parse_errors": 0,
          "blocked": 0
        },
        "threads": {
          "status": "done",
          "attempts": 1,
          "parse_errors": 0,
          "blocked": 0
        },
        "naver_kin": {
          "status": "done",
          "attempts": 1,
          "parse_errors": 0,
          "blocked": 0
        },
        "cook82": {
          "status": "done",
          "attempts": 1,
          "parse_errors": 0,
          "blocked": 0
        }
      },
      "list_tasks": {
        "cook82": {
          "done": 1,
          "target": 1
        },
        "naver_kin": {
          "done": 1,
          "target": 1
        },
        "threads": {
          "done": 1,
          "target": 1
        },
        "youtube_vlog": {
          "done": 1,
          "target": 1
        }
      },
      "skipped": {}
    },
    "channels": {
      "youtube_vlog": {
        "status": "done",
        "attempts": 1,
        "parse_errors": 0,
        "blocked": 0
      },
      "threads": {
        "status": "done",
        "attempts": 1,
        "parse_errors": 0,
        "blocked": 0
      },
      "naver_kin": {
        "status": "done",
        "attempts": 1,
        "parse_errors": 0,
        "blocked": 0
      },
      "cook82": {
        "status": "done",
        "attempts": 1,
        "parse_errors": 0,
        "blocked": 0
      }
    },
    "paused_channels": [],
    "stopReason": null,
    "snapshot_id": "99f697f7e163452a9a717fc8aeb09d19",
    "gate": [
      {
        "kw": "qa-empty",
        "axis": "physical",
        "sub": "product_physical",
        "per_source": {
          "cook82": {
            "listed": 0,
            "filtered": 0,
            "unique": 0
          },
          "naver_kin": {
            "listed": 0,
            "filtered": 0,
            "unique": 0
          },
          "threads": {
            "listed": 0,
            "filtered": 0,
            "unique": 0
          },
          "youtube_vlog": {
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
      }
    ],
    "estimate": {
      "urls": 0,
      "minutes": 0
    },
    "report": null,
    "updatedAt": "2026-10-20T07:01:40.524990+00:00"
  }
}
```

## Evidence files

- [empty-sample-final-data.json](empty-sample-final-data.json)
- [empty-sample-cases.js](empty-sample-cases.js)

Screenshots were saved using explicit absolute paths and inspected for relevant states:

- [QA-EDGE-001.png](QA-EDGE-001.png) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-001.png`

Shared main browser console/network: [console-main.log](console-main.log), [network-main.log](network-main.log). Main console: no errors; logo aspect-ratio warning. Scenario-specific API responses and variant network records are in the JSON above or linked raw evidence. Screenshots supplement DOM/API evidence, not replace it.
