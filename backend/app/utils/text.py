import re


def clean_text(t: str) -> str:
    if not t:
        return ""
    t = re.sub(r"<[^>]+>", "", t)
    t = re.sub(r"&amp;", "&", t)
    t = re.sub(r"&lt;", "<", t)
    t = re.sub(r"&gt;", ">", t)
    return t.strip()
