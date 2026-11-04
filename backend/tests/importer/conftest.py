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
SITES = {'naver_cafe': '네이버카페', 'naver_kin': '네이버지식인',
         'daum_cafe': '다음카페', 'daum_brunch': '다음블로그_브런치'}


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
