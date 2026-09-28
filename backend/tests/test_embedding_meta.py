"""T4 · known_insights 임베딩 + Pinecone 메타 확장.

계획: docs/development/dcx-step07-11/03-plan.md P0/T4
  RED 메타에 doc_id·cluster_id·persona_id·context_id·dist_centroid·band·
      author_hash 가 들어가고, filter 3키로 조회 시 다른 클러스터 문서가
      섞이지 않음
  RED known_insights 가 별도 네임스페이스에 저장되고
      max_sim_to_known 계산이 0~1 범위
  수용 기준 known_insights 가 비면 max_sim_to_known = 0 (감점 없음)
           — 이 경우 quality == relevance
"""
import math

import pytest

from app.services.embedding import (
    build_metadata, vector_id, context_filter, KNOWN_NAMESPACE,
    max_sim_to_known, quality_score,
)


def rec(**over):
    r = {"doc_id": "d_8223959b487da62b", "title": "에어팟 심박", "desc": "러닝 중",
         "kw": "심박", "cafe": "애플사용자모임", "author_hash": "a_35153ba5"}
    r.update(over)
    return r


# ── 메타데이터 ────────────────────────────────────────────────

def test_metadata_carries_every_field_09_needs():
    m = build_metadata(rec(cluster_id="CL0", persona_id="CL0-P1",
                           context_id="CL0-P1-C2", dist_centroid=0.41, band="Core"))
    for k in ("doc_id", "cluster_id", "persona_id", "context_id",
              "dist_centroid", "band", "author_hash"):
        assert k in m, f"{k} 없음"


def test_metadata_keeps_the_existing_five():
    m = build_metadata(rec())
    for k in ("title", "desc", "kw", "cafe", "cluster"):
        assert k in m


def test_metadata_has_no_none_pinecone_rejects_it():
    """Pinecone 메타는 None 을 받지 않는다 — 빈 문자열·숫자 기본값으로 내려야 한다."""
    m = build_metadata(rec(author_hash=None))
    assert all(v is not None for v in m.values())
    assert m["author_hash"] == ""


def test_unassigned_ids_are_empty_not_a_real_looking_value():
    """07·08 이 아직 안 돌았으면 클러스터가 없다. 실제 ID 처럼 보이는 값을
    넣으면 09 filter 가 미배정 문서를 같이 집어온다."""
    m = build_metadata(rec())
    assert m["cluster_id"] == ""
    assert m["persona_id"] == ""
    assert m["context_id"] == ""
    assert m["dist_centroid"] == -1.0
    assert m["band"] == ""


def test_metadata_does_not_carry_the_author_string():
    m = build_metadata(rec(meta={"author": "홍길동"}))
    assert "홍길동" not in repr(m)


# ── 벡터 ID — doc_id 를 쓴다 ────────────────────────────────────

def test_vector_id_is_the_doc_id():
    """예전에는 배치 순번(doc_0, doc_1)이라 다시 임베딩하면 같은 문서가
    다른 벡터가 됐고, 09 가 doc_id 로 벡터를 되찾을 수 없었다."""
    assert vector_id(rec(), 7) == "d_8223959b487da62b"


def test_vector_id_is_stable_across_reruns():
    assert vector_id(rec(), 0) == vector_id(rec(), 999)


def test_vector_id_falls_back_when_doc_id_missing():
    vid = vector_id(rec(doc_id=None), 7)
    assert vid and vid != "d_8223959b487da62b"


# ── filter 3키 ────────────────────────────────────────────────

def test_context_filter_uses_all_three_keys():
    f = context_filter("CL0", "CL0-P1", "CL0-P1-C2")
    assert f == {"cluster_id": {"$eq": "CL0"},
                 "persona_id": {"$eq": "CL0-P1"},
                 "context_id": {"$eq": "CL0-P1-C2"}}


def test_context_filter_omits_keys_not_given():
    assert context_filter("CL0", None, None) == {"cluster_id": {"$eq": "CL0"}}


def _matches(meta, flt):
    """Pinecone $eq filter 를 흉내낸다."""
    return all(meta.get(k) == c["$eq"] for k, c in flt.items())


def test_other_clusters_do_not_leak_through_the_filter():
    rows = [
        build_metadata(rec(doc_id="d_1", cluster_id="CL0", persona_id="CL0-P1", context_id="CL0-P1-C2")),
        build_metadata(rec(doc_id="d_2", cluster_id="CL0", persona_id="CL0-P1", context_id="CL0-P1-C3")),
        build_metadata(rec(doc_id="d_3", cluster_id="CL1", persona_id="CL1-P1", context_id="CL1-P1-C2")),
        build_metadata(rec(doc_id="d_4")),   # 미배정
    ]
    f = context_filter("CL0", "CL0-P1", "CL0-P1-C2")
    hit = [m["doc_id"] for m in rows if _matches(m, f)]
    assert hit == ["d_1"]


# ── known_insights — 별도 네임스페이스 ─────────────────────────

