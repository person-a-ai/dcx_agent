"""Start stage three outside HTTP; shared by the API and the importer."""
from app.context import store
from app.context.stale import clear_stale
from app.prep.config import PrepConfig
from app.prep.guards import assert_ready
from app.work import runner


def start_prep(sid: str, version: str | None = None) -> dict:
    from app.routers.prep import _root, _save, _session, _view

    with store.locked(sid):
        data = _session(sid, version, writable=True)
        cfg = PrepConfig.model_validate(data.get('prep', {}).get('config', {}))
        ref = assert_ready(sid, data, cfg)
        current = _view(sid, data)
        if current['status'] in ('running', 'paused'):
            return current
        root = _root(sid, ref['collectionId'], ref['prepKey'])
        manifest = store.read_json(root / 'manifest.json')
        # Only fully published results can bypass the worker (and provider setup).
        if (manifest and manifest.get('collectionFinalized') is True and manifest.get('status') == 'done'
                and (root / 'stage_3.json').exists()):
            _save(sid, config=cfg.model_dump(), derivedRef=ref, status='done', runId=None, reused=True)
            clear_stale(sid, data['version'], 'stage3', already_locked=True)
            return {**_view(sid, store.load_session(sid)), 'reused': True}
        work = runner.start(sid, data['version'], 'prep', {'config': cfg.model_dump()})
        _save(sid, config=cfg.model_dump(), derivedRef=ref, status=work['state'], runId=work['runId'], reused=False)
        return dict(status=work['state'], runId=work['runId'], progress=work['progress'], reused=False)
