import json
import hashlib
import re
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser as EventHTMLParser
from pathlib import Path
from urllib.parse import quote, unquote

import pytest
from selectolax.parser import HTMLParser

from app.config import settings
from app.crawl.adapters.base import AdapterBlocked, ListItem

FIXTURES = Path(__file__).parents[2] / 'fixtures' / 'http' / 'threads'
FIXTURE_NAMES = ['manifest.json', 'search.html', 'search-empty.html', 'login-wall.html', 'changed-shape.html']


@pytest.fixture(autouse=True)
def salt(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, 'author_salt_path', str(tmp_path / 'salt'))
    # All adapter tests must inject a bridge/provider; never construct a browser.
    def forbidden(*args, **kwargs):
        pytest.fail('adapter tests must inject their render bridge')
    monkeypatch.setattr('app.crawl.render.RenderBridge.__init__', forbidden)


class Bridge:
    def __init__(self, file):
        self.html = (FIXTURES / file).read_text()
        self.urls, self.timeouts = [], []
        self.closed = False

    def fetch_html(self, url, *, timeout_s):
        self.urls.append(url)
        self.timeouts.append(timeout_s)
        return self.html

    def close(self):
        self.closed = True


def threads(file):
    from app.crawl.adapters.threads import ThreadsAdapter, WebSearchProvider
    bridge = Bridge(file)
    return ThreadsAdapter(provider=WebSearchProvider(bridge)), bridge


def test_search_returns_posts_from_embedded_json(monkeypatch):
    monkeypatch.setattr(settings, 'threads_render_timeout_s', 7)
    adapter, bridge = threads('search.html')
    page = adapter.list_page('에어컨', None)
    assert bridge.urls == ['https://www.threads.com/search?q=%EC%97%90%EC%96%B4%EC%BB%A8&serp_type=default']
    assert bridge.timeouts == [7]
    assert len(page.items) == page.total_hint == 19 and page.next_cursor is None
    assert len({i.url for i in page.items}) == len(page.items)
    assert all(i.url == f'https://www.threads.com/@user{n}/post/SYNTH{n:04d}'
               for n, i in enumerate(page.items, 1))
    assert all(i.snippet and i.date and len(i.date) == 10 for i in page.items)
    assert all(set(i.src_meta) == {'post_code', 'like_count', 'reply_count'} for i in page.items)
    assert 'Log in' in bridge.html  # normal results also have the login link


def test_fetch_turns_list_item_into_document_without_network():
    adapter, bridge = threads('search.html')
    item = adapter.list_page('에어컨', None).items[0]
    calls = len(bridge.urls)
    doc, = adapter.fetch(item)
    assert len(bridge.urls) == calls
    assert doc.body == item.snippet and doc.title == '' and doc.access == 'public'
    assert doc.comments == [] and doc.date == item.date
    assert doc.src_meta == item.src_meta and doc.src_meta is not item.src_meta
    assert doc.author_raw == item.url.split('/@', 1)[1].split('/post/', 1)[0]
    adapter.close()
    assert bridge.closed


def test_unparsable_page_is_a_parse_error_not_an_empty_page():
    adapter, _ = threads('changed-shape.html')
    with pytest.raises(ValueError):
        adapter.list_page('에어컨', None)


def test_login_wall_is_blocked():
    adapter, _ = threads('login-wall.html')
    with pytest.raises(AdapterBlocked) as error:
        adapter.list_page('에어컨', None)
    assert error.value.host == 'threads.com'


def test_no_results_is_empty_page():
    adapter, _ = threads('search-empty.html')
    page = adapter.list_page('zxqwvplmn', None)
    assert page.items == [] and page.next_cursor is None and page.total_hint == 0


@pytest.mark.parametrize('marker', ['No results', '검색 결과가 없습니다', '결과 없음'])
def test_no_results_wins_over_login_link(marker):
    adapter, bridge = threads('login-wall.html')
    bridge.html += f'<p>{marker}</p>'
    assert adapter.list_page('에어컨', None).items == []


@pytest.mark.parametrize('cursor', ['2', '', '0'])
def test_cursor_is_rejected(cursor):
    adapter, bridge = threads('search.html')
    with pytest.raises(ValueError):
        adapter.list_page('에어컨', cursor)
    assert bridge.urls == []


def post(**changes):
    return {'code': 'SYNTH0001', 'caption': {'text': '합성 에어컨 본문 1입니다.'},
            'taken_at': 1792418400, 'like_count': 2, 'user': {'username': 'user1'},
            'text_post_app_info': {'direct_reply_count': 1}, **changes}


def markup(payload):
    return '<script type="application/json">' + json.dumps(payload, ensure_ascii=False) + '</script>'


