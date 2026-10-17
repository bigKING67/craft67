# Finding Lifecycle and Decisions

## Contents

1. Candidate fields
2. Relationship to a change
3. Simplification proof
4. Validation outcomes
5. Re-review convergence
6. Severity and priority
7. Decision rules
8. Performance claims

## Candidate fields

Use stable IDs such as `RC-ARCH-001`. Record category, type, title, exact locations,
evidence, claimed impact, confidence, and a separate validation record. Candidate
evidence should explain the trace, not merely quote a suspicious line.
For canonical run.v5, generate every location with `anchor-location` and reuse the exact
returned object in its matching finding; do not hand-author or copy an anchor across spans.

## Relationship to a change

When the user supplies a change boundary and causal attribution matters, explain the
finding's relationship to that change using one of these prose descriptions:

- Introduced by this change: the base satisfies the relevant invariant and the current
  change breaks it under the stated conditions.
- Exposed by this change: faulty code already exists, but a changed caller, input,
  configuration, or lifecycle makes the failure newly reachable or materially worse.
- Pre-existing: the same failure is reachable under the same relevant conditions in the
  base, and the change does not materially alter its impact.
- Undetermined: the available base, execution path, or environment cannot establish the
  relationship. State the missing evidence rather than guessing.

Support attribution with an exact base/current comparison and a causal trace or decisive
reproduction. A changed line, an unchanged line, or `git blame` alone is insufficient.
Keep attribution separate from validation status, severity, and priority: a confirmed
defect can have undetermined origin. In a change-focused review, keep any in-scope
pre-existing issue distinct from regressions. Do not add an unrelated finding beyond the
declared scope unless an explicit P0/P1 exception applies. Repository-wide reviews still
include in-scope pre-existing defects.

For bounded output, include the relationship and its evidence with the finding. For
canonical output, use the existing candidate evidence and finding `rootCause`,
`currentImpact`, and `evidenceRefs` fields. These descriptions add no schema fields,
enums, severity changes, or automatic merge-blocking policy.

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

## Re-review convergence

Apply this guidance when the user requests another host review or an authorized fix
needs re-review. It does not require repeated passes, authorize source edits, or add
runtime scheduling or history comparison.

- Review the declared scope on the first pass. On a later pass, identify the previous
  reviewed source state and inspect the new diff, selected findings, and directly affected
  callers, invariants, and tests. Widen only when observed coupling or risk justifies it,
  and explain the reason. Missing prior state or evidence is an explicit limitation.
- Match previous candidates by root cause, affected behavior, and source lineage, rather
  than title or line number alone. Preserve their IDs and dispositions where applicable;
  recheck evidence against current source. Reopen a previously resolved or rejected claim
  only when changed source or new evidence invalidates its disposition. An unresolved
  claim stays visible without being counted or posted again as a new finding.
- When evidence establishes a common defect class, inspect its relevant in-scope instances
  so the fix addresses the mechanism. Keep distinct claims and per-instance evidence;
  shared wording alone does not establish a common cause.
- After three review-and-fix rounds on the same task without convergence, stop repeating
  the same approach and reassess root cause, solution, scope, and verification. State what
  evidence or changed approach justifies further work within existing authorization.
  Three rounds are a reassessment trigger, not a required pass count or a success condition.
- Close a finding only when its verification criteria are met. Report unresolved findings,
  blocked evidence, scope changes, and any reassessment instead of declaring a pass from
  the round count. A delta review proves only its stated scope; it cannot inherit full
  coverage, a score, or independent verification from stale artifacts.

Keep sealed canonical runs immutable. A changed source baseline needs fresh source-bound
artifacts through the existing canonical workflow when that work is authorized. Command
retries on unchanged source are separate from these host review rounds; follow
[remediation.md](remediation.md) for their unchanged-source and lineage requirements.

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
