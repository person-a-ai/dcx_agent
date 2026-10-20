# v1-cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Under the development harness every task is implemented by a fresh Codex worker (`codex:codex-rescue --wait --fresh`, write mode), committed by the Controller, and reviewed by a different fresh Codex reviewer.

- 상태: 계획 승인 대기(제품 승인·설계 승인 2026-10-20 기록됨)
- 입력: [01-brainstorm.md](01-brainstorm.md) · [02-design.md](02-design.md) · 근거 조사 [plan.md](plan.md) · QA: [QA_PLAN-v1-cleanup.md](QA_PLAN-v1-cleanup.md)

**Goal:** DCX 1.0(v1) 코드를 main에서 걷어 내고, 전처리 전 새 세션이 v1 화면으로 빠지는 오분기를 사이드바 잠금 + 배너로 막는다.

**Architecture:** 백엔드는 ① v2가 쓰는 공용 함수를 `app/prep/documents.py`로 옮기고 ② 호환 파일(`preprocessed/`)을 없앤 뒤 ③ v1 라우터·서비스를 삭제한다. 프론트는 ④ 세 페이지와 사이드바가 같은 순수 함수 `laterStageGate`로 분기하게 하고 ⑤ 고아가 된 v1 화면·컴포넌트·API 함수를 삭제한다. 데이터 형식은 바꾸지 않는다(`desc`·`cafe`·`link` 유지).

**Tech Stack:** FastAPI · pytest(+xdist) · Python 3.12 / Next.js 16 · React 19 · vitest(node 환경, 컴포넌트를 함수로 호출하거나 `renderToStaticMarkup`) · eslint.

## Global Constraints

- 범위 밖, 수정 금지: `backend/app/routers/chat.py`, `/chat`, `/insight-chat`, `frontend/src/app/insights/layout.tsx`, `frontend/src/components/ChatPanel.tsx`, `sendChat`·`sendInsightChat`, `.worktrees/`, v2 라우터의 `is_legacy` 가드.
- 유지 필수(챗봇 의존): `app/services/s3.py`, `app/services/claude.py`, `app/jobs/manager.py`, `app/known/filter.py`, `models/schemas.py`의 `ChatRequest`·`InsightChatRequest`·`SearchRequest`·`SessionSaveRequest`, `app/services/voyage.py`(`vectors/embedder.py`가 씀).
- v2 전처리 문서에 `desc`(본문+댓글, 최대 4,000자)·`cafe`·`link`를 계속 붙인다.
- 배너 문구(정확히):
  - needs-prep: `3단계(전처리)를 먼저 완료하세요. 전처리가 끝나야 {단계 이름} 화면을 열 수 있습니다.` 버튼 `전처리 화면으로` → `/pipeline/preprocess` (variant `primary`)
  - legacy: `구버전 세션은 이 단계를 열 수 없습니다. 새 프로젝트를 만들어 진행하세요.` 버튼 `프로젝트 선택하기` → `/pipeline/start`
  - no-session: `프로젝트를 먼저 선택하세요.` 버튼 `프로젝트 선택하기` → `/pipeline/start`
  - 사이드바 잠금 툴팁: `전처리(3단계)를 먼저 완료하세요`
- 작업 디렉터리(모든 Task의 cwd): `/Users/yunho/Documents/dcx_agent-v1-cleanup` (하네스 `worktree` 명령으로 만든 `chore/v1-cleanup` 체크아웃). 백엔드 파이썬은 `backend/.venv/bin/python`.
- 모든 구현 dispatch에 그대로 넣는 문장: "Do not create Git commits. Complete the implementation and verification, then return READY_FOR_COMMIT with the exact changed-file list and a proposed commit message. Repository state transitions are owned by the controller."
- 워커는 `allowed_files` 밖을 고치지 않는다. 범위 밖 수정이 필요하면 BLOCKED로 돌려보낸다.
- RED는 **단언 실패**여야 한다(import 오류·환경 오류는 RED가 아님).
- 백엔드 전체 검사 기준선: `-n auto`에서 2842 통과·3 실패(타이밍 불안정 3개, 단독 실행 시 통과 — 01-brainstorm.md "기준선"). 각 Task 끝에서 같은 3개 외의 실패가 없어야 하고, 그 3개는 단독 재실행으로 통과를 보인다.

공통 검사 명령(각 Task의 마지막 단계):

```bash
backend/.venv/bin/python -m pytest backend/tests -q -p no:cacheprovider -n auto
npm --prefix frontend run lint
npm --prefix frontend test
npm --prefix frontend run build
```

---

## File Structure

| 파일 | 책임 | Task |
|---|---|---|
| `backend/app/prep/documents.py` (새) | collection 체인 읽기 + D-084~086 필터 + 내보내기 필드 | T1 |
| `backend/tests/prep/test_documents.py` (새) | 위 함수의 동작 고정(이전 `preprocess_data` 경유 테스트를 옮김) | T1 |
| `backend/tests/test_v1_boundary.py` (새) | 앱 코드가 v1 모듈을 import하지 않는다 + 지운 경로가 등록되지 않는다 | T1 생성, T3 확장 |
| `backend/app/prep/pipeline.py`, `backend/app/routers/prep.py` | 호환 파일 쓰기·검사 제거 | T2 |
| `backend/app/routers/*`, `backend/app/services/*`, `backend/app/main.py` 등 | v1 삭제 | T3 |
| `backend/requirements.txt`, `backend/constraints.txt`, `README.md`, `workflow.py` | 의존성·원형 정리 | T4 |
| `frontend/src/lib/logic/laterStageGate.ts` (새) | 6~9단계 열림 판단 순수 함수 | T5 |
| `frontend/src/components/LaterStageBanner.tsx` (새) | 세 배너 | T5 |
| `frontend/src/components/StepBar.tsx`, `frontend/src/app/globals.css`, 세 `page.tsx` | 분기 적용 | T5 |
| `frontend/src/lib/api.ts` 등 | v1 함수·고아 컴포넌트 삭제 | T6 |

Task 순서: T1 → T2 → T3 → T4 → T5 → T6 (T5·T6은 백엔드와 독립이지만 하네스는 Task마다 commit → 리뷰 PASS 후 다음으로 간다).

---

### Task 1: 전처리 공용 함수를 `app/prep/documents.py`로 옮기기

**allowed_files:**
- Create: `backend/app/prep/documents.py`, `backend/tests/prep/test_documents.py`, `backend/tests/test_v1_boundary.py`
- Modify: `backend/app/prep/pipeline.py` (21행 import, 195행 호출), `backend/app/services/preprocessing.py` (공용 함수 정의 제거 → `app.prep.documents`에서 import; `preprocess_data`는 T3까지 남김), `backend/tests/prep/test_pipeline.py` (189행 monkeypatch 대상), `backend/tests/crawl/test_final_w5.py`, `backend/tests/test_integration_stage0_2.py` (`test_preprocess_reads_collection_chain`, `test_quality_and_desc_limit`만)

**Interfaces:**
- Produces:
  - `app.prep.documents.crawl_docs(sid: str, session: dict) -> list[dict]`
  - `app.prep.documents.filter_documents(documents, ad_filter=(), excluded=(), min_body_chars=10, *, full_text=False) -> tuple[list[dict], dict[str, int]]` — 반환 dict 키: `ad`, `excluded_source`, `duplicate`, `too_short`
  - 비공개 도우미 `_export_fields(item: dict) -> dict`, `_passes_quality(item: dict, min_body_chars: int = 10) -> bool`

- [ ] **Step 1: 경계 테스트(RED) 작성** — `backend/tests/test_v1_boundary.py`

T1은 모듈 **최상위** import만 본다. `pipeline.py:118`의 함수 안 `from app.services import preprocessing`(`_publish_compat`)은 T2에서 함수와 함께 사라지고, T2가 함수 안 import까지 보는 테스트를 추가한다.

```python
"""v1 code must not be reachable from v2 modules (v1-cleanup)."""
import ast
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / 'app'


def top_level_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding='utf-8'))
    names = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
            names.update(f'{node.module}.{alias.name}' for alias in node.names)
        elif isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
    return names


def test_prep_package_does_not_import_v1_preprocessing():
    offenders = {str(p.relative_to(APP)): sorted(m for m in top_level_imports(p) if m.startswith('app.services.preprocessing'))
                 for p in (APP / 'prep').glob('*.py')}
    assert {k: v for k, v in offenders.items() if v} == {}
```

- [ ] **Step 2: RED 확인**

Run: `backend/.venv/bin/python -m pytest backend/tests/test_v1_boundary.py -q`
Expected: FAIL — `AssertionError: assert {'pipeline.py': ['app.services.preprocessing', 'app.services.preprocessing._crawl_docs', 'app.services.preprocessing.filter_documents']} == {}`

