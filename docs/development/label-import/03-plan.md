# 라벨 결과 가져오기 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 서버에서 `dcxctl import-labels <zip|csv>` 한 번으로 외부 라벨링 결과(dcx-label 결과 CSV)를 새 DCX 프로젝트로 가져와 0~5단계를 끝내고, 웹에서 6단계(세그먼트)부터 진행하게 한다.

**Architecture:** 새 패키지 `backend/app/importer/`가 CSV를 스트리밍으로 읽고 검증한 뒤, 기존 저장 형식(세션 v2, 끝난 수집본 c1, 전처리 워커, `labels.sqlite.final`, 모델 없는 내보내기)을 그대로 만든다. 수집·전처리·내보내기 코드는 재사용하고, 4단계에서만 `labelerMode='imported'`일 때 가져온 라벨을 보호하는 분기를 넣는다.

**Tech Stack:** Python 3.12, FastAPI 백엔드 내부 모듈, sqlite3, pydantic, pytest. Bash(`ops/macmini/dcxctl`).

설계: [02-design.md](02-design.md) (non-ui, 2026-11-03 승인). 기획: [01-brainstorm.md](01-brainstorm.md).

## Global Constraints

- 웹 화면(`frontend/`)은 바꾸지 않는다.
- 0단계 값은 모두 `.`. 고르는 칸은 `projectType.choice="new"`, `taskMode="explore"`, `channels=["naver_cafe"]`, `productCategory={"l1":".","source":"user"}`.
- 최종 라벨 출처 값은 `imported`, route는 `accepted`, `confidence`는 `NULL`.
- 세션 `labeling` = `{"started": true, "status": "done", "mode": "imported", "labelerMode": "imported"}`.
- `sid` 기본값 = `imp-` + sha256(결과 CSV 바이트)[:12].
- `labelerMode != 'imported'`인 기존 세션의 동작은 바뀌지 않는다(기존 테스트 전부 통과).
- 테스트는 네트워크·실제 임베딩·모델 호출을 하지 않는다(`embed_backend='fake'`, `runner.start` 대체).
- 검증 명령(하네스 고정): `backend/.venv/bin/python -m pytest backend/tests -q`, `npm --prefix frontend run lint`, `npm --prefix frontend run build`, `npm --prefix frontend test`.
- 사용자에게 보이는 문구는 한국어. 기존 메시지 형식(`store.StoreError`)을 따른다.

## File Structure

| 파일 | 역할 | 태스크 |
|---|---|---|
| `backend/app/importer/__init__.py` | 패키지 표시(빈 파일) | T1 |
| `backend/app/importer/read.py` | 입력 열기(zip/csv), 컬럼·행 검증, 행 → Doc·라벨 매핑, sha256 | T1 |
| `backend/tests/importer/__init__.py`, `conftest.py` | 작은 CSV/zip 만드는 픽스처 | T1 |
| `backend/tests/importer/test_read.py` | T1 테스트 | T1 |
| `backend/app/label/schema.py` | `Label.source`에 `imported` | T2 |
| `backend/app/label/route.py` | imported 모드에서 final 재생성·감사 라운드 건너뜀, 버전 변경 삭제 대상에서 제외 | T2 |
| `backend/app/context/stale.py` | `_judges_complete`: imported는 실행 기록 없이 완료 | T2 |
| `backend/app/routers/labeling_v2.py` | imported 모드에서 start/mode/control 거절 | T2 |
| `backend/app/label/overview.py` | imported 모드에서 Jev·GPT 정확도 비움 | T2 |
| `backend/tests/label/test_imported_mode.py` | T2 테스트 | T2 |
| `backend/app/prep/launch.py` | 3단계 시작 공통 함수 `start_prep` | T3 |
| `backend/app/routers/prep.py` | `run`이 `start_prep` 호출 | T3 |
| `backend/tests/prep/test_launch.py` | T3 테스트 | T3 |
| `backend/app/importer/steps.py` | 단계 A~E와 `run_import` | T4 |
| `backend/tests/importer/test_steps.py` | T4 흐름·이어하기 테스트 | T4 |
| `backend/app/importer/__main__.py` | 명령 인자, 출력, 종료 코드 | T5 |
| `ops/macmini/dcxctl` | `import-labels` 하위 명령 | T5 |
| `backend/tests/importer/test_main.py`, `backend/tests/ops/test_dcxctl.py` | T5 테스트 | T5 |

의존: T1, T2, T3은 서로 독립. T4는 T1·T2·T3 이후. T5는 T4 이후.

## 실행 환경 준비 (worktree를 만든 직후, 컨트롤러)

하네스는 Python 의존성을 설치하지 않는다. 이 체크아웃의 `backend/venv`에는 `torch`가 없어 전체 테스트를 모으지 못한다(2026-11-03 확인). 사용자 결정(계획 검토, 2026-11-03): worktree에 CI와 같은 구성의 새 가상환경을 만든다.

```bash
cd <worktree> && python3.12 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt -r backend/requirements-dev.txt -c backend/constraints.txt
DCX_BASH=/bin/bash backend/.venv/bin/python -m pytest backend/tests -q -p no:cacheprovider   # 기준선: 구현 전 통과 확인
```

- `backend/.venv/`는 이미 `.gitignore`(76행)에 있다. 추적되지 않는 파일이 생기지 않는다.
- 기준선이 실패하면 구현을 시작하지 않고 실패 목록을 사용자에게 보고한다(이 기능과 무관한 기존 실패를 PASS로 덮지 않는다).
- 모든 태스크의 `Run:` 명령은 worktree의 `backend/.venv/bin/python`을 쓴다.

---

### Task T1: 입력 읽기·검증·매핑 (`app/importer/read.py`)

**Files:**
- Create: `backend/app/importer/__init__.py`(빈 파일), `backend/app/importer/read.py`
- Create: `backend/tests/importer/__init__.py`(빈 파일), `backend/tests/importer/conftest.py`, `backend/tests/importer/test_read.py`

**Interfaces:**
- Consumes: `app.crawl.urls.normalize_url(url, source) -> str`, `app.crawl.urls.doc_id(source, url_norm) -> str`, `app.crawl.hashing.author_hash(source, raw_id) -> str`, `app.label.rule.grade(tags: dict) -> str`, `app.label.rule.SEM`, `app.label.rule.RULE_VERSION`, `app.label.questions.QVER`, `app.label.schema.Tags`.
- Produces:
  - `class ImportError_(Exception)`: 사용자에게 보여 줄 한국어 메시지(`str(exc)`).
  - `@dataclass(frozen=True) class Source: name: str; sha256: str; open: Callable[[], ContextManager[TextIO]]`
  - `open_source(path: str | Path) -> Source`
  - `@dataclass class Scan: total: int; done: int; skipped: Counter[str]; keywords: list[str]`
  - `scan(source: Source) -> Scan` — 사전 검증 패스. 오류는 `ImportError_`.
  - `iter_records(source: Source, crawled_at: str) -> Iterator[Record]`, `@dataclass(frozen=True) class Record: doc: dict; label: dict | None`(`doc`은 `crawl.schema.Doc` 모양 dict, `label`은 done이면 final 행 값 dict, 아니면 None; site가 다르거나 status가 done이 아닌 행은 내지 않는다)
  - `REQUIRED: tuple[str, ...]`

- [ ] **Step 1: 테스트 픽스처 작성** — `backend/tests/importer/conftest.py`

```python
import csv
import io
import zipfile

import pytest

from app.config import settings
from app.crawl.urls import doc_id, normalize_url

COLUMNS = ['date', 'keyword', 'title', 'contents', 'comments', 'answers', 'site', 'url',
           'author_nickname', 'comment_nicknames', 'doc_id', 'status', 'anchor', 'sense', 'feel',
           'think', 'act', 'relate', 'outcome', 'situation', 'evidence_level', 'reason_code',
           'signal', 'error', 'questions_version', 'rule_version']


def row(n, **over):
    url = f'https://cafe.naver.com/club{n % 3}/{1000 + n}'
    base = dict(date='2026.03.30. 22:02', keyword=f'건강 키워드{n % 2}', title=f'제목 {n}',
                contents=f'충분히 긴 본문입니다 번호 {n}', comments="['댓글 하나', '댓글 둘']", answers='[]',
                site='네이버카페', url=url, author_nickname=f'닉{n}', comment_nicknames='a | b',
                doc_id=doc_id('naver_cafe', normalize_url(url, 'naver_cafe')), status='done',
                anchor='1', sense='1', feel='1', think='1', act='1', relate='1', outcome='1', situation='1',
                evidence_level='core', reason_code='', signal='pain', error='',
                questions_version='q1', rule_version='r1')
    base.update(over)
    return base


def write_csv(path, rows, columns=COLUMNS):
    with path.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_zip(path, members):
    with zipfile.ZipFile(path, 'w') as archive:
        for name, data in members.items():
            archive.writestr(name, data)
    return path


@pytest.fixture
def salt(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, 'author_salt_path', str(tmp_path / '.author_salt'))
```

