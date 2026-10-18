# Release Notes — v0.1.0

## Summary

SIM800 Platform v0.1.0 provides a reproducible, MIT-licensed foundation for SIM800 AT-command data products, validation, version diffing and a lightweight modem driver/adapter.

## Data Products

- `dataset/commands.jsonl`: **357** command records
- `dataset/error_codes.jsonl`: **255** error-code records
- `dataset/deprecated_commands.jsonl`: **43** documented deprecation candidates
- `dataset/commands_versions.jsonl`: **1095** version-matrix records

The deprecated candidates are traceable to the removed-command entries in `data/diffs/` and retain their compared versions and rationale.

## Quality and Validation

- **34 tests passing**
- **97.70% source coverage** with `pytest --cov=src`
- `mypy src/`: PASS
- `ruff check .`: PASS
- `pre-commit run --all-files`: PASS
- Great Expectations `commands_checkpoint`: **PASS**, 4 of 4 expectations met

All seven release QA Gates are PASS:

1. Schema Conformance
2. Data Completeness
3. Cross-Reference
4. Reproducibility
5. CI Syntax
6. License Compliance
7. License Compatibility

## Licensing

Project code and JSON schemas are released under the **MIT License**. The original SimCom PDF datasheets remain externally owned and are excluded from the release archives; the repository retains only structural, provenance and validation information needed for reproducibility.
