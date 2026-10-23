from contextlib import closing
import csv
from dataclasses import replace

import pytest

from app.config import settings
from app.crawl import report, worker
from app.crawl.adapters import REGISTRY
from app.crawl.adapters.base import AdapterSkipped
from app.crawl.adapters.fixture import FixtureAdapter
from app.crawl.control import ReadQueue
from app.crawl.filters import FilterConfig
from app.crawl.queue import CrawlQueue
from app.crawl.writer import read_docs


@pytest.fixture
def corpus(tmp_path, monkeypatch):
    path = tmp_path / 'corpus.csv'
    with path.open('w') as f:
        w = csv.writer(f)
        w.writerow(['review'])
        w.writerows([[f'에어컨 소음 {i}'] for i in range(20)])
    monkeypatch.setattr(settings, 'fixture_corpus_path', str(path))
    monkeypatch.setattr(settings, 'enable_fixture_channel', True)
    monkeypatch.setattr(settings, 'author_salt_path', str(tmp_path / '.salt'))
    return path


def run(tmp_path, monkeypatch, corpus):
    class Skipping(FixtureAdapter):
        def fetch(self, item):
            if int(item.url.rsplit('/', 1)[1]) % 2:
                raise AdapterSkipped('no_ko_captions')
            return super().fetch(item)
    snapshot = worker.run_list('S', collection=tmp_path, keywords=['에어컨'], sources=['fixture'],
                               filters=FilterConfig(date_from=None, date_to=None))
    monkeypatch.setitem(REGISTRY, 'fixture', lambda: Skipping(corpus))
    worker.run_detail('S', snapshot, collection=tmp_path,
                      filters=FilterConfig(date_from=None, date_to=None), backoff_s=0.001)


def test_skipped_items_get_status_reason_and_no_document(tmp_path, corpus, monkeypatch):
    run(tmp_path, monkeypatch, corpus)
    with closing(CrawlQueue(tmp_path / 'queue.sqlite')) as q:
        rows = dict(q.connection.execute('SELECT status,count(*) FROM urls GROUP BY status').fetchall())
        reasons = {r[0] for r in q.connection.execute("SELECT last_error FROM urls WHERE status='skipped'")}
    assert rows == {'done': 10, 'skipped': 10}
    assert reasons == {'no_ko_captions'}
    assert len(list(read_docs(tmp_path / 'docs'))) == 10


def test_skipped_is_not_counted_as_attempt_block_or_parse_error(tmp_path, corpus, monkeypatch):
    run(tmp_path, monkeypatch, corpus)
    import json
    channel = json.loads((tmp_path / 'worker_state.json').read_text())['channels']['fixture']
    assert channel['attempts'] == 10
    assert channel['blocked'] == 0 and channel['parse_errors'] == 0
    assert not channel['status'].startswith('paused')


def test_report_and_progress_count_skips_by_reason(tmp_path, corpus, monkeypatch):
    run(tmp_path, monkeypatch, corpus)
    queue = ReadQueue(tmp_path / 'queue.sqlite')
    assert report.progress(queue)['skipped'] == {'fixture': {'no_ko_captions': 10}}
    built = report.build_report(queue)
    assert built['channels']['fixture']['skip_reasons'] == {'no_ko_captions': 10}
    assert built['channels']['fixture']['skipped'] == 10


def test_report_and_progress_count_restricted_exclusions_as_skips(tmp_path, corpus, monkeypatch):
    snapshot = worker.run_list('S', collection=tmp_path, keywords=['에어컨'], sources=['fixture'],
                               filters=FilterConfig(date_from=None, date_to=None))

    class Restricted(FixtureAdapter):
        exclude_restricted = True

        def fetch(self, item):
            return [replace(super().fetch(item)[0], access='restricted')]

    monkeypatch.setitem(REGISTRY, 'fixture', lambda: Restricted(corpus))
    worker.run_detail('S', snapshot, collection=tmp_path,
                      filters=FilterConfig(date_from=None, date_to=None), backoff_s=0.001)
    assert list(read_docs(tmp_path / 'docs')) == []
    with closing(CrawlQueue(tmp_path / 'queue.sqlite')) as q:
        assert q.counts()['excluded'] == 20
        assert {r[0] for r in q.connection.execute('SELECT last_error FROM urls')} == {'restricted'}
    queue = ReadQueue(tmp_path / 'queue.sqlite')
    assert report.progress(queue)['skipped'] == {'fixture': {'restricted': 20}}
    assert report.build_report(queue)['channels']['fixture']['skip_reasons'] == {'restricted': 20}
