"""Browser QA data and worker-hook isolation, with networking forbidden."""

from collections import Counter
import importlib
import json
from pathlib import Path
import sys
from urllib.parse import parse_qs, urlsplit

import pytest

from app.config import settings
from app.crawl import report, worker
from app.crawl.adapters import REGISTRY
from app.crawl.adapters.base import AdapterBlocked, AdapterSkipped, FetchedDoc
from app.crawl.channels import NEW_CHANNELS, channel_defaults
from app.crawl.control import ReadQueue
from app.crawl.filters import FilterConfig
from app.crawl.ratelimit import ChannelLimiter
from app.crawl.schema import Doc
from app.crawl.writer import read_docs
from app.services.preprocessing import filter_documents


HOOK_MODULE = 'channel_expansion_qa'
EXPECTED_COUNTS = {'youtube_vlog': 6, 'threads': 25, 'naver_kin': 5, 'cook82': 8}


@pytest.fixture
def hook_environment(monkeypatch, tmp_path):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'qa_hooks'))
    monkeypatch.delenv('DCX_TEST_ADAPTER_MODULE', raising=False)
    monkeypatch.delenv('QA_THREADS_MODE', raising=False)
    monkeypatch.setattr(settings, 'author_salt_path', str(tmp_path / '.salt'))
    # Record originals before the hook's import-time registration.
    for source in NEW_CHANNELS:
        monkeypatch.setitem(REGISTRY, source, REGISTRY[source])
    monkeypatch.delitem(sys.modules, HOOK_MODULE, raising=False)
    yield
    # A cached hook would not register again in a later worker-hook test.
    sys.modules.pop(HOOK_MODULE, None)


@pytest.fixture
def hook(hook_environment, monkeypatch):
    monkeypatch.setenv('DCX_TEST_ADAPTER_MODULE', HOOK_MODULE)
    worker._load_hook()
    return sys.modules[HOOK_MODULE]


@pytest.mark.parametrize('module', [None, 'some_other_hook'])
def test_hook_is_inert_without_explicit_selection(hook_environment, monkeypatch, module):
    original = dict(REGISTRY)
    if module is not None:
        monkeypatch.setenv('DCX_TEST_ADAPTER_MODULE', module)
    else:
        worker._load_hook()
        assert HOOK_MODULE not in sys.modules
    importlib.import_module(HOOK_MODULE)
    assert REGISTRY == original


@pytest.mark.parametrize('keyword', ['에어컨 청소', '제습기'])
@pytest.mark.parametrize('source,count', EXPECTED_COUNTS.items())
def test_hook_keyword_data_and_skip_positions(hook, source, count, keyword):
    adapter = REGISTRY[source]()
    assert adapter.source == source
    assert type(adapter).__module__ == HOOK_MODULE
    options = (
        dict(videos_per_keyword=20, min_duration_s=60, max_duration_s=3600)
        if source == 'youtube_vlog' else {}
    )
    page = adapter.list_page(keyword, None, **options)
    assert page == adapter.list_page(keyword, None, **options)
    assert len(page.items) == page.total_hint == count
    assert page.next_cursor is None
    assert len({item.url for item in page.items}) == count
    for position, item in enumerate(page.items, 1):
        assert parse_qs(urlsplit(item.url).query)['k'] == [keyword]
        reason = None
        if source == 'youtube_vlog' and position % 3 == 0:
            reason = 'no_ko_captions'
        elif source == 'naver_kin' and position == 5:
            reason = 'deleted'
        if reason:
            with pytest.raises(AdapterSkipped) as error:
                adapter.fetch(item)
            assert error.value.reason == reason
            continue
        docs = adapter.fetch(item)
        assert len(docs) == (2 if source == 'youtube_vlog' else 1)
        assert all(isinstance(doc, FetchedDoc) for doc in docs)
        assert all(doc.access == 'public' and doc.author_raw == 'qa-author' for doc in docs)
        assert all(doc.title == item.title and doc.date == item.date and doc.body for doc in docs)
        if source == 'youtube_vlog':
            assert [doc.thread_key for doc in docs] == ['0-90', '90-180']
            assert all(doc.src_meta['segmenter'] == 'embedding' for doc in docs)
        else:
            assert docs[0].thread_key == ''