- [ ] **Step 3: 동작 고정 테스트를 옛 위치로 먼저 작성(GREEN 상태 확인용)** — `backend/tests/prep/test_documents.py`. 처음에는 `from app.services.preprocessing import _crawl_docs as crawl_docs, filter_documents`로 작성해 **현재 코드에서 통과**하는지 확인한 뒤(Step 4), Step 5에서 import만 `from app.prep.documents import crawl_docs, filter_documents`로 바꾼다.

```python
from contextlib import closing

import pytest

from app.context import store
from app.crawl.queue import CrawlQueue
from app.crawl.writer import DocWriter
from app.services.preprocessing import _crawl_docs as crawl_docs, filter_documents  # Step 5: from app.prep.documents import crawl_docs, filter_documents


def put_collection(data_dir, sid, cid, parent, docs):
    root = data_dir / 'crawl' / sid / 'collections' / cid
    store.write_json(root / 'manifest.json', {'id': cid, 'parent': parent})
    with closing(CrawlQueue(root / 'queue.sqlite')) as queue:
        queue.finish_run(queue.register_run('detail'), 'done')
    writer = DocWriter(root / 'docs')
    try:
        for doc in docs:
            writer.write(doc)
    finally:
        writer.close()


def document(doc_id, **kwargs):
    return dict(doc_id=doc_id, source='youtube', title='', body='충분히 긴 본문 내용입니다', comments=[{'text': '댓글 내용'}],
                src_meta={}, url=f'https://example.test/{doc_id}', fetch_level='full', **kwargs)


def test_collection_chain_child_wins_and_export_fields(data_dir):
    parent = document('shared')
    child = {**parent, 'body': '자식 수집본의 본문 내용입니다', 'src_meta': {'cafe': '지정 카페'}}
    put_collection(data_dir, 's', 'c1', None, [parent, document('parent')])
    put_collection(data_dir, 's', 'c2', 'c1', [child, document('child'), child])
    put_collection(data_dir, 's', 'c3', None, [document('unrelated')])
    raw = crawl_docs('s', {'collectionId': 'c2'})
    filtered, removed = filter_documents(raw)
    docs = {d['doc_id']: d for d in filtered}
    assert set(docs) == {'shared', 'parent', 'child'}
    assert docs['shared']['desc'] == child['body'] + '\n댓글 내용'
    assert docs['shared']['cafe'] == '지정 카페'
    assert docs['parent']['cafe'] == '유튜브'
    assert docs['shared']['link'] == child['url']
    assert all(docs['shared'][k] == v for k, v in child.items())
    assert removed == {'ad': 0, 'excluded_source': 0, 'duplicate': 0, 'too_short': 0}


@pytest.mark.parametrize('cid', ['', 'x1', 'c0', '../c1', None])
def test_crawl_docs_rejects_invalid_collection(data_dir, cid):
    with pytest.raises(ValueError):
        crawl_docs('s', {'collectionId': cid})


def test_crawl_docs_rejects_cycle(data_dir):
    put_collection(data_dir, 's', 'c1', 'c2', [document('a')])
    put_collection(data_dir, 's', 'c2', 'c1', [document('b')])
    with pytest.raises(ValueError, match='Cyclic'):
        crawl_docs('s', {'collectionId': 'c1'})


def test_quality_rules_and_desc_limit():
    docs = [document('full'), {**document('short'), 'body': '짧음'},
            {**document('long'), 'body': '긴' * 4100},
            {**document('snippet_ok'), 'fetch_level': 'snippet', 'title': '다섯글자제목', 'body': '', 'snippet': '충분히 긴 설명 내용입니다'},
            {**document('snippet_bad_title'), 'fetch_level': 'snippet', 'title': '짧음', 'snippet': '충분히 긴 설명 내용입니다'},
            {**document('snippet_bad_desc'), 'fetch_level': 'snippet', 'title': '다섯글자제목', 'body': '', 'snippet': '짧음'},
            {**document('snippet_both_short'), 'fetch_level': 'snippet', 'title': '짧음', 'body': '', 'snippet': '짧음'}]
    filtered, removed = filter_documents(docs)
    result = {d['doc_id']: d for d in filtered}
    assert set(result) == {'full', 'long', 'snippet_ok', 'snippet_bad_title', 'snippet_bad_desc'}
    assert result['long']['desc'] == '긴' * 4000
    assert removed['too_short'] == 2


def test_excludes_cafe_name_and_slug_not_body():
    docs = [
        {'doc_id': 'name', 'src_meta': {'cafe': 'Joong market'}},
        {'doc_id': 'slug', 'src_meta': {'cafe': '중고나라', 'cafe_id': 'joonggonara'}},
        {'doc_id': 'keep', 'src_meta': {'cafe': 'Other', 'cafe_id': 'other', 'note': 'joong'}},
        {'doc_id': 'no_meta'},
    ]
    docs = [{**doc, 'body': 'joong in article content is retained', 'fetch_level': 'full'} for doc in docs]
    filtered, removed = filter_documents(docs, excluded=['JOONG'])
    assert [doc['doc_id'] for doc in filtered] == ['keep', 'no_meta']
    assert removed['excluded_source'] == 2


def test_full_text_ads_channel_exclusion_and_duplicates():
    docs = [{**document('ad'), 'comments': [{'text': '협찬 받은 글'}]},
            {**document('chan'), 'source': 'naver_blog'},
            document('dup'), document('dup')]
    filtered, removed = filter_documents(docs, ad_filter=['협찬'], excluded=['naver_blog'], full_text=True)
    assert [d['doc_id'] for d in filtered] == ['dup']
    assert removed == {'ad': 1, 'excluded_source': 1, 'duplicate': 1, 'too_short': 0}
    assert filtered[0]['idx'] == 2
```

- [ ] **Step 4: 옛 위치에서 통과 확인**

Run: `backend/.venv/bin/python -m pytest backend/tests/prep/test_documents.py -q`
Expected: PASS (`test_crawl_docs_rejects_invalid_collection`의 `''`·`None`은 지금 코드가 `load_data(f"crawl/{sid}/")`로 넘어가 **실패**한다 — 이 두 경우는 옛 분기 삭제를 증명하는 두 번째 RED다. 실패 메시지를 기록해 둔다: `Failed: DID NOT RAISE <class 'ValueError'>`.)

- [ ] **Step 5: `app/prep/documents.py` 작성 + 호출처 바꾸기**

```python
"""Stage-three document intake shared by the prep pipeline (moved from services/preprocessing, v1-cleanup)."""
import json
from pathlib import Path
import re

from app.config import settings
from app.context.labels import LABELS
from app.crawl.writer import read_docs


def crawl_docs(sid: str, session: dict) -> list[dict]:
    """Read the active collection chain child-first so the child's doc_id wins."""
    cid = session.get('collectionId')
    base = Path(settings.local_data_dir) / 'crawl' / sid / 'collections'
    collections = set()
    docs = {}
    while True:
        if not isinstance(cid, str) or not re.fullmatch(r'c[1-9][0-9]*', cid):
            raise ValueError('Invalid crawl collection id')
        if cid in collections:
            raise ValueError('Cyclic crawl collection chain')
        collections.add(cid)
        root = base / cid
        try:
            manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
        except (OSError, ValueError):
            raise ValueError(f'수집본을 읽을 수 없습니다 ({cid})') from None
        for doc in read_docs(root / 'docs'):
            docs.setdefault(doc['doc_id'], doc)
        cid = manifest.get('parent')
        if not cid:
            return list(docs.values())


def _export_fields(item: dict) -> dict:
    """desc/cafe/link are read by the stage-five export (model/export.py) and the chat search results."""
    source = item.get('source', '')
    comments = '\n'.join(comment.get('text', '') for comment in item.get('comments', []))
    return {
        **item,
        'desc': (item.get('body', '') + '\n' + comments)[:4000],
        'cafe': item.get('src_meta', {}).get('cafe') or LABELS['channels'].get(source, source),
        'link': item.get('url', ''),
    }


def _passes_quality(item: dict, min_body_chars: int = 10) -> bool:
    if item.get('fetch_level') == 'snippet':
        description = item.get('snippet', '') or item.get('body', '')
        return len(item.get('title', '')) >= 5 or len(description) >= 10
    # Full documents (including title-less YouTube threads) use body alone.
    return len(item.get('body', '')) >= min_body_chars


def filter_documents(documents, ad_filter=(), excluded=(), min_body_chars=10, *, full_text=False):
    """D-084–086 rules; full_text uses uncapped body/comments for ad matching."""
    seen = set()
    filtered = []
    removed = dict(ad=0, excluded_source=0, duplicate=0, too_short=0)
    for idx, raw in enumerate(documents):
        item = _export_fields(raw)
        text = item.get('title', '') + ' ' + item.get('desc', '')
        if full_text:
            text = item.get('body', '') + '\n' + '\n'.join(
                c.get('text', '') for c in item.get('comments', []))
        cafe = item.get('cafe', '').lower()
        cafe_id = str((item.get('src_meta') or {}).get('cafe_id') or '').lower()
        identity = item['doc_id']
        reason = None
        if any(ad.lower() in text.lower() for ad in ad_filter):
            reason = 'ad'
        elif any(ex.lower() in cafe or ex.lower() in cafe_id or
                 (full_text and ex.lower() == item.get('source', '').lower()) for ex in excluded):
            reason = 'excluded_source'
        elif identity in seen:
            reason = 'duplicate'
        else:
            seen.add(identity)
            if not _passes_quality(item, min_body_chars):
                reason = 'too_short'
        if reason:
            removed[reason] += 1
            continue
        item['idx'] = idx
        filtered.append(item)
    return filtered, removed
```

