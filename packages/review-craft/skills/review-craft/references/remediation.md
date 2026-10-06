# Remediation and Fix Verification

Use this workflow only after a canonical review is sealed and the user explicitly
selects findings to change. The runtime binds evidence and verifies the result; it
never edits the target source itself.

## 1. Prepare before editing

The target must still match the sealed review. Select explicit finding IDs and the
smallest configured command set that can verify them:

```text
python3 <skill-root>/scripts/review_craft.py prepare-fix \
  --run-dir <sealed-run-dir> \
  --finding RC-FINDING-001 \
  --command test
```

Use `--all-actionable` only when the user authorized every actionable finding.
Use `--all-commands` only when running every configured command is proportionate.
`KEEP`, `DEFER`, and `MEASURE` outcomes are not actionable fix selections.

Preparation writes a `review-craft.fix.v1` session outside the target and records:

- the sealed review manifest and selected finding/decision hashes;
- the complete pre-change fingerprint and file hashes for the sealed review's configured
  source projection; excluded and out-of-scope contents remain outside that claim;
- verification criteria and the selected command configuration;
- `EXPLICIT_USER_REQUIRED` as the source-mutation authorization boundary.

Preparation is read-only. If it changes the target, treat that as a defect.

## 2. Apply only the authorized change

After preparation, use the host's normal editing tools to implement only the selected
findings. Preserve unrelated dirty work. Do not let a configured command or the
Review Craft runtime act as a source-editing mechanism.

For `DELETE` or `REWRITE`, follow the migration, compatibility, rollback, and
verification gates already bound in the canonical decision. Stop if those details are
not executable. A decision in a report is not itself authorization to modify source.

For an authorized `CLEAN_UP`, `MERGE`, `REPLACE`, or `DELETE` whose benefit is retiring
accidental complexity, read `simplification.md`. Carry its vertical cut, residue search,
decisive proof, discovery-query repeat, boundary comparison, diff audit, and realized net
effect into the existing fix plan and immutable attempt evidence. Do not create a second
receipt or let the runtime apply or roll back source changes.

## 3. Capture commands before assessment

Use the attempt protocol for new source-checkout workflows:

```text
python3 <skill-root>/scripts/review_craft.py capture-fix-attempt \
  --fix-dir <fix-dir>
```

This creates an independent directory under `<fix-dir>/attempts/`, executes the bound
commands into an attempt-local receipt ledger, and writes:

```text
<attempt-dir>/
├── attempt-manifest.json
├── attempt-evidence.json
└── evidence/
    ├── commands.jsonl
    └── commands/
```

No assessment exists yet. `attempt-evidence.json` records command completion time,
source before and after commands, baseline-relative changes, command and semantic-claim
results, skipped commands, structured claim observations, and classified failure reasons.
The capture exits `0`, `4`, or `5` for `PASSED`, `FAILED`, or `NO_CHANGES`; contract errors
exit `2`. A failed capture is still evidence and must not be deleted or rewritten merely to
obtain a green result.

## 4. Create a post-command assessment

Read the captured receipts and structured stdout, then create the assessment outside the
target repository:

```json
{
  "documentType": "review-craft.fix-attempt-assessment",
  "schemaVersion": "review-craft.fix-attempt.v1",
  "fixId": "rcf-...",
  "attemptId": "attempt-0001-...",
  "evidenceSha256": "<sha256 of attempt-evidence.json>",
  "kind": "AGENT_ASSISTED",
  "assessor": "Codex",
  "assessedAt": "2026-08-02T06:00:00Z",
  "findings": [
    {
      "findingId": "RC-FINDING-001",
      "status": "RESOLVED",
      "rationale": "The captured test claim and measured runtime value match the fix criteria.",
      "evidenceRefs": [
        "change:src/example.py",
        "claim:test:fixed-behavior",
        "measurement:startup-ms"
      ]
    }
  ],
  "measurements": [
    {
      "id": "startup-ms",
      "command": "test",
      "jsonPointer": "/metrics/startupMs",
      "value": 123.5,
      "unit": "ms"
    }
  ],
  "remainingRisks": []
}
```

`assessedAt` must be at or after `attempt-evidence.completedAt`. Evidence references are:

- `change:<repository-relative-path>` for a baseline-relative captured source change;
- `command:<configured-name>` for an executed command;
- `claim:<command>:<claim-id>` for a structured configured claim;
- `measurement:<id>` for an exact scalar read from a command's JSON stdout;
- `manual:<description>` only for a declared `HUMAN` assessment.

The runtime re-reads the command stdout at finalization. A missing pointer, nonexistent
command or claim, or measurement value that conflicts with the captured JSON is rejected.
Free-text rationale does not override structured evidence.

## 5. Finalize, validate, and retry without erasing history

