# 프런트엔드 파이프라인

## 전체 구조

단계 화면은 `frontend/src/app/pipeline/<stage>/page.tsx`에 있다. 화면 목록은 `frontend/src/components/StepBar.tsx`, 상태는 `frontend/src/stores/`, REST API 클라이언트는 `frontend/src/lib/`에서 관리한다. 요청은 백엔드 `backend/app/routers/`로 전달된다.

외부 연동은 OpenAI API(기본 LLM), Claude API(선택 LLM), Codex(`codex exec`, 라벨링), Voyage AI(임베딩), 네이버 오픈 API, 네이버 검색광고 API, YouTube Data API, Jev(라벨 판정)다. 설정과 호출 구현은 `backend/app/config.py`, `backend/app/llm/`, `backend/app/external/`, `backend/app/label/`, `backend/app/vectors/`에서 확인할 수 있다.

기본 저장소는 로컬 디스크(`STORAGE=local`)이고 데이터 루트는 `LOCAL_DATA_DIR`(기본값 data)다. `backend/app/services/s3.py`의 저장소 추상화는 `STORAGE=s3` 선택도 지원한다. 아래 저장 위치는 데이터 루트 기준의 **런타임 경로**이며, 세션·전처리·워커의 로컬 파일 구조를 함께 표시한다.

## 0단계 시작 — /pipeline/start

제품·리서치 질문·분석 목적 등 프로젝트 맥락을 입력하고 세션을 만든다.
입력으로 프로젝트 맥락 문서를 생성하며, 뒤 단계의 생성·판정에 같은 맥락을 전달한다.

- 백엔드: `backend/app/routers/context.py` → `backend/app/context/`
- API: `/context`, `/context/{sid}` 및 제품군 제안 `/context/category-suggest`
- 저장: `sessions/{sid}/meta.json`, `sessions/{sid}/versions/vN/session.json`, 같은 버전의 `project_context.md`

## 1단계 키워드 — /pipeline/keywords

프로젝트 맥락에 맞는 키워드를 라운드별로 생성하고 사람이 승인·이동·거절한다.
검색량과 커버리지를 확인하고, 피드백을 다음 생성에 반영해 수집할 키워드를 정한다.

- 백엔드: `backend/app/routers/keywords_v2.py` → `backend/app/keywords/`, 외부 연동 `backend/app/external/`
- API 접두사: `/keywords/{sid}`
- 저장: `sessions/{sid}/versions/vN/session.json`, 같은 버전의 `keyword_events.jsonl`, `keyword_feedback.md`

## 2단계 크롤링 — /pipeline/crawling

키워드·채널별 목록 수집 후 게이트를 설정하고 상세 원문을 수집·정규화한다.
수집 상태와 리포트를 확인하며, 수집본은 세션 버전과 분리해 재사용한다.

- 백엔드: `backend/app/routers/crawl_v2.py` → `backend/app/crawl/`
- API 접두사: `/crawl/{sid}` (설정·목록·게이트·상세·상태·리포트)
- 저장: `crawl/{sid}/collections/{collectionId}/` 아래 `manifest.json`, `queue.sqlite`, `docs/part-*.jsonl`, `report.json`; 버전에는 `collectionId` 참조
- 채널 어댑터: `backend/app/crawl/adapters/`의 naver_cafe, naver_blog, naver_kin, youtube, youtube_vlog, threads, cook82(82쿡), clien, ppomppu

## 3단계 전처리 — /pipeline/preprocess

규칙 필터와 정형 문구 제거를 적용하고, 문서를 임베딩용 텍스트와 토큰 경로로 정제한다.
Voyage 벡터를 로컬 샤드로 저장해 이후 학습·군집·검색에서 재사용한다.

- 백엔드: `backend/app/routers/prep.py` → `backend/app/prep/`, `backend/app/vectors/`
- API 접두사: `/prep/{sid}`
- 저장: `derived/{sid}/{collectionId}/{prepKey}/` 아래 `manifest.json`, `docs/`, `tokens/`, `vectors/`, `stage_3.json`; 버전의 `prep.derivedRef`가 참조

## 4단계 라벨링 — /pipeline/labeling

LLM 판정과 사람 검수로 문서의 태그·근거 등급을 결정한다.
캘리브레이션과 감사 결과를 관리하며, GPT 라벨러의 기본 백엔드는 Codex 실행이다.

- 백엔드: `backend/app/routers/labeling_v2.py` → `backend/app/label/`, 호출 공통 층 `backend/app/llm/`
- API 접두사: `/label/{sid}`; 규칙 미리보기 `/label/rule/preview`
- 저장: `sessions/{sid}/versions/vN/labels.sqlite`와 `session.json`; 판정 캐시는 버전 밖 `judge/{sid}/{prepKey}/{labeler}/{qver}/votes.sqlite` (`qver` 디렉터리에는 맥락 해시도 포함)

## 5단계 학습 — /pipeline/training

라벨과 벡터로 다중 헤드 분류 모델을 학습하고 모델 지표·추론 결과를 확인한다.
전체 분류 결과와 Core·Supporting 문서를 내보내 다음 단계 입력으로 확정한다.

