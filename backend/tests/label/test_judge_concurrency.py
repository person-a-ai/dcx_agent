from collections import Counter
import os
import threading
import time

import pytest

from app.config import settings
from app.label import gpt
from app.label.rule import SEM
from app.label.votes import VoteCache
from app.work.status import transaction
from tests.label.test_judge import Context, cache_for, setup_judge


@pytest.fixture
def concurrent_judge(setup_judge, monkeypatch):
    env = setup_judge
    env.prepare(8)
    monkeypatch.setattr(settings, 'label_batch_size', 2)
    monkeypatch.setattr(settings, 'label_concurrency', 4)
    monkeypatch.setattr(settings, 'jev_backend', 'fake')
    env.puts = []
    env.fails = []
    owner = threading.get_ident()
    put, fail = VoteCache.put, VoteCache.fail

    def record_put(cache, doc_id, payload):
        assert threading.get_ident() == owner
        env.puts.append(doc_id)
        put(cache, doc_id, payload)

    def record_fail(cache, doc_id, reason):
        assert threading.get_ident() == owner
        env.fails.append((doc_id, reason))
        fail(cache, doc_id, reason)

    monkeypatch.setattr(VoteCache, 'put', record_put)
    monkeypatch.setattr(VoteCache, 'fail', record_fail)
    return env


def votes(docs):
    return {d['doc_id']: gpt.GptVote(anchor=False, sem=dict.fromkeys(SEM, 0),
            situation=False, reason_code='no_needs', signal=None) for d in docs}, []


def rows(env):
    with cache_for(env, 'gpt')._db() as db:
        return {r['doc_id']: dict(r) for r in db.execute('SELECT * FROM votes')}


@pytest.mark.parametrize('concurrency', [4, 1, 0])
def test_batches_overlap_and_put_once(concurrent_judge, monkeypatch, concurrency):
    env = concurrent_judge
    monkeypatch.setattr(settings, 'label_concurrency', concurrency)
    barrier = threading.Barrier(4, timeout=5) if concurrency == 4 else None
    lock = threading.Lock()
    calls = []
    active = maximum = 0

    def judge(docs, *args, **kwargs):
        nonlocal active, maximum
        with lock:
            calls.append([d['doc_id'] for d in docs])
            active += 1
            maximum = max(maximum, active)
        try:
            if barrier:
                barrier.wait()
            else:
                time.sleep(.01)
            return votes(docs)
        finally:
            with lock:
                active -= 1

    monkeypatch.setattr(gpt, 'judge_batch', judge)
    env.judge.run_worker(Context('gpt'))
    assert maximum == max(1, concurrency)
    assert sorted(calls) == [[f'd{i:03}', f'd{i+1:03}'] for i in range(0, 8, 2)]
    assert Counter(env.puts) == Counter(f'd{i:03}' for i in range(8))
    assert cache_for(env, 'gpt').counts() == dict(pending=0, done=8, bad=0)


