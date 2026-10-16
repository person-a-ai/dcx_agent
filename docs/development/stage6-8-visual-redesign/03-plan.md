# 페르소나 화면 재구성 · 구현 계획 + QA 계획

> **For agentic workers:** 구현은 하네스 규칙에 따라 Task마다 `codex:codex-rescue`(`--wait --fresh`, 쓰기 가능 작업)로 위임한다. 각 Task는 RED → GREEN → 리팩터링 순서로 진행하고, Task별 보고서를 `docs/development/stage6-8-visual-redesign/tasks/T<n>.md`에 남긴다. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 근거 탐색에서 버려지던 페인포인트를 페르소나 카드까지 연결하고(없으면 카드 생성 LLM이 근거로 채움), 페르소나 화면을 시안의 Action Map 구조로 재구성해 깨짐을 없앤다.

**Architecture:** 백엔드는 근거 묶음(`evidence-package/1`)에 선택 필드 `pain_point`를 더하고, 카드 생성 스키마에 Context별 `pain_points`와 코드 집계 페르소나 `pain_points`를 더한다. 프론트는 지도 척도·구역 계산을 순수 함수(`personaView.ts`)로 분리하고, 페르소나 화면을 목록·요약·비교 표·지도·보조 패널 컴포넌트로 나눈다.

**Tech Stack:** FastAPI + Pydantic v2 + pytest (backend, Python 3.12), Next.js 16 + React 19 + vitest (frontend, `renderToStaticMarkup` 기반 테스트).

**Spec:** `docs/development/stage6-8-visual-redesign/01-brainstorm.md`, `docs/development/stage6-8-visual-redesign/02-design.md`

## Global Constraints

- 근거 태깅 LLM은 다시 호출하지 않는다. 저장된 태깅 결과(`pain_point {text, quote}`)만 쓴다.
- 새 API 엔드포인트를 만들지 않는다. `GET /persona/{sid}/cards` 응답에 필드만 추가한다.
- 기존 `package.json`(pain_point 없음)과 기존 카드(pain_points 없음)를 읽을 수 있어야 한다.
- 중요도·만족도·ODI·구역 산식은 바꾸지 않는다. 화면 표시 척도만 바꾼다.
- 지도 눈금은 0~10으로 바꾸지 않는다. 원래 값(0~1)을 로그 척도 위치에 표시한다. `k = 50`.
- 색은 `frontend/src/styles/tokens.css`의 기존 토큰만 쓴다. 새 hex 값 금지.
- 세라젬_261012_sk v2 운영 데이터 재생성은 하지 않는다.
- 사용자에게 보이는 문구는 02-design.md 4.1 상태 표의 문장을 그대로 쓴다.

## Review Focus

1. **근거 번호가 다른 Context를 가리키는 페인포인트** → 스키마 검증 실패로 재시도, 2회 실패 시 카드 실패 (T2 테스트 `test_pain_cite_must_belong_to_context`).
2. **태깅 `pain_point`가 `{"text": "", "quote": null}`처럼 비어 있는 근거** → 묶음에서 None으로 정규화 (T1 테스트 `test_pain_point_blank_becomes_none`).
3. **이전에 만든 카드(필드 없음)를 새 화면에서 열기** → 화면이 깨지지 않고 안내 문구 표시 (T5 테스트 `legacy card shows regenerate hint`).
4. **i 또는 s가 null인 지도 점, 같은 좌표에 겹친 점** → null 점은 지도에서 빠지고 안내 문구, 겹친 점은 결정적 위치로 흩어짐 (T4 테스트).
5. **47자 넘는 페르소나 이름과 긴 Context 문장** → 목록은 2줄 말줄임, 표 칸은 3줄 말줄임 (T5·T6 테스트).

---

## 파일 구조

| 파일 | 책임 | Task |
|---|---|---|
| `backend/app/evidence/package.py` | `PainPoint` 모델, `EvidenceItem.pain_point` | T1 |
| `backend/app/evidence/assemble.py` | `_item()`이 태깅 `pain_point` 정규화해 싣기 | T1 |
| `backend/app/persona/package.py` | 페르소나 쪽 `Evidence` 계약에 `pain_point` | T1 |
| `backend/app/persona/cards.py` | 페인포인트 스키마·검증·등급·집계, dims 덮어쓰기 제거 | T2 |
| `backend/app/persona/prompts/card.v1.md` | 페인포인트 생성 지시 | T2 |
| `backend/app/persona/grade.py` | `pain_point` trace 행 | T2 |
| `backend/tests/fixtures/evidence_package.py` | 가짜 근거·가짜 LLM에 페인포인트 | T1, T2 |
| `frontend/src/lib/types.ts` | 페인포인트 타입 | T3 |
| `frontend/src/components/persona/personaView.ts` | `logScale`, `zoneRegions`, `labelOffsets`, `jitter`, `topOpportunity` | T3 |
| `frontend/src/components/persona/OpportunityMap.tsx` | 지도 재작성 | T4 |
| `frontend/src/components/persona/PersonaList.tsx` (신규) | 왼쪽 목록 + 좁은 화면 select | T5 |
| `frontend/src/components/persona/PersonaSummary.tsx` (신규) | 이름·메타·Desire·Goal·Pain Points | T5 |
| `frontend/src/components/persona/CCMTable.tsx` | 행 추가, 3줄 말줄임, +N, sticky 항목 열 | T6 |
| `frontend/src/components/persona/HierarchyTree.tsx` | 들여쓰기 목록 | T7 |
| `frontend/src/components/persona/OpportunityBars.tsx` | HTML 그리드 | T7 |
| `frontend/src/components/persona/PersonaScreen.tsx` | 레이아웃 조립, 첫 화면, 상태 표 | T8 |
| `frontend/src/components/persona/persona.css` (신규) | 레이아웃·반응형·line-clamp 규칙 | T5~T8 |

의존 관계: T1 → T2. T3 → T4. T3 → T5, T6, T7 → T8. 백엔드(T1~T2)와 프론트(T3~T7)는 파일이 겹치지 않아 병렬 가능. T8은 T4~T7 이후 순차.

---

### Task 1: 근거 묶음에 페인포인트 싣기

**Files:**
- Modify: `backend/app/evidence/package.py` (`EvidenceItem`)
- Modify: `backend/app/evidence/assemble.py:228-238` (`_item`)
- Modify: `backend/app/persona/package.py:31-45` (`Evidence`)
- Modify: `backend/tests/fixtures/evidence_package.py` (근거 일부에 `pain_point`)
- Test: `backend/tests/evidence/test_assemble.py`, `backend/tests/persona/test_package.py`

**Interfaces:**
- Produces: `class PainPoint(PackageModel): text: str; quote: str | None; verified: bool = False` (R4) (evidence/package.py). `EvidenceItem.pain_point: PainPoint | None = None`. 페르소나 쪽 `Evidence.pain_point: dict | None = None` (`{text, quote}`), `EvidenceRef`가 상속.

