# Deprecated Commands Validation

- Candidate records checked: **43**
- Source diff artifacts: `commands_v1.01_to_v1.10.json`, `commands_v1.10_to_v1.12.json`
- Extraction method: union of each diff artifact's `removed` array, preserving the target version as `deprecated_in`.
- Provenance cross-check: **PASS** — every candidate `(command, deprecated_in)` pair exactly matches one removed entry from `data/diffs/`.
- Documentation cross-check: **PASS** — every record contains a non-empty `deprecated_reason`, source and compared versions.
- Semantic status: these are documented **candidates**, not unverified replacement claims.
