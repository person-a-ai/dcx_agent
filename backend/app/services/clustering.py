import numpy as np
from datetime import datetime
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.feature_extraction.text import TfidfVectorizer

from app.services.s3 import load_data, save_jsonl, save_json
from app.services.voyage import get_embeddings
from app.jobs.manager import job_manager
from app.utils.text import get_text

# ── 07 군집 → Touch Point (03-plan.md P1/T6) ──────────────────
#
# 두 갈래를 나란히 돌린다. 1.0 결과물은 이미 검증된 산출이고, 임베딩
# 기반 분할이 그 결과를 얼마나 보존하는지는 아직 아무도 모른다. 한쪽을
# 지우면 그 질문을 영구히 답할 수 없다.
#
# 다만 **ID 는 한 갈래에서만** 발급한다. 둘 다 발급하면 같은 cluster_id 가
# 두 뜻을 갖고 STEP 09 의 3키 filter 가 무너진다. 임베딩 갈래가 발급처고,
# Ward 갈래는 비교용 라벨(ward_cluster)만 남긴다.

K_MIN, K_MAX = 3, 14

# 밴드는 dist_centroid 의 백분위다. Core 는 그 클러스터를 대표하고,
# Edge 는 **반례 후보**다 — 지우지 않고 보존한다. 지우면 STEP 09 가
# 반례를 영원히 찾지 못한다.
BAND_CORE, BAND_FRINGE, BAND_EDGE = "Core", "Fringe", "Edge"
_P_CORE, _P_FRINGE = 50, 90


def cluster_id_for(i: int) -> str:
    return f"CL{int(i)}"


def scan_k(X, k_min: int = K_MIN, k_max: int = K_MAX):
    """k 를 훑어 실루엣 곡선을 만들고 봉우리를 고른다.

    곡선을 통째로 돌려주는 게 핵심이다. 1.0 은 best_k 만 쓰고 곡선을 버려서
    사람이 k 선택을 검증할 방법이 없었다 — 목업의 '실루엣 스코어 그래프'가
    이 곡선이다.
    """
    X = np.asarray(X)
    n = len(X)
    upper = min(k_max, n - 1)
    curve = []
    for k in range(k_min, upper + 1):
        try:
            km = KMeans(n_clusters=k, random_state=42, n_init=10)
            lbls = km.fit_predict(X)
            if len(set(lbls)) < 2:
                continue
            curve.append({"k": k, "silhouette": round(float(silhouette_score(X, lbls)), 4)})
        except Exception:
            continue
    if not curve:
        return 0, []
    return max(curve, key=lambda p: p["silhouette"])["k"], curve


def distances_to_centroid(X, labels, centroids):
    """문서마다 **자기 클러스터** 중심까지의 거리."""
    X = np.asarray(X, dtype=float)
    centroids = np.asarray(centroids, dtype=float)
    return [float(np.linalg.norm(X[i] - centroids[int(l)])) for i, l in enumerate(labels)]


def assign_bands(distances) -> list[str]:
    """거리 백분위로 Core / Fringe / Edge 를 나눈다 (P50 / P90).

    거리가 모두 같으면 전부 Core 다 — 흩어지지 않은 군집에서 Edge 를
    억지로 만들어내면 있지도 않은 반례를 STEP 09 로 흘려보낸다.
    """
    if not len(distances):
        return []
    d = np.asarray(distances, dtype=float)
    p50, p90 = np.percentile(d, _P_CORE), np.percentile(d, _P_FRINGE)
    return [BAND_CORE if x <= p50 else (BAND_FRINGE if x <= p90 else BAND_EDGE)
            for x in d]


def c_tf_idf(docs_by_cluster: dict, top_n: int = 10) -> dict:
    """클러스터를 **한 문서로 합쳐** 상위 어휘를 뽑는다.

    1.0 은 클러스터별 TF-IDF 평균이라 어느 클러스터에나 흔한 말이 올라왔다.
    클러스터를 한 문서로 합치면 IDF 가 클러스터 사이에서 계산되므로
    '다른 클러스터와 구별되는 어휘'가 뜬다 (BERTopic 의 c-TF-IDF).
    """
    keys = list(docs_by_cluster)
    joined = [" ".join(docs_by_cluster[k]) for k in keys]
    out = {k: [] for k in keys}
    if not any(j.strip() for j in joined):
        return out
    try:
        vec = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")
        M = vec.fit_transform(joined)
        names = list(vec.get_feature_names_out())
    except Exception:
        return out
    for row, k in enumerate(keys):
        if not joined[row].strip():
            continue
        scores = M[row].toarray().ravel()
        out[k] = [names[i] for i in scores.argsort()[::-1][:top_n] if scores[i] > 0]
    return out