- [ ] **Step 1: 실패 테스트 작성** (`test_assemble.py`)
  - `test_pain_point_carried`: 태그 `{'pain_point': {'text': '추가비용 불안', 'quote': '기본비용이라고'}}`인 문서의 `_item(...)['pain_point'] == {'text': '추가비용 불안', 'quote': '기본비용이라고'}`.
  - `test_pain_quote_verified` (R4): 태그 pain_point.quote가 문서 본문에 있으면 `pain_point.verified is True`, 없으면 False. 일반 인용 검증값과 독립.
  - `test_pain_point_blank_becomes_none`: 태그 `pain_point`가 `None`, `{}`, `{'text': '  ', 'quote': 'x'}`, `{'text': 'a', 'quote': 3}` 각각 → 앞 셋은 `None`, 넷째는 `{'text': 'a', 'quote': None}`.
  - `test_package_schema_and_fields`(기존)에 `EvidenceItem.model_validate`가 `pain_point` 없는 dict도 받는지 단언 추가.
  - `test_dump_omits_none_pain_point` (R1): `pain_point=None`인 `EvidenceItem.model_dump(mode='json', by_alias=True)`에 `pain_point` 키가 없고, 값이 있으면 키가 있다.
- [ ] **Step 2: 실패 테스트 작성** (`tests/persona/test_package.py`)
  - `test_load_package_with_and_without_pain_point`: `pain_point` 있는 package.json과 없는 package.json 모두 `load_package` 성공, `evidence_index(block)`의 ref에 `pain_point` 값 유지.
  - `test_existing_package_digest_unchanged` (R1, CRITICAL 회귀): `pain_point` 없는 기존 package.json을 `load_package`한 뒤 `pipeline._digest(package)`가 변경 전 코드로 계산한 값(픽스처에 고정 문자열로 저장)과 같다. 카드가 있는 세션에서 `mark_stale_if_changed`가 False를 반환한다.
- [ ] **Step 3: RED 확인** — `cd backend && .venv/bin/python -m pytest tests/evidence/test_assemble.py tests/persona/test_package.py -q` → 새 테스트 FAIL.
- [ ] **Step 4: 구현** — 위 Interfaces 그대로. 두 모델 모두 `pain_point`가 None이면 직렬화에서 키를 생략한다(pydantic `model_serializer(mode='wrap')`로 None일 때만 제거). `_item()`은 페인포인트 인용을 기존 `locate()`로 원문에서 찾아 `verified`를 저장하고(R4), `tag.get('pain_point')`가 dict이고 `text.strip()`이 비어 있지 않을 때만 `{'text': text.strip(), 'quote': quote if isinstance(quote, str) else None}`.
- [ ] **Step 5: GREEN 확인** — 같은 명령 PASS, 이어서 `tests/evidence tests/persona -q` 전체 PASS.
- [ ] **Step 6: 커밋** — `feat(evidence): 근거 묶음에 페인포인트 싣기`

### Task 2: 카드 생성에서 Context·페르소나 페인포인트 만들기

**Files:**
- Modify: `backend/app/persona/cards.py` (스키마 `PainCell`, `ContextOut.pain_points`, `_card_schema` 검증, `_evidence_payload`, `generate_card` 후처리, 집계 함수)
- Modify: `backend/app/persona/prompts/card.v1.md`
- Modify: `backend/app/persona/grade.py` (`pain_point` trace)
- Modify: `backend/tests/fixtures/evidence_package.py` (`fake_persona_backend`가 `pain_points` 출력)
- Test: `backend/tests/persona/test_cards.py`, `backend/tests/persona/test_grade.py`

**Interfaces:**
- Consumes: T1의 `EvidenceRef.pain_point`.
- Produces:
  - `class PainCell(Output): text: str; cite: list[str] = Field(min_length=1)`; `ContextOut.pain_points: list[PainCell] = Field(default_factory=list, max_length=3)`.
  - 카드 Context 항목: `pain_points: list[{'text': str, 'cite': list[str], 'grade': 'observed'|'inferred', 'source_pain': str | None}]` (cite는 전역 E 번호).
  - 카드 최상위: `pain_points: list[{'text': str, 'grade': str, 'context_ids': list[str], 'cite': list[str]}]` (최대 5).
  - `def aggregate_pain_points(contexts: list[dict], context_docs: dict[str, int]) -> list[dict]` (cards.py).

- [ ] **Step 1: 실패 테스트 작성** (`test_cards.py`)
  - `test_pain_points_observed_from_tagged_evidence`: 근거 E1에 `pain_point`와 검증된 인용, LLM이 `pain_points=[{'text': '...', 'cite': ['E1']}]` → 카드 Context `pain_points[0]['grade'] == 'observed'`, `source_pain == E1.pain_point.text`.
  - `test_pain_points_inferred_when_rewritten` (R4): 인용 근거에 검증된 pain_point가 있어도 LLM 문장이 태그 문장과 다르면 `grade == inferred`.
  - `test_pain_points_observed_requires_pain_quote_verified` (R4): 일반 인용은 verified지만 pain_point.verified가 False면 `inferred`.
  - `test_pain_points_inferred_when_untagged`: 인용 근거에 `pain_point` 없음 → `grade == 'inferred'`, `source_pain is None`.
  - `test_pain_cite_must_belong_to_context`: 다른 Context의 E 번호 인용 → `_card_schema` 검증 실패 → 2회 후 `CardResult('failed', error='schema')`.
  - `test_pain_cite_required`: `cite: []` → 검증 실패.
  - `test_pain_points_empty_without_evidence`: 근거 없는 Context는 LLM이 무엇을 내도 `pain_points == []`.
  - `test_barrier_filled_from_pain_point`: LLM `barrier.text = None`, `pain_points` 1개 → 카드 `barrier == {'text': 첫 페인포인트 text, 'cite': 그 cite}`.
  - (R2, CRITICAL 회귀) `test_dims_situation_refined_only`(기존)를 두 테스트로 바꾼다: `test_dims_situation_keeps_cited_llm_text` — LLM `state`가 `{'text': '다듬은 문장', 'cite': ['E1']}`이면 그 문장이 남는다. `test_dims_situation_uncited_falls_back` — LLM `state`가 `{'text': '근거에 없는 완전히 다른 상황', 'cite': []}`이면 키워드 원문(`context.situation.state`)으로 대체된다.
  - `test_aggregate_pain_points`: 같은 문장(공백·문장부호만 다름) 두 Context → 1개로 합치고 `context_ids` 2개, 정렬은 observed 우선 → cite 수 내림차순 → Context 문서 수 내림차순, 최대 5개.
  - `test_null_when_no_evidence`(기존)에 카드 최상위 `pain_points == []` 단언 추가.
- [ ] **Step 2: 실패 테스트 작성** (`test_grade.py`)
  - `test_pain_point_trace_rows`: Context `pain_points`의 각 cite가 `trace`에 `field == 'pain_point'` 행으로 들어간다.
- [ ] **Step 3: RED 확인** — `cd backend && .venv/bin/python -m pytest tests/persona/test_cards.py tests/persona/test_grade.py -q` → 새 테스트 FAIL.
- [ ] **Step 4: 구현**
  - `_evidence_payload()`에 `pain_point: ref.pain_point['text'] if ref.pain_point else None`.
  - `_card_schema` 검증에 `pain_points` cite도 기존 규칙(그 Context 근거)으로 검사.
  - `generate_card` 후처리: 근거 없으면 `pain_points = []`; dims 덮어쓰기 분기(현재 192~194행)를 'LLM cite가 비었을 때만 키워드 원문으로 대체'로 좁힘(R2); 등급은 "인용 근거 중 `pain_point.verified`가 참이고 LLM 문장이 그 태그 문장과 같은(공백·문장부호 정규화) 것이 있으면 observed, 아니면 inferred"(R4); `barrier.text is None and pain_points`면 첫 항목으로 채움; cite를 전역 번호로 바꿈.
  - 카드 완성 후 `card['pain_points'] = aggregate_pain_points(rows, {c.context_id: c.metrics.doc_count ...})`. 정규화 키: `re.sub(r'[\s\W_]+', '', text)`.
  - `card.v1.md`에 02-design.md 2.2의 지시 4줄을 추가하고 출력 항목 문장을 `context_id, state, emotion, barrier, pain_points`로 바꾼다.
  - `grade.py`의 `grade_card`가 Context `pain_points` 리스트의 cite를 `field='pain_point'`로 trace에 추가(등급 계산 대상 필드에는 넣지 않음).
  - `fake_persona_backend`는 근거가 있는 Context마다 `pain_points=[{'text': '가짜 불편', 'cite': [첫 근거]}]`를 낸다.
