"""Read-only QA checks over the fake server log, the judge vote cache and the labels DB.

Usage: python3 analyze.py --log LOG.jsonl [--votes votes.sqlite] [--labels labels.sqlite]
Prints a JSON summary. Never writes to the product data.
"""
import argparse
import collections
import json
import re
import sqlite3

EXPECTED = ['anchor', 'sense', 'feel', 'think', 'act', 'situation', 'relate_outcome', 'reason_code']
PROB_KEYS = {'anchor', 'sense', 'feel', 'think', 'act', 'situation', 'relate', 'outcome'}


def ro(path):
    return sqlite3.connect(f'file:{path}?mode=ro', uri=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--log')
    p.add_argument('--votes')
    p.add_argument('--labels')
    a = p.parse_args()
    out = {}
    if a.log:
        rows = [json.loads(line) for line in open(a.log, encoding='utf-8') if line.strip()]
        out['requests'] = len(rows)
        out['paths'] = dict(collections.Counter(r['path'] for r in rows))
        out['status'] = dict(collections.Counter(r['status'] for r in rows))
        out['order_ok'] = sum(r['question_names'] == EXPECTED for r in rows)
        out['idempotency_key_present'] = sum(r['has_idempotency_key'] for r in rows)
        out['key_slots'] = dict(collections.Counter(str(r['key_slot']) for r in rows))
        slots = [r['key_slot'] for r in sorted(rows, key=lambda r: r['ts'])]
        out['key_alternates'] = all(slots[i] != slots[i + 1] for i in range(len(slots) - 1)) if len(slots) > 1 else None
        out['first_slots'] = slots[:8]
        out['header_names_sample'] = rows[0]['header_names'] if rows else None
        out['unique_inputs'] = len({r['input_sha'] for r in rows})
        per_input = collections.Counter(r['input_sha'] for r in rows)
        out['max_requests_per_input'] = max(per_input.values()) if per_input else 0
        out['marker_requests'] = [dict(doc_tag=r['doc_tag'], sha=r['input_sha'], status=r['status']) for r in rows if r['marker']]
        out['max_input_len_json'] = max((r['input_len_json'] for r in rows), default=0)
        out['doc302'] = [dict(input_len_json=r['input_len_json'], status=r['status']) for r in rows if r['doc_tag'] == '302']
        out['models_sent'] = dict(collections.Counter(r['model'] for r in rows))
    if a.votes:
        with ro(a.votes) as db:
            votes = db.execute('SELECT doc_id, status, payload_json, last_error, attempts FROM votes').fetchall()
        out['vote_status'] = dict(collections.Counter(v[1] for v in votes))
        done = [json.loads(v[2]) for v in votes if v[1] == 'done' and v[2]]
        out['done_with_8_probs'] = sum(set(d.get('probs', {})) == PROB_KEYS for d in done)
        out['done_with_reason_probs'] = sum(bool(d.get('reason_probs')) for d in done)
        out['done_models'] = dict(collections.Counter(d.get('model') for d in done))
        out['truncated_doc_ids'] = [v[0] for v in votes if v[1] == 'done' and v[2] and json.loads(v[2]).get('truncated')]
        out['bad'] = [dict(doc_id=v[0], last_error=v[3], attempts=v[4], payload=v[2]) for v in votes if v[1] == 'bad']
        out['sample_vote'] = done[0] if done else None
        if a.labels:
            with ro(a.labels) as db:
                docs = {r[0]: json.loads(r[1]) for r in db.execute('SELECT doc_id, payload FROM documents')}
            def tag(doc_id):
                m = re.search(r'후기 (\d+)', docs.get(doc_id, {}).get('body', ''))
                return m.group(1) if m else None
            out['truncated_doc_tags'] = [tag(d) for d in out['truncated_doc_ids']]
            out['bad_doc_tags'] = [tag(b['doc_id']) for b in out['bad']]
            out['bad_doc_markers'] = ['QA-REFUSE-MARK' in docs.get(b['doc_id'], {}).get('body', '') for b in out['bad']]
            long_ids = [d for d, doc in docs.items() if len(doc.get('body', '')) > 8000]
            out['long_body_docs'] = [dict(doc_id=d, tag=tag(d), body_len=len(docs[d]['body'])) for d in long_ids]
            out['documents'] = len(docs)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
