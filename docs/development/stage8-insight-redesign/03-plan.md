# 인사이트(8-E) 화면 재구성 · 구현 계획 + QA 계획

> **For agentic workers:** 구현은 하네스 규칙에 따라 Task마다 `codex:codex-rescue`(`--wait --fresh`, 쓰기 가능 작업)로 위임한다. 각 Task는 RED → GREEN → 리팩터링 순서로 진행하고, Task별 보고서를 `docs/development/stage8-insight-redesign/tasks/T<n>.md`에 남긴다. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 인사이트 도출·채팅 수정이 headline·statements·hashtags·flow를 내고, 코드가 Context별 보기 정보를 계산해, 인사이트 화면을 시안처럼 한 개씩 넘겨 보는 구조로 다시 만든다.

**Architecture:** 백엔드는 `insights.py`에 출력 스키마 확장과 공통 검사 `validate_items`, Context 보기 계산 `context_view`를 두고, 조회 API가 `summary`와 예전 판 보기 정보를 채운다. 채팅 수정은 같은 검사와 `focus_id`를 쓴다. 프론트는 순수 함수 `insightView.ts`가 대체 규칙·라벨·칩 문구를 만들고, 화면은 상단 바·헤더·레이더·막대·흐름·채팅 띠·컨셉 컴포넌트로 나눈다.

**Tech Stack:** FastAPI + Pydantic v2 + pytest (backend, Python 3.12), Next.js 16 + React 19 + vitest (frontend, `renderToStaticMarkup` 기반 테스트).

**Spec:** `docs/development/stage8-insight-redesign/01-brainstorm.md`, `docs/development/stage8-insight-redesign/02-design.md` (디자인 검토 결정 1A~10A 포함)

**설계와 다른 점:** 아래 Eng Review의 R1~R7 승인 결정이 설계 문서와 다르면 이 계획이 우선한다(예: 설계 4.1 "다시 도출 버튼은 범위 밖" → R1로 추가, 설계 3.1 focus_id → R3 '현재 인사이트' 대상으로 보강, 설계 5.0 1A → R7 조건).

## Global Constraints

- 새 API 엔드포인트를 만들지 않는다. `GET /insight/{sid}` 응답에 `summary`를, `POST /insight/{sid}/chat` 본문에 선택 필드 `focus_id`를 더할 뿐이다.
- 근거 묶음 모델(`backend/app/persona/package.py`, `backend/app/evidence/package.py`)은 바꾸지 않는다. 바꾸면 모든 세션 페르소나가 "갱신 필요"가 된다(학습 기록 evidence-package-digest-stale).
- 숫자·축·차원·반례는 코드가 채운다. LLM 출력의 숫자 필드는 버린다.
- 레이더 축 정의(`RADAR_AXES`)·ODI·구역 산식은 바꾸지 않는다.
- 새 필드가 없는 예전 인사이트 판을 읽을 수 있어야 한다. 조회 때 임베딩을 부르지 않는다.
- 프롬프트는 `derive.v2.md`, `edit.v2.md`를 새로 만들고 v1 파일은 지우지 않는다.
- 색·글자는 `frontend/src/styles/tokens.css` 기존 토큰만 쓴다(설계 5.1 표). 새 hex 값·새 토큰 금지.
- 사용자에게 보이는 문구는 설계 4.1, 6.1, 4절 칩 문구(10A)의 문장을 그대로 쓴다.
- 운영 데이터(`~/srv/dcx-agent/shared/data`)는 바꾸지 않는다. QA는 복사본에서만 한다.

## Review Focus

1. **Context가 1개인 인사이트** → `flow` 1개 허용, 카드 1개·화살표 없음, 칩 ② 숨김 (T1 `test_validate_flow_single_context`, T4 `single context hides second chip`).
2. **LLM이 `#심박`, `“제목”`처럼 기호를 붙여 내는 출력** → 저장 전 정리 (T1 `test_validate_cleans_hashtag_and_quotes`).
3. **채팅으로 `context_ids`를 바꿨는데 `flow`가 옛 ID를 가리킴** → 검사 실패 → `FAILURE_COPY`, 판 유지 (T3 `test_edit_rejects_stale_flow`).
4. **같은 마지막 어절의 페르소나 두 개("…러너", "…러너")** → 둘 다 전체 이름 (T4 `persona short label collision`).
5. **예전 판 + 근거 묶음 없음(`PackageMissing`)** → 조회 성공, `contexts`는 짧은 번호만, `context_odi_mean` null (T2 `test_get_insights_without_package`).

---

## 파일 구조

| 파일 | 책임 | Task |
|---|---|---|
| `backend/app/persona/insights.py` | `FlowStep`, `InsightItem` 확장, `validate_items`, `context_view`, `summary`, `recompute`의 `contexts` 저장 | T1, T2 |
| `backend/app/persona/prompts/derive.v2.md` (신규) | 새 필드 생성 지시 | T1 |
| `backend/app/persona/store.py` | `_concept_identity`에 새 문구 키 (R2) | T1 |
| `backend/app/persona/chat.py` | 인사이트 수정 검사 → `validate_items`, `focus_id`, `insight:{id}` 대상(R3), Context 요약(R5) | T3 |
| `backend/app/persona/insight_pipeline.py` | fresh 다시 도출 (R1) | T3 |
| `backend/app/persona/prompts/edit.v2.md` (신규) | 새 스키마·focus_id 지시 | T3 |
| `backend/app/routers/stage8.py` | `get_insights`에 `summary`·예전 판 `contexts`, `Chat.focus_id` | T2, T3 |
| `backend/tests/fixtures/llm/insight.derive.json`, `insight.derive.echo.json`, `insight.edit.json` | 새 필드 | T1, T3 |
| `backend/tests/persona/test_insights.py` | T1·T2 테스트 | T1, T2 |
| `backend/tests/persona/test_chat.py`, `test_api.py` | T2·T3 테스트 | T2, T3 |
| `frontend/src/lib/types.ts` | 새 필드·`InsightContextView`·`summary`·`focus_id` 타입 | T4 |
| `frontend/src/lib/api/insight.ts`, `components/persona/insightActions.ts` | `chat(target, message, focusId?)` | T4 |
| `frontend/src/components/persona/insightView.ts` (신규) + `insightView.test.ts` | 대체 규칙·라벨·막대·칩 | T4 |
| `frontend/src/components/persona/Radar.tsx`, `OpportunityBars.tsx`, `InsightFlow.tsx` (신규) | 차트·흐름 | T5 |
| `frontend/src/components/persona/InsightTopBar.tsx`, `InsightHeader.tsx`, `InsightChatBar.tsx`, `InsightConcept.tsx` (신규), `frontend/src/components/ChatPanel.tsx` | 상단·헤더·채팅 띠·컨셉 | T6 |
| `frontend/src/components/persona/InsightScreen.tsx`, `insight.css` (신규), `InsightScreen.qa.test.ts`, `insight.test.ts` | 조립·레이아웃·상태 | T7 |

의존 관계: T1 → T2 → T3 (같은 파일, 순차). T4 → T5, T6 → T7. 백엔드(T1~T3)와 프론트(T4~T7)는 파일이 겹치지 않아 병렬 가능. T5와 T6은 파일이 겹치지 않아 병렬 가능.

---

### Task 1: 도출 출력 스키마 확장과 공통 검사

**Files:**
- Modify: `backend/app/persona/insights.py` (`InsightItem`, `DeriveOut`, `derive()`의 검사·재시도 문구·프롬프트 경로)
- Create: `backend/app/persona/prompts/derive.v2.md`
- Modify (R2): `backend/app/persona/store.py:20-22` (`_concept_identity`)
- Modify: `backend/tests/fixtures/llm/insight.derive.json`, `insight.derive.echo.json`
- Test: `backend/tests/persona/test_insights.py`, `backend/tests/persona/test_store.py` (R2, 없으면 test_insights.py)

**Interfaces:**
- Produces:
  - `class FlowStep(BaseModel): context_id: Text; text: Text` (`text` 1~80자)
  - `InsightItem`에 `headline: Text`, `statements: list[Text]` (정확히 2), `hashtags: list[Text]` (2~4), `flow: list[FlowStep]` (min 1)
  - `def validate_items(items: list[dict], available: set[str], *, require_new: bool = True, previous: list[dict] | None = None) -> list[dict]` — 설계 2.2 규칙, 실패 시 `ValueError`, 정리한 사본 반환(hashtag `#`·공백 제거, headline 앞뒤 따옴표 `" “ ” '` 제거). `require_new=False`(채팅 수정)면 항목마다 새 필드 4개가 모두 있거나 모두 없어야 하고, `previous`에서 새 필드가 있던 같은 id가 새 필드를 잃으면 실패 (R4).
  - `class EditItem(InsightItem)`의 새 필드 4개를 `None` 허용 선택값으로 둔 수정용 모델, `class EditOut(BaseModel): items: list[EditItem]` (R4).

