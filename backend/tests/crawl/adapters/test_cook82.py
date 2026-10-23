import json
import re
from dataclasses import asdict
from hashlib import sha256
from html import unescape
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlsplit

import httpx
import pytest
from selectolax.parser import HTMLParser

from app.config import settings
from app.crawl.adapters.base import AdapterBlocked, ListItem
from app.crawl.adapters.cook82 import Cook82Adapter, SEARCH_SCOPE
from app.crawl.hashing import author_hash

FIXTURES = Path(__file__).parents[2] / 'fixtures' / 'http' / 'cook82'
FIXTURE_NAMES = ['manifest.json', 'list-1.html', 'list-empty.html', 'list-changed.html',
                 'article-1.html', 'article-2.html', 'article-3.html']


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def sleep(self, duration):
        self.now += duration


@pytest.fixture(autouse=True)
def salt(tmp_path, monkeypatch):
    path = tmp_path / 'salt'
    path.write_text('b' * 64)
    monkeypatch.setattr(settings, 'author_salt_path', str(path))


@pytest.fixture
def make_adapter():
    clients = []

    def make(status=200, transform=None):
        manifest = json.loads((FIXTURES / 'manifest.json').read_text())
        seen = []

        def respond(request):
            seen.append(str(request.url))
            query = parse_qs(request.url.query.decode())
            for capture in manifest['requests']:
                target = urlsplit(capture['url'])
                if target.path == request.url.path and query == parse_qs(target.query):
                    content = (FIXTURES / capture['file']).read_bytes()
                    if transform:
                        content = transform(content)
                    return httpx.Response(status, content=content)
            raise AssertionError(f'Unrecorded request: {request.url}')

        clock = Clock()
        client = httpx.Client(transport=httpx.MockTransport(respond))
        clients.append(client)
        return Cook82Adapter(client, clock=clock, sleep=clock.sleep), manifest, seen

    yield make
    for client in clients:
        client.close()


def test_list_skips_notices_and_normalizes_urls(make_adapter):
    adapter, manifest, seen = make_adapter()
    page = adapter.list_page(manifest['keyword'], None)
    assert len(page.items) == manifest['list_count'] == 25
    assert len({item.url for item in page.items}) == 25  # photolink is not a second result
    assert all(item.url.startswith('https://www.82cook.com/entiz/read.php?bn=15&num=')
               for item in page.items)
    assert not set(manifest['notice_nums']) & {item.src_meta['num'] for item in page.items}
    assert [item.date for item in page.items] == manifest['list_dates']
    assert page.next_cursor == '2'
    assert SEARCH_SCOPE == '1'
    assert parse_qs(urlsplit(seen[0]).query)['search1'] == ['1']
    assert all(set(item.src_meta) == {'board', 'num', 'comment_count', 'author'} for item in page.items)
    assert all(item.snippet == '' and item.title for item in page.items)
    assert all(isinstance(item.src_meta['comment_count'], int) for item in page.items)


def test_empty_search(make_adapter):
    adapter, manifest, _ = make_adapter()
    page = adapter.list_page(manifest['empty_keyword'], None)
    assert page.items == [] and page.next_cursor is None and page.total_hint == 0


def test_changed_markup_is_a_parse_error_not_an_empty_page(make_adapter):
    adapter, manifest, _ = make_adapter()
    with pytest.raises(ValueError):
        adapter.list_page(manifest['changed_keyword'], None)


def test_changed_fixture_removes_only_non_notice_title_links():
    tree = HTMLParser((FIXTURES / 'list-1.html').read_text())
    for row in tree.css('tbody tr:not(.noticeList)'):
        for link in row.css('td.title a[href*="read.php"]'):
            link.decompose()
    changed = (FIXTURES / 'list-changed.html').read_text()
    assert '\n'.join(line.rstrip() for line in tree.html.splitlines()) + '\n' == changed
    assert '검색결과가 없습니다' not in changed
    assert HTMLParser(changed).css('a.photolink')


def test_no_result_marker_is_required(make_adapter):
    adapter, manifest, _ = make_adapter(transform=lambda _: b'<html><body>changed</body></html>')
    with pytest.raises(ValueError):
        adapter.list_page(manifest['keyword'], None)


def test_last_page_without_later_page_links(make_adapter):
    def transform(content):
        tree = HTMLParser(content.decode())
        for link in tree.css('a[href]'):
            target = urlsplit(link.attributes.get('href') or '')
            if target.path.endswith('enti.php') and 'page' in parse_qs(target.query):
                link.decompose()
        # A script/other endpoint mentioning page=99 must not extend pagination.
        return tree.html.encode() + b'<script>var x="?page=99";</script><a href="read.php?num=1&page=99">x</a>'

    adapter, manifest, _ = make_adapter(transform=transform)
    page = adapter.list_page(manifest['keyword'], None)
    assert len(page.items) == 25 and page.next_cursor is None


@pytest.mark.parametrize('cursor', ['0', '-1', 'invalid', '1.5', ''])
def test_invalid_cursor_is_rejected_before_request(make_adapter, cursor):
    adapter, manifest, seen = make_adapter()
    with pytest.raises(ValueError):
        adapter.list_page(manifest['keyword'], cursor)
    assert seen == []


def test_date_attribute_has_priority_and_text_is_fallback(make_adapter):
    adapter, _, _ = make_adapter()
    tree = HTMLParser('''<table><tbody>
        <tr><td class="title"><a href="read.php?bn=15&num=1">제목</a></td>
        <td class="regdate" title="2026-10-06 20:58:00">99.1.1</td></tr>
        <tr><td class="title"><a href="/entiz/read.php?num=2&bn=15">제목</a></td>
        <td class="regdate">2026.10.05</td></tr></tbody></table>''')
    page = adapter.parse_list(tree, None)
    assert [item.date for item in page.items] == ['2026-10-06', '2026-10-05']
    assert page.items[1].url == 'https://www.82cook.com/entiz/read.php?bn=15&num=2'


