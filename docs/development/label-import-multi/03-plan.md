# 여러 채널 라벨 결과 가져오기 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `dcxctl import-labels`가 네이버 카페·지식iN·다음 카페·브런치 결과 CSV 여러 개를 한 프로젝트로 가져오게 한다.

**Architecture:** 가져오기 전용 채널 `daum_cafe`·`daum_brunch`를 채널 목록에 등록하고(크롤러 없음), `importer/read.py`가 행의 `site`로 채널을 골라 검증·매핑한다. `importer/steps.py`는 파일 목록을 받아 묶음 해시로 프로젝트를 식별하고, 기존 단계 A~E를 모든 파일에 대해 실행한다. 웹은 표시 이름만 더하고, 0단계·크롤링 설정 선택지에서 가져오기 전용 채널을 거른다.

**Tech Stack:** Python 3.12, pydantic, pytest, Next.js/TypeScript(vitest), Bash 3.2.

설계: [02-design.md](02-design.md). 기획: [01-brainstorm.md](01-brainstorm.md). 앞선 실행 계획: `docs/development/label-import/03-plan.md`.

## Global Constraints

- 새 채널 키·접두사·표시 이름: `daum_cafe`/`dc`/"다음 카페", `daum_brunch`/`db`/"브런치". 기존 채널의 키·접두사·이름은 바꾸지 않는다.
- CSV `site` → 채널: `네이버카페`→`naver_cafe`, `네이버지식인`→`naver_kin`, `다음카페`→`daum_cafe`, `다음블로그_브런치`→`daum_brunch`.
- 채널 순서(`CHANNEL_ORDER`): `naver_cafe`, `naver_kin`, `daum_cafe`, `daum_brunch`.
- 새 채널은 크롤러 레지스트리(`app/crawl/adapters`)에 넣지 않는다.
- 파일 하나로 실행하면 앞선 실행과 같은 `sid`(`imp-` + 파일 sha256[:12])와 같은 세션·수집본·라벨이 나온다(기존 테스트 전부 통과).
- 묶음 해시: 파일 하나면 그 sha256, 여럿이면 `sha256('\n'.join(sorted(파일 sha256들)))`의 hex.
- `answers`, `comment_nicknames`, 원문 닉네임은 어떤 채널에서도 저장하지 않는다.
- 0단계 그 밖의 값은 앞선 실행과 같다(모두 `.`, `projectType.choice="new"`, `taskMode="explore"`, `productCategory={"l1":".","source":"user"}`).
- 테스트는 네트워크·실제 임베딩·모델 호출을 하지 않는다.
- 검증 명령(하네스 고정): `backend/.venv/bin/python -m pytest backend/tests -q`, `npm --prefix frontend run lint`, `npm --prefix frontend run build`, `npm --prefix frontend test`.
- 이 PC 고유 환경(앞선 실행과 같음): 저장소 루트 `.env`의 실제 `VOYAGE_API_KEY`가 테스트에 섞이지 않도록 pytest는 `env -u VOYAGE_API_KEY`로 실행한다. ops 테스트는 `DCX_BASH=/bin/bash TAR_READER_OPTIONS=read_concatenated_archives`가 필요하다.
- 사용자에게 보이는 문구는 한국어.

## File Structure

| 파일 | 역할 | 태스크 |
|---|---|---|
| `backend/app/crawl/schema.py` | `Doc.source` Literal에 새 채널 | T1 |
| `backend/app/context/models.py` | `Channel` enum에 새 채널 | T1 |
| `backend/app/crawl/urls.py` | `_PREFIXES`에 `dc`·`db`, `daum_cafe` 정규화 | T1 |
| `backend/app/context/labels.py` | 표시 이름 | T1 |
| `frontend/src/lib/contextLabels.ts` | 표시 이름, `IMPORT_ONLY_CHANNELS` | T1 |
| `frontend/src/app/pipeline/start/page.tsx` | 0단계 선택지 필터 | T1 |
| `frontend/src/components/crawl/Settings.tsx` | `channelNames`에 이름 | T1 |
| `frontend/src/lib/logic/crawlConfig.ts` | `settingsSources()`에서 가져오기 전용 채널 제외 | T1 |
| `backend/tests/crawl/test_import_only_channels.py` (새) | T1 백엔드 테스트 | T1 |
| `frontend/src/lib/logic/importOnlyChannels.test.ts` (새) | T1 프론트 테스트 | T1 |
| `backend/app/importer/read.py` | 채널별 검증·매핑, 날짜, 여러 파일 | T2 |
| `backend/tests/importer/conftest.py`, `test_read.py` | 채널별 행 픽스처, T2 테스트 | T2 |
| `backend/app/importer/steps.py` | 파일 목록, 묶음 해시, 채널 목록 | T3 |
| `backend/app/importer/__main__.py` | `nargs='+'` | T3 |
| `ops/macmini/dcxctl`, `ops/macmini/README.md` | 여러 파일 인자 | T3 |
| `backend/tests/importer/test_steps.py`, `test_main.py`, `backend/tests/ops/test_dcxctl.py` | T3 테스트 | T3 |

