# DCX 1.0(v1) 코드 정리 계획

- 작성: 2026-10-19 · 기준: `main` @ `4444a50` · 작업 브랜치: `chore/v1-cleanup` (워크트리 `../dcx_agent-v1-cleanup`, 공용 체크아웃은 `main` 그대로)
- 상태: **계획 · 사용자 승인 대기**. 승인 전에는 코드를 바꾸지 않는다. 이 파일은 승인 후 브랜치의 첫 커밋으로 옮긴다.
- 범위 밖(2026-10-19 사용자 결정): 사이드바 챗봇(B-120). `routers/chat.py`, `/chat`, `/insight-chat`, `sendChat`/`sendInsightChat`, `app/insights/layout.tsx`, `ChatPanel`은 건드리지 않는다. 챗봇이 쓰는 `services/s3.py`, `services/claude.py`, `jobs/manager.py`, `app.known.filter`, `models/schemas.py`의 `ChatRequest`/`InsightChatRequest`/`SearchRequest`는 유지한다.
- 범위 밖: `.worktrees/`, `integrate/dcx-step07-11` 브랜치, v2 라우터 안의 `is_legacy` 가드(옛 세션 데이터로부터 v2 API를 지키는 코드라 그대로 둔다).

## 0. 결정이 필요한 것

| # | 질문 | 영향 |
|---|---|---|
| Q1 | 맥미니에 아직 열어 봐야 하는 옛 세션(`schemaVersion` 없음)이 있는가? | 3단계 범위가 A(전부 삭제) / B(읽기 전용만 남김) / C(그대로) 중 하나로 정해진다 |
| Q2 | 루트 `workflow.py`(1,351줄 Flask 원형, `initial files` 커밋 이후 그대로, 어디서도 import·실행하지 않음)를 지워도 되는가? | 지우면 `preprocessed/` 경로를 쓰는 마지막 파일도 사라진다 |

맥미니에서 옛 세션 수 확인(읽기만 함). `GET /sessions`는 최근 20개만 돌려주므로 디스크를 직접 센다.

```bash
cd /배포루트/shared/data/sessions && python3 -c 'import json,glob; s=[p.split("/")[0] for p in glob.glob("*/session.json") if "schemaVersion" not in json.load(open(p))]; print(len(s), s)'
```

참고: 개발 맥의 `backend/data/sessions` 4개는 모두 옛 세션이다(테스트 잔여물로 보이며 맥미니 상황과는 무관).

### 답 (2026-10-19)

- **Q1 → 3-A(전부 삭제).** 운영 API(`https://dcx-api.person-a.ai/sessions`, 읽기만)를 확인하니 세션은 4개(20개 상한 미만이라 전부)이고 **모두 `schemaVersion: 2`, 옛 세션 0개**다. 사용자 지시: "안 열리면 어차피 깃에 다 남겨져 있어서 없애도 되는 거잖아." 단, 4개 중 1개(`s795910f…`, step `r1`)는 `prep.derivedRef`가 없어 지금 클러스터링·페르소나·인사이트를 누르면 Legacy 화면으로 빠진다(아래 절의 오분기). 화면 선택이 세션 상태를 쓸 수 있어 UI로 열어 보지는 않았다.
- **Q2 → `workflow.py` 삭제.**

### Legacy 화면은 옛 세션만 쓰는 게 아니다

세 화면의 분기 조건은 `schemaVersion`이 아니라 **`prep.derivedRef` 유무**다(`app/pipeline/clustering/page.tsx:19`, `personas/page.tsx:18`, `insights/page.tsx:12`). 사이드바(`components/StepBar.tsx:68`)는 `derivedRef`가 없을 때 "근거 탐색"(8번째) 하나만 잠그므로, **3단계(전처리)를 아직 끝내지 않은 새 v2 세션**도 클러스터링·페르소나·인사이트를 누르면 Legacy 화면이 뜬다.

- `LegacyClusteringPage`는 `readonly = true`라 실행은 막힌다.
- `LegacyPersonasPage`는 막지 않는다. "시작"을 누르면 `/embed`·`/persona`(v1)를 부르고 `saveSession`으로 `step: "persona-start"`를 저장한다. v2 세션이면 `run_persona`가 `clusters/` 파일을 못 찾아 "no data" 오류로 끝나지만 `step` 값은 이미 바뀐다. 옛 세션이면 D-060(읽기 전용)을 어긴다.

