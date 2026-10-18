import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from capabilities.validator import validate


def test_valid_database():
    root = Path(__file__).resolve().parents[2]
    errors = validate(root)
    assert errors == [], "Validation errors:\n" + "\n".join(errors)