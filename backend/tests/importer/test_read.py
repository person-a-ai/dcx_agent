import json
import re

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
    path = write_csv(tmp_path / 'r.csv', [row(1, site='네이버지식인'), row(2)])
    records = list(read.iter_records(read.open_source(path), 'now'))
    assert [record.doc['doc_id'] for record in records] == [row(2)['doc_id']]