@pytest.mark.parametrize('index', [1, 2, 3])
def test_article_body_comments_and_no_ip(make_adapter, index):
    adapter, manifest, _ = make_adapter()
    article = manifest['articles'][index - 1]
    item = ListItem(article['url'], '목록 제목', '', article['date'],
                    {'board': '15', 'num': article['num'], 'comment_count': 999,
                     'author': 'user999', 'ip': '192.0.2.7', 'unexpected': 'sidebar'})
    doc, = adapter.fetch(item)
    assert doc.title == article['title']
    assert doc.body and len(doc.body) <= 80
    assert len(doc.comments) == article['comment_count']
    assert [comment.date for comment in doc.comments] == article['comment_dates']
    assert [comment.author_hash for comment in doc.comments] == [
        author_hash('cook82', name) if name else '' for name in article['comment_authors']]
    assert all(comment.depth == 0 and 0 < len(comment.text) <= 80 for comment in doc.comments)
    assert doc.src_meta == {'board': '15', 'num': article['num'], 'comment_count': len(doc.comments)}
    assert doc.date == item.date and doc.access == 'public' and doc.author_raw == 'user999'
    raw = json.dumps(asdict(doc), ensure_ascii=False, default=lambda value: value.model_dump())
    assert not re.search(IP_PATTERN, raw) and 'xxx' not in raw and 'IP' not in raw
    assert 'sidebar' not in raw
    assert item.src_meta['author'] == 'user999'  # do not mutate queue metadata


def test_detail_derives_ids_without_list_metadata(make_adapter):
    adapter, manifest, _ = make_adapter()
    article = manifest['articles'][0]
    doc, = adapter.fetch(ListItem(article['url'], '', '', '2026-10-06', {}))
    assert doc.src_meta == {'board': '15', 'num': article['num'], 'comment_count': 6}
    assert doc.author_raw is None


@pytest.mark.parametrize('index', [1, 2])
def test_delreple_with_real_content_is_kept(make_adapter, index):
    adapter, manifest, _ = make_adapter()
    article = manifest['articles'][index - 1]
    tree = HTMLParser((FIXTURES / f'article-{index}.html').read_text())
    marked = tree.css_first('ul.reples > li.rp.delReple p')
    expected = ' '.join(marked.text(separator=' ', strip=True).split())
    doc, = adapter.fetch(ListItem(article['url'], '', '', None, {}))
    assert expected in [comment.text for comment in doc.comments]
    assert len(doc.comments) == article['comment_count']


@pytest.mark.parametrize('placeholder', ['삭제된 댓글입니다.', '삭제된 댓글입니다', '작성자가 삭제한 댓글입니다.'])
def test_delreple_deletion_placeholder_is_skipped(make_adapter, placeholder):
    def transform(content):
        tree = HTMLParser(content.decode())
        tree.css_first('li.delReple p').replace_with(f'<p>{placeholder}</p>')
        return tree.html.encode()

    adapter, manifest, _ = make_adapter(transform=transform)
    article = manifest['articles'][0]
    doc, = adapter.fetch(ListItem(article['url'], '', '', None, {}))
    assert len(doc.comments) == article['comment_count'] - 1
    assert all(comment.text != placeholder for comment in doc.comments)


@pytest.mark.parametrize('nickname', ['', ' ', '...', ' ·!? … ', '___', '。。'])
def test_placeholder_nicknames_have_no_author(make_adapter, nickname):
    adapter, _, _ = make_adapter()
    item = ListItem('https://www.82cook.com/entiz/read.php?bn=15&num=1', '', '', None,
                    {'author': nickname})
    tree = HTMLParser(f'''<div id="articleBody">합성 본문입니다.</div><ul class="reples">
        <li class="rp"><h5><strong>{nickname}</strong></h5><p>합성 댓글입니다.</p>
        <div class="repleFunc"><em>'26.10.6 8:58 PM</em><em class="ip">192.0.2.7</em></div>
        </li></ul>''')
    doc = adapter.parse_detail(tree, item)
    assert doc.author_raw is None
    assert doc.comments[0].author_hash == ''
    assert doc.comments[0].date == '2026-10-06'


def test_ip_nodes_are_never_read_as_dates_or_authors(make_adapter):
    adapter, _, _ = make_adapter()
    tree = HTMLParser('''<h4 class="title bbstitle">합성 제목</h4><div id="articleBody">합성 본문</div>
        <div id="writerIP">192.0.2.7</div><table><tr><td class="user_function">sidebar</td></tr></table>
        <ul class="reples"><li class="rp"><h5><strong>user1</strong></h5><p>합성 댓글</p>
        <div class="repleFunc"><em class="ip">'26.10.6 192.0.2.7</em></div></li></ul>''')
    doc = adapter.parse_detail(tree, ListItem('https://www.82cook.com/entiz/read.php?bn=15&num=1', '', '', None, {}))
    assert doc.comments[0].date == ''
    assert doc.comments[0].author_hash == author_hash('cook82', 'user1')
    assert doc.author_raw is None
    assert '192.0.2.7' not in json.dumps(asdict(doc), default=lambda value: value.model_dump())


def test_missing_article_body_is_parse_error(make_adapter):
    adapter, manifest, _ = make_adapter(transform=lambda content: content.replace(b'id="articleBody"', b'id="changedBody"'))
    with pytest.raises(ValueError):
        adapter.fetch(ListItem(manifest['articles'][0]['url'], '', '', None, {}))


@pytest.mark.parametrize('status', [403, 429])
@pytest.mark.parametrize('operation', ['list', 'fetch'])
def test_blocked_response_is_not_retried(make_adapter, status, operation):
    adapter, manifest, seen = make_adapter(status=status)
    with pytest.raises(AdapterBlocked):
        if operation == 'list':
            adapter.list_page(manifest['keyword'], None)
        else:
            adapter.fetch(ListItem(manifest['articles'][0]['url'], '', '', None, {}))
    assert len(seen) == 1


def test_request_spacing_uses_channel_defaults(make_adapter, monkeypatch):
    from app.crawl import channels

    monkeypatch.setitem(channels._DEFAULTS, 'cook82', (1, 1.25))
    adapter, manifest, _ = make_adapter()
    adapter._limiter.rng = lambda: 0.5
    adapter.list_page(manifest['keyword'], None)
    adapter.fetch(ListItem(manifest['articles'][0]['url'], '', '', None, {}))
    assert adapter._limiter.clock() == 1.25


