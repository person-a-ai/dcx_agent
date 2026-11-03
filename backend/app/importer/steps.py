"""Stages A–E of an external label import. Each stage is idempotent."""
from contextlib import closing, contextmanager
import fcntl
import json
from pathlib import Path
import shutil
import sqlite3
import time
from typing import Callable

from app.config import settings
from app.context import store, versions
from app.crawl.control import phase_state
from app.crawl.queue import CrawlQueue
from app.crawl.writer import DocWriter
from app.importer.read import ImportError_, Source, iter_records, open_source, scan
from app.label.route import IMPORTED, schema as label_schema

ORDER = ('session', 'crawl', 'prep', 'labels', 'export')
STEP_FUNCTIONS = {'session': 'create_session', 'crawl': 'register_collection', 'prep': 'run_prep_step',
                  'labels': 'insert_labels', 'export': 'export_step'}
DOT = '.'
WARNING = "주의: 0단계 값이 모두 '.'입니다. 6~8단계 결과는 주제 정보 없이 만들어집니다."
_BATCH = 5000


def default_sid(source: Source) -> str:
    return 'imp-' + source.sha256[:12]


def _context():
    return dict(bk=DOT, oneLiner=DOT, researchQuestion=dict(text=DOT), projectType=dict(choice='new', note=DOT),
                taskMode='explore', constraints=[], channels=['naver_cafe'],
                productCategory=dict(l1=DOT, source='user'))


def _imported(sid):
    return (store.load_session(sid) or {}).get('imported') or {}


def _assert_version(sid, claimed):
    """Caller holds the session lock through any following writes."""
    try:
        return store.assert_writable(sid, claimed)
    except store.StoreError as exc:
        raise ImportError_('가져오는 동안 프로젝트 버전이 바뀌었습니다. 같은 명령을 다시 실행하세요.') from exc


def _mark(sid, step, *, version=None, **counts):
    with store.locked(sid):
        data = _assert_version(sid, version) if version is not None else store.load_session(sid)
        imported = data.setdefault('imported', {})
        imported.setdefault('steps', {})[step] = store.now()
        imported.setdefault('counts', {}).update(counts)
        directory = versions.version_dir(sid, version) if version is not None else store.session_dir(sid)
        store.write_json(directory / 'session.json', data)


def create_session(sid, source, result):
    keywords = [dict(kw=k, text=k, status='approved', axis='', sub='') for k in result.keywords]
    store.update_session(sid, {'schemaVersion': 2, 'sid': sid, 'projectContext': _context(), 'keywords': keywords,
                               'imported': dict(file=source.name, sha256=source.sha256, steps={}, counts={})})


def register_collection(sid, source):
    base = Path(settings.local_data_dir) / 'crawl' / sid / 'collections'
    final, partial = base / 'c1', base / 'c1.partial'
    if not final.exists():
        shutil.rmtree(partial, ignore_errors=True)
        partial.mkdir(parents=True)
        now = store.now()
        keywords = [dict(kw=k['kw'], axis='', sub='') for k in store.load_session(sid)['keywords']]
        meta = dict(id='c1', parent=None, createdAt=now, keywords=keywords, status='done')
        store.write_json(partial / 'meta.json', meta)
        store.write_json(partial / 'manifest.json', dict(meta, channels=['naver_cafe'], config={}, snapshotId=None,
                                                         imported=dict(file=source.name, sha256=source.sha256)))
        writer = DocWriter(partial / 'docs')
        urls = []
        with closing(CrawlQueue(partial / 'queue.sqlite')) as queue:
            try:
                for record in iter_records(source, now):
                    writer.write(record.doc)
                    urls.append(dict(url=record.doc['url'], source='naver_cafe', kw=record.doc['kw'],
                                     title=record.doc['title'], date=record.doc['date'],
                                     src_meta=record.doc['src_meta']))
                    if len(urls) >= _BATCH:  # bounded memory: never hold all ~200k URL rows
                        queue.add_urls(urls)
                        urls.clear()
            finally:
                writer.close()
            if urls:
                queue.add_urls(urls)
            with queue._write() as db:
                db.execute("UPDATE urls SET status='done', doc_count=1, fetch_level='full', access='public'")
            queue.finish_run(queue.register_run('detail'), 'done')
        partial.rename(final)
    store.update_session(sid, {'collectionId': 'c1', 'step': 'preprocess-setup'}, confirm_stage='stage2')
    if phase_state(sid, 'c1') != 'done':
        raise ImportError_('수집본을 완료 상태로 만들지 못했습니다')


