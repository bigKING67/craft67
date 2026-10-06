---
name: 3d-craft
description: "创建/修复/导出/验证 Blender 产品道具、GLB 与 Three.js/R3F 查看器。V0.1 不支持参考图重建、角色、模拟、游戏或 WebGPU。"
license: MIT
metadata:
  author: bigKING67
  version: "0.1.0"
  compatibility: "Portable across Agent Skills hosts; deterministic automation requires Python 3, Node.js 22.12+, Blender 5.2.1 LTS, and Chromium; browser runtime evidence uses browser67; MCP integrations are optional and not bundled."
---

# 3D Craft

Create and deliver 3D work through a visible, reproducible, evidence-bound
production loop. Do not use successful code execution as the completion
criterion. Completion requires the applicable asset, visual, structural,
handoff, runtime, and delivery gates.

## V0.1 product boundary

Support these workflows:

- create a product or prop in Blender from a text brief;
- inspect or repair an existing product/prop `.blend` or `.glb`;
- export Blender work to a validated GLB;
- integrate a GLB into Three.js or React Three Fiber;
- validate a web 3D viewer in a real browser;
- produce a hash-bound evidence and validation report.

Return `unsupported_in_v0_1` for reference-image reconstruction, characters,
sculpting, rigging, complex animation, simulation, games, WebGPU, NeRF,
Gaussian splats, photogrammetry, or external AI 3D generation. Explain the
nearest supported slice without pretending the full request was completed.

## Explanation-only questions

For a conceptual explanation, design discussion, or interpretation that does
not request inspection, creation, repair, export, integration, or runtime
validation of a concrete asset, answer from the supplied facts and state any
unverified assumption. Do not start the production loop, run `doctor`, create
run state, invoke Blender, or open a browser merely to answer it. A later
request to act on an identified asset starts at routing and does not convert an
earlier explanation into production evidence.

## Start here

1. Classify the request. End after an explanation-only answer when no concrete
   production or validation action is requested; otherwise establish the
   target, intent, profile, quality tier, authoring mode, and evidence level.
2. Run `scripts/3d_craft.py route` with fixed enum values.
3. Read only the references named by the route result.
4. Run `scripts/3d_craft.py doctor --json` before tool-backed work.
5. Declare the durable authoring authority and output boundary.
6. Create or load the scene contract before building.
7. After asset and GLB inspection, run `bind-asset` to create the manifest and
   bind the scene hash; do not hand-invent hashes.
8. For rendered work, run `init-visual-review`, inspect the bound views, and
   complete every critical/major feature assessment before claiming identity.
9. For runtime work, use the development Viewer's profile control when strict
   performance evidence is required, link its schema-valid output from the
   browser67 draft, and run `bind-browser-evidence`; do not hand-copy measured
   profile fields, screenshots, or asset hashes.
10. Work in causal stages. At the first failed hard gate, stop downstream
    stages and completion claims; only an authorized smallest causal repair and
    the affected evidence recheck may continue, under the three-attempt limit.
11. Bind every delivered claim to observed evidence, hashes, and versions.

For an end-to-end product asset, the default route is:

```bash
python3 scripts/3d_craft.py route \
  --target bridge \
  --intent build \
  --profile product-asset \
  --quality-tier production \
  --authoring-mode hybrid \
  --evidence-level assured \
  --json
```

Use `procedural` when a Blender Python script is the source of truth. Use
`native` when a `.blend` file is the source of truth. Use `hybrid` for normal
production: the `.blend` owns artistic geometry and deterministic scripts own
normalization, inspection, and export.

## Routing contract

Use only these V0.1 values:

- `target`: `blender`, `bridge`, `web3d`
- `intent`: `build`, `validate`, `repair`
- `profile`: `product-asset`, `prop`
- `quality_tier`: `draft`, `production`
- `authoring_mode`: `procedural`, `native`, `hybrid`
- `evidence_level`: `static`, `rendered`, `runtime`, `assured`

Do not invent a route as free text. A valid route returns selected references,
required capabilities, hard gates, and explicit unsupported features.
`runtime` is invalid for a Blender-only target, and `rendered` is invalid for a
Web3D-only target; use `assured` for the highest evidence applicable to either.

## Authority and evidence

Read `references/authority-and-evidence.md` for every task. Keep these states
distinct:

- `SPECIFIED`: required by a brief, contract, or user instruction;
- `OBSERVED`: directly read from a file, command, renderer, or runtime;
- `INFERRED`: derived from observed evidence with a stated chain;
- `HYPOTHESIZED`: a testable explanation not yet confirmed;
- `UNVERIFIED`: required evidence was unavailable or not run.