- [ ] **Step 2: 실패하는 테스트 작성** — `backend/tests/importer/test_read.py`

```python
import pytest

from app.importer import read
from tests.importer.conftest import COLUMNS, row, write_csv, write_zip


def test_scan_counts_done_skipped_and_other_site(tmp_path, salt):
    rows = [row(1), row(2), row(3, status='skipped', error='short_body', evidence_level=''),
            row(4, site='네이버지식인')]
    source = read.open_source(write_csv(tmp_path / 'r.csv', rows))
    result = read.scan(source)
    assert (result.total, result.done) == (4, 2)
    assert result.skipped == {'skipped': 1, 'unknown_site': 1}
    assert result.keywords == ['건강 키워드1', '건강 키워드0']


def test_missing_columns_named(tmp_path):
    path = write_csv(tmp_path / 'r.csv', [row(1)], [c for c in COLUMNS if c not in ('signal', 'url')])
    with pytest.raises(read.ImportError_, match=r'r\.csv.*signal.*url|r\.csv.*url.*signal'):
        read.scan(read.open_source(path))


@pytest.mark.parametrize('over, message', [
    (dict(questions_version='q2'), '판정 버전'),
    (dict(doc_id='nc_0000000000000000'), 'doc_id'),
    (dict(evidence_level='non'), '등급'),
    (dict(anchor='2'), '태그'),
    (dict(signal='weird'), 'signal'),
])
def test_scan_rejects_invalid_rows(tmp_path, over, message):
    source = read.open_source(write_csv(tmp_path / 'r.csv', [row(1), row(2, **over)]))
    with pytest.raises(read.ImportError_, match=message):
        read.scan(source)


def test_duplicate_doc_id_rejected(tmp_path):
    source = read.open_source(write_csv(tmp_path / 'r.csv', [row(1), row(1)]))
    with pytest.raises(read.ImportError_, match='중복'):
        read.scan(source)


def test_zip_picks_result_csv_and_ignores_probs(tmp_path):
    csv_path = write_csv(tmp_path / 'r.csv', [row(1)])
    data = csv_path.read_bytes()
    archive = write_zip(tmp_path / 'a.zip', {'폴더/': b'', '폴더/x_full.csv': data, '폴더/x_full_probs.csv': b'doc_id\n'})
    source = read.open_source(archive)
    assert source.name == 'x_full.csv'
    assert source.sha256 == read.open_source(csv_path).sha256
    assert read.scan(source).done == 1


def test_zip_with_two_result_csvs_rejected(tmp_path):
    archive = write_zip(tmp_path / 'a.zip', {'a.csv': b'x', 'b.csv': b'y'})
    with pytest.raises(read.ImportError_, match='결과 CSV'):
        read.open_source(archive)


def test_records_map_to_doc_and_label(tmp_path, salt):
    rows = [row(1), row(2, comments='깨진 [문자열', anchor='0', sense='0', feel='0', think='0', act='0',
                       relate='0', outcome='0', situation='0', evidence_level='non', reason_code='ad', signal=''),
            row(3, status='skipped', evidence_level='')]
    records = list(read.iter_records(read.open_source(write_csv(tmp_path / 'r.csv', rows)), '2026-11-03T00:00:00+00:00'))
    assert len(records) == 2
    doc, label = records[0].doc, records[0].label
    assert doc['source'] == 'naver_cafe' and doc['kw'] == '건강 키워드1' and doc['kw_hits'] == ['건강 키워드1']
    assert doc['date'] == '2026-03-30' and doc['fetch_level'] == 'full' and doc['access'] == 'public'
    assert doc['src_meta'] == {'cafe': 'club1', 'cafe_id': 'club1', 'imported': True}
    assert [c['text'] for c in doc['comments']] == ['댓글 하나', '댓글 둘']
    assert doc['comments'][0] == {'text': '댓글 하나', 'depth': 0, 'date': '', 'author_hash': ''}
    assert len(doc['author_hash']) == 16
    assert label['level'] == 'core' and label['signal'] == 'pain' and label['reason_code'] is None
    assert label['tags']['sem'] == {k: 1 for k in ('sense', 'feel', 'think', 'act', 'relate', 'outcome')}
    non = records[1]
    assert [c['text'] for c in non.doc['comments']] == ['깨진 [문자열']
    assert non.label['level'] == 'non' and non.label['signal'] is None and non.label['reason_code'] == 'ad'
    from app.crawl.schema import Doc
    Doc.model_validate(doc)


def test_records_do_not_keep_nicknames_or_answers(tmp_path, salt):
    rows = [row(1, author_nickname='비밀닉네임', comment_nicknames='댓글닉A | 댓글닉B', answers="['지식인 답변']")]
    record = next(read.iter_records(read.open_source(write_csv(tmp_path / 'r.csv', rows)), 'now'))
    text = json.dumps(record.doc, ensure_ascii=False)
    for secret in ('비밀닉네임', '댓글닉A', '지식인 답변'):
        assert secret not in text
    assert 'answers' not in record.doc
    assert re.fullmatch(r'[0-9a-f]{16}', record.doc['author_hash'])


def test_blank_keyword_becomes_dot(tmp_path, salt):
    source = read.open_source(write_csv(tmp_path / 'r.csv', [row(1, keyword='  ')]))
    assert read.scan(source).keywords == ['.']
    assert next(read.iter_records(source, 'now')).doc['kw'] == '.'
```

테스트 파일 맨 위 import에 `import json`, `import re`를 더한다.

- [ ] **Step 3: 실패 확인**

Run: `cd backend && .venv/bin/python -m pytest tests/importer/test_read.py -q`
Expected: FAIL (`ModuleNotFoundError: app.importer`)

- [ ] **Step 4: 구현** — `backend/app/importer/read.py`