- [ ] **Step 1: 실패 테스트 작성** (`test_insights.py`)
  - `test_validate_ok`: 정상 항목 → 그대로 반환(정리 후).
  - `test_validate_statements_count`: statements 1개·3개 → `ValueError` (pydantic 단계에서 이미 막히면 `DeriveOut.model_validate`가 실패함을 단언).
  - `test_validate_flow_outside_context_ids`: flow에 그 인사이트 `context_ids` 밖 ID → `ValueError`.
  - `test_validate_flow_count`: `context_ids` 3개, flow 1개 → `ValueError`; flow 2·3개 → 통과; flow 중복 ID → `ValueError`.
  - `test_validate_flow_single_context`: `context_ids` 1개, flow 1개 → 통과.
  - `test_validate_length_caps` (R7): headline 30자 통과·31자 `ValueError`, statements 70자 통과·71자 `ValueError`(정리 후 길이 기준).
  - `test_validate_cleans_hashtag_and_quotes`: hashtags `['#심박', ' 수면 ']` → `['심박', '수면']`; headline `'“귀로 재는 컨디션”'` → `'귀로 재는 컨디션'`; 정리 후 빈 hashtag·중복 hashtag → `ValueError`.
  - `test_validate_edit_all_or_none` (R4): `require_new=False`에서 새 필드 4개 모두 없음 → 통과, 모두 있음 → 통과(규칙 검사), 일부만 있음 → `ValueError`.
  - `test_validate_edit_no_regression` (R4): `previous`에 새 필드가 있던 I1이 답에서 새 필드 없음 → `ValueError`.
  - `test_validate_keeps_existing_rules`: 개수 `INSIGHT_RANGE` 밖, 중복 id, 없는 Context ID, `context_ids` 중복 → 각각 `ValueError`.
  - `test_derive_retries_once_on_invalid_flow`: 첫 응답 flow가 밖 ID, 두 번째 정상 → 성공, 호출 2회, 두 번째 payload `retry` 문구에 "flow" 포함.
  - `test_derive_uses_v2_prompt`: 첫 호출 `instructions`에 `derive.v2.md` 내용(예: "headline")이 들어 있다.
  - `test_concept_outdated_on_statement_change` (R2): 컨셉이 있는 인사이트의 `statements`만 바뀐 새 판 → 그 컨셉 `outdated == True`. `hashtags`만 바뀐 새 판 → `outdated == False`.
  - `test_legacy_concept_not_outdated_by_new_keys` (R2, 회귀): 새 필드 없는 판 → 같은 내용의 새 판(새 필드 없음) 저장 시 컨셉 outdated 아님.
- [ ] **Step 2: RED 확인** — `backend/.venv/bin/python -m pytest backend/tests/persona/test_insights.py -q` → 새 테스트 FAIL.
- [ ] **Step 3: 구현** — 위 Interfaces. `derive()`의 인라인 검사를 `validate_items(candidates, contexts.keys())` 호출로 바꾸고 `ValueError`면 재시도. 재시도 문구: `'인사이트를 3~8개 생성하고 고유 ID와 입력에 있는 Context ID만 사용하세요. headline은 30자 이하, statements는 정확히 2개이며 각 70자 이하, hashtags는 2~4개, flow는 그 인사이트 context_ids 안에서 고르세요.'` (R7) `derive.v2.md`는 v1 전문 + 설계 3절 규칙 4개 + "headline·statements는 title·pain_point와 같은 내용을 짧게 다시 쓴 것"(R2). `_concept_identity` 키에 `headline`, `statements`, `flow` 추가(R2).
- [ ] **Step 4: fixture 갱신** — `insight.derive*.json` 각 항목에 `headline`, `statements`(2), `hashtags`(2), `flow`(그 항목 `context_ids` 각각 1개씩) 추가. 기존 테스트가 쓰는 값은 바꾸지 않는다.
- [ ] **Step 5: GREEN 확인** — 같은 명령 PASS, 이어서 `backend/.venv/bin/python -m pytest backend/tests/persona -q` PASS.
- [ ] **Step 6: 커밋** — `feat(insight): 도출 출력에 headline·statements·hashtags·flow와 공통 검사`

### Task 2: Context 보기 정보와 조회 요약

**Files:**
- Modify: `backend/app/persona/insights.py` (`context_view`, `context_axis`, `dominant_dim`, `summary`, `recompute`)
- Modify: `backend/app/routers/stage8.py:243-256` (`get_insights`)
- Test: `backend/tests/persona/test_insights.py`, `backend/tests/persona/test_api.py`

**Interfaces:**
- Consumes: T1의 `InsightItem`.
- Produces:
  - `def dominant_dim(context: ContextEvidence) -> str | None` — 지지 근거(`evidence`)만, `tags` 목록 집계, 동률 Sense→Feel→Think→Act→Relate→Outcome, 반환은 첫 글자 대문자(`'Think'`). 태그가 소문자로 저장돼 있다(실데이터 `think`).
  - `def context_axis(centroid: np.ndarray, axes: np.ndarray) -> str | None` — `radar({cid: centroid}, {cid: 1}, axes)['raw']` 최댓값 축, 동률 `RADAR_AXES` 순서, 전부 0이면 None.
  - `def context_view(package: Package | None, cards: dict | None, item: dict, axes_by_cid: dict[str, str | None] | None = None) -> list[dict]` — 설계 2.3 행(`context_id, short, persona_id, persona_name, context_name, odi, axis, dim, counter, pain_point`), 순서 = `item['context_ids']`. package None이면 `{'context_id', 'short'}` 외 필드 None/False.
  - `def summary(package: Package | None, items: list[dict]) -> dict` — `{'context_odi_mean': float | None, 'radar_mean': dict | None}`.
  - `recompute()`가 각 item에 `contexts`를 저장(축 포함). `GET`은 `contexts` 없는 item에 `context_view(..., axes_by_cid=None)`을 채우고 응답 최상위에 `summary`를 더한다.

- [ ] **Step 1: 실패 테스트 작성** (`test_insights.py`)
  - `test_dominant_dim_counts_support_only`: 지지 근거 tags `['think','act']`,`['act']`, 반례 근거 `['feel']×5` → `'Act'`.
  - `test_dominant_dim_tie_and_empty`: `['sense']`,`['feel']` → `'Sense'`; 근거 없음 → None.
  - `test_dominant_dim_ignores_non_list_tags` (F2): `tags`가 dict·None·문자열인 근거와 알 수 없는 차원 값은 건너뛴다. 전부 그러면 None.
  - `test_context_axis_max_and_zero`: 축 벡터와 같은 방향 centroid → 그 축; 영벡터 → None; 두 축 동률 → 앞 축.
  - `test_context_view_rows`: fixture package에서 행 필드·순서·`short`(`CL0-P0-C1` → `C1`)·`counter`(flags) 확인, `cards['personas'][persona_id]['card']['contexts'][i]['pain_points'][0]['text']`가 `pain_point`로, 그 키가 없는 예전 카드면 None (F1).
  - `test_recompute_stores_contexts_with_axis`: `recompute` 후 각 item `contexts[*].axis`가 `RADAR_AXES` 키 중 하나.
  - `test_summary_means`: Context ODI `[1.0, None, 3.0]` → `context_odi_mean == 2.0`; items radar raw 평균; items 없음 → 둘 다 None.
- [ ] **Step 2: 실패 테스트 작성** (`test_api.py`)
  - `test_get_insights_summary_and_legacy_contexts`: `contexts` 없는 예전 insights.json → 응답 item에 `contexts` 채워지고 `axis is None`, 최상위 `summary` 있음, 임베더 호출 0회(가짜 임베더 호출 수 단언).
  - `test_get_insights_enriches_history` (R6): history 판 항목(`contexts` 없음)도 응답에서 `contexts`가 채워지고, 임베더 호출 0회.
  - `test_get_insights_without_package`: package.json 없음 → 200, `contexts == [{'context_id': ..., 'short': ...}, ...]` 형태(나머지 None/False), `summary.context_odi_mean is None`.
- [ ] **Step 3: RED 확인** — `backend/.venv/bin/python -m pytest backend/tests/persona/test_insights.py backend/tests/persona/test_api.py -q` → 새 테스트 FAIL.
- [ ] **Step 4: 구현** — 위 Interfaces. `recompute`는 이미 계산하는 `centroids`와 `axes`로 `axes_by_cid`를 만든다. `get_insights`는 `load_package`의 `PackageMissing`을 잡아 None으로 넘긴다. 카드는 `store.read('cards')`.
- [ ] **Step 5: GREEN 확인** — 같은 명령 PASS, 이어서 `backend/.venv/bin/python -m pytest backend/tests -q` PASS.
- [ ] **Step 6: 커밋** — `feat(insight): Context 보기 정보와 조회 요약`

### Task 3: 채팅 수정 검사 통일과 focus_id

**Files:**
- Modify: `backend/app/persona/chat.py:33-90` (`edit`)
- Create: `backend/app/persona/prompts/edit.v2.md`
- Modify: `backend/app/routers/stage8.py` (`Chat` 모델에 `focus_id: Text | None = None`, `edit_insight` 전달)
- Modify: `backend/tests/fixtures/llm/insight.edit.json`
- Modify (R1): `backend/app/persona/insight_pipeline.py` (fresh 도출), `backend/app/routers/stage8.py` (`InsightRun.fresh`)
- Test: `backend/tests/persona/test_chat.py`, `backend/tests/persona/test_api.py`, `backend/tests/persona/test_insights.py` (R1)

