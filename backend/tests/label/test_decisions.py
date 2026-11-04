import copy
import json
from pathlib import Path

import httpx
import pytest

from app.config import Settings, settings
from app.label import jev
from app.label.jev import JevError, get_jev_client, jev_available
from app.label.questions import jev_questions

FIXTURE = Path(__file__).parents[1] / 'fixtures/decisions/success.json'
DOC = {'doc_id': 'nc_1', 'title': '제목', 'body': '본문', 'comments': ['댓글']}
ORDER = ['anchor', 'sense', 'feel', 'think', 'act', 'situation', 'relate_outcome', 'reason_code']
BASE = 'https://api.openai.com/v1'


@pytest.fixture
def answer():
    return json.loads(FIXTURE.read_text())


@pytest.fixture(autouse=True)
def decisions_env(monkeypatch):
    jev.reset_limiter_pool()
    monkeypatch.setattr('app.label.jev.time.sleep', lambda _: None)
    monkeypatch.setattr('app.label.jev.ChannelLimiter.wait_start', lambda _: None)
    monkeypatch.setattr('app.label.decisions.time.sleep', lambda _: None, raising=False)
    monkeypatch.setattr(settings, 'jev_backend', 'decisions')
    monkeypatch.setattr(settings, 'decisions_api_keys', [], raising=False)
    monkeypatch.setattr(settings, 'openai_api_key', '')
    monkeypatch.setattr(settings, 'decisions_model', 'gpt-6-luna', raising=False)
    monkeypatch.setattr(settings, 'decisions_rate_per_min', 120, raising=False)
    monkeypatch.setattr(settings, 'decisions_base_url', BASE, raising=False)
    yield
    jev.reset_limiter_pool()


def make_client(handler, keys=('secret',)):
    from app.label.decisions import DecisionsClient
    return DecisionsClient(list(keys), 'gpt-6-luna', transport=httpx.MockTransport(handler))


def respond(payload, status=200):
    def handle(_):
        if isinstance(payload, (bytes, str)):
            return httpx.Response(status, content=payload)
        return httpx.Response(status, json=payload)
    return handle


def judge_with(payload, status=200, truncated_doc=None):
    with make_client(respond(payload, status)) as client:
        return client.judge(truncated_doc or DOC, '대상 경험')


def assert_bad(payload, status=200, transient=False):
    with pytest.raises(JevError) as caught:
        judge_with(payload, status)
    assert caught.value.code == 'bad'
    assert caught.value.transient is transient
    return caught.value


# --- request shape ---

def test_request_snapshot(answer):
    seen = []

    def handle(request):
        seen.append(request)
        return httpx.Response(200, json=answer)

    with make_client(handle) as client:
        client.judge(DOC, '대상 경험', idempotency_key='ignored-key')
    request = seen[0]
    assert request.method == 'POST'
    assert str(request.url) == f'{BASE}/decisions'
    assert request.headers['Authorization'] == 'Bearer secret'
    assert 'Idempotency-Key' not in request.headers
    body = json.loads(request.content)
    assert body['model'] == 'gpt-6-luna'
    assert isinstance(body['input'], str)
    assert body['input'].splitlines()[0] == '[맥락] 대상 경험'
    questions = body['questions']
    assert [q['name'] for q in questions] == ORDER
    assert [q['type'] for q in questions] == ['predicate'] * 6 + ['choice'] * 2
    defs = jev_questions('대상 경험')
    for q in questions[:6]:
        assert set(q) == {'type', 'name', 'instructions'}
        assert q['instructions'] == defs[q['name']]['instructions'] + '\n' + defs[q['name']]['criteria']
        assert q['instructions'].endswith(defs[q['name']]['criteria'])
    for q in questions[6:]:
        assert set(q) == {'type', 'name', 'instructions', 'choices'}
        assert q['instructions'] == defs[q['name']]['instructions']
        criteria = defs[q['name']]['criteria']
        assert q['choices'] == [{'value': k, 'description': v} for k, v in criteria.items()]
    assert [c['value'] for c in questions[6]['choices']] == ['none', 'relate', 'outcome', 'both']


