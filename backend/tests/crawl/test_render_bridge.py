import asyncio
import importlib.util
from pathlib import Path
import sys
import threading
import time
from types import SimpleNamespace

import pytest

from app.crawl.render import RenderBridge


class FakeResult:
    def __init__(self, html, success=True):
        self.html, self.success = html, success


class FakeCrawler:
    def __init__(self):
        self.starts = self.closes = 0
        self.urls = []
        self.thread_ids = []

    async def start(self):
        self.starts += 1
        self.thread_ids.append(threading.get_ident())

    async def arun(self, url, config=None):
        self.urls.append(url)
        self.thread_ids.append(threading.get_ident())
        await asyncio.sleep(0)
        return FakeResult(f'<html>{url}</html>')

    async def close(self):
        self.closes += 1
        self.thread_ids.append(threading.get_ident())


@pytest.fixture(autouse=True)
def fake_crawl4ai(monkeypatch):
    # Never import the installed package or allow its browser factory in tests.
    def forbidden(**kwargs):
        pytest.fail('a real browser factory must never be used')
    module = SimpleNamespace(AsyncWebCrawler=forbidden, BrowserConfig=forbidden,
                             CrawlerRunConfig=lambda **kwargs: kwargs)
    monkeypatch.setitem(sys.modules, 'crawl4ai', module)
    return module


def test_fetch_html_runs_async_crawler_from_sync_code():
    crawler = FakeCrawler()
    bridge = RenderBridge(crawler_factory=lambda: crawler)
    try:
        assert bridge.fetch_html('https://example.invalid/a', timeout_s=5) == '<html>https://example.invalid/a</html>'
        assert bridge.fetch_html('https://example.invalid/b', timeout_s=5).endswith('/b</html>')
        assert crawler.starts == 1
        assert crawler.urls == ['https://example.invalid/a', 'https://example.invalid/b']
    finally:
        bridge.close()
    assert crawler.closes == 1
    assert set(crawler.thread_ids) == {bridge._thread.ident}
    assert bridge._thread.ident != threading.get_ident()


@pytest.mark.parametrize('result', [FakeResult('', False), FakeResult(''), FakeResult('html', False)])
def test_failed_render_raises_value_error(result):
    class Failing(FakeCrawler):
        async def arun(self, url, config=None):
            return result
    bridge = RenderBridge(crawler_factory=Failing)
    try:
        with pytest.raises(ValueError, match='Render failed') as error:
            bridge.fetch_html('https://example.invalid/', timeout_s=5)
        assert isinstance(error.value.__cause__, ValueError)
    finally:
        bridge.close()


def test_hung_render_times_out_and_bridge_stays_usable():
    cancelled = threading.Event()
    class Slow(FakeCrawler):
        async def arun(self, url, config=None):
            if url.endswith('/slow'):
                try:
                    await asyncio.sleep(60)
                finally:
                    cancelled.set()
            return FakeResult(f'<html>{url}</html>')
    bridge = RenderBridge(crawler_factory=Slow)
    try:
        with pytest.raises(TimeoutError):
            bridge.fetch_html('https://example.invalid/slow', timeout_s=0.05)
        assert cancelled.wait(2)
        assert bridge.fetch_html('https://example.invalid/ok', timeout_s=5).endswith('/ok</html>')
    finally:
        bridge.close()


def test_start_timeout_waits_for_rollback_and_replaces_crawler():
    cleaning, release, cleaned = threading.Event(), threading.Event(), threading.Event()

    class SlowStart(FakeCrawler):
        async def start(self):
            self.starts += 1
            try:
                await asyncio.sleep(60)
            finally:
                cleaning.set()
                while not release.is_set():
                    await asyncio.sleep(0.005)
                cleaned.set()

        async def close(self):
            assert cleaned.is_set(), 'close overlapped startup rollback'
            await super().close()

    stale, fresh = SlowStart(), FakeCrawler()
    crawlers = iter([stale, fresh])
    bridge = RenderBridge(crawler_factory=lambda: next(crawlers))
    try:
        before = time.monotonic()
        with pytest.raises(TimeoutError):
            bridge.fetch_html('https://example.invalid/', timeout_s=0.05)
        assert time.monotonic() - before < 0.5
        assert cleaning.wait(1)
        with pytest.raises(TimeoutError):
            bridge.fetch_html('https://example.invalid/retry', timeout_s=0.05)
        assert stale.starts == 1 and stale.urls == [] and stale.closes == 0
        release.set()
        assert bridge.fetch_html('https://example.invalid/ok', timeout_s=2).endswith('/ok</html>')
        assert bridge.fetch_html('https://example.invalid/later', timeout_s=2).endswith('/later</html>')
        assert stale.closes == 1 and fresh.starts == 1
    finally:
        release.set()
        bridge.close()
    assert fresh.closes == 1
    assert not bridge._thread.is_alive() and bridge._loop.is_closed()


