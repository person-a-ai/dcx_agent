# 2단계 크롤링 채널 확장 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 2단계 크롤링에 `youtube_vlog`(유튜브 브이로그 자막) · `threads` · `naver_kin`(지식iN 질문) · `cook82`(82쿡) 네 채널을 기존 목록 → 게이트 → 상세 → 보고서 흐름 그대로 추가한다.

**Architecture:** 채널마다 기존 `ChannelAdapter` 규약(`list_page` → `fetch`)을 따르는 어댑터 파일 하나. 공통 변경은 "건너뜀"(`AdapterSkipped` → 큐 `skipped`) 경로, 채널 식별(스키마 · URL · 이름 · 기본 한도), 브이로그 자막 분할 모듈(`captions.py`), Threads용 Crawl4AI 다리(`render.py`)다. 프론트는 설정 · 게이트 · 진행 · 결과 화면에 행 · 열 · 문구를 더한다.

**Tech Stack:** Python 3.12 · FastAPI · Pydantic v2 · httpx · selectolax · yt-dlp · crawl4ai(Playwright Chromium) · numpy · SQLite / Next.js 16 · React 19 · Vitest

**Spec:** [01-brainstorm.md](01-brainstorm.md) (제품 승인) · [02-design.md](02-design.md) (설계 승인) · 목업 [mockup/index.html](mockup/index.html) · QA [QA_PLAN-channel-expansion.md](QA_PLAN-channel-expansion.md)

## Global Constraints

- 구현 · 테스트 작성 · 수정은 Codex 워커가 한다. 모든 구현 dispatch에 다음 문장을 그대로 넣는다: *"Do not create Git commits. Complete the implementation and verification, then return READY_FOR_COMMIT with the exact changed-file list and a proposed commit message. Repository state transitions are owned by the controller."* 각 Task의 "Commit" 단계는 Controller가 `repository-gate` → `repository-commit`으로 수행한다.
- 실행 환경: `backend/.venv`(Python 3.12). 백엔드 명령은 build worktree 루트에서 `backend/.venv/bin/python -m pytest ...`, 프론트는 `npm --prefix frontend ...`.
- 크롤링 테스트는 네트워크 금지(`backend/tests/crawl/conftest.py`의 `no_network`). 어댑터는 녹화 응답 픽스처나 가짜 객체로만 테스트한다.
- 로그인 · 쿠키 · 캡차 우회 · 프록시 회전 · 브라우저 위장(stealth) 설정은 어떤 채널에도 넣지 않는다(기획 G2). 유튜브 PO 토큰 생성기 같은 봇 검증 우회 도구도 넣지 않는다.
- 채널 ID: `youtube_vlog`, `threads`, `naver_kin`, `cook82`. 화면 이름: 유튜브 브이로그 · Threads · 지식iN · 82쿡. doc_id 접두사: `yv` · `th` · `kn` · `c8`.
- 기본 동시 수 / 요청 간격: `youtube_vlog` 2 / 0초, `threads` 1 / 2초, `naver_kin` 1 / 0.5초, `cook82` 1 / 0.5초.
- 브이로그 기본값: 키워드당 영상 20개, 길이 60초 ≤ d ≤ 3600초, 자막 창 20초, 구간 하한 45초 · 상한 300초, 대체 고정 구간 90초.
- 건너뜀 사유 코드: `no_ko_captions`(한국어 자막 없음), `deleted`(삭제된 글). 기존 `restricted` · `blocked` · `parse_error`와 함께 표시한다.
- 분류 모델 입력 차원 1032 유지 — `backend/app/model/features.py`는 바꾸지 않는다.
- 저장 금지 개인정보: 82쿡 IP(`#writerIP`, `.ip`), Threads 사용자 이름 원문(작성자는 `author_hash`로만).
- 기존 테스트는 전부 통과해야 한다. 하네스 검증 명령: `backend/.venv/bin/python -m pytest backend/tests -q`, `npm --prefix frontend run lint`, `npm --prefix frontend run build`, `npm --prefix frontend test`.

## 설계와 달라지는 점 (계획 승인 대상)

- **Threads 최신 보기 제외.** 설계 3.2는 인기 · 최신 두 화면을 합치기로 했으나, 로그인 없이 `&filter=recent`를 붙이면 리디렉트로 조건이 지워져 같은 결과가 온다(2026-10-20 확인). 인기 화면 한 번만 렌더링하고 키워드당 약 19~20건을 받는다. 목업 · 화면 문구의 "약 20~60건"은 "약 20건"으로 쓴다.
- **브이로그 `segmenter` 값에 `single` 추가.** 영상이 구간 하한(45초)보다 짧거나 자막 창이 1개뿐이면 나눌 경계가 없으므로 구간 1개 · `segmenter='single'`로 표기한다(설계의 `embedding` · `fixed`와 구분).
- **Threads 목록 파싱 근거.** 렌더링된 페이지의 `script[type="application/json"]` 안 글 객체(`code`, `caption.text`, `taken_at`, `like_count`, `user.username`, `text_post_app_info.direct_reply_count`)를 읽는다. 화면 DOM의 클래스 이름은 난독화돼 있어 쓰지 않는다.

## 다른 작업과의 겹침 (`chore/v1-cleanup`, 같은 main `4444a50`에서 진행 중)

| 겹치는 곳 | v1-cleanup 계획 | 이 계획에 미치는 영향 | 처리 |
|---|---|---|---|
| `crawl4ai` 의존성 | requirements · constraints에서 `crawl4ai`(와 그것만 쓰던 `playwright` 등)를 지우고, `backend/tests/ops/test_v1_dependencies.py::test_crawl4ai_not_required_or_documented`로 다시 들어오지 못하게 막는다. README의 `crawl4ai-setup` 줄도 지운다 | T7 Threads가 `crawl4ai`를 쓴다. 두 브랜치를 모두 합치면 그 테스트가 실패한다 | **결정됨 (사용자, 2026-10-20, plan-eng-review 1A):** v1-cleanup에서 crawl4ai 삭제 단계를 뺀다(그 세션에 전달, v1-cleanup 쪽 계획 수정 · 재승인). 이 계획은 `crawl4ai` · `playwright` 고정과 README 설치 안내를 그대로 둔다. 합칠 때 `test_crawl4ai_not_required_or_documented`가 main에 들어와 있으면 이 계획을 멈추고 사용자에게 알린다 |
| 전처리 공용 함수 | `filter_documents` · `_crawl_docs`를 `app/prep/documents.py`로 옮긴다(`desc` · `cafe` · `link`는 유지) | T9 테스트가 `app.services.preprocessing.filter_documents`를 import한다 | T9 dispatch 시 main에 v1-cleanup이 이미 합쳐졌으면 `from app.prep.documents import filter_documents`로 쓴다. 단언 내용은 같다 |
| 의존성 설치 명령 | `pip install ... -c backend/constraints.txt` | T0 Step 2 | T0 Step 2에서 `-c backend/constraints.txt`를 붙인다 |

## File Structure

| 파일 | 책임 | Task |
|---|---|---|
| `backend/app/crawl/adapters/base.py` | `AdapterSkipped` 예외 | T1 |
| `backend/app/crawl/queue.py` | `mark_skipped` | T1 |
| `backend/app/crawl/worker.py` | 건너뜀 처리, 채널 기본값 사용, 브이로그 목록 옵션 · 상한 | T1, T2 |
| `backend/app/crawl/report.py` | `progress.skipped`, `channels[s].skip_reasons` | T1 |
| `backend/app/crawl/channels.py` (새) | 채널 기본 동시 수 · 간격, 구어 채널 집합 | T2 |
| `backend/app/crawl/control.py` | 기본 간격을 `channels.py`에서 | T2 |
| `backend/app/crawl/schema.py`, `backend/app/context/models.py` | `source` · `Channel` 값 4개 | T2 |
| `backend/app/crawl/urls.py` | 접두사 · 정규화 규칙 | T2 |
| `backend/app/routers/crawl_v2.py` | `Config.youtube_vlog` | T2 |
| `backend/app/config.py` | 자막 · Threads 설정값 | T2 |
| `backend/app/context/labels.py`, `frontend/src/lib/contextLabels.ts` | 채널 이름 | T2 |
| `backend/app/prep/boilerplate.v1.json`, `frontend/src/components/prep/prep.ts` | 채널별 상투어(빈 목록) · 채널 목록 | T2 |
| `backend/app/keywords/prompts.py` | 구어 채널 집합 사용 | T2 |
| `backend/app/crawl/captions.py` (새) | json3 파싱 · 화제 분할 | T3 |
| `backend/app/crawl/adapters/youtube.py` | `extract_info()` 모듈 함수로 분리(동작 동일) | T4 |
| `backend/app/crawl/adapters/youtube_vlog.py` (새) | 브이로그 어댑터 | T4 |
| `backend/app/crawl/adapters/naver_kin.py` (새) | 지식iN 어댑터 | T5 |
| `backend/app/crawl/adapters/cook82.py` (새) | 82쿡 어댑터 | T6 |
| `backend/app/crawl/render.py` (새) | Crawl4AI 다리 | T7 |
| `backend/app/crawl/adapters/threads.py` (새) | Threads 어댑터 · 공급자 경계 | T7 |
| `backend/app/crawl/adapters/__init__.py`, `backend/tests/crawl/test_adapter_wiring.py` | 레지스트리 · 사용 가능 판정 | T4~T7 (순서대로 한 줄씩) |
| `frontend/src/lib/api/crawl.ts`, `lib/logic/crawlConfig.ts`, `lib/logic/finishPartial.ts`, `components/crawl/Settings.tsx`, `components/crawl/Progress.tsx`, `app/pipeline/crawling/page.tsx` | 화면 변경 | T8 |
| `backend/tests/crawl/test_channel_expansion_flow.py` (새) | 새 채널 문서가 전처리 · 특징까지 지나가는 통합 테스트 | T9 |

---

### Task T0: 작업 공간 준비 · 녹화 · 사전 확인 (Controller, 코드 변경 없음)

**담당:** Controller(Main Claude). 제품 코드 · 테스트를 쓰지 않는다. 산출물은 `.harness/captures/channel-expansion/`(Git 추적 제외)와 보고서 `docs/development/channel-expansion/reports/T0.md`뿐이다.

- [ ] **Step 1: 승인 자료 커밋 · build worktree 생성**

```bash
git add -- docs/development/channel-expansion/01-brainstorm.md docs/development/channel-expansion/02-design.md docs/development/channel-expansion/design-bundle.json docs/development/channel-expansion/mockup/index.html docs/development/channel-expansion/mockup/app.css docs/development/channel-expansion/03-plan.md docs/development/channel-expansion/QA_PLAN-channel-expansion.md docs/development/channel-expansion/plan-bundle.json
git commit -m "docs: 채널 확장 기획 · 설계 · 계획 승인"
~/.local/bin/development-harness worktree /Users/yunho/Documents/dcx_agent-channels-build feature/channel-expansion
```

- [ ] **Step 2: 의존성 설치 · 기준 검사** (build worktree에서)

```bash
python3.12 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt -r backend/requirements-dev.txt -c backend/constraints.txt
backend/.venv/bin/crawl4ai-setup
npm --prefix frontend ci
backend/.venv/bin/python -m pytest backend/tests -q
npm --prefix frontend test
```
Expected: 기준 테스트 모두 PASS(실패가 있으면 기존 실패 목록으로 T0.md에 기록하고 사용자에게 보고).

- [ ] **Step 3: 녹화** — `.harness/captures/channel-expansion/`에 원본 저장(마스킹은 각 Task의 Codex가 픽스처로 옮길 때 한다).
  - 지식iN: 검색 `list.naver?query=에어컨&page=1`, `page=2`, 결과 없음 검색어(`query=zxqwvplmn`), 질문 페이지 3건, 삭제된 질문 1건(검색 결과에서 못 찾으면 존재하지 않는 `docId` 요청 응답).
  - 82쿡: 검색 `enti.php?bn=15&searchType=search&search1=1&keys=에어컨&page=1`, 글 3건(댓글 있는 글 2건 포함), 결과 없음 검색어.
  - Threads: Step 4의 Crawl4AI 렌더링 결과 HTML(정상 · 결과 없음 검색어). 헤드리스로 로그인 창만 나오면 그 HTML도 저장한다.
  - 브이로그: yt-dlp `extract_info` 결과 JSON 3건(수동 자막 있음 · 자동만 · 자막 없음)과 json3 자막 1건. 자막 · 설명 본문은 픽스처에서 합성 문장으로 바꾼다.

- [ ] **Step 4: Threads 헤드리스 확인** — Crawl4AI 기본 설정(헤드리스, 위장 없음)으로 `https://www.threads.com/search?q=에어컨&serp_type=default`를 렌더링하고 `script[type="application/json"]` 안 글 객체 수를 센다.
  - 10건 이상: T7 진행.
  - 0건 · 로그인 창만: T7은 진행하되 Step 4 결과를 사용자에게 보고하고, `threads`의 기본 사용 가능 판정을 끄는 설정(`threads_enabled=False`)을 T7에 추가할지 결정을 받는다. 사용자 결정 전에는 T7을 dispatch하지 않는다.

- [ ] **Step 5: 82쿡 검색 범위** — `search1=1`과 `search1=2`(또는 화면에 있는 다른 값)로 같은 검색어를 요청해 결과 차이를 비교하고 "제목+본문"에 해당하는 값을 T0.md에 기록한다. T6은 그 값을 쓴다.

- [ ] **Step 6: 운영 확인 항목 기록** — `ops/macmini/install.sh`에 `crawl4ai-setup`이 있는지, 운영 `.env`에 Voyage 키가 설정됐는지(값은 기록하지 않고 유무만). 없으면 T0.md에 "운영 반영 시 필요"로 남긴다(이번 범위에서 운영 스크립트는 바꾸지 않는다).

---

### Task T1: 건너뜀 경로 (`AdapterSkipped` → `skipped` → 보고서)

**Files:**
- Modify: `backend/app/crawl/adapters/base.py`, `backend/app/crawl/adapters/__init__.py`(export만), `backend/app/crawl/queue.py`, `backend/app/crawl/worker.py`, `backend/app/crawl/report.py`
- Test: `backend/tests/crawl/test_skipped.py` (새)

**Interfaces:**
- Produces: `app.crawl.adapters.base.AdapterSkipped(reason: str)` (속성 `reason`); `CrawlQueue.mark_skipped(url_norm: str, source: str, reason: str) -> None`; `report.progress(queue)['skipped']: dict[str, dict[str, int]]`; `report.build_report(queue)['channels'][source]['skip_reasons']: dict[str, int]`.

- [ ] **Step 1: 실패 테스트 작성** — `backend/tests/crawl/test_skipped.py`