def test_to_decisions_questions_order():
    from app.label.decisions import to_decisions_questions
    converted = to_decisions_questions(jev_questions('x'))
    assert [q['name'] for q in converted] == ORDER


# --- success ---

def test_success_vote(answer):
    vote = judge_with(answer)
    assert vote.model == 'gpt-6-luna-2026-10-01'
    assert vote.truncated is False
    assert vote.probs['anchor'] == pytest.approx(.96)
    assert vote.probs['sense'] == pytest.approx(.12)
    assert vote.probs['act'] == 0
    assert vote.probs['situation'] == 1
    assert vote.probs['relate'] == pytest.approx(.3)
    assert vote.probs['outcome'] == pytest.approx(.7)
    assert set(vote.reason_probs) == {'ad', 'no_needs', 'pure_criticism', 'other', 'not_non'}
    assert sum(vote.reason_probs.values()) == pytest.approx(1)
    assert vote.reason_probs['not_non'] == pytest.approx(.75 / .8)


def test_success_truncated(answer):
    vote = judge_with(answer, truncated_doc={**DOC, 'body': '가' * 12000})
    assert vote.truncated is True


# --- bad responses ---

def _drop(a):
    del a['answers'][3]


def _dup(a):
    a['answers'][3] = copy.deepcopy(a['answers'][2])


def _swap(a):
    a['answers'][0], a['answers'][1] = a['answers'][1], a['answers'][0]


def _type_pred(a):
    a['answers'][0]['type'] = 'choice'


def _type_choice(a):
    a['answers'][6]['type'] = 'predicate'
    a['answers'][6]['probability'] = .5


def _prob(value):
    def mutate(a):
        a['answers'][1]['probability'] = value
    return mutate


def _choice_prob(value):
    def mutate(a):
        a['answers'][7]['probabilities'][0]['probability'] = value
    return mutate


def _choice_missing(a):
    del a['answers'][6]['probabilities'][0]


def _choice_extra(a):
    a['answers'][6]['probabilities'].append({'value': 'other', 'probability': .1})


def _choice_dup(a):
    a['answers'][6]['probabilities'][0]['value'] = 'relate'


def _choice_zero(a):
    for item in a['answers'][6]['probabilities']:
        item['probability'] = 0


def _model_empty(a):
    a['model'] = ''


def _model_missing(a):
    del a['model']


def _answers_dict(a):
    a['answers'] = {item['name']: item for item in a['answers']}


def _choice_dict(a):
    a['answers'][6]['probabilities'] = {'none': .1, 'relate': .2, 'outcome': .6, 'both': .1}


BAD_MUTATIONS = {
    'missing': _drop, 'duplicate': _dup, 'reordered': _swap,
    'type_predicate': _type_pred, 'type_choice': _type_choice,
    'prob_negative': _prob(-0.1), 'prob_over': _prob(1.1), 'prob_nan': _prob(float('nan')),
    'prob_string': _prob('0.5'), 'prob_bool': _prob(True),
    'choice_prob_over': _choice_prob(1.1),
    'choice_missing': _choice_missing, 'choice_extra': _choice_extra, 'choice_dup': _choice_dup,
    'choice_zero': _choice_zero, 'model_empty': _model_empty, 'model_missing': _model_missing,
    'answers_dict': _answers_dict, 'choice_dict': _choice_dict,
}


@pytest.mark.parametrize('name', sorted(BAD_MUTATIONS))
def test_bad_payload(answer, name):
    BAD_MUTATIONS[name](answer)
    # Raw bytes so NaN reaches the parser exactly as a provider would send it.
    assert_bad(json.dumps(answer).encode())


def test_non_json_body():
    assert_bad(b'not json')