def run_prep_step(sid, log, poll_s=10, sleep=time.sleep):
    from app.prep.launch import start_prep
    from app.work import runner
    for attempt in (1, 2):
        data = store.load_session(sid)
        if data.get('prep', {}).get('status') == 'done':
            log('[3/5] 전처리 완료')
            return
        work = start_prep(sid)
        run_id = work.get('runId')
        log(f'[3/5] 전처리 run {run_id} 시작' if work.get('status') != 'done' else '[3/5] 전처리 결과 재사용')
        while True:
            # start_prep returns {'status': …}; runner.status rows carry {'state': …}.
            row = next((r for r in runner.status(sid) if run_id and r['runId'] == run_id), None)
            state = row['state'] if row else work.get('status')
            if state == 'done' or store.load_session(sid).get('prep', {}).get('status') == 'done':
                break
            if state in ('failed', 'interrupted'):
                log(f'      전처리 {state}: {(row or {}).get("error") or ""}')
                break
            progress = (row or work).get('progress') or 0
            log(f'      {time.strftime("%H:%M:%S")}  {round(progress * 100)}%')
            sleep(poll_s)
        if store.load_session(sid).get('prep', {}).get('status') == 'done':
            log('[3/5] 전처리 완료')
            return
    raise ImportError_('전처리에 실패했습니다. 서버 로그를 확인하고 같은 명령을 다시 실행하세요.')


def insert_labels(sid, source) -> dict:
    from app.label.overview import index_documents, labels_for
    from app.label import rule
    from app.label.questions import QVER
    from app.model import infer
    with store.locked(sid):
        data = store.load_session(sid)
        claimed = data['version']
        _assert_version(sid, claimed)
        labeling = data.get('labeling', {})
        if labeling.get('started') and labeling.get('labelerMode') != IMPORTED:
            raise ImportError_('이미 라벨링을 시작한 프로젝트입니다')
        # Claim stage four before writing labels; API starts take the same lock.
        data = store._update_locked(sid, {'labeling': {'started': True, 'mode': IMPORTED,
                                                      'labelerMode': IMPORTED, 'status': 'running'}})
    root = infer.prepared_root(sid, data) / 'docs'
    if not root.is_dir():
        raise store.StoreError('전처리 문서를 찾을 수 없습니다.')
    prepared = set()
    for path in sorted(root.glob('*.jsonl')):
        with path.open(encoding='utf-8') as stream:
            for line in stream:
                if not line.strip():
                    continue
                doc_id = json.loads(line)['doc_id']
                if doc_id in prepared:
                    raise ValueError('Duplicate prepared document ID')
                prepared.add(doc_id)
    with store.locked(sid):
        _assert_version(sid, claimed)
        labels = labels_for(sid, data)
        label_schema(labels)
    votes = json.dumps({'imported': dict(file=source.name, sha256=source.sha256[:12])})
    labeled, batch = set(), []
    dropped = 0
    def flush():
        with store.locked(sid):
            _assert_version(sid, claimed)
            with labels._db() as db:
                db.executemany('INSERT OR REPLACE INTO final VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', batch)
        batch.clear()
    for record in iter_records(source, ''):
        doc_id = record.doc['doc_id']
        if doc_id not in prepared:
            dropped += 1
            continue
        lab = record.label
        batch.append((doc_id, lab['level'], None, IMPORTED, 'accepted', lab['tags_json'], lab['reason_code'],
                      lab['signal'], rule.RULE_VERSION, QVER, votes, '[]', 0))
        labeled.add(doc_id)
        if len(batch) >= _BATCH:
            flush()
    if batch:
        flush()
    counts = dict(labeled=len(labeled), unlabeled=len(prepared - labeled), droppedByPrep=dropped)
    with store.locked(sid):
        _assert_version(sid, claimed)
        index_documents(sid, data, labels)
        store._update_locked(sid, {'labeling': {'started': True, 'status': 'done', 'mode': IMPORTED,
                                               'labelerMode': IMPORTED}, 'step': 'train-start'})
    _mark(sid, 'labels', version=claimed, **counts)
    return counts