따라서 Q1의 답과 무관하게, 3단계에서 **v2 세션이 `derivedRef` 없이 6·8·9단계에 들어오면 Legacy 화면 대신 "3단계(전처리)를 먼저 완료하세요" 배너**를 보여 주도록 바꾼다. 옛 세션 화면을 남길지(Q1)는 `schemaVersion`으로 따로 가른다.

## 1단계 — 죽은 코드 삭제 (어떤 화면에서도 호출하지 않음)

| 대상 | 처리 | 근거 |
|---|---|---|
| `backend/app/routers/keywords.py` | 삭제 + `main.py` 등록 제거 | 빈 `APIRouter()` 뿐("Legacy keyword endpoints removed") |
| `backend/app/routers/labeling.py` (`GET /sample/{sid}`) | 삭제 | 프론트 `getSample` 호출처 없음. `preprocessed/{sid}/`를 읽는 곳 중 하나 |
| `backend/app/routers/training.py` (`POST /train`, `GET /train-status/{sid}`) + `services/training.py` | 삭제 | 프론트 `startTrain`/`getTrainStatus` 호출처 없음. 옛 세션 학습 화면은 v2 `training_v2.py:60`의 `is_legacy` 분기가 이미 처리. `services/training.py`는 저장된 결과를 다시 읽기만 하는 껍데기 |
| `backend/app/routers/preprocessing.py` (`POST /preprocess`, `GET /preprocess-status/{sid}`) + `services/preprocessing.preprocess_data`·`_InlineContext` | 삭제 | 프론트 `startPreprocess`/`getPreprocessStatus` 호출처 없음(새 화면은 `/prep/{sid}/run`). 옛 세션 실행은 D-060에 따라 필요 없음 |
| `models/schemas.py`의 `CrawlRequest`, `PreprocessRequest`, `TrainRequest`, `KeywordGenRequest`, `ScoreKeywordsRequest`, `SuggestWordsRequest` | 삭제 | 위 라우터 전용이거나 사용처 0(grep) |
| `utils/text.py`의 `get_llm_predictions` | 삭제 (`clean_text`는 유지: `crawl/worker.py`가 씀) | 사용처 0 |
| `backend/requirements.txt`의 `crawl4ai` | 삭제. `README.md` 103·107행 `crawl4ai-setup` 안내 삭제. `constraints.txt`에서 crawl4ai만 끌어오던 고정(예: `playwright`, `playwright-stealth`)은 crawl4ai 없이 새 venv를 만들어 `pip freeze` 차이로 확인한 것만 삭제 | `backend/app`에 `crawl4ai`·`playwright` import 0. D-094 이후 카페도 httpx로 수집 |
| `frontend/src/lib/api.ts`: `deleteSession`, `suggestWords`, `startCrawl`, `getCrawlStatus`, `startPreprocess`, `getPreprocessStatus`, `getSample`, `startTrain`, `getTrainStatus`, `getEmbedStatus` | 삭제 | 모두 `lib/api.ts` 밖 import 0. `suggestWords`(옛 `POST /suggest-words`)·`getCrawlStatus`(옛 `/status/{sid}`)는 백엔드 경로도 이미 없음. 키워드·수집 화면은 `lib/api/keywords.ts`·`lib/api/crawl.ts`의 같은 이름 함수를 씀 |
| `frontend/src/components/SuggestedWordsPanel.tsx` | 삭제 | importer 0, 없는 백엔드 경로를 부름 |

테스트 수정(1단계):

- `tests/model/test_model_mode.py::test_legacy_train_is_readonly` — 삭제(삭제한 `/train` 전용).
- `tests/context/test_versions.py::test_create_version_copies_all_but_collection`, `tests/context/test_api.py::test_labeling_save_then_train_reads` — `from app.services.training import load_json` → `from app.services.s3 import load_json`(같은 함수를 다시 내보낸 것일 뿐).
- `tests/test_review_fix1.py::test_c3_legacy_endpoint_rejects_unfinished`, `test_legacy_direct_service_guard` — 삭제(`/preprocess`·`preprocess_data` 전용). `test_g5_changed_prep_identity_locked`, `test_g5_same_ref_reuse_allowed_after_labeling`은 `legacy` 파라미터 쪽만 지우고 `/prep/{sid}/run` 쪽은 유지.
- `tests/test_integration_stage0_2.py` — `test_legacy_session_preprocess_still_reads_old_crawl` 삭제. `test_preprocess_reads_collection_chain`, `test_quality_and_desc_limit`, `test_missing_manifest_status_hides_path`(112~120행의 `/preprocess` 왕복 포함)는 `preprocess_data` 대신 2단계에서 옮길 `app.prep.documents` 함수를 직접 부르거나 `/prep/{sid}/run`으로 바꾼다(단언은 유지).
- `tests/crawl/test_final_w5.py::test_finish_partial`, `test_preprocess_excludes_cafe_name_and_slug` — 같은 방식으로 `filter_documents`/`crawl_docs` 직접 호출로 바꾼다(카페 이름·슬러그 제외 규칙 D-084~086 검증 유지).
- `tests/prep/test_pipeline.py::test_unconnected_exports_before_embedding` — `preprocess_data` 부분 제거, `run_prep` 경로 단언 유지.

