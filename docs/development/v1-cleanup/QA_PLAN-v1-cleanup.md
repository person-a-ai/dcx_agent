# QA Plan — v1-cleanup

| | |
|---|---|
| Source spec | [01-brainstorm.md](01-brainstorm.md) · [02-design.md](02-design.md) · [03-plan.md](03-plan.md) |
| Branch / version | `chore/v1-cleanup` (base `4444a50`) |
| Author | Main Claude (Controller) |
| Last updated | 2026-10-20 |
| Status | reviewed (plan-eng-review), 계획 승인 대기 |

## 1. Scope

**In scope**
- 전처리 전 새 세션의 사이드바 잠금(클러스터링·근거 탐색·페르소나·인사이트)과 세 페이지 배너
- 옛 세션(`schemaVersion` 없음)과 세션 미선택 상태의 세 페이지 배너
- 전처리를 끝낸 새 세션의 세 페이지·사이드바가 바뀌지 않음
- v2 전처리가 호환 파일 없이 끝나고 재사용됨
- 삭제한 v1 API 경로가 404이고 이름이 비슷한 v2 경로는 살아 있음
- 챗봇(범위 밖) 회귀

**Out of scope**
- 챗봇 답변 품질·내용(B-120). 회귀는 "열리고 요청이 404가 아님"까지만 본다.
- 운영 서버(dcx.person-a.ai) — QA는 로컬 실행 환경에서만 한다. 배포는 별도 요청.
- 맥미니 데이터 파일 정리.
- 로그인·권한(제품에 권한 모델이 없음).

**Open questions**
- 없음(Q1·Q2·잠금 방식은 2026-10-19~20 사용자 결정으로 확정).

## 2. Acceptance Criteria

| # | Criterion | Covered by |
|---|---|---|
| AC-1 | 지운 13개 v1 경로가 등록되지 않는다. `/chat`, `/insight-chat`, `/search`, v2 경로는 그대로다 | QA-NEG-001, QA-NEG-002, QA-REG-001 |
| AC-2 | 앱 코드에 v1 모듈 참조가 없다 | 단위 테스트 `backend/tests/test_v1_boundary.py`(브라우저 QA 대상 아님) |
| AC-3 | v2 전처리가 `preprocessed/`에 아무것도 쓰지 않고, 끝난 결과는 호환 파일 없이 재사용된다 | QA-E2E-006 |
| AC-4 | 전처리 전 새 세션: 사이드바 6~9단계가 잠기고, 세 페이지 URL은 배너를 보이며 v1 API를 부르지 않는다 | QA-E2E-001, QA-E2E-002, QA-E2E-003, QA-E2E-004, QA-EDGE-001, QA-EDGE-004 |
| AC-5 | 옛 세션: 세 페이지에서 "구버전 세션" 배너 | QA-E2E-007 |
| AC-6 | 전처리를 끝낸 새 세션의 세 화면·사이드바, 챗봇은 바뀌지 않는다 | QA-E2E-005, QA-EDGE-002, QA-REG-001, QA-REG-002 |
| AC-7 | 백엔드 pytest, 프론트 lint·vitest·build 통과 | 하네스 `evidence`(브라우저 QA 대상 아님) |
| AC-8 | v2 전처리 문서에 `desc`·`cafe`·`link`가 남는다 | QA-REG-003 |

## 3. Critical User Journeys

| # | Journey | Tier | Priority |
|---|---|---|---|
| J-1 | 새 세션이 전처리 전에 6~9단계로 가려 함 → 막히고 전처리로 안내됨 | data(옛 화면이 세션 `step`을 덮어쓰던 경로 제거) | P0 |
| J-2 | 전처리를 끝낸 새 세션이 클러스터링·페르소나·인사이트를 씀 | core | P0 |
| J-3 | 새 세션의 전처리 실행·재실행 | data | P0 |
| J-4 | 옛 세션 또는 세션 없이 6~9단계 URL로 들어옴 | other | P1 |
| J-5 | 사이드바 챗봇 사용 | core(범위 밖 회귀) | P1 |

## 4. E2E Scenarios

```
QA-E2E-001
Priority: P0
Type: Acceptance / E2E
Journey: J-1
Given: 전처리를 하지 않은 새(schemaVersion 2) 세션 "QA 전처리 전"을 시작 화면에서 선택한 상태
When: 왼쪽 사이드바를 본다
Then:
  - "클러스터링", "근거 탐색", "페르소나", "인사이트" 4개 항목이 aria-disabled="true"이다
  - 4개 항목 모두 title이 "전처리(3단계)를 먼저 완료하세요"이다
  - 4개 항목에 href가 없다
  - "시작"~"학습" 6개 항목은 href가 있는 링크다
  - 잠긴 "클러스터링"을 클릭해도 URL이 바뀌지 않는다
```