- [ ] **Step 5: GREEN 확인** — 같은 명령 PASS, 이어서 `cd backend && .venv/bin/python -m pytest tests -q` 전체 PASS.
- [ ] **Step 6: 커밋** — `feat(persona): 카드 생성에서 페인포인트 만들기와 키워드 덮어쓰기 제거`

### Task 3: 페인포인트 타입과 지도 계산 함수

**Files:**
- Modify: `frontend/src/lib/types.ts:262-270`
- Modify: `frontend/src/components/persona/personaView.ts`
- Test: `frontend/src/components/persona/personaView.test.ts`
- Create: `frontend/src/components/persona/fixtures/map-s8b25-v2.json` (R8 테스트용, 운영 API `GET /persona/s8b25bf1f185143118303600ee0ec5293/map?version=v2` 응답을 그대로 저장. 개인정보 없음: Context ID·좌표·구역만 포함)

**Interfaces:**
- Produces (types.ts): `PersonaPainPoint = { text: string; grade: PersonaGrade; context_ids: string[]; cite: string[] }`, `PersonaCardContextPain = { text: string; cite: string[]; grade: PersonaGrade; source_pain?: string | null }`; `PersonaCardBody.pain_points?: PersonaPainPoint[]`; `PersonaCardContext.pain_points?: PersonaCardContextPain[]`.
- Produces (personaView.ts):
  - `logScale(v: number, k = 50): number` — `Math.log1p(k*v)/Math.log1p(k)`, 입력은 [0,1]로 clamp.
  - `LOG_TICKS = [0, 0.02, 0.05, 0.1, 0.2, 0.5, 1]`.
  - `zoneRegions(base: PersonaMap['base'], edgeSamples = 128): Record<PersonaZone, [number, number][]>` (R8) — 원래 값 공간 [0,1]²를 기준선 3개(`s = s_line`, `s = s_mean + (1 - s_mean)·i`, `s = (i - i_mean)/(1 - i_mean)`)로 정확히 잘라 구역별 볼록 다각형을 만들고, 각 변을 `edgeSamples`점으로 나눠 `logScale`로 변환한 다각형을 반환. 경계는 백엔드 규칙과 같이 위쪽 포함. `i_mean = 1`이면 diag2 구역(C·F)은 빈 다각형.
  - `zoneOf(i: number, s: number, base): PersonaZone` — 백엔드 `opportunity.zone`과 같은 규칙(경계는 위쪽 포함).
  - `jitter(index: number, count: number, radius = 3): [number, number]` — 겹친 점 n개 중 index번째의 고정 각도 오프셋(`2π·index/count`).
  - `topOpportunity(points: PersonaMapPoint[]): string | null` — odi 최대 Context ID(null 제외, 동점은 context_id 오름차순 첫 번째).

- [ ] **Step 1: 실패 테스트 작성**
  - `logScale(0)===0`, `logScale(1)===1`, `logScale(0.08)`이 0.4 이상이고 선형 위치(0.08)의 5배 이상(몰림 해소, 실제 값 ≈ 0.4093), 단조 증가, 범위 밖 입력 clamp.
  - `zoneOf`가 백엔드 테스트 `tests/persona/test_opportunity.py`의 경계 사례(동일 값 3개 이상 복사)와 같은 결과.
  - `zoneRegions` (R8): 6개 구역 키 모두 존재. 세라젬_261012_sk v2 지도 픽스처(점 114개, `base` 포함)의 모든 점에 대해, 로그 변환 좌표가 백엔드가 준 `zone`의 다각형 안에 있다(점-다각형 포함 판정, 경계 위 허용). `i_mean = 1`일 때 C·F 다각형이 비어 있다.
  - `jitter(0,1)`은 `[0,0]`, `jitter(i,4)` 4개가 서로 다르고 반지름 3 이내.
  - `topOpportunity`: null odi 제외, 동점 처리.
- [ ] **Step 2: RED 확인** — `npm --prefix frontend test -- personaView` → FAIL.
- [ ] **Step 3: 구현** — 위 시그니처. 볼록 다각형 자르기는 단위 정사각형에서 시작해 반평면 3개로 자르는 Sutherland–Hodgman 방식(R8). 다각형 계산은 `base`가 바뀔 때만 다시 하도록 `OpportunityMap`에서 `useMemo`로 감싼다.
- [ ] **Step 4: GREEN 확인** — 같은 명령 PASS.
- [ ] **Step 5: 커밋** — `feat(persona): 지도 로그 척도와 구역 계산 함수`

### Task 4: Opportunity Map 재작성

**Files:**
- Modify: `frontend/src/components/persona/OpportunityMap.tsx`
- Test: `frontend/src/components/persona/components.test.ts` (지도 부분)

**Interfaces:**
- Consumes: T3 함수.
- Produces: `OpportunityMapProps = { map: PersonaMap; highlightedId?: string | null; selectedPersonaId?: string | null; focusPersonaId?: string | null; compact?: boolean; onHighlight?: (id: string | null) => void; onOpenCard?: (personaId: string, contextId: string) => void }`.

- [ ] **Step 1: 실패 테스트 작성**
  - 구역 면 6개가 `data-zone` 속성으로 렌더, F 면 fill이 `var(--danger-soft)`, C가 `var(--warning-soft)`, 나머지 `var(--sunken)`.
  - 축 눈금 텍스트가 `LOG_TICKS` 값(`0.02` 등)이고 "로그 척도" 문구가 있다. "10" 눈금은 없다.
  - 강조·선택이 없으면 점 라벨 `<text data-label>` 0개. `highlightedId` 지정 시 해당 점에만 라벨 1개.
  - `focusPersonaId` 지정 시 다른 페르소나 점 `opacity="0.25"`, 해당 점 1.
  - 범례 버튼 수 = 클러스터 수(페르소나 버튼 없음). 클릭 시 해당 클러스터 점 숨김.
  - i 또는 s가 null인 점은 렌더하지 않고 "지도에 없는 Context N개는 표에서 확인하세요." 표시.
  - 같은 좌표 점 2개는 서로 다른 translate.
- [ ] **Step 2: RED 확인** — `npm --prefix frontend test -- components` → FAIL.
- [ ] **Step 3: 구현** — 02-design.md 3.3 그대로. SVG viewBox 600×420, 최소 높이 320px. 툴팁 `<title>`에는 원래 값.
- [ ] **Step 4: GREEN 확인** — 같은 명령 PASS.
- [ ] **Step 5: 커밋** — `feat(persona): 구역 면과 로그 척도의 기회 지도`

### Task 5: 왼쪽 목록과 상단 요약(Pain Points)

**Files:**
- Create: `frontend/src/components/persona/PersonaList.tsx`, `frontend/src/components/persona/PersonaSummary.tsx`, `frontend/src/components/persona/persona.css`
- Test: `frontend/src/components/persona/components.test.ts`