def export_step(sid, partial: bool) -> dict:
    from app.model import export
    with store.locked(sid):
        claimed = store.load_session(sid)['version']
        _assert_version(sid, claimed)
    try:
        exported = export.write(sid, claimed, without_model=True, partial=partial)
    except store.StoreError:
        with store.locked(sid):
            _assert_version(sid, claimed)
        raise
    with store.locked(sid):
        _assert_version(sid, claimed)
        store._update_locked(sid, {'step': 'cluster-start'})
    _mark(sid, 'export', version=claimed)
    return exported


def run_import(path, *, sid: str | None = None, log: Callable[[str], None] = print,
               poll_s: float = 10, sleep=time.sleep) -> dict:
    source = open_source(path)
    log(f'가져오기: {Path(path).name} → {source.name} (sha256 {source.sha256[:12]})')
    result = scan(source)
    skipped = ' · '.join(f'{k} {v:,}' for k, v in result.skipped.items()) or '없음'
    log(f'검증  {result.total:,}행 · done {result.done:,} · 건너뜀 {skipped}')
    sid = sid or default_sid(source)
    try:
        store.root_dir(sid)  # validates the id before anything is written
        with _import_lock(sid):
            return _run_locked(sid, source, result, log, poll_s, sleep)
    except (store.StoreError, OSError, sqlite3.Error) as exc:
        raise ImportError_(str(exc)) from exc


@contextmanager
def _import_lock(sid):
    path = Path(settings.local_data_dir) / 'imports' / f'{sid}.lock'
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ImportError_('같은 프로젝트의 가져오기가 이미 실행 중입니다') from None
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def _run_locked(sid, source, result, log, poll_s, sleep):
    existing = store.load_session(sid) if (store.root_dir(sid)).exists() else None
    if existing is not None:
        info = existing.get('imported')
        if not info:
            raise ImportError_(f'{sid}는 가져오기로 만든 프로젝트가 아닙니다. --sid로 다른 이름을 주세요.')
        if info.get('sha256') != source.sha256:
            raise ImportError_(f'{sid}는 다른 파일로 만든 프로젝트입니다. --sid로 다른 이름을 주세요.')
    counts = dict(_imported(sid).get('counts', {}))
    for step in ORDER:
        if step in _imported(sid).get('steps', {}):
            continue
        fn = globals()[STEP_FUNCTIONS[step]]
        if step == 'session':
            fn(sid, source, result)
            log(f'[1/5] 프로젝트 {sid} 만듦')
        elif step == 'crawl':
            fn(sid, source)
            log(f'[2/5] 수집본 c1 등록 {result.done:,}건')
        elif step == 'prep':
            fn(sid, log, poll_s=poll_s, sleep=sleep)
        elif step == 'labels':
            counts.update(fn(sid, source))
            log(f"[4/5] 라벨 {counts['labeled']:,}건 넣음 · 판정 없음 {counts['unlabeled']:,} · 전처리에서 빠짐 {counts['droppedByPrep']:,}")
        elif step == 'export':
            exported = fn(sid, partial=counts.get('unlabeled', 0) > 0)
            log(f"[5/5] 내보내기 완료 · core+supporting {exported['relevant']:,}건")
        if step not in ('labels', 'export'):  # These stages checkpoint their claimed version.
            _mark(sid, step)
    data = store.load_session(sid)
    log(f'완료. 웹 프로젝트 목록에서 {sid}를 열고 6단계(세그먼트)부터 진행하세요.')
    log(WARNING)
    return dict(sid=sid, counts=data['imported'].get('counts', {}), exportRef=data.get('training', {}).get('exportRef'))