## 2단계 — v2가 v1에 기대는 부분 옮기기 + 호환 파일(D-065) 제거

### 2-1. 공용 함수 이동 (`services/preprocessing.py` → `app/prep/documents.py`)

| 함수 | 처리 | 근거 |
|---|---|---|
| `_crawl_docs` | `crawl_docs`로 이름을 바꿔 이동. `collectionId`가 없을 때 `load_data(f"crawl/{sid}/")`로 넘어가는 옛 분기는 삭제 | 호출처는 `prep/pipeline.py:195` 하나이고, `run_prep`이 바로 앞에서 `cid`를 `c[1-9][0-9]*`로 검증하므로 옛 분기에 닿을 수 없음 |
| `filter_documents` | 그대로 이동 | `prep/pipeline.py:225`가 씀(D-084~086 규칙) |
| `_compat_fields` | 이동하되 **`desc`·`cafe`·`link` 필드는 계속 붙인다**. 이름은 `_export_fields`로 바꾸고 docstring에 읽는 곳을 적는다. `doc_id` 없는 옛 문서 분기는 삭제 | 아래 "남겨야 하는 이유". `crawl_docs`가 `doc["doc_id"]`로 색인하므로 v2 문서는 항상 `doc_id`가 있음 |
| `_passes_quality` | 이동. `doc_id` 없는 옛 문서 분기 삭제 | 같은 이유 |
| `services/preprocessing.py` | 1단계 삭제분과 합쳐 파일 전체 삭제 | 남는 사용처 0 |

**`desc`·`cafe`·`link`를 남겨야 하는 이유.** 이 필드는 호환 파일에만 있는 게 아니라 `filter_documents`가 돌려주는 문서 자체에 붙어 `derived/{sid}/{cid}/{key}/docs/*.jsonl`에 저장되고, v2가 읽는다.

- `app/model/export.py:93-94` — 5단계 내보내기가 `doc['desc']`(본문+댓글, 최대 4,000자)와 `doc['cafe']`를 옮긴다. 필드를 빼면 `desc`가 `body`만으로 바뀌어 내보내기 내용이 달라진다.
- 챗봇(`routers/chat.py:62`)이 `search_docs` 결과의 `desc`를 보여 준다 — 범위 밖이므로 깨면 안 된다.

v2 문서에서 이 필드를 빼는 일은 내보내기 형식 변경이라 이번 정리에 넣지 않는다(후속 과제).

### 2-2. 호환 파일 `preprocessed/{sid}/*.jsonl` 제거

읽는 곳 전수(grep `preprocessed/`, `compatRef`, `compatWritten`):

| 읽는 곳 | 처리 |
|---|---|
| `routers/labeling.py:12` (`/sample`) | 1단계에서 삭제 |
| `services/clustering.py:42` | 옛 세션 분기 전용(`is_legacy`일 때만). 옛 v1 전처리가 예전에 써 둔 파일을 읽으며, `_publish_compat`가 만든 파일(v2 세션 것)은 이 분기에 오지 않는다. 3단계 결정에 따른다 |
| `routers/prep.py:107-111` | 재사용 조건에서 `manifest.get('compatWritten')`과 `compatRef` 파일 존재 검사를 뺀다. 남는 조건: `collectionFinalized`, `status == 'done'`, `stage_3.json` 존재 |
| `workflow.py` | Q2 |
| 프론트 | 없음 |

`prep/pipeline.py`에서 삭제: `_publish_compat`(114~125행), `_publish`와 `_run` 안의 호출(128·239행), 새 manifest의 `compatRef`(190행). 기존 manifest의 `compatRef`/`compatWritten` 키는 무시되므로 데이터 이전은 필요 없다. 디스크에 남은 `preprocessed/` 파일은 데이터라 코드 정리에서 지우지 않는다(원하면 맥미니에서 따로 정리).