**Interfaces:**
- Consumes: T3 타입.
- Produces:
  - `PersonaList({ groups, selectedId, onSelect }: { groups: { clusterId: string; items: { id: string; name: string; status: PersonaState; future?: boolean }[] }[]; selectedId: string | null; onSelect: (id: string) => void })` — 768px 이상 목록, 미만 `<select>`+`<optgroup>` (CSS로 전환, 둘 다 렌더).
  - `PersonaSummary({ name, future, meta, desire, goals, painPoints, legacy, onOpenEvidence })` — `painPoints: PersonaPainPoint[] | undefined`, `legacy: boolean`(필드 자체가 없음).

- [ ] **Step 1: 실패 테스트 작성**
  - 목록: 이름 47자 항목에 `title` 전체 이름, 클래스 `persona-name`(CSS line-clamp 2), 상태 점 + 숨김 텍스트("완료" 등), `aria-current`는 선택 항목만.
  - 목록: `<select>`에 클러스터 수만큼 `<optgroup>`.
  - 요약: Pain Points 3개 → 번호 목록 3항목, 각 항목에 GradeMark·Context 칩·근거 수.
  - 요약 (R6): `legacy`면 버튼 없이 "근거 탐색을 다시 실행한 뒤 페르소나를 다시 만들면 페인포인트가 표시됩니다. 인사이트도 다시 만들어야 합니다." + `/pipeline/evidence` 링크(`<a>` 1개, `<button>` 없음), 빈 배열이면 "근거가 부족해 페인포인트를 만들지 못했습니다.", 2개면 "근거가 적어 2개만 찾았습니다.".
  - CSS 파일에 `.persona-name{-webkit-line-clamp:2}`와 `@media (max-width: 767px)` 전환 규칙, 누르는 요소 `min-height: 44px`.
- [ ] **Step 2: RED 확인** — `npm --prefix frontend test -- components` → FAIL.
- [ ] **Step 3: 구현** — 02-design.md 3.2, 3.4-1, 4.1, 6. 색은 토큰만.
- [ ] **Step 4: GREEN 확인** — PASS.
- [ ] **Step 5: 커밋** — `feat(persona): 페르소나 목록과 Pain Points 요약`

### Task 6: Context 비교 표

**Files:**
- Modify: `frontend/src/components/persona/CCMTable.tsx`
- Modify: `frontend/src/components/persona/persona.css`
- Test: `frontend/src/components/persona/components.test.ts`

**Interfaces:**
- Produces: `ccmRows`에 `['pain_point', '페인포인트']`(장벽 다음)과 `['evidence_count', '근거 수']`(마지막) 추가. `CCMCell`에 `more?: number`(+N 표시).

- [ ] **Step 1: 실패 테스트 작성**
  - 행 이름 순서가 행동·상태·감정·장벽·페인포인트·키워드·쓰는 제품·수단·만족도·기회·근거 수.
  - 칸 텍스트 요소에 클래스 `ccm-clamp`(3줄), 페인포인트 `more: 2`면 "+2".
  - 항목 이름 열 `th[scope=row]`에 클래스 `ccm-sticky`, 표 래퍼 `ccm-scroll`.
  - 근거 없는 칸은 "근거 부족" + 클래스 `ccm-empty`.
- [ ] **Step 2: RED 확인** — FAIL.
- [ ] **Step 3: 구현** — 02-design.md 3.4-2, 6. `.ccm-scroll{overflow-x:auto}`, 768px 미만 열 `min-width:200px`.
- [ ] **Step 4: GREEN 확인** — PASS.
- [ ] **Step 5: 커밋** — `feat(persona): 페인포인트 행과 말줄임을 갖춘 비교 표`

### Task 7: 구조 트리와 기회 순위

**Files:**
- Modify: `frontend/src/components/persona/HierarchyTree.tsx`, `frontend/src/components/persona/OpportunityBars.tsx`
- Test: `frontend/src/components/persona/components.test.ts`

**Interfaces:**
- Produces: `HierarchyTree({ root, expandedId }: { root: HierarchyNode; expandedId?: string | null })`; `OpportunityBars`의 props는 그대로.

- [ ] **Step 1: 실패 테스트 작성**
  - 트리: `<svg>` 없음, 중첩 `<ul>`, 클러스터·페르소나 행에 `aria-expanded` 버튼, 각 행에 막대(`data-ratio`)와 문서 수, `expandedId` 페르소나만 펼침.
  - 기회 순위: `<svg>` 없음, 행마다 순위·문장·막대·값 4칸 그리드, 평균선 요소는 막대 영역 안(`data-mean`).
- [ ] **Step 2: RED 확인** — FAIL.
- [ ] **Step 3: 구현** — 02-design.md 3.4-4, 3.6.
- [ ] **Step 4: GREEN 확인** — PASS (인사이트 화면 테스트 `insight.test.ts`, `InsightScreen.qa.test.ts` 포함).
- [ ] **Step 5: 커밋** — `feat(persona): 들여쓰기 구조 트리와 그리드 기회 순위`

### Task 8: 페르소나 화면 조립

**Files:**
- Modify: `frontend/src/components/persona/PersonaScreen.tsx`
- Test: `frontend/src/components/persona/PersonaScreen.test.ts`, `frontend/src/components/persona/finalReview.test.ts`

**Interfaces:**
- Consumes: T4~T7 컴포넌트, T3 `topOpportunity`.

- [ ] **Step 1: 실패 테스트 작성**
  - 첫 진입 보기 = 전체 맵, `topOpportunity` Context가 오른쪽 상세에 선택돼 있음.
  - 카드 보기: 렌더 순서가 PersonaSummary → 비교 표 + 지도(`focusPersonaId` = 선택 페르소나) → 8-B·8-C·8-D 한 줄(탭 역할 요소 없음) → 구조 트리.
  - `ds-card` 클래스 요소가 카드 본문에서 Pain Points 항목 수 + 지도 1개 외에는 없음.
  - 로딩 중 Skeleton이 영역별로 표시(4.1), 지도만 실패하면 지도 자리 오류 + 나머지 정상.
  - (R7) 설계 4.1의 '처방만 실패하면 처방 패널에만 오류'는 적용하지 않는다. 백엔드가 처방 실패 시 카드 전체를 failed로 저장하므로, 8-B·8-C·8-D 패널은 카드 실패와 같은 화면("이 페르소나 카드를 만들지 못했습니다." + 기존 [다시 만들기])을 쓴다. 테스트: 카드 status failed면 세 패널 대신 실패 안내 1개.
  - 기존 테스트(인사이트 도출 버튼, stale 재생성 확인, 근거 탐색 이동)는 그대로 통과.
- [ ] **Step 2: RED 확인** — `npm --prefix frontend test -- PersonaScreen finalReview` → FAIL.
- [ ] **Step 3: 구현** — 02-design.md 3.1, 3.4, 3.5, 3.5.1, 4.1. 영역별 부분 실패는 기존 `Promise.allSettled` 결과를 영역별로 전달.
- [ ] **Step 4: GREEN 확인** — `npm --prefix frontend test`, `npm --prefix frontend run lint`, `npm --prefix frontend run build` 모두 PASS.
- [ ] **Step 5: 커밋** — `feat(persona): 페르소나 화면 재구성`

---

## QA 계획

### 환경

