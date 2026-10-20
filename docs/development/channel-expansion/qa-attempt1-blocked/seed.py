"""Create QA sessions through POST /context, then seed approved keywords via the app store.

Run with the same LOCAL_DATA_DIR and PYTHONPATH as the backend. Data must be
under this QA evidence directory. No crawl is started by this script.
"""
import json
import os
from pathlib import Path
import sys
from urllib.request import Request, urlopen

QA = Path(__file__).resolve().parent
ROOT = QA.parents[3]
DATA = Path(os.environ["LOCAL_DATA_DIR"]).resolve()
if not DATA.is_relative_to(QA):
    raise SystemExit("LOCAL_DATA_DIR must be inside the QA evidence directory")
sys.path.insert(0, str(ROOT / "backend"))
from app.context.store import update_session

API = os.environ.get("QA_API_URL", "http://localhost:8000")
NEW = ["youtube_vlog", "threads", "naver_kin", "cook82"]
sessions = {}
for name, words, channels in [
    ("QA 채널 확장", ["에어컨 청소", "제습기", "qa-empty"], NEW),
    ("QA 빈 결과", ["qa-empty"], NEW),
    ("QA 샘플", ["에어컨 청소"], ["fixture"]),
]:
    context = {
        "bk": name,
        "oneLiner": "생활 가전 사용 경험을 조사하는 QA 프로젝트",
        "researchQuestion": {"text": "생활 가전을 사용하는 경험은 어떠한가?"},
        "projectType": {"choice": "new"},
        "taskMode": "explore",
        "constraints": [],
        "channels": channels,
        "productCategory": {"l1": "생활가전", "source": "user"},
    }
    request = Request(API + "/context",
                      data=json.dumps(context, ensure_ascii=False).encode(),
                      headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=10) as response:
        created = json.load(response)
    sid = created["sid"]
    keywords = [
        {"id": f"qa-{i}", "kw": word, "text": word, "axis": "생활",
         "sub": "가전", "status": "approved", "round": 1}
        for i, word in enumerate(words, 1)
    ]
    update_session(sid, {
        "step": "crawling", "keywords": keywords, "allKw": keywords,
        "crawlConfig": {"channels": channels},
    }, confirm_stage="stage1")
    sessions[name] = {"sid": sid, "keywords": words, "channels": channels}
    (QA / "seed-sessions.json").write_text(
        json.dumps(sessions, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"name": name, **sessions[name]}, ensure_ascii=False))
