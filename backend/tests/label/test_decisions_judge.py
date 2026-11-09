"""Judge worker, estimate and overview wiring for the Decisions backend (JEV_BACKEND=decisions)."""
import copy
import json
import math
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

from app.config import settings
from app.context import store, versions
from app.crawl.ratelimit import ChannelLimiter
from app.label import jev
from app.label.questions import jev_questions
from app.label.schema import JevVote

FIXTURE = Path(__file__).parents[1] / 'fixtures/decisions/success.json'
BASE = 'https://api.openai.com/v1'
ONE_LINER = '사용 경험'
PREP_KEY = 'p_123456789abc'


class Context:
    sid = 'session'
    version = 'v1'
    run_id = 'run'

    def __init__(self, labeler='jev'):
        self.args = {'labeler': labeler}
        self.details = []
        self.stopped = False

    def heartbeat(self, progress, detail):
        self.details.append(json.loads(json.dumps(detail)))

    def should_stop(self):
        return self.stopped


def refusal(answer):
    refused = copy.deepcopy(answer)
    refused['answers'][2] = {'name': 'feel', 'type': 'refusal', 'refusal': '거절 사유'}
    return refused


@pytest.fixture
def env(data_dir, monkeypatch):
    from app.label import judge
    jev.reset_limiter_pool()
    monkeypatch.setattr(ChannelLimiter, 'wait_start', lambda self: None)
    monkeypatch.setattr('app.label.decisions.time.sleep', lambda _: None)
    monkeypatch.setattr(settings, 'jev_backend', 'decisions')
    monkeypatch.setattr(settings, 'jev_api_keys', ['jev-key'])
    monkeypatch.setattr(settings, 'jev_model', 'jev-latest')
    monkeypatch.setattr(settings, 'decisions_api_keys', ['dec-key'])
    monkeypatch.setattr(settings, 'decisions_model', 'gpt-6-luna')
    monkeypatch.setattr(settings, 'decisions_rate_per_min', 120)
    monkeypatch.setattr(settings, 'decisions_base_url', BASE)
    monkeypatch.setattr(settings, 'openai_api_key', '')
    monkeypatch.setattr(settings, 'label_gpt_backend', 'fake')
    answer = json.loads(FIXTURE.read_text())
    requests = []
    responder = {'fn': lambda body: httpx.Response(200, json=answer)}

    def handle(request):
        body = json.loads(request.content)
        requests.append(dict(auth=request.headers.get('Authorization'), url=str(request.url), body=body))
        return responder['fn'](body)

    # Route through the real backend selection; only the transport is offline.
    monkeypatch.setattr(judge, 'JevClient',
                        lambda keys, model: jev.get_jev_client(keys, model, transport=httpx.MockTransport(handle)))

    def prepare(n=3):
        session = dict(projectContext={'oneLiner': ONE_LINER},
                       prep={'derivedRef': {'collectionId': 'c1', 'prepKey': PREP_KEY}})
        store.write_json(versions.version_dir('session', 'v1') / 'session.json', session)
        root = data_dir / f'derived/session/c1/{PREP_KEY}/docs'
        root.mkdir(parents=True, exist_ok=True)
        docs = [dict(doc_id=f'd{i:03}', body='본문', title=f'제목{i:03}') for i in range(n)]
        (root / '000.jsonl').write_text(''.join(json.dumps(doc, ensure_ascii=False) + '\n' for doc in docs))
        return docs

    yield SimpleNamespace(judge=judge, prepare=prepare, requests=requests, responder=responder, answer=answer)
    jev.reset_limiter_pool()


def cache_for(env, labeler='jev'):
    from app.label.votes import VoteCache
    return VoteCache(env.judge.cache_root('session', PREP_KEY, labeler, ONE_LINER))


def rows(cache):
    with cache._db() as db:
        return {r[0]: dict(status=r[1], payload=r[2], error=r[3])
                for r in db.execute('SELECT doc_id, status, payload_json, last_error FROM votes')}


def test_decisions_worker_fills_jev_slot_and_merges_with_gpt(env):
    from app.label.store import LabelStore
    env.prepare(3)
    env.judge.run_worker(Context('jev'))
    assert {r['auth'] for r in env.requests} == {'Bearer dec-key'}
    assert {r['body']['model'] for r in env.requests} == {'gpt-6-luna'}
    assert {r['url'] for r in env.requests} == {f'{BASE}/decisions'}
    cache = cache_for(env)
    assert cache.counts() == dict(pending=0, done=3, bad=0)
    for row in rows(cache).values():
        vote = JevVote.model_validate(json.loads(row['payload']))
        assert vote.model == 'gpt-6-luna-2026-10-01'
    env.judge.run_worker(Context('gpt'))
    with LabelStore(versions.version_dir('session', 'v1'))._db() as db:
        assert db.execute('SELECT count(*) FROM final').fetchone()[0] == 3
    # This minimal fixture session reads as legacy in overview(); the API test
    # below covers crossLabeler on a full session.
    assert jev.labeler_mode(versions._data('session', 'v1')) == 'cross'


def test_refused_document_is_bad_with_refused_code(env):
    env.prepare(3)
    env.responder['fn'] = lambda body: httpx.Response(
        200, json=refusal(env.answer) if '[제목] 제목001' in body['input'] else env.answer)
    env.judge.run_worker(Context('jev'))
    result = rows(cache_for(env))
    assert result['d001']['status'] == 'bad'
    assert result['d001']['error'] == 'refused'
    assert result['d000']['status'] == result['d002']['status'] == 'done'
    # Refusal is final: one request, no client retry, no worker re-lease.
    refused_calls = [r for r in env.requests if '[제목] 제목001' in r['body']['input']]
    assert len(refused_calls) == 1
    assert len(env.requests) == 3