```
QA-E2E-002
Priority: P0
Type: Acceptance / E2E
Journey: J-1
Given: QA-E2E-001과 같은 세션이 선택된 상태, 브라우저 네트워크 기록을 비운 상태
When: 주소창에 /pipeline/clustering 을 직접 입력해 연다
Then:
  - "3단계(전처리)를 먼저 완료하세요. 전처리가 끝나야 클러스터링 화면을 열 수 있습니다." 문구가 보인다
  - "전처리 화면으로" 버튼이 보인다
  - 네트워크 기록에 /cluster-status, /cluster, /cluster-refine, /save-session 요청이 없다
  - "전처리 화면으로"를 누르면 URL이 /pipeline/preprocess 가 된다
```

```
QA-E2E-003
Priority: P0
Type: Acceptance / E2E
Journey: J-1
Given: QA-E2E-001과 같은 세션이 선택된 상태, 네트워크 기록을 비운 상태
When: /pipeline/personas 를 직접 연다
Then:
  - "전처리가 끝나야 페르소나 화면을 열 수 있습니다." 문구가 보인다
  - 화면에 "시작" 버튼(옛 페르소나 생성)이 없다
  - 네트워크 기록에 /embed, /persona(POST), /persona-status, /save-session 요청이 없다
  - 백엔드 GET /session/{sid} 응답의 data.step 값이 이 동작 전과 같다
```

```
QA-E2E-004
Priority: P0
Type: Acceptance / E2E
Journey: J-1
Given: QA-E2E-001과 같은 세션이 선택된 상태, 네트워크 기록을 비운 상태
When: /pipeline/insights 를 직접 연다
Then:
  - "전처리가 끝나야 인사이트 화면을 열 수 있습니다." 문구가 보인다
  - 네트워크 기록에 /sessions(옛 인사이트 화면의 세션 목록), /persona-status, /cluster-status, /sna-data 요청이 없다
```

```
QA-E2E-005
Priority: P0
Type: Acceptance / E2E
Journey: J-2
Given: 전처리를 끝낸(prep.derivedRef 있음) 새 세션 "QA 전처리 완료"를 선택한 상태
When: 사이드바에서 클러스터링, 페르소나, 인사이트를 차례로 누른다
Then:
  - 사이드바 10개 항목 모두 href가 있고 aria-disabled 항목이 없다
  - /pipeline/clustering 에서 "클러스터링 실행" 버튼 또는 기존 클러스터 결과 목록이 보인다(새 구획 화면)
  - /pipeline/personas 에서 새 페르소나 화면이 보이고 "전처리를 먼저 완료하세요" 문구가 없다
  - /pipeline/insights 에서 새 인사이트 화면이 보이고 "구버전 세션" 문구가 없다
  - 세 화면에서 콘솔 오류(error 레벨)가 0건이다
```

```
QA-E2E-006
Priority: P0
Type: Acceptance / E2E
Journey: J-3
Given: 수집이 끝난 새 세션 "QA 전처리 실행"(fixture 채널, 임베더 fake), 로컬 데이터 폴더에 preprocessed/ 폴더가 없는 상태
When: /pipeline/preprocess 에서 전처리를 실행하고 끝날 때까지 기다린 뒤, 같은 설정으로 다시 실행한다
Then:
  - 첫 실행 후 GET /prep/{sid}/status 의 status가 "done"이다
  - 로컬 데이터 폴더에 preprocessed/ 폴더가 생기지 않는다
  - derived/{sid}/{collectionId}/{prepKey}/manifest.json 에 compatRef 키가 없다
  - 두 번째 POST /prep/{sid}/run 응답의 reused 가 true 이다
  - 실행 후 사이드바의 클러스터링 항목이 링크로 바뀐다(QA-EDGE-002와 같은 확인)
```

```
QA-E2E-007
Priority: P1
Type: Acceptance / E2E
Journey: J-4
Given: schemaVersion 키가 없는 옛 세션 "QA 옛 세션"을 데이터 폴더에 직접 만들어 시작 화면에서 선택한 상태
When: /pipeline/clustering, /pipeline/personas, /pipeline/insights 를 차례로 직접 연다
Then:
  - 세 페이지 모두 "구버전 세션은 이 단계를 열 수 없습니다. 새 프로젝트를 만들어 진행하세요." 문구가 보인다
  - "프로젝트 선택하기"를 누르면 URL이 /pipeline/start 가 된다
  - 네트워크 기록에 /cluster-status, /persona-status, /sna-data, /embed 요청이 없다
```

## 5. Negative Scenarios