```text
python3 <skill-root>/scripts/review_craft.py finalize-fix-attempt \
  --attempt-dir <attempt-dir> \
  --assessment <assessment.json>

python3 <skill-root>/scripts/review_craft.py validate-fix-attempt \
  --attempt-dir <attempt-dir>

python3 <skill-root>/scripts/review_craft.py list-fix-attempts \
  --fix-dir <fix-dir>
```

Finalization writes `fix-assessment.json` and `attempt-verification.json` exactly once.
Assessment/evidence/finalization timestamp ordering, evidence references, measurements, and
schema fields are validated before either terminal file is written; rejected input leaves
the captured attempt awaiting a corrected assessment rather than a partial terminal pair.
Snapshot validation verifies hashes, receipts, semantic observations, measurements,
assessment timing, finding results, and the predecessor link. Live validation additionally
requires the target to still match captured evidence; use `--snapshot-only` for an older
attempt after the checkout has intentionally moved on.

A retry is permitted only after the previous attempt is finalized and only when all of the
following still match its pre-command source:

- source and worktree fingerprints;
- Git revision, branch, remote, and status fingerprint;
- sealed review and fix-plan provenance;
- selected command configuration.

The retry creates the next attempt directory and binds the prior verification hash. It
does not overwrite the first attempt. A successful retry after an isolated command failure
is projected as `VERIFIED_WITH_RETRY` with `FLAKY_COMMAND_RECOVERED`. A changed source or
configuration requires a new `prepare-fix` baseline instead of being mislabeled as a retry.
Only the latest attempt may await assessment. An orphan receipt, missing predecessor,
deleted failure, modified stdout, changed assessment, or duplicate finalization makes
validation fail closed.

## Legacy `review-craft.fix.v1` compatibility

The legacy v0.5-compatible workflow remains available when a host cannot use attempt
lineage. In this protocol, create the assessment before command execution.

### Create a legacy assessment

Create a JSON assessment outside the target:

```json
{
  "documentType": "review-craft.fix-assessment",
  "schemaVersion": "review-craft.fix.v1",
  "kind": "AGENT_ASSISTED",
  "assessor": "Codex",
  "assessedAt": "2026-07-30T03:00:00Z",
  "findings": [
    {
      "findingId": "RC-FINDING-001",
      "status": "RESOLVED",
      "rationale": "The corrected branch now preserves the validated invariant.",
      "evidenceRefs": ["change:src/example.py", "command:test"]
    }
  ],
  "remainingRisks": []
}
```

Assessment statuses are `RESOLVED`, `LIKELY_RESOLVED`, `PARTIAL`, `UNRESOLVED`,
`REGRESSED`, and `NOT_APPLICABLE`. Assess every selected finding exactly once.

Evidence references are deliberately narrow:

- `change:<repository-relative-path>` must name a file changed from the baseline;
- `command:<configured-name>` must name a command executed by this verification;
- `manual:<description>` is accepted only for a declared `HUMAN` assessment.

An `AUTOMATED` resolved result requires command evidence. Source change alone is not
runtime or behavioral proof. `AGENT_ASSISTED` is not independent human validation.

### Verify and revalidate the legacy session

Run the selected commands and bind the assessment:

```text
python3 <skill-root>/scripts/review_craft.py verify-fix \
  --fix-dir <fix-dir> \
  --assessment <assessment.json>

python3 <skill-root>/scripts/review_craft.py validate-fix \
  --fix-dir <fix-dir>
```

The status is:

- `VERIFIED`: source changed, all selected commands passed, and every result is
  `RESOLVED` or `NOT_APPLICABLE`;
- `PARTIAL`: evidence is valid but at least one result remains likely or partial;
- `FAILED`: a command failed, timed out, mutated source, or a result is unresolved or
  regressed;
- `NO_CHANGES`: the source fingerprint still matches the prepared baseline.

`verify-fix` exits `0`, `3`, `4`, or `5` for those statuses respectively. Contract or
input errors exit `2`. `validate-fix` validates artifact integrity, not remediation
success; a content-valid `FAILED` result therefore validates successfully while still
remaining a failed remediation.

Every fix command receipt is also bound to the selected command configuration stored
by `prepare-fix`. Its name, argv, and cwd must match exactly. Recomputing receipt IDs,
output filenames, or hashes after changing argv/cwd is tampering and makes
`validate-fix` fail with exit `2`.
When a selected command declares semantic claims or artifacts, fix verification preserves
those receipt fields and their content identity. An unverified claim, rejected artifact,
or copied-artifact hash mismatch fails verification even if the subprocess exit code is
zero.

`verify-fix` owns an exclusive session lock from the pre-attempt freshness check through
command execution, assessment binding, terminal artifact creation, and validation. Exactly
one concurrent caller can produce the terminal result; another caller waits for the lock
and then exits `2` because the session is already completed. Sequential repeat calls are
rejected for the same reason.

A fix session is deliberately single-attempt and fail-closed:

- both `fix-assessment.json` and `fix-verification.json` make the session completed and
  read-only;
- only one terminal artifact means the session is incomplete and cannot be resumed;
- command receipts without both terminal artifacts mean an interrupted attempt and cannot
  be reused;
