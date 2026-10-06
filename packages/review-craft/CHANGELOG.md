# Changelog

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
