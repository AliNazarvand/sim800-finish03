import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from capabilities.audit import audit, conflicts_report


def test_audit_returns_rows():
    root = Path(__file__).resolve().parents[2]
    rows = audit(root)
    assert len(rows) > 0
    assert {"model", "field_path", "status"} <= set(rows[0].keys())


def test_conflicts_report_empty_is_list():
    root = Path(__file__).resolve().parents[2]
    rows = conflicts_report(root)
    assert isinstance(rows, list)