```python
from contextlib import closing
import csv

import pytest

from app.config import settings
from app.crawl import report, worker
from app.crawl.adapters import REGISTRY
from app.crawl.adapters.base import AdapterSkipped
from app.crawl.adapters.fixture import FixtureAdapter
from app.crawl.control import ReadQueue
from app.crawl.filters import FilterConfig
from app.crawl.queue import CrawlQueue
from app.crawl.writer import read_docs


@pytest.fixture
def corpus(tmp_path, monkeypatch):
    path = tmp_path / 'corpus.csv'
    with path.open('w') as f:
        w = csv.writer(f)
        w.writerow(['review'])
        w.writerows([[f'에어컨 소음 {i}'] for i in range(20)])
    monkeypatch.setattr(settings, 'fixture_corpus_path', str(path))
    monkeypatch.setattr(settings, 'enable_fixture_channel', True)
    monkeypatch.setattr(settings, 'author_salt_path', str(tmp_path / '.salt'))
    return path


def run(tmp_path, monkeypatch, corpus):
    class Skipping(FixtureAdapter):
        def fetch(self, item):
            if int(item.url.rsplit('/', 1)[1]) % 2:
                raise AdapterSkipped('no_ko_captions')
            return super().fetch(item)
    snapshot = worker.run_list('S', collection=tmp_path, keywords=['에어컨'], sources=['fixture'],
                               filters=FilterConfig(date_from=None, date_to=None))
    monkeypatch.setitem(REGISTRY, 'fixture', lambda: Skipping(corpus))
    worker.run_detail('S', snapshot, collection=tmp_path,
                      filters=FilterConfig(date_from=None, date_to=None), backoff_s=0.001)


def test_skipped_items_get_status_reason_and_no_document(tmp_path, corpus, monkeypatch):
    run(tmp_path, monkeypatch, corpus)
    with closing(CrawlQueue(tmp_path / 'queue.sqlite')) as q:
        rows = dict(q.connection.execute('SELECT status,count(*) FROM urls GROUP BY status').fetchall())
        reasons = {r[0] for r in q.connection.execute("SELECT last_error FROM urls WHERE status='skipped'")}
    assert rows == {'done': 10, 'skipped': 10}
    assert reasons == {'no_ko_captions'}
    assert len(list(read_docs(tmp_path / 'docs'))) == 10


def test_skipped_is_not_counted_as_attempt_block_or_parse_error(tmp_path, corpus, monkeypatch):
    run(tmp_path, monkeypatch, corpus)
    import json
    channel = json.loads((tmp_path / 'worker_state.json').read_text())['channels']['fixture']
    assert channel['attempts'] == 10
    assert channel['blocked'] == 0 and channel['parse_errors'] == 0
    assert not channel['status'].startswith('paused')


def test_report_and_progress_count_skips_by_reason(tmp_path, corpus, monkeypatch):
    run(tmp_path, monkeypatch, corpus)
    queue = ReadQueue(tmp_path / 'queue.sqlite')
    assert report.progress(queue)['skipped'] == {'fixture': {'no_ko_captions': 10}}
    built = report.build_report(queue)
    assert built['channels']['fixture']['skip_reasons'] == {'no_ko_captions': 10}
    assert built['channels']['fixture']['skipped'] == 10
```

- [ ] **Step 2: 실패 확인**

Run: `backend/.venv/bin/python -m pytest backend/tests/crawl/test_skipped.py -q`
Expected: FAIL — `ImportError: cannot import name 'AdapterSkipped'`

- [ ] **Step 3: 구현**

`backend/app/crawl/adapters/base.py` (AdapterBlocked 아래):

```python
class AdapterSkipped(Exception):
    """The item intentionally yields no document (not a failure), e.g. no Korean captions."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason
```

`backend/app/crawl/adapters/__init__.py`: `from app.crawl.adapters.base import AdapterBlocked, AdapterSkipped, ...` 그리고 `__all__`에 `"AdapterSkipped"` 추가.

`backend/app/crawl/queue.py` (`mark_excluded` 바로 아래):

```python
    def mark_skipped(self, url_norm: str, source: str, reason: str) -> None:
        with self._write() as db:
            self._owns_completion(db, url_norm, source)
            db.execute("""UPDATE urls SET status='skipped',last_error=?,
                lease_until=NULL,lease_run_id=NULL,retry_at=NULL WHERE url_norm=? AND source=?""",
                       (reason, url_norm, source))
```

`backend/app/crawl/worker.py`:
- import에 `AdapterSkipped` 추가: `from app.crawl.adapters.base import AdapterBlocked, AdapterSkipped, FetchedDoc, ListItem, ListPage`
- `_Run.outcome` 맨 앞:

```python
    def outcome(self, source, error):
        if isinstance(error, AdapterSkipped):
            return  # Intentional skips are neither attempts nor failures.
        c = self.channels[source]
```

- `run_detail` 루프에서 `last_error = ...` 바로 위:

```python
            for row, fetched, error in _detail_results(run, adapters, stop, batch, commit):
                if isinstance(error, AdapterSkipped):
                    run.q.mark_skipped(row.url_norm, row.source, error.reason)
                    continue
```

`backend/app/crawl/report.py`:
- `progress()`의 `with` 블록 안, `tasks = ...` 다음:

```python
        skipped = {}
        # Members-only cafe posts are 'excluded' with reason 'restricted'; show them with the skips.
        for source, reason, count in db.execute(
                """SELECT source,coalesce(last_error,''),count(*) FROM urls
                   WHERE status='skipped' OR (status='excluded' AND last_error='restricted')
                   GROUP BY source,last_error"""):
            skipped.setdefault(source, {})[reason] = count
```
(T1 테스트에 `restricted` 케이스를 하나 더한다: `test_worker.py::test_exclude_restricted_adapter_excludes_urls`와 같은 방식으로 `exclude_restricted = True` 어댑터를 써서 20건을 모두 제외한 뒤 `report.progress(queue)['skipped'] == {'fixture': {'restricted': 20}}`.)
- `return dict(...)`에 `skipped=skipped` 추가.
- `build_report()`의 `distribution[source] = dict(...)`에 `skip_reasons=p['skipped'].get(source, {})` 추가.

- [ ] **Step 4: 통과 확인**

Run: `backend/.venv/bin/python -m pytest backend/tests/crawl/test_skipped.py backend/tests/crawl -q`
Expected: PASS (새 3건 + 기존 crawl 테스트 전부)

- [ ] **Step 5: Commit** (Controller) — `feat(crawl): 의도적 건너뜀(AdapterSkipped) 상태와 사유별 집계`

---

### Task T2: 새 채널 식별 · 설정 · 기본값

**Files:**
- Create: `backend/app/crawl/channels.py`
- Modify: `backend/app/crawl/schema.py`, `backend/app/context/models.py`, `backend/app/crawl/urls.py`, `backend/app/crawl/worker.py`, `backend/app/crawl/control.py`, `backend/app/routers/crawl_v2.py`, `backend/app/config.py`, `backend/app/context/labels.py`, `backend/app/prep/boilerplate.v1.json`, `backend/app/keywords/prompts.py`, `frontend/src/lib/contextLabels.ts`, `frontend/src/components/prep/prep.ts`
- Test: `backend/tests/crawl/test_channel_identity.py` (새), `backend/tests/crawl/test_urls.py`(케이스 추가)

**Interfaces:**
- Consumes: 없음
- Produces: `app.crawl.channels.NEW_CHANNELS = ('youtube_vlog', 'threads', 'naver_kin', 'cook82')`; `channel_defaults(source: str) -> tuple[int, float]` (동시 수, 간격); `COLLOQUIAL_CHANNELS: frozenset[str]`; `crawl_v2.YoutubeVlog(videos_per_keyword=20, min_duration_s=60, max_duration_s=3600)`; 설정 `settings.caption_window_s=20`, `caption_min_segment_s=45`, `caption_max_segment_s=300`, `caption_fixed_segment_s=90`, `threads_render_timeout_s=30`; 워커가 `youtube_vlog` 어댑터 `list_page(kw, cursor, *, videos_per_keyword, min_duration_s, max_duration_s)`를 호출하고 키워드당 상한을 `youtube_vlog.videos_per_keyword`로 둔다.

- [ ] **Step 1: 실패 테스트 작성** — `backend/tests/crawl/test_channel_identity.py`

```python
from contextlib import closing
import json

import pytest
from pydantic import ValidationError

from app.crawl import worker
from app.crawl.adapters import REGISTRY
from app.crawl.adapters.base import ListItem, ListPage
from app.crawl.channels import COLLOQUIAL_CHANNELS, NEW_CHANNELS, channel_defaults
from app.crawl.filters import FilterConfig
from app.crawl.queue import CrawlQueue
from app.crawl.schema import Doc
from app.crawl.urls import doc_id, normalize_url
from app.context.labels import LABELS
from app.context.models import Channel
from app.routers.crawl_v2 import Config


@pytest.mark.parametrize('source,expected', [
    ('youtube_vlog', (2, 0)), ('threads', (1, 2.0)), ('naver_kin', (1, 0.5)), ('cook82', (1, 0.5)),
    ('naver_blog', (1, 0.5)), ('youtube', (2, 0)), ('fixture', (4, 0)),
])
def test_channel_defaults(source, expected):
    assert channel_defaults(source) == expected


def test_new_channels_are_known_everywhere():
    assert NEW_CHANNELS == ('youtube_vlog', 'threads', 'naver_kin', 'cook82')
    for source in NEW_CHANNELS:
        assert Channel(source).value == source
        assert source in LABELS['channels']
        assert Doc.model_fields['source'].annotation.__args__.count(source) == 1
    assert {'threads', 'cook82', 'naver_kin', 'youtube', 'naver_cafe', 'ppomppu', 'clien'} <= COLLOQUIAL_CHANNELS


@pytest.mark.parametrize('source,prefix', [('youtube_vlog', 'yv'), ('threads', 'th'), ('naver_kin', 'kn'), ('cook82', 'c8')])
def test_new_prefixes(source, prefix):
    assert doc_id(source, 'https://example.com/a').startswith(prefix + '_')


def test_kin_url_keeps_question_identity_only():
    url = 'https://kin.naver.com/qna/detail.naver?dirId=80901&docId=493036426&answerNo=4&qb=7JeQ'
    assert normalize_url(url, 'naver_kin') == 'https://kin.naver.com/qna/detail.naver?dirId=80901&docId=493036426'


def test_cook82_url_keeps_board_and_number_only():
    url = 'https://www.82cook.com/entiz/read.php?bn=15&num=4245917&page=1&searchType=search&search1=1&keys=x'
    assert normalize_url(url, 'cook82') == 'https://www.82cook.com/entiz/read.php?bn=15&num=4245917'


def test_threads_url_is_canonical():
    assert normalize_url('https://threads.net/@abc/post/DNG2tXiBjzN/?xmt=1', 'threads') == \
        'https://www.threads.com/@abc/post/DNG2tXiBjzN'


def test_vlog_config_validation():
    ok = Config(channels=['youtube_vlog'])
    assert ok.youtube_vlog.model_dump() == {'videos_per_keyword': 20, 'min_duration_s': 60, 'max_duration_s': 3600}
    with pytest.raises(ValidationError):
        Config(channels=['youtube_vlog'], youtube_vlog={'min_duration_s': 600, 'max_duration_s': 60})
    with pytest.raises(ValidationError):
        Config(channels=['youtube_vlog'], youtube_vlog={'videos_per_keyword': 0})


def test_worker_passes_vlog_options_and_caps_per_keyword(tmp_path, monkeypatch):
    calls = []
    class Vlog:
        source = 'youtube_vlog'
        def list_page(self, kw, cursor, *, videos_per_keyword, min_duration_s, max_duration_s):
            calls.append((kw, videos_per_keyword, min_duration_s, max_duration_s))
            return ListPage([ListItem(f'https://www.youtube.com/watch?v={i:011d}', '', '', None, {})
                             for i in range(50)], None, 50)
        def fetch(self, item):
            return []
    monkeypatch.setitem(REGISTRY, 'youtube_vlog', Vlog)
    (tmp_path / 'manifest.json').write_text(json.dumps({'config': {
        'youtube_vlog': {'videos_per_keyword': 5, 'min_duration_s': 120, 'max_duration_s': 900}}}))
    worker.run_list('S', collection=tmp_path, keywords=['에어컨'], sources=['youtube_vlog'],
                    filters=FilterConfig(date_from=None, date_to=None))
    assert calls == [('에어컨', 5, 120, 900)]
    with closing(CrawlQueue(tmp_path / 'queue.sqlite')) as q:
        assert q.connection.execute("SELECT count(*) FROM urls WHERE source='youtube_vlog'").fetchone()[0] == 5
```

`backend/tests/crawl/test_urls.py`의 `test_doc_id_deterministic_and_prefixed` parametrize 목록에도 네 쌍을 추가한다.

- [ ] **Step 2: 실패 확인**

Run: `backend/.venv/bin/python -m pytest backend/tests/crawl/test_channel_identity.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.crawl.channels'`

- [ ] **Step 3: 구현**

`backend/app/crawl/channels.py`:

```python
"""Per-channel defaults shared by the worker, status API and keyword prompts."""

NEW_CHANNELS = ('youtube_vlog', 'threads', 'naver_kin', 'cook82')

_DEFAULTS = {
    'youtube': (2, 0), 'youtube_vlog': (2, 0),
    'threads': (1, 2.0),
    'naver_blog': (1, 0.5), 'naver_cafe': (1, 0.5), 'naver_kin': (1, 0.5),
    'clien': (1, 0.5), 'ppomppu': (1, 0.5), 'cook82': (1, 0.5),
}

COLLOQUIAL_CHANNELS = frozenset({'youtube', 'youtube_vlog', 'naver_cafe', 'ppomppu', 'clien',
                                 'community', 'threads', 'cook82', 'naver_kin'})


def channel_defaults(source: str) -> tuple[int, float]:
    """Return (concurrency, min_interval_s) used when a channel has no saved limits."""
    return _DEFAULTS.get(source, (4, 0))
```

`backend/app/crawl/worker.py` `_Run.__init__`의 기본값 줄을 바꾼다:

```python
        for s in sources:
            defaults = channel_defaults(s)
```
(`from app.crawl.channels import channel_defaults`). `execute()`의 목록 호출에 브이로그 옵션을 더한다:

```python
                    if source == 'youtube_vlog':
                        vlog = self.config.get('youtube_vlog', {})
                        options = {'videos_per_keyword': vlog.get('videos_per_keyword', 20),
                                   'min_duration_s': vlog.get('min_duration_s', 60),
                                   'max_duration_s': vlog.get('max_duration_s', 3600)}
```
(기존 `youtube` 분기 바로 뒤, `page = adapter.list_page(job.kw, job.cursor, **options)` 앞). `list_remaining`에:

```python
        if task.source == 'youtube_vlog':
            caps.append(self.config.get('youtube_vlog', {}).get('videos_per_keyword') or 0)
```

`backend/app/crawl/control.py` `_status_settings`의 `intervals` 계산을 `channel_defaults(source)[1]`로 바꾼다:

```python
        intervals = {source: limits.get(source, {}).get('min_interval_s', channel_defaults(source)[1])
                     for source in channels}
```

`backend/app/crawl/schema.py`: `source: Literal["naver_cafe", "naver_blog", "youtube", "ppomppu", "clien", "fixture", "youtube_vlog", "threads", "naver_kin", "cook82"]`.