```python
"""External labeled-CSV intake: open, validate, and map rows to DCX shapes."""
import ast
import csv
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import io
from pathlib import Path
import re
from typing import Callable, Iterator
from urllib.parse import urlsplit
import zipfile

from app.crawl.hashing import author_hash
from app.crawl.urls import doc_id as make_doc_id, normalize_url
from app.label import rule
from app.label.questions import QVER
from app.label.schema import ReasonCode, Signal, Tags

csv.field_size_limit(2 ** 31 - 1)
SITE = '네이버카페'
SOURCE = 'naver_cafe'
REQUIRED = ('date', 'keyword', 'title', 'contents', 'comments', 'answers', 'site', 'url',
            'author_nickname', 'comment_nicknames', 'doc_id', 'status', 'anchor', *rule.SEM,
            'situation', 'evidence_level', 'reason_code', 'signal', 'questions_version', 'rule_version')
REASONS = set(ReasonCode.__args__)
SIGNALS = set(Signal.__args__)
_EXAMPLES = 5


class ImportError_(Exception):
    """User-facing import failure; nothing has been written."""


@dataclass(frozen=True)
class Source:
    name: str
    sha256: str
    open: Callable


@dataclass
class Scan:
    total: int
    done: int
    skipped: Counter
    keywords: list


@dataclass(frozen=True)
class Record:
    doc: dict
    label: dict | None


def _digest(opener):
    digest = hashlib.sha256()
    with opener() as raw:
        for chunk in iter(lambda: raw.read(1 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def open_source(path) -> Source:
    path = Path(path).expanduser().resolve()
    if not path.is_file():
        raise ImportError_(f'파일이 없습니다: {path}')
    if path.suffix.lower() == '.zip':
        with zipfile.ZipFile(path) as archive:
            members = [i.filename for i in archive.infolist() if not i.is_dir()
                       and i.filename.lower().endswith('.csv') and not i.filename.lower().endswith('_probs.csv')]
        if len(members) != 1:
            raise ImportError_(f'{path.name}: 결과 CSV가 정확히 하나여야 합니다(찾은 수 {len(members)})')
        member = members[0]

        @contextmanager
        def raw():
            with zipfile.ZipFile(path) as archive, archive.open(member) as stream:
                yield stream
        name = Path(member).name
    else:
        @contextmanager
        def raw():
            with path.open('rb') as stream:
                yield stream
        name = path.name
    return Source(name=name, sha256=_digest(raw), open=raw)


@contextmanager
def _rows(source):
    with source.open() as raw:
        reader = csv.DictReader(io.TextIOWrapper(raw, encoding='utf-8-sig', newline=''))
        missing = [c for c in REQUIRED if c not in (reader.fieldnames or [])]
        if missing:
            raise ImportError_(f'{source.name}: 필수 컬럼이 없습니다: {", ".join(missing)}')
        yield reader


def _tags(row):
    values = {name: row[name].strip() for name in ('anchor', *rule.SEM, 'situation')}
    if any(v not in ('0', '1') for v in values.values()):
        return None
    return {k: int(v) for k, v in values.items()}


def _problems(row):
    """Return the first validation problem of a done row, or None."""
    if row['questions_version'] != QVER or row['rule_version'] != rule.RULE_VERSION:
        return f'판정 버전이 DCX({QVER}/{rule.RULE_VERSION})와 다릅니다: {row["questions_version"]}/{row["rule_version"]}'
    if make_doc_id(SOURCE, normalize_url(row['url'], SOURCE)) != row['doc_id']:
        return 'doc_id가 DCX 규칙(URL 해시)과 다릅니다'
    tags = _tags(row)
    if tags is None:
        return '태그 값이 0/1이 아닙니다'
    if rule.grade(tags) != row['evidence_level']:
        return f'등급이 DCX 규칙과 다릅니다: {row["evidence_level"]} → {rule.grade(tags)}'
    if row['reason_code'] and row['reason_code'] not in REASONS:
        return f'reason_code 값이 허용 범위 밖입니다: {row["reason_code"]}'
    if row['signal'] and row['signal'] not in SIGNALS:
        return f'signal 값이 허용 범위 밖입니다: {row["signal"]}'
    return None


def scan(source: Source) -> Scan:
    seen, problems = set(), []
    total = done = 0
    skipped, keywords = Counter(), {}
    with _rows(source) as reader:
        for line, row in enumerate(reader, start=2):
            total += 1
            if row['doc_id'] in seen:
                problems.append(f'{line}행 {row["doc_id"]}: 중복된 doc_id')
            seen.add(row['doc_id'])
            if row['site'] != SITE:
                skipped['unknown_site'] += 1
                continue
            if row['status'] != 'done':
                skipped[row['status'] or 'blank'] += 1
                continue
            problem = _problems(row)
            if problem:
                problems.append(f'{line}행 {row["doc_id"]}: {problem}')
            done += 1
            keywords.setdefault(_keyword(row), None)
            if len(problems) >= _EXAMPLES:
                break
    if problems:
        raise ImportError_(f'{source.name}: 가져올 수 없는 행이 있습니다\n' + '\n'.join(problems))
    return Scan(total=total, done=done, skipped=skipped, keywords=list(keywords))


def _comments(value):
    text = (value or '').strip()
    if not text or text == '[]':
        return []
    try:
        parsed = ast.literal_eval(text)
    except (ValueError, SyntaxError):
        parsed = [text]
    if not isinstance(parsed, list) or not all(isinstance(i, str) for i in parsed):
        parsed = [text]
    return [dict(text=item, depth=0, date='', author_hash='') for item in parsed if item.strip()]


def _date(value):
    match = re.match(r'\s*(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})', value or '')
    return f'{int(match[1]):04d}-{int(match[2]):02d}-{int(match[3]):02d}' if match else ''


def _keyword(row):
    # Crawl queue rows require a non-empty keyword.
    return (row['keyword'] or '').strip() or '.'


def _doc(row, crawled_at):
    url = normalize_url(row['url'], SOURCE)
    cafe = urlsplit(url).path.strip('/').split('/')[0]
    nickname = (row['author_nickname'] or '').strip()
    kw = _keyword(row)
    return dict(doc_id=row['doc_id'], source=SOURCE, src_meta=dict(cafe=cafe, cafe_id=cafe, imported=True),
                kw=kw, kw_axis='', kw_sub='', kw_hits=[kw],
                title=row['title'] or '', body=row['contents'] or '', comments=_comments(row['comments']),
                date=_date(row['date']), url=url, fetch_level='full', access='public',
                snippet=(row['contents'] or '')[:200],
                author_hash=author_hash(SOURCE, nickname) if nickname else '', crawled_at=crawled_at)


def _label(row):
    tags = _tags(row)
    level = rule.grade(tags)
    non = level == 'non'
    model = Tags(anchor=bool(tags['anchor']), situation=bool(tags['situation']),
                 sem={k: tags[k] for k in rule.SEM},
                 reason_code=(row['reason_code'] or None) if non else None,
                 signal=None if non else (row['signal'] or None))
    return dict(level=level, tags=model.model_dump(), tags_json=model.model_dump_json(),
                reason_code=model.reason_code, signal=model.signal)


def iter_records(source: Source, crawled_at: str) -> Iterator[Record]:
    with _rows(source) as reader:
        for row in reader:
            if row['site'] != SITE or row['status'] != 'done':
                continue
            yield Record(doc=_doc(row, crawled_at), label=_label(row))
```

`Record.label`은 위 설계상 done 행만 내므로 항상 dict다(인터페이스 타입은 미래 확장을 위해 `dict | None`로 둔다).

- [ ] **Step 5: 통과 확인**

Run: `cd backend && .venv/bin/python -m pytest tests/importer/test_read.py -q`
Expected: PASS

- [ ] **Step 6: 커밋** — `feat(importer): 외부 라벨 CSV 읽기·검증·매핑`

---

### Task T2: 가져온 라벨 보호 (`labelerMode='imported'`)

**Files:**
- Modify: `backend/app/label/schema.py` (`Label.source`)
- Modify: `backend/app/label/route.py` (`rebuild_final` 버전 변경 삭제·첫 동기화 검사, `rebuild_queue`, `sync`)
- Modify: `backend/app/context/stale.py` (`_judges_complete`)
- Modify: `backend/app/routers/labeling_v2.py` (`mode`, `start`, `control`)
- Modify: `backend/app/label/overview.py` (`overview`)
- Create: `backend/tests/label/test_imported_mode.py`

**Interfaces:**
- Consumes: 세션 `labeling.labelerMode == 'imported'`(T4가 씀), `final.source == 'imported'`.
- Produces: `app.label.route.IMPORTED = 'imported'`. `IMPORTED_MESSAGE = '가져온 라벨입니다. 새 버전에서 다시 하세요.'`(같은 모듈). T4가 이 상수를 쓴다.

- [ ] **Step 1: 실패하는 테스트 작성** — `backend/tests/label/test_imported_mode.py`

```python
import json

from app.context import store
from app.context.stale import _judges_complete
from app.label import route, rule
from app.label.overview import labels_for, overview
from app.label.questions import QVER


def _imported_session(sid='imp-test'):
    store.update_session(sid, {'schemaVersion': 2})
    data = store.load_session(sid)
    data['labeling'] = {'started': True, 'status': 'done', 'mode': 'imported', 'labelerMode': 'imported'}
    data['prep'] = {'status': 'done', 'derivedRef': None}
    store.write_json(store.session_dir(sid) / 'session.json', data)
    labels = labels_for(sid, store.load_session(sid))
    route.schema(labels)  # opens its own transaction; never call inside labels._db()
    tags = dict(anchor=True, situation=True, sem={k: 1 for k in rule.SEM}, reason_code=None, signal='pain')
    with labels._db() as db:
        for i in range(3):
            db.execute('INSERT INTO final VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
                       (f'nc_{i:016x}', 'core', None, 'imported', 'accepted', json.dumps(tags), None, 'pain',
                        'r0' if i == 0 else rule.RULE_VERSION, QVER, '{}', '[]', 0))
    return sid, labels


def test_rebuild_and_sync_keep_imported_rows(data_dir):
    sid, labels = _imported_session()
    route.rebuild_queue(labels, None, None, mode='imported')
    route.sync(labels, None, None, mode='imported')
    with labels._db() as db:
        assert db.execute("SELECT count(*) FROM final WHERE source='imported'").fetchone()[0] == 3
        assert db.execute('SELECT count(*) FROM audit_set').fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM queue WHERE status='open'").fetchone()[0] == 0


def test_version_change_does_not_delete_imported_rows(data_dir, tmp_path):
    from app.label.votes import VoteCache
    sid, labels = _imported_session()
    gpt = VoteCache(tmp_path / 'gpt')
    route.rebuild_final(labels, None, gpt, mode='gpt_only')
    with labels._db() as db:
        assert db.execute("SELECT count(*) FROM final WHERE source='imported'").fetchone()[0] == 3


def test_judges_complete_without_runs():
    import sqlite3
    db = sqlite3.connect(':memory:')
    db.execute('CREATE TABLE runs (labeler TEXT, state TEXT, version TEXT, kind TEXT, started_at REAL)')
    assert _judges_complete(db, 'v1', mode='imported') is True
    assert _judges_complete(db, 'v1', mode='gpt_only') is False


def test_overview_reports_imported_totals(data_dir):
    sid, _ = _imported_session()
    view = overview(sid, sync=True)
    assert view['labelerAccuracy']['jev'] is None and view['labelerAccuracy']['gpt'] is None
    assert view['levelDistribution']['core'] == 3


def test_label_api_refuses_judging(client, data_dir):
    sid, _ = _imported_session()
    for method, path, body in (('post', f'/label/{sid}/start', None),
                               ('post', f'/label/{sid}/mode', {'mode': 'llm'}),
                               ('post', f'/label/{sid}/judge/gpt/resume', None)):
        response = getattr(client, method)(path, json=body) if body else getattr(client, method)(path)
        assert response.status_code == 409, (path, response.text)
        assert '가져온 라벨' in response.text
```

