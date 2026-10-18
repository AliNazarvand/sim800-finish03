"""Run the seven release QA gates and persist evidence reports."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / "data/validation"
PRODUCTS = {
    "commands": (ROOT / "dataset/commands.jsonl", ROOT / "data/schemas/commands.schema.json"),
    "commands_versions": (
        ROOT / "dataset/commands_versions.jsonl",
        ROOT / "data/schemas/commands_versions.schema.json",
    ),
    "deprecated_commands": (
        ROOT / "dataset/deprecated_commands.jsonl",
        ROOT / "data/schemas/deprecated_commands.schema.json",
    ),
    "error_codes": (ROOT / "dataset/error_codes.jsonl", ROOT / "data/schemas/error_codes.schema.json"),
}


def rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def gate(name: str, checks: list[dict[str, Any]]) -> dict[str, Any]:
    result = {
        "gate": name,
        "status": "PASS" if all(item["status"] == "PASS" for item in checks) else "FAIL",
        "checks": checks,
    }
    safe = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    (VALIDATION / f"gate_{safe}.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (VALIDATION / f"gate_{safe}.md").write_text(
        f"# {name}\n\n**Status: {result['status']}**\n\n"
        + "\n".join(f"- **{item['name']}**: {item['status']} — {item['detail']}" for item in checks)
        + "\n",
        encoding="utf-8",
    )
    return result


def check(name: str, passed: bool, detail: str) -> dict[str, str]:
    return {"name": name, "status": "PASS" if passed else "FAIL", "detail": detail}


def main() -> int:
    VALIDATION.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []

    schema_checks = []
    for product, (data_path, schema_path) in PRODUCTS.items():
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        try:
            Draft7Validator.check_schema(schema)
            valid = sum(1 for row in rows(data_path) if not list(Draft7Validator(schema).iter_errors(row)))
            total = len(rows(data_path))
            schema_checks.append(check(product, valid == total, f"{valid}/{total} rows conform to Draft 7 schema"))
        except Exception as exc:  # pragma: no cover - release guard
            schema_checks.append(check(product, False, str(exc)))
    results.append(gate("Schema Conformance", schema_checks))

    counts = {name: len(rows(data_path)) for name, (data_path, _) in PRODUCTS.items()}
    results.append(
        gate(
            "Data Completeness",
            [
                check("commands", counts["commands"] >= 50, f"{counts['commands']} records; minimum 50"),
                check("error_codes", counts["error_codes"] >= 50, f"{counts['error_codes']} records; minimum 50"),
                check(
                    "deprecated_candidates",
                    counts["deprecated_commands"] == 43,
                    f"{counts['deprecated_commands']} candidates; expected 43",
                ),
                check(
                    "commands_versions",
                    counts["commands_versions"] >= counts["commands"],
                    f"{counts['commands_versions']} version rows",
                ),
            ],
        )
    )

    command_rows, version_rows, deprecated_rows, error_rows = (rows(PRODUCTS[key][0]) for key in PRODUCTS)
    command_names = {row["command"] for row in command_rows}
    supported = {row["command"] for row in version_rows if row.get("supported")}
    cross_checks = [
        check(
            "supported command references",
            command_names <= supported,
            f"{len(command_names & supported)}/{len(command_names)} command identifiers referenced by version matrix",
        ),
        check(
            "error categories",
            {row["category"] for row in error_rows} == {"CME", "CMS"},
            "both CME and CMS categories present",
        ),
        check(
            "deprecated provenance",
            all(row.get("compared_versions") and row.get("source") for row in deprecated_rows),
            "all candidates have compared versions and source",
        ),
        check(
            "diff artifacts",
            all(
                (ROOT / f"data/diffs/{name}").exists()
                for name in ("commands_v1.01_to_v1.10.json", "commands_v1.10_to_v1.12.json")
            ),
            "adjacent-version diff artifacts exist",
        ),
    ]
    results.append(gate("Cross-Reference", cross_checks))

    reproducible_targets = [PRODUCTS[key][0] for key in PRODUCTS] + [
        ROOT / "data/diffs/commands_v1.01_to_v1.10.json",
        ROOT / "data/diffs/commands_v1.10_to_v1.12.json",
    ]
    before = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in reproducible_targets}
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/build_products.py")], cwd=ROOT, check=True, stdout=subprocess.DEVNULL
    )
    after = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in reproducible_targets}
    results.append(
        gate(
            "Reproducibility",
            [
                check(
                    "rebuild hash stability",
                    before == after,
                    "product and diff hashes are unchanged after a clean rebuild",
                )
            ],
        )
    )

    try:
        import yaml  # type: ignore[import-not-found]

        workflow_checks = []
        for path in sorted((ROOT / ".github/workflows").glob("*.yml")):
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
            workflow_checks.append(check(path.name, bool(document and document.get("jobs")), "valid YAML with jobs"))
        precommit = yaml.safe_load((ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
        workflow_checks.append(
            check("pre-commit", bool(precommit and precommit.get("repos")), "valid YAML with repositories")
        )
    except Exception as exc:
        workflow_checks = [check("YAML configuration", False, str(exc))]
    results.append(gate("CI Syntax", workflow_checks))

    pdfs = list(ROOT.rglob("*.pdf")) + list(ROOT.rglob("*.PDF"))
    results.append(
        gate(
            "License Compliance",
            [
                check("no raw PDFs", not pdfs, f"{len(pdfs)} raw PDF files in release tree"),
                check(
                    "MIT license",
                    (ROOT / "LICENSE").read_text(encoding="utf-8").startswith("MIT License"),
                    "project license is MIT",
                ),
                check(
                    "license guidance",
                    (ROOT / "docs/LICENSE_COMPATIBILITY.md").exists(),
                    "compatibility guidance exists",
                ),
            ],
        )
    )

    results.append(
        gate(
            "License Compatibility",
            [
                check(
                    "source boundary",
                    "Package-Datasheet-sim800" in (ROOT / "data/raw/README.md").read_text(encoding="utf-8"),
                    "raw source policy documents external ownership",
                ),
                check(
                    "provenance",
                    all(row.get("source") for row in command_rows + deprecated_rows + error_rows),
                    "all populated product rows carry source provenance",
                ),
                check(
                    "no long-form source text",
                    all(
                        len(json.dumps(row, ensure_ascii=False)) < 2000
                        for row in command_rows + deprecated_rows + error_rows
                    ),
                    "records remain structural/concise",
                ),
            ],
        )
    )

    summary = {
        "status": "PASS" if all(result["status"] == "PASS" for result in results) else "FAIL",
        "gates": results,
        "counts": counts,
    }
    (VALIDATION / "qa_gates_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (VALIDATION / "qa_gates_summary.md").write_text(
        "# Final QA Gates\n\n"
        + "\n".join(f"- {result['gate']}: **{result['status']}**" for result in results)
        + f"\n\nOverall: **{summary['status']}**\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
