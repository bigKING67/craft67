# Roadmap

The roadmap protects the creative method from premature provider coupling and
separates contract maturity from claims about creative quality.

## 0.1 — foundation

Implemented the canonical skill, authority files, provider profiles, v1 jobs,
prompt compilation, local validation, scoring, tests, and fictional example.

## 0.2 — evidence-bound production graph

Implemented:

- project manifest with safe project-relative paths and SHA-256 binding;
- formal Creative Direction, Image/Video Job v2, Execution Receipt, Output
  Inspection, Revision Lineage, Evaluation v2, and Delivery v2;
- JSON Schema structural truth plus runtime/reference parity checks;
- cross-artifact reference, Provider, Surface, rights, digest, and state
  validation;
- derived job lifecycle rather than generated/approved self-declaration;
- evidence coverage, strength, distribution, confidence, uncertainty, and gate
  projection;
- draft inspection/revision CLI, atomic installer, install provenance, Pi/Codex
  package discovery contracts, and GitHub CI.

This version includes synthetic lifecycle fixtures but no real provider output
claim.

## 0.2.2 — portable brand authority

Implemented without changing the `0.3` Golden Eval milestone:

- generic Brand Pack and project Brand Binding contracts;
- separate private Brand Skill initialization with placeholder-only authority;
- content, digest, path, symlink, rights, consent, source, and approval checks;
- immutable project snapshots with `BRAND.md` projection and Asset Ledger merge;
- explicit snapshot update, previous-binding lineage, backup, full validation,
  and rollback;
- backward compatibility for projects that do not bind a Brand Pack.

No company-specific knowledge or asset is included in the public package.

## 0.2.3 — portable reference intelligence

Implemented without weakening Primary Brand authority:

- generic non-authoritative Reference Pack and multi-binding contracts;
- separate private Reference Skill initialization with empty draft content;
- evidence-classed observations, transferable principles, explicit
  non-transferable elements, source identity, and asset-use policy;
- `0..N` immutable project snapshots with selected-entity asset merge;
- scoped snapshot update, previous-binding lineage, backup, full validation,
  and rollback without changing other packs;
- hard `may_override_primary_brand: false`, revoked-pack rejection, and draft
  warnings that do not block Ready Jobs;
- installed-runtime and package-boundary coverage for the new contracts.

Partner/co-brand federation remains intentionally unimplemented until a real
joint-authority workflow supplies concrete requirements and evidence.

## 0.2.4 — reference evidence and filesystem hardening

Implemented before the `0.3` Golden Eval milestone:

- symlink-safe, project-contained Brand and Reference write destinations;
- exact-tree rollback cleanup for failed snapshot operations;
- copied and digest-verified source snapshots for reviewed Reference Packs;
- registered immutable Reference Binding history with complete chain validation;
- explicit superseded-pack behavior for new and historical bindings;
- installed leaf-runtime bind, update, validation, and rollback E2E coverage;
- safe extraction and the same Reference lifecycle E2E against the exact release
  `.tgz` rather than only the source checkout;
- public release receipts with normalized rather than local absolute paths.

## 0.2.5 — evidence-safe seed and project diagnostics

Implemented without claiming new provider or creative-quality evidence:

- descriptive versus normative authority separation for current and historical
  assets;
- planning-only seed behavior that cannot pre-create lifecycle evidence;
- manifest-registered, Asset Ledger-bound Critique;
- read-only diagnosis of invalid graphs and unregistered known artifacts;
- deterministic `seed_template_residue` classification by SHA-256 identity;
- source, installed-runtime, package-boundary, macOS, Windows, and CI coverage.

## 0.2.6 — review evidence and transaction hardening

Implemented without claiming new provider or creative-quality evidence:

- target-bound output and delivery Evaluation evidence traversal;
- symlink-safe, same-filesystem staged-tree seed transactions;
- symlink-free Project Manifest authority and read-only unsafe-link diagnosis;
- JSON deep-equality for `uniqueItems` plus keyword-complete Schema parity;
- timezone-bearing lifecycle timestamps normalized to UTC;
- repository-local Review Craft E3 and exact packaged-runtime evidence gates.

## 0.3.0 — copy authority and modular runtime

Released on 2026-08-26 without claiming new Provider or real image/video output
evidence:

- first-class Copy Sheet v1 covering strategy, tension, proposition, voice,
  proof, mandatory/prohibited/legal copy, distinct routes, exact units,
  evidence, render method, approval, and unknowns;
- Project Manifest v2 copy binding, reviewed internal-readiness gates, and
  approved public-delivery gates with named owner accountability;
