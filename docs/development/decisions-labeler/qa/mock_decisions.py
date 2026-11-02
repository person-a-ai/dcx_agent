"""Local fake OpenAI Decisions server for browser QA (no real network).

Usage:
  MOCK_PORT=8399 MOCK_MODE=normal MOCK_LOG=/path/requests.jsonl \
  MOCK_KEY_NAMES=qa-key-1,qa-key-2 python3 mock_decisions.py

Modes (MOCK_MODE):
  normal  deterministic answers for every question, in request order
  refuse  like normal, but when MOCK_REFUSE_MARKER is in the request input,
          the reason_code answer has type "refusal"
  401     every request gets 401 with a body that must never be shown
  quota   every request gets 429 {"error":{"code":"insufficient_quota"}}

The log records header NAMES, which key slot (1/2/unknown) was used, question
names, input length (JSON-serialized, ensure_ascii=False) and a short input
hash. Key values and Authorization values are never written.
"""
import hashlib
import json
import os
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get('MOCK_PORT', '8399'))
MODE = os.environ.get('MOCK_MODE', 'normal')
LOG = os.environ.get('MOCK_LOG', 'mock_requests.jsonl')
MODEL = os.environ.get('MOCK_MODEL', 'mock-decisions-1')
MARKER = os.environ.get('MOCK_REFUSE_MARKER', 'QA-REFUSE-MARK')
DELAY = float(os.environ.get('MOCK_DELAY_S', '0'))
KEY_NAMES = [k.strip() for k in os.environ.get('MOCK_KEY_NAMES', '').split(',') if k.strip()]
SECRET_BODY = 'MOCK-SECRET-BODY-should-never-appear'
_lock = threading.Lock()


def _unit(seed: str) -> float:
    return int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def answer(question: dict, text: str) -> dict:
    name = question['name']
    if question['type'] == 'predicate':
        return {'name': name, 'type': 'predicate', 'probability': round(_unit(text + name), 4)}
    raw = [(c['value'], 0.05 + _unit(text + name + c['value'])) for c in question['choices']]
    total = sum(p for _, p in raw)
    return {'name': name, 'type': 'choice',
            'probabilities': [{'value': v, 'probability': round(p / total, 4)} for v, p in raw]}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._send(200, {'ok': True, 'mode': MODE})

    def do_POST(self):
        length = int(self.headers.get('Content-Length', '0'))
        raw = self.rfile.read(length)
        try:
            body = json.loads(raw)
        except ValueError:
            body = {}
        auth = self.headers.get('Authorization', '')
        token = auth[7:] if auth.startswith('Bearer ') else None
        slot = (KEY_NAMES.index(token) + 1) if token in KEY_NAMES else ('none' if token is None else 'unknown')
        text = body.get('input') if isinstance(body.get('input'), str) else ''
        questions = body.get('questions') or []
        doc = re.search(r'후기 (\d+)', text)
        entry = {
            'ts': time.time(), 'path': self.path, 'mode': MODE,
            'header_names': sorted(self.headers.keys()),
            'has_idempotency_key': any(h.lower() == 'idempotency-key' for h in self.headers.keys()),
            'key_slot': slot, 'model': body.get('model'),
            'question_names': [q.get('name') for q in questions],
            'question_types': [q.get('type') for q in questions],
            'input_len_json': len(json.dumps(text, ensure_ascii=False)),
            'input_sha': hashlib.sha256(text.encode()).hexdigest()[:12],
            'doc_tag': doc.group(1) if doc else None,
            'marker': MARKER in text,
        }
        if DELAY:
            time.sleep(DELAY)
        if self.path.rstrip('/') != '/v1/decisions':
            status, payload = 404, {'error': {'message': 'not found'}}
        elif MODE == '401':
            status, payload = 401, {'error': {'message': SECRET_BODY, 'code': 'invalid_api_key'}}
        elif MODE == 'quota':
            status, payload = 429, {'error': {'code': 'insufficient_quota', 'message': SECRET_BODY}}
        else:
            answers = [answer(q, text) for q in questions]
            if MODE == 'refuse' and MARKER in text:
                answers = [{'name': a['name'], 'type': 'refusal', 'refusal': 'mock refusal'}
                           if a['name'] == 'reason_code' else a for a in answers]
            status, payload = 200, {'id': 'dec_' + entry['input_sha'], 'model': MODEL, 'answers': answers}
        entry['status'] = status
        with _lock, open(LOG, 'a', encoding='utf-8') as stream:
            stream.write(json.dumps(entry, ensure_ascii=False) + '\n')
        self._send(status, payload)


if __name__ == '__main__':
    print(f'mock decisions on :{PORT} mode={MODE} log={LOG}', flush=True)
    ThreadingHTTPServer(('127.0.0.1', PORT), Handler).serve_forever()
