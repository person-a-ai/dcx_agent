from contextlib import closing

import httpx
import pytest

from app.config import settings
from app.context import store
from app.crawl import worker
from app.crawl.adapters import REGISTRY
from app.crawl.adapters.base import AdapterBlocked
from app.crawl.adapters.naver_blog import NaverBlogAdapter
from app.crawl.adapters.naver_cafe import NaverCafeAdapter
from app.crawl.filters import FilterConfig, check_doc, check_list
from app.crawl.queue import CrawlQueue
from app.crawl.ratelimit import ChannelLimiter


@pytest.fixture
def credentials(monkeypatch):
    monkeypatch.setattr(settings, 'naver_client_id', 'test-id')
    monkeypatch.setattr(settings, 'naver_client_secret', 'test-secret')


def entry(kind='blog', number=1):
    return dict(link=f'https://{kind}.naver.com/owner/{number}', title='<b>제목</b> &amp; 내용',
                description='요약 &lt;텍스트&gt;', bloggername='블로그', cafename='카페', postdate='20260925')


@pytest.mark.parametrize('cls,endpoint', [(NaverBlogAdapter, 'blog'), (NaverCafeAdapter, 'cafearticle')])
def test_api_mapping(credentials, cls, endpoint):
    def handle(request):
        assert request.url.path == f'/v1/search/{endpoint}.json'
        assert dict(request.url.params) == dict(query='검색어', display='100', start='1', sort='sim')
        assert request.headers['X-Naver-Client-Id'] == 'test-id'
        assert request.headers['X-Naver-Client-Secret'] == 'test-secret'
        kind = 'blog' if cls is NaverBlogAdapter else 'cafe'
        return httpx.Response(200, json=dict(total=2, start=1, display=100,
            items=[entry(kind), dict(entry(kind), link='https://example.com/profile')]))
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        page = cls(client).list_page('검색어')
    assert page.total_hint == 2 and page.next_cursor == 'date:1'
    item, = page.items
    assert item.title == '제목 & 내용' and item.snippet == '요약 <텍스트>'
    assert item.date == ('2026-09-25' if cls is NaverBlogAdapter else None)
    assert item.src_meta == ({'article_id': '1', 'blog_id': 'owner', 'blog_name': '블로그'}
                            if cls is NaverBlogAdapter else {'article_id': '1', 'cafe_id': 'owner', 'cafe': '카페'})


@pytest.mark.parametrize('status,error', [(429, AdapterBlocked), (401, ValueError), (403, ValueError)])
def test_api_errors(credentials, status, error):
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(status))) as client:
        with pytest.raises(error) as caught:
            NaverBlogAdapter(client).list_page('k')
    assert 'test-secret' not in str(caught.value)
    if error is ValueError:
        assert str(caught.value) == 'Naver API credentials rejected'


@pytest.mark.parametrize('total,count,cursor,expected', [
    (10000, 100, 'sim:901', 'date:1'), (10000, 100, 'date:901', None),
    (100, 100, 'sim:1', 'date:1'), (101, 100, 'sim:1', 'sim:101'),
    (10000, 99, 'date:1', None), (0, 0, 'date:1', None),
])
def test_api_stop_conditions(credentials, total, count, cursor, expected):
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200,
            json=dict(total=total, start=1, display=100, items=[entry()] * count)))) as client:
        assert NaverBlogAdapter(client).list_page('k', cursor).next_cursor == expected


@pytest.mark.parametrize('cap,expected', [(None, 250), (225, 225)])
def test_worker_both_sorts_unique_cap(credentials, tmp_path, monkeypatch, cap, expected):
    calls = []
    def handle(request):
        start, sort = int(request.url.params['start']), request.url.params['sort']
        calls.append((request.url.params["query"], sort, start))
        numbers = range(start, min(start + 100, 151))
        offset = 100 if sort == 'date' else 0
        return httpx.Response(200, json=dict(total=150, start=start, display=100,
            items=[entry(number=n + offset) for n in numbers]))
    config = {'perChannel': {'naver_blog': {'max_per_keyword': cap}}} if cap else {}
    store.write_json(tmp_path / 'manifest.json', {'config': config})
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        monkeypatch.setitem(REGISTRY, 'naver_blog', lambda: NaverBlogAdapter(client))
        worker.run_list('S', collection=tmp_path, keywords=['k', 'other'], sources=['naver_blog'],
                        filters=FilterConfig(date_from=None, date_to=None))
    for kw in ('k', 'other'):
        assert [(sort, start) for query, sort, start in calls if query == kw] == [
            ('sim', 1), ('sim', 101), ('date', 1), ('date', 101)]
    with closing(CrawlQueue(tmp_path / 'queue.sqlite')) as q:
        assert q.connection.execute('SELECT count(*) FROM urls').fetchone()[0] == expected
        assert q.connection.execute('SELECT count(*) FROM url_hits').fetchone()[0] == expected * 2
        assert {r[0] for r in q.connection.execute('SELECT total_hint FROM list_tasks')} == {150}


