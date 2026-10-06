# Project Quality Model

## Contents

1. Purpose
2. Critical paths
3. Invariants
4. Compatibility and budgets
5. Non-goals
6. Evidence quality

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

## Compatibility and budgets

Record supported platforms, data formats, public APIs, migration formats, and host
versions. Record performance budgets only when the project or user establishes
them. Otherwise state which metrics require baselining.

## Non-goals

Explicitly exclude capabilities the project does not need. Examples may include
multi-tenancy, enterprise RBAC, distributed services, public APIs, cloud hosting,
or a comprehensive observability platform. Do not deduct points for non-goals.

## Evidence quality

Separate facts, assumptions, and unknowns. A source-backed assumption is not a user
requirement. A stale document is not current runtime evidence. A passing unit test
is not proof of production behavior outside its exercised boundary.
