import json
import re
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlsplit

import httpx
import pytest

from app.config import settings
from app.crawl.adapters.base import AdapterBlocked, AdapterSkipped

FIXTURES = Path(__file__).parents[2] / 'fixtures' / 'http' / 'naver_kin'


class Clock:
    def __init__(self):
        self.now = 0.0
    def __call__(self):
        return self.now
    def sleep(self, d):
        self.now += d


@pytest.fixture(autouse=True)
def salt(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, 'author_salt_path', str(tmp_path / 'salt'))


def adapter(status=200, transform=None):
    manifest = json.loads((FIXTURES / 'manifest.json').read_text())
    seen = []
    def respond(request):
        seen.append(str(request.url))
        q = parse_qs(urlsplit(str(request.url)).query)
        for cap in manifest['requests']:
            cq = parse_qs(urlsplit(cap['url']).query)
            if urlsplit(cap['url']).path == request.url.path and q == cq:
                content = (FIXTURES / cap['file']).read_bytes()
                if transform:
                    content = transform(content)
                return httpx.Response(status, content=content)
        raise AssertionError(f'Unrecorded request: {request.url}')
    from app.crawl.adapters.naver_kin import NaverKinAdapter
    clock = Clock()
    return NaverKinAdapter(httpx.Client(transport=httpx.MockTransport(respond)), clock=clock, sleep=clock.sleep), manifest, seen


def test_list_page_parses_ten_normalized_questions_and_next_cursor():
    a, manifest, _ = adapter()
    page = a.list_page(manifest['keyword'], None)
    assert len(page.items) == 10
    assert all(i.url.startswith('https://kin.naver.com/qna/detail.naver?dirId=') and 'answerNo' not in i.url for i in page.items)
    assert len({i.url for i in page.items}) == 10
    assert all(i.title for i in page.items)
    assert all(isinstance(i.src_meta['answer_count'], int) for i in page.items)
    assert [i.title for i in page.items] == [f'합성 에어컨 질문 {n}' for n in range(1, 11)]
    assert all(i.snippet == '에어컨 관리 방법을 확인하는 합성 요약입니다.' for i in page.items)
    assert page.items[0].date == '2026-10-07'
    assert page.items[0].src_meta['answer_count'] == 4
    assert page.next_cursor == '2'


def test_empty_search_ends_without_error():
    a, manifest, _ = adapter()
    page = a.list_page(manifest['empty_keyword'], None)
    assert page.items == [] and page.next_cursor is None


def test_fetch_reads_question_only():
    a, manifest, _ = adapter()
    from app.crawl.adapters.base import ListItem
    url = manifest['question_url']
    doc = a.fetch(ListItem(url, '', '', None, {}))[0]
    assert doc.title and doc.body
    assert doc.comments == []
    assert doc.date and len(doc.date) == 10
    assert doc.src_meta['doc_id'] == parse_qs(urlsplit(url).query)['docId'][0]
    assert doc.src_meta['answer_count'] >= 1
    # The manifest's historical answer prefix is no longer in the minimized
    # recording. Assert against an answer that is actually present instead.
    assert ANSWER_TEXT in (FIXTURES / 'question-1.html').read_text()
    assert ANSWER_TEXT not in doc.body


def test_deleted_question_is_skipped():
    a, manifest, _ = adapter()
    from app.crawl.adapters.base import ListItem
    with pytest.raises(AdapterSkipped) as raised:
        a.fetch(ListItem(manifest['deleted_url'], '', '', None, {}))
    assert raised.value.reason == 'deleted'


def test_http_429_is_blocked():
    a, manifest, _ = adapter(status=429)
    with pytest.raises(AdapterBlocked):
        a.list_page(manifest['keyword'], None)


def test_changed_markup_is_a_parse_error_not_an_empty_page():
    a, manifest, _ = adapter()
    with pytest.raises(ValueError):
        a.list_page(manifest['changed_keyword'], None)  # No result rows or no-result marker.


def test_pagination_reads_second_page():
    a, manifest, seen = adapter()
    first = a.list_page(manifest['keyword'], None)
    second = a.list_page(manifest['keyword'], first.next_cursor)
    assert len(second.items) == 10
    assert second.next_cursor == '3'
    assert first.items[0].url != second.items[0].url
    assert parse_qs(urlsplit(seen[-1]).query)['page'] == ['2']