- worktree에서 백엔드 가상환경: `cd backend && /opt/homebrew/bin/python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt -r requirements-dev.txt -c constraints.txt` (하네스 검증 명령이 `backend/.venv/bin/python`을 쓴다).
- 프론트: `npm --prefix frontend ci`.
- QA 데이터: 운영 데이터를 바꾸지 않도록 **복사본**을 쓴다. `QA_DATA=/private/tmp/dcx-qa-data`에 `~/srv/dcx-agent/shared/data`에서 `sessions/s8b25bf1f185143118303600ee0ec5293`, `sessions/s89d92341bdb340b0bd7a5943a1c86dc7`, 두 세션의 `llmcache`, `preprocessed`, `classified`, `.author_salt`를 복사한다.
- 서버 시작:
  - 백엔드: `cd backend && LOCAL_DATA_DIR=$QA_DATA AUTHOR_SALT_PATH=$QA_DATA/.author_salt LABEL_GPT_BACKEND=codex_exec .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8411`
  - 프론트: `cd frontend && NEXT_PUBLIC_API_URL=http://127.0.0.1:8411 npx next dev -p 3411`
- **테스트 URL:** `http://localhost:3411/pipeline/personas` (세션 선택 후)
- 페인포인트 화면 확인용 재생성은 **복사본에서만**: 세션 s8b25 v2의 근거 묶음을 다시 만들고(태깅 캐시 사용) `POST /persona/{sid}/run?version=v2 {"fresh":true}`로 카드 재생성.

### 브라우저 시나리오 (gstack `qa-only`)

| # | 시나리오 | 기대 결과 | 수용 기준 |
|---|---|---|---|
| Q1 | 세라젬 AI 웰니스 모듈러하우스(이전 카드) 페르소나 단계 진입 | 전체 맵으로 열림, 점이 축 대부분에 퍼짐, 구역 면 6개, 라벨 겹침 없음, 범례 7개 | 기획 6·7 |
| Q2 | 같은 세션에서 페르소나 카드 열기 | Pain Points 자리에 "다시 만들면 표시" 안내, 화면 깨짐 없음 | 기획 13, 설계 4.1 |
| Q3 | 복사본 s8b25 v2 카드 재생성 후 카드 열기 | 상단 Pain Points 3~5개, 관측/추론 표시, 원문 펼침 | 기획 1~3·9 |
| Q4 | 같은 카드의 비교 표 | 장벽·상태·감정이 문장, "청소 비용 1.5W~36W 10분" 같은 키워드 나열 없음, 3줄 말줄임과 펼치기 | 기획 4·9 |
| Q5 | 카드 오른쪽 지도 | 선택 페르소나 점만 진하고 나머지 흐림 | 기획 10 |
| Q6 | 구조 트리 펼치기, 인사이트 화면 기회 순위 | 선 겹침·잘림 없음, 문장과 막대 겹침 없음 | 기획 11 |
| Q7 | 768px 폭 | 목록이 select로, 표 가로 스크롤 + 항목 열 고정, 누르는 요소 44px | 기획 12 |
| Q8 | 키보드 Tab 이동 | 목록 → 보기 버튼 → 페인포인트 항목 → 표 칸 순서, 포커스 링 보임 | 기획 12 |

### 검증 명령 (하네스 `verificationCommands`)

- `backend/.venv/bin/python -m pytest backend/tests -q`
- `npm --prefix frontend run lint`
- `npm --prefix frontend run build`
- `npm --prefix frontend test`

## 되돌리기

- 기능 브랜치를 merge하지 않으면 운영 영향이 없다.
- merge 후 문제가 생기면 `git revert <merge-commit>`로 되돌린다. 단, 이전 코드는 `extra='forbid'`라 새 코드가 `pain_point`를 실어 만든 근거 묶음을 거부한다(R5). 되돌린 뒤 그런 세션은 근거 탐색 화면에서 근거 묶음을 다시 조립해야 한다(태깅 LLM은 캐시를 써서 다시 호출하지 않음). 이번 실행은 운영 데이터를 다시 만들지 않으므로 배포 직후 되돌리면 영향받는 세션이 없다. 새 카드의 추가 필드는 이전 화면이 무시한다.
- 운영 배포는 이 실행 범위가 아니며, 사용자가 따로 요청할 때만 한다.

## Self-Review

- 기획 수용 기준 1~13 → T1(1), T2(2·3·4·5), T4(6·7·10), T5(8·9 상단), T6(9 표), T7(11), T8(9·12), 전 Task(13).
- 설계 결정 1A(T5·T8), 2A(T5·T8), 3A(T3 `topOpportunity`·T8), 4A(T8), 5A(T4·T5), 6A(T5·T6), 7A(T6).
- 타입 이름: `PersonaPainPoint`, `PersonaCardContextPain`, `aggregate_pain_points`, `logScale`, `zoneRegions`, `zoneOf`, `jitter`, `topOpportunity` — 정의한 Task와 사용하는 Task가 같은 이름을 쓴다.

---

# Eng Review (plan-eng-review) — 대상: docs/development/stage6-8-visual-redesign/03-plan.md

## Scope record

feature answers: 기능 축소 제안 없음; structure: A Original arrangement (D2 답변); accepted scope: 03-plan.md Task 1~8 그대로, 파일 배치 원안(PersonaList.tsx, PersonaSummary.tsx, persona.css 신규); pending remedies: R1, R2 (R3 철회: 64×64 격자 계산은 1ms 미만이라 성능 문제 아님)

Scope Challenge 결과: scope accepted as-is

## Decision ledger

### R1: 근거 묶음 해시가 바뀌어 모든 세션 페르소나가 "갱신 필요"로 바뀌는 문제
Finding: 1, P1, confidence 9/10, backend/app/persona/pipeline.py:73-75 `_digest` = `hashlib.sha256(json.dumps(package.model_dump(mode='json', by_alias=True), ...))`, :118 `cards.get('package_hash', _digest(package)) != _digest(package)`, reviewer: Claude (plan-eng-review)
Plan baseline: Task 1이 `EvidenceItem.pain_point: PainPoint | None = None`을 추가 (원안, 승인 없음)
Runtime evidence: 기존 package.json을 새 모델로 읽어 model_dump하면 모든 근거 항목에 `"pain_point": null`이 추가되어 해시가 달라짐 → `mark_stale_if_changed`가 카드가 있는 모든 세션(예: 세라젬 AI 웰니스 모듈러하우스)을 stale로 표시하고 인사이트도 stale. 구현 전이라 관찰은 아니고 코드 읽기로 추론.
Comparison grid:
| Choice | Current | A | B |
|---|---|---|---|
| R1 None 값 직렬화 | 원안: `pain_point: null` 항상 출력 | 값이 None이면 직렬화에서 생략(두 계약 모델 모두), 기존 묶음 해시 불변 테스트 추가 | 원안 유지, 배포 후 모든 세션이 "갱신 필요"가 됨 |
Question D3: 근거 묶음 해시 변경 문제 (질문 본문은 아래 AskUserQuestion과 동일)
Header: 해시 보호
Options:
A) None이면 생략 (Recommended)
EvidenceItem과 페르소나 쪽 Evidence가 pain_point가 None일 때 직렬화에서 필드를 빼도록 합니다. 기존 package.json의 해시가 그대로라 이미 완성된 세션이 갱신 필요로 바뀌지 않습니다. 테스트: 기존 묶음 로드→dump 해시가 변경 전과 같음. (human: ~1h / CC: ~10min)
B) 원안 유지
항상 pain_point: null을 출력합니다. 배포 직후 카드가 있는 모든 세션의 페르소나·인사이트가 갱신 필요로 바뀌어 다시 만들어야 합니다.

