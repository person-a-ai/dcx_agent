import math

from app.services.s3 import load_data, load_json
from app.services.voyage import get_embeddings
from app.config import settings
from app.jobs.manager import job_manager
from app.utils.text import get_text

# known_insights 는 본문과 **다른 네임스페이스**에 둔다. 같은 곳에 두면
# STEP 09 근거 검색이 "이미 아는 이야기" 문장 자체를 근거랍시고 되돌려준다.
KNOWN_NAMESPACE = "known_insights"

# STEP 09 리랭킹 계수 (목업 Declare 화면에 명시된 값)
#   quality = relevance × (1 − α·max_sim_to_known) × (1 + β·combo_rarity)
PENALTY_ALPHA = 0.5
BONUS_BETA = 0.3

# 07·08 이 아직 안 돌았을 때의 값. 빈 문자열이라야 09 의 $eq filter 가
# 미배정 문서를 집어오지 않는다.
_UNASSIGNED_ID = ""
_UNASSIGNED_DIST = -1.0


def build_metadata(rec: dict) -> dict:
    """Pinecone 메타를 만든다.

    Pinecone 은 None 을 받지 않으므로 모르는 값은 빈 문자열·음수 기본값으로
    내린다. 작성자는 해시만 올린다 — 닉네임 원문은 어디에도 두지 않는다.
    """
    return {
        # 기존 5개 — 검색 결과를 사람이 읽을 수 있게 한다
        "title": (rec.get("title") or "")[:200],
        "desc": (rec.get("desc") or "")[:500],
        "kw": rec.get("kw") or "",
        "cafe": rec.get("cafe") or "",
        "cluster": rec.get("cluster", -1),
        # 09 가 요구하는 것들
        "doc_id": rec.get("doc_id") or "",
        "cluster_id": rec.get("cluster_id") or _UNASSIGNED_ID,
        "persona_id": rec.get("persona_id") or _UNASSIGNED_ID,
        "context_id": rec.get("context_id") or _UNASSIGNED_ID,
        "dist_centroid": float(rec.get("dist_centroid", _UNASSIGNED_DIST)),
        "band": rec.get("band") or "",
        "author_hash": rec.get("author_hash") or "",
    }


def vector_id(rec: dict, fallback_index: int) -> str:
    """벡터 ID 는 doc_id 다.

    예전에는 배치 순번(doc_0, doc_1)이었다. 다시 임베딩하면 같은 문서가
    다른 벡터가 되고, 09 가 doc_id 로 벡터를 되찾을 수 없었다.
    """
    return rec.get("doc_id") or f"row_{fallback_index}"


def context_filter(cluster_id=None, persona_id=None, context_id=None) -> dict:
    """09 의 3키 filter. 주지 않은 키는 넣지 않는다."""
    keys = (("cluster_id", cluster_id), ("persona_id", persona_id),
            ("context_id", context_id))
    return {k: {"$eq": v} for k, v in keys if v}


def _cosine(a, b) -> float:
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0.0 or nb == 0.0:
        return 0.0          # 임베딩 실패분(0 벡터) — 코사인이 정의되지 않는다
    return sum(x * y for x, y in zip(a, b)) / (na * nb)


def max_sim_to_known(emb, known_embs) -> float:
    """이 문서가 '이미 아는 문장' 중 가장 가까운 것과 얼마나 닮았는가. 0~1.

    known_insights 가 비면 0 이다 — 감점이 없고, 그때 quality 는 relevance 와
    같아진다. 음수 코사인(정반대 방향)도 0 으로 자른다. 되돌려주면 감점이
    가점이 되어 quality 가 부풀려진다.
    """
    best = 0.0
    for k in known_embs or []:
        best = max(best, _cosine(emb, k))
    return min(1.0, max(0.0, best))


def quality_score(relevance: float, max_sim: float = 0.0,
                  combo_rarity: float = 0.0) -> float:
    """quality = relevance × (1 − α·max_sim_to_known) × (1 + β·combo_rarity)

    아는 이야기는 내리고(감점), 드문 조합은 올린다(가점).
    """
    q = relevance * (1 - PENALTY_ALPHA * max_sim) * (1 + BONUS_BETA * combo_rarity)
    return max(0.0, q)


def embed_known_insights(index, sid: str) -> int:
    """세션의 known_insights 에 좌표를 붙여 전용 네임스페이스에 올린다.

    id 는 STEP 01 이 문장 내용에서 뽑은 것을 그대로 쓴다 — 문장을 고치면
    id 가 바뀌므로 자연히 새 좌표를 받는다.
    """
    session = load_json(f"sessions/{sid}/session.json") or {}
    insights = session.get("known_insights") or []
    texts = [i.get("text", "") for i in insights if i.get("text")]
    if not texts:
        return 0

    embs = get_embeddings(texts)
    vectors = [
        {"id": ins["id"], "values": emb, "metadata": {"text": ins["text"][:500]}}
        for ins, emb in zip(insights, embs)
        if any(v != 0.0 for v in emb)
    ]
    if vectors:
        index.upsert(vectors=vectors, namespace=KNOWN_NAMESPACE)
    return len(vectors)


def run_embedding(config: dict) -> None:
    """Mini-RAG: Voyage embeddings -> Pinecone storage."""
    sid = config.get("sid", "s0")
    job_manager.set("embed", sid, {"status": "running", "progress": 0, "phase": "loading"})

    try:
        from pinecone import Pinecone

        pc = Pinecone(api_key=settings.pinecone_api_key)

        data = load_data(f"classified/{sid}/relevant_")
        if not data:
            data = load_data(f"preprocessed/{sid}/")
        if not data:
            job_manager.set("embed", sid, {"status": "error", "error": "no data"})
            return

        job_manager.update("embed", sid, progress=10, phase="embedding")

        index_name = f"cx-{sid.replace('_', '-').lower()}"[:45]
        existing = [idx.name for idx in pc.list_indexes()]
        if index_name not in existing:
            pc.create_index(
                name=index_name, dimension=1024, metric="cosine",
                spec={"serverless": {"cloud": "aws", "region": "us-east-1"}},
            )
        index = pc.Index(index_name)

        job_manager.update("embed", sid, progress=20)

        batch_size = 50
        for i in range(0, len(data), batch_size):
            batch = data[i : i + batch_size]
            texts = [get_text(d) for d in batch]
            embeddings = get_embeddings(texts)

            vectors = []
            for j, (d, emb) in enumerate(zip(batch, embeddings)):
                if any(v != 0.0 for v in emb):
                    vectors.append({
                        "id": vector_id(d, i + j),
                        "values": emb,
                        "metadata": build_metadata(d),
                    })
            if vectors:
                index.upsert(vectors=vectors)
            job_manager.update("embed", sid, progress=20 + int(70 * (i + len(batch)) / len(data)))

        # known_insights 에도 좌표를 붙인다 — 09 감점 항의 기준점이다.
        job_manager.update("embed", sid, progress=95, phase="known_insights")
        n_known = embed_known_insights(index, sid)

        job_manager.set("embed", sid, {
            "status": "done", "progress": 100, "total": len(data),
            "index": index_name, "known_insights": n_known,
        })
    except Exception as e:
        job_manager.set("embed", sid, {"status": "error", "error": str(e)})
