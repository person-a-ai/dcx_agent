"""Durable preparation, with a single writer per immutable preparation key."""
from concurrent.futures import ThreadPoolExecutor
import fcntl
import json
import os
from pathlib import Path
import re
import tempfile
import time
from threading import Event
from types import SimpleNamespace

import numpy as np

from app.config import settings
from app.context import store
from app.context.stale import clear_stale
from app.context.versions import version_dir
from app.prep.clean import clean_html, strip_boilerplate, token_text
from app.prep.config import PrepConfig, analyzer_version, prep_key
from app.prep.report import stage3_report
from app.prep.tokens import tokenize_many
from app.prep.documents import iter_crawl_docs, iter_filtered
from app.vectors.embedder import EmbedderUnconnected, FakeEmbedder, VoyageEmbedder, get_embedder, embedder_name
from app.vectors.store import VectorStore
from app.work.status import HEARTBEAT_INTERVAL

SHARD_ROWS = 10_000
DOC_SHARD_ROWS = 5_000
BATCH_ROWS = 128


def _jsonl(path, rows):
    store.atomic_write(path, ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows))


def _text(doc):
    return '\n'.join([doc.get('title', ''), doc.get('body', ''),
                      *(comment.get('text', '') for comment in doc.get('comments', []))])


def _embed(embedder, texts):
    vectors = np.zeros((len(texts), embedder.dim), dtype=np.float32)
    failed = np.ones(len(texts), dtype=bool)
    batches = [np.arange(start, min(start + BATCH_ROWS, len(texts))) for start in range(0, len(texts), BATCH_ROWS)]
    # Batches write disjoint rows, so several provider requests can run at once.
    with ThreadPoolExecutor(max(1, getattr(embedder, 'concurrency', 1))) as pool:
        list(pool.map(lambda indexes: _embed_batch(embedder, texts, indexes, vectors, failed), batches))
    return vectors, failed.tolist()


def _embed_batch(embedder, texts, indexes, vectors, failed):
    for _ in range(3):
        try:
            result = np.asarray(embedder.embed([texts[i][:2000] for i in indexes]), dtype=np.float32)
            if result.shape != (len(indexes), embedder.dim):
                continue
            valid = np.isfinite(result).all(axis=1) & (np.linalg.norm(result, axis=1) > 0)
            valid &= (np.abs(result) <= np.finfo(np.float16).max).all(axis=1)
            vectors[indexes[valid]] = result[valid]
            failed[indexes[valid]] = False
            indexes = indexes[~valid]
            if not len(indexes):
                break
        except EmbedderUnconnected:
            raise
        except Exception:
            # Provider payloads may include credentials or document text.
            continue


def _retry_failed(vectors, embedder, lookup, checkpoint):
    """Retry stored failures once per run, preserving successful rows and shard shape.

    Publish replacement bytes before clearing failure flags. A crash between the
    two writes leaves rows marked failed and safely retryable on the next run.
    """
    if not vectors.index.exists():
        return True
    records = [json.loads(line) for line in vectors.index.read_text().splitlines() if line.strip()]
    groups = {}
    for record in records:
        groups.setdefault(record['shard'], []).append(record)
    failed_ids = {record['doc_id'] for record in records if record.get('failed')}
    if not failed_ids:
        return True
    # Only failures need their documents; look them up instead of loading every document.
    by_id = lookup(failed_ids)
    for shard, group in groups.items():
        retry = [record for record in group if record.get('failed') and record['doc_id'] in by_id]
        if not retry:
            continue
        if not checkpoint():
            return False
        matrix, failed = _embed(embedder, [_text(by_id[record['doc_id']]) for record in retry])
        _, replacement = vectors.get([record['doc_id'] for record in group])
        for record, vector, flag in zip(retry, matrix, failed):
            replacement[record['row']] = vector
            record['failed'] = flag
        # Keep the original row layout: VectorStore readers derive dimensions
        # from the index's complete row count for each shard.
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=vectors.directory, delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(replacement.astype(np.float16).tobytes())
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, vectors.directory / f'shard-{shard:05d}.f16')
            _jsonl(vectors.index, records)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    return True


