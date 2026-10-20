"""Network-free browser QA adapters, enabled only by the worker's module hook.

Use DCX_TEST_ADAPTER_MODULE=channel_expansion_qa with this directory on
PYTHONPATH. QA_THREADS_MODE=blocked simulates detail-stage login blocks.
"""

import os
from urllib.parse import urlencode, urlsplit

from app.crawl.adapters import REGISTRY
from app.crawl.adapters.base import AdapterBlocked, AdapterSkipped, FetchedDoc, ListItem, ListPage


COUNTS = {'youtube_vlog': 6, 'threads': 25, 'naver_kin': 5, 'cook82': 8}


def _adapter(source):
    class QAAdapter:
        def __init__(self):
            self.source = source

        def list_page(self, kw, cursor=None, **options):
            # Accept the worker's vlog size/duration options; QA data stays fixed.
            count = 0 if kw == 'qa-empty' else COUNTS[source]
            query = urlencode({'k': kw})
            return ListPage(
                items=[
                    ListItem(
                        url=f'https://qa.invalid/{source}/{i}?{query}',
                        title=f'{kw} {source} 글 {i}',
                        snippet=f'{kw} 요약 {i}',
                        date='2026-10-01',
                        src_meta={'author': f'qa{i}'},
                    )
                    for i in range(count)
                ],
                next_cursor=None,
                total_hint=count,
            )

        def fetch(self, item):
            index = int(urlsplit(item.url).path.rsplit('/', 1)[1])
            if source == 'threads' and os.environ.get('QA_THREADS_MODE') == 'blocked':
                raise AdapterBlocked('Threads requires login', host='threads.com')
            if source == 'youtube_vlog' and index % 3 == 2:
                raise AdapterSkipped('no_ko_captions')
            if source == 'naver_kin' and index == 4:
                raise AdapterSkipped('deleted')
            parts = 2 if source == 'youtube_vlog' else 1
            return [
                FetchedDoc(
                    title=item.title,
                    body=f'{item.title} 생활 이야기 구간 {part}',
                    comments=[],
                    date=item.date,
                    src_meta={'segmenter': 'embedding'} if source == 'youtube_vlog' else {},
                    access='public',
                    author_raw='qa-author',
                    thread_key=f'{part * 90}-{(part + 1) * 90}' if source == 'youtube_vlog' else '',
                )
                for part in range(parts)
            ]

    return QAAdapter


if os.environ.get('DCX_TEST_ADAPTER_MODULE') == __name__:
    for _source in COUNTS:
        REGISTRY[_source] = _adapter(_source)