def test_last_page_without_later_links_ends():
    from selectolax.parser import HTMLParser

    def without_pagination(content):
        tree = HTMLParser(content.decode())
        for node in tree.css('a[href]'):
            if 'page' in parse_qs(urlsplit(node.attributes['href']).query):
                node.decompose()
        return tree.html.encode()

    a, manifest, _ = adapter(transform=without_pagination)
    page = a.list_page(manifest['keyword'], None)
    assert len(page.items) == 10
    assert page.next_cursor is None


@pytest.mark.parametrize('cursor', ['0', '-1', 'invalid'])
def test_invalid_page_rejected_before_request(cursor):
    a, manifest, seen = adapter()
    with pytest.raises(ValueError):
        a.list_page(manifest['keyword'], cursor)
    assert seen == []


@pytest.mark.parametrize('index,title,date,count,tags', [
    (1, '구형 에어컨 송풍팬 분해 방법', '2026-04-19', 4, ['에어컨청소', '에어컨']),
    (2, '에어컨 분해 청소 후 냄새', '2026-06-29', 5, ['에어컨청소']),
    (3, '주차 공간 에어컨 실외기 설치', '2026-10-16', 3, []),
])
def test_details_use_question_date_and_decoded_tags(index, title, date, count, tags):
    from app.crawl.adapters.base import ListItem

    a, manifest, _ = adapter()
    url = next(r['url'] for r in manifest['requests'] if r['file'] == f'question-{index}.html')
    doc, = a.fetch(ListItem(url, '검색 제목', '', '2026-10-20', {}))
    assert doc.title == title
    assert doc.date == date
    assert doc.body and len(doc.body) <= 80
    assert ANSWER_TEXT in (FIXTURES / f'question-{index}.html').read_text()
    assert ANSWER_TEXT not in doc.body
    assert doc.comments == []
    assert doc.access == 'public' and doc.author_raw is None
    assert doc.src_meta == {
        'dir_id': '80902' if index == 3 else '80901',
        'doc_id': ['493036426', '494092059', '495568872'][index - 1],
        'answer_count': count,
        'tags': tags,
    }


@pytest.mark.parametrize('index', [1, 2, 3])
def test_missing_question_date_does_not_borrow_search_date(index):
    from app.crawl.adapters.base import ListItem

    a, manifest, _ = adapter(transform=lambda content: content.replace(
        '작성일'.encode(), '질문'.encode(),
    ))
    url = next(r['url'] for r in manifest['requests'] if r['file'] == f'question-{index}.html')
    doc, = a.fetch(ListItem(url, '', '', '2026-10-20', {}))
    assert doc.date is None


@pytest.mark.parametrize('status', [403, 429])
@pytest.mark.parametrize('operation', ['list', 'fetch'])
def test_blocked_response_is_not_retried(status, operation):
    from app.crawl.adapters.base import ListItem

    a, manifest, seen = adapter(status=status)
    with pytest.raises(AdapterBlocked):
        if operation == 'list':
            a.list_page(manifest['keyword'], None)
        else:
            a.fetch(ListItem(manifest['question_url'], '', '', None, {}))
    assert len(seen) == 1


def test_missing_question_body_is_parse_error():
    from app.crawl.adapters.base import ListItem

    a, manifest, _ = adapter(transform=lambda content: content.replace(
        b'class="questionDetail', b'class="changedQuestionDetail'))
    with pytest.raises(ValueError):
        a.fetch(ListItem(manifest['question_url'], '', '', None, {}))


def test_missing_result_title_is_parse_error():
    a, manifest, _ = adapter(transform=lambda content: content.replace(
        b'_searchListTitleAnchor', b'changedTitleAnchor'))
    with pytest.raises(ValueError):
        a.list_page(manifest['keyword'], None)


def test_request_spacing_uses_channel_defaults(monkeypatch):
    from app.crawl import channels

    monkeypatch.setitem(channels._DEFAULTS, 'naver_kin', (1, 1.25))
    a, manifest, _ = adapter()
    a._limiter.rng = lambda: 0.5
    first = a.list_page(manifest['keyword'], None)
    a.fetch(first.items[0])
    assert a._limiter.clock() == 1.25