`levelDistribution`·`labelerAccuracy` 키 이름은 `label/overview.overview`의 현재 반환값을 따른다. 구현 전에 반환 dict를 읽고, 이름이 다르면 테스트를 실제 키에 맞춘다(의미는 유지: 정확도 None, core 개수 3).

- [ ] **Step 2: 실패 확인**

Run: `cd backend && .venv/bin/python -m pytest tests/label/test_imported_mode.py -q`
Expected: FAIL (`Label.source`·라우터·`_judges_complete`가 imported를 모름)

- [ ] **Step 3: 구현**

`label/schema.py`:
```python
    source: Literal['agreed', 'human', 'model', 'gpt_only', 'imported']
```

`label/route.py` 상단에 추가:
```python
IMPORTED = 'imported'
IMPORTED_MESSAGE = '가져온 라벨입니다. 새 버전에서 다시 하세요.'
```
`rebuild_final` 안의 두 곳을 바꾼다:
```python
            changed = db.execute("""SELECT 1 FROM final WHERE source NOT IN ('human','model','imported')
                AND (rule_version!=? OR questions_version!=?) LIMIT 1""",
...
        if changed:
            db.execute("DELETE FROM final WHERE source NOT IN ('human','model','imported')")
```
`rebuild_queue`에서 final 재생성 조건에 모드를 넣는다:
```python
    if mode != IMPORTED and not model_mode and gpt_cache is not None and (mode == 'gpt_only' or jev_cache is not None):
        rebuild_final(store, jev_cache, gpt_cache, mode=mode)
```
`sync`:
```python
def sync(store, jev_cache=None, gpt_cache=None, mode='cross'):
    rebuild_queue(store, jev_cache, gpt_cache, mode=mode)
    if mode == IMPORTED:
        return
    ...(기존 그대로)
```

`context/stale.py`의 `_judges_complete` 첫 줄:
```python
    if mode == 'imported':
        return True
```

`routers/labeling_v2.py`: `mode`, `start`, `control` 각각 `session(...)`을 읽은 직후에 넣는다.
```python
from app.label.route import IMPORTED, IMPORTED_MESSAGE
...
        if labeler_mode(data) == IMPORTED:
            raise store.StoreError(IMPORTED_MESSAGE, 409)
```

`label/overview.py`의 `overview`에서 `if mode == 'gpt_only': accuracy['jev'] = None` 바로 아래에:
```python
    if mode == 'imported':
        accuracy['jev'] = accuracy['gpt'] = None
```
그 밖에 `overview`가 Jev·GPT 표 캐시(`caches_for`)에서 진행 수치를 읽는 부분이 imported 세션(`derivedRef`가 있어도 표가 비어 있음)에서 예외를 내면, 모드가 imported일 때 그 부분을 0/None으로 채운다. 테스트 `test_overview_reports_imported_totals`가 통과하는 최소 변경만 한다.

- [ ] **Step 4: 통과·회귀 확인**

Run: `cd backend && .venv/bin/python -m pytest tests/label tests/context tests/test_integration_stage3_5.py -q`
Expected: PASS (새 테스트와 기존 라벨·세션·통합 테스트 모두)

- [ ] **Step 5: 커밋** — `feat(label): 가져온 라벨(imported) 보호`

---

### Task T3: 3단계 시작 공통 함수 (`app/prep/launch.py`)

**Files:**
- Create: `backend/app/prep/launch.py`
- Modify: `backend/app/routers/prep.py` (`run`)
- Create: `backend/tests/prep/test_launch.py`

**Interfaces:**
- Consumes: `routers/prep.py`의 `_session`, `_root`, `_save`, `_view` 동작(그대로 옮김).
- Produces: `start_prep(sid: str, version: str | None = None) -> dict` — 기존 `POST /prep/{sid}/run` 응답과 같은 dict(`status, runId, progress, reused` 또는 재사용 시 `_view` + `reused: True`). 세션 잠금을 스스로 잡는다.

- [ ] **Step 1: 실패하는 테스트 작성** — `backend/tests/prep/test_launch.py`

```python
from contextlib import closing

from app.config import settings
from app.context import store
from app.crawl.queue import CrawlQueue
from app.work import runner


def _ready(data_dir, sid='launch'):
    root = data_dir / 'crawl' / sid / 'collections/c1'
    store.write_json(root / 'manifest.json', {'parent': None})
    with closing(CrawlQueue(root / 'queue.sqlite')) as queue:
        queue.finish_run(queue.register_run('detail'), 'done')
    store.update_session(sid, {'schemaVersion': 2, 'collectionId': 'c1'})
    return sid


def test_start_prep_launches_worker_and_saves_run(data_dir, monkeypatch):
    monkeypatch.setattr(settings, 'embed_backend', 'fake')
    launched = []
    monkeypatch.setattr(runner, 'start', lambda sid, v, kind, args: launched.append((kind, args)) or
                        {'runId': 'r1', 'state': 'running', 'progress': 0})
    from app.prep.launch import start_prep
    sid = _ready(data_dir)
    result = start_prep(sid)
    assert result['runId'] == 'r1' and result['status'] == 'running'
    assert launched[0][0] == 'prep'
    prep = store.load_session(sid)['prep']
    assert prep['runId'] == 'r1' and prep['derivedRef']['collectionId'] == 'c1'


def test_router_uses_start_prep(client, data_dir, monkeypatch):
    monkeypatch.setattr(settings, 'embed_backend', 'fake')
    monkeypatch.setattr(runner, 'start', lambda *a: {'runId': 'r2', 'state': 'running', 'progress': 0})
    sid = _ready(data_dir, 'launch2')
    response = client.post(f'/prep/{sid}/run')
    assert response.status_code == 200 and response.json()['runId'] == 'r2'
```

- [ ] **Step 2: 실패 확인** — Run: `cd backend && .venv/bin/python -m pytest tests/prep/test_launch.py -q` / Expected: FAIL (`app.prep.launch` 없음)

- [ ] **Step 3: 구현** — `backend/app/prep/launch.py`

```python
"""Start stage three outside HTTP; shared by the API and the importer."""
from app.context import store
from app.context.stale import clear_stale
from app.prep.config import PrepConfig
from app.prep.guards import assert_ready
from app.work import runner


def start_prep(sid: str, version: str | None = None) -> dict:
    from app.routers.prep import _root, _save, _session, _view
    with store.locked(sid):
        data = _session(sid, version, writable=True)
        cfg = PrepConfig.model_validate(data.get('prep', {}).get('config', {}))
        ref = assert_ready(sid, data, cfg)
        current = _view(sid, data)
        if current['status'] in ('running', 'paused'):
            return current
        root = _root(sid, ref['collectionId'], ref['prepKey'])
        manifest = store.read_json(root / 'manifest.json')
        if (manifest and manifest.get('collectionFinalized') is True and manifest.get('status') == 'done'
                and (root / 'stage_3.json').exists()):
            _save(sid, config=cfg.model_dump(), derivedRef=ref, status='done', runId=None, reused=True)
            clear_stale(sid, data['version'], 'stage3', already_locked=True)
            return {**_view(sid, store.load_session(sid)), 'reused': True}
        work = runner.start(sid, data['version'], 'prep', {'config': cfg.model_dump()})
        _save(sid, config=cfg.model_dump(), derivedRef=ref, status=work['state'], runId=work['runId'], reused=False)
        return dict(status=work['state'], runId=work['runId'], progress=work['progress'], reused=False)
```

`routers/prep.py`의 `run`:
```python
@router.post('/{sid}/run')
def run(sid: str, version: str | None = None):
    from app.prep.launch import start_prep
    return start_prep(sid, version)
```
`run`에서만 쓰이던 import(`clear_stale` 등)는 다른 곳에서 쓰지 않으면 지운다.

- [ ] **Step 4: 통과·회귀 확인** — Run: `cd backend && .venv/bin/python -m pytest tests/prep tests/test_integration_stage3_5.py -q` / Expected: PASS

- [ ] **Step 5: 커밋** — `refactor(prep): 3단계 시작을 start_prep으로 분리`

---

### Task T4: 가져오기 단계 A~E (`app/importer/steps.py`)

**Files:**
- Create: `backend/app/importer/steps.py`
- Create: `backend/tests/importer/test_steps.py`

