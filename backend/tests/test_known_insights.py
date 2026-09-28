"""T3 · known_insights 입력 (STEP 01).

계획: docs/development/dcx-step07-11/03-plan.md P0/T3
  RED 세션 저장/조회 왕복에서 known_insights[{id,text}] 가 보존됨
      5~10개 범위 밖이면 경고(차단 아님)

왜 필요한가 — 계약 §2.3:
  known_insights 가 없으면 09 의
    quality = relevance × (1 − α·max_sim_to_known) × (1 + β·combo_rarity)
  에서 감점 항이 항상 1 이 되어, "아는 이야기를 내린다"는 설계의 핵심이
  무력화된다.
"""
import pytest

from app.models.schemas import (
    SessionSaveRequest, normalize_known_insights, make_insight_id,
    KNOWN_INSIGHTS_MIN, KNOWN_INSIGHTS_MAX,
)


SENTENCES = [
    "러너는 심박을 보려고 워치를 추가로 착용한다",
    "땀이 많은 사용자는 이어팁 이탈을 가장 큰 불만으로 든다",
    "장시간 착용하면 귀가 아파 결국 빼게 된다",
    "이어폰 센서 정확도를 믿지 못하는 사람이 있다",
    "운동 앱과 건강 앱 사이에서 기록을 손으로 옮긴다",
]


def texts(n):
    return [{"text": t} for t in SENTENCES[:n]]


# ── 정규화 ────────────────────────────────────────────────────

def test_assigns_an_id_when_the_client_sends_none():
    out, _ = normalize_known_insights(texts(5))
    assert all(i["id"] for i in out)
    assert all(i["id"].startswith("ki_") for i in out)


def test_id_is_derived_from_the_text_so_it_is_stable():
    """같은 문장은 어느 세션에서든 같은 id 여야 STEP 05 가 붙인 좌표를 다시 쓸 수 있다."""
    a, _ = normalize_known_insights([{"text": SENTENCES[0]}])
    b, _ = normalize_known_insights([{"text": SENTENCES[0]}])
    assert a[0]["id"] == b[0]["id"] == make_insight_id(SENTENCES[0])


def test_editing_the_text_changes_the_id():
    """문장이 바뀌면 좌표도 다시 잡아야 한다 — 같은 id 로 두면 STEP 09 가 옛 좌표로 감점한다."""
    a, _ = normalize_known_insights([{"text": "러너는 워치를 찬다"}])
    b, _ = normalize_known_insights([{"text": "러너는 워치를 두 개 찬다"}])
    assert a[0]["id"] != b[0]["id"]


def test_keeps_a_client_supplied_id():
    out, _ = normalize_known_insights([{"id": "ki_custom", "text": SENTENCES[0]}])
    assert out[0]["id"] == "ki_custom"


def test_trims_and_drops_empty_lines():
    out, _ = normalize_known_insights(
        [{"text": "  러너는 워치를 찬다  "}, {"text": ""}, {"text": "   "}, {"text": None}]
    )
    assert len(out) == 1
    assert out[0]["text"] == "러너는 워치를 찬다"


def test_drops_duplicate_sentences():
    out, _ = normalize_known_insights([{"text": SENTENCES[0]}, {"text": SENTENCES[0]}])
    assert len(out) == 1


def test_accepts_plain_strings_too():
    out, _ = normalize_known_insights(SENTENCES[:5])
    assert [i["text"] for i in out] == SENTENCES[:5]


def test_keeps_only_id_and_text():
    out, _ = normalize_known_insights([{"id": "ki_1", "text": SENTENCES[0], "junk": 1}])
    assert set(out[0]) == {"id", "text"}


# ── 5~10 경고 — 차단이 아니다 ───────────────────────────────────

@pytest.mark.parametrize("n", [5, 6, 10])
def test_no_warning_inside_the_range(n):
    many = SENTENCES + [f"추가로 아는 사실 {i}" for i in range(n)]
    out, warnings = normalize_known_insights(texts(min(n, 5)) + [{"text": s} for s in many[5:n]])
    assert len(out) == n
    assert warnings == []


def test_warns_when_too_few_but_keeps_them():
    out, warnings = normalize_known_insights(texts(2))
    assert len(out) == 2, "차단하지 않는다"
    assert warnings and str(KNOWN_INSIGHTS_MIN) in warnings[0]


def test_warns_when_too_many_but_keeps_them():
    rows = [{"text": f"아는 사실 {i}"} for i in range(14)]
    out, warnings = normalize_known_insights(rows)
    assert len(out) == 14, "차단하지 않는다"
    assert warnings and str(KNOWN_INSIGHTS_MAX) in warnings[0]


def test_empty_is_warned_not_an_error():
    """비어 있어도 파이프라인은 돈다 — 다만 09 감점 항이 사라진다는 걸 알려준다."""
    out, warnings = normalize_known_insights([])
    assert out == []
    assert warnings


# ── 세션 왕복 ──────────────────────────────────────────────────

@pytest.fixture
def store(monkeypatch):
    from app.routers import sessions as S
    saved: dict[str, dict] = {}
    monkeypatch.setattr(S, "save_json", lambda k, d: saved.__setitem__(k, d))
    monkeypatch.setattr(S, "load_json", lambda k: saved.get(k))
    return saved


def test_round_trip_preserves_known_insights(store):
    from app.routers.sessions import save_session, get_session

    res = save_session(SessionSaveRequest(
        sid="s1", data={"bk": "에어팟", "problemDef": "운동 맥락",
                        "known_insights": texts(5)}))
    assert res["status"] == "saved"

    got = get_session("s1")["data"]["known_insights"]
    assert [i["text"] for i in got] == SENTENCES[:5]
    assert all(i["id"] for i in got)


def test_save_returns_the_warning_without_refusing(store):
    from app.routers.sessions import save_session, get_session

    res = save_session(SessionSaveRequest(sid="s1", data={"known_insights": texts(2)}))
    assert res["status"] == "saved", "경고는 차단이 아니다"
    assert res["warnings"]
    assert len(get_session("s1")["data"]["known_insights"]) == 2


def test_save_leaves_the_rest_of_the_session_alone(store):
    from app.routers.sessions import save_session, get_session

    save_session(SessionSaveRequest(sid="s1", data={
        "bk": "에어팟", "problemDef": "운동 맥락", "ages": ["직장인"],
        "allKw": [{"kw": "심박", "cat": "기능"}], "step": "r1",
        "known_insights": texts(5)}))
    d = get_session("s1")["data"]
    assert d["bk"] == "에어팟" and d["step"] == "r1"
    assert d["allKw"] == [{"kw": "심박", "cat": "기능"}]


def test_session_without_known_insights_still_saves(store):
    from app.routers.sessions import save_session, get_session

    res = save_session(SessionSaveRequest(sid="s1", data={"bk": "에어팟"}))
    assert res["status"] == "saved"
    assert get_session("s1")["data"]["known_insights"] == []
