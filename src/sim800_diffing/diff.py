"""Version-aware dataset diffing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_commands(path: Path) -> dict[str, dict[str, Any]]:
    """Index command JSONL by canonical command name."""
    result: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            item = json.loads(line)
            key = str(item.get("command", item.get("command_text", ""))).strip()
            if key:
                result[key] = item
    return result


def diff_commands(old: Path, new: Path) -> dict[str, list[str]]:
    """Return added, removed and changed command identifiers."""
    left, right = load_commands(old), load_commands(new)
    added = sorted(set(right) - set(left))
    removed = sorted(set(left) - set(right))
    changed = sorted(k for k in set(left) & set(right) if left[k] != right[k])
    return {"added": added, "removed": removed, "changed": changed}


def write_diff(old: Path, new: Path, output: Path) -> dict[str, list[str]]:
    """Write a machine-readable diff artifact."""
    result = diff_commands(old, new)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"old": old.name, "new": new.name, **result}, indent=2) + "\n", encoding="utf-8")
    return result
