"""Naver KiN question search and question bodies; answers are never stored."""
import re
import time
from collections import OrderedDict
from threading import Lock
from urllib.parse import parse_qs, unquote, urlencode, urlsplit

from app.crawl.adapters.base import AdapterSkipped, FetchedDoc, ListItem, ListPage
from app.crawl.adapters.community import CommunityAdapter, date_text, selected, text
from app.crawl.channels import channel_defaults
from app.crawl.ratelimit import ChannelLimiter
from app.crawl.urls import normalize_url


class NaverKinAdapter(CommunityAdapter):
    source = 'naver_kin'
    origin = 'https://kin.naver.com'
    NO_RESULT_SELECTORS = '.noresult, .no_result, #noResult'
    NO_RESULT_TEXT = ('검색결과가 없습니다', '검색 결과가 없습니다')

    def __init__(self, client=None, *, clock=time.monotonic, sleep=time.sleep):
        super().__init__(client, clock=clock, sleep=sleep)
        self._limiter = ChannelLimiter(*channel_defaults(self.source), clock=clock, sleep=sleep)
        self._pages = OrderedDict()
        self._pages_lock = Lock()

    def list_page(self, kw, cursor=None):
        page = super().list_page(kw, cursor)
        start = int(cursor or 1)
        signature = frozenset(item.url for item in page.items)
        with self._pages_lock:
            previous = self._pages.get(kw)
            repeated = previous is not None and previous[0] == signature and previous[1] < start
            # Retain the first cursor so retrying a repeated page stays terminal.
            self._pages[kw] = (signature, previous[1] if repeated else start)
            self._pages.move_to_end(kw)
            if len(self._pages) > 256:
                self._pages.popitem(last=False)
        return ListPage(page.items, None if repeated else page.next_cursor, page.total_hint)

    def list_url(self, kw, cursor):
        page = int(cursor or 1)
        if page < 1:
            raise ValueError('KiN page must be positive')
        return f'{self.origin}/search/list.naver?{urlencode({"query": kw, "page": page})}'

    def parse_list(self, tree, cursor):
        items, seen = [], set()
        rows = tree.css('ul.basic1 > li')
        if not rows:
            body = tree.body.text() if tree.body else ''
            if tree.css_first(self.NO_RESULT_SELECTORS) is not None or any(
                marker in body for marker in self.NO_RESULT_TEXT
            ):
                return ListPage([], None, 0)
            raise ValueError('KiN search results could not be parsed')
        for row in rows:
            link = row.css_first('a._searchListTitleAnchor')
            if link is None or not link.attributes.get('href'):
                raise ValueError('KiN result title missing')
            url = normalize_url(self.absolute_url(link.attributes['href']), self.source)
            query = parse_qs(urlsplit(url).query)
            if 'docId' not in query or 'dirId' not in query:
                raise ValueError('KiN result question ID missing')
            if url in seen:
                continue
            seen.add(url)
            hit = re.search(r'답변수\s*(\d+)', selected(row, '.hit'))
            snippet = ' '.join(
                text(dd) for dd in row.css('dl > dd')
                if not set(dd.attributes.get('class', '').split())
                & {'txt_inline', 'tag_area', 'txt_block'}
            )
            items.append(ListItem(
                url, text(link), snippet, date_text(selected(row, 'dd.txt_inline')),
                {'dir_id': query['dirId'][0], 'doc_id': query['docId'][0],
                 'answer_count': int(hit[1]) if hit else 0},
            ))
        current = int(cursor or 1)
        later = False
        for link in tree.css('a[href]'):
            target = urlsplit(link.attributes['href'])
            pages = parse_qs(target.query).get('page', [])
            if target.path == '/search/list.naver' and any(
                page.isdigit() and int(page) > current for page in pages
            ):
                later = True
                break
        return ListPage(items, str(current + 1) if items and later else None, None)

    def parse_detail(self, tree, item):
        body = tree.css_first('.questionDetail')
        if body is None:
            # Deleted captures have no body: the alert lives in a head script.
            if re.search(r'게시물이 삭제되어|삭제된 게시물|존재하지 않', tree.html or ''):
                raise AdapterSkipped('deleted')
            raise ValueError('KiN question body missing')
        for node in body.css('._waitingForReplaceImage, script, style'):
            node.decompose()
        title_node = tree.css_first('.endTitleSection')
        for node in (title_node.css('.blind, svg') if title_node else []):
            node.decompose()
        tags = [tag.strip() for tag in unquote(body.attributes.get('data-tag', '')).split(',')
                if tag.strip()]
        query = parse_qs(urlsplit(item.url).query)
        written = re.search(r'작성일</span>\s*([0-9.]+)', tree.html or '')
        return FetchedDoc(
            text(title_node) or item.title, text(body), [],
            date_text(written[1]) if written else None,
            {**item.src_meta, 'dir_id': query.get('dirId', [''])[0],
             'doc_id': query.get('docId', [''])[0],
             'answer_count': len(tree.css('.answerArea')), 'tags': tags},
            'public', None,
        )