`prep_key`/`analyzer_version`은 바뀌지 않으므로 기존 전처리 결과는 그대로 재사용된다(문서 내용이 같기 때문에 맞는 동작).

테스트 수정(2단계):

- `tests/prep/test_pipeline.py::test_version_snapshot_and_compat_output` — 호환 파일 단언 삭제, 버전 스냅샷 단언 유지. `test_done_cache_does_not_read_collection_again` — monkeypatch 대상 `pipeline._crawl_docs` → `pipeline.crawl_docs`.
- `tests/test_review_fix1.py`의 픽스처 manifest(`compatWritten`, `compatRef`) — 새 재사용 조건이 드러나도록 키를 지운다. `test_c3_unfinished_crawl_cannot_start_or_reuse`, `test_c3_unverified_old_result_not_reused_after_finalization` 단언 유지.
- 새 테스트: 호환 파일 없이 `stage_3.json`만 있어도 `/prep/{sid}/run`이 `reused: True`가 되는지, `run_prep`이 `preprocessed/` 아래에 아무것도 쓰지 않는지.

## 3단계 — 클러스터링·페르소나·인사이트의 v1 화면

공통(Q1과 무관, 사용자 선택 "사이드바 잠금 + 배너"): `prep.derivedRef`가 없으면 `components/StepBar.tsx`가 근거 탐색(8번째)뿐 아니라 클러스터링(7)·페르소나(9)·인사이트(10)도 같은 방식(`aria-disabled`, "다음 묶음에서 열립니다" 대신 "전처리를 먼저 완료하세요")으로 잠근다. URL로 직접 오면 `schemaVersion === 2`일 때 세 페이지 모두 `Banner tone="warning"`("3단계(전처리)를 먼저 완료하세요" + 전처리 화면 이동 버튼)을 보여 준다. 크롤링·전처리 페이지의 배너와 같은 형태. 프론트 테스트로 고정한다.

### 3-A. 옛 세션이 필요 없음 → 전부 삭제 (추천: 맥미니 옛 세션이 0개이거나 아무도 열지 않을 때)

| 대상 | 처리 |
|---|---|
| `routers/clustering.py`, `routers/embedding.py`, `routers/personas.py`, `services/clustering.py`, `services/embedding.py`, `services/personas.py` | 삭제 + `main.py` 등록 제거 |
| `context/compat.py` (`fill_bk_problem`) | 삭제(사용처가 위 라우터와 1단계 `training.py`뿐) |
| `schemas.py`의 `ClusterRequest`, `ClusterRefineRequest`, `EmbedRequest`, `PersonaRequest` | 삭제 |
| `services/voyage.py` | 유지(`vectors/embedder.py`가 씀) |
| 프론트 `LegacyClusteringPage`, `LegacyPersonasPage`(각 page.tsx 안), `app/insights/LegacyInsightsPage.tsx` | 삭제. 옛 세션이면 "구버전 세션은 이 단계를 열 수 없습니다" 배너 |
| `components/PersonaCard.tsx`, `components/SNAGraph.tsx`, `components/ProgressBar.tsx`, `components/Spinner.tsx` | 삭제(importer가 옛 화면뿐. `components/ds`의 `ProgressBar`와는 다른 파일) |
| `lib/api.ts`: `listSessions`, `startCluster`, `getClusterStatus`, `clusterRefine`, `startEmbed`, `startPersona`, `getPersonaStatus`, `getSNAData` | 삭제(`getSession`·`saveSession`·`sendChat`·`sendInsightChat` 유지). `lib/types.ts`의 옛 화면 전용 타입(`ClusterPersona` 등)도 사용처 0이면 삭제 |
| `d3` 의존성 | 유지(`components/segment/WordNetwork.tsx`가 씀) |
| `sessions.py`의 `clustersDone` | 유지(저장된 `clustering.status`만 읽음. 형식 정리는 후속 과제) |

챗봇 영향: `chat.py`는 `personas/{sid}/`, `clusters_refined/{sid}/`, `clusters/{sid}/` 파일을 직접 읽고 v1 서비스를 import하지 않는다. 이 파일을 쓰던 v1 서비스가 사라져도 챗봇 코드는 그대로 돈다(새 세션에 이 파일이 없는 건 지금도 같음 — B-120).

