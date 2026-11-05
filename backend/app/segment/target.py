"""Target-persona mode: anchor documents to stage-0 persona cards.

Pure helpers plus LLM steps that take a ``run_task`` callable, so the pipeline
can route calls through its counted, cached registry. Documents are the
compact stage-six docs (title, body and first comment, 300 characters each).
"""
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import random
import re
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from app.config import settings
from app.llm.base import Attachment, LLMTask
from app.segment import l1, l2, params

TRIED = ('전문 관리·병원·약', '셀프 관리(운동·스트레칭)', '제품·기기', '식단·영양', '휴식·환경 바꾸기', '언급 없음')
RESULTS = ('효과 있음', '일시적', '효과 없음', '언급 없음')
AD = re.compile(r'(체험단|협찬|원고료|제공받|소정의|광고|구매링크|최저가|naver\.me)')
NEED = re.compile(r'(고민|힘들|힘드|어떻게|싶|걱정|못 |못하|못자|불편|까요|할까|추천|방법|포기|후회|망설|부담|스트레스|짜증|괴롭|해결|궁금|필요|아쉽|문제|실패|작심|귀찮|피곤|지쳐|지친|방전|어렵|어려|아프|아파|통증)')
SPLIT = re.compile(r'(?<=[.!?~ㅠㅜ])\s+|\n+|(?<=[다요죠네까])\s+(?=[가-힣A-Za-z0-9])')


class _Out(BaseModel):
    model_config = ConfigDict(extra='ignore', str_strip_whitespace=True)


class JudgeOut(_Out):
    match: Literal['yes', 'partial', 'no']


class NeedsOut(_Out):
    mine: bool
    cause: str = ''
    tried: Literal[TRIED] = '언급 없음'
    result: Literal[RESULTS] = '언급 없음'


class CauseGroup(_Out):
    label: str = Field(min_length=1)
    members: list[int]


class CausesOut(_Out):
    groups: list[CauseGroup]


class DiscoverOut(_Out):
    name: str = Field(min_length=1)
    who: str = ''
    pain: str = ''
    consumer_voice: bool = False


def cards(project_context):
    """Persona seeds that carry a filled card, numbered T1.. in input order."""
    seeds = ((project_context or {}).get('personaSeeds') or {}).get('items') or []
    result = []
    for seed in seeds:
        card = seed.get('card') or {}
        if any(card.get(k) for k in ('desire', 'context', 'pain', 'unmet', 'keywords', 'quotes')):
            result.append(dict(id=f'T{len(result) + 1}', name=seed['text'], card=card))
    return result


def card_text(persona):
    card = persona['card']
    parts = [f"이름: {persona['name']}"] + [f'{label}: {card[key]}' for key, label in (
        ('desire', 'Desire'), ('context', 'Context'), ('pain', 'Pain Point'), ('unmet', 'Unmet Needs')) if card.get(key)]
    if card.get('keywords'):
        parts.append('키워드: ' + ', '.join(card['keywords']))
    if card.get('quotes'):
        parts.append('대표 원문: ' + ' / '.join(card['quotes']))
    return '\n'.join(parts)


def anchor_texts(persona):
    """The card as a whole plus its situation-bearing slices; quotes stand alone."""
    card = persona['card']
    texts = [card_text(persona).replace('\n', '. ')]
    for keys in (('desire', 'context', 'pain'), ('pain', 'unmet')):
        joined = '. '.join(card[k] for k in keys if card.get(k))
        if joined:
            texts.append(joined)
    if card.get('keywords'):
        texts.append(', '.join(card['keywords']))
    texts.extend(card.get('quotes') or [])
    return list(dict.fromkeys(texts))


def _unit(matrix):
    matrix = np.asarray(matrix, dtype=np.float32)
    return matrix / np.maximum(np.linalg.norm(matrix, axis=1, keepdims=True), 1e-9)


