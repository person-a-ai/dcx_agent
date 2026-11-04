import hashlib

import pytest

from app.context.labels import LABELS
from app.context.models import Channel, ProjectContext
from app.crawl.adapters import available_sources
from app.crawl.schema import Doc
from app.crawl.urls import doc_id, normalize_url


def sha16(text):
    return hashlib.sha1(text.encode()).hexdigest()[:16]


def test_daum_cafe_drops_query_and_uses_dc_prefix():
    url = 'https://cafe.daum.net/chonanmam/8gn1/1469?q=%EA%B1%B4%EA%B0%95%20%2BPT&re=1'
    canonical = 'https://cafe.daum.net/chonanmam/8gn1/1469'
    assert normalize_url(url, 'daum_cafe') == canonical
    assert doc_id('daum_cafe', canonical) == 'dc_' + sha16(canonical)
    assert normalize_url('http://m.cafe.daum.net/a/b/1/?x=1', 'daum_cafe') == 'https://cafe.daum.net/a/b/1'


def test_daum_brunch_uses_db_prefix_with_common_rules():
    url = 'https://brunch.co.kr/@8c909cfe8a424c2/159'
    assert normalize_url(url, 'daum_brunch') == url
    assert normalize_url(url + '/?utm_source=test&keep=1#section', 'daum_brunch') == url + '?keep=1'
    assert doc_id('daum_brunch', url) == 'db_' + sha16(url)


@pytest.mark.parametrize('source', ['daum_cafe', 'daum_brunch'])
def test_import_only_channels_are_valid_but_not_crawlable(source):
    assert Channel(source).value == source
    assert source in LABELS['channels']
    assert source not in available_sources()
    doc = Doc(
        doc_id='dc_0', source=source, src_meta={}, kw='k', kw_axis='', kw_sub='', kw_hits=['k'],
        title='', body='b', comments=[], date='', url='https://x', fetch_level='full',
        access='public', snippet='b', author_hash='', crawled_at='2026-11-04T00:00:00Z',
    )
    assert doc.source == source
    context = ProjectContext(
        bk='test', oneLiner='test', researchQuestion={'text': 'test'},
        projectType={'choice': 'new'}, taskMode='explore', constraints=[],
        channels=[source], productCategory={'l1': 'test', 'source': 'user'},
    )
    assert context.channels == [Channel(source)]


def test_existing_channels_unchanged():
    assert normalize_url('https://cafe.naver.com/ca-fe/club/1?art=x', 'naver_cafe') == 'https://cafe.naver.com/club/1'
    assert doc_id('naver_kin', 'u').startswith('kn_')
