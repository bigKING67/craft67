# Visual reference workflow

Use this contract for discovery-source research, Reference Cards/Packs,
reusable pattern promotion, or Shadow Labs. A reference is evidence for a
bounded design mechanism, not permission to copy a brand or override project
authority. Direct supplied/selected-image implementation uses
`image-reference-implementation.md`; requested web comps use
`web-image-direction.md`. Those tasks do not require a catalog or Pack unless
they also enter the discovery or pattern-promotion workflow.

## Contents

- [Authority and source classes](#authority-and-source-classes)
- [Reference Card](#reference-card)
- [Review procedure](#review-procedure)
- [Reference Pack](#reference-pack)
- [Pattern promotion](#pattern-promotion)
- [Peekpaper adapter](#peekpaper-adapter)
- [Evidence and artifact boundary](#evidence-and-artifact-boundary)
- [Runtime-unavailable visual baseline](#runtime-unavailable-visual-baseline)
- [Disposable Shadow Lab](#disposable-shadow-lab)
- [Comparative Shadow Lab closeout](#comparative-shadow-lab-closeout)
- [Operational cadence](#operational-cadence)
- [Completion](#completion)

## Authority and source classes

Resolve conflicts in this order:

1. User constraints and the target's live runtime behavior.
2. Scoped `PRODUCT.md`, `DESIGN.md`, tokens, components, and platform rules.
3. An approved Reference Pack for the current task.
4. Reviewed Reference Cards.
5. Mutable discovery sources such as Peekpaper.

Discovery sources are not code upstreams, product requirements, design-system
authorities, engineering proof, or training corpora. Keep source observations
separate from target-project decisions.

## Reference Card

Use `design-craft.visual-reference-card.v1`. Every card records:

- canonical discovery and origin URLs plus observation date and source digest;
- source surface, product archetype, possible reference roles, and target fit;
- desktop, mobile, origin-runtime, interaction, accessibility, and performance
  evidence with explicit observed, partial, unverified, or unavailable states;
- observations, transferable mechanisms, do-not-copy boundaries, and cases
  where the reference is unsuitable;
- reference-only rights, lifecycle, and any later project validation.

A screenshot may establish composition, hierarchy, type scale, color
relationships, and visible desktop/mobile differences. It cannot establish
hover, focus, loading, errors, accessibility, performance, DOM semantics, or
interaction physics.

## Review procedure

1. Classify the target surface as `Persuade`, `Operate`, `Read`, or
   `Experience` from its primary job, not its brand category.
2. Observe desktop and mobile separately. Record only visible facts.
3. Name the mechanism without brand nouns. Prefer causal language such as
   "proof follows the promise before detailed features" over visual labels
   such as "large hero".
4. Record what must not transfer: trademarks, copy, proprietary imagery,
   distinctive illustration, exact geometry, and unsupported interactions.
5. Record target modes where the mechanism is useful or blocked.
6. Audit the origin only when a claim depends on runtime behavior. Preserve
   inaccessible states as unavailable or unverified.
7. Set a review-after date. A stale card cannot enter a ready Reference Pack.

Review outcomes may be `reviewed`, `exemplar_only`, `rejected`, or
`unavailable`. Do not force a positive outcome to satisfy a sample count.

## Reference Pack

Use `design-craft.visual-reference-pack.v1` immediately before target design or
implementation. A ready Pack contains one to three cards total, including any
counter-reference. An incomplete diagnostic Pack may contain zero when no
selection is usable. Each selected card has exactly one role:

- `structure`: information order, grouping, or composition;
- `responsive`: reprioritization across viewport or platform constraints;
- `tone`: typography, color relationship, density, or visual rhythm;
- `interaction`: origin-audited behavior only;
- `counter_reference`: a concrete example of what the target must reject.

For every positive reference, copy reviewed mechanisms into `adapt`, explicit
boundaries into `reject`, and incomplete evidence into `unverified`. A positive
reference blocked for the target surface makes the Pack incomplete. At least
one positive reference is required.

## Pattern promotion

One work is an exemplar, not a pattern. Promotion requires:

1. at least three reviewed cards with different origin URLs supporting the
   same mechanism;
2. at least one origin live audit for a runtime-dependent claim;
3. at least one target project or prototype validation;
4. a comparative evaluation using the same target input and acceptance rules.

Only then may a hypothesis move through `proposed`, `project_validated`,
`comparative_validated`, and `absorbed`. Golden contract fixtures prove schema
and blocking behavior; they do not satisfy target or comparative evidence.
One artifact may satisfy only one promotion rung for a given hypothesis:
`target_validation_refs` and `comparative_eval_refs` must be disjoint. A first
target result cannot be counted again as the later comparative evaluation;
promotion requires a distinct result with its own pre-registered comparison.

## Peekpaper adapter

Peekpaper is a mutable discovery source. Prefer its official issue JSON over
HTML scraping and cite the canonical post HTML page. The portable adapter:

- permits only explicit issue dates at the official HTTPS issue endpoint;
- defaults to offline fixtures and requires `--allow-network` for live fetches;
- limits issue count, post count, response size, timeout, content type, and
  redirects;
- keeps public title, origin, description, capture availability, dimensions,
  and capture time while discarding internal selection fields and CDN keys;
- never downloads or redistributes screenshots;
- permanently enforces reference-only, no-training use.

If the source policy becomes stricter, stop online refreshes until the policy
is reviewed. Source availability never changes project authority.

## Evidence and artifact boundary

Keep screenshot PNGs repo-external. Checked-in manifests may record a portable
artifact reference, viewport, byte size, SHA-256, dimensions, target URL,
observation time, and availability. A local-only path is not remote or release
evidence.

Origin audit should cover desktop and mobile, page structure, one meaningful
reachable interaction, keyboard focus, visible semantics, and console errors.
Check Reduced Motion only when motion exists. Keep complete accessibility and
performance status unverified unless separately measured with the applicable
contract.

## Runtime-unavailable visual baseline

When the target app cannot run, start with a committed visual-regression golden
or screenshot fixture only when the target repository owns it. Treat this as a
runtime-unavailable fallback, not as a replacement for current browser or
native evidence:

- resolve the exact tracked target, repository revision, viewport, theme, and
  variant that the artifact claims to represent;
- compare its provenance and capture context with current tokens, CSS,
  components, assets, content shape, and applicable platform rules;
- inspect every relevant committed theme or variant capture instead of choosing
  the most favorable image;
- mark the sample `stale` or `unavailable` when its target, freshness, or
  capture context cannot be reconciled with current source;
- use a valid sample only for visible composition, hierarchy, density, color,
  and regression hypotheses. Keep interaction, focus, accessibility,
  performance, and current runtime behavior unverified.

An untracked screenshot, unexplained export, or stale golden is not an
incumbent visual authority. When live validation is required but unavailable,
the task remains `incomplete` even if the fallback is useful for diagnosis.

## Disposable Shadow Lab

Use `scripts/design_craft_shadow_lab.py` when a real target repository is only
an evaluation input and must not receive edits, generated files, dependency
installs, test artifacts, or cleanup. The helper creates a repo-external
snapshot from one resolved Git commit. It does not copy dirty tracked content,
untracked content, `.git`, submodules, or symlinks.

The manifest contract is
`contracts/shadow-lab-manifest.schema.json`. It records the fixed commit,
repo-external worktree, source status and tracked-diff digests, dirty path
metadata, Git index metadata, and an explicit `source_writes_allowed=false`
boundary. Dirty and untracked file contents are not read for baseline capture.

Resolve `DESIGN_CRAFT_RUNTIME` to the absolute directory of the loaded Skill,
as described in `SKILL.md`. The commands below work from either the source
repository or the target directory; their script path is never target-relative.
Use `PYTHONDONTWRITEBYTECODE=1` for direct Python checks in the source repository.

Prepare and inspect a lab:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 "$DESIGN_CRAFT_RUNTIME/scripts/design_craft_shadow_lab.py" prepare \
  --source /absolute/path/to/target-repo \
  --ref <full-commit> \
  --network-policy install_only \
  --output-root /tmp/design-craft-shadow-labs
PYTHONDONTWRITEBYTECODE=1 python3 "$DESIGN_CRAFT_RUNTIME/scripts/design_craft_shadow_lab.py" verify \
  --manifest /tmp/design-craft-shadow-labs/<lab-id>/.design-craft-shadow-lab.json
```

`prepare` declares a network policy but does not claim to enforce or observe a
command that has not run. Use `execute` for each evidence-bearing phase:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 "$DESIGN_CRAFT_RUNTIME/scripts/design_craft_shadow_lab.py" execute \
  --manifest /tmp/design-craft-shadow-labs/<lab-id>/.design-craft-shadow-lab.json \
  --evidence-id install \
  --phase install \
  --network-mode allowed \
  -- pnpm install --frozen-lockfile

PYTHONDONTWRITEBYTECODE=1 python3 "$DESIGN_CRAFT_RUNTIME/scripts/design_craft_shadow_lab.py" execute \
  --manifest /tmp/design-craft-shadow-labs/<lab-id>/.design-craft-shadow-lab.json \
  --evidence-id build \
  --phase build \
  --network-mode denied \
  -- pnpm build
```

`denied` is evidence only when the host has a supported enforcer. The current
implementation uses macOS `sandbox-exec` with `deny network-outbound`: external
egress is denied while local IPC remains available to build tools. Unsupported
hosts fail closed instead of relabeling an ordinary subprocess as offline.
`allowed` means no denial was required by the declared policy, not that network
traffic occurred. Each command writes a manifest/commit/worktree-bound receipt
plus hashed stdout and stderr outside the disposable worktree. `verify` reports
`unverified`, `observed`, or `failed` from those receipts; a failed receipt
makes verification return nonzero. The legacy
`network_allowed=false` manifest field means the helper itself grants no
network authority; actual phase truth is the explicit `network_boundary` and
its receipts.

For a retry, use a new `--evidence-id` and retain the previous receipt and logs.
Report `source.source_unchanged`, individual phase outcomes, and aggregate
`boundary.network.evidence_status` separately. A successful retry does not
erase an earlier failure: aggregate verification still fails and returns
nonzero. State which attempt succeeded and which evidence remains incomplete;
never delete failed receipts or reinterpret aggregate failure as proof that
the latest build failed. Invalid receipts or source drift are not retry success.

Choose `execute --timeout-seconds` for the expected phase before starting it.
Install readiness is a completed package-manager command; build readiness is
a completed build plus its expected outputs. For a persistent preview, use the
task's managed process runner and require a listening port plus a successful
local HTTP/health response, not process exit. Record preview/browser evidence
separately from build receipts and stop task-owned servers after inspection.

If a launcher stalls, inspect the bounded task process tree and captured output
before retrying. When the installed CLI can perform the same selected phase,
calling it directly is an option; record the exact executable/arguments and
any project-script steps it omits. Preserve the original network restrictions
and package policy. Direct CLI success does not certify omitted build steps.
Browser tab and empty Agent-window cleanup outcomes are separate; report an
external browser cleanup error without broadening cleanup or repairing the
browser runtime as part of a design task.

Run only the selected design-craft checks against the manifest's `worktree`.
Do not point package managers, formatters, screenshot output, caches, or build
output at the source repository. A build may mutate the disposable worktree;
that is acceptable, but it is not evidence that the source repository changed.
The workflow does not independently authorize network access or other external
side effects; `--network-policy` records authority already granted by the
caller.

Cleanup is fail-closed and requires the root ownership marker, the direct-child
lab layout, disjoint source/output paths, and explicit confirmation:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 "$DESIGN_CRAFT_RUNTIME/scripts/design_craft_shadow_lab.py" cleanup \
  --manifest /tmp/design-craft-shadow-labs/<lab-id>/.design-craft-shadow-lab.json \
  --confirm
```

`verify` and `cleanup` report whether the source baseline still matches. A
source mismatch remains visible even though confirmed cleanup removes only the
owned lab. Never report Shadow Lab success as browser, native, production, or
visual acceptance evidence; it proves snapshot and source-write boundaries.

Package managers may add internal symlinks inside the disposable worktree.
`verify` fingerprints those links without following them only when their
resolved targets remain inside the lab. Absolute or escaping links still fail
closed. The fixed-commit snapshot itself remains symlink-free.

On POSIX hosts, the output root must be owned by the current user and deny
group/other access. Native Windows access control is ACL-based, and Python's
POSIX ownership and mode fields do not prove ACL privacy there, so the helper
does not apply those two POSIX checks on Windows. It still requires a real,
disjoint directory, an owned root marker, a direct-child lab layout, and scoped
cleanup. This contract does not claim that Windows ACLs were audited.

## Comparative Shadow Lab closeout

After two to five genuine directions have been implemented and observed, use
`scripts/design_craft_shadow_compare.py` to bind the comparison. This is a
closeout contract, not a design generator or permission to promote production
code. It requires:

- distinct Shadow Labs using the same source repository and fixed commit;
- one shared target job, acceptance rules, required evidence roles, and runtime
  checks;
- a named divergence axis, hypothesis, invariants, and risks for each variant;
- repo-external, hash-bound artifacts that cover every required evidence role;
- the same runtime-check IDs for every variant, with failed and unverified
  states kept visible;
- an explicit `absorb`, `adapt`, `reject`, and `unverified` decision record.

Create the spec outside the source repository, then write the comparison beside
the external evidence bundle:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 "$DESIGN_CRAFT_RUNTIME/scripts/design_craft_shadow_compare.py" create \
  --spec /absolute/external/path/comparison-spec.json \
  --output /absolute/external/path/comparison.json
PYTHONDONTWRITEBYTECODE=1 python3 "$DESIGN_CRAFT_RUNTIME/scripts/design_craft_shadow_compare.py" validate \
  --manifest /absolute/external/path/comparison.json \
  --require-live-labs
```

Use `ready_for_selection` when no direction has been chosen. `recommended`
requires the user to have delegated the recommendation; `selected` requires an
explicit user selection. Every comparison fixes
`production_promotion_authorized=false`: choosing a direction and authorizing
production edits remain separate scopes. Static validation preserves the
artifact hashes after closeout; `--require-live-labs` additionally rechecks
the retained labs, their current tree fingerprints, and the source baseline.

## Operational cadence

Use a bounded manual cycle rather than a crawler or archive import:

1. ingest no more than a small set of issues;
2. shortlist for product and surface diversity;
3. review a smaller set of cards;
4. live-audit only claims that need origin runtime evidence;
5. build a task-specific Pack;
6. validate on the target before considering promotion.

Do not batch the full archive. New source material can add candidates without
changing installed design rules.

## Completion

Reference work is complete only when:

- the card, catalog, or Pack passes its machine contract;
- authority, target fit, evidence limits, and rights are explicit;
- unavailable and stale evidence remains visible;
- no third-party screenshot or asset entered the repository or package;
- no candidate or proposed hypothesis is reported as an absorbed capability.