def score(vectors, personas, embed, chunk=50_000):
    """Return [n, P] maximum cosine between each document and each persona's anchors."""
    texts, owner = [], []
    for j, persona in enumerate(personas):
        for text in anchor_texts(persona):
            texts.append(text)
            owner.append(j)
    anchors = _unit(embed(texts))
    owner = np.asarray(owner)
    scores = np.empty((len(vectors), len(personas)), dtype=np.float32)
    for start in range(0, len(vectors), chunk):
        sims = _unit(vectors[start:start + chunk]) @ anchors.T
        for j in range(len(personas)):
            scores[start:start + len(sims), j] = sims[:, owner == j].max(axis=1)
    return scores


def doc_text(doc):
    return '\n'.join(filter(None, [doc.get('title') or '', doc.get('body') or '',
                                   *((c.get('text') or '') for c in doc.get('comments') or [])]))


def _task(sid, name, instructions, attachments, model, max_tokens=600):
    prompt = (Path(__file__).with_name('prompts') / f'{name}.v1.md').read_text(encoding='utf-8')
    return LLMTask(task=f'segment.{name}', sid=sid, instructions=prompt + ('\n\n' + instructions if instructions else ''),
                   attachments=attachments, output_schema=model, max_tokens=max_tokens)


def _run(run_task, task):
    try:
        result = run_task(task)
        if result.ok and isinstance(result.data, task.output_schema):
            return result.data
    except Exception:
        pass  # One failed call only drops its sample.
    return None


def _map(fn, items):
    # Hundreds of short judge calls per persona: run wider than the drafts pool.
    with ThreadPoolExecutor(max_workers=max(1, settings.segment_concurrency, params.TARGET_CONCURRENCY)) as pool:
        return list(pool.map(fn, items))


def calibrate(sid, scores, ids, docs, personas, run_task, rng=None, fetch=None):
    """Per-persona threshold from LLM-judged samples in fixed score bands.

    The threshold is the lowest band from which every higher judged band keeps
    mean precision (yes=1, partial=.5) at or above TARGET_PASS; None when the
    top band already fails. A band the search reaches whose precision lies within
    TARGET_BORDER of TARGET_PASS is judged again on up to TARGET_RECHECK documents
    before it decides anything, so twenty samples cannot flip the threshold alone.
    Returns {persona_id: {threshold, bands}}.
    `fetch(doc_ids) -> {doc_id: text}` supplies longer originals for the sampled
    documents; anything it misses falls back to the stored preview.
    """
    rng = rng or random.Random(params.SEED)
    best, top = scores.argmax(1), scores.max(1)
    edges = list(params.TARGET_BANDS) + [1.01]
    pools = {(j, b): np.flatnonzero((best == j) & (top >= edges[b]) & (top < edges[b + 1])).tolist()
             for j in range(len(personas)) for b in range(len(edges) - 1)}
    picked = {key: rng.sample(rows, min(params.TARGET_PER_BAND, len(rows))) for key, rows in pools.items()}
    votes = {key: [] for key in pools}

    def judge(job):
        j, _, row, text = job
        out = _run(run_task, _task(sid, 'target_judge', '', [
            Attachment(title='페르소나', body=card_text(personas[j])),
            Attachment(title='원문', body=text or doc_text(docs[ids[row]]))], JudgeOut, 200))
        return None if out is None else {'yes': 1., 'partial': .5, 'no': 0.}[out.match]

    pending = [(j, b, row) for (j, b), rows in picked.items() for row in rows]
    while pending:
        full = fetch({ids[row] for _, _, row in pending}) if fetch else {}
        for (j, b, _), value in zip(pending, _map(judge, [(j, b, row, full.get(ids[row])) for j, b, row in pending])):
            if value is not None:
                votes[(j, b)].append(value)
        pending = []
        for j in range(len(personas)):
            for b in _threshold(_bands(j, edges, pools, votes))[1]:
                key = (j, b)
                if len(picked[key]) >= min(params.TARGET_RECHECK, len(pools[key])):
                    continue
                rest = sorted(set(pools[key]) - set(picked[key]))
                extra = rng.sample(rest, min(params.TARGET_RECHECK - len(picked[key]), len(rest)))
                picked[key] += extra
                pending += [(j, b, row) for row in extra]
    result = {}
    for j, persona in enumerate(personas):
        bands = _bands(j, edges, pools, votes)
        result[persona['id']] = dict(threshold=_threshold(bands)[0], bands=bands)
    return result


