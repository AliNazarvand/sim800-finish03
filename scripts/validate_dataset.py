"""Validate every dataset product against its JSON Schema."""

import json
from pathlib import Path

from sim800_validation import validate_directory


def main() -> int:
    """Run validation and write a machine-readable report."""
    root = Path(__file__).resolve().parents[1]
    reports = validate_directory(root / "dataset", root / "data/schemas", root / "data/quarantine")
    (root / "data/validation/dataset_validation.json").write_text(
        json.dumps(reports, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(reports, indent=2))
    return 1 if any(item["invalid"] for item in reports) else 0


if __name__ == "__main__":
    raise SystemExit(main())
