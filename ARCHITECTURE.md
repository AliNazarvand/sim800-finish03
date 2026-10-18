# SIM800 Platform Architecture

The platform has five dependency-light Python packages under `src/`:

- `sim800_driver`: transport protocol, AT response parser, timeout/retry policy.
- `sim800_adapter`: TinyGSM-like facade for readiness, signal quality and SMS.
- `sim800_tools`: operational CLI for validation and version diffing.
- `sim800_validation`: JSON Schema validation with quarantine output.
- `sim800_diffing`: deterministic command-set comparison and machine-readable diffs.

The data flow is **PDF source (external/read-only) → structural extraction → JSONL products → schema validation → quarantine/reporting → release artifacts**. Original PDF files are excluded from release archives and secrets are never read by application code.