- the receipt ledger must contain exactly the receipts referenced by the terminal
  verification; any orphan or missing receipt makes `validate-fix` fail.

There is no automatic resume or attempt-history protocol in `review-craft.fix.v1`. To rerun
after a crash, rejected attempt, or further source edit, explicitly run `prepare-fix` again
and use the newly created fix session. Preserve the old session as failure evidence or
remove it only under the host's normal artifact-retention policy.

If a verification command mutates source, Review Craft stops before later commands,
records them in `skippedCommands`, and returns `FAILED`. It does not revert the mutation.

Any source change after verification invalidates the result. Prepare a new fix session
after further edits. Keep rollback instructions from the canonical decision available;
the runtime records evidence but does not perform rollback.

## Post-delivery attestation

Fix verification intentionally stops before Git delivery. Keep protocol selection
explicit: `verify-delivery` accepts only finalized legacy `review-craft.fix.v1`, while
`verify-attempt-delivery` accepts only the latest finalized `VERIFIED` attempt from a
lineage whose aggregate is `VERIFIED` or `VERIFIED_WITH_RETRY`. Neither producer searches
backward for an older green result or converts one protocol into the other. Do not rewrite
verification artifacts after commit, push, CI, or release state changes. After the host has
committed a verified fix, create the matching delivery artifact:

```bash
python3 <skill-root>/scripts/review_craft.py verify-delivery \
  --fix-dir <fix-dir>

python3 <skill-root>/scripts/review_craft.py validate-delivery \
  --delivery-dir <delivery-dir>
```

For attempt lineage:

```bash
python3 <skill-root>/scripts/review_craft.py verify-attempt-delivery \
  --attempt-dir <latest-verified-attempt-dir>

python3 <skill-root>/scripts/review_craft.py validate-delivery \
  --delivery-dir <delivery-dir>
```

The local-only result is `PARTIAL`: it proves that the target is a clean Git checkout and
that its current source fingerprint still matches the captured fix verification, while
leaving remote delivery unknown. It does not run a network command.

Use explicit network-backed proof only when the user authorizes it:

```bash
python3 <skill-root>/scripts/review_craft.py verify-delivery \
  --fix-dir <fix-dir> \
  --verify-push \
  --github-run <github-actions-run-id>
```

Use the same flags with `verify-attempt-delivery` when the source protocol is
`review-craft.fix-attempt.v1`.

`--verify-push` runs `git ls-remote` without a shell and verifies that the configured
remote branch SHA equals local `HEAD`. `--github-run` runs `gh run view` without a shell
and binds the run ID, workflow, head SHA, status, conclusion, URL, and normalized job list.
Failed, incomplete, unreadable, or mismatched requested proof produces a valid `FAILED`
attestation. Both producers exit `0`, `3`, or `4` for `VERIFIED`, `PARTIAL`, or `FAILED`;
contract and input errors exit `2`.

Every invocation creates a new content-bound directory under the system temporary directory
or `--output-root`:

```text
<delivery-dir>/
├── delivery-attestation.json
├── delivery-state.json
├── source/
│   ├── fix-plan.json
│   ├── fix-assessment.json
│   ├── fix-verification.json
│   └── source-configuration.json
└── evidence/
    ├── git-remote.json             # only when executed
    └── github-actions-run.json     # only when executed
```

Raw stdout and stderr are not stored. Command argv, duration, exit state, byte counts, and
output hashes remain in normalized evidence. GitHub Release and npm registry adapters are
not implemented in `delivery.v1`; both stages remain `NOT_VERIFIED`. `validate-delivery`
uses only copied artifacts and therefore continues to work after the original fix directory
or target checkout is unavailable.

Attempt delivery uses the separate `review-craft.delivery.v2` schema and copies the whole
canonical lineage rather than only the selected terminal result:

```text
<delivery-dir>/
├── delivery-attestation.json
├── delivery-state.json
├── source/
│   ├── fix-plan.json
│   ├── source-configuration.json
│   ├── fix-lineage.json
│   └── attempts/
│       ├── attempt-0001-<hash>/
│       │   ├── attempt-manifest.json
│       │   ├── attempt-evidence.json
│       │   ├── fix-assessment.json
│       │   └── attempt-verification.json
│       └── attempt-0002-<hash>/
│           └── ...
└── evidence/
    ├── git-remote.json             # only when executed
    └── github-actions-run.json     # only when executed
```

Portable v2 validation checks contiguous sequence, predecessor verification hashes,
manifest/evidence/assessment/verification bindings, deterministic lineage projection,
the selected latest verified attempt, local source fingerprint, delivery ID, and optional
push/CI evidence. It intentionally does not copy raw attempt receipt ledgers or command
stdout/stderr, so the delivery can verify canonical JSON and hash lineage but cannot replay
the raw command payload. GitHub Release and npm registry remain `NOT_VERIFIED` in v2.