# --- refusal ---

def test_refusal(answer):
    answer['answers'][2] = {'name': 'feel', 'type': 'refusal', 'refusal': '거절 사유'}
    with pytest.raises(JevError) as caught:
        judge_with(answer)
    assert caught.value.code == 'refused'
    assert caught.value.transient is False
    assert str(caught.value) == 'Decisions가 이 문서 판정을 거절했습니다'


def test_refusal_beats_format_error(answer):
    answer['answers'][2] = {'name': 'feel', 'type': 'refusal', 'refusal': '거절'}
    answer['answers'][0]['probability'] = 5
    del answer['answers'][7]
    answer['model'] = ''
    with pytest.raises(JevError) as caught:
        judge_with(answer)
    assert caught.value.code == 'refused'


# --- HTTP errors ---

BODY_SECRET = 'provider-body-detail-xyz'


def test_401_unconnected():
    with pytest.raises(JevError) as caught:
        judge_with({'error': {'message': BODY_SECRET}}, 401)
    assert caught.value.code == 'unconnected'
    assert BODY_SECRET not in str(caught.value) and 'secret' not in str(caught.value)


def test_429_insufficient_quota_no_retry():
    calls = []

    def handle(_):
        calls.append(1)
        return httpx.Response(429, json={'error': {'code': 'insufficient_quota', 'message': BODY_SECRET}})

    with make_client(handle) as client, pytest.raises(JevError) as caught:
        client.judge(DOC, '맥락')
    assert caught.value.code == 'insufficient'
    assert caught.value.transient is False
    assert len(calls) == 1
    assert BODY_SECRET not in str(caught.value)


@pytest.mark.parametrize('status', [429, 500, 503])
def test_retry_then_success(answer, status):
    calls = []

    def handle(_):
        calls.append(1)
        if len(calls) < 3:
            return httpx.Response(status, json={'error': {'code': 'rate_limit_exceeded'}})
        return httpx.Response(200, json=answer)

    with make_client(handle) as client:
        vote = client.judge(DOC, '맥락')
    assert vote.model == 'gpt-6-luna-2026-10-01'
    assert len(calls) == 3


@pytest.mark.parametrize('status', [429, 500, 503])
def test_retry_exhausted(monkeypatch, status):
    calls, sleeps = [], []
    monkeypatch.setattr('app.label.decisions.time.sleep', sleeps.append)

    def handle(_):
        calls.append(1)
        return httpx.Response(status, text=BODY_SECRET)

    with make_client(handle) as client, pytest.raises(JevError) as caught:
        client.judge(DOC, '맥락')
    assert caught.value.code == 'bad'
    assert caught.value.transient is True
    assert len(calls) == 6
    assert sleeps == [1, 2, 4, 8, 16]
    assert BODY_SECRET not in str(caught.value)


def test_connect_error_transient():
    def handle(request):
        raise httpx.ConnectError('boom secret', request=request)

    with make_client(handle) as client, pytest.raises(JevError) as caught:
        client.judge(DOC, '맥락')
    assert caught.value.code == 'bad'
    assert caught.value.transient is True
    assert 'secret' not in str(caught.value)


@pytest.mark.parametrize('status', [400, 404])
def test_other_status_bad(status):
    error = assert_bad({'error': {'message': BODY_SECRET}}, status)
    assert BODY_SECRET not in str(error) and 'secret' not in str(error)


# --- keys ---

def test_env_keys_split(monkeypatch):
    monkeypatch.setenv('DECISIONS_API_KEY', ' k1 , k2 ,')
    monkeypatch.setenv('DECISIONS_MODEL', '')
    monkeypatch.setenv('DECISIONS_RATE_PER_MIN', '')
    monkeypatch.setenv('DECISIONS_BASE_URL', '')
    monkeypatch.setenv('JEV_BACKEND', 'decisions')
    loaded = Settings(_env_file=None)
    assert loaded.decisions_api_keys == ['k1', 'k2']
    assert loaded.decisions_model == 'gpt-6-luna'
    assert loaded.decisions_rate_per_min == 120
    assert loaded.decisions_base_url == 'https://api.openai.com/v1'
    assert loaded.jev_backend == 'decisions'