def test_cafe_detail_date_filter(credentials):
    def handle(request):
        if request.url.host == 'openapi.naver.com':
            return httpx.Response(200, json=dict(total=1, start=1, display=100, items=[entry('cafe')]))
        return httpx.Response(200, json={'result': {'article': {
            'contentHtml': '본문', 'writeDate': '2020-01-01', 'subject': '제목'}}})
    cfg = FilterConfig(date_from='2026-01-01', date_to='2026-12-31')
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        adapter = NaverCafeAdapter(client)
        item, = adapter.list_page('k').items
        assert item.date is None and check_list(item, cfg) is None
        doc, = adapter.fetch(item)
        assert check_doc(doc, cfg) == '①'


@pytest.mark.parametrize('status', [200, 403, 500])
def test_search_block_stops_host(tmp_path, monkeypatch, status):
    calls = []
    def handle(request):
        calls.append(request)
        return httpx.Response(status, text='검색 서비스 이용이 제한되었습니다')
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        for cls in (NaverBlogAdapter, NaverCafeAdapter):
            monkeypatch.setitem(REGISTRY, cls.source, lambda cls=cls: cls(client))
        worker.run_list('S', collection=tmp_path, keywords=['k'], sources=['naver_blog', 'naver_cafe'],
                        limiters={s: ChannelLimiter(1, 0) for s in ('naver_blog', 'naver_cafe')})
    assert len(calls) == 1
    state = store.read_json(tmp_path / 'worker_state.json')
    assert {c['status'] for c in state['channels'].values()} == {'paused_blocked'}
    with closing(CrawlQueue(tmp_path / 'queue.sqlite')) as q:
        assert {r[0] for r in q.connection.execute('SELECT attempts FROM list_tasks')} == {0}


def test_three_blocks_then_success_preserves_attempts(credentials, tmp_path, monkeypatch):
    calls = []
    def handle(request):
        calls.append(request)
        return httpx.Response(429) if len(calls) <= 3 else httpx.Response(200,
            json=dict(total=0, start=1, display=100, items=[]))
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        monkeypatch.setitem(REGISTRY, 'naver_blog', lambda: NaverBlogAdapter(client))
        worker.run_list('S', collection=tmp_path, keywords=['k'], sources=['naver_blog'])
    assert len(calls) == 5
    with closing(CrawlQueue(tmp_path / 'queue.sqlite')) as q:
        assert {tuple(r) for r in q.connection.execute('SELECT status,attempts FROM list_tasks')} == {('done', 1)}


@pytest.mark.parametrize('client_id,secret', [('', 'secret'), ('id', ''), ('x', 'secret'), ('id', 'x')])
def test_missing_credentials_keep_html(monkeypatch, client_id, secret):
    monkeypatch.setattr(settings, 'naver_client_id', client_id)
    monkeypatch.setattr(settings, 'naver_client_secret', secret)
    def handle(request):
        assert request.url.host == 'search.naver.com'
        return httpx.Response(200, text='<div class="not_found">검색 결과가 없습니다</div>')
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        assert NaverBlogAdapter(client).list_page('k').next_cursor is None


def test_worker_host_limiters(tmp_path, monkeypatch):
    captured = []
    class Blog(NaverBlogAdapter):
        def list_page(self, kw, cursor):
            captured.append(self)
            return worker.ListPage([], None, 0)
    class Cafe(NaverCafeAdapter):
        list_page = Blog.list_page
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200))) as client:
        monkeypatch.setitem(REGISTRY, 'naver_blog', lambda: Blog(client))
        monkeypatch.setitem(REGISTRY, 'naver_cafe', lambda: Cafe(client))
        worker.run_list('S', collection=tmp_path, keywords=['k'], sources=['naver_blog', 'naver_cafe'],
            limiters={'naver_blog': ChannelLimiter(4, .2), 'naver_cafe': ChannelLimiter(4, .4)})
    a, b = captured
    assert a.search_limiter is b.search_limiter
    assert (a.search_limiter.concurrency, a.search_limiter.min_interval_s) == (1, .4)
    assert a.api_limiter is b.api_limiter and a.api_limiter is not a.search_limiter
    assert (a.api_limiter.concurrency, a.api_limiter.min_interval_s) == (2, .1)
    assert a._limiter is not b._limiter


def test_detail_blocks_preserve_attempts_on_resume(tmp_path):
    with closing(CrawlQueue(tmp_path / 'queue.sqlite')) as q:
        q.add_list_tasks(worker._keywords(['k']), ['naver_blog'])
        q.add_urls([dict(url=entry()['link'], source='naver_blog', kw='k')])
        snapshot = q.take_snapshot()
        run = q.register_run('detail')
        for _ in range(3):
            row, = q.lease_urls(snapshot, 1, 60)
            assert row.attempts == 1 and not row.exhausted
            assert q.mark_failed_attempt(row.url_norm, row.source, 'AdapterBlocked',
                                         backoff_s=0, blocked=True) == 'pending'
        q.finish_run(run, 'paused')
        q.register_run('detail')
        row, = q.lease_urls(snapshot, 1, 60)
        assert row.attempts == 1 and not row.exhausted
        q.mark_done(row.url_norm, row.source, 1)
        assert q.counts()['done'] == 1