def test_close_waits_for_cancelled_render_cleanup():
    cleaning, release, cleaned = threading.Event(), threading.Event(), threading.Event()
    errors = []

    class SlowRender(FakeCrawler):
        async def arun(self, url, config=None):
            try:
                await asyncio.sleep(60)
            finally:
                cleaning.set()
                while not release.is_set():
                    await asyncio.sleep(0.005)
                cleaned.set()

        async def close(self):
            assert cleaned.is_set(), 'close overlapped render cleanup'
            await super().close()

    crawler = SlowRender()
    bridge = RenderBridge(crawler_factory=lambda: crawler)

    def close_bridge():
        try:
            bridge.close()
        except BaseException as exc:
            errors.append(exc)

    closer = threading.Thread(target=close_bridge)
    try:
        with pytest.raises(TimeoutError):
            bridge.fetch_html('https://example.invalid/', timeout_s=0.05)
        assert cleaning.wait(1)
        with pytest.raises(TimeoutError):
            bridge.fetch_html('https://example.invalid/retry', timeout_s=0.05)
        closer.start()
        closer.join(timeout=0.05)
        assert closer.is_alive() and crawler.closes == 0
    finally:
        release.set()
        if closer.ident is not None:
            closer.join(timeout=2)
        bridge.close()
    assert errors == []
    assert crawler.closes == 1
    assert not closer.is_alive() and not bridge._thread.is_alive()
    assert bridge._loop.is_closed()


def test_failed_start_discards_crawler_even_if_best_effort_close_fails():
    original = OSError('startup failed')

    class Broken(FakeCrawler):
        async def start(self):
            raise original

        async def close(self):
            await super().close()
            raise OSError('cleanup failed')

    stale, fresh = Broken(), FakeCrawler()
    crawlers = iter([stale, fresh])
    bridge = RenderBridge(crawler_factory=lambda: next(crawlers))
    try:
        with pytest.raises(ValueError) as error:
            bridge.fetch_html('https://example.invalid/', timeout_s=1)
        assert error.value.__cause__ is original
        assert bridge.fetch_html('https://example.invalid/retry', timeout_s=1)
        assert stale.closes == 1 and fresh.starts == 1
    finally:
        bridge.close()


@pytest.mark.parametrize('phase', ['factory', 'start', 'arun', 'config'])
def test_crawler_exceptions_are_chained_value_errors(phase, fake_crawl4ai):
    original = OSError('crawler failed')

    class Failing(FakeCrawler):
        async def start(self):
            if phase == 'start':
                raise original
            await super().start()

        async def arun(self, url, config=None):
            if phase == 'arun':
                raise original
            return await super().arun(url, config=config)

    stale, fresh = Failing(), FakeCrawler()
    attempts = []

    def factory():
        attempts.append(True)
        if len(attempts) == 1:
            if phase == 'factory':
                raise original
            return stale
        return fresh

    if phase == 'config':
        def fail_config(**kwargs):
            raise original
        fake_crawl4ai.CrawlerRunConfig = fail_config
    bridge = RenderBridge(crawler_factory=factory)
    try:
        with pytest.raises(ValueError, match='Render failed') as error:
            bridge.fetch_html('https://example.invalid/', timeout_s=1)
        assert error.value.__cause__ is original
        if phase in {'factory', 'start'}:
            assert bridge.fetch_html('https://example.invalid/retry', timeout_s=1)
            assert len(attempts) == 2
            assert stale.closes == int(phase == 'start')
    finally:
        bridge.close()


