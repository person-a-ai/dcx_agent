"""Read-only bulk keyword preview and classification."""
import json
from concurrent.futures import ThreadPoolExecutor

from pydantic import BaseModel

from app.context import store
from app.keywords.normalize import norm_key
from app.keywords.rounds import _all_keywords
from app.keywords.taxonomy import AXES, is_valid
from app.llm import registry
from app.llm.base import Attachment, LLMTask

MAX_ROWS = 500
CLASSIFY_CHUNK = 100


class ClassifiedItem(BaseModel):
    index: int
    axis: str
    sub: str


class Classified(BaseModel):
    items: list[ClassifiedItem]


def preview(sid: str, rows: list[dict], version: str | None = None) -> dict:
    with store.locked(sid):
        data = store.assert_writable(sid, version)
        directory = store.session_dir(sid)
    words = [''.join(row['kw'].split()) for row in rows]
    if not words or len(words) > MAX_ROWS or any(not kw or len(kw) > 100 for kw in words):
        raise store.StoreError('키워드와 분류를 확인하세요', 422, 'validation')

    keywords = _all_keywords(data)
    existing = {norm_key(k.kw): k for k in keywords}
    allowed = [{'axis': axis, 'sub': sub} for axis, subs in AXES.items() for sub in subs]
    allowed_pairs = {(item['axis'], item['sub']) for item in allowed}
    for keyword in keywords:
        pair = (keyword.axis, keyword.sub)
        if keyword.sub.startswith('custom:') and pair not in allowed_pairs:
            allowed.append({'axis': keyword.axis, 'sub': keyword.sub})
            allowed_pairs.add(pair)

    output, pending, first_rows = [], [], {}
    for index, (row, kw) in enumerate(zip(rows, words)):
        axis, sub = row.get('axis'), row.get('sub')
        item = {'row': index, 'kw': kw, 'axis': axis, 'sub': sub, 'source': None}
        key = norm_key(kw)
        if key in existing:
            keyword = existing[key]
            item.update(status='existing', duplicateOf={
                'id': keyword.id, 'kw': keyword.kw, 'axis': keyword.axis, 'sub': keyword.sub})
        elif key in first_rows:
            item.update(status='in_list_duplicate', firstRow=first_rows[key])
        elif axis and sub and is_valid(axis, sub):
            item.update(status='new', source='input')
        else:
            item.update(status='needs_class', source='llm_failed')
            pending.append(item)
        first_rows.setdefault(key, index)
        output.append(item)

    response = {'rows': output}
    if not pending:
        return response
    context_md = (directory / 'project_context.md').read_text(encoding='utf-8')
    chunks = [pending[i:i + CLASSIFY_CHUNK] for i in range(0, len(pending), CLASSIFY_CHUNK)]

    def classify(chunk):
        instructions = (
            '다음 키워드마다 소비자 경험 분류(축/하위분류)를 하나씩 고르세요. 허용 목록 밖의 값은 쓰지 마세요. 각 항목은 index와 axis, sub를 답합니다.\n허용 목록: '
            + json.dumps(allowed, ensure_ascii=False) + '\n키워드: '
            + json.dumps([{'index': i, 'kw': item['kw']} for i, item in enumerate(chunk)], ensure_ascii=False))
        return registry.run_task(LLMTask(
            task='kw_bulk_classify', sid=sid, max_tokens=4000, instructions=instructions,
            attachments=[Attachment(title='project_context.md', body=context_md)], output_schema=Classified))

    with ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(classify, chunks))
    for chunk, result in zip(chunks, results):
        if not result.ok:
            response.setdefault('classifyError', {'kind': result.error.kind, 'message': result.error.message})
            continue
        seen = set()
        for answer in result.data.items:
            index = answer.index
            if not 0 <= index < len(chunk) or index in seen:
                continue
            seen.add(index)
            if (answer.axis, answer.sub) in allowed_pairs:
                chunk[index].update(axis=answer.axis, sub=answer.sub, status='new', source='llm')
    return response