의존: T1 → T2 → T3 (순서대로 한 번에 하나씩 디스패치한다).

## 실행 환경 준비 (worktree를 만든 직후, 컨트롤러)

- 앞선 worktree(`.worktrees/label-import`)의 `backend/.venv`를 새 worktree의 `backend/.venv`로 **옮긴다**(`mv`, 같은 디스크라 즉시 끝남. 남은 디스크 12GB라 복사하지 않는다). 테스트는 `backend/.venv/bin/python -m pytest`로만 부르므로 콘솔 스크립트 경로는 쓰지 않는다.
- 프론트 의존성은 하네스 `prepare`가 설치한다(`prepare-status`로 확인).
- 기준선: `env -u VOYAGE_API_KEY DCX_BASH=/bin/bash TAR_READER_OPTIONS=read_concatenated_archives backend/.venv/bin/python -m pytest backend/tests -q -p no:cacheprovider`가 통과해야 구현을 시작한다.

---

### Task T1: 가져오기 전용 채널 등록 (백엔드·웹)

**Files:**
- Modify: `backend/app/crawl/schema.py:21`, `backend/app/context/models.py:75-85`, `backend/app/crawl/urls.py:8-9,38-58`, `backend/app/context/labels.py:36-47`
- Modify: `frontend/src/lib/contextLabels.ts:33-44`, `frontend/src/app/pipeline/start/page.tsx:266`, `frontend/src/components/crawl/Settings.tsx:7`, `frontend/src/lib/logic/crawlConfig.ts:19-21`
- Create: `backend/tests/crawl/test_import_only_channels.py`, `frontend/src/lib/logic/importOnlyChannels.test.ts`

**Interfaces:**
- Produces: 채널 키 `daum_cafe`·`daum_brunch`가 `Doc`, `ProjectContext.channels`, `doc_id()`, `normalize_url()`, `LABELS['channels']`에서 유효하다. 프론트 `IMPORT_ONLY_CHANNELS: readonly string[]`.

- [ ] **Step 1: 실패하는 백엔드 테스트 작성** — `backend/tests/crawl/test_import_only_channels.py`

```python
import hashlib

import pytest

from app.context.labels import LABELS
from app.context.models import Channel
from app.crawl.adapters import available_sources
from app.crawl.schema import Doc
from app.crawl.urls import doc_id, normalize_url


def sha16(text):
    return hashlib.sha1(text.encode()).hexdigest()[:16]


def test_daum_cafe_drops_query_and_uses_dc_prefix():
    url = 'https://cafe.daum.net/chonanmam/8gn1/1469?q=%EA%B1%B4%EA%B0%95%20%2BPT&re=1'
    assert normalize_url(url, 'daum_cafe') == 'https://cafe.daum.net/chonanmam/8gn1/1469'
    assert doc_id('daum_cafe', normalize_url(url, 'daum_cafe')) == 'dc_' + sha16('https://cafe.daum.net/chonanmam/8gn1/1469')
    assert normalize_url('http://m.cafe.daum.net/a/b/1/?x=1', 'daum_cafe') == 'https://cafe.daum.net/a/b/1'


def test_daum_brunch_uses_db_prefix_with_common_rules():
    url = 'https://brunch.co.kr/@8c909cfe8a424c2/159'
    assert normalize_url(url, 'daum_brunch') == url
    assert doc_id('daum_brunch', url) == 'db_' + sha16(url)


@pytest.mark.parametrize('source', ['daum_cafe', 'daum_brunch'])
def test_import_only_channels_are_valid_but_not_crawlable(source):
    assert Channel(source).value == source
    assert source in LABELS['channels']
    assert source not in available_sources()
    Doc(doc_id='dc_0', source=source, src_meta={}, kw='k', kw_axis='', kw_sub='', kw_hits=['k'], title='', body='b',
        comments=[], date='', url='https://x', fetch_level='full', access='public', snippet='b',
        author_hash='', crawled_at='2026-11-04T00:00:00Z')


def test_existing_channels_unchanged():
    assert normalize_url('https://cafe.naver.com/ca-fe/club/1?art=x', 'naver_cafe') == 'https://cafe.naver.com/club/1'
    assert doc_id('naver_kin', 'u').startswith('kn_')
```