def _bands(j, edges, pools, votes):
    bands = []
    for b in range(len(edges) - 1):
        got = votes[(j, b)]
        bands.append(dict(start=edges[b], docs=len(pools[(j, b)]), judged=len(got),
                          precision=round(sum(got) / len(got), 3) if got else None,
                          yes=sum(1 for v in got if v == 1.)))
    return bands


def _threshold(bands):
    """(threshold, indices of borderline bands the search reached) from the top band down."""
    threshold, border = None, []
    for b in reversed(range(len(bands))):
        band = bands[b]
        if band['precision'] is None:
            if band['docs']:
                break
            continue
        if band['judged'] < params.TARGET_MIN_JUDGED:
            continue
        if params.TARGET_PASS - params.TARGET_BORDER <= band['precision'] < params.TARGET_PASS + params.TARGET_BORDER:
            border.append(b)
        if band['precision'] < params.TARGET_PASS:
            break
        threshold = band['start']
    return threshold, border


def near_duplicates(vectors, cos=params.VIRAL_COS, neighbours=params.VIRAL_NEIGHBOURS, chunk=1000):
    """Mask documents with more than ``neighbours`` near-identical documents in the pool."""
    unit = _unit(vectors)
    counts = np.zeros(len(unit), dtype=int)
    for start in range(0, len(unit), chunk):
        counts[start:start + chunk] = ((unit[start:start + chunk] @ unit.T) >= cos).sum(1) - 1
    return counts >= neighbours


def is_ad(doc):
    return bool(AD.search(doc_text(doc)))


def assign(scores, thresholds, personas, excluded):
    """Index of the assigned persona per document, or -1 (other)."""
    best, top = scores.argmax(1), scores.max(1)
    result = np.full(len(scores), -1)
    for j, persona in enumerate(personas):
        threshold = thresholds[persona['id']]['threshold']
        if threshold is not None:
            result[(best == j) & (top >= threshold) & ~excluded] = j
    return result


def need_sentences(text, limit=3):
    out, seen = [], set()
    for sentence in SPLIT.split(text or ''):
        sentence = ' '.join(sentence.split())
        if 12 <= len(sentence) <= 220 and NEED.search(sentence) and sentence[:20] not in seen:
            seen.add(sentence[:20])
            out.append(sentence)
        if len(out) == limit:
            break
    return out


def quotes(doc_ids, docs, limit=params.TARGET_QUOTES):
    """First documents (caller's order) with need sentences, skipping ads and repeated titles."""
    result, titles = [], set()
    for doc_id in doc_ids:
        doc = docs[doc_id]
        title = (doc.get('title') or '').strip()
        if is_ad(doc) or (title and title[:15] in titles):
            continue
        sentences = need_sentences('\n'.join(filter(None, [doc.get('body') or '', *((c.get('text') or '') for c in doc.get('comments') or [])])))
        if sentences:
            titles.add(title[:15])
            result.append(dict(docId=doc_id, title=title[:60], source=doc.get('source', ''), sentences=sentences))
        if len(result) == limit:
            break
    return result