**Interfaces:**
- Consumes: T1 `validate_items`, T2 `recompute`.
- Produces: `def edit(sid, version, target: str, message: str, *, focus_id: str | None = None, run_task=None) -> dict`. `focus_id`는 `target == 'insights'`이고 현재 판 id에 있을 때만 `payload['focus_id']`로 넣는다.
- Produces (R3): 대상 `insight:{id}` 지원. `_target('insight:I2') -> ('insights', 'I2', 'item')`처럼 문서 이름·id·모드를 돌려준다. `class ItemOut(BaseModel): item: EditItem` (R4). 이 대상이면 payload에 `current`(목록 전체, 맥락용)와 `item_id`를 넣고 `ItemOut`을 요구한다. 서버는 `item['id'] = item_id`로 고정해 그 위치에 교체한다. 존재하지 않는 id → `StoreError(400, 'validation')`. 되돌리기(`revert`)는 `insight:*` 대상을 `insights` 문서로 처리한다.

- [ ] **Step 1: 실패 테스트 작성** (`test_chat.py`)
  - `test_edit_attaches_context_sources` (R5): `insights`·`insight:I1` 대상 attachment JSON에 `contexts` 목록, 각 항목 `{context_id, context_name, pain_point}`, fixture 카드 페인포인트가 들어 있고 근거 없는 Context는 `pain_point: null`. `concept:` 대상에는 없음.
  - `test_edit_passes_focus_id`: `focus_id='I2'` → LLM attachment JSON에 `"focus_id": "I2"`.
  - `test_edit_ignores_unknown_focus_id`: `focus_id='nope'` → attachment에 `focus_id` 없음, 수정은 정상.
  - `test_edit_ignores_focus_for_concept`: `target='concept:I1'` → attachment에 `focus_id` 없음.
  - `test_edit_rejects_stale_flow`: LLM이 `context_ids`를 바꾸고 flow는 옛 ID → `{'ok': False, 'message': FAILURE_COPY}`, 판 번호 그대로.
  - `test_edit_uses_v2_prompt`: instructions에 `edit.v2.md` 내용(예: "focus_id").
  - `test_item_target_replaces_only_that_item` (R3): `target='insight:I2'`, LLM이 `{item: {...id:'I9'...}}` 답 → 새 판에서 I2 위치만 바뀌고 id는 'I2', I1·I3 항목은 이전 판과 dict 동일.
  - `test_item_target_unknown_id` (R3): `insight:nope` → 400 validation.
  - `test_item_target_invalid_item_fails` (R3): 답의 flow가 그 항목 context_ids 밖 → `FAILURE_COPY`, 판 그대로.
  - `test_item_target_revert` (R3): `revert('insight:I2', 1)` → insights 판 1로 되돌림.
  - `test_edit_legacy_list_stays_legacy` (R4): 현재 판이 예전 형식이고 LLM이 새 필드 없이 답하면 성공, 새 판도 예전 형식. 일부 필드만 채워 답하면 `FAILURE_COPY`.
- [ ] **Step 2: 실패 테스트 작성** (`test_api.py`) — `test_chat_accepts_focus_id`: `POST /insight/{sid}/chat {"target":"insights","message":"m","focus_id":"I1"}` → 200, `chat.edit`이 `focus_id='I1'`로 불림(monkeypatch); `focus_id` 없는 기존 본문도 200.
- [ ] **Step 2b: 실패 테스트 작성 (R1 다시 도출)**
  - `test_fresh_derive_creates_new_revision`: 판 1이 있을 때 `{"mode":"derive","fresh":true}` → derive 호출, 판 2 생성, 판 1은 history에 남아 되돌리기 가능.
  - `test_derive_without_fresh_still_skips`: 기존 동작(판 있으면 derive 안 함) 유지 — 회귀 보호.
  - `test_fresh_derive_clears_confirmed`: 확정 `['I1']` → fresh 도출 후 `insight.confirmed == []`.
  - `test_fresh_derive_outdates_concepts`: 컨셉이 있던 인사이트가 바뀌면 GET에서 그 컨셉 `outdated == True`.
- [ ] **Step 3: RED 확인** — `backend/.venv/bin/python -m pytest backend/tests/persona/test_chat.py backend/tests/persona/test_api.py backend/tests/persona/test_insights.py -q` → 새 테스트 FAIL.
- [ ] **Step 4: 구현** — `edit()`의 인사이트 인라인 검사를 `items = insights.validate_items(draft['items'], available, require_new=False, previous=current['items'])`로 바꾸고 결과를 `recompute`에 넘긴다. 출력 스키마는 `EditOut`/`ItemOut`(R4). `edit.v2.md`는 v1 전문 + 설계 3절·3.1 문장 두 개 + R2 규칙 문장 + R5 근거 규칙. Context 요약은 T2의 `context_view`와 같은 카드 경로(F1)로 만든다.
- [ ] **Step 5: fixture 갱신** — `insight.edit.json` 항목에 새 필드.
- [ ] **Step 6: GREEN 확인** — 같은 명령 PASS, 이어서 `backend/.venv/bin/python -m pytest backend/tests -q` PASS.
- [ ] **Step 7: 커밋** — `feat(insight): 채팅 수정 검사 통일과 focus_id`

### Task 4: 프론트 타입과 insightView

**Files:**
- Modify: `frontend/src/lib/types.ts:293-324`
- Modify: `frontend/src/lib/api/insight.ts` (변경 없음 확인: `chatInsight`는 body를 그대로 보냄), `frontend/src/components/persona/insightActions.ts`
- Create: `frontend/src/components/persona/insightView.ts`, `frontend/src/components/persona/insightView.test.ts`
- Test: `frontend/src/components/persona/insight.test.ts` (actions)

**Interfaces:**
- Produces:
  - 타입: `InsightFlowStep = {context_id: string; text: string}`; `InsightContextView = {context_id: string; short: string; persona_id?: string|null; persona_name?: string|null; context_name?: string|null; odi?: number|null; axis?: 'Computed'|'Connected'|'Shared'|null; dim?: string|null; counter?: boolean; pain_point?: string|null}`; `InsightItem`에 선택 `headline?`, `statements?`, `hashtags?`, `flow?`, `contexts?`; `InsightSummary = {context_odi_mean: number|null; radar_mean: Record<'Computed'|'Connected'|'Shared', number>|null}`; `InsightResponse.summary?: InsightSummary`; `InsightChatRequest.focus_id?: string`; `InsightRunRequest.fresh?: boolean` (R1). `InsightTarget = 'insights' | `insight:${string}` | `concept:${string}`` (R3).
  - `insightActions.chat(target, message, focusId?: string)` — `target === 'insights'`이고 `focusId`가 있으면 body에 `focus_id`. `insight:*` 대상은 body `{target, message}` 그대로(R3).
  - `export function toInsightView(item: InsightItem, summary?: InsightSummary | null): InsightView` with `InsightView = {headline: string; statements: string[]; hashtags: string[]; personas: string[]; flow: FlowCard[]; bars: BarRow[]; legacy: boolean; chips: string[]}`, `FlowCard = {contextId: string; label: string; text: string; dim: string | null; axis: InsightContextView['axis']; counter: boolean}`, `BarRow = {contextId: string; short: string; label: string; value: number | null}`.
  - `export function personaShortLabels(contexts: InsightContextView[]): Record<string, string>` (persona_id → 축약).
  - `export function radarMean(items: InsightItem[]): Record<'Computed'|'Connected'|'Shared', number> | null` (R6) — 축별 `radar.raw` 평균, 값 없는 항목 제외, 하나도 없으면 null.

- [ ] **Step 1: 실패 테스트 작성** (`insightView.test.ts`)
  - `new fields pass through`: 새 필드 있는 item → headline·statements·hashtags 그대로, `legacy === false`.
  - `legacy fallback`: headline·statements·flow 없음 → `headline === title`, `statements === [pain_point]`, `hashtags === []`, flow = `context_ids` 순서, 문장 `contexts[].pain_point` → 없으면 `context_name` → 없으면 `short`, `legacy === true`.
  - `persona short label`: "귀로 건강 재는 러너" → "러너"; label `러너-C1`.
  - `persona short label collision`: "귀로 재는 러너"와 "새벽 러너" → 둘 다 전체 이름.
  - `personas deduped in context order`.
  - `bars keep null distinct from zero`: odi `[null, 0, 2.5]` → values `[null, 0, 2.5]`.
  - `radarMean` (R6): 항목 2개 raw 평균, raw 없는 항목 제외, 전부 없으면 null.
  - `chips`: flow 2개 이상 → `['이 인사이트 문장을 더 짧게 다시 써줘', '흐름에서 러너-C1과 베개-C9 순서를 바꿔줘']`(첫·마지막 카드 label).
  - `single context hides second chip`: flow 1개 → chips 길이 1.
  - `dim null shows 근거 부족`: `FlowCard.dim === null`은 그대로 두고, 표시 문자열 함수 `dimLabel(null) === '근거 부족'`.
- [ ] **Step 2: 실패 테스트 작성** (`insight.test.ts`) — `chat sends focus_id only for insights target`: `actions.chat('insights','m','I2')` → body `{target:'insights',message:'m',focus_id:'I2'}`; `actions.chat('concept:I2','m','I2')` → body에 `focus_id` 없음.
- [ ] **Step 3: RED 확인** — `npm --prefix frontend test -- src/components/persona/insightView.test.ts src/components/persona/insight.test.ts` → FAIL.
- [ ] **Step 4: 구현** — 위 Interfaces. `dimLabel(dim: string | null): string`도 `insightView.ts`에.
- [ ] **Step 5: GREEN 확인** — 같은 명령 PASS, `npm --prefix frontend run lint` PASS.
- [ ] **Step 6: 커밋** — `feat(insight): 프론트 타입과 insightView`

