#!/usr/bin/env python3
"""T2 · 기존 세션에 doc_id · author_hash · ISO date 를 부여한다.

T1 이전에 수집된 레코드에는 이 세 값이 없다. 07~11 은 doc_id 로 근거를
인용하고 author_hash 로 작성자를 세므로, 구 세션은 여기를 통과해야
새 단계에 들어갈 수 있다.

규칙은 수집 시점과 **같은 함수**를 쓴다 (app.utils.identity) —
마이그레이션이 따로 계산하면 같은 링크가 다른 ID 를 받는다.

사용
    python scripts/migrate_doc_id.py --list
    python scripts/migrate_doc_id.py s1              # 미리보기 (기본)
    python scripts/migrate_doc_id.py s1 --apply      # 실제 적용
    python scripts/migrate_doc_id.py --all --apply

기본이 미리보기다. 남의 과거 데이터를 덮어쓰는 일이라 --apply 를
명시해야만 쓴다.
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.services.s3 import (  # noqa: E402
    load_data, save_jsonl, list_objects, delete_object, list_prefixes,
)
from app.utils.identity import make_doc_id, make_author_hash, to_iso_date  # noqa: E402

BATCH = 500


def migrate_record(rec: dict) -> tuple[dict, bool]:
    """레코드 하나를 계약에 맞춘다. (새 레코드, 바뀌었는지) 를 돌려준다.

    이미 있는 doc_id · author_hash 는 건드리지 않는다 — 한 번 부여된 ID 를
    바꾸면 그 ID 로 걸린 인용이 전부 끊긴다. 입력은 변경하지 않는다.
    """
    out = dict(rec)
    changed = False

    if not out.get("doc_id"):
        doc_id = make_doc_id(out.get("link"))
        if doc_id != out.get("doc_id"):
            out["doc_id"] = doc_id
            changed = True
        out.setdefault("doc_id", None)

    iso = to_iso_date(out.get("date"))
    if iso != out.get("date"):
        out["date"] = iso
        changed = True

    # T1 이전에는 crawl4ai 의 meta 를 통째로 붙여서 작성자 닉네임 원문이
    # 그대로 저장됐다. 해시로 옮기고 원문은 지운다.
    meta = out.get("meta")
    legacy_author = meta.get("author") if isinstance(meta, dict) else None

    if "author_hash" not in out:
        out["author_hash"] = None
        changed = True
    if not out.get("author_hash") and legacy_author:
        out["author_hash"] = make_author_hash(legacy_author)
        changed = True

    if isinstance(meta, dict) and "author" in meta:
        out["meta"] = {k: v for k, v in meta.items() if k != "author"}
        changed = True

    return out, changed


def migrate_records(rows: list[dict]) -> tuple[list[dict], dict]:
    """여러 레코드를 옮기고 doc_id 가 겹치는 것을 정리한다.

    앞선 실행이 '쓰기' 뒤 '삭제' 전에 죽으면 같은 문서가 두 벌 남는다.
    다시 돌렸을 때 스스로 정리되도록 doc_id 기준으로 첫 것만 남긴다.
    """
    seen: set[str] = set()
    out: list[dict] = []
    stats = {"total": len(rows), "changed": 0, "unchanged": 0, "duplicates": 0}

    for rec in rows:
        migrated, changed = migrate_record(rec)
        doc_id = migrated.get("doc_id")
        if doc_id and doc_id in seen:
            stats["duplicates"] += 1
            continue
        if doc_id:
            seen.add(doc_id)
        out.append(migrated)
        stats["changed" if changed else "unchanged"] += 1

    return out, stats


def migrate_session(sid: str, apply: bool = False, prefix: str = "crawl") -> dict:
    """한 세션의 JSONL 을 전부 읽어 옮긴다.

    **새 파일을 먼저 쓰고 그 다음에 옛 파일을 지운다.** 반대로 하면
    중간에 죽었을 때 원본이 사라진다. 이 순서면 최악의 경우가 중복이고,
    중복은 다시 돌리면 정리된다.
    """
    base = f"{prefix}/{sid}/"
    old_keys = [o["Key"] for o in list_objects(base) if o.get("Key", "").endswith(".jsonl")]
    rows = load_data(base)
    migrated, stats = migrate_records(rows)
    stats["session"] = sid
    stats["files"] = len(old_keys)
    stats["applied"] = False

    if not apply or not migrated:
        return stats

    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    new_keys = set()
    for i in range(0, len(migrated), BATCH):
        key = f"{base}mig_{ts}_{i // BATCH:04d}.jsonl"
        save_jsonl(key, migrated[i:i + BATCH])
        new_keys.add(key)

    # 방금 쓴 파일은 지우지 않는다. 같은 초에 다시 돌리면 타임스탬프가
    # 겹쳐 새 파일이 옛 파일 이름을 덮어쓸 수 있고, 그 상태로 old_keys 를
    # 그대로 지우면 옮긴 데이터가 통째로 사라진다.
    for key in old_keys:
        if key not in new_keys:
            delete_object(key)

    stats["applied"] = True
    return stats


def list_sessions(prefix: str = "crawl") -> list[str]:
    return [p.rstrip("/").split("/")[-1] for p in list_prefixes(f"{prefix}/")]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sid", nargs="?", help="세션 ID")
    ap.add_argument("--all", action="store_true", help="모든 세션")
    ap.add_argument("--list", action="store_true", help="세션 목록만 보기")
    ap.add_argument("--apply", action="store_true",
                    help="실제로 쓴다. 없으면 미리보기만 한다")
    ap.add_argument("--prefix", default="crawl", help="crawl | classified")
    args = ap.parse_args()

    if args.list:
        for s in list_sessions(args.prefix):
            print(s)
        return 0

    if args.all:
        targets = list_sessions(args.prefix)
    elif args.sid:
        targets = [args.sid]
    else:
        ap.error("세션 ID 를 주거나 --all / --list 를 쓴다")
        return 2

    if not targets:
        print("옮길 세션이 없다")
        return 0

    mode = "적용" if args.apply else "미리보기"
    print(f"[{mode}] {args.prefix} · 세션 {len(targets)}개\n")
    total = {"changed": 0, "unchanged": 0, "duplicates": 0}
    for sid in targets:
        st = migrate_session(sid, apply=args.apply, prefix=args.prefix)
        for k in total:
            total[k] += st.get(k, 0)
        print(f"  {sid:20s} 총 {st['total']:>7,}  변경 {st['changed']:>7,}"
              f"  유지 {st['unchanged']:>7,}  중복제거 {st['duplicates']:>5,}")

    print(f"\n  합계  변경 {total['changed']:,} · 유지 {total['unchanged']:,}"
          f" · 중복제거 {total['duplicates']:,}")
    if not args.apply:
        print("\n  아직 아무것도 쓰지 않았다. 적용하려면 --apply 를 붙인다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