Never promote source presence to render proof, a screenshot to interaction
proof, desktop evidence to mobile GPU proof, or a tool plan to a run receipt.
Every visual, performance, and runtime conclusion names its evidence artifact.

Keep run state outside the source repository by default:

```text
$THREE_D_CRAFT_RUN_ROOT/<project-key>/<run-id>/
```

When the environment variable is unset, use the operating system state-data
directory. An explicit absolute `--run-dir` always wins. User-selected final
assets may be copied to their delivery location only after validation.

## Capability discovery

Ask for capabilities rather than one product-specific MCP:

```text
blender.version
blender.inspect
blender.execute
blender.render
blender.export
asset.gltf.validate
asset.gltf.inspect
web.scene.inspect
browser.navigate
browser.capture
browser.console.read
browser.network.read
browser.performance.profile
```

V0.1 prefers Blender headless CLI for Blender work and browser67 for browser
work. Do not fall back from browser67 to an in-app browser. A missing optional
capability makes its gate `UNVERIFIED`; it does not authorize fabricated
evidence.

## Production workflow

Run only the stages selected by the route. A Blender-only asset route does not
start web integration or browser QA; a Web3D route does not start Blender
authoring or export unless the requested repair has an in-scope editable source
asset. A bridge route runs both applicable portions and binds the handoff. Do
not manufacture unused evidence to make a route appear more complete.

### 0. Preflight

Confirm the authority file, write boundary, Blender version, target runtime,
asset licenses, allowed execution, delivery format, and available tools.
Record them in `run.json`. Do not execute unknown Blender add-ons or scripts,
download unlicensed assets, upload private models, or connect to a personal
browser profile.

### 1. Scene contract

Define units, Z-up authoring coordinates, dimensions, origin policy,
components, materials, identity features, cameras, web runtime, budgets, and
required evidence. `required_evidence` must exactly match the deterministic
route; do not add unsupported evidence names or silently omit a routed artifact.
Unknown budgets are `provisional`, never measured facts.

### 2. Blockout

Resolve primary scale, silhouette, part count, relative placement, and camera
framing. Do not spend time on micro-bevels, complex shaders, or decorative
lighting while the shape contract still fails.

### 3. Structural gate

Inspect dimensions, transforms, hierarchy, naming, topology, normals, UVs,
materials, missing textures, cameras, and lights. Render fixed front, back,
left, right, top, and perspective views. Failed proportions return to
blockout; materials do not conceal a shape failure. The render script proves
that images exist and bind to the candidate—it does not prove that they look
correct. Initialize `visual-review.json`, inspect the images, and record
feature-level verdicts, views, notes, reviewer identity, and review time.

### 4. Production modeling and look development

Create deliberate topology, bevels, smoothing, pivots, material regions, PBR
values, UVs, light shape, and camera composition. Read
`references/blender-production.md` for the deterministic Blender boundary.

### 5. GLB handoff

Export with fixed settings, run Khronos validation, then inspect semantic node,
material, primitive, texture, animation, extension, bounding-box, and file-size
facts. Read `references/gltf-web-handoff.md`. Compression is valid only when the
viewer has the corresponding decoder and the optimized asset is revalidated.

### 6. Web integration

Own Loading, Ready, Error, resize, camera framing, color management, tone
mapping, shadows, interaction, cleanup, and reduced motion. In development and
tests, expose the read-only `window.__THREE_D_CRAFT__` observability snapshot.

### 7. Browser runtime QA

Read `references/web3d-runtime-qa.md`. Use a browser67-managed dedicated tab,
background-preferred. Establish and verify the target viewport before waiting
for semantic readiness, inspect console and network, verify RAF progress and
renderer statistics, test remount/dispose behavior, and check desktop plus
mobile layout. A final screenshot may use one bounded foreground interval;
restore or finalize the exact managed task afterward. A viewport transaction
that wakes a hidden canvas is readiness evidence only, not visual acceptance.
For an approved strict profile, call the development/test-only
`window.__THREE_D_CRAFT_TEST__.runPerformanceAndResourceProfile()` control and
save its exact `3d-craft.web-profile-observation.v1` result outside the source
repository. Link that file from a `3d-craft.browser-runtime-draft.v1`
observation as described in `references/web3d-runtime-qa.md`, then run
`bind-browser-evidence`. The command rejects hidden or viewport-mismatched
PNGs, verifies that served and profiled GLB hashes match the candidate, seals
accepted bytes into the run, and writes the candidate-bound
`browser-runtime.json`. External browser-cache paths remain provenance; they
are not portable delivery evidence.