def _checkpoint(ctx, done, total, **extra):
    detail = {'done_shards': done, 'total_shards': total, **extra}
    ctx.heartbeat(done / max(total, 1), detail)
    while ctx.should_pause() and not ctx.should_stop():
        time.sleep(.1)
        ctx.heartbeat(done / max(total, 1), detail)
    return not ctx.should_stop()


def _publish(sid, version, root, cfg, manifest, *, reused=False):
    with store.locked(sid):
        path = version_dir(sid, version) / 'session.json'
        session = store.read_json(path)
        if session is not None:
            from app.prep.guards import assert_ready
            ref = assert_ready(sid, session, cfg)
            if ref != dict(collectionId=manifest['collectionId'], prepKey=root.name):
                raise store.StoreError('전처리 대상 수집본이 바뀌었습니다. 다시 실행하세요.')
            session['prep'] = dict(config=cfg.model_dump(),
                                   derivedRef=dict(collectionId=manifest['collectionId'], prepKey=root.name),
                                   status='done', savedAt=store.now(), reused=reused)
            store.write_json(path, session)
            clear_stale(sid, version, 'stage3', already_locked=True)


def run_prep(ctx, sid: str, version: str) -> Path:
    session = store.read_json(version_dir(sid, version) / 'session.json')
    if session is None:
        raise ValueError('Session version not found')
    cid = session.get('collectionId')
    if not isinstance(cid, str) or not re.fullmatch(r'c[1-9][0-9]*', cid):
        raise ValueError('Invalid crawl collection id')
    values = {**session.get('prep', {}).get('config', {}), **getattr(ctx, 'args', {}).get('config', {})}
    cfg = PrepConfig.model_validate(values)
    from app.prep.guards import assert_ready
    assert_ready(sid, session, cfg)
    unconnected = None
    try:
        if cfg.embedder == settings.embed_backend:
            embedder = get_embedder()
        else:
            embedder = FakeEmbedder() if cfg.embedder == 'fake' else VoyageEmbedder()
    except EmbedderUnconnected as error:
        if cfg.embedder == 'fake':
            raise
        # Identity only: defer the error until the non-embedding outputs are durable.
        unconnected = error
        embedder = SimpleNamespace(name=cfg.embedder, model=settings.embed_model, dim=settings.embed_dim)
    if (embedder.model, embedder.dim) != (cfg.embedModel, cfg.embedDim):
        raise ValueError('Preparation embedding model/dimension must match configured embedder')
    key = prep_key(cid, cfg, embedder)
    root = Path(settings.local_data_dir) / 'derived' / sid / cid / key
    root.mkdir(parents=True, exist_ok=True)
    with (root / '.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        manifest = store.read_json(root / 'manifest.json')
        if manifest and manifest.get('collectionFinalized') is not True:
            # Old results may have snapshotted an unfinished crawl. Rebuild all
            # shards, including vectors, rather than resume/reuse that snapshot.
            import shutil
            for artifact in root.iterdir():
                if artifact.name != '.lock':
                    shutil.rmtree(artifact) if artifact.is_dir() else artifact.unlink()
            manifest = None
        if manifest and manifest['status'] == 'done':
            _publish(sid, version, root, cfg, manifest, reused=True)
            return root
        if manifest is None:
            manifest = dict(collectionId=cid, prepKey=key, config=cfg.model_dump(), collectionFinalized=True,
                            embedder=dict(name=embedder.name, model=embedder.model, dim=embedder.dim),
                            analyzer=analyzer_version(), createdAt=store.now(), counts={}, progress={})
        manifest['embedderName'] = embedder_name(manifest['embedder'])
        manifest['status'] = 'running'
        store.write_json(root / 'manifest.json', manifest)
        try:
            documents = iter_crawl_docs(sid, session)
            return _run(ctx, sid, version, root, cfg, embedder, documents, manifest, unconnected)
        except Exception as error:
            if isinstance(error, EmbedderUnconnected):
                error.prep_counts = manifest['counts']
            manifest['status'] = 'failed'
            store.write_json(root / 'manifest.json', manifest)
            raise


class _Stopped(Exception):
    """The run was stopped while documents were being written."""


def _clean(raw, cfg, replacements):
    doc = dict(raw)
    phrases = cfg.boilerplate.get(doc.get('source', ''), [])
    doc['title'] = clean_html(doc.get('title', ''))
    if 'snippet' in doc:
        doc['snippet'] = clean_html(doc['snippet'])
    doc['body'], count = strip_boilerplate(clean_html(doc.get('body', '')), phrases)
    doc['comments'] = []
    for comment in raw.get('comments', []):
        text, n = strip_boilerplate(clean_html(comment.get('text', '')), phrases)
        doc['comments'].append({**comment, 'text': text})
        count += n
    if count:
        source = doc.get('source', '')
        replacements[source] = replacements.get(source, 0) + count
    return doc


def _parts_per_shard():
    return (SHARD_ROWS + DOC_SHARD_ROWS - 1) // DOC_SHARD_ROWS


def _part_path(root, kind, part):
    return root / kind / f'part-{part:05d}.jsonl'


def _read_part(root, part):
    path = _part_path(root, 'docs', part)
    if not path.exists():
        return []
    with path.open(encoding='utf-8') as stream:
        return [json.loads(line) for line in stream if line.strip()]


def _shard_parts(shard):
    first = (shard - 1) * _parts_per_shard() + 1
    return range(first, first + _parts_per_shard())


def _run(ctx, sid, version, root, cfg, embedder, documents, manifest, unconnected=None):
    # Large imports do not fit in memory, so documents stream to disk once and
    # every later pass (tokens, vectors) reads them back one part at a time.
    replacements = {}
    removed = dict(ad=0, excluded_source=0, duplicate=0, too_short=0, excluded_channel=0)
    beat_at = [time.monotonic()]

    def beat(**detail):
        if time.monotonic() - beat_at[0] >= HEARTBEAT_INTERVAL:
            if not _checkpoint(ctx, 0, 0, **detail):
                raise _Stopped()
            beat_at[0] = time.monotonic()

    try:
        original, after = _write_docs(root, cfg, documents, removed, replacements, beat)
    except _Stopped:
        manifest['status'] = 'interrupted'
        store.write_json(root / 'manifest.json', manifest)
        return root
    total = (after + SHARD_ROWS - 1) // SHARD_ROWS
    state = dict(done=manifest['progress'].get('done_shards', 0), tokenized=0)

    def check():
        # Either thread may heartbeat; report tokenizing progress until it finishes.
        extra = {} if state['tokenized'] is None else dict(tokenized_docs=state['tokenized'], total_docs=after)
        return _checkpoint(ctx, state['done'], total, **extra)

    stop = Event()
    counts = dict(original=original, after=after)
    if unconnected is not None:
        # Make the non-embedding outputs durable before reporting the missing key.
        _write_tokens(root, cfg, total, state, stop, check)
        manifest['counts'] = counts
        raise unconnected
    # Tokenizing is CPU-bound and embedding waits on the provider, so overlap them.
    with ThreadPoolExecutor(1) as pool:
        parts = pool.submit(_write_tokens, root, cfg, total, state, stop, check)
        try:
            existing = _embed_shards(root, embedder, after, manifest, state, check)
        except EmbedderUnconnected:
            # Same contract as a missing key at start: finish the non-embedding outputs.
            parts.result()
            manifest['counts'] = counts
            raise
        except BaseException:
            stop.set()
            raise
        if existing is None:
            stop.set()
        written = parts.result()
    manifest['counts'] = counts
    if existing is None or not written or not check():
        manifest['status'] = 'interrupted'
        store.write_json(root / 'manifest.json', manifest)
        return root
    failures = sum(existing.values())
    report = stage3_report(original=original, after=after, removed=removed,
                           boilerplate_replaced=replacements, tokens_written=after,
                           embedded=len(existing) - failures, embed_failed_zero_vector=failures,
                           prepKey=root.name, embedder=embedder_name(manifest['embedder']), analyzer=analyzer_version())
    store.write_json(root / 'stage_3.json', report)
    manifest['counts'] = report
    manifest['status'] = 'done'
    store.write_json(root / 'manifest.json', manifest)
    _publish(sid, version, root, cfg, manifest)
    return root


def _write_docs(root, cfg, documents, removed, replacements, beat):
    """Clean, filter and write document parts, holding one shard at a time; (original, after)."""
    channels = set(cfg.excludeChannels)
    original = 0

    def kept():
        nonlocal original
        for raw in documents:
            original += 1
            beat(prepared_docs=original)
            doc = _clean(raw, cfg, replacements)
            if doc.get('source', '') in channels:
                removed['excluded_channel'] += 1
                continue
            yield doc

    shard, batch, after = 0, [], 0

    def flush():
        for offset in range(0, len(batch), DOC_SHARD_ROWS):
            part = (shard - 1) * _parts_per_shard() + offset // DOC_SHARD_ROWS + 1
            _jsonl(_part_path(root, 'docs', part), batch[offset:offset + DOC_SHARD_ROWS])

    for item in iter_filtered(kept(), cfg.adFilter, cfg.excludeSources, cfg.minBodyChars, removed, full_text=True):
        if not batch:
            shard += 1
        batch.append(item)
        after += 1
        if len(batch) == SHARD_ROWS:
            flush()
            batch = []
    if batch:
        flush()
    # A previous run of the same key may have left more parts; readers glob them.
    last = shard * _parts_per_shard()
    for kind in ('docs', 'tokens'):
        for path in (root / kind).glob('part-*.jsonl'):
            if int(path.stem.split('-')[1]) > last:
                path.unlink()
    return original, after


def _write_tokens(root, cfg, total, state, stop, check):
    """Write token parts from the document parts; False when the run was stopped."""
    beat_at = time.monotonic()
    for shard in range(1, total + 1):
        for part in _shard_parts(shard):
            docs = _read_part(root, part)
            if not docs:
                continue
            if _tokens_match(root, part, docs):
                # Same documents, same config (the prep key): reuse a part written earlier.
                state['tokenized'] += len(docs)
                continue
            rows = []
            for d, tokens in zip(docs, tokenize_many((token_text(_text(d)) for d in docs), cfg.tokenPos)):
                if stop.is_set():
                    return False
                # Kiwi can starve the pulse thread, so heartbeat from here too.
                if time.monotonic() - beat_at >= HEARTBEAT_INTERVAL:
                    if not check():
                        stop.set()
                        return False
                    beat_at = time.monotonic()
                rows.append(dict(doc_id=d['doc_id'], tokens=tokens))
                state['tokenized'] += 1
            _jsonl(_part_path(root, 'tokens', part), rows)
    state['tokenized'] = None
    return True


def _tokens_match(root, part, docs):
    path = _part_path(root, 'tokens', part)
    if not path.exists():
        return False
    try:
        with path.open(encoding='utf-8') as stream:
            ids = [json.loads(line)['doc_id'] for line in stream if line.strip()]
    except (OSError, ValueError, KeyError, TypeError):
        return False
    return ids == [d['doc_id'] for d in docs]


def _find_docs(root, total, doc_ids):
    found = {}
    for shard in range(1, total + 1):
        for part in _shard_parts(shard):
            found.update((d['doc_id'], d) for d in _read_part(root, part) if d['doc_id'] in doc_ids)
    return found


def _embed_shards(root, embedder, after, manifest, state, check):
    """Embed shards not yet stored; the stored-vector map, or None when stopped."""
    total = (after + SHARD_ROWS - 1) // SHARD_ROWS
    vectors = VectorStore(root)
    if not _retry_failed(vectors, embedder, lambda ids: _find_docs(root, total, ids), check):
        return None
    existing = {doc_id: bool(failed[i]) for ids, _, failed in vectors.iter_shards()
                for i, doc_id in enumerate(ids)}
    for shard in range(1, total + 1):
        if shard <= state['done']:
            continue
        if not check():
            return None
        batch = [d for part in _shard_parts(shard) for d in _read_part(root, part)]
        pending = [d for d in batch if d['doc_id'] not in existing]
        if pending:
            matrix, failed = _embed(embedder, [_text(d) for d in pending])
            ids = [d['doc_id'] for d in pending]
            vectors.write_shard(ids, matrix, failed)
            existing.update(zip(ids, failed))
        state['done'] = shard
        written = min(shard * SHARD_ROWS, after)
        manifest['progress'] = dict(done_shards=shard, total_shards=total,
                                    docs_written=written, tokens_written=written,
                                    vectors_written=len(existing))
        store.write_json(root / 'manifest.json', manifest)
    return existing
