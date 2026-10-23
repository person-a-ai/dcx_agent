"""Korean caption cues → topic segments (TextTiling over window embeddings).

Deterministic: identical cues and embedder output yield identical boundaries.
Boundaries are whole seconds because they become document thread keys.
"""
from dataclasses import dataclass
import math
import re

import numpy as np

_MARKER = re.compile(r'\[[^\]\n]{1,12}\]')
_EPS = 1e-9


@dataclass(frozen=True)
class Cue:
    start_ms: int
    end_ms: int
    text: str


@dataclass(frozen=True)
class Segment:
    start_s: int
    end_s: int
    text: str


def parse_json3(data: dict) -> list[Cue]:
    cues = []
    for event in data.get('events') or []:
        segs = event.get('segs')
        if not segs or 'tStartMs' not in event:
            continue
        text = ' '.join(_MARKER.sub(' ', ''.join(s.get('utf8', '') for s in segs)).split())
        if text:
            start = int(event['tStartMs'])
            cues.append(Cue(start, start + int(event.get('dDurationMs') or 0), text))
    return sorted(cues, key=lambda c: (c.start_ms, c.end_ms))


def _text(cues):
    return ' '.join(c.text for c in cues)


def _cut(cues, bounds):
    out = []
    for a, b in zip(bounds, bounds[1:]):
        part = [c for c in cues if a * 1000 <= c.start_ms < b * 1000]
        if part:
            out.append(Segment(a, b, _text(part)))
    return out


def _fixed_bounds(a, b, fixed_s):
    return list(range(a + fixed_s, b, fixed_s))


def segment(cues, embedder, *, window_s=20, min_s=45, max_s=300, fixed_s=90):
    if not cues:
        return [], 'single'
    # The final bound is exclusive, including when the last cue has no duration.
    end_s = max(
        1,
        math.ceil(max(c.end_ms for c in cues) / 1000),
        max(c.start_ms for c in cues) // 1000 + 1,
    )
    groups = {}
    for c in cues:
        groups.setdefault(c.start_ms // (window_s * 1000), []).append(c)
    windows = [(k * window_s, groups[k]) for k in sorted(groups)]
    if end_s < min_s or len(windows) < 2:
        return [Segment(0, end_s, _text(cues))], 'single'
    if embedder is None:
        return _cut(cues, [0, *_fixed_bounds(0, end_s, fixed_s), end_s]), 'fixed'
    try:
        vectors = np.asarray(embedder.embed([_text(w) for _, w in windows]), dtype=np.float64)
    except Exception:
        return _cut(cues, [0, *_fixed_bounds(0, end_s, fixed_s), end_s]), 'fixed'
    norms = np.linalg.norm(vectors, axis=1) if vectors.ndim == 2 else np.zeros(0)
    if vectors.ndim != 2 or len(vectors) != len(windows) or not np.isfinite(vectors).all() or (norms < _EPS).any():
        return _cut(cues, [0, *_fixed_bounds(0, end_s, fixed_s), end_s]), 'fixed'
    unit = vectors / norms[:, None]
    sims = (unit[:-1] * unit[1:]).sum(axis=1)
    depth = np.asarray([(sims[:i + 1].max() - s) + (sims[i:].max() - s) for i, s in enumerate(sims)])
    gaps = [windows[i + 1][0] for i in range(len(sims))]
    cutoff = depth.mean() - depth.std() / 2
    bounds = [0, end_s]
    for i in sorted(range(len(sims)), key=lambda i: (-depth[i], gaps[i])):
        if not bounds[0] < gaps[i] < bounds[-1]:
            continue
        if depth[i] <= _EPS or depth[i] <= cutoff:
            continue
        trial = sorted({*bounds, gaps[i]})
        k = trial.index(gaps[i])
        if gaps[i] - trial[k - 1] >= min_s and trial[k + 1] - gaps[i] >= min_s:
            bounds = trial

    def split_long(a, b):
        if b - a <= max_s:
            return []
        inside = [(depth[i], gaps[i]) for i in range(len(sims))
                  if depth[i] > _EPS and a < gaps[i] < b
                  and a + min_s <= gaps[i] <= b - min_s]
        if not inside:
            return _fixed_bounds(a, b, fixed_s)
        t = sorted(inside, key=lambda d: (-d[0], d[1]))[0][1]
        return [*split_long(a, t), t, *split_long(t, b)]

    final = [0]
    for a, b in zip(bounds, bounds[1:]):
        final += [*split_long(a, b), b]
    return _cut(cues, final), 'embedding'