def _decode_fixture(content):
    while True:
        decoded = re.sub(r'\\(?:u([0-9a-fA-F]{4})|x([0-9a-fA-F]{2}))',
                         lambda match: chr(int(match[1] or match[2], 16)),
                         unescape(unquote(content)).replace(r'\/', '/'))
        if decoded == content:
            return content
        content = decoded


IP_PATTERN = r'(?<![\w.])(?:\d{1,3}|[xX*]{1,3})(?:\.(?:\d{1,3}|[xX*]{1,3})){3}(?![\w.])'
# Exact public UI text retained for parser behavior. These are whole-value
# matches, never substrings removed before scanning.
SITE_UI_TEXT = {'공지', '검색결과가 없습니다'}
SYNTHETIC_TEXT = {'...', '0.0.xxx.0', '에어컨', '합성검색결과없음', '합성구조변경'}
DATE_PATTERN = (r"(?:20[0-9]{2}-[0-9]{2}-[0-9]{2}(?: [0-9]{2}:[0-9]{2}:[0-9]{2})?"
                r"|[0-9]{2}\.[0-9]{1,2}\.[0-9]{1,2}"
                r"|'[0-9]{2}\.[0-9]{1,2}\.[0-9]{1,2} [0-9]{1,2}:[0-9]{2} [AP]M)")
SYNTHETIC_PATTERN = r'user[1-9][0-9]*|합성 질문 [1-9][0-9]*|합성 (?:본문|댓글) [1-9][0-9]*입니다\.'
URL_PATTERN = (
    r'(?:https://www\.82cook\.com/entiz/|/entiz/)?'
    r'(?:read\.php\?bn=15&num=[1-9][0-9]{0,6}'
    r'|enti\.php\?bn=15&searchType=search&search1=1'
    r'&keys=(?:에어컨|합성검색결과없음|합성구조변경)&page=[1-9][0-9]*)'
)
HTML_TAGS = {'html', 'head', 'body', 'table', 'tbody', 'tr', 'td', 'a', 'em',
             'h4', 'div', 'p', 'br', 'ul', 'li', 'h5', 'strong'}
CLASS_VALUES = {'noticeList', 'title', 'regdate', 'user_function', 'photolink',
                'title bbstitle', 'reples', 'rp', 'rp delReple', 'repleFunc', 'ip'}
ID_VALUES = {'articleBody', 'writerIP'}
MANIFEST_KEYS = {'keyword', 'empty_keyword', 'changed_keyword', 'requests', 'file',
                 'url', 'list_count', 'notice_nums', 'list_dates', 'articles',
                 'num', 'title', 'date', 'comment_count', 'comment_dates', 'comment_authors'}


def _allowed_fixture_text(value, *, numeric=False):
    return (not value or value in SITE_UI_TEXT | SYNTHETIC_TEXT
            or re.fullmatch(SYNTHETIC_PATTERN, value) is not None
            or (numeric and re.fullmatch(r'[0-9]{1,7}', value) is not None))


# This intentionally accepts a small, lossless HTML language, not browser error
# recovery. match(..., position) below must consume every decoded character.
HTML_TOKEN = re.compile(
    r'(?P<doctype><!DOCTYPE html>)'
    r'|(?P<end></[a-z][a-z0-9]*[ \t\r\n\f]*>)'
    r'|(?P<start><[a-z][a-z0-9]*(?:[ \t\r\n\f]+[a-z][a-z0-9-]*[ \t\r\n\f]*=[ \t\r\n\f]*'
    r'''(?:"[^"<>]*"|'[^'<>]*'))*[ \t\r\n\f]*/?>)'''
    r'|(?P<text>[^<>]+)', re.I | re.ASCII,
)
HTML_ATTRIBUTE = re.compile(r'''([a-z][a-z0-9-]*)\s*=\s*(?:"([^"]*)"|'([^']*)')''', re.I)
# No implied end tags, foster parenting, raw-text elements or optional tags.
INLINE_TAGS = {'a', 'em', 'strong', 'br'}
FLOW_TAGS = HTML_TAGS - {'html', 'head', 'body', 'tbody', 'tr', 'td', 'li'}
CHILD_TAGS = {
    '': FLOW_TAGS | {'html'}, 'html': {'head', 'body'}, 'head': set(),
    'body': FLOW_TAGS, 'div': FLOW_TAGS, 'td': FLOW_TAGS, 'li': FLOW_TAGS,
    'table': {'tbody'}, 'tbody': {'tr'}, 'tr': {'td'}, 'ul': {'li'},
    **{tag: INLINE_TAGS for tag in {'p', 'a', 'em', 'strong', 'h4', 'h5'}},
}
EMAIL_PATTERN = r'[\w.!#$%&\'*+/=?^`{|}~-]+@[\w-]+(?:\.[\w-]+)+'
PHONE_SEPARATOR = r'[\s().\-‐‑‒–—]*'
PHONE_PATTERN = (
    r'(?<!\d)(?:0(?:1[0-9]|2|[3-6][1-5]|70|80|50[2-8]?)'
    r'|(?:\+?82)' + PHONE_SEPARATOR
    + r'(?:\(0\)' + PHONE_SEPARATOR + r')?(?:1[0-9]|2|[3-6][1-5]|70|80|50[2-8]?))'
    + PHONE_SEPARATOR + r'\d{3,4}' + PHONE_SEPARATOR + r'\d{4}(?!\d)'
    + r'|(?<!\d)1[568]\d{2}' + PHONE_SEPARATOR + r'\d{4}(?!\d)'
)


