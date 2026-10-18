"""Inspect external datasheets without copying copyrighted PDFs into release data."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path


def inspect(path: Path) -> dict[str, object]:
    """Return safe metadata from pdfinfo."""
    proc = subprocess.run(["pdfinfo", str(path)], text=True, capture_output=True, check=False)
    fields: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    return {
        "file": path.name,
        "size_bytes": path.stat().st_size,
        "healthy": proc.returncode == 0,
        "pages": fields.get("Pages"),
        "encrypted": fields.get("Encrypted"),
    }


def main() -> int:
    """Write datasheet availability and health report."""
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, default=Path("data/validation/pdf_health.json"))
    args = parser.parse_args()
    files = sorted(p for p in args.directory.rglob("*") if p.suffix.lower() == ".pdf")
    report = {"checked_at": datetime.now(UTC).isoformat(), "count": len(files), "files": [inspect(p) for p in files]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
