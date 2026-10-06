# Iteration and versioning

Iteration should reduce uncertainty, not create untraceable drift.

## Revision unit

Every revision records:

- source version;
- primary variable changed;
- reason;
- change instructions;
- preserved invariants;
- provider/model or production method;
- output version;
- observed result;
- decision;
- next action.

## Edit strategy

Use the smallest valid intervention:

1. copy or metadata correction;
2. local edit;
3. composition or timing edit;
4. regeneration with stronger constraints;
5. route-level rework;
6. new concept;
7. live reshoot or manual production.

Do not regenerate an entire asset to fix a local issue when a reliable local
edit exists. Do not keep patching a fundamentally wrong concept.

## Convergence gate

Iteration follows the state of the direction:

- **unselected or reopened direction:** reduce uncertainty with a small set of
  distinct routes or one decisive question; do not auto-polish one candidate;
- **selected direction with a bounded defect:** use the smallest reliable edit;
- **selected direction with a structural failure:** recompose or regenerate,
  while preserving the selected premise and stated invariants;
- **approved output with a technical defect:** use deterministic correction
  when exact text, size, crop, or unchanged pixels are required.

Feedback that changes shot scale, subject hierarchy, visual world, narrative
mechanism, or product role reopens the direction even when the current asset is
technically well made. Explicit current feedback outranks an earlier Agent
recommendation.

## Bounded refinement loop

After direction selection and execution authorization:

1. inspect the actual output;
2. identify one primary causal variable;
3. produce a targeted revision;
4. compare it with the best prior candidate;
5. keep the better candidate and stop or repeat once.

Two targeted passes are a maximum, not a completion requirement. Stop early
when the asset passes, the revision does not materially improve it, direction
feedback reopens, evidence conflicts, or the cost/authorization boundary is
reached. A critique or refinement request does not by itself authorize a
networked or cost-bearing provider call.

## Single-change rule

Default to one primary change per iteration. Supporting changes may be required
for integration, but name them.

Example:

```text
Primary change: reduce foreground hand scale by 40%.
Preserve: jewelry geometry, stone texture, cord knots, bead count, lighting,
crop, background, copy, and all other subjects.
Integration: reconstruct only the newly revealed background.
```

## Shared project revisions

For human and Agent edits to the same project, read the latest project before
writing and use the host's revision precondition or equivalent concurrency
control. A saved project revision and a rendered output version are separate:
record which revision produced the inspected output.

On a conflict, re-read and reassess the intended change against the user's latest
edits; never replay a stale whole-project snapshot over them. If the host has no
safe concurrent-write mechanism, use a supported isolated copy or serialized
editing session. Otherwise keep the change as a proposal and explain the limit.

After a timeout or ambiguous mutation result, inspect project/job state before
retrying. Use a host-supported idempotency mechanism when available; do not
blindly duplicate edits, renders or cost-bearing generation. For partial success,
report what actually persisted and repair only the remaining authorized scope.
Rollback must preserve newer unrelated edits: use a revision-aware undo or a
bounded corrective edit rather than restoring an old snapshot indiscriminately.

See [video-production.md](video-production.md#editing-an-existing-project) for
source/instance targeting and audiovisual verification. These rules apply when
editing shared project state, not to an ordinary copy suggestion or critique.

## Naming

Recommended:

```text
<project>_<route>_<asset>_<channel>_<ratio>_v###.<ext>
```

Example:

```text
northstar_motion-is-proof_hero_douyin_9x16_v004.mp4
```

Do not encode approval solely in a filename. Approval belongs in the manifest.

## Status

- `exploration`;
- `candidate`;
- `selected`;
- `needs_revision`;
- `approved`;
- `delivered`;
- `superseded`;
- `rejected`;
- `archived`.

## Prompt lineage

Record:

- prompt text or hash;
- reference asset IDs and roles;
- provider/model/snapshot when available;
- output parameters;
- generation or edit time;
- operator/host;
- output asset ID/checksum;
- moderation or provider error;
- review decision.

When a host does not expose seed or internal settings, record `not_exposed`
rather than inventing them.

## Adaptation

An adaptation remains the same concept only if its mechanism and proposition
survive. Mark `concept_changed: true` when a channel version introduces a new
mechanism, claim, or narrative.

## Rollback

Keep the selected source and prior approved output until the replacement is
validated. Destructive cleanup follows delivery, not experimentation.
