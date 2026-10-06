# Traceable Project

Use this mode only when durable project state, multi-agent handoff, repeated
provider execution, formal approvals, provenance, or delivery verification is
material to the work. Quick Craft does not require these artifacts.

## Artifact graph

```text
project-manifest.v2 (project-manifest.v1 remains readable)
-> optional 0..1 brand-binding.v1 -> immutable brand-pack.v1 snapshot
-> optional 0..N reference-binding.v1 -> immutable reference-pack.v1 snapshots
-> brief.v1
-> concept-routes.v1
-> creative-direction.v1
-> copy-sheet.v1
-> image-job.v2 / video-job.v2
-> execution-receipt.v1
-> output-inspection.v1
-> revision-lineage.v1
-> evaluation.v2
-> delivery.v2
```

JSON Schema is the structural authority. The bundled CLI validates structure,
project-relative paths, content digests, cross-artifact references, provider
and surface semantics, rights, and lifecycle evidence.

## State and approval boundaries

Read [copy-sheet-contract.md](copy-sheet-contract.md) before creating,
reviewing, binding, or approving a formal Copy Sheet. It preserves the copy
authority, evidence, render-method, and approval requirements of this mode.

- Manifest v2 uses `copy_policy=required`. Each Image/Video Job binds one Copy
  Sheet plus explicit copy-unit references.
- A draft Copy Sheet supports exploration only. A reviewed Copy Sheet can
  support an internal-ready Job. Public `ready` or `delivered` Delivery v2
  requires an approved/public Copy Sheet with a named owner, approval time, and
  basis. Approved public copy cannot rely on `HYPOTHESIZED` or `UNVERIFIED`
  evidence.
- Job v2 may declare only `draft`, `ready`, or `superseded`. Generation,
  inspection, approval, and delivery are derived from receipts, actual files,
  digests, inspections, and delivery evidence.
- An Execution Receipt proves only what a host/provider attempted. It is not a
  quality approval.
- `inspect-output` creates a digest-bound draft skeleton. The actual image or
  video must be inspected before findings or approval are added.
- Evaluation v2 claims cite resolvable
  `cc://<artifact-type>/<artifact-id>#<json-pointer>` evidence. Coverage and
  strength remain separate; complete prose does not turn a hypothesis into
  strong evidence.
- Delivery v2 marked `delivered` requires real files, digest parity, cleared or
  explicitly limited rights, approved inspections, and linked upstream
  evidence.
- Manifest v1 and legacy copy-unbound Jobs remain readable. Never silently
  upgrade or approve them.

## Brand and reference snapshots

Keep company authority in a separate private Brand Skill. Bind registered
content into the project's immutable `.creative-craft/brand-snapshot/`; do not
substitute a live checkout or symlink. Draft Brand Packs are exploratory and
cannot support a `ready` bound Job.

Keep reference intelligence in separate private Reference Skills. A project
may bind `0..N` immutable Reference Pack snapshots. Every reference entity is
non-authoritative and declares `may_override_primary_brand: false`. Use
`OBSERVED` before `INFERRED`; never present `HYPOTHESIZED` as fact. Public
availability is not permission to use an asset as generation input.

Large assets stay in controlled storage and are referenced by stable URI and
SHA-256. Updates are explicit, scoped, validated, and lineage-recorded; never
silently refresh a historical snapshot.

## Common commands

From the installed `skills/creative-craft` directory:

```bash
python3 scripts/creative_craft.py self-test --json
python3 scripts/creative_craft.py seed --target <project>
python3 scripts/creative_craft.py doctor-project --root <project> --json
python3 scripts/creative_craft.py validate-project --root <project>
python3 scripts/creative_craft.py project-status --root <project> --json
python3 scripts/creative_craft.py score --file <evaluation.json> --root <project>
python3 scripts/creative_craft.py verify-delivery --root <project> --file <delivery.json>
```

For private packs:

```bash
python3 scripts/creative_craft.py validate-brand-pack --root <brand-skill>
python3 scripts/creative_craft.py validate-reference-pack --root <reference-skill>
python3 scripts/creative_craft.py bind-reference-pack --target <project> --reference-pack <reference-skill>
```

`self-test` reports `scope=runtime` in an installed leaf Skill and does not
require repository-only metadata. `seed` is a Traceable Project initializer,
not a prerequisite for ordinary creative responses and not evidence that any
authority was approved, provider was called, or output was inspected.
