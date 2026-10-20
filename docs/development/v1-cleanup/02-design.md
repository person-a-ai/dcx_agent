# v1-cleanup · 02 설계

- 작성: 2026-10-20 · 상태: 설계 승인 대기(제품 승인 2026-10-20 기록됨)
- 입력: [01-brainstorm.md](01-brainstorm.md), 근거 조사 [plan.md](plan.md)
- 목업: [mockup/index.html](mockup/index.html) — 상태 3개(새 세션·전처리 전 / 옛 세션 / 새 세션·전처리 완료) × 화면 3개 × 폭 3개(데스크톱 / ≤1100px / 375px)를 버튼으로 바꿔 볼 수 있다.

## 목업 도구 기록

`/claude-design`(설치 확인됨)은 사용하지 않았다. 이유: ① 사용자의 로그인된 Chrome으로 claude.ai/design을 구동하는데 사용자가 원격 접속 중이고, ② 코드베이스 컨텍스트를 외부 서비스로 보내며, ③ 이번 UI 변경은 이미 있는 `Banner`(ds)와 사이드바 규칙 한 줄이라 새 시각 디자인이 없다. 대신 실제 `frontend/src/styles/tokens.css`와 `components/ds/ds.css`(@`4444a50`)를 그대로 인라인한 로컬 HTML 목업을 Claude가 작성했다. 승인 후 바꾸기 원하면 `/claude-design`으로 다시 만든다.

## 1. 화면

### 1-1. 사이드바 잠금 (`components/StepBar.tsx`)

| 조건 | 지금 | 바뀐 뒤 |
|---|---|---|
| `prep.derivedRef` 없음 | 근거 탐색(인덱스 7)만 잠김, 툴팁 "다음 묶음에서 열립니다" | 클러스터링(6)·근거 탐색(7)·페르소나(8)·인사이트(9) 잠김, 툴팁 "전처리(3단계)를 먼저 완료하세요" |
| `prep.derivedRef` 있음 | 모두 열림 | 변경 없음 |

- 잠긴 항목은 지금 근거 탐색과 같은 마크업(`<a role="link" aria-disabled="true" title=…>`, `href` 없음, 키보드 포커스 없음)이다.
- 새 CSS 한 규칙(`app/globals.css`): `.pipeline-nav a[aria-disabled="true"] { color:var(--sub); cursor:not-allowed; }`, 번호 원은 `opacity:.6`. 지금은 잠긴 항목에 시각 구분이 없다.
- 잠금 여부는 지금처럼 `derivedRef` 하나로 정한다. 옛 세션도 `derivedRef`가 없으므로 같은 4개가 잠긴다(옛 세션은 운영에 0개).
- 완료 표시(체크)와 "진행 중" 표시 규칙은 바꾸지 않는다.

### 1-2. 세 페이지 분기 (`app/pipeline/{clustering,personas,insights}/page.tsx`)

| 세션 | `prep.derivedRef` | 지금 | 바뀐 뒤 |
|---|---|---|---|
| 새(v2) | 있음 | `SegmentScreen` / `PersonaScreen` / `InsightScreen` | **변경 없음** |
| 새(v2) | 없음 | Legacy 화면(v1 API 호출) | 배너 A |
| 옛(`schemaVersion` 없음) | 없음 | Legacy 화면 | 배너 B |
| 선택 안 됨(`sid` 없음) | — | Legacy 화면(빈 상태) | 지금 크롤링·전처리 페이지와 같은 "프로젝트를 먼저 선택하세요" 배너 |

- 배너 A: `Banner tone="warning"` — "3단계(전처리)를 먼저 완료하세요. 전처리가 끝나야 {단계 이름} 화면을 열 수 있습니다." + 주 버튼 "전처리 화면으로"(`/pipeline/preprocess`).
- 배너 B: `Banner tone="warning"` — "구버전 세션은 이 단계를 열 수 없습니다. 새 프로젝트를 만들어 진행하세요." + 버튼 "프로젝트 선택하기"(`/pipeline/start`).
- 배너만 그리고 **어떤 API도 부르지 않는다**(지금 Legacy 화면은 `getClusterStatus`·`getPersonaStatus`·`listSessions`·`getSNAData`를 부른다).
- 상태: 정상(위 표) / 로딩 — 세션 로딩은 지금처럼 `pipeline/layout.tsx`가 처리하므로 페이지 자체 로딩 상태 없음 / 빈 화면 — 세션 미선택 배너 / 오류 — 해당 없음(API 호출 없음) / 권한 부족 — 로그인·권한 모델 없음(현행 유지).
- 모바일: ≤1100px에서 사이드바가 번호만 보이는 72px로 접히는 현행 규칙 그대로. 375px에서 배너 버튼이 다음 줄로 내려간다(`ds-note`의 기존 줄바꿈). 목업의 "모바일 375px"로 확인.
- 배너 문구에 단계 이름은 `STEP_NAMES`에서 가져온다(하드코딩 금지).

공통 분기는 작은 순수 함수로 둔다(테스트 쉬움):

```ts
// frontend/src/lib/logic/laterStageGate.ts
export type LaterStageGate = 'no-session' | 'legacy' | 'needs-prep' | 'open';
export function laterStageGate(sid: string | null, session: Record<string, unknown> | null | undefined): LaterStageGate;
```

세 페이지와 `StepBar`가 같은 함수를 쓴다(`StepBar`는 `!== 'open'`이면 6~9 잠금).

### 1-3. 삭제되는 화면·컴포넌트

`LegacyClusteringPage`, `LegacyPersonasPage`, `app/insights/LegacyInsightsPage.tsx`, `components/PersonaCard.tsx`, `components/SNAGraph.tsx`, `components/ProgressBar.tsx`, `components/Spinner.tsx`, `components/SuggestedWordsPanel.tsx`. `/insights` → `/pipeline/insights` 리다이렉트(`app/insights/page.tsx`)와 `app/insights/layout.tsx`(챗봇)는 유지.

