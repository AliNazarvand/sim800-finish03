"""Load YAML data files for the sim800-capabilities database."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

import yaml


def load_yaml(path: Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_scope(root: Path) -> dict[str, Any]:
    return cast(dict[str, Any], load_yaml(Path(root) / "data" / "capabilities" / "scope.yaml"))


def load_sources(root: Path) -> dict[str, Any]:
    return cast(dict[str, Any], load_yaml(Path(root) / "data" / "capabilities" / "sources.yaml"))


def load_out_of_scope(root: Path) -> dict[str, Any]:
    return cast(dict[str, Any], load_yaml(Path(root) / "data" / "capabilities" / "out-of-scope.yaml"))


def load_model(root: Path, model: str) -> dict[str, Any]:
    path = Path(root) / "data" / "capabilities" / "models" / f"{model.lower()}.yaml"
    return cast(dict[str, Any], load_yaml(path))


def load_all_models(root: Path) -> list[dict[str, Any]]:
    scope = load_scope(root)
    return [load_model(root, m) for m in scope["models"]]


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def compute_content_hash(models: list[dict[str, Any]], sources: list[dict[str, Any]]) -> str:
    payload = {"models": models, "sources": sources}
    return sha256_text(canonical_json(payload))


def compute_scope_hash(scope: dict[str, Any]) -> str:
    payload = {
        "models": scope["models"],
        "family_map": scope["family_map"],
        "in_scope_capabilities": scope["in_scope_capabilities"],
        "out_of_scope_capabilities": scope["out_of_scope_capabilities"],
        "excluded_models": scope.get("excluded_models", []),
    }
    return sha256_text(canonical_json(payload))