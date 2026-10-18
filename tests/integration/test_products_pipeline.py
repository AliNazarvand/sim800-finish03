import json
from pathlib import Path


def test_products_have_expected_scale_and_provenance():
    root = Path(__file__).resolve().parents[2]
    commands = [json.loads(line) for line in (root / "dataset/commands.jsonl").read_text().splitlines() if line]
    errors = [json.loads(line) for line in (root / "dataset/error_codes.jsonl").read_text().splitlines() if line]
    deprecated = [
        json.loads(line) for line in (root / "dataset/deprecated_commands.jsonl").read_text().splitlines() if line
    ]
    assert len(commands) >= 50
    assert len(errors) >= 50
    assert len(deprecated) >= 1
    assert all(item["source"] for item in commands)
    assert {item["category"] for item in errors} == {"CME", "CMS"}
    assert all(item["compared_versions"] for item in deprecated)


def test_cli_validate_and_diff(tmp_path, capsys):
    from sim800_tools.cli import main

    schema_dir = tmp_path / "schemas"
    dataset_dir = tmp_path / "dataset"
    schema_dir.mkdir()
    dataset_dir.mkdir()
    (schema_dir / "commands.schema.json").write_text(json.dumps({"type": "object", "required": ["command"]}))
    (dataset_dir / "commands.jsonl").write_text('{"command":"AT+A"}\n')
    assert main(["validate", "--dataset-dir", str(dataset_dir), "--schema-dir", str(schema_dir)]) == 0
    old = tmp_path / "old.jsonl"
    new = tmp_path / "new.jsonl"
    output = tmp_path / "diff.json"
    old.write_text('{"command":"AT+A"}\n')
    new.write_text('{"command":"AT+B"}\n')
    assert main(["diff", str(old), str(new), "--output", str(output)]) == 0
    assert json.loads(output.read_text())["added"] == ["AT+B"]
    assert capsys.readouterr().out
