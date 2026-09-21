"""T1 · 수집 레코드에 doc_id · author_hash · ISO date.

계약: resources/DCX_STEP07-11_개발안_데이터계약.md §2.1
계획: docs/development/dcx-step07-11/03-plan.md P0/T1
"""
import pytest

from app.utils.identity import make_doc_id, make_author_hash, to_iso_date


# ── doc_id — link 기준 안정적 ───────────────────────────────────

def test_doc_id_is_stable_for_same_link():
    """같은 링크를 다시 수집해도 같은 doc_id 여야 한다.
    09 인용 추적 · 10 Reviews · 11 계보가 이 안정성에 의존한다."""
    link = "https://cafe.naver.com/appleuser/12345"
    assert make_doc_id(link) == make_doc_id(link)


def test_doc_id_differs_for_different_links():
    a = make_doc_id("https://cafe.naver.com/appleuser/12345")
    b = make_doc_id("https://cafe.naver.com/appleuser/12346")
    assert a != b


def test_doc_id_has_stable_prefix_and_shape():
    doc_id = make_doc_id("https://cafe.naver.com/appleuser/12345")
    assert doc_id.startswith("d_")
    body = doc_id[2:]
    assert len(body) == 16
    assert all(c in "0123456789abcdef" for c in body)


def test_doc_id_ignores_incidental_link_variation():
    """추적 쿼리·후행 슬래시가 붙었다고 다른 문서가 되면 중복 인용이 생긴다."""
    base = "https://cafe.naver.com/appleuser/12345"
    assert make_doc_id(base + "/") == make_doc_id(base)
    assert make_doc_id(base + "?utm_source=share") == make_doc_id(base)


def test_doc_id_requires_a_link():
    """링크가 없으면 안정적 ID 를 만들 수 없다 — 지어내지 않고 None 을 준다."""
    assert make_doc_id("") is None
    assert make_doc_id(None) is None


# ── author_hash — 원문을 저장하지 않는다 ────────────────────────

def test_author_hash_is_salted_sha256_first_4_bytes():
    import hashlib
    from app.config import settings

    author = "홍길동"
    expected = hashlib.sha256(
        settings.author_hash_salt.encode("utf-8") + author.encode("utf-8")
    ).digest()[:4].hex()
    assert make_author_hash(author) == f"a_{expected}"


def test_author_hash_does_not_contain_the_author_string():
    author = "홍길동"
    h = make_author_hash(author)
    assert author not in h
    assert "홍" not in h


def test_author_hash_is_stable_and_distinct():
    assert make_author_hash("홍길동") == make_author_hash("홍길동")
    assert make_author_hash("홍길동") != make_author_hash("김철수")


def test_author_hash_is_salted_not_bare_sha256():
    """소금 없이 해시하면 닉네임 사전으로 되돌릴 수 있다."""
    import hashlib
    bare = hashlib.sha256("홍길동".encode("utf-8")).digest()[:4].hex()
    assert make_author_hash("홍길동") != f"a_{bare}"


def test_author_hash_is_none_when_author_unknown():
    """작성자를 모르면 추측해서 채우지 않는다 (T2 수용 기준과 같은 규칙)."""
    assert make_author_hash("") is None
    assert make_author_hash(None) is None


# ── date — ISO 정규화 ──────────────────────────────────────────

@pytest.mark.parametrize("raw,iso", [
    ("20260502", "2026-05-02"),
    ("2026-05-02", "2026-05-02"),
    ("20260101", "2026-01-01"),
])
def test_to_iso_date_normalizes(raw, iso):
    assert to_iso_date(raw) == iso


@pytest.mark.parametrize("raw", ["", None, "not-a-date", "2026050"])
def test_to_iso_date_passes_through_when_unparseable(raw):
    """파싱 못 하면 날짜를 지어내지 않는다."""
    assert to_iso_date(raw) == (raw or "")


# ── 실제 수집 경로 — crawl_keywords 가 내는 레코드 ─────────────

@pytest.fixture
def crawl_env(monkeypatch):
    """네이버 API · S3 · job manager 를 걷어내고 저장된 레코드를 붙잡는다."""
    from app.services import crawling as C

    saved: list[dict] = []

    def fake_search(query, display=100, start=1):
        if start > 1:
            return {"items": []}
        return {"items": [
            {"title": "에어팟 심박 측정 되나요",
             "description": "러닝할 때 에어팟으로 심박 보고 싶은데",
             "link": "https://cafe.naver.com/appleuser/12345",
             "cafename": "애플사용자모임", "postdate": "20260502"},
            {"title": "에어팟 프로 배터리",
             "description": "에어팟 오래 쓰니 배터리가",
             "link": "https://cafe.naver.com/appleuser/12346?utm_source=share",
             "cafename": "애플사용자모임", "postdate": "20260103"},
        ]}

    monkeypatch.setattr(C, "search_naver_cafe", fake_search)
    monkeypatch.setattr(C, "save_jsonl", lambda key, rows: saved.extend(rows))
    monkeypatch.setattr(C.job_manager, "update", lambda *a, **k: None)
    monkeypatch.setattr(C.job_manager, "is_stop_requested", lambda *a, **k: False)
    monkeypatch.setattr(C.time, "sleep", lambda *a, **k: None)
    return saved