```
QA-NEG-001
Priority: P1
Type: Negative
Journey: J-3
Given: 로컬 백엔드가 실행 중
When: POST /preprocess, GET /preprocess-status/x, GET /sample/x, POST /train, GET /train-status/x, POST /cluster, GET /cluster-status/x, POST /cluster-refine, POST /embed, GET /embed-status/x, POST /persona, GET /persona-status/x, GET /sna-data/x 를 보낸다(JSON 본문 {"sid":"x"})
Then:
  - 13개 모두 HTTP 404 또는 405이다
  - 어느 응답에도 파이썬 Traceback 문자열이 없다
```

```
QA-NEG-002
Priority: P1
Type: Negative
Journey: J-2
Given: QA-E2E-005의 세션 sid
When: GET /persona/{sid}/status, GET /train/{sid}/status, GET /prep/{sid}/status 를 보낸다
Then:
  - 세 응답 모두 404가 아니다(경로 접두사가 비슷한 v2 경로가 살아 있음)
```

```
QA-NEG-003
Priority: P1
Type: Negative
Journey: J-4
Given: 브라우저 저장소를 비워 선택된 세션이 없는 상태
When: /pipeline/clustering 을 직접 연다
Then:
  - "프로젝트를 먼저 선택하세요." 문구가 보인다
  - "프로젝트 선택하기"를 누르면 URL이 /pipeline/start 가 된다
  - 콘솔 오류가 0건이다
```

## 6. Edge Cases

```
QA-EDGE-001
Priority: P1
Family: Navigation and lifecycle / 모바일
Given: QA-E2E-001과 같은 세션, 뷰포트 375×812
When: /pipeline/personas 를 연다
Then:
  - 사이드바가 번호만 보이는 접힌 폭(72px)이다
  - 배너 문구 전체가 잘리지 않고 보인다
  - "전처리 화면으로" 버튼이 화면 안에 있고 누를 수 있다
  - 가로 스크롤이 생기지 않는다(document.documentElement.scrollWidth ≤ 375)
```

```
QA-EDGE-002
Priority: P0
Family: State and session
Given: QA-E2E-006의 첫 전처리 실행이 진행 중이고 사이드바 6~9가 잠긴 상태
When: 전처리가 끝날 때까지 새로고침 없이 기다린다
Then:
  - 끝난 뒤 새로고침 없이 사이드바 "클러스터링" 항목에 href="/pipeline/clustering" 이 생긴다
  - 새로고침해도 링크 상태가 유지된다
```

```
QA-EDGE-003
Priority: P2
Family: State and session / 버전
Given: QA-E2E-005의 세션에서 3단계부터 다시 시작해 새 버전(v2)을 만든 상태(전처리 결과 없음)
When: 사이드바와 /pipeline/clustering 을 본다
Then:
  - 사이드바 6~9가 잠긴다
  - /pipeline/clustering 에 "3단계(전처리)를 먼저 완료하세요" 배너가 보인다
```

```
QA-EDGE-004
Priority: P2
Family: Navigation and lifecycle / 키보드
Given: QA-E2E-001과 같은 세션
When: 사이드바에서 Tab 키로 항목을 차례로 이동한다
Then:
  - 잠긴 4개 항목에는 포커스가 가지 않는다
  - 잠기지 않은 항목은 포커스 링(2px outline)이 보인다
```

## 7. Regression Scope

| ID | Existing behavior at risk | Why | Priority |
|---|---|---|---|
| QA-REG-001 | 파이프라인 사이드바 챗봇: 패널이 열리고 메시지 전송 시 POST /chat 이 404가 아니며 답변 또는 오류 문구가 패널에 표시된다. 인사이트 화면 챗봇도 POST /insight-chat 이 404가 아니다 | `lib/api.ts`에서 `sendChat`·`sendInsightChat`만 남기고 정리, 챗봇 의존 모듈 유지 확인 | P1 |
| QA-REG-002 | `/insights` 로 가면 `/pipeline/insights` 로 이동한다 | `app/insights/page.tsx` 유지, `LegacyInsightsPage.tsx` 삭제 | P1 |
| QA-REG-003 | 전처리 결과 문서(`derived/.../docs/*.jsonl`)의 각 행에 `desc`·`cafe`·`link` 키가 있고 `desc`는 4,000자 이하다 | `filter_documents`를 `app/prep/documents.py`로 옮김. 5단계 내보내기·챗봇이 읽음 | P0 |
| QA-REG-004 | 키워드 화면(`/pipeline/keywords`)이 열리고 콘솔 오류가 0건이다 | `lib/api.ts`의 옛 `suggestWords` 삭제(키워드 화면은 `lib/api/keywords.ts` 사용) | P2 |
| QA-REG-005 | 옛 세션으로 `/pipeline/crawling` 을 열면 기존 "구버전 세션은 0~2단계를 편집할 수 없습니다" 배너가 그대로 보인다 | 옛 세션 처리 문구가 섞이지 않는지 | P2 |

