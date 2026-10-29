# 키워드 일괄 입력 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 1단계 키워드 화면에서 CSV·리스트로 정리한 키워드를 한 번에 넣는다. 분류 없는 행은 LLM이 축·하위분류를 제안하고, 사람이 미리보기에서 확인·수정한 뒤 추가한다.

**Architecture:** 백엔드 `app/keywords/bulk.py`에 저장 없는 `preview`(중복 판정 + LLM 분류)와 한 번에 저장하는 `add_many`를 두고, `routers/keywords_v2.py`에 엔드포인트 2개를 연다. 프런트는 순수 로직 `lib/logic/bulkKeywords.ts`(파싱·값 인식·미리보기 선택자)와 카드 컴포넌트 `components/keywords/BulkAdd.tsx`로 나누고, 키워드 화면에 카드를 끼운다.

**Tech Stack:** Python 3.12 · FastAPI · Pydantic v2 / Next.js 16 · React 19 · Vitest(node 환경, `renderToStaticMarkup`)

**Spec:** [01-brainstorm.md](01-brainstorm.md) (제품 승인) · [02-design.md](02-design.md) (설계 승인) · 목업 [mockup/index.html](mockup/index.html) · QA [QA_PLAN-kw-bulk-input.md](QA_PLAN-kw-bulk-input.md)

## Global Constraints

- 구현·테스트는 하네스가 고정한 구현 워커가 한다(`dispatch implementer`). 워커는 커밋하지 않고 `READY_FOR_COMMIT` 보고서를 낸다. 각 Task의 "Commit"은 Controller가 `repository-gate` → `repository-commit`으로 한다.
- 실행: build worktree 루트에서 `backend/.venv/bin/python -m pytest …`, `npm --prefix frontend …`. 테스트는 네트워크 금지(기존 `data_dir` 픽스처가 소켓 연결을 막는다), LLM은 `FakeBackend(responses=…)`로 대체.
- 한 요청 최대 **500행**, 키워드 길이 **1~100자**, LLM 분류 묶음 **100개**, LLM 작업 이름 **`kw_bulk_classify`**.
- 추가되는 키워드는 단건 직접 추가와 같다: `id='manual-'+uuid4().hex`, `kw=''.join(kw.split())`, `origin='manual'`, `status='approved'`, round는 `add_manual` 규칙, 검색량(`volumes`), `add` 이벤트, `write_feedback_md`.
- 비교 키는 `normalize.norm_key`(NFC·공백 제거·소문자). 분류 유효성은 `taxonomy.is_valid`.
- 두 API 모두 `store.assert_writable(sid, version)`. 오류 봉투는 기존 `KeywordRoute`.
- 화면 문구·클래스는 목업(`mockup/index.html`)을 따른다. 새 CSS 클래스는 `kwb-*`로 `keywords.css`에 둔다.
- 입력 중 화면을 떠나면 입력 내용은 사라진다(저장 안 함) — 이번 범위에서 허용.
- 하네스 검증 명령: `backend/.venv/bin/python -m pytest backend/tests -q`, `npm --prefix frontend run lint`, `npm --prefix frontend run build`, `npm --prefix frontend test`.

## 설계와 달라지는 점 (계획 승인 대상)

- **구분자 판정 단위.** 설계 3절은 "줄에 탭이 있으면 탭"이었으나, 엑셀 붙여넣기에서 셀이 비어 탭 없이 끝나는 줄이 생길 수 있어 **텍스트 전체에 탭이 하나라도 있으면 탭 구분**으로 정한다(T3).
- **LLM 분류 묶음 동시 호출.** 설계는 순서를 정하지 않았다. 운영 타임아웃(nginx·gunicorn 300초)을 넘지 않도록 묶음을 최대 5개 동시에 보낸다(T1, plan-eng-review D2).

## Review Focus

1. **엑셀에서 복사한 표**: 탭 구분, 끝의 빈 열, 따옴표로 감싼 셀(셀 안 쉼표·줄바꿈) — 셀이 잘못 쪼개지면 엉뚱한 키워드가 대량으로 생긴다. → T3 `parses excel paste with quotes and trailing tabs`.
2. **첫 셀 BOM**: CSV를 붙여넣거나 파일로 읽을 때 `﻿키워드`가 머리글로 인식되지 않으면 머리글이 키워드 1개로 추가된다. → T3 `strips BOM before header detection`.
3. **미리보기 이후 생긴 중복**: 미리보기와 추가 사이에 다른 탭·사람이 같은 키워드를 추가. 중복 저장되면 안 된다. → T2 `test_add_many_rechecks_duplicates_inside_lock`.
4. **LLM의 엉뚱한 응답**: 없는 index, 같은 index 두 번, 축과 맞지 않는 하위분류(`physical`/`emotion`), 세션에 없는 `custom:`. 저장 가능한 잘못된 분류가 미리보기에 "자동 제안"으로 뜨면 안 된다. → T1 `test_preview_rejects_invalid_llm_answers`.
5. **100자 넘는 셀**: 문단을 통째로 붙여넣으면 한 행 때문에 요청 전체가 422로 막힌다. 프런트에서 그 행만 빼고 알린다. → T3 `skips cells longer than 100 chars`.

## File Structure

