"""T6 · 07 군집 → Touch Point.

계획: docs/development/dcx-step07-11/03-plan.md P1/T6
  RED clusters/{sid}/result_{ts}.json 스키마 · k 3~14 스캔 곡선 저장
      문서별 dist_centroid 로 Core/Fringe/Edge 밴드 부여(P50/P90)
      c-TF-IDF 상위 어휘
  RED ID 는 임베딩 갈래에서만 발급 — Ward 갈래 결과에 cluster_id 가 없음
  수용 기준 Edge 밴드 문서가 삭제되지 않고 보존됨
"""
import numpy as np
import pytest

from app.services.clustering import (
    scan_k, assign_bands, c_tf_idf, cluster_id_for, distances_to_centroid,
    build_result, BAND_CORE, BAND_FRINGE, BAND_EDGE, K_MIN, K_MAX,
)


def three_blobs(n=30, seed=0):
    rng = np.random.default_rng(seed)
    centers = np.array([[0.0, 0.0], [10.0, 0.0], [0.0, 10.0]])
    return np.vstack([c + rng.normal(0, 0.35, (n, 2)) for c in centers])


# ── k 스캔 곡선 ────────────────────────────────────────────────

def test_scan_returns_a_curve_not_just_the_winner():
    """목업의 '실루엣 스코어 그래프'가 이 곡선이다. 1.0 은 best_k 만 쓰고
    곡선을 버려서, 사람이 k 선택을 검증할 방법이 없었다."""
    best_k, curve = scan_k(three_blobs(), k_max=6)
    assert len(curve) >= 2
    assert all({"k", "silhouette"} <= set(p) for p in curve)


def test_scan_covers_the_documented_range():
    _, curve = scan_k(three_blobs(n=60))
    ks = [p["k"] for p in curve]
    assert min(ks) == K_MIN
    assert max(ks) <= K_MAX


def test_scan_picks_the_peak_of_its_own_curve():
    best_k, curve = scan_k(three_blobs(), k_max=6)
    assert best_k == max(curve, key=lambda p: p["silhouette"])["k"]


def test_scan_finds_three_blobs():
    best_k, _ = scan_k(three_blobs(), k_max=6)
    assert best_k == 3


def test_scan_is_deterministic():
    X = three_blobs()
    assert scan_k(X, k_max=6)[0] == scan_k(X, k_max=6)[0]


def test_scan_handles_too_few_documents():
    """문서가 k 보다 적으면 군집이 성립하지 않는다 — 터지지 않고 비운다."""
    best_k, curve = scan_k(np.array([[0.0, 0.0], [1.0, 1.0]]))
    assert best_k == 0 and curve == []


# ── 밴드 — Core / Fringe / Edge ────────────────────────────────

def test_bands_split_at_p50_and_p90():
    d = list(range(100))                     # 0..99
    bands = assign_bands(d)
    assert bands[0] == BAND_CORE
    assert bands[60] == BAND_FRINGE
    assert bands[95] == BAND_EDGE


def test_band_proportions_are_roughly_50_40_10():
    bands = assign_bands(list(range(100)))
    assert bands.count(BAND_CORE) == pytest.approx(50, abs=2)
    assert bands.count(BAND_FRINGE) == pytest.approx(40, abs=2)
    assert bands.count(BAND_EDGE) == pytest.approx(10, abs=2)


def test_every_document_gets_a_band():
    """밴드가 없는 문서가 생기면 09 filter 에서 조용히 빠진다."""
    d = [0.1, 0.2, 0.3, 0.4, 0.5]
    assert len(assign_bands(d)) == len(d)
    assert all(b in (BAND_CORE, BAND_FRINGE, BAND_EDGE) for b in assign_bands(d))


def test_identical_distances_do_not_manufacture_edges():
    assert set(assign_bands([0.5] * 10)) == {BAND_CORE}


def test_bands_on_an_empty_list():
    assert assign_bands([]) == []