@pytest.mark.parametrize('source', EXPECTED_COUNTS)
def test_hook_empty_keyword(hook, source):
    page = REGISTRY[source]().list_page('qa-empty', None)
    assert page.items == []
    assert page.total_hint == 0
    assert page.next_cursor is None


def test_hook_threads_block_only_in_detail(hook, monkeypatch):
    monkeypatch.setenv('QA_THREADS_MODE', 'blocked')
    adapter = REGISTRY['threads']()
    page = adapter.list_page('에어컨 청소', None)
    assert len(page.items) == 25
    for item in page.items:
        with pytest.raises(AdapterBlocked) as error:
            adapter.fetch(item)
        assert error.value.host == 'threads.com'
    # The mode is confined to Threads; other channels still yield documents.
    for source in ('youtube_vlog', 'naver_kin', 'cook82'):
        adapter = REGISTRY[source]()
        assert adapter.fetch(adapter.list_page('에어컨 청소', None).items[0])


def _run_hook(collection, keywords, sources):
    filters = FilterConfig(date_from=None, date_to=None)
    # Preserve channel concurrency while removing real-site rate delays.
    limiters = {
        source: ChannelLimiter(channel_defaults(source)[0], 0) for source in sources
    }
    snapshot = worker.run_list(
        'S', collection=collection, keywords=keywords, sources=sources,
        filters=filters, limiters=limiters,
    )
    worker.run_detail(
        'S', snapshot, collection=collection, filters=filters,
        limiters=limiters, backoff_s=0.001,
    )
    return ReadQueue(collection / 'queue.sqlite')


def test_hook_data_survives_worker_writer_and_preprocessing(hook, tmp_path):
    queue = _run_hook(tmp_path, ['에어컨 청소', '제습기', 'qa-empty'], list(NEW_CHANNELS))
    docs = list(read_docs(tmp_path / 'docs'))
    assert Counter(doc['source'] for doc in docs) == {
        'youtube_vlog': 16, 'threads': 50, 'naver_kin': 8, 'cook82': 16,
    }
    assert len({doc['doc_id'] for doc in docs}) == 90
    assert {doc['kw'] for doc in docs} == {'에어컨 청소', '제습기'}
    for doc in docs:
        Doc.model_validate(doc)
        assert doc['fetch_level'] == 'full'
        assert doc['author_hash'] and doc['author_hash'] != 'qa-author'
        if doc['source'] == 'youtube_vlog':
            assert doc['src_meta']['segmenter'] == 'embedding'
    kept, removed = filter_documents(docs, [], [])
    assert len(kept) == 90 and sum(removed.values()) == 0
    assert all(doc['desc'] and doc['link'] for doc in kept)
    expected_skips = {'youtube_vlog': {'no_ko_captions': 4}, 'naver_kin': {'deleted': 2}}
    assert report.progress(queue)['skipped'] == expected_skips
    built = report.build_report(queue)
    assert built['totals']['urls_listed'] == 88
    assert built['totals']['doc_count'] == 90
    for source, reasons in expected_skips.items():
        assert built['channels'][source]['skip_reasons'] == reasons
    state = json.loads((tmp_path / 'worker_state.json').read_text())
    assert all(channel['status'] == 'done' for channel in state['channels'].values())


def test_hook_blocked_mode_pauses_worker(hook, monkeypatch, tmp_path):
    monkeypatch.setenv('QA_THREADS_MODE', 'blocked')
    _run_hook(tmp_path, ['에어컨 청소'], ['threads'])
    state = json.loads((tmp_path / 'worker_state.json').read_text())
    assert state['paused_channels'] == ['threads']
    assert state['channels']['threads']['status'] == 'paused_blocked'
    assert state['channels']['threads']['blocked'] == 20
    assert list(read_docs(tmp_path / 'docs')) == []
