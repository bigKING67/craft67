# Case and evidence contract

## Layout

```text
<home>/runs/<case-id>/
|-- case.json
|-- evidence.json
|-- findings.json
|-- paths.json
|-- events.ndjson
|-- artifacts/
|-- reports/
`-- seal.json                 present only after seal
```

JSON snapshots are written atomically. `events.ndjson` is append-only through the CLI and each event includes
its previous event hash. New cases also persist `event_count` and `last_event_hash` in `case.json`; validation
compares that tail anchor and reconciles evidence/finding/path events with their snapshots. This detects
ordinary tail truncation, reordering, record corruption, and partial writes. A per-case lock serializes writers.
`schemas/event.schema.json` applies to each NDJSON record, while `schemas/seal.schema.json` describes the final
seal receipt; source validation keeps their field sets aligned with the dependency-free runtime validator.

Cases created before the tail anchor was introduced remain readable. Validation reports a legacy warning and
the next successful mutation upgrades the case. An open case is still a local self-consistency record, not an
externally anchored or signed audit log: a party able to rewrite every case file can forge a new consistent
history. Use a protected external digest, signature, transparency service, or WORM storage when adversarial
tamper evidence is required.

## State

`open -> sealed`. Open cases accept evidence, findings, paths, and report rendering. A sealed case is
logically immutable: mutating CLI commands fail. `case validate` remains read-only after seal and verifies
snapshot shape, references, artifact hashes, event hash continuity, and the seal manifest.

The case root, artifact store, report store, event stream, generated snapshots, copied artifacts, reports, and
setup journals are created owner-only on POSIX (`0700` directories, `0600` files). Windows uses the platform's
ACL semantics instead of POSIX mode bits. These defaults reduce accidental disclosure; they are not encryption.

## Entities

- **Evidence**: `E-NNNN`, source, kind, acquisition method, timestamp, size, SHA-256, stored or external path,
  optional note and route/run reference.
- **Finding**: `F-NNNN`, title, status (`hypothesis|supported|confirmed|refuted`), severity, confidence,
  evidence IDs, statement, and optional reproduction.
- **Path**: `P-NNNN`, ordered finding IDs, title, status, preconditions, impact, and validation note.
- **Report**: deterministic Markdown projection; it is not new evidence.

## Minimum evidence rules

- `supported` and `confirmed` findings require at least one existing evidence ID.
- A `confirmed` finding requires `confidence=high` or an explicit reproduction note.
- Paths require at least one existing, non-refuted finding.
- Sealing requires zero validation errors and at least one evidence item.
- External evidence must remain readable with matching size/hash at validation time.
- Copied evidence remains under `artifacts/`; report output remains under `reports/` and cannot target case metadata.
- Structurally malformed snapshots or events fail validation as data errors; they do not become Python tracebacks.

Use evidence notes for provenance and observation, not secrets or entire logs. Put large output in an artifact
and cite its hash/ID.

## browser67 references

Do not copy browser67 run directories into a case by default. Add a small JSON receipt or external evidence
record containing the browser67 `run_id`, selected evidence artifact path, size, and hash. browser67 remains
the runtime owner; Reverse Craft owns the cross-domain finding/path graph.