### Task 5: 레이더·Opportunity Score·흐름 카드

**Files:**
- Modify: `frontend/src/components/persona/Radar.tsx` (재작성)
- Modify: `frontend/src/components/persona/OpportunityBars.tsx` (재작성)
- Create: `frontend/src/components/persona/InsightFlow.tsx`
- Test: `frontend/src/components/persona/insightCharts.test.ts` (신규)

**Interfaces:**
- Consumes: T4 `BarRow`, `FlowCard`, `dimLabel`, `RadarValues`(기존 타입 유지).
- Produces:
  - `Radar({values, mean, label}: {values: RadarValues; mean: Record<'Computed'|'Connected'|'Shared', number> | null; label: string})` — 높이 240px 영역 안 SVG.
  - `OpportunityBars({rows, mean}: {rows: BarRow[]; mean: number | null})`.
  - `InsightFlow({cards}: {cards: FlowCard[]})`.

- [ ] **Step 1: 실패 테스트 작성** (`renderToStaticMarkup`)
  - `radar draws mean dashed polygon only when mean given`: mean 있음 → `stroke-dasharray` polygon 1개, 범례 "평균(전체 인사이트)"; mean null → 둘 다 없음.
  - `radar empty state`: 세 축 raw 모두 null → "경험 차원 값이 없습니다".
  - `radar aria label has raw and percentile`.
  - `bars null and zero`: null → "값 없음" 텍스트 + 막대 요소 없음; 0 → 높이 0 막대 존재.
  - `bars mean line`: mean 있으면 "평균 x.x"(소수 1자리), null이면 없음.
  - `bars all null`: "이 인사이트의 Context에 ODI 값이 없습니다", 축 없음.
  - `flow ordered list with arrows`: `<ol aria-label="Context 흐름">`, 카드 사이 `→` (n-1개), 카드 1개면 화살표 0개.
  - `counter card`: counter true → 텍스트 "반례", 클래스 `insight-flow-card--counter`.
  - `axis badge hidden when null`, `dim null shows 근거 부족`.
  - `no hardcoded colors`: 세 컴포넌트 소스 파일에 `#[0-9a-fA-F]{3,6}` 없음(`readFileSync`).