| 파일 | 책임 | Task |
|---|---|---|
| `backend/app/keywords/bulk.py` (새) | `preview`, `add_many`, LLM 분류 | T1, T2 |
| `backend/app/keywords/rounds.py` | `add_manual`의 round 계산을 `manual_round(data)`로 분리(동작 동일) | T2 |
| `backend/app/routers/keywords_v2.py` | `/bulk/preview`, `/bulk` 라우트와 요청 모델 | T1, T2 |
| `backend/tests/keywords/test_bulk.py` (새) | 백엔드 테스트 | T1, T2 |
| `frontend/src/lib/api/keywords.ts` | `previewBulk`, `addBulk`, 타입 | T3 |
| `frontend/src/lib/logic/bulkKeywords.ts` (새) | 디코딩·파싱·값 인식·미리보기 선택자 | T3 |
| `frontend/src/lib/logic/bulkKeywords.test.ts` (새) | 순수 로직 테스트 | T3 |
| `frontend/src/components/keywords/BulkAdd.tsx` (새) | 카드 UI·상태 흐름 | T4 |
| `frontend/src/components/keywords/BulkAdd.test.ts` (새) | 정적 렌더 테스트 | T4 |
| `frontend/src/components/keywords/keywords.css` | `kwb-*` 클래스 | T4 |
| `frontend/src/app/pipeline/keywords/page.tsx` | 카드 배치·콜백 연결 | T4 |
| `backend/tests/fixtures/llm/kw_bulk_classify.json` (새) | 가짜 LLM 응답(dev 확인용) | T4 |

---

### Task T1: 미리보기 API (`bulk.preview`, `POST /keywords/{sid}/bulk/preview`)

**Files:**
- Create: `backend/app/keywords/bulk.py`, `backend/tests/keywords/test_bulk.py`
- Modify: `backend/app/routers/keywords_v2.py`

**Interfaces:**
- Consumes: `rounds._all_keywords(data) -> list[Keyword]`, `normalize.norm_key`, `taxonomy.AXES`, `taxonomy.is_valid`, `llm.registry.run_task`, `llm.base.LLMTask/Attachment`, `store.locked/assert_writable/session_dir/StoreError`.
- Produces:
  - `bulk.MAX_ROWS = 500`, `bulk.CLASSIFY_CHUNK = 100`
  - `bulk.preview(sid: str, rows: list[dict], version: str | None = None) -> dict` — `rows` 원소 `{'kw': str, 'axis': str | None, 'sub': str | None}`.
  - 응답 `{'rows': [{'row': int, 'kw': str, 'axis': str|None, 'sub': str|None, 'source': 'input'|'llm'|'llm_failed'|None, 'status': 'new'|'existing'|'in_list_duplicate'|'needs_class', 'duplicateOf'?: {'id','kw','axis','sub'}, 'firstRow'?: int}], 'classifyError'?: {'kind': str, 'message': str}}`. `row`는 요청 순서의 0부터 번호. `kw`는 공백 제거 후 값. `existing`·`in_list_duplicate` 행은 `source=None`이고 입력 분류를 그대로 돌려준다(없으면 None).
  - 라우터 모델: `BulkRow(kw: str = Field(min_length=1, max_length=100), axis: str | None = None, sub: str | None = None)`, `BulkPreviewRequest(rows: list[BulkRow] = Field(min_length=1, max_length=500))`.

- [ ] **Step 1: 실패하는 테스트 작성** — `test_bulk.py`는 `test_rounds_api.py`의 `data_dir`·`client` 픽스처를 같은 방식으로 정의(또는 `conftest`로 옮기지 말고 복사)하고, LLM은 `monkeypatch.setattr(registry, 'get_backend', lambda task: FakeBackend(responses={'kw_bulk_classify': json.dumps({...})}))`로 바꾼다. 세션에 기존 키워드 `{'id':'k1','kw':'저소음','axis':'physical','sub':'sense','round':1,'origin':'llm','status':'approved'}`와 `{'id':'k2','kw':'창문','axis':'physical','sub':'custom:설치환경',…}`를 넣는다.

```python
def test_preview_marks_input_existing_and_in_list_duplicates(client, llm):
    rows = [{'kw': '층간소음', 'axis': 'physical', 'sub': 'sense'},
            {'kw': '저 소음'}, {'kw': '층간 소음'}]
    body = client.post('/keywords/test/bulk/preview', json={'rows': rows}).json()
    assert [r['status'] for r in body['rows']] == ['new', 'existing', 'in_list_duplicate']
    assert body['rows'][0]['source'] == 'input'
    assert body['rows'][1]['duplicateOf']['id'] == 'k1'
    assert body['rows'][2]['firstRow'] == 0
    assert llm.calls == []                       # 분류 없는 새 행이 없으면 LLM 호출 안 함

def test_preview_classifies_only_unclassified_rows(client, llm):
    llm.answer = {'items': [{'index': 0, 'axis': 'psychological', 'sub': 'emotion'}]}
    body = client.post('/keywords/test/bulk/preview', json={'rows': [
        {'kw': '불안감'}, {'kw': '퇴근후', 'axis': 'physical', 'sub': 'time'}]}).json()
    assert body['rows'][0].items() >= {'axis': 'psychological', 'sub': 'emotion', 'source': 'llm', 'status': 'new'}.items()
    assert len(llm.calls) == 1 and '불안감' in llm.calls[0].instructions and '퇴근후' not in llm.calls[0].instructions
    assert 'custom:설치환경' in llm.calls[0].instructions

def test_preview_rejects_invalid_llm_answers(client, llm):
    llm.answer = {'items': [{'index': 0, 'axis': 'physical', 'sub': 'emotion'},
                            {'index': 1, 'axis': 'physical', 'sub': 'custom:없는그룹'},
                            {'index': 9, 'axis': 'physical', 'sub': 'sense'},
                            {'index': 2, 'axis': 'physical', 'sub': 'sense'},
                            {'index': 2, 'axis': 'behavioral', 'sub': 'coping'}]}
    body = client.post('/keywords/test/bulk/preview', json={'rows': [{'kw': 'a1'}, {'kw': 'a2'}, {'kw': 'a3'}, {'kw': 'a4'}]}).json()
    assert [(r['status'], r['source']) for r in body['rows']] == [('needs_class', 'llm_failed')] * 2 + [('new', 'llm'), ('needs_class', 'llm_failed')]
    assert body['rows'][2]['sub'] == 'sense'     # 같은 index 중복은 첫 답 채택

def test_preview_llm_failure_keeps_rows(client, llm):
    llm.fail = True
    body = client.post('/keywords/test/bulk/preview', json={'rows': [{'kw': '불안감'}]}).json()
    assert body['rows'][0]['status'] == 'needs_class' and body['classifyError']['kind']

def test_preview_chunks_by_100_and_saves_nothing(client, llm):
    before = (store.session_dir('test') / 'session.json').read_bytes()
    client.post('/keywords/test/bulk/preview', json={'rows': [{'kw': f'단어{i}'} for i in range(250)]})
    assert len(llm.calls) == 3                       # 100 + 100 + 50
    assert (store.session_dir('test') / 'session.json').read_bytes() == before

def test_preview_chunks_run_concurrently_and_keep_row_order(client, llm):
    # 가짜 백엔드 run()이 Barrier(3, timeout=5)에서 기다린다 → 세 묶음이 동시에 돌 때만 통과(차례 실행이면 BrokenBarrierError → 분류 실패)
    llm.barrier = Barrier(3, timeout=5)
    llm.answer = {'items': [{'index': 0, 'axis': 'physical', 'sub': 'time'}]}
    body = client.post('/keywords/test/bulk/preview', json={'rows': [{'kw': f'단어{i}'} for i in range(250)]}).json()
    assert [r['row'] for r in body['rows']] == list(range(250))
    assert [r['row'] for r in body['rows'] if r['source'] == 'llm'] == [0, 100, 200]

def test_preview_validation_and_readonly(client):
    assert client.post('/keywords/test/bulk/preview', json={'rows': []}).status_code == 422
    assert client.post('/keywords/test/bulk/preview', json={'rows': [{'kw': 'x'}] * 501}).status_code == 422
    assert client.post('/keywords/test/bulk/preview', json={'rows': [{'kw': 'x' * 101}]}).status_code == 422
    assert client.post('/keywords/test/bulk/preview', json={'rows': [{'kw': '소음'}, {'kw': '   '}]}).status_code == 422
    # 읽기 전용 버전: test_rounds_api.py의 create_version('test','v1','stage1','') 패턴
    ...  # create_version 후 ?version=v1 → 409
```

