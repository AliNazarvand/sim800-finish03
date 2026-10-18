# ADR-002: Structural PDF extraction without reproducing source text

## Status
Accepted

## Context
The external repository contains 13 SIM800 PDFs, some encrypted and all subject to source ownership. The product needs machine-readable identifiers, error codes, provenance and version support without publishing long-form source text.

## Decision
Use `pdftotext -layout` read-only, extract only AT identifiers and numeric rows from the explicit CME/CMS Summary sections, preserve source filename and applicable versions, and leave unverified fields null. Encrypted PDFs are not decrypted.

## Consequences
The products are reproducible and copyright-conscious. Table extraction is more precise than searching every `<err>` placeholder, but descriptions remain concise and tied to the Summary tables.

## Alternatives Considered
OCR was retained as an available fallback for scanned PDFs but was not needed for these text-readable sources. Full-text publication was rejected.
