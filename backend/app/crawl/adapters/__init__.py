"""Channel factories read configuration when called, never at import time."""

from collections.abc import Callable
from contextlib import contextmanager

from app.config import settings
from app.crawl.adapters.base import (
    AdapterBlocked,
    AdapterSkipped,
    ChannelAdapter,
    FetchedDoc,
    ListItem,
    ListPage,
)
from app.crawl.adapters.fixture import FixtureAdapter
from app.crawl.adapters.youtube import YoutubeAdapter
from app.crawl.adapters.youtube_vlog import YoutubeVlogAdapter
from app.crawl.adapters.clien import ClienAdapter
from app.crawl.adapters.ppomppu import PpomppuAdapter
from app.crawl.adapters.naver_blog import NaverBlogAdapter
from app.crawl.adapters.naver_cafe import NaverCafeAdapter
from app.crawl.adapters.naver_kin import NaverKinAdapter
from app.crawl.adapters.cook82 import Cook82Adapter
from app.crawl.adapters.threads import ThreadsAdapter


REGISTRY: dict[str, Callable[[], ChannelAdapter]] = {
    "naver_blog": NaverBlogAdapter,
    "naver_cafe": NaverCafeAdapter,
    "naver_kin": NaverKinAdapter,
    "cook82": Cook82Adapter,
    "threads": ThreadsAdapter,
    "fixture": lambda: FixtureAdapter(settings.fixture_corpus_path),
    "youtube": YoutubeAdapter,
    "youtube_vlog": YoutubeVlogAdapter,
    "clien": ClienAdapter,
    "ppomppu": PpomppuAdapter,
}


@contextmanager
def managed_adapter(factory):
    adapter = factory()
    try:
        yield adapter
    finally:
        close = getattr(adapter, "close", None)
        if callable(close):
            close()


def available_sources() -> list[str]:
    sources = []
    for source, factory in REGISTRY.items():
        # Built-in real adapters expose a class method: no HTTP client allocation.
        check = getattr(factory, 'is_available', None)
        if isinstance(getattr(check, '__self__', None), type):
            if check():
                sources.append(source)
            continue
        with managed_adapter(factory) as adapter:
            if adapter.is_available():
                sources.append(source)
    return sources


__all__ = [
    "AdapterBlocked", "AdapterSkipped", "ChannelAdapter", "FetchedDoc", "ListItem", "ListPage",
    "REGISTRY", "available_sources",
]
