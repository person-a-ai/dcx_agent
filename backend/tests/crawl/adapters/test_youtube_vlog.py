import json

import numpy as np
import pytest
import yt_dlp

from app.config import settings
from app.crawl.adapters.base import AdapterBlocked, AdapterSkipped, ListItem


def json3(blocks):
    events, t = [], 0
    for word, seconds in blocks:
        for _ in range(seconds // 5):
            events.append({'tStartMs': t * 1000, 'dDurationMs': 5000, 'segs': [{'utf8': f'{word} 이야기 {t}'}]})
            t += 5
    return json.dumps({'events': events}).encode()


class TopicEmbedder:
    def embed(self, texts, input_type='document'):
        return np.asarray([[1.0, 0.0] if '청소' in t else [0.0, 1.0] for t in texts], dtype=np.float32)


VIDEOS = {
    'manualvid01': {'id': 'manualvid01', 'title': '여름 일상', 'duration': 240, 'channel': '채널A', 'channel_id': 'UC_A',
                    'timestamp': 1790000000, 'view_count': 10,
                    'subtitles': {'ko': [{'ext': 'json3', 'url': 'https://cap/manual'}]},
                    'automatic_captions': {'ko': [{'ext': 'json3', 'url': 'https://cap/auto'}]}},
    'autovid0002': {'id': 'autovid0002', 'title': '집안일', 'duration': 240, 'channel': '채널B', 'channel_id': 'UC_B',
                    'timestamp': 1790000000, 'subtitles': {},
                    'automatic_captions': {'ko': [{'ext': 'vtt', 'url': 'https://cap/vtt'}, {'ext': 'json3', 'url': 'https://cap/auto2'}]}},
    'nocaption03': {'id': 'nocaption03', 'title': '무음', 'duration': 240, 'channel_id': 'UC_C',
                    'subtitles': {}, 'automatic_captions': {'en': [{'ext': 'json3', 'url': 'https://cap/en'}]}},
}
CAPTIONS = {'https://cap/manual': json3([('청소', 120), ('전기세', 120)]),
            'https://cap/auto2': json3([('청소', 240)])}


@pytest.fixture
def ytdl(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, 'author_salt_path', str(tmp_path / 'salt'))
    calls = []

    class Response:
        def __init__(self, body):
            self.body = body
        def read(self):
            return self.body

    class YoutubeDL:
        def __init__(self, options):
            self.options = options
        def __enter__(self):
            return self
        def __exit__(self, *a):
            pass
        def extract_info(self, url, download=True):
            calls.append(('extract', url, self.options))
            if url.startswith('ytsearch'):
                return {'entries': [
                    {'id': 'short000001', 'duration': 30, 'title': 'shorts'},
                    {'id': 'manualvid01', 'duration': 240, 'title': '여름 일상', 'timestamp': 1790000000},
                    None,
                    {'id': 'toolong0001', 'duration': 7200, 'title': 'live'},
                    {'id': 'autovid0002', 'duration': 240, 'title': '집안일'},
                    {'id': 'nodur000001', 'title': 'unknown length'},
                ]}
            return dict(VIDEOS[url.rsplit('=', 1)[1]])
        def urlopen(self, url):
            calls.append(('urlopen', url))
            return Response(CAPTIONS[url])

    monkeypatch.setattr(yt_dlp, 'YoutubeDL', YoutubeDL)
    return calls


def item(video):
    return ListItem(f'https://www.youtube.com/watch?v={video}', '', '', None, {'video_id': video})


def test_list_appends_vlog_filters_duration_and_limits(ytdl):
    from app.crawl.adapters.youtube_vlog import YoutubeVlogAdapter
    page = YoutubeVlogAdapter(embedder_factory=TopicEmbedder).list_page(
        '에어컨', None, videos_per_keyword=1, min_duration_s=60, max_duration_s=3600)
    assert ytdl[0][1] == 'ytsearch2:에어컨 브이로그'
    assert [i.url for i in page.items] == ['https://www.youtube.com/watch?v=manualvid01']
    assert page.next_cursor is None


def test_fetch_prefers_manual_captions_and_splits_by_topic(ytdl):
    from app.crawl.adapters.youtube_vlog import YoutubeVlogAdapter
    docs = YoutubeVlogAdapter(embedder_factory=TopicEmbedder).fetch(item('manualvid01'))
    assert ('urlopen', 'https://cap/manual') in ytdl
    assert [(d.src_meta['segment_start_s'], d.src_meta['segment_end_s']) for d in docs] == [(0, 120), (120, 240)]
    assert [d.thread_key for d in docs] == ['0-120', '120-240']
    assert {d.src_meta['caption_kind'] for d in docs} == {'manual'}
    assert {d.src_meta['segmenter'] for d in docs} == {'embedding'}
    assert docs[0].title == '여름 일상' and docs[0].author_raw == 'UC_A' and docs[0].access == 'public'
    assert '전기세' not in docs[0].body


def test_fetch_uses_json3_auto_captions_when_no_manual(ytdl):
    from app.crawl.adapters.youtube_vlog import YoutubeVlogAdapter
    docs = YoutubeVlogAdapter(embedder_factory=TopicEmbedder).fetch(item('autovid0002'))
    assert ('urlopen', 'https://cap/auto2') in ytdl
    assert {d.src_meta['caption_kind'] for d in docs} == {'auto'}


def test_no_korean_captions_is_skipped(ytdl):
    from app.crawl.adapters.youtube_vlog import YoutubeVlogAdapter
    with pytest.raises(AdapterSkipped) as raised:
        YoutubeVlogAdapter(embedder_factory=TopicEmbedder).fetch(item('nocaption03'))
    assert raised.value.reason == 'no_ko_captions'


def test_unavailable_embedder_falls_back_to_fixed(ytdl):
    from app.crawl.adapters.youtube_vlog import YoutubeVlogAdapter
    def missing():
        raise RuntimeError('Voyage API key is not configured')
    docs = YoutubeVlogAdapter(embedder_factory=missing).fetch(item('manualvid01'))
    assert {d.src_meta['segmenter'] for d in docs} == {'fixed'}
    assert [d.thread_key for d in docs] == ['0-90', '90-180', '180-240']


def test_bot_check_is_blocked(monkeypatch, ytdl):
    from app.crawl.adapters.youtube_vlog import YoutubeVlogAdapter
    def refuse(self, url, download=True):
        raise yt_dlp.utils.DownloadError("Sign in to confirm you're not a bot")
    monkeypatch.setattr(yt_dlp.YoutubeDL, 'extract_info', refuse)
    with pytest.raises(AdapterBlocked):
        YoutubeVlogAdapter(embedder_factory=TopicEmbedder).fetch(item('manualvid01'))


def test_original_korean_auto_captions_take_priority(monkeypatch, ytdl):
    from app.crawl.adapters.youtube_vlog import YoutubeVlogAdapter
    monkeypatch.setitem(VIDEOS['autovid0002'], 'automatic_captions', {
        'ko': [{'ext': 'json3', 'url': 'https://cap/manual'}],
        'ko-orig': [{'ext': 'json3', 'url': 'https://cap/auto2'}],
    })
    docs = YoutubeVlogAdapter(embedder_factory=TopicEmbedder).fetch(item('autovid0002'))
    assert ('urlopen', 'https://cap/auto2') in ytdl
    assert {d.src_meta['caption_kind'] for d in docs} == {'auto'}
    assert all('전기세' not in d.body for d in docs)


@pytest.mark.parametrize('captions', [
    {'events': []},
    {'events': [{'tStartMs': 0, 'segs': [{'utf8': '[음악]'}]}]},
])
def test_empty_cues_are_skipped_without_creating_embedder(monkeypatch, ytdl, captions):
    from app.crawl.adapters.youtube_vlog import YoutubeVlogAdapter
    monkeypatch.setitem(CAPTIONS, 'https://cap/manual', json.dumps(captions).encode())

    def forbidden():
        pytest.fail('empty captions must not create an embedder')

    with pytest.raises(AdapterSkipped) as raised:
        YoutubeVlogAdapter(embedder_factory=forbidden).fetch(item('manualvid01'))
    assert raised.value.reason == 'no_ko_captions'


def test_korean_captions_without_json3_are_skipped(monkeypatch, ytdl):
    from app.crawl.adapters.youtube_vlog import YoutubeVlogAdapter
    monkeypatch.setitem(VIDEOS['autovid0002'], 'automatic_captions', {
        'ko': [{'ext': 'vtt', 'url': 'https://cap/vtt'}],
    })
    with pytest.raises(AdapterSkipped) as raised:
        YoutubeVlogAdapter(embedder_factory=TopicEmbedder).fetch(item('autovid0002'))
    assert raised.value.reason == 'no_ko_captions'


@pytest.mark.parametrize('status', [403, 429])
def test_caption_http_blocks_are_reported(monkeypatch, ytdl, status):
    from urllib.error import HTTPError
    from app.crawl.adapters.youtube_vlog import YoutubeVlogAdapter

    def refuse(self, url):
        raise HTTPError(url, status, 'blocked', None, None)

    monkeypatch.setattr(yt_dlp.YoutubeDL, 'urlopen', refuse)
    with pytest.raises(AdapterBlocked):
        YoutubeVlogAdapter(embedder_factory=TopicEmbedder).fetch(item('manualvid01'))


def test_default_embedder_is_created_lazily_and_reused(monkeypatch, ytdl):
    from app.crawl.adapters.youtube_vlog import YoutubeVlogAdapter
    from app.vectors import embedder
    calls = []

    def factory():
        calls.append('created')
        return TopicEmbedder()

    monkeypatch.setattr(embedder, 'get_embedder', factory)
    adapter = YoutubeVlogAdapter()
    adapter.list_page('에어컨', None)
    assert calls == []
    for _ in range(2):
        docs = adapter.fetch(item('manualvid01'))
        assert [d.thread_key for d in docs] == ['0-120', '120-240']
    assert calls == ['created']