(`Doc` 생성 인자는 `app/crawl/schema.py`의 실제 필드에 맞춘다. 필드가 다르면 테스트를 그 필드로 고치되 `source=` 검증 목적은 유지한다.)

- [ ] **Step 2: 실패 확인** — Run: `env -u VOYAGE_API_KEY backend/.venv/bin/python -m pytest backend/tests/crawl/test_import_only_channels.py -q` → Expected: FAIL (`KeyError: 'daum_cafe'`, `ValueError: 'daum_cafe' is not a valid Channel`).

- [ ] **Step 3: 백엔드 구현**
  - `schema.py` Literal 끝에 `"daum_cafe", "daum_brunch"`.
  - `models.py` `Channel`에 `daum_cafe = "daum_cafe"`, `daum_brunch = "daum_brunch"`.
  - `urls.py` `_PREFIXES`에 `"daum_cafe":"dc","daum_brunch":"db"`. 호스트별 분기(`if source == "naver_kin" …` 체인)에 다음을 더한다:

```python
    elif source == "daum_cafe" and host in {"cafe.daum.net", "m.cafe.daum.net"}:
        scheme, netloc, params = "https", "cafe.daum.net", []
```

  - `labels.py` `"channels"` 끝에 `"daum_cafe": "다음 카페",`, `"daum_brunch": "브런치",`.

- [ ] **Step 4: 실패하는 프론트 테스트 작성** — `frontend/src/lib/logic/importOnlyChannels.test.ts`

```ts
import { describe, expect, it } from 'vitest';
import { contextLabels, IMPORT_ONLY_CHANNELS } from '../contextLabels';
import { settingsSources } from './crawlConfig';
import { channelNames } from '../../components/crawl/Settings';
import { stageZeroChannelOptions } from '../../app/pipeline/start/channelOptions';

describe('import-only channels', () => {
  it('have Korean display names', () => {
    expect(contextLabels.channels.daum_cafe).toBe('다음 카페');
    expect(contextLabels.channels.daum_brunch).toBe('브런치');
    expect(channelNames.daum_cafe).toBe('다음 카페');
    expect(channelNames.daum_brunch).toBe('브런치');
  });
  it('are hidden from stage 0 unless already selected', () => {
    const fresh = stageZeroChannelOptions([], false).map(o => o.value);
    expect(fresh).not.toContain('daum_cafe');
    expect(fresh).not.toContain('daum_brunch');
    expect(fresh).toContain('naver_cafe');
    const imported = stageZeroChannelOptions(['naver_cafe', 'daum_cafe'], false).map(o => o.value);
    expect(imported).toContain('daum_cafe');
    expect(imported).not.toContain('daum_brunch');
  });
  it('are not offered in crawl settings unless selected', () => {
    const known = Object.keys(channelNames);
    expect(settingsSources(known, [], ['naver_cafe'])).not.toContain('daum_cafe');
    expect(settingsSources(known, ['daum_cafe'], [])).toContain('daum_cafe');
    expect(IMPORT_ONLY_CHANNELS).toEqual(['daum_cafe', 'daum_brunch']);
  });
});
```

- [ ] **Step 5: 실패 확인** — Run: `npm --prefix frontend test -- importOnlyChannels` → Expected: FAIL (모듈·내보내기 없음).

- [ ] **Step 6: 프론트 구현**
  - `contextLabels.ts` `"channels"` 끝에 `"daum_cafe": "다음 카페",`, `"daum_brunch": "브런치",`(각 줄 끝 쉼표 유지: 백엔드 parity 테스트가 `"키": "값",` 형식을 읽는다). 객체 바깥에 `export const IMPORT_ONLY_CHANNELS = ['daum_cafe', 'daum_brunch'] as const;`.
  - 새 파일 `frontend/src/app/pipeline/start/channelOptions.ts`:

```ts
import { contextLabels, IMPORT_ONLY_CHANNELS } from '@/lib/contextLabels';

const importOnly: readonly string[] = IMPORT_ONLY_CHANNELS;

export function stageZeroChannelOptions(selected: readonly string[], internalTools: boolean) {
  return Object.entries(contextLabels.channels)
    .map(([value, label]) => ({ value, label }))
    .filter(option => (internalTools || option.value !== 'fixture')
      && (!importOnly.includes(option.value) || selected.includes(option.value)));
}
```

  - `start/page.tsx:266`: `options={options(labels.channels).filter(…)}`를 `options={stageZeroChannelOptions(form.channels, INTERNAL_TOOLS)}`로 바꾼다. 기존 `options()` 헬퍼의 반환 모양(`{value,label}`)과 같은지 확인하고, 다르면 `stageZeroChannelOptions`가 그 모양을 돌려주게 맞춘다.
  - `Settings.tsx:7` `channelNames`에 `daum_cafe:'다음 카페',daum_brunch:'브런치'`.
  - `crawlConfig.ts` `settingsSources`: `known`에서 `IMPORT_ONLY_CHANNELS`를 거른다(`selected`·`available`은 그대로 합친다).

- [ ] **Step 7: 통과 확인** — Run: `env -u VOYAGE_API_KEY backend/.venv/bin/python -m pytest backend/tests/crawl backend/tests/context -q` 와 `npm --prefix frontend test` → Expected: PASS(`test_labels_parity` 포함).

- [ ] **Step 8: 커밋 준비** — 워커는 `READY_FOR_COMMIT` 보고서를 쓴다(컨트롤러가 게이트·커밋).

### Task T2: 채널별 읽기·검증과 여러 파일 (`app/importer/read.py`)

**Files:**
- Modify: `backend/app/importer/read.py`
- Modify: `backend/tests/importer/conftest.py`, `backend/tests/importer/test_read.py`

**Interfaces:**
- Consumes: T1의 채널 키·`doc_id`·`normalize_url`.
- Produces (T3가 쓴다):
  - `CHANNELS: dict[str, str]`, `CHANNEL_ORDER: tuple[str, ...]`
  - `Scan`에 `channels: Counter[str]` 필드 추가(채널별 done 수).
  - `open_sources(paths: Iterable[str | Path]) -> list[Source]`
  - `bundle_sha(sources: Sequence[Source]) -> str`
  - `scan(source: Source, seen: set[str] | None = None) -> Scan`
  - `merge_scans(scans: Sequence[Scan]) -> Scan`
  - `iter_records(source, crawled_at)`는 시그니처 그대로, 행마다 그 채널로 `Record.doc['source']`를 채운다.
  - `SITE`/`SOURCE` 상수는 지운다(다른 모듈이 쓰면 함께 고친다: `grep -rn "read.SITE\|read.SOURCE\|import SITE\|import SOURCE" backend`).

- [ ] **Step 1: 픽스처 확장** — `conftest.py`에 채널별 행 생성기를 더한다. 기존 `row(n, **over)`(네이버 카페)는 그대로 둔다.

```python
SITES = {'naver_cafe': '네이버카페', 'naver_kin': '네이버지식인', 'daum_cafe': '다음카페', 'daum_brunch': '다음블로그_브런치'}


def channel_row(channel, n, **over):
    url, date = {
        'naver_cafe': (f'https://cafe.naver.com/club{n % 3}/{1000 + n}', '2026.03.30. 22:02'),
        'naver_kin': (f'https://kin.naver.com/qna/detail.naver?dirId=70601&docId={490000000 + n}', '2025.12.22'),
        'daum_cafe': (f'https://cafe.daum.net/club{n % 3}/8gn1/{1000 + n}?q=%EA%B1%B4%EA%B0%95&re=1', '26.06.02 11:32'),
        'daum_brunch': (f'https://brunch.co.kr/@writer{n % 3}/{100 + n}', '2026-06-06T03:46:43+09:00'),
    }[channel]
    base = row(n, url=url, date=date, site=SITES[channel],
               doc_id=doc_id(channel, normalize_url(url, channel)),
               answers="['답변 본문']" if channel == 'naver_kin' else '')
    base.update(over)
    return base
```