주의(동작 동일성): 원본 `_crawl_docs`는 `while cid:` 루프였다. 위 코드는 첫 cid가 비면 바로 `ValueError`를 내고(옛 `crawl/{sid}/` 분기 삭제), 부모 체인은 `parent`가 비면 끝낸다 — 원본과 같은 순서·결과다. `doc_id` 없는 옛 문서 분기 두 곳은 삭제했다(`crawl_docs`가 `doc['doc_id']`로 색인하므로 v2 문서에는 항상 있다).

`backend/app/prep/pipeline.py`:
- 21행 `from app.services.preprocessing import _crawl_docs, filter_documents` → `from app.prep.documents import crawl_docs, filter_documents`
- 195행 `documents = _crawl_docs(sid, session=session)` → `documents = crawl_docs(sid, session)`
- 118행 함수 안 import(`_publish_compat`)는 **건드리지 않는다**(T2).

`backend/app/services/preprocessing.py`: `_crawl_docs`, `_compat_fields`, `_passes_quality`, `filter_documents` 정의를 지우고 맨 위에 `from app.prep.documents import crawl_docs, filter_documents`. `preprocess_data`의 `all_data = _crawl_docs(sid)` → `all_data = crawl_docs(sid, session)`(바로 위에서 읽은 `session`). `preprocess_data`의 옛 세션 경로(collection 없음)는 이제 `ValueError`로 `status: error`가 된다 — 이 파일 전체가 T3에서 지워지므로 허용한다.

테스트 이동:
- `backend/tests/prep/test_documents.py` 맨 위 import를 `from app.prep.documents import crawl_docs, filter_documents`로.
- `backend/tests/prep/test_pipeline.py:189` `monkeypatch.setattr(pipeline, '_crawl_docs', forbidden)` → `monkeypatch.setattr(pipeline, 'crawl_docs', forbidden)`.
- `backend/tests/test_integration_stage0_2.py`: `test_preprocess_reads_collection_chain`, `test_quality_and_desc_limit` 삭제(→ `test_documents.py`의 `test_collection_chain_child_wins_and_export_fields`, `test_quality_rules_and_desc_limit`가 같은 단언을 가짐). `put_collection`·`document` 도우미는 다른 테스트가 쓰지 않으면 함께 삭제(grep으로 확인).
- `backend/tests/crawl/test_final_w5.py`: `from app.services import preprocessing` 삭제, `from app.prep.documents import crawl_docs` 추가. `test_finish_partial`의 마지막 부분을

```python
    assert [doc['doc_id'] for doc in crawl_docs('S', store.load_session('S'))] == ['collected']
```

  로 바꾼다(`saved`, `monkeypatch.setattr(preprocessing, …)`, `preprocess_data` 줄 삭제; 함수 시그니처의 `monkeypatch` 인자는 쓰지 않으면 제거). `test_preprocess_excludes_cafe_name_and_slug`는 삭제(→ `test_excludes_cafe_name_and_slug_not_body`; 문자열 `' JOONG , unused '` 쪼개기는 v1 `preprocess_data` 전용 입력 파싱이라 옮기지 않음).

- [ ] **Step 6: GREEN 확인**

Run: `backend/.venv/bin/python -m pytest backend/tests/test_v1_boundary.py backend/tests/prep backend/tests/crawl/test_final_w5.py backend/tests/test_integration_stage0_2.py -q`
Expected: PASS

- [ ] **Step 7: 공통 검사 4개 실행**, 결과를 보고서에 기록 후 READY_FOR_COMMIT.

제안 커밋 메시지: `refactor(prep): 전처리 공용 함수를 app/prep/documents.py로 옮김`

---

### Task 2: 호환 파일 `preprocessed/{sid}/*.jsonl` 제거 (D-065)

**allowed_files:**
- Modify: `backend/app/prep/pipeline.py`, `backend/app/routers/prep.py`, `backend/tests/test_v1_boundary.py`, `backend/tests/prep/test_pipeline.py`, `backend/tests/prep/test_prep_api.py`, `backend/tests/test_review_fix1.py`, `backend/tests/test_integration_stage0_2.py` (`offline` 픽스처와 `full_flow`만)

**Interfaces:**
- Consumes: T1의 `crawl_docs`, `filter_documents`.
- Produces: `/prep/{sid}/run` 재사용 조건 = `manifest.collectionFinalized is True and manifest.status == 'done' and (root/'stage_3.json').exists()`.

- [ ] **Step 1: RED 테스트 작성**

`backend/tests/test_v1_boundary.py`에 추가(이번엔 함수 안 import까지 본다 — Step 1의 `imported_modules`):

```python
def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding='utf-8'))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
            names.update(f'{node.module}.{alias.name}' for alias in node.names)
        elif isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
    return names


def test_prep_package_has_no_nested_v1_import():
    offenders = {str(p.relative_to(APP)): sorted(m for m in imported_modules(p) if m.startswith('app.services.preprocessing'))
                 for p in (APP / 'prep').glob('*.py')}
    assert {k: v for k, v in offenders.items() if v} == {}
```

`backend/tests/prep/test_pipeline.py`의 `test_version_snapshot_and_compat_output`를 `test_version_snapshot_writes_no_compat_output`로 이름을 바꾸고 마지막 두 줄을

```python
    assert not (data_dir / 'preprocessed').exists()
    assert 'compatRef' not in store.read_json(root / 'manifest.json')
```

로 바꾼다.

`backend/tests/prep/test_prep_api.py`에 추가:

```python
def test_finished_result_reused_without_compat_file(collected, data_dir):
    configure(collected)
    assert collected.post('/prep/s/run').status_code == 200
    first = finished(collected)
    assert first['status'] == 'done', first
    assert not (data_dir / 'preprocessed').exists()
    response = collected.post('/prep/s/run')
    assert response.status_code == 200, response.text
    assert response.json()['reused'] is True
```

- [ ] **Step 2: RED 확인**

Run: `backend/.venv/bin/python -m pytest backend/tests/test_v1_boundary.py backend/tests/prep/test_pipeline.py::test_version_snapshot_writes_no_compat_output backend/tests/prep/test_prep_api.py::test_finished_result_reused_without_compat_file -q`
Expected: 3 FAIL — 경계 테스트 `{'pipeline.py': ['app.services', 'app.services.preprocessing']} == {}` 형태(118행), `assert not PosixPath('…/preprocessed').exists()`, 마지막은 `assert not …preprocessed…exists()`.

- [ ] **Step 3: 구현**

`backend/app/prep/pipeline.py`:
- `_publish_compat` 함수(114~125행) 삭제.
- `_publish` 첫 줄 `_publish_compat(root, manifest)` 삭제.
- 새 manifest dict(190행)에서 `compatRef=f'preprocessed/{sid}/{time.time_ns()}.jsonl'` 삭제.
- `_run`의 `_publish_compat(root, manifest)`(239행) 삭제. 그 위 주석 `# Complete document/token preparation and the legacy export before any vectors.` → `# Complete document/token preparation before any vectors.`
- `time` import가 더 이상 안 쓰이면 남겨 둔다(다른 곳에서 `time.sleep` 사용 — 확인 후 판단).

`backend/app/routers/prep.py` 107~111행 조건을

```python
        if (manifest and manifest.get('collectionFinalized') is True and manifest.get('status') == 'done'
                and (root / 'stage_3.json').exists()):
```

로 바꾼다. `settings`·`Path` import가 이 파일에서 더 안 쓰이면 지운다.

테스트 정리:
- `backend/tests/prep/test_pipeline.py::test_unconnected_exports_before_embedding`: `entry` 파라미터와 `legacy_service` 분기, `preprocessing` import, `save` 가로채기를 지우고 다음으로 바꾼다.