@pytest.mark.parametrize('phase', ['start', 'arun'])
def test_crawler_timeout_error_is_preserved(phase):
    original = TimeoutError('crawler timeout')

    class Failing(FakeCrawler):
        async def start(self):
            if phase == 'start':
                raise original

        async def arun(self, url, config=None):
            raise original

    bridge = RenderBridge(crawler_factory=Failing)
    try:
        with pytest.raises(TimeoutError) as error:
            bridge.fetch_html('https://example.invalid/', timeout_s=1)
        assert error.value is original
    finally:
        bridge.close()


@pytest.mark.parametrize('fetch_first', [False, True])
def test_close_is_idempotent_and_stops_thread(fetch_first):
    crawler = FakeCrawler()
    bridge = RenderBridge(crawler_factory=lambda: crawler)
    if fetch_first:
        bridge.fetch_html('https://example.invalid/', timeout_s=5)
    bridge.close()
    bridge.close()
    assert crawler.closes == int(fetch_first)
    assert not bridge._thread.is_alive()
    assert bridge._loop.is_closed()
    before = time.monotonic()
    with pytest.raises(RuntimeError, match='closed'):
        bridge.fetch_html('https://example.invalid/', timeout_s=0.1)
    assert time.monotonic() - before < 0.1


def assert_bridge_stopped(bridge):
    assert not bridge._thread.is_alive()
    assert bridge._loop.is_closed()
    assert not asyncio.all_tasks(bridge._loop)


@pytest.mark.parametrize('phase', ['startup_rollback', 'crawler_close'])
def test_close_bounds_stalled_cleanup_and_repeats_the_timeout(phase):
    cleaning, release, cancelled = threading.Event(), threading.Event(), threading.Event()

    async def stalled_cleanup():
        cleaning.set()
        try:
            while not release.is_set():
                await asyncio.sleep(0.005)
        finally:
            cancelled.set()

    class Stalled(FakeCrawler):
        async def start(self):
            if phase == 'startup_rollback':
                try:
                    await asyncio.sleep(60)
                finally:
                    await stalled_cleanup()
            else:
                await super().start()

        async def close(self):
            await super().close()
            if phase == 'crawler_close':
                await stalled_cleanup()

    bridge = RenderBridge(crawler_factory=Stalled)
    try:
        if phase == 'startup_rollback':
            with pytest.raises(TimeoutError):
                bridge.fetch_html('https://example.invalid/', timeout_s=0.025)
            assert cleaning.wait(1)
        else:
            bridge.fetch_html('https://example.invalid/', timeout_s=1)
        before = time.monotonic()
        with pytest.raises(TimeoutError) as first:
            bridge.close(timeout_s=0.05)
        assert time.monotonic() - before < 1
        assert cleaning.is_set() and cancelled.is_set()
        assert_bridge_stopped(bridge)
        before = time.monotonic()
        with pytest.raises(TimeoutError) as second:
            bridge.close(timeout_s=0.05)
        assert second.value is first.value
        assert time.monotonic() - before < 0.1
        assert_bridge_stopped(bridge)
    finally:
        release.set()
        if bridge._thread.is_alive():
            bridge.close()


@pytest.mark.parametrize('second_timeout', [1, 0])
def test_concurrent_close_waits_for_same_teardown_and_fetch_rejects_immediately(second_timeout):
    closing, release, second_entered = threading.Event(), threading.Event(), threading.Event()
    errors = []

    class SlowClose(FakeCrawler):
        async def close(self):
            await super().close()
            closing.set()
            while not release.is_set():
                await asyncio.sleep(0.005)

    crawler = SlowClose()
    bridge = RenderBridge(crawler_factory=lambda: crawler)
    bridge.fetch_html('https://example.invalid/', timeout_s=1)

    def close_bridge(second=False):
        if second:
            second_entered.set()
        try:
            bridge.close(timeout_s=second_timeout if second else 1)
        except BaseException as exc:
            errors.append(exc)

    first = threading.Thread(target=close_bridge)
    second = threading.Thread(target=close_bridge, args=(True,))
    try:
        first.start()
        assert closing.wait(1)
        second.start()
        assert second_entered.wait(1)
        second.join(timeout=0.03)
        assert second.is_alive(), 'a requested teardown is not a completed teardown'
        before = time.monotonic()
        with pytest.raises(RuntimeError, match='closed'):
            bridge.fetch_html('https://example.invalid/', timeout_s=1)
        assert time.monotonic() - before < 0.1
    finally:
        release.set()
        first.join(timeout=2)
        if second.ident is not None:
            second.join(timeout=2)
        bridge.close()
    assert errors == []
    assert not first.is_alive() and not second.is_alive()
    assert crawler.closes == 1
    assert_bridge_stopped(bridge)


