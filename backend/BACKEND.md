# DCX Agent 백엔드 구조

> FastAPI 기반 소비자 인사이트 파이프라인 백엔드

## 폴더 구조

```
backend/app/
├── main.py                  # FastAPI 앱 설정 (CORS, 라우터 등록)
├── config.py                # 환경변수 설정 (Pydantic Settings)
├── __init__.py
│
├── models/
│   ├── schemas.py           # Pydantic 요청/응답 스키마
│   └── __init__.py
│
├── routers/                 # API 엔드포인트 (단계별)
│   ├── sessions.py          # 세션 관리
│   ├── keywords_v2.py       # 키워드 생성
│   ├── crawling.py          # 웹 크롤링
│   ├── prep.py              # 데이터 전처리
│   ├── labeling_v2.py       # 라벨링·검수
│   ├── training_v2.py       # 모델 학습·내보내기
│   ├── segment.py           # 클러스터링
│   ├── evidence.py          # 근거 탐색
│   ├── stage8.py            # 페르소나·인사이트
│   ├── chat.py              # 챗봇 (파이프라인 + 인사이트)
│   ├── search.py            # 유사 문서 검색
│   └── __init__.py
│
├── services/                # 비즈니스 로직
│   ├── claude.py            # Claude API 통합
│   ├── crawling.py          # Naver Cafe 크롤링 로직
│   ├── naver.py             # Naver API 래퍼
│   ├── voyage.py            # Voyage AI 임베딩
│   ├── pinecone_svc.py      # Pinecone 벡터 검색
│   ├── s3.py                # AWS S3 파일 입출력
│   └── __init__.py
│
├── jobs/
│   ├── manager.py           # 스레드 안전 작업 상태 관리
│   └── __init__.py
│
└── utils/
    └── text.py              # 텍스트 정제 유틸리티
```

---

## main.py — 앱 설정

FastAPI 앱 인스턴스 생성, CORS 미들웨어 설정 (모든 origin 허용), 전체 라우터 등록.

| 함수 | 엔드포인트 | 설명 |
|------|-----------|------|
| `health()` | `GET /health` | API 헬스체크 |

---

## config.py — 환경변수

Pydantic `BaseSettings`를 상속한 `Settings` 클래스. `.env` 파일에서 로드.

| 변수 | 용도 |
|------|------|
| `s3_bucket`, `s3_region` | AWS S3 버킷/리전 |
| `naver_client_id`, `naver_client_secret` | Naver API 인증 |
| `claude_api_key` | Claude API 키 |
| `pinecone_api_key` | Pinecone API 키 |
| `voyage_api_key` | Voyage AI API 키 |

---

## models/schemas.py — 요청/응답 스키마

세션·검색·챗봇 요청에 사용되는 Pydantic `BaseModel` 정의:

| 스키마 | 용도 | 주요 필드 |
|--------|------|----------|
| `SessionSaveRequest` | 세션 저장 | `sid`, `data` |
| `SearchRequest` | 유사 문서 검색 | `sid`, `query`, `topK` |
| `ChatRequest` | 파이프라인 챗봇 | `sid`, `message`, `context` |
| `InsightChatRequest` | 인사이트 챗봇 | `sid`, `message`, `personas`, `clusters` |

---

## routers/ — API 엔드포인트

### routers/sessions.py — 세션 관리

| 함수 | 엔드포인트 | 설명 |
|------|-----------|------|
| `save_session(req)` | `POST /save-session` | 세션 데이터를 S3에 저장 |
| `get_session(sid)` | `GET /session/{sid}` | S3에서 세션 로드 |
| `list_sessions()` | `GET /sessions` | 전체 세션 목록 (최근 20개) |
| `delete_session(sid)` | `DELETE /delete-session/{sid}` | 세션 삭제 |
| `pipeline_status(sid)` | `GET /pipeline-status/{sid}` | 전체 파이프라인 작업 상태 조회 |

### routers/keywords_v2.py — 키워드 생성

키워드 생성·검토는 `/keywords/{sid}/*` 경로를 사용한다.

### routers/crawling.py — 웹 크롤링

| 함수 | 엔드포인트 | 설명 |
|------|-----------|------|
| `start_crawl(req)` | `POST /crawl` | 크롤링 작업 시작 (데몬 스레드) |
| `get_status(sid)` | `GET /status/{sid}` | 크롤링 진행 상태 + 카페 통계 |

**상태 응답 구조:**
- `status`: running / done / error / not_found
- `total`: 수집된 총 건수
- `cafe_stats`: 카페별 수집 통계
- S3 폴백: JobManager에 상태 없으면 S3 데이터로 추정