```python
@pytest.mark.parametrize('failure_at', ['factory', 'embed'])
def test_unconnected_keeps_documents_before_embedding(setup, monkeypatch, data_dir, failure_at):
    from app.vectors.embedder import EmbedderUnconnected

    setup([doc('one'), doc('two')], {'embedder': 'voyage'})
    monkeypatch.setattr(settings, 'embed_backend', 'voyage')
    monkeypatch.setattr(pipeline, 'SHARD_ROWS', 1)
    identity = Embedder()
    identity.name = 'voyage'
    root = data_dir / 'derived/s/c1' / prep_key('c1', PrepConfig(embedder='voyage'), identity)

    def unconnected():
        raise EmbedderUnconnected('not configured')

    def embed(texts):
        assert len(rows(root, 'docs')) == len(rows(root, 'tokens')) == 2
        raise EmbedderUnconnected('not configured')

    identity.embed = embed
    monkeypatch.setattr(pipeline, 'get_embedder', unconnected if failure_at == 'factory' else lambda: identity)
    with pytest.raises(EmbedderUnconnected):
        pipeline.run_prep(Context(), 's', 'v1')
    docs = rows(root, 'docs')
    assert [d['doc_id'] for d in docs] == ['one', 'two']
    assert all({'desc', 'cafe', 'link'} <= d.keys() for d in docs)
    manifest = store.read_json(root / 'manifest.json')
    assert manifest['status'] == 'failed' and 'compatRef' not in manifest
    assert not (data_dir / 'preprocessed').exists()
    assert not list((root / 'vectors').glob('*.f16'))
    assert VectorStore(root).count() == 0
    assert store.load_session('s')['prep'].get('status') != 'done'
```

- `backend/tests/test_review_fix1.py`: 픽스처 manifest 4곳의 `compatWritten=True, compatRef='compat.jsonl'`과 `(data_dir / 'compat.jsonl').write_text('')` 줄 삭제. 단언은 그대로(`test_c3_unfinished_crawl_cannot_start_or_reuse` 409, `test_c3_unverified_old_result_not_reused_after_finalization` reused False, `test_g5_same_ref_reuse_allowed_after_labeling` 200).
- `backend/tests/test_integration_stage0_2.py::full_flow`: `/preprocess` 왕복(지금 115~123행)을 v2 경로로 바꾼다.

```python
    request('PUT', f'/prep/{sid}/config', json={'embedder': 'fake'})
    request('POST', f'/prep/{sid}/run')
    deadline = time.monotonic() + 30
    while True:
        prep_status = request('GET', f'/prep/{sid}/status')
        if prep_status['status'] in {'done', 'failed', 'interrupted'} or time.monotonic() > deadline:
            break
        time.sleep(.05)
    assert prep_status['status'] == 'done', prep_status
    ref = store.load_session(sid)['prep']['derivedRef']
    docs = load_data(f"derived/{sid}/{ref['collectionId']}/{ref['prepKey']}/docs/")
    assert len(docs) == 200
    assert all(d['desc'] == d['body'] + '\n' and d['cafe'] == '개발용 샘플' and d['link'] == d['url'] for d in docs)
```

  prep 워커는 **하위 프로세스**로 돈다(`app/work/runner.py:39`, `subprocess.Popen(..., env=dict(os.environ, ...))`). `offline` 픽스처의 `monkeypatch.setattr(settings, …)`는 하위 프로세스에 닿지 않으므로, 같은 파일의 `offline` 픽스처 맨 앞에 `prep/test_prep_api.py::collected`와 같은 환경 변수를 넣는다:

```python
    for name, value in {'STORAGE': 'local', 'EMBED_BACKEND': 'fake', 'EMBED_MODEL': 'voyage-4',
                        'EMBED_DIM': '1024', 'VOYAGE_API_KEY': ''}.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(settings, 'voyage_api_key', '')
```

  (`test_no_api_keys_full_run`의 "키 없이 끝까지" 단언과도 맞는다.)

- [ ] **Step 4: GREEN 확인**

Run: `backend/.venv/bin/python -m pytest backend/tests/test_v1_boundary.py backend/tests/prep backend/tests/test_review_fix1.py backend/tests/test_integration_stage0_2.py -q`
Expected: PASS

- [ ] **Step 5: 공통 검사 4개** → READY_FOR_COMMIT. 제안 커밋 메시지: `refactor(prep): 호환 파일 preprocessed/ 쓰기와 재사용 조건에서 제거 (D-065)`

---

### Task 3: v1 백엔드 경로·서비스 삭제

**allowed_files:**
- Delete: `backend/app/routers/keywords.py`, `backend/app/routers/labeling.py`, `backend/app/routers/training.py`, `backend/app/routers/preprocessing.py`, `backend/app/routers/clustering.py`, `backend/app/routers/embedding.py`, `backend/app/routers/personas.py`, `backend/app/services/training.py`, `backend/app/services/preprocessing.py`, `backend/app/services/clustering.py`, `backend/app/services/embedding.py`, `backend/app/services/personas.py`, `backend/app/context/compat.py`
- Modify: `backend/app/main.py`, `backend/app/models/schemas.py`, `backend/app/utils/text.py`, `backend/tests/test_v1_boundary.py`, `backend/tests/test_integration_stage0_2.py`, `backend/tests/test_integration_stage3_5.py`, `backend/tests/test_review_fix1.py`, `backend/tests/known/test_known.py`, `backend/tests/context/test_session_completion.py`, `backend/tests/context/test_versions.py`, `backend/tests/context/test_api.py`, `backend/tests/model/test_model_mode.py`, `backend/BACKEND.md`, `frontend/PIPELINE.md`

**Interfaces:**
- Consumes: T1·T2 결과(`services/preprocessing.py`에 남은 건 `preprocess_data`뿐).
- Produces: 앱 라우트에서 아래 13개 경로가 사라짐.

- [ ] **Step 1: RED 테스트 추가** — `backend/tests/test_v1_boundary.py`

```python
from app.main import app

REMOVED = {('POST', '/train'), ('GET', '/train-status/{sid}'), ('POST', '/preprocess'), ('GET', '/preprocess-status/{sid}'),
           ('GET', '/sample/{sid}'), ('POST', '/cluster'), ('GET', '/cluster-status/{sid}'), ('POST', '/cluster-refine'),
           ('POST', '/embed'), ('GET', '/embed-status/{sid}'), ('POST', '/persona'), ('GET', '/persona-status/{sid}'),
           ('GET', '/sna-data/{sid}')}
KEPT = {('POST', '/chat'), ('POST', '/insight-chat'), ('POST', '/search'), ('GET', '/sessions'), ('GET', '/session/{sid}'),
        ('POST', '/save-session'), ('POST', '/prep/{sid}/run'), ('GET', '/health')}
V1_MODULES = ('app.services.preprocessing', 'app.services.training', 'app.services.clustering',
              'app.services.embedding', 'app.services.personas', 'app.context.compat',
              'app.routers.labeling', 'app.routers.training', 'app.routers.preprocessing',
              'app.routers.clustering', 'app.routers.embedding', 'app.routers.personas', 'app.routers.keywords')


def registered():
    return {(method, route.path) for route in app.routes for method in getattr(route, 'methods', ()) or ()}


def test_v1_routes_removed_and_chat_kept():
    routes = registered()
    assert REMOVED & routes == set()
    assert KEPT <= routes


def test_app_imports_no_v1_module():
    offenders = {}
    for path in APP.rglob('*.py'):
        hits = sorted(m for m in imported_modules(path) for v1 in V1_MODULES if m == v1 or m.startswith(v1 + '.'))
        if hits:
            offenders[str(path.relative_to(APP))] = hits
    assert offenders == {}
```

(`from app.services import clustering` 같은 형태는 `imported_modules`가 `app.services.clustering`으로 만든다.)

- [ ] **Step 2: RED 확인**

Run: `backend/.venv/bin/python -m pytest backend/tests/test_v1_boundary.py -q`
Expected: 2 FAIL — 첫째는 `REMOVED & routes`에 13개가 남아 있다는 단언 실패, 둘째는 `main.py`·`routers/*.py` 등 offender 목록.

- [ ] **Step 3: 삭제**

- 위 Delete 목록 13개 파일 삭제.
- `backend/app/main.py`: import 목록과 `include_router`에서 `keywords`, `preprocessing`, `labeling`, `training`, `clustering`, `embedding`, `personas` 제거.
- `backend/app/models/schemas.py`: `CrawlRequest`, `PreprocessRequest`, `TrainRequest`, `ClusterRequest`, `ClusterRefineRequest`, `EmbedRequest`, `PersonaRequest`, `KeywordGenRequest`, `ScoreKeywordsRequest`, `SuggestWordsRequest` 삭제(남는 것: `SessionSaveRequest`, `SearchRequest`, `ChatRequest`, `InsightChatRequest`). 쓰지 않게 된 import도 정리.
- `backend/app/utils/text.py`: `get_llm_predictions` 삭제(`clean_text` 유지). 쓰지 않게 된 import 정리.

- [ ] **Step 4: 테스트 정리** (각 항목은 v1 전용임을 확인한 뒤 삭제. v2 단언이 섞여 있으면 그 부분은 남긴다)

