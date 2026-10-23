# DCX Agent 백엔드 구조

> FastAPI 기반 소비자 인사이트 파이프라인 백엔드

## 1. 개요

`app/main.py`에서 FastAPI 앱과 CORS를 설정하고 라우터 14개를 등록한다: sessions, integrations, context, keywords_v2, crawl_v2, prep, labeling_v2, training_v2, segment, stage8, evidence, chat, search, known.

GET /health는 `{"status": "ok", "release": "…"}`를 반환한다. release는 환경변수 `DCX_RELEASE_SHA` 값이며, 없으면 `dev`다.

## 2. 패키지 구조

단계 번호는 0 시작 → 1 키워드 → 2 크롤링 → 3 전처리 → 4 라벨링 → 5 학습 → 6 클러스터링 → 7 근거 탐색 → 8 페르소나·인사이트다.

| 패키지 | 단계 | 역할 |
|---|---|---|
| `app/context/` | 0·공통 | 프로젝트 맥락 검증·Markdown 생성, 세션 버전 관리 |
| `app/crawl/` | 2 | 채널 어댑터·큐·워커, 수집 문서·URL·작성자 정규화 |
| `app/evidence/` | 7 | 근거 검색·선택과 Evidence Package 생성 |
| `app/external/` | 1~2·공통 | 외부 서비스 연동 어댑터 |
| `app/jobs/` | 공통 | 스레드 안전한 인메모리 작업 상태 관리 |
| `app/keywords/` | 1 | 키워드 분류·정규화, 라운드 생성·피드백·커버리지 |
| `app/known/` | 공통 | Known Insight 저장·로컬 검색 및 검색 제외 필터 |
| `app/label/` | 4 | 라벨 스키마·등급 규칙, 판정·검수·감사 |
| `app/lexicon/` | 6 | 로컬 KNU 감성사전 로딩·문서 감성 점수 |
| `app/llm/` | 공통 | LLM 백엔드와 태스크 실행 |
| `app/model/` | 5 | CPU 멀티태스크 앙상블 학습·보정·저장·추론 |
| `app/models/` | 공통 | 세션·검색·챗봇 요청의 Pydantic 스키마 |
| `app/persona/` | 8 | Evidence Package 기반 지표·카드·맵·인사이트·채팅 수정 |
| `app/prep/` | 3 | 규칙 필터·텍스트 정제·토큰화와 재사용 전처리 산출물 |
| `app/routers/` | 0~8·공통 | 단계별 REST API와 세션·검색·챗봇 엔드포인트 |
| `app/segment/` | 6 | 클러스터링·품질·신호 계산, 초안·확정 및 버전별 결과 |
| `app/services/` | 공통 | 저장소·Claude·네이버·Voyage 서비스 함수 |
| `app/utils/` | 공통 | HTML 태그·엔티티 등 텍스트 정제 |
| `app/vectors/` | 3·공통 | 임베딩·로컬 벡터 샤드 저장·코사인 검색 |
| `app/work/` | 공통 | 긴 작업의 별도 프로세스 워커·SQLite 작업표·heartbeat·이어 하기 |

## 3. LLM 공통 층

`app/llm/registry.py`의 `get_backend(task_name)`가 태스크에 쓸 백엔드를 선택하고, `run_task(task)`가 실행과 출력 스키마 검증을 담당한다. 파싱·스키마 오류는 최대 2회 시도한다.

| 백엔드 이름 | 역할 |
|---|---|
| `openai_api` | OpenAI API, 기본 백엔드 |
| `claude_api` | Claude API |
| `codex_exec` | Codex 실행 백엔드 |
| `fake` | 테스트용 가짜 백엔드 |

`app/config.py`의 `LLM_BACKEND` 설정을 기본으로 사용한다. `LLM_BACKEND_OVERRIDES`는 태스크 이름 패턴과 백엔드 이름의 매핑이며, `fnmatchcase`로 처음 일치한 패턴의 설정을 적용한다.

## 4. 저장소와 데이터 경로

`app/services/s3.py`는 `STORAGE=local`이면 `LOCAL_DATA_DIR` 아래 로컬 디스크를, `STORAGE=s3`이면 AWS S3를 사용한다. JSON·JSONL 저장/로드와 객체·접두사 목록, 객체 삭제 함수를 같은 인터페이스로 제공한다. `app/config.py`의 기본값은 `STORAGE=local`, `LOCAL_DATA_DIR=data`다.

아래는 3~5단계·6~8단계 설계 문서 1절의 주요 데이터 경로다. 버전별 결정·사람 확정값은 버전 안에, 재사용할 전처리 결과·판정·모델·LLM 캐시는 버전 밖에 둔다.