테스트(3-A): `tests/known/test_known.py`의 군집·페르소나·임베딩 테스트 6개, `tests/context/test_session_completion.py`의 `cluster_service` 테스트 3개, `tests/test_integration_stage0_2.py`의 `test_downstream_clustering_reads_compat_fields`·`test_fallback_*` 2개 삭제. `tests/test_integration_stage3_5.py::test_end_to_end_fixture`는 끝의 군집 부분만 잘라 내고 라벨→내보내기 단언 유지. 프론트 `app/pipeline/clustering/page.test.ts`, `components/persona/insight-route.test.ts`, `components/persona/insight.test.ts:41`의 `LegacyInsightsPage` 단언은 "배너로 분기" 단언으로 바꾼다.

### 3-B. 옛 세션을 아직 봐야 함 → 읽기 전용만 남김

- 삭제: 쓰기 경로 `POST /cluster`, `POST /cluster-refine`, `POST /embed`, `POST /persona`, `GET /embed-status/{sid}`와 `run_clustering`, `refine_clusters`, `run_persona`, `services/embedding.py`, `context/compat.py`, 해당 스키마.
- 유지: `GET /cluster-status/{sid}`, `GET /persona-status/{sid}`, `GET /sna-data/{sid}`(저장 파일만 읽음)와 세 Legacy 화면. 화면은 `schemaVersion`이 없을 때만 열리고, 시작·정제·저장 버튼과 `startCluster`/`clusterRefine`/`startEmbed`/`startPersona`/`saveSession` 호출을 걷어 내 D-060대로 열람만 한다.
- `services/clustering.py`·`personas.py`는 GET이 쓰지 않으므로 삭제. 테스트 삭제 범위는 3-A와 같고, 남은 GET 3개에 "쓰기 없음" 테스트를 붙인다.

### 3-C. 그대로 둠

1·2단계와 "공통" 배너만 한다. 옛 세션의 `LegacyPersonasPage` 쓰기 경로는 후속 과제로 남긴다.

## 4단계 — 문서

- `backend/BACKEND.md` 141~182·403·424~436행, `frontend/PIPELINE.md` 200~214·254·306·353~354·421~424·443행: 삭제한 경로를 지우고 v2 경로로 안내.
- `docs/development/dcx2-stage0-2/decision-log.md` D-065 아래 "제거(v1-cleanup)" 한 줄. Q1 결과는 D-060·D-303 아래 한 줄.
- 이 계획 옆에 `report.md`(지운 것, 테스트 결과).

## 검증 (단계마다, 모두 통과해야 다음 단계로)

```bash
cd backend && venv/bin/python -m pytest tests -q -p no:cacheprovider -n auto
npm --prefix frontend run lint
npm --prefix frontend test
npm --prefix frontend run build
```

추가 확인:

- `grep -rn "app.services.preprocessing\|_publish_compat\|compatRef\|services.training\|routers.labeling" backend/app` → 0건.
- `cd backend && venv/bin/python -c "from app.main import app; print(sorted(r.path for r in app.routes))"`로 지운 경로가 없고 `/chat`, `/insight-chat`, `/search`, `/prep/{sid}/run`이 남아 있는지 확인.
- 챗봇 회귀: `components/chat-flow.test.ts`와 백엔드 chat 관련 테스트가 그대로 통과.

기준선(`main` @ `4444a50`, 2026-10-19): 프론트 lint 통과, vitest 76파일 · 942테스트 통과, build 통과. 백엔드 pytest는 작업 워크트리의 새 venv(CI와 같은 `requirements*.txt` + `constraints.txt`)로 측정해 report.md에 적는다. 공용 `backend/venv`에는 torch·pytest-xdist가 없어 79개 모듈이 import 단계에서 실패한다(이 정리와 무관).

## 커밋 순서

1. `docs: v1 정리 계획` (이 파일)
2. `chore(v1): 호출처 없는 v1 경로·함수 삭제` (1단계)
3. `refactor(prep): 문서 읽기·필터를 app/prep로 옮기고 호환 파일 제거` (2단계)
4. `fix(pipeline): 3단계 전 새 세션이 v1 화면으로 빠지지 않게` (3단계 공통)
5. `chore(v1): 옛 세션 화면 정리` (3단계 A/B, Q1 결과에 따라)
6. `docs: v1 정리 반영` (4단계 + report.md)

PR 하나로 올리되 커밋 단위로 되돌릴 수 있게 한다.

## 후속 과제 (이번 범위 밖)

- v2 문서에서 `desc`·`cafe`·`link`를 빼고 `model/export.py`가 `body`/`src_meta`를 직접 쓰게 하기(내보내기 형식 변경).
- 세션 완료 표시 `clustersDone`을 v2(`segmentDone`) 하나로 합치기.
- 챗봇이 v2 결과를 읽게 하기(B-120).