`backend/app/context/models.py` `Channel`에 `youtube_vlog = "youtube_vlog"`, `threads = "threads"`, `naver_kin = "naver_kin"`, `cook82 = "cook82"`.

`backend/app/crawl/urls.py`:
- `_PREFIXES`에 `"youtube_vlog":"yv","threads":"th","naver_kin":"kn","cook82":"c8"`.
- `normalize_url`의 `trackers` 선택에 `youtube_vlog`를 `youtube`와 같게(`elif source in {"youtube", "youtube_vlog"}`), 호스트 정리 분기에도 `youtube_vlog` 포함.
- `return` 직전에 추가:

```python
    if source == "naver_kin" and host == "kin.naver.com":
        params = [(k, v) for k, v in params if k in {"dirId", "docId"}]
    elif source == "cook82" and host in {"www.82cook.com", "82cook.com"}:
        netloc = "www.82cook.com"
        params = [(k, v) for k, v in params if k in {"bn", "num"}]
    elif source == "threads" and host in {"threads.net", "www.threads.net", "threads.com", "www.threads.com"}:
        scheme, netloc, params = "https", "www.threads.com", []
```

`backend/app/routers/crawl_v2.py`:

```python
class YoutubeVlog(BaseModel):
    model_config = ConfigDict(extra='forbid')
    videos_per_keyword: int = Field(default=20, ge=1)
    min_duration_s: int = Field(default=60, ge=0)
    max_duration_s: int = Field(default=3600, ge=1)

    @model_validator(mode='after')
    def ordered(self):
        if self.min_duration_s >= self.max_duration_s:
            raise ValueError('min_duration_s must be below max_duration_s')
        return self
```
그리고 `Config`에 `youtube_vlog: YoutubeVlog = Field(default_factory=YoutubeVlog)`.

`backend/app/config.py` `Settings`에:

```python
    caption_window_s: int = 20
    caption_min_segment_s: int = 45
    caption_max_segment_s: int = 300
    caption_fixed_segment_s: int = 90
    threads_render_timeout_s: int = 30
```

`backend/app/context/labels.py`와 `frontend/src/lib/contextLabels.ts`의 `channels`에 `"youtube_vlog": "유튜브 브이로그"`, `"threads": "Threads"`, `"naver_kin": "지식iN"`, `"cook82": "82쿡"`.

`backend/app/prep/boilerplate.v1.json`에 `"youtube_vlog": [], "threads": [], "naver_kin": [], "cook82": []`. `frontend/src/components/prep/prep.ts`의 `DEFAULT_BOILERPLATE`에 같은 키를 빈 배열로, `CHANNELS`에 `['youtube_vlog', '유튜브 브이로그'], ['threads', 'Threads'], ['naver_kin', '지식iN'], ['cook82', '82쿡']`.

`backend/app/keywords/prompts.py`: `if set(state.channels) & {"youtube", ...}:` 를 `if set(state.channels) & COLLOQUIAL_CHANNELS:` 로(`from app.crawl.channels import COLLOQUIAL_CHANNELS`).

- [ ] **Step 4: 통과 확인**

Run: `backend/.venv/bin/python -m pytest backend/tests/crawl backend/tests/context backend/tests/keywords backend/tests/prep -q && npm --prefix frontend test`
Expected: PASS (라벨 동기화 · 상투어 동기화 테스트가 있으면 함께 통과)

- [ ] **Step 5: Commit** (Controller) — `feat(crawl): 새 채널 4개 식별자 · URL 정규화 · 기본 한도 · 브이로그 설정`

---

### Task T3: 자막 파싱 · 화제 분할 (`captions.py`)

**Files:**
- Create: `backend/app/crawl/captions.py`
- Test: `backend/tests/crawl/test_captions.py`

**Interfaces:**
- Produces: `Cue(start_ms: int, end_ms: int, text: str)`; `Segment(start_s: int, end_s: int, text: str)`; `parse_json3(data: dict) -> list[Cue]`; `segment(cues: list[Cue], embedder, *, window_s=20, min_s=45, max_s=300, fixed_s=90) -> tuple[list[Segment], str]` — 두 번째 값은 `'embedding' | 'fixed' | 'single'`. `embedder`는 `embed(texts: list[str]) -> array[n, dim]`을 가진 객체 또는 `None`.

- [ ] **Step 1: 실패 테스트 작성** — `backend/tests/crawl/test_captions.py`

```python
import numpy as np
import pytest

from app.crawl.captions import Cue, Segment, parse_json3, segment


class TopicEmbedder:
    def embed(self, texts, input_type='document'):
        return np.asarray([[1.0, 0.0] if '청소' in t else [0.0, 1.0] for t in texts], dtype=np.float32)


class Broken:
    def embed(self, texts, input_type='document'):
        raise RuntimeError('down')


class Zero:
    def embed(self, texts, input_type='document'):
        return np.zeros((len(texts), 2), dtype=np.float32)


def cues(spec):
    """spec: list of (topic_word, seconds) blocks, one 5-second cue per 5 seconds."""
    out, t = [], 0
    for word, seconds in spec:
        for _ in range(seconds // 5):
            out.append(Cue(t * 1000, (t + 5) * 1000, f'{word} 이야기 {t}'))
            t += 5
    return out


def test_parse_json3_strips_markers_and_empty_events():
    data = {'events': [
        {'tStartMs': 0, 'dDurationMs': 2000, 'segs': [{'utf8': '[음악]'}]},
        {'tStartMs': 2000, 'dDurationMs': 3000, 'segs': [{'utf8': '에어컨 '}, {'utf8': '청소 [박수] 했어요'}]},
        {'tStartMs': 6000},
    ]}
    assert parse_json3(data) == [Cue(2000, 5000, '에어컨 청소 했어요')]


def test_splits_at_topic_change():
    result, method = segment(cues([('청소', 120), ('전기세', 120)]), TopicEmbedder())
    assert method == 'embedding'
    assert [(s.start_s, s.end_s) for s in result] == [(0, 120), (120, 240)]
    assert '청소' in result[0].text and '전기세' not in result[0].text


def test_same_input_same_segments():
    data = cues([('청소', 100), ('전기세', 140), ('청소', 100)])
    assert segment(data, TopicEmbedder()) == segment(data, TopicEmbedder())


def test_boundaries_respect_minimum_length():
    result, _ = segment(cues([('청소', 120), ('전기세', 20), ('청소', 120)]), TopicEmbedder(), min_s=45)
    assert all(s.end_s - s.start_s >= 45 for s in result)


def test_long_single_topic_is_split_by_fixed_length():
    result, method = segment(cues([('청소', 700)]), TopicEmbedder(), max_s=300, fixed_s=90)
    assert method == 'embedding'
    assert [s.start_s for s in result] == [0, 90, 180, 270, 360, 450, 540, 630]
    assert result[-1].end_s == 700


@pytest.mark.parametrize('embedder', [None, Broken(), Zero()])
def test_fallback_to_fixed_segments(embedder):
    result, method = segment(cues([('청소', 120), ('전기세', 120)]), embedder, fixed_s=90)
    assert method == 'fixed'
    assert [(s.start_s, s.end_s) for s in result] == [(0, 90), (90, 180), (180, 240)]


def test_short_video_is_single_segment():
    result, method = segment(cues([('청소', 30)]), TopicEmbedder(), min_s=45)
    assert method == 'single'
    assert result == [Segment(0, 30, ' '.join(c.text for c in cues([('청소', 30)])))]


def test_empty_cues():
    assert segment([], TopicEmbedder()) == ([], 'single')
```

- [ ] **Step 2: 실패 확인**

Run: `backend/.venv/bin/python -m pytest backend/tests/crawl/test_captions.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.crawl.captions'`

- [ ] **Step 3: 구현** — `backend/app/crawl/captions.py`

```python
"""Korean caption cues → topic segments (TextTiling over window embeddings).

Deterministic: identical cues and embedder output yield identical boundaries.
Boundaries are whole seconds because they become document thread keys.
"""
from dataclasses import dataclass
import math
import re

import numpy as np

_MARKER = re.compile(r'\[[^\]\n]{1,12}\]')
_EPS = 1e-9


@dataclass(frozen=True)
class Cue:
    start_ms: int
    end_ms: int
    text: str


@dataclass(frozen=True)
class Segment:
    start_s: int
    end_s: int
    text: str


def parse_json3(data: dict) -> list[Cue]:
    cues = []
    for event in data.get('events') or []:
        segs = event.get('segs')
        if not segs or 'tStartMs' not in event:
            continue
        text = ' '.join(_MARKER.sub(' ', ''.join(s.get('utf8', '') for s in segs)).split())
        if text:
            start = int(event['tStartMs'])
            cues.append(Cue(start, start + int(event.get('dDurationMs') or 0), text))
    return sorted(cues, key=lambda c: (c.start_ms, c.end_ms))


def _text(cues):
    return ' '.join(c.text for c in cues)


def _cut(cues, bounds):
    out = []
    for a, b in zip(bounds, bounds[1:]):
        part = [c for c in cues if a * 1000 <= c.start_ms < b * 1000]
        if part:
            out.append(Segment(a, b, _text(part)))
    return out


def _fixed_bounds(a, b, fixed_s):
    return list(range(a + fixed_s, b, fixed_s))


def segment(cues, embedder, *, window_s=20, min_s=45, max_s=300, fixed_s=90):
    if not cues:
        return [], 'single'
    end_s = max(1, math.ceil(max(c.end_ms for c in cues) / 1000))
    groups = {}
    for c in cues:
        groups.setdefault(c.start_ms // (window_s * 1000), []).append(c)
    windows = [(k * window_s, groups[k]) for k in sorted(groups)]
    if end_s < min_s or len(windows) < 2:
        return [Segment(0, end_s, _text(cues))], 'single'
    if embedder is None:
        return _cut(cues, [0, *_fixed_bounds(0, end_s, fixed_s), end_s]), 'fixed'
    try:
        vectors = np.asarray(embedder.embed([_text(w) for _, w in windows]), dtype=np.float64)
    except Exception:
        return _cut(cues, [0, *_fixed_bounds(0, end_s, fixed_s), end_s]), 'fixed'
    norms = np.linalg.norm(vectors, axis=1) if vectors.ndim == 2 else np.zeros(0)
    if vectors.ndim != 2 or len(vectors) != len(windows) or not np.isfinite(vectors).all() or (norms < _EPS).any():
        return _cut(cues, [0, *_fixed_bounds(0, end_s, fixed_s), end_s]), 'fixed'
    unit = vectors / norms[:, None]
    sims = (unit[:-1] * unit[1:]).sum(axis=1)
    depth = np.asarray([(sims[:i + 1].max() - s) + (sims[i:].max() - s) for i, s in enumerate(sims)])
    gaps = [windows[i + 1][0] for i in range(len(sims))]
    cutoff = depth.mean() - depth.std() / 2
    bounds = [0, end_s]
    for i in sorted(range(len(sims)), key=lambda i: (-depth[i], gaps[i])):
        if depth[i] <= _EPS or depth[i] <= cutoff:
            continue
        trial = sorted({*bounds, gaps[i]})
        k = trial.index(gaps[i])
        if gaps[i] - trial[k - 1] >= min_s and trial[k + 1] - gaps[i] >= min_s:
            bounds = trial

    def split_long(a, b):
        if b - a <= max_s:
            return []
        inside = [(depth[i], gaps[i]) for i in range(len(sims))
                  if depth[i] > _EPS and a + min_s <= gaps[i] <= b - min_s]
        if not inside:
            return _fixed_bounds(a, b, fixed_s)
        t = sorted(inside, key=lambda d: (-d[0], d[1]))[0][1]
        return [*split_long(a, t), t, *split_long(t, b)]

    final = [0]
    for a, b in zip(bounds, bounds[1:]):
        final += [*split_long(a, b), b]
    return _cut(cues, final), 'embedding'
```

- [ ] **Step 4: 통과 확인**

Run: `backend/.venv/bin/python -m pytest backend/tests/crawl/test_captions.py -q`
Expected: PASS (9건)

- [ ] **Step 5: Commit** (Controller) — `feat(crawl): 자막 json3 파싱과 임베딩 기반 화제 분할`

---

### Task T4: 유튜브 브이로그 어댑터

**Files:**
- Modify: `backend/app/crawl/adapters/youtube.py` (`_extract` 본문을 모듈 함수 `extract_info(url, **options)`로 옮기고 메서드는 그 함수를 부른다 — 동작 동일), `backend/app/crawl/adapters/__init__.py`, `backend/tests/crawl/test_adapter_wiring.py`
- Create: `backend/app/crawl/adapters/youtube_vlog.py`
- Test: `backend/tests/crawl/adapters/test_youtube_vlog.py`

**Interfaces:**
- Consumes: T1 `AdapterSkipped`; T2 설정값 · `youtube_vlog` 목록 옵션; T3 `parse_json3`, `segment`; `app.vectors.embedder.get_embedder`
- Produces: `YoutubeVlogAdapter(embedder_factory=None)`, `source = 'youtube_vlog'`, `is_available()`(유튜브와 같은 조건), `list_page(kw, cursor, *, videos_per_keyword=20, min_duration_s=60, max_duration_s=3600)`, `fetch(item) -> list[FetchedDoc]`. 문서 `src_meta` 키: `video_id, video_title, channel, duration, view_count, segment_start_s, segment_end_s, caption_kind('manual'|'auto'), segmenter`.

- [ ] **Step 1: 실패 테스트 작성** — `backend/tests/crawl/adapters/test_youtube_vlog.py`