- [ ] **Step 2: RED 확인** — `npm --prefix frontend test -- src/components/persona/insightCharts.test.ts` → FAIL.
- [ ] **Step 3: 구현** — 설계 4절 표, 5.1 토큰, 6.1 상태. 막대 라벨 2줄(`short` / `label`)은 HTML로 그려 SVG 텍스트 겹침을 피한다(PR #34 `OpportunityBars` 그리드 방식 재사용).
- [ ] **Step 4: GREEN 확인** — 같은 명령 PASS.
- [ ] **Step 5: 커밋** — `feat(insight): 레이더·기회 막대·흐름 카드`

### Task 6: 상단 바·헤더·채팅 띠·컨셉

**Files:**
- Create: `frontend/src/components/persona/InsightTopBar.tsx`, `InsightHeader.tsx`, `InsightChatBar.tsx`, `InsightConcept.tsx`
- Modify: `frontend/src/components/ChatPanel.tsx` (선택 prop `suggestions?: string[]`)
- Test: `frontend/src/components/persona/insightParts.test.ts` (신규)

**Interfaces:**
- Consumes: T4 `InsightView`.
- Produces:
  - `InsightTopBar({count, index, onPrev, onNext, confirmed, onToggleConfirm, confirmDisabled, onDerive, deriveDisabled})` — `index`는 0부터. count 0이면 넘김·확정 숨기고 `인사이트 도출` 버튼.
  - `InsightHeader({view, index, knownBadge, onRederive, rederiveDisabled})` (R1).
  - `InsightChatBar({target, onTarget, conceptAvailable, focusLabel, chips, disabled, onSend, historyCount, revisions})` — `revisions`는 기존 `RevisionList` props 묶음.
  - `ConceptDetail` 이동: `InsightConcept.tsx`에서 `export function ConceptDetail` (기존 코드 그대로) + `export function InsightConcept({concept, onCreate, disabled})`.
  - `ChatPanel`의 `suggestions` 칩 클릭 → 입력값을 그 문장으로, 입력창 포커스.

- [ ] **Step 1: 실패 테스트 작성**
  - `pager group and boundaries`: `role="group" aria-label="인사이트 넘기기"`, index 0이면 "이전 인사이트" disabled, 마지막이면 "다음 인사이트" disabled, `aria-live="polite"`에 "Insight 2 / 5".
  - `pager arrow keys only on group`: 그룹의 `onKeyDown`에 `ArrowRight` → `onNext` 1회; 문서 전역 리스너를 등록하지 않음(`InsightTopBar.tsx` 소스에 `addEventListener` 없음).
  - `confirm toggle`: `aria-pressed`, 문구 "확정됨"/"확정하기", disabled 반영.
  - `empty list shows derive button`.
  - `header statements clamp` (R7): 문장 요소에 클래스 `insight-clamp-2`와 전체 문장 `title` 속성.
  - `header renders quote, numbered statements, hashtags`: “headline”, `<ol>` 2항목, `#심박`; hashtags 빈 배열 → 태그 줄 없음; personas 빈 배열 → "기여 페르소나" 줄 없음.
  - `legacy notice`: `legacy` → 설계 4.1 한 줄 + `<details>` "자세히" 안 초기화 문장.
  - `legacy notice rederive` (R1): 예전 판 안내 옆 "다시 도출" 버튼, 누르면 확인 대화상자 문구 "다시 도출하면 확정과 컨셉이 초기화됩니다. 이전 판은 판 목록에서 되돌릴 수 있습니다.", 확인 시에만 `onRederive` 호출, 읽기 전용·처리 중 비활성.
  - `chat bar focus label` (R3): target `insight:I2` → "Insight 2에 대해 수정 요청"; `insights` → "인사이트 목록 전체 수정"; `concept:I2` → "선택 컨셉 수정". 대상 선택 옵션 3개(현재 인사이트 / 인사이트 목록 / 선택 컨셉), 컨셉이 없으면 셋째 비활성.
  - `chat bar history zero disabled`: historyCount 0 → "대화 기록 0" disabled.
  - `chat panel suggestions optional`: `suggestions` 없이 렌더하면 칩 없음(다른 화면 회귀 방지), 있으면 버튼 2개.
  - `touch targets`: 넘김·확정·칩·대화 기록 버튼에 클래스 `insight-hit`(44px 규칙은 T7 CSS).
- [ ] **Step 2: RED 확인** — `npm --prefix frontend test -- src/components/persona/insightParts.test.ts` → FAIL.
- [ ] **Step 3: 구현** — 설계 4절 표, 5절 키보드·터치, 5.1 토큰, 3.1 대상 표시, 4.1 안내 문구.
- [ ] **Step 4: GREEN 확인** — 같은 명령 PASS, `npm --prefix frontend test` 전체 PASS(ChatPanel 회귀).
- [ ] **Step 5: 커밋** — `feat(insight): 상단 바·헤더·채팅 띠·컨셉 컴포넌트`

### Task 7: 인사이트 화면 조립

**Files:**
- Modify: `frontend/src/components/persona/InsightScreen.tsx` (데이터·폴링·mutate 유지, 그리기 교체)
- Create: `frontend/src/components/persona/insight.css`
- Modify: `frontend/src/components/persona/InsightScreen.qa.test.ts`, `insight.test.ts` (깨지는 기존 테스트를 새 구조에 맞춤, 단언 의미는 유지)
- Test: `frontend/src/components/persona/InsightScreen.qa.test.ts`

**Interfaces:**
- Consumes: T4~T6 전부.
- Produces: 화면 동작 — 현재 인사이트 index 상태, 선택 초기값(설계 6절), 사라진 인사이트 → 첫 인사이트, 미리보기 판에서 넘김 가능·확정/채팅 비활성, 채팅 `focus_id` 전달.

- [ ] **Step 1: 실패 테스트 작성** (`InsightScreen.qa.test.ts`)
  - `renders one insight at a time`: items 3개 → `InsightHeader` 1개, TopBar index는 `bars.targets[0]` 위치.
  - `selected insight removed falls back to first`.
  - `preview disables confirm and chat but keeps pager`.
  - `preview uses viewed revision radar mean` (R6): 미리보기 중 Radar `mean` prop이 `radarMean(viewed.items)`이고 현재 판 summary 값이 아니다.
  - `rederive starts fresh run` (R1): `onRederive` → `api.startInsight(sid, {mode:'derive', fresh:true}, version)`, pending 상태 진입.
  - `chat default target is current insight` (R3): 기본 대상 `insight:<현재 id>`, `›`로 넘기면 대상도 새 현재 id로 바뀐다(대상이 `insight:*`일 때만). `onSend` → `actions.chat('insight:I2', m)`.
  - `list target sends focus id`: 대상 `insights`일 때 `actions.chat('insights', m, 현재 id)`.
  - 기존 `QA-F2 concept failure`·`missing ODI distinct from zero` 테스트를 새 컴포넌트(`OpportunityBars rows`) 기준으로 옮겨 유지.
  - `css uses tokens only`: `insight.css`에 hex 없음, `.insight-hit`에 `min-width:44px; min-height:44px`, `.insight-charts` 높이 240px, `.insight-clamp-2`에 `-webkit-line-clamp:2` (R7).
- [ ] **Step 2: RED 확인** — `npm --prefix frontend test -- src/components/persona/InsightScreen.qa.test.ts` → FAIL.
- [ ] **Step 3: 구현** — 설계 5.0 레이아웃(바깥 `ds-card` 하나, 5.0.1), 반응형 3단계(≥1280, 768~1279, ≤767), 6·6.1 상태. 컨셉은 패널 밖 "컨셉" 구간.
- [ ] **Step 4: GREEN 확인** — `npm --prefix frontend test` PASS, `npm --prefix frontend run lint` PASS, `npm --prefix frontend run build` PASS.
- [ ] **Step 5: 커밋** — `feat(insight): 인사이트 화면을 한 개씩 넘기는 구조로 조립`

---

## QA 계획

### 환경

- worktree에서 백엔드 가상환경: `cd backend && /opt/homebrew/bin/python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt -r requirements-dev.txt -c constraints.txt`. 프론트: `npm --prefix frontend ci`.
- QA 데이터는 **복사본**: `QA_DATA=/private/tmp/dcx-qa-insight`에 `~/srv/dcx-agent/shared/data`에서 `sessions/s8b25bf1f185143118303600ee0ec5293`(세라젬_261012_sk, v2에 예전 형식 인사이트 있음), `llmcache`, `.author_salt`를 복사한다.
- 서버 시작:
  - 백엔드: `cd backend && LOCAL_DATA_DIR=$QA_DATA AUTHOR_SALT_PATH=$QA_DATA/.author_salt LABEL_GPT_BACKEND=codex_exec .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8411`
  - 프론트: `cd frontend && NEXT_PUBLIC_API_URL=http://127.0.0.1:8411 npx next dev -p 3411`
- **테스트 URL:** `http://localhost:3411/pipeline/insights` (세션 세라젬_261012_sk, v2 선택)
- 새 형식 확인은 복사본에서 인사이트 다시 도출(`인사이트 도출` 또는 `POST /insight/{sid}/run?version=v2 {"mode":"derive"}`). 이 세션은 반례 Context가 0개라 반례 카드는 단위 테스트(T5)로 확인한다.

### 브라우저 시나리오 (gstack `qa-only`)

| # | 시나리오 | 기대 결과 | 수용 기준 |
|---|---|---|---|
| Q1 | 예전 형식 인사이트(다시 도출 전) 열기 | 한 개씩 표시, 제목·pain_point 대체, 예전 판 안내 한 줄 + 자세히, 흐름 카드 축 배지 없음, 깨짐 없음 | 기획 8-9, 설계 4.1 |
| Q2 | 복사본에서 다시 도출 후 열기 | 따옴표 제목, 번호 문장 2개, 해시태그, 기여 페르소나, 흐름 카드에 차원·축 배지 | 기획 8-1·3·6 |
| Q3 | 1280×800 첫 화면 (흐름 카드 4개 이하 인사이트) | 스크롤 없이 상단 바~흐름 카드 하단까지 보임. 5개 이상 인사이트는 첫 줄까지 보이고 둘째 줄은 아래 | 설계 5.0 (1A), R7 |
| Q4 | 레이더·Opportunity Score | 평균 점선, Context별 막대 + 세션 평균선, 라벨 겹침 없음 | 기획 8-4·5 |
| Q5 | `›` 클릭, 넘김 그룹 포커스 후 → 키, 본문 포커스에서 → 키 | 앞 둘은 다음 인사이트, 셋째는 넘기지 않음. 처음·끝 비활성 | 기획 8-2, 설계 8A |
| Q6 | 칩 ① 누르고 전송 | 입력 채워짐, 입력창 위 "Insight n에 대해 수정 요청", 수정 후 같은 인사이트 유지, 대화 기록 수 증가 | 기획 8-7, 설계 4A·10A |
| Q7 | 확정 토글, 컨셉 만들기 | 확정 저장(새로고침 후 유지), 컨셉 영역 동작 | 기획 8-8 |
| Q8 | 768px, 375px | 768: 레이더·막대 2열, 흐름 2개씩. 375: 1열, `↓`. 버튼 44px | 기획 8-10, 설계 5 |
| Q9 | 판 목록에서 이전 판 보기 | 넘김 가능, 확정·채팅 비활성, "현재 판으로" 복귀 | 설계 6 |

### 검증 명령 (하네스 `verificationCommands`)

- `backend/.venv/bin/python -m pytest backend/tests -q`
- `npm --prefix frontend run lint`
- `npm --prefix frontend run build`
- `npm --prefix frontend test`

## 되돌리기

- 기능 브랜치를 merge하지 않으면 운영 영향이 없다.
- merge 후 되돌릴 때는 `git revert <merge-commit>`. 조회는 저장된 dict를 그대로 돌려주고 이전 화면은 모르는 필드를 무시하므로 새 필드가 있는 판도 열린다. 이전 코드의 `InsightItem`은 `extra='ignore'`라, 되돌린 뒤 채팅 수정을 하면 새 필드(headline 등)는 다음 판에서 빠질 뿐 오류는 없다. v1 프롬프트가 남아 있어 이전 코드의 도출·수정도 그대로 동작한다.
- 운영 배포는 이 실행 범위가 아니며, 사용자가 따로 요청할 때만 한다.

## Self-Review

- 기획 수용 기준 1~11 → T1(1), T7·T6(2), T4·T6(3), T5(4·5·6), T6·T3(7), T6·T7(8), T4·T7(9), T7(10), 전 Task(11).
- 설계 결정 1A(T7), 2A(T5·T6·T7), 3A(T6), 4A(T3·T4·T6·T7), 5A(T7), 6A(T6), 7A(T5·T7), 8A(T6·T7), 9A(T5), 10A(T4).
- 이름 일관성: `validate_items`, `context_view`, `context_axis`, `dominant_dim`, `summary`, `toInsightView`, `personaShortLabels`, `dimLabel`, `FlowCard`, `BarRow`, `InsightContextView`, `InsightSummary` — 정의 Task와 사용 Task가 같은 이름.

---

# Eng Review (plan-eng-review) — 대상: docs/development/stage8-insight-redesign/03-plan.md

## Scope record

feature answers: 제안된 기능 삭감 없음(모든 기능이 승인된 기획 수용 기준·디자인 결정에 묶임); structure: A Original arrangement (D1, 사용자 답 "Original arrangement (recommended)"); accepted scope: 03-plan.md T1~T7 파일 구성 그대로; pending remedies: none. Scope Challenge 결과: scope accepted as-is.

## Decision ledger

### F1: 사실 정정 — 카드에서 Context 페인포인트를 읽는 경로
Finding: Q1, P2, confidence 9/10, 03-plan.md T2 Interfaces ("카드 `pain_points[0].text`"), reviewer: plan-eng-review (Claude)
Plan baseline: T2 `context_view`가 "카드 `pain_points[0].text`"를 `pain_point`로 쓴다.
Runtime evidence: 실데이터 `persona/cards.json` 구조는 `{"personas": {"CL0-P0": {"status", "card": {"contexts": [{"context_id", "state", ..., "pain_points"?}]}}}}`. PR #34 이전 카드에는 `pain_points` 키가 없다(s8b25 v2 확인).
Correction: 경로를 `cards['personas'][persona_id]['card']['contexts'][i]['pain_points'][0]['text']`로 명시하고, 키가 없거나 빈 목록이면 None. 동작 변경 없음 → 질문 없음.

### F2: 승인된 동작의 필요한 증명 — tags가 리스트가 아닌 근거
Finding: Q2, P2, confidence 8/10, `backend/app/persona/package.py:34` (`tags: Any`), reviewer: plan-eng-review (Claude)
Plan baseline: 설계 6.1 (2A 승인) "`dim` null → '근거 부족'".
Runtime evidence: 실데이터 태그는 소문자 문자열 리스트(`evidence/assemble.py:244`), 계약 타입은 `Any`.
Accepted scope (carried from 2A): `dominant_dim`은 리스트가 아닌 `tags`를 건너뛰고, 알려진 6개 차원 외 값은 무시한다. 테스트 `test_dominant_dim_ignores_non_list_tags` 추가. 새 동작이 아니라 승인된 null 처리의 증명이라 질문 없음.

### R1: 예전 판을 새 형식으로 바꾸는 경로 (다시 도출)
Finding: OV1, P1, confidence 9/10, `backend/app/persona/insight_pipeline.py:109` (`if not current.get('revision'): derive(...)`), reviewer: Codex outside voice (확인: Claude)
Plan baseline: 설계 4.1 "다시 도출 버튼은 이번 범위에 넣지 않는다"(제품·설계 승인), 안내 문구는 "다시 도출하면 제목·문장·흐름이 채워집니다"(3A).
Runtime evidence: 판이 있으면 derive 요청이 아무 일도 하지 않는다. 인사이트 도출 버튼도 목록이 비었을 때만 보인다. 기존 세션은 새 형식을 얻을 방법이 없다.
Comparison grid:
| 항목 | 현재 | A | B |
|---|---|---|---|
| 다시 도출 API | 없음(판 있으면 무시) | `{"mode":"derive","fresh":true}`면 판이 있어도 도출해 **새 판**으로 저장(되돌리기 가능), 확정 목록 비움, 컨셉은 identity 비교로 outdated | 없음 |
| 화면 | 안내만 | 예전 판 안내 옆 "다시 도출" 버튼 + 확인 대화상자("다시 도출하면 확정과 컨셉이 초기화됩니다. 이전 판은 판 목록에서 되돌릴 수 있습니다.") | 안내 문구를 "예전 방식으로 만든 인사이트입니다."로만 줄임(약속 삭제) |
| QA Q2 | 불가 | 화면에서 다시 도출로 확인 | 복사본에서 insights.json 삭제 후 도출 |
Question D2: 예전 판을 새 형식으로 바꾸는 "다시 도출" 경로를 만들까요? (권장 A)
Header: D2 다시 도출
Options:
A) 다시 도출 경로 추가 (recommended) — fresh 도출을 새 판으로 저장, 확정 비움, 확인 대화상자. human ~4h / CC ~20min
B) 경로 없이 약속 문구 삭제 — 기존 세션은 예전 형식 유지
State: approved
Actual answer: A) 다시 도출 경로 추가 (D2 답)
Accepted scope: `InsightRun.fresh: bool = False`; mode derive + fresh면 판이 있어도 도출해 새 판으로 저장(by='generate'), 세션 `insight.confirmed`/`confirmed_ids`의 현재 판 id를 비움, 컨셉은 기존 identity 비교로 outdated. 화면: 예전 판 안내 옆 "다시 도출" 버튼 + 확인 대화상자 문구 "다시 도출하면 확정과 컨셉이 초기화됩니다. 이전 판은 판 목록에서 되돌릴 수 있습니다." 계획 T3·T6·T7에 반영.
History: 설계 4.1 승인값 "버튼 범위 밖"을 새 증거(OV1)로 다시 엶. D2에서 A 승인.