`llm` 픽스처: `calls` 목록, `answer`(dict, 기본 `{'items': []}`), `fail`(True면 `failure('backend','down')` 반환), `barrier`(있으면 `run()` 시작에서 `barrier.wait()`; `BrokenBarrierError`는 `failure('backend', …)`로)을 갖는 가짜 백엔드. 위 `...` 줄은 기존 `test_rounds_api.py`의 버전 409 테스트와 같은 단언으로 채운다.

- [ ] **Step 2: 실패 확인** — `backend/.venv/bin/python -m pytest backend/tests/keywords/test_bulk.py -q` → 404(라우트 없음)로 FAIL.

- [ ] **Step 3: `bulk.preview` 구현**
  - 정규화한 키워드(`''.join(kw.split())`)가 빈 행이 하나라도 있으면 `StoreError('키워드와 분류를 확인하세요', 422, 'validation')`. 분류 판정은 `axis and sub and is_valid(axis, sub)`(None 가드).
  - `store.locked(sid)` 안에서 `assert_writable` 후 `data`·`directory` 확보(잠금은 LLM 호출 전 해제 — `suggest_words`와 같은 패턴).
  - 기존 키 맵 `{norm_key(k.kw): k for k in _all_keywords(data)}`, 허용 목록 = `AXES`의 모든 `(axis, sub)` + 기존 키워드의 `custom:` 하위분류.
  - LLM 대상 행을 100개씩 묶어 **`ThreadPoolExecutor(max_workers=5)`로 동시에** 보낸다(최대 500행 → 묶음 5개, 대기 ≈ 호출 1번; plan-eng-review D2). 결과는 묶음 순서대로 합친다. 각 묶음은 `LLMTask(task='kw_bulk_classify', sid=sid, max_tokens=4000, attachments=[Attachment(title='project_context.md', body=…)], output_schema=Classified)`로 보낸다. `Classified(BaseModel): items: list[ClassifiedItem]`, `ClassifiedItem(index: int, axis: str, sub: str)`. `index`는 묶음 안 0부터.
  - 지시문(그대로 사용):
    `'다음 키워드마다 소비자 경험 분류(축/하위분류)를 하나씩 고르세요. 허용 목록 밖의 값은 쓰지 마세요. 각 항목은 index와 axis, sub를 답합니다.\n허용 목록: ' + json.dumps(allowed, ensure_ascii=False) + '\n키워드: ' + json.dumps([{'index': i, 'kw': kw} …], ensure_ascii=False)`. `allowed`는 `[{'axis','sub'}]` 목록.
  - 답 검증: index 범위 안, 첫 답만, `(axis, sub)`가 허용 목록 안 → `new/llm`; 아니면 `needs_class/llm_failed`. `result.ok`가 거짓이면 그 묶음 전부 `needs_class/llm_failed`, 응답에 첫 오류의 `classifyError={'kind': result.error.kind, 'message': result.error.message}`.
  - 라우트 `@router.post('/{sid}/bulk/preview') def bulk_preview(sid, body: BulkPreviewRequest, version: str | None = None): return bulk.preview(sid, [r.model_dump() for r in body.rows], version=version)`.

- [ ] **Step 4: 통과 확인** — 같은 명령 PASS, `backend/.venv/bin/python -m pytest backend/tests/keywords -q` PASS.

- [ ] **Step 5: READY_FOR_COMMIT** — 제안 메시지 `feat(keywords): 일괄 입력 미리보기 API`.

---

### Task T2: 일괄 추가 API (`bulk.add_many`, `POST /keywords/{sid}/bulk`)

**Files:**
- Modify: `backend/app/keywords/bulk.py`, `backend/app/keywords/rounds.py`, `backend/app/routers/keywords_v2.py`, `backend/tests/keywords/test_bulk.py`