def test_distances_to_centroid_are_per_own_cluster():
    X = np.array([[0.0, 0.0], [0.1, 0.0], [10.0, 0.0], [10.2, 0.0]])
    labels = [0, 0, 1, 1]
    centroids = np.array([[0.05, 0.0], [10.1, 0.0]])
    d = distances_to_centroid(X, labels, centroids)
    assert d[0] == pytest.approx(0.05) and d[2] == pytest.approx(0.1)


# ── c-TF-IDF — 클러스터를 한 문서로 합친다 ─────────────────────

def test_c_tf_idf_surfaces_the_distinguishing_word_not_the_common_one():
    """1.0 은 클러스터별 TF-IDF 라 어느 클러스터에서나 흔한 말이 올라왔다.
    c-TF-IDF 는 클러스터를 한 문서로 합쳐 계산하므로 '구별하는 어휘'가 뜬다."""
    docs = {
        0: ["에어팟 심박 러닝", "에어팟 심박 측정", "에어팟 심박 워치"],
        1: ["에어팟 배터리 충전", "에어팟 배터리 방전", "에어팟 배터리 교체"],
    }
    top = c_tf_idf(docs, top_n=2)
    assert "심박" in top[0]
    assert "배터리" in top[1]
    # '에어팟' 은 양쪽에 다 있으므로 구별 어휘가 아니다
    assert "에어팟" not in top[0][:1]


def test_c_tf_idf_returns_a_list_per_cluster():
    docs = {0: ["가 나 다"], 1: ["라 마 바"]}
    top = c_tf_idf(docs, top_n=3)
    assert set(top) == {0, 1}
    assert all(isinstance(v, list) for v in top.values())


def test_c_tf_idf_survives_an_empty_cluster():
    top = c_tf_idf({0: ["가 나 다"], 1: []}, top_n=3)
    assert top[1] == []


# ── cluster_id ────────────────────────────────────────────────

def test_cluster_id_shape():
    assert cluster_id_for(0) == "CL0"
    assert cluster_id_for(11) == "CL11"


# ── result 파일 스키마 ─────────────────────────────────────────

def _result():
    X = three_blobs(n=20)
    labels = [0] * 20 + [1] * 20 + [2] * 20
    rows = [{"doc_id": f"d_{i}", "title": f"t{i}", "desc": "심박 러닝"}
            for i in range(60)]
    return build_result(sid="s1", rows=rows, X=X, labels=labels,
                        best_k=3, curve=[{"k": 3, "silhouette": 0.7}],
                        method="embedding")


def test_result_has_the_sections_the_plan_names():
    res, _ = _result()
    for k in ("method", "k", "k_scan", "clusters", "counts"):
        assert k in res, k


def test_result_keeps_the_k_scan_curve():
    res, _ = _result()
    assert res["k_scan"] == [{"k": 3, "silhouette": 0.7}]


def test_each_cluster_reports_its_band_distribution():
    res, _ = _result()
    for c in res["clusters"]:
        assert {"cluster_id", "size", "top_terms", "bands"} <= set(c)
        assert set(c["bands"]) == {BAND_CORE, BAND_FRINGE, BAND_EDGE}


# ── ID 는 임베딩 갈래에서만 ────────────────────────────────────

def test_embedding_branch_issues_ids_and_bands():
    _, rows = _result()
    assert all(r["cluster_id"].startswith("CL") for r in rows)
    assert all(r["band"] in (BAND_CORE, BAND_FRINGE, BAND_EDGE) for r in rows)
    assert all(r["dist_centroid"] >= 0 for r in rows)


def test_ward_branch_issues_no_cluster_id():
    """두 갈래가 모두 ID 를 발급하면 같은 persona_id 가 두 뜻을 갖고
    STEP 09 filter 가 무너진다. Ward 는 비교용이지 ID 발급처가 아니다."""
    X = three_blobs(n=20)
    labels = [0] * 20 + [1] * 20 + [2] * 20
    rows = [{"doc_id": f"d_{i}", "title": "t", "desc": "심박"} for i in range(60)]
    res, out = build_result(sid="s1", rows=rows, X=X, labels=labels, best_k=3,
                            curve=[], method="ward")
    assert res["method"] == "ward"
    assert all("cluster_id" not in r for r in out)
    assert all("ward_cluster" in r for r in out), "비교는 되어야 한다"