def test_dedupe_across_nested_json_and_scripts():
    from app.crawl.adapters.threads import parse_search
    html = markup({'data': [{'edges': [{'node': {'post': post()}}]}]}) + markup(post())
    html += markup({'data': []}) + '<script type="application/json">invalid</script>'
    assert len(parse_search(html)) == 1


def test_date_from_taken_at_is_kst():
    from app.crawl.adapters.threads import parse_search
    stamp = datetime(2026, 10, 19, 15, 1, tzinfo=timezone.utc).timestamp()
    item, = parse_search(markup(post(taken_at=stamp)))
    assert item.date == '2026-10-20'
    assert item.src_meta == {'post_code': 'SYNTH0001', 'like_count': 2, 'reply_count': 1}
    assert parse_search(markup(post(taken_at=None)))[0].date is None


@pytest.mark.parametrize('changes', [
    {'user': {}}, {'user': {'username': ''}}, {'user': None},
    {'caption': {}}, {'caption': {'text': ''}}, {'caption': None}, {'code': ''},
])
def test_posts_missing_username_or_text_are_skipped(changes):
    from app.crawl.adapters.threads import parse_search
    assert parse_search(markup(post(**changes))) == []


def test_invalid_post_does_not_hide_later_valid_duplicate():
    from app.crawl.adapters.threads import parse_search
    assert len(parse_search(markup([post(user={}), post()]))) == 1


def test_is_available_false_when_real_channels_disabled(monkeypatch):
    from app.crawl.adapters.threads import ThreadsAdapter
    monkeypatch.setattr(settings, 'real_channels_enabled', False)
    monkeypatch.setattr('app.crawl.render.RenderBridge.available', classmethod(lambda cls: True))
    assert ThreadsAdapter.is_available() is False


def test_provider_boundary_accepts_non_web_provider():
    from app.crawl.adapters.threads import ThreadsAdapter
    item = ListItem('https://www.threads.com/@user1/post/SYNTH0001', '', '합성 본문', None, {})
    class Provider:
        closed = False
        def search(self, kw):
            assert kw == '에어컨'
            return [item]
        def close(self):
            self.closed = True
    provider = Provider()
    adapter = ThreadsAdapter(provider=provider)
    assert adapter.list_page('에어컨').items == [item]
    adapter.close()
    assert provider.closed


def _decode_fixture(content):
    while True:
        decoded = re.sub(r'\\(?:u([0-9a-fA-F]{4})|x([0-9a-fA-F]{2}))',
                         lambda match: chr(int(match[1] or match[2], 16)),
                         unescape(unquote(content)).replace(r'\/', '/'))
        if decoded == content:
            return content
        content = decoded


# Exact public UI strings needed to distinguish results, empty results and login.
# Whole-value matches only: no substring exemptions for surrounding identities.
SITE_UI_TEXT = {'Log in', 'No results', '검색 결과가 없습니다', '결과 없음'}
SYNTHETIC_PATTERN = r'user[1-9][0-9]*|SYNTH[0-9]{4}|합성 에어컨 본문 [1-9][0-9]*입니다\.'
STRUCTURAL_KEYS = {'require', '__bbox', 'result', 'data', 'searchResults', 'edges',
                   'node', 'thread', 'thread_items', 'post'}
POST_KEYS = {'code', 'caption', 'taken_at', 'like_count', 'user', 'text_post_app_info'}
JSON_KEYS = STRUCTURAL_KEYS | POST_KEYS | {'text', 'username', 'direct_reply_count'}
MANIFEST_KEYS = {'keyword', 'list_count', 'requests', 'file', 'url'}
SEARCH_URL = 'https://www.threads.com/search?q=에어컨&serp_type=default'
EMPTY_URL = 'https://www.threads.com/search?q=합성검색결과없음&serp_type=default'


def _allowed_fixture_text(value):
    return not value or value in SITE_UI_TEXT or re.fullmatch(SYNTHETIC_PATTERN, value) is not None