State: approved
Actual answer: A) None이면 생략 (D3 답변)
Accepted scope: EvidenceItem(evidence/package.py)과 페르소나 쪽 Evidence(persona/package.py)가 pain_point가 None이면 직렬화에서 필드를 생략. Task 1에 기존 묶음 해시 불변 테스트 추가.
History: none

### R2: 키워드 덮어쓰기 제거 시 지켜야 할 회귀 계약
Finding: 2, P2, confidence 9/10, backend/app/persona/cards.py:192-194 `elif (cell['text'] is not None and context.situation_origin == 'dims' and getattr(context.situation, field) is not None): cell['text'] = getattr(context.situation, field)`, 기존 테스트 backend/tests/persona/test_cards.py:80-87 `test_dims_situation_refined_only`, reviewer: Claude (plan-eng-review)
Plan baseline: Task 2가 분기를 삭제하고 LLM 문장을 항상 유지 (설계 2.3 승인 범위: "키워드로 덮어쓰지 않는다")
Runtime evidence: 현재 코드는 LLM이 근거와 다른 상황을 써도 키워드 원문으로 되돌린다(기존 테스트가 '근거에 없는 완전히 다른 상황'을 막음). 삭제하면 이 보호가 사라진다.
Comparison grid:
| Choice | Current | A | B |
|---|---|---|---|
| R2 LLM 문장 유지 조건 | 원안: 항상 LLM 문장 | 근거 번호(cite)가 1개 이상이면 LLM 문장, cite가 없으면 키워드 원문으로 대체 | 항상 LLM 문장(원안) |
Question D4: 키워드 덮어쓰기 제거 회귀 계약
Header: 덮어쓰기 규칙
Options:
A) 근거 있을 때만 문장 (Recommended)
상태·감정·장벽 칸은 LLM 문장에 그 Context의 근거 번호가 1개 이상 있을 때만 문장을 쓰고, 근거 번호가 없으면 지금처럼 키워드 원문으로 둡니다. 테스트: cite 있는 문장은 유지, cite 없는 다른 문장은 키워드 원문으로 대체. (human: ~1h / CC: ~10min)
B) 항상 LLM 문장
원안대로 항상 LLM 문장을 씁니다. 근거 번호 없는 문장은 등급만 낮게(추론 이하) 표시되고 화면에는 그대로 나옵니다.

State: approved
Actual answer: A) 근거 있을 때만 문장 (D4 답변)
Accepted scope: situation_origin이 dims인 상태·감정·장벽 칸은 LLM 문장의 cite가 1개 이상이면 문장 유지, cite가 비면 키워드 원문으로 대체. Task 2 테스트 2개로 고정.
History: none

### F5: 사실 정정 — logScale 테스트 기준값
Finding: Outside voice #5, P2, confidence 10/10, 03-plan.md Task 3 Step 1, reviewer: Codex
Plan baseline: `logScale(0.08)`이 0.5 이상
Runtime evidence: `math.log1p(50*0.08)/math.log1p(50) = 0.40934`. 0.5 기준은 올바른 구현도 실패시킨다.
Correction: 기준을 "0.4 이상이고 선형 위치의 5배 이상"으로 바꿈. 산식·k=50·동작은 그대로라 질문 없이 기록.

### R4: 페인포인트 '관측' 판정 기준
Finding: Outside voice #1, P1, confidence 9/10, backend/app/persona/package.py:173 `verified=item.quote.verified if item.quote else False` (일반 인용의 검증값), backend/app/evidence/assemble.py:230-232 `quote = next((q for q in located if q['verified']), ...)`, reviewer: Codex (Claude 확인)
Plan baseline: Task 2 "인용 근거 중 pain_point가 있고 verified인 것이 하나 이상이면 observed" (설계 2.2 승인: 관측=태깅 페인포인트 있고 원문 인용 검증)
Runtime evidence: verified는 페인포인트 인용이 아니라 문서의 일반 인용 검증 결과다. LLM이 새로 쓴 문장도 태그가 있는 근거를 인용하면 관측이 된다.
Comparison grid:
| Choice | Current | A | B |
|---|---|---|---|
| R4 관측 판정 | 일반 인용 verified + 태그 존재 | 묶음 조립 때 pain_point.quote를 문서에서 찾아 `pain_point.verified` 저장. 관측 = 인용 근거의 pain_point.verified가 참이고 LLM 문장이 그 태그 문장과 같을 때(정규화 비교). 그 외 추론 | 원안 유지 |
Question D5: 페인포인트 관측 판정 기준 (질문 본문은 AskUserQuestion과 동일)
Header: 관측 기준
Options:
A) 페인포인트 인용 직접 검증 (Recommended)
묶음을 만들 때 페인포인트 인용을 원문에서 찾아 검증 결과를 함께 저장합니다. 카드에서는 검증된 태그 페인포인트 문장을 그대로 고른 경우만 관측, LLM이 새로 쓰거나 고친 문장은 추론입니다. (human: ~2h / CC: ~15min)
B) 원안 유지
문서의 일반 인용 검증값과 태그 존재만으로 관측을 판정합니다. 가짜 페인포인트 인용이나 LLM이 새로 쓴 문장도 관측으로 보일 수 있습니다.
State: approved
Actual answer: A) 페인포인트 인용 직접 검증 (D5 답변)
Accepted scope: 묶음 조립 때 pain_point.quote를 locate()로 원문에서 찾아 pain_point.verified 저장. 카드 관측 = 인용 근거의 pain_point.verified가 참이고 LLM 문장이 그 태그 문장과 정규화 비교로 같을 때, 그 외 추론. Task 1·2 테스트로 고정.
History: none

### R5: 되돌리기 계약
Finding: Outside voice #2, P1, confidence 9/10, backend/app/evidence/package.py:11 `model_config = ConfigDict(extra='forbid', populate_by_name=True)`, reviewer: Codex (Claude 확인)
Plan baseline: 03-plan.md 되돌리기 "선택 필드라 이전 코드가 그대로 읽는다"
Runtime evidence: 이전 코드는 extra='forbid'라 pain_point가 저장된 새 묶음을 거부한다(PackageInvalid → "근거 탐색을 다시 실행하세요").
Comparison grid:
| Choice | Current | A | B |
|---|---|---|---|
| R5 되돌리기 | 코드만 revert | 되돌리기 절차에 "revert 후 해당 세션 근거 묶음 다시 조립(태깅 캐시 사용)" 명시 + 이번 실행은 운영 데이터 재생성 없음을 근거로 운영 영향 없음 기록 | 이전 코드에서도 읽히도록 먼저 extra 허용 배포 후 본 기능 배포(2단계 배포) |
Question D6: 되돌리기 계약
Header: 되돌리기
Options:
A) 절차에 재조립 명시 (Recommended)
되돌릴 때 코드 revert 뒤 새 묶음을 만든 세션만 근거 묶음을 다시 조립하도록 절차에 적습니다. 이번 실행은 운영 데이터를 다시 만들지 않으므로 배포 직후 되돌려도 영향받는 세션이 없습니다. (human: ~15min / CC: ~2min)
B) 2단계 배포
먼저 이전 코드가 모르는 필드를 무시하도록 바꿔 배포하고, 그다음 본 기능을 배포합니다. 되돌리기는 코드만으로 되지만 배포가 두 번 필요합니다.
State: approved
Actual answer: A) 절차에 재조립 명시 (D6 답변)
Accepted scope: 되돌리기 절에 revert 후 새 코드로 근거 묶음을 만든 세션은 근거 묶음 재조립(태깅 캐시 사용) 필요, 이번 실행은 운영 데이터 재생성 없음 명시. 코드 변경 없음.
History: none