# SHA-256 sentinels derived offline from all six recordings; no raw nicknames.
RECORDED_NICKNAME_HASHES = {
    '04949859e75f1ab9ba49c8d5a45282beddc175882a4d3a54ca3b47bb043d9282',
    '077ab88f373b925034279d3779ee4961e189a5c3c871155f7e3910875c9cee15',
    '0ff116ca83fffc831ba74aa356b3e720483d278e4bc867d77e821d2c34934c96',
    '1303522e0b59179b948c1713105ac8f9d13c62080a743118617fecef799e92e5',
    '1b629e2fcbaae859d7c9b56a669f479cfcf1b39309314f7b7e4e0266875c82fb',
    '1c0ddfd0050938404c354c36d541bada7f72efa79371d4f96a75a9ad0bc11af0',
    '1dbd1db7e2427222fde8d01cd52939eee0d2d1e59a33b446816daf1c9f2712aa',
    '27e52728bf8f93a8e8c88ae1f26126919dcf9f7a0ae315835b15abb95d72f5eb',
    '2b32977be358fc0b0eea9ae5e804dfc3846e5c2baf3c05ea57ccea7a07190586',
    '2be966630e3cf4f17ada1ab7fd9ea89cee27a2654b8391becf4b8f08bc23beef',
    '2e274ebad4675928ad87c90dddc9874a98e0cdc3347c5f72f8a8ac7ba934856c',
    '2f445073d27495657658966e37d9e42e74cd2dbcdc368283199563430e29a142',
    '35688a85f0be1c636cd83847b4bbb23350a19d0c185f3ed7ee86684a01467352',
    '3809df8a2995325a657b00e0ba8986f2644b5a7596680a391fd55b954c97cd6d',
    '3c8977ef7207c8bd64465250e02e8f90d5a97360df96d3d7547793e4af914b0b',
    '3cb39684a0694a1d4447ba64248ca78a926ee271ec0c621ba0e1c11cd3e9f406',
    '4423734e5c9df50547461ab22bed6f21724268b2174004207421b8ec3aeb5f2a',
    '444b15b71bee24501188455d24c11826b6479b567b68245c5fd6f88598a3d459',
    '4641fbad3b128eddb044ad0efc1a4576dc2d29ca090b2dc42093f52a5df66b3c',
    '4b56c91da0e9e901037d0f1ce979dca59e7f699128c70273cb7314a093305687',
    '560c0b0951b6376fef23ddc060508643f4bde1f32a0839cb2fd995890e193a76',
    '591eb94c7f95f27a3032b024ae2fab5dc878d3734133ee02c8e8dc904a71908b',
    '5c67e8578836de397afde0c61cd2ed52f8d02fcacf9d6d08c39d6a2e21f1706d',
    '607bf0b239c83a8ff069bd619c9b47c69471207e74ca9cf68cef274891f544f9',
    '666599febd987f532ea6ab000ee16ee7d5838beed690d2f9b174aab30ce78307',
    '734c4471a0b2049933aa54449d6a9db574a305b60e4256b6225cc2cbaaafdd25',
    '73d7886be321a7a8364afdef92292a5d3db2a249d451b43e71a0d52aeff5918c',
    '7b817cd54fa0af72b6947e16d624c14a85664f1a8cc557bdbbd110feeb3c8854',
    '817dba840b9cf352629cde70cf13d42eea297d822e31c06656470cc5bb8ccbb7',
    '826d351f4fc913a4377c90a658119bc57a5bb231f21ce6f71fef7c262d9b2f97',
    '8294e2876ace53517c65bca5780a814c481308d719329960bca5507a16f29398',
    '83d8c35e7450cb041aabae0596cd7b3b611c8beba65779c8fc829ba27afb1d67',
    '8419dab52ceccac1586e550e184b4feeada24d450a750689f06846c7c4927aa3',
    '9429d8c1a056112b539da33477569cc7a8b64c9c23d1ef6747f0c7b401aaf0e8',
    '98b7fe155d8ec2c0ddf22d9d169503168bdf0f25bd6a43d928327743070e1e64',
    '9a1c609712d2db0e30b8d3b94049fb54defdf0b364f4bdfdad6830c3542ddfe5',
    '9b7ecc6eeb83abf9ade10fe38865df4499be3568dcc507ae2ec3b44989cb0093',
    'a4d62adc40cad7ff917115d386cf08ad5fd00e30bf088580ce28b1d3eeccc04f',
    'a7265fac89d7d46384dc88359b12c8186a9c9b38cd7a8284bbde724d477b55f3',
    'a9eae366b07b7280eaaa4964f6af69fa7e7671256899fd22070c85e02d9cb1f5',
    'ac83269d431edc9dd655e05544dd08a03f82f3c07aba742e6f91664c629a59f0',
    'ad66ac88a7a2a2b3ffc994894a590a37aa9aa3c01cb9b390455f7a4b616e90f6',
    'b547720c866bfcbdf6012f0465e2e2b4684c833cbc4c931c2326deaf6f9effde',
    'b75ba9f82e45cc310fd19cbcc8af428466e4dc7072dbadf6d3239705884710f9',
    'bd7e0731e32f0719c25fc011d0d783de04e8ee847e4820d29d21dd6d6a1e7dc3',
    'c2b5d0f012e6f24e4f758afa96d20a7ea63d8d581ddefe32eef6a618e29e551e',
    'c6223af51d8fc7cc3dd34446f8ad6e6c39fd2be057e99e370941aa113402f3fa',
    'c7f962ec8146f58573e6901283f9a8b3eccea176527052a8988a3d4127e7e9e7',
    'c99406fc3132c80df65d67ff65961732557d3191c9b0597dc48c711a4eb42f91',
    'c9c3abb6e3fb5e1ee73682139284e20a4b59f0ca0f19fd420ac9688d16301646',
    'd110cb250c186f31b2dca9ad027e92025366ec126430d1034439138801c7e5da',
    'd798e80bd2d0c8c8d8bee1499f9869a22f68c8920ca3e23d0e36049f0c5d9d49',
    'f123177dde5fa8f48570e7ee48809bb1a39c3e0d43530d6ddab079fbbff47be4',
    'f1534392279bddbf9d43dde8701cb5be14b82f76ec6607bf8d6ad557f60f304e',
    'f5587d3c3ac433ca2f3de090ab3a8c8c101d969062b052759895d5dd2689c527',
    'f6e0a1e2ac41945a9aa7ff8a8aaa0cebc12a3bcc981a929ad5cf810a090e11ae',
    'f99f6e0c4bae7e26958a2e16ee0a1c17c0add2dbd94c6bfc3ff92a2e8c31c706',
    'fa1e0f95285b4b72f76c8906a259871de649a38fa912f4bafe3713ab87da78e8',
    'fd39882a2b2c0d6456444952c51668d224e682966e814a9c7d9b5b9fd495cc1d',
}
NICKNAME_LENGTHS = (1, 2, 3, 4, 5, 6, 7, 8)


