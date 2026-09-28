from app.config import settings
from app.services.embedding import context_filter
from app.services.voyage import get_embeddings


def search_similar(sid: str, query: str, top_k: int = 10,
                   cluster_id=None, persona_id=None, context_id=None) -> list[dict]:
    """Mini-RAG: Voyage embedding + Pinecone search.

    3키(cluster_id·persona_id·context_id)를 주면 그 맥락 안에서만 찾는다.
    09 가 한 Context 의 근거를 모을 때 다른 클러스터 문서가 섞이면
    "이 사람의 근거"가 아니게 된다.
    """
    try:
        from pinecone import Pinecone

        pc = Pinecone(api_key=settings.pinecone_api_key)
    except Exception:
        return []
    try:
        index_name = f"cx-{sid.replace('_', '-').lower()}"[:45]
        existing = [idx.name for idx in pc.list_indexes()]
        if index_name not in existing:
            return []
        index = pc.Index(index_name)
        query_emb = get_embeddings([query])[0]
        flt = context_filter(cluster_id, persona_id, context_id)
        kwargs = {"vector": query_emb, "top_k": top_k, "include_metadata": True}
        if flt:
            kwargs["filter"] = flt
        results = index.query(**kwargs)
        return [{"score": m.score, **m.metadata} for m in results.matches]
    except Exception as e:
        print(f"Search error: {e}")
        return []