def test_build_result_does_not_mutate_the_input_rows():
    rows = [{"doc_id": "d_0", "title": "t", "desc": "심박"}] * 1
    X = np.array([[0.0, 0.0]])
    build_result(sid="s1", rows=rows, X=X, labels=[0], best_k=1, curve=[],
                 method="embedding")
    assert "cluster_id" not in rows[0]


# ── 수용 기준: Edge 는 보존된다 ────────────────────────────────

def test_edge_documents_are_kept_not_dropped():
    """Edge 는 반례 후보다. 지우면 STEP 09 가 반례를 영원히 못 찾는다."""
    res, rows = _result()
    assert len(rows) == 60, "문서가 사라졌다"
    assert any(r["band"] == BAND_EDGE for r in rows)
    assert sum(c["bands"][BAND_EDGE] for c in res["clusters"]) > 0


# ── run_clustering 배선 ────────────────────────────────────────

@pytest.fixture
def cluster_env(monkeypatch):
    import app.services.clustering as C

    jsonl: dict[str, list] = {}
    js: dict[str, dict] = {}
    state: dict = {}

    rows = ([{"doc_id": f"d_{i}", "title": "심박 러닝 워치", "desc": "운동"} for i in range(20)]
            + [{"doc_id": f"e_{i}", "title": "배터리 충전 방전", "desc": "전원"} for i in range(20)]
            + [{"doc_id": f"f_{i}", "title": "통화 마이크 풍절음", "desc": "소음"} for i in range(20)])
    X = three_blobs(n=20)

    monkeypatch.setattr(C, "load_data", lambda p: rows if "classified" in p else [])
    monkeypatch.setattr(C, "get_embeddings", lambda t: X.tolist())
    monkeypatch.setattr(C, "save_jsonl", lambda k, v: jsonl.__setitem__(k, v))
    monkeypatch.setattr(C, "save_json", lambda k, v: js.__setitem__(k, v))
    monkeypatch.setattr(C.job_manager, "set", lambda kind, sid, v: state.update(v))
    monkeypatch.setattr(C.job_manager, "update", lambda *a, **k: None)
    return jsonl, js, state, rows


def test_run_clustering_writes_the_result_file(cluster_env):
    from app.services.clustering import run_clustering
    _, js, state, _ = cluster_env
    run_clustering({"sid": "s1"})
    assert state["status"] == "done", state.get("error")
    res = next(v for k, v in js.items() if "/result_" in k)
    assert res["method"] == "embedding"
    assert res["k_scan"], "k 스캔 곡선이 저장되지 않았다"
    assert res["clusters"]


def test_run_clustering_keeps_every_document_including_edges(cluster_env):
    """수용 기준: Edge 밴드 문서가 삭제되지 않는다."""
    jsonl, js, _, rows = cluster_env
    from app.services.clustering import run_clustering
    run_clustering({"sid": "s1"})
    saved = [r for v in jsonl.values() for r in v]
    assert len(saved) == len(rows), "문서가 사라졌다"
    assert any(r["band"] == BAND_EDGE for r in saved)


def test_run_clustering_reports_agreement_with_the_ward_branch(cluster_env):
    from app.services.clustering import run_clustering
    _, js, _, _ = cluster_env
    run_clustering({"sid": "s1"})
    res = next(v for k, v in js.items() if "/result_" in k)
    assert set(res["agreement_with_ward"]) == {"ari", "nmi"}


def test_ward_run_does_not_issue_ids(cluster_env):
    from app.services.clustering import run_clustering
    jsonl, js, state, _ = cluster_env
    run_clustering({"sid": "s1", "method": "ward", "num_clusters": 3})
    assert state["status"] == "done", state.get("error")
    saved = [r for v in jsonl.values() for r in v]
    assert all("cluster_id" not in r for r in saved)
    assert all("ward_cluster" in r for r in saved)
