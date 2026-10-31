# Project Quality Model

The structural-quality, test-sensitivity, state-ownership, and refactoring guidance
here and in `simplification.md` is independently written, informed by a bounded reading of
[`ub-mode/SKILL.md`](https://github.com/unclebob/ub-mode/blob/57a8bdd28e45ed41900ace0bafa2ff76dd9ed70f/SKILL.md).
Its tools, thresholds, and execution workflow are not Review Craft requirements.

## Contents

1. Purpose
2. Critical paths
3. Invariants
4. Failure modes and accepted tradeoffs
5. Structural clarity and change cost
6. Compatibility and budgets
7. Non-goals
8. Evidence quality

## Purpose

Describe the real problem, audience, scale, and usage pattern. Use source and runtime
facts. If project intent remains ambiguous and materially changes the review, ask
one focused question and record the answer as authority.

## Critical paths

List the flows whose failure would invalidate the project's purpose. Trace each
flow from entrypoint through state transitions and side effects to its observable
result. Map tests and runtime evidence to these paths before evaluating coverage.

## Invariants

Record behaviors or data properties that must remain true, including persistence,
ordering, idempotency, authentication, compatibility, and recovery constraints.
Findings should identify a violated invariant or a measurable engineering cost.

## Failure modes and accepted tradeoffs

For each material critical path, connect an observable failure to its invariant and the
smallest decisive check, or record the evidence gap. Use existing critical-path and
invariant descriptions; no additional artifact or exhaustive checklist is required.
Select only paths supported by the project's actual purpose. These examples illustrate
the mapping rather than impose features or validation gates:

| Project path | Observable failure and invariant | Decisive evidence example |
| --- | --- | --- |
| Installer or updater | An interrupted upgrade loses user configuration; supported recovery must preserve it. | Configuration-retention and interrupted-upgrade recovery probe on the affected supported platform. |
| Data pipeline | Retrying a partially completed job duplicates a committed record or drops pending work. | Retry the same input after a controlled partial failure and inspect persisted identities and completion state. |
| Agent Skill | A request selects the wrong workflow, crosses authorization, or reports unsupported success. | A realistic request and raw artifacts showing actual routing, permitted actions, and evidence-limited conclusions. |

Record an accepted tradeoff with its authority, rationale, and operating limits. Check
whether the implementation stays within those limits before proposing a change. A
documented preference cannot waive current user requirements or conceal an observed
failure outside the accepted boundary. Keep unknown intent explicit.

Reuse relevant `ENGINEERING.md` context or a project policy explicitly named by the user
or scoped `AGENTS.md`. The mere presence of `ENGINEERING.md` or `REVIEW.md` does not grant
workflow authority; resolve control-file uncertainty through
[authority-and-scope.md](authority-and-scope.md). Treat documentation and these examples
as context, not proof that the reviewer follows them. Behavioral validation, when requested,
must inspect actual decisions and evidence rather than file presence or wording matches.

## Structural clarity and change cost

Trace a representative critical path through domain names, data and state models,
decision owners, and dependency boundaries. Ground clarity concerns in concrete change
sites, contradictory meanings, representable invalid states, or ownership crossings.
Identify the violated invariant or evidenced navigation and maintenance cost; visual
uniformity, shorter code, and preferred naming alone do not establish a finding.

Look for one authoritative home for the same business decision. Similar syntax does
not establish shared semantics, ownership, or change boundaries. Preserve independent
rules and clear local implementations. Before recommending an abstraction, helper, or
layer, name the current consumer, invariant, or evidenced change cost it serves and
compare the smallest adequate alternative. Use existing source and project vocabulary;
do not require a new glossary, diagram, or metric. Investigate justified consolidation
or removal through [simplification.md](simplification.md); retain `KEEP` when the
current structure already fits.

## Compatibility and budgets

Record supported platforms, data formats, public APIs, migration formats, and host
versions. Record performance budgets only when the project or user establishes
them. Otherwise state which metrics require baselining.

Complexity, coverage, duplication, and mutation results are investigation leads. Bind
them to the analyzed source and exercised scope; retain unsupported or skipped paths
as gaps. A metric alone does not establish a finding or justify splitting functions,
merging similar code, or deleting untested code. Identify the violated behavior or
evidenced maintenance cost. Use project-approved tools and thresholds when relevant;
this reference adds no mandatory tool, installation, or universal numeric gate.

## Non-goals

Explicitly exclude capabilities the project does not need. Examples may include
multi-tenancy, enterprise RBAC, distributed services, public APIs, cloud hosting,
or a comprehensive observability platform. Do not deduct points for non-goals.

## Evidence quality

Separate facts, assumptions, and unknowns. A source-backed assumption is not a user
requirement. A stale document is not current runtime evidence. A passing unit test
is not proof of production behavior outside its exercised boundary.

When tests support a material claim, check whether their inputs and assertions would
distinguish the required observable result from a plausible defect on that path.
For example, a retry test that checks only a success status cannot establish that no
duplicate durable record was created. Internal call counts or mocks alone may miss the
claimed outcome. Use the smallest decisive evidence within the review's execution scope.

For a regression, prefer evidence that the relevant test fails on the faulty behavior
for the expected reason and passes after the correction. Reuse existing evidence;
writing or changing tests belongs to authorized remediation. If a practical behavioral
check is unavailable, preserve the evidence gap rather than adding a test that merely
mirrors implementation structure or claiming the behavior is verified.