### v2 파이프라인 라우터

전처리는 `/prep/{sid}/*`, 라벨링은 `/label/{sid}/*`, 학습·내보내기는 `/train/{sid}` 및 `/train/{sid}/*`, 클러스터링은 `/segment/{sid}/*`, 근거 탐색은 `/evidence/{sid}/*`, 페르소나는 `/persona/{sid}/*`, 인사이트는 `/insight/{sid}/*`를 사용한다.

구현: `routers/prep.py`, `routers/labeling_v2.py`, `routers/training_v2.py`, `routers/segment.py`, `routers/evidence.py`, `routers/stage8.py`.

### routers/chat.py — 챗봇

| 함수 | 엔드포인트 | 설명 |
|------|-----------|------|
| `chat_agent(req)` | `POST /chat` | 파이프라인 챗봇 — RAG 검색 + 키워드 추가 지원 |
| `insight_chat(req)` | `POST /insight-chat` | 인사이트 챗봇 — 클러스터/페르소나 수정 지원 |

**chat_agent 특수 기능:**
- Pinecone RAG로 유사 문서 검색 후 컨텍스트 주입
- `ADDED_KEYWORDS:` 플래그로 키워드 자동 추가

**insight_chat 특수 기능:**
- 클러스터 병합/이름 변경 지원
- 페르소나 필드 수정 지원
- `MODIFIED_DATA` JSON 블록으로 변경사항 반환

### routers/search.py — 유사 문서 검색

| 함수 | 엔드포인트 | 설명 |
|------|-----------|------|
| `search_docs(req)` | `POST /search` | Pinecone RAG로 유사 문서 검색 |

---

## services/ — 비즈니스 로직

### services/claude.py — Claude API

| 함수 | 파라미터 | 반환 | 설명 |
|------|---------|------|------|
| `call_claude(prompt, max_tokens, model, timeout)` | `prompt: str`, `max_tokens: int = 4096`, `model: str = "claude-sonnet-4-20250514"`, `timeout: int = 120` | `str \| None` | Anthropic Claude API 호출. 실패 시 None 반환 |

### services/naver.py — Naver API

| 함수 | 파라미터 | 반환 | 설명 |
|------|---------|------|------|
| `search_naver_cafe(query, display, start)` | `query: str`, `display: int = 100`, `start: int = 1` | `dict \| None` | Naver Cafe 검색 API 호출. 인증 헤더 포함 |

### services/crawling.py — 크롤링 로직

| 함수 | 파라미터 | 반환 | 설명 |
|------|---------|------|------|
| `crawl_keywords(config)` | `config: dict` (sid, bk, keywords, target, dateFrom, dateTo, includeCafes, excludeCafes, adFilters) | `int` | Naver Cafe 게시글 대량 수집. 키워드별 최대 1,000건, 500건 단위 배치 S3 저장 |

**config 필드:**
- `sid`: 세션 ID
- `bk`: 메인 키워드 (제품명)
- `keywords`: 검색 키워드 목록
- `target`: 목표 수집 건수
- `dateFrom/dateTo`: 날짜 범위
- `includeCafes`: 포함할 카페 목록
- `excludeCafes`: 제외할 카페 목록
- `adFilters`: 광고 필터 키워드 목록

**크롤링 필터 순서:**
1. 날짜 범위 체크
2. 광고 키워드 필터
3. 제외 카페 필터
4. 포함 카페 필터 (지정 시)
5. 제품명 포함 여부
6. 링크 기준 중복 제거

### v2 단계별 처리

전처리 문서 읽기·필터링은 `prep/documents.py`, 실행은 `prep/pipeline.py`가 담당한다. 라벨링·학습·내보내기·클러스터링·근거·페르소나·인사이트 처리는 위 v2 경로를 통해 실행한다. 전처리 문서의 `desc`·`cafe`·`link`는 내보내기와 검색을 위해 유지한다.

### services/voyage.py — Voyage AI 임베딩

| 함수 | 파라미터 | 반환 | 설명 |
|------|---------|------|------|
| `get_embeddings(texts)` | `texts: list[str]` | `list[list[float]]` | Voyage multilingual-2 모델로 임베딩 생성 (128건 배치, 텍스트 2000자 절삭) |

### services/pinecone_svc.py — Pinecone 검색

| 함수 | 파라미터 | 반환 | 설명 |
|------|---------|------|------|
| `search_similar(sid, query, top_k)` | `sid: str`, `query: str`, `top_k: int = 5` | `list[dict]` | 쿼리 임베딩 → Pinecone 검색 → 메타데이터 포함 결과 반환 |

### services/s3.py — AWS S3 입출력

