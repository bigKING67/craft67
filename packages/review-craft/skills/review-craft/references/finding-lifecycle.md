# Finding Lifecycle and Decisions

## Contents

1. Candidate fields
2. Simplification proof
3. Validation outcomes
4. Severity and priority
5. Decision rules
6. Performance claims

## Candidate fields

Use stable IDs such as `RC-ARCH-001`. Record category, type, title, exact locations,
evidence, claimed impact, confidence, and a separate validation record. Candidate
evidence should explain the trace, not merely quote a suspicious line.
For canonical run.v5, generate every location with `anchor-location` and reuse the exact
returned object in its matching finding; do not hand-author or copy an anchor across spans.

## Simplification proof

Read `simplification.md` when a candidate proposes retiring a maintenance obligation
through `CLEAN_UP`, `MERGE`, `REPLACE`, or `DELETE`. Its smell-to-behavior investigation
depth is evidence about how far the analysis progressed; it does not replace the canonical
validation outcomes below. Preserve its consumer map, cut boundary, surrendered behavior,
decisive proof, and net effect through existing canonical artifacts.

## Validation outcomes

- `CONFIRMED`: direct reproduction, decisive static trace, or equivalent proof.
- `LIKELY`: strong evidence remains but one bounded condition is unverified.
- `NEEDS_MEASUREMENT`: plausible claim requires benchmark, profile, trace, or scale.
- `BLOCKED`: decisive evidence cannot currently be obtained.
- `REJECTED`: evidence disproves the claim or impact.
- `NOT_APPLICABLE`: the relevant invariant or environment is outside project goals.

Keep rejected candidates to measure false positives and prevent rediscovery drift.

For a bounded review, keep each candidate's evidence and validation disposition distinct.
Several candidates may be resolved in one declared scope when their required checks remain
narrow and relevant. Do not merge independent claims into one finding, infer a shared cause
without evidence, or turn the candidate count itself into a reason to require canonical
artifacts.

For dead-code candidates, a text search with no call sites is insufficient by
itself. Check exports and public API, reflection and plugin registration, build and
packaging entrypoints, generated consumers, and runtime coverage where applicable.
Without those checks, keep the candidate `LIKELY`, `BLOCKED`, or `REJECTED` rather
than claiming safe deletion.

For test-gap candidates, uncovered branches are inventory evidence, not impact.
Promote a gap only when it maps to a critical path or invariant and names a credible
failure that the current suite would not catch.

## Severity and priority

Severity describes the issue itself. Priority describes the current cost-benefit of
fixing it. Consider impact, probability, affected scope, modification frequency,
future amplification, repair cost, and regression risk. A high-severity unreachable
compatibility issue can be P2; a medium issue blocking daily changes can be P1.

## Decision rules

- `KEEP`: implementation is appropriate for current goals.
- `CLEAN_UP`: local simplification without boundary change.
- `MERGE`: semantically duplicate implementations should share one authority.
- `REPLACE`: a bounded alternative has better cost and risk.
- `REWRITE`: structural faults make incremental repair worse than reimplementation.
- `DELETE`: the capability has no valid entrypoint, contract, or hidden build role.
- `DEFER`: current net benefit is insufficient.
- `MEASURE`: evidence is insufficient for a change decision.
- `DOCUMENT`: implementation is reasonable but its constraints are implicit.

`REWRITE` requires a behavioral baseline, structural root cause, rejected smaller
alternatives, phased migration, rollback, and measurable acceptance. `DELETE`
requires reference and entrypoint analysis, compatibility and hidden-role checks,
migration where needed, rollback, and post-deletion verification.

## Performance claims

- `MEASURED_REGRESSION`: a baseline and comparable measurement show regression.
- `ALGORITHMIC_RISK`: the complete path, complexity, scale, and frequency establish risk.
- `LIKELY_HOT_PATH`: plausible and important; decide `MEASURE`.
- `UNVERIFIED_SUSPICION`: insufficient evidence; reject or keep pending outside findings.