- 백엔드: `backend/app/routers/training_v2.py` → `backend/app/model/`
- API: `/train/{sid}`, 하위 `/status`·`/export`; 모델 목록·메타데이터 `/models`
- 저장: `models/{modelId}/` 아래 `members/`, `meta.json`, `calib.json`; 내보내기는 `classified/{sid}/vN/gen-{id}/`의 `all.jsonl`, `relevant.jsonl`, `stage_5.json`. 버전의 `training.exportRef`·`stage5Ref`가 해당 세대를 참조하며 버전 폴더에도 `stage_5.json`을 기록

## 6단계 클러스터링 — /pipeline/clustering

전처리 벡터·토큰과 분류 문서를 Cluster → Persona → Context의 세 층으로 나눈다.
품질·신호를 검토하고 층별 이름·Desire·Goal·행동을 사람이 확정한다.

- 백엔드: `backend/app/routers/segment.py` → `backend/app/segment/`, 감성 사전 `backend/app/lexicon/`
- API 접두사: `/segment/{sid}`
- 저장: `sessions/{sid}/versions/vN/segment/`의 `segment.sqlite`, `stage_6.json`; 버전 밖 LLM 캐시 `llmcache/{sid}/{prepKey}/dims-{pver}.sqlite`

## 7단계 근거 탐색 — /pipeline/evidence

확정된 Context별로 질의를 만들고 허용 문서 안에서 검색·태깅·근거 선택을 수행한다.
전체 근거와 새 발견을 구분하고, 다음 단계가 읽을 Evidence Package를 구성한다.

- 백엔드: `backend/app/routers/evidence.py` → `backend/app/evidence/`, 검색 `backend/app/vectors/`
- API 접두사: `/evidence/{sid}`
- 저장: `sessions/{sid}/versions/vN/evidence/`의 `evidence.sqlite`, `queries.json`, `package.json`, `stage_7.json`; 버전 밖 태깅 캐시 `llmcache/{sid}/{prepKey}/tag-{pver}.sqlite`

## 8단계 페르소나 — /pipeline/personas · 인사이트 — /pipeline/insights

Evidence Package에서 근거를 인용하는 페르소나 카드·맵·트리를 생성한다.
인사이트와 컨셉을 도출하고 채팅 수정·판 되돌리기·확정을 통해 결과를 다듬는다.

- 백엔드: `backend/app/routers/stage8.py` → `backend/app/persona/`
- API 접두사: `/persona/{sid}`, `/insight/{sid}`
- 저장: `sessions/{sid}/versions/vN/persona/`의 `cards.json`, `map.json`, `tree.json`, `insights.json`, `concepts.json`, `chat.jsonl`, `stage_8.json`; 인사이트·컨셉은 revision과 history로 판을 보관

## 데이터 흐름

```text
0 프로젝트 맥락 → 1 키워드 확정 → 2 수집본(collectionId)
                                     ↓
3 정제 문서·토큰·벡터(derivedRef) → 4 판정 캐시·사람 라벨
                                     ↓
5 학습·분류·내보내기(exportRef: Core + Supporting)
  → 6 Cluster / Persona / Context 확정
  → 7 Evidence Package → 8 페르소나 카드·맵 → 인사이트·컨셉

세션 버전: 입력·설정·확정값·결과 참조
버전 밖 재사용: 수집본 / 전처리 결과 / 판정·LLM 캐시 / 모델
```

## 공통 기능

- **세션 버전·비교:** `backend/app/context/`가 버전 복사·활성 버전·stale 상태를 관리한다. `/sessions/{sid}/versions`, `/sessions/{sid}/active-version`, `/sessions/{sid}/compare`를 사용하며, 비교 화면은 `/pipeline/compare`다. 수집본·전처리 결과·판정 캐시는 참조로 재사용한다.
- **Known Insight 서랍:** `backend/app/routers/known.py`와 `backend/app/known/`의 `/known/{sid}`에서 이미 아는 문장·원문을 관리하고 새 발견의 제외 기준으로 사용한다. 문장과 참조는 버전의 `session.json`, 문장 벡터는 `known_vectors.f16`에 저장한다. 같은 제품의 확정 인사이트는 `/known/{sid}/suggestions`에서 추천하며 사용자가 추가한다.
- **챗봇:** `backend/app/routers/chat.py`가 `/chat`, `/insight-chat`을 제공한다. 새 인사이트 화면의 수정·기록은 `backend/app/routers/stage8.py`의 `/insight/{sid}/chat`과 연결된다.
- **검색:** `backend/app/routers/search.py`가 `/search`를 제공한다. 로컬 벡터 저장·검색 구현은 `backend/app/vectors/`에 있다.
- **긴 작업:** `backend/app/work/`가 별도 프로세스 실행·SQLite 작업표·heartbeat·이어 하기를 담당한다. 작업표는 `work/{sid}/runs.sqlite`에 저장한다. 크롤링 큐·워커는 `backend/app/crawl/`에서 관리한다.

전체 설치·실행 안내는 [루트 README](../README.md), 프런트 개발 명령은 [프런트 README](README.md)를 참고한다.