| 데이터 경로 | 역할 |
|---|---|
| `sessions/{sid}/versions/vN/…` | 버전별 결정·사람 라벨·설정 |
| `sessions/{sid}/versions/vN/segment/` | 6단계 결과: segment.sqlite·stage_6.json |
| `sessions/{sid}/versions/vN/evidence/` | 7단계 결과: queries.json·evidence.sqlite·package.json·stage_7.json |
| `sessions/{sid}/versions/vN/persona/` | 8단계 결과: cards.json·map.json·insights.json·concepts.json·chat.jsonl·stage_8.json |
| `derived/{sid}/{collectionId}/{prepKey}/` | 버전 간 재사용하는 3단계 전처리 결과 |
| `judge/{sid}/{prepKey}/{labeler}/{qver}/` | 버전 간 공유하는 LLM 판정 캐시 |
| `models/{modelId}/` | 세션 밖 분류 모델 저장소 |
| `work/{sid}/{runId}/` | 워커 작업표·로그 |
| `llmcache/{sid}/{prepKey}/` | dims·지연 태깅 LLM 캐시 |

## 5. API

`app.openapi()` 기준 93개 operation. 경로 파라미터 이름은 OpenAPI와 같다.

### `app/routers/sessions.py` — 세션 관리

| Method | Path | 설명 |
|---|---|---|
| POST | `/save-session` | 세션 저장 |
| GET | `/session/{sid}` | 세션 조회 |
| GET | `/sessions` | 세션 목록 조회 |
| DELETE | `/delete-session/{sid}` | 세션 삭제 |
| GET | `/pipeline-status/{sid}` | 파이프라인 작업 상태 조회 |

### `app/routers/integrations.py` — 외부 연동

| Method | Path | 설명 |
|---|---|---|
| GET | `/integrations` | 외부 서비스 연결 상태 조회 |

### `app/routers/context.py` — 프로젝트 맥락·버전

| Method | Path | 설명 |
|---|---|---|
| POST | `/context` | 프로젝트 맥락과 새 세션 생성 |
| POST | `/context/category-suggest` | 제품군 제안 |
| GET | `/context/{sid}` | 프로젝트 맥락 조회 |
| PUT | `/context/{sid}` | 프로젝트 맥락 저장 |
| PATCH | `/context/{sid}` | 프로젝트 맥락 부분 수정 |
| PATCH | `/session/{sid}` | 세션 단계·초안 부분 수정 |
| GET | `/sessions/{sid}/versions` | 버전 목록 조회 |
| POST | `/sessions/{sid}/versions` | 버전 생성 |
| PUT | `/sessions/{sid}/active-version` | 활성 버전 변경 |
| GET | `/sessions/{sid}/compare` | 단계별 버전 비교 |

### `app/routers/keywords_v2.py` — 키워드

| Method | Path | 설명 |
|---|---|---|
| POST | `/keywords/{sid}/rounds/{n}` | 키워드 라운드 생성 시작 |
| GET | `/keywords/{sid}/rounds/{n}` | 라운드 상태·키워드 조회 |
| POST | `/keywords/{sid}/rounds/{n}/commit` | 라운드 검토 결정 확정 |
| POST | `/keywords/{sid}/manual` | 수동 키워드 추가 |
| POST | `/keywords/{sid}/suggest-words` | 분류별 키워드 제안 |
| POST | `/keywords/{sid}/coverage` | 커버리지 계산 |
| GET | `/keywords/{sid}` | 키워드·라운드·피드백 조회 |
| POST | `/keywords/{sid}/events` | 키워드 검토 이벤트 기록 |

### `app/routers/crawl_v2.py` — 크롤링

| Method | Path | 설명 |
|---|---|---|
| PUT | `/crawl/{sid}/config` | 크롤링 설정 저장 |
| POST | `/crawl/{sid}/list` | 목록 수집 시작 |
| PUT | `/crawl/{sid}/gate` | 수집 제외 목록 저장 |
| POST | `/crawl/{sid}/detail` | 상세 수집 시작 |
| GET | `/crawl/{sid}/status` | 크롤링 상태 조회 |
| GET | `/crawl/{sid}/report` | 버전별 수집 리포트 조회 |
| POST | `/crawl/{sid}/resume` | 크롤링 재개 |
| POST | `/crawl/{sid}/stop` | 크롤링 중지 |
| PUT | `/crawl/{sid}/auto-chain` | 수집 후 전처리·라벨링 자동 실행 설정 |
| POST | `/crawl/{sid}/finish-partial` | 부분 수집 완료 처리 |

### `app/routers/prep.py` — 전처리

| Method | Path | 설명 |
|---|---|---|
| PUT | `/prep/{sid}/config` | 전처리 설정 저장 |
| POST | `/prep/{sid}/run` | 전처리 실행 또는 완료 산출물 재사용 |
| GET | `/prep/{sid}/status` | 전처리 상태 조회 |

### `app/routers/labeling_v2.py` — 라벨링·검수

| Method | Path | 설명 |
|---|---|---|
| POST | `/label/rule/preview` | 태그 기반 등급 미리보기 |
| POST | `/label/{sid}/mode` | 라벨링 방식 설정 |
| POST | `/label/{sid}/judge` | 라벨 판정 또는 모델 추론 시작 |
| POST | `/label/{sid}/start` | 라벨 판정 또는 모델 추론 시작 |
| POST | `/label/{sid}/judge/{labeler}/{action}` | 판정·추론 워커 일시정지·재개·중지 |
| GET | `/label/{sid}/overview` | 라벨링 현황 조회 |
| GET | `/label/{sid}/next` | 다음 검수 문서 조회 |
| POST | `/label/{sid}/seen` | 라벨링 방문 시각 기록 |
| POST | `/label/{sid}/submit` | 사람 검수 결과 제출 |
| POST | `/label/{sid}/audit` | 감사 라운드 생성 |