**Interfaces:**
- Consumes: T1의 `bulk.py`; `rounds.volumes(kws) -> list[Keyword]`, `rounds._all_keywords`, `store._update_locked(sid, patch, confirm_stage='stage1')`, `events.append_event`, `KeywordEvent`, `feedback.write_feedback_md`, `display.with_display`.
- Produces:
  - `rounds.manual_round(data: dict) -> int` — `add_manual`의 기존 round 식을 그대로 옮긴 함수. `add_manual`이 이를 호출한다.
  - `bulk.add_many(sid: str, items: list[dict], version: str | None = None) -> dict` — `items` 원소 `{'kw','axis','sub'}`. 응답 `{'results': [{'index': int, 'status': 'added'|'duplicate'|'invalid', 'id'?: str, 'duplicateOf'?: str}], 'keywords': with_display(added_dicts)}`.
  - 라우터 모델 `BulkItem(kw: str = Field(min_length=1, max_length=100), axis: Literal['physical','psychological','behavioral'], sub: str)`, `BulkAddRequest(items: list[BulkItem] = Field(min_length=1, max_length=500))`.

- [ ] **Step 1: 실패하는 테스트 작성**

```python
def test_add_many_matches_single_manual_add(client, volume_calls):
    body = client.post('/keywords/test/bulk', json={'items': [
        {'kw': '층간 소음', 'axis': 'physical', 'sub': 'sense'},
        {'kw': '불안감', 'axis': 'psychological', 'sub': 'emotion'}]}).json()
    assert [r['status'] for r in body['results']] == ['added', 'added']
    saved = {k['kw']: k for k in store.load_session('test')['keywords']}
    assert saved['층간소음'].items() >= {'origin': 'manual', 'status': 'approved', 'axis': 'physical', 'sub': 'sense'}.items()
    assert saved['층간소음']['id'].startswith('manual-') and saved['층간소음']['volume']['source'] == 'unconnected'
    assert [e.type for e in load_events('test')][-2:] == ['add', 'add']
    assert len(volume_calls) == 1                       # 검색량 조회 한 번
    assert '층간소음' in (store.session_dir('test') / 'keyword_feedback.md').read_text()

def test_add_many_skips_invalid_and_in_request_duplicates(client):
    body = client.post('/keywords/test/bulk', json={'items': [
        {'kw': '저 소음', 'axis': 'physical', 'sub': 'sense'},      # 기존 k1
        {'kw': '환기', 'axis': 'physical', 'sub': 'emotion'},       # 잘못된 분류
        {'kw': '환기', 'axis': 'behavioral', 'sub': 'coping'},
        {'kw': '환 기', 'axis': 'behavioral', 'sub': 'coping'}]}).json()
    assert [(r['status'], r.get('duplicateOf')) for r in body['results']] == [
        ('duplicate', 'k1'), ('invalid', None), ('added', None), ('duplicate', body['results'][2]['id'])]

def test_add_many_rejects_blank_keyword(client):
    before = (store.session_dir('test') / 'session.json').read_bytes()
    body = client.post('/keywords/test/bulk', json={'items': [{'kw': '  ', 'axis': 'physical', 'sub': 'sense'}]}).json()
    assert body['results'] == [{'index': 0, 'status': 'invalid'}]
    assert (store.session_dir('test') / 'session.json').read_bytes() == before

def test_add_many_rechecks_duplicates_inside_lock(client, monkeypatch):
    original = bulk.rounds.volumes
    fired = []
    def racing(kws):                      # 검색량 조회(잠금 밖) 중 다른 요청이 같은 키워드를 추가 — 한 번만(재귀 방지)
        if not fired:
            fired.append(1)
            client.post('/keywords/test/manual', json={'kw': '층간소음', 'axis': 'physical', 'sub': 'sense'})
        return original(kws)
    monkeypatch.setattr(bulk.rounds, 'volumes', racing)
    body = client.post('/keywords/test/bulk', json={'items': [{'kw': '층간소음', 'axis': 'physical', 'sub': 'sense'}]}).json()
    assert body['results'][0]['status'] == 'duplicate'
    assert [k['kw'] for k in store.load_session('test')['keywords']].count('층간소음') == 1

def test_add_many_readonly_and_validation(client):
    assert client.post('/keywords/test/bulk', json={'items': []}).status_code == 422
    assert client.post('/keywords/test/bulk', json={'items': [{'kw': 'x', 'axis': 'nope', 'sub': 'sense'}]}).status_code == 422
    ...  # 읽기 전용 버전 409 (T1과 같은 패턴), session.json 바이트 불변
```

`volume_calls` 픽스처: `monkeypatch`로 `app.keywords.volume.naver_searchad.monthly_volume`을 감싸 호출 인자를 기록하고 `Unconnected`를 던진다(기존 미연결 동작 유지).

- [ ] **Step 2: 실패 확인** — `pytest backend/tests/keywords/test_bulk.py -q` → 새 테스트 404로 FAIL.

- [ ] **Step 3: 구현**
  - `rounds.manual_round(data)`로 round 식을 옮기고 `add_manual`이 사용(기존 테스트로 동작 동일 확인).
  - `add_many`: 잠금 안 `assert_writable`(version 확보) → 잠금 밖에서 정규화 키워드가 비지 않고 `is_valid` 통과한 항목만(나머지 `invalid`) `Keyword(id='manual-'+uuid4().hex, kw=''.join(kw.split()), axis, sub, round=1, origin='manual', status='approved')`로 만들고 `rounds.volumes(...)` **한 번** → 잠금 안에서 다시 `assert_writable`, 현재 키워드 키 맵으로 중복 판정(요청 안 앞 항목 포함), round=`manual_round(data)`, `store._update_locked(sid, {'keywords': data['keywords'] + added}, confirm_stage='stage1')` 한 번, 추가된 것마다 `append_event(… type='add', kwId, kw …, directory=directory)`, `write_feedback_md` 한 번. 추가된 것이 없으면 저장·피드백을 건너뛴다.
  - 라우트 `@router.post('/{sid}/bulk')`.

- [ ] **Step 4: 통과 확인** — `pytest backend/tests/keywords -q` PASS(기존 `test_rounds_api.py` 수동 추가 테스트 포함).