# SHA-256 only: 19 usernames and 35 code values from the two ignored T0
# recordings. Raw capture identifiers must never enter committed fixtures.
RECORDED_IDENTIFIER_HASHES = {
    '0509807bbb39827abc5655f8bb5ddcefba116c5ea783fbd750ddea08352bcff5',
    '0a0b51d5246ba55fd777f910e9136d6cb2f34c762c30ec17ece24427be78aa88',
    '1090c107914b68fa546f29b686cdaeed9d825e66ec9b9f5dcb36338a1bb6a994',
    '11500ecb4240cab10216add70b20a51e8f56628ab47eacd597cc874548d9c561',
    '125f74c345acf405a7d68c41cfc34a34b120f7949fb0ddd6e4246d05ded3fed1',
    '14fc70c0c2e93c292e259f8fbcae9e7ca8e9a59bebf43fe53382fa99d3a7534c',
    '1c8851d426668c14d78f1c048ff02e8d0b4b6ca9722116fd0f849a3c6d0705af',
    '1cc8531e65539c3eddbe8fb03b91e71dc4e50319d5405bdb6f002f58b15f2508',
    '209b92f7bafbe6df24d0db5d4b8be3a62a1d463fc160a849a71cf699d82a6165',
    '2aef97450cbb0d8d15b8a40f4ff4c7ccf22c2515eb60a5e71102cf2b0c0747ed',
    '2b384badcff7e5be37f17e7d927a607eb77ae7a09884692214e1fb05de907adc',
    '2fb4ec7a993b9dd8fbf62e0c3cad019733316941e5abc6473791f2a426766337',
    '33c5b1895b1cbaa5b59bcc15cd76f5c00e7c7591d004423a54b02c813072a92a',
    '345a189785b5088a3dcecd14f679b4cb36184e8ba8613ca5871e961aeb6c341f',
    '417d25f8c5e18590ea54d95e03b175c1e9408667d34eb79353188efb9a7b4050',
    '45b604e4d87fbdc6e4f8738ca57dff0107601eaa707b0ddb2c32951abff93de9',
    '4a7fa901a8f49da2ebb5f56af33ae4cdc95c49d025ffa901b80fd7b6a38f44f4',
    '4c739ddd39d0088d73cfff74981a591ed7cd2bef05335ed83649ce9e90632c0e',
    '4d593706305fc8d115e521ca7ab8f0c92eda8d38a0673b32a7bb5c7491337bc0',
    '4e51953b5a8974c89151830ff1f22511db8e7ee1a860605a2a69cdafc4bdc822',
    '5fd6811188e92c8dcbec868cbf828b376dcf13460948676dc7cca78e6346e45d',
    '64e22651c751f8a8e6f9843fe2ec8fc1a576fb386ca8822d1bc09309755f5ad6',
    '6745713ddd0e606145e9f0afba5561c8bcc071886b758efaa45e1a6da91798ef',
    '674ac4b0bd40c5764a1ddf4e0119e9b4ee02f743211eefcf7b27c932a4831a4b',
    '6a437f3129aadcf83444c62174948d62c4d1566deb68122618c3d7b25074ffd8',
    '6bbf0e2758f80028f3252693ddfd0bb830a8f322de21a247eacdc6e12ce8d9c3',
    '6d66618cd730ef019870a7169c2838270c9bf8d8c482a4b8945acb91cd2bbdc4',
    '7d04c0c3e1e559559c2a9028fea7ce422ecc6a8bf7746729692144834a3f7498',
    '888c2c6af1e7185fc56a551fbbeb58fe56b6cffbb80d3605c7c49acbd61bfbca',
    '89dbbed3985d3508456ab747a3730a30e89b063b868f0eb1212b3b3ca785b7ff',
    '89f43ef3dbb098e94d0cb9a7bb6d5844b2049caad93fbc18a7441725b9576e47',
    '96f47740e6df313f1a27f11cac58a9cd9ce43137ff4a202517802470f723a5af',
    '9f292082baa4333ff3514ba2608d31dfb9ef071b1dc1ba5f21f13f275579d32b',
    'a379aef20756b30344b8ce7a90a2abd53e56d3ced808cfd24708b879707fea71',
    'a8f45c8da857e4202b8f29335710533048d5c26fdfa0119805501241e9b85a49',
    'aba5331b5044ce3a77d86cbc575e387c801530970f4c753bec12687cddefdf05',
    'b060289457d499ab392dfeccf46ba53419044764ae494fbd28cc0999764d3d83',
    'b0e04e86a4715ac6c1e1fbe967cd763c9d32b33207ac514f40ceda5b89846547',
    'bb2f06fd2626c71cd2fd6be0b20541b203dc9c858dac8f97549ab77efc07cb8f',
    'c3aac00065ed7cab99a1641c4091e4c70d8c0220380f4ee89350c473c28de5ed',
    'c5f8a1ab0ff1094ecdab335e3c2cfcda14be4f6c41f88cf27e7ac982ff017a10',
    'cd869eb2c0f1f9495b5663a1bdff5e7f5c5a7bdd5e7de65d360996f257144d6c',
    'cde2ef9a83761f3a04adcfd9afced134c7c9aab87393b55828772ff3050a1864',
    'd633d287f3c4ae9b837d559d5dfba9d47c027c13b9dccb9c1a3e3d0b9291407b',
    'e8e2c020e326ba54896b091215f74381cc92269be9edd6ab2e0ea7b7c81a5ffc',
    'ea3a47a72324e4d392efd426d14dd52e59aece0aad127d01dbdb46fd3c78ef0a',
    'eafe9720db0b547b0f9c200b334170a32587e530396edae10f9b763e62fe714a',
    'eb21eb6a52a021ba4d7918175e026016511e629c4ad9820bcdc785f7f89b048c',
    'f1d19e468fc01f9d4aaa921f9ae729cb9c8cfbf23d99532c8d57b72d420dd9cc',
    'f2dc3b7f39adbf34b707eab2aa1129d0ff2bc1eea24efa8875dd4a3c8bb7bc7d',
    'f4d8a4be74feb233758a368fb56a1c8e7fa5134943fdb2d6c40b3048e08baaf8',
    'f519c5e16e8e47144fc47a257d69fa353ec041433ce985686ad558b65a18bdb0',
    'fc90775e228dd9c4583865988751610c9f918ebdee38cae96fcde2dfc5e02c6f',
    'fe1bbd626ff3685a941e4e85603b17e2b391c75418b8024bf039f672ecd08971',
}


