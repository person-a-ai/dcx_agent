import json
import numpy as np
from datetime import datetime

from app.services.s3 import load_data, load_json, save_jsonl, save_json
from app.utils.text import get_text
from app.config import settings
from app.jobs.manager import job_manager

# ── 06 산출 계약 (resources/DCX_STEP07-11_개발안_데이터계약.md §2) ──
#
# alpha 는 "이 정도 오류는 감수한다"는 목표 오류율이고, 검수량을 정하는
# **입력**이다. escalate_threshold 는 거기서 계산되는 **출력**이라
# 사람이 직접 만지지 않는다 — 임계를 직접 돌리면 alpha 가 뜻을 잃고,
# 같은 alpha 로 돌린 두 run 을 비교할 수 없게 된다.
#
# 점수가 0.5 근처일수록 모델이 헷갈린 것이다. 그 언저리를 사람에게
# 넘기고, 바깥쪽은 자동 판정한다. alpha 가 작을수록(엄격할수록)
# 넘기는 구간이 넓어진다.
#
# 아래 두 앵커는 계약의 worked example(alpha 0.03 → 0.62)에 맞춰
# 잡은 **잠정값**이다. 실제 보정은 T8 에서 홀드아웃 데이터로 다시 잡는다.
DEFAULT_ALPHA = 0.03
_ALPHA_STRICT, _BAND_STRICT = 0.01, 0.18   # 엄격 — 넓게 넘긴다
_ALPHA_LOOSE, _BAND_LOOSE = 0.10, 0.05     # 느슨 — 좁게 넘긴다


def escalate_threshold_for(alpha: float) -> float:
    """목표 오류율 alpha 에서 사람에게 넘길 구간의 위쪽 경계를 구한다.

    밴드는 0.5 를 중심으로 대칭이다 — 위 경계가 t 면 아래 경계는 1 − t.
    alpha 를 로그 축에서 선형 보간한다. 0.01 과 0.10 은 한 자릿수 차이인데
    선형 축에서 보간하면 그 사이가 거의 평평해져 alpha 를 조절하는 의미가
    사라지기 때문이다.
    """
    import math

    a = min(max(float(alpha), _ALPHA_STRICT), _ALPHA_LOOSE)
    t = ((math.log10(a) - math.log10(_ALPHA_STRICT))
         / (math.log10(_ALPHA_LOOSE) - math.log10(_ALPHA_STRICT)))
    band = _BAND_STRICT + t * (_BAND_LOOSE - _BAND_STRICT)
    return round(0.5 + band, 2)


def decide(score: float, threshold: float) -> tuple[str, int]:
    """한 문서의 판정. (decision, label) 을 돌려준다.

    밴드 안이면 escalated 지만 **잠정 라벨은 붙인다** — 사람이 보기 전에도
    파이프라인은 돌아야 하고, 멈춰 세우면 검수가 병목이 된다.
    """
    if score >= threshold or score <= 1 - threshold:
        return "auto", int(score >= 0.5)
    return "escalated", int(score >= 0.5)


def classify_records(rows: list[dict], scores, alpha: float = DEFAULT_ALPHA):
    """예측 점수로 레코드에 decision·label·reviewed_by 를 붙인다.

    임계를 인자로 받지 않는다 — alpha 에서만 나온다.
    입력 레코드는 건드리지 않는다.
    """
    threshold = escalate_threshold_for(alpha)
    out: list[dict] = []
    counts = {"total": len(rows), "auto": 0, "escalated": 0, "human": 0}

    for rec, score in zip(rows, scores):
        score = float(score)
        decision, label = decide(score, threshold)
        item = dict(rec)
        item["relevance_score"] = score     # 기존 필드 — 그대로 둔다
        item["decision"] = decision
        item["label"] = label
        item["reviewed_by"] = None          # 사람이 볼 때만 채운다
        counts[decision] += 1
        out.append(item)

    return out, counts


def build_run_sidecar(alpha: float, counts: dict, model_scores: dict,
                      calibration: dict) -> dict:
    """classified/{sid}/run_{ts}.json — 이 run 을 재현하는 데 필요한 값.

    예전에는 모델 점수·앙상블·총계가 job 상태로만 남아 서버를 재시작하면
    사라졌다. 07~11 이 "어떤 판정 기준으로 걸러진 근거인가"를 되짚을 수
    있어야 해서 파일로 남긴다.
    """
    scores = {k: round(float(v), 3) for k, v in (model_scores or {}).items()}
    combined = round(sum(scores.values()) / len(scores), 3) if scores else 0.0
    return {
        "alpha": alpha,
        "escalate_threshold": escalate_threshold_for(alpha),
        "calibration": calibration or {},
        "ensemble": {"models": list(scores), "scores": scores, "combined": combined},
        "counts": counts or {},
    }


