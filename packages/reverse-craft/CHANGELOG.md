# Changelog

## Unreleased

## 0.2.0 - 2026-08-27

- Added first-class R44 CTI/OSINT routing, a public-source intelligence module, bilingual routing coverage, and an
  offline IOC-enrichment scenario; explicit CTI intent now takes priority over mixed malware terminology.
- Added bounded R0 progress-stall replanning after three evidence-free actions or two stage switches while retaining R0
  as primary and requiring the current hypothesis, attempts, evidence gap, decision delta, and a feasibility-gated plan
  change.
- Added a blind, profile-specific Codex/Pi R0 Host contract with content-bound receipts and bounded offline regrading of
  `hypothesis` to canonical `current hypothesis`; raw payloads, hashes, and source failures remain preserved.
- Excluded generated Python bytecode/cache directories from the npm candidate archive.
- Split case mutation/orchestration from case validation and manifest logic without changing the public CLI or data contracts.
- Added event-record and seal JSON Schemas with source/runtime field-drift checks and stricter seal reconciliation.
- Added redacted `crash.v1` diagnostics for unexpected CLI exceptions without exposing exception messages or tracebacks.
- Hardened `doctor` MCP discovery so raw transport arguments, environment/header values, URL secrets, unknown
  transport fields, and failing command stderr are never returned.
- Made new case/setup runtime directories and generated artifacts owner-only on POSIX.
- Added strict fail-closed validation for malformed case snapshots/events and schema/runtime field-drift checks.
- Anchored new case event tails in `case.json`, reconciled entity events with snapshots, and documented the
  remaining local-consistency versus external-authenticity boundary.
- Restricted copied evidence and rendered reports to their dedicated case subdirectories.

## 0.1.0 - 2026-08-21

- Added one installable `$reverse-craft` Skill with 42 deterministic specialist routes.
- Added dependency-free case, evidence, finding, path, report, seal, doctor, setup, and provenance CLI.
- Added browser67 `js-reverse` orchestration boundary and live MCP gate.
- Added 252 bilingual routing cases, 10 offline end-to-end scenarios, unit tests, and real Codex/Pi evaluations.
- Added macOS, Linux, and Windows CI validation. No npm publication, tag, or release is part of this version.
