"""Synchronous Decisions API client that answers the Jev questions as a JevVote."""
import threading
import time

import httpx

from app.config import settings
from app.label.jev import JevError, _limiter_for, _probability, build_state
from app.label.questions import jev_questions
from app.label.schema import JevVote

MAX_RETRIES = 5
_BAD_MESSAGE = 'Decisions 요청 또는 응답을 확인해 주세요'


def _bad():
    return JevError('bad', _BAD_MESSAGE)


def to_decisions_questions(questions: dict) -> list[dict]:
    """Convert Jev wire questions to the ordered Decisions question list."""
    converted = []
    for name, question in questions.items():
        if question['type'] == 'noul':
            converted.append({
                'type': 'predicate', 'name': name,
                'instructions': question['instructions'] + '\n' + question['criteria'],
            })
        else:
            converted.append({
                'type': 'choice', 'name': name, 'instructions': question['instructions'],
                'choices': [{'value': key, 'description': text} for key, text in question['criteria'].items()],
            })
    return converted


def _parse_decision(payload, questions: list[dict], truncated: bool) -> JevVote:
    try:
        answers = payload['answers']
        if not isinstance(answers, list):
            raise _bad()
        # Refusal wins over any format problem elsewhere in the response.
        if any(isinstance(item, dict) and item.get('type') == 'refusal' for item in answers):
            raise JevError('refused', 'Decisions가 이 문서 판정을 거절했습니다')
        if len(answers) != len(questions):
            raise _bad()
        model = payload['model']
        if not isinstance(model, str) or not model:
            raise _bad()
        probs, choices = {}, {}
        for question, answer in zip(questions, answers):
            name = question['name']
            if answer['name'] != name or answer['type'] != question['type']:
                raise _bad()
            if question['type'] == 'predicate':
                probs[name] = _probability(answer['probability'])
                continue
            items = answer['probabilities']
            if not isinstance(items, list):
                raise _bad()
            values = {}
            for item in items:
                value = item['value']
                if not isinstance(value, str) or value in values:
                    raise _bad()
                values[value] = _probability(item['probability'])
            if set(values) != {choice['value'] for choice in question['choices']}:
                raise _bad()
            total = sum(values.values())
            if total <= 0:
                raise _bad()
            choices[name] = {key: value / total for key, value in values.items()}
        combined = choices['relate_outcome']
        probs['relate'] = combined['relate'] + combined['both']
        probs['outcome'] = combined['outcome'] + combined['both']
        return JevVote(probs=probs, reason_probs=choices['reason_code'], model=model, truncated=truncated)
    except JevError as error:
        if error.code == 'refused':
            raise
        raise _bad() from None
    except (KeyError, TypeError, ValueError, OverflowError):
        raise _bad() from None


def _insufficient_quota(response: httpx.Response) -> bool:
    try:
        return response.json()['error']['code'] == 'insufficient_quota'
    except (ValueError, KeyError, TypeError):
        return False


class DecisionsClient:
    def __init__(self, keys, model, transport=None):
        keys = list(keys or ())
        if not any(key.strip() for key in keys) and settings.openai_api_key:
            keys = [settings.openai_api_key]
        self._keys = tuple(dict.fromkeys(key.strip() for key in keys if key.strip()))
        self.model = model
        rate = settings.decisions_rate_per_min
        if not rate > 0:
            raise ValueError('decisions_rate_per_min must be positive')
        self._limiters = [_limiter_for(key, rate) for key in self._keys]
        self._url = settings.decisions_base_url.rstrip('/') + '/decisions'
        self._lock = threading.Lock()
        self._next_key = 0
        self._http = httpx.Client(transport=transport, timeout=60)

    def close(self):
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def judge(self, doc: dict, one_liner: str, *, idempotency_key: str | None = None) -> JevVote:
        # idempotency_key is accepted for interface parity; Decisions does not take it.
        if not self._keys:
            raise JevError('unconnected', 'Decisions 연결 키가 없습니다')
        state, truncated = build_state(doc, one_liner)
        questions = to_decisions_questions(jev_questions(one_liner))
        with self._lock:
            index = self._next_key
            self._next_key = (index + 1) % len(self._keys)
        headers = {'Authorization': f'Bearer {self._keys[index]}'}
        body = {'model': self.model, 'input': state, 'questions': questions}
        for attempt in range(MAX_RETRIES + 1):
            try:
                with self._limiters[index]:
                    response = self._http.post(self._url, headers=headers, json=body)
            except httpx.RequestError:
                raise JevError('bad', 'Decisions 요청을 완료하지 못했습니다', transient=True) from None
            status = response.status_code
            if status == 401:
                raise JevError('unconnected', 'Decisions 연결 키를 확인해 주세요')
            if status == 429 and _insufficient_quota(response):
                raise JevError('insufficient', 'Decisions 사용 한도가 부족합니다')
            if status == 429 or 500 <= status < 600:
                if attempt < MAX_RETRIES:
                    time.sleep(2 ** attempt)
                    continue
                raise JevError('bad', _BAD_MESSAGE, transient=True)
            if status != 200:
                raise _bad()
            try:
                payload = response.json()
            except ValueError:
                raise _bad() from None
            return _parse_decision(payload, questions, truncated)
        raise _bad()