**Interfaces:**
- Consumes: T1 `open_source, scan, iter_records, ImportError_, Source, Scan`; T2 `route.IMPORTED`; T3 `start_prep`; `store.update_session/locked/load_session/session_dir/write_json/root_dir`, `crawl.writer.DocWriter`, `crawl.queue.CrawlQueue`, `crawl.queue.KwMeta`(필요 시), `crawl.control.phase_state`, `work.runner.status`, `model.infer.documents`, `label.overview.labels_for/index_documents`, `label.route.schema`, `model.export.write`.
- Produces:
  - `default_sid(source: Source) -> str` (`'imp-' + source.sha256[:12]`)
  - `run_import(path, *, sid: str | None = None, log: Callable[[str], None] = print, poll_s: float = 10, sleep=time.sleep) -> dict` — 요약 `{sid, counts: {...}, exportRef}` 반환, 오류는 `ImportError_`.
  - 단계 함수(테스트용 공개): `create_session(sid, source, scan)`, `register_collection(sid, source)`, `run_prep_step(sid, log, poll_s, sleep)`, `insert_labels(sid, source) -> dict`, `export_step(sid, partial: bool) -> dict`.

- [ ] **Step 1: 실패하는 테스트 작성** — `backend/tests/importer/test_steps.py`

```python
import json
from types import SimpleNamespace

import pytest

from app.config import settings
from app.context import store
from app.crawl.control import phase_state
from app.importer import read, steps
from app.prep import pipeline
from app.work import runner
from tests.importer.conftest import row, write_csv


@pytest.fixture
def env(data_dir, salt, monkeypatch, tmp_path):
    """runner.start only records the launch (start_prep holds the session lock);
    the injected sleep runs the prepared worker outside that lock, like a detached child."""
    monkeypatch.setattr(settings, 'embed_backend', 'fake')
    runs, pending = {}, []

    class Ctx:
        def __init__(self, sid, version, args):
            self.sid, self.version, self.args, self.run_id = sid, version, args, 'prep-1'
        def heartbeat(self, *a): pass
        def should_stop(self): return False
        def should_pause(self): return False

    def start(sid, version, kind, args):
        assert kind == 'prep'
        pending.append((sid, version, args))
        runs[sid] = {'runId': 'prep-1', 'kind': 'prep', 'state': 'running', 'progress': 0, 'detail': {}, 'error': None}
        return dict(runs[sid])

    def sleep(_seconds):
        while pending:
            sid, version, args = pending.pop()
            pipeline.run_prep(Ctx(sid, version, args), sid, version)
            runs[sid].update(state='done', progress=1)

    monkeypatch.setattr(runner, 'start', start)
    monkeypatch.setattr(runner, 'status', lambda sid: [dict(runs[sid])] if sid in runs else [])
    rows = [row(i) for i in range(6)] + [row(6, status='skipped', evidence_level=''), row(7, site='네이버지식인')]
    rows[1].update(anchor='0', sense='0', feel='0', think='0', act='0', relate='0', outcome='0', situation='0',
                   evidence_level='non', reason_code='ad', signal='')
    return SimpleNamespace(path=write_csv(tmp_path / 'r.csv', rows), logs=[], runs=runs, sleep=sleep)


def run(env, **kw):
    return steps.run_import(env.path, log=env.logs.append, poll_s=0, sleep=env.sleep, **kw)


def test_full_import_reaches_stage6(env, data_dir):
    summary = run(env)
    sid = summary['sid']
    assert sid == 'imp-' + read.open_source(env.path).sha256[:12]
    data = store.load_session(sid)
    ctx = data['projectContext']
    assert (ctx['bk'], ctx['oneLiner'], ctx['researchQuestion']['text'], ctx['taskMode']) == ('.', '.', '.', 'explore')
    assert [k['kw'] for k in data['keywords']] == ['건강 키워드0', '건강 키워드1']
    assert phase_state(sid, 'c1') == 'done'
    assert data['prep']['status'] == 'done'
    assert data['labeling'] == {**data['labeling'], 'started': True, 'status': 'done', 'labelerMode': 'imported'}
    assert data['step'] == 'cluster-start'
    assert summary['counts']['labeled'] == 6 and summary['counts']['unlabeled'] == 0
    from app.known.filter import read_export
    relevant = read_export(sid, data)
    assert len(relevant) == 5 and all(r['source'] == 'imported' for r in relevant)
    from app.routers.sessions import _completion
    done = _completion(sid, data)
    assert done['crawlDone'] and done['prepDone'] and done['labelingDone'] and done['exportDone']
    assert any('0단계' in line for line in env.logs)


def test_rerun_is_noop(env):
    first = run(env)
    before = store.load_session(first['sid'])
    second = run(env)
    after = store.load_session(first['sid'])
    assert second['sid'] == first['sid']
    assert after['training']['exportRef'] == before['training']['exportRef']


@pytest.mark.parametrize('blocked', ['register_collection', 'run_prep_step', 'insert_labels', 'export_step'])
def test_resume_after_interruption(env, monkeypatch, blocked):
    original = getattr(steps, blocked)
    def boom(*a, **k):
        raise KeyboardInterrupt
    monkeypatch.setattr(steps, blocked, boom)
    with pytest.raises(KeyboardInterrupt):
        run(env)
    monkeypatch.setattr(steps, blocked, original)
    summary = run(env)
    data = store.load_session(summary['sid'])
    assert data['step'] == 'cluster-start' and data['training']['exportRef']


def test_partial_collection_is_rebuilt(env, data_dir, monkeypatch):
    from app.crawl import writer
    real_close = writer.DocWriter.close
    def crash(self):
        real_close(self)
        raise KeyboardInterrupt
    monkeypatch.setattr(writer.DocWriter, 'close', crash)
    with pytest.raises(KeyboardInterrupt):
        run(env)
    sid = 'imp-' + read.open_source(env.path).sha256[:12]
    assert (data_dir / 'crawl' / sid / 'collections/c1.partial').exists()
    assert not (data_dir / 'crawl' / sid / 'collections/c1').exists()
    monkeypatch.setattr(writer.DocWriter, 'close', real_close)
    run(env)
    assert phase_state(sid, 'c1') == 'done'
    assert not (data_dir / 'crawl' / sid / 'collections/c1.partial').exists()


def test_short_body_dropped_by_prep_is_reported(env, tmp_path):
    rows = [row(i) for i in range(3)] + [row(9, contents='짧음')]
    env.path = write_csv(tmp_path / 'short.csv', rows)
    summary = run(env)
    assert summary['counts']['droppedByPrep'] == 1 and summary['counts']['labeled'] == 3
    from app.label.overview import labels_for
    data = store.load_session(summary['sid'])
    with labels_for(summary['sid'], data)._db() as db:
        assert db.execute('SELECT 1 FROM final WHERE doc_id=?', (row(9)['doc_id'],)).fetchone() is None
    assert any('전처리에서 빠짐 1' in line for line in env.logs)


def test_unlabeled_prepared_docs_use_partial_export(env, monkeypatch):
    from app.model import export
    calls = []
    real = export.write
    monkeypatch.setattr(export, 'write', lambda *a, **k: calls.append(k) or real(*a, **k))
    real_iter = steps.iter_records
    def drop_first_label(source, crawled_at):
        for i, record in enumerate(real_iter(source, crawled_at)):
            if crawled_at == '' and i == 0:
                continue  # insert_labels reads with crawled_at='': skip one label only there
            yield record
    monkeypatch.setattr(steps, 'iter_records', drop_first_label)
    summary = run(env)
    assert summary['counts']['unlabeled'] == 1
    assert calls[-1]['partial'] is True
    assert store.load_session(summary['sid'])['training']['exportPartial'] is True


def test_concurrent_import_refused(env, data_dir):
    import fcntl
    sid = 'imp-' + read.open_source(env.path).sha256[:12]
    lock = data_dir / 'imports' / f'{sid}.lock'
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open('a') as held:
        fcntl.flock(held, fcntl.LOCK_EX)
        with pytest.raises(read.ImportError_, match='이미 실행 중'):
            run(env)
    assert not (data_dir / 'sessions' / sid).exists()


def test_same_sid_different_file_rejected(env, tmp_path):
    run(env, sid='imp-fixed')
    other = write_csv(tmp_path / 'other.csv', [row(20)])
    with pytest.raises(read.ImportError_, match='다른 파일'):
        steps.run_import(other, sid='imp-fixed', log=lambda s: None, poll_s=0, sleep=lambda s: None)


def test_invalid_file_creates_nothing(env, tmp_path, data_dir):
    bad = write_csv(tmp_path / 'bad.csv', [row(1, questions_version='q9')])
    with pytest.raises(read.ImportError_):
        steps.run_import(bad, log=lambda s: None, poll_s=0, sleep=lambda s: None)
    assert not (data_dir / 'sessions').exists() or not any((data_dir / 'sessions').iterdir())


def test_prep_failure_reported(env, monkeypatch):
    monkeypatch.setattr(runner, 'start', lambda *a: {'runId': 'x', 'kind': 'prep', 'state': 'failed',
                                                     'progress': 0, 'detail': {}, 'error': 'Boom'})
    monkeypatch.setattr(runner, 'status', lambda sid: [{'runId': 'x', 'kind': 'prep', 'state': 'failed',
                                                       'progress': 0, 'detail': {}, 'error': 'Boom'}])
    with pytest.raises(read.ImportError_, match='전처리'):
        run(env)
```