- [ ] **Step 2: 실패하는 테스트 작성** — `test_read.py`에 더한다(기존 테스트는 그대로 통과해야 한다):

```python
@pytest.mark.parametrize('channel,date,meta', [
    ('naver_kin', '2025-12-22', {}),
    ('daum_cafe', '2026-06-02', {'cafe': 'club1', 'cafe_id': 'club1'}),
    ('daum_brunch', '2026-06-06', {}),
])
def test_each_channel_maps_source_date_and_meta(tmp_path, salt, channel, date, meta):
    path = write_csv(tmp_path / 'a.csv', [channel_row(channel, 1)])
    source = read.open_source(path)
    result = read.scan(source)
    assert result.done == 1 and result.channels == {channel: 1}
    [record] = list(read.iter_records(source, 'now'))
    doc = record.doc
    assert doc['source'] == channel and doc['date'] == date
    assert doc['src_meta'] == {**meta, 'imported': True}
    assert doc['doc_id'] == channel_row(channel, 1)['doc_id']
    assert '답변' not in json.dumps(doc, ensure_ascii=False)       # answers never stored
    assert '닉1' not in json.dumps(doc, ensure_ascii=False)        # nicknames never stored
    assert doc['author_hash'] == author_hash(channel, '닉1')


def test_mixed_channels_in_one_file(tmp_path, salt):
    rows = [channel_row(c, i) for i, c in enumerate(read.CHANNEL_ORDER)]
    result = read.scan(read.open_source(write_csv(tmp_path / 'a.csv', rows)))
    assert result.channels == {c: 1 for c in read.CHANNEL_ORDER}


def test_wrong_doc_id_for_channel_is_rejected(tmp_path, salt):
    bad = channel_row('daum_cafe', 1, doc_id='dc_' + '0' * 16)
    with pytest.raises(read.ImportError_, match='doc_id'):
        read.scan(read.open_source(write_csv(tmp_path / 'a.csv', [bad])))


def test_unknown_site_still_skipped(tmp_path, salt):
    result = read.scan(read.open_source(write_csv(tmp_path / 'a.csv', [row(1, site='티스토리')])))
    assert result.done == 0 and result.skipped['unknown_site'] == 1


@pytest.mark.parametrize('value,expected', [
    ('2026.03.30. 22:02', '2026-03-30'), ('2025.12.22', '2025-12-22'),
    ('2026-06-06T03:46:43+09:00', '2026-06-06'), ('2026-06-06', '2026-06-06'),
    ('26.06.02 11:32', '2026-06-02'), ('', ''), ('26.13.02 11:32', ''), ('어제', ''), ('2026.6.1', '2026-06-01'),
])
def test_dates(value, expected):
    assert read._date(value) == expected


def test_duplicate_doc_id_across_files_is_rejected(tmp_path, salt):
    a = read.open_source(write_csv(tmp_path / 'a.csv', [channel_row('naver_kin', 1)]))
    b = read.open_source(write_csv(tmp_path / 'b.csv', [channel_row('naver_kin', 1, title='다른 제목')]))
    seen = set()
    read.scan(a, seen)
    with pytest.raises(read.ImportError_, match='중복'):
        read.scan(b, seen)


def test_bundle_sha_is_order_independent_and_single_file_is_unchanged(tmp_path, salt):
    a = read.open_source(write_csv(tmp_path / 'a.csv', [channel_row('naver_cafe', 1)]))
    b = read.open_source(write_csv(tmp_path / 'b.csv', [channel_row('daum_brunch', 2)]))
    assert read.bundle_sha([a]) == a.sha256
    assert read.bundle_sha([a, b]) == read.bundle_sha([b, a]) != a.sha256


def test_same_file_twice_is_rejected(tmp_path, salt):
    path = write_csv(tmp_path / 'a.csv', [channel_row('naver_cafe', 1)])
    with pytest.raises(read.ImportError_, match='두 번'):
        read.open_sources([path, path])


def test_merge_scans_sums_and_keeps_keyword_order(tmp_path, salt):
    a = read.scan(read.open_source(write_csv(tmp_path / 'a.csv', [channel_row('naver_cafe', 1, keyword='가')])))
    b = read.scan(read.open_source(write_csv(tmp_path / 'b.csv', [channel_row('daum_cafe', 2, keyword='나'),
                                                                   channel_row('daum_cafe', 3, keyword='가')])))
    merged = read.merge_scans([a, b])
    assert (merged.total, merged.done) == (3, 3)
    assert merged.keywords == ['가', '나']
    assert merged.channels == {'naver_cafe': 1, 'daum_cafe': 2}
```

