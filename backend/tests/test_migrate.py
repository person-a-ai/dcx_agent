"""T2 · 기존 세션 마이그레이션.

계획: docs/development/dcx-step07-11/03-plan.md P0/T2
  RED 구 레코드(doc_id 없음)를 읽어 같은 규칙으로 부여하고,
      두 번 돌려도 결과가 같음(멱등)
  수용 기준 author_hash 는 원문이 없으면 null — 추측해서 채우지 않는다
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from migrate_doc_id import migrate_record, migrate_records, migrate_session  # noqa: E402
from app.utils.identity import make_doc_id, make_author_hash  # noqa: E402


LINK = "https://cafe.naver.com/appleuser/12345"


def old_record(**over):
    """T1 이전에 저장된 모양 — doc_id · author_hash 없음, date 는 YYYYMMDD."""
    rec = {"kw": "심박", "title": "에어팟 심박", "desc": "러닝 중",
           "link": LINK, "cafe": "애플사용자모임", "date": "20260502"}
    rec.update(over)
    return rec


# ── 레코드 하나 ────────────────────────────────────────────────

def test_assigns_doc_id_by_the_same_rule_as_collection():
    out, changed = migrate_record(old_record())
    assert changed
    assert out["doc_id"] == make_doc_id(LINK)


def test_normalizes_date_to_iso():
    out, _ = migrate_record(old_record())
    assert out["date"] == "2026-05-02"


def test_keeps_every_existing_field():
    src = old_record(body="본문", relevance_score=0.87)
    out, _ = migrate_record(src)
    assert set(out) >= set(src)
    assert out["relevance_score"] == 0.87
    assert out["body"] == "본문"


def test_author_hash_is_null_when_author_unknown():
    """수용 기준: 원문이 없으면 null. 추측해서 채우지 않는다."""
    out, _ = migrate_record(old_record())
    assert out["author_hash"] is None


def test_derives_author_hash_from_leaked_meta_author_and_removes_it():
    """T1 이전 레코드에는 crawl4ai 의 meta 가 통째로 붙어 작성자 원문이 남아 있다.
    마이그레이션이 그 값을 해시로 옮기고 원문을 지운다."""
    src = old_record(meta={"crawl_status": "success", "author": "홍길동",
                           "view_count": 10})
    out, _ = migrate_record(src)
    assert out["author_hash"] == make_author_hash("홍길동")
    assert "author" not in out["meta"]
    assert "홍길동" not in repr(out)
    assert out["meta"]["view_count"] == 10   # 나머지 meta 는 남는다


def test_does_not_overwrite_an_existing_doc_id():
    """이미 부여된 ID 를 바꾸면 그 ID 로 걸린 인용이 끊긴다."""
    src = old_record(doc_id="d_aaaaaaaaaaaaaaaa")
    out, _ = migrate_record(src)
    assert out["doc_id"] == "d_aaaaaaaaaaaaaaaa"


def test_does_not_overwrite_an_existing_author_hash():
    src = old_record(author_hash="a_11223344",
                     meta={"author": "홍길동"})
    out, _ = migrate_record(src)
    assert out["author_hash"] == "a_11223344"


def test_record_without_link_gets_null_doc_id_not_a_guess():
    out, _ = migrate_record(old_record(link=""))
    assert out["doc_id"] is None


def test_migrate_record_is_idempotent():
    once, _ = migrate_record(old_record(meta={"author": "홍길동"}))
    twice, changed = migrate_record(dict(once))
    assert twice == once
    assert changed is False


def test_migrate_record_does_not_mutate_its_input():
    src = old_record()
    migrate_record(src)
    assert "doc_id" not in src
    assert src["date"] == "20260502"


# ── 여러 레코드 ────────────────────────────────────────────────

def test_migrate_records_reports_what_changed():
    rows = [old_record(), old_record(link=LINK + "6"),
            old_record(doc_id="d_aaaaaaaaaaaaaaaa", date="2026-05-02",
                       author_hash=None)]
    out, stats = migrate_records(rows)
    assert len(out) == 3
    assert stats["changed"] == 2
    assert stats["unchanged"] == 1


def test_migrate_records_drops_duplicates_by_doc_id():
    """앞선 실행이 쓰기 뒤 삭제 전에 죽으면 같은 문서가 두 벌 남는다.
    다시 돌리면 스스로 정리되어야 한다."""
    rows = [old_record(), old_record()]
    out, stats = migrate_records(rows)
    assert len(out) == 1
    assert stats["duplicates"] == 1


# ── 세션 단위 I/O ──────────────────────────────────────────────

@pytest.fixture
def store(monkeypatch):
    """저장소를 메모리 딕셔너리로 바꾼다. {key: [records]}"""
    import migrate_doc_id as M

    files: dict[str, list[dict]] = {
        "crawl/s1/20260502_120000_000001.jsonl": [old_record(), old_record(link=LINK + "6")],
    }

    monkeypatch.setattr(M, "list_objects", lambda p: [{"Key": k} for k in files if k.startswith(p)])
    monkeypatch.setattr(M, "load_data", lambda p: [r for k, v in files.items() if k.startswith(p) for r in v])
    monkeypatch.setattr(M, "save_jsonl", lambda k, rows: files.__setitem__(k, [dict(r) for r in rows]))
    monkeypatch.setattr(M, "delete_object", lambda k: files.pop(k, None))
    return files


def test_migrate_session_assigns_ids(store):
    stats = migrate_session("s1", apply=True)
    rows = [r for v in store.values() for r in v]
    assert stats["changed"] == 2
    assert all(r["doc_id"] for r in rows)
    assert all(r["date"] == "2026-05-02" for r in rows)


def test_migrate_session_is_idempotent(store):
    migrate_session("s1", apply=True)
    first = sorted((r["doc_id"], r["date"]) for v in store.values() for r in v)
    stats = migrate_session("s1", apply=True)
    second = sorted((r["doc_id"], r["date"]) for v in store.values() for r in v)
    assert first == second
    assert stats["changed"] == 0


def test_migrate_session_writes_new_files_before_deleting_old(store, monkeypatch):
    """쓰기 전에 지우면 중간에 죽었을 때 원본이 사라진다."""
    import migrate_doc_id as M
    order: list[str] = []
    real_save, real_del = M.save_jsonl, M.delete_object
    monkeypatch.setattr(M, "save_jsonl", lambda k, r: (order.append("save"), real_save(k, r))[1])
    monkeypatch.setattr(M, "delete_object", lambda k: (order.append("delete"), real_del(k))[1])
    migrate_session("s1", apply=True)
    assert order.index("save") < order.index("delete")


def test_migrate_session_dry_run_writes_nothing(store):
    before = {k: [dict(r) for r in v] for k, v in store.items()}
    stats = migrate_session("s1", apply=False)
    assert stats["changed"] == 2      # 무엇이 바뀔지는 알려준다
    assert store == before            # 건드리지는 않는다
