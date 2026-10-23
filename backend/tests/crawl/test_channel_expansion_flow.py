"""New sources retain their identities through crawl, prep and model features."""

from collections import Counter
from dataclasses import replace
import json

import numpy as np
import pytest

from app.config import settings
from app.crawl import report, worker
from app.crawl.adapters import REGISTRY
from app.crawl.adapters.base import AdapterSkipped, FetchedDoc, ListItem, ListPage
from app.crawl.channels import NEW_CHANNELS, channel_defaults
from app.crawl.control import ReadQueue
from app.crawl.filters import FilterConfig
from app.crawl.ratelimit import ChannelLimiter
from app.crawl.writer import read_docs
from app.model.features import INPUT_DIM, build_features
from app.prep.documents import filter_documents


def fake(source):
    class Fake:
        def __init__(self):
            self.source = source

        def list_page(self, kw, cursor=None, **options):
            return ListPage([
                ListItem(
                    url=f'https://{source}.example.invalid/{i}',
                    title=f'{source} 제목 {i}',
                    snippet=f'{kw} {source} 요약 {i}',
                    date='2026-10-01',
                    src_meta={'author': f'u{i}'},
                )
                for i in range(3)
            ], None, 3)

        def fetch(self, item):
            if source == 'youtube_vlog' and item.url.endswith('/2'):
                raise AdapterSkipped('no_ko_captions')
            return [FetchedDoc(
                title=item.title,
                body=f'{source} 본문 충분히 긴 내용 {item.url}',
                comments=[],
                date=item.date,
                src_meta={},
                access='public',
                author_raw='author',
                thread_key='',
            )]

    return Fake


@pytest.fixture
def channels(tmp_path, monkeypatch):
    monkeypatch.delenv('DCX_TEST_ADAPTER_MODULE', raising=False)
    monkeypatch.setattr(settings, 'author_salt_path', str(tmp_path / '.salt'))
    for source in NEW_CHANNELS:
        monkeypatch.setitem(REGISTRY, source, fake(source))


def test_new_channels_flow_to_prep_and_features(tmp_path, channels):
    filters = FilterConfig(date_from=None, date_to=None)
    limiters = {
        source: ChannelLimiter(channel_defaults(source)[0], 0) for source in NEW_CHANNELS
    }
    snapshot = worker.run_list(
        'S', collection=tmp_path, keywords=['에어컨'], sources=list(NEW_CHANNELS),
        filters=filters, limiters=limiters,
    )
    worker.run_detail(
        'S', snapshot, collection=tmp_path, filters=filters,
        limiters=limiters, backoff_s=0.001,
    )
    docs = list(read_docs(tmp_path / 'docs'))
    assert Counter(doc['source'] for doc in docs) == {
        'youtube_vlog': 2, 'threads': 3, 'naver_kin': 3, 'cook82': 3,
    }
    assert len(docs) == 3 * len(NEW_CHANNELS) - 1
    assert {doc['doc_id'][:3] for doc in docs} == {'yv_', 'th_', 'kn_', 'c8_'}
    assert all(doc['fetch_level'] == 'full' for doc in docs)
    kept, removed = filter_documents(docs, [], [])
    assert len(kept) == len(docs) and sum(removed.values()) == 0
    assert all(doc['desc'] and doc['link'] for doc in kept)
    features = build_features(kept, np.zeros((len(kept), 1024), dtype=np.float32))
    assert INPUT_DIM == 1032
    assert features.shape == (len(kept), INPUT_DIM)
    assert not features[:, 1024:1029].any()
    state = json.loads((tmp_path / 'worker_state.json').read_text())
    assert state['kind'] == 'detail'
    # Intentional skips are excluded from the per-channel detail attempt count.
    assert state['channels']['youtube_vlog']['attempts'] == 2


def test_report_counts_unique_completed_videos_shared_by_keywords(tmp_path, channels, monkeypatch):
    class SegmentedVlog(fake('youtube_vlog')):
        def fetch(self, item):
            doc = super().fetch(item)[0]
            return [replace(doc, thread_key=f'segment-{i}') for i in range(3)]

    monkeypatch.setitem(REGISTRY, 'youtube_vlog', SegmentedVlog)
    filters = FilterConfig(date_from=None, date_to=None)
    limiters = {source: ChannelLimiter(channel_defaults(source)[0], 0) for source in NEW_CHANNELS}
    keywords = ['에어컨', '에어컨 소음']
    snapshot = worker.run_list(
        'S', collection=tmp_path, keywords=keywords, sources=list(NEW_CHANNELS),
        filters=filters, limiters=limiters,
    )
    worker.run_detail(
        'S', snapshot, collection=tmp_path, filters=filters,
        limiters=limiters, backoff_s=0.001,
    )
    queue = ReadQueue(tmp_path / 'queue.sqlite')
    built = report.build_report(queue)
    vlog = built['channels']['youtube_vlog']
    assert Counter(doc['source'] for doc in read_docs(tmp_path / 'docs')) == {
        'youtube_vlog': 6, 'threads': 3, 'naver_kin': 3, 'cook82': 3,
    }
    assert vlog['docs'] == 6
    assert vlog['skipped'] == 1
    assert vlog['skip_reason'] == 'no_ko_captions'
    assert vlog['skip_reasons'] == {'no_ko_captions': 1}
    assert report.progress(queue)['skipped'] == {'youtube_vlog': {'no_ko_captions': 1}}
    assert built['totals']['doc_count'] == 15
    assert built['totals']['urls_done'] == 11
    # Both keywords retain attribution for the same two completed videos.
    cells = [built['matrix'][kw]['youtube_vlog'] for kw in keywords]
    assert [cell['urls_done'] for cell in cells] == [2, 2]
    assert [cell['full'] for cell in cells] == [6, 6]
    # First-keyword ownership includes the skipped video, so it is not the count.
    assert sum(cell['unique'] for cell in cells) == 3
    assert vlog['urls_done'] == 2
    assert {source: channel['urls_done'] for source, channel in built['channels'].items()} == {
        'youtube_vlog': 2, 'threads': 3, 'naver_kin': 3, 'cook82': 3,
    }
