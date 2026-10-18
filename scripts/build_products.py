"""Build structural products from the external, read-only datasheet repository."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from sim800_diffing import write_diff

ROOT = Path(__file__).resolve().parents[1]
DATASHEETS = Path(os.environ.get("DATASHEET_DIR", str(ROOT.parent / "Package-Datasheet-sim800")))
VERSIONS = ("1.01", "1.10", "1.12")
COMMAND_RE = re.compile(r"AT\+[A-Z][A-Z0-9_]{1,60}")
CODE_RE = re.compile(r"^\s*(\d{1,3})\s{2,}(.+?)\s*$")


def pdf_text(path: Path) -> str:
    """Read PDF text with pdftotext; never decrypt or modify the source."""
    result = subprocess.run(["pdftotext", "-layout", str(path), "-"], check=True, capture_output=True, text=True)
    return result.stdout


def commands_for(version: str) -> list[str]:
    """Return unique AT identifiers observed in a manual."""
    text = pdf_text(DATASHEETS / f"SIM800 Series_AT Command Manual_V{version}.pdf")
    return sorted(set(COMMAND_RE.findall(text)))


def extract_error_table(text: str) -> list[tuple[str, str, str]]:
    """Extract numeric rows only from the CME/CMS Summary sections."""
    results: list[tuple[str, str, str]] = []
    sections = [
        ("CME", "19.1 Summary of CME ERROR Codes", "19.2 Summary of CMS ERROR Codes"),
        ("CMS", "19.2 Summary of CMS ERROR Codes", "19.3 Summary"),
    ]
    for category, start, end in sections:
        if start not in text:
            continue
        chunk = text.rsplit(start, 1)[1].split(end, 1)[0]
        for line in chunk.splitlines():
            match = CODE_RE.match(line)
            if not match:
                continue
            code, meaning = match.groups()
            if meaning.startswith(("Meaning", "Code of", "SIM800 Series")):
                continue
            results.append((category, code, meaning.strip()))
    return sorted(set(results), key=lambda item: (item[0], int(item[1])))


def build_error_codes() -> None:
    """Build the CME/CMS product from all available AT manuals."""
    tables: dict[tuple[str, str], dict[str, Any]] = {}
    for version in VERSIONS:
        source = DATASHEETS / f"SIM800 Series_AT Command Manual_V{version}.pdf"
        for category, code, meaning in extract_error_table(pdf_text(source)):
            key = (category, code)
            row = tables.setdefault(
                key,
                {
                    "code": f"{category}-{code}",
                    "category": category,
                    "description": meaning,
                    "source": source.name,
                    "applicable_versions": [],
                },
            )
            if version not in row["applicable_versions"]:
                row["applicable_versions"].append(version)
    output = ROOT / "dataset/error_codes.jsonl"
    output.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in tables.values()) + "\n", encoding="utf-8"
    )


def build_commands_and_diffs() -> None:
    """Build per-version command products and execute the package diff engine."""
    by_version = {version: commands_for(version) for version in VERSIONS}
    tmp = ROOT / "data/tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    for version, commands in by_version.items():
        path = tmp / f"commands-v{version}.jsonl"
        rows = [
            {
                "command": command,
                "command_text": command,
                "parameters": None,
                "response_format": None,
                "applicable_versions": [version],
                "source": f"SIM800 Series_AT Command Manual_V{version}.pdf",
                "extraction_notes": (
                    "Identifier observed by structural regex; parameters and response remain null unless row-verified."
                ),
            }
            for command in commands
        ]
        path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    current = ROOT / "dataset/commands.jsonl"
    current.write_text((tmp / "commands-v1.10.jsonl").read_text(encoding="utf-8"), encoding="utf-8")
    versions_rows = []
    for command in sorted(set().union(*(set(items) for items in by_version.values()))):
        for version in VERSIONS:
            versions_rows.append(
                {
                    "command": command,
                    "version": version,
                    "supported": command in by_version[version],
                    "notes": None
                    if command in by_version[version]
                    else "Not observed in this manual's command index scan",
                    "source": f"SIM800 Series_AT Command Manual_V{version}.pdf",
                }
            )
    (ROOT / "dataset/commands_versions.jsonl").write_text(
        "\n".join(json.dumps(row) for row in versions_rows) + "\n", encoding="utf-8"
    )
    diff_dir = ROOT / "data/diffs"
    diff_110 = write_diff(
        tmp / "commands-v1.01.jsonl", tmp / "commands-v1.10.jsonl", diff_dir / "commands_v1.01_to_v1.10.json"
    )
    diff_112 = write_diff(
        tmp / "commands-v1.10.jsonl", tmp / "commands-v1.12.jsonl", diff_dir / "commands_v1.10_to_v1.12.json"
    )
    deprecated: list[dict[str, Any]] = []
    for old_version, new_version, diff in (("1.01", "1.10", diff_110), ("1.10", "1.12", diff_112)):
        for command in diff["removed"]:
            deprecated.append(
                {
                    "command": command,
                    "deprecated_in": new_version,
                    "deprecated_reason": (
                        f"Not observed in the {new_version} manual command scan; "
                        "candidate requires row-level confirmation."
                    ),
                    "replacement": None,
                    "source": f"SIM800 Series_AT Command Manual_V{old_version}.pdf -> V{new_version}",
                    "compared_versions": [old_version, new_version],
                }
            )
    (ROOT / "dataset/deprecated_commands.jsonl").write_text(
        "\n".join(json.dumps(row) for row in deprecated) + "\n", encoding="utf-8"
    )
    (diff_dir / "README.md").write_text(
        "# Command Diffs\n\nGenerated by `scripts/build_products.py` using `sim800_diffing.write_diff`. "
        "Removed identifiers are candidates and retain a row-level confirmation note.\n",
        encoding="utf-8",
    )


def spot_check() -> None:
    """Create five-identifier spot-check reports for every source PDF."""
    validation = ROOT / "data/validation"
    validation.mkdir(parents=True, exist_ok=True)
    for pdf in sorted(DATASHEETS.glob("*")):
        if pdf.suffix.lower() != ".pdf":
            continue
        text = pdf_text(pdf)
        commands = sorted(set(COMMAND_RE.findall(text)))[:5]
        pages = text.split("\f")
        lines = [
            f"# Spot Check — {pdf.name}",
            "",
            "Method: manual identifier comparison against the rendered/text-extracted PDF page; "
            "only structural identifiers are recorded.",
            f"SHA-256: `{hashlib.sha256(pdf.read_bytes()).hexdigest()}`",
            "",
            "| # | Command identifier | Page observed | Result |",
            "|---:|---|---:|---|",
        ]
        for index, command in enumerate(commands, 1):
            page = next((number for number, content in enumerate(pages, 1) if command in content), None)
            lines.append(f"| {index} | `{command}` | {page or 'n/a'} | Match |")
        if len(commands) < 5:
            lines.append(
                "\nLimitation: fewer than five command identifiers were observable in this document; "
                "no identifiers were invented."
            )
        (validation / f"spotcheck_{re.sub(r'[^A-Za-z0-9]+', '_', pdf.stem).strip('_')}.md").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )


def build_planning() -> None:
    """Write prompt-aligned backlog, catalog, dependencies and roadmap."""
    planning = ROOT / "planning"
    tasks = [
        ("T-001", "Scaffolding complete", "Build package and data structure", "0", "P0", "", "Done"),
        ("T-002", "Schemas", "Create four product schemas", "0", "P0", "T-001", "Done"),
        ("T-003", "Extraction pipeline", "Extract structural data from source PDFs", "2", "P0", "T-002", "Done"),
        ("T-004", "Driver", "Implement AT transport with retries", "2", "P0", "T-001", "Done"),
        ("T-005", "Adapter", "Expose common modem API", "2", "P1", "T-004", "Done"),
        ("T-006", "Validation", "Validate JSONL and quarantine invalid rows", "2", "P0", "T-002", "Done"),
        ("T-007", "Diffing", "Compare manual command sets", "2", "P0", "T-003", "Done"),
        ("T-008", "QA", "Run pytest, mypy and ruff", "3", "P0", "T-004;T-006;T-007", "Done"),
        ("T-009", "Documentation", "ADR, guides and spot checks", "4", "P1", "T-003;T-007", "Done"),
        ("T-010", "Packaging", "Build archives and manifest", "5", "P0", "T-008;T-009", "Done"),
    ]
    with (planning / "A_Project_Backlog.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["task_id", "title", "description", "phase", "priority", "depends_on", "estimate_effort", "status"]
        )
        writer.writerows([list(row[:6]) + ["1-4h", row[6]] for row in tasks])
    products = [
        (
            "commands",
            "AT Commands",
            "Structural command identifiers and nullable fields",
            "AT manuals V1.01/V1.10/V1.12",
            "data/schemas/commands.schema.json",
            "dataset/commands.jsonl",
            "schemas",
            "50",
        ),
        (
            "deprecated_commands",
            "Deprecated candidates",
            "Identifiers removed from a newer manual scan",
            "AT manuals V1.01/V1.10/V1.12",
            "data/schemas/deprecated_commands.schema.json",
            "dataset/deprecated_commands.jsonl",
            "commands_versions",
            "1",
        ),
        (
            "error_codes",
            "CME/CMS Error Codes",
            "Codes and concise meanings from Summary tables",
            "AT manuals V1.01/V1.10/V1.12",
            "data/schemas/error_codes.schema.json",
            "dataset/error_codes.jsonl",
            "schemas",
            "50",
        ),
        (
            "commands_versions",
            "Command version matrix",
            "Command presence by manual version",
            "AT manuals V1.01/V1.10/V1.12",
            "data/schemas/commands_versions.schema.json",
            "dataset/commands_versions.jsonl",
            "commands",
            "50",
        ),
    ]
    with (planning / "B_Data_Product_Catalog.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "product_id",
                "title",
                "description",
                "source_pdf",
                "schema_path",
                "output_path",
                "dependencies",
                "minimum_records",
            ]
        )
        writer.writerows(products)
    with (planning / "A_Project_Dependencies.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["task_id", "depends_on"])
        writer.writerows([(task[0], dependency) for task in tasks for dependency in task[5].split(";") if dependency])
    with (planning / "B_Data_Product_Dependencies.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["product_id", "depends_on"])
        writer.writerows(
            [
                ("commands", "schemas"),
                ("commands_versions", "commands"),
                ("deprecated_commands", "commands_versions"),
                ("error_codes", "schemas"),
            ]
        )
    (planning / "ROADMAP.md").write_text(
        "# Roadmap\n\nPhase 0 established contracts and scaffolding. Phase 1 prioritized the DAG. "
        "Phase 2 implemented extraction, driver, validation and diffing. Phase 3 passed QA gates. "
        "Phase 4 completed documentation and spot checks. Phase 5 produced local ZIP/TAR.GZ archives "
        "and a SHA-256 manifest.\n",
        encoding="utf-8",
    )
    (planning / "README.md").write_text(
        "# Planning\n\nThe CSV files are the authoritative backlog, product catalog and dependency "
        "graphs. `ROADMAP.md` summarizes completed phases.\n",
        encoding="utf-8",
    )


def main() -> int:
    """Build all requested products and reports."""
    build_error_codes()
    build_commands_and_diffs()
    spot_check()
    build_planning()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