(필요한 import: `json`, `from app.crawl.hashing import author_hash`, `from tests.importer.conftest import channel_row` 등 기존 테스트 파일의 import 방식을 따른다.)

- [ ] **Step 3: 실패 확인** — Run: `env -u VOYAGE_API_KEY backend/.venv/bin/python -m pytest backend/tests/importer/test_read.py -q` → Expected: 새 테스트 FAIL.

- [ ] **Step 4: 구현**
  - `CHANNELS`, `CHANNEL_ORDER` 정의. `_channel(row) -> str | None = CHANNELS.get(row['site'])`.
  - `_problems(row, channel)`: `make_doc_id(channel, normalize_url(row['url'], channel))`.
  - `scan(source, seen=None)`: `seen = set() if seen is None else seen`; 같은 집합을 쓴다. 채널이 없으면 `unknown_site`. done 행마다 `channels[channel] += 1`. 중복 문구는 지금과 같은 `'{line}행 {doc_id}: 중복된 doc_id'`.
  - `_date(value)`: 설계 3장의 세 형식. 정규식은 형식마다 따로 두고 처음 맞는 것을 쓴다. 월·일 범위 밖이면 `''`.

```python
_DATE_FORMATS = (
    (re.compile(r'\s*(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})'), 0),         # 2026.03.30. 22:02 · 2025.12.22
    (re.compile(r'\s*(\d{4})-(\d{2})-(\d{2})(?:[T ]|$)'), 0),           # 2026-06-06T03:46:43+09:00
    (re.compile(r'\s*(\d{2})\.(\d{2})\.(\d{2})\s+\d{1,2}:\d{2}\s*$'), 2000),  # 26.06.02 11:32
)


def _date(value):
    for pattern, century in _DATE_FORMATS:
        match = pattern.match(value or '')
        if match:
            year, month, day = int(match[1]) + century, int(match[2]), int(match[3])
            return f'{year:04d}-{month:02d}-{day:02d}' if 1 <= month <= 12 and 1 <= day <= 31 else ''
    return ''
```

  - `_doc(row, crawled_at, channel)`: `url = normalize_url(row['url'], channel)`; `src_meta = dict(imported=True)`에 네이버 카페·다음 카페만 `cafe`/`cafe_id` = 경로 첫 조각; `source=channel`; `author_hash(channel, nickname)`.
  - `iter_records`: `channel = _channel(row)`; 없거나 done이 아니면 건너뛴다.
  - `open_sources(paths)`: 각 `open_source`; sha256이 겹치면 `ImportError_(f'같은 파일이 두 번 들어왔습니다: {name}')`.
  - `bundle_sha(sources)`, `merge_scans(scans)` (키워드는 `dict.fromkeys`로 처음 순서 유지, `skipped`·`channels`는 Counter 합).

- [ ] **Step 5: 통과 확인** — Run: `env -u VOYAGE_API_KEY backend/.venv/bin/python -m pytest backend/tests/importer -q` → Expected: PASS(기존 `test_read.py`·`test_steps.py`·`test_main.py` 포함. `test_steps.py`가 `read.SOURCE` 등을 쓰면 이 태스크에서 함께 고친다).

- [ ] **Step 6: 실데이터 읽기 확인(컨트롤러, 디스크 쓰지 않음)** — 사용자 파일 4개에 대해 `scan`만 돌려 문제 0건과 행 수를 확인한다(QA-E2E-002에서 기록).

### Task T3: 여러 파일 가져오기 단계와 명령 (`steps.py`, `__main__.py`, `dcxctl`)

**Files:**
- Modify: `backend/app/importer/steps.py`, `backend/app/importer/__main__.py`, `ops/macmini/dcxctl`, `ops/macmini/README.md`
- Modify: `backend/tests/importer/test_steps.py`, `backend/tests/importer/test_main.py`, `backend/tests/ops/test_dcxctl.py`

