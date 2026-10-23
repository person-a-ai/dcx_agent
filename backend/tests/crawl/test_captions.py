import numpy as np
import pytest

from app.crawl.captions import Cue, Segment, parse_json3, segment


class TopicEmbedder:
    def embed(self, texts, input_type='document'):
        return np.asarray([[1.0, 0.0] if '청소' in t else [0.0, 1.0] for t in texts], dtype=np.float32)


class Broken:
    def embed(self, texts, input_type='document'):
        raise RuntimeError('down')


class Zero:
    def embed(self, texts, input_type='document'):
        return np.zeros((len(texts), 2), dtype=np.float32)


def cues(spec):
    """spec: list of (topic_word, seconds) blocks, one 5-second cue per 5 seconds."""
    out, t = [], 0
    for word, seconds in spec:
        for _ in range(seconds // 5):
            out.append(Cue(t * 1000, (t + 5) * 1000, f'{word} 이야기 {t}'))
            t += 5
    return out


def test_parse_json3_strips_markers_and_empty_events():
    data = {'events': [
        {'tStartMs': 0, 'dDurationMs': 2000, 'segs': [{'utf8': '[음악]'}]},
        {'tStartMs': 2000, 'dDurationMs': 3000, 'segs': [{'utf8': '에어컨 '}, {'utf8': '청소 [박수] 했어요'}]},
        {'tStartMs': 6000},
    ]}
    assert parse_json3(data) == [Cue(2000, 5000, '에어컨 청소 했어요')]


def test_splits_at_topic_change():
    result, method = segment(cues([('청소', 120), ('전기세', 120)]), TopicEmbedder())
    assert method == 'embedding'
    assert [(s.start_s, s.end_s) for s in result] == [(0, 120), (120, 240)]
    assert '청소' in result[0].text and '전기세' not in result[0].text


def test_same_input_same_segments():
    data = cues([('청소', 100), ('전기세', 140), ('청소', 100)])
    assert segment(data, TopicEmbedder()) == segment(data, TopicEmbedder())


def test_boundaries_respect_minimum_length():
    result, _ = segment(cues([('청소', 120), ('전기세', 20), ('청소', 120)]), TopicEmbedder(), min_s=45)
    assert all(s.end_s - s.start_s >= 45 for s in result)


def test_long_single_topic_is_split_by_fixed_length():
    result, method = segment(cues([('청소', 700)]), TopicEmbedder(), max_s=300, fixed_s=90)
    assert method == 'embedding'
    assert [s.start_s for s in result] == [0, 90, 180, 270, 360, 450, 540, 630]
    assert result[-1].end_s == 700


@pytest.mark.parametrize('embedder', [None, Broken(), Zero()])
def test_fallback_to_fixed_segments(embedder):
    result, method = segment(cues([('청소', 120), ('전기세', 120)]), embedder, fixed_s=90)
    assert method == 'fixed'
    assert [(s.start_s, s.end_s) for s in result] == [(0, 90), (90, 180), (180, 240)]


def test_short_video_is_single_segment():
    result, method = segment(cues([('청소', 30)]), TopicEmbedder(), min_s=45)
    assert method == 'single'
    assert result == [Segment(0, 30, ' '.join(c.text for c in cues([('청소', 30)])))]


def test_empty_cues():
    assert segment([], TopicEmbedder()) == ([], 'single')


def test_parse_json3_sorts_cues_and_skips_events_without_start():
    data = {'events': [
        {'tStartMs': 4000, 'dDurationMs': 1000, 'segs': [{'utf8': '마지막'}]},
        {'segs': [{'utf8': '시각 없음'}]},
        {'tStartMs': 1000, 'dDurationMs': 2000, 'segs': [{'utf8': '긴 자막'}]},
        {'tStartMs': 1000, 'dDurationMs': 1000, 'segs': [{'utf8': '짧은 자막'}]},
        {'tStartMs': 3000, 'segs': [{'utf8': ' \n '}]},
    ]}
    assert parse_json3(data) == [
        Cue(1000, 2000, '짧은 자막'),
        Cue(1000, 3000, '긴 자막'),
        Cue(4000, 5000, '마지막'),
    ]


@pytest.mark.parametrize('data', [{}, {'events': None}, {'events': []}])
def test_parse_json3_without_events(data):
    assert parse_json3(data) == []


@pytest.mark.parametrize('vectors', [
    np.ones(12),
    np.ones((11, 2)),
    np.ones((12, 2, 1)),
    np.empty((12, 0)),
    np.full((12, 2), np.nan),
    np.full((12, 2), np.inf),
    np.asarray([[0.0, 0.0]] + [[1.0, 0.0]] * 11),
], ids=['one-dimensional', 'wrong-row-count', 'three-dimensional',
        'no-dimensions', 'nan', 'infinity', 'one-zero-row'])
def test_invalid_embeddings_fall_back_to_fixed_segments(vectors):
    class InvalidEmbedder:
        def embed(self, texts):
            return vectors

    result, method = segment(cues([('청소', 240)]), InvalidEmbedder())
    assert method == 'fixed'
    assert [(s.start_s, s.end_s) for s in result] == [(0, 90), (90, 180), (180, 240)]


def test_one_caption_window_is_single_even_for_long_cue():
    assert segment([Cue(1500, 60100, '긴 자막')], Broken()) == (
        [Segment(0, 61, '긴 자막')], 'single'
    )


def test_fixed_boundaries_keep_fractional_cues_once_and_round_end_up():
    result, method = segment([
        Cue(500, 1500, '시작'),
        Cue(89900, 90900, '경계 전'),
        Cue(90000, 91000, '경계'),
        Cue(180100, 181100, '마지막'),
    ], None)
    assert method == 'fixed'
    assert result == [
        Segment(0, 90, '시작 경계 전'),
        Segment(90, 180, '경계'),
        Segment(180, 182, '마지막'),
    ]
    assert all(isinstance(s.start_s, int) and isinstance(s.end_s, int) for s in result)


@pytest.mark.parametrize('duration_fields', [
    {}, {'dDurationMs': None}, {'dDurationMs': 0},
], ids=['missing', 'null', 'zero'])
@pytest.mark.parametrize('embedder, expected_method', [
    (None, 'fixed'), (TopicEmbedder(), 'embedding'),
], ids=['fixed', 'embedding'])
def test_final_whole_second_cue_without_duration_is_retained(duration_fields, embedder, expected_method):
    data = parse_json3({'events': [
        {'tStartMs': 0, 'dDurationMs': 1000, 'segs': [{'utf8': 'first'}]},
        {'tStartMs': 180000, 'segs': [{'utf8': 'last'}], **duration_fields},
    ]})
    assert data[-1] == Cue(180000, 180000, 'last')

    result, method = segment(data, embedder)

    assert method == expected_method
    assert [word for s in result for word in s.text.split()] == [c.text for c in data]
    assert result[-1].end_s == 181
    assert all(isinstance(s.start_s, int) and isinstance(s.end_s, int) for s in result)


@pytest.mark.parametrize('duration_fields', [
    {}, {'dDurationMs': None}, {'dDurationMs': 0},
], ids=['missing', 'null', 'zero'])
def test_topic_change_at_final_zero_duration_cue_keeps_all_cues(duration_fields):
    data = parse_json3({'events': [
        {'tStartMs': 0, 'dDurationMs': 1000, 'segs': [{'utf8': '청소-first'}]},
        {'tStartMs': 60000, 'dDurationMs': 1000, 'segs': [{'utf8': '청소-middle'}]},
        {'tStartMs': 180000, 'segs': [{'utf8': '전기세-last'}], **duration_fields},
    ]})

    result, method = segment(data, TopicEmbedder())

    assert method == 'embedding'
    assert [word for s in result for word in s.text.split()] == [c.text for c in data]
    assert [(s.start_s, s.end_s) for s in result] == [(0, 181)]