def _identifier_categories(value):
    """Scan whole decoded values, independently of the synthetic allowlist."""
    value = _decode_fixture(value)
    categories = []
    patterns = {
        'email': r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}',
        'phone': (r'(?<!\d)(?:0|\+82[ .-]?)(?:1[016789]|2|[3-6][1-5]|70|80|50[2-8])'
                  r'[ .-]?\d{3,4}[ .-]?\d{4}(?!\d)'),
        'IPv4': r'(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])',
    }
    for category, pattern in patterns.items():
        if re.search(pattern, value):
            categories.append(category)
    for handle in re.findall(r'@([\w.-]+)', value):
        if re.fullmatch(r'user[1-9][0-9]*', handle) is None:
            categories.append('handle')
    for username in re.findall(r'threads\.com/@([\w.-]+)', value, re.I):
        if re.fullmatch(r'user[1-9][0-9]*', username) is None:
            categories.append('Threads URL')
    if any(hashlib.sha256(token.encode()).hexdigest() in RECORDED_IDENTIFIER_HASHES
           for token in re.findall(r'[\w.-]+', value)):
        categories.append('recorded identifier')
    return categories


def _lexical_violations(source):
    """Consume every decoded character; never trust HTML error recovery."""
    violations, stack = [], []
    parents = {'html': {None}, 'head': {'html'}, 'body': {'html'},
               'p': {None, 'body'}, 'a': {None, 'body', 'p'},
               'script': {None, 'head', 'body'}}
    seen = set()
    fragment = False
    offset = 0
    while offset < len(source):
        text = re.match(r'[^<>]+', source[offset:])
        if text:
            value = text[0]
            if value.strip() and ((stack and stack[-1] in {'html', 'head'})
                                  or (not stack and 'html' in seen)):
                violations.append('misplaced text')
            if value.strip() and not stack:
                fragment = True
            offset += len(value)
            continue
        if source.startswith('<!DOCTYPE html>', offset) and not source[:offset].strip():
            offset += len('<!DOCTYPE html>')
            continue
        closing = re.match(r'</([a-z]+)>', source[offset:])
        opening = re.match(r'<([a-z]+)((?: [a-z]+="[^"<>]*")*)>', source[offset:])
        if closing:
            if not stack or stack.pop() != closing[1]:
                violations.append('unbalanced element')
            offset += len(closing[0])
        elif opening:
            tag = opening[1]
            parent = stack[-1] if stack else None
            if tag not in parents or parent not in parents[tag]:
                violations.append('element structure')
            if parent is None and 'html' in seen:
                violations.append('content after document')
            if tag == 'html' and fragment:
                violations.append('content before document')
            if parent is None and tag != 'html':
                fragment = True
            if tag in {'html', 'head', 'body'}:
                if tag in seen or (tag == 'head' and 'body' in seen):
                    violations.append('element order')
                seen.add(tag)
            stack.append(tag)
            offset += len(opening[0])
        else:
            # Includes closing-tag extras, stray angle brackets, comments,
            # PI, non-HTML declarations and all CDATA, even empty sections.
            violations.append('invalid markup token')
            break
    if stack:
        violations.append('unclosed element')
    return violations