@pytest.mark.parametrize('failure', ['limit', 'backend', 'missing', 'error', 'mixed'])
@pytest.mark.parametrize('attempts', [0, 2])
def test_chunk_failures_preserve_peers(concurrent_judge, monkeypatch, failure, attempts):
    env = concurrent_judge
    monkeypatch.setattr(settings, 'label_gpt_backend', 'codex_exec')
    monkeypatch.setattr(settings, 'label_failure_pause_after', 5)
    # Collect the initial group together to make success evidence deterministic.
    real_wait = env.judge.wait
    monkeypatch.setattr(env.judge, 'wait', lambda fs, **kw: real_wait(fs))
    cache = cache_for(env, 'gpt')
    cache.seed(f'd{i:03}' for i in range(8))
    with cache._db() as db:
        db.execute('UPDATE votes SET attempts=?', (attempts,))
    barrier = threading.Barrier(4, timeout=5)
    seen = set()
    lock = threading.Lock()
    error = ValueError('unexpected failure')

    def judge(docs, *args, **kwargs):
        ids = [d['doc_id'] for d in docs]
        with lock:
            first = ids[0] not in seen
            seen.update(ids)
        if first:
            barrier.wait()
        if ids[0] == 'd000':
            if failure in ('limit', 'mixed'):
                raise gpt.LabelerPaused('usage limit', usage_limit=True)
            if failure == 'backend':
                raise gpt.LabelerPaused('backend failed')
            if failure == 'error':
                raise error
            result, _ = votes(docs[1:])
            return result, ids[:1]
        if failure == 'mixed' and ids[0] == 'd002':
            raise gpt.LabelerPaused('backend failed')
        return votes(docs)

    ctx = Context('gpt')
    with transaction(ctx.sid) as db:
        db.execute("INSERT INTO runs(run_id,version,kind,args_json,pid,state,heartbeat_at,started_at) VALUES ('run','v1','judge','{}',?,'running',?,?)", (os.getpid(), time.time(), time.time()))
    heartbeat = ctx.heartbeat

    def stop_on_pause(progress, detail):
        heartbeat(progress, detail)
        if detail.get('reason'):
            ctx.stopped = True

    ctx.heartbeat = stop_on_pause
    monkeypatch.setattr(gpt, 'judge_batch', judge)
    if failure == 'error':
        with pytest.raises(ValueError) as caught:
            env.judge.run_worker(ctx)
        assert caught.value is error
    else:
        env.judge.run_worker(ctx)
    result = rows(env)
    failed = {'d000'} if failure == 'missing' else {'d000', 'd001'}
    if failure == 'mixed':
        failed |= {'d002', 'd003'}
    successful = set(result) - failed
    assert Counter(env.puts) == Counter(successful)
    assert all(result[i]['status'] == 'done' for i in successful)
    assert all(r['run_id'] is None for r in result.values())
    for doc_id in failed:
        row = result[doc_id]
        retry = failure in ('backend', 'missing') or (failure == 'mixed' and doc_id >= 'd002')
        assert row['status'] == ('bad' if retry and (attempts == 2 or failure == 'missing') else 'pending')
        assert row['last_error'] == (('invalid_or_missing_vote' if failure == 'missing' else 'gpt_backend_failed') if retry else None)
        assert row['attempts'] == (3 if failure == 'missing' else attempts + int(retry))
    if failure in ('limit', 'mixed') or (failure == 'backend' and attempts == 0):
        with transaction(ctx.sid) as db:
            assert db.execute("SELECT state FROM runs WHERE run_id='run'").fetchone()[0] == 'paused'
        assert [d['reason'] for d in ctx.details if 'reason' in d] == [
            env.judge.BREAKER_MESSAGE if failure == 'backend' else 'usage limit']


def test_finished_slot_is_refilled_while_a_slow_batch_runs(concurrent_judge, monkeypatch):
    env = concurrent_judge
    monkeypatch.setattr(settings, 'label_concurrency', 2)
    third_started = threading.Event()
    order = []
    lock = threading.Lock()

    def judge(docs, *args, **kwargs):
        with lock:
            order.append(docs[0]['doc_id'])
            position = len(order)
        if position == 1:
            # The slow first batch only finishes once a refilled batch has started.
            assert third_started.wait(5), 'slot was not refilled while the slow batch ran'
        elif position == 3:
            third_started.set()
        return votes(docs)

    monkeypatch.setattr(gpt, 'judge_batch', judge)
    env.judge.run_worker(Context('gpt'))
    assert third_started.is_set() and sorted(env.puts) == sorted(rows(env))


def run_failure_case(env, monkeypatch, judge, *, threshold=5, concurrency=1, resumes=0, backend='codex_exec'):
    monkeypatch.setattr(settings, 'label_gpt_backend', backend)
    monkeypatch.setattr(settings, 'label_failure_pause_after', threshold)
    monkeypatch.setattr(settings, 'label_concurrency', concurrency)
    monkeypatch.setattr(gpt, 'judge_batch', judge)
    ctx = Context('gpt')
    reasons = []
    with transaction(ctx.sid) as db:
        db.execute("INSERT INTO runs(run_id,version,kind,args_json,pid,state,heartbeat_at,started_at) VALUES ('run','v1','judge','{}',?,'running',?,?)", (os.getpid(), time.time(), time.time()))
    original_pause = env.judge._pause

    def pause(context, reason, detail):
        reasons.append(reason)
        original_pause(context, reason, detail)
        if len(reasons) > resumes:
            context.stopped = True
    monkeypatch.setattr(env.judge, '_pause', pause)
    env.judge.run_worker(ctx)
    return reasons


def backend_failure(*args, **kwargs):
    raise gpt.LabelerPaused('API 실패')


def test_isolated_failures_do_not_pause(concurrent_judge, monkeypatch):
    env = concurrent_judge
    calls = Counter()
    def judge(docs, *a, **kw):
        key = docs[0]['doc_id']
        calls[key] += 1
        if key == 'd000' and calls[key] <= 2:
            return backend_failure()
        return votes(docs)
    assert run_failure_case(env, monkeypatch, judge) == []
    assert cache_for(env, 'gpt').counts() == dict(done=8, pending=0, bad=0)


