import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from capabilities.cpp import render_from_root, write_cpp_header


def test_render_header_contains_namespace_and_models():
    root = Path(__file__).resolve().parents[2]
    text = render_from_root(root)
    assert "namespace sim800_capabilities" in text
    assert "inline constexpr Model kModels[]" in text
    assert "kModelCount" in text
    for name in ("SIM800", "SIM800A", "SIM800C", "SIM800C-DS", "SIM800F",
                 "SIM800H", "SIM800L", "SIM808", "SIM868"):
        assert '"' + name + '"' in text, f"missing model {name}"


def test_render_header_has_families_and_statuses():
    root = Path(__file__).resolve().parents[2]
    text = render_from_root(root)
    for fam in ("Family::SIM800", "Family::SIM808", "Family::SIM868"):
        assert fam in text
    for st in ("Status::documented", "Status::not_supported", "Status::not_documented"):
        assert st in text


def test_write_cpp_header(tmp_path):
    root = Path(__file__).resolve().parents[2]
    out = tmp_path / "capabilities.hpp"
    p = write_cpp_header(root, out)
    assert p == out
    assert p.exists()
    content = p.read_text(encoding="utf-8")
    assert content.startswith("// AUTO-GENERATED")
    assert "namespace sim800_capabilities" in content
    assert "SIM868" in content


def test_write_cpp_header_default_path(tmp_path, monkeypatch):
    root = Path(__file__).resolve().parents[2]
    # redirect default location by copying data into tmp root is overkill;
    # instead just verify function returns a path under <root>/include when no out given.
    import shutil
    scratch = tmp_path / "proj"
    scratch.mkdir()
    shutil.copytree(root / "data" / "capabilities", scratch / "data" / "capabilities")
    p = write_cpp_header(scratch)
    assert p == scratch / "generated" / "cpp" / "sim800_capabilities.hpp"
    assert p.exists()