`run_import`는 단계 함수를 호출할 때마다 모듈 전역에서 이름으로 찾는다(`globals()[STEP_FUNCTIONS[step]]`). 그래서 `monkeypatch.setattr(steps, '<함수>', …)`가 그대로 적용된다.

- [ ] **Step 2: 실패 확인** — Run: `cd backend && .venv/bin/python -m pytest tests/importer/test_steps.py -q` / Expected: FAIL (`app.importer.steps` 없음)

- [ ] **Step 3: 구현** — `backend/app/importer/steps.py`

```python
"""Stages A–E of an external label import. Each stage is idempotent."""
from contextlib import closing, contextmanager
import fcntl
import json
from pathlib import Path
import shutil
import sqlite3
import time

from app.config import settings
from app.context import store
from app.crawl.control import phase_state
from app.crawl.queue import CrawlQueue
from app.crawl.writer import DocWriter
from app.importer.read import ImportError_, Source, iter_records, open_source, scan
from app.label.route import IMPORTED, schema as label_schema

ORDER = ('session', 'crawl', 'prep', 'labels', 'export')
STEP_FUNCTIONS = {'session': 'create_session', 'crawl': 'register_collection', 'prep': 'run_prep_step',
                  'labels': 'insert_labels', 'export': 'export_step'}
DOT = '.'
WARNING = "주의: 0단계 값이 모두 '.'입니다. 6~8단계 결과는 주제 정보 없이 만들어집니다."
_BATCH = 5000


def default_sid(source: Source) -> str:
    return 'imp-' + source.sha256[:12]


def _context():
    return dict(bk=DOT, oneLiner=DOT, researchQuestion=dict(text=DOT), projectType=dict(choice='new', note=DOT),
                taskMode='explore', constraints=[], channels=['naver_cafe'],
                productCategory=dict(l1=DOT, source='user'))


def _imported(sid):
    return (store.load_session(sid) or {}).get('imported') or {}


def _mark(sid, step, **counts):
    with store.locked(sid):
        data = store.load_session(sid)
        imported = data.setdefault('imported', {})
        imported.setdefault('steps', {})[step] = store.now()
        imported.setdefault('counts', {}).update(counts)
        store.write_json(store.session_dir(sid) / 'session.json', data)


def create_session(sid, source, result, log):
    keywords = [dict(kw=k, text=k, status='approved', axis='', sub='') for k in result.keywords]
    store.update_session(sid, {'schemaVersion': 2, 'sid': sid, 'projectContext': _context(), 'keywords': keywords,
                               'imported': dict(file=source.name, sha256=source.sha256, steps={}, counts={})})
    log(f'[1/5] 프로젝트 {sid} 만듦')


def register_collection(sid, source, result, log):
    base = Path(settings.local_data_dir) / 'crawl' / sid / 'collections'
    final, partial = base / 'c1', base / 'c1.partial'
    if not final.exists():
        shutil.rmtree(partial, ignore_errors=True)
        partial.mkdir(parents=True)
        now = store.now()
        keywords = [dict(kw=k, axis='', sub='') for k in result.keywords]
        meta = dict(id='c1', parent=None, createdAt=now, keywords=keywords, status='done')
        store.write_json(partial / 'meta.json', meta)
        store.write_json(partial / 'manifest.json', dict(meta, channels=['naver_cafe'], config={}, snapshotId=None,
                                                         imported=dict(file=source.name, sha256=source.sha256)))
        writer = DocWriter(partial / 'docs')
        urls = []
        with closing(CrawlQueue(partial / 'queue.sqlite')) as queue:
            try:
                for record in iter_records(source, now):
                    writer.write(record.doc)
                    urls.append(dict(url=record.doc['url'], source='naver_cafe', kw=record.doc['kw'],
                                     title=record.doc['title'], date=record.doc['date'],
                                     src_meta=record.doc['src_meta']))
                    if len(urls) >= _BATCH:  # bounded memory: never hold all ~200k URL rows
                        queue.add_urls(urls)
                        urls.clear()
            finally:
                writer.close()
            if urls:
                queue.add_urls(urls)
            with queue._write() as db:
                db.execute("UPDATE urls SET status='done', doc_count=1, fetch_level='full', access='public'")
            queue.finish_run(queue.register_run('detail'), 'done')
        partial.rename(final)
    store.update_session(sid, {'collectionId': 'c1', 'step': 'preprocess-setup'}, confirm_stage='stage2')
    if phase_state(sid, 'c1') != 'done':
        raise ImportError_('수집본을 완료 상태로 만들지 못했습니다')
    docs = sum(1 for p in (final / 'docs').glob('shard-*.jsonl') for line in p.open(encoding='utf-8') if line.strip())
    log(f'[2/5] 수집본 c1 등록 {docs:,}건')


def run_prep_step(sid, source, result, log, *, poll_s=10, sleep=time.sleep):
    from app.prep.launch import start_prep
    from app.work import runner
    for attempt in (1, 2):
        data = store.load_session(sid)
        if data.get('prep', {}).get('status') == 'done':
            log('[3/5] 전처리 완료')
            return
        work = start_prep(sid)
        run_id = work.get('runId')
        log(f'[3/5] 전처리 run {run_id} 시작' if work.get('status') != 'done' else '[3/5] 전처리 결과 재사용')
        while True:
            # start_prep returns {'status': …}; runner.status rows carry {'state': …}.
            row = next((r for r in runner.status(sid) if run_id and r['runId'] == run_id), None)
            state = row['state'] if row else work.get('status')
            if state == 'done' or store.load_session(sid).get('prep', {}).get('status') == 'done':
                break
            if state in ('failed', 'interrupted'):
                log(f'      전처리 {state}: {(row or {}).get("error") or ""}')
                break
            progress = (row or work).get('progress') or 0
            log(f'      {time.strftime("%H:%M:%S")}  {round(progress * 100)}%')
            sleep(poll_s)
        if store.load_session(sid).get('prep', {}).get('status') == 'done':
            log('[3/5] 전처리 완료')
            return
    raise ImportError_('전처리에 실패했습니다. 서버 로그를 확인하고 같은 명령을 다시 실행하세요.')


def insert_labels(sid, source, result, log):
    from app.label.overview import index_documents, labels_for
    from app.label import rule
    from app.label.questions import QVER
    from app.model import infer
    data = store.load_session(sid)
    prepared = set(infer.documents(sid, data))
    labels = labels_for(sid, data)
    label_schema(labels)
    votes = json.dumps({'imported': dict(file=source.name, sha256=source.sha256[:12])})
    labeled, batch = set(), []
    def flush():
        with labels._db() as db:
            db.executemany('INSERT OR REPLACE INTO final VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', batch)
        batch.clear()
    for record in iter_records(source, ''):
        doc_id = record.doc['doc_id']
        if doc_id not in prepared:
            continue
        lab = record.label
        batch.append((doc_id, lab['level'], None, IMPORTED, 'accepted', lab['tags_json'], lab['reason_code'],
                      lab['signal'], rule.RULE_VERSION, QVER, votes, '[]', 0))
        labeled.add(doc_id)
        if len(batch) >= _BATCH:
            flush()
    if batch:
        flush()
    index_documents(sid, data, labels)
    counts = dict(labeled=len(labeled), unlabeled=len(prepared - labeled), droppedByPrep=result.done - len(labeled))
    store.update_session(sid, {'labeling': {'started': True, 'status': 'done', 'mode': IMPORTED,
                                            'labelerMode': IMPORTED}, 'step': 'train-start'})
    log(f"[4/5] 라벨 {counts['labeled']:,}건 넣음 · 판정 없음 {counts['unlabeled']:,} · 전처리에서 빠짐 {counts['droppedByPrep']:,}")
    return counts


def export_step(sid, source, result, log, *, partial=False):
    from app.model import export
    exported = export.write(sid, without_model=True, partial=partial)  # keyword args: tests assert on them
    store.update_session(sid, {'step': 'cluster-start'})
    log(f"[5/5] 내보내기 완료 · core+supporting {exported['relevant']:,}건")
    return exported


def run_import(path, *, sid=None, log=print, poll_s=10, sleep=time.sleep) -> dict:
    source = open_source(path)
    log(f'가져오기: {Path(path).name} → {source.name} (sha256 {source.sha256[:12]})')
    result = scan(source)
    skipped = ' · '.join(f'{k} {v:,}' for k, v in result.skipped.items()) or '없음'
    log(f'검증  {result.total:,}행 · done {result.done:,} · 건너뜀 {skipped}')
    sid = sid or default_sid(source)
    store.root_dir(sid)  # validates the id before anything is written
    with _import_lock(sid):
        return _run_locked(sid, source, result, log, poll_s, sleep)


@contextmanager
def _import_lock(sid):
    path = Path(settings.local_data_dir) / 'imports' / f'{sid}.lock'
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ImportError_('같은 프로젝트의 가져오기가 이미 실행 중입니다') from None
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def _run_locked(sid, source, result, log, poll_s, sleep):
    existing = store.load_session(sid) if (store.root_dir(sid)).exists() else None
    if existing is not None:
        info = existing.get('imported')
        if not info:
            raise ImportError_(f'{sid}는 가져오기로 만든 프로젝트가 아닙니다. --sid로 다른 이름을 주세요.')
        if info.get('sha256') != source.sha256:
            raise ImportError_(f'{sid}는 다른 파일로 만든 프로젝트입니다. --sid로 다른 이름을 주세요.')
    counts = dict(_imported(sid).get('counts', {}))
    for step in ORDER:
        if step in _imported(sid).get('steps', {}):
            continue
        fn = globals()[STEP_FUNCTIONS[step]]
        if step == 'prep':
            fn(sid, source, result, log, poll_s=poll_s, sleep=sleep)
        elif step == 'export':
            fn(sid, source, result, log, partial=counts.get('unlabeled', 0) > 0)
        else:
            out = fn(sid, source, result, log)
            if step == 'labels':
                counts.update(out)
        _mark(sid, step, **({k: v for k, v in counts.items()} if step == 'labels' else {}))
    data = store.load_session(sid)
    log(f'완료. 웹 프로젝트 목록에서 {sid}를 열고 6단계(세그먼트)부터 진행하세요.')
    log(WARNING)
    return dict(sid=sid, counts=data['imported'].get('counts', {}), exportRef=data.get('training', {}).get('exportRef'))
```