def _identifier_categories(value):
    """Independent deny checks, including values reconstructed across tags."""
    found = []
    if re.search(EMAIL_PATTERN, value):
        found.append('email')
    if re.search(PHONE_PATTERN, value):
        found.append('phone')
    if any(match[0] != '0.0.xxx.0' for match in re.finditer(IP_PATTERN, value)):
        found.append('ip')
    # Recorded nicknames overlap approved UI keywords and dates. Remove only
    # whole approved scaffolding before hashing substrings, never raw names.
    remaining = re.sub(URL_PATTERN, '\0', value)
    remaining = re.sub(DATE_PATTERN, '\0', remaining)
    remaining = re.sub(SYNTHETIC_PATTERN, '\0', remaining)
    for word in SITE_UI_TEXT | SYNTHETIC_TEXT:
        remaining = re.sub(r'(?<!\w)' + re.escape(word) + r'(?!\w)', '\0', remaining)
    for length in NICKNAME_LENGTHS:
        if any(sha256(remaining[start:start + length].encode()).hexdigest()
               in RECORDED_NICKNAME_HASHES
               for start in range(len(remaining) - length + 1)
               if '\0' not in remaining[start:start + length]
               # Numeric recording names collide with counts/ids. Their use
               # as names is rejected by the full author-field allowlist.
               and not remaining[start:start + length].isdecimal()):
            found.append('nickname')
            break
    return found


def _fixture_identifier_violations(content):
    """Validate decoded source tokens and complete fields without DOM repair.

    All diagnostics are categories: never echo a rejected identifier. JSON
    duplicate keys are rejected recursively before constructing dictionaries.
    """
    content = _decode_fixture(content)
    violations = []

    def check_attributes(tag, attrs):
        for name, value in attrs.items():
            allowed = {
                'class': value in CLASS_VALUES,
                'id': value in ID_VALUES,
                'href': tag == 'a' and re.fullmatch(URL_PATTERN, value) is not None,
                'title': tag == 'td' and attrs.get('class') == 'regdate'
                         and re.fullmatch(DATE_PATTERN, value) is not None,
                'data-rn': tag == 'li' and attrs.get('class') in {'rp', 'rp delReple'}
                           and re.fullmatch(r'[1-9][0-9]{0,6}', value) is not None,
            }.get(name, False)
            if not allowed:
                violations.append('attribute')

    def text_of(node):
        return ''.join(child if isinstance(child, str) else text_of(child)
                       for child in node['children'])

    def check_fields(node, parent=None, owned=False):
        tag, attrs = node['tag'], node['attrs']
        parent = parent or {'tag': '', 'attrs': {}}
        value = text_of(node).strip()
        kind = attrs.get('class')
        parent_kind = parent['attrs'].get('class')
        author = (tag == 'td' and kind == 'user_function'
                  or tag == 'strong' and parent['tag'] == 'h5')
        date = (tag == 'td' and kind == 'regdate'
                or tag == 'em' and parent_kind == 'repleFunc' and kind != 'ip')
        # A number's permission comes from its field, never its inline tag.
        count = tag == 'em' and parent['tag'] == 'td' and parent_kind == 'title'
        query = parse_qs(urlsplit(attrs.get('href', '')).query)
        number = (query.get('num') if kind == 'photolink'
                  else query.get('page') if 'enti.php?' in attrs.get('href', '') else None)
        content_field = (tag in {'p', 'h4'} or attrs.get('id') == 'articleBody'
                         or tag == 'a' and parent_kind == 'title')
        if author:
            allowed = re.fullmatch(r'user[1-9][0-9]*|\.\.\.', value) is not None
        elif date:
            allowed = re.fullmatch(DATE_PATTERN, value) is not None
        elif count:
            allowed = re.fullmatch(r'[0-9]{1,7}', value) is not None
        elif number:
            allowed = len(number) == 1 and value == number[0]
        elif content_field:
            # Paragraphs/br may separate several complete synthetic sentences.
            allowed = (_allowed_fixture_text(value)
                       or re.fullmatch(r'(?:\s*합성 (?:본문|댓글) [1-9][0-9]*입니다\.\s*)+',
                                       value) is not None)
        else:
            allowed = owned or _allowed_fixture_text(''.join(
                child for child in node['children'] if isinstance(child, str)).strip())
        if not allowed:
            violations.append('field')
        if author or date or count or number or content_field:
            violations.extend(_identifier_categories(value))
        # Inline fragments inherit ownership, but nested semantic fields still
        # enforce their own rules (e.g. a comment author inside articleBody).
        for child in node['children']:
            if isinstance(child, dict):
                check_fields(child, node, owned or bool(
                    author or date or count or number or content_field))

    def check_html():
        root = {'tag': '', 'attrs': {}, 'children': []}
        stack = [root]
        source_views = [[], []]  # tags -> space; tags -> nothing
        position, doctype_seen = 0, False
        while position < len(content):
            token = HTML_TOKEN.match(content, position)
            if token is None:
                # Do not hand unconsumed syntax to a forgiving HTML parser.
                violations.extend(['markup', 'text'])
                return
            position = token.end()
            raw = token[0]
            if token.lastgroup == 'text':
                if stack[-1]['tag'] in {'html', 'head', 'table', 'tbody', 'tr', 'ul'} and raw.strip():
                    violations.append('structural text')
                stack[-1]['children'].append(raw)
                for view in source_views:
                    view.append(raw)
                continue
            if token.lastgroup == 'doctype':
                if doctype_seen or content[:token.start()].strip():
                    violations.append('doctype')
                doctype_seen = True
                continue
            tag = re.match(r'</?([a-z][a-z0-9]*)', raw, re.I)[1].lower()
            if tag not in HTML_TAGS:
                violations.append('element')
            # Independent cells/rows are separate fields. A hard boundary
            # prevents phone regex whitespace from joining unrelated numbers.
            boundary = '\0' if tag in {'td', 'tr'} else ''
            source_views[0].append(boundary or ' ')
            source_views[1].append(boundary)
            if token.lastgroup == 'end':
                if len(stack) == 1 or stack[-1]['tag'] != tag:
                    violations.append('nesting')
                else:
                    stack.pop()
                continue
            attrs = {}
            for match in HTML_ATTRIBUTE.finditer(raw):
                name, value = match[1].lower(), match[2] if match[2] is not None else match[3]
                if name in attrs:
                    violations.append('duplicate attribute')
                violations.extend(_identifier_categories(value))
                attrs[name] = value
            check_attributes(tag, attrs)
            # Reject structures HTML parsers auto-close or move elsewhere.
            parent = stack[-1]['tag']
            if tag not in CHILD_TAGS.get(parent, set()):
                violations.append('nesting')
            if tag == 'a' and any(node['tag'] == 'a' for node in stack):
                violations.append('nesting')
            if tag in {'html', 'head', 'body'} and any(
                    isinstance(child, dict) and child['tag'] == tag
                    for child in stack[-1]['children']):
                violations.append('duplicate document element')
            if tag == 'head' and any(isinstance(child, dict) and child['tag'] == 'body'
                                     for child in stack[-1]['children']):
                violations.append('document order')
            node = {'tag': tag, 'attrs': attrs, 'children': []}
            stack[-1]['children'].append(node)
            if tag != 'br':
                if raw.endswith('/>'):
                    violations.append('self closing nonvoid')
                stack.append(node)
        if len(stack) != 1:
            violations.append('unclosed element')
        if any(isinstance(child, dict) and child['tag'] == 'html' for child in root['children']):
            if any(child.strip() if isinstance(child, str) else child['tag'] != 'html'
                   for child in root['children']):
                violations.append('outside document')
        for view in source_views:
            violations.extend(_identifier_categories(''.join(view)))
        check_fields(root)

    def unique_json_object(pairs):
        # object_pairs_hook runs for every object, including objects in arrays.
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate manifest key')
            result[key] = value
        return result

    def check_json(value, field=None):
        if isinstance(value, dict):
            for key, child in value.items():
                if key not in MANIFEST_KEYS:
                    violations.append('manifest key')
                check_json(child, key)
        elif isinstance(value, list):
            for child in value:
                check_json(child, field)
        elif type(value) is int:
            if field not in {'list_count', 'comment_count', 'num', 'notice_nums'} or not 0 <= value <= 9999999:
                violations.append('manifest number')
        elif isinstance(value, str):
            violations.extend(_identifier_categories(value))
            if field == 'comment_authors':
                allowed = not value or re.fullmatch(r'user[1-9][0-9]*|\.\.\.', value)
            else:
                allowed = (_allowed_fixture_text(value, numeric=field in {'num', 'notice_nums'})
                           or field in {'date', 'list_dates', 'comment_dates'}
                           and re.fullmatch(DATE_PATTERN, value)
                           or value in FIXTURE_NAMES
                           or re.fullmatch(URL_PATTERN, value))
            if not allowed:
                violations.append('manifest value')
        else:
            violations.append('manifest type')

    if content.lstrip().startswith(('{', '[')):
        try:
            check_json(json.loads(content, object_pairs_hook=unique_json_object))
        except (ValueError, TypeError):
            violations.append('invalid manifest')
    else:
        check_html()
    return violations