def _decode_fixture(content):
    # Decode to a fixed point: escapes can themselves hide entities/percent escapes.
    while True:
        decoded = re.sub(
            r'\\(?:u([0-9a-fA-F]{4})|x([0-9a-fA-F]{2}))',
            lambda match: chr(int(match[1] or match[2], 16)),
            unescape(unquote(content)).replace(r'\/', '/'),
        )
        if decoded == content:
            return content
        content = decoded


# Only the head-only deletion capture needs executable content. Compare the
# entire decoded script, including whitespace; no arbitrary JS/JSON is allowed.
DELETED_SCRIPT = (
    'window.alert("게시물이 삭제되어 요청하신 페이지를 표시할 수 없습니다.");'
    'top.location.replace("/");'
)
ANSWER_TEXT = '합성 답변입니다. 질문 본문에는 포함하지 않습니다.'
SYNTHETIC_TEXT = {
    '구형 에어컨 송풍팬 분해 방법', '에어컨 분해 청소 후 냄새',
    '주차 공간 에어컨 실외기 설치',
    '에어컨 청소 방법을 확인하는 합성 질문입니다.',
    '청소 후 냄새를 확인하는 합성 질문입니다.',
    '실외기 설치 위치를 확인하는 합성 질문입니다.',
    '에어컨 관리 방법을 확인하는 합성 요약입니다.',
    ANSWER_TEXT, 'synthetic text', 'synthetic career', 'synthetic nickname',
}
# Exact public UI strings, never a matching row/element exemption. The help
# label exists only to regression-test the previously unsafe row exemption.
SITE_UI_TEXT = {
    '질문', '작성일', "'훗뽝켄껌퇭뿍' 에 대한 검색결과가 없습니다.",
    '검색결과가 없습니다.', '정신건강상담전화 1577-0199',
}
# Full attribute values, not individual tokens or arbitrary class/id patterns.
STRUCTURAL_ATTRIBUTES = {
    'class': {
        'basic1', '_searchListTitleAnchor', 'txt_inline', 'hit', 'txt_block',
        'endTitleSection', 'blind', 'questionDetail', 'answerArea',
        'se-main-container', 'counsel_info_list',
    },
    'id': {'noResult'},
    'data-tag': {'에어컨청소,에어컨', '에어컨청소'},
}
ALLOWED_TAGS = {
    'html', 'head', 'body', 'ul', 'li', 'dl', 'dt', 'dd', 'a', 'div',
    'span', 'p', 'strong', 'script',
}


def _synthetic_value(value):
    return value in SYNTHETIC_TEXT or re.fullmatch(
        r'(?:user[1-9][0-9]*|blog-user[1-9][0-9]*|합성 에어컨 질문 [1-9][0-9]?|'
        r'https://example\.invalid/(?:user[1-9][0-9]*|blog-user[1-9][0-9]*|synthetic)(?:\.png)?)',
        value,
    ) is not None


def _allowed_text(value):
    return value in SITE_UI_TEXT or _synthetic_value(value) or re.fullmatch(
        r'(?:[1-9][0-9]?|답변수 [0-9]{1,2}|[0-9]{4}\.[0-9]{2}\.[0-9]{2}\.)',
        value,
    ) is not None


def _allowed_attribute(name, value):
    if value in STRUCTURAL_ATTRIBUTES.get(name, set()):
        return True
    # Numeric IDs are allowed only in question URLs, never as arbitrary account
    # or contact attribute values. Search query is the fixture's exact keyword.
    if name == 'href':
        return _synthetic_value(value) or re.fullmatch(
            r'(?:https://kin\.naver\.com)?(?:'
            r'/qna/detail\.naver\?dirId=[1-9][0-9]*&docId=[1-9][0-9]*|'
            r'/search/list\.naver\?query=에어컨&page=[1-9][0-9]*)',
            value,
        ) is not None
    # Keep synthetic attribute probes meaningful without exempting their values.
    return name in {'title', 'data-contact'} and _synthetic_value(value)