| 파일 | 처리 |
|---|---|
| `tests/test_integration_stage0_2.py` | 삭제: `from app.services.preprocessing import preprocess_data`, `test_legacy_session_preprocess_still_reads_old_crawl`, `test_downstream_clustering_reads_compat_fields`, `test_downstream_context_fallback`, `test_downstream_unavailable_context`, `test_fallback_unavailable_leaves_config_unchanged`, `test_fallback_preserves_explicit_values`. `test_missing_manifest_status_hides_path`는 아래로 교체 |
| `tests/test_review_fix1.py` | 삭제: `test_c3_legacy_endpoint_rejects_unfinished`, `test_legacy_direct_service_guard`. `test_g5_changed_prep_identity_locked`·`test_g5_same_ref_reuse_allowed_after_labeling`에서 `legacy` 파라미터와 `app.routers.preprocessing.threading` monkeypatch 삭제(항상 `/prep/prepcheck/run`) |
| `tests/test_integration_stage3_5.py::test_end_to_end_fixture` | `from app.services import clustering`과 `api_calls = []`부터 끝(군집 부분)까지 삭제. 내보내기 단언(`rows` 검사)까지 유지. 쓰지 않게 된 import(`job_manager` 등) 정리 |
| `tests/known/test_known.py` | 삭제: `test_clustering_reads_store_no_embed_calls`, `test_clustering_input_is_core_supporting_only`, `test_zero_vectors_and_missing_export`, `test_personas_queries_batched`, `test_embedding_immediately_done`, `test_clustering_follows_inherited_export_ref`, 픽스처 `persona_prompt`, `test_persona_fallback_reasons_and_known_exclusion`, `test_persona_skips_empty_queries`. `test_zero_vectors_and_missing_export`에 search/known 단언이 섞였다면 그 부분만 새 테스트로 남긴다 |
| `tests/context/test_session_completion.py` | 삭제: 픽스처 `cluster_service`, `test_clustering_publishes_version_local_completion_surviving_restart`, `test_failed_cluster_publication_preserves_stale`, `test_cluster_cannot_complete_a_different_active_version` |
| `tests/context/test_versions.py`, `tests/context/test_api.py` | `from app.services.training import load_json` → `from app.services.s3 import load_json` |
| `tests/model/test_model_mode.py` | 삭제: `test_legacy_train_is_readonly` |

`test_missing_manifest_status_hides_path` 교체:

```python
def test_missing_manifest_run_hides_path(client, data_dir):
    sid = client.post('/context', json=CTX).json()['sid']
    store.update_session(sid, {'collectionId': 'c2'})
    response = client.post(f'/prep/{sid}/run')
    assert response.status_code == 409
    assert response.json()['error']['message'] == '수집이 끝난 뒤에 전처리를 실행할 수 있습니다.'
    assert str(data_dir) not in response.text
```

- [ ] **Step 5: 문서** — `backend/BACKEND.md` 141~182행의 지운 함수 표 행, 403행 `preprocessed/{sid}/{ts}.jsonl` 행, 424~436행의 지운 경로 행을 삭제하고, 그 자리에 v2 경로(`/prep/{sid}/*`, `/label/{sid}/*`, `/train/{sid}/*`, `/segment/{sid}/*`, `/evidence/{sid}/*`, `/persona/{sid}/*`, `/insight/{sid}/*`)를 가리키는 한 줄을 둔다. `frontend/PIPELINE.md` 200~214·254·306·353~354·421~424·443행도 같은 방식.

- [ ] **Step 6: GREEN 확인**

Run: `backend/.venv/bin/python -m pytest backend/tests/test_v1_boundary.py -q && grep -rn "app.services.preprocessing\|_publish_compat\|compatRef\|services.training\|routers.labeling\|context.compat" backend/app ; test $? -eq 1`
Expected: PASS, grep 0건

- [ ] **Step 7: 공통 검사 4개** → READY_FOR_COMMIT. 제안 커밋 메시지: `chore(v1): v1 백엔드 경로·서비스 삭제`

---

### Task 4: 쓰지 않는 의존성 `crawl4ai`와 루트 `workflow.py` 정리

**allowed_files:**
- Delete: `workflow.py`
- Modify: `backend/requirements.txt`, `backend/constraints.txt`, `README.md`, `backend/tests/ops/test_v1_dependencies.py` (Create)

- [ ] **Step 1: RED 테스트** — `backend/tests/ops/test_v1_dependencies.py`

```python
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_crawl4ai_not_required_or_documented():
    assert 'crawl4ai' not in (ROOT / 'backend/requirements.txt').read_text(encoding='utf-8')
    assert 'crawl4ai' not in (ROOT / 'backend/constraints.txt').read_text(encoding='utf-8')
    assert 'crawl4ai' not in (ROOT / 'README.md').read_text(encoding='utf-8')


def test_flask_prototype_removed():
    assert not (ROOT / 'workflow.py').exists()
```

- [ ] **Step 2: RED 확인** — Run: `backend/.venv/bin/python -m pytest backend/tests/ops/test_v1_dependencies.py -q` · Expected: 2 FAIL (`assert 'crawl4ai' not in …`, `assert not True`).

- [ ] **Step 3: 구현**
  1. `backend/requirements.txt`에서 `crawl4ai` 줄 삭제.
  2. crawl4ai만 끌어오던 고정 찾기: 임시 venv(`python3.12 -m venv /tmp/v1c-a` 대신 워크트리 밖 스크래치 경로)에 원래 `requirements.txt`로, 다른 임시 venv에 수정본으로 `pip install -r … -c constraints.txt` 후 `pip freeze` 두 결과의 차이를 구한다. 차이에 있는 패키지 중 `constraints.txt`에 있는 줄만 삭제(예상: `crawl4ai`, `playwright`, `playwright-stealth` 등). 차이 목록을 보고서 notes에 남긴다. 다른 패키지가 같은 의존성을 쓰면 남긴다(차이에 없으니 자동으로 남음).
  3. `README.md` 103행 `crawl4ai-setup` 줄과 107행 설명 줄 삭제. `test_review_fix1.py::test_g6_environment_documentation`이 보는 환경변수 이름은 건드리지 않는다.
  4. `workflow.py` 삭제(어디서도 import·실행하지 않음: `grep -rn "workflow" ops scripts nginx .github README.md backend/BACKEND.md` 0건 확인 후).

- [ ] **Step 4: GREEN** — 같은 명령 PASS. 수정한 `requirements.txt`+`constraints.txt`로 새 venv 설치가 성공하는지 확인(`pip install … -c constraints.txt` 종료 코드 0).

- [ ] **Step 5: 공통 검사 4개** → READY_FOR_COMMIT. 제안 커밋 메시지: `chore(deps): 쓰지 않는 crawl4ai와 Flask 원형 workflow.py 삭제`

---

### Task 5: 전처리 전 세션의 사이드바 잠금 + 세 페이지 배너

**allowed_files:**
- Create: `frontend/src/lib/logic/laterStageGate.ts`, `frontend/src/lib/logic/laterStageGate.test.ts`, `frontend/src/components/LaterStageBanner.tsx`, `frontend/src/components/LaterStageBanner.test.ts`, `frontend/src/app/pipeline/personas/page.test.ts`
- Modify: `frontend/src/components/StepBar.tsx`, `frontend/src/app/globals.css`, `frontend/src/app/pipeline/clustering/page.tsx`, `frontend/src/app/pipeline/personas/page.tsx`, `frontend/src/app/pipeline/insights/page.tsx`, `frontend/src/app/pipeline/clustering/page.test.ts`, `frontend/src/components/persona/insight-route.test.ts`, `frontend/src/components/persona/insight.test.ts`, `frontend/src/lib/logic/completedThrough.test.ts`

**Interfaces:**
- Produces:
  - `laterStageGate(sid: string | null | undefined, session: Record<string, unknown> | null | undefined): LaterStageGate` where `type LaterStageGate = 'no-session' | 'legacy' | 'needs-prep' | 'open'`
  - `laterStagesOpen(session: Record<string, unknown> | null | undefined): boolean`
  - `LATER_STAGE_LOCK_TITLE = '전처리(3단계)를 먼저 완료하세요'`
  - `LaterStageBanner({ gate, stage }: { gate: Exclude<LaterStageGate, 'open'>; stage: string })` (React 컴포넌트)

- [ ] **Step 1: RED 테스트** — `frontend/src/lib/logic/laterStageGate.test.ts`

```ts
import { describe, expect, it } from 'vitest';
import { laterStageGate, laterStagesOpen } from './laterStageGate';

describe('laterStageGate', () => {
  it.each([
    [null, {schemaVersion: 2, prep: {derivedRef: {prepKey: 'p'}}}, 'no-session'],
    ['s', null, 'no-session'],
    ['s', {schemaVersion: 2, prep: {derivedRef: {prepKey: 'p'}}}, 'open'],
    ['s', {schemaVersion: 2}, 'needs-prep'],
    ['s', {schemaVersion: 2, prep: {status: 'running'}}, 'needs-prep'],
    ['s', {step: 'clustering'}, 'legacy'],
    ['s', {prep: {derivedRef: ''}}, 'legacy'],
  ] as const)('sid=%j session=%j → %s', (sid, session, expected) => {
    expect(laterStageGate(sid, session as Record<string, unknown> | null)).toBe(expected);
  });
  it('opens later stages only with a derived reference', () => {
    expect(laterStagesOpen({prep: {derivedRef: {prepKey: 'p'}}})).toBe(true);
    expect(laterStagesOpen({prep: {}})).toBe(false);
    expect(laterStagesOpen(undefined)).toBe(false);
  });
});
```