### R6: 이전 카드의 "페르소나 다시 만들기" 동작
Finding: Outside voice #3, P1, confidence 9/10, backend/app/persona/pipeline.py:290 `if active in done ...: continue`, :238 `shutil.rmtree(root, ignore_errors=True)` (fresh), reviewer: Codex (Claude 확인)
Plan baseline: 설계 4.1 "필드 없음: '페르소나를 다시 만들면 페인포인트가 표시됩니다.' + [페르소나 다시 만들기]", Task 5는 버튼 존재만 검사
Runtime evidence: 일반 실행은 완료 카드를 건너뛰고, fresh는 카드·인사이트를 모두 지운다. 기존 묶음에는 pain_point가 없어 묶음 재조립 없이 카드만 다시 만들면 태그 페인포인트가 들어가지 않는다.
Comparison grid:
| Choice | Current | A | B |
|---|---|---|---|
| R6 이전 카드 안내 | 버튼, 동작 미정 | 버튼 대신 안내 문구 + [근거 탐색으로] 링크: "근거 탐색을 다시 실행한 뒤 페르소나를 다시 만들면 페인포인트가 표시됩니다. 인사이트도 다시 만들어야 합니다." | 버튼이 근거 묶음 재조립 → fresh 페르소나 실행을 연달아 호출(확인 창, 새 백엔드 엔드포인트 필요) |
Question D7: 이전 카드 갱신 경로
Header: 갱신 경로
Options:
A) 안내 + 근거 탐색 링크 (Recommended)
이전 카드에는 버튼 대신 순서를 알려 주는 안내와 근거 탐색 화면 링크를 둡니다. 기존 근거 탐색·페르소나 재생성 흐름을 그대로 써서 새 엔드포인트가 필요 없습니다. (human: ~30min / CC: ~5min)
B) 한 번에 갱신 버튼
버튼 하나로 근거 묶음 재조립과 페르소나 재생성을 이어서 실행합니다. 편하지만 새 백엔드 엔드포인트와 확인 창, 실패 처리가 추가됩니다. (human: ~1d / CC: ~1h)
State: approved
Actual answer: A) 안내 + 근거 탐색 링크 (D7 답변)
Accepted scope: 이전 카드(필드 없음)는 버튼 대신 순서 안내 문구와 /pipeline/evidence 링크. 설계 4.1 Pain Points 빈 값 문구를 이 문구로 정정. Task 5 테스트로 고정.
History: none

### R7: 8-D 처방 부분 실패 약속
Finding: Outside voice #4, P2, confidence 9/10, backend/app/persona/pipeline.py:293-300 (처방·scope 실패 시 카드 전체 failed), 02-design.md 4.1 "처방만 실패하면 처방 패널에만 오류", reviewer: Codex (Claude 확인)
Plan baseline: 설계 4.1 상태 표 부분 열 (결정 2A)
Runtime evidence: 현재 백엔드는 처방 실패 시 카드 본문 없이 전체 failed를 저장해 프론트가 분리 표시할 수 없다.
Comparison grid:
| Choice | Current | A | B |
|---|---|---|---|
| R7 처방 부분 실패 | 처방 패널만 오류(구현 불가) | 상태 표의 해당 칸을 "카드 실패와 같음(다시 만들기)"으로 정정, 백엔드 변경 없음 | 백엔드가 처방 실패 시 카드는 done, prescription=null+오류를 저장하도록 변경 |
Question D8: 처방 부분 실패
Header: 부분 실패
Options:
A) 상태 표 정정 (Recommended)
처방만 실패하는 경우를 따로 다루지 않고 지금처럼 카드 실패로 보여 줍니다. 상태 표의 약속만 실제 동작에 맞게 고칩니다. (human: ~10min / CC: ~2min)
B) 백엔드 부분 저장 추가
처방이 실패해도 카드 본문은 저장하고 처방 패널에만 오류를 보이도록 백엔드를 바꿉니다. 범위가 늘어나고 재시도 경로도 필요합니다. (human: ~4h / CC: ~30min)
State: approved
Actual answer: A) 상태 표 정정 (D8 답변)
Accepted scope: 처방 단독 부분 실패는 다루지 않고 카드 실패와 같은 화면으로 표시. 백엔드 변경 없음. Task 8에 정정 문구와 테스트 반영.
History: none

### R8: 구역 면 그리는 방식
Finding: Outside voice #6, P2, confidence 8/10, 03-plan.md Task 3 `zoneRegions` 64×64 격자, backend/app/persona/opportunity.py:28-40 (직선 3개로 구역 판정), reviewer: Codex (Claude 확인: 첫 셀 [0,1/64]이 로그 척도에서 축의 약 14.7%)
Plan baseline: Task 3 격자 분류 후 다각형 반환 (설계 3.3 승인 동작: 구역 면은 백엔드 판정과 같은 경계)
Runtime evidence: 저값 영역에서 격자 한 칸이 화면의 큰 부분을 차지해 점의 구역과 배경색이 어긋날 수 있다.
Comparison grid:
| Choice | Current | A | B |
|---|---|---|---|
| R8 구역 다각형 계산 | 64×64 격자 분류 | 원래 공간에서 직선 3개로 구역 다각형을 정확히 자른 뒤, 각 변을 촘촘히(변당 128점) 샘플링해 로그 척도로 변환. 테스트: 점 114개 픽스처의 백엔드 zone과 다각형 포함 판정 일치 | 격자를 256×256으로 늘림 |
Question D9: 구역 면 계산 방식
Header: 구역 계산
Options:
A) 직선으로 정확히 자르기 (Recommended)
원래 값 공간에서 기준선 3개로 구역 다각형을 정확히 자른 뒤 변만 촘촘히 변환합니다. 점의 구역과 배경색이 항상 일치합니다. (human: ~2h / CC: ~15min)
B) 격자 촘촘히
격자를 256×256으로 늘려 오차를 줄입니다. 계산이 16배 늘고 저값 영역 오차가 여전히 남습니다.
State: approved
Actual answer: A) 직선으로 정확히 자르기 (D9 답변)
Accepted scope: zoneRegions를 기준선 3개로 원래 공간에서 정확히 자르고 변만 128점 샘플링해 로그 변환. 실제 세션 점 114개의 구역 일치 테스트로 고정.
History: none

Approval readiness: PASS — R1(D3 A), R2(D4 A), R4(D5 A), R5(D6 A), R6(D7 A), R7(D8 A), R8(D9 A) 모두 실제 답변 인용. R3 철회, F5 사실 정정.

## 검토 결과 요약 (plan-eng-review)

### 항목별 결과
- Scope Challenge: scope accepted as-is (원안 파일 배치, D2)
- 1. Architecture: 1건 — R1 근거 묶음 해시 변경으로 전 세션 stale (P1, 승인 A)
- 2. Code quality: 1건 — R2 키워드 덮어쓰기 제거 회귀 계약 (P2, 승인 A). 백엔드 `zone()` 규칙의 프론트 재구현은 R8 테스트로 일치 확인.
- 3. Tests: 아래 다이어그램, 공백 0 (계획 테스트 + R1·R2·R4·R8 테스트 추가 후). 프롬프트 변경은 QA Q3(복사본 실제 LLM 재생성)으로 확인 [→EVAL].
- 4. Performance: 문제 없음 (R3 철회)
- Outside voice (Codex): 6건 — #1→R4, #2→R5, #3→R6, #4→R7, #5→F5 사실 정정, #6→R8. 모두 반영.