- [ ] **Step 5: READY_FOR_COMMIT** — `feat(keywords): 키워드 일괄 추가 API`.

---

### Task T3: 프런트 파싱·선택자·API 클라이언트

**Files:**
- Create: `frontend/src/lib/logic/bulkKeywords.ts`, `frontend/src/lib/logic/bulkKeywords.test.ts`
- Modify: `frontend/src/lib/api/keywords.ts`

**Interfaces:**
- Consumes: `components/keywords/taxonomy.ts`의 `axes`, `destinations`, `subLabel`, `groupKey`; T1·T2 API 계약.
- Produces (`lib/api/keywords.ts`):
  - `type BulkRowIn = { kw: string; axis?: Axis; sub?: string }`
  - `type BulkPreviewRow = { row: number; kw: string; axis: Axis | null; sub: string | null; source: 'input' | 'llm' | 'llm_failed' | null; status: 'new' | 'existing' | 'in_list_duplicate' | 'needs_class'; duplicateOf?: { id: string; kw: string; axis: Axis; sub: string }; firstRow?: number }`
  - `type BulkPreview = { rows: BulkPreviewRow[]; classifyError?: { kind: string; message: string } }`
  - `type BulkResult = { results: { index: number; status: 'added' | 'duplicate' | 'invalid'; id?: string; duplicateOf?: string }[]; keywords: Keyword[] }`
  - `previewBulk(sid, rows: BulkRowIn[], version?) => Promise<BulkPreview>`, `addBulk(sid, items: (Destination & { kw: string })[], version?) => Promise<BulkResult>` (기존 `request` 사용, 경로 `/bulk/preview`, `/bulk`).
- Produces (`lib/logic/bulkKeywords.ts`):
  - `MAX_BULK_ROWS = 500`, `MAX_KW_LENGTH = 100`
  - `decodeCsv(buf: ArrayBuffer): string` — `new TextDecoder('utf-8', { fatal: true })` 실패 시 `new TextDecoder('euc-kr')`, 앞 BOM 제거.
  - `resolveGroup(axis: string | undefined, sub: string | undefined, groups: Destination[]): Destination | null`
  - `parseBulk(text: string, groups: Destination[]): { rows: BulkRowIn[]; truncated: number; tooLong: string[] }`
  - `type BulkEdit = Record<number, { include?: boolean; to?: Destination }>`
  - `type BulkView = BulkPreviewRow & { include: boolean; chosen: boolean; state: 'new' | 'existing' | 'in_list_duplicate' | 'needs_class' | 'excluded' }`
  - `viewRows(preview: BulkPreview, edits: BulkEdit): BulkView[]` — `existing`·`in_list_duplicate`는 항상 `include=false`·편집 무시. 그 외 `edits[row].to`가 있으면 그 분류·`chosen=true`, 분류가 생긴 `needs_class`는 `new`. `include=false`면 `state='excluded'`.
  - `bulkSummary(rows: BulkView[]): { new: number; existing: number; inListDuplicate: number; needsClass: number; excluded: number }`
  - `addableItems(rows: BulkView[]): (Destination & { kw: string; row: number })[]` — `state==='new'`이고 분류 있는 행.
  - `applyToIncluded(rows: BulkView[], edits: BulkEdit, to: Destination): BulkEdit` — `include`이고 `new|needs_class`인 행에 `to` 지정.
  - `retryRows(rows: BulkView[]): BulkRowIn[]` — 모든 행을 순서대로. 입력값·직접 선택·LLM 성공 분류는 넣고, 실패 행은 분류 없이.

- [ ] **Step 1: 실패하는 테스트 작성** (`bulkKeywords.test.ts`, `describe('bulkKeywords')`)
  - `parses Korean and English headers`: `'키워드,축,하위분류\n층간소음,물리,감각\n불안감,,'` → `[{kw:'층간소음',axis:'physical',sub:'sense'},{kw:'불안감'}]`; `'kw\tAXIS\tsub\n소음\tphysical\tsense'` 동일 인식.
  - `strips BOM before header detection`: `'﻿키워드\n소음'` → `[{kw:'소음'}]`.
  - `treats a single headerless line as a comma list`: `'소음, 환기 ,  ,습도'` → kw `['소음','환기','습도']`.
  - `uses first cell per line and tries axis/sub without header`: `'소음,물리,감각\n환기'` → `[{kw:'소음',axis:'physical',sub:'sense'},{kw:'환기'}]`.
  - `parses excel paste with quotes and trailing tabs`: `'"a, b"\t심리\t감정\t\t\n"줄\n바꿈"\t\t'` → `[{kw:'a, b',axis:'psychological',sub:'emotion'},{kw:'줄\n바꿈'}]` (키워드 공백 정리는 서버가 함).
  - `resolves sub-only, labels, codes and custom names`: `resolveGroup(undefined,'정보탐색',destinations)` → `{axis:'behavioral',sub:'info_search'}`; `resolveGroup('심리','emotion',…)` → psychological/emotion; `resolveGroup('물리','설치환경',[...destinations,{axis:'physical',sub:'custom:설치환경'}])` → custom; `resolveGroup('물리', undefined, …)` → `null`; `resolveGroup('심리','감각',…)` → `null`(축 불일치).
  - `truncates to 500 rows`: 520줄 → `rows.length===500`, `truncated===20`.
  - `skips cells longer than 100 chars`: 101자 셀 → rows에 없고 `tooLong.length===1`.
  - `decodes utf-8, BOM and cp949`: `new TextEncoder().encode('키워드')`, BOM 붙인 버퍼, CP949 바이트 `Uint8Array.from([0xc5,0xb0,0xbf,0xf6,0xb5,0xe5])`(“키워드”) → 모두 `'키워드'`.
  - `view rows, summary, addable and bulk apply`: 미리보기 4행(new/input, existing, in_list_duplicate, needs_class) + edits `{3:{to:{axis:'physical',sub:'space'}}, 0:{include:false}}` → states `['excluded','existing','in_list_duplicate','new']`, summary `{new:1,existing:1,inListDuplicate:1,needsClass:0,excluded:1}`, `addableItems` → row 3만; `applyToIncluded`가 existing 행엔 손대지 않음.
  - `retry keeps chosen and input classes`: `retryRows`가 llm_failed 행은 분류 없이, chosen 행은 고른 분류로.
  - `edits survive retry`: 같은 행 순서의 새 미리보기에 이전 `edits`(row 1 `include:false`)를 그대로 적용하면 row 1이 `excluded`로 남는다.
  - `quoted tab does not switch delimiter`: `'키워드,축,하위분류\n"a\tb",물리,감각'` → `[{kw:'a\tb',axis:'physical',sub:'sense'}]`.
  - `unterminated quote ends at line end`: `'"abc\n소음'` → kw `['abc','소음']`(여는 따옴표는 버리고 그 줄 끝까지 한 셀, 다음 줄은 독립 행).

