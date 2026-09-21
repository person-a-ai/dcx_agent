"""수집 레코드의 식별자 — doc_id · author_hash · ISO date.

07~11 전 단계가 이 세 값에 의존한다 (계약 §2.3):
  doc_id       09 인용 추적 · 10 Reviews · 11 계보
  author_hash  08·10 의 "작성자 N명"
  date         기간 필터 · 근거 표기

두 해시의 성격이 다르다는 점이 중요하다.
  doc_id      은 **소금을 치지 않는다**. 같은 링크가 어느 세션·어느 배포에서든
              같은 ID 여야 인용이 이어진다. 링크는 이미 공개된 값이라
              되돌려도 잃을 것이 없다.
  author_hash 는 **소금을 친다**. 작성자 닉네임은 개인을 가리키므로,
              소금이 없으면 흔한 닉네임 사전으로 되돌릴 수 있다.
              우리는 작성자가 누구인지 알 필요가 없고 몇 명인지만 세면 된다.
"""
import hashlib
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

from app.config import settings

# 문서를 가리키지 않는 유입 추적 파라미터. 이것 때문에 같은 글이
# 다른 doc_id 를 받으면 같은 근거가 두 번 인용된다.
_TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "ref", "referrer", "share", "from", "fbclid", "gclid",
}

_DOC_ID_BYTES = 8   # 16 hex — 링크 공간에서 충돌이 사실상 없다
_AUTHOR_HASH_BYTES = 4  # 8 hex — 계획 P0/T1 "salted SHA-256 앞 4바이트"


def canonical_link(link: str | None) -> str:
    """doc_id 계산용으로 링크를 정규화한다.

    조각(#…)과 유입 추적 파라미터만 떼고 **나머지 쿼리는 남긴다** —
    네이버 카페의 구 주소는 `ArticleRead.nhn?clubid=..&articleid=..` 처럼
    쿼리가 글을 가리키므로, 쿼리를 통째로 버리면 서로 다른 글이
    같은 doc_id 로 뭉친다.
    """
    if not link:
        return ""
    parts = urlsplit(link.strip())
    kept = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
            if k.lower() not in _TRACKING_PARAMS]
    kept.sort()
    path = parts.path.rstrip("/")
    return urlunsplit((parts.scheme, parts.netloc, path, urlencode(kept), ""))


def make_doc_id(link: str | None) -> str | None:
    """링크에서 안정적인 문서 ID 를 만든다. 링크가 없으면 None."""
    canon = canonical_link(link)
    if not canon:
        return None
    digest = hashlib.sha256(canon.encode("utf-8")).digest()[:_DOC_ID_BYTES]
    return f"d_{digest.hex()}"


def make_author_hash(author: str | None) -> str | None:
    """작성자를 되돌릴 수 없는 형태로 센다. 작성자를 모르면 None — 추측하지 않는다."""
    if not author:
        return None
    salted = settings.author_hash_salt.encode("utf-8") + author.strip().encode("utf-8")
    digest = hashlib.sha256(salted).digest()[:_AUTHOR_HASH_BYTES]
    return f"a_{digest.hex()}"


def to_iso_date(raw: str | None) -> str:
    """네이버의 `YYYYMMDD` 를 `YYYY-MM-DD` 로 맞춘다.

    파싱할 수 없으면 원문을 그대로 돌려준다 — 날짜를 지어내는 것보다
    모양이 어긋난 채 남는 편이 낫다. 어긋난 값은 뒤에서 걸러낼 수 있지만
    지어낸 값은 걸러낼 수 없다.
    """
    if not raw:
        return ""
    s = str(raw).strip()
    if len(s) == 10 and s[4] == "-" and s[7] == "-":
        return s
    if len(s) == 8 and s.isdigit():
        return f"{s[0:4]}-{s[4:6]}-{s[6:8]}"
    return s