- readable legacy v1/copy-unbound projects without automatic migration;
- domain runtime modules behind the stable CLI facade and domain-split tests;
- random exclusive atomic writes plus fail-closed symlink Project roots;
- indexed `uniqueItems` validation with reference parity and a scaling-ratio
  benchmark;
- declared Python `>=3.10` and expanded CI/package evidence boundaries.
- Quick Craft as the default Agent path, with Traceable Project governance
  loaded only for multi-agent, provenance, approval, or delivery needs;
- a shorter, more discriminating Skill entrypoint that excludes content
  calendars, KOL planning, brand strategy, media buying, UI/UX, and software
  review;
- a repository-only isolated Codex A/B/C text evaluation harness covering nine
  creative cases, blind weighted judging, and four description-routing cases.

The fictional Copy Sheet is reviewed for internal contract testing only. The
text harness incurs model cost and is intentionally outside CI; it does not call
an image/video Provider or constitute a real Creative Golden Eval.

## 0.3.1 — direction-gated refinement and Grok discovery candidate

Implemented as an unreleased, backward-compatible candidate:

- distinguish local/technical defects from feedback that reopens a creative
  direction;
- keep unresolved high-impact direction choices exploratory and bound automatic
  refinement to selected directions, existing execution authority, measurable
  improvement, and a two-pass maximum;
- preserve the best prior candidate and stop when a revision does not improve,
  feedback reopens the direction, or cost/authorization runs out;
- document deterministic fallbacks for exact pixel preservation;
- add Grok discovery documentation and an optional no-model-call host smoke;
- add paired Agent-evaluation cases for unlocked direction change and locked
  local correction without embedding the expected production decision in the
  prompt;
- isolate all user-level Skill discovery roots, verify observed Skill reads
  against digest-bound fixtures, and support honest `PARTIAL` subset reports.

This milestone does not satisfy the real Provider-output evidence planned below
and does not promote Grok to a runtime-verified Tier 1 host.

## 0.3.x — real provider-output creative evals

Planned:

- high-fidelity product edit case;
- exact-copy commercial key visual and adaptation case;
- 15-30 second Seedance product film, extension, and timestamp-edit case;
- immutable actual outputs, human inspections, failed revisions, comparisons,
  and model-version regression baselines.

## 0.4 — Seedance guide internalization

Planned after the owner-supplied official guides are exported and reviewable:

- Jimeng and Doubao Pro surface-specific rules;
- prompt grammar, reference, editing, and extension fixtures;
- official example/source mapping and dated regression tests.

Do not infer an API contract from UI behavior.

## 0.5 — optional provider adapters

Planned only when credentials, cost consent, moderation, errors, receipts,
snapshot identity, and rollback behavior can be tested:

- optional GPT Image 2 Image API / Responses Image Tool adapter;
- Seedance API adapter only after stable official API availability;
- multi-turn and extension receipt lineage.

## Image Harness v1 — local P0/P1 and Provider adapter