Searched: `grep`으로 `lib/api.ts` 함수별 importer, `components/*` importer, 백엔드 `preprocessed/`·`compatRef`·`desc`·`cafe` 읽는 곳, `routers/chat.py` import, `StepBar` 사용처와 기존 테스트(`completedThrough.test.ts`, `insight.test.ts`, `insight-route.test.ts`, `clustering/page.test.ts`)를 확인했다.

## 8. Test Data / Preconditions

| Item | Value / source | Notes |
|---|---|---|
| 실행 환경 | 워크트리 `/Users/yunho/Documents/dcx_agent-v1-cleanup`의 최신 task commit. 백엔드 `backend/.venv/bin/python -m uvicorn app.main:app --port 8000`(cwd `backend`), 프론트 `npm --prefix frontend run dev`(`NEXT_PUBLIC_API_URL=http://localhost:8000`) | QA 워커가 직접 띄운다 |
| 환경 변수 | `STORAGE=local`, `LOCAL_DATA_DIR=<QA 전용 임시 폴더>`, `EMBED_BACKEND=fake`, `ENABLE_FIXTURE_CHANNEL=true`, `CORS_ORIGINS=http://localhost:3000` | 실제 API 키 불필요 |
| 계정 | 없음(권한 모델 없음) | |
| 세션 "QA 전처리 전" | `POST /context`로 생성, 수집·전처리 안 함 | QA-E2E-001~004, QA-EDGE-001, QA-EDGE-004 |
| 세션 "QA 전처리 실행" | `POST /context` → fixture 채널로 수집 완료(또는 `backend/tests/prep/test_prep_api.py`의 `collected` 픽스처처럼 `crawl/{sid}/collections/c1`에 manifest·queue·docs를 직접 기록) | QA-E2E-006, QA-EDGE-002, QA-REG-003 |
| 세션 "QA 전처리 완료" | "QA 전처리 실행" 세션의 전처리 완료 후 그대로 사용 | QA-E2E-005, QA-NEG-002, QA-EDGE-003 |
| 세션 "QA 옛 세션" | `LOCAL_DATA_DIR/sessions/qaold/session.json`에 `{"bk":"옛 제품","step":"clustering"}` 기록(`schemaVersion` 없음) | QA-E2E-007, QA-REG-005 |
| 시드 스크립트 위치 | `docs/development/v1-cleanup/qa/` 아래(QA 워커가 쓸 수 있는 유일한 경로) | 제품 소스·Git 변경 금지 |
| External services | 모두 끔(fake 임베더, fixture 채널). 챗봇 LLM 키가 없으면 QA-REG-001은 "404가 아님 + 패널에 오류 문구 표시"로 판정 | |

## 9. Priority

- **P0** — 데이터를 잘못 쓰던 경로(J-1)와 전처리 데이터(J-3), 핵심 화면 회귀(J-2), 내보내기 필드(QA-REG-003)
- **P1** — 옛 세션·세션 없음(J-4), 삭제 경로 확인, 챗봇 회귀, 모바일
- **P2** — 키보드 포커스, 버전 재시작, 화면 문구 회귀

## 10. Expected Result

**Pass condition** — 모든 활성 ID(QA-E2E-001~007, QA-NEG-001~003, QA-EDGE-001~004, QA-REG-001~005)가 PASS이고, 각 시나리오에 실행 단계·기대/실제·시간·스크린샷 또는 응답 로그 경로가 `docs/development/v1-cleanup/qa/`에 있다. FAIL/BLOCKED/NOT_RUN이 하나라도 있으면 browser-qa 단계를 완료하지 않는다.

**Known gaps**
- QA-REG-001은 LLM 키 없이 답변 내용을 볼 수 없다 → "요청 경로 생존 + UI 오류 처리"까지만 판정한다.
- QA-E2E-003의 "세션 step 불변"은 화면만으로 볼 수 없어 GET /session/{sid}로 보강한다(승인된 읽기 도구).
- QA-E2E-006·QA-REG-003의 파일 확인은 로컬 데이터 폴더 읽기로 보강한다.

**Already covered by existing tests**
- AC-2: `backend/tests/test_v1_boundary.py`(T1~T3에서 추가)
- QA-NEG-001의 경로 목록: `test_v1_boundary.py::test_v1_routes_removed_and_chat_kept`(앱 라우트 수준). 브라우저 QA는 실제 HTTP 응답으로 다시 확인한다.
- QA-E2E-001·QA-E2E-005의 사이드바 마크업: `frontend/src/lib/logic/completedThrough.test.ts`(T5에서 바꿈). 브라우저 QA는 실제 세션 데이터로 다시 확인한다.
