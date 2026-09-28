"""T5 · 06 산출 계약.

계획: docs/development/dcx-step07-11/03-plan.md P0/T5
  RED 레코드에 decision·label·reviewed_by
      사이드카 classified/{sid}/run_{ts}.json 에
      alpha·escalate_threshold·calibration·ensemble·counts
  RED escalate_threshold 는 alpha 에서 계산된다 —
      같은 alpha 면 같은 임계, 직접 주입 불가
  수용 기준 기존 relevance_score 유지 · 0.5 하드코딩 제거
"""
import pytest

from app.services.training import (
    escalate_threshold_for, decide, classify_records, build_run_sidecar,
    DEFAULT_ALPHA,
)


# ── escalate_threshold 는 alpha 에서 나온다 ────────────────────

def test_same_alpha_gives_the_same_threshold():
    assert escalate_threshold_for(0.03) == escalate_threshold_for(0.03)


def test_threshold_matches_the_worked_example_in_the_contract():
    """계약 §2.2 예시: alpha 0.03 → escalate_threshold 0.62"""
    assert escalate_threshold_for(0.03) == 0.62


def test_stricter_alpha_escalates_more():
    """오류를 덜 허용할수록 사람이 볼 구간이 넓어져야 한다."""
    assert escalate_threshold_for(0.01) > escalate_threshold_for(0.10)


def test_threshold_stays_above_the_midpoint_and_below_one():
    for a in (0.001, 0.01, 0.03, 0.10, 0.5, 1.0):
        t = escalate_threshold_for(a)
        assert 0.5 < t < 1.0, (a, t)


def test_threshold_is_clamped_outside_the_calibrated_range():
    assert escalate_threshold_for(0.0) == escalate_threshold_for(0.001)
    assert escalate_threshold_for(0.9) == escalate_threshold_for(0.5)


def test_threshold_cannot_be_injected_directly():
    """사람이 임계를 직접 만지면 alpha 가 뜻을 잃는다."""
    import inspect
    sig = inspect.signature(classify_records)
    assert "escalate_threshold" not in sig.parameters
    assert "alpha" in sig.parameters


# ── decide — auto / escalated ─────────────────────────────────

def test_confident_high_score_is_auto_relevant():
    d, label = decide(0.95, threshold=0.62)
    assert (d, label) == ("auto", 1)


def test_confident_low_score_is_auto_irrelevant():
    d, label = decide(0.05, threshold=0.62)
    assert (d, label) == ("auto", 0)


def test_the_uncertain_band_is_escalated():
    for p in (0.39, 0.50, 0.61):
        d, _ = decide(p, threshold=0.62)
        assert d == "escalated", p


def test_the_band_is_symmetric_around_the_midpoint():
    """0.62 가 위쪽 경계면 아래쪽 경계는 0.38 이다."""
    assert decide(0.62, 0.62)[0] == "auto"
    assert decide(0.38, 0.62)[0] == "auto"
    assert decide(0.6199, 0.62)[0] == "escalated"
    assert decide(0.3801, 0.62)[0] == "escalated"


def test_escalated_still_gets_a_provisional_label():
    """사람이 보기 전에도 파이프라인은 돌아야 한다."""
    assert decide(0.61, 0.62)[1] == 1
    assert decide(0.39, 0.62)[1] == 0


# ── 레코드 ────────────────────────────────────────────────────

def _rows(n=4):
    return [{"doc_id": f"d_{i}", "title": f"t{i}", "desc": "d"} for i in range(n)]


def test_records_carry_decision_label_reviewed_by():
    out, _ = classify_records(_rows(4), [0.95, 0.61, 0.05, 0.39], alpha=0.03)
    for r in out:
        assert r["decision"] in ("auto", "escalated", "human")
        assert r["label"] in (0, 1)
        assert "reviewed_by" in r


def test_reviewed_by_is_none_until_a_person_looks():
    out, _ = classify_records(_rows(2), [0.95, 0.61], alpha=0.03)
    assert all(r["reviewed_by"] is None for r in out)


def test_relevance_score_is_kept():
    """수용 기준: 기존 필드를 유지한다."""
    out, _ = classify_records(_rows(1), [0.87], alpha=0.03)
    assert out[0]["relevance_score"] == pytest.approx(0.87)


def test_existing_fields_survive():
    src = [{"doc_id": "d_1", "title": "t", "desc": "d", "kw": "심박",
            "author_hash": "a_35153ba5", "date": "2026-05-02"}]
    out, _ = classify_records(src, [0.9], alpha=0.03)
    assert set(out[0]) >= set(src[0])