The 2026-10-04 [image plan](content-production-architecture.md#image-harness-v1)
extends the existing Image Job method with editable composition, revision-bound
operations, generation candidates and controlled raster compositing. Research
is recorded in the [upstream register](upstream-absorption.md#image-engineering-references)
and the existing drift watch list. The optional source-checkout
[image module](../integrations/image-production/README.md) now implements local P0, P1-A/B and a GPT Image 2.5 adapter;
this is not a released Skill or host integration.

P0 uses Satori/resvg-js/Sharp with a bound static Chinese font, local raster and
text/rectangle objects, immutable revisions, stale/locked edit rejection,
dry-run, undo, preview and PNG export. Fifteen local behavior tests and a
continuous synthetic poster smoke pass on macOS / Node 24, including reopen/
undo PNG parity and 1:1, 4:5, 9:16 output. Real product/brand quality and remote
CI remain unverified; the format and render receipt are local experimental
contracts, separate from formal Image Job/Receipt/Inspection.

P1-A/B adds local candidates, whole-poster comparisons, mutually exclusive
accept/discard, immutable decisions, stale rejection, explicit context and
generation/protection/blend masks. Premultiplied-alpha compositing verifies
protected and outside pixels before acceptance. All 29 local image tests pass;
the candidate smoke and current-session Chinese Agent operation smoke pass,
with visual inspection limited to synthetic posters. Independent Agent, Pi
host and real Provider evidence remain unverified.

P1-C now bridges canonical Image Job v2 and Execution Receipt to a source-checkout
adapter using the authorized global URL/key. Sunburst generation received HTTP
200; the gateway returned 1254×1254 for a 1024×1024 request. An explicit offline,
same-aspect resize preserved the native image and original partial receipt,
then produced an accepted background with price-edit/reopen/undo parity. All
47 image tests pass; default tests and CI use a mock Provider. Live evidence is
PARTIAL in its first round: two generation POSTs, no edit or Flare call then.
A subsequent bounded round completed one real Sunburst masked edit and one
generation per model with the same compiled prompt, 1024-square request and
medium quality. Protected/outside composite changes were zero; visual review
found softer patch texture. Accept/undo/restore/reopen PNG parity passed.
The single generation samples took 26.514 seconds for Sunburst and 23.732 for
Flare through comparison output; these include local processing and do not
establish a stable model ranking. All returned 1254-square PNGs, explicitly
normalized with original files retained. Account cost, actual upstream routing
and real-product quality remain unverified. The adapter profiles stay outside
the released Skill and host registry.

A supplied real GROLAND photo subsequently passed a bounded near-white peripheral
background workflow: original 1254-square pixels were padded, not resized;
one Sunburst edit plus offline blend refinement preserved 515,312 protected
pixels even in the final export. Independent title edits, undo/restore/reopen
and render from an extracted complete-project archive passed. This is a flat
raster scene with separate text objects, not a product cutout; its translucent
appearance retains the old baked-in white backdrop/reflections.

The same real-product project also passed 1:1 (1280×1280), 4:5 (1280×1600)
and 9:16 (1296×2304) adaptations in an independent copy, without model calls.
Copy only changed line breaks; bound assets and fonts stayed identical, and
all 515,312 protected product pixels remained unchanged in each export.
Actual PNGs were inspected. Per-revision reopen, undo/restore and all three
renders from an extracted complete-project ZIP matched their PNG digests;
the original project stayed intact. These generic aspect ratios do not yet
prove platform overlay safety or an integrated Pi/AIOS editing experience.
Evidence: `dist/image-real-formats-2026-10-04-b1440128/format-index.json`,
`visual-inspection.json` and `portability-report.json`.

A real upstream Pi CLI 1.0.0 session subsequently loaded the explicit source
Skill and performed a natural-language title edit, 4:5 reflow and undo on a
copied GROLAND project. Skill/reference reads, revision-bound dry-runs and four
actual image-tool reads were observed. Independent checks passed: 413 changed
pixels inside the title box and zero outside, all 515,312 protected product
pixels unchanged, and undo/reopen PNG parity. The medium-thinking session hit
the 360-second test deadline before its final reply; single-session delivery
remains PARTIAL. A separate low-thinking, read-only session inspected the report
and two images and completed its handoff normally. Both preserved the five
observed Pi/Codex config/auth files. No image Provider calls or shared installs
occurred. Evidence: `dist/image-pi-host-2026-10-04-0419ffc7/acceptance-report.json`.

A subsequent independent full replay on the same configured model with low
thinking completed normally in 285.622 seconds under a 600-second deadline:
20 Agent turns, 25 tool calls, three revision-bound edits, four actual PNG reads
and a final handoff. Protected/title/undo/reopen checks and five global-file
parity checks passed. Single-session bounded CLI delivery now has a PASS sample;
the earlier timeout remains recorded. Different thinking, prompt and deadline
conditions prevent a stable performance conclusion. Evidence:
`dist/image-pi-complete-2026-10-04-dcece006/acceptance-report.json`.

Project-native Pi discovery now has a PASS sample. `.pi/settings.json` selects
the source Skill without `--skill`; both isolated and real-user-settings RPC
probes selected that path when the project was trusted, and selected the
existing shared Skill when project resources were ignored. The real user
default remained deepseek/deepseek-flash. A natural-language session supplied
only the copied project location, found the Skill and executor itself, edited
the title and undid the edit: 213.684 seconds, 18 turns, 17 tool calls, two
revision-bound dry-runs, three actual PNG reads and a normal final handoff.
Independent product/title/undo/reopen checks passed, and five global files plus
the shared Skill tree stayed unchanged. Evidence:
`dist/image-pi-discovery-2026-10-04-989bd3ef/acceptance-report.json`.

The user subsequently authorized a skills-only global Pi configuration delta.
It was applied with a byte-for-byte settings backup. A real-user-settings RPC
probe outside the repository selected the source Skill at user scope without
project resources or `--skill`; defaults, other settings, credentials and the
shared Skill tree stayed unchanged. No model task was submitted. Evidence:
`dist/image-global-activation-2026-10-04-6c060829/activation-receipt.json`.

Actual cross-workspace use also passed on real user settings: the copied
product project lived outside the repository, project resources were ignored,
and the task supplied no Skill/executor path or object IDs. Pi found the source
tools, moved two text objects as one batch, inspected three PNGs, undid the edit
and delivered normally in 279.581 seconds (18 turns, 17 tools). Independent
movement/product/undo checks and relocated project reopen parity passed; all
five observed global files and the shared tree stayed unchanged. Evidence:
`dist/image-pi-cross-workspace-2026-10-04-8021ff3a/acceptance-report.json`.

The reviewed shared upgrade was subsequently authorized and applied: eight
content files updated, seven added, and all 90 equal to source. The full old
directory backup, provenance binding and installed leaf self-test passed.
Codex CLI 0.160.0 natively discovered the shared Skill at enabled user scope
inside and outside the repository; Pi CLI 1.0.0 shared auto-discovery and its
real-user-settings selection of development source both passed, without model
tasks or changes to five observed configuration/auth files. Evidence:
`dist/shared-skill-upgrade-2026-10-04-5bda3972/acceptance-report.json`.
This is an unreleased 0.3.2 candidate, with the optional image executor and
font binaries still outside the shared package. It does not upgrade the
published release or prove model prompt injection.

The current enabled extension configuration subsequently passed a bounded
image edit/undo session, with memory read-only, three actual PNG reads, zero
out-of-box/product-protected pixel changes, relocated reopen parity and all
five configuration/auth guards plus shared-tree preservation. The 233.986-second
repeat retains four installed-package startup dependency warnings; its earlier
attempt remains partial due to unattributed Codex config drift. Evidence:
`dist/image-pi-daily-2026-10-04-e32f1850/acceptance-report.json` and
`dist/image-pi-daily-2026-10-04-f4c86e31/config-drift-note.json`.

The earlier Desktop harness acceptance remains deferred. The running packaged macOS app was observed, but its
image task was not executed because native capture/input failed even after an
isolated reconnect. Preserve the prepared workspace/task and transport receipt
in the earlier attempt directory. Individual extension-tool behavior,
learning-enabled memory and Windows remain separate checks. Keep native
resource discovery, bounded model sessions and packaged host acceptance distinct.

Acceptance closeout also observed an independent branch/HEAD change to
`feat/cut-tools` / `80f0c94eed410ea1c63a86c61b41e8d22eb1e6e0`. The source entrypoint
and image reference remain bound to the observed image session, but the shared
installation now differs by one video reference. Preserve that change; the
prior installation pass applies to its earlier candidate. Evidence:
`dist/image-pi-daily-2026-10-04-e32f1850/source-drift-closeout.json`.
Verify mattes and changed backgrounds through transparent/reflected products,
representative model comparisons and account billing as their use cases arise. Interactive editors,
local ComfyUI execution and segmentation/matting remain conditional on a
demonstrated gap. Provider adapters still need the evidence specified in the
0.5 milestone.

The user's current scope is image engineering only; host extensions and Desktop
transport are not the next work item. A known RGBA product acceptance now checks
light/dark background candidates, opaque-label preservation, partial-alpha
source-over color, move/scale bounds, invisible-RGB resampling invariance,
opacity, contain/cover, undo, reopen and relocation. All 15 checks and 48 image
tests passed locally. Evidence:
`dist/image-alpha-2026-10-04-e029b940/acceptance-report.json`; run
`npm run smoke:alpha` in the image module to retain a fresh project and comparison
sheet. The fixture proves existing RGBA handling, not real-product matting or
glass optics. Next evaluate the user's flat white-background bottle for an
independent matte, edge color contamination, label/shape preservation and
light/dark background fusion before adopting a segmentation/matting component.

That real-product evaluation now has a local Vision/PyMatting comparison and an
independent editable preview project. Packaging RGBA preservation, whole-scene
move/scale, undo, reopen and relocation passed; light output is a review candidate,
while dark output fails due to edge grain and retained white/reflections in the
pool/interior. Evidence:
`dist/image-matte-2026-10-04-4224e675/acceptance-report.json`.
PyMatting remains an isolated research candidate with watched source paths,
not a production dependency. Next resolve foreground color/interior matte and
pool fusion using adequate source evidence; retain the dark failure as an
acceptance case and keep ordinary light-background work on the verified path.

A subsequent single Sunburst transparency request returned actual alpha at the
original 1254-square size, with cleaner outer edges but changed product RGB.
The existing masked compositor restored 291,174 declared opaque core RGBA
pixels, including 59,159 packaging pixels; packaging-only restoration was
discarded for tonal seams. The new independent project retains the previous
light image as current, with the core-protected candidate pending. Reopen,
relocation and extracted-delivery previews match. Evidence:
`dist/image-sunburst-alpha-2026-10-04-3338ec38/acceptance-report.json`.
Dark pool/interior optics still fail. This was an isolated imagegen CLI trial,
not support for transparent jobs in the canonical v2/Adapter at that time.
The subsequent approved contract now supports transparent v2 jobs for explicitly
capable profiles and PNG/WebP; the optional Adapter remains PNG-only. Raw,
normalized and composed alpha checks reject opaque/empty output, bind counts to
bytes and preserve ordinary jobs/receipts. Offline recovery and candidate
readback recheck the evidence. The retained product replay confirms protected
pixels, candidate-only staging, technical accept/undo/reopen/relocation and the
same previously inspected light PNG, with zero external provider requests.
Evidence: `dist/image-transparent-contract-2026-10-04-92fb3d73/acceptance-report.json`.
The formal adapter has now made one real Sunburst transparent edit request
through the configured gateway. HTTP 200 returned actual alpha at 1254 square
instead of the requested 1280 square. Strict validation retained the partial
receipt; explicit offline recovery, protected composition, candidate readback
and relocation passed without another provider call. Visual review rejected
both light and dark output: generated geometry drift produced duplicate pump
and pool contours around the unchanged original core. The candidate is discarded,
its acceptance is refused and the current revision remains unchanged.
Evidence: `dist/image-transparent-live-2026-10-05-f08c2d91/acceptance-report.json`.
This covers a live failure-and-recovery path, not successful extraction quality
or Flare behavior. Add geometry alignment, duplicate parts and protection-boundary
seams to future real-image reviews; alpha and protected-pixel counts alone cannot
approve a result. Local edge repair or better foreground/optical source evidence
was the next bounded quality experiment. Shared installation and release remain
separate; no further broad regeneration is justified by the current result.

The local experiment now limits edits to an asset-specific pump-edge band on
the retained PyMatting result, with zero model requests. The selected variant
changes 3,070 RGBA pixels while preserving the exact 50%-alpha silhouette,
protected core/packaging and every pixel outside that band. Existing local
masked-candidate context, readback, technical accept/undo and relocation pass
14 checks. The delivered project keeps the candidate pending. Actual inspection
shows only a modest reduction in edge grain; the dark pool/interior remains
rejected. Evidence: `dist/image-edge-local-2026-10-05-c1849a62/acceptance-report.json`.
The processing prototype is not a production dependency or a universal matting
tool. Keep broader optical extraction conditional on suitable source material
and representative acceptance; this bounded edge-maintenance case can close.

Standalone candidate render receipts now retain checked-at decision context:
ready/stale/discarded/pending, acceptance history and whether the candidate is
currently applied. The image remains tied to its immutable basis, and visual
quality remains UNVERIFIED; the snapshot is not a future acceptance grant.
Unverifiable decision records fail the render without leaving its output image.
All 72 image tests pass, and three retained real projects show matching PNGs
with the corrected metadata and unchanged project files. Evidence:
`dist/image-candidate-context-2026-10-05-52d098c1/acceptance-report.json`.
No model calls or image-quality claims are added by this receipt correction.

The bounded image-module closeout repaired three validated defects: undo could
reorder a currently locked object, a maximum JSON-escaped discard summary could
be written but not reopened, and live acceptance could report ready when only
the Provider had succeeded. Six targeted checks and all 78 image tests pass;
two independent read-only reviewers confirmed the fixes. Provider outcome and
candidate/comparison readiness now remain separate. Evidence:
`dist/image-closeout-2026-10-05-901be134/acceptance-report.json`.

The same closeout checked five image upstreams. OpenPencil's changed watched
files were reviewed and its research pin advanced; author-aware undo, document
closing, settings and lint are documented as explicit adoption/defer decisions
in `docs/upstream-absorption.md`. The other four watched-path comparisons and
the Satori/Sharp npm versions were unchanged. This is a manual, scoped review,
not an automatic watcher or proof that every upstream is current. The next
quality gate is representative user-approved source material and visual
acceptance; transparent optics remain conditional, not a reason to keep adding
unproven engine features. No new model call, installation or release occurred.

## 1.0 — operational evidence

Requires several real end-to-end projects, current Provider/Surface profiles,
cross-host verification, output inspection evidence, controlled comparisons,
stable migrations, and reproducible release artifacts.

Version numbers indicate contract maturity, not a universal creative-quality
score.