@pytest.mark.parametrize('name', FIXTURE_NAMES)
def test_fixture_identifiers_are_synthetic(name):
    assert _fixture_identifier_violations((FIXTURES / name).read_text()) == []


# Invented sentinels only; the checker must reject unknown values without a
# capture-derived denylist, in every node and attribute position.
MUTATIONS = [
    '누출식별자테스트', '192.0.2.7', '1.2.xxx.4', '1.2.***.4',
    'leaked@example.test', '010-2345-6789', '01023456789',
    '<script>{"nickname":"누출식별자테스트"}</script>',
    '<script>{"analytics_user_key":"user1"}</script>',
    '{"display_name":"누출식별자테스트"}',
    '<span title="leaked@example.test">user1</span>',
    '<span data-contact="010-2345-6789">user1</span>',
    '<span class="user1 누출식별자테스트">user1</span>',
    '<span data-user-id="user1">user1</span>',
    '<!-- 누출식별자테스트 -->',
    '<a href="read.php?bn=15&num=1&nickname=user1">user1</a>',
    '<p>합성 본문 1입니다. 누출식별자테스트</p>',
]


def _encode_mutation(value, encoding):
    if encoding == 'raw':
        return value
    if encoding == 'entities':
        return ''.join(f'&#{ord(char)};' for char in value)
    if encoding == 'percent':
        return quote(quote(value, safe=''), safe='')
    if encoding == 'unicode':
        return ''.join(f'\\u{ord(char):04x}' for char in value)
    if encoding == 'hex':
        return ''.join(f'\\x{ord(char):02x}' if ord(char) < 256 else f'\\u{ord(char):04x}' for char in value)
    # Stacked encodings require fixed-point decoding, including escaped slashes.
    return quote(''.join(f'&#{ord(char)};' for char in value.replace('/', r'\/')), safe='')


ENCODINGS = ['raw', 'entities', 'percent', 'unicode', 'hex', 'mixed']
CLOSING_TAG_MUTATIONS = [
    f'<p>user1</p{suffix}>'
    for value in ['invented@example.test', '010-2468-1357', '01024681357']
    for suffix in [f' title="{value}"', f' {value}']
]
SPLIT_PHONE_MUTATIONS = [
    wrapper.format(''.join(f'<em>{part}</em>' for part in parts))
    for parts in [('010246', '81357'), ('010', '2468', '1357'),
                  ('010', '24', '68', '1357')]
    for wrapper in [
        '<table><tbody><tr><td class="user_function">{}</td></tr></tbody></table>',
        '<h5><strong>{}</strong></h5>',
        '<div id="articleBody"><p>{}</p></div>',
        '<h4 class="title bbstitle">{}</h4>',
        '<table><tbody><tr><td>{}</td></tr></tbody></table>',
    ]
]


