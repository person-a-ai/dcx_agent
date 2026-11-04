import hashlib
import json
import re

import pytest

from app.crawl.hashing import author_hash
from app.crawl.urls import normalize_url
from app.importer import read
from tests.importer.conftest import COLUMNS, SITES, channel_row, row, write_csv, write_zip


def test_scan_counts_done_skipped_and_other_site(tmp_path, salt):
    rows = [row(1), row(2), row(3, status='skipped', error='short_body', evidence_level=''),
            row(4, site='티스토리')]
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


@pytest.mark.parametrize('metadata_paths', [
    ['__MACOSX/dir/._x_full.csv', '__MACOSX/dir/._x_full_probs.csv', '__MACOSX/._dir'],
    ['dir/__MACOSX/x_full.csv'],
    ['dir/._x_full.csv'],
])
def test_zip_ignores_macos_metadata(tmp_path, metadata_paths):
    rows = [channel_row('daum_cafe', 1), channel_row('daum_cafe', 2)]
    csv_path = write_csv(tmp_path / 'r.csv', rows)
    members = {'dir/x_full.csv': csv_path.read_bytes(), 'dir/x_full_probs.csv': b'doc_id\n'}
    members.update({name: b'metadata' for name in metadata_paths})
    archive = write_zip(tmp_path / '다음 카페.zip', members)
    source = read.open_source(archive)
    assert source.name == 'x_full.csv'
    assert source.sha256 == read.open_source(csv_path).sha256
    assert read.scan(source).done == len(rows)


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


@pytest.mark.parametrize('channel', SITES)
def test_records_do_not_keep_nicknames_or_answers(tmp_path, salt, channel):
    rows = [channel_row(channel, 1, author_nickname='비밀닉네임', comment_nicknames='댓글닉A | 댓글닉B',
                        answers="['지식인 답변']")]
    record = next(read.iter_records(read.open_source(write_csv(tmp_path / 'r.csv', rows)), 'now'))
    text = json.dumps(record.doc, ensure_ascii=False)
    for secret in ('비밀닉네임', '댓글닉A', '댓글닉B', '지식인 답변'):
        assert secret not in text
    assert 'answers' not in record.doc
    assert re.fullmatch(r'[0-9a-f]{16}', record.doc['author_hash'])


def test_blank_keyword_becomes_dot(tmp_path, salt):
    source = read.open_source(write_csv(tmp_path / 'r.csv', [row(1, keyword='  ')]))
    assert read.scan(source).keywords == ['.']
    assert next(read.iter_records(source, 'now')).doc['kw'] == '.'


@pytest.mark.parametrize('over, message', [
    (dict(rule_version='r2'), '판정 버전'),
    (dict(reason_code='invalid'), 'reason_code'),
    (dict(url='https://cafe.naver.com:invalid/club1/1001'), 'URL'),
])
def test_scan_rejects_more_invalid_values(tmp_path, over, message):
    source = read.open_source(write_csv(tmp_path / 'r.csv', [row(1, **over)]))
    with pytest.raises(read.ImportError_, match=message):
        read.scan(source)


def test_source_opens_reusable_text_stream_and_hashes_original_bytes(tmp_path):
    import hashlib

    path = write_csv(tmp_path / 'r.csv', [row(1)])
    source = read.open_source(path)
    assert source.sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
    for _ in range(2):
        with source.open() as stream:
            assert stream.read().startswith('date,keyword,')
    assert stream.closed


def test_scan_accepts_contract_text_source(tmp_path):
    import io

    path = write_csv(tmp_path / 'r.csv', [row(1)])
    text = path.read_text(encoding='utf-8-sig')
    source = read.Source('memory.csv', '', lambda: io.StringIO(text))
    assert read.scan(source).done == 1


@pytest.mark.parametrize('filename, data', [('bad.zip', b'not a zip'), ('bad.csv', b'\xff')])
def test_unreadable_input_has_user_facing_error(tmp_path, filename, data):
    path = tmp_path / filename
    path.write_bytes(data)
    with pytest.raises(read.ImportError_, match=filename):
        read.scan(read.open_source(path))


def test_short_csv_row_has_user_facing_error(tmp_path):
    path = write_csv(tmp_path / 'short.csv', [])
    with path.open('a') as stream:
        stream.write('2026.03.30.,keyword\n')
    with pytest.raises(read.ImportError_, match='short.csv.*2행'):
        read.scan(read.open_source(path))


def test_records_skip_other_sites(tmp_path, salt):
    path = write_csv(tmp_path / 'r.csv', [row(1, site='티스토리'), row(2)])
    records = list(read.iter_records(read.open_source(path), 'now'))
    assert [record.doc['doc_id'] for record in records] == [row(2)['doc_id']]


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
    assert doc['url'] == normalize_url(channel_row(channel, 1)['url'], channel)
    assert '답변' not in json.dumps(doc, ensure_ascii=False)
    assert '닉1' not in json.dumps(doc, ensure_ascii=False)
    assert doc['author_hash'] == author_hash(channel, '닉1')