### R2: 새 문구가 바뀌어도 컨셉이 '최신'으로 남는 문제
Finding: OV2, P1, confidence 9/10, `backend/app/persona/store.py:22` (`for key in ('id', 'title', 'pain_point', 'context_ids')`), `backend/app/known/store.py:224` (`title=row['title'], painPoint=row['pain_point']`), reviewer: Codex outside voice (확인: Claude)
Plan baseline: 계획에 컨셉 무효화·Known Insight 내보내기 변경 없음.
Runtime evidence: 컨셉 outdated 판단은 이전 판과 새 판의 위 4개 키만 비교한다(store.py:106, 130). 채팅으로 statements·headline·flow만 바꾸면 컨셉이 최신으로 남는다. Known 내보내기는 title/pain_point를 쓰며, 이 둘은 계속 저장되고 의미가 있다(화면 대체 규칙의 원천).
Comparison grid:
| 항목 | 현재 | A | B |
|---|---|---|---|
| 컨셉 identity 키 | id,title,pain_point,context_ids | + headline, statements, flow (hashtags 제외) | 그대로 |
| title·pain_point 위상 | 저장됨 | 정본 유지. 프롬프트에 "headline·statements는 title·pain_point와 같은 내용을 짧게 다시 쓴 것" 규칙 | 같음 |
| Known 내보내기 | title/pain_point | 그대로(정본) | 그대로 |
| 예전 판 영향 | — | 예전 판끼리는 새 키가 둘 다 None이라 기존 컨셉이 outdated 되지 않음 | 없음 |
Question D3: 새 문구(headline·statements·flow)가 바뀌면 컨셉을 '다시 만들어야 함'으로 표시할까요? (권장 A)
Header: D3 컨셉 무효화
Options:
A) identity에 headline·statements·flow 추가 (recommended) — title·pain_point는 정본, 내보내기 그대로. human ~1h / CC ~5min
B) 그대로 — 새 문구만 바꾸면 컨셉 최신 유지
State: approved
Actual answer: A) identity에 새 문구 추가 (D3 답)
Accepted scope: `backend/app/persona/store.py` `_concept_identity` 키에 `headline`, `statements`, `flow` 추가(hashtags 제외). title·pain_point는 정본, Known 내보내기 변경 없음. `derive.v2.md`·`edit.v2.md`에 "headline·statements는 title·pain_point와 같은 내용을 짧게 다시 쓴 것" 규칙. 계획 T1에 반영.
History: D3에서 A 승인.

### R3: '이 인사이트' 수정이 다른 인사이트를 바꾸지 못하게 하는 방식
Finding: OV4, P1, confidence 9/10, `backend/app/persona/chat.py:65-72` (인사이트 목록 전체를 LLM 답으로 교체, 개수·ID·Context만 검사), reviewer: Codex outside voice (확인: Claude)
Plan baseline: 설계 3.1 (4A 승인) "채팅 요청에 `focus_id`, 입력창 위 'Insight n에 대해 수정 요청' 표시". 승인된 결과는 "채팅이 현재 인사이트를 안다"이고, 메커니즘은 프롬프트 힌트.
Runtime evidence: LLM이 목록 전체를 돌려주므로 프롬프트를 어기면 다른 인사이트가 바뀌거나 사라져도 막을 장치가 없다.
Comparison grid:
| 항목 | 현재 계획 | A | B |
|---|---|---|---|
| 채팅 대상 | 인사이트 목록 / 선택 컨셉 (+focus_id 힌트) | **현재 인사이트**(기본, `insight:{id}`) / 인사이트 목록 / 선택 컨셉 | 그대로 |
| 현재 인사이트 수정 | 목록 전체 교체 | LLM은 그 항목 하나만 답하고, 서버가 id 고정으로 그 항목만 바꿔 끼움. 다른 항목은 바이트 그대로 | 목록 전체 교체 |
| 목록 단위 작업(묶기·나누기) | 가능 | "인사이트 목록" 대상으로 가능(지금 방식, focus_id 힌트 유지) | 가능 |
| 입력창 위 표시 | "Insight n에 대해 수정 요청" | 같음(대상이 현재 인사이트일 때). 목록이면 "인사이트 목록 전체 수정" | 같음 |
| 4A 결과 | — | 유지(채팅이 현재 인사이트를 앎, 더 강하게 보장) | 유지(프롬프트만) |
Question D4: '이 인사이트' 수정을 서버가 그 인사이트만 바꾸도록 막을까요? (권장 A)
Header: D4 수정 범위
Options:
A) '현재 인사이트' 대상 추가 (recommended) — 기본 대상, LLM은 한 항목만 답하고 서버가 그 항목만 교체. 목록 작업은 '인사이트 목록' 대상. human ~4h / CC ~20min
B) 지금 계획대로 focus_id 힌트만
State: approved
Actual answer: A) '현재 인사이트' 대상 추가 (D4 답)
Accepted scope: 채팅 대상 `insight:{id}` 추가(화면 기본값 = 현재 인사이트). 이 대상이면 LLM 출력 스키마 `ItemOut{item: InsightItem}`, 서버가 `item.id`를 대상 id로 고정해 그 항목만 바꿔 끼운 뒤 `validate_items`(목록 전체)와 `recompute`. 다른 항목은 바이트 그대로. 저장·되돌리기·판 목록은 `insights` 문서를 공유. `insights` 대상(목록 작업)은 기존 방식 + focus_id 힌트 유지. 화면 대상 선택: 현재 인사이트 / 인사이트 목록 / 선택 컨셉. 계획 T3·T4·T6·T7에 반영.
History: D4에서 A 승인. 설계 4A의 결과(채팅이 현재 인사이트를 앎)는 유지되고 보장이 강해짐.

### R4: 채팅 수정 결과에서 새 필드를 필수로 할지
Finding: OV3(일부), P1, confidence 8/10, 03-plan.md T3 `test_edit_legacy_list_gets_new_fields`("LLM이 새 필드를 빼고 답하면 FAILURE_COPY"), reviewer: Codex outside voice (확인: Claude)
Plan baseline: T3 — 채팅 수정도 `DeriveOut`(새 필드 필수)을 쓴다. 예전 형식 목록을 고치면 모든 항목이 새 필드를 얻어야 성공.
Runtime evidence: 예전 판 항목에는 flow 문장을 쓸 근거가 수정 입력에 없다(chat.py:48, R5 참고). R1로 "다시 도출" 경로가 생겨 채팅이 형식 전환을 맡을 필요가 없어졌다.
Comparison grid:
| 항목 | 현재 계획 | A | B |
|---|---|---|---|
| 도출(derive) 출력 | 새 필드 필수 | 필수(그대로) | 필수 |
| 채팅 수정 출력 | 새 필드 필수 | 항목마다 "새 필드 4개 모두 있음 또는 모두 없음". 있으면 T1 규칙 검사, 없으면 예전 형식으로 저장. 이전 판에서 새 필드가 있던 항목이 답에서 빠지면 실패(퇴보 금지) | 필수 |
| 예전 판 채팅 | 모든 항목 새 필드 생성 요구 → 실패 위험 | 예전 형식 그대로 고칠 수 있음, 새 형식은 다시 도출(R1)로 | 실패 위험 유지 |
Question D5: 채팅 수정 결과에서 새 필드를 '모두 있음 또는 모두 없음'으로 허용할까요? (권장 A)
Header: D5 수정 필드
Options:
A) 수정은 전부 있음/전부 없음 허용 (recommended) — 예전 항목은 예전 형식으로 고치고, 새 형식이던 항목은 새 필드 유지 필수. human ~1h / CC ~10min
B) 지금 계획대로 수정에도 필수
State: approved
Actual answer: A) 전부 있음/전부 없음 허용 (D5 답)
Accepted scope: 도출은 새 필드 필수(그대로). 채팅 수정 출력 스키마 `EditItem`(새 필드 4개 선택)·`EditOut`·`ItemOut.item: EditItem`. `validate_items(items, available, *, require_new: bool = True, previous: list[dict] | None = None)` — `require_new=False`면 항목마다 4개 모두 있음(→ T1 규칙 검사) 또는 모두 없음만 허용, `previous`에서 새 필드가 있던 같은 id 항목이 답에서 새 필드를 잃으면 `ValueError`. 계획 T1·T3에 반영. `test_edit_legacy_list_gets_new_fields`는 이 규칙으로 대체.
History: D5에서 A 승인.

