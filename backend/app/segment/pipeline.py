"""Resumable stage-six orchestration; session locks only protect publication.

Step artifacts are local to a segmentation, while dims owns its cross-version
cache. A fresh run replaces layers; resume retains artifacts and rotates the
public run UUID so old confirmation clients cannot write to the resumed run.

T10 args contract: {'k': int | None, 'fresh': bool}, defaulting to None/False.
With k=None and fresh=False, reuse any checkpoint (including completed runs)
and keep confirmations. An integer k or fresh=True resets L1-L3 and confirmations.
T10 sends fresh=True only after confirmReset. Without a checkpoint, initialize
new layers. The legacy resume argument is unnecessary and cannot override reset.
"""
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import hashlib
import threading
import os
import shutil
import tempfile
import json
import logging
import time
from types import FunctionType
import uuid

import numpy as np

from app.config import settings
from app.context import store as sessions
from app.context.stale import clear_stale
from app.context.versions import version_dir
from app.llm import registry
from app.llm.base import validate
from app.segment import ctfidf, dims, drafts, inputs, l1, l2, l3, params, quality, signals, stopwords, target
from app.segment.store import SegmentStore
from app.vectors.embedder import get_embedder

STEPS = ('load', 'L1', 'L2', 'L3', 'quality', 'dims', 'drafts')
# Target-persona mode anchors documents to stage-0 persona cards instead of k-means.
TARGET_STEPS = ('load', 'anchor', 'calibrate', 'assign', 'L2', 'L3', 'needs', 'discover', 'quality', 'dims', 'drafts')


LLM_REASON = 'LLM이 연결되지 않았거나 한도를 넘었습니다. 연결을 확인한 뒤 이어서 진행하세요.'
GENERIC_REASON = '클러스터링 중 오류가 났습니다. 이어서 진행하거나 다시 실행하세요.'


class _LLMUnavailable(BaseException):
    """The shared worker maps non-Exception exits to interrupted."""


class _Stopped(BaseException):
    """Escape provider catch-all handlers at cooperative boundaries."""