```python
import json

import numpy as np
import pytest
import yt_dlp

from app.config import settings
from app.crawl.adapters.base import AdapterBlocked, AdapterSkipped, ListItem


def json3(blocks):
    events, t = [], 0
    for word, seconds in blocks:
        for _ in range(seconds // 5):
            events.append({'tStartMs': t * 1000, 'dDurationMs': 5000, 'segs': [{'utf8': f'{word} 이야기 {t}'}]})
            t += 5
    return json.dumps({'events': events}).encode()


class TopicEmbedder:
    def embed(self, texts, input_type='document'):
        return np.asarray([[1.0, 0.0] if '청소' in t else [0.0, 1.0] for t in texts], dtype=np.float32)


VIDEOS = {
    'manualvid01': {'id': 'manualvid01', 'title': '여름 일상', 'duration': 240, 'channel': '채널A', 'channel_id': 'UC_A',
                    'timestamp': 1790000000, 'view_count': 10,
                    'subtitles': {'ko': [{'ext': 'json3', 'url': 'https://cap/manual'}]},
                    'automatic_captions': {'ko': [{'ext': 'json3', 'url': 'https://cap/auto'}]}},
    'autovid0002': {'id': 'autovid0002', 'title': '집안일', 'duration': 240, 'channel': '채널B', 'channel_id': 'UC_B',
                    'timestamp': 1790000000, 'subtitles': {},
                    'automatic_captions': {'ko': [{'ext': 'vtt', 'url': 'https://cap/vtt'}, {'ext': 'json3', 'url': 'https://cap/auto2'}]}},
    'nocaption03': {'id': 'nocaption03', 'title': '무음', 'duration': 240, 'channel_id': 'UC_C',
                    'subtitles': {}, 'automatic_captions': {'en': [{'ext': 'json3', 'url': 'https://cap/en'}]}},
}
CAPTIONS = {'https://cap/manual': json3([('청소', 120), ('전기세', 120)]),
            'https://cap/auto2': json3([('청소', 240)])}


@pytest.fixture
def ytdl(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, 'author_salt_path', str(tmp_path / 'salt'))
    calls = []

    class Response:
        def __init__(self, body):
            self.body = body
        def read(self):
            return self.body

    class YoutubeDL:
        def __init__(self, options):
            self.options = options
        def __enter__(self):
            return self
        def __exit__(self, *a):
            pass
        def extract_info(self, url, download=True):
            calls.append(('extract', url, self.options))
            if url.startswith('ytsearch'):
                return {'entries': [
                    {'id': 'short000001', 'duration': 30, 'title': 'shorts'},
                    {'id': 'manualvid01', 'duration': 240, 'title': '여름 일상', 'timestamp': 1790000000},
                    None,
                    {'id': 'toolong0001', 'duration': 7200, 'title': 'live'},
                    {'id': 'autovid0002', 'duration': 240, 'title': '집안일'},
                    {'id': 'nodur000001', 'title': 'unknown length'},
                ]}
            return dict(VIDEOS[url.rsplit('=', 1)[1]])
        def urlopen(self, url):
            calls.append(('urlopen', url))
            return Response(CAPTIONS[url])

    monkeypatch.setattr(yt_dlp, 'YoutubeDL', YoutubeDL)
    return calls


def item(video):
    return ListItem(f'https://www.youtube.com/watch?v={video}', '', '', None, {'video_id': video})


def test_list_appends_vlog_filters_duration_and_limits(ytdl):
    from app.crawl.adapters.youtube_vlog import YoutubeVlogAdapter
    page = YoutubeVlogAdapter(embedder_factory=TopicEmbedder).list_page(
        '에어컨', None, videos_per_keyword=1, min_duration_s=60, max_duration_s=3600)
    assert ytdl[0][1] == 'ytsearch2:에어컨 브이로그'
    assert [i.url for i in page.items] == ['https://www.youtube.com/watch?v=manualvid01']
    assert page.next_cursor is None


def test_fetch_prefers_manual_captions_and_splits_by_topic(ytdl):
    from app.crawl.adapters.youtube_vlog import YoutubeVlogAdapter
    docs = YoutubeVlogAdapter(embedder_factory=TopicEmbedder).fetch(item('manualvid01'))
    assert ('urlopen', 'https://cap/manual') in ytdl
    assert [(d.src_meta['segment_start_s'], d.src_meta['segment_end_s']) for d in docs] == [(0, 120), (120, 240)]
    assert [d.thread_key for d in docs] == ['0-120', '120-240']
    assert {d.src_meta['caption_kind'] for d in docs} == {'manual'}
    assert {d.src_meta['segmenter'] for d in docs} == {'embedding'}
    assert docs[0].title == '여름 일상' and docs[0].author_raw == 'UC_A' and docs[0].access == 'public'
    assert '전기세' not in docs[0].body


def test_fetch_uses_json3_auto_captions_when_no_manual(ytdl):
    from app.crawl.adapters.youtube_vlog import YoutubeVlogAdapter
    docs = YoutubeVlogAdapter(embedder_factory=TopicEmbedder).fetch(item('autovid0002'))
    assert ('urlopen', 'https://cap/auto2') in ytdl
    assert {d.src_meta['caption_kind'] for d in docs} == {'auto'}


def test_no_korean_captions_is_skipped(ytdl):
    from app.crawl.adapters.youtube_vlog import YoutubeVlogAdapter
    with pytest.raises(AdapterSkipped) as raised:
        YoutubeVlogAdapter(embedder_factory=TopicEmbedder).fetch(item('nocaption03'))
    assert raised.value.reason == 'no_ko_captions'


def test_unavailable_embedder_falls_back_to_fixed(ytdl):
    from app.crawl.adapters.youtube_vlog import YoutubeVlogAdapter
    def missing():
        raise RuntimeError('Voyage API key is not configured')
    docs = YoutubeVlogAdapter(embedder_factory=missing).fetch(item('manualvid01'))
    assert {d.src_meta['segmenter'] for d in docs} == {'fixed'}
    assert [d.thread_key for d in docs] == ['0-90', '90-180', '180-240']


def test_bot_check_is_blocked(monkeypatch, ytdl):
    from app.crawl.adapters.youtube_vlog import YoutubeVlogAdapter
    def refuse(self, url, download=True):
        raise yt_dlp.utils.DownloadError("Sign in to confirm you're not a bot")
    monkeypatch.setattr(yt_dlp.YoutubeDL, 'extract_info', refuse)
    with pytest.raises(AdapterBlocked):
        YoutubeVlogAdapter(embedder_factory=TopicEmbedder).fetch(item('manualvid01'))
```

`backend/tests/crawl/test_adapter_wiring.py`의 `test_real_registry_availability_is_offline`: 기대 집합에 `'youtube_vlog'`를 더하고, 클래스 확인 목록에 `('youtube_vlog', YoutubeVlogAdapter)`를 더한다.

- [ ] **Step 2: 실패 확인**

Run: `backend/.venv/bin/python -m pytest backend/tests/crawl/adapters/test_youtube_vlog.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.crawl.adapters.youtube_vlog'`

- [ ] **Step 3: 구현**

`backend/app/crawl/adapters/youtube.py`: 메서드 `_extract`의 본문을 모듈 함수로 옮긴다.

```python
def extract_info(url: str, **options) -> dict:
    yt_dlp = importlib.import_module('yt_dlp')
    try:
        with yt_dlp.YoutubeDL(dict(quiet=True, no_warnings=True, skip_download=True, **options)) as extractor:
            result = extractor.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as exc:
        if _blocked(exc):
            raise AdapterBlocked('YouTube blocked the request') from exc
        raise
    if not isinstance(result, dict):
        raise ValueError('Expected a yt-dlp information dictionary')
    return result
```
`YoutubeAdapter._extract(self, url, **options)`는 `return extract_info(url, **options)`.

`backend/app/crawl/adapters/youtube_vlog.py`:

```python
"""Korean vlog captions as topic-segment documents; media is never downloaded."""
import importlib
import json

from app.config import settings
from app.crawl.adapters.base import AdapterBlocked, AdapterSkipped, FetchedDoc, ListItem, ListPage
from app.crawl.adapters.youtube import YoutubeAdapter, _blocked, _date, _metadata, extract_info
from app.crawl.captions import parse_json3, segment

_UNSET = object()


def _korean_track(info):
    for kind, key, langs in (('manual', 'subtitles', ('ko',)), ('auto', 'automatic_captions', ('ko-orig', 'ko'))):
        tracks = info.get(key) or {}
        for lang in langs:
            for track in tracks.get(lang) or []:
                if track.get('ext') == 'json3' and track.get('url'):
                    return track, kind
    return None, None


class YoutubeVlogAdapter:
    source = 'youtube_vlog'

    @classmethod
    def is_available(cls) -> bool:
        return YoutubeAdapter.is_available()

    def __init__(self, embedder_factory=None):
        if embedder_factory is None:
            from app.vectors.embedder import get_embedder
            embedder_factory = get_embedder
        self._factory = embedder_factory
        self._embedder = _UNSET

    def _get_embedder(self):
        if self._embedder is _UNSET:
            try:
                self._embedder = self._factory()
            except Exception:
                self._embedder = None
        return self._embedder

    def list_page(self, kw, cursor, *, videos_per_keyword=20, min_duration_s=60, max_duration_s=3600):
        if cursor is not None:
            raise ValueError('YouTube search has no continuation cursor')
        if videos_per_keyword <= 0:
            raise ValueError('videos_per_keyword must be positive')
        info = extract_info(f'ytsearch{videos_per_keyword * 2}:{kw} 브이로그', extract_flat=True)
        items = []
        for entry in info.get('entries') or []:
            duration = (entry or {}).get('duration')
            if not entry or not entry.get('id') or duration is None:
                continue
            if not min_duration_s <= duration <= max_duration_s:
                continue
            items.append(ListItem(f"https://www.youtube.com/watch?v={entry['id']}", entry.get('title') or '',
                                  entry.get('description') or '', _date(entry), _metadata(entry)))
            if len(items) >= videos_per_keyword:
                break
        return ListPage(items, None, len(items))

    def fetch(self, item):
        yt_dlp = importlib.import_module('yt_dlp')
        try:
            with yt_dlp.YoutubeDL(dict(quiet=True, no_warnings=True, skip_download=True)) as ydl:
                info = ydl.extract_info(item.url, download=False)
                track, kind = _korean_track(info or {})
                if track is None:
                    raise AdapterSkipped('no_ko_captions')
                data = json.loads(ydl.urlopen(track['url']).read().decode('utf-8'))
        except (AdapterSkipped, AdapterBlocked):
            raise
        except Exception as exc:
            if _blocked(exc):
                raise AdapterBlocked('YouTube blocked the request') from exc
            raise
        cues = parse_json3(data)
        if not cues:
            raise AdapterSkipped('no_ko_captions')
        segments, method = segment(cues, self._get_embedder(), window_s=settings.caption_window_s,
                                   min_s=settings.caption_min_segment_s, max_s=settings.caption_max_segment_s,
                                   fixed_s=settings.caption_fixed_segment_s)
        meta = _metadata(info)
        author = info.get('channel_id') or info.get('uploader_id')
        return [FetchedDoc(info.get('title') or item.title, s.text, [], _date(info),
                           {**meta, 'segment_start_s': s.start_s, 'segment_end_s': s.end_s,
                            'caption_kind': kind, 'segmenter': method},
                           'public', author, f'{s.start_s}-{s.end_s}') for s in segments]
```

`backend/app/crawl/adapters/__init__.py`: `from app.crawl.adapters.youtube_vlog import YoutubeVlogAdapter`, `REGISTRY`에 `"youtube_vlog": YoutubeVlogAdapter`.

- [ ] **Step 4: 통과 확인**

Run: `backend/.venv/bin/python -m pytest backend/tests/crawl/adapters/test_youtube_vlog.py backend/tests/crawl/adapters/test_youtube.py backend/tests/crawl/test_adapter_wiring.py -q`
Expected: PASS

- [ ] **Step 5: Commit** (Controller) — `feat(crawl): 유튜브 브이로그 채널 — 한국어 자막 화제 구간 문서`

---

### Task T5: 지식iN 어댑터

**Files:**
- Create: `backend/app/crawl/adapters/naver_kin.py`, `backend/tests/fixtures/http/naver_kin/` (manifest.json + T0 녹화에서 옮긴 마스킹 HTML: `list-1.html`, `list-2.html`, `list-empty.html`, `question-1.html`~`question-3.html`, `question-deleted.html`)
- Modify: `backend/app/crawl/adapters/__init__.py`, `backend/tests/crawl/test_adapter_wiring.py`
- Test: `backend/tests/crawl/adapters/test_naver_kin.py`

**픽스처 마스킹:** 질문 · 답변 본문은 앞 80자만 남기고 나머지를 지운다. 답변자 닉네임 · 아이디(`kpla****` 등)는 `user1`… 로 바꾼다. 마크업 구조(클래스 · 속성)는 그대로 둔다.

**Interfaces:**
- Consumes: T1 `AdapterSkipped`, T2 정규화 · 기본값, `CommunityAdapter`
- Produces: `NaverKinAdapter(client=None, *, clock, sleep)`, `source='naver_kin'`, `origin='https://kin.naver.com'`. 목록 커서 = 다음 페이지 번호 문자열. `src_meta` 키: `dir_id, doc_id, answer_count, tags`.

- [ ] **Step 1: 실패 테스트 작성** — `backend/tests/crawl/adapters/test_naver_kin.py`

```python
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest

from app.config import settings
from app.crawl.adapters.base import AdapterBlocked, AdapterSkipped

FIXTURES = Path(__file__).parents[2] / 'fixtures' / 'http' / 'naver_kin'


class Clock:
    def __init__(self):
        self.now = 0.0
    def __call__(self):
        return self.now
    def sleep(self, d):
        self.now += d


@pytest.fixture(autouse=True)
def salt(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, 'author_salt_path', str(tmp_path / 'salt'))


def adapter(status=200):
    manifest = json.loads((FIXTURES / 'manifest.json').read_text())
    seen = []
    def respond(request):
        seen.append(str(request.url))
        q = parse_qs(urlsplit(str(request.url)).query)
        for cap in manifest['requests']:
            cq = parse_qs(urlsplit(cap['url']).query)
            if urlsplit(cap['url']).path == request.url.path and all(q.get(k) == cq.get(k) for k in ('query', 'page', 'docId')):
                return httpx.Response(status, content=(FIXTURES / cap['file']).read_bytes())
        raise AssertionError(f'Unrecorded request: {request.url}')
    from app.crawl.adapters.naver_kin import NaverKinAdapter
    clock = Clock()
    return NaverKinAdapter(httpx.Client(transport=httpx.MockTransport(respond)), clock=clock, sleep=clock.sleep), manifest, seen


def test_list_page_parses_ten_normalized_questions_and_next_cursor():
    a, manifest, _ = adapter()
    page = a.list_page(manifest['keyword'], None)
    assert len(page.items) == 10
    assert all(i.url.startswith('https://kin.naver.com/qna/detail.naver?dirId=') and 'answerNo' not in i.url for i in page.items)
    assert len({i.url for i in page.items}) == 10
    assert all(i.title for i in page.items)
    assert all(isinstance(i.src_meta['answer_count'], int) for i in page.items)
    assert page.next_cursor == '2'


def test_empty_search_ends_without_error():
    a, manifest, _ = adapter()
    page = a.list_page(manifest['empty_keyword'], None)
    assert page.items == [] and page.next_cursor is None


def test_fetch_reads_question_only():
    a, manifest, _ = adapter()
    from app.crawl.adapters.base import ListItem
    url = manifest['question_url']
    doc = a.fetch(ListItem(url, '', '', None, {}))[0]
    assert doc.title and doc.body
    assert doc.comments == []
    assert doc.date and len(doc.date) == 10
    assert doc.src_meta['doc_id'] == parse_qs(urlsplit(url).query)['docId'][0]
    assert doc.src_meta['answer_count'] >= 1
    assert manifest['answer_marker'] not in doc.body  # first words of an answer in the capture


def test_deleted_question_is_skipped():
    a, manifest, _ = adapter()
    from app.crawl.adapters.base import ListItem
    with pytest.raises(AdapterSkipped) as raised:
        a.fetch(ListItem(manifest['deleted_url'], '', '', None, {}))
    assert raised.value.reason == 'deleted'


def test_http_429_is_blocked():
    a, manifest, _ = adapter(status=429)
    with pytest.raises(AdapterBlocked):
        a.list_page(manifest['keyword'], None)


def test_changed_markup_is_a_parse_error_not_an_empty_page():
    a, manifest, _ = adapter()
    with pytest.raises(ValueError):
        a.list_page(manifest['changed_keyword'], None)  # list-changed.html: list-1.html에서 ul.basic1만 지운 사본
```

