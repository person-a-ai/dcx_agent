from contextlib import contextmanager
import pytest
from app.context import store as sessions
from app.persona import insight_pipeline
from app.routers import stage8
from tests.persona.test_insights import env
from tests.persona.test_chat import ready, context


def test_fresh_recorded_returned_and_retry_derives(ready, monkeypatch):
    session, store, _, backend = ready
    monkeypatch.setattr(insight_pipeline.registry, 'run_task', backend.run)
    ctx = context(ready, mode='derive', fresh=True)
    ctx.should_stop = lambda: True
    insight_pipeline.run(ctx)
    monkeypatch.setattr(stage8.runner, 'status', lambda sid: [])
    worker = stage8._insight_worker(session.sid, sessions.load_session(session.sid))
    assert worker['fresh'] is True
    insight_pipeline.run(context(ready, mode=worker['mode'], fresh=worker['fresh']))
    assert store.read('insights')['revision'] == 2


@pytest.mark.parametrize('stop', [True, False, 'error'])
def test_fresh_confirmation_clear_survives_post_publish_stop_and_reads_locked(ready, monkeypatch, stop):
    session, store, _, backend = ready
    sessions.update_session(session.sid, {'insight': {'confirmed': ['I1'], 'confirmed_ids': ['I1', 'hidden']}})
    monkeypatch.setattr(insight_pipeline.registry, 'run_task', backend.run)
    original = insight_pipeline.derive
    published = False
    locked = False
    original_lock = sessions.locked
    original_read = sessions.read_json
    @contextmanager
    def tracked_lock(sid):
        nonlocal locked
        with original_lock(sid):
            locked = True
            try:
                yield
            finally:
                locked = False
    checked = False
    def read(path):
        nonlocal checked
        if not checked and published and str(path).endswith('session.json'):
            assert locked, 'confirmation state read outside session lock'
            checked = True
        return original_read(path)
    def derive(*args, **kwargs):
        nonlocal published
        result = original(*args, **kwargs)
        published = True
        if stop == 'error':
            raise RuntimeError('failure after revision publication')
        return result
    monkeypatch.setattr(sessions, 'locked', tracked_lock)
    monkeypatch.setattr(sessions, 'read_json', read)
    monkeypatch.setattr(insight_pipeline, 'derive', derive)
    ctx = context(ready, mode='derive', fresh=True)
    ctx.should_stop = lambda: published and stop is True
    if stop == 'error':
        with pytest.raises(RuntimeError, match='after revision'):
            insight_pipeline.run(ctx)
    else:
        insight_pipeline.run(ctx)
    monkeypatch.setattr(sessions, 'read_json', original_read)
    state = sessions.load_session(session.sid)['insight']
    assert checked
    assert state['confirmed'] == []
    assert state['confirmed_ids'] == ['hidden']


def test_edit_v2_prompt_declares_flow_length_and_unique_hashtags():
    from pathlib import Path
    prompt = (Path(insight_pipeline.__file__).parent / 'prompts' / 'edit.v2.md').read_text()
    assert 'flow text: 각 문장은 1~80자.' in prompt
    assert 'hashtags: 중복 없이 2~4개' in prompt
