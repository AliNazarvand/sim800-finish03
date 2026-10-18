import json
from pathlib import Path

import pytest
from jsonschema import SchemaError

from sim800_diffing import diff_commands, load_commands, write_diff
from sim800_validation import validate_directory, validate_jsonl


def write_schema(path: Path, schema=None):
    path.write_text(
        json.dumps(schema or {"type": "object", "required": ["command"], "properties": {"command": {"type": "string"}}})
    )


def test_validate_jsonl(tmp_path: Path):
    schema, data = tmp_path / "s.json", tmp_path / "d.jsonl"
    write_schema(schema)
    data.write_text('{"command":"AT"}\n{"bad":1}\n')
    report = validate_jsonl(data, schema)
    assert report["valid"] == 1 and report["invalid"] == 1


def test_validate_jsonl_ignores_blank_lines(tmp_path: Path):
    schema, data = tmp_path / "s.json", tmp_path / "d.jsonl"
    write_schema(schema)
    data.write_text('\n {"command":"AT"}\n\n')
    assert validate_jsonl(data, schema)["total"] == 1


def test_validate_jsonl_rejects_malformed_json(tmp_path: Path):
    schema, data = tmp_path / "s.json", tmp_path / "d.jsonl"
    write_schema(schema)
    data.write_text('{"command":\n')
    report = validate_jsonl(data, schema)
    assert report["invalid"] == 1 and "Expecting" in report["errors"][0]["errors"][0]


def test_validate_jsonl_rejects_schema_type_violation(tmp_path: Path):
    schema, data = tmp_path / "s.json", tmp_path / "d.jsonl"
    write_schema(schema)
    data.write_text('{"command":42}\n')
    report = validate_jsonl(data, schema)
    assert report["invalid"] == 1 and report["errors"][0]["line"] == 1


def test_validate_jsonl_writes_quarantine(tmp_path: Path):
    schema, data, quarantine = tmp_path / "s.json", tmp_path / "d.jsonl", tmp_path / "q" / "bad.jsonl"
    write_schema(schema)
    data.write_text('{"bad":1}\n')
    report = validate_jsonl(data, schema, quarantine)
    assert report["invalid"] == 1 and quarantine.exists() and '"line": 1' in quarantine.read_text()


def test_validate_jsonl_appends_quarantine(tmp_path: Path):
    schema, data, quarantine = tmp_path / "s.json", tmp_path / "d.jsonl", tmp_path / "q.jsonl"
    write_schema(schema)
    quarantine.write_text('{"old":true}\n')
    data.write_text('{"bad":1}\n')
    validate_jsonl(data, schema, quarantine)
    assert len(quarantine.read_text().splitlines()) == 2


def test_validate_jsonl_rejects_invalid_schema(tmp_path: Path):
    schema, data = tmp_path / "s.json", tmp_path / "d.jsonl"
    schema.write_text('{"type":"not-a-real-type"}')
    data.write_text('{"command":"AT"}\n')
    with pytest.raises(SchemaError):
        validate_jsonl(data, schema)


def test_validate_directory_matches_nonempty_schemas(tmp_path: Path):
    dataset, schemas = tmp_path / "dataset", tmp_path / "schemas"
    dataset.mkdir()
    schemas.mkdir()
    (dataset / "commands.jsonl").write_text('{"command":"AT"}\n')
    write_schema(schemas / "commands.schema.json")
    (dataset / "unmatched.jsonl").write_text('{"x":1}\n')
    assert len(validate_directory(dataset, schemas)) == 1


def test_load_commands_uses_command_text_fallback(tmp_path: Path):
    path = tmp_path / "commands.jsonl"
    path.write_text('{"command_text":"AT+FALLBACK"}\n')
    assert load_commands(path) == {"AT+FALLBACK": {"command_text": "AT+FALLBACK"}}


def test_load_commands_skips_blank_lines_and_missing_keys(tmp_path: Path):
    path = tmp_path / "commands.jsonl"
    path.write_text('\n{"x":1}\n{"command":"AT"}\n')
    assert list(load_commands(path)) == ["AT"]


def test_load_commands_duplicate_keeps_last_record(tmp_path: Path):
    path = tmp_path / "commands.jsonl"
    path.write_text('{"command":"AT","version":1}\n{"command":"AT","version":2}\n')
    assert load_commands(path)["AT"]["version"] == 2


def test_load_commands_rejects_bad_json(tmp_path: Path):
    path = tmp_path / "commands.jsonl"
    path.write_text("{bad}\n")
    with pytest.raises(json.JSONDecodeError):
        load_commands(path)


def test_diff_commands_detects_added_removed_changed(tmp_path: Path):
    old, new = tmp_path / "old.jsonl", tmp_path / "new.jsonl"
    old.write_text('{"command":"AT+A","x":1}\n{"command":"AT+OLD"}\n')
    new.write_text('{"command":"AT+A","x":2}\n{"command":"AT+NEW"}\n')
    assert diff_commands(old, new) == {"added": ["AT+NEW"], "removed": ["AT+OLD"], "changed": ["AT+A"]}


def test_diff_commands_empty_files(tmp_path: Path):
    old, new = tmp_path / "old.jsonl", tmp_path / "new.jsonl"
    old.write_text("")
    new.write_text("")
    assert diff_commands(old, new) == {"added": [], "removed": [], "changed": []}


def test_write_diff_creates_parent_and_relative_metadata(tmp_path: Path):
    old, new, output = tmp_path / "old.jsonl", tmp_path / "new.jsonl", tmp_path / "nested" / "diff.json"
    old.write_text('{"command":"AT+A"}\n')
    new.write_text('{"command":"AT+B"}\n')
    result = write_diff(old, new, output)
    saved = json.loads(output.read_text())
    assert result["added"] == ["AT+B"] and saved["old"] == "old.jsonl" and output.parent.exists()