주의:
- `run_import`는 `globals()[...]`로 단계 함수를 찾으므로, 테스트에서 `monkeypatch.setattr(steps, 'insert_labels', …)`로 바꾼 함수가 그대로 쓰인다.
- `store.update_session`은 `projectContext`가 패치에 있으면 `ProjectContext`로 검증하고 `project_context.md`를 쓴다. `_context()`가 검증을 통과해야 한다(T4 테스트가 확인).
- `register_collection`은 URL 행을 5,000건씩 큐에 넣고 비운다. 메모리에 전체 행을 두지 않는다.
- 같은 `sid`의 가져오기가 동시에 두 번 돌지 않도록, `run_import`는 검증 직후부터 끝날 때까지 `LOCAL_DATA_DIR/imports/<sid>.lock`에 `fcntl.flock(LOCK_EX | LOCK_NB)`를 잡는다. 못 잡으면 `ImportError_('같은 프로젝트의 가져오기가 이미 실행 중입니다')`. (세션 `.lock`은 단계 함수들이 짧게 잡으므로 따로 둔다.)
- 4단계가 이미 다른 방식으로 시작된 세션(`labeling.started`이면서 `labelerMode != 'imported'`)이면 `insert_labels` 시작 시 `ImportError_('이미 라벨링을 시작한 프로젝트입니다')`.

- [ ] **Step 4: 통과·회귀 확인** — Run: `cd backend && .venv/bin/python -m pytest tests/importer tests/label tests/prep tests/crawl -q` / Expected: PASS

- [ ] **Step 5: 커밋** — `feat(importer): 가져오기 단계 A~E`

---

### Task T5: 명령과 `dcxctl import-labels`

**Files:**
- Create: `backend/app/importer/__main__.py`
- Modify: `ops/macmini/dcxctl`
- Create: `backend/tests/importer/test_main.py`
- Modify: `backend/tests/ops/test_dcxctl.py`
- Modify: `ops/macmini/README.md`(사용법 한 절)

**Interfaces:**
- Consumes: T4 `run_import(path, sid=, log=)`, `ImportError_`.
- Produces: `python -m app.importer <파일> [--sid ID]`, 종료 코드 0/1/130. `dcxctl import-labels <파일> [--sid ID]`.

- [ ] **Step 1: 실패하는 테스트 작성**

`backend/tests/importer/test_main.py`:
```python
from app.importer import __main__ as cli
from app.importer import read, steps


def test_main_success(monkeypatch, capsys):
    monkeypatch.setattr(steps, 'run_import', lambda path, sid=None, log=print: log('ok') or {'sid': 'imp-x'})
    assert cli.main(['some.zip']) == 0
    assert 'ok' in capsys.readouterr().out


def test_main_import_error(monkeypatch, capsys):
    def fail(*a, **k):
        raise read.ImportError_('필수 컬럼이 없습니다: url')
    monkeypatch.setattr(steps, 'run_import', fail)
    assert cli.main(['x.csv']) == 1
    assert '필수 컬럼' in capsys.readouterr().err


def test_main_interrupt(monkeypatch, capsys):
    def stop(*a, **k):
        raise KeyboardInterrupt
    monkeypatch.setattr(steps, 'run_import', stop)
    assert cli.main(['x.csv', '--sid', 'imp-a']) == 130
    assert '다시 실행' in capsys.readouterr().err
```

`backend/tests/ops/test_dcxctl.py`에 추가:
```python
def _fake_python(m):
    backend = m.root / f'releases/{m.a}/backend'
    python = backend / '.venv/bin/python'
    python.parent.mkdir(parents=True, exist_ok=True)
    python.write_text('#!/bin/bash\nprintf "%s\\n" "$@" > "$(dirname "$0")/../../args.txt"\n')
    python.chmod(0o755)
    return backend / 'args.txt'


def test_import_labels_runs_release_importer(macmini, tmp_path):
    m = macmini
    args = _fake_python(m)
    data = tmp_path / 'data.zip'
    data.write_bytes(b'x')
    r = ctl(m, 'import-labels', str(data), '--sid', 'imp-a')
    assert r.returncode == 0, r.stderr
    text = args.read_text()
    assert str(data) in text and 'imp-a' in text and 'app.importer' in text


def test_import_labels_refused_in_maintenance(macmini, tmp_path):
    m = macmini
    args = _fake_python(m)
    (m.root / 'shared/maintenance').write_text('test')  # env.sh: MAINTENANCE="$SHARED/maintenance"
    r = ctl(m, 'import-labels', str(tmp_path / 'x.zip'))
    assert r.returncode == 1 and '점검' in r.stderr
    assert not args.exists()


def test_import_labels_requires_file(macmini):
    r = ctl(macmini, 'import-labels')
    assert r.returncode == 2
```

기존 `test_status_reports_hold`가 점검 상태를 만드는 방법이 `shared/maintenance` 파일 쓰기와 다르면 그 방법을 따른다.

- [ ] **Step 2: 실패 확인** — Run: `cd backend && .venv/bin/python -m pytest tests/importer/test_main.py tests/ops/test_dcxctl.py -q` / Expected: FAIL

- [ ] **Step 3: 구현**

`backend/app/importer/__main__.py`:
```python
"""python -m app.importer <zip|csv> [--sid ID]"""
import argparse
import sys

from app.importer import read, steps


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog='dcxctl import-labels', description='외부 라벨 결과를 새 프로젝트로 가져옵니다')
    parser.add_argument('path', help='결과 CSV 또는 그것을 담은 zip')
    parser.add_argument('--sid', help='프로젝트 id (기본: imp-<파일 해시>)')
    args = parser.parse_args(argv)
    try:
        steps.run_import(args.path, sid=args.sid, log=lambda line: print(line, flush=True))
    except read.ImportError_ as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('중단했습니다. 같은 명령을 다시 실행하면 이어서 합니다.', file=sys.stderr)
        return 130
    return 0


if __name__ == '__main__':
    sys.exit(main())
```

