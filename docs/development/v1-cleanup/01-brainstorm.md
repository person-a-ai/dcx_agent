# v1-cleanup · 01 기획

- 작성: 2026-10-20 · 하네스 실행 `v1-cleanup` (base `4444a50`)
- 근거 조사(파일·행 단위 증거, 테스트 영향 목록): [plan.md](plan.md)

## 문제

DCX 2.0은 단계별로 다시 만들었고(0-2, 3-5, 6-8), 그동안 옛 세션은 옛 화면에서 읽기 전용으로 두고(D-060, D-303) 아직 다시 만들지 않은 뒤 단계를 살리려고 호환층(D-065)을 두었다. 모든 단계가 v2로 바뀌었는데 마지막 v1 제거를 하지 않아 두 구현이 공존한다. 그 결과:

1. 호출처 없는 v1 경로·함수가 남아 읽는 사람을 헷갈리게 한다(`/sample`, `/train`, `/preprocess`, 빈 `keywords` 라우터, `lib/api.ts`의 옛 함수 10개, 쓰지 않는 `crawl4ai` 의존성, 루트 `workflow.py`).
2. v2 전처리가 v1 파일(`services/preprocessing.py`)에서 함수를 import하고, 아무도 읽지 않는 호환 파일 `preprocessed/{sid}/*.jsonl`을 매번 쓴다.
3. **실제 오동작:** 클러스터링·페르소나·인사이트 페이지는 `schemaVersion`이 아니라 `prep.derivedRef` 유무로 옛 화면을 고른다. 사이드바는 "근거 탐색"만 잠그므로, 전처리를 끝내지 않은 새 세션이 세 단계를 누르면 v1 화면이 뜬다. `LegacyPersonasPage`는 실행을 막지 않아 v1 `/embed`·`/persona`를 부르고 세션 `step`을 `persona-start`로 저장한다.

## 운영 확인 (2026-10-19, 읽기만)

`https://dcx-api.person-a.ai/sessions`: 세션 4개(상한 20개 미만이라 전부), **모두 `schemaVersion: 2`, 옛 세션 0개.** 1개(`s795910f…`, step `r1`)는 `prep.derivedRef`가 없어 위 3번 오동작에 바로 걸린다.

## 결정

| # | 결정 | 출처 |
|---|---|---|
| 1 | 사이드바 챗봇(B-120)과 챗봇이 쓰는 모듈은 손대지 않는다 | 사용자, 2026-10-19 |
| 2 | 옛 세션 화면(Legacy 3개)과 그 백엔드(v1 군집·임베딩·페르소나)를 **전부 삭제**한다. 옛 세션을 열면 "구버전 세션은 이 단계를 열 수 없습니다" 배너 | 사용자: "안 열리면 어차피 깃에 다 남겨져 있어서 없애도 되는 거잖아" + 운영 옛 세션 0개 |
| 3 | 루트 `workflow.py` 삭제 | 사용자 |
| 4 | 전처리 전 새 세션: 사이드바에서 클러스터링·페르소나·인사이트도 잠그고(근거 탐색과 같은 방식), URL로 직접 오면 "전처리(3단계)를 먼저 완료하세요" 배너 + 전처리 화면 버튼 | 사용자 선택 |
| 5 | v2 전처리 문서의 `desc`·`cafe`·`link` 필드는 **유지**한다. 별도 호환 파일만 없앤다 | `model/export.py:93-94`(5단계 내보내기)와 챗봇이 이 필드를 읽음. 빼면 내보내기 내용이 바뀜 → 후속 과제 |
| 6 | 공유 함수 `_crawl_docs`·`filter_documents`(+ 내부 도우미)를 `app/prep/documents.py`로 옮기고 v1 전용 분기(collection 없는 옛 crawl 파일, `doc_id` 없는 옛 문서)는 지운다 | v2 호출 경로에서 닿을 수 없음(plan.md 2-1) |
| 7 | 데이터(맥미니의 `preprocessed/`, `clusters/`, `personas/` 파일)는 지우지 않는다. 코드만 정리 | 범위 최소화. 챗봇이 `clusters/`·`personas/`를 읽음 |

## 고려한 대안

