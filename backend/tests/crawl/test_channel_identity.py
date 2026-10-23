from contextlib import closing
import json

import pytest
from pydantic import ValidationError

from app.crawl import worker
from app.crawl.adapters import REGISTRY
from app.crawl.adapters.base import ListItem, ListPage
from app.crawl.channels import COLLOQUIAL_CHANNELS, NEW_CHANNELS, channel_defaults
from app.crawl.filters import FilterConfig
from app.crawl.queue import CrawlQueue
from app.crawl.schema import Doc
from app.crawl.urls import doc_id, normalize_url
from app.context.labels import LABELS
from app.context.models import Channel
from app.routers.crawl_v2 import Config


@pytest.mark.parametrize('source,expected', [
    ('youtube_vlog', (2, 0)), ('threads', (1, 2.0)), ('naver_kin', (1, 0.5)), ('cook82', (1, 0.5)),
    ('naver_blog', (1, 0.5)), ('youtube', (2, 0)), ('fixture', (4, 0)),
])
def test_channel_defaults(source, expected):
    assert channel_defaults(source) == expected


def test_new_channels_are_known_everywhere():
    assert NEW_CHANNELS == ('youtube_vlog', 'threads', 'naver_kin', 'cook82')
    for source in NEW_CHANNELS:
        assert Channel(source).value == source
        assert source in LABELS['channels']
        assert Doc.model_fields['source'].annotation.__args__.count(source) == 1
    assert {'threads', 'cook82', 'naver_kin', 'youtube', 'naver_cafe', 'ppomppu', 'clien'} <= COLLOQUIAL_CHANNELS


@pytest.mark.parametrize('source,prefix', [('youtube_vlog', 'yv'), ('threads', 'th'), ('naver_kin', 'kn'), ('cook82', 'c8')])
def test_new_prefixes(source, prefix):
    assert doc_id(source, 'https://example.com/a').startswith(prefix + '_')


def test_kin_url_keeps_question_identity_only():
    url = 'https://kin.naver.com/qna/detail.naver?dirId=80901&docId=493036426&answerNo=4&qb=7JeQ'
    assert normalize_url(url, 'naver_kin') == 'https://kin.naver.com/qna/detail.naver?dirId=80901&docId=493036426'


def test_cook82_url_keeps_board_and_number_only():
    url = 'https://www.82cook.com/entiz/read.php?bn=15&num=4245917&page=1&searchType=search&search1=1&keys=x'
    assert normalize_url(url, 'cook82') == 'https://www.82cook.com/entiz/read.php?bn=15&num=4245917'


def test_threads_url_is_canonical():
    assert normalize_url('https://threads.net/@abc/post/DNG2tXiBjzN/?xmt=1', 'threads') == \
        'https://www.threads.com/@abc/post/DNG2tXiBjzN'


def test_vlog_config_validation():
    ok = Config(channels=['youtube_vlog'])
    assert ok.youtube_vlog.model_dump() == {'videos_per_keyword': 20, 'min_duration_s': 60, 'max_duration_s': 3600}
    with pytest.raises(ValidationError):
        Config(channels=['youtube_vlog'], youtube_vlog={'min_duration_s': 600, 'max_duration_s': 60})
    with pytest.raises(ValidationError):
        Config(channels=['youtube_vlog'], youtube_vlog={'videos_per_keyword': 0})


@pytest.mark.parametrize('vlog_config,expected', [
    ({'videos_per_keyword': 5, 'min_duration_s': 120, 'max_duration_s': 900}, (5, 120, 900)),
    ({}, (20, 60, 3600)),
    ({'min_duration_s': 120}, (20, 120, 3600)),
])
def test_worker_passes_vlog_options_and_caps_per_keyword(tmp_path, monkeypatch, vlog_config, expected):
    calls = []
    class Vlog:
        source = 'youtube_vlog'
        def list_page(self, kw, cursor, *, videos_per_keyword, min_duration_s, max_duration_s):
            calls.append((kw, videos_per_keyword, min_duration_s, max_duration_s))
            return ListPage([ListItem(f'https://www.youtube.com/watch?v={i:011d}', '', '', None, {})
                             for i in range(50)], None, 50)
        def fetch(self, item):
            return []
    monkeypatch.setitem(REGISTRY, 'youtube_vlog', Vlog)
    (tmp_path / 'manifest.json').write_text(json.dumps({'config': {'youtube_vlog': vlog_config}}))
    worker.run_list('S', collection=tmp_path, keywords=['에어컨'], sources=['youtube_vlog'],
                    filters=FilterConfig(date_from=None, date_to=None))
    assert calls == [('에어컨', *expected)]
    with closing(CrawlQueue(tmp_path / 'queue.sqlite')) as q:
        assert q.connection.execute("SELECT count(*) FROM urls WHERE source='youtube_vlog'").fetchone()[0] == expected[0]


@pytest.mark.parametrize('options', [
    {'min_duration_s': -1}, {'max_duration_s': 0},
    {'min_duration_s': 60, 'max_duration_s': 60},
])
def test_vlog_config_rejects_invalid_duration_bounds(options):
    with pytest.raises(ValidationError):
        Config(channels=['youtube_vlog'], youtube_vlog=options)


@pytest.mark.parametrize('url', [
    'https://youtu.be/AbC_123?si=abc&feature=share&t=10&pp=abc',
    'http://m.youtube.com/watch?v=AbC_123&utm_source=x#fragment',
    'https://www.youtube.com/watch?v=AbC_123',
])
def test_vlog_urls_use_youtube_normalization(url):
    assert normalize_url(url, 'youtube_vlog') == 'https://www.youtube.com/watch?v=AbC_123'
