import json
from datetime import datetime

from app.context.store import load_session

from app.prep.documents import crawl_docs, filter_documents
from app.services.s3 import save_jsonl
from app.jobs.manager import job_manager


class _InlineContext:
    def __init__(self, config):
        self.args = {'config': config}

    def heartbeat(self, progress, detail):
        pass

    def should_pause(self):
        return False

    def should_stop(self):
        return False


def preprocess_data(config: dict) -> None:
    sid = config.get("sid", "s0")
    ad_filter = config.get("adFilter", [])
    exclude_cafes = config.get("excludeCafes", [])

    if isinstance(exclude_cafes, str):
        exclude_cafes = [x.strip() for x in exclude_cafes.split(",") if x.strip()]

    try:
        session = load_session(sid) or {}
        if session.get('schemaVersion') == 2:
            from app.prep.pipeline import run_prep
            from app.vectors.embedder import EmbedderUnconnected
            from app.prep.guards import assert_ready, legacy_config
            cfg = legacy_config(session, config)
            assert_ready(sid, session, cfg)
            prep_config = cfg.model_dump()
            try:
                root = run_prep(_InlineContext(prep_config), sid, session.get('version', 'v1'))
            except EmbedderUnconnected as error:
                counts = error.prep_counts
                job_manager.set('preprocess', sid, {
                    'status': 'done', 'original': counts['original'], 'filtered': counts['after'],
                    'embedding': 'unconnected',
                })
                return
            report = json.loads((root / 'stage_3.json').read_text(encoding='utf-8'))
            job_manager.set('preprocess', sid, {
                'status': 'done', 'original': report['original'], 'filtered': report['after'],
            })
            return
        all_data = crawl_docs(sid, session)
        original = len(all_data)
        filtered, _ = filter_documents(all_data, ad_filter, exclude_cafes)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_jsonl(f"preprocessed/{sid}/{ts}.jsonl", filtered)
        job_manager.set("preprocess", sid, {
            "status": "done", "original": original, "filtered": len(filtered),
        })
    except Exception as e:
        job_manager.set("preprocess", sid, {"status": "error", "error": str(e)})