@pytest.mark.parametrize('mutation', CLOSING_TAG_MUTATIONS + SPLIT_PHONE_MUTATIONS)
@pytest.mark.parametrize('encoding', ENCODINGS)
@pytest.mark.parametrize('fixture', [None, 'list-1.html', 'article-1.html'])
def test_fixture_checker_rejects_dropped_tokens_and_joined_phone(mutation, encoding, fixture):
    if fixture:
        original = (FIXTURES / fixture).read_text()
        assert _fixture_identifier_violations(original) == []
        mutation = original.replace('</body>', mutation + '</body>')
    assert _fixture_identifier_violations(_encode_mutation(mutation, encoding))


@pytest.mark.parametrize('encoding', ENCODINGS)
@pytest.mark.parametrize('markup', [
    '<p>user1</p extra>', '<p>user1</p/>', '<p>user1</ p>',
    '<p>user1</p', '<p>user1</p><', '<p>user1</p>>',
    '<p>user1</p><!---->', '<!--user1-->', '<?user1?>',
    '<!DOCTYPE other><p>user1</p>', '<!DOCTYPE html SYSTEM "user1">',
    '<![CDATA[user1]]>', '<!user1>', '<p/>', '<p>user1',
    '<p>user1</div>', '<p><div>user1</div></p>', '<p>user1<p>user2</p>',
    '<table>user1</table>', '<table><p>user1</p></table>',
    '<a><a>user1</a></a>', '<html><body></body><body></body></html>',
    '<html><body></body><head></head></html>',
    '<html><head></head><body></body></html><p>user1</p>',
    'user1<html><head></head><body></body></html>',
    '<p\u2003id="articleBody">user1</p>', '<p>user1</p\u2003>',
    '<p id=articleBody>user1</p>', '<p id="articleBody" id="articleBody">user1</p>',
])
def test_fixture_checker_requires_complete_lossless_markup(markup, encoding):
    assert _fixture_identifier_violations(_encode_mutation(markup, encoding))


@pytest.mark.parametrize('encoding', ENCODINGS)
@pytest.mark.parametrize('field', [
    '<table><tbody><tr><td class="user_function">{}</td></tr></tbody></table>',
    '<h5><strong>{}</strong></h5>',
])
@pytest.mark.parametrize('value', [
    '공지', '합성 질문 1', '2026-10-06', '', 'user1<em>user2</em>',
    '<em>12</em><em>34</em>', '<em>...</em><em>...</em>',
])
def test_fixture_checker_requires_one_complete_synthetic_author(field, value, encoding):
    assert _fixture_identifier_violations(_encode_mutation(field.format(value), encoding))


@pytest.mark.parametrize('encoding', ENCODINGS)
def test_fixture_checker_keeps_author_rules_inside_content_fields(encoding):
    markup = '<div id="articleBody"><h5><strong>공지</strong></h5></div>'
    assert _fixture_identifier_violations(_encode_mutation(markup, encoding))


@pytest.mark.parametrize('encoding', ENCODINGS)
@pytest.mark.parametrize('value', [
    '01024681357', '011-246-1357', '016 2468 1357', '017.246.1357',
    '018(2468)1357', '019‐2468‐1357', '(02)246-1357', '031-2468-1357',
    '070 2468 1357', '0507-2468-1357', '+82 10 2468 1357',
    '82-2-246-1357', '+82 (0)10-2468-1357', '1588-2468', '1688 1357', '1899.2468',
    'invented@example.test', '192.0.2.7', '1.2.xxx.4', '1.2.***.4',
])
@pytest.mark.parametrize('location', ['text', 'inline', 'attribute'])
def test_fixture_checker_category_safety_net(value, encoding, location):
    category = 'email' if '@' in value else 'ip' if re.fullmatch(IP_PATTERN, value) else 'phone'
    if location == 'attribute':
        markup = f'<p title="{value}">user1</p>'
    elif location == 'inline':
        # Character-level splitting exercises both tag replacement projections.
        markup = '<p>' + ''.join(f'<em>{char}</em>' for char in value) + '</p>'
    else:
        markup = f'<p>{value}</p>'
    assert category in _fixture_identifier_violations(_encode_mutation(markup, encoding))


@pytest.mark.parametrize('encoding', ENCODINGS)
def test_fixture_checker_hash_safety_net_without_recording_plaintext(monkeypatch, encoding):
    invented = '가상닉네임센티널'
    monkeypatch.setitem(globals(), 'RECORDED_NICKNAME_HASHES', {sha256(invented.encode()).hexdigest()})
    monkeypatch.setitem(globals(), 'NICKNAME_LENGTHS', (len(invented),))
    markup = '<p><em>가상닉네임</em><strong>센티널</strong></p>'
    assert 'nickname' in _fixture_identifier_violations(_encode_mutation(markup, encoding))
    assert 'nickname' in _fixture_identifier_violations(
        _encode_mutation(f'<p title="{invented}">user1</p>', encoding))


@pytest.mark.parametrize('encoding', ENCODINGS)
@pytest.mark.parametrize('markup', [
    '<!DOCTYPE html><html><head></head><body><p>user1</p ></body></html>',
    '<h5><strong><em>user</em><em>12</em></strong></h5>',
    '<h5><strong><em>.</em><em>..</em></strong></h5>',
    '<p><em>합성 본문 </em><strong>1</strong>입니다.<br />합성 댓글 2입니다.</p>',
    '<div id="articleBody"><p>합성 본문 1입니다.</p><p>합성 본문 2입니다.</p></div>',
    '<h4 class="title bbstitle"><em>합성 질문 </em><strong>12</strong></h4>',
    '<table><tbody><tr><td class="title"><a href="read.php?bn=15&num=1">'
    '합성 질문 1</a><em><strong>1</strong>2</em></td></tr></tbody></table>',
    '<a href="enti.php?bn=15&searchType=search&search1=1&keys=에어컨&page=2"><em>2</em></a>',
    '<ul class="reples"><li class="rp" data-rn="123"><p>합성 댓글 1입니다.</p></li></ul>',
    # Unrelated count cells would spell a phone if their boundaries were lost.
    '<table><tbody><tr><td class="title"><em>010</em></td>'
    '<td class="title"><em>2468</em></td><td class="title"><em>1357</em></td></tr></tbody></table>',
])
def test_fixture_checker_allows_complete_synthetic_fields(markup, encoding):
    assert _fixture_identifier_violations(_encode_mutation(markup, encoding)) == []


