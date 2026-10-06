# Scoring, Evidence, and Report Contract

## Contents

1. Dimensions
2. Deductions
3. Evidence levels
4. Confidence
5. Report projection

## Dimensions

Use the fixed 100-point model:

- correctness and stability: 20;
- architecture and module design: 20;
- long-term maintainability: 15;
- performance and resources: 15;
- code quality and consistency: 10;
- testing and engineering systems: 10;
- dependencies and basic security governance: 5;
- repository structure, documentation, and developer experience: 5.

Map observability and recovery to correctness/testing according to their impact.
Do not silently change weights for a preferred architecture.

## Deductions

Start from the dimension maximum and deduct only for a validated finding or explicit
evidence gap. Cite IDs. The finalizer checks that deduction points equal maximum
minus awarded points and computes the total.

For a final `review-craft.run.v4` or `review-craft.run.v5` scorecard, every deduction
reference must resolve to an existing finding ID or match the canonical
`evidence-gap:<id>` namespace, where `<id>` is a lowercase ASCII identifier using letters,
digits, `_`, or `-`. Bare `artifact:<id>`, paths, typos, and nonexistent finding IDs do not
close a score deduction and fail validation. Draft validation may use the runtime-owned
`coverage:draft` placeholder until coverage is closed. Sealed `review-craft.run.v3`
artifacts retain their published free-form reference validation and are not silently
upgraded to run.v4 or run.v5 semantics.

Only the canonical finalizer may produce the numeric total. When the runtime or
finalizer is unavailable, report the evidence level and qualitative gaps without
a numeric table, approximate total, or alternate weighting model.

Use a provisional score when coverage or candidates remain open. Accounted coverage
means every file has a final disposition; reviewed coverage counts only `REVIEWED`
and `COVERED_BY_PARENT`. Generated, vendored, and binary dispositions are accounted
but never presented as reviewed. `PENDING`, `DEFERRED`, `UNREADABLE`, and
`OUT_OF_SCOPE` review gaps prevent a final score. Do not deduct for an explicit
non-goal. Do not inflate a score merely because source files, schemas, or tests exist.

Canonical `fast` assurance is always provisional and capped at E2 even when its bounded
scope is fully accounted. `assured` is final only with E3+ evidence, no unverified claims,
and exactly one current v2 independent verification artifact binding the entire canonical
findings document by SHA-256 and covering every finding. Stale receipts remain immutable;
changed findings require renewed independent assessment. The
finalizer derives the assurance block; do not hand-author completion or verifier status.

## Evidence levels

- E0: description or documentation only; no formal score.
- E1: current source and configuration reviewed.
- E2: at least one relevant configured check, test, or build completed successfully
  without timeout or repository mutation.
- E3: critical runtime, benchmark, profile, or trace evidence captured.
- E4: clean and deployment-representative reproduction.

E2-E4 require a command receipt whose name, argv, and cwd match the canonical command
configuration. Scores of 95 or more require E3. Scores of 98-100 require E4. These
gates prevent source completeness, self-consistent receipt tampering, or
self-evaluation from masquerading as operational proof.

An optional semantic receipt makes a multi-stage command machine-readable. Claims are
verified from structured stdout, never from configuration alone. Canonical kinds map to
evidence ceilings: check/test/build/package to E2; isolated-install/runtime/benchmark/
profile/trace to E3; clean-deployment-reproduction to E4. If a run contains semantic
receipts, E3/E4 require a matching verified claim. A declared claim or artifact failure
also prevents that receipt from satisfying the ordinary E2 success gate. Registered
manual runtime, benchmark, profile, or trace artifacts can support a finding, but do not
replace the successful canonical command receipt required for E2-E4.

## Confidence

Confidence reflects coverage, validation quality, evidence level, and unresolved
conditions. It is not a stylistic expression of certainty. Record low confidence
when critical paths, environments, or scale cannot be reproduced.

## Report projection

The report is a deterministic view of canonical JSON. It contains the executive
summary, eight scores, full findings, dispositions, target design, Phase 0-4 plan,
final five answers, score status, accounted coverage, reviewed coverage, and coverage
disposition counts. Edit JSON and rerun finalization instead of patching the Markdown.

The score label is mode-bound: `review` is repository-wide, while `focus` and `diff`
explicitly state that their score applies only to the selected scope. Findings, evidence
gaps, and remaining risks are separate deterministic sections. `CONFIRMED` and `LIKELY`
findings have independent counts and sections; a `LIKELY` finding remains visible but is
never projected as confirmed. Evidence gaps are deduped
from scorecard deduction references beginning with `evidence-gap:`; remaining risks come
from `quality-model.json.unknowns`. Verified semantic claims and copied command artifacts
are listed from canonical command receipts. Current run.v5 reports list every registered
`artifact:<id>` with kind, producer, SHA-256, and byte size; sealed run.v4 reports retain
that same historical projection.
Current reports also project assurance level, completion status, budget consumption,
verifier status, unverified claims, and skipped dimensions. These fields distinguish a
complete standard or assured review from a bounded provisional run.

`reportLanguage: zh-CN` requires human-facing canonical text such as finding rationale,
target architecture, phase scope, benefits, risks, and acceptance criteria to be authored
in Chinese before finalization. Code identifiers, commands, paths, and canonical enum values
remain unchanged. The finalizer projects text deterministically and never performs implicit
translation.

New run.v5 scorecards write `accountedPercent` and `reviewedPercent`, with
`coveragePercent` retaining the reviewed value. Sealed run.v4 scorecards retain those
same published fields and semantics. For compatibility, a historical run.v3 scorecard
without the two explicit fields is validated using its original `coveragePercent`
accounting semantics; restart unfinished historical runs with current preflight rather
than silently changing their meaning.
