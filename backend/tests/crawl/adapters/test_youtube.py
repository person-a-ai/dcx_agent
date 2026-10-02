import copy
from datetime import datetime, timezone
import json
from pathlib import Path

import pytest
import yt_dlp

from app.config import settings
from app.crawl.hashing import author_hash


FIXTURES = Path(__file__).resolve().parents[2] / 'fixtures' / 'http' / 'youtube'


@pytest.fixture
def recording(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, 'author_salt_path', str(tmp_path / 'salt'))
    listing = json.loads((FIXTURES / 'list.json').read_text())
    details = [json.loads((FIXTURES / f'detail-{i}.json').read_text()) for i in range(1, 4)]
    calls = []

    class YoutubeDL:
        def __init__(self, options):
            self.options = options

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def extract_info(self, url, download=True):
            calls.append((url, download, self.options))
            if url.startswith('ytsearch'):
                return copy.deepcopy(listing)
            return copy.deepcopy(next(d for d in details if d['id'] in url))

    monkeypatch.setattr(yt_dlp, 'YoutubeDL', YoutubeDL)
    return listing, details, calls


def test_list_returns_videos_as_items(recording):
    from app.crawl.adapters.youtube import YoutubeAdapter

    listing, _, calls = recording
    adapter = YoutubeAdapter()
    page = adapter.list_page('에어컨 소음', None)
    assert adapter.source == 'youtube'
    assert adapter.is_available()
    assert len(page.items) == 10
    assert page.next_cursor is None
    assert page.total_hint == 10
    for item, entry in zip(page.items, listing['entries'], strict=True):
        assert item.url == entry['url']
        assert item.title == ''
        assert item.snippet == entry['description']
        assert item.src_meta['video_id'] == entry['id']
    assert calls[0][0:2] == ('ytsearch10:에어컨 소음', False)
    assert calls[0][2]['extract_flat'] is True


def test_fetch_groups_replies_into_threads(recording):
    from app.crawl.adapters.youtube import YoutubeAdapter

    _, details, _ = recording
    adapter = YoutubeAdapter()
    items = adapter.list_page('에어컨 소음', None).items
    for item, detail in zip(items, details):
        docs = adapter.fetch(item)
        description, *threads = docs
        assert description.thread_key == ''
        assert description.body == detail['description']
        assert description.comments == []
        roots = [c for c in detail['comments'] if c['parent'] == 'root']
        assert [d.thread_key for d in threads] == [c['id'] for c in roots]
        for doc, root in zip(threads, roots, strict=True):
            assert doc.body == root['text']
            assert doc.author_raw == root['author_id']
            assert doc.date == datetime.fromtimestamp(root['timestamp'], timezone.utc).date().isoformat()
            replies = [c for c in detail['comments'] if c['parent'] == root['id']]
            assert [c.text for c in doc.comments] == [c['text'] for c in replies]
            assert [c.depth for c in doc.comments] == [1] * len(replies)
            assert [c.author_hash for c in doc.comments] == [author_hash('youtube', c['author_id']) for c in replies]


def test_video_meta_in_src_meta_not_title(recording):
    from app.crawl.adapters.youtube import YoutubeAdapter

    _, details, _ = recording
    adapter = YoutubeAdapter()
    for item, detail in zip(adapter.list_page('에어컨 소음', None).items, details):
        for doc in adapter.fetch(item):
            assert doc.title == ''
            assert doc.src_meta['video_title'] == detail['title']
            assert doc.src_meta['video_id'] == detail['id']
            assert doc.src_meta['channel'] == detail['channel']
            assert doc.access == 'public'