def build_result(sid, rows, X, labels, best_k, curve, method="embedding"):
    """result_{ts}.json 과 밴드가 붙은 레코드를 만든다.

    입력 레코드는 건드리지 않는다. Ward 갈래에는 cluster_id 를 붙이지 않는다.
    """
    X = np.asarray(X, dtype=float)
    labels = [int(l) for l in labels]
    uniq = sorted(set(labels))
    centroids = np.array([X[[i for i, l in enumerate(labels) if l == c]].mean(axis=0)
                          for c in uniq])
    remap = {c: i for i, c in enumerate(uniq)}
    dense = [remap[l] for l in labels]

    dists = distances_to_centroid(X, dense, centroids)

    # 밴드는 클러스터 안에서 매긴다 — 퍼진 정도가 군집마다 다르므로
    # 전체 백분위로 자르면 넓은 군집이 통째로 Edge 가 된다.
    bands = [""] * len(rows)
    for c in range(len(uniq)):
        idx = [i for i, l in enumerate(dense) if l == c]
        for i, b in zip(idx, assign_bands([dists[i] for i in idx])):
            bands[i] = b

    docs_by_cluster = {c: [get_text(rows[i]) for i, l in enumerate(dense) if l == c]
                       for c in range(len(uniq))}
    top_terms = c_tf_idf(docs_by_cluster)

    out = []
    for i, rec in enumerate(rows):
        item = dict(rec)
        if method == "embedding":
            item["cluster_id"] = cluster_id_for(dense[i])
            item["dist_centroid"] = round(dists[i], 6)
            item["band"] = bands[i]
        else:
            # 비교는 되어야 하지만 ID 발급처는 아니다.
            item["ward_cluster"] = dense[i]
        item["cluster"] = dense[i]      # 기존 필드 유지
        out.append(item)

    clusters = []
    for c in range(len(uniq)):
        idx = [i for i, l in enumerate(dense) if l == c]
        clusters.append({
            "cluster_id": cluster_id_for(c),
            "size": len(idx),
            "top_terms": top_terms.get(c, []),
            "bands": {b: sum(1 for i in idx if bands[i] == b)
                      for b in (BAND_CORE, BAND_FRINGE, BAND_EDGE)},
        })

    result = {
        "sid": sid,
        "method": method,
        "k": len(uniq),
        "best_k": best_k,
        "k_scan": curve,
        "clusters": clusters,
        "counts": {
            "total": len(rows),
            **{b: sum(1 for x in bands if x == b)
               for b in (BAND_CORE, BAND_FRINGE, BAND_EDGE)},
        },
    }
    return result, out


def ward_labels(texts, k: int):
    """기존 방법(1.0) 갈래 — Ward 연결 + TF-IDF 입력.

    1.0 은 형태소 토큰을 넣었다. 여기서는 같은 텍스트의 TF-IDF 를 쓴다 —
    형태소 분석기를 끌어오지 않고도 "임베딩이 아닌 표현으로 자른 결과"를
    비교 대상으로 세우려는 것이다. 이 갈래는 ID 를 발급하지 않는다.
    """
    from sklearn.cluster import AgglomerativeClustering

    vec = TfidfVectorizer(max_features=3000, ngram_range=(1, 2))
    V = vec.fit_transform(texts).toarray()
    return AgglomerativeClustering(n_clusters=k, linkage="ward").fit_predict(V), V