def build_calibration(scores, labels, alpha: float = DEFAULT_ALPHA) -> dict:
    """라벨이 있는 표본에서 모델과 사람이 얼마나 일치했는지 센다."""
    threshold = escalate_threshold_for(alpha)
    n = min(len(scores), len(labels))
    disagreements = sum(
        1 for i in range(n) if decide(float(scores[i]), threshold)[1] != int(labels[i])
    )
    return {
        "n": n,
        "agreement": round((n - disagreements) / n, 3) if n else 0.0,
        "disagreements": disagreements,
    }


def finish_classification(sid, all_data, ensemble, model_scores, phase,
                          train_scores=None, train_labels=None,
                          alpha: float = DEFAULT_ALPHA) -> None:
    """판정 → 저장 → 사이드카 → job 상태. 두 학습 경로가 함께 쓴다.

    relevant/irrelevant 분리는 label 로 한다 — escalated 도 잠정 라벨이
    있으므로 검수를 기다리며 파이프라인이 멈추지 않는다.
    """
    rows, counts = classify_records(all_data, ensemble, alpha=alpha)
    relevant = [r for r in rows if r["label"] == 1]
    irrelevant = [r for r in rows if r["label"] == 0]

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_jsonl(f"classified/{sid}/relevant_{ts}.jsonl", relevant)
    save_jsonl(f"classified/{sid}/irrelevant_{ts}.jsonl", irrelevant)

    calibration = (build_calibration(train_scores, train_labels, alpha)
                   if train_scores is not None and train_labels is not None else {})
    sidecar = build_run_sidecar(alpha, counts, model_scores, calibration)
    save_json(f"classified/{sid}/run_{ts}.json", sidecar)

    job_manager.set("train", sid, {
        "status": "done", "progress": 100, "phase": phase,
        "total": len(all_data), "relevant": len(relevant), "irrelevant": len(irrelevant),
        "scores": sidecar["ensemble"]["scores"],
        "models": sidecar["ensemble"]["models"],
        "alpha": alpha,
        "escalate_threshold": sidecar["escalate_threshold"],
        "counts": counts,
        "run": f"classified/{sid}/run_{ts}.json",
    })


def train_models(config: dict) -> None:
    """3중 준지도 학습: LSTM + CNN + GRU + LLM 앙상블"""
    sid = config.get("sid", "s0")
    job_manager.set("train", sid, {"status": "running", "phase": "init", "progress": 0})

    try:
        # Load labeled data from session
        labeled = []
        try:
            session = load_json(f"sessions/{sid}/session.json")
            if session:
                labeled = session.get("labeledData", [])
        except Exception:
            pass

        if len(labeled) < 5:
            job_manager.set("train", sid, {"status": "error", "error": "Need at least 5 labeled samples"})
            return

        texts = [get_text(d) for d in labeled]
        labels = [1 if d.get("label") == "relevant" or d.get("label") == 1 else 0 for d in labeled]

        job_manager.update("train", sid, progress=10, phase="preparing")

        # Try tensorflow first, fallback to sklearn
        use_tf = False
        try:
            import tensorflow as tf
            from tensorflow.keras.preprocessing.text import Tokenizer
            from tensorflow.keras.preprocessing.sequence import pad_sequences
            from tensorflow.keras.models import Sequential
            from tensorflow.keras.layers import (
                Embedding, LSTM, GRU, Conv1D, GlobalMaxPooling1D, Dense, Dropout,
            )
            use_tf = True
        except ImportError:
            pass

        alpha = float(config.get("alpha", DEFAULT_ALPHA))
        if use_tf:
            _train_tensorflow(sid, texts, labels, alpha)
        else:
            _train_sklearn(sid, texts, labels, alpha)

    except Exception as e:
        job_manager.set("train", sid, {"status": "error", "error": str(e)})


