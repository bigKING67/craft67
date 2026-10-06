# Simplification Proof

Use this reference when the stated objective or a material candidate is to retire
accidental complexity through `CLEAN_UP`, `MERGE`, `REPLACE`, or `DELETE`. It refines
candidate investigation and remediation evidence; it does not define a new Review Craft
mode, score, ledger, report, or source-editing runtime.

This reference selectively adapts simplification concepts from
[`tt-a1i/simplify-codebase`](https://github.com/tt-a1i/simplify-codebase) at reviewed
revision `5da55efcb52db690e7406f06f827a23b15da2706` (original adaptation review:
`add872f3db2a96f90081bedc070dde5d723afa95`), plus structural-review concepts
from Cursor's
[`thermo-nuclear-code-quality-review`](https://github.com/cursor/plugins/tree/main/cursor-team-kit/skills/thermo-nuclear-code-quality-review)
at reviewed revision `6ed0f7a9504f577d7529064103cecce9be7dfc5e` (the tracked Skill blob
is unchanged from original adaptation review `397c8660da6d3d873a91e18c2ca2f22cac1f0ac1`). See the packaged
`THIRD_PARTY_NOTICES.md` for provenance and the MIT license notices.

The absence-evidence and composition-testing guidance also selectively adapts concepts
from [Understand Anything](https://github.com/Egonex-AI/Understand-Anything) at
`6df3065f1d8ddc2ce3615314d1d493f36d6b1c80`. It does not add symbol extraction,
incremental graph reuse, or an automatic deletion decision.

## Contents

1. Qualify the candidate
2. Map consumers and obligations
3. Compare the structural regression delta
4. Investigate beyond the first smell
5. Validate canonical ownership and placement
6. Build the proof record
7. Protect boundaries and lifecycle guarantees
8. Decide on net benefit
9. Evaluate replacement dependencies
10. Verify an authorized cut
11. Preserve design history

## Qualify the candidate

A simplification candidate must name a maintenance obligation that can be retired, such
as a duplicated state, dormant contract, redundant API or forwarding layer, ownerless
extension point, parallel lifecycle representation, obsolete compatibility path, local
infrastructure, or fossil left by a removed feature.

Do not use this reference for style-only cleanup, ordinary naming changes, broad rewrites,
or performance work whose primary claim requires measurement. Fewer lines or files are
supporting observations, not the benefit. `KEEP`, `DEFER`, `MEASURE`, and `DOCUMENT` remain
valid outcomes when the inspected complexity protects a current contract or cannot be
removed safely.

## Map consumers and obligations

Trace the candidate from entrypoints through configuration, registration, dispatch,
persistence, processes, wire formats, generated artifacts, and compatibility paths. For
every search hit, classify the consumer instead of counting it:

- **Runtime**: shipped code, operational configuration, migrations, loaders, packaging,
  deployment, or real entrypoints.
- **Support**: tests, snapshots, documentation, comments, examples proved to be
  illustrative, and generated expectations that do not ship.
- **Uncertain**: public exports, fixtures, reflection, plugins, lazy imports, string
  dispatch, manifests, generated code, examples that may be smoke paths, and consumers
  outside the repository.

Record public, dynamic, persisted, generated, external, and compatibility-sensitive
surfaces separately. An unknown external or dynamic consumer is an evidence gap, not an
assumption of non-use.

The contract map is sufficient only when each in-scope entrypoint and authority boundary
has an owner and observable obligation, and every uninspected or externally unknowable
surface is explicit.

### Bound claims of absence

Keep observed declarations or consumers, analyzer coverage gaps, and possible dynamic
consumers separate. An empty search result, a valid graph, or a successful parse does
not establish that the candidate is absent. Identify the exact path, owner, symbol, and
source state; disclose unsupported syntax, skipped files, scope exclusions, and
unresolved dispatch in the existing proof record.

A deletion or non-use claim needs evidence covering that candidate's possible scope.
Keep a relevant unresolved gap as `Uncertain` and defer the destructive decision until
decisive source or behavior evidence resolves it. Do not let an unrelated local name or
an unrelated skipped file invalidate an independently established fact; explain why the
gap can or cannot reach the candidate. Never infer owner identity from a name match alone.

### Verify the evidence model under composition

When a cut depends on an analyzer's absence claim, test the underlying invariant rather
than only the triggering example. Vary unrelated declarations, nesting, name shadowing,
and line positions: facts about the same consumer must remain stable after source
locations are rebound. Introduce a parse failure or an unresolved dynamic target: reduced
coverage must remain an explicit gap, not become stronger evidence of absence. Include
a known surviving consumer and a verified removal so that both false deletion and
unnecessary blocking are detectable. Use controlled fixtures and existing test tools;
these checks do not authorize executing arbitrary review-target code.

## Compare the structural regression delta

In `diff` mode, compare the baseline and head obligations instead of judging only the
head's absolute shape. Account for concepts, owners, branches, optional states, lifecycle
stages, helper or policy layers, coupling edges, and synchronized edit sites that the
change adds, removes, or relocates. A lower-obligation alternative is material only when
its ownership, compatibility, call-chain, and net-effect claims can be validated; do not
presume that an elegant refactor exists and then use that presumption as a blocker.

File growth and absolute line count may trigger investigation, but no universal file-line
threshold establishes a finding. Validate the maintenance cost: added owner crossings,
duplicated policy, additional state transitions, wider change amplification, or another
violated invariant. Record the delta in the existing candidate and evidence artifacts;
do not introduce a parallel structural-regression score or ledger.

## Investigate beyond the first smell

Use these lenses to generate leads without treating them as findings:

- **Dormant contract**: a public or internal surface has no demonstrated production owner.
- **Split truth**: multiple states, caches, summaries, or event families encode one fact.
- **Ownerless flexibility**: an abstraction, fallback, strategy, or flag promises no
  current product path.
- **Relay layer**: a wrapper forwards behavior without establishing an ownership,
  compatibility, isolation, or policy boundary.
- **Parallel lifecycle**: flags, promises, queues, sentinels, controllers, or callbacks
  represent the same transition for the same owner.
- **Boundary theater**: validation, copying, or rollback protects a trusted same-owner
  handoff rather than a real trust, mutation, lifetime, or failure boundary.
- **Local infrastructure**: custom parsing, retry, framing, matching, diffing, scheduling,
  or collection code owns policy already provided by a suitable platform facility or
  existing dependency.
- **Support drag**: support artifacts are the only remaining consumers of an otherwise
  retired contract.
- **Feature fossil**: schema, configuration, compatibility code, tests, or records preserve
  a capability whose implementation and product owner are gone.

Classify investigation depth independently from the candidate's canonical validation
status:

1. **Smell**: visible awkwardness or duplication.
2. **Static lead**: search or analysis indicates limited use.
3. **Consumer map**: repository hits and relevant callers and callees are classified.
4. **Contract proof**: dynamic, external, persisted, compatibility, ownership, and design
   history questions are resolved or bounded.
5. **Behavior proof**: a decisive check and recovery path would expose an incorrect cut.

Smell and static-lead evidence cannot authorize deletion. A high-confidence destructive
decision normally needs both contract and behavior proof.

## Validate canonical ownership and placement

Treat logic in a surprising layer, a near-duplicate helper, or a feature check scattered
through a shared flow as a lead, not a placement finding. Before recommending
consolidation, identify:

- the existing canonical owner or boundary and the contract it demonstrably owns;
- the duplicated or displaced obligation and whether its semantics actually match;
- affected callers, consumers, and synchronized edit sites;
- compatibility, policy, isolation, or lifecycle reasons that may justify separate owners;
  and
- the ownership obligation that consolidation would retire rather than merely relocate.

Reuse an existing helper only when its current contract covers the required behavior.
Do not turn preferred layering, generic utility placement, or architectural taste into a
finding without a violated invariant or evidenced change-amplification cost.

## Build the proof record

For every lead that could retire a meaningful obligation, preserve this reasoning in the
existing candidate, evidence registry, finding, and decision artifacts:

```text
Candidate: exact contract, representation, or layer proposed for retirement
Burden: synchronization, publication, testing, support, or conceptual cost
Consumer map: Runtime, Support, and Uncertain consumers and blind spots
Current owner: why the surface exists and whether that reason remains current
Cut boundary: declarations, members, branches, artifacts, docs, and dependencies affected
Surrendered behavior: capability, compatibility, or optionality intentionally removed
Confidence and risk: evidence depth, blast radius, reversibility, and remaining uncertainty
Decisive proof: smallest check that would reveal an incorrect cut
Net effect: obligations retired minus replacement and migration machinery introduced
```

Do not create a parallel simplification ledger. Map the record into canonical Review Craft
fields and register any decisive manual artifact before citing it. Prove shared artifacts
below file granularity: account for candidate-exclusive selectors, members, fields, keys,
registry entries, generated fragments, and fixtures while preserving surviving owners.

Keep the canonical finding ID stable across its proof record, source links, and delivery.
Record verified owner, symbol, and path or source-span details; state any missing locus
facts explicitly. Describe topology only when its nodes, relationships, and cut set
are evidenced. This reference does not add a visual companion or renderer.

Lead delivery with the decision, then give the proof record, decision-relevant uncertainty,
and separate validation layers. Do not repeat the investigation narrative or add empty
sections; concision must retain the candidate, evidence strength, consequence, and boundary.

## Protect boundaries and lifecycle guarantees

Before calling validation, copying, retry, rollback, cancellation, or cleanup redundant,
identify the value or resource origin, current and next owners, mutation rights, lifetime,
and failure domain. Preserve authorization, untrusted-input validation, security isolation,
accessibility essentials, data-loss prevention, and durable-format compatibility unless
changing that protection is an independently authorized objective.

For asynchronous or stateful candidates, map each flag, promise, queue, sentinel,
callback, controller, and terminal result:

```text
Mechanism | writer/owner | readers | represented transition | protected failure window |
terminal or cleanup guarantee
```

Two mechanisms are redundant only when they represent the same transition for the same
owner and protect the same failure window. Preserve distinct mechanisms that separately
provide publication rollback, callback isolation, terminal arbitration, worker ownership,
durability transitions, or quiescent disposal.

When related updates can leave a half-applied state, map the precondition, each write or
publication step, observers, failure windows, rollback or compensation, and retry
semantics. Promote the lead only when an intermediate state can violate an observable
contract, corrupt durable truth, mislead a consumer, or make recovery non-idempotent.
Do not recommend parallel execution merely because operations appear independent;
ordering, race, resource, and error-aggregation claims require a complete trace or
measurement under the normal performance and concurrency evidence gates.

For cleanup changes, returning from `dispose` or setting a stopped flag is insufficient.
Name the evidence that no owned timer, listener, stream, process, worker, promise, queue,
retry, descriptor, or deferred write can publish or mutate state after the terminal
boundary.

## Decide on net benefit

Rank confidence separately from benefit. A small proved cut outranks a high-value guess.
Keep, downgrade, or reject the candidate when:

- a current runtime or external consumer exists;
- dynamic, generated, persisted, or compatibility reachability remains unresolved;
- a current decision record still owns the design;
- the change relocates rather than removes complexity;
- replacement or migration machinery costs at least as much as the obligation retired;
- the cut is outside the authorized scope; or
- no available check can distinguish success from accidental breakage.

A conclusion that no safe simplification exists is valid when evidence-backed. Do not
reward deleted lines, candidate count, or dramatic scope.

## Evaluate replacement dependencies

When a simplification proposes replacing local infrastructure with a platform facility,
an existing dependency, or a new dependency, compare the complete obligation delta rather
than source size alone. Record:

- exact semantic parity and any unsupported residual behavior;
- local policy, adapters, wrappers, and dedicated tests that would remain;
- adoption, migration, rollback, and platform-compatibility work;
- release cadence, maintenance ownership, security posture, license compatibility,
  transitive footprint, and supply-chain exposure; and
- local code, dependencies, fixtures, and operational duties that would actually retire.

Prefer a suitable platform facility, then a dependency already present in the product,
and introduce a new dependency only when evidence shows a clear net ownership reduction.
Delegating one primitive while retaining most local policy is not a proved simplification;
preserve that residual contract and choose `KEEP`, `DEFER`, or `MEASURE` when the net effect
is unresolved.

## Verify an authorized cut

Apply source changes only through the existing Review Craft remediation authorization and
host editing boundary. Retire one coherent ownership boundary at a time and account for
the obligation vertically:

- declarations, schemas, commands, options, and manifests;
- registration, dispatch, parsing, and compatibility paths;
- implementations, adapters, state, events, and cleanup;
- imports, exports, packages, builds, and generated inventories;
- migrations, fixtures, examples, documentation, and operational configuration;
- dedicated tests, surviving-contract tests, dependencies, and scripts.

Bind proportionate checks into the existing fix plan and immutable attempt receipts. Use
the applicable widening rings and report each separately:

1. residue search for removed names, formats, flags, paths, and documentation;
2. the decisive behavior check from the proof record;
3. repetition of the discovery query or analyzer that produced the lead;
4. affected-package type, lint, unit, integration, build, generation, or smoke gates;
5. broader repository gates when justified by cost and blast radius;
6. public output, persisted representation, wire behavior, lifecycle, or user-visible
   boundary comparison;
7. complete diff, generated-artifact, dependency-lock, and whitespace audit.

Record the realized net effect, preserved and intentionally changed behavior, remaining
risk, retained candidates, and a recovery path proportional to the side effects. A narrow
green check does not establish integration, deployment, production, or user acceptance.
The Review Craft runtime records this evidence but never edits or rolls back target source.

## Preserve design history

When a selected simplification affects an ADR, RFC, design note, or architectural
inventory, follow the repository's native lifecycle. Classify the older record as current,
partly displaced, or fully displaced from shipped code, configuration, schema, persistence,
wire, migration, compatibility, and inbound-link evidence.

Do not rewrite immutable history merely because implementation changed. Before retiring a
fully displaced record, transfer rationale that still prevents mistakes, including
alternatives, consequences, surrendered capability, reintroduction conditions, and the
new evidence that changed the decision. Repair indexes and inbound links, and leave
uncertain product decisions in the evidence report rather than scattering speculative
TODOs through source.