manifest.json 형식(Codex가 T0 녹화로 작성):

```json
{"keyword": "에어컨", "empty_keyword": "zxqwvplmn",
 "question_url": "https://kin.naver.com/qna/detail.naver?dirId=80901&docId=493036426",
 "deleted_url": "https://kin.naver.com/qna/detail.naver?dirId=1&docId=1",
 "answer_marker": "<캡처 속 첫 답변의 앞 몇 글자>",
 "requests": [{"url": "https://kin.naver.com/search/list.naver?query=에어컨&page=1", "file": "list-1.html"}]}
```

`test_adapter_wiring.py` 기대 집합에 `'naver_kin'`, 클래스 목록에 `('naver_kin', NaverKinAdapter)`.

- [ ] **Step 2: 실패 확인**

Run: `backend/.venv/bin/python -m pytest backend/tests/crawl/adapters/test_naver_kin.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.crawl.adapters.naver_kin'`

- [ ] **Step 3: 구현** — `backend/app/crawl/adapters/naver_kin.py`

```python
"""Naver KiN question search and question bodies; answers are never stored."""
import re
from urllib.parse import parse_qs, urlencode, urlsplit

from app.crawl.adapters.base import AdapterSkipped, FetchedDoc, ListItem, ListPage
from app.crawl.adapters.community import CommunityAdapter, date_text, selected, text
from app.crawl.urls import normalize_url


class NaverKinAdapter(CommunityAdapter):
    source = 'naver_kin'
    origin = 'https://kin.naver.com'

    def list_url(self, kw, cursor):
        page = int(cursor or 1)
        if page < 1:
            raise ValueError('KiN page must be positive')
        return f'{self.origin}/search/list.naver?{urlencode({"query": kw, "page": page})}'

    # T0 녹화(list-empty.html)에서 확인한 "결과 없음" 표시로 맞춘다.
    NO_RESULT_SELECTORS = '.noresult, .no_result, #noResult'
    NO_RESULT_TEXT = ('검색결과가 없습니다', '검색 결과가 없습니다')

    def parse_list(self, tree, cursor):
        items, seen = [], set()
        rows = tree.css('ul.basic1 > li')
        if not rows:
            body = tree.body.text() if tree.body else ''
            if tree.css_first(self.NO_RESULT_SELECTORS) is not None or any(t in body for t in self.NO_RESULT_TEXT):
                return ListPage([], None, 0)
            raise ValueError('KiN search results could not be parsed')  # never a silent empty page
        for row in rows:
            link = row.css_first('a._searchListTitleAnchor')
            if link is None or not link.attributes.get('href'):
                raise ValueError('KiN result title missing')
            url = normalize_url(link.attributes['href'], self.source)
            query = parse_qs(urlsplit(url).query)
            if url in seen or 'docId' not in query:
                continue
            seen.add(url)
            hit = re.search(r'답변수\s*(\d+)', selected(row, '.hit'))
            snippet = ' '.join(text(dd) for dd in row.css('dl > dd')
                               if not set(dd.attributes.get('class', '').split()) & {'txt_inline', 'tag_area', 'txt_block'})
            items.append(ListItem(url, text(link), snippet, date_text(selected(row, 'dd.txt_inline')),
                                  {'dir_id': query.get('dirId', [''])[0], 'doc_id': query['docId'][0],
                                   'answer_count': int(hit[1]) if hit else 0}))
        current = int(cursor or 1)
        later = [int(m) for m in re.findall(r'[?&]page=(\d+)', tree.html or '') if int(m) > current]
        return ListPage(items, str(current + 1) if items and later else None, None)

    def parse_detail(self, tree, item):
        body = tree.css_first('.questionDetail')
        if body is None:
            if re.search(r'삭제|존재하지 않', tree.body.text() if tree.body else ''):
                raise AdapterSkipped('deleted')
            raise ValueError('KiN question body missing')
        for node in body.css('._waitingForReplaceImage, script, style'):
            node.decompose()
        title_node = tree.css_first('.endTitleSection')
        for node in (title_node.css('.blind, svg, .iconQuestion') if title_node else []):
            node.decompose()
        tags = [t for t in (body.attributes.get('data-tag') or '').split(',') if t]
        query = parse_qs(urlsplit(item.url).query)
        written = re.search(r'작성일</span>\s*([0-9.]+)', tree.html or '')
        return FetchedDoc(
            text(title_node) or item.title, text(body), [],
            date_text((written[1] if written else '').replace('.', '-')) or item.date,
            {**item.src_meta, 'dir_id': query.get('dirId', [''])[0], 'doc_id': query.get('docId', [''])[0],
             'answer_count': len(tree.css('.answerArea')), 'tags': tags},
            'public', None,
        )
```

주의: `data-tag`는 URL 인코딩일 수 있다 — 녹화 값이 퍼센트 인코딩이면 `urllib.parse.unquote` 후 분리한다(테스트는 태그가 비어 있지 않음만 확인하도록 위 테스트에 `assert doc.src_meta['tags']`를 추가해도 된다). `date_text`는 `YYYY-MM-DD`/`YYYY.MM.DD` 패턴을 받는다.

`__init__.py` 등록: `"naver_kin": NaverKinAdapter`.

- [ ] **Step 4: 통과 확인**

Run: `backend/.venv/bin/python -m pytest backend/tests/crawl/adapters/test_naver_kin.py backend/tests/crawl/test_adapter_wiring.py -q`
Expected: PASS

- [ ] **Step 5: Commit** (Controller) — `feat(crawl): 지식iN 채널 — 질문 제목 · 본문만 수집`

---

### Task T6: 82쿡 어댑터

**Files:**
- Create: `backend/app/crawl/adapters/cook82.py`, `backend/tests/fixtures/http/cook82/` (manifest.json, `list-1.html`, `list-empty.html`, `article-1.html`~`article-3.html`)
- Modify: `backend/app/crawl/adapters/__init__.py`, `backend/tests/crawl/test_adapter_wiring.py`
- Test: `backend/tests/crawl/adapters/test_cook82.py`

**픽스처 마스킹:** 닉네임 → `user1`…, IP 문자열(`#writerIP`, `.ip` 안 값) → `0.0.xxx.0`, 본문 · 댓글은 앞 80자만. 마크업 구조 유지.

**Interfaces:**
- Consumes: T2 정규화 · 기본값, T0에서 확정한 `search1` 값(이하 `SEARCH_SCOPE`), `CommunityAdapter`
- Produces: `Cook82Adapter`, `source='cook82'`, `origin='https://www.82cook.com'`, 커서 = 다음 페이지 번호 문자열. `src_meta` 키: `board`, `num`, `comment_count`.

- [ ] **Step 1: 실패 테스트 작성** — `backend/tests/crawl/adapters/test_cook82.py`

```python
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest

from app.config import settings
from app.crawl.adapters.base import ListItem
from app.crawl.hashing import author_hash

FIXTURES = Path(__file__).parents[2] / 'fixtures' / 'http' / 'cook82'


class Clock:
    def __init__(self):
        self.now = 0.0
    def __call__(self):
        return self.now
    def sleep(self, d):
        self.now += d


@pytest.fixture(autouse=True)
def salt(tmp_path, monkeypatch):
    path = tmp_path / 'salt'
    path.write_text('b' * 64)
    monkeypatch.setattr(settings, 'author_salt_path', str(path))


def adapter():
    manifest = json.loads((FIXTURES / 'manifest.json').read_text())
    def respond(request):
        q = parse_qs(urlsplit(str(request.url)).query)
        for cap in manifest['requests']:
            cq = parse_qs(urlsplit(cap['url']).query)
            if urlsplit(cap['url']).path == request.url.path and all(q.get(k) == cq.get(k) for k in ('keys', 'page', 'num')):
                return httpx.Response(200, content=(FIXTURES / cap['file']).read_bytes())
        raise AssertionError(f'Unrecorded request: {request.url}')
    from app.crawl.adapters.cook82 import Cook82Adapter
    clock = Clock()
    return Cook82Adapter(httpx.Client(transport=httpx.MockTransport(respond)), clock=clock, sleep=clock.sleep), manifest


def test_list_skips_notices_and_normalizes_urls():
    a, manifest = adapter()
    page = a.list_page(manifest['keyword'], None)
    assert len(page.items) == manifest['list_count']  # recorded non-notice rows (25 in the capture)
    assert all(i.url.startswith('https://www.82cook.com/entiz/read.php?bn=15&num=') for i in page.items)
    assert manifest['notice_num'] not in {i.src_meta['num'] for i in page.items}
    assert all(i.date and len(i.date) == 10 for i in page.items)
    assert page.next_cursor == '2'


def test_empty_search():
    a, manifest = adapter()
    page = a.list_page(manifest['empty_keyword'], None)
    assert page.items == [] and page.next_cursor is None


def test_article_body_comments_and_no_ip():
    a, manifest = adapter()
    url = manifest['article_url']
    doc = a.fetch(ListItem(url, '', '', '2026-10-04', {'num': parse_qs(urlsplit(url).query)['num'][0]}))[0]
    assert doc.title and doc.body
    assert len(doc.comments) == manifest['comment_count']
    assert all(c.depth == 0 and len(c.date) == 10 for c in doc.comments)
    assert doc.comments[0].author_hash == author_hash('cook82', manifest['first_commenter'])
    raw = json.dumps([doc.body, [c.text for c in doc.comments], doc.src_meta], ensure_ascii=False)
    assert 'xxx' not in raw and 'IP' not in raw


def test_changed_markup_is_a_parse_error_not_an_empty_page():
    a, manifest = adapter()
    with pytest.raises(ValueError):
        a.list_page(manifest['changed_keyword'], None)  # list-changed.html: list-1.html에서 결과 행 링크만 지운 사본
```

`test_adapter_wiring.py` 기대 집합에 `'cook82'`, 클래스 목록에 `('cook82', Cook82Adapter)`.

- [ ] **Step 2: 실패 확인**

Run: `backend/.venv/bin/python -m pytest backend/tests/crawl/adapters/test_cook82.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.crawl.adapters.cook82'`

- [ ] **Step 3: 구현** — `backend/app/crawl/adapters/cook82.py`

```python
"""82cook free board search, article bodies and comments; IP fragments are never read."""
import re
from urllib.parse import parse_qs, urlencode, urlsplit

from app.crawl.adapters.base import FetchedDoc, ListItem, ListPage
from app.crawl.adapters.community import CommunityAdapter, html_text, selected, text
from app.crawl.urls import normalize_url

SEARCH_SCOPE = '1'  # T0 Step 5: the value that searches title+body


def _date(value):
    match = re.search(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", value or '')
    if match:
        return f'{int(match[1]):04d}-{int(match[2]):02d}-{int(match[3]):02d}'
    match = re.search(r"'(\d{2})\.(\d{1,2})\.(\d{1,2})", value or '')
    return f'20{match[1]}-{int(match[2]):02d}-{int(match[3]):02d}' if match else None


class Cook82Adapter(CommunityAdapter):
    source = 'cook82'
    origin = 'https://www.82cook.com'

    def list_url(self, kw, cursor):
        page = int(cursor or 1)
        if page < 1:
            raise ValueError('82cook page must be positive')
        return f'{self.origin}/entiz/enti.php?' + urlencode(
            {'bn': 15, 'searchType': 'search', 'search1': SEARCH_SCOPE, 'keys': kw, 'page': page})

    NO_RESULT_TEXT = ('검색된 글이 없', '게시물이 없', '검색결과가 없')  # T0 list-empty.html 문구로 맞춘다

    def parse_list(self, tree, cursor):
        items, seen = [], set()
        rows = [r for r in tree.css('tbody tr') if 'noticeList' not in r.attributes.get('class', '').split()]
        if not any(r.css_first('td.title a[href*="read.php"]') for r in rows):
            body = tree.body.text() if tree.body else ''
            if any(t in body for t in self.NO_RESULT_TEXT):
                return ListPage([], None, 0)
            raise ValueError('82cook search results could not be parsed')  # never a silent empty page
        for row in rows:
            link = row.css_first('td.title a[href*="read.php"]')
            if link is None:
                continue
            url = normalize_url(self.absolute_url('/entiz/' + link.attributes['href'].lstrip('/')), self.source)
            if url in seen:
                continue
            seen.add(url)
            regdate = row.css_first('td.regdate')
            comment = re.search(r'\d+', selected(row, 'td.title em'))
            num = parse_qs(urlsplit(url).query).get('num', [''])[0]
            items.append(ListItem(url, text(link), '', _date((regdate.attributes.get('title') if regdate else '') or text(regdate)),
                                  {'board': '15', 'num': num, 'comment_count': int(comment[0]) if comment else 0,
                                   'author': selected(row, 'td.user_function')}))
        current = int(cursor or 1)
        later = [int(m) for m in re.findall(r'[?&](?:amp;)?page=(\d+)', tree.html or '') if int(m) > current]
        return ListPage(items, str(current + 1) if items and later else None, None)

    def parse_detail(self, tree, item):
        body = tree.css_first('#articleBody')
        if body is None:
            raise ValueError('82cook article body missing')
        comments = []
        for row in tree.css('ul.reples > li.rp'):
            content = row.css_first('p')
            if content is None:
                continue
            stamp = row.css_first('.repleFunc em')
            comments.append(self.comment(html_text(content.html), 0, _date(text(stamp)) or '',
                                         selected(row, 'h5 strong')))
        meta = {k: v for k, v in item.src_meta.items() if k != 'author'}
        meta['comment_count'] = len(comments)
        return FetchedDoc(selected(tree, 'h4.title.bbstitle') or item.title, html_text(body.html), comments,
                          item.date, meta, 'public', item.src_meta.get('author') or None)
```

주의: `CommunityAdapter.comment()`는 날짜를 `date_text()`로 다시 거르므로 `_date()` 결과(`YYYY-MM-DD`)를 넘긴다. 목록 링크는 상대 경로(`read.php?...`)라 `/entiz/`를 붙인다.

`__init__.py` 등록: `"cook82": Cook82Adapter`.

- [ ] **Step 4: 통과 확인**

Run: `backend/.venv/bin/python -m pytest backend/tests/crawl/adapters/test_cook82.py backend/tests/crawl/test_adapter_wiring.py -q`
Expected: PASS

- [ ] **Step 5: Commit** (Controller) — `feat(crawl): 82쿡 채널 — 자유게시판 본문 · 댓글, IP 미저장`

---

### Task T7: Crawl4AI 다리 · Threads 어댑터

**선행 조건:** T0 Step 4 결과가 "10건 이상"이거나, 사용자가 진행 방식을 결정했다.

**Files:**
- Create: `backend/app/crawl/render.py`, `backend/app/crawl/adapters/threads.py`, `backend/tests/fixtures/http/threads/` (`search.html`, `search-empty.html`, `login-wall.html`, `changed-shape.html`(= `search.html`에서 글 JSON 스크립트만 지운 사본), manifest.json)
- Modify: `backend/app/crawl/adapters/__init__.py`, `backend/tests/crawl/test_adapter_wiring.py`
- Test: `backend/tests/crawl/test_render.py`, `backend/tests/crawl/adapters/test_threads.py`