`ops/macmini/dcxctl`의 `case`에 추가(`rollback)` 앞):
```bash
    import-labels)
        shift
        [[ $# -ge 1 ]] || { echo '사용법: dcxctl import-labels <zip 또는 csv> [--sid ID]' >&2; exit 2; }
        [[ ! -e "$MAINTENANCE" ]] || { echo '서버 점검 중이라 가져오기를 실행하지 않습니다' >&2; exit 1; }
        sha="$(current_sha)"
        [[ -n "$sha" ]] || { echo 'current 릴리스가 없습니다' >&2; exit 1; }
        backend="$APP_ROOT/releases/$sha/backend"
        file="$1"; shift
        [[ "$file" == /* ]] || file="$PWD/$file"
        # Same dotenv loading as run-api.sh, then the release interpreter runs the importer.
        exec "$backend/.venv/bin/python" -c '
import os, pathlib, sys
from dotenv import dotenv_values
root = pathlib.Path(sys.argv[1]); backend = pathlib.Path(sys.argv[2])
for name in ("app.env", "runtime.env"):
    os.environ.update({k: v for k, v in dotenv_values(root / "shared" / name, interpolate=False).items() if v is not None})
os.chdir(backend)
python = str(backend / ".venv/bin/python")
os.execv(python, [python, "-m", "app.importer", *sys.argv[3:]])
' "$APP_ROOT" "$backend" "$file" "$@"
        ;;
```
(가짜 python 테스트는 `-c` 뒤의 인자들을 기록하므로 `app.importer` 문자열은 프로그램 텍스트에서, 파일 경로·`--sid`는 뒤 인자에서 찾는다.)

`ops/macmini/README.md`에 "외부 라벨 결과 가져오기" 절: 파일을 서버로 옮기는 예(`scp ~/Downloads/네이버\ 카페.zip mini:~/`), `dcxctl import-labels ~/네이버\ 카페.zip`, 다시 실행하면 이어서 함, 0단계 `.` 주의, 끝나면 웹 6단계.

- [ ] **Step 4: 통과·회귀 확인** — Run: `cd backend && DCX_BASH=/bin/bash .venv/bin/python -m pytest tests/importer tests/ops -q -p no:cacheprovider` / Expected: PASS

- [ ] **Step 5: 전체 검증** — 하네스 검증 명령 4개 실행. Expected: 모두 PASS(프론트는 변경 없음, 회귀 확인용)

- [ ] **Step 6: 커밋** — `feat(ops): dcxctl import-labels`

---

## 리뷰 체크리스트 (태스크별 리뷰어에게 전달)

- 기존 세션(`labelerMode` cross/gpt_only/model)의 경로가 바뀌지 않았는가(분기는 `imported`에서만).
- `final` 삭제 조건에서 `imported`가 빠졌는가, 감사 라운드가 imported에서 생기지 않는가.
- 가져오기는 검증 실패 시 아무것도 쓰지 않는가(`sessions/`, `crawl/` 모두).
- 수집본 공개는 `c1.partial` → `c1` 이름 바꾸기로 원자적인가.
- 원문 닉네임이 저장되지 않는가(작성자 해시만). 지식인 `answers`·`comment_nicknames`가 문서에 없는가.
- 1GB 입력을 메모리에 통째로 올리지 않는가(스트리밍; URL 목록만 메모리).
- `dcxctl import-labels`가 점검 중에 실행되지 않는가, 비밀값을 출력하지 않는가.

## 되돌리기

- 코드: 태스크 커밋을 역순으로 revert. T2·T3는 기존 동작을 바꾸지 않으므로 단독 revert도 안전하다.
- 데이터: 가져온 프로젝트는 `sessions/<imp-…>`, `crawl/<imp-…>`, `derived/<imp-…>`, `classified/<imp-…>`, `judge/<imp-…>`(있으면), `work/<imp-…>`(run DB) 폴더만 쓴다. 웹의 프로젝트 삭제나 이 폴더 삭제로 지운다. 다른 프로젝트 데이터는 건드리지 않는다.

## 계획 검토 결과 (plan-eng-review, 2026-11-03)

**Step 0 범위:** 범위를 그대로 둔다. 새 파일은 `importer/` 3개와 `prep/launch.py` 1개, 기존 파일은 6개를 바꾼다. 새 클래스는 dataclass 3개(Source, Scan, Record)뿐이다. 수집·전처리·내보내기는 새로 만들지 않고 기존 코드를 재사용한다.

**이미 있는 것과 재사용**

| 하위 문제 | 기존 코드 | 계획 |
|---|---|---|
| 끝난 수집본 | `CrawlQueue.register_run/finish_run`, `DocWriter`, `report.can_finalize` | 재사용(통합 테스트와 같은 방식) |
| 전처리 시작·대기 | `routers/prep.run`, `work/runner.start/status` | `start_prep`으로 옮겨 공유 |
| 모델 없는 내보내기 | `model/export.write(without_model, partial)` | 재사용 |
| 판정 없는 4단계 | `labeling.mode='model'` 경로 | 참고만. imported는 별도 모드 |
| doc_id 규칙 | `crawl/urls.doc_id` | 재사용. 실제 CSV 2건으로 일치 확인 |

**검토에서 반영한 것**
1. (환경) 하네스는 Python 의존성을 설치하지 않고 `backend/venv`에는 torch가 없다. 사용자 결정에 따라 worktree에 `.venv`를 새로 만들고 기준선을 확인한다.
2. (성능·메모리) 수집 URL 행을 5,000건씩 큐에 넣는다.
3. (동시성) 같은 sid의 가져오기 동시 실행을 잠금으로 막는다. 테스트 `test_concurrent_import_refused`, QA-NEG-011을 추가했다.
4. (테스트) 흐름 테스트의 가짜 전처리가 세션 잠금 안에서 `run_prep`을 부르면 교착된다(flock은 같은 프로세스에서도 새 fd면 막힌다). 그래서 `sleep` 주입 지점에서 실행하도록 고쳤다.
5. (정확성) `start_prep`의 반환 키(`status`)와 `runner.status` 행의 키(`state`)가 달라서 맞췄다.

**커버리지**
```
read.py      open_source ─ zip 1개 ★★★ / zip 0·2개 ★★★ / csv ★★
             scan ─ 컬럼 누락 ★★★ / 버전·doc_id·등급·태그·signal·중복 ★★★ / site·status 집계 ★★
             iter_records ─ 댓글 3형태 ★★★ / 날짜 ★★ / Non 정리 ★★★ / 닉네임·답변 제외 ★★★ / 빈 키워드 ★★
steps.py     run_import ─ 정상 ★★★ / 재실행 무변경 ★★★ / 단계별 중단 후 재개 ×4 ★★★
                          / 다른 파일 같은 sid ★★★ / 검증 실패 무생성 ★★★ / 동시 실행 ★★★
             register_collection ─ partial 재작성 ★★★
             run_prep_step ─ 완료 ★★ / 실패 2회 ★★★
             insert_labels ─ 전처리에서 빠진 글 ★★★ / 판정 없는 글 → partial 내보내기 ★★★
label 보호   rebuild/sync 유지 ★★★ / 버전 변경 삭제 제외 ★★★ / API 409 ×3 ★★★ / overview ★★ / judges_complete ★★
CLI·ops      main 0/1/130 ★★★ / dcxctl 실행·점검·인자 ★★★
[→E2E] 실제 1GB 파일 스모크: QA-E2E-005(수동, 사용자 확인 후)
```

**실패 모드**

| 경로 | 실제로 일어날 수 있는 실패 | 테스트 | 처리 | 사용자에게 보이나 |
|---|---|---|---|---|
| 1GB zip 읽기 | 디스크 부족·zip 손상 | 없음 | `zipfile` 예외 → 종료 코드 1 | 보임(파이썬 오류 메시지) |
| 전처리 | 서버 임베딩 API 미연결·요금 한도 | `test_prep_failure_reported` | 2회 시도 후 안내 | 보임 |
| 전처리 대기 중 Ctrl+C | 워커는 계속 돈다 | `test_main_interrupt` | 다시 실행하면 같은 run을 기다린다 | 보임 |
| 라벨 넣기 | 중간에 끊겨 일부만 들어감 | 단계 재개 테스트 | `INSERT OR REPLACE`로 다시 넣는다 | 보임 |
| 4단계 화면 | overview의 빈 값 처리 | `test_overview_reports_imported_totals` | None 값 | UAT에서 화면 확인 |

조용히 실패하면서 테스트도 처리도 없는 경로(critical gap)는 없다.

**범위 밖 (검토에서 고려하고 미룸)**
- 확률 CSV로 `confidence` 채우기: 승인된 제외 범위. 6단계 이후가 confidence를 쓰는지 UAT에서 보고 결정한다.
- 웹에서 가져오기 진행률 보기: 3단계 run은 웹에서도 보인다. 나머지 단계는 터미널만.
- 수백만 행 입력: 단일 프로세스·3회 읽기 구조. 이번 데이터(약 20만)에는 충분하다.

**병렬화:** T1·T2·T3은 모듈이 겹치지 않는다(`importer/`, `label/`+`routers/labeling_v2`+`context/stale`, `prep/`+`routers/prep`). 병렬로 진행할 수 있다. T4는 세 태스크를 합친 뒤, T5는 T4 뒤에 진행한다. 하네스 디스패치는 태스크마다 하나씩이므로 순서대로 해도 된다.
