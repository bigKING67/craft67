# Architecture

Creative Craft separates timeless creative method from changing provider
capabilities and from organization-specific authority.

## Repository boundary

Creative Craft is the public protocol. Company or client authority belongs in
a separate private Primary Brand Skill, creative research belongs in one or
more private Reference Skills, and campaign evidence belongs in a project.

```text
public Creative Craft
  -> 0..1 private Primary Brand Skill -> immutable brand snapshot
  -> 0..N private Reference Skills    -> immutable reference snapshots
  -> project evidence and outputs
```

The public core must not contain proprietary claims, internal links, brand
assets, or organization-specific rules. A thin Brand Skill calls the generic
method instead of copying it. This lets any team install the same Creative Craft
runtime while supplying its own governed authority and non-authoritative
reference intelligence.

## Layers

### 1. Canonical skill

`skills/creative-craft/SKILL.md`

Owns:

- scope and authority;
- evidence states;
- modes and routing;
- end-to-end workflow;
- non-negotiable behavior;
- delivery boundary.

It must not accumulate volatile API parameters.

### 2. References

`skills/creative-craft/references/`

Own reusable professional methods:

- brief and strategy;
- concept development;
- creative direction;
- image and video production;
- existing-asset analysis;
- evaluation/testing;
- iteration/versioning;
- rights/provenance;
- delivery.

References are loaded by task, not all at once.

### 3. Provider profiles

`skills/creative-craft/providers/`

Own dated facts:

- model/version;
- current capabilities;
- limits;
- availability;
- official sources;
- known limitations;
- compatibility notes.

A provider update should not require rewriting the creative method.

Execution surfaces live under `providers/surfaces/` and distinguish the model
from the UI/API used to execute it. A surface declares availability, compatible
provider profiles, supported modes, and surface-specific limitations.

### Private Brand Skills (external)

A Brand Skill is not a directory inside this repository. It owns only curated
brand, product, claims, visual, verbal, channel, rights, source, and Asset Ledger
authority. Large media stays in DAM/object storage; the ledger binds stable URIs
to SHA-256, rights, consent, and allowed use.

`creative-craft.brand-pack.v1` registers the exact authority files and digests.
`creative-craft.brand-binding.v1` records which pack/version/source was copied
into a project. Binding copies registered files and safe local assets into
`.creative-craft/brand-snapshot/`; no live symlink or implicit refresh is
allowed. Updating a snapshot creates a backup and lineage record, then validates
the complete project or rolls back.

### Private Reference Skills (external)

A Reference Skill is not a subdirectory of the public repository or the
Primary Brand Skill. It stores research entities such as brands, companies,
teams, agencies, creators, campaigns, products, visual systems, films,
photography, packaging, editorial systems, or social accounts.

`creative-craft.reference-pack.v1` separates `OBSERVED`, `INFERRED`,
`HYPOTHESIZED`, and `UNVERIFIED` evidence; records transferable principles and
non-transferable expression; binds sources and optional assets; and permanently
sets `may_override_primary_brand` to false. A reviewed source must include a
symlink-free local snapshot whose content SHA-256 matches the manifest.
`creative-craft.reference-binding.v1` records the selected entities, source
identity, and snapshot tree digest. Each update archives its prior Binding as a
registered `creative-craft.reference-binding-history.v1` artifact so the entire
predecessor chain can be resolved and validated.

A project may bind many Reference Packs. Each complete pack snapshot lives at
`.creative-craft/reference-snapshots/<pack-id>/`, each binding lives under
`.creative-craft/reference-bindings/`, immutable predecessors live under
`.creative-craft/reference-lineage/<pack-id>/`, and only assets from selected
entities are merged into the project ledger. Updating one reference creates a
scoped backup and cannot replace the Primary Brand Pack or another Reference
Pack. Every write destination rejects symlinks and project-root escapes. Draft
packs warn but do not block Ready Jobs; revoked packs fail closed; superseded
snapshots remain readable only when already bound as historical evidence.

### 4. Versioned artifacts and schemas

`skills/creative-craft/templates/`
`skills/creative-craft/schemas/`

Own contracts between strategy, direction, production, review, and delivery.
Artifacts are both human-readable and machine-validatable.

Project Manifest v2 makes copy governance explicit with
`copy_policy=required`. `creative-craft.copy-sheet.v1` binds the Brief,
Creative Direction, selected concept/copy routes, evidence-classed proof,
exact copy units, render method, and approval. Image/Video Job v2 points to one
Copy Sheet and explicit copy-unit references. Draft copy is exploratory;
reviewed copy can support internal-ready Jobs; public `ready` or `delivered`
Delivery v2 requires an approved public Copy Sheet with a named owner. Project
Manifest v1 remains readable as a copy-unbound legacy contract and is never
silently upgraded or approved.

### 5. Portable tooling

`skills/creative-craft/scripts/creative_craft.py` is the stable executable and
compatibility facade. Domain truth is owned by:

- `creative_craft_contracts.py`: registries, Schema evaluation, semantic
  artifact validators, and safe atomic writes;
- `creative_craft_project.py`: project graph, cross-artifact invariants, and
  lifecycle projection;
- `creative_craft_evaluation.py`: prompt compilation and evidence-aware score
  projection;
- `creative_craft_packs.py`: Brand/Reference transactions, snapshots, lineage,
  rollback, and write boundaries;
- `creative_craft_project_ops.py`: seed, diagnosis, inspection, revision, and
  delivery CLI operations;
- `creative_craft_runtime.py`: repository/installed-leaf checks and core CLI
  adapters;
- `creative_craft_entrypoint.py`: parser and command dispatch only.

