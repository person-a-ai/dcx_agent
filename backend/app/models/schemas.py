import hashlib

from pydantic import BaseModel

# ── known_insights (STEP 01) ──────────────────────────────────
# "이건 이미 아는 것"을 파이프라인에 알려주는 유일한 장치다.
# STEP 05 가 좌표를 부여하고, STEP 09 리랭킹이 감점 항으로 쓴다:
#   quality = relevance × (1 − α·max_sim_to_known) × (1 + β·combo_rarity)
# 비어 있으면 감점 항이 항상 1 이 되어 RAG 가 이미 아는 이야기를
# 근거랍시고 되돌려준다.

KNOWN_INSIGHTS_MIN = 5
KNOWN_INSIGHTS_MAX = 10


class KnownInsight(BaseModel):
    id: str = ""
    text: str = ""


def make_insight_id(text: str) -> str:
    """문장에서 안정적인 id 를 만든다.

    내용에서 뽑는 이유: 같은 문장은 어느 세션에서든 같은 id 라야 STEP 05 가
    붙인 좌표를 다시 쓸 수 있고, 문장을 고치면 id 가 바뀌어 좌표를 다시
    잡게 된다. 순번(ki_1, ki_2)으로 두면 목록을 재정렬하는 것만으로
    id 가 다른 문장을 가리키게 된다.
    """
    digest = hashlib.sha256(text.strip().encode("utf-8")).digest()[:6]
    return f"ki_{digest.hex()}"


def normalize_known_insights(raw) -> tuple[list[dict], list[str]]:
    """입력을 [{id, text}] 로 맞추고 경고를 돌려준다.

    경고는 **차단이 아니다**. 개수가 어긋난 채로도 파이프라인은 돌아야
    하고, 몇 개가 적절한지는 사람이 판단할 몫이다.
    """
    items: list[dict] = []
    seen: set[str] = set()

    for entry in raw or []:
        if isinstance(entry, str):
            entry = {"text": entry}
        if not isinstance(entry, dict):
            continue
        text = (entry.get("text") or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        items.append({"id": (entry.get("id") or "").strip() or make_insight_id(text),
                      "text": text})

    warnings: list[str] = []
    n = len(items)
    if n == 0:
        warnings.append(
            "known_insights 가 비어 있습니다 — STEP 09 가 이미 아는 이야기를 "
            f"내리지 못합니다. {KNOWN_INSIGHTS_MIN}~{KNOWN_INSIGHTS_MAX}문장을 권합니다."
        )
    elif n < KNOWN_INSIGHTS_MIN:
        warnings.append(
            f"known_insights 가 {n}개입니다 — {KNOWN_INSIGHTS_MIN}개 미만이면 "
            "STEP 09 의 감점이 거의 걸리지 않습니다."
        )
    elif n > KNOWN_INSIGHTS_MAX:
        warnings.append(
            f"known_insights 가 {n}개입니다 — {KNOWN_INSIGHTS_MAX}개를 넘으면 "
            "감점이 과해져 새로운 근거까지 밀려날 수 있습니다."
        )
    return items, warnings




class CrawlRequest(BaseModel):
    sid: str = "s_unknown"
    bk: str = ""
    keywords: list[str] = []
    target: int = 50000
    dateFrom: str = ""
    dateTo: str = ""
    cafes: str | list = ""
    excludeCafes: str | list = ""
    adFilter: str | list = ""
    mode: str = "api_only"          # "api_only" | "api_crawl4ai"
    cookies: str | None = None      # Naver login cookies for Crawl4AI


class PreprocessRequest(BaseModel):
    sid: str = "s_unknown"
    extraFilter: str = ""
    excludeCafes: list[str] = []


class TrainRequest(BaseModel):
    sid: str = "s_unknown"
    bk: str = ""
    problemDef: str = ""


class ClusterRequest(BaseModel):
    sid: str = "s_unknown"
    num_clusters: int = 0


class ClusterRefineRequest(BaseModel):
    sid: str = "s_unknown"
    bk: str = ""
    keepClusters: str | list = ""
    mergeClusters: str | list = ""


class EmbedRequest(BaseModel):
    sid: str = "s_unknown"


class PersonaRequest(BaseModel):
    sid: str = "s_unknown"
    bk: str = ""
    problemDef: str = ""


class SessionSaveRequest(BaseModel):
    sid: str = "s_unknown"
    data: dict = {}


class SearchRequest(BaseModel):
    sid: str = "s0"
    query: str = ""
    top_k: int = 10


class ChatRequest(BaseModel):
    sid: str = "s0"
    query: str = ""
    pipeline_context: str = ""


class InsightChatRequest(BaseModel):
    sid: str = "s0"
    query: str = ""
    bk: str = ""


class KeywordGenRequest(BaseModel):
    sid: str = ""
    bk: str = ""
    problemDef: str = ""
    existingKeywords: list[str] = []
    round: int = 1
    ages: list[str] = []
    ageRange: list[str] = []
    gens: list[str] = []


class ScoreKeywordsRequest(BaseModel):
    bk: str = ""
    keywords: list[dict] = []  # [{"kw": "...", "cat": "..."}]


class SuggestWordsRequest(BaseModel):
    bk: str = ""
    problemDef: str = ""
    category: str = ""
    existingKeywords: list[str] = []