- [ ] **Step 2: 실패 확인** — `npm --prefix frontend test -- bulkKeywords` → 모듈 없음 FAIL.

- [ ] **Step 3: 구현** — CSV 분해는 따옴표(`""` 이스케이프 포함)를 아는 작은 상태 기계 하나로 줄·셀을 나눈다(외부 라이브러리 추가 안 함). 구분자: **따옴표 밖에** 탭이 하나라도 있으면 탭, 아니면 쉼표. 닫히지 않은 따옴표는 그 줄 끝까지를 한 셀로 본다(다음 줄을 삼키지 않음). 머리글 별칭 비교는 `trim().toLowerCase()`. 하위분류 표시 이름은 `subLabel`로 역매핑.

- [ ] **Step 4: 통과 확인** — `npm --prefix frontend test`, `npm --prefix frontend run lint` PASS.

- [ ] **Step 5: READY_FOR_COMMIT** — `feat(keywords): 일괄 입력 파싱과 API 클라이언트`.

---

### Task T4: 일괄 추가 카드와 화면 연결

**Files:**
- Create: `frontend/src/components/keywords/BulkAdd.tsx`, `frontend/src/components/keywords/BulkAdd.test.ts`
- Create: `backend/tests/fixtures/llm/kw_bulk_classify.json` (`{"items": [{"index": 0, "axis": "psychological", "sub": "emotion"}, {"index": 1, "axis": "behavioral", "sub": "coping"}]}` — `LLM_BACKEND=fake` dev·브라우저 QA용: 묶음의 앞 두 행만 분류되고 나머지는 "분류 필요")
- Modify: `frontend/src/components/keywords/keywords.css`, `frontend/src/app/pipeline/keywords/page.tsx`

**Interfaces:**
- Consumes: T3 전부, ds `Banner`·`Badge`·`Button`·`Card`·`Select`·`TextArea`·`Table`·`Skeleton`, `taxonomy.groupLabel/groupKey`, `lib/api/errors.displayError`.
- Produces:
  - `type BulkState = { stage: 'closed' | 'input' | 'loading' | 'preview' | 'result'; text: string; parsed?: ReturnType<typeof parseBulk>; preview?: BulkPreview; edits: BulkEdit; result?: BulkResult; error?: string }`
  - `export function BulkAdd(props: { groups: Destination[]; disabled: boolean; readonly: boolean; preview: (rows: BulkRowIn[]) => Promise<BulkPreview>; add: (items: (Destination & { kw: string })[]) => Promise<BulkResult>; onReveal: (groups: Destination[]) => void; initialState?: BulkState })` — 네트워크 호출은 페이지가 넘긴 `preview`·`add`만 쓴다. `initialState`는 테스트용(기본 `{stage:'closed', text:'', edits:{}}`).

- [ ] **Step 1: 실패하는 테스트 작성** (`BulkAdd.test.ts`, `renderToStaticMarkup(createElement(BulkAdd, {...}))`)
  - `closed shows title and open button`: `'키워드 일괄 추가'`, `'일괄 추가하기'`.
  - `readonly shows notice only`: `'읽기 전용 버전에서는 키워드를 추가할 수 없습니다.'`, `'일괄 추가하기'` 없음.
  - `input shows textarea hint, file button and row count`: text `'소음\n환기'` → `'2행 인식'`, `'CSV 파일 선택하기'`, `'한 번에 최대 500행'`; text `''` → 미리보기 버튼 `disabled`.
  - `loading shows status`: `'자동 분류하는 중'`, `role="status"`.
  - `preview shows summary, statuses and add count`: 4행 미리보기(new input · existing · in_list_duplicate · needs_class) → `'추가 예정 1'`, `'이미 있음 1'`, `'리스트 안 중복 1'`, `'분류 필요 1'`, `'1개 추가하기'`, existing 행에 `'“저소음”'`, in_list_duplicate 행에 `'1행과 같음'`(firstRow+1).
  - `preview with classifyError shows retry`: `'자동 분류에 실패했습니다'`, `'자동 분류 다시 하기'`.
  - `truncated shows notice`: `parsed.truncated=20` → `'앞 500행만 불러왔습니다(나머지 20행 제외)'`.
  - `result shows added and skipped rows`: results `[added, duplicate]` → `'키워드 1개를 추가했습니다. 1개는 건너뛰었습니다.'`, `'추가한 키워드 보기'`, `'새 리스트 넣기'`.
  - `disabled blocks add`: `disabled:true`인 preview → 추가 버튼 `disabled`; 추가 예정 0인 preview → `'0개 추가하기'`이고 `disabled`.

- [ ] **Step 2: 실패 확인** — `npm --prefix frontend test -- BulkAdd` FAIL.