def run_clustering(config: dict) -> None:
    """07 군집. 임베딩 갈래가 ID 발급처고, Ward 갈래는 비교용이다."""
    sid = config.get("sid", "s0")
    num_clusters = config.get("num_clusters", 0)
    method = config.get("method", "embedding")
    job_manager.set("cluster", sid, {"status": "running", "phase": "loading", "progress": 0})

    try:
        data = load_data(f"classified/{sid}/relevant_")
        if not data:
            data = load_data(f"preprocessed/{sid}/")
        if not data:
            job_manager.set("cluster", sid, {"status": "error", "error": "no data"})
            return

        job_manager.update("cluster", sid, progress=10, phase="embedding")
        texts = [get_text(d) for d in data]
        X = np.array(get_embeddings(texts))

        job_manager.update("cluster", sid, progress=40, phase="k_scan")
        if num_clusters and num_clusters > 0:
            best_k, curve = num_clusters, []
        else:
            best_k, curve = scan_k(X)
            if not best_k:
                job_manager.set("cluster", sid, {"status": "error",
                                                 "error": "문서가 너무 적어 군집이 성립하지 않는다"})
                return

        job_manager.update("cluster", sid, progress=60, phase="clustering")
        if method == "ward":
            labels, _ = ward_labels(texts, best_k)
        else:
            labels = KMeans(n_clusters=best_k, random_state=42, n_init=10).fit_predict(X)

        job_manager.update("cluster", sid, progress=80, phase="banding")
        result, rows = build_result(sid, data, X, labels, best_k, curve, method)

        # 두 갈래가 얼마나 겹치는지 — 1.0 결과를 얼마나 보존하는가.
        if method == "embedding" and len(data) >= best_k:
            try:
                from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
                w, _ = ward_labels(texts, best_k)
                result["agreement_with_ward"] = {
                    "ari": round(float(adjusted_rand_score(labels, w)), 3),
                    "nmi": round(float(normalized_mutual_info_score(labels, w)), 3),
                }
            except Exception:
                pass

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_json(f"clusters/{sid}/result_{ts}.json", result)
        # Edge 밴드는 반례 후보다 — 걸러내지 않고 그대로 같이 저장한다.
        for c in range(result["k"]):
            save_jsonl(f"clusters/{sid}/cluster_{c}_{ts}.jsonl",
                       [r for r in rows if r.get("cluster") == c])

        job_manager.set("cluster", sid, {
            "status": "done", "progress": 100,
            "method": method,
            "num_clusters": result["k"], "total": len(rows),
            "k_scan": curve, "counts": result["counts"],
            "clusters": {c["cluster_id"]: c for c in result["clusters"]},
            "agreement_with_ward": result.get("agreement_with_ward"),
            "result": f"clusters/{sid}/result_{ts}.json",
        })
    except Exception as e:
        job_manager.set("cluster", sid, {"status": "error", "error": str(e)})


def refine_clusters(config: dict) -> dict:
    """Refine clusters: keep/merge selected clusters."""
    sid = config.get("sid", "s_unknown")
    keep = config.get("keepClusters", [])
    merge = config.get("mergeClusters", [])

    try:
        all_data = load_data(f"clusters/{sid}/cluster_")
        if keep:
            all_data = [d for d in all_data if d.get("cluster") in set(keep)]
        if merge and len(merge) > 1:
            for item in all_data:
                if item.get("cluster") in set(merge):
                    item["cluster"] = merge[0]

        unique = sorted(set(d.get("cluster", -1) for d in all_data))
        cmap = {old: new for new, old in enumerate(unique)}
        for item in all_data:
            item["cluster"] = cmap.get(item.get("cluster", -1), 0)

        texts = [get_text(d) for d in all_data]
        vec = TfidfVectorizer(max_features=3000, ngram_range=(1, 2), min_df=2, max_df=0.95)
        X = vec.fit_transform(texts)
        fnames = list(vec.get_feature_names_out())

        clusters_info = {}
        for cid in range(len(unique)):
            idxs = [j for j, d in enumerate(all_data) if d.get("cluster") == cid]
            cdata = [all_data[j] for j in idxs]
            if idxs:
                tfidf_mean = X[idxs].mean(axis=0).A1
                top_kw = [fnames[x] for x in tfidf_mean.argsort()[-10:][::-1]]
            else:
                top_kw = []
            samples = [
                {"title": d.get("title", "")[:80], "desc": d.get("desc", "")[:150], "cafe": d.get("cafe", "")}
                for d in cdata[:5]
            ]
            clusters_info[str(cid)] = {
                "id": cid, "size": len(cdata), "keywords": top_kw, "samples": samples, "name": "",
            }

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_jsonl(f"clusters_refined/{sid}/data_{ts}.jsonl", all_data)

        return {
            "status": "done", "kept_clusters": len(unique),
            "total_docs": len(all_data), "clusters": clusters_info,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
