"""Per-channel defaults shared by the worker, status API and keyword prompts."""

NEW_CHANNELS = ('youtube_vlog', 'threads', 'naver_kin', 'cook82')

_DEFAULTS = {
    'youtube': (2, 0), 'youtube_vlog': (2, 0),
    'threads': (1, 2.0),
    'naver_blog': (1, 0.5), 'naver_cafe': (1, 0.5), 'naver_kin': (1, 0.5),
    'clien': (1, 0.5), 'ppomppu': (1, 0.5), 'cook82': (1, 0.5),
}

COLLOQUIAL_CHANNELS = frozenset({'youtube', 'youtube_vlog', 'naver_cafe', 'ppomppu', 'clien',
                                'community', 'threads', 'cook82', 'naver_kin'})


def channel_defaults(source: str) -> tuple[int, float]:
    """Return (concurrency, min_interval_s) used when a channel has no saved limits."""
    return _DEFAULTS.get(source, (4, 0))
