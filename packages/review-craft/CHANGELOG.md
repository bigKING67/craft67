# Changelog

## 0.7.4 — source update 2026-10-17 (not published)

### Review guidance

- Describe whether a finding is introduced, exposed, pre-existing, or undetermined relative
  to an explicit change boundary. Require causal base/current evidence and keep attribution
  separate from validation, severity, and priority through existing free-text fields.
- Guide explicitly requested host re-review toward the new diff and affected behavior,
  retain prior candidate dispositions, and reassess the approach after three non-converging
  review-and-fix rounds. Keep unchanged-source command retries and immutable canonical
  evidence separate from host review rounds.
- Add project-specific failure-mode examples and accepted-tradeoff guidance to the quality
  model and engineering-context template. Connect observable failures to invariants and
  decisive checks while preserving repository trust and command-authorization boundaries.

Selectively informed by [How the Claude Code team does code review](https://claude.dev/blog/solving-code-review-at-anthropic/).
This update adds no schema, automated multi-pass workflow, or runtime history comparison.
It does not claim a new model evaluation, host acceptance, installation, tag, or publication.

### Scope selection

- Normalize repeated leading `./` prefixes in current scope selectors so equivalent
  directory, file, and root spellings retain the same canonical inventory. Keep literal
  filename whitespace and POSIX backslashes unchanged, and preserve frozen run.v3/v4
  selection semantics through the existing private compatibility path.
- Add real-Git and filesystem inventory regressions, root-selector union checks, and a
  CLI preflight/validation regression. Refresh only the Alibaba reference pin and reviewed
  blobs for this selective adaptation; keep earlier adaptation provenance and exclusions.

## 0.7.3 — source update 2026-09-23 (not published)

### Verification

- Add the read-only `verification-input --run-dir` command and
  `review-craft.assurance-verification.v2`. Bind independent assessments to the complete
  canonical findings document using `findingsSha256`, in addition to run and source identity.
- Require exactly one receipt matching the current findings content. Preserve stale receipts
  without accepting them for finalization; material changes require renewed assessment.
- Keep sealed v1-only historical runs validation-readable. New assured finalization requires
  v2; existing draft v1 receipts do not qualify. No automatic migration is performed.
- Serialize verification input as ASCII-safe JSON for Windows redirected output. JSON decoding
  preserves Unicode findings and their canonical digest.

### Git and upstream references

- Preserve whitespace in current Git repository root identities without changing frozen
  legacy identity semantics. Cover special filenames, renames, and deletions with real Git tests.
- Register `cloudflare/security-audit-skill` as a selectively absorbed reference, with pinned
  source blobs, license attribution, candidate falsification guidance, precise blockers, and
  reassessment requirements. Do not import its full security-audit or multi-agent workflow.
- Refresh Cursor and Alibaba reference pins and selected Alibaba path-handling surfaces.
  Enforce the upstream check's offline default in tests.

This entry records the source version and installed runtime update only. It is not evidence
of a published tag, GitHub Release, npm package, or new host-quality evaluation.