**픽스처 마스킹:** JSON 안 `username` → `user1`…, `profile_pic_url` 등 URL → `https://example.invalid/`, `caption.text`는 앞 80자. 글 코드(`code`)는 그대로.

**Interfaces:**
- Consumes: T2 설정값(`threads_render_timeout_s`) · 정규화 · 기본값
- Produces: `RenderBridge(crawler_factory=None)` — `available() -> bool`(classmethod, 네트워크 · 브라우저 실행 없이 판정), `fetch_html(url: str, *, timeout_s: float) -> str`, `close()`. `ThreadsSearchProvider` 프로토콜 `search(kw: str) -> list[ListItem]`; `WebSearchProvider(bridge)`; `parse_search(html: str) -> list[ListItem]`; `ThreadsAdapter(provider=None)`, `source='threads'`, `list_page(kw, cursor)`(커서 없음), `fetch(item)`(네트워크 없음). `src_meta` 키: `post_code`, `like_count`, `reply_count`, `username_hash`는 두지 않는다(작성자는 `author_raw`로만 전달).

- [ ] **Step 1: 실패 테스트 작성**

`backend/tests/crawl/test_render.py`:

```python
import asyncio

import pytest

from app.crawl.render import RenderBridge


class FakeResult:
    def __init__(self, html, success=True):
        self.html, self.success = html, success


class FakeCrawler:
    def __init__(self):
        self.started = self.closed = False
        self.urls = []
    async def start(self):
        self.started = True
    async def arun(self, url, config=None):
        self.urls.append(url)
        await asyncio.sleep(0)
        return FakeResult(f'<html>{url}</html>')
    async def close(self):
        self.closed = True


def test_fetch_html_runs_async_crawler_from_sync_code():
    crawler = FakeCrawler()
    bridge = RenderBridge(crawler_factory=lambda: crawler)
    try:
        assert bridge.fetch_html('https://example.invalid/a', timeout_s=5) == '<html>https://example.invalid/a</html>'
        assert bridge.fetch_html('https://example.invalid/b', timeout_s=5).endswith('/b</html>')
        assert crawler.started and crawler.urls == ['https://example.invalid/a', 'https://example.invalid/b']
    finally:
        bridge.close()
    assert crawler.closed


def test_failed_render_raises_value_error():
    class Failing(FakeCrawler):
        async def arun(self, url, config=None):
            return FakeResult('', success=False)
    bridge = RenderBridge(crawler_factory=Failing)
    try:
        with pytest.raises(ValueError):
            bridge.fetch_html('https://example.invalid/', timeout_s=5)
    finally:
        bridge.close()


def test_hung_render_times_out_and_bridge_stays_usable():
    class Slow(FakeCrawler):
        async def arun(self, url, config=None):
            if url.endswith('/slow'):
                await asyncio.sleep(5)
            return FakeResult(f'<html>{url}</html>')
    bridge = RenderBridge(crawler_factory=Slow)
    try:
        with pytest.raises(TimeoutError):
            bridge.fetch_html('https://example.invalid/slow', timeout_s=0.1)
        assert bridge.fetch_html('https://example.invalid/ok', timeout_s=5).endswith('/ok</html>')
    finally:
        bridge.close()


def test_available_is_false_without_crawl4ai(monkeypatch):
    import importlib.util
    monkeypatch.setattr(importlib.util, 'find_spec', lambda name: None)
    assert RenderBridge.available() is False
```

`backend/tests/crawl/adapters/test_threads.py`:

```python
from pathlib import Path

import pytest

from app.config import settings
from app.crawl.adapters.base import AdapterBlocked, ListItem

FIXTURES = Path(__file__).parents[2] / 'fixtures' / 'http' / 'threads'


@pytest.fixture(autouse=True)
def salt(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, 'author_salt_path', str(tmp_path / 'salt'))


class Bridge:
    def __init__(self, file):
        self.file, self.urls = file, []
    def fetch_html(self, url, *, timeout_s):
        self.urls.append(url)
        return (FIXTURES / self.file).read_text()
    def close(self):
        pass


def threads(file):
    from app.crawl.adapters.threads import ThreadsAdapter, WebSearchProvider
    bridge = Bridge(file)
    return ThreadsAdapter(provider=WebSearchProvider(bridge)), bridge


def test_search_returns_posts_from_embedded_json():
    adapter, bridge = threads('search.html')
    page = adapter.list_page('에어컨', None)
    assert bridge.urls == ['https://www.threads.com/search?q=%EC%97%90%EC%96%B4%EC%BB%A8&serp_type=default']
    assert len(page.items) >= 10 and page.next_cursor is None
    assert all(i.url.startswith('https://www.threads.com/@') and '/post/' in i.url for i in page.items)
    assert len({i.url for i in page.items}) == len(page.items)
    assert all(i.snippet and i.date and len(i.date) == 10 for i in page.items)
    assert all(set(i.src_meta) == {'post_code', 'like_count', 'reply_count'} for i in page.items)


def test_fetch_turns_list_item_into_document_without_network():
    adapter, bridge = threads('search.html')
    item = adapter.list_page('에어컨', None).items[0]
    calls = len(bridge.urls)
    doc = adapter.fetch(item)[0]
    assert len(bridge.urls) == calls
    assert doc.body == item.snippet and doc.title == '' and doc.access == 'public'
    assert doc.author_raw == item.url.split('/@', 1)[1].split('/post/', 1)[0]


def test_unparsable_page_is_a_parse_error_not_an_empty_page():
    adapter, _ = threads('changed-shape.html')  # 녹화 search.html에서 글 JSON만 지운 사본(로그인 · 결과 없음 문구 없음)
    with pytest.raises(ValueError):
        adapter.list_page('에어컨', None)


def test_login_wall_is_blocked():
    adapter, _ = threads('login-wall.html')
    with pytest.raises(AdapterBlocked):
        adapter.list_page('에어컨', None)


def test_no_results_is_empty_page():
    adapter, _ = threads('search-empty.html')
    page = adapter.list_page('zxqwvplmn', None)
    assert page.items == [] and page.next_cursor is None


def test_cursor_is_rejected():
    adapter, _ = threads('search.html')
    with pytest.raises(ValueError):
        adapter.list_page('에어컨', '2')
```

`test_adapter_wiring.py`: `monkeypatch.setattr('app.crawl.render.RenderBridge.available', classmethod(lambda cls: True))`를 먼저 두고 기대 집합에 `'threads'`를 더한다. 별도 테스트로 `available`이 `False`면 `'threads'`가 빠지는지 확인한다.

- [ ] **Step 2: 실패 확인**

Run: `backend/.venv/bin/python -m pytest backend/tests/crawl/test_render.py backend/tests/crawl/adapters/test_threads.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.crawl.render'`

- [ ] **Step 3: 구현**

`backend/app/crawl/render.py`:

```python
"""One Crawl4AI browser per adapter, driven from synchronous worker threads.

No login, cookies, proxies or stealth options are configured (D-094, G2).
"""
import asyncio
import importlib
import importlib.util
import os
from pathlib import Path
import threading


def _default_crawler():
    crawl4ai = importlib.import_module('crawl4ai')
    return crawl4ai.AsyncWebCrawler(config=crawl4ai.BrowserConfig(headless=True, verbose=False))


class RenderBridge:
    def __init__(self, crawler_factory=None):
        self._factory = crawler_factory or _default_crawler
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()
        self._crawler = None
        self._lock = threading.Lock()

    @classmethod
    def available(cls) -> bool:
        if importlib.util.find_spec('crawl4ai') is None:
            return False
        root = Path(os.environ.get('PLAYWRIGHT_BROWSERS_PATH') or Path.home() / 'Library' / 'Caches' / 'ms-playwright')
        return root.is_dir() and any(p.name.startswith('chromium') for p in root.iterdir())

    def _run(self, coroutine, timeout_s):
        future = asyncio.run_coroutine_threadsafe(coroutine, self._loop)
        try:
            return future.result(timeout_s)
        except TimeoutError:
            future.cancel()  # stop the hung render instead of leaving it on the loop
            raise

    def fetch_html(self, url, *, timeout_s):
        with self._lock:
            if self._crawler is None:
                self._crawler = self._factory()
                self._run(self._crawler.start(), timeout_s)
            result = self._run(self._arun(url), timeout_s)
        if not getattr(result, 'success', False) or not getattr(result, 'html', ''):
            raise ValueError('Render failed')
        return result.html

    async def _arun(self, url):
        config = None
        try:
            crawl4ai = importlib.import_module('crawl4ai')
            config = crawl4ai.CrawlerRunConfig(wait_until='networkidle')
        except Exception:
            pass
        return await self._crawler.arun(url, config=config)

    def close(self):
        try:
            if self._crawler is not None:
                self._run(self._crawler.close(), 30)
        finally:
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._thread.join(timeout=5)
```

주의: `PLAYWRIGHT_BROWSERS_PATH` 기본 경로는 macOS 기준이다. Linux CI가 있으면 `~/.cache/ms-playwright`도 함께 본다.

`backend/app/crawl/adapters/threads.py`:

```python
"""Threads logged-out search; the listing already carries each post's full text."""
from datetime import datetime
import json
import re
from typing import Protocol
from urllib.parse import quote
from zoneinfo import ZoneInfo

from selectolax.parser import HTMLParser

from app.config import settings
from app.crawl.adapters.base import AdapterBlocked, FetchedDoc, ListItem, ListPage
from app.crawl.render import RenderBridge

KST = ZoneInfo('Asia/Seoul')


def _posts(node, out, depth=0):
    if depth > 80:
        return
    if isinstance(node, dict):
        caption = node.get('caption')
        if node.get('code') and isinstance(caption, dict) and isinstance(node.get('user'), dict):
            out.append(node)
            return
        for value in node.values():
            _posts(value, out, depth + 1)
    elif isinstance(node, list):
        for value in node:
            _posts(value, out, depth + 1)


def parse_search(html: str) -> list[ListItem]:
    tree = HTMLParser(html)
    found = []
    for script in tree.css('script[type="application/json"]'):
        try:
            _posts(json.loads(script.text()), found)
        except ValueError:
            continue
    items, seen = [], set()
    for post in found:
        code, user = post['code'], post['user'].get('username') or ''
        text = (post['caption'] or {}).get('text') or ''
        if code in seen or not text or not user:
            continue
        seen.add(code)
        info = post.get('text_post_app_info') or {}
        taken = post.get('taken_at')
        date = datetime.fromtimestamp(taken, KST).date().isoformat() if isinstance(taken, (int, float)) else None
        # The username stays only in the public post URL; it is not copied into metadata.
        items.append(ListItem(f'https://www.threads.com/@{user}/post/{code}', '', text, date,
                              {'post_code': code, 'like_count': post.get('like_count'),
                               'reply_count': info.get('direct_reply_count')}))
    return items


# T0 녹화(search-empty.html)에서 확인한 "결과 없음" 문구로 맞춘다.
_NO_RESULT_TEXT = ('No results', '검색 결과가 없습니다', '결과 없음')


def _no_results(html: str) -> bool:
    return any(t in html for t in _NO_RESULT_TEXT)


def _login_wall(html: str) -> bool:
    lowered = html.lower()
    return '/login' in lowered or 'log in' in lowered


class ThreadsSearchProvider(Protocol):
    def search(self, kw: str) -> list[ListItem]: ...
    def close(self) -> None: ...


class WebSearchProvider:
    def __init__(self, bridge=None):
        self.bridge = bridge or RenderBridge()

    def search(self, kw):
        url = f'https://www.threads.com/search?q={quote(kw)}&serp_type=default'
        html = self.bridge.fetch_html(url, timeout_s=settings.threads_render_timeout_s)
        items = parse_search(html)
        if items:
            return items
        if _no_results(html):
            return []
        if _login_wall(html):
            raise AdapterBlocked('Threads requires login', host='threads.com')
        raise ValueError('Threads search returned no parsable posts')  # never a silent empty page

    def close(self):
        self.bridge.close()


class ThreadsAdapter:
    """Request spacing comes from the worker's channel limiter (1 · 2s); no second limiter here."""
    source = 'threads'

    def __init__(self, provider=None):
        self.provider = provider or WebSearchProvider()

    @classmethod
    def is_available(cls) -> bool:
        return settings.real_channels_enabled and RenderBridge.available()

    def list_page(self, kw, cursor=None):
        if cursor is not None:
            raise ValueError('Threads search has no continuation cursor')
        items = self.provider.search(kw)
        return ListPage(items, None, len(items))

    def fetch(self, item):
        match = re.search(r'/@([^/]+)/post/', item.url)
        return [FetchedDoc('', item.snippet, [], item.date, dict(item.src_meta), 'public', match[1] if match else None)]

    def close(self):
        self.provider.close()
```

주의:
- "결과 없음" 녹화가 글 JSON 없이 빈 상태 문구만 있으면 `parse_search`가 `ValueError`를 낸다. 녹화를 보고, 결과 없음 표시(빈 결과 문구 또는 빈 결과 JSON)를 판정해 빈 목록을 돌려주도록 조건을 맞춘다. 테스트 `test_no_results_is_empty_page`가 기준이다.
- `ListItem.src_meta['author']`는 목록 단계에서 큐(SQLite)에 저장된다. 문서(`Doc`)에는 `author_hash`만 남고, `src_meta`에서는 빠진다(위 `fetch`).
- `RenderBridge()` 생성은 `WebSearchProvider` 생성 시점이다. `REGISTRY` 팩토리가 어댑터를 만드는 건 워커 실행 때뿐이고, `available_sources()`는 `is_available` 클래스 메서드만 쓴다(브라우저를 띄우지 않는다).

`__init__.py` 등록: `"threads": ThreadsAdapter`.

- [ ] **Step 4: 통과 확인**

Run: `backend/.venv/bin/python -m pytest backend/tests/crawl/test_render.py backend/tests/crawl/adapters/test_threads.py backend/tests/crawl/test_adapter_wiring.py -q`
Expected: PASS

- [ ] **Step 5: Commit** (Controller) — `feat(crawl): Threads 채널 — 로그인 없는 검색 화면(Crawl4AI), API 교체 경계`

---

### Task T8: 크롤링 화면

**Files:**
- Modify: `frontend/src/lib/api/crawl.ts`, `frontend/src/lib/logic/crawlConfig.ts`, `frontend/src/lib/logic/finishPartial.ts`, `frontend/src/components/crawl/Settings.tsx`, `frontend/src/components/crawl/Progress.tsx`, `frontend/src/app/pipeline/crawling/page.tsx`
- Test: `frontend/src/lib/logic/crawlConfig.test.ts`(추가), `frontend/src/lib/logic/channelExpansion.test.ts`(새), `backend/tests/crawl/test_channel_defaults_parity.py`(새)

