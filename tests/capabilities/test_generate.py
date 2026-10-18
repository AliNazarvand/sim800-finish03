import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from capabilities.generate import generate


def test_generate_hashes():
    root = Path(__file__).resolve().parents[2]
    doc = generate(root)
    assert doc["generated"] is True
    assert len(doc["content_hash"]) == 64
    assert len(doc["scope_hash"]) == 64
    assert len(doc["models"]) == 9