def _fixture_identifier_violations(content):
    class PrivacyParser(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.violations = []
            self.in_script = False
            self.script_parts = []
            self.script_count = 0

        def handle_decl(self, decl):
            if decl != 'DOCTYPE html':
                self.violations.append('unexpected declaration')

        def handle_comment(self, data):
            self.violations.append('comment')

        def handle_pi(self, data):
            self.violations.append('processing instruction')

        def unknown_decl(self, data):
            self.violations.append('unknown declaration')

        def handle_starttag(self, tag, attrs):
            if tag not in ALLOWED_TAGS:
                self.violations.append('unexpected element')
            # Scan every attribute, including attributes on allowed UI rows and
            # script elements. Duplicate attributes are retained by HTMLParser.
            for name, value in attrs:
                if value is None or not _allowed_attribute(name, _decode_fixture(value)):
                    self.violations.append('attribute: ' + name)
            if tag == 'script':
                self.in_script = True
                self.script_parts = []
                self.script_count += 1
                if self.script_count > 1:
                    self.violations.append('extra script')

        def handle_endtag(self, tag):
            if tag == 'script':
                if _decode_fixture(''.join(self.script_parts)) != DELETED_SCRIPT:
                    self.violations.append('script content')
                self.in_script = False

        def handle_data(self, data):
            if self.in_script:
                self.script_parts.append(data)
            else:
                value = _decode_fixture(data).strip()
                if value and not _allowed_text(value):
                    self.violations.append('text')

    violations = []
    # Scan both representations: decoding markup must not turn a dangerous
    # attribute value into a different parse tree and hide the original value.
    for representation in (content, _decode_fixture(content)):
        parser = PrivacyParser()
        parser.feed(representation)
        parser.close()
        if parser.in_script:
            parser.violations.append('unclosed script')
        violations.extend(parser.violations)
    return violations


@pytest.mark.parametrize('fixture', sorted(FIXTURES.glob('*.html')), ids=lambda p: p.name)
def test_fixture_identifiers_are_synthetic(fixture):
    assert _fixture_identifier_violations(fixture.read_text()) == []


@pytest.mark.parametrize('encoding', [
    'raw', 'entities', 'percent', 'double-percent', 'unicode', 'hex',
    'escaped-slashes', 'nested',
])
@pytest.mark.parametrize('mutation', [
    r'https:\/\/blog\u002enaver\u002ecom/\u006ceaked-account',
    r'https:\/\/m\x2eblog\x2enaver\x2ecom/leaked-account',
    'https://in.naver.com/leaked-account',
    'https%253A%252F%252Fblog.naver.com%252Fleaked-account',
    'leaked@example.test',
    r'leaked\u0040example\x2etest',
    '010-2345-6789', '01123456789', '02-345-6789', '0312345678',
    '010 2345 6789', '연락처010.2345.6789입니다', '070-2345-6789',
    '(02) 3456-7890', '+82-10-2345-6789', '1588-1234', '16881234',
    '#12348765', '#12345678901', '&#35;12348765',
    '<script>{"memberId":"leaked-account"}</script>',
    r'<script>{"user\u0049d":"leaked-account"}</script>',
    '<script>{"nickname":"실제이름"}</script>',
    '<script>{"display_name":"실제이름"}</script>',
    '<script>{"userNickname":"실제이름"}</script>',
    '<script>{"storeId":123456789,"productId":987654321}</script>',
    '<script>{"expertId":"leaked-account","profileId":"leaked-account"}</script>',
    '/profile/index.naver?u=leaked-account',
    '<div class="profile_card"><strong class="name">실제이름</strong></div>',
    '<div class="profile_card"><strong class="name">물신</strong></div>',
    '<div class="profile_card"><span>실제 사업체</span></div>',
    '<div class="career_list"><span>실제 경력</span></div>',
    '<div class="introduction"><p>실제 소개</p></div>',
    '<div class="profile_card"><div class="intro">실제 소개</div></div>',
    # A help-panel number is not exempt when copied into an answerer's contact.
    '<div class="profile_card">1577-0199</div>',
])
def test_fixture_identifier_checker_rejects_mutations(mutation, encoding):
    assert _fixture_identifier_violations(
        '<html><body>' + _encode_mutation(mutation, encoding) + '</body></html>',
    )


def _encode_mutation(value, encoding):
    if encoding == 'raw':
        return value
    if encoding == 'entities':
        return ''.join(f'&#{ord(char)};' for char in value)
    if encoding == 'percent':
        return quote(value, safe='')
    if encoding == 'double-percent':
        return quote(quote(value, safe=''), safe='')
    if encoding == 'unicode':
        return ''.join(f'\\u{ord(char):04x}' for char in value)
    if encoding == 'hex':
        return ''.join(f'\\x{ord(char):02x}' if ord(char) < 256 else f'\\u{ord(char):04x}'
                       for char in value)
    if encoding == 'escaped-slashes':
        return value.replace('/', r'\/')
    if encoding == 'nested':
        return quote(_encode_mutation(_encode_mutation(value, 'entities'), 'unicode'), safe='')
    raise AssertionError(encoding)


ENCODINGS = ['raw', 'entities', 'percent', 'double-percent', 'unicode', 'hex',
             'escaped-slashes', 'nested']

# All identifiers below are invented mutation sentinels, not captured identities.
# Keep wrappers fixed so the encoded value itself must be examined.
@pytest.mark.parametrize('template,value', [
    ('<dd class="txt_block">{}</dd>', '누출표시이름 (user1)'),
    ('<dd class="txt_block">{}</dd>', '누출사업체 (user2)'),
    ('<script>{}</script>', 'var baQuestionUserKey = "leaked-account";'),
    ('<script>{}</script>', 'memberId = leakedAccount;'),
    ('<script>{}</script>', 'memberId = "leaked-account";'),
    ('<li data-contact="{}">정신건강상담전화 1577-0199</li>', 'leaked@example.test'),
    ('<li data-contact="{}">정신건강상담전화 1577-0199</li>', '010-2345-6789'),
    ('<li data-contact="{}">검색결과가 없습니다.</li>', 'leaked@example.test'),
    ('<a href="{}">user1</a>', '/expert?storeId={{=product.storeId}}leaked-account'),
    ('<p>{}</p>', '{{=product.storeId}}leaked-account'),
    ('<p>{}</p>', 'leaked@example.test'),
    *[('<p>{}</p>', phone) for phone in (
        '010-2345-6789', '01123456789', '02-345-6789', '0312345678',
        '010 2345 6789', '연락처010.2345.6789입니다', '070-2345-6789',
        '(02) 3456-7890', '+82-10-2345-6789', '1588-1234', '16881234',
        '#12348765', '#12345678901',
    )],
    *[('<a href="{}">user1</a>', url) for url in (
        'https://blog.naver.com/leaked-account',
        'https://m.blog.naver.com/leaked-account',
        'https://in.naver.com/leaked-account',
        'https://expert.naver.com/expert?expertId=leaked-account',
        'https://expert.naver.com/expert?storeId=123456789',
        'https://expert.naver.com/expert?productId=987654321',
        '/profile/index.naver?u=leaked-account',
        'https://example.invalid/user1/leaked-account',
    )],
    *[('<p>{}</p>', value) for value in (
        'expertId=leaked-account', 'storeId=123456789', 'productId=987654321',
        'profileId=leaked-account', 'user1 leaked-account', 'blog-user1suffix',
        '에어컨 청소 방법을 확인하는 합성 질문입니다. 누출이름',
    )],
    ('<div class="{}">user1</div>', 'questionDetail leaked-account'),
    ('<div id="{}">user1</div>', 'noResultleaked-account'),
    ('<div data-tag="{}">user1</div>', '에어컨청소,누출이름'),
    ('<script>{}</script>', DELETED_SCRIPT + 'var memberId = "leaked-account";'),
])
@pytest.mark.parametrize('encoding', ENCODINGS)
def test_allowlist_rejects_encoded_category_mutations(template, value, encoding):
    assert _fixture_identifier_violations(template.format(_encode_mutation(value, encoding)))


@pytest.mark.parametrize('encoding', ENCODINGS)
@pytest.mark.parametrize('value', [
    'user19', 'blog-user2', 'synthetic text', 'synthetic career',
    'https://example.invalid/user1', 'https://example.invalid/blog-user2.png',
    *sorted(SYNTHETIC_TEXT),
])
def test_allowlist_accepts_encoded_synthetic_values(value, encoding):
    encoded = _encode_mutation(value, encoding)
    assert _fixture_identifier_violations(f'<p>{encoded}</p>') == []
    assert _fixture_identifier_violations(f'<div title="{encoded}">user1</div>') == []


@pytest.mark.parametrize('content', [
    '<li data-contact="user1">정신건강상담전화 1577-0199</li>',
    '<div class="questionDetail" data-tag="에어컨청소">synthetic text</div>',
    '<a href="/qna/detail.naver?dirId=80901&amp;docId=493036426">user1</a>',
    '<a href="/search/list.naver?query=에어컨&amp;page=2">2</a>',
    '<html><head><script>' + DELETED_SCRIPT + '</script></head></html>',
])
def test_fixture_identifier_checker_allows_synthetic_and_site_metadata(content):
    assert _fixture_identifier_violations(content) == []


@pytest.mark.parametrize('content', [
    '<script>{"memberId":"user19"}</script>',
    '<script></script>',
    '<script>' + DELETED_SCRIPT + ' </script>',
    '<script title="leaked@example.test">' + DELETED_SCRIPT + '</script>',
    '<!-- user1 -->', '<img src="https://example.invalid/user1.png">',
    '<input type="hidden" value="user1">',
    '<span id="SE-8e1fec8a-6da1-4699-8e06-1609156ae988"></span>',
    '<p title="user1" title="leaked@example.test">user1</p>',
    '<p>&lt;img src="https://example.invalid/user1.png"&gt;</p>',
])
def test_minimal_fixtures_reject_unneeded_markup_even_if_synthetic(content):
    assert _fixture_identifier_violations(content)


@pytest.mark.parametrize('fixture', sorted(FIXTURES.glob('*.html')), ids=lambda p: p.name)
def test_minimized_fixture_structure_and_whitespace(fixture):
    from selectolax.parser import HTMLParser

    content = fixture.read_text()
    assert all(line == line.rstrip() for line in content.splitlines())
    tree = HTMLParser(content)
    assert not tree.css('img, input, style, .profile_card, .expertList, dd.txt_block')
    scripts = tree.css('script')
    if fixture.name == 'question-deleted.html':
        assert '<body' not in content
        assert len(scripts) == 1
        assert scripts[0].parent.tag == 'head'
        assert scripts[0].text() == DELETED_SCRIPT
    else:
        assert scripts == []
    for node in tree.css('.questionDetail, .answerArea'):
        assert 0 < len(node.text().strip()) <= 80


@pytest.fixture
def repeating_adapter():
    from app.crawl.adapters.naver_kin import NaverKinAdapter

    content = (FIXTURES / 'list-1.html').read_bytes()
    clock = Clock()
    with httpx.Client(transport=httpx.MockTransport(
        lambda request: httpx.Response(200, content=content),
    )) as client:
        yield NaverKinAdapter(client, clock=clock, sleep=clock.sleep)


def test_repeated_page_terminates_and_terminal_retry_stays_terminal(repeating_adapter):
    a = repeating_adapter
    first = a.list_page('에어컨', None)
    second = a.list_page('에어컨', first.next_cursor)
    assert len(second.items) == 10
    assert {item.url for item in first.items} == {item.url for item in second.items}
    assert second.next_cursor is None
    assert a.list_page('에어컨', '2').next_cursor is None


def test_same_cursor_retry_keeps_next_page(repeating_adapter):
    a = repeating_adapter
    assert a.list_page('에어컨', None).next_cursor == '2'
    assert a.list_page('에어컨', '1').next_cursor == '2'


def test_repeat_detection_is_independent_for_each_keyword(repeating_adapter):
    a = repeating_adapter
    assert a.list_page('에어컨', '1').next_cursor == '2'
    assert a.list_page('선풍기', '2').next_cursor == '3'
    assert a.list_page('에어컨', '2').next_cursor is None
    assert a.list_page('선풍기', '2').next_cursor == '3'


def test_repeat_history_is_bounded(repeating_adapter):
    a = repeating_adapter
    for index in range(257):
        assert a.list_page(f'keyword-{index}', '1').next_cursor == '2'
    # The oldest keyword has been evicted; a recent one still detects repetition.
    assert a.list_page('keyword-0', '2').next_cursor == '3'
    assert a.list_page('keyword-256', '2').next_cursor is None
