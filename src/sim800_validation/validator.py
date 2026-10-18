"""Schema and domain validation for dataset products."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator


def validate_jsonl(dataset: Path, schema: Path, quarantine: Path | None = None) -> dict[str, Any]:
    """Validate every JSONL record and return deterministic QA metrics."""
    contract = json.loads(schema.read_text(encoding="utf-8"))
    Draft7Validator.check_schema(contract)
    validator = Draft7Validator(contract)
    valid = invalid = 0
    errors: list[dict[str, Any]] = []
    for number, line in enumerate(dataset.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
            problems = sorted(validator.iter_errors(record), key=lambda e: list(e.path))
            if problems:
                invalid += 1
                errors.append({"line": number, "errors": [e.message for e in problems]})
                if quarantine:
                    quarantine.parent.mkdir(parents=True, exist_ok=True)
                    with quarantine.open("a", encoding="utf-8") as handle:
                        handle.write(
                            json.dumps(
                                {"line": number, "record": record, "errors": errors[-1]["errors"]}, ensure_ascii=False
                            )
                            + "\n"
                        )
            else:
                valid += 1
        except (json.JSONDecodeError, TypeError) as exc:
            invalid += 1
            errors.append({"line": number, "errors": [str(exc)]})
    return {
        "dataset": str(dataset),
        "schema": str(schema),
        "valid": valid,
        "invalid": invalid,
        "total": valid + invalid,
        "errors": errors,
    }


def validate_directory(dataset_dir: Path, schema_dir: Path, quarantine_dir: Path | None = None) -> list[dict[str, Any]]:
    """Validate all products for which a matching schema exists."""
    reports = []
    for dataset in sorted(dataset_dir.glob("*.jsonl")):
        schema = schema_dir / f"{dataset.stem}.schema.json"
        if schema.exists() and schema.stat().st_size > 0:
            reports.append(validate_jsonl(dataset, schema, (quarantine_dir / dataset.name) if quarantine_dir else None))
    return reports