def test_max_comments_respected(recording):
    from app.crawl.adapters.youtube import YoutubeAdapter

    _, details, calls = recording
    adapter = YoutubeAdapter(max_comments=2)
    item = adapter.list_page('에어컨 소음', None).items[1]
    docs = adapter.fetch(item)
    threads = [d for d in docs if d.thread_key]
    assert len(threads) + sum(len(d.comments) for d in threads) == 2
    assert threads[0].body == details[1]['comments'][0]['text']
    assert threads[0].comments[0].text == details[1]['comments'][1]['text']
    assert calls[-1][1] is False
    assert calls[-1][2]['getcomments'] is True
    assert calls[-1][2]['extractor_args']['youtube']['max_comments'] == ['2', 'all', '10', '5']


@pytest.mark.parametrize('status', [403, 429, 500])
@pytest.mark.parametrize('method', ['list', 'fetch'])
def test_wrapped_http_errors(recording, monkeypatch, status, method):
    from io import BytesIO
    from yt_dlp.networking.common import Response
    from yt_dlp.networking.exceptions import HTTPError
    from yt_dlp.utils import DownloadError, ExtractorError
    from app.crawl.adapters.base import AdapterBlocked
    from app.crawl.adapters.youtube import YoutubeAdapter

    adapter = YoutubeAdapter()
    item = adapter.list_page('에어컨 소음', None).items[0]
    http_error = HTTPError(Response(BytesIO(), item.url, {}, status))
    wrapped = ExtractorError('request failed', cause=http_error)
    error = DownloadError('extraction failed', exc_info=(type(wrapped), wrapped, None))

    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(yt_dlp.YoutubeDL, 'extract_info', fail)
    with pytest.raises(AdapterBlocked if status in (403, 429) else DownloadError):
        if method == 'list':
            adapter.list_page('에어컨 소음', None)
        else:
            adapter.fetch(item)


def test_availability_without_dependency(monkeypatch):
    import sys
    from app.crawl.adapters.youtube import YoutubeAdapter

    monkeypatch.setitem(sys.modules, 'yt_dlp', None)
    assert not YoutubeAdapter().is_available()


@pytest.mark.parametrize('limit', [0, 1, 3, 30])
def test_worker_override_and_zero_limit(recording, limit):
    from app.crawl.adapters.youtube import YoutubeAdapter

    _, _, calls = recording
    adapter = YoutubeAdapter(max_comments=2)
    item = adapter.list_page('에어컨 소음', None).items[0]
    docs = adapter.fetch(item, max_comments=limit)
    assert sum(bool(d.thread_key) + len(d.comments) for d in docs) == limit
    assert calls[-1][2]['getcomments'] is (limit > 0)
    assert calls[-1][2]['extractor_args']['youtube']['max_comments'][0] == str(limit)
    assert adapter.max_comments == 2


def test_reply_order_and_orphans(recording):
    from app.crawl.adapters.youtube import YoutubeAdapter

    _, details, _ = recording
    root, reply, _, orphan = details[1]['comments']
    details[1]['comments'] = [reply, orphan, root]
    adapter = YoutubeAdapter()
    item = adapter.list_page('에어컨 소음', None).items[1]
    threads = [d for d in adapter.fetch(item) if d.thread_key]
    assert len(threads) == 1
    assert threads[0].thread_key == root['id']
    assert [c.text for c in threads[0].comments] == [reply['text']]


def test_empty_comments_and_description(recording):
    from app.crawl.adapters.youtube import YoutubeAdapter

    _, details, _ = recording
    details[0]['comments'] = None
    adapter = YoutubeAdapter()
    item = adapter.list_page('에어컨 소음', None).items[0]
    assert [d.thread_key for d in adapter.fetch(item)] == ['']
    details[0]['description'] = ''
    assert adapter.fetch(item) == []


