# Validation

- Full unittest discovery: 210 tests, 207 passed, 3 optional rendering skips.
- New preview/replay tests: 15 passed, including exclusive creation, tampering, changed evidence, future evidence, separate expectation origins, fiscal basis mismatch, local before-disclosure clock, reconstructed history, cancellation evidence, first-disclosure mismatch, restatement rejection and CLI round trip.
- Source validator: valid, no warnings/errors.
- Package acceptance: all seven checks passed (allowlist/size, extraction, identity, runtime, temporary install and research smoke).
- OpenSpec strict validation and git diff whitespace check passed.

Scope: synthetic, source-bound engineering fixtures; no demonstrated live forecast performance or fresh official-source research in this batch. Local timestamps/hashes are not externally trusted or administrator-proof. No host installation, commit, push, publication, application or trading actions.

## Forward-use acceptance, 2026-09-15

- Added inspect-preview and civil-date/offset fixes after using the current-date workflow.
- Final full suite: 213 tests, 210 passed, 3 optional rendering skips; baseline suite: 18 passed.
- Source validation, seven package checks, strict OpenSpec validation and whitespace checks passed.
- Two official filing files captured in the repo-local ignored evidence directory. Current dated forward baseline sealed without altering earlier revisions; six Decimal calculations audited.
- Local investment run has six receipts; receipt/artifact verification returned ok=true.
- The historical forecast formula remains an analyst continuity assumption; independent numeric corroboration is missing. Research readiness PARTIAL; no actual 2026 Q3 outcome or full-report audit claimed. See acceptance/earnings/forward-preview.md for reproduction and scope.

## Captured numeric crosscheck, 2026-09-15

- Added bounded Fuyao income crosscheck core and CLI with explicit cumulative-basis confirmation; no additional dependencies.
- Eleven synthetic regression tests cover cumulative subtraction, exact 1%/5% boundaries, missing/null/basis, identity metadata, duplicate periods, business error, nonfinite values, capture tampering and future capture.
- Full suite: 224 tests, 221 passed, 3 optional rendering skips. Source validation, package checks, OpenSpec strict validation and diff whitespace checks passed.
- Live Fuyao income request succeeded. Six declared forecast inputs match formal filing extracts with zero relative difference; raw Provider response remains ignored/private. Baseline hash unchanged.
- Separate local crosscheck run: four receipts, completed, artifact verification ok=true. This verifies the declared numeric comparison only; overall research readiness remains PARTIAL and no historical point-in-time or full-report assurance is claimed.
