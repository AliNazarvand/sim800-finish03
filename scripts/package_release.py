"""Create release archives, a SHA-256 manifest, and retain local Git history."""

from __future__ import annotations

import hashlib
import tarfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path


def main() -> int:
    """Package source and local history while excluding PDFs and caches."""
    root = Path(__file__).resolve().parents[1]
    out = root.parent
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    manifest = root / "MANIFEST.txt"
    excluded = {
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "data/backup",
        "data/tmp",
        "data/quarantine",
    }
    files = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if path == manifest or path.suffix.lower() == ".pdf":
            continue
        if any(str(rel) == item or str(rel).startswith(item + "/") for item in excluded):
            continue
        files.append((path, rel))
    manifest_lines = []
    for path, rel in files:
        if str(rel) == ".git" or str(rel).startswith(".git/"):
            continue
        manifest_lines.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {rel}")
    manifest.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    files.append((manifest, manifest.relative_to(root)))
    zip_path = out / f"sim800-platform-all-{stamp}.zip"
    tar_path = out / f"sim800-platform-all-{stamp}.tar.gz"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path, rel in files:
            archive.write(path, Path(root.name) / rel)
    with tarfile.open(tar_path, "w:gz") as archive:
        for path, rel in files:
            archive.add(path, arcname=Path(root.name) / rel)
    print(zip_path)
    print(tar_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