### 테스트 커버리지

```
CODE PATHS                                               USER FLOWS
[+] evidence/assemble.py _item                           [+] 전체 맵 진입
  ├── [PLAN ★★★] pain_point 실림/빈 값/None 생략 (T1,R1)    ├── [PLAN ★★] 기회 최대 Context 미리 선택 (T8)
  └── [PLAN ★★★] 페인포인트 인용 검증 (T1,R4)              └── [PLAN ★★] 범례 토글·라벨 조건 (T4)
[+] persona/package.py load/digest                       [+] 카드 열기
  └── [PLAN ★★★] 기존 묶음 해시 불변 CRITICAL (T1,R1)      ├── [PLAN ★★★] Pain Points 3/2/0/필드없음 (T5,R6)
[+] persona/cards.py generate_card                         ├── [PLAN ★★] 비교 표 말줄임·+N·sticky (T6)
  ├── [PLAN ★★★] 관측/추론 판정 (T2,R4)                    └── [PLAN ★★] 카드 실패 시 패널 대체 (T8,R7)
  ├── [PLAN ★★★] 인용 소속·필수 검증 (T2)                [+] 좁은 화면 768px
  ├── [PLAN ★★★] dims cited 유지/uncited 대체 CRITICAL (T2,R2) └── [→E2E] QA Q7 (브라우저)
  ├── [PLAN ★★] 장벽 비면 페인포인트로 채움 (T2)
  └── [PLAN ★★★] 페르소나 집계 정렬·중복 (T2)        LLM integration: [→EVAL] card.v1.md 변경 — QA Q3
[+] personaView.ts
  ├── [PLAN ★★★] logScale·zoneOf·jitter·topOpportunity (T3)
  └── [PLAN ★★★] zoneRegions 실제 점 114개 일치 (T3,R8)

COVERAGE(계획 기준): 코드 경로 13/13, 사용자 흐름 7/8 (768px은 브라우저 QA)
```

### NOT in scope
- 처방 단독 실패 시 부분 저장 (R7에서 상태 표 정정으로 결정)
- 이전 카드 한 번에 갱신 버튼·새 엔드포인트 (R6에서 안내 + 링크로 결정)
- 2단계 배포 (R5에서 되돌리기 절차 명시로 결정)
- 6·7단계 화면, DESIGN.md (기획·설계 범위 밖)

### What already exists (재사용)
- `evidence/quotes.locate()` — 페인포인트 인용 검증(R4)에 그대로 사용
- `persona/grade.grade_card()` trace — `pain_point` 행 추가만
- `persona/pipeline._digest`·`mark_stale_if_changed` — 변경 없이 R1 직렬화 규칙으로 보호
- 프론트 `GradeMark`, `Skeleton`, `ds-tbl`, `foldColumns`, `usePolling`, `displayError`

### Failure modes
| 경로 | 실패 | 대응 | 사용자에게 보이는가 |
|---|---|---|---|
| 근거 묶음 조립 | 태그 pain_point 형식 이상 | None 정규화 (T1 테스트) | 해당 근거 페인포인트 없음, 정상 |
| 카드 생성 LLM | 다른 Context 근거 인용·빈 cite | 스키마 실패 → 재시도 → 카드 실패 (T2) | "카드를 만들지 못했습니다" + 다시 만들기 |
| 배포 후 기존 세션 | 해시 변경 | R1 None 생략 (T1 CRITICAL) | 변화 없음 |
| 되돌리기 | 이전 코드가 새 묶음 거부 | R5 절차: 근거 묶음 재조립 | "근거 탐색을 다시 실행하세요" 안내 |
| 지도 | null 좌표·저값 구역 | 표로 안내, R8 정확 경계 | 안내 문구 |
- critical gap 0개

### Worktree 병렬화
| Step | Modules touched | Depends on |
|---|---|---|
| T1→T2 | backend/app/evidence, backend/app/persona, backend/tests | — |
| T3→T4 | frontend/src/components/persona(personaView, OpportunityMap), frontend/src/lib | — |
| T5, T6, T7 | frontend/src/components/persona(신규 컴포넌트·CCMTable·Tree·Bars) | T3 |
| T8 | frontend/src/components/persona/PersonaScreen | T4~T7 |

- Lane A: T1 → T2 (백엔드). Lane B: T3 → T4. Lane C: T5 → T6 → T7 (같은 persona.css를 만지므로 순차). 이후 T8.
- 실행 순서: A와 B를 동시에 시작, B 완료 후 C, A·C 완료 후 T8.
- 충돌: `persona.css`(T5·T6·T8), `components.test.ts`(T4~T7) — 같은 Lane에서 순차 처리.

### Implementation Tasks (검토에서 추가된 작업)
- [ ] **E1 (P1, human: ~1h / CC: ~10min)** — evidence/persona package — None pain_point 직렬화 생략 + 해시 불변 테스트 (R1, Task 1에 반영)
- [ ] **E2 (P1, human: ~2h / CC: ~15min)** — assemble/cards — 페인포인트 인용 검증과 관측 판정 (R4, Task 1·2에 반영)
- [ ] **E3 (P2, human: ~1h / CC: ~10min)** — cards — dims cited 유지/uncited 대체 (R2, Task 2에 반영)
- [ ] **E4 (P2, human: ~30min / CC: ~5min)** — PersonaSummary — 이전 카드 안내 + 근거 탐색 링크 (R6, Task 5에 반영)
- [ ] **E5 (P2, human: ~10min / CC: ~2min)** — PersonaScreen — 카드 실패 시 패널 대체 (R7, Task 8에 반영)
- [ ] **E6 (P2, human: ~2h / CC: ~15min)** — personaView — 정확한 구역 다각형 (R8, Task 3에 반영)
- [ ] **E7 (P3, human: ~5min / CC: ~1min)** — 되돌리기 절차 문서 (R5, 반영 완료)

### Unresolved decisions
- 없음

### Completion summary
- Step 0: Scope Challenge — scope accepted as-is
- Architecture Review: 1 issues found
- Code Quality Review: 1 issues found
- Test Review: diagram produced, 0 gaps identified (검토 결정 반영 후)
- Performance Review: 0 issues found
- NOT in scope: written
- What already exists: written
- TODOS.md updates: 0 items proposed to user
- Failure modes: 0 critical gaps flagged
- Unresolved decisions: 0 in this review
- Outside voice: codex, completed (6 findings, 모두 반영)
- Parallelization: 3 lanes, 2 parallel / 1 sequential
- Lake Score: 7/7

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | `/plan-ceo-review` | Scope & strategy | 0 | — | — |
| Outside Review | codex via `/plan-eng-review` | Independent 2nd opinion | 1 | completed | 6 findings (5 decisions + 1 correction), all resolved |
| Eng Review | `/plan-eng-review` | Architecture & tests (required) | 1 | issues_open | 2 issues, 0 critical gaps (all resolved in plan) |
| Design Review | `/plan-design-review` | UI/UX gaps | 1 | clean | score: 5/10 → 8/10, 7 decisions |
| DX Review | `/plan-devex-review` | Developer experience gaps | 0 | — | — |

- **OUTSIDE COVERAGE:** codex, plan-review, completed, 6 findings (R4~R8, F5) — 모두 이 계획에 반영.
- **VERDICT:** Design Review CLEAR. Eng Review는 발견 2건을 계획에 반영했으며 미해결 결정 없음(상태 issues_open은 발견 건수 기준). 구현 준비 완료.

NO UNRESOLVED DECISIONS
