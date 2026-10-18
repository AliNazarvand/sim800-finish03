import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from capabilities.query import find, get_path, list_models, resolve_model


def test_list_models():
    root = Path(__file__).resolve().parents[2]
    rows = list_models(root)
    assert len(rows) == 9
    assert all("model" in r and "family" in r for r in rows)


def test_find():
    root = Path(__file__).resolve().parents[2]
    hits = find(root, "sim808")
    assert any(h["model"] == "SIM808" for h in hits)


def test_resolve_and_get():
    root = Path(__file__).resolve().parents[2]
    doc = resolve_model(root, "SIM800")
    assert doc is not None
    fv = get_path(doc, "capabilities.bands.type")
    assert fv["value"] == "quad-band"