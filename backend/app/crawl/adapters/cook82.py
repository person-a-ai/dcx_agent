"""82cook title search, article bodies and comments; IP nodes are never read."""
import re
import time
from urllib.parse import parse_qs, urlencode, urljoin, urlsplit

from app.crawl.adapters.base import FetchedDoc, ListItem, ListPage
from app.crawl.adapters.community import CommunityAdapter, html_text, selected, text
from app.crawl.channels import channel_defaults
from app.crawl.ratelimit import ChannelLimiter
from app.crawl.urls import normalize_url

# search1: 1=title, 2=content, 3=nickname. T0 Step 5 chose titles only
# because body search also includes passing mentions.
SEARCH_SCOPE = '1'


def _date(value):
    match = re.search(r'(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})', value or '')
    if match:
        return f'{int(match[1]):04d}-{int(match[2]):02d}-{int(match[3]):02d}'
    match = re.search(r"'(\d{2})\.(\d{1,2})\.(\d{1,2})", value or '')
    return f'20{match[1]}-{int(match[2]):02d}-{int(match[3]):02d}' if match else None


def _author(value):
    # Punctuation-only placeholders identify no person; never hash them together.
    value = (value or '').strip()
    return value if any(char.isalnum() for char in value) else ''


def _page(cursor):
    page = 1 if cursor is None else int(cursor)
    if page < 1:
        raise ValueError('82cook page must be positive')
    return page


class Cook82Adapter(CommunityAdapter):
    source = 'cook82'
    origin = 'https://www.82cook.com'
    NO_RESULT_TEXT = ('검색결과가 없습니다',)

    def __init__(self, client=None, *, clock=time.monotonic, sleep=time.sleep):
        super().__init__(client, clock=clock, sleep=sleep)
        self._limiter = ChannelLimiter(*channel_defaults(self.source), clock=clock, sleep=sleep)

    def list_url(self, kw, cursor):
        return f'{self.origin}/entiz/enti.php?' + urlencode({
            'bn': 15, 'searchType': 'search', 'search1': SEARCH_SCOPE,
            'keys': kw, 'page': _page(cursor),
        })

    def parse_list(self, tree, cursor):
        items, seen = [], set()
        for row in tree.css('tbody tr:not(.noticeList)'):
            # The number-cell photolink duplicates the title link.
            link = row.css_first('td.title a[href*="read.php"]')
            if link is None:
                continue
            target = urljoin(f'{self.origin}/entiz/', link.attributes['href'])
            url = normalize_url(self.absolute_url(target), self.source)
            parts = urlsplit(url)
            query = parse_qs(parts.query)
            if parts.path != '/entiz/read.php' or not query.get('num'):
                raise ValueError('82cook result article ID missing')
            if url in seen:
                continue
            seen.add(url)
            regdate = row.css_first('td.regdate')
            comment = re.search(r'\d+', selected(row, 'td.title em'))
            items.append(ListItem(
                url, text(link), '',
                _date((regdate.attributes.get('title') if regdate else '') or text(regdate)),
                {'board': query.get('bn', ['15'])[0], 'num': query['num'][0],
                 'comment_count': int(comment[0]) if comment else 0,
                 'author': _author(selected(row, 'td.user_function'))},
            ))
        if not items:
            if any(marker in text(tree.body) for marker in self.NO_RESULT_TEXT):
                return ListPage([], None, 0)
            raise ValueError('82cook search results could not be parsed')

        current = _page(cursor)
        later = False
        for link in tree.css('a[href]'):
            target = urlsplit(urljoin(f'{self.origin}/entiz/', link.attributes['href'] or ''))
            pages = parse_qs(target.query).get('page', [])
            if (target.netloc == urlsplit(self.origin).netloc
                    and target.path == '/entiz/enti.php'
                    and any(page.isdigit() and int(page) > current for page in pages)):
                later = True
                break
        return ListPage(items, str(current + 1) if later else None, None)

    def parse_detail(self, tree, item):
        body = tree.css_first('#articleBody')
        if body is None:
            raise ValueError('82cook article body missing')
        comments = []
        for row in tree.css('ul.reples > li.rp'):
            content = row.css_first('p')
            if content is None:
                continue
            value = html_text(content.html)
            # Both recorded delReple rows contain real comments (and a deletion
            # control), not tombstones. Keep them unless the entire p is a
            # deletion placeholder; a discussion mentioning deletion is valid.
            if 'delReple' in row.attributes.get('class', '').split() and re.fullmatch(
                r'(?:삭제된 댓글입니다|작성자가 삭제한 댓글입니다)\.?\s*', value,
            ):
                continue
            stamp = row.css_first('.repleFunc em')
            # Only the first em is the date. Never read an IP node, even if
            # changed markup puts one first; later em values are not dates.
            if stamp is not None and 'ip' in stamp.attributes.get('class', '').split():
                stamp = None
            comments.append(self.comment(
                value, 0, _date(text(stamp)) or '', _author(selected(row, 'h5 strong')),
            ))
        query = parse_qs(urlsplit(item.url).query)
        # Explicit allowlist prevents transient authors or unexpected IP metadata
        # from entering the stored document.
        meta = {
            'board': query.get('bn', [item.src_meta.get('board', '15')])[0],
            'num': query.get('num', [item.src_meta.get('num', '')])[0],
            'comment_count': len(comments),
        }
        return FetchedDoc(
            selected(tree, 'h4.title.bbstitle') or item.title, html_text(body.html),
            comments, item.date, meta, 'public', _author(item.src_meta.get('author')) or None,
        )