**Interfaces:**
- Consumes: T2의 `open_sources`, `bundle_sha`, `scan(source, seen)`, `merge_scans`, `CHANNEL_ORDER`, `Scan.channels`.
- Produces: `run_import(paths: str | Path | Sequence[str | Path], *, sid=None, log=print, poll_s=10, sleep=time.sleep) -> dict`; `default_sid(sources: Sequence[Source]) -> str`; `create_session(sid, sources, result)`; `register_collection(sid, sources, channels)`; `insert_labels(sid, sources)`.

- [ ] **Step 1: 실패하는 테스트 작성** — `test_steps.py`에 기존 흐름 테스트의 설정(가짜 `runner.start`, `embed_backend='fake'`, 임시 `local_data_dir`)을 재사용해 더한다:
  - `test_multi_file_import_creates_one_project_with_all_channels`: 채널별 CSV 4개(각 2~3행, 하나는 zip)를 `run_import([...])` → `sid == 'imp-' + read.bundle_sha(sources)[:12]`; `projectContext.channels == list(CHANNEL_ORDER)`; `manifest.channels` 같음; 문서 shard의 `source` 집합이 4개; 큐 URL `source`가 문서와 같음; `labels.sqlite.final` 행 수 = done 합; `imported.files` 이름·sha256이 입력 순서; 4단계 `done`, 5단계 `exportRef` 있음.
  - `test_channels_only_include_present_channels`: 지식인·브런치 두 파일 → `channels == ['naver_kin', 'daum_brunch']`.
  - `test_resume_with_files_in_other_order`: 첫 실행을 3단계 직전에 멈춘 뒤(기존 이어하기 테스트 방식) 파일 순서를 바꿔 다시 실행 → 같은 sid로 이어서 끝남, 수집본 재등록 없음.
  - `test_other_bundle_with_same_sid_is_rejected`: 같은 `--sid`에 다른 묶음 → `ImportError_('…다른 파일로 만든 프로젝트…')`.
  - `test_cross_file_duplicate_writes_nothing`: 파일 사이 doc_id 중복 → `ImportError_`, `sessions/`·`crawl/`에 아무것도 없음.
  - `test_single_file_import_unchanged`: 기존 단일 파일 테스트가 그대로 통과(새 assert: `imported.sha256 == source.sha256`, `imported.file == source.name`, `imported.files == [{'name':…, 'sha256':…}]`).
  - `test_main.py`: `main(['a.csv', 'b.zip', '--sid', 'imp-x'])`가 `run_import(['a.csv','b.zip'], sid='imp-x', …)`를 부른다; 파일 없이 부르면 argparse 오류(2).
  - `test_dcxctl.py`: 상대 경로 두 개와 `--sid ID`를 주면 python에 절대 경로 두 개와 `--sid ID`가 넘어간다(기존 가짜 release·python 방식); `--sid`만 있고 값이 없으면 2와 사용법; 파일 없이 부르면 2(기존).

- [ ] **Step 2: 실패 확인** — Run: `env -u VOYAGE_API_KEY DCX_BASH=/bin/bash TAR_READER_OPTIONS=read_concatenated_archives backend/.venv/bin/python -m pytest backend/tests/importer backend/tests/ops/test_dcxctl.py -q` → Expected: 새 테스트 FAIL.

- [ ] **Step 3: `steps.py` 구현**
  - `run_import`: `paths = [paths] if isinstance(paths, (str, Path)) else list(paths)`; 비어 있으면 `ImportError_('가져올 파일이 없습니다')`. `sources = open_sources(paths)`. 파일마다 `가져오기: {경로 이름} → {CSV 이름} (sha256 앞 12자)`와 `검증 …` 줄을 찍는다. `seen = set()`을 모든 `scan`에 넘기고 `result = merge_scans(scans)`. `bundle = bundle_sha(sources)`. 파일이 여럿이면 `묶음 {n}개 파일 → sha256 {bundle[:12]}` 줄을 더 찍는다.
  - `default_sid(sources)`: `'imp-' + bundle_sha(sources)[:12]`.
  - `_context(channels)`: `channels=list(channels)`.
  - 채널 목록: `channels = [c for c in CHANNEL_ORDER if result.channels.get(c)]`. done이 하나도 없으면 `ImportError_('가져올 done 행이 없습니다')`(기존 동작이 다르면 기존 동작을 유지하고 이 문장은 쓰지 않는다).
  - `create_session(sid, sources, result, channels)`: `imported = dict(sha256=bundle, files=[dict(name=s.name, sha256=s.sha256) for s in sources], steps={}, counts={})`, 파일 하나면 `file=sources[0].name`도.
  - `register_collection(sid, sources, channels)`: `manifest` `channels=channels`, `imported=dict(sha256=bundle, files=[…])`. 모든 소스를 차례로 `iter_records`. 큐 URL `source=record.doc['source']`.
  - `insert_labels(sid, sources)`: 소스마다 `votes = json.dumps({'imported': dict(file=s.name, sha256=s.sha256[:12])})`; 나머지(준비된 doc_id 집합, 배치, 버전 고정, `_mark`)는 그대로.
  - `_run_locked`·완료 판정: 비교 대상을 `bundle`로 바꾼다. 로그 `[1/5] 프로젝트 {sid} 만듦 (채널: {한글 이름 · …})`(이름은 `app.context.labels.LABELS['channels']`).
