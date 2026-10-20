from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_flask_prototype_removed():
    assert not (ROOT / 'workflow.py').exists()