**Interfaces:**
- Consumes: 상태 API `progress.skipped: Record<string, Record<string, number>>`, `report.channels[s].skip_reasons: Record<string, number>`, 설정 `youtube_vlog: {videos_per_keyword, min_duration_s, max_duration_s}`
- Produces: `CrawlConfig.youtube_vlog`; `limits(source)`가 `channels.py` 기본값과 같다; `skipReasonLabel(reason: string): string`; `skipRows(report): {source: string; reason: string; count: number}[]`; `channelDescriptions: Record<string, string>`; `vlogDocsLabel(docs: number, videos: number): string`.

- [ ] **Step 1: 실패 테스트 작성**

`frontend/src/lib/logic/channelExpansion.test.ts`:

```ts
import { describe, expect, it } from 'vitest';
import { limits } from './crawlConfig';
import { skipReasonLabel, skipRows } from './finishPartial';
import { channelDescriptions } from '../../components/crawl/Settings';

describe('channel expansion', () => {
  it('uses backend channel defaults', () => {
    expect(limits('youtube_vlog')).toEqual({ concurrency: 2, min_interval_s: 0, max_per_keyword: 1000 });
    expect(limits('threads')).toEqual({ concurrency: 1, min_interval_s: 2, max_per_keyword: 1000 });
    expect(limits('naver_kin')).toEqual({ concurrency: 1, min_interval_s: 0.5, max_per_keyword: 1000 });
    expect(limits('cook82')).toEqual({ concurrency: 1, min_interval_s: 0.5, max_per_keyword: 1000 });
  });

  it('labels skip reasons in Korean', () => {
    expect(skipReasonLabel('no_ko_captions')).toBe('한국어 자막 없음');
    expect(skipReasonLabel('deleted')).toBe('삭제된 글');
    expect(skipReasonLabel('restricted')).toBe('회원 전용 · 폐쇄 카페(제외)');
    expect(skipReasonLabel('blocked')).toBe('차단으로 여기까지 마침');
    expect(skipReasonLabel('parse_error')).toBe('파싱 오류로 여기까지 마침');
    expect(skipReasonLabel('other')).toBe('other');
  });

  it('flattens report skip reasons into sorted rows', () => {
    const report = { channels: {
      youtube_vlog: { docs: 10, share: 0.5, status: 'done', errors_top: [], skip_reasons: { no_ko_captions: 37 } },
      threads: { docs: 5, share: 0.5, status: 'done', errors_top: [], skip_reasons: { blocked: 9 } },
      clien: { docs: 0, share: 0, status: 'done', errors_top: [], skipped: 4, skip_reason: 'parse_error' },
    } };
    expect(skipRows(report)).toEqual([
      { source: 'youtube_vlog', reason: 'no_ko_captions', count: 37 },
      { source: 'threads', reason: 'blocked', count: 9 },
      { source: 'clien', reason: 'parse_error', count: 4 },
    ]);
  });

  it('describes every new channel', () => {
    for (const source of ['youtube_vlog', 'threads', 'naver_kin', 'cook82']) expect(channelDescriptions[source]).toBeTruthy();
  });
});
```

`backend/tests/crawl/test_channel_defaults_parity.py` (기존 `tests/context/test_labels_parity.py`와 같은 방식 — 백엔드 · 프론트 기본값이 갈라지지 않게):

```python
import re
from pathlib import Path

from app.crawl.channels import _DEFAULTS


def test_ts_channel_defaults_match_python():
    source = (Path(__file__).resolve().parents[3] / 'frontend/src/lib/logic/crawlConfig.ts').read_text()
    block = re.search(r'const DEFAULTS: Record<string, \[number, number\]> = \{(.*?)\};', source, re.S)[1]
    ts = {name: (int(c), float(i)) for name, c, i in re.findall(r'(\w+): \[(\d+), ([\d.]+)\]', block)}
    assert ts == {k: (c, float(i)) for k, (c, i) in _DEFAULTS.items()}
```

`crawlConfig.test.ts`에 추가:

```ts
  it('defaults youtube_vlog settings when none are saved', () => {
    const loaded = deriveCrawlLoad({ data: { crawlConfig: { channels: ['naver_blog'] } } }, initial, null, false);
    expect(loaded.config.youtube_vlog).toEqual({ videos_per_keyword: 20, min_duration_s: 60, max_duration_s: 3600 });
  });
```

- [ ] **Step 2: 실패 확인**

Run: `npm --prefix frontend test -- src/lib/logic/channelExpansion.test.ts src/lib/logic/crawlConfig.test.ts`
Expected: FAIL — `skipReasonLabel` export 없음, `youtube_vlog` undefined

- [ ] **Step 3: 구현**

`frontend/src/lib/api/crawl.ts`:
- `CrawlConfig`에 `youtube_vlog:{videos_per_keyword:number;min_duration_s:number;max_duration_s:number}`.
- `CrawlStatus.progress`에 `skipped?:Record<string,Record<string,number>>`, `report.channels[...]`에 `skip_reasons?:Record<string,number>`.

`frontend/src/lib/logic/crawlConfig.ts`:

```ts
const DEFAULTS: Record<string, [number, number]> = {
  youtube: [2, 0], youtube_vlog: [2, 0], threads: [1, 2],
  naver_blog: [1, 0.5], naver_cafe: [1, 0.5], naver_kin: [1, 0.5],
  clien: [1, 0.5], ppomppu: [1, 0.5], cook82: [1, 0.5],
};
export const limits = (source: string): Limits => {
  const [concurrency, min_interval_s] = DEFAULTS[source] ?? [4, 0];
  return { concurrency, min_interval_s, max_per_keyword: 1000 };
};
export const VLOG_DEFAULTS = { videos_per_keyword: 20, min_duration_s: 60, max_duration_s: 3600 };
```
`deriveCrawlLoad`의 `base`에 `youtube_vlog: { ...VLOG_DEFAULTS, ...(raw?.youtube_vlog ?? {}) },`.

`frontend/src/lib/logic/finishPartial.ts`:

```ts
const SKIP_REASONS: Record<string, string> = {
  no_ko_captions: '한국어 자막 없음', deleted: '삭제된 글', restricted: '회원 전용 · 폐쇄 카페(제외)',
  blocked: '차단으로 여기까지 마침', parse_error: '파싱 오류로 여기까지 마침',
};
export const skipReasonLabel = (reason: string) => SKIP_REASONS[reason] ?? reason;
type ReportChannels = { channels: Record<string, { skip_reasons?: Record<string, number>; skipped?: number; skip_reason?: string | null }> };
export function skipRows(report: ReportChannels) {
  return Object.entries(report.channels).flatMap(([source, c]) => {
    const reasons = c.skip_reasons ?? (c.skipped ? { [c.skip_reason ?? 'blocked']: c.skipped } : {});
    return Object.entries(reasons).filter(([, count]) => count > 0).map(([reason, count]) => ({ source, reason, count }));
  }).sort((a, b) => b.count - a.count);
}
```

`frontend/src/components/crawl/Settings.tsx`:
- `channelNames`에 `youtube_vlog:'유튜브 브이로그', threads:'Threads', naver_kin:'지식iN', cook82:'82쿡'`.
- 설명 표를 export하고 표 셀에서 사용:

```tsx
export const channelDescriptions: Record<string, string> = {
  naver_cafe: '검색 결과 화면 · 본문 (회원 전용 글은 제외)', naver_blog: '검색 결과 화면 · 본문',
  youtube: '영상 검색 · 댓글 스레드',
  youtube_vlog: '"키워드 브이로그" 영상 검색 · 한국어 자막을 화제 단위로 나눠 문서화',
  threads: '검색 화면(로그인 없음) · 글 본문 · 키워드당 약 20건',
  naver_kin: '질문 검색 · 질문 제목과 본문 (답변 제외)', cook82: '자유게시판 검색 · 본문 · 댓글',
  ppomppu: '사이트 검색 · 본문 · 댓글', clien: '사이트 검색 · 본문 · 댓글',
};
const NEW_CHANNELS = new Set(['youtube_vlog', 'threads', 'naver_kin', 'cook82']);
```
  채널 이름 셀에 `{NEW_CHANNELS.has(source) && <Badge tone="info">새 채널</Badge>}`. 사용 불가이고 `source==='threads'`이면 설명 아래 `<p className="ds-t-caption">Crawl4AI 브라우저가 설치돼 있지 않아 사용할 수 없습니다.</p>`.
- 고급 설정에 브이로그 칸(분 단위 입력, 저장은 초):

```tsx
{config.channels.includes('youtube_vlog') && <><h3 className="ds-t-label">유튜브 브이로그</h3><div className="crawl-fields">
  <Input label="키워드당 영상 수" type="number" min={1} value={config.youtube_vlog.videos_per_keyword} onChange={e=>set('youtube_vlog',{...config.youtube_vlog,videos_per_keyword:Number(e.target.value)})}/>
  <Input label="최소 길이(분)" type="number" min={0} value={config.youtube_vlog.min_duration_s/60} onChange={e=>set('youtube_vlog',{...config.youtube_vlog,min_duration_s:Math.round(Number(e.target.value)*60)})}/>
  <Input label="최대 길이(분)" type="number" min={1} value={config.youtube_vlog.max_duration_s/60} onChange={e=>set('youtube_vlog',{...config.youtube_vlog,max_duration_s:Math.round(Number(e.target.value)*60)})}/>
</div><p className="ds-t-caption">1분 미만 쇼츠와 60분이 넘는 영상은 목록에서 뺍니다. 한국어 자막이 없는 영상은 건너뛰고 결과에 건수를 남깁니다.</p></>}
```
- 확정 키워드 카드 안내에 `{config.channels.includes('youtube_vlog') && ' 유튜브 브이로그는 검색어 뒤에 "브이로그"를 붙입니다.'}`.

`frontend/src/app/pipeline/crawling/page.tsx`:
- `valid`에 `&&config.youtube_vlog.videos_per_keyword>=1&&Number.isInteger(config.youtube_vlog.videos_per_keyword)&&config.youtube_vlog.min_duration_s>=0&&config.youtube_vlog.min_duration_s<config.youtube_vlog.max_duration_s`.
- 게이트 화면 상단(InsightCard 위)에 `{config.channels.includes('threads')&&<Banner>Threads는 로그인 없이 볼 수 있는 결과만 모아 키워드당 약 20건입니다. Threads 때문에 "저수율" 배지가 붙은 키워드는 다른 채널 수치를 함께 보고 판단하세요.</Banner>}`.
- 상세 수집 예상 카드 캡션 뒤에 `{config.channels.includes('youtube_vlog')&&<p className="ds-t-caption">유튜브 브이로그는 영상마다 자막 구간을 나누므로 영상 1개가 문서 여러 건이 됩니다.</p>}`.
- 멈춤 배너 문단 끝에 `{pausedChannels.includes('threads')&&<p>Threads가 로그인 화면을 보여 주어 멈췄습니다. 로그인은 시도하지 않습니다. 간격을 늘리고 재개하거나 여기까지로 마치세요.</p>}`.

`frontend/src/components/crawl/Progress.tsx`:
- 채널 상태 표 머리에 `<th>건너뜀</th>`, 행에 `<td>{skippedCell(p?.skipped?.[source])}</td>` — `skippedCell(r)`는 합계와 첫 사유(`11 (자막 없음)`)를, 없으면 `—`.
- 결과 카드의 `report.channels...skippedSummary` 문단들을 표로 교체:

```tsx
<h2 className="ds-t-card">건너뛴 항목</h2>
{skipRows(report).length ? <Table aria-label="채널별 건너뛴 사유"><thead><tr><th>채널</th><th>사유</th><th>건수</th></tr></thead><tbody>
  {skipRows(report).map(r=><tr key={`${r.source}:${r.reason}`}><td>{channelNames[r.source]??r.source}</td><td>{skipReasonLabel(r.reason)}</td><td>{number(r.count)}{r.source==='youtube_vlog'?'개 영상':'건'}</td></tr>)}
</tbody></Table> : <p className="ds-t-caption">건너뛴 항목이 없습니다.</p>}
```
- 채널 분포 `displayValue`: `youtube_vlog`이면 `` `${number(c.docs)} · ${(c.share*100).toFixed(1)}% (영상 ${number(videos)}개 → 구간 ${number(c.docs)})` `` — `videos`는 `report.matrix`에서 `youtube_vlog` 셀의 `urls_done` 합.

- [ ] **Step 4: 통과 확인**

Run: `npm --prefix frontend test && npm --prefix frontend run lint && npm --prefix frontend run build && backend/.venv/bin/python -m pytest backend/tests/crawl/test_channel_defaults_parity.py -q`
Expected: PASS

- [ ] **Step 5: 변경 화면 자체 확인** — 개발 서버에서 크롤링 화면을 열어 목업 4개 화면과 비교(설정 행 · 브이로그 칸 · 게이트 배너 · 결과 표). 스크린샷을 `docs/development/channel-expansion/reports/T8/`에 저장.

- [ ] **Step 6: Commit** (Controller) — `feat(ui): 크롤링 화면 — 새 채널 4개, 브이로그 설정, 건너뜀 사유 표`

---

### Task T9: 통합 확인 · 실제 사이트 수동 확인

**Files:**
- Test: `backend/tests/crawl/test_channel_expansion_flow.py` (새)
- Create: `backend/tests/qa_hooks/channel_expansion_qa.py` (브라우저 QA 전용 가짜 어댑터, `DCX_TEST_ADAPTER_MODULE=channel_expansion_qa` + `PYTHONPATH=backend/tests/qa_hooks`로만 로드), `backend/tests/crawl/test_qa_hook.py`
- Create: `docs/development/channel-expansion/reports/T9-manual.md` (Controller가 수동 확인 결과 기록)

**QA 훅 모듈** — `backend/tests/qa_hooks/channel_expansion_qa.py` (워커 프로세스에서만 로드되어 실제 어댑터를 덮는다. API 프로세스의 사용 가능 판정은 실제 클래스 그대로):

```python
"""Browser-QA-only adapters for the four new channels (worker hook, never imported by the app)."""
import os

from app.crawl.adapters import REGISTRY
from app.crawl.adapters.base import AdapterBlocked, AdapterSkipped, FetchedDoc, ListItem, ListPage

COUNTS = {'youtube_vlog': 6, 'threads': 25, 'naver_kin': 5, 'cook82': 8}


def _adapter(source):
    class QAAdapter:
        def __init__(self):
            self.source = source

        def list_page(self, kw, cursor=None, **options):
            n = 0 if kw == 'qa-empty' else COUNTS[source]
            return ListPage([ListItem(f'https://qa.invalid/{source}/{i}?k={kw}', f'{kw} {source} 글 {i}',
                                      f'{kw} 요약 {i}', '2026-10-01', {'author': f'qa{i}'}) for i in range(n)], None, n)

        def fetch(self, item):
            i = int(item.url.split('?')[0].rsplit('/', 1)[1])
            if source == 'threads' and os.environ.get('QA_THREADS_MODE') == 'blocked':
                raise AdapterBlocked('Threads requires login', host='threads.com')
            if source == 'youtube_vlog' and i % 3 == 2:
                raise AdapterSkipped('no_ko_captions')
            if source == 'naver_kin' and i == 4:
                raise AdapterSkipped('deleted')
            parts = 2 if source == 'youtube_vlog' else 1
            return [FetchedDoc(item.title, f'{item.title} 생활 이야기 구간 {k}', [], item.date,
                               {'segmenter': 'embedding'} if source == 'youtube_vlog' else {}, 'public', 'qa-author',
                               f'{k * 90}-{(k + 1) * 90}' if source == 'youtube_vlog' else '') for k in range(parts)]
    return QAAdapter


for _source in COUNTS:
    REGISTRY[_source] = _adapter(_source)
```