def test_bounded_search_and_invalid_options(recording):
    from app.crawl.adapters.youtube import YoutubeAdapter

    _, _, calls = recording
    adapter = YoutubeAdapter(videos_per_keyword=2)
    page = adapter.list_page('소음', None)
    assert len(page.items) == page.total_hint == 2
    assert calls[-1][0] == 'ytsearch2:소음'
    with pytest.raises(ValueError, match='cursor'):
        adapter.list_page('소음', '2')
    with pytest.raises(ValueError, match='videos_per_keyword'):
        YoutubeAdapter(videos_per_keyword=0)
    with pytest.raises(ValueError, match='max_comments'):
        YoutubeAdapter(max_comments=-1)
    with pytest.raises(ValueError, match='max_comments'):
        adapter.fetch(page.items[0], max_comments=-1)


@pytest.mark.parametrize('message', ["Sign in to confirm you're not a bot", "confirm you’re not a bot", "Video unavailable"])
@pytest.mark.parametrize('method', ['list', 'fetch'])
def test_bot_confirmation_download_error(recording, monkeypatch, message, method):
    from yt_dlp.utils import DownloadError
    from app.crawl.adapters.base import AdapterBlocked
    from app.crawl.adapters.youtube import YoutubeAdapter

    adapter = YoutubeAdapter()
    item = adapter.list_page('test', None).items[0]
    def fail(*args, **kwargs):
        raise DownloadError(message)
    monkeypatch.setattr(yt_dlp.YoutubeDL, 'extract_info', fail)
    with pytest.raises(DownloadError if message == 'Video unavailable' else AdapterBlocked):
        if method == 'list':
            adapter.list_page('test', None)
        else:
            adapter.fetch(item)


@pytest.mark.parametrize('ext,payload', [
    ('json3', json.dumps({'events': [
        {'segs': [{'utf8': '첫 '}, {'utf8': '문장\n둘째 문장'}]},
        {'segs': [{'utf8': '둘째 문장\n마지막   문장'}]}, {'tStartMs': 100}]})),
    ('vtt', 'WEBVTT\nKind: captions\n\n1\n00:00:00.000 --> 00:00:02.000\n<c>첫 문장</c>\n둘째 문장\n\n'
            'cue-id\n00:00:02.000 --> 00:00:04.000 align:start\n둘째 문장\n마지막   문장\n\nNOTE ignored\nmetadata'),
    ('srv3', '<timedtext><body><p><s>첫 </s><s>문장</s>\n둘째 문장</p>'
             '<p>둘째 문장\n마지막   문장</p></body></timedtext>'),
])
def test_caption_parsing(ext, payload):
    from app.crawl.adapters.youtube import _caption_text

    assert _caption_text(payload, ext) == '첫 문장 둘째 문장 마지막 문장'


@pytest.mark.parametrize('language', ['ko', 'ko-KR', 'ko-orig'])
@pytest.mark.parametrize('manual', [True, False])
def test_korean_subtitle_document(recording, monkeypatch, language, manual):
    import httpx
    from app.crawl.adapters.youtube import YoutubeAdapter

    _, details, _ = recording
    info = details[0]
    info['automatic_captions'] = {'ko': [{'ext': 'json3', 'url': 'https://caption.test/auto'}]}
    if manual:
        info['subtitles'] = {language: [
            {'ext': 'vtt', 'url': 'https://caption.test/vtt'},
            {'ext': 'json3', 'url': 'https://caption.test/manual'}]}
    else:
        info['automatic_captions'][language] = info['automatic_captions'].pop('ko')
    info['availability'] = 'needs_auth'
    calls = []
    def get(url, **kwargs):
        calls.append((url, kwargs))
        return httpx.Response(200, json={'events': [{'segs': [{'utf8': '진료 여정 ' * 5000}]}]},
                              request=httpx.Request('GET', url))
    monkeypatch.setattr(httpx, 'get', get)
    adapter = YoutubeAdapter()
    docs = adapter.fetch(adapter.list_page('진료', None).items[0])
    subtitle, = [d for d in docs if d.thread_key == 'subtitle']
    assert subtitle.title == '' and subtitle.comments == []
    assert subtitle.body == ('진료 여정 ' * 5000)[:20000]
    assert subtitle.date == docs[0].date
    assert subtitle.access == 'restricted'
    assert subtitle.author_raw == info['channel_id']
    assert subtitle.src_meta == {**docs[0].src_meta, 'doc_kind': 'subtitle',
                                 'subtitle_kind': 'manual' if manual else 'auto'}
    assert docs[0].src_meta['doc_kind'] == 'description'
    assert all(d.src_meta['doc_kind'] == 'comment' for d in docs[2:])
    assert calls == [('https://caption.test/' + ('manual' if manual else 'auto'),
                      {'timeout': 20, 'follow_redirects': True})]