def needs(sid, persona, doc_ids, docs, run_task, rng=None):
    """Classify a sample: first-person need, cause, tried solution and its result."""
    rng = rng or random.Random(params.SEED)
    sample = rng.sample(list(doc_ids), min(params.NEEDS_SAMPLE, len(doc_ids)))

    def one(doc_id):
        return _run(run_task, _task(sid, 'target_needs', '', [
            Attachment(title='페르소나', body=card_text(persona)),
            Attachment(title='원문', body=doc_text(docs[doc_id]))], NeedsOut, 300))

    outs = _map(one, sample)
    mine = [(doc_id, out) for doc_id, out in zip(sample, outs) if out is not None and out.mine]
    judged = sum(out is not None for out in outs)
    causes = [out.cause for _, out in mine if out.cause]
    groups = group_causes(sid, persona, causes, run_task) if causes else []
    tried = defaultdict(Counter)
    for _, out in mine:
        if out.tried != '언급 없음':
            tried[out.tried][out.result] += 1
    examples = quotes([doc_id for doc_id, _ in mine], docs, limit=8)
    detail = {doc_id: out for doc_id, out in mine}
    for example in examples:
        out = detail[example['docId']]
        example.update(cause=out.cause, tried=out.tried, result=out.result)
    return dict(sampled=len(sample), judged=judged, mine=len(mine),
                share=round(len(mine) / judged, 3) if judged else None,
                causes=groups, tried=[dict(tried=k, total=sum(v.values()), **{r: v.get(r, 0) for r in RESULTS[:3]})
                                      for k, v in sorted(tried.items(), key=lambda kv: -sum(kv[1].values()))],
                examples=examples)


def group_causes(sid, persona, causes, run_task):
    """Fold free-text causes into at most CAUSE_GROUPS labelled counts; raw counts if the call fails."""
    numbered = '\n'.join(f'{i}. {cause}' for i, cause in enumerate(causes))
    out = _run(run_task, _task(sid, 'target_causes', f'최대 {params.CAUSE_GROUPS}개 범주로 묶으세요.', [
        Attachment(title='페르소나', body=card_text(persona)), Attachment(title='원인 목록', body=numbered)], CausesOut, 800))
    if out is None:
        return [dict(label=label, count=count) for label, count in Counter(causes).most_common(params.CAUSE_GROUPS)]
    seen, groups = set(), []
    for group in out.groups:
        members = {m for m in group.members if 0 <= m < len(causes) and m not in seen}
        seen |= members
        if members:
            groups.append(dict(label=group.label[:20], count=len(members)))
    if len(seen) < len(causes):
        groups.append(dict(label='기타', count=len(causes) - len(seen)))
    return sorted(groups, key=lambda g: -g['count'])


def discover(sid, other_ids, vectors, nouns, docs, bk, run_task, pulse=lambda: None):
    """Cluster 'other' documents (L1 k-means + L2) and summarise each group as a persona candidate."""
    if len(other_ids) < max(params.DISCOVER_K * 10, 30):
        return []
    k = params.DISCOVER_K
    labels, centers = l1.cluster(vectors, k, np.random.default_rng(params.SEED))
    centers = _unit(centers)
    groups = []
    for c in range(k):
        pulse()
        idx = np.flatnonzero(labels == c)
        if not len(idx):
            continue
        members = [other_ids[i] for i in idx]
        result = l2.personas(members, nouns, bk)
        by_sub = defaultdict(list)
        for i in idx:
            by_sub[result.assign[other_ids[i]]].append(i)
        # Closeness to the group's center, computed per group to avoid a float32 copy of every vector.
        closeness = dict(zip(idx.tolist(), (_unit(vectors[idx]) @ centers[c]).tolist()))
        for sub, rows in by_sub.items():
            rows = sorted(rows, key=lambda i: -closeness[i])
            groups.append(dict(id=f'N{c + 1}-{sub + 1}', docs=len(rows),
                               keywords=[w for w, _ in result.centrality[sub][:10]],
                               quotes=quotes([other_ids[i] for i in rows[:200]], docs, limit=params.DISCOVER_QUOTES)))

    def label(group):
        body = '\n'.join(f"- [{q['title']}] " + ' / '.join(q['sentences']) for q in group['quotes'])
        out = _run(run_task, _task(sid, 'target_discover', '', [
            Attachment(title='키워드', body=', '.join(group['keywords'])), Attachment(title='원문', body=body)], DiscoverOut, 400))
        return out.model_dump() if out else None

    for group, out in zip(groups, _map(label, groups)):
        group['label'] = out
    return sorted(groups, key=lambda g: -g['docs'])