- [ ] **Step 3: 구현**
  - 문구·배치는 목업 그대로. 상태 전환: 닫힘 →(일괄 추가하기) 입력 →(미리보기) 로딩 →(응답) 미리보기 / (실패) 입력 + 위험 배너 → (N개 추가하기) 결과 / (실패) 미리보기 + 위험 배너. "닫기"는 언제나 닫힘으로(입력 버림), "입력으로 돌아가기", "새 리스트 넣기"는 입력으로.
  - 파일 선택: 숨긴 `<input type="file" accept=".csv,text/csv,text/plain">` → `decodeCsv` → 텍스트 영역에 넣기. 실패 시 `'파일을 읽지 못했습니다. CSV(UTF-8 또는 엑셀 CSV)인지 확인하세요.'`.
  - 인식 0행이면 `'키워드를 찾지 못했습니다'`, 100자 초과가 있으면 `'100자를 넘는 N개는 제외했습니다'`.
  - 로딩 문구: `처리 중… 분류 없는 키워드 N개를 자동 분류하는 중 · 보통 10~40초 · 경과 m:ss` (N은 입력 분류 없는 행 수, 1초 타이머).
  - 미리보기: 상단 정보 배너 `'N행을 읽었습니다. 분류가 없던 M개는 자동 제안입니다. 확인하고 필요하면 바꾸세요.'`(M>0일 때), `classifyError`면 경고 배너 `'자동 분류에 실패했습니다(원인: {message}). 분류가 필요한 K개는 직접 고르거나 다시 시도하세요.'` + 다시 하기(`previewBulk(retryRows(rows))`, 편집 초기화). 표 열: 포함 체크 · 키워드 · 분류 `<select>`(값 `groupKey`, 옵션 `groups`, `needs_class`면 '분류 선택' 빈 옵션) · 분류 출처(입력값/자동 제안/분류 실패/직접 선택) · 상태 배지와 보조 문구. existing·중복 행은 체크 비활성·`kwb-off`. 일괄 변경 `Select` + `'모두 이 그룹으로'`(`applyToIncluded`).
  - 요청 번호: `useRef(0)`를 미리보기·다시 하기·파일 읽기·닫기마다 올리고, 응답이 올 때 번호가 다르면 무시한다(닫은 뒤 도착한 응답이 새 입력을 덮지 않게).
  - 다시 하기: `preview(retryRows(rows))` 후 `edits`를 **유지**한다(행 순서가 같으므로 제외·직접 선택이 남는다).
  - 추가: 버튼 문구 `{addableItems.length}개 추가하기`, `addableItems.length === 0 || disabled || 요청 중`이면 비활성(요청 중엔 `loading`) — 이중 클릭으로 두 번 요청하지 않는다. `add(addableItems(rows))` → `result`, 실패하면 미리보기 유지 + 카드 안 위험 배너. 결과 화면 건너뛴 행 표(`duplicate` → '이미 있음', `invalid` → '분류 오류'). "추가한 키워드 보기" → `onReveal(추가된 키워드의 고유 분류 목록)`.
  - `keywords.css`: 목업의 `kwb-*` 규칙과 640px 미디어 쿼리 그대로.
  - `page.tsx`: 방향 지시 `Card` 바로 다음, `running`이 아닐 때 `{(ui.canEdit || readonly) && <BulkAdd groups={groups} disabled={busy} readonly={readonly} preview={rows => previewBulk(sid, rows, version)} add={addViaQueue} onReveal={revealGroups} />}`.
    - `addViaQueue(items)`: 기존 `review`/`move`처럼 `action(async () => { try { result = await addBulk(sid, items, version) } catch (e) { failed = e; return } … }, true)`로 **페이지 작업 큐 안에서** 실행해 `busy`를 세운다(그동안 '다음 라운드 생성' 등 비활성). 성공 뒤 같은 작업 안에서 `reload()`; `reload` 실패는 추가 실패로 바꾸지 않고 페이지 `setError('추가는 완료했지만 목록을 새로 불러오지 못했습니다. 새로고침하세요.')`. 작업이 끝난 뒤 `failed`가 있으면 throw(카드가 배너 표시), 아니면 `result` 반환.
    - `revealGroups(gs)`: `setAxis('all'); setFilter('전체'); setQuery('')`와 각 그룹 `all:${groupKey(g)}`를 펼침(기존 `reveal`과 같은 방식).
    - 기존 동작은 바꾸지 않는다.

- [ ] **Step 4: 통과 확인** — `npm --prefix frontend test`, `run lint`, `run build` PASS. 워커는 dev 서버에서 키워드 화면을 열어 입력 → 미리보기 → 추가, 그리고 분류 중 닫기 → 새 입력(늦은 응답 무시)을 한 번씩 확인하고 화면 근거를 보고서에 남긴다(가짜 LLM 백엔드 설정 시 위 픽스처를 사용).

- [ ] **Step 5: READY_FOR_COMMIT** — `feat(keywords): 키워드 일괄 추가 카드`.


---

## 알려진 위험 (plan-eng-review에서 기록만)

- **검색량 조회 시간.** 500개 추가 시 검색광고 API를 5개씩 최대 100번 차례로 부른다(요청당 15초 제한, 첫 오류에서 중단 후 `request_failed`). 보통 1분 이내지만 느린 응답이 이어지면 300초 제한에 가까워질 수 있다. 기존 라운드 생성과 같은 함수라 이번 범위에서 바꾸지 않는다.
- **저장 후 이벤트 기록 실패.** 세션 저장 뒤 이벤트를 하나씩 기록하는 중 디스크 오류가 나면 키워드는 저장되고 일부 이벤트·피드백이 빠질 수 있다. 단건 추가(`add_manual`)와 같은 방식이며 이벤트는 피드백 표시용이다.
- **Codex 백엔드 한 번 호출이 600초까지 걸릴 수 있음**(`codex_timeout_s`). 그 경우 미리보기 요청이 300초 제한에 걸려 실패 배너가 뜨고 입력은 유지된다(QA-NEG-003과 같은 화면).

## 되돌리기

- 기능 전체: 이 브랜치의 Task 커밋 4개를 되돌리면 된다. 저장 데이터 형식은 바꾸지 않으므로(키워드는 기존 `manual` 형식) 이미 추가된 키워드는 되돌린 뒤에도 정상 표시된다.
- 부분: T4만 되돌리면 API는 남고 화면에서 사라진다.