The dependency direction is contracts -> project -> evaluation/runtime, with
pack and project-operation modules consuming those lower layers. Domain modules
do not import the CLI parser. The facade re-exports the historical Python
surface while the public command path and exit codes remain stable.

Standard-library CLI:

- checks repository integrity;
- seeds project authority;
- initializes and validates private Brand Skills;
- binds and explicitly updates immutable project Brand Pack snapshots;
- initializes and validates private Reference Skills;
- binds multiple Reference Packs and updates one immutable snapshot at a time;
- validates JSON Schema structure and cross-field semantics;
- validates a content-bound project graph and derives lifecycle status;
- compiles provider-aware prompts;
- calculates evidence-bound coverage, strength, confidence, and scores;
- hashes assets.

It does not call providers or incur costs.

### 6. Examples and evals

`examples/`
`tests/`
`evals/agent-quality/`
`scripts/evaluate_agent_quality.py`

Examples and unit tests prove that contracts and compilation work. The
repository-only Agent evaluation harness separately compares no-Skill,
temporary committed-comparison, and worktree-candidate behavior in an isolated
Codex and user home, performs blind text scoring, and checks description-level
routing. Event-ledger contracts bind each observed Skill read to the intended
isolated fixture before later calls can run. The comparison export is deleted
after generation. Generated evidence is ignored under
`dist/evals/agent-quality/`; model calls are not part of CI. Subset reports are
supported but cannot satisfy the complete-suite acceptance gate.

This is still not a real Provider-output Golden Eval. A future layer must add
immutable generated images/videos, human judgments, failed revisions, and
controlled comparisons without promoting historical results to current model
guarantees.

## Data flow

```text
private Brand Skill -- source ref/commit and reviewed authority
        |
        v
immutable Brand Pack snapshot -> project BRAND.md / project asset ledger ----+
                                                                             |
private Reference Skills -- evidence states / selected entities / source lineage
        |                                                                    |
        v                                                                    v
immutable Reference Pack snapshots -> selected evidence and assets ------> user / project authority
        |
        v
project manifest -- content hashes and artifact registry
        |
        v
creative brief ---- asset ledger
        |
        v
concept routes -> selected route -> creative direction -> copy sheet
        |                                                 |
        |                                                 v
        |                                      image job / video job
        |                                                 |
        |                                         provider execution
        |                                                 |
        v                                                 v
evaluation <--------------------------- actual output inspection
        |
        v
revision lineage -> adaptation -> delivery manifest -> learning
```

The declared state inside image/video Job v2 is intentionally limited to
`draft`, `ready`, and `superseded`. The resolver projects `generated`,
`inspected`, `revision_required`, `approved`, and `delivered` only when the
corresponding receipt, output file, digest, inspection, approval, and delivery
evidence exists.

Output-stage Evaluation follows the same causal boundary. A Job target is
observed only through a matching Job -> successful Receipt -> declared Output
-> digest-bound Inspection chain. An Inspection from another Job cannot satisfy
the gate. Delivery-stage Evaluation accepts a Delivery v2 target only and
requires every delivered file to resolve through its matching causal chain.
For a copy-bound v2 project, the same delivery transition also requires each Job
to resolve to an approved/public Copy Sheet with a named owner. An approved
sheet cannot retain `HYPOTHESIZED` or `UNVERIFIED` release evidence.

Project seeding uses a same-filesystem staged copy of the complete target tree.
All seed destinations and parents are checked for symlinks and non-directory
collisions before the staged copy is changed. Templates, force backups, the
generated Manifest, and an optional Brand binding are validated together; only
then is the staged directory exchanged with the target. A failed operation
leaves the pre-operation project tree unchanged. Project Manifest authority and
registered artifacts use the same symlink-free containment rule, while
`doctor-project` reports top-level unsafe JSON symlinks without following them
or recursively scanning immutable snapshot contents.

## Why no direct model adapter

The first failure mode of a creative system is usually not API syntax. It is a
missing brief, collapsed concept/execution thinking, vague reference use,
uncontrolled edits, unobserved output claims, or absent rights.

The `0.3.0` release stabilizes the end-to-end evidence contracts. Direct
adapters can be added later as opt-in integrations with explicit credentials,
cost, network, moderation, receipt, and provider-version handling.

## Compatibility principle

Artifacts use versioned `schema_version` values. A future version may add
fields without changing the meaning of existing fields. Breaking semantic
changes require a new schema version and migration notes.

JSON Schema is the structural source of truth. The installed standard-library
runtime interprets the schema keyword subset used by this repository; CI compares
that result with the `jsonschema` Draft 2020-12 reference implementation. Python
semantic validators are limited to Provider/Surface capability rules,
cross-field constraints, digests, references, rights, and lifecycle evidence.
The leaf evaluator implements JSON deep-equality for `uniqueItems`, and the
parity gate generates an invalid duplicate mutation for every `uniqueItems`
keyword in the public schemas. The implementation uses typed canonical keys and
verifies candidates inside collision buckets, preserving JSON equality while
avoiding unbounded quadratic scans. Receipt and approved-Inspection timestamps
must carry a timezone and are normalized to UTC before ordering.

The declared portable runtime is Python `>=3.10`. Installed-leaf execution uses
only the standard library. CI exercises the minimum plus Python 3.11 and 3.13;
repository-only parity and lint dependencies remain development requirements.

## Release package evidence

Repository and installed-leaf checks do not prove the final archive. The release
builder therefore creates one `.tgz`, validates all tar members before extraction,
rejects absolute/traversal paths and link or special-file members, and exercises
the extracted `package/skills/creative-craft` leaf directly. Its self-test and
Reference bind/update/validation/rollback E2E must pass before the package digest
and release receipt are written. This remains package-runtime evidence, not npm
publication or live validation in every compatible Agent host.