기존 테스트 기대값 변경(같은 Step에서):

- `frontend/src/lib/logic/completedThrough.test.ts`의 `'renders the ten stages in order with evidence disabled and personas and insights navigable'`를 두 테스트로 바꾼다.

```ts
function lockedTag(html: string, name: string) {
  return html.match(new RegExp(`<([a-z]+)\\b([^>]*aria-label="[^"]*${name}[^"]*"[^>]*)>`));
}

it('locks clustering, evidence, personas and insights until preprocessing is derived', () => {
  const html = sidebar('start');
  const names = [...html.matchAll(/<span>([^<]+)<\/span>/g)].map(match => match[1]);
  expect(names).toEqual(['시작', '키워드', '크롤링', '전처리', '라벨링', '학습', '클러스터링', '근거 탐색', '페르소나', '인사이트']);
  for (const name of ['클러스터링', '근거 탐색', '페르소나', '인사이트']) {
    const tag = lockedTag(html, name);
    expect(tag).not.toBeNull();
    expect(tag![2]).toContain('aria-disabled="true"');
    expect(tag![2]).toContain('title="전처리(3단계)를 먼저 완료하세요"');
    expect(tag![2]).not.toMatch(/\bhref=/);
  }
  expect([...html.matchAll(/\bhref="([^"]+)"/g)].map(match => match[1])).toEqual([
    '/pipeline/start', '/pipeline/keywords', '/pipeline/crawling', '/pipeline/preprocess', '/pipeline/labeling', '/pipeline/training',
  ]);
});

it('opens every stage once preprocessing is derived', () => {
  const html = sidebar('start', {schemaVersion: 2, prep: {derivedRef: {prepKey: 'p'}}});
  expect(html).not.toContain('aria-disabled="true"');
  expect([...html.matchAll(/\bhref="([^"]+)"/g)].map(match => match[1])).toEqual([
    '/pipeline/start', '/pipeline/keywords', '/pipeline/crawling', '/pipeline/preprocess', '/pipeline/labeling',
    '/pipeline/training', '/pipeline/clustering', '/pipeline/evidence', '/pipeline/personas', '/pipeline/insights',
  ]);
});
```

- `frontend/src/components/persona/insight.test.ts:47`의 세션을 `{prep:{derivedRef:{prepKey:'p'}},completion:{insightDone:true}}`로(링크 기대는 그대로).
- `frontend/src/components/persona/insight.test.ts:41`의 `expect(route).toContain('<LegacyInsightsPage');` → `expect(route).toContain('<LaterStageBanner');` 그리고 테스트 이름을 `'redirects old route and branches new route on derivedRef with a gate banner'`로.
- `frontend/src/components/persona/insight-route.test.ts`: `vi.mock('@/app/insights/LegacyInsightsPage', …)`와 `import Legacy …` 삭제, `import { LaterStageBanner } from '@/components/LaterStageBanner';` 추가, `'retains old insights component for legacy sessions'`를 다음으로 교체.

```ts
it('shows the prep banner for v2 sessions and the legacy banner for old sessions', () => {
 state.sd = {schemaVersion:2, prep:{derivedRef:''}, insight:{confirmed:[]}} as any;
 let page = Page(); expect(page.type).toBe(LaterStageBanner); expect(page.props).toEqual({gate:'needs-prep', stage:'인사이트'});
 state.sd = {prep:{derivedRef:''}, insight:{confirmed:[]}} as any;
 page = Page(); expect(page.type).toBe(LaterStageBanner); expect(page.props).toEqual({gate:'legacy', stage:'인사이트'});
});
```

  (마지막 테스트가 `state.sd.prep.derivedRef='derived'`를 쓰므로 `state.sd`를 원래 모양 `{prep:{derivedRef:''},insight:{confirmed:['I1']}}`로 되돌리는 줄을 그 테스트 맨 앞에 추가.)
- `frontend/src/app/pipeline/clustering/page.test.ts`의 첫 테스트를 교체.

```ts
it('routes derived sessions to SegmentScreen and others to a gate banner without v1 calls',()=>{
 expect(nodes(Page()).some(n=>n.type===SegmentScreen)).toBe(true);
 state.session.sd={schemaVersion:2};
 let page:any=Page();expect(page.type).toBe(LaterStageBanner);expect(page.props).toEqual({gate:'needs-prep',stage:'클러스터링'});
 state.session.sd={};
 page=Page();expect(page.type).toBe(LaterStageBanner);expect(page.props).toEqual({gate:'legacy',stage:'클러스터링'});
});
```

  (`import { LaterStageBanner } from '@/components/LaterStageBanner';` 추가.)
- 페르소나 페이지 분기 테스트 새 파일 — `frontend/src/app/pipeline/personas/page.test.ts`:

```ts
import { describe, expect, it, vi } from 'vitest';
const page = vi.hoisted(() => ({session: {sid: 's', sd: {schemaVersion: 2}} as any}));
vi.mock('@/stores/useSessionStore', () => ({useSessionStore: () => page.session}));
vi.mock('@/components/versions/VersionProvider', () => ({useVersion: () => ({version: 'v1', readonly: false, conflict: false, session: null})}));
vi.mock('@/components/persona/PersonaScreen', () => ({PersonaScreen: () => null}));
vi.mock('@/lib/api', () => { throw new Error('v1 api must not be imported by the personas page'); });
vi.mock('next/navigation', () => ({useRouter: () => ({push: vi.fn()})}));
import PersonasPage from '@/app/pipeline/personas/page';
import { LaterStageBanner } from '@/components/LaterStageBanner';
import { PersonaScreen } from '@/components/persona/PersonaScreen';

describe('personas page gate', () => {
  it('routes by gate', () => {
    page.session = {sid: 's', sd: {schemaVersion: 2}};
    expect(PersonasPage()).toMatchObject({type: LaterStageBanner, props: {gate: 'needs-prep', stage: '페르소나'}});
    page.session = {sid: 's', sd: {}};
    expect(PersonasPage()).toMatchObject({type: LaterStageBanner, props: {gate: 'legacy', stage: '페르소나'}});
    page.session = {sid: null, sd: null};
    expect(PersonasPage()).toMatchObject({type: LaterStageBanner, props: {gate: 'no-session', stage: '페르소나'}});
    page.session = {sid: 's', sd: {schemaVersion: 2, prep: {derivedRef: {prepKey: 'p'}}}};
    expect(PersonasPage().type).toBe(PersonaScreen);
  });
});
```

(`vi.mock('@/lib/api', () => { throw … })`는 페이지가 v1 `@/lib/api`를 import하면 테스트가 실패하게 만든다 — 지금 페이지는 import하므로 RED.)

- 배너 단위 테스트 새 파일 — `frontend/src/components/LaterStageBanner.test.ts`:

```ts
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
const nav = vi.hoisted(() => ({push: vi.fn()}));
vi.mock('next/navigation', () => ({useRouter: () => nav}));
import { LaterStageBanner } from './LaterStageBanner';

describe('LaterStageBanner', () => {
  it.each([
    ['needs-prep', '3단계(전처리)를 먼저 완료하세요. 전처리가 끝나야 페르소나 화면을 열 수 있습니다.', '/pipeline/preprocess', '전처리 화면으로'],
    ['legacy', '구버전 세션은 이 단계를 열 수 없습니다. 새 프로젝트를 만들어 진행하세요.', '/pipeline/start', '프로젝트 선택하기'],
    ['no-session', '프로젝트를 먼저 선택하세요.', '/pipeline/start', '프로젝트 선택하기'],
  ] as const)('%s', (gate, text, route, label) => {
    nav.push.mockClear();
    const tree = LaterStageBanner({gate, stage: '페르소나'});
    const html = renderToStaticMarkup(tree);
    expect(html.replace(/<!-- -->/g, '')).toContain(text);
    expect(html).toContain(label);
    tree.props.actions.props.onClick();
    expect(nav.push).toHaveBeenCalledWith(route);
  });
});
```

