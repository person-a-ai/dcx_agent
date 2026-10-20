"""Offline stage 0–2, preparation, and v2 export contracts."""
import importlib.util
import json
from pathlib import Path
import socket
import time

import numpy as np
import httpx
import pytest

from app.config import settings
from app.context import store
from app.crawl import control, worker
from app.external import naver_searchad, naver_shopping
from app.external.base import integration_status
from app.keywords import rounds
from app.keywords.prompts import MIN_COUNT
from app.llm.fake import FakeBackend
from app.services.s3 import load_data, save_jsonl

CTX = dict(bk='에어컨', oneLiner='시원한 공기', researchQuestion={'text': '냉방 경험은?'},
           projectType={'choice': 'new'}, analysisGoal={'choice': 'needs'}, keyMetrics=['만족'],
           constraints=[], positioning={'price': 'value', 'market': 'new'}, channels=['fixture'],
           productCategory={'l1': '가전', 'source': 'user'})
KEY_FIELDS = [name for name in type(settings).model_fields
              if name != 'keyword_locked_rounds'
              and ('key' in name or 'secret' in name or name in ('naver_client_id', 'searchad_customer_id'))]


@pytest.fixture
def offline(data_dir, monkeypatch):
    for name, value in {'STORAGE': 'local', 'EMBED_BACKEND': 'fake', 'EMBED_MODEL': 'voyage-4',
                        'EMBED_DIM': '1024', 'VOYAGE_API_KEY': ''}.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(settings, 'voyage_api_key', '')
    def no_network(*args, **kwargs):
        raise AssertionError('Network is forbidden')
    monkeypatch.setattr(socket.socket, 'connect', no_network)
    for name in KEY_FIELDS:
        monkeypatch.setattr(settings, name, '')
    monkeypatch.setattr(settings, 'author_salt_path', str(data_dir / '.author_salt'))
    monkeypatch.setattr(settings, 'enable_fixture_channel', True)
    corpus = data_dir / 'corpus.csv'
    spec = importlib.util.spec_from_file_location('make_corpus', Path(__file__).parent / 'fixtures/make_corpus.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.write_corpus(corpus, 200)
    # Keep all 200 reviews reachable after R2 is skipped, using R1 fixture terms.
    corpus.write_text(corpus.read_text(encoding='utf-8').replace('냉방2단어', '냉방1단어'),
                      encoding='utf-8')
    monkeypatch.setattr(settings, 'fixture_corpus_path', str(corpus))
    fake_dir = data_dir / 'fake_llm'
    fake_dir.mkdir()
    responses = {'category_suggest': {'l1': '가전', 'l2': '계절가전', 'l3': '에어컨'}}
    for n in range(1, 5):
        responses[f'kw_round_{n}'] = {'keywords': [
            {'kw': f'냉방{n}단어{i}', 'axis': 'physical', 'sub': 'space', 'why': '상황'}
            for i in range(MIN_COUNT[n])]}
    for name, response in responses.items():
        (fake_dir / f'{name}.json').write_text(json.dumps(response), encoding='utf-8')
    monkeypatch.setattr(FakeBackend, 'fixture_dir', fake_dir)
    monkeypatch.setattr(settings, 'llm_backend_overrides', {'kw_round_*': 'fake', 'category_suggest': 'fake'})
    monkeypatch.setattr(rounds, 'execute', lambda fn: fn())
    # Defer execution until API session/collection locks are released.
    pending = []
    def spawn(sid, root, queue, kind, snapshot=None):
        pending.append((sid, root, kind, snapshot))
        return {'collectionId': root.name, 'kind': kind, 'status': 'running', 'pid': 0}
    monkeypatch.setattr(control, '_spawn', spawn)
    return pending


def full_flow(client, offline, default_config=False):
    responses = []
    def request(method, path, **kwargs):
        response = client.request(method, path, **kwargs)
        responses.append(response.json())
        assert response.status_code < 300, response.text
        return response.json()
    def work():
        sid, root, kind, snapshot = offline.pop(0)
        if kind == 'list':
            worker.run_list(sid, collection=root)
        else:
            worker.run_detail(sid, snapshot, collection=root, backoff_s=0)
    category = request('POST', '/context/category-suggest', json={'bk': CTX['bk'], 'oneLiner': CTX['oneLiner']})
    sid = request('POST', '/context', json={**CTX, 'productCategory': category})['sid']
    for n in range(1, 5):
        if rounds.locked(n):
            continue
        request('POST', f'/keywords/{sid}/rounds/{n}')
        state = request('GET', f'/keywords/{sid}/rounds/{n}')
        assert state['status'] == 'done' and len(state['keywords']) == MIN_COUNT[n]
        assert state['below_min'] is None
        request('POST', f'/keywords/{sid}/rounds/{n}/commit', json={
            'gen': state['gen'], 'decisions': [{'id': k['id'], 'status': 'approved'} for k in state['keywords']]})
    request('PUT', f'/crawl/{sid}/config', json={
        'channels': ['fixture'], **({} if default_config else {'dateFrom': None, 'dateTo': None}),
        'perChannel': {'fixture': {'concurrency': 4, 'min_interval_s': 0}}})
    request('POST', f'/crawl/{sid}/list')
    work()
    status = request('GET', f'/crawl/{sid}/status')
    assert status['gate'] and status['status'] == 'done'
    request('PUT', f'/crawl/{sid}/gate', json={'exclusions': []})
    request('POST', f'/crawl/{sid}/detail', json={'snapshot_id': status['snapshot_id']})
    work()
    status = request('GET', f'/crawl/{sid}/status')
    assert status['report']['totals']['doc_count'] == 200
    request('PUT', f'/prep/{sid}/config', json={'embedder': 'fake'})
    request('POST', f'/prep/{sid}/run')
    deadline = time.monotonic() + 30
    while True:
        prep_status = request('GET', f'/prep/{sid}/status')
        if prep_status['status'] in {'done', 'failed', 'interrupted'} or time.monotonic() > deadline:
            break
        time.sleep(.05)
    assert prep_status['status'] == 'done', prep_status
    ref = store.load_session(sid)['prep']['derivedRef']
    docs = load_data(f"derived/{sid}/{ref['collectionId']}/{ref['prepKey']}/docs/")
    assert len(docs) == 200
    assert all(d['desc'] == d['body'] + '\n' and d['cafe'] == '개발용 샘플' and d['link'] == d['url'] for d in docs)
    request('GET', f'/context/{sid}')
    request('GET', '/integrations')
    request('GET', '/sessions')
    request('GET', f'/session/{sid}')
    request('GET', f'/sessions/{sid}/versions')
    return sid, docs, responses


def test_end_to_end_0_to_preprocess(client, offline):
    full_flow(client, offline)


def test_no_api_keys_full_run(client, offline):
    _, _, responses = full_flow(client, offline)
    response = client.get('/integrations')
    assert response.status_code == 200
    responses.append(response.json())
    assert response.json() == [entry.model_dump() for entry in integration_status()]
    assert [entry['name'] for entry in response.json()] == ['openai', 'claude']
    assert all(not entry['connected'] for entry in response.json())


def test_integrations_never_exposes_configured_secrets(client, offline, monkeypatch):
    sentinels = [f'SENTINEL_{name.upper()}_9f3a' for name in KEY_FIELDS]
    for name, sentinel in zip(KEY_FIELDS, sentinels):
        monkeypatch.setattr(settings, name, sentinel)
    external_requests = {'shopping': [], 'searchad': []}

    def record_request(service, request):
        external_requests[service].append(request)
        assert all(sentinel not in str(request.url) for sentinel in sentinels)
        assert all(sentinel not in part
                   for key, value in request.url.params.multi_items()
                   for part in (key, value) for sentinel in sentinels)

    def shopping_handler(request):
        record_request('shopping', request)
        assert request.url.host == 'openapi.naver.com'
        assert request.url.path == '/v1/search/shop.json'
        assert request.headers['X-Naver-Client-Id'] == settings.naver_client_id
        assert request.headers['X-Naver-Client-Secret'] == settings.naver_client_secret
        return httpx.Response(200, json={'items': [
            {'title': '샘플 에어컨', 'category1': '디지털/가전',
             'category2': '계절가전', 'category3': '에어컨'}]})

    def searchad_handler(request):
        record_request('searchad', request)
        assert request.url.host == 'api.searchad.naver.com'
        assert request.url.path == '/keywordstool'
        assert request.headers['X-API-KEY'] == settings.searchad_api_key
        assert request.headers['X-Customer'] == settings.searchad_customer_id
        return httpx.Response(200, json={'keywordList': [
            {'relKeyword': kw, 'monthlyPcQcCnt': 20, 'monthlyMobileQcCnt': 30}
            for kw in request.url.params['hintKeywords'].split(',')]})

    monkeypatch.setattr(naver_shopping, 'client_factory', lambda: httpx.Client(
        transport=httpx.MockTransport(shopping_handler)))
    monkeypatch.setattr(naver_searchad, 'client_factory', lambda: httpx.Client(
        transport=httpx.MockTransport(searchad_handler)))
    from app.routers import integrations
    calls = []
    def status():
        calls.append(True)
        return integration_status()
    monkeypatch.setattr(integrations, 'integration_status', status)
    _, _, responses = full_flow(client, offline)
    assert all(external_requests.values()), 'Both configured HTTP clients must be exercised'
    assert responses[0]['source'] == 'shopping'
    round_states = [body for body in responses if 'keywords' in body and body.get('status') == 'done']
    assert [state['round'] for state in round_states] == [1, 3, 4]
    assert all(kw['volume']['source'] == 'searchad' and kw['volume']['monthly'] == 50
               for state in round_states for kw in state['keywords'])
    assert all(sentinel not in json.dumps(responses) for sentinel in sentinels)
    response = client.get('/integrations')
    assert calls == [True, True]
    assert response.json() == [entry.model_dump() for entry in integration_status()]
    assert [entry['name'] for entry in response.json()] == ['openai', 'claude']
    assert all(getattr(settings, name) not in response.text for name in KEY_FIELDS)


def test_downstream_export_preserves_prepared_fields(client, offline, data_dir):
    from app.label import questions, rule
    from app.label.schema import Tags
    from app.label.store import LabelStore
    from app.routers.prep import _root
    from app.vectors.store import VectorStore

    sid, docs, _ = full_flow(client, offline)
    # Seed stage-three artifacts and final labels, then use the real stage-five export.
    cid = store.load_session(sid)['collectionId']
    prep_key = 'p_123456789abc'
    root = _root(sid, cid, prep_key)
    save_jsonl(f'derived/{sid}/{cid}/{prep_key}/docs/part-00001.jsonl', docs)
    vectors = np.random.default_rng(42).normal(size=(len(docs), settings.embed_dim))
    VectorStore(root).write_shard([d['doc_id'] for d in docs], vectors, [False] * len(docs))
    store.update_session(sid, {'prep': {'status': 'done', 'derivedRef': {
        'collectionId': cid, 'prepKey': prep_key}}})
    labels = LabelStore(store.session_dir(sid))
    tags = Tags(anchor=True, situation=True, sem={k: int(k == 'sense') for k in rule.SEM})
    with labels._db() as db:
        db.executemany('INSERT INTO final VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', [
            (d['doc_id'], 'core', 1., 'agreed', 'accepted', tags.model_dump_json(),
             None, None, rule.RULE_VERSION, questions.QVER, '{}', '[]', 0) for d in docs])
    response = client.post(f'/train/{sid}/export', json={'withoutModel': True})
    assert response.status_code == 200, response.text
    assert response.json()['total'] == response.json()['relevant'] == 200
    assert response.json()['stage5']['model'] is None
    assert store.load_session(sid)['training']['exportRef'] == response.json()['exportRef']

    rows = [json.loads(line) for line in (data_dir / response.json()['exportRef']).read_text().splitlines()]
    exported = {d['doc_id']: d for d in rows}
    assert set(exported) == {d['doc_id'] for d in docs}
    assert all(exported[d['doc_id']][field] == d[field]
               for d in docs for field in ('desc', 'cafe', 'link'))


def test_missing_manifest_run_hides_path(client, data_dir):
    sid = client.post('/context', json=CTX).json()['sid']
    store.update_session(sid, {'collectionId': 'c2'})
    response = client.post(f'/prep/{sid}/run')
    assert response.status_code == 409
    assert response.json()['error']['message'] == '수집이 끝난 뒤에 전처리를 실행할 수 있습니다.'
    assert str(data_dir) not in response.text


def test_context_router_has_no_duplicate_integrations():
    from app.routers.context import router
    assert not any(route.path == '/integrations' for route in router.routes)


def test_default_crawl_config_reaches_preprocess(client, offline):
    # Independent of shared corpus fixtures edited by other work waves.
    import csv
    with Path(settings.fixture_corpus_path).open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['review'])
        writer.writerows([[f'냉방1단어0 에어컨 사용 경험을 기록합니다 {i}'] for i in range(200)])
    full_flow(client, offline, default_config=True)
