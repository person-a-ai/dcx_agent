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
from typing import Callable, ContextManager, Iterator, TextIO
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
REQUIRED: tuple[str, ...] = ('date', 'keyword', 'title', 'contents', 'comments', 'answers', 'site', 'url',
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
    open: Callable[[], ContextManager[TextIO]]


@dataclass
class Scan:
    total: int
    done: int
    skipped: Counter[str]
    keywords: list[str]


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


def _open_source(path: str | Path) -> Source:
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
    @contextmanager
    def text():
        with raw() as stream:
            with io.TextIOWrapper(stream, encoding='utf-8-sig', newline='') as decoded:
                yield decoded

    return Source(name=name, sha256=_digest(raw), open=text)


def open_source(path: str | Path) -> Source:
    try:
        return _open_source(path)
    except (OSError, zipfile.BadZipFile, RuntimeError, NotImplementedError) as exc:
        raise ImportError_(f'{Path(path).name}: 파일을 읽을 수 없습니다: {exc}') from exc


@contextmanager
def _rows(source: Source):
    try:
        with source.open() as stream:
            reader = csv.DictReader(stream)
            missing = [c for c in REQUIRED if c not in (reader.fieldnames or [])]
            if missing:
                raise ImportError_(f'{source.name}: 필수 컬럼이 없습니다: {", ".join(missing)}')
            yield reader
    except (OSError, UnicodeError, csv.Error, zipfile.BadZipFile) as exc:
        raise ImportError_(f'{source.name}: CSV를 읽을 수 없습니다: {exc}') from exc


def _tags(row):
    values = {name: row[name].strip() for name in ('anchor', *rule.SEM, 'situation')}
    if any(v not in ('0', '1') for v in values.values()):
        return None
    return {k: int(v) for k, v in values.items()}


def _problems(row):
    """Return the first validation problem of a done row, or None."""
    if row['questions_version'] != QVER or row['rule_version'] != rule.RULE_VERSION:
        return f'판정 버전이 DCX({QVER}/{rule.RULE_VERSION})와 다릅니다: {row["questions_version"]}/{row["rule_version"]}'
    try:
        expected_id = make_doc_id(SOURCE, normalize_url(row['url'], SOURCE))
    except ValueError:
        return 'URL 형식이 올바르지 않습니다'
    if expected_id != row['doc_id']:
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
            if any(row.get(column) is None for column in REQUIRED) or None in row:
                raise ImportError_(f'{source.name}: {line}행의 컬럼 수가 헤더와 다릅니다')
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
