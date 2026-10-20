# DCX Agent 파이프라인 단계별 구성

> 소비자 인사이트 분석 파이프라인 — Naver Cafe 데이터 기반 페르소나 도출 시스템

## 전체 아키텍처

- **Backend**: FastAPI (Python) — `backend/app/`
- **Frontend**: Next.js 16 + React 19 + Zustand + Tailwind CSS — `frontend/src/`
- **외부 서비스**: AWS S3, Naver Cafe API, Claude API, Voyage AI, Pinecone
- **데이터 흐름**: 각 단계 결과가 S3에 JSONL/JSON으로 저장되어 다음 단계 입력으로 사용

```
시작 → 키워드 → 크롤링 → 전처리 → 라벨링 → 학습 → 클러스터링 → 페르소나
```

---

## 1단계: 시작 (Start)

### 목적

세션을 생성하고, 분석 대상 제품 및 문제 정의를 입력받는 초기 설정 단계.

### 입력 항목

| 항목 | 필드명 | 설명 |
|------|--------|------|
| 메인 키워드 | `bk` | 분석 대상 제품명 |
| 문제 정의 | `problemDef` | 분석하려는 문제/질문 |
| 타겟 유형 | `ages` | 주부, 직장인, 1인가구 등 |
| 나이대 | `ageRange` | 20대, 30대, 40대, 50대+ |
| 성별 | `gens` | 남성, 여성 |

### 주요 흐름

1. 사용자가 제품명 및 문제 정의 입력
2. 세션 ID 자동 생성: `s{timestamp}` 형식
3. S3에 `sessions/{sid}/session.json`으로 저장
4. 기존 세션 목록 조회 및 불러오기 가능 (`SessionList` 컴포넌트)

### 관련 파일

- **프론트엔드**: `frontend/src/app/pipeline/start/page.tsx`
- **백엔드**: `backend/app/routers/sessions.py`
- **컴포넌트**: `frontend/src/components/SessionList.tsx`

### API 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/save-session` | 세션 저장 |
| GET | `/session/{sid}` | 세션 불러오기 |
| GET | `/sessions` | 전체 세션 목록 |
| DELETE | `/delete-session/{sid}` | 세션 삭제 |

### 데이터 저장 경로

- S3: `sessions/{sid}/session.json`

---

## 2단계: 키워드 (Keywords)

### 목적

Claude AI를 활용하여 소비자 인사이트 발굴을 위한 검색 키워드를 반복적으로 생성·확장·수렴.

### 4라운드 워크플로우

| 라운드 | 유형 | 동작 |
|--------|------|------|
| R1 | 발산 | 제품 + 문제정의 기반 70개 이상 키워드 생성 |
| R2 | 발산 | 기존 키워드 제외 100개 이상 추가 생성 |
| R3 | 수렴 | 총 160개 미만이면 100개 이상 추가 |
| R3-Expand | 재발산 | 필요 시 추가 확장 |
| Final | 검토 | 카테고리별 수동 승인/거절 |

### 키워드 스코어링

각 키워드를 Naver Cafe API로 검색량 조회 후 점수 부여:

| 검색 결과 수 | 점수 |
|-------------|------|
| 10,000건 이상 | 95점 |
| 5,000~10,000건 | 85점 |
| 1,000~5,000건 | 75점 |
| 그 이하 | 점수 감소 |

### 키워드 카테고리

`상황맥락`, `감정표현`, `문제상황`, `숨은니즈`, `타겟특화`, `시즌시간`, `공간장소`

### 관련 파일

- **프론트엔드**: `frontend/src/app/pipeline/keywords/page.tsx`
- **백엔드 라우터**: `backend/app/routers/keywords_v2.py`
- **서비스 (Claude)**: `backend/app/services/claude.py`
- **서비스 (Naver)**: `backend/app/services/naver.py`
- **컴포넌트**: `frontend/src/components/KeywordTag.tsx`

### API 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/keywords/{sid}/rounds/{n}` | 키워드 생성 (라운드별) |

### 데이터 저장 경로

- S3: `sessions/{sid}/session.json` 내 `allKw` 배열에 누적

---

## 3단계: 크롤링 (Crawling)

### 목적

승인된 키워드를 사용하여 Naver Cafe에서 소비자 게시글을 대량 수집.

### 설정 항목

| 항목 | 기본값 | 설명 |
|------|--------|------|
| 목표 수집 건수 | 50,000 | 최대 수집할 문서 수 |
| 날짜 범위 | - | from/to 날짜 지정 |
| 포함 카페 | 전체 | 특정 카페만 포함 (미입력 시 전체) |
| 제외 카페 | - | 중고거래 등 제외할 카페 |
| 광고 필터 | - | 광고 게시글 필터 키워드 |

### 크롤링 로직

1. 각 키워드에 대해 `{bk} {keyword}`로 Naver Cafe API 호출
2. 페이지당 100건, 키워드당 최대 1,000건 조회
3. 필터링: 날짜 범위, 광고 키워드, 제외 카페, 제품명 포함 여부
4. 링크 기준 중복 제거
5. 500건마다 배치 저장, 목표 도달 시 중단

