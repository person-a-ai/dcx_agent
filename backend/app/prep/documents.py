"""Stage-three document intake shared by the prep pipeline (moved from services/preprocessing, v1-cleanup)."""
import json
from pathlib import Path
import re

from app.config import settings
from app.context.labels import LABELS
from app.crawl.writer import read_docs


def crawl_docs(sid: str, session: dict) -> list[dict]:
    """Read the active collection chain child-first so the child's doc_id wins."""
    cid = session.get('collectionId')
    base = Path(settings.local_data_dir) / 'crawl' / sid / 'collections'
    collections = set()
    docs = {}
    while True:
        if not isinstance(cid, str) or not re.fullmatch(r'c[1-9][0-9]*', cid):
            raise ValueError('Invalid crawl collection id')
        if cid in collections:
            raise ValueError('Cyclic crawl collection chain')
        collections.add(cid)
        root = base / cid
        try:
            manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
        except (OSError, ValueError):
            raise ValueError(f'수집본을 읽을 수 없습니다 ({cid})') from None
        for doc in read_docs(root / 'docs'):
            docs.setdefault(doc['doc_id'], doc)
        cid = manifest.get('parent')
        if not cid:
            return list(docs.values())


def _export_fields(item: dict) -> dict:
    """desc/cafe/link are read by the stage-five export (model/export.py) and the chat search results."""
    source = item.get('source', '')
    comments = '\n'.join(comment.get('text', '') for comment in item.get('comments', []))
    return {
        **item,
        'desc': (item.get('body', '') + '\n' + comments)[:4000],
        'cafe': item.get('src_meta', {}).get('cafe') or LABELS['channels'].get(source, source),
        'link': item.get('url', ''),
    }


def _passes_quality(item: dict, min_body_chars: int = 10) -> bool:
    if item.get('fetch_level') == 'snippet':
        description = item.get('snippet', '') or item.get('body', '')
        return len(item.get('title', '')) >= 5 or len(description) >= 10
    # Full documents (including title-less YouTube threads) use body alone.
    return len(item.get('body', '')) >= min_body_chars


def filter_documents(documents, ad_filter=(), excluded=(), min_body_chars=10, *, full_text=False):
    """D-084–086 rules; full_text uses uncapped body/comments for ad matching."""
    seen = set()
    filtered = []
    removed = dict(ad=0, excluded_source=0, duplicate=0, too_short=0)
    for idx, raw in enumerate(documents):
        item = _export_fields(raw)
        text = item.get('title', '') + ' ' + item.get('desc', '')
        if full_text:
            text = item.get('body', '') + '\n' + '\n'.join(
                c.get('text', '') for c in item.get('comments', []))
        cafe = item.get('cafe', '').lower()
        cafe_id = str((item.get('src_meta') or {}).get('cafe_id') or '').lower()
        identity = item['doc_id']
        reason = None
        if any(ad.lower() in text.lower() for ad in ad_filter):
            reason = 'ad'
        elif any(ex.lower() in cafe or ex.lower() in cafe_id or
                 (full_text and ex.lower() == item.get('source', '').lower()) for ex in excluded):
            reason = 'excluded_source'
        elif identity in seen:
            reason = 'duplicate'
        else:
            seen.add(identity)
            if not _passes_quality(item, min_body_chars):
                reason = 'too_short'
        if reason:
            removed[reason] += 1
            continue
        item['idx'] = idx
        filtered.append(item)
    return filtered, removed