- [ ] **Step 2: RED 확인** — Run: `npm --prefix frontend test -- src/lib/logic/laterStageGate.test.ts src/components/LaterStageBanner.test.ts src/app/pipeline/personas/page.test.ts src/lib/logic/completedThrough.test.ts src/app/pipeline/clustering/page.test.ts src/components/persona/insight-route.test.ts src/components/persona/insight.test.ts` · Expected: FAIL — `laterStageGate.test.ts`는 모듈이 없어 import 실패이므로 **먼저 `laterStageGate.ts`를 `export function laterStageGate(): LaterStageGate { return 'open'; }`·`export function laterStagesOpen() { return true; }` 껍데기로 만들어** 단언 실패(`expected 'open' to be 'no-session'`)를 RED로 기록한다. 나머지 파일은 `LaterStageBanner` 껍데기(`export function LaterStageBanner() { return null; }`)를 만든 뒤 단언 실패를 확인한다.

- [ ] **Step 3: 구현**

`frontend/src/lib/logic/laterStageGate.ts`:

```ts
export type LaterStageGate = 'no-session' | 'legacy' | 'needs-prep' | 'open';

export const LATER_STAGE_LOCK_TITLE = '전처리(3단계)를 먼저 완료하세요';

/** Stages 6–9 need a derived preprocessing result (prep.derivedRef). */
export function laterStagesOpen(session: Record<string, unknown> | null | undefined): boolean {
  return !!(session?.prep as {derivedRef?: unknown} | undefined)?.derivedRef;
}

export function laterStageGate(sid: string | null | undefined, session: Record<string, unknown> | null | undefined): LaterStageGate {
  if (!sid || !session) return 'no-session';
  if (laterStagesOpen(session)) return 'open';
  // Same rule as backend store.is_legacy: old sessions have no schemaVersion key.
  return 'schemaVersion' in session ? 'needs-prep' : 'legacy';
}
```

`frontend/src/components/LaterStageBanner.tsx`:

```tsx
"use client";
import { useRouter } from "next/navigation";
import { Banner, Button } from "@/components/ds";
import type { LaterStageGate } from "@/lib/logic/laterStageGate";

export function LaterStageBanner({ gate, stage }: { gate: Exclude<LaterStageGate, "open">; stage: string }) {
  const router = useRouter();
  if (gate === "needs-prep") {
    return <Banner tone="warning" actions={<Button variant="primary" onClick={() => router.push("/pipeline/preprocess")}>전처리 화면으로</Button>}>
      3단계(전처리)를 먼저 완료하세요. 전처리가 끝나야 {stage} 화면을 열 수 있습니다.
    </Banner>;
  }
  if (gate === "legacy") {
    return <Banner tone="warning" actions={<Button onClick={() => router.push("/pipeline/start")}>프로젝트 선택하기</Button>}>
      구버전 세션은 이 단계를 열 수 없습니다. 새 프로젝트를 만들어 진행하세요.
    </Banner>;
  }
  return <Banner actions={<Button onClick={() => router.push("/pipeline/start")}>프로젝트 선택하기</Button>}>프로젝트를 먼저 선택하세요.</Banner>;
}
```

`frontend/src/components/StepBar.tsx`: import `laterStagesOpen`, `LATER_STAGE_LOCK_TITLE`; 지금 68~71행을

```tsx
    const path = i >= 6 && !laterStagesOpen(session) ? null : step.path;
    return path === null
      ? <a key={step.name} {...props} role="link" aria-disabled="true" title={LATER_STAGE_LOCK_TITLE}>{content}</a>
```

로 바꾼다(나머지 그대로).

`frontend/src/app/globals.css` 30행(`.pipeline-nav small`) 다음에:

```css
.pipeline-nav a[aria-disabled="true"] { color:var(--sub); cursor:not-allowed; }
.pipeline-nav a[aria-disabled="true"] .n { opacity:.6; }
```

세 페이지 — `Legacy*Page` 함수(그리고 그 함수만 쓰는 import 전부: `@/lib/api`, `usePolling`, `ProgressBar`, `Spinner`, `PersonaCard`, `useRouter`, `useState`, `useCallback`, `useStageCompletionRefresh` 등, 남은 코드가 안 쓰면)를 지우고:

`app/pipeline/clustering/page.tsx`:

```tsx
"use client";
import { useSessionStore } from "@/stores/useSessionStore";
import { useVersion } from "@/components/versions/VersionProvider";
import { SegmentScreen } from "@/components/segment/SegmentScreen";
import { LaterStageBanner } from "@/components/LaterStageBanner";
import { laterStageGate } from "@/lib/logic/laterStageGate";
import type { SegmentDraft } from "@/lib/types";

export default function ClusteringPage() {
  const {sid, sd} = useSessionStore();
  const view = useVersion();
  const gate = laterStageGate(sid, sd);
  if (gate !== 'open') return <LaterStageBanner gate={gate} stage="클러스터링" />;
  return <SegmentScreen key={`${sid}:${view.version ?? ''}`} sid={sid!} version={view.version} readonly={view.readonly || !!view.conflict} draft={sd?.drafts?.segment as SegmentDraft | undefined} />;
}
```

`app/pipeline/personas/page.tsx`: 같은 형태, `stage="페르소나"`, `<PersonaScreen key=… sid={sid!} version={view.version} readonly={view.readonly || !!view.conflict} />`.

`app/pipeline/insights/page.tsx`: `const session = view.session ?? sd;` 유지, `const gate = laterStageGate(sid, session);`, `stage="인사이트"`, 열림이면 지금과 같은 `<InsightScreen … initialConfirmed={insight?.confirmed ?? []}/>`. `LegacyInsightsPage` import 삭제(파일 자체는 T6에서 삭제).

`sd`의 타입이 `Record<string, unknown>`이 아니면 `laterStageGate(sid, sd as Record<string, unknown> | null | undefined)`로 넘긴다.

- [ ] **Step 4: GREEN** — Step 2 명령 PASS.

- [ ] **Step 5: 화면 자체 확인** — `npm --prefix frontend run dev`와 백엔드(`backend/.venv/bin/python -m uvicorn app.main:app --port 8000`, cwd `backend`, `STORAGE=local`, 임시 `LOCAL_DATA_DIR`)를 띄우고 전처리 전 v2 세션 하나를 만들어(`POST /context`) 클러스터링 URL로 가서 배너와 사이드바 잠금을 확인, 스크린샷 1장을 보고서 notes 경로에 남긴다(`docs/development/v1-cleanup/qa/T5-self.png`는 **QA 산출물 경로라 쓰지 않는다** — 워커 보고서 경로 `.harness/` 아래에 둔다).

- [ ] **Step 6: 공통 검사 4개** → READY_FOR_COMMIT. 제안 커밋 메시지: `fix(pipeline): 전처리 전 세션은 6~9단계를 잠그고 배너로 안내`

---

### Task 6: 고아가 된 v1 프론트 코드 삭제

**allowed_files:**
- Delete: `frontend/src/app/insights/LegacyInsightsPage.tsx`, `frontend/src/components/PersonaCard.tsx`, `frontend/src/components/SNAGraph.tsx`, `frontend/src/components/ProgressBar.tsx`, `frontend/src/components/Spinner.tsx`, `frontend/src/components/SuggestedWordsPanel.tsx`
- Modify: `frontend/src/lib/api.ts`
- Create: `frontend/src/lib/api.test.ts`

- [ ] **Step 1: RED 테스트** — `frontend/src/lib/api.test.ts`

```ts
import { existsSync } from 'node:fs';
import { expect, it } from 'vitest';
import * as api from './api';

it('keeps only the session and chat helpers in the v1 api module', () => {
  expect(Object.keys(api).sort()).toEqual(['getSession', 'saveSession', 'sendChat', 'sendInsightChat']);
});

it('removes orphaned v1 screens and components', () => {
  for (const file of ['src/app/insights/LegacyInsightsPage.tsx', 'src/components/PersonaCard.tsx', 'src/components/SNAGraph.tsx',
    'src/components/ProgressBar.tsx', 'src/components/Spinner.tsx', 'src/components/SuggestedWordsPanel.tsx']) {
    expect(existsSync(file), file).toBe(false);
  }
});
```

- [ ] **Step 2: RED 확인** — Run: `npm --prefix frontend test -- src/lib/api.test.ts` · Expected: 2 FAIL (키 목록 불일치, `expected true to be false`).

- [ ] **Step 3: 구현** — Delete 목록 6개 파일 삭제. `frontend/src/lib/api.ts`에서 `listSessions`, `deleteSession`, `suggestWords`, `startCrawl`, `getCrawlStatus`, `startPreprocess`, `getPreprocessStatus`, `getSample`, `startTrain`, `getTrainStatus`, `startCluster`, `getClusterStatus`, `clusterRefine`, `startEmbed`, `getEmbedStatus`, `startPersona`, `getPersonaStatus`, `getSNAData`와 빈 구역 주석 삭제. 남는 것: `request`, `getSession`, `saveSession`, `sendChat`, `sendInsightChat`. 삭제 전 `grep -rn "from \"@/lib/api\"\|from '@/lib/api'" frontend/src`로 남은 importer가 이 4개만 쓰는지 확인. `d3`는 `components/segment/WordNetwork.tsx`가 쓰므로 `package.json` 그대로.