### 수집 데이터 구조

```json
{
  "kw": "검색 키워드",
  "title": "게시글 제목",
  "desc": "게시글 설명",
  "link": "카페 게시글 URL",
  "cafe": "카페명",
  "date": "YYYYMMDD"
}
```

### 관련 파일

- **프론트엔드**: `frontend/src/app/pipeline/crawling/page.tsx`
- **백엔드 라우터**: `backend/app/routers/crawling.py`
- **서비스**: `backend/app/services/crawling.py`, `backend/app/services/naver.py`
- **작업 관리**: `backend/app/jobs/manager.py`

### API 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/crawl` | 크롤링 시작 (비동기) |
| GET | `/status/{sid}` | 진행 상태 조회 |

### 비동기 처리

- 데몬 스레드로 백그라운드 실행
- `JobManager`로 스레드 안전한 상태 추적
- 프론트엔드에서 3초 간격 폴링

### 데이터 저장 경로

- S3: `crawl/{sid}/*.jsonl` (500건 단위 배치)

---

## 전처리 이후 단계 — v2 API

v1 전처리·라벨링·학습·클러스터링·임베딩·페르소나 API는 제거되었다. 현재 단계별 요청은 아래 v2 경로를 사용한다.

| 단계 | API 경로 | 백엔드 라우터 | 프론트엔드 페이지 |
|------|----------|---------------|------------------|
| 전처리 | `/prep/{sid}/*` (`POST /prep/{sid}/run`으로 실행) | `backend/app/routers/prep.py` | `frontend/src/app/pipeline/preprocess/page.tsx` |
| 라벨링·검수 | `/label/{sid}/*` | `backend/app/routers/labeling_v2.py` | `frontend/src/app/pipeline/labeling/page.tsx` |
| 학습·내보내기 | `/train/{sid}`, `/train/{sid}/*` | `backend/app/routers/training_v2.py` | `frontend/src/app/pipeline/training/page.tsx` |
| 클러스터링 | `/segment/{sid}/*` | `backend/app/routers/segment.py` | `frontend/src/app/pipeline/clustering/page.tsx` |
| 근거 탐색 | `/evidence/{sid}/*` | `backend/app/routers/evidence.py` | `frontend/src/app/pipeline/evidence/page.tsx` |
| 페르소나 | `/persona/{sid}/*` | `backend/app/routers/stage8.py` | `frontend/src/app/pipeline/personas/page.tsx` |
| 인사이트 | `/insight/{sid}/*` | `backend/app/routers/stage8.py` | `frontend/src/app/pipeline/insights/page.tsx` |

전처리는 `backend/app/prep/documents.py`에서 collection 체인의 문서를 읽고 필터링하며, `backend/app/prep/pipeline.py`에서 실행한다. 결과는 `derived/{sid}/{collectionId}/{prepKey}/`에 저장하고, `desc`·`cafe`·`link`는 내보내기와 검색을 위해 유지한다. 별도의 v1 전처리 호환 파일은 생성하지 않는다.

라벨링→학습→내보내기 결과는 세션의 `training.exportRef`로 찾는다. 기존 `clusters/`, `clusters_refined/`, `personas/` 데이터는 챗봇이 읽으므로 유지한다. `/chat`, `/insight-chat`, `/search`와 세션 API는 그대로 사용한다.

---

## 전체 데이터 파이프라인 요약

```
[시작] 세션 생성
   ↓ sessions/{sid}/session.json
[키워드] Claude AI 키워드 생성 (4라운드)
   ↓ sessions/{sid}/session.json → allKw
[크롤링] Naver Cafe 대량 수집
   ↓ crawl/{sid}/*.jsonl
[전처리] 문서 필터링·벡터 준비 — /prep/{sid}/*
   ↓ derived/{sid}/{collectionId}/{prepKey}/
[라벨링] 판정·사람 검수 — /label/{sid}/*
[학습·내보내기] /train/{sid}, /train/{sid}/*
   ↓ training.exportRef
[클러스터링] /segment/{sid}/*
[근거 탐색] /evidence/{sid}/*
[페르소나] /persona/{sid}/*
[인사이트] /insight/{sid}/*
```

---

## 공통 인프라

| 구성요소 | 기술 | 역할 |
|----------|------|------|
| 비동기 작업 관리 | `JobManager` (데몬 스레드) | 크롤링/학습/클러스터링/임베딩/페르소나 비동기 실행 |
| 상태 폴링 | `usePolling` 커스텀 훅 | 3~5초 간격 작업 상태 확인 |
| 상태 관리 | Zustand | 세션·키워드·단계 전역 상태 |
| UI 레이아웃 | 3컬럼 구조 | StepBar(진행바) + Content(메인) + ChatPanel(챗봇) |
| 챗봇 | `POST /chat`, `/insight-chat` | 파이프라인 컨텍스트 기반 대화 + RAG 검색 |