### R5: 인사이트 채팅 수정에 Context 근거 요약을 넘길지
Finding: OV3, P1, confidence 9/10, `backend/app/persona/chat.py:48-56` (`payload = dict(current=current, message=message, target=target)`, 근거는 `concept:` 대상에만 첨부), reviewer: Codex outside voice (확인: Claude)
Plan baseline: 계획 T3 — 인사이트 수정 payload는 현재 판·메시지·대상(+focus_id/item_id)만.
Runtime evidence: 새 형식 항목에서 "C9를 흐름에 넣어줘"처럼 Context를 바꾸면 LLM은 그 Context의 페인포인트를 모른 채 흐름 문장을 써야 한다. 도출(derive)은 카드 전체를 받는다.
Comparison grid:
| 항목 | 현재 계획 | A | B |
|---|---|---|---|
| 인사이트 수정 payload | current, message, target | + `contexts: [{context_id, context_name, pain_point}]` (근거 묶음 전체 Context, 카드 페인포인트 첫 문장, 없으면 null) | 그대로 |
| 크기 | — | 실데이터 114개 × 짧은 문장 (수 KB) | — |
| 프롬프트 | — | edit.v2에 "flow 문장은 contexts의 pain_point·context_name에 근거해 쓰고 없는 내용을 만들지 마세요" | — |
| 테스트 | — | attachment JSON에 `contexts` 존재·필드 단언 | — |
Question D6: 인사이트 채팅 수정에 Context 근거 요약을 함께 넘길까요? (권장 A)
Header: D6 수정 근거
Options:
A) Context 요약 첨부 (recommended) — 전체 Context의 이름·대표 페인포인트, 프롬프트 근거 규칙. human ~1h / CC ~10min
B) 그대로 — 현재 판만 보고 수정
State: approved
Actual answer: A) Context 요약 첨부 (D6 답)
Accepted scope: `insights`·`insight:*` 대상 수정 payload에 `contexts: [{context_id, context_name, pain_point}]`(근거 묶음 전체 Context, 카드 페인포인트 첫 문장(F1 경로) 또는 null). 근거 묶음이 없으면 `contexts: []`. `edit.v2.md`에 "flow 문장은 contexts의 pain_point·context_name에 근거해 쓰고 없는 내용을 만들지 마세요". 계획 T3에 반영.
History: D6에서 A 승인.

### R6: 이전 판 미리보기의 데이터
Finding: OV5, P2, confidence 9/10, `frontend/src/components/persona/InsightScreen.tsx:84` (`const insightItems = target === 'insights' && Array.isArray(viewed?.items) ? viewed.items ...`), reviewer: Codex outside voice (확인: Claude)
Plan baseline: 설계 6 "판 미리보기: 미리보기 판의 인사이트로 넘김이 동작하고 확정·채팅 비활성". 계획 T2는 현재 판 항목만 `contexts`를 채우고 `summary`는 현재 판 기준.
Runtime evidence: 미리보기는 `history[*].items`를 그린다. 그 항목에는 `contexts`가 없을 수 있고(예전 판·예전 계산), 레이더 평균은 현재 판 기준이라 미리보기 판과 맞지 않는다.
Comparison grid:
| 항목 | 현재 계획 | A | B |
|---|---|---|---|
| history 항목 `contexts` | 없음 | GET이 history 각 판 항목에도 `context_view`로 채움(임베딩 없음, 축은 저장값 있으면 유지) | 없음 |
| 미리보기 레이더 평균 | 현재 판 summary | 프론트가 보고 있는 판 항목의 `radar.raw`로 축별 평균 계산(`insightView.radarMean(items)`) | 차트 숨김 |
| 미리보기 화면 | 정의 없음 | 현재 판과 같은 화면 | 헤더·흐름 문구만, 차트 자리 "이전 판 미리보기에서는 차트를 보여 주지 않습니다" |
| context_odi_mean | 현재 근거 묶음 | 같음(세션 단위 값) | — |
Question D7: 이전 판 미리보기에도 Context 정보와 그 판 기준 평균을 채울까요? (권장 A)
Header: D7 미리보기
Options:
A) history도 채우고 평균은 보고 있는 판 기준 (recommended) — 미리보기도 현재 판과 같은 화면. human ~2h / CC ~10min
B) 미리보기는 문구만, 차트 숨김
State: approved
Actual answer: A) history도 채움, 판 기준 평균 (D7 답)
Accepted scope: GET이 `insights.history[*].items` 중 `contexts` 없는 항목에도 `context_view`(임베딩 없음)를 채운다. 프론트 `insightView.radarMean(items)`가 보고 있는 판 항목의 `radar.raw` 축별 평균을 계산하고, 미리보기 중에는 그 값을 레이더 평균으로 쓴다(현재 판은 `summary.radar_mean`과 같은 값). 계획 T2·T4·T7에 반영.
History: D7에서 A 승인.

### R7: 긴 문구·많은 Context에서 첫 화면 보장
Finding: OV6, P2, confidence 8/10, 02-design.md 5.0 ("헤더는 최대 180px", "흐름 카드 한 줄(카드 4개까지 가로, 넘치면 줄바꿈)"), 03-plan.md T1 (`headline`·`statements` 길이 제한 없음), reviewer: Codex outside voice (확인: Claude)
Plan baseline: 설계 1A — 1280×800에서 상단 바~흐름 카드가 스크롤 없이 보임. 길이 상한 없음.
Runtime evidence: LLM 출력 길이·Context 수에 상한이 없어 헤더 180px·흐름 한 줄 예산을 넘을 수 있다. 실데이터 인사이트의 context_ids 개수는 1~6개.
Comparison grid:
| 항목 | 현재 계획 | A | B |
|---|---|---|---|
| headline 길이 | 제한 없음 | 1~30자 검사(T1 `validate_items`) | 제한 없음 |
| statements 길이 | 제한 없음 | 각 1~70자 검사 | 제한 없음 |
| 헤더 표시 | — | 문장마다 2줄 말줄임(`line-clamp:2`), 전체 문장은 `title` | — |
| 흐름 5개 이상 | 줄바꿈 | 줄바꿈 허용. 1A 보장은 "흐름 카드 4개 이하"로 명시, 5개 이상이면 둘째 줄은 스크롤 아래여도 됨 | 같음 |
| 1A 수용 기준 문장 | 무조건 | "흐름 카드 4개 이하이고 T1 길이 규칙을 지킨 인사이트에서" | 같은 조건만 추가 |
| 테스트 | — | 31자 headline·71자 문장 거부, 긴 문장 말줄임 클래스, 6개 흐름 렌더 | 6개 흐름 렌더만 |
Question D8: 긴 문구 상한과 말줄임을 넣어 첫 화면 보장을 지킬까요? (권장 A)
Header: D8 길이 상한
Options:
A) 상한 + 말줄임 + 조건 명시 (recommended) — headline ≤30자, 문장 ≤70자, 2줄 말줄임, 1A는 흐름 4개 이하 기준. human ~2h / CC ~10min
B) 조건만 명시 — 상한 없이 1A 기준을 좁힘
State: approved
Actual answer: A) 상한 + 말줄임 + 조건 (D8 답)
Accepted scope: `validate_items`에 headline 1~30자, statements 각 1~70자 검사(도출·수정 공통, 새 필드가 있을 때). 프롬프트 v2에 같은 상한 문장. 헤더 문장 `line-clamp:2` + 전체 문장 `title`. 설계 1A 보장은 "흐름 카드 4개 이하이고 길이 규칙을 지킨 인사이트" 기준(QA Q3 조건), 5개 이상이면 흐름 둘째 줄은 스크롤 아래 허용. 계획 T1·T6·T7·QA에 반영.
History: D8에서 A 승인.

Approval readiness: PASS — D1(구조), R1/D2 A, R2/D3 A, R3/D4 A, R4/D5 A, R5/D6 A, R6/D7 A, R7/D8 A(각 사용자 답), F1(사실 정정), F2(2A 승인 인용). 미해결 없음.

## 검토 결과 요약 (plan-eng-review)

### 항목별 결과

- **Scope Challenge:** 기능 삭감 없음, 구조 Original arrangement(D1). scope accepted as-is.
- **1. Architecture:** 이슈 0. GET이 근거 묶음을 읽는 비용은 실측 24ms(1.7MB, Context 114개), 폴링 3초 간격이라 문제없음.
- **2. Code Quality:** 사실 정정 1(F1 카드 경로), 승인된 동작의 증명 1(F2 tags 타입).
- **3. Tests:** 아래 다이어그램. 새 동작마다 테스트가 Task에 들어 있음. 공백 0.
- **4. Performance:** 이슈 0 (R5 Context 요약도 수 KB, R6 history 보강은 임베딩 없음).
- **Outside voice (Codex):** P1 4건, P2 2건, 모두 코드로 확인 → R1~R7로 결정(OV3는 R4·R5 둘로 나눔).

