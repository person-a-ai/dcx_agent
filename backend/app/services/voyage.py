from typing import Literal

import numpy as np
import voyageai

from app.config import settings


def get_embeddings(texts: list[str], input_type: Literal['document', 'query'] | None = None,
                   api_key: str | None = None) -> list[list[float]]:
    """Voyage AI multilingual embeddings for Korean."""
    if len(texts) == 0:
        return []
    # The client waits and retries rate-limit errors instead of returning zero vectors.
    vo = voyageai.Client(api_key=api_key or settings.voyage_api_key, max_retries=3)
    # D-256: stored document vectors used no input_type; preserve that request.
    input_kwargs = {'input_type': 'query'} if input_type == 'query' else {}
    all_embs = []
    for i in range(0, len(texts), 128):
        batch = texts[i : i + 128]
        batch = [t[:2000] if len(t) > 2000 else t for t in batch]
        batch = [t if t.strip() else "빈 문서" for t in batch]
        try:
            result = vo.embed(batch, model=settings.embed_model, output_dimension=settings.embed_dim, **input_kwargs)
            rows = [[0.0] * settings.embed_dim for _ in batch]
            for row, embedding in enumerate(result.embeddings[:len(batch)]):
                try:
                    vector = np.asarray(embedding, dtype=np.float32)
                except (TypeError, ValueError, OverflowError):
                    continue
                if vector.shape == (settings.embed_dim,) and np.isfinite(vector).all():
                    rows[row] = vector.tolist()
            all_embs.extend(rows)
        except Exception:
            # Provider errors can contain credentials; never print their payload.
            all_embs.extend([[0.0] * settings.embed_dim for _ in batch])
    return all_embs