def test_mixed_channels_in_one_file(tmp_path, salt):
    assert read.CHANNEL_ORDER == ('naver_cafe', 'naver_kin', 'daum_cafe', 'daum_brunch')
    rows = [channel_row(c, i) for i, c in enumerate(read.CHANNEL_ORDER)]
    source = read.open_source(write_csv(tmp_path / 'a.csv', rows))
    result = read.scan(source)
    assert result.channels == {c: 1 for c in read.CHANNEL_ORDER}
    assert [record.doc['source'] for record in read.iter_records(source, 'now')] == list(read.CHANNEL_ORDER)


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
    ('26.06.02 11:32', '2026-06-02'), ('', ''), ('26.13.02 11:32', ''), ('어제', ''),
    ('2026.6.1', '2026-06-01'), ('2026.13.02', ''), ('2026-06-32', ''), ('26.00.02 11:32', ''),
    ('2026.06.021', ''), ('2026.06.02garbage', ''),
    ('2026.06.02 garbage', ''), ('2026.06.02.garbage', ''), ('2026.06.02.123', ''),
    ('2026-06-06 garbage', ''), ('2026-06-06T03:46:43+09:00x', ''),
    ('2026.06.02.', '2026-06-02'), ('2026-06-06T03:46:43Z', '2026-06-06'),
    ('2026-06-06 03:46', '2026-06-06'),
    ('2026. 6. 2. 03:46:43  ', '2026-06-02'), ('2026.06.02 03:46', '2026-06-02'),
    ('2026-06-06T03:46:43.123+0900  ', '2026-06-06'),
    ('2026-06-06T03:46-09:00', '2026-06-06'), ('2026-06-06  ', '2026-06-06'),
    ('2026.06.02. 03:46x', ''), ('2026-06-06T', ''), ('2026-06-06T03:46.123', ''),
])
def test_dates(value, expected):
    assert read._date(value) == expected


def test_duplicate_doc_id_across_files_is_rejected(tmp_path, salt):
    a = read.open_source(write_csv(tmp_path / 'a.csv', [channel_row('naver_kin', 1)]))
    b = read.open_source(write_csv(tmp_path / 'b.csv', [channel_row('naver_kin', 1, title='다른 제목')]))
    seen = set()
    read.scan(a, seen)
    assert seen == {channel_row('naver_kin', 1)['doc_id']}
    with pytest.raises(read.ImportError_, match='중복'):
        read.scan(b, seen)


def test_bundle_sha_is_order_independent_and_single_file_is_unchanged(tmp_path, salt):
    a = read.open_source(write_csv(tmp_path / 'a.csv', [channel_row('naver_cafe', 1)]))
    b = read.open_source(write_csv(tmp_path / 'b.csv', [channel_row('daum_brunch', 2)]))
    expected = hashlib.sha256('\n'.join(sorted([a.sha256, b.sha256])).encode('utf-8')).hexdigest()
    assert read.bundle_sha([a]) == a.sha256
    assert read.bundle_sha([a, b]) == read.bundle_sha([b, a]) == expected != a.sha256


def test_same_file_twice_is_rejected(tmp_path, salt):
    path = write_csv(tmp_path / 'a.csv', [channel_row('naver_cafe', 1)])
    with pytest.raises(read.ImportError_, match='두 번'):
        read.open_sources([path, path])


def test_same_csv_in_zip_is_rejected(tmp_path):
    path = write_csv(tmp_path / 'a.csv', [row(1)])
    archive = write_zip(tmp_path / 'a.zip', {'result.csv': path.read_bytes()})
    with pytest.raises(read.ImportError_, match='두 번.*result.csv'):
        read.open_sources([path, archive])


def test_open_sources_accepts_iterable_and_preserves_order(tmp_path):
    paths = [write_csv(tmp_path / f'{n}.csv', [row(n)]) for n in (2, 1)]
    sources = read.open_sources(str(path) for path in paths)
    assert [source.name for source in sources] == ['2.csv', '1.csv']
    assert [read.scan(source).done for source in sources] == [1, 1]


def test_merge_scans_sums_and_keeps_keyword_order(tmp_path, salt):
    a = read.scan(read.open_source(write_csv(tmp_path / 'a.csv', [
        channel_row('naver_cafe', 1, keyword='가'), row(4, status='skipped')])))
    b = read.scan(read.open_source(write_csv(tmp_path / 'b.csv', [
        channel_row('daum_cafe', 2, keyword='나'), channel_row('daum_cafe', 3, keyword='가'),
        channel_row('daum_cafe', 5, status='skipped'), row(6, site='티스토리')])))
    merged = read.merge_scans([a, b])
    assert (merged.total, merged.done) == (6, 3)
    assert merged.keywords == ['가', '나']
    assert merged.channels == {'naver_cafe': 1, 'daum_cafe': 2}
    assert merged.skipped == {'skipped': 2, 'unknown_site': 1}
    assert a.skipped == {'skipped': 1} and a.keywords == ['가']