`QA_THREADS_MODE=blocked`는 상세 단계에서 연속 차단을 만들어 `paused_blocked` 화면(멈춤 배너 + Threads 문장)을 재현한다. 실제 Threads 어댑터는 상세 단계에서 네트워크를 쓰지 않으므로, 이 모드는 화면 상태 재현 전용이다.

`backend/tests/crawl/test_qa_hook.py`:

```python
import importlib
import sys
from pathlib import Path

import pytest

from app.crawl.adapters import REGISTRY
from app.crawl.adapters.base import AdapterBlocked, AdapterSkipped, ListItem


@pytest.fixture
def hook(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'qa_hooks'))
    for source in ('youtube_vlog', 'threads', 'naver_kin', 'cook82'):
        monkeypatch.setitem(REGISTRY, source, REGISTRY.get(source))
    sys.modules.pop('channel_expansion_qa', None)
    return importlib.import_module('channel_expansion_qa')


def test_hook_replaces_new_channels_with_deterministic_fakes(hook, monkeypatch):
    vlog = REGISTRY['youtube_vlog']()
    page = vlog.list_page('에어컨', None, videos_per_keyword=20)
    assert len(page.items) == 6
    with pytest.raises(AdapterSkipped):
        vlog.fetch(page.items[2])
    assert REGISTRY['naver_kin']().list_page('qa-empty', None).items == []
    monkeypatch.setenv('QA_THREADS_MODE', 'blocked')
    with pytest.raises(AdapterBlocked):
        REGISTRY['threads']().fetch(ListItem('https://qa.invalid/threads/0?k=x', '', '', None, {}))
```

**Interfaces:**
- Consumes: T1~T7 전부

- [ ] **Step 1: 실패 테스트 작성** — 새 채널 이름으로 등록한 가짜 어댑터 4개가 목록 → 상세 → 문서까지 가고, 그 문서가 전처리 필터 · 분류 특징까지 지나가는지 확인한다.

```python
import json

import numpy as np
import pytest

from app.config import settings
from app.crawl import worker
from app.crawl.adapters import REGISTRY
from app.crawl.adapters.base import AdapterSkipped, FetchedDoc, ListItem, ListPage
from app.crawl.channels import NEW_CHANNELS
from app.crawl.filters import FilterConfig
from app.crawl.writer import read_docs
from app.model.features import INPUT_DIM, build_features
from app.services.preprocessing import filter_documents


def fake(source):
    class Fake:
        def __init__(self):
            self.source = source
        def list_page(self, kw, cursor, **options):
            return ListPage([ListItem(f'https://{source}.example.invalid/{i}', f'{source} 제목 {i}',
                                      f'{source} 요약 {i}', '2026-10-01', {'author': f'u{i}'}) for i in range(3)], None, 3)
        def fetch(self, item):
            if item.url.endswith('/2') and source == 'youtube_vlog':
                raise AdapterSkipped('no_ko_captions')
            return [FetchedDoc(item.title, f'{source} 본문 충분히 긴 내용 {item.url}', [], item.date, {}, 'public', 'author', '')]
    return Fake


@pytest.fixture
def channels(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, 'author_salt_path', str(tmp_path / '.salt'))
    for source in NEW_CHANNELS:
        monkeypatch.setitem(REGISTRY, source, fake(source))


def test_new_channels_flow_to_prep_and_features(tmp_path, channels):
    filters = FilterConfig(date_from=None, date_to=None)
    snapshot = worker.run_list('S', collection=tmp_path, keywords=['에어컨'], sources=list(NEW_CHANNELS), filters=filters)
    worker.run_detail('S', snapshot, collection=tmp_path, filters=filters, backoff_s=0.001)
    docs = list(read_docs(tmp_path / 'docs'))
    assert {d['source'] for d in docs} == set(NEW_CHANNELS)
    assert len(docs) == 3 * len(NEW_CHANNELS) - 1
    assert {d['doc_id'][:3] for d in docs} == {'yv_', 'th_', 'kn_', 'c8_'}
    kept, removed = filter_documents(docs, [], [])
    assert len(kept) == len(docs) and sum(removed.values()) == 0
    assert all(d['desc'] and d['link'] for d in kept)
    features = build_features(kept, np.zeros((len(kept), 1024), dtype=np.float32))
    assert features.shape == (len(kept), INPUT_DIM)
    assert not features[:, 1024:1029].any()  # new channels carry no channel one-hot
    assert json.loads((tmp_path / 'worker_state.json').read_text())['channels']['youtube_vlog']['attempts'] == 2
```

- [ ] **Step 2: 실행** — T1~T7이 끝났다면 바로 PASS할 수 있다. FAIL이면 원인 Task의 구현 담당에게 되돌린다(이 Task에서 제품 코드를 고치지 않는다).

Run: `backend/.venv/bin/python -m pytest backend/tests/crawl/test_channel_expansion_flow.py -q`
Expected: PASS

- [ ] **Step 3: 전체 검증**

Run: `backend/.venv/bin/python -m pytest backend/tests -q && npm --prefix frontend run lint && npm --prefix frontend run build && npm --prefix frontend test`
Expected: PASS

- [ ] **Step 4: 실제 사이트 수동 확인 (Controller, AC-12)** — build worktree에서 임시 세션 하나로 채널마다 키워드 2개(`에어컨 청소`, `제습기`)를 목록 → 게이트 → 상세 → 보고서까지 돌린다. 채널별 목록 수 · 문서 수 · 건너뜀 사유 · 차단 여부, 브이로그 `segmenter` 분포, 소요 시간을 `reports/T9-manual.md`에 기록한다. 네트워크가 막히면 BLOCKED로 기록하고 PASS로 적지 않는다.

- [ ] **Step 5: Commit** (Controller) — `test(crawl): 새 채널 통합 흐름 확인과 수동 확인 기록`

---

## Self-Review

- **Spec coverage:** AC-01(T2 · T4~T8 사용 가능 판정 · 화면) · AC-02(T1 · T2 · T9) · AC-03(T4 목록 길이) · AC-04/05(T3 · T4) · AC-06(T1 · T4 · T8) · AC-07(T7) · AC-08(T5) · AC-09(T6) · AC-10(T9) · AC-11(각 Task + T9 Step 3) · AC-12(T9 Step 4). 설계 6절 화면 변경은 T8, 설계 8절 확인 항목은 T0.
- **Placeholder scan:** 녹화 기반 값(`manifest.json`의 `answer_marker`, `list_count`, `notice_num`, `first_commenter`, `comment_count`)은 T0 녹화에서 Codex가 채운다 — 테스트가 manifest를 읽으므로 코드에 하드코딩하지 않는다. `SEARCH_SCOPE`는 T0 Step 5 결과로 확정.
- **Type consistency:** `AdapterSkipped.reason`, `mark_skipped(url_norm, source, reason)`, `progress()['skipped']`, `skip_reasons`, `channel_defaults()`, `segment(...) -> (list[Segment], str)`, `YoutubeVlogAdapter(embedder_factory=...)`, `RenderBridge.fetch_html(url, *, timeout_s)`, `WebSearchProvider(bridge)`, `skipRows`/`skipReasonLabel`이 Task 사이에서 같은 이름 · 시그니처로 쓰인다.

## 되돌리기

각 Task는 독립 커밋이다. 문제가 생기면 해당 커밋을 `git revert`한다. T2 이후 새 채널이 선택된 세션이 있으면 T2를 되돌리기 전에 그 세션의 `crawlConfig.channels`에서 새 채널을 빼야 한다(스키마 `source` 검증 실패 방지). 레지스트리에서 채널만 빼고 싶으면 `__init__.py`의 한 줄을 지우는 커밋으로 충분하다(기존 수집본 문서는 `Doc.source` 값이 남아 있으므로 T2는 유지).

## Plan Eng Review (2026-10-20)

**Step 0 · 범위:** 파일 약 30개 · 새 모듈 6개로 복잡도 경고 조건에 걸린다. 하지만 채널 4개가 각자 어댑터를 가져야 하는 본질적 복잡도라 줄이지 않았다. Threads(새 브라우저 인프라)는 T0 헤드리스 확인과 T7 독립 커밋으로 위험을 묶었다.

**반영한 수정 (선택지가 갈리지 않는 것)**
1. 지식iN · 82쿡 · Threads 목록이 0건일 때 "결과 없음" 표시가 확인될 때만 빈 페이지, 아니면 파싱 오류(조용한 과소 수집 방지). 테스트 `test_changed_markup_is_a_parse_error_not_an_empty_page`, `test_unparsable_page_is_a_parse_error_not_an_empty_page` 추가.
2. Threads 사용자 이름을 큐 `src_meta`에 넣지 않고 URL에서 꺼낸다.
3. Threads 어댑터 안의 중복 요청 간격 제한기 제거(워커 채널 제한기만 사용).
4. `RenderBridge` 시간 초과 시 코루틴 취소 + 테스트 `test_hung_render_times_out_and_bridge_stays_usable`.
5. 채널 기본값 백엔드 · 프론트 일치 테스트 `test_channel_defaults_parity.py`(기존 라벨 일치 테스트 방식).
6. `YoutubeVlogAdapter.is_available`을 명시적 클래스 메서드로.

**사용자 결정:** 1A — v1-cleanup에서 crawl4ai 삭제 단계를 뺀다(그 세션에 전달). 외부 검토(Codex): 건너뜀.

### NOT in scope
- Threads 공식 API 공급자 — 앱 심사가 선행 조건. 교체 경계만 둔다.
- 말 없는 브이로그의 화면 글자 OCR · 직접 음성 인식 — `no_ko_captions` 건수를 보고 따로 결정.
- 분류 모델 채널 특징 확장 · 재학습 — 입력 차원 변경으로 기존 모델 호환이 깨진다.
- Threads 답글, 지식iN 답변, 82쿡 다른 게시판.
- 운영 설치 스크립트의 `crawl4ai-setup` 반영 — T0에서 유무만 기록.
- 수집 정책(robots.txt · 약관) 문서 — 별도 작업.

### What already exists (재사용)
- `ChannelAdapter` 규약 · 레지스트리 · 워커 대기열 · 게이트 · 보고서 — 그대로 쓴다.
- `CommunityAdapter`(httpx · selectolax · 제한기 · 403/429 차단) — 지식iN · 82쿡이 상속.
- `youtube.py`의 `_blocked` · `_date` · `_metadata` · yt-dlp 호출 — 브이로그가 재사용(`extract_info`로 분리).
- `vectors.embedder.get_embedder`(Voyage/fake) — 자막 분할에 재사용.
- `FetchedDoc.thread_key` · `doc_id(source, url, thread_key)` — 브이로그 구간 식별에 재사용.
- `exclude_restricted` · `finish_partial`의 `skipped` — 건너뜀 집계가 같은 표에 모은다.
- `DCX_TEST_ADAPTER_MODULE` 워커 훅 — 브라우저 QA 가짜 어댑터.
- `test_labels_parity.py` 방식 — 기본값 일치 테스트.

### Failure modes
| 새 경로 | 실제 실패 | 테스트 | 처리 | 사용자에게 |
|---|---|---|---|---|
| 브이로그 자막 수신 | YouTube가 봇 확인 요구 | `test_bot_check_is_blocked` | `AdapterBlocked` → 채널 멈춤 | 멈춤 배너 |
| 브이로그 분할 | Voyage 키 없음 · 장애 | `test_unavailable_embedder_falls_back_to_fixed` | 고정 90초 | 문서 메타 `segmenter='fixed'` (화면 표시 없음, 의도) |
| Threads 렌더링 | 헤드리스에서 로그인 창 | `test_login_wall_is_blocked` | `AdapterBlocked` | 멈춤 배너 + Threads 문장 |
| Threads 렌더링 | Chromium 멈춤 | `test_hung_render_times_out_and_bridge_stays_usable` | 시간 초과 → 키워드 실패 | 채널 표 실패 수 |
| Threads · 지식iN · 82쿡 파싱 | 사이트 구조 변경 | `test_*_parse_error_not_an_empty_page` | 파싱 오류, 30% 넘으면 멈춤 | 멈춤 배너 |
| 건너뜀 기록 | 소유권 잃은 URL에 기록 | `_owns_completion`(기존 테스트) | `LeaseLost` | 이어서 진행 |

조용히 실패하는(테스트 · 처리 · 표시가 모두 없는) 경로: **없음**(수정 1로 제거).

### 병렬화
| 단계 | 모듈 | 선행 |
|---|---|---|
| T1 · T2 | `app/crawl` 핵심, `routers`, `context` | — |
| T3 | `app/crawl/captions` | T2 |
| T4 | `adapters`(youtube 계열) | T1 · T2 · T3 |
| T5 · T6 · T7 | `adapters`, 픽스처 | T1 · T2 |
| T8 | `frontend` | T1 · T2(API 모양) |
| T9 | 테스트 | 전부 |

T4~T7은 모두 `adapters/__init__.py`와 `test_adapter_wiring.py`에 한 줄씩 더하므로 충돌 위험이 있다 → 하네스 기본대로 **순차 실행**(T1 → T2 → T3 → T4 → T5 → T6 → T7 → T8 → T9). T8은 백엔드와 파일이 겹치지 않아 병렬이 가능하지만, 리뷰 · 커밋 순서를 단순하게 두기 위해 순차로 둔다.

### Completion summary
- Step 0: 범위 그대로 수용(본질적 복잡도)
- Architecture: 3건(crawl4ai 충돌 — 사용자 결정, Threads 사용자 이름, 이중 제한기)
- Code quality: 2건(명시적 클래스 메서드, 기본값 이중 정의 → 일치 테스트)
- Test review: 경로 다이어그램 기준 공백 4건 → 테스트 추가(빈 페이지 3, 시간 초과 1)
- Performance: 문제 없음 — 브이로그 영상당 임베딩 1회 묶음 호출, 키워드 42개 × 영상 20개면 약 840회(동시 2, 대략 30분 안팎). Chromium은 목록 단계에서만 1개.
- Failure modes: 치명 공백 0
- 외부 검토: 건너뜀 · 병렬화: 순차

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | `/plan-ceo-review` | Scope & strategy | 0 | — | — |
| Codex Review | `/codex review` | Independent 2nd opinion | 0 | — | — |
| Eng Review | `/plan-eng-review` | Architecture & tests (required) | 1 | CLEAR (PLAN) | 9 issues, 0 critical gaps |
| Design Review | `/plan-design-review` | UI/UX gaps | 0 | — | — |
| DX Review | `/plan-devex-review` | Developer experience gaps | 0 | — | — |

- **UNRESOLVED:** 0
- **VERDICT:** ENG CLEARED — ready to implement