| 함수 | 파라미터 | 반환 | 설명 |
|------|---------|------|------|
| `load_data(prefix)` | `prefix: str` | `list[dict]` | S3 프리픽스 하위 모든 JSONL 파일 로드 후 합산 |
| `save_jsonl(key, data)` | `key: str`, `data: list[dict]` | `None` | JSONL 형식으로 S3 저장 |
| `save_json(key, data)` | `key: str`, `data: dict` | `None` | JSON 형식으로 S3 저장 |
| `load_json(key)` | `key: str` | `dict \| None` | S3에서 JSON 로드 |
| `list_objects(prefix)` | `prefix: str` | `list[dict]` | S3 프리픽스 하위 객체 목록 조회 |
| `list_prefixes(prefix)` | `prefix: str` | `list[str]` | S3 프리픽스 하위 폴더 목록 조회 |
| `delete_object(key)` | `key: str` | `None` | S3 객체 삭제 |

---

## jobs/ — 작업 상태 관리

### jobs/manager.py — JobManager

스레드 안전한 인메모리 작업 상태 추적 클래스.

| 메서드 | 파라미터 | 반환 | 설명 |
|--------|---------|------|------|
| `get(job_type, sid)` | `job_type: str`, `sid: str` | `dict` | 작업 상태 조회. 없으면 `{"status": "not_found"}` |
| `set(job_type, sid, data)` | `job_type: str`, `sid: str`, `data: dict` | `None` | 작업 상태 설정/교체 |
| `update(job_type, sid, **kwargs)` | `job_type: str`, `sid: str`, `**kwargs` | `None` | 작업 상태 부분 업데이트 |

**작업 유형 (job_type):**
- `crawl`, `preprocess`, `train`, `cluster`, `embed`, `persona`

**상태 값 (status):**
- `running`, `done`, `error`, `not_found`

**전역 싱글턴:** `job_manager = JobManager()`

---

## utils/ — 유틸리티

### utils/text.py — 텍스트 정제

| 함수 | 파라미터 | 반환 | 설명 |
|------|---------|------|------|
| `clean_text(t)` | `t: str` | `str` | HTML 태그 제거 + HTML 엔티티 디코딩 (&amp;, &lt;, &gt;) |

---

## S3 데이터 경로 정리

전처리 결과는 `derived/{sid}/{collectionId}/{prepKey}/`에 저장한다. 기존 `clusters/`, `clusters_refined/`, `personas/` 파일은 챗봇이 읽으므로 그대로 유지한다.

| 경로 패턴 | 단계 | 형식 | 설명 |
|-----------|------|------|------|
| `sessions/{sid}/session.json` | 시작~라벨링 | JSON | 세션 메타데이터, 키워드, 라벨 데이터 |
| `crawl/{sid}/*.jsonl` | 크롤링 | JSONL | 수집된 게시글 (500건 단위 배치) |
| `classified/{sid}/relevant_{ts}.jsonl` | 학습 | JSONL | 관련 문서 (relevance_score 포함) |
| `classified/{sid}/irrelevant_{ts}.jsonl` | 학습 | JSONL | 무관 문서 |
| `clusters/{sid}/cluster_{id}_{ts}.jsonl` | 클러스터링 | JSONL | 초기 클러스터 데이터 |
| `clusters_refined/{sid}/data_{ts}.jsonl` | 클러스터링 | JSONL | 정제된 클러스터 데이터 |
| `personas/{sid}/result_{ts}.json` | 페르소나 | JSON | 페르소나 결과 |

---

## 전체 API 엔드포인트 요약

| 단계 | Method | Endpoint | 비동기 | 설명 |
|------|--------|----------|--------|------|
| 시작 | POST | `/save-session` | - | 세션 저장 |
| | GET | `/session/{sid}` | - | 세션 로드 |
| | GET | `/sessions` | - | 세션 목록 |
| | DELETE | `/delete-session/{sid}` | - | 세션 삭제 |
| | GET | `/pipeline-status/{sid}` | - | 전체 파이프라인 상태 |
| 키워드 | POST | `/keywords/{sid}/rounds/{n}` | O | 키워드 생성 |
| 크롤링 | POST | `/crawl` | O | 크롤링 시작 |
| | GET | `/status/{sid}` | - | 크롤링 상태 |
| 챗봇 | POST | `/chat` | - | 파이프라인 챗봇 |
| | POST | `/insight-chat` | - | 인사이트 챗봇 |
| 검색 | POST | `/search` | - | 유사 문서 검색 |
| 공통 | GET | `/health` | - | 헬스체크 |

전처리 이후 단계의 API는 위 **v2 파이프라인 라우터** 안내를 따른다.