def _run(saved, **over):
    from app.services.crawling import crawl_keywords
    cfg = {"sid": "s_test", "bk": "에어팟", "keywords": ["심박"], "target": 10}
    cfg.update(over)
    crawl_keywords(cfg)
    return saved


def test_crawl_record_carries_the_three_new_fields(crawl_env):
    rows = _run(crawl_env)
    assert rows, "레코드가 하나도 안 나왔다"
    for r in rows:
        assert r["doc_id"].startswith("d_")
        assert "author_hash" in r          # API 단계에선 아직 모른다 → None
        assert r["date"] == to_iso_date(r["date"])


def test_crawl_record_keeps_every_existing_field(crawl_env):
    """수용 기준: 기존 필드 하나도 제거하지 않는다."""
    rows = _run(crawl_env)
    for r in rows:
        assert set(r) >= {"kw", "title", "desc", "link", "cafe", "date"}


def test_crawl_record_date_is_iso(crawl_env):
    rows = _run(crawl_env)
    assert {r["date"] for r in rows} == {"2026-05-02", "2026-01-03"}


def test_crawl_record_doc_id_survives_recollection(crawl_env):
    """같은 세션을 다시 돌려도 같은 링크는 같은 doc_id 여야 한다."""
    first = {r["link"]: r["doc_id"] for r in _run(crawl_env)}
    crawl_env.clear()
    second = {r["link"]: r["doc_id"] for r in _run(crawl_env)}
    assert first == second


def test_crawl_record_author_hash_is_none_before_body_crawl(crawl_env):
    """API 단계는 작성자를 모른다 — 지어내지 않는다."""
    rows = _run(crawl_env)
    assert all(r["author_hash"] is None for r in rows)


def test_body_crawl_stores_author_hash_not_the_author(monkeypatch):
    """Phase 2 는 작성자를 해시로만 남긴다.

    회귀 방지: 예전에는 crawl4ai 의 meta 를 통째로 레코드에 붙여서
    작성자 닉네임 원문이 그대로 저장됐다."""
    from app.services import crawling as C

    saved: list[dict] = []
    base = {"kw": "심박", "title": "t", "desc": "d",
            "link": "https://cafe.naver.com/appleuser/12345",
            "cafe": "애플사용자모임", "date": "2026-05-02",
            "doc_id": "d_deadbeefdeadbeef", "author_hash": None}

    monkeypatch.setattr(C, "load_data", lambda prefix: [dict(base)])
    monkeypatch.setattr(C, "list_objects", lambda prefix: [])
    monkeypatch.setattr(C, "delete_object", lambda key: None)
    monkeypatch.setattr(C, "save_jsonl", lambda key, rows: saved.extend(rows))
    def fake_search(query, display=100, start=1):
        if start > 1:
            return {"items": []}
        return {"items": [{"title": "에어팟 심박", "description": "러닝 중 에어팟",
                           "link": base["link"], "cafename": "애플사용자모임",
                           "postdate": "20260502"}]}
    monkeypatch.setattr(C, "search_naver_cafe", fake_search)
    monkeypatch.setattr(C.job_manager, "update", lambda *a, **k: None)
    monkeypatch.setattr(C.job_manager, "is_stop_requested", lambda *a, **k: False)
    monkeypatch.setattr(C.time, "sleep", lambda *a, **k: None)

    async def fake_crawl(urls, cookies, on_progress=None, should_stop=None):
        return [{"url": base["link"], "body": "본문",
                 "meta": {"crawl_status": "success", "author": "홍길동",
                          "body_length": 6, "view_count": 10,
                          "board_name": "자유게시판"}}]

    import app.services.crawl4ai_svc as svc
    monkeypatch.setattr(svc, "crawl_cafe_posts", fake_crawl)

    C.crawl_keywords({"sid": "s_test", "bk": "에어팟", "keywords": ["심박"],
                      "target": 10, "mode": "api_crawl4ai"})

    merged = [r for r in saved if r.get("body")]
    assert merged, "병합 후 저장된 레코드가 없다"
    rec = merged[-1]
    assert rec["author_hash"] == make_author_hash("홍길동")
    blob = repr(rec)
    assert "홍길동" not in blob, "작성자 원문이 레코드에 남았다"