## 2. 백엔드 구조

### 2-1. 삭제

| 모듈 | 경로 |
|---|---|
| `routers/keywords.py` | (빈 라우터) |
| `routers/labeling.py` | `GET /sample/{sid}` |
| `routers/training.py`, `services/training.py` | `POST /train`, `GET /train-status/{sid}` |
| `routers/preprocessing.py`, `services/preprocessing.py` | `POST /preprocess`, `GET /preprocess-status/{sid}` |
| `routers/clustering.py`, `services/clustering.py` | `POST /cluster`, `GET /cluster-status/{sid}`, `POST /cluster-refine` |
| `routers/embedding.py`, `services/embedding.py` | `POST /embed`, `GET /embed-status/{sid}` |
| `routers/personas.py`, `services/personas.py` | `POST /persona`, `GET /persona-status/{sid}`, `GET /sna-data/{sid}` |
| `context/compat.py` | (`fill_bk_problem`) |
| `models/schemas.py` 일부 | `CrawlRequest`, `PreprocessRequest`, `TrainRequest`, `ClusterRequest`, `ClusterRefineRequest`, `EmbedRequest`, `PersonaRequest`, `KeywordGenRequest`, `ScoreKeywordsRequest`, `SuggestWordsRequest` |
| `utils/text.py` 일부 | `get_llm_predictions` |
| 루트 `workflow.py` | (Flask 원형) |
| `requirements.txt` | `crawl4ai` (+ crawl4ai만 끌어오던 `constraints.txt` 고정) |

v2 `/persona/{sid}/...`(stage8)와 `/train/{sid}/...`(training_v2)는 경로가 달라 영향 없음(D-303 리뷰에서 충돌 없음 확인됨).

### 2-2. 이동: `app/prep/documents.py` (새 파일)

```python
def crawl_docs(sid: str, session: dict) -> list[dict]:
    """활성 collection 체인을 자식부터 읽어 doc_id 기준으로 합친다. cid 검증·순환 검사 유지."""

def filter_documents(documents, ad_filter=(), excluded=(), min_body_chars=10, *, full_text=False
                     ) -> tuple[list[dict], dict[str, int]]:
    """D-084~086 규칙. 돌려주는 문서에 desc·cafe·link를 붙인다(_export_fields)."""
```

- 동작 변경 없음. 지우는 분기: `collectionId` 없을 때 `crawl/{sid}/` 직접 읽기, `doc_id` 없는 옛 문서 처리(두 곳). `crawl_docs`의 `session` 인자는 필수로 바꾼다(유일한 호출처가 항상 넘김).
- `desc`·`cafe`·`link`는 계속 붙인다. 읽는 곳: `app/model/export.py:93-94`, 챗봇(`routers/chat.py:62`, `search_docs` 결과).
- `prep/pipeline.py`는 `from app.prep.documents import crawl_docs, filter_documents`.

### 2-3. 호환 파일 제거

- `prep/pipeline.py`: `_publish_compat` 삭제, 새 manifest에 `compatRef` 안 씀.
- `routers/prep.py` 재사용 조건: `collectionFinalized is True and status == 'done' and stage_3.json 존재`. 옛 manifest의 `compatRef`/`compatWritten`은 읽지 않는다(데이터 이전 없음).
- `prep_key`·`analyzer_version` 불변 → 기존 전처리 결과 재사용(문서 내용 동일).

## 3. 데이터

- 저장 형식 변경 없음. 새로 쓰지 않게 되는 것: `preprocessed/{sid}/*.jsonl`, manifest의 `compatRef`/`compatWritten`.
- 맥미니의 기존 `preprocessed/`, `clusters/`, `clusters_refined/`, `personas/` 파일은 그대로 둔다(챗봇이 뒤의 셋을 읽음).
- 세션 필드 `clustering`(완료 표시 `clustersDone`의 근거)은 새로 쓰는 곳이 없어지지만 읽기는 유지(후속 과제).

## 4. API 변화 요약

- 제거: 2-1 표의 13개 경로.
- 유지(변경 없음): `/sessions`, `/session/{sid}`, `/save-session`, `/chat`, `/insight-chat`, `/search`, `/integrations`, `/prep/*`, `/label/*`, `/train/{sid}/*`, `/segment/*`, `/evidence/*`, `/persona/{sid}/*`, `/insight/*`, `/known/*`, 키워드·수집 v2 경로, `/health`.
- 동작 변화: `/prep/{sid}/run` 재사용 조건(2-3)만.

## 5. 권한

로그인·권한 모델이 없고 바꾸지 않는다. 쓰기 경로를 줄이는 변경이라 권한 노출이 늘지 않는다.

## 6. 테스트 방침

- 프론트: `laterStageGate` 4경우 단위 테스트, `StepBar` 잠금 6~9 / 열림 테스트, 세 페이지가 배너 분기에서 `@/lib/api`를 부르지 않는다는 테스트, 기존 `clustering/page.test.ts`·`insight-route.test.ts`·`insight.test.ts:41`의 Legacy 단언을 배너 단언으로 교체.
- 백엔드: plan.md 1·2·3-A 절의 테스트 목록대로 삭제·이동, `filter_documents` 이동 전후 동일 결과 테스트, 재사용 조건 새 테스트, 앱 라우트 목록 테스트(지운 13개 없음 + 챗봇·v2 경로 있음).
- 브라우저 QA: 로컬 앱에서 세 상태(목업과 동일) × 세 페이지 + 사이드바 잠금 + 챗봇 열기 회귀.