def test_known_insights_live_in_their_own_namespace():
    """본문과 같은 네임스페이스에 두면 근거 검색이 '아는 이야기' 자체를
    근거로 되돌려준다."""
    assert KNOWN_NAMESPACE
    assert KNOWN_NAMESPACE != ""


# ── max_sim_to_known ──────────────────────────────────────────

def test_max_sim_is_zero_when_nothing_is_known():
    """수용 기준: known_insights 가 비면 감점이 없다."""
    assert max_sim_to_known([1.0, 0.0], []) == 0.0


def test_max_sim_is_one_for_an_identical_sentence():
    assert max_sim_to_known([1.0, 0.0], [[1.0, 0.0]]) == pytest.approx(1.0)


def test_max_sim_takes_the_closest_not_the_average():
    v = [1.0, 0.0]
    known = [[0.0, 1.0], [1.0, 0.0]]     # 직교 하나 + 동일 하나
    assert max_sim_to_known(v, known) == pytest.approx(1.0)


@pytest.mark.parametrize("v,known", [
    ([1.0, 0.0], [[-1.0, 0.0]]),          # 정반대 → 코사인 -1
    ([1.0, 0.0], [[0.0, 1.0]]),           # 직교 → 0
    ([0.6, 0.8], [[0.8, 0.6]]),
])
def test_max_sim_stays_inside_zero_and_one(v, known):
    s = max_sim_to_known(v, known)
    assert 0.0 <= s <= 1.0, s


def test_max_sim_clamps_negative_similarity_to_zero():
    """정반대 방향이라고 해서 감점을 되돌려주면(음수) quality 가 부풀려진다."""
    assert max_sim_to_known([1.0, 0.0], [[-1.0, 0.0]]) == 0.0


def test_max_sim_ignores_zero_vectors():
    """임베딩 실패분은 0 벡터로 온다 — 코사인이 정의되지 않는다."""
    assert max_sim_to_known([1.0, 0.0], [[0.0, 0.0]]) == 0.0
    assert max_sim_to_known([0.0, 0.0], [[1.0, 0.0]]) == 0.0


# ── quality — 감점·가점 두 항 ──────────────────────────────────

def test_quality_equals_relevance_when_nothing_is_known():
    """수용 기준을 테스트가 직접 못박는다."""
    rel = 0.87
    assert quality_score(rel, max_sim=0.0, combo_rarity=0.0) == pytest.approx(rel)


def test_quality_drops_when_the_document_repeats_what_we_know():
    rel = 0.87
    assert quality_score(rel, max_sim=1.0, combo_rarity=0.0) < rel


def test_quality_rises_with_a_rare_combination():
    rel = 0.87
    assert quality_score(rel, max_sim=0.0, combo_rarity=1.0) > rel


def test_quality_follows_the_documented_formula():
    """quality = relevance × (1 − α·max_sim) × (1 + β·combo_rarity)"""
    from app.services.embedding import PENALTY_ALPHA, BONUS_BETA
    rel, s, c = 0.8, 0.5, 0.4
    expect = rel * (1 - PENALTY_ALPHA * s) * (1 + BONUS_BETA * c)
    assert quality_score(rel, s, c) == pytest.approx(expect)


def test_quality_is_never_negative():
    assert quality_score(0.9, max_sim=1.0, combo_rarity=0.0) >= 0.0


# ── 검색이 filter 를 실제로 넘기는가 ───────────────────────────

def test_search_passes_the_three_key_filter_to_pinecone(monkeypatch):
    import app.services.pinecone_svc as P

    captured = {}

    class FakeIndex:
        def query(self, **kw):
            captured.update(kw)
            class R: matches = []
            return R()

    class FakePC:
        def __init__(self, *a, **k): pass
        def list_indexes(self):
            class I: name = "cx-s1"
            return [I()]
        def Index(self, name): return FakeIndex()

    import sys, types
    mod = types.ModuleType("pinecone"); mod.Pinecone = FakePC
    monkeypatch.setitem(sys.modules, "pinecone", mod)
    monkeypatch.setattr(P, "get_embeddings", lambda t: [[1.0, 0.0]])

    P.search_similar("s1", "워치", top_k=5,
                     cluster_id="CL0", persona_id="CL0-P1", context_id="CL0-P1-C2")
    assert captured["filter"] == context_filter("CL0", "CL0-P1", "CL0-P1-C2")


def test_search_without_a_context_sends_no_filter(monkeypatch):
    import app.services.pinecone_svc as P

    captured = {}

    class FakeIndex:
        def query(self, **kw):
            captured.update(kw)
            class R: matches = []
            return R()

    class FakePC:
        def __init__(self, *a, **k): pass
        def list_indexes(self):
            class I: name = "cx-s1"
            return [I()]
        def Index(self, name): return FakeIndex()

    import sys, types
    mod = types.ModuleType("pinecone"); mod.Pinecone = FakePC
    monkeypatch.setitem(sys.modules, "pinecone", mod)
    monkeypatch.setattr(P, "get_embeddings", lambda t: [[1.0, 0.0]])

    P.search_similar("s1", "워치")
    assert "filter" not in captured
