# ADR-001: Choose jsonschema for dataset validation

## Status
Accepted

## Context
Products are JSONL records governed by JSON Schema contracts. The validator must remain lightweight and usable from scripts and CI.

## Decision
Use `jsonschema` and Draft 7 schemas. Great Expectations and Pandera remain optional analytics tools, not runtime dependencies.

## Consequences
Schemas are portable and validation is deterministic. Domain-specific checks can be layered above schema validation.

## Alternatives Considered
Great Expectations offers richer data docs but adds operational weight. Pandera is excellent for tabular data but is less direct for nested JSONL contracts.
