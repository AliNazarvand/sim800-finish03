"""Command-line interface for the SIM800 platform."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from capabilities.cli import main as capabilities_main
from sim800_diffing import write_diff
from sim800_validation import validate_directory


def main(argv: list[str] | None = None) -> int:
    """Run the platform CLI."""
    parser = argparse.ArgumentParser(prog="sim800")
    sub = parser.add_subparsers(dest="action", required=True)
    check = sub.add_parser("validate", help="validate JSONL products")
    check.add_argument("--dataset-dir", type=Path, default=Path("dataset"))
    check.add_argument("--schema-dir", type=Path, default=Path("data/schemas"))
    check.add_argument("--quarantine-dir", type=Path, default=Path("data/quarantine"))
    capabilities = sub.add_parser("capabilities", help="query and validate hardware capabilities")
    capabilities.add_argument("args", nargs=argparse.REMAINDER)
    diff = sub.add_parser("diff", help="compare two command products")
    diff.add_argument("old", type=Path)
    diff.add_argument("new", type=Path)
    diff.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.action == "capabilities":
        return capabilities_main(args.args)
    if args.action == "validate":
        reports = validate_directory(args.dataset_dir, args.schema_dir, args.quarantine_dir)
        print(json.dumps(reports, indent=2))
        return 1 if any(r["invalid"] for r in reports) else 0
    result = write_diff(args.old, args.new, args.output)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