def test_consecutive_failures_pause(concurrent_judge, monkeypatch):
    env = concurrent_judge
    assert run_failure_case(env, monkeypatch, backend_failure, concurrency=4) == [env.judge.BREAKER_MESSAGE]
    assert cache_for(env, 'gpt').counts()['bad'] == 0
    assert all(r['attempts'] <= 2 for r in rows(env).values())
    with transaction('session') as db:
        assert db.execute("SELECT state FROM runs WHERE run_id='run'").fetchone()[0] == 'paused'


@pytest.mark.parametrize('attempts', [0, 2])
def test_outage_does_not_spend_attempts(concurrent_judge, monkeypatch, attempts):
    env = concurrent_judge
    env.prepare(2)
    monkeypatch.setattr(settings, 'label_gpt_backend', 'codex_exec')
    cache = cache_for(env, 'gpt')
    cache.seed(['d000', 'd001'])
    with cache._db() as db:
        db.execute('UPDATE votes SET attempts=?', (attempts,))
    assert run_failure_case(env, monkeypatch, backend_failure) == [env.judge.BREAKER_MESSAGE]
    assert all(r['attempts'] == attempts and r['status'] == 'pending' for r in rows(env).values())


def test_success_resets_counter(concurrent_judge, monkeypatch):
    calls = Counter()
    def judge(docs, *a, **kw):
        key = docs[0]['doc_id']
        calls[key] += 1
        if key in ('d000', 'd004') and calls[key] == 1:
            return backend_failure()
        return votes(docs)
    assert run_failure_case(concurrent_judge, monkeypatch, judge, threshold=2) == []


def test_resume_resets_counter(concurrent_judge, monkeypatch):
    env = concurrent_judge
    env.prepare(2)
    calls = 0
    def judge(docs, *a, **kw):
        nonlocal calls
        calls += 1
        if calls <= 3:
            return backend_failure()
        return votes(docs)
    assert run_failure_case(env, monkeypatch, judge, threshold=2, resumes=1) == [env.judge.BREAKER_MESSAGE]
    assert cache_for(env, 'gpt').counts()['done'] == 2


def test_failures_between_successes_count(concurrent_judge, monkeypatch):
    env = concurrent_judge
    def judge(docs, *a, **kw):
        if docs[0]['doc_id'] == 'd000':
            return backend_failure()
        return votes(docs)
    reasons = run_failure_case(env, monkeypatch, judge, resumes=3)
    assert 1 <= len(reasons) <= 3
    assert cache_for(env, 'gpt').counts() == dict(done=6, pending=0, bad=2)
    assert all(rows(env)[i]['attempts'] == 3 for i in ('d000', 'd001'))


def test_successes_counted_first(concurrent_judge, monkeypatch):
    env = concurrent_judge
    barrier = threading.Barrier(4, timeout=5)
    calls = Counter()
    lock = threading.Lock()
    real_wait = env.judge.wait
    monkeypatch.setattr(env.judge, 'wait', lambda fs, **kw: real_wait(fs))
    def judge(docs, *a, **kw):
        key = docs[0]['doc_id']
        with lock:
            calls[key] += 1
            first = calls[key] == 1
        if first:
            barrier.wait()
            if key != 'd006':
                return backend_failure()
        return votes(docs)
    assert run_failure_case(env, monkeypatch, judge, threshold=4, concurrency=4) == []
    assert cache_for(env, 'gpt').counts()['done'] == 8
    assert all(rows(env)[f'd{i:03}']['attempts'] == 1 for i in range(6))


def test_api_backend_still_pauses_immediately(concurrent_judge, monkeypatch):
    env = concurrent_judge
    assert run_failure_case(env, monkeypatch, backend_failure, backend='openai_api') == ['API 실패']
    assert rows(env)['d000']['attempts'] == 1


def test_failed_chunk_does_not_starve_peers(concurrent_judge, monkeypatch):
    env = concurrent_judge
    calls = Counter()

    def judge(docs, *a, **kw):
        key = docs[0]['doc_id']
        calls[key] += 1
        if key == 'd000':
            return backend_failure()
        return votes(docs)

    assert run_failure_case(env, monkeypatch, judge, concurrency=1, resumes=0) == [env.judge.BREAKER_MESSAGE]
    result = rows(env)
    assert all(result[f'd{i:03}']['status'] == 'done' for i in range(2, 8))
    assert cache_for(env, 'gpt').counts() == dict(done=6, pending=2, bad=0)
    for doc_id in ('d000', 'd001'):
        assert result[doc_id]['status'] == 'pending'
        assert result[doc_id]['attempts'] == 1
        assert result[doc_id]['last_error'] == 'gpt_backend_failed'
        assert result[doc_id]['run_id'] is None
    assert calls == Counter(d000=6, d002=1, d004=1, d006=1)