def test_401_stops_worker_unconnected(env, monkeypatch):
    env.prepare(3)
    env.responder['fn'] = lambda body: httpx.Response(401, json={'error': {'message': 'bad key'}})
    monkeypatch.setattr(env.judge, '_pause', lambda *a: pytest.fail('401 must stop, not pause'))
    ctx = Context('jev')
    with pytest.raises(jev.JevError) as caught:
        env.judge.run_worker(ctx)
    assert caught.value.code == 'unconnected'
    assert ctx.details[-1]['code'] == 'unconnected'
    assert cache_for(env).counts() == dict(pending=3, done=0, bad=0)
    assert len(env.requests) == 1


def test_429_insufficient_quota_pauses(env, monkeypatch):
    env.prepare(3)
    env.responder['fn'] = lambda body: httpx.Response(429, json={'error': {'code': 'insufficient_quota'}})
    reasons = []

    def pause(ctx, reason, detail):
        reasons.append(reason)
        ctx.stopped = True

    monkeypatch.setattr(env.judge, '_pause', pause)
    env.judge.run_worker(Context('jev'))
    assert reasons == ['Decisions 사용 한도가 부족합니다']
    assert cache_for(env).counts() == dict(pending=3, done=0, bad=0)
    assert len(env.requests) == 1


def test_cache_root_differs_between_http_and_decisions(env, monkeypatch):
    decisions_root = env.judge.cache_root('session', PREP_KEY, 'jev', ONE_LINER)
    decisions_key = env.judge.context_key(ONE_LINER, 'jev')
    monkeypatch.setattr(settings, 'jev_backend', 'http')
    http_root = env.judge.cache_root('session', PREP_KEY, 'jev', ONE_LINER)
    assert decisions_root != http_root
    assert decisions_root.parent == http_root.parent
    # The Decisions identity follows its own model, not jev_model.
    monkeypatch.setattr(settings, 'jev_backend', 'decisions')
    monkeypatch.setattr(settings, 'jev_model', 'other-jev')
    assert env.judge.context_key(ONE_LINER, 'jev') == decisions_key
    monkeypatch.setattr(settings, 'decisions_model', 'other-decisions')
    assert env.judge.context_key(ONE_LINER, 'jev') != decisions_key


def decisions_tokens(docs):
    from app.label.decisions import to_decisions_questions
    questions = to_decisions_questions(jev_questions(ONE_LINER))
    return sum(math.ceil(len(json.dumps(dict(model=settings.decisions_model, input=jev.build_state(d, ONE_LINER)[0],
                                                 questions=questions),
                                            ensure_ascii=False, separators=(',', ':'))) / 4) for d in docs)


def test_decisions_estimate_seconds_tokens_and_cost(env, monkeypatch):
    monkeypatch.setattr(settings, 'decisions_api_keys', ['k1', 'k2', 'k2'])
    monkeypatch.setattr(settings, 'decisions_rate_per_min', 60)
    docs = [dict(doc_id=f'd{i:03}', body='본문', title='제목') for i in range(120)]
    result = env.judge.estimate(docs, ONE_LINER, 'jev')
    assert result['seconds'] == 60
    tokens = decisions_tokens(docs)
    assert result['jevTokens'] == tokens
    assert result['jevCostUsd'] == pytest.approx(tokens * 0.10 / 1_000_000)


def test_decisions_estimate_falls_back_to_one_openai_key(env, monkeypatch):
    monkeypatch.setattr(settings, 'decisions_api_keys', [])
    monkeypatch.setattr(settings, 'openai_api_key', 'sk-test')
    monkeypatch.setattr(settings, 'decisions_rate_per_min', 60)
    docs = [dict(doc_id=f'd{i:03}', body='본문', title='제목') for i in range(60)]
    assert env.judge.estimate(docs, ONE_LINER, 'jev')['seconds'] == 60
    monkeypatch.setattr(settings, 'openai_api_key', '')
    assert env.judge.estimate(docs, ONE_LINER, 'jev')['seconds'] is None


@pytest.mark.parametrize('labeler', ['jev', 'gpt'])
def test_non_decisions_estimate_has_no_cost(env, monkeypatch, labeler):
    monkeypatch.setattr(settings, 'jev_backend', 'http')
    docs = [dict(doc_id='d000', body='본문', title='제목')]
    assert env.judge.estimate(docs, ONE_LINER, labeler).get('jevCostUsd') is None


def test_worker_publishes_cost_in_estimate(env):
    env.prepare(3)
    ctx = Context('jev')
    env.judge.run_worker(ctx)
    costs = [d['estimate'].get('jevCostUsd') for d in ctx.details if 'estimate' in d]
    assert costs and all(c is not None and c > 0 for c in costs)


@pytest.mark.parametrize('backend, name', [('decisions', 'Decisions'), ('http', 'Jev')])
def test_overview_api_cross_labeler(client, data_dir, monkeypatch, backend, name):
    from tests.model.test_gpt_only_training import seed_gpt
    monkeypatch.setattr(settings, 'jev_backend', backend)
    sid, _, _ = seed_gpt(data_dir)
    store.update_session(sid, {'labeling': {'labelerMode': 'cross'}})
    response = client.get(f'/label/{sid}/overview')
    assert response.status_code == 200
    view = response.json()
    assert view['crossLabeler'] == name
    assert 'jevCostUsd' in view['progress']['jev']['estimate']
