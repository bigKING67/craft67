# Change: Fix research status reliability (UP-01)

## Why

Unknown hypothesis/red-line evidence currently produces SUPPORTED with ten points. Tracking status echoes unverified historical pointer values. Decimal nonfinite inputs and overflow can escape the calculation audit. Research documents can cite internally consistent source IDs that are absent from the actual run evidence.

## What Changes

- Introduce tracking v2 output with nullable scores and explicit WATCH/UNVERIFIED states; preserve verification of sealed v1 records without rewriting them.
- Derive current tracking assessment from verified artifacts and an optional research-defined review deadline. Missing, future or expired review windows do not produce current support or scores.
- Reject nonfinite financial inputs and surface calculation failures as failed audits.
- Bind report and thesis citations to captured/imported evidence; distinguish workflow completion, evidence coverage, citation integrity and unverified semantic support/freshness.
- Update Skill references and behavior regressions. Keep the existing Python core, CLI workflows, provider-gap policy and package boundaries.

## Authorization and Scope

The user requested continuation after the upstream-governance delivery explicitly identified UP-01 as the next capability. This is that authorized reliability batch. No account access, trading, installation, commit, push or application work. Automated issuer/filing-period semantic validation is not added: its absence remains UNVERIFIED rather than being implied by successful ingestion.

## Compatibility and Rollback

New tracking state/current/revision/status use explicit v2 schemas because null scores and new states change the consumer contract. Original v1 schemas remain for sealed history. Legacy workspaces must update state to v2 before sealing. Research assessment fields are additive; legacy completion receipts remain inspectable and current assessment is recomputed.

No historical artifacts are migrated. Reverting code does not make old readers understand new v2 artifacts; retain a v2-capable reader once new tracking revisions exist. Before delivery, validate legacy verification, unknown/adverse cases, stale windows, invalid pointer/citation/number failures and temporary packaged runtime behavior.