@pytest.mark.parametrize('markup', [
    '<em>123</em>', '<a>123</a>',
    '<table><tbody><tr><td>123</td></tr></tbody></table>',
    '<p>2026-10-06</p>', '<p>123</p>',
    '<a class="photolink" href="read.php?bn=15&num=1">2</a>',
    '<p data-rn="123">user1</p>',
    '{"keyword":123}', '{"title":"123"}',
])
def test_fixture_checker_does_not_grant_numbers_outside_known_fields(markup):
    assert _fixture_identifier_violations(markup)


@pytest.mark.parametrize('mutation', MUTATIONS)
@pytest.mark.parametrize('encoding', ['raw', 'entities', 'percent', 'unicode', 'hex', 'mixed'])
def test_fixture_identifier_checker_rejects_mutations(mutation, encoding):
    assert _fixture_identifier_violations(_encode_mutation(mutation, encoding))


@pytest.mark.parametrize('value', [
    '누출식별자테스트', '192.0.2.7', '1.2.xxx.4', '1.2.***.4',
    'leaked@example.test', '010-2345-6789', '01023456789',
    'user1',  # Even otherwise allowed values must not permit duplicate keys.
])
@pytest.mark.parametrize('wrapper', [
    '{}', '{{"requests": {}}}', '{{"articles": [{{"requests": {}}}]}}',
], ids=['root', 'nested-object', 'nested-array-object'])
@pytest.mark.parametrize('encoding', ['raw', 'entities', 'percent', 'unicode', 'hex', 'mixed'])
def test_fixture_identifier_checker_rejects_duplicate_json_keys(value, wrapper, encoding):
    duplicate = '{"keyword":' + json.dumps(value, ensure_ascii=False) + ',"keyword":"user1"}'
    mutation = wrapper.format(duplicate)
    assert _fixture_identifier_violations(_encode_mutation(mutation, encoding))


@pytest.mark.parametrize('encoding', ['raw', 'entities', 'percent', 'unicode', 'hex', 'mixed'])
def test_fixture_identifier_checker_rejects_duplicate_key_in_real_manifest(encoding):
    content = (FIXTURES / 'manifest.json').read_text()
    assert _fixture_identifier_violations(content) == []
    # Mutate in memory so the committed fixture remains untouched.
    mutation = content.replace('{', '{"keyword":"leaked@example.test",', 1)
    assert _fixture_identifier_violations(_encode_mutation(mutation, encoding))


@pytest.mark.parametrize('value', [
    '누출식별자테스트', '192.0.2.7', '1.2.xxx.4', '1.2.***.4',
    'leaked@example.test', '010-2345-6789', '01023456789',
])
@pytest.mark.parametrize('encoding', ['raw', 'entities', 'percent', 'unicode', 'hex', 'mixed'])
def test_fixture_identifier_checker_scans_cdata(value, encoding):
    mutation = '<p><![CDATA[' + value + ']]></p>'
    assert 'text' in _fixture_identifier_violations(_encode_mutation(mutation, encoding))


@pytest.mark.parametrize('value', ['user19', '...', '0.0.xxx.0', '합성 본문 1입니다.', '합성 질문 1'])
@pytest.mark.parametrize('encoding', ['raw', 'entities', 'percent', 'unicode', 'hex', 'mixed'])
def test_fixture_identifier_checker_allows_synthetic_values(value, encoding):
    assert _fixture_identifier_violations('<p>' + _encode_mutation(value, encoding) + '</p>') == []


@pytest.mark.parametrize('name', FIXTURE_NAMES[1:])
def test_fixtures_contain_only_minimal_parser_markup(name):
    tree = HTMLParser((FIXTURES / name).read_text())
    allowed_tags = {'html', 'head', 'body', 'table', 'tbody', 'tr', 'td', 'a', 'em',
                    'h4', 'div', 'p', 'br', 'ul', 'li', 'h5', 'strong'}
    assert all(node.tag in allowed_tags for node in tree.root.traverse())
    assert all(set(node.attributes) <= {'class', 'id', 'href', 'title'}
               for node in tree.root.traverse())
    if name.startswith('article'):
        assert not tree.css('table, a')
        assert tree.css_first('#writerIP').text(strip=True) == '0.0.xxx.0'
        assert all(node.text(strip=True) == '0.0.xxx.0' for node in tree.css('em.ip'))
    if name == 'list-1.html':
        assert len(tree.css('tr.noticeList')) == 1


def test_only_first_comment_em_can_supply_date(make_adapter):
    adapter, _, _ = make_adapter()
    tree = HTMLParser("""<div id="articleBody">합성 본문</div><ul class="reples">
        <li class="rp"><p>합성 댓글</p><div class="repleFunc">
        <em class="ip">0.0.xxx.0</em><em>'26.10.6 8:58 PM</em>
        </div></li></ul>""")
    item = ListItem('https://www.82cook.com/entiz/read.php?bn=15&num=1', '', '', None, {})
    assert adapter.parse_detail(tree, item).comments[0].date == ''


def test_detail_ignores_surrounding_page_content(make_adapter):
    adapter, manifest, _ = make_adapter()
    article = manifest['articles'][0]
    content = (FIXTURES / 'article-1.html').read_text()
    tree = HTMLParser(content)
    item = ListItem(article['url'], '', '', None, {})
    expected = adapter.parse_detail(tree, item)
    injected = content.replace('<body>', '<body><aside><h4>외부 제목</h4><p>외부 본문</p>'
                               '<li class="rp"><h5><strong>외부 작성자</strong></h5>'
                               '<p>외부 댓글</p></li></aside>')
    assert adapter.parse_detail(HTMLParser(injected), item) == expected