### 테스트 커버리지

```
CODE PATHS                                              USER FLOWS
[+] insights.validate_items (T1)                        [+] 인사이트 한 개씩 보기
  ├── [★★★] 개수·ID·Context 기존 규칙                    ├── [★★★] 넘김 경계·그룹 키 (T6)
  ├── [★★★] statements 2개·hashtags·flow 범위·개수       ├── [★★ ] 선택 초기값·사라진 인사이트 (T7)
  ├── [★★★] 길이 상한 (R7)                               └── [→E2E] Q3·Q5 브라우저
  ├── [★★★] 수정: 전부/없음·퇴보 금지 (R4)              [+] 예전 판
  └── [★★★] 기호 정리                                     ├── [★★★] 대체 규칙·안내·다시 도출 버튼 (T4·T6)
[+] derive (T1)                                           └── [→E2E] Q1·Q2 (다시 도출 후 새 형식)
  ├── [★★ ] v2 프롬프트, 재시도 1회                     [+] 채팅 수정
  └── [→EVAL] 프롬프트 품질 → QA Q2 실데이터 도출         ├── [★★★] 현재 인사이트만 교체 (R3)
[+] fresh 다시 도출 (T3, R1)                              ├── [★★★] 목록 대상 + focus_id
  ├── [★★★] 새 판·확정 비움·컨셉 outdated                 ├── [★★★] Context 요약 첨부 (R5)
  └── [★★★] fresh 없으면 건너뜀(회귀)                     └── [→E2E] Q6
[+] context_view / dominant_dim / context_axis (T2)     [+] 판 미리보기
  ├── [★★★] 동률·빈 값·비리스트 tags (F2)                 ├── [★★★] 판 기준 레이더 평균 (R6)
  └── [★★★] 카드 경로·예전 카드 (F1)                      └── [→E2E] Q9
[+] GET /insight (T2)                                   [+] 반응형·접근성
  ├── [★★★] summary·예전 판·history 보강 (R6)             └── [→E2E] Q8 (768·375px, 44px)
  └── [★★★] 근거 묶음 없음
[+] _concept_identity (T1, R2)
  ├── [★★★] 문장 변경 → outdated, 해시태그만 → 유지
  └── [★★★] 예전 판끼리 회귀 없음
[+] Radar / OpportunityBars / InsightFlow (T5)
  └── [★★★] 평균 유무·null·0·전부 null·반례·하드코딩 색

COVERAGE: 계획된 코드 경로 모두 단위 테스트, 사용자 흐름은 브라우저 QA Q1~Q9
LLM: [→EVAL] derive.v2·edit.v2 — 저장소에 eval 묶음 없음, 형식은 validate_items가 강제, 품질은 Q2·Q6 실데이터 확인
```

### 실패 모드

| 경로 | 운영에서 생길 실패 | 테스트/처리 | 사용자에게 보이는가 |
|---|---|---|---|
| derive v2 | LLM이 길이·flow 규칙을 계속 어김 | 재시도 1회 후 실패 문구 (T1) | 보임: "인사이트를 만들지 못했습니다. 다시 시도하세요." |
| fresh 다시 도출 | 도출 중 실패 | 기존 판 유지, 실패 알림 (T3) | 보임 |
| 현재 인사이트 수정 | LLM이 다른 id를 답함 | 서버가 id 고정 (R3 테스트) | 해당 없음(막힘) |
| 목록 수정 | 새 형식 항목이 새 필드를 잃음 | 퇴보 금지 실패 (R4) | 보임: FAILURE_COPY |
| GET | 근거 묶음 없음·카드 없음 | 최소 행·null (T2) | 보임: 영역별 빈 상태 문구 |
| GET | tags가 리스트 아님 | 건너뜀 (F2) | 보임: "근거 부족" |

critical gap 0.

### NOT in scope

- 대표 이미지, `⋯` 메뉴 새 기능, 컨셉(8-F) 재구성: 기획 9절.
- LLM 품질 eval 묶음 신설: 저장소에 eval 체계가 없고, 형식은 코드 검사로 강제. QA Q2·Q6에서 실데이터로 확인.
- 기존 세션 자동 다시 도출: 기획 7절 6번. R1 버튼으로 사용자가 직접.

### What already exists (재사용)

- `radar()`·`embed_axes()`·`session_percentiles` (Context 축), `opportunity_bars`(평균 패턴), `PersonaStore.new_revision`(판·되돌리기), `_concept_identity`(무효화), `chat.edit`·`_target`(대상 분기), `RevisionList`·`ChatPanel`·`ConceptDetail`, PR #34 막대 그리드·44px 처리.
- 새로 만드는 것은 검사 함수·보기 계산·화면 부품뿐이며 위 경로를 대체하지 않는다.

### Worktree 병렬화

| Step | Modules touched | Depends on |
|---|---|---|
| T1 | backend/app/persona (insights, store, prompts) | — |
| T2 | backend/app/persona, backend/app/routers | T1 |
| T3 | backend/app/persona (chat, insight_pipeline, prompts), backend/app/routers | T2 |
| T4 | frontend/src/lib, frontend/src/components/persona (insightView) | — |
| T5 | frontend/src/components/persona (차트·흐름) | T4 |
| T6 | frontend/src/components/persona (상단·헤더·채팅), frontend/src/components (ChatPanel) | T4 |
| T7 | frontend/src/components/persona (InsightScreen, css) | T5, T6 |

Lane A: T1 → T2 → T3 (backend, 순차). Lane B: T4 → (T5 ∥ T6) → T7 (frontend). A와 B는 동시에 시작. T7 브라우저 확인은 T3 이후(새 API 필드 필요).
충돌 주의: T5·T6은 같은 폴더지만 파일이 겹치지 않음. `types.ts`는 T4만 수정.

### Implementation Tasks (검토에서 추가된 작업)

- [ ] **E1 (P1, human ~4h / CC ~20min)** — backend+frontend — fresh 다시 도출 경로와 버튼 (R1) · Files: insight_pipeline.py, stage8.py, InsightHeader.tsx, InsightScreen.tsx · Verify: T3 Step 2b 테스트, QA Q2
- [ ] **E2 (P1, human ~1h / CC ~5min)** — backend — 컨셉 identity에 새 문구 (R2) · Files: store.py · Verify: `test_concept_outdated_on_statement_change`
- [ ] **E3 (P1, human ~4h / CC ~20min)** — backend+frontend — '현재 인사이트' 채팅 대상 (R3) · Files: chat.py, stage8.py, types.ts, InsightChatBar.tsx · Verify: `test_item_target_*`, QA Q6
- [ ] **E4 (P1, human ~1h / CC ~10min)** — backend — 수정 출력 전부/없음 (R4) · Files: insights.py, chat.py · Verify: `test_validate_edit_*`
- [ ] **E5 (P1, human ~1h / CC ~10min)** — backend — 수정에 Context 요약 (R5) · Files: chat.py, edit.v2.md · Verify: `test_edit_attaches_context_sources`
- [ ] **E6 (P2, human ~2h / CC ~10min)** — backend+frontend — 미리보기 데이터 (R6) · Files: stage8.py, insightView.ts · Verify: `test_get_insights_enriches_history`, QA Q9
- [ ] **E7 (P2, human ~2h / CC ~10min)** — backend+frontend — 길이 상한·말줄임 (R7) · Files: insights.py, InsightHeader.tsx, insight.css · Verify: `test_validate_length_caps`, QA Q3

### Unresolved decisions

없음.

### Completion summary

- Step 0: Scope Challenge — scope accepted as-is
- Architecture Review: 0 issues found
- Code Quality Review: 2 issues found (F1 정정, F2 증명)
- Test Review: diagram produced, 0 gaps identified
- Performance Review: 0 issues found
- NOT in scope: written
- What already exists: written
- TODOS.md updates: 0 items proposed to user
- Failure modes: 0 critical gaps flagged
- Unresolved decisions: 0 in this review
- Outside voice: codex, completed (P1 4, P2 2 → R1~R7 모두 A 승인)
- Parallelization: 2 lanes, 2 parallel / T5∥T6 내부 병렬
- Lake Score: 7/7

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | `/plan-ceo-review` | Scope & strategy | 0 | — | — |
| Outside Review | codex (`/plan-eng-review` outside voice) | Independent 2nd opinion | 1 | completed | 6 findings (P1 4, P2 2), 7 decisions all accepted |
| Eng Review | `/plan-eng-review` | Architecture & tests (required) | 1 | issues_open | 2 issues, 0 critical gaps (all resolved in plan) |
| Design Review | `/plan-design-review` | UI/UX gaps | 1 | clean | score: 6/10 → 9/10, 10 decisions |
| DX Review | `/plan-devex-review` | Developer experience gaps | 0 | — | — |

- **OUTSIDE COVERAGE:** codex, plan-review phase, completed; 6 findings verified against code and resolved as R1~R7.
- **CROSS-MODEL:** Claude review found 2 code-quality items (F1, F2); Codex found 6 different contract gaps (regeneration, concept identity, edit sources, edit scope, preview data, overflow). No overlap; Claude confirmed all 6 by reading code.
- **VERDICT:** DESIGN CLEARED. ENG findings all resolved into plan tasks (status issues_open reflects mapped work) — ready for plan approval.

NO UNRESOLVED DECISIONS