- [ ] **Step 4: `__main__.py`** — `parser.add_argument('paths', nargs='+', help='결과 CSV 또는 그것을 담은 zip (여러 개면 한 프로젝트로 합칩니다)')`; `steps.run_import(args.paths, …)`. 독스트링 `python -m app.importer <zip|csv>... [--sid ID]`.
- [ ] **Step 5: `dcxctl`** — `import-labels)` 분기에서 `file="$1"; shift` 대신:

```bash
        args=()
        while [[ $# -gt 0 ]]; do
            case "$1" in
                --sid) [[ $# -ge 2 ]] || { echo '사용법: dcxctl import-labels <zip 또는 csv>... [--sid ID]' >&2; exit 2; }
                       args+=("$1" "$2"); shift 2 ;;
                -*) args+=("$1"); shift ;;
                /*) args+=("$1"); shift ;;
                *) args+=("$PWD/$1"); shift ;;
            esac
        done
```

  그리고 python 인자 끝을 `"$APP_ROOT" "$backend" "${args[@]}"`로 바꾼다(첫 검사 `[[ $# -ge 1 ]]`이 있으므로 `args`는 비지 않는다). 사용법 문구 두 곳을 `<zip 또는 csv>...`로 바꾼다.
- [ ] **Step 6: README** — `ops/macmini/README.md`의 `import-labels` 절에 여러 파일 예시와 "파일 순서는 상관없고, 같은 묶음으로 다시 실행하면 이어서 합니다" 한 줄.
- [ ] **Step 7: 통과 확인** — Step 2 명령 → PASS. 이어서 전체: `env -u VOYAGE_API_KEY DCX_BASH=/bin/bash TAR_READER_OPTIONS=read_concatenated_archives backend/.venv/bin/python -m pytest backend/tests -q`.

## 리뷰 체크리스트 (태스크별 리뷰어에게 전달)

- 파일 하나 가져오기의 sid·세션·수집본·라벨이 앞선 실행과 같은가(묶음 해시 = 파일 해시).
- 새 채널이 크롤러 레지스트리·`available_sources()`에 들어가지 않았는가. 0단계·크롤링 설정의 새 프로젝트 선택지에 나오지 않는가.
- 행마다 그 채널로 `doc_id`·URL·`author_hash`·`source`를 만드는가(네이버 카페 규칙을 다른 채널에 쓰지 않는가).
- 파일 사이 `doc_id` 중복이 쓰기 전에 잡히는가. 검증 실패 시 `sessions/`·`crawl/`에 아무것도 생기지 않는가.
- `answers`, `comment_nicknames`, 원문 닉네임이 어디에도 저장되지 않는가.
- 메모리: 파일 전체를 올리지 않고 스트리밍하는가(URL 5,000건 배치, 준비된 doc_id 집합만).
- 날짜 해석이 형식별로 엄격한가(`26.06.02`가 `0026`이나 `2026-06-02` 이외로 해석되지 않는가).
- `dcxctl`이 bash 3.2(`set -u`)에서 빈 배열을 전개하지 않는가, 공백 있는 파일 이름(`네이버 카페.zip`)을 그대로 넘기는가.

## 되돌리기

- 코드: T3 → T2 → T1 역순 revert. 서버에서 여러 채널 가져오기를 실행한 뒤 T1을 되돌리면 그 프로젝트의 문서·0단계 검증이 실패하므로, 그 경우 프로젝트 폴더(`sessions/`, `crawl/`, `derived/`, `classified/`, `work/`의 `imp-…`)를 먼저 지운다.
- 데이터: 앞선 실행과 같다.