def _json(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(type(value).__name__)


def _write(path, data):
    sessions.atomic_write(path, json.dumps(data, ensure_ascii=False, default=_json))


def _session(sid, version, values, *, reset=False):
    with sessions.locked(sid):
        sessions.assert_writable(sid, version)
        path = version_dir(sid, version) / 'session.json'
        data = sessions.read_json(path)
        if reset:
            data['segment'] = {}
            if data.get('evidence', {}).get('status', 'none') != 'none':
                data['evidence'] = {'status': 'stale'}
            data.setdefault('completion', {}).pop('evidenceDone', None)
            data.setdefault('completion', {}).pop('segmentDone', None)
            data.get('drafts', {}).pop('segment', None)
        data.setdefault('segment', {}).update(values)
        sessions.write_json(path, data)


def _confirm_counts(store):
    return {layer: f'{sum(bool(r["confirmed_at"]) for r in rows)}/{len(rows)}'
            for layer in ('clusters', 'personas', 'contexts')
            for rows in [getattr(store, layer)()]}


def mark_done_if_complete(sid, version):
    """T10 calls after confirmations; an empty result is never complete."""
    with sessions.locked(sid):
        sessions.assert_writable(sid, version)
        store = SegmentStore.open(sid, version)
        rows = store.contexts()
        path = version_dir(sid, version) / 'session.json'
        data = sessions.read_json(path)
        data.setdefault('segment', {})['confirm'] = _confirm_counts(store)
        complete = bool(rows) and all(row['confirmed_at'] for row in rows)
        if complete:
            data['segment'].update(status='done', savedAt=sessions.now())
            data.setdefault('completion', {})['segmentDone'] = True
        sessions.write_json(path, data)
        if complete:
            clear_stale(sid, version, 'stage6', already_locked=True)
        return complete


def _bind(function, **dependencies):
    """Bind a private dependency per invocation, never monkeypatch shared modules.

    T7/T8 do not expose a registry injection argument. Copies share the original
    implementation and schemas but have run-local registry/cache instrumentation.
    """
    bound = FunctionType(function.__code__, {**function.__globals__, **dependencies},
                         function.__name__, function.__defaults__, function.__closure__)
    bound.__kwdefaults__ = function.__kwdefaults__
    return bound


class _Calls:
    def __init__(self, root, pulse):
        self.root, self.pulse = root, pulse
        self.lock = threading.Lock()  # Segment LLM calls run concurrently (SEGMENT_CONCURRENCY).
        self.results = []
        self.path = root / 'llm_calls.json'
        self.counts = sessions.read_json(self.path) or dict.fromkeys(
            ('cluster_name', 'persona_draft', 'context_draft', 'dims'), 0)

    def run_task(self, task):
        with self.lock:
            self.pulse()
        name = task.task.split('.')[-1]
        payload = task.model_dump(exclude={'output_schema'})
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        path = self.root / 'draft_cache' / f'{digest}.json'
        cached = sessions.read_json(path) if name != 'dims' else None
        if cached is not None and cached.get('ok'):
            result = validate(task, cached['raw'])
            return result
        with self.lock:
            self.counts[name] = self.counts.get(name, 0) + 1
            _write(self.path, self.counts)
        try:
            result = registry.run_task(task)
        except (TimeoutError, ConnectionError):
            from app.llm.base import failure
            result = failure('backend', 'Provider unavailable')
        with self.lock:
            self.results.append(None if result.ok else result.error.kind if result.error else 'unknown')
            if name != 'dims' and result.ok:
                _write(path, {'ok': True, 'raw': result.raw})
        return result


class _DraftStore:
    """Keep T8's layer order and parent evidence; pulse before each Persona."""
    def __init__(self, store, pulse):
        self.store, self.pulse = store, pulse

    def __getattr__(self, key):
        return getattr(self.store, key)

    def personas(self):
        return _PulsedRows(self.store.personas(), self.pulse)

    def contexts(self):
        return _PulsedRows(self.store.contexts(), self.pulse)


class _PulsedRows(list):
    # T8 similarity traverses Personas twice; preserve the store's reusable list
    # contract while pulsing lazily immediately before each unit of work.
    def __init__(self, rows, pulse):
        super().__init__(rows)
        self.pulse = pulse

    def __iter__(self):
        previous = None
        for row in super().__iter__():
            if row['persona_id'] != previous:
                previous = row['persona_id']
                self.pulse(previous)
            yield row


def _save_row(store, table, key, row):
    values = store._encode(table, {k: v for k, v in row.items() if k != key})
    with store._db(write=True) as db:
        db.execute(f'UPDATE {table} SET ' + ','.join(f'{k}=?' for k in values) + f' WHERE {key}=?',
                   (*values.values(), row[key]))


def _reps(source, ids, centroid=None, *, edge=False):
    """Documents nearest the centroid, or with edge=True the farthest (hidden-need candidates)."""
    if not ids:
        return []
    # Float32 only for individual vectors; stable ID tie break.
    if centroid is None:
        centroid = sum((np.asarray(source.vectors[source.index[i]], dtype=np.float32) for i in ids)) / len(ids)
    norm = np.linalg.norm(centroid)
    center = centroid / norm if norm else centroid
    sign = 1. if edge else -1.
    ids = sorted(ids, key=lambda i: (sign * float(np.asarray(source.vectors[source.index[i]], dtype=np.float32) @ center), i))
    result = []
    for doc_id in ids[:params.REPS]:
        doc = source.docs[doc_id]
        field, idx, text = 'body', None, doc.get('body') or ''
        if not text:
            field, text = 'title', doc.get('title') or ''
        if not text and doc.get('comments'):
            field, idx, text = 'comments', 0, doc['comments'][0].get('text', '')
        result.append(dict(docId=doc_id, text=text[:300], source=doc.get('source', ''), field=field, idx=idx))
    return result


def _groups(rows, field):
    result = defaultdict(list)
    for row in rows:
        result[row[field]].append(row['doc_id'])
    return result


def _l1_summary(source, state, sid, version):
    grouped = defaultdict(list)
    for doc_id, label in zip(source.ids, state['labels']):
        grouped[f'CL{label}'].append(doc_id)
    return _summary(source, state, sid, version, grouped)


def _summary(source, state, sid, version, grouped):
    session = sessions.read_json(version_dir(sid, version) / 'session.json')
    state['bk'] = session.get('projectContext', {}).get('bk', '')
    keywords = ctfidf.ctfidf({key: [source.nouns[i] for i in ids] for key, ids in grouped.items()},
                             params.CTFIDF_TOP, bk=state['bk'])
    return [dict(id=key, docs=len(ids), keywords=keywords[key], reps=_reps(source, ids),
                 edges=_reps(source, ids, edge=True), name='', nameFailed=False)
            for key, ids in grouped.items()]


def _preview_personas(root, sid, version, state, draft, source):
    """After L2, show personas and their LLM Desire/Goal drafts while L3 runs on."""
    preview = sessions.read_json(root / 'preview.json')
    if not preview:
        return
    members = _groups(state['docs'], 'persona_id')
    counts = {pid: len(ids) for pid, ids in members.items()}
    names = {row['id']: row.get('name', '') for row in state.get('l1_summary', [])}
    rows = [dict(id=p['persona_id'], cluster=p['cluster_id'], docs=counts[p['persona_id']],
                 centrality=[word for word, _ in p['centrality'][:params.CENTRALITY_TOP]],
                 reps=p['reps'], edges=_reps(source, members[p['persona_id']], edge=True),
                 name='', desire='', goals=[], draftFailed=False)
            for p in state['personas']]
    preview.update(personas=rows, personaDrafting='pending')
    _write(root / 'preview.json', preview)
    session = sessions.read_json(version_dir(sid, version) / 'session.json')
    context = session.get('projectContext', {})

    extra = _target_evidence(state, context)

    def persona_draft(persona):
        # Same task and evidence as the drafts step, so its result can be reused there.
        return draft(sid, 'persona_draft', drafts.PersonaDraftOut, context.get('oneLiner', ''),
                     {'targetScope': context.get('targetScope'),
                      'centrality': persona['centrality'][:params.CENTRALITY_TOP],
                      'reps': persona['reps'][:params.REPS], 'cluster_name': names.get(persona['cluster_id'], ''),
                      **extra.get(persona['cluster_id'], {})})
    with ThreadPoolExecutor(max_workers=max(1, settings.segment_concurrency)) as pool:
        results = list(pool.map(persona_draft, state['personas']))
    state['persona_drafts'] = {}
    for row, result in zip(rows, results):
        if result:
            row.update(name=result['name'], desire=result['desire'], goals=result['goals'])
            state['persona_drafts'][row['id']] = result
        row['draftFailed'] = result is None
    preview['personaDrafting'] = 'done'
    _write(root / 'preview.json', preview)


def _target_evidence(state, context):
    """Per target cluster: the persona card plus the full stage-0 research context."""
    personas = (state.get('target') or {}).get('personas') or []
    if not personas:
        return {}
    shared = {'researchQuestion': (context.get('researchQuestion') or {}).get('text', ''),
              'knownInsights': context.get('knownInsights') or []}
    return {p['id']: {**shared, 'targetPersona': target.card_text(p)} for p in personas}


def _backfill_preview(root, sid, version, state, source, draft):
    preview = sessions.read_json(root / 'preview.json')
    if not preview or not state.get('personas'):
        return
    if any('edges' not in cluster for cluster in preview['clusters']):
        members = defaultdict(list)
        for doc_id, label in zip(source.ids, state['labels']):
            members[f'CL{label}'].append(doc_id)
        for cluster in preview['clusters']:
            cluster['edges'] = _reps(source, members[cluster['id']], edge=True)
        for cluster in state.get('l1_summary', []):
            cluster['edges'] = _reps(source, members[cluster['id']], edge=True)
        _write(root / 'preview.json', preview)
    if 'personas' not in preview:
        _preview_personas(root, sid, version, state, draft, source)


def _boundary_sample(vectors, labels):
    # Stratification guarantees small target clusters are present. quality's
    # own cap still applies and samples this already bounded matrix in full.
    rng = np.random.default_rng(params.SEED)
    groups = [np.flatnonzero(labels == label) for label in np.unique(labels)]
    quota = max(1, params.WARD_SAMPLE // len(groups))
    indices = np.concatenate([rng.choice(g, min(len(g), quota), replace=False) for g in groups])
    return vectors[indices], labels[indices]


def _assign_support(source, store):
    """Attach auxiliary-channel documents to the nearest Context centroid (cosine)."""
    support_ids = getattr(source, 'support_ids', None) or []
    if not support_ids:
        store.write_support([])
        return
    with store._db() as db:
        rows = db.execute('SELECT doc_id, cluster_id, persona_id, context_id FROM docs WHERE context_id IS NOT NULL').fetchall()
    groups = defaultdict(list)
    parents = {}
    for doc_id, cluster_id, persona_id, context_id in rows:
        if doc_id in source.index:
            groups[context_id].append(source.index[doc_id])
            parents[context_id] = (cluster_id, persona_id)
    if not groups:
        store.write_support([])
        return
    names = sorted(groups)
    centers = np.stack([np.asarray(source.vectors[groups[n]], dtype=np.float32).mean(axis=0) for n in names])
    centers /= np.maximum(np.linalg.norm(centers, axis=1, keepdims=True), 1e-12)
    result = []
    for start in range(0, len(support_ids), 20000):
        sims = np.asarray(source.support_vectors[start:start + 20000], dtype=np.float32) @ centers.T
        best = sims.argmax(axis=1)
        for offset, column in enumerate(best):
            name = names[column]
            result.append(dict(doc_id=support_ids[start + offset], cluster_id=parents[name][0],
                               persona_id=parents[name][1], context_id=name, sim=float(sims[offset, column])))
    store.write_support(result)


def run(context):
    sid, version = context.sid, context.version
    root = version_dir(sid, version) / 'segment'
    with sessions.locked(sid):
        sessions.assert_writable(sid, version)
    checkpoint = sessions.read_json(root / 'checkpoint.json') or {}
    mode = context.args.get('mode') or checkpoint.get('mode') or 'clusters'
    resume = bool(checkpoint and context.args.get('k') is None
                  and not context.args.get('fresh', False)
                  and checkpoint.get('mode', 'clusters') == mode)
    run_id = str(uuid.uuid4())
    store = SegmentStore.open(sid, version)
    if not resume:
        # Remove only this segmentation's artifacts; shared dims/nouns survive.
        for path in root.iterdir():
            if not path.name.startswith('segment.sqlite'):
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
        store.write_layers()
        store.write_support([])
        with store._db(write=True) as db:
            db.execute('DELETE FROM meta')
        checkpoint = {'done': [], 'k': context.args.get('k'), 'mode': mode,
                      'structureSources': context.args.get('structureSources') or None,
                      'stopwords': stopwords.stopwords_signature()}
    if resume and 'drafts' in checkpoint.get('done', []):
        with store._db() as db:
            row = db.execute("SELECT value FROM meta WHERE key='draft_flags'").fetchone()
        if row and any('draft_failed' in flags for flags in json.loads(row[0]).values()):
            checkpoint['done'].remove('drafts')
    steps = TARGET_STEPS if mode == 'target' else STEPS
    store.set_run(run_id)
    checkpoint['run'] = run_id
    _write(root / 'checkpoint.json', checkpoint)
    all_params = {k: v for k, v in vars(params).items() if k.isupper()}
    # Resumes retain the list signature that produced their stored keywords.
    # Legacy checkpoints have no signature; do not relabel their old results.
    if 'stopwords' in checkpoint:
        all_params['stopwords'] = checkpoint['stopwords']
    _session(sid, version, dict(status='running', run=run_id, params=all_params, reason=None, detail={}), reset=not resume)
    state = sessions.read_json(root / 'state.json') or {'warnings': []}
    source = None
    step = 'load'

    active_detail = {}
    last_load_pulse = 0.

    def pulse(persona=None, completed=None, **counts):
        nonlocal active_detail, last_load_pulse
        if context.should_stop():
            raise _Stopped()
        if counts and counts.get('docs') not in (0, counts.get('total')):
            if time.monotonic() - last_load_pulse < .2:
                return
        if counts:
            last_load_pulse = time.monotonic()
        if active_detail.get('step') != step:
            active_detail = {'step': step}
        if persona is not None:
            ids = [p['persona_id'] for p in state.get('personas', [])]
            active_detail.update(persona=ids.index(persona) + 1, personas=len(ids))
        active_detail.update(counts)
        detail = dict(active_detail)
        if completed is not None:
            detail['completed'] = completed
        progress = len(checkpoint['done']) / len(steps)
        context.heartbeat(progress, detail)
        _session(sid, version, dict(step=step, progress=progress, detail=detail))
        if context.should_stop():
            raise _Stopped()

    calls = _Calls(root, pulse)
    try:
        for step in steps:
            pulse()
            if step == 'load':
                if step not in checkpoint['done']:
                    source = inputs.load_input(sid, version, pulse=pulse,
                                               structure_sources=checkpoint.get('structureSources'))
                    np.save(root / 'support.npy', source.support_vectors, allow_pickle=False)
                    if len(source.ids) < 3:
                        raise sessions.StoreError('클러스터링할 문서가 없습니다.' if not source.ids else '클러스터링할 문서가 부족합니다.', 409)
                    fd, temporary = tempfile.mkstemp(dir=root, prefix='.vectors-')
                    try:
                        with os.fdopen(fd, 'wb') as stream:
                            np.save(stream, source.vectors, allow_pickle=False)
                            stream.flush()
                            os.fsync(stream.fileno())
                        os.replace(temporary, root / 'vectors.npy')
                    finally:
                        if os.path.exists(temporary):
                            os.unlink(temporary)
                    _write(root / 'input.json', {'ids': source.ids, 'report': source.report,
                                                 'support_ids': source.support_ids})
                    state['input'] = source.report
                else:
                    saved = sessions.read_json(root / 'input.json')
                    source = inputs.restore_input(sid, version, saved,
                        np.load(root / 'vectors.npy', mmap_mode='r', allow_pickle=False), pulse=pulse)
                    source.support_ids = saved.get('support_ids', [])
                    support_path = root / 'support.npy'
                    source.support_vectors = (np.load(support_path, allow_pickle=False) if support_path.exists()
                                              else np.empty((0, source.vectors.shape[1]), dtype=np.float16))
                source.index = {doc_id: i for i, doc_id in enumerate(source.ids)}
            if step in checkpoint['done']:
                continue
            calls.results.clear()
            if step == 'L1':
                suggestion = l1.suggest_k(source.vectors, np.random.default_rng(params.SEED)) if len(source.ids) >= 4 else dict(k=3, silhouette={}, inertia={}, sample=3)
                k = checkpoint['k'] or suggestion['k']
                if len(source.ids) < params.MIN_DOCS_WARN:
                    k = 3
                    state['warnings'] = [dict(key='few_docs', message=f'문서가 적어({len(source.ids)}건) 군집이 불안정할 수 있습니다.')]
                labels, centers = l1.cluster(source.vectors, k, np.random.default_rng(params.SEED))
                state['L1'] = {**suggestion, 'k': k, 'suggested': suggestion['k']}
                state['labels'], state['centers'] = labels.tolist(), centers.tolist()
                state['l1_summary'] = _l1_summary(source, state, sid, version)
                preview = dict(run=run_id, k=k, suggested=suggestion['k'],
                    silhouette=suggestion['silhouette'], sample=suggestion['sample'],
                    clusters=state['l1_summary'], naming='pending')
                _write(root / 'preview.json', preview)
                session = sessions.read_json(version_dir(sid, version) / 'session.json')
                one_liner = session.get('projectContext', {}).get('oneLiner', '')
                draft = _bind(drafts._draft, registry=calls)
                def name_cluster(cluster):
                    return draft(sid, 'cluster_name', drafts.ClusterNameOut, one_liner,
                                 {'keywords': cluster['keywords'], 'reps': cluster['reps']})
                with ThreadPoolExecutor(max_workers=max(1, settings.segment_concurrency)) as pool:
                    names = list(pool.map(name_cluster, state['l1_summary']))
                for cluster, name in zip(state['l1_summary'], names):
                    cluster.update(name=name['name'] if name else '', nameFailed=name is None)
                preview['naming'] = 'done'
                _write(root / 'preview.json', preview)
            elif step == 'L2':
                state['clusters'], state['personas'], state['docs'], state['l2'] = [], [], [], {}
                grouped = defaultdict(list)
                if mode == 'target':
                    for doc_id, label in zip(source.ids, state['target']['assign']):
                        if label >= 0:
                            grouped[state['target']['personas'][label]['id']].append(doc_id)
                else:
                    for doc_id, label in zip(source.ids, state['labels']):
                        grouped[f'CL{label}'].append(doc_id)
                if 'l1_summary' not in state:
                    state['l1_summary'] = _l1_summary(source, state, sid, version)
                summary = {row['id']: row for row in state['l1_summary']}
                for cluster_id, ids in grouped.items():
                    pulse()
                    result = l2.personas(ids, source.nouns, state['bk'])
                    state['clusters'].append(dict(cluster_id=cluster_id, keywords=summary[cluster_id]['keywords'], reps=summary[cluster_id]['reps'], quality={}, requests=[]))
                    state['l2'][cluster_id] = dict(fallback_assign=result.fallback_ratio)
                    for p in sorted(set(result.assign.values())):
                        pid = f'{cluster_id}-P{p}'
                        members = [i for i in ids if result.assign[i] == p]
                        state['personas'].append(dict(persona_id=pid, cluster_id=cluster_id,
                            centrality=result.centrality[p], network=result.network, flags=result.flags,
                            reps=_reps(source, members), similar=[]))
                        state['docs'].extend(dict(doc_id=i, cluster_id=cluster_id, persona_id=pid) for i in members)
                _preview_personas(root, sid, version, state, _bind(drafts._draft, registry=calls), source)
            elif step == 'L3':
                # Runs resumed from a checkpoint taken before the preview had
                # personas or edge documents fill them in here, before slow L3.
                _backfill_preview(root, sid, version, state, source, _bind(drafts._draft, registry=calls))
                state.setdefault('l3', {})
                state.setdefault('contexts', [])
                grouped = _groups(state['docs'], 'persona_id')
                doc_rows = {r['doc_id']: r for r in state['docs']}
                sig = signals.document_signals(source)
                vectors = {i: source.vectors[source.index[i]] for i in source.ids}
                for persona in state['personas']:
                    pid = persona['persona_id']
                    pulse(pid)
                    if pid in state['l3']:
                        continue
                    ids = grouped[pid]
                    sampled = {'fit_sample': params.L3_FIT_SAMPLE} if mode == 'target' else {}
                    result = l3.contexts(ids, source.tokens, vectors,
                        sentiment_by_id={i: sig[i]['sentiment'] for i in ids}, bk=state['bk'], **sampled)
                    state['l3'][pid] = dict(scan=result.scan, topic_ids=result.topic_ids)
                    if 'granularity_exceeded' in result.flags:
                        persona['flags'] = list(dict.fromkeys(persona['flags'] + ['granularity_exceeded']))
                    for local, center in result.centroids.items():
                        state['contexts'].append(dict(context_id=f'{pid}-{local}', persona_id=pid,
                            keywords=result.topic_words[local], centroid=center.tolist(), quality={},
                            flags=list(dict.fromkeys([f for f in result.flags if f != 'counter_context'] + result.context_flags.get(local, [])))))
                    for i in ids:
                        doc = source.docs[i]
                        doc_rows[i].update(context_id=f'{pid}-{result.assign[i]}', theta=result.theta[i],
                            theta_json=result.theta_all[i], dist_centroid=result.dist[i], band=result.band[i],
                            **sig[i], evidence_level=doc.get('evidence_level_pred'),
                            **{k: doc.get(k) for k in ('source', 'author_hash', 'date')})
                    _write(root / 'state.json', state)
                store.write_layers(clusters=state['clusters'], personas=state['personas'], contexts=state['contexts'], docs=state['docs'])
            elif step == 'anchor':
                session = sessions.read_json(version_dir(sid, version) / 'session.json')
                personas = target.cards(session.get('projectContext', {}))
                if not personas:
                    raise sessions.StoreError('0단계 페르소나 카드를 1개 이상 채운 뒤 실행하세요.', 409)
                scores = target.score(source.vectors, personas, get_embedder().embed)
                np.save(root / 'target_scores.npy', scores, allow_pickle=False)
                state['target'] = {'personas': personas}
            elif step == 'calibrate':
                scores = np.load(root / 'target_scores.npy', allow_pickle=False)
                state['target']['calibration'] = target.calibrate(
                    sid, scores, source.ids, source.docs, state['target']['personas'], calls.run_task,
                    fetch=lambda wanted: inputs.full_texts(sid, version, wanted, params.TARGET_JUDGE_CHARS))
            elif step == 'assign':
                _target_assign(root, sid, version, run_id, source, state)
            elif step == 'needs':
                members = _groups(state['docs'], 'cluster_id')
                state['target']['needs'] = {}
                for persona in state['target']['personas']:
                    pulse()
                    ids = members.get(persona['id'], [])
                    state['target']['needs'][persona['id']] = (
                        target.needs(sid, persona, ids, source.docs, calls.run_task) if ids else None)
            elif step == 'discover':
                other = [i for i, label in zip(source.ids, state['target']['assign']) if label < 0]
                vectors = source.vectors[[source.index[i] for i in other]] if other else source.vectors[:0]
                state['target']['discovered'] = target.discover(
                    sid, other, vectors, source.nouns, source.docs, state['bk'], calls.run_task, pulse=pulse)
            elif step == 'quality':
                _assign_support(source, store)
                if mode == 'target':
                    _target_quality(source, state, store, pulse)
                else:
                    _quality(source, state, store, pulse)
            elif step == 'dims':
                extract = _bind(dims.extract_sample, _extract=_bind(dims._extract, registry=calls))
                state['dims'] = extract(sid, version, store)
            elif step == 'drafts':
                session = sessions.read_json(version_dir(sid, version) / 'session.json')
                reps = {key: _reps(source, ids) for key, ids in _groups(state['docs'], 'context_id').items()}
                generate = _bind(drafts.generate_drafts, _draft=_bind(drafts._draft, registry=calls))
                result = generate(sid, _DraftStore(store, pulse), session.get('projectContext', {}), context_reps=reps,
                    cluster_drafts={row['id']: {'name': row.get('name', '')}
                                    for row in state.get('l1_summary', [])},
                    persona_drafts=state.get('persona_drafts', {}),
                    persona_extra=_target_evidence(state, session.get('projectContext', {})))
                for persona in store.personas():
                    persona['flags'] = list(dict.fromkeys([flag for flag in (persona['flags'] or []) if flag != 'draft_failed'] + result['flags'].get(persona['persona_id'], [])))
                    _save_row(store, 'personas', 'persona_id', persona)
            if step in ('calibrate', 'needs', 'discover', 'dims', 'drafts') and calls.results and all(
                    kind in ('backend', 'timeout') for kind in calls.results):
                _session(sid, version, {'status': 'interrupted', 'reason': LLM_REASON})
                raise _LLMUnavailable()
            _write(root / 'state.json', state)
            checkpoint['done'].append(step)
            _write(root / 'checkpoint.json', checkpoint)
            pulse(completed=step)
        result = _report(state, store, calls.counts, run_id, all_params)
        _write(root / 'stage_6.json', result)
        if mode == 'target':
            _write(root / 'target.json', _target_report(state, source))
        _session(sid, version, dict(status='review', step='drafts', progress=1,
            k={'L1': state['L1']['k'], 'suggested': state['L1']['suggested']},
            confirm=_confirm_counts(store), savedAt=result['at']))
        if resume:
            mark_done_if_complete(sid, version)
        return result
    except _Stopped:
        _session(sid, version, {'status': 'interrupted'})
    except Exception as exc:
        reason = str(exc) if isinstance(exc, sessions.StoreError) else GENERIC_REASON
        try:
            _session(sid, version, {'status': 'failed', 'reason': reason})
        except Exception:
            logging.getLogger(__name__).exception('Could not publish failed segment status')
        raise


def _quality(source, state, store, pulse):
    labels = np.asarray(state['labels'])
    ari = quality.resample_ari(source.vectors, labels)
    sample, sample_labels = _boundary_sample(source.vectors, labels)
    by_cluster = _groups(state['docs'], 'cluster_id')
    by_persona = _groups(state['docs'], 'persona_id')
    by_context = _groups(state['docs'], 'context_id')
    doc_rows = {r['doc_id']: r for r in state['docs']}
    for cluster in state['clusters']:
        pulse()
        cid = cluster['cluster_id']
        ids = by_cluster[cid]
        vectors = source.vectors[[source.index[i] for i in ids]]
        cluster['quality'] = dict(cohesion=quality.cohesion(vectors),
            boundary=quality.boundary(sample, sample_labels, target_label=int(cid[2:])), ari=ari)
        cluster['quality']['flags'] = quality.flags(**cluster['quality'])
        distribution = quality.channel_distribution(source.docs[i] for i in ids)
        cluster['channels'] = distribution['channels']
        cluster['metrics'] = dict(docs=len(ids), channel_skew=distribution['channel_skew'])
        _save_row(store, 'clusters', 'cluster_id', cluster)
        def recluster(indices, rng):
            selected = [ids[int(i)] for i in indices]
            result = l2.personas(selected, source.nouns, state['bk'])
            return [result.assign[i] for i in selected]
        par = quality.resample_ari(vectors, [doc_rows[i]['persona_id'] for i in ids], level='L2', recluster=recluster)
        state['l2'][cid]['ari'] = par
        for persona in state['personas']:
            if persona['cluster_id'] == cid:
                members = [i for i in ids if doc_rows[i]['persona_id'] == persona['persona_id']]
                persona['quality'] = dict(cohesion=quality.cohesion(source.vectors[[source.index[i] for i in members]]),
                    boundary=quality.boundary(vectors, [doc_rows[i]['persona_id'] for i in ids], target_label=persona['persona_id']), stability_ari=par)
                persona['flags'] = list(dict.fromkeys(persona['flags'] + quality.flags(ari=par, level='L2')))
                _save_row(store, 'personas', 'persona_id', persona)
    for row in state['contexts']:
        ids = by_context[row['context_id']]
        row['quality'] = dict(cohesion=quality.cohesion(source.vectors[[source.index[i] for i in ids]], row['centroid']),
            npmi=quality.npmi(row['keywords'], (source.tokens[i] for i in by_persona[row['persona_id']])))
        _save_row(store, 'contexts', 'context_id', row)


def _target_assign(root, sid, version, run_id, source, state):
    """Assign documents to persona cards; near-duplicate (viral) and ad posts become 'other'."""
    scores = np.load(root / 'target_scores.npy', allow_pickle=False)
    personas, calibration = state['target']['personas'], state['target']['calibration']
    best, top = scores.argmax(1), scores.max(1)
    excluded = np.zeros(len(source.ids), dtype=bool)
    pools, viral, ads = {}, {}, {}
    for j, persona in enumerate(personas):
        threshold = calibration[persona['id']]['threshold']
        rows = np.flatnonzero((best == j) & (top >= threshold)) if threshold is not None else np.empty(0, dtype=int)
        duplicate = target.near_duplicates(source.vectors[rows]) if len(rows) else np.zeros(0, dtype=bool)
        ad = np.array([target.is_ad(source.docs[source.ids[r]]) for r in rows], dtype=bool)
        excluded[rows[duplicate | ad]] = True
        pools[persona['id']], viral[persona['id']] = int(len(rows)), int(duplicate.sum())
        ads[persona['id']] = int((ad & ~duplicate).sum())
    assigned = target.assign(scores, calibration, personas, excluded)
    if not (assigned >= 0).any():
        raise sessions.StoreError('목표 페르소나 카드에 맞는 문서가 없습니다. 카드 내용을 구체적으로 고친 뒤 다시 실행하세요.', 409)
    # Closest-to-card documents first, for the report's quotes.
    top_ids = {}
    for j, persona in enumerate(personas):
        rows = np.flatnonzero(assigned == j)
        rows = rows[np.argsort(-scores[rows, j], kind='stable')][:300]
        top_ids[persona['id']] = [source.ids[r] for r in rows]
    state['target'].update(assign=assigned.tolist(), pool=pools, viral=viral, ads=ads, top=top_ids)
    grouped = defaultdict(list)
    for doc_id, label in zip(source.ids, assigned):
        if label >= 0:
            grouped[personas[label]['id']].append(doc_id)
    state['L1'] = dict(k=len(grouped), suggested=None, mode='target', silhouette={}, inertia={}, sample=0)
    names = {p['id']: p['name'] for p in personas}
    state['l1_summary'] = [dict(row, name=names[row['id']]) for row in _summary(source, state, sid, version, grouped)]
    _write(root / 'preview.json', dict(run=run_id, mode='target', k=len(grouped), suggested=None, silhouette={},
                                       sample=0, clusters=state['l1_summary'], naming='done',
                                       other=int((assigned < 0).sum())))


def _target_quality(source, state, store, pulse):
    """Target mode has no k-means labels: cohesion, channels and Context npmi only."""
    by_cluster = _groups(state['docs'], 'cluster_id')
    by_persona = _groups(state['docs'], 'persona_id')
    by_context = _groups(state['docs'], 'context_id')
    for cluster in state['clusters']:
        pulse()
        ids = by_cluster[cluster['cluster_id']]
        cluster['quality'] = dict(cohesion=quality.cohesion(source.vectors[[source.index[i] for i in ids]]))
        cluster['quality']['flags'] = quality.flags(cohesion=cluster['quality']['cohesion'])
        distribution = quality.channel_distribution(source.docs[i] for i in ids)
        cluster['channels'] = distribution['channels']
        cluster['metrics'] = dict(docs=len(ids), channel_skew=distribution['channel_skew'])
        _save_row(store, 'clusters', 'cluster_id', cluster)
    for persona in state['personas']:
        members = by_persona[persona['persona_id']]
        persona['quality'] = dict(cohesion=quality.cohesion(source.vectors[[source.index[i] for i in members]]))
        _save_row(store, 'personas', 'persona_id', persona)
    for row in state['contexts']:
        ids = by_context[row['context_id']]
        row['quality'] = dict(cohesion=quality.cohesion(source.vectors[[source.index[i] for i in ids]], row['centroid']),
            npmi=quality.npmi(row['keywords'], (source.tokens[i] for i in by_persona[row['persona_id']])))
        _save_row(store, 'contexts', 'context_id', row)


def _target_report(state, source):
    """Everything the target-persona report tab shows; source quotes are capped at 300 characters."""
    data = state['target']
    assigned = np.asarray(data['assign'])
    members = _groups(state['docs'], 'cluster_id')
    personas = []
    for persona in data['personas']:
        pid = persona['id']
        ids = members.get(pid, [])
        calibration = data['calibration'][pid]
        needs = data.get('needs', {}).get(pid)
        estimate = round(len(ids) * needs['share']) if needs and needs.get('share') is not None else None
        personas.append(dict(id=pid, name=persona['name'], card=persona['card'], threshold=calibration['threshold'],
            bands=calibration['bands'], pool=data['pool'].get(pid, 0), viral=data['viral'].get(pid, 0),
            ads=data['ads'].get(pid, 0), docs=len(ids), firstPerson=estimate, needs=needs,
            quotes=target.quotes(data.get('top', {}).get(pid, []), source.docs),
            flags=['no_match'] if calibration['threshold'] is None else []))
    return dict(total=len(assigned), assigned=int((assigned >= 0).sum()), other=int((assigned < 0).sum()),
                personas=personas, discovered=data.get('discovered', []), at=sessions.now())


def _report(state, store, counts, run_id, all_params):
    groups = {layer: _groups(state['docs'], key) for layer, key in
              [('clusters', 'cluster_id'), ('personas', 'persona_id'), ('contexts', 'context_id')]}
    bands = Counter(row['band'] for row in state['docs'])
    return dict(run=run_id, input=state['input'], L1=state['L1'],
        clusters=[dict(id=r['cluster_id'], docs=len(groups['clusters'][r['cluster_id']]),
            **r['quality'], channels=r['channels'], channel_skew=r['metrics']['channel_skew']) for r in store.clusters()],
        personas=[dict(id=r['persona_id'], docs=len(groups['personas'][r['persona_id']]),
            **state['l2'][r['cluster_id']], flags=r['flags']) for r in store.personas()],
        contexts=[dict(id=r['context_id'], docs=len(groups['contexts'][r['context_id']]), **r['quality'],
            topics_scanned={k: v['cv'] for k, v in state['l3'][r['persona_id']]['scan'].items()},
            flags=r['flags']) for r in store.contexts()],
        bands={k: bands[k] / len(state['docs']) for k in ('core', 'fringe', 'edge')},
        dims=state['dims'], llm_calls=counts, params=all_params, warnings=state['warnings'], at=sessions.now())