def _train_tensorflow(sid: str, texts: list[str], labels: list[int],
                      alpha: float = DEFAULT_ALPHA) -> None:
    import tensorflow as tf
    from tensorflow.keras.preprocessing.text import Tokenizer
    from tensorflow.keras.preprocessing.sequence import pad_sequences
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import (
        Embedding, LSTM, GRU, Conv1D, GlobalMaxPooling1D, Dense, Dropout,
    )

    MAX_WORDS = 10000
    MAX_LEN = 200

    tokenizer = Tokenizer(num_words=MAX_WORDS, oov_token="<OOV>")
    tokenizer.fit_on_texts(texts)
    sequences = tokenizer.texts_to_sequences(texts)
    X = pad_sequences(sequences, maxlen=MAX_LEN, padding="post", truncating="post")
    y = np.array(labels)

    job_manager.update("train", sid, progress=20, phase="LSTM")

    # Model 1: LSTM
    m1 = Sequential([
        Embedding(MAX_WORDS, 128, input_length=MAX_LEN),
        LSTM(64, dropout=0.2, recurrent_dropout=0.2),
        Dense(32, activation="relu"), Dropout(0.5), Dense(1, activation="sigmoid"),
    ])
    m1.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
    m1.fit(X, y, epochs=5, batch_size=32, verbose=0)
    s1 = m1.evaluate(X, y, verbose=0)[1]

    job_manager.update("train", sid, progress=40, phase="CNN")

    # Model 2: CNN
    m2 = Sequential([
        Embedding(MAX_WORDS, 128, input_length=MAX_LEN),
        Conv1D(64, 5, activation="relu"), GlobalMaxPooling1D(),
        Dense(32, activation="relu"), Dropout(0.5), Dense(1, activation="sigmoid"),
    ])
    m2.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
    m2.fit(X, y, epochs=5, batch_size=32, verbose=0)
    s2 = m2.evaluate(X, y, verbose=0)[1]

    job_manager.update("train", sid, progress=60, phase="GRU")

    # Model 3: GRU
    m3 = Sequential([
        Embedding(MAX_WORDS, 128, input_length=MAX_LEN),
        GRU(64, dropout=0.2, recurrent_dropout=0.2),
        Dense(32, activation="relu"), Dropout(0.5), Dense(1, activation="sigmoid"),
    ])
    m3.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
    m3.fit(X, y, epochs=5, batch_size=32, verbose=0)
    s3_score = m3.evaluate(X, y, verbose=0)[1]

    job_manager.update("train", sid, progress=80, phase="classifying")

    all_data = load_data(f"preprocessed/{sid}/")
    if all_data:
        all_texts = [get_text(d) for d in all_data]
        all_seq = tokenizer.texts_to_sequences(all_texts)
        X_all = pad_sequences(all_seq, maxlen=MAX_LEN, padding="post", truncating="post")

        p1 = m1.predict(X_all, verbose=0).flatten()
        p2 = m2.predict(X_all, verbose=0).flatten()
        p3 = m3.predict(X_all, verbose=0).flatten()
        ensemble = (p1 + p2 + p3) / 3

        train_pred = (m1.predict(X, verbose=0).flatten()
                      + m2.predict(X, verbose=0).flatten()
                      + m3.predict(X, verbose=0).flatten()) / 3
        finish_classification(
            sid, all_data, ensemble,
            {"LSTM": s1, "CNN": s2, "GRU": s3_score},
            "complete", train_pred, y, alpha)
    else:
        job_manager.set("train", sid, {"status": "error", "error": "No preprocessed data"})


def _train_sklearn(sid: str, texts: list[str], labels: list[int],
                   alpha: float = DEFAULT_ALPHA) -> None:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.model_selection import cross_val_score

    vec = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
    X = vec.fit_transform(texts)
    y = np.array(labels)

    job_manager.update("train", sid, progress=20, phase="LogisticRegression")

    m1 = LogisticRegression(max_iter=500, C=1.0)
    s1 = cross_val_score(m1, X, y, cv=min(3, len(y)), scoring="accuracy").mean()
    m1.fit(X, y)

    job_manager.update("train", sid, progress=40, phase="RandomForest")

    m2 = RandomForestClassifier(n_estimators=100, random_state=42)
    s2 = cross_val_score(m2, X, y, cv=min(3, len(y)), scoring="accuracy").mean()
    m2.fit(X, y)

    job_manager.update("train", sid, progress=60, phase="GradientBoosting")

    m3 = GradientBoostingClassifier(n_estimators=100, random_state=42)
    s3_score = cross_val_score(m3, X, y, cv=min(3, len(y)), scoring="accuracy").mean()
    m3.fit(X, y)

    job_manager.update("train", sid, progress=80, phase="classifying")

    all_data = load_data(f"preprocessed/{sid}/")
    if all_data:
        all_texts = [get_text(d) for d in all_data]
        X_all = vec.transform(all_texts)
        p1 = m1.predict_proba(X_all)[:, 1]
        p2 = m2.predict_proba(X_all)[:, 1]
        p3 = m3.predict_proba(X_all)[:, 1]
        ensemble = (p1 + p2 + p3) / 3

        train_pred = (m1.predict_proba(X)[:, 1] + m2.predict_proba(X)[:, 1]
                      + m3.predict_proba(X)[:, 1]) / 3
        finish_classification(
            sid, all_data, ensemble,
            {"LogisticRegression": s1, "RandomForest": s2, "GradientBoosting": s3_score},
            "complete (sklearn fallback)", train_pred, y, alpha)
    else:
        job_manager.set("train", sid, {"status": "error", "error": "No preprocessed data"})
