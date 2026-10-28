"""Offline bulk preview API contracts."""
import json
import socket
from threading import Barrier, BrokenBarrierError

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.context import store
from app.keywords import rounds
from app.llm import registry
from app.llm.base import failure
from app.llm.fake import FakeBackend
from app.main import app


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, 'local_data_dir', str(tmp_path))
    monkeypatch.setattr(settings, 'searchad_api_key', '')
    monkeypatch.setattr(settings, 'autocomplete_backend', 'fake')
    def no_network(*args, **kwargs):
        raise AssertionError('Network access is forbidden')
    monkeypatch.setattr(socket.socket, 'connect', no_network)
    monkeypatch.setattr(rounds, 'execute', lambda fn: fn())
    store.update_session('test', {'schemaVersion': 2, 'keywords': [
        {'id': 'k1', 'kw': '저소음', 'axis': 'physical', 'sub': 'sense',
         'round': 1, 'origin': 'llm', 'status': 'approved'},
        {'id': 'k2', 'kw': '창문', 'axis': 'physical', 'sub': 'custom:설치환경',
         'round': 1, 'origin': 'llm', 'status': 'approved'}]})
    (store.session_dir('test') / 'project_context.md').write_text('원문 맥락\n- 리서치 질문: 냉방 경험은?')
    return tmp_path


@pytest.fixture
def llm(monkeypatch):
    class RecordingFake(FakeBackend):
        def __init__(self):
            super().__init__()
            self.calls = []
            self.answer = {'items': []}
            self.fail = False
            self.barrier = None

        def run(self, task):
            self.calls.append(task)
            if self.barrier:
                try:
                    self.barrier.wait()
                except BrokenBarrierError:
                    return failure('backend', 'barrier broken')
            if self.fail:
                return failure('backend', 'down')
            return FakeBackend(responses={task.task: json.dumps(self.answer)}).run(task)

    fake = RecordingFake()
    monkeypatch.setattr(registry, 'get_backend', lambda task: fake)
    return fake


@pytest.fixture
def client(data_dir, llm):
    return TestClient(app)


def test_preview_marks_input_existing_and_in_list_duplicates(client, llm):
    rows = [{'kw': '층간소음', 'axis': 'physical', 'sub': 'sense'},
            {'kw': '저 소음'}, {'kw': '층간 소음'}]
    response = client.post('/keywords/test/bulk/preview', json={'rows': rows})
    assert response.status_code == 200, response.text
    body = response.json()
    assert [r['status'] for r in body['rows']] == ['new', 'existing', 'in_list_duplicate']
    assert body['rows'][0]['source'] == 'input'
    assert body['rows'][1]['duplicateOf']['id'] == 'k1'
    assert body['rows'][2]['firstRow'] == 0
    assert body['rows'][1]['kw'] == '저소음'
    assert all(body['rows'][i]['source'] is None for i in (1, 2))
    assert all(body['rows'][i]['axis'] is None and body['rows'][i]['sub'] is None for i in (1, 2))
    assert llm.calls == []                       # 분류 없는 새 행이 없으면 LLM 호출 안 함

def test_preview_classifies_only_unclassified_rows(client, llm):
    llm.answer = {'items': [{'index': 0, 'axis': 'psychological', 'sub': 'emotion'}]}
    body = client.post('/keywords/test/bulk/preview', json={'rows': [
        {'kw': '불안감'}, {'kw': '퇴근후', 'axis': 'physical', 'sub': 'time'}]}).json()
    assert body['rows'][0].items() >= {'axis': 'psychological', 'sub': 'emotion', 'source': 'llm', 'status': 'new'}.items()
    assert len(llm.calls) == 1 and '불안감' in llm.calls[0].instructions and '퇴근후' not in llm.calls[0].instructions
    assert 'custom:설치환경' in llm.calls[0].instructions
    assert llm.calls[0].attachments[0].title == 'project_context.md'
    assert '원문 맥락' in llm.calls[0].attachments[0].body
    assert llm.calls[0].max_tokens == 4000

def test_preview_rejects_invalid_llm_answers(client, llm):
    llm.answer = {'items': [{'index': 0, 'axis': 'physical', 'sub': 'emotion'},
                            {'index': 1, 'axis': 'physical', 'sub': 'custom:없는그룹'},
                            {'index': 9, 'axis': 'physical', 'sub': 'sense'},
                            {'index': 2, 'axis': 'physical', 'sub': 'sense'},
                            {'index': 2, 'axis': 'behavioral', 'sub': 'coping'}]}
    body = client.post('/keywords/test/bulk/preview', json={'rows': [{'kw': 'a1'}, {'kw': 'a2'}, {'kw': 'a3'}, {'kw': 'a4'}]}).json()
    assert [(r['status'], r['source']) for r in body['rows']] == [('needs_class', 'llm_failed')] * 2 + [('new', 'llm'), ('needs_class', 'llm_failed')]
    assert body['rows'][2]['sub'] == 'sense'     # 같은 index 중복은 첫 답 채택

def test_preview_llm_failure_keeps_rows(client, llm):
    llm.fail = True
    body = client.post('/keywords/test/bulk/preview', json={'rows': [{'kw': '불안감'}]}).json()
    assert body['rows'][0]['status'] == 'needs_class' and body['classifyError']['kind']

def test_preview_chunks_by_100_and_saves_nothing(client, llm):
    before = (store.session_dir('test') / 'session.json').read_bytes()
    client.post('/keywords/test/bulk/preview', json={'rows': [{'kw': f'단어{i}'} for i in range(250)]})
    assert len(llm.calls) == 3                       # 100 + 100 + 50
    assert sorted(len(json.loads(task.instructions.split('\n키워드: ')[1])) for task in llm.calls) == [50, 100, 100]
    assert (store.session_dir('test') / 'session.json').read_bytes() == before

def test_preview_chunks_run_concurrently_and_keep_row_order(client, llm):
    # 가짜 백엔드 run()이 Barrier(3, timeout=5)에서 기다린다 → 세 묶음이 동시에 돌 때만 통과(차례 실행이면 BrokenBarrierError → 분류 실패)
    llm.barrier = Barrier(3, timeout=5)
    llm.answer = {'items': [{'index': 0, 'axis': 'physical', 'sub': 'time'}]}
    body = client.post('/keywords/test/bulk/preview', json={'rows': [{'kw': f'단어{i}'} for i in range(250)]}).json()
    assert [r['row'] for r in body['rows']] == list(range(250))
    assert [r['row'] for r in body['rows'] if r['source'] == 'llm'] == [0, 100, 200]

def test_preview_validation_and_readonly(client):
    assert client.post('/keywords/test/bulk/preview', json={'rows': []}).status_code == 422
    assert client.post('/keywords/test/bulk/preview', json={'rows': [{'kw': 'x'}] * 501}).status_code == 422
    assert client.post('/keywords/test/bulk/preview', json={'rows': [{'kw': 'x' * 101}]}).status_code == 422
    assert client.post('/keywords/test/bulk/preview', json={'rows': [{'kw': '소음'}, {'kw': '   '}]}).status_code == 422
    # 읽기 전용 버전: test_rounds_api.py의 create_version('test','v1','stage1','') 패턴
    from app.context.versions import create_version, version_dir
    create_version('test', 'v1', 'stage1', '')
    before = (version_dir('test', 'v1') / 'session.json').read_bytes()
    assert client.post('/keywords/test/bulk/preview?version=v1', json={'rows': [{'kw': '소음'}]}).status_code == 409
    assert (version_dir('test', 'v1') / 'session.json').read_bytes() == before