def _fixture_identifier_violations(content):
    """Fail closed over all text, attributes and JSON keys/values after decoding.

    Inspect event-parser attributes (including duplicates), not a repaired DOM.
    Diagnostics contain categories only, never the rejected identity.
    """
    violations = []

    def pairs_hook(pairs):
        # Called recursively for every object, including objects inside arrays.
        # Compare decoded keys before building a dict so no earlier value can
        # disappear behind either a literal or an encoded duplicate.
        result = {}
        for key, value in pairs:
            key = _decode_fixture(key)
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result

    def check_json(value, field=None, manifest=False):
        # Validate the field's type before recursing; an array/object must not
        # smuggle several individually allowed strings into a scalar field.
        string_fields = {'username', 'code', 'text', 'keyword', 'file', 'url'}
        number_fields = {'like_count', 'direct_reply_count', 'taken_at', 'list_count'}
        if ((field in string_fields and not isinstance(value, str))
                or (field in number_fields and type(value) is not int)
                or (field in {'user', 'caption', 'text_post_app_info'} and not isinstance(value, dict))):
            violations.append('JSON field type')
        if isinstance(value, dict):
            allowed = MANIFEST_KEYS if manifest else JSON_KEYS
            # Post identity objects are narrower than the traversal wrappers.
            if not manifest:
                allowed = {'username'} if field == 'user' else allowed
                allowed = {'text'} if field == 'caption' else allowed
                allowed = {'direct_reply_count'} if field == 'text_post_app_info' else allowed
                allowed = POST_KEYS if field == 'post' or 'code' in value else allowed
            for key, child in value.items():
                violations.extend(_identifier_categories(key))
                if key not in allowed:
                    violations.append('JSON key')
                check_json(child, key, manifest)
        elif isinstance(value, list):
            for child in value:
                check_json(child, field, manifest)
        elif value is None:
            if field not in STRUCTURAL_KEYS:
                violations.append('JSON null')
        elif type(value) is int:
            if not ((field in {'like_count', 'direct_reply_count'} and 0 <= value <= 99)
                    or (manifest and field == 'list_count' and value == 19)
                    or (field == 'taken_at' and 1700000000 <= value <= 2000000000)):
                violations.append('JSON number')
        elif isinstance(value, str):
            value = _decode_fixture(value)
            violations.extend(_identifier_categories(value))
            patterns = {'username': r'user[1-9][0-9]*', 'code': r'SYNTH[0-9]{4}',
                        'text': r'합성 에어컨 본문 [1-9][0-9]*입니다\.'}
            allowed = (field in patterns and re.fullmatch(patterns[field], value) is not None)
            if manifest:
                allowed = ((field == 'keyword' and value == '에어컨')
                           or (field == 'file' and value in FIXTURE_NAMES[1:])
                           or (field == 'url' and value in {SEARCH_URL, EMPTY_URL}))
            if not allowed:
                violations.append('JSON string')
        else:
            violations.append('JSON type')

    def read_json(value, *, manifest=False):
        try:
            # Parse JSON escapes before decoding its individual strings. Decoding
            # the serialized document first corrupts double-escaped \u / \x data.
            try:
                parsed = json.loads(value, object_pairs_hook=pairs_hook)
            except json.JSONDecodeError:
                parsed = json.loads(_decode_fixture(value), object_pairs_hook=pairs_hook)
            check_json(parsed, manifest=manifest)
        except (ValueError, TypeError):
            violations.append('invalid JSON')

    class FixtureParser(EventHTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.in_script = False
            self.parts = []

        def handle_starttag(self, tag, attrs):
            if tag not in {'html', 'head', 'body', 'p', 'a', 'script'}:
                violations.append('element')
            if len({name for name, _ in attrs}) != len(attrs):
                violations.append('duplicate attribute')
            for name, value in attrs:
                value = _decode_fixture(value or '')
                violations.extend(_identifier_categories(value))
                if not ((tag == 'script' and name == 'type' and value == 'application/json')
                        or (tag == 'a' and name == 'href' and value == '/login')):
                    violations.append('attribute')
            if tag == 'script':
                if attrs != [('type', 'application/json')]:
                    violations.append('script attributes')
                self.in_script, self.parts = True, []

        def handle_endtag(self, tag):
            if tag == 'script':
                read_json(''.join(self.parts))
                self.in_script = False

        def handle_data(self, value):
            if self.in_script:
                self.parts.append(value)
            elif not _allowed_fixture_text(_decode_fixture(value).strip()):
                violations.append('text')

        def handle_comment(self, value):
            violations.append('comment')

        def handle_decl(self, value):
            if value != 'DOCTYPE html':
                violations.append('declaration')

        def handle_pi(self, value):
            violations.append('processing instruction')

        def unknown_decl(self, value):
            violations.append('unknown declaration')

    # Keep native HTML/JSON intact; values are decoded by their handlers. Fully
    # encoded mutation probes still need decoding before the outer parse.
    source = _decode_fixture(content)
    # Removing tags without inserting whitespace reconstructs identifiers
    # deliberately split across adjacent text nodes.
    violations.extend(_identifier_categories(re.sub(r'<[^>]*>', '', source)))
    decoded = content if content.lstrip().startswith(('<', '{', '[')) else source
    if decoded.lstrip().startswith(('{', '[')):
        read_json(decoded, manifest=True)
    else:
        violations.extend(_lexical_violations(source))
        parser = FixtureParser()
        try:
            parser.feed(decoded)
            parser.close()
        except (ValueError, AssertionError):
            violations.append('invalid HTML')
        if parser.in_script:
            violations.append('unclosed script')
    return violations


@pytest.mark.parametrize('name', FIXTURE_NAMES)
def test_fixture_identifiers_are_synthetic(name):
    assert _fixture_identifier_violations((FIXTURES / name).read_text()) == []


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
    return quote(''.join(f'&#{ord(char)};' for char in value.replace('/', r'\/')), safe='')


ENCODINGS = ['raw', 'entities', 'percent', 'unicode', 'hex', 'mixed']
# Invented probes only; captured identities above are stored exclusively as hashes.
MUTATIONS = [
    'seoul_daily.writer', '@seoul_daily.writer', 'DVrealCode123',
    'https://www.threads.com/@seoul_daily.writer/post/DVrealCode123',
    'https://cdn.example.test/profile_pic.jpg', 'leaked@example.test',
    '010-2345-6789', '01023456789', '실제처럼보이는이름',
    'user1 leaked@example.test', 'Log in leaked@example.test',
]


@pytest.mark.parametrize('value', MUTATIONS)
@pytest.mark.parametrize('encoding', ENCODINGS)
@pytest.mark.parametrize('position', ['text', 'attribute', 'json'])
def test_privacy_checker_rejects_identity_values_in_every_position(value, encoding, position):
    encoded = _encode_mutation(value, encoding)
    if position == 'text':
        content = f'<p>{encoded}</p>'
    elif position == 'attribute':
        content = f'<a href="{encoded}">Log in</a>'
    else:
        content = markup(post(user={'username': encoded}))
    assert _fixture_identifier_violations(content)


@pytest.mark.parametrize('key,value', [
    ('pk', 12345), ('full_name', 'user1'), ('profile_pic_url', 'user1'),
    ('id', 'SYNTH0001'), ('is_verified', False), ('email', 'user1'),
])
@pytest.mark.parametrize('encoding', ENCODINGS)
def test_privacy_checker_rejects_extra_identity_keys_even_with_synthetic_values(key, value, encoding):
    payload = post()
    payload['user'][_encode_mutation(key, encoding)] = value
    assert _fixture_identifier_violations(markup(payload))


@pytest.mark.parametrize('encoding', ENCODINGS)
@pytest.mark.parametrize('value', ['user19', 'SYNTH0019', '합성 에어컨 본문 19입니다.'])
def test_privacy_checker_allows_encoded_synthetic_values(value, encoding):
    assert _fixture_identifier_violations('<p>' + _encode_mutation(value, encoding) + '</p>') == []


@pytest.mark.parametrize('content', [
    '<script>var username = "user1";</script>', '<!-- user1 -->',
    '<script type="application/json">{"user":{"username":"user1","pk":1}}</script>',
    '<a href="/login" href="leaked@example.test">Log in</a>',
    '<p>합성 에어컨 본문 1입니다. leaked@example.test</p>',
    '<script type="application/json">{"user":{"username":"leaked@example.test","username":"user1"}}</script>',
])
def test_privacy_checker_rejects_unneeded_markup_and_duplicate_keys(content):
    assert _fixture_identifier_violations(content)


def test_fixtures_keep_minimal_nested_shape_duplicates_and_nonpost_script():
    from app.crawl.adapters.threads import _posts
    tree = HTMLParser((FIXTURES / 'search.html').read_text())
    payloads = [json.loads(script.text()) for script in tree.css('script[type="application/json"]')]
    posts = []
    empty_scripts = 0
    for payload in payloads:
        found = []
        _posts(payload, found)
        empty_scripts += not found
        posts.extend(found)
    assert empty_scripts >= 1 and len(posts) == 20
    assert len({p['code'] for p in posts}) == 19
    # Preserve the captured path, including nested list offsets and bbox wrappers.
    nested = payloads[1]['require'][0][3][0]['__bbox']['require'][0][3][1]
    assert nested['__bbox']['result']['data']['searchResults']['edges'][0]['node']['thread']['thread_items'][0]['post'] == posts[0]
    for value in posts:
        assert set(value) == POST_KEYS
        assert set(value['user']) == {'username'}
        assert set(value['caption']) == {'text'}
        assert set(value['text_post_app_info']) == {'direct_reply_count'}
        assert 0 < len(value['caption']['text']) <= 80
    changed = (FIXTURES / 'changed-shape.html').read_text()
    assert not HTMLParser(changed).css('script, a')
    assert not any(marker in changed for marker in SITE_UI_TEXT)
    assert 'No results' in (FIXTURES / 'search-empty.html').read_text()
    assert not HTMLParser((FIXTURES / 'search-empty.html').read_text()).css('script')
    assert all(line == line.rstrip() for name in FIXTURE_NAMES
               for line in (FIXTURES / name).read_text().splitlines())


@pytest.mark.parametrize('encoding', ENCODINGS)
def test_privacy_checker_allows_encoded_synthetic_json_strings(encoding):
    payload = post()
    payload['user']['username'] = _encode_mutation('user1', encoding)
    payload['code'] = _encode_mutation('SYNTH0001', encoding)
    payload['caption']['text'] = _encode_mutation('합성 에어컨 본문 1입니다.', encoding)
    assert _fixture_identifier_violations(markup(payload)) == []


# Invented identifiers only. An allowed final value must never hide an earlier
# value with the same key, including inside arrays and real fixture documents.
DUPLICATE_IDENTITIES = [
    'seoul_daily.writer',
    'https://www.threads.com/@seoul_daily.writer/post/DVrealCode123',
    'leaked@example.test', '010-2345-6789',
]


@pytest.mark.parametrize('value', DUPLICATE_IDENTITIES)
@pytest.mark.parametrize('encoding', ENCODINGS)
@pytest.mark.parametrize('fixture,field,allowed', [
    ('manifest.json', 'keyword', '에어컨'),
    ('manifest.json', 'file', 'search.html'),
    ('search.html', 'username', 'user1'),
])
def test_privacy_checker_rejects_duplicate_keys_in_valid_fixtures(fixture, field, allowed, value, encoding):
    content = (FIXTURES / fixture).read_text()
    assert _fixture_identifier_violations(content) == []
    # Locate exactly one key/value; keep the containing post script or manifest
    # otherwise unchanged. The overwritten value is always allowed.
    target = rf'"{field}"\s*:\s*{re.escape(json.dumps(allowed, ensure_ascii=False))}'
    duplicate = (json.dumps(field) + ':' + json.dumps(value, ensure_ascii=False)
                 + ',' + json.dumps(field) + ':' + json.dumps(allowed, ensure_ascii=False))
    mutated, count = re.subn(target, lambda match: duplicate, content, count=1)
    assert count == 1
    assert _fixture_identifier_violations(_encode_mutation(mutated, encoding))


@pytest.mark.parametrize('encoding', ENCODINGS)
@pytest.mark.parametrize('kind', ['manifest', 'post'])
def test_privacy_checker_rejects_keys_that_duplicate_after_decoding(encoding, kind):
    # Even synthetic values cannot make duplicate keys acceptable. Normalize
    # keys before comparing: JSON parsing alone only resolves JSON escapes.
    field, value = ('keyword', '에어컨') if kind == 'manifest' else ('username', 'user1')
    duplicate = ('{' + json.dumps(_encode_mutation(field, encoding)) + ':'
                 + json.dumps(value, ensure_ascii=False) + ',' + json.dumps(field)
                 + ':' + json.dumps(value, ensure_ascii=False) + '}')
    content = duplicate if kind == 'manifest' else (
        '<script type="application/json">{"data":[{"user":' + duplicate + '}]}</script>')
    assert _fixture_identifier_violations(content)


@pytest.mark.parametrize('value', DUPLICATE_IDENTITIES)
@pytest.mark.parametrize('encoding', ENCODINGS)
def test_privacy_checker_scans_cdata_for_identifiers(value, encoding):
    content = '<html><body><![CDATA[' + _encode_mutation(value, encoding) + ']]></body></html>'
    assert _fixture_identifier_violations(content)


@pytest.mark.parametrize('value', ['', 'user1', 'SYNTH0001', '합성 에어컨 본문 1입니다.', 'invented.identity'])
@pytest.mark.parametrize('encoding', ENCODINGS)
def test_privacy_checker_rejects_every_cdata(value, encoding):
    content = '<html><body><![CDATA[' + value + ']]></body></html>'
    assert _fixture_identifier_violations(_encode_mutation(content, encoding))


@pytest.mark.parametrize('encoding', ENCODINGS)
@pytest.mark.parametrize('mutation', [
    '</p user1>', '</p/>', '</p >', '</unknown>', '<', '>', '< >',
    '<!-- user1 -->', '<?user1?>', '<!DOCTYPE user1>', '<![CDATA[]]>',
    '<p><a href="/login">Log in</p></a>', '<p>user1<p>user2</p>',
    '<p/>', '<p href=/login>user1</p>', '<html><body><head></head></body></html>',
    '<a href="/login" href="/login">Log in</a>',
])
def test_privacy_checker_rejects_unvalidated_markup_in_full_fixture(mutation, encoding):
    content = (FIXTURES / 'search.html').read_text()
    content = content.replace('</body>', mutation + '</body>')
    assert _fixture_identifier_violations(_encode_mutation(content, encoding))


@pytest.mark.parametrize('encoding', ENCODINGS)
@pytest.mark.parametrize('suffix', ['<p>user1</p>', 'user1'])
def test_privacy_checker_rejects_content_after_document(suffix, encoding):
    content = (FIXTURES / 'search.html').read_text() + suffix
    assert _fixture_identifier_violations(_encode_mutation(content, encoding))


@pytest.mark.parametrize('encoding', ENCODINGS)
@pytest.mark.parametrize('prefix', ['<p>user1</p>', 'user1'])
def test_privacy_checker_rejects_content_before_document(prefix, encoding):
    content = (FIXTURES / 'search.html').read_text().replace('<!DOCTYPE html>', '')
    assert _fixture_identifier_violations(_encode_mutation(prefix + content, encoding))


@pytest.mark.parametrize('encoding', ENCODINGS)
@pytest.mark.parametrize('field,value', [
    ('username', 1792418400), ('username', ['user1']), ('username', {'text': '합성 에어컨 본문 1입니다.'}),
    ('code', ['SYNTH0001']), ('code', 'user1'), ('username', 'SYNTH0001'),
    ('text', ['합성 에어컨 본문 1입니다.']), ('text', 'user1'),
    ('username', None), ('code', None), ('text', 123), ('data', 19),
    ('username', 'user1@invented.test'), ('code', 'SYNTH0001leak'),
    ('text', '합성 에어컨 본문 1입니다. leaked@example.test'),
])
def test_privacy_checker_checks_whole_fields_in_full_fixture(field, value, encoding):
    content = (FIXTURES / 'search.html').read_text()
    if field == 'data':
        content = content.replace('{"data":[]}', json.dumps({'data': value}))
    else:
        content, count = re.subn(
            rf'"{field}":"[^"]*"', lambda match: json.dumps(field) + ':' + json.dumps(value),
            content, count=1)
        assert count == 1
    assert _fixture_identifier_violations(_encode_mutation(content, encoding))


@pytest.mark.parametrize('encoding', ENCODINGS)
@pytest.mark.parametrize('value,category', [
    ('leaked@example.test', 'email'), ('010-2345-6789', 'phone'),
    ('01023456789', 'phone'), ('02-234-5678', 'phone'), ('+82 10 2345 6789', 'phone'),
    ('010.2345.6789', 'phone'), ('070-2345-6789', 'phone'), ('0507-2345-6789', 'phone'),
    ('192.168.1.2', 'IPv4'), ('@invented.writer', 'handle'),
    ('@user1.extra', 'handle'), ('https://www.threads.com/@invented.writer/post/ABC', 'Threads URL'),
])
@pytest.mark.parametrize('position', ['split-text', 'attribute', 'json'])
def test_privacy_categories_scan_decoded_source_attributes_and_json(value, category, position, encoding):
    content = (FIXTURES / 'search.html').read_text()
    if position == 'split-text':
        # Join across tags before scanning; neither individual text node
        # contains the complete identifier.
        middle = len(value) // 2
        injected = '<p>' + value[:middle] + '</p><p>' + value[middle:] + '</p>'
        content = content.replace('</body>', injected + '</body>')
    elif position == 'attribute':
        content = content.replace('href="/login"', 'href="' + value + '"')
    else:
        content = content.replace('합성 에어컨 본문 1입니다.', '합성 에어컨 본문 1입니다. ' + value, 1)
    assert category in _fixture_identifier_violations(_encode_mutation(content, encoding))


@pytest.mark.parametrize('encoding', ENCODINGS)
@pytest.mark.parametrize('position', ['split-text', 'attribute', 'json'])
def test_privacy_categories_match_only_hashes_of_recorded_identifiers(monkeypatch, encoding, position):
    # Exercise the capture hash path using an invented value; never put a
    # captured identity in a mutation, assertion diagnostic or test ID.
    invented = 'invented_recorded_identifier'
    monkeypatch.setitem(globals(), 'RECORDED_IDENTIFIER_HASHES', {
        hashlib.sha256(invented.encode()).hexdigest(),
    })
    content = (FIXTURES / 'search.html').read_text()
    if position == 'split-text':
        content = content.replace('</body>', '<p>invented_recorded_</p><p>identifier</p></body>')
    elif position == 'attribute':
        content = content.replace('href="/login"', 'href="' + invented + '"')
    else:
        content = content.replace('"username":"user1"', '"username":"' + invented + '"', 1)
    assert 'recorded identifier' in _fixture_identifier_violations(_encode_mutation(content, encoding))


@pytest.mark.parametrize('encoding', ENCODINGS)
@pytest.mark.parametrize('value', [
    '@user1', 'https://www.threads.com/@user19/post/SYNTH0019',
    '합성 에어컨 본문 19입니다.', '1792418400', 'user19', 'SYNTH0019',
])
def test_privacy_categories_allow_synthetic_identifiers(value, encoding):
    assert _identifier_categories(_encode_mutation(value, encoding)) == []


@pytest.mark.parametrize('encoding', ENCODINGS)
@pytest.mark.parametrize('name', FIXTURE_NAMES)
def test_privacy_checker_allows_whole_encoded_fixtures(name, encoding):
    assert _fixture_identifier_violations(_encode_mutation((FIXTURES / name).read_text(), encoding)) == []