### `app/routers/training_v2.py` — 학습·내보내기

| Method | Path | 설명 |
|---|---|---|
| GET | `/models` | 호환 분류 모델 목록 조회 |
| GET | `/models/{model_id}` | 분류 모델 메타데이터 조회 |
| POST | `/train/{sid}` | 모델 학습 시작 |
| GET | `/train/{sid}/status` | 학습·추론·감시 상태 조회 |
| POST | `/train/{sid}/export` | 세션 결과 내보내기 |

### `app/routers/segment.py` — 클러스터링

| Method | Path | 설명 |
|---|---|---|
| POST | `/segment/{sid}/run` | 클러스터링 시작 |
| GET | `/segment/{sid}/status` | 클러스터링 상태 조회 |
| GET | `/segment/{sid}/clusters` | 클러스터 목록 조회 |
| GET | `/segment/{sid}/personas` | 페르소나 후보 목록 조회 |
| GET | `/segment/{sid}/contexts` | 맥락 후보 목록 조회 |
| PUT | `/segment/{sid}/clusters/{item_id}` | 클러스터 확정 |
| PUT | `/segment/{sid}/personas/{item_id}` | 페르소나 후보 확정 |
| PUT | `/segment/{sid}/contexts/{item_id}` | 맥락 확정 |
| POST | `/segment/{sid}/personas/{item_id}/confirm-contexts` | 페르소나별 맥락 일괄 확정 |
| POST | `/segment/{sid}/requests` | 요청 메모 저장 |
| GET | `/segment/{sid}/support-counts` | 지지 문서 수 조회 |
| GET | `/segment/{sid}/docs` | 필터별 문서 조회 |

### `app/routers/stage8.py` — 페르소나·인사이트

| Method | Path | 설명 |
|---|---|---|
| POST | `/persona/{sid}/run` | 페르소나 생성 시작 |
| GET | `/persona/{sid}/status` | 페르소나 생성 상태 조회 |
| GET | `/persona/{sid}/cards` | 페르소나 카드 목록 조회 |
| GET | `/persona/{sid}/cards/{item_id}` | 페르소나 카드 상세 조회 |
| POST | `/persona/{sid}/cards/{item_id}/retry` | 페르소나 카드 재생성 |
| GET | `/persona/{sid}/map` | 페르소나 맵 조회 |
| GET | `/persona/{sid}/tree` | 페르소나 트리 조회 |
| POST | `/insight/{sid}/run` | 인사이트·콘셉트 생성 시작 |
| GET | `/insight/{sid}` | 인사이트·콘셉트와 작업 상태 조회 |
| POST | `/insight/{sid}/concept/{item_id}` | 선택 인사이트의 콘셉트 생성 |
| POST | `/insight/{sid}/chat` | 채팅으로 결과 수정 |
| POST | `/insight/{sid}/revert` | 결과를 지정 리비전으로 복원 |
| PUT | `/insight/{sid}/confirm` | 인사이트 확정 |

### `app/routers/evidence.py` — 근거 탐색

| Method | Path | 설명 |
|---|---|---|
| POST | `/evidence/{sid}/run` | 근거 탐색 시작 |
| GET | `/evidence/{sid}/status` | 근거 탐색 상태 조회 |
| GET | `/evidence/{sid}/contexts/{context_id}` | 맥락별 선택·반대·희소 근거 조회 |
| GET | `/evidence/{sid}/personas/{persona_id}` | 페르소나별 Desire 지지 근거 조회 |
| POST | `/evidence/{sid}/contexts/{context_id}/refresh-new` | 새로운 근거 탭 갱신 |
| POST | `/evidence/{sid}/contexts/{context_id}/skip` | 맥락 건너뛰기 |
| GET | `/evidence/{sid}/package` | Evidence Package 조회 |

### `app/routers/chat.py` — 챗봇

| Method | Path | 설명 |
|---|---|---|
| POST | `/chat` | 파이프라인 챗봇 질의 |
| POST | `/insight-chat` | 인사이트 챗봇 분석·수정 질의 |

### `app/routers/search.py` — 검색

| Method | Path | 설명 |
|---|---|---|
| POST | `/search` | 로컬 벡터 유사 문서 검색 |

### `app/routers/known.py` — Known Insight

| Method | Path | 설명 |
|---|---|---|
| GET | `/known/{sid}` | Known Insight 목록 조회 |
| GET | `/known/{sid}/suggestions` | Known Insight 후보 조회 |
| POST | `/known/{sid}` | Known Insight 추가 |
| PATCH | `/known/{sid}/{item_id}` | Known Insight 수정 |
| DELETE | `/known/{sid}/{item_id}` | Known Insight 삭제 |

### `app/main.py` — 헬스체크

| Method | Path | 설명 |
|---|---|---|
| GET | `/health` | 상태·릴리스 식별자 조회 |
