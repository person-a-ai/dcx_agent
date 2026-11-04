from functools import lru_cache

from kiwipiepy import Kiwi

from app.config import settings


@lru_cache(maxsize=1)
def _kiwi():
    return Kiwi(num_workers=max(1, settings.kiwi_workers))


def tokenize(text, pos) -> list[str]:
    allowed = set(pos)
    return [token.form for token in _kiwi().tokenize(text) if token.tag in allowed]


def tokenize_many(texts, pos):
    """Yield token lists in input order; Kiwi spreads the batch over its worker threads."""
    allowed = set(pos)
    for tokens in _kiwi().tokenize(list(texts)):
        yield [token.form for token in tokens if token.tag in allowed]
