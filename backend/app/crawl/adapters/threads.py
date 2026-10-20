"""Threads logged-out search; the listing already carries each post's full text."""
from datetime import datetime
import json
import re
from typing import Protocol
from urllib.parse import quote
from zoneinfo import ZoneInfo

from selectolax.parser import HTMLParser

from app.config import settings
from app.crawl.adapters.base import AdapterBlocked, FetchedDoc, ListItem, ListPage
from app.crawl.render import RenderBridge

KST = ZoneInfo('Asia/Seoul')


def _posts(node, out, depth=0):
    if depth > 80:
        return
    if isinstance(node, dict):
        caption = node.get('caption')
        if node.get('code') and isinstance(caption, dict) and isinstance(node.get('user'), dict):
            out.append(node)
            return
        for value in node.values():
            _posts(value, out, depth + 1)
    elif isinstance(node, list):
        for value in node:
            _posts(value, out, depth + 1)


def parse_search(html: str) -> list[ListItem]:
    tree = HTMLParser(html)
    found = []
    for script in tree.css('script[type="application/json"]'):
        try:
            _posts(json.loads(script.text()), found)
        except ValueError:
            continue
    items, seen = [], set()
    for post in found:
        code, user = post['code'], post['user'].get('username') or ''
        text = (post['caption'] or {}).get('text') or ''
        if code in seen or not text or not user:
            continue
        seen.add(code)
        info = post.get('text_post_app_info') or {}
        taken = post.get('taken_at')
        date = datetime.fromtimestamp(taken, KST).date().isoformat() if isinstance(taken, (int, float)) else None
        # The username stays only in the public post URL; it is not copied into metadata.
        items.append(ListItem(f'https://www.threads.com/@{user}/post/{code}', '', text, date,
                              {'post_code': code, 'like_count': post.get('like_count'),
                               'reply_count': info.get('direct_reply_count')}))
    return items


# T0 녹화(search-empty.html)에서 확인한 "결과 없음" 문구로 맞춘다.
_NO_RESULT_TEXT = ('No results', '검색 결과가 없습니다', '결과 없음')


def _no_results(html: str) -> bool:
    return any(t in html for t in _NO_RESULT_TEXT)


def _login_wall(html: str) -> bool:
    lowered = html.lower()
    return '/login' in lowered or 'log in' in lowered


class ThreadsSearchProvider(Protocol):
    def search(self, kw: str) -> list[ListItem]: ...
    def close(self) -> None: ...


class WebSearchProvider:
    def __init__(self, bridge=None):
        self.bridge = bridge or RenderBridge()

    def search(self, kw):
        url = f'https://www.threads.com/search?q={quote(kw)}&serp_type=default'
        html = self.bridge.fetch_html(url, timeout_s=settings.threads_render_timeout_s)
        items = parse_search(html)
        if items:
            return items
        if _no_results(html):
            return []
        if _login_wall(html):
            raise AdapterBlocked('Threads requires login', host='threads.com')
        raise ValueError('Threads search returned no parsable posts')  # never a silent empty page

    def close(self):
        self.bridge.close()


class ThreadsAdapter:
    """Request spacing comes from the worker's channel limiter (1 · 2s); no second limiter here."""
    source = 'threads'

    def __init__(self, provider=None):
        self.provider = provider or WebSearchProvider()

    @classmethod
    def is_available(cls) -> bool:
        return settings.real_channels_enabled and RenderBridge.available()

    def list_page(self, kw, cursor=None):
        if cursor is not None:
            raise ValueError('Threads search has no continuation cursor')
        items = self.provider.search(kw)
        return ListPage(items, None, len(items))

    def fetch(self, item):
        match = re.search(r'/@([^/]+)/post/', item.url)
        return [FetchedDoc('', item.snippet, [], item.date, dict(item.src_meta), 'public', match[1] if match else None)]

    def close(self):
        self.provider.close()
