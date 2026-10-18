import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from capabilities.validator import validate


def test_data_integrity_passes():
    root = Path(__file__).resolve().parents[2]
    errors = validate(root)
    assert errors == [], "Validation errors:\n" + "\n".join(errors)


def test_all_models_are_parseable():
    import yaml
    root = Path(__file__).resolve().parents[2]
    scope = yaml.safe_load((root / "data" / "capabilities" / "scope.yaml").read_text(encoding="utf-8"))
    for m in scope["models"]:
        p = root / "data" / "capabilities" / "models" / f"{m.lower()}.yaml"
        assert p.exists(), f"missing model file for {m}"
        doc = yaml.safe_load(p.read_text(encoding="utf-8"))
        assert doc["model"] == m
        assert "capabilities" in doc
        assert "power" in doc["capabilities"]
        assert "current_consumption" in doc["capabilities"]["power"]