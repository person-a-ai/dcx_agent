"""Build the QA corpus: make_corpus.py (200 rows) + 2 refusal-marker rows + 1 row over 8000 chars.

Usage: backend/.venv/bin/python docs/development/decisions-labeler/qa/make_qa_corpus.py OUT.csv
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'backend'))
from tests.fixtures.make_corpus import write_corpus  # noqa: E402


def main():
    out = Path(sys.argv[1])
    write_corpus(out, 200)
    fixtures = ROOT / 'backend/tests/fixtures/llm'
    words = [item['kw'] for n in range(1, 5)
             for item in json.loads((fixtures / f'kw_round_{n}.json').read_text(encoding='utf-8'))['keywords']]
    rows = []
    for i, tag in ((300, 'A'), (301, 'B')):
        kws = ', '.join(words[(i * 3 + k) % len(words)] for k in range(5))
        rows.append(f'냉방1단어{i % 42} {kws} 에어컨 사용 후기 {i}: QA-REFUSE-MARK-{tag} 거절 표식 문서입니다. 리모컨 반응과 필터 교체 주기를 따로 적었습니다.')
    kws = ', '.join(words[k % len(words)] for k in range(5))
    padding = ' '.join(f'문단{k}: 거실 {k % 9 + 1}번 창가에서 {k * 3 % 37}분 동안 냉방을 돌리며 소음 {30 + k % 20}dB와 습도 {40 + k % 30}%를 기록했다.' for k in range(260))
    rows.append(f'냉방2단어7 {kws} 에어컨 사용 후기 302: 긴 본문 문서입니다. {padding}')
    with out.open('a', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['review'])
        for row in rows:
            writer.writerow({'review': row})
    print(json.dumps({'path': str(out), 'rows': 200 + len(rows), 'long_len': len(rows[-1])}, ensure_ascii=False))


if __name__ == '__main__':
    main()