### 8. Validation and repair

Aggregate the applicable gates as `PASS`, `FAIL`, `UNVERIFIED`, or `BLOCKED`.
If a gate fails, read `references/repair-and-security.md` and make the smallest
causal repair. Re-run the same evidence. Stop after three repair attempts and
report the remaining blocker.

## Hard gates

Apply only relevant gates, but never waive one silently:

- `authority`: durable source, version, inputs, hashes, and authorization;
- `reproduction`: clean rebuild or deterministic re-export;
- `scene_integrity`: dimensions, transforms, hierarchy, topology, materials;
- `identity`: required components, proportions, silhouette, key features;
- `gltf`: valid GLB and complete semantic contract;
- `cross_runtime`: asset bounds, pose, materials, and key components survive;
- `web_runtime`: visible model, no blocking error, functioning interaction and
  lifecycle cleanup;
- `delivery`: declared files, evidence, hashes, versions, and limitations.

A hard-gate failure produces `FAIL` without a compensating total score. At the
first failure, stop all downstream stages and do not claim completion. Existing
authorization may cover the smallest causal repair and rerunning the failed or
invalidated evidence, as described in `repair-and-security.md`; it does not
waive the gate or authorize unrelated work. V0.1 does not issue a numeric
quality score.

`static` evidence is useful for preliminary structural inspection, but it
cannot prove silhouette or key visual features. Its identity and delivery
gates therefore remain `UNVERIFIED`; use `rendered` or `assured` for a finished
Blender asset.

## Default V0.1 fixture budgets

These values are approved only for the bundled coffee-grinder evaluation:

- GLB size at most 5 MiB;
- triangles at most 75,000;
- draw calls at most 30;
- textures at most 8;
- frame p95 at most 25ms at 1440x900 in current Mac Chrome, after a three-
  second warmup and over a ten-second sample;
- cross-runtime bounding-box drift at most 0.5 percent;
- required node and material coverage exactly 100 percent;
- front and perspective flat-mask IoU at least 0.92 when comparable captures
  are actually available.

Mobile layout is required. Mobile GPU performance remains `UNVERIFIED` unless
measured on an approved target device.

## Deterministic tools

Run tools from the Skill directory or use absolute paths:

```bash
python3 scripts/3d_craft.py doctor --json
python3 scripts/3d_craft.py init-run --project-key demo --json
blender --background asset.blend --python-exit-code 2 \
  --python scripts/blend_inspect.py -- \
  --scene-contract /absolute/run/scene.json \
  --output /absolute/run/evidence/blend-inspection.json
blender --background asset.blend --python-exit-code 2 \
  --python scripts/render_evidence.py -- \
  --scene-contract /absolute/run/scene.json \
  --output-dir /absolute/run/evidence
node scripts/gltf_validate.mjs asset.glb \
  --output /absolute/run/evidence/gltf-validation.json
python3 scripts/3d_craft.py bind-asset \
  --run-dir /absolute/run \
  --source /absolute/source.blend \
  --license MIT \
  --license-subject "original asset" \
  --json
python3 scripts/3d_craft.py init-visual-review \
  --run-dir /absolute/run \
  --reviewer-kind agent \
  --reviewer-name "<agent identity>" \
  --json
# Inspect the fixed views, then complete evidence/visual-review.json.
python3 scripts/3d_craft.py bind-browser-evidence \
  --run-dir /absolute/run \
  --observation /absolute/browser-runtime-draft.json \
  --json
python3 scripts/3d_craft.py validate \
  --run-dir /absolute/run --json
```

JSON modes write machine output to stdout and diagnostics to stderr. A real
failure exits nonzero. Do not parse human prose as a machine contract.

## Delivery

Deliver only what was produced and checked:

- route and authoring authority;
- source and derived asset paths with SHA-256;
- Blender and runtime versions;
- inspection, fixed-view render, GLB, browser, and performance evidence;
- gate status and issue list;
- exact candidate-scoped command receipts, replayed only with a new empty run
  directory;
- repairs attempted and same-evidence verdicts;
- unsupported, skipped, and unverified scope.

For visible web work, distinguish build success, managed browser behavior,
screenshot artifact, and final visual review. A screenshot existing is not a
visual-review pass by itself.