def test_counts_add_up():
    out, counts = classify_records(_rows(4), [0.95, 0.61, 0.05, 0.39], alpha=0.03)
    assert counts["total"] == 4
    assert counts["auto"] + counts["escalated"] + counts["human"] == 4
    assert counts["auto"] == 2 and counts["escalated"] == 2


def test_no_hardcoded_half_threshold():
    """0.5 하드코딩 제거 — alpha 를 바꾸면 판정이 바뀐다."""
    scores = [0.61] * 4
    strict = classify_records(_rows(4), scores, alpha=0.01)[1]
    loose = classify_records(_rows(4), scores, alpha=0.10)[1]
    assert strict["escalated"] != loose["escalated"]


def test_does_not_mutate_the_input_rows():
    src = _rows(1)
    classify_records(src, [0.9], alpha=0.03)
    assert "decision" not in src[0]


# ── 사이드카 ──────────────────────────────────────────────────

def test_sidecar_has_every_section_the_contract_names():
    side = build_run_sidecar(
        alpha=0.03,
        counts={"total": 4, "auto": 2, "escalated": 2, "human": 0},
        model_scores={"LSTM": 0.887, "CNN": 0.862, "GRU": 0.879},
        calibration={"n": 412, "agreement": 0.93, "disagreements": 29},
    )
    for k in ("alpha", "escalate_threshold", "calibration", "ensemble", "counts"):
        assert k in side, k
    assert set(side["ensemble"]) >= {"models", "scores", "combined"}


def test_sidecar_threshold_comes_from_its_own_alpha():
    side = build_run_sidecar(alpha=0.10, counts={}, model_scores={}, calibration={})
    assert side["escalate_threshold"] == escalate_threshold_for(0.10)


def test_sidecar_lists_the_models_that_actually_ran():
    side = build_run_sidecar(alpha=DEFAULT_ALPHA, counts={},
                             model_scores={"LSTM": 0.9, "CNN": 0.8}, calibration={})
    assert side["ensemble"]["models"] == ["LSTM", "CNN"]
    assert side["ensemble"]["combined"] == pytest.approx(0.85)


# ── 저장까지 — 사이드카가 실제로 떨어지는가 ────────────────────

def test_finish_classification_writes_records_and_the_sidecar(monkeypatch):
    import app.services.training as T

    jsonl: dict[str, list] = {}
    js: dict[str, dict] = {}
    monkeypatch.setattr(T, "save_jsonl", lambda k, v: jsonl.__setitem__(k, v))
    monkeypatch.setattr(T, "save_json", lambda k, v: js.__setitem__(k, v))
    monkeypatch.setattr(T.job_manager, "set", lambda *a, **k: None)

    rows = [{"doc_id": f"d_{i}"} for i in range(4)]
    T.finish_classification(
        "s1", rows, [0.95, 0.61, 0.05, 0.39],
        {"LSTM": 0.887, "CNN": 0.862, "GRU": 0.879},
        "complete", [0.9, 0.2], [1, 0], alpha=0.03)

    rel = next(v for k, v in jsonl.items() if "relevant_" in k and "irrelevant" not in k)
    irr = next(v for k, v in jsonl.items() if "irrelevant_" in k)
    assert len(rel) == 2 and len(irr) == 2
    assert all("decision" in r and "label" in r and "reviewed_by" in r for r in rel + irr)

    side = next(v for k, v in js.items() if "/run_" in k)
    assert side["alpha"] == 0.03
    assert side["escalate_threshold"] == 0.62
    assert side["counts"]["total"] == 4
    assert side["ensemble"]["models"] == ["LSTM", "CNN", "GRU"]
    assert side["calibration"]["n"] == 2


def test_escalated_documents_still_reach_the_next_step(monkeypatch):
    """검수를 기다리며 파이프라인이 멈추면 검수가 병목이 된다."""
    import app.services.training as T
    jsonl: dict[str, list] = {}
    monkeypatch.setattr(T, "save_jsonl", lambda k, v: jsonl.__setitem__(k, v))
    monkeypatch.setattr(T, "save_json", lambda k, v: None)
    monkeypatch.setattr(T.job_manager, "set", lambda *a, **k: None)

    T.finish_classification("s1", [{"doc_id": "d_1"}], [0.61], {"LSTM": 0.9},
                            "complete", alpha=0.03)
    rel = next(v for k, v in jsonl.items() if "relevant_" in k and "irrelevant" not in k)
    assert len(rel) == 1
    assert rel[0]["decision"] == "escalated"
    assert rel[0]["label"] == 1


def test_train_request_takes_alpha_not_a_threshold():
    from app.models.schemas import TrainRequest
    assert TrainRequest().alpha == 0.03
    assert "escalate_threshold" not in TrainRequest.model_fields