@pytest.mark.parametrize('failure', [404, 429, 'timeout', 'parse', 'shape'])
def test_subtitle_failure_preserves_other_docs(recording, monkeypatch, caplog, failure):
    import httpx
    from app.crawl.adapters.youtube import YoutubeAdapter

    _, details, _ = recording
    adapter = YoutubeAdapter()
    item = adapter.list_page('진료', None).items[0]
    expected = adapter.fetch(item)
    url = 'https://caption.test/caption?token=secret'
    details[0]['subtitles'] = {'ko': [{'ext': 'json3', 'url': url}]}
    def get(*args, **kwargs):
        if failure == 'timeout':
            raise httpx.ReadTimeout(url)
        return httpx.Response(failure if isinstance(failure, int) else 200,
                              text='{}' if failure == 'shape' else 'bad json',
                              request=httpx.Request('GET', url))
    monkeypatch.setattr(httpx, 'get', get)
    assert adapter.fetch(item) == expected
    assert 'Skipping unavailable YouTube subtitles' in caplog.text
    assert 'secret' not in caplog.text and url not in caplog.text


@pytest.mark.parametrize('mode', ['no-korean', 'constructor', 'override'])
def test_subtitles_no_request(recording, monkeypatch, mode):
    import httpx
    from app.crawl.adapters.youtube import YoutubeAdapter

    _, details, _ = recording
    tracks = {'en' if mode == 'no-korean' else 'ko': [
        {'ext': 'json3', 'url': 'https://caption.test/subtitle'}]}
    details[0].update(subtitles=tracks, automatic_captions=tracks)
    def forbidden(*args, **kwargs):
        pytest.fail('caption request must be skipped')
    monkeypatch.setattr(httpx, 'get', forbidden)
    adapter = YoutubeAdapter(subtitles=mode != 'constructor')
    item = adapter.list_page('진료', None).items[0]
    docs = adapter.fetch(item, **({'subtitles': False} if mode == 'override' else {}))
    assert docs and all(d.thread_key != 'subtitle' for d in docs)


@pytest.mark.parametrize('ext,payload', [
    ('vtt', 'WEBVTT\n\n00:00:00.000 --> 00:00:01.000\n진료 &amp; 수납'),
    ('srv3', '<timedtext><body><p>진료 &amp; 수납</p></body></timedtext>'),
])
def test_caption_format_fallback(recording, monkeypatch, ext, payload):
    import httpx
    from app.crawl.adapters.youtube import YoutubeAdapter

    _, details, _ = recording
    url = 'https://caption.test/' + ext
    details[0]['subtitles'] = {'ko': [{'ext': ext, 'url': url}]}
    details[0]['automatic_captions'] = {'ko': [{'ext': 'json3', 'url': 'https://caption.test/auto'}]}
    def get(requested, **kwargs):
        assert requested == url
        return httpx.Response(200, text=payload, request=httpx.Request('GET', url))
    monkeypatch.setattr(httpx, 'get', get)
    adapter = YoutubeAdapter()
    docs = adapter.fetch(adapter.list_page('진료', None).items[0])
    subtitle, = [d for d in docs if d.thread_key == 'subtitle']
    assert subtitle.body == '진료 & 수납'
    assert subtitle.src_meta['subtitle_kind'] == 'manual'
