"""One Crawl4AI browser per adapter, driven from synchronous worker threads.

No login, cookies, proxies or stealth options are configured (D-094, G2).
"""
import asyncio
from concurrent.futures import Future, wait
import importlib
import importlib.util
import os
from pathlib import Path
import sys
import threading
import time


def _default_crawler():
    crawl4ai = importlib.import_module('crawl4ai')
    return crawl4ai.AsyncWebCrawler(config=crawl4ai.BrowserConfig(headless=True, verbose=False))


class RenderBridge:
    _DRAIN_TIMEOUT_S = 0.2
    _JOIN_TIMEOUT_S = 0.2

    def __init__(self, crawler_factory=None):
        self._factory = crawler_factory or _default_crawler
        self._loop = asyncio.new_event_loop()
        self._crawler = None
        self._started = False
        self._closed = False
        self._pending = None
        self._lock = threading.Lock()
        self._state_lock = threading.Lock()
        self._shutdown_future = None
        self._shutdown_deadline = None
        self._close_error = None
        # Python cannot interrupt a thread blocked in synchronous native/OS
        # code. Such a thread must not prevent process exit; shutdown resumes
        # when that call returns, and later close calls can still join it.
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def _serve(self):
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_forever()
        finally:
            try:
                self._loop.run_until_complete(self._drain())
            finally:
                self._loop.close()

    async def _drain(self):
        pending = asyncio.all_tasks(self._loop) - {asyncio.current_task()}
        for task in pending:
            task.cancel()
        if pending:
            # wait_for(gather(...)) can itself hang waiting for cancellation
            # cleanup. wait() imposes a bound without awaiting that cleanup.
            await asyncio.wait(pending, timeout=self._DRAIN_TIMEOUT_S)
        # Interrupt stalled finally blocks, including new cleanup tasks.
        remaining = asyncio.all_tasks(self._loop) - {asyncio.current_task()}
        for task in remaining:
            task.cancel()
        await asyncio.sleep(0)
        for task in pending | remaining:
            if task.done() and not task.cancelled():
                task.exception()

    @classmethod
    def available(cls) -> bool:
        # A local capability check only; importing/starting the crawler here
        # would allocate browser resources during channel listing.
        try:
            if importlib.util.find_spec('crawl4ai') is None:
                return False
            configured = os.environ.get('PLAYWRIGHT_BROWSERS_PATH')
            root = (Path(configured) if configured else
                    Path.home() / ('Library/Caches/ms-playwright' if sys.platform == 'darwin'
                                   else '.cache/ms-playwright'))
            return root.is_dir() and any(
                path.name.startswith('chromium') and path.is_dir() for path in root.iterdir()
            )
        except Exception:
            # Missing packages, inaccessible homes and disappearing cache dirs
            # mean unavailable, never a broken channel-list request.
            return False

    def _submit(self, coroutine, *, stop_loop=False):
        # Unlike run_coroutine_threadsafe's proxy, this future is completed only
        # by the Task's done callback, after all cancellation cleanup has run.
        completion = Future()
        tasks = []

        def done(task):
            try:
                completion.set_result(task.result())
            except BaseException as exc:
                completion.set_exception(exc)
            finally:
                if stop_loop:
                    self._loop.stop()

        def start():
            task = self._loop.create_task(coroutine)
            tasks.append(task)
            task.add_done_callback(done)

        self._loop.call_soon_threadsafe(start)
        self._pending = completion
        return completion, lambda: tasks[0].cancel() if not tasks[0].done() else None

    def _run(self, operation, deadline):
        if self._pending is not None:
            # Do not cancel an earlier operation again: its finally block may
            # still be rolling back browser state.
            if not wait([self._pending], timeout=max(0, deadline - time.monotonic())).done:
                raise TimeoutError('Render cleanup is still pending')
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('Render deadline exceeded')
        with self._state_lock:
            if self._closed:
                raise RuntimeError('RenderBridge is closed')
            future, cancel = self._submit(operation())
        try:
            return future.result(remaining)
        except TimeoutError:
            if not future.done():
                try:
                    self._loop.call_soon_threadsafe(cancel)
                except RuntimeError:
                    if not self._loop.is_closed():
                        raise
            raise
        except asyncio.CancelledError:
            if self._closed:
                raise RuntimeError('RenderBridge is closed') from None
            raise

    def fetch_html(self, url: str, *, timeout_s: float) -> str:
        if self._closed:
            raise RuntimeError('RenderBridge is closed')
        deadline = time.monotonic() + timeout_s
        if not self._lock.acquire(timeout=max(0, timeout_s)):
            raise TimeoutError('Render bridge is busy')
        try:
            if self._closed:
                raise RuntimeError('RenderBridge is closed')
            return self._run(lambda: self._fetch(url), deadline)
        finally:
            self._lock.release()

    async def _fetch(self, url):
        try:
            if self._crawler is None:
                self._crawler = self._factory()
            if not self._started:
                try:
                    await self._crawler.start()
                except BaseException:
                    # A failed start can leave partially allocated resources.
                    # Never reuse it, even when best-effort close also fails.
                    try:
                        await self._close_crawler()
                    except Exception:
                        pass
                    raise
                self._started = True
            result = await self._arun(url)
            if not getattr(result, 'success', False) or not getattr(result, 'html', ''):
                raise ValueError('Crawler returned unsuccessful or empty HTML')
            return result.html
        except TimeoutError:
            raise
        except Exception as exc:
            raise ValueError('Render failed') from exc

    async def _close_crawler(self):
        crawler, self._crawler = self._crawler, None
        self._started = False
        if crawler is not None:
            await crawler.close()

    async def _arun(self, url):
        config = None
        try:
            crawl4ai = importlib.import_module('crawl4ai')
        except ImportError:
            pass  # An injected crawler can run without the optional package.
        else:
            config = crawl4ai.CrawlerRunConfig(wait_until='networkidle')
        return await self._crawler.arun(url, config=config)

    async def _shutdown(self, pending, deadline):
        async def graceful():
            if pending is not None:
                try:
                    # Cancelling teardown must not cancel the completion
                    # future: it represents actual rollback completion (R1).
                    await asyncio.shield(asyncio.wrap_future(pending))
                except asyncio.CancelledError:
                    if asyncio.current_task().cancelling():
                        raise
                except Exception:
                    pass
            await self._close_crawler()

        cleanup = self._loop.create_task(graceful())
        done, _ = await asyncio.wait(
            {cleanup}, timeout=max(0, deadline - time.monotonic()),
        )
        if not done:
            # _serve cancels and drains *all* tasks before closing the loop.
            raise TimeoutError('RenderBridge close timed out')
        cleanup.result()

    def close(self, timeout_s: float = 30):
        """Allow graceful cleanup, then cancel/drain and join within a bound.

        The first call sets a shared grace deadline. Concurrent callers attach
        to that teardown; later calls can allow timeout_s to join it again.
        Drain/join allowances add at most 0.4s to the grace period. Repeated
        calls preserve the teardown error, even after an earlier timeout.
        Only synchronous code blocking the loop can outlive this bound; that
        thread is a daemon and teardown continues when it becomes responsive.
        """
        deadline = time.monotonic() + max(0, timeout_s)
        with self._state_lock:
            if not self._closed:
                self._closed = True
                self._shutdown_deadline = deadline
                self._shutdown_future, _ = self._submit(
                    self._shutdown(self._pending, deadline), stop_loop=True,
                )
            deadline = max(deadline, self._shutdown_deadline)
        # Do not hold either lock while waiting: closing rejects new fetches
        # immediately and concurrent close calls attach to the same lifecycle.
        self._thread.join(timeout=max(
            0, deadline - time.monotonic() + self._DRAIN_TIMEOUT_S + self._JOIN_TIMEOUT_S,
        ))
        with self._state_lock:
            if self._thread.is_alive():
                if self._close_error is None:
                    self._close_error = TimeoutError('RenderBridge close timed out; loop thread is a daemon')
            elif self._close_error is None:
                try:
                    self._shutdown_future.result(timeout=0)
                except BaseException as exc:
                    self._close_error = exc
            if self._close_error is not None:
                raise self._close_error
