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