def test_close_does_not_wait_for_active_fetch_lock():
    rendering, release = threading.Event(), threading.Event()
    fetch_errors, close_errors = [], []

    class Active(FakeCrawler):
        async def arun(self, url, config=None):
            rendering.set()
            while not release.is_set():
                await asyncio.sleep(0.005)
            return FakeResult('<html>done</html>')

    bridge = RenderBridge(crawler_factory=Active)

    def fetch():
        try:
            bridge.fetch_html('https://example.invalid/', timeout_s=5)
        except BaseException as exc:
            fetch_errors.append(exc)

    def close():
        try:
            bridge.close(timeout_s=0.1)
        except BaseException as exc:
            close_errors.append(exc)

    fetcher, closer = threading.Thread(target=fetch), threading.Thread(target=close)
    before = time.monotonic()
    try:
        fetcher.start()
        assert rendering.wait(1)
        closer.start()
        until = time.monotonic() + 0.5
        while not bridge._closed and time.monotonic() < until:
            time.sleep(0.001)
        assert bridge._closed
        started = time.monotonic()
        with pytest.raises(RuntimeError, match='closed'):
            bridge.fetch_html('https://example.invalid/retry', timeout_s=1)
        assert time.monotonic() - started < 0.1
        closer.join(timeout=1)
        fetcher.join(timeout=1)
        assert time.monotonic() - before < 1
        assert not closer.is_alive() and not fetcher.is_alive()
        assert len(close_errors) == 1 and isinstance(close_errors[0], TimeoutError)
        assert len(fetch_errors) == 1 and isinstance(fetch_errors[0], RuntimeError)
        assert_bridge_stopped(bridge)
    finally:
        release.set()
        if closer.ident is not None:
            closer.join(timeout=2)
        fetcher.join(timeout=2)
        if bridge._thread.is_alive():
            bridge.close()


def test_close_error_still_stops_loop_and_is_preserved_on_retry():
    original = OSError('close failed')

    class BrokenClose(FakeCrawler):
        async def close(self):
            raise original

    bridge = RenderBridge(crawler_factory=BrokenClose)
    bridge.fetch_html('https://example.invalid/', timeout_s=1)
    for _ in range(2):
        with pytest.raises(OSError) as error:
            bridge.close(timeout_s=0.05)
        assert error.value is original
        assert_bridge_stopped(bridge)


def test_close_bounds_final_drain_of_background_tasks():
    cleaning, release = threading.Event(), threading.Event()
    tasks = []

    async def background():
        try:
            await asyncio.sleep(60)
        finally:
            cleaning.set()
            while not release.is_set():
                await asyncio.sleep(0.005)

    class BackgroundCrawler(FakeCrawler):
        async def start(self):
            await super().start()
            tasks.append(asyncio.create_task(background()))

    bridge = RenderBridge(crawler_factory=BackgroundCrawler)
    try:
        bridge.fetch_html('https://example.invalid/', timeout_s=1)
        before = time.monotonic()
        bridge.close(timeout_s=0.05)
        assert time.monotonic() - before < 1
        assert cleaning.is_set()
        assert all(task.done() for task in tasks)
        assert_bridge_stopped(bridge)
    finally:
        release.set()
        if bridge._thread.is_alive():
            bridge.close()