- 옛 화면 처리: (A) 전부 삭제 ← 채택, (B) 읽기 전용 GET 3개만 남김, (C) 그대로. 운영에 옛 세션이 없어 B·C는 쓰는 사람 없는 코드를 남긴다.
- 전처리 전 새 세션: (가) 사이드바 잠금 + 배너 ← 채택, (나) 배너만. (가)는 잘못 들어가는 길 자체를 없앤다.
- 호환 필드: 이번에 함께 제거 vs 유지 ← 유지. 제거는 내보내기 형식 변경이라 별도 검증이 필요하다.

## 범위

**포함:** plan.md 1단계(죽은 코드), 2단계(이동 + 호환 파일 제거), 3단계 공통(사이드바 잠금 + 배너) + 3-A(옛 화면·백엔드 삭제), `workflow.py` 삭제, 문서(`BACKEND.md`, `PIPELINE.md`, `README.md`, decision-log D-060·D-065·D-303 한 줄씩).

**제외:** 챗봇(B-120), `.worktrees/`, `integrate/dcx-step07-11`, v2 라우터의 `is_legacy` 가드, `desc`·`cafe`·`link` 필드 제거, `clustersDone` 정리, 맥미니 데이터 파일 삭제, 배포.

## 성공 기준

1. 백엔드 앱이 더 이상 `/sample`, `/train`, `/train-status`, `/preprocess`, `/preprocess-status`, `/cluster`, `/cluster-status`, `/cluster-refine`, `/embed`, `/embed-status`, `/persona`(POST), `/persona-status`, `/sna-data`를 등록하지 않는다. `/chat`, `/insight-chat`, `/search`, v2 경로는 그대로다.
2. `backend/app`에 `app.services.preprocessing`, `services.training`, `services.clustering`, `services.personas`, `services.embedding`, `_publish_compat`, `compatRef` 참조가 0건이다.
3. v2 전처리를 돌려도 `preprocessed/` 아래에 파일이 생기지 않고, 이미 끝난 전처리는 호환 파일 없이 재사용된다.
4. 전처리 전 새 세션: 사이드바의 클러스터링·근거 탐색·페르소나·인사이트가 잠기고, 세 페이지 URL에 직접 가면 배너가 보이며 v1 API를 부르지 않는다.
5. 옛 세션(`schemaVersion` 없음): 세 페이지에서 "구버전 세션" 배너가 보인다.
6. 전처리를 끝낸 새 세션의 클러스터링·페르소나·인사이트 화면과 챗봇은 바뀌지 않는다.
7. 검사 통과: 백엔드 pytest, 프론트 lint · vitest · build.

## 기준선 (main `4444a50`)

- 프론트: lint 통과, vitest 76파일 · 942테스트 통과, build 통과.
- 백엔드(CI와 같은 의존성으로 새로 만든 venv, `-n auto`): 2842 통과, 3 실패. 실패 3개(`test_prep_api.py::test_qa_q1_server_default_exposed_and_first_run_succeeds`, `test_run_then_status_done`, `test_integration_stage0_2.py::test_end_to_end_0_to_preprocess`)는 단독 실행 시 모두 통과 → 병렬 부하에서 전처리 완료 대기 시간 초과(타이밍 불안정). 정리 후에도 같은 기준으로 비교하고, 불안정 테스트는 단독 재실행으로 확인한다.
- 공용 체크아웃의 `backend/venv`에는 torch·pytest-xdist가 없어 79개 모듈 import가 실패한다. `harness.config.json`은 `backend/.venv`를 기대하므로 작업 워크트리에 `backend/.venv`를 만든다.

## 위험

- 테스트 삭제가 v2 동작 검증까지 지우지 않도록, 지우는 테스트마다 plan.md에 v2 대응 테스트 또는 "v1 전용" 근거를 적는다.
- `filter_documents` 이동 중 동작이 바뀌면 전처리 결과가 달라진다 → 이동 전후 같은 입력으로 같은 출력을 내는지 테스트로 고정(카페 이름·슬러그 제외, 품질 기준, `desc` 4,000자 제한).
- 사이드바 잠금 조건을 바꾸면 전처리를 끝낸 세션이 잘못 잠길 수 있다 → `derivedRef` 있음/없음 × `schemaVersion` 있음/없음 네 경우를 테스트로 고정.