## Self-Review

- 기획 AC1~AC11 → T3(AC1·AC2·AC3·AC9), T1(AC3·AC4·AC6·AC10), T4(AC5·AC9 안내), T2(AC6·AC7·AC8·AC10), 모든 Task Step 4(AC11).
- 설계 5절 오류 표의 각 줄 → T4 Step 3 문구로 대응. 6절 권한 → T1·T2 409 테스트.
- 이름 일관성: `previewBulk/addBulk`, `BulkPreviewRow.row`, `firstRow`, `duplicateOf`(미리보기는 객체, 추가 결과는 id 문자열 — 의도적으로 다름; 결과 화면은 id로 `groups`가 아닌 키워드 목록에서 찾지 않고 '이미 있음'만 표시).

## Plan Eng Review (2026-10-28)

대상: `03-plan.md` + `QA_PLAN-kw-bulk-input.md` (spec 01·02). 범위 결과: scope accepted as-is.

### Decision ledger

- **D1 구조** — 파일 12개·새 단위 2개(복잡도 게이트). 답: Original arrangement (recommended). 적용: 변경 없음.
- **D2 분류 동시성** — [P1] (confidence: 8/10) `nginx/dcx-agent.conf:36` `proxy_read_timeout 300s`, `scripts/systemd/dcx-backend.service` `--timeout 300`, `backend/app/config.py:25` `codex_timeout_s: int = 600`. 차례 호출 5번이면 300초 초과 가능. 답: 동시 5개 (recommended). 적용: T1 Step 3 `ThreadPoolExecutor(max_workers=5)` + Barrier 동시성 테스트.
- **D3 외부 검토 반영** — Codex 지적 10건 중 ①~⑧ 반영, 2건 위험 기록. 답: 모두 반영 (recommended). 적용: T1(공백 키워드 422·None 가드), T2(공백 invalid·경쟁 테스트 1회 가드), T3(따옴표 밖 탭·닫히지 않은 따옴표·retry 후 edits 유지), T4(props를 `preview`/`add`/`onReveal(groups)`로, 페이지 작업 큐로 추가, 요청 번호 가드, reload 실패 분리, 그룹 펼침), QA(R3·NEG-005·AUTOCOMPLETE_BACKEND·EDGE-009·EDGE-010), "알려진 위험" 절.

### 1. Architecture
- 경계: 저장 없는 미리보기와 잠금 안 1회 저장 분리 — 적절. LLM 호출은 잠금 밖(`suggest_words`와 같은 패턴).
- 실패 1건(경로별): 미리보기 LLM 지연 → D2. 추가 중 라운드 생성 경합 → D3①.
```
붙여넣기/CSV ─parseBulk─▶ rows ─POST /bulk/preview─▶ [lock: 중복 판정] ─▶ LLM 묶음×≤5 (동시) ─▶ 미리보기
미리보기 ─edits─▶ addableItems ─page action(busy)─▶ POST /bulk ─▶ volumes(잠금 밖) ─▶ [lock: 재중복 판정·저장 1회·이벤트] ─▶ reload
```

### 2. Code quality
- `rounds.manual_round` 분리로 단건·일괄이 round 규칙 공유(중복 제거, 기존 테스트로 보호).
- 설계와 달라지는 점 2건 계획 상단에 기록.

### 3. Tests
```
CODE PATHS                                   USER FLOWS
[+] bulk.preview                             [+] 붙여넣기→미리보기→추가   QA-E2E-001/002/005 [→E2E]
  ├── [★★★] 입력/기존/리스트 중복 T1          ├── CSV UTF-8/CP949           QA-E2E-003/004
  ├── [★★★] LLM 성공/목록 밖/실패 T1          ├── 분류 실패→직접 선택→재시도 QA-NEG-001
  ├── [★★★] 동시 묶음·행 순서 T1              ├── 닫기 후 늦은 응답         QA-EDGE-009
  └── [★★ ] 422/409 T1                        ├── 추가 중 다른 버튼 비활성  QA-EDGE-010
[+] bulk.add_many                            └── 모바일                    QA-EDGE-005
  ├── [★★★] 단건과 동일 저장·검색량 1회 T2
  ├── [★★★] 중복/invalid/공백 T2
  └── [★★★] 잠금 안 재중복(경쟁) T2
[+] bulkKeywords.ts  [★★★] 머리글/BOM/엑셀/따옴표/500/100자/디코딩/선택자 T3
[+] BulkAdd.tsx      [★★ ] 상태별 정적 렌더 T4 + 브라우저 QA
LLM integration: 가짜 백엔드만. 실제 분류 품질은 범위 밖(QA 1절).
```
- 회귀: 단건 추가·추천 단어·다음 라운드·이동(QA-REG-001~005), `manual_round` 분리는 기존 `test_rounds_api.py`가 보호.

### 4. Performance
- 검색량 조회 최대 100회 차례 호출 — 위험으로 기록(알려진 위험). 세션 저장 1회, 이벤트 N회 추가 쓰기 — 500건에서 허용 범위.

### Outside voice
- Codex(`codex exec`, read-only) 10건. 반영 8, 위험 기록 2(검색량 시간·저장 후 이벤트 실패). 반영 근거는 D3.

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|---|---|---|---|---|---|
| Eng Review | harness plan phase | 구현·QA 실행 가능성 확인 | 1 | DONE | 2 decisions (D2, D3) applied; structure kept (D1) |
| Outside Voice | default-on | 독립 검토 | 1 | DONE (codex) | 10 findings: 8 applied, 2 recorded as risks |

VERDICT: READY FOR PLAN APPROVAL — scope accepted as-is, all decisions resolved.
OUTSIDE COVERAGE / CROSS-MODEL: codex agreed on structure and concurrency; added 8 correctness fixes.

NO UNRESOLVED DECISIONS