def test_blocked_loop_uses_daemon_and_repeated_close_finishes_teardown():
    # Python cannot interrupt synchronous native/OS calls in another thread.
    # The timeout must still bound close; release simulates that call returning.
    blocked, release = threading.Event(), threading.Event()

    class Blocking(FakeCrawler):
        async def start(self):
            blocked.set()
            release.wait(3)

    bridge = RenderBridge(crawler_factory=Blocking)
    try:
        with pytest.raises(TimeoutError):
            bridge.fetch_html('https://example.invalid/', timeout_s=0.025)
        assert blocked.wait(1)
        before = time.monotonic()
        with pytest.raises(TimeoutError) as first:
            bridge.close(timeout_s=0.05)
        assert time.monotonic() - before < 1
        assert bridge._thread.is_alive() and bridge._thread.daemon
        release.set()
        with pytest.raises(TimeoutError) as second:
            bridge.close(timeout_s=0.5)
        assert second.value is first.value
        assert_bridge_stopped(bridge)
    finally:
        release.set()
        if bridge._thread.is_alive():
            bridge.close()


def test_default_factory_uses_only_headless_configuration(fake_crawl4ai):
    browser_options, run_options = [], []
    crawler = FakeCrawler()
    fake_crawl4ai.BrowserConfig = lambda **kw: browser_options.append(kw) or kw
    fake_crawl4ai.CrawlerRunConfig = lambda **kw: run_options.append(kw) or kw
    fake_crawl4ai.AsyncWebCrawler = lambda *, config: crawler
    bridge = RenderBridge()
    try:
        bridge.fetch_html('https://example.invalid/', timeout_s=5)
    finally:
        bridge.close()
    assert browser_options == [{'headless': True, 'verbose': False}]
    assert run_options == [{'wait_until': 'networkidle'}]


def test_available_is_false_without_crawl4ai(monkeypatch):
    monkeypatch.setattr(importlib.util, 'find_spec', lambda name: None)
    assert RenderBridge.available() is False


@pytest.mark.parametrize('platform,relative', [
    ('darwin', 'Library/Caches/ms-playwright'), ('linux', '.cache/ms-playwright'),
])
def test_available_uses_platform_browser_path_without_launching(tmp_path, monkeypatch, platform, relative):
    monkeypatch.setattr(importlib.util, 'find_spec', lambda name: object())
    monkeypatch.setattr(sys, 'platform', platform)
    monkeypatch.setattr(Path, 'home', classmethod(lambda cls: tmp_path))
    monkeypatch.delenv('PLAYWRIGHT_BROWSERS_PATH', raising=False)
    root = tmp_path / relative
    assert RenderBridge.available() is False
    root.mkdir(parents=True)
    (root / 'firefox-1').mkdir()
    (root / 'chromium-file').touch()
    assert RenderBridge.available() is False
    (root / 'chromium-1').mkdir()
    assert RenderBridge.available() is True


def test_available_honors_explicit_path(tmp_path, monkeypatch):
    monkeypatch.setattr(importlib.util, 'find_spec', lambda name: object())
    monkeypatch.setenv('PLAYWRIGHT_BROWSERS_PATH', str(tmp_path / 'custom'))
    assert RenderBridge.available() is False
    (tmp_path / 'custom/chromium_headless_shell-1').mkdir(parents=True)
    assert RenderBridge.available() is True


@pytest.mark.parametrize('operation,error', [
    ('find_spec', ImportError), ('find_spec', ValueError),
    ('iterdir', PermissionError), ('iterdir', FileNotFoundError), ('is_dir', PermissionError),
])
def test_available_never_raises_on_import_or_filesystem_errors(tmp_path, monkeypatch, operation, error):
    monkeypatch.setattr(importlib.util, 'find_spec', lambda name: object())
    monkeypatch.setenv('PLAYWRIGHT_BROWSERS_PATH', str(tmp_path))
    def fail(*args):
        raise error('unavailable')
    monkeypatch.setattr(importlib.util if operation == 'find_spec' else Path, operation, fail)
    assert RenderBridge.available() is False


def test_explicit_browser_path_does_not_require_home_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(importlib.util, 'find_spec', lambda name: object())
    monkeypatch.setenv('PLAYWRIGHT_BROWSERS_PATH', str(tmp_path))
    (tmp_path / 'chromium-1').mkdir()
    def missing_home(cls):
        raise RuntimeError('home unavailable')
    monkeypatch.setattr(Path, 'home', classmethod(missing_home))
    assert RenderBridge.available() is True