def test_keys_round_robin(answer, monkeypatch):
    seen = []

    def handle(request):
        seen.append(request.headers['Authorization'])
        return httpx.Response(200, json=answer)

    monkeypatch.setattr(settings, 'decisions_api_keys', ['k1', 'k2', 'k1'])
    with get_jev_client(transport=httpx.MockTransport(handle)) as client:
        for _ in range(4):
            client.judge(DOC, '맥락')
    assert seen == ['Bearer k1', 'Bearer k2', 'Bearer k1', 'Bearer k2']


def test_openai_key_fallback(answer, monkeypatch):
    seen = []

    def handle(request):
        seen.append(request.headers['Authorization'])
        return httpx.Response(200, json=answer)

    monkeypatch.setattr(settings, 'openai_api_key', 'sk-openai')
    with get_jev_client(transport=httpx.MockTransport(handle)) as client:
        client.judge(DOC, '맥락')
    assert seen == ['Bearer sk-openai']


def test_no_keys_unconnected():
    calls = []
    with get_jev_client(transport=httpx.MockTransport(lambda r: calls.append(r))) as client:
        with pytest.raises(JevError) as caught:
            client.judge(DOC, '맥락')
    assert caught.value.code == 'unconnected'
    assert calls == []


def test_rate_must_be_positive(monkeypatch):
    monkeypatch.setattr(settings, 'decisions_rate_per_min', 0)
    with pytest.raises(ValueError):
        make_client(respond({}))
    monkeypatch.setattr(settings, 'decisions_rate_per_min', 1000)
    make_client(respond({})).close()


# --- backend selection ---

def test_jev_available_branches(monkeypatch):
    assert jev_available() is False
    monkeypatch.setattr(settings, 'decisions_api_keys', ['k'])
    assert jev_available() is True
    monkeypatch.setattr(settings, 'decisions_api_keys', [])
    monkeypatch.setattr(settings, 'openai_api_key', 'sk')
    assert jev_available() is True
    monkeypatch.setattr(settings, 'jev_backend', 'http')
    monkeypatch.setattr(settings, 'jev_api_keys', [])
    assert jev_available() is False
    monkeypatch.setattr(settings, 'jev_api_keys', ['j'])
    assert jev_available() is True
    monkeypatch.setattr(settings, 'jev_backend', 'fake')
    monkeypatch.setattr(settings, 'label_fake_jev_cross', True)
    assert jev_available() is True


def test_get_jev_client_branches(monkeypatch):
    from app.label.decisions import DecisionsClient
    client = get_jev_client()
    assert isinstance(client, DecisionsClient)
    assert client.model == 'gpt-6-luna'
    client.close()
    client = get_jev_client(keys=['x'], model='other')
    assert isinstance(client, DecisionsClient) and client.model == 'other'
    client.close()
    monkeypatch.setattr(settings, 'jev_backend', 'http')
    client = get_jev_client()
    assert isinstance(client, jev.JevClient)
    client.close()
    monkeypatch.setattr(settings, 'jev_backend', 'fake')
    assert isinstance(get_jev_client(), jev.FakeJevClient)


def test_real_socket_blocked_by_conftest(monkeypatch):
    # An IP literal avoids DNS; the conftest guard must escape rather than be wrapped as `bad`.
    monkeypatch.setattr(settings, 'decisions_base_url', 'https://203.0.113.10/v1')
    monkeypatch.setattr(settings, 'decisions_api_keys', ['k'])
    with get_jev_client() as client:
        with pytest.raises(pytest.fail.Exception, match='External network connection forbidden'):
            client.judge(DOC, '맥락')
