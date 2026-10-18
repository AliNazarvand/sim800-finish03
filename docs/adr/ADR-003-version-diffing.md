# ADR-003: Version diffing by canonical command identifiers

## Status
Accepted

## Context
Three AT manuals expose overlapping but non-identical command sets. A release must show additions, removals and changes and must not silently turn absence into a confirmed replacement.

## Decision
Normalize each manual into JSONL keyed by the canonical `AT+...` identifier, call `sim800_diffing.write_diff` for adjacent versions, and emit removed identifiers to `deprecated_commands.jsonl` as candidates with compared versions and an explicit row-level confirmation note.

## Consequences
Diff artifacts are deterministic and reviewable. A removed candidate is not presented as a guaranteed semantic deprecation until manual confirmation is complete.

## Alternatives Considered
Comparing full PDF text was rejected because layout and revision history create noise. Comparing only command counts was rejected because it cannot identify removals.