- [ ] **Step 4: GREEN** — Step 2 명령 PASS.

- [ ] **Step 5: 공통 검사 4개** → READY_FOR_COMMIT. 제안 커밋 메시지: `chore(v1): 고아가 된 v1 화면·컴포넌트·API 함수 삭제`

---

## Controller 마무리(워커 Task 아님)

- `docs/development/dcx2-stage0-2/decision-log.md` D-065 아래 `- 2026-10-xx v1-cleanup에서 호환 파일 제거(필드 desc·cafe·link는 v2 문서에 유지).`, D-060 아래와 `docs/development/dcx2-stage8/decision-log.md` D-303 아래 `- 2026-10-xx v1-cleanup: 운영 옛 세션 0개 확인 후 옛 화면 삭제, 배너로 대체.` 한 줄씩.
- `docs/development/v1-cleanup/report.md`: Task별 커밋·리뷰·QA 결과, 기준선 대비 테스트 수.
- 하네스 `evidence` → `complete verification` → 사용자 UAT. PR·push·배포는 별도 요청이 있을 때만.

## 되돌리기

Task별 커밋이라 `git revert <task_commit>`으로 하나씩 되돌린다. 데이터 형식·저장 위치를 바꾸지 않았으므로 데이터 복구는 필요 없다(이미 있는 `preprocessed/` 파일은 지우지 않음). T5만 되돌리면 Legacy 화면 import가 다시 필요하므로 T6 → T5 순서로 되돌린다.

## Self-review 결과

- 명세 대응: 성공 기준 1→T3, 2→T1·T2·T3, 3→T2, 4→T5, 5→T5, 6→T5(분기 테스트)·QA 회귀, 7→모든 Task 공통 검사. 결정 3(`workflow.py`)→T4, 결정 5(필드 유지)→T1 `_export_fields`·T2 단언.
- 이름 일관성: `crawl_docs`·`filter_documents`·`_export_fields`(T1) ↔ T2 테스트, `laterStageGate`·`laterStagesOpen`·`LATER_STAGE_LOCK_TITLE`·`LaterStageBanner`(T5) ↔ T6 무관.
- 해결한 불확실성: T2 `full_flow`의 prep 워커는 하위 프로세스라 환경 변수가 필요 → `offline` 픽스처에 `setenv` 추가(plan-eng-review 1번).


## 엔지니어링 리뷰 (plan-eng-review, 2026-10-20)

**Step 0 범위 점검** — 수정·삭제 파일이 8개를 넘지만 대부분 삭제다. 새 코드는 3개(`app/prep/documents.py` 이동분, `laterStageGate.ts`, `LaterStageBanner.tsx`)이고 새 서비스·클래스는 없다. 줄일 범위 없음. 이미 있는 것을 다시 쓴다: 배너는 `components/ds`의 `Banner`·`Button`, 잠금 마크업은 지금 근거 탐색 잠금 그대로, 전처리 재사용은 `routers/prep.py`의 기존 경로.

**1. 아키텍처**
- [P1] (confidence 9/10) `app/work/runner.py:39` — prep 워커는 `subprocess.Popen`이라 테스트의 `monkeypatch.setattr(settings, …)`가 닿지 않는다. T2 `full_flow`가 그대로면 워커가 voyage 임베더를 찾다 실패한다. → T2에 `offline` 픽스처 `setenv` 추가(반영).
- [P3] (confidence 7/10) `app/pipeline/layout.tsx:101` — 사이드바 세션은 `view.session ?? (view.readonly ? null : store.sd)`. 읽기 전용 버전을 불러오는 짧은 순간 `null`이면 6~9가 잠겨 보인다(지금은 근거 탐색만). 불러오면 풀리므로 그대로 두고 QA-EDGE-003에서 관찰.

**2. 코드 품질** — 세 페이지의 분기는 `laterStageGate` 하나 + `LaterStageBanner` 하나로 모아 중복 없음. `crawl_docs` 루프 구조를 바꾸므로 체인·순환·잘못된 id 테스트로 고정(T1). 문제 없음.

**3. 테스트**

```
CODE PATHS                                              USER FLOWS
[T1] app/prep/documents.py                              [J-1] 전처리 전 6~9단계 접근
  crawl_docs                                              [★★★] 사이드바 잠금 — completedThrough.test.ts(T5) + QA-E2E-001
    [★★★] 자식 우선·순환·잘못된 id — test_documents.py   [★★★] URL 직접 → 배너, v1 호출 없음 — page tests(T5) + QA-E2E-002~004
  filter_documents                                        [★★ ] 모바일 — QA-EDGE-001 [→E2E]
    [★★★] 광고·제외·중복·품질·4,000자 — test_documents.py [J-2] 전처리 후 화면 그대로 — QA-E2E-005, clustering/insight 테스트
[T2] pipeline/prep 재사용                                [J-3] 전처리 실행·재사용 — test_prep_api.py(T2) + QA-E2E-006 [→E2E]
  [★★★] 호환 파일 없이 재사용 / 미완료 수집 409 / 옛 결과 재생성 — test_prep_api, test_review_fix1
  [★★ ] 임베더 미연결 시 문서 보존 — test_pipeline.py
[T3] 라우트 목록·import 경계 — test_v1_boundary.py       [J-4] 옛 세션·세션 없음 — gate·page tests + QA-E2E-007, QA-NEG-003
[T5] laterStageGate 4분기 — laterStageGate.test.ts       [J-5] 챗봇 회귀 — QA-REG-001 [→E2E]
     LaterStageBanner 3분기·버튼 경로 — LaterStageBanner.test.ts (리뷰에서 추가)
[T6] api 모듈 export·고아 파일 — api.test.ts
COVERAGE: 계획된 새 분기 전부 테스트 있음 | GAP: 0 (리뷰 전 1개: 배너 버튼 경로 → 추가)
```

회귀 규칙: 바뀌는 기존 동작(사이드바 잠금 범위, 세 페이지 분기, 재사용 조건)은 모두 기존 테스트를 고쳐 새 기대값으로 고정한다(T2·T5).

**4. 성능** — 삭제 위주라 새 비용 없음. 재사용 조건에서 파일 존재 검사 1개가 줄어든다. 문제 없음.

**실패 모드**

| 새 경로 | 현실적 실패 | 테스트 | 처리 | 사용자에게 |
|---|---|---|---|---|
| `crawl_docs` | collection manifest 손상 | 있음(기존 메시지 유지) | `ValueError('수집본을 읽을 수 없습니다')` | 전처리 실패 상태로 표시 |
| 재사용 조건 | 옛 manifest에 `collectionFinalized` 없음 | 있음(`test_c3_unverified…`) | 재사용 안 하고 다시 실행 | 정상 실행 |
| `laterStageGate` | 세션 불러오기 전 `sd` 없음 | 있음(no-session) | "프로젝트를 먼저 선택하세요" 배너 | 잠깐 배너 후 화면 |
| 사이드바 잠금 | 읽기 전용 버전 로딩 중 `null` | 부분(QA-EDGE-003) | 로딩 후 풀림 | 잠깐 잠김(조용하지만 무해) |

치명적 공백(테스트·처리·안내 모두 없음): 0개.

**범위 밖(이번에 하지 않음)** — `desc`·`cafe`·`link` 제거(내보내기 형식 변경), `clustersDone` 정리, 챗봇 v2 연결(B-120), 맥미니 데이터 정리, 배포.

**병렬화** — 백엔드(T1→T2→T3→T4)와 프론트(T5→T6)는 모듈이 겹치지 않아 두 줄로 나눌 수 있지만, 하네스는 Task마다 commit → 독립 리뷰 PASS 후 다음으로 가므로 순차 실행한다.

**바깥 의견(outside voice)** — 실행하지 않음. 하네스가 Task마다 새 Codex 리뷰어로 독립 리뷰를 하므로 계획 단계에서는 생략했다. 원하면 계획 승인 전에 실행한다.

**요약** — Step 0: 범위 그대로 · 아키텍처 2건(반영 1, 관찰 1) · 코드 품질 0건 · 테스트 공백 1건(반영) · 성능 0건 · 치명적 공백 0 · 병렬화: 순차.

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | `/plan-ceo-review` | Scope & strategy | 0 | — | — |
| Codex Review | `/codex review` | Independent 2nd opinion | 0 | — | — |
| Eng Review | `/plan-eng-review` | Architecture & tests (required) | 1 | CLEAR (PLAN) | 3 issues, 0 critical gaps (2 반영, 1 관찰) |
| Design Review | `/plan-design-review` | UI/UX gaps | 0 | — | — |
| DX Review | `/plan-devex-review` | Developer experience gaps | 0 | — | — |

- **UNRESOLVED:** 0
- **VERDICT:** ENG CLEARED — 하네스 제출은 제품 승인(`decide approve`) 후.
