# Authority and evidence

Read this for every routed task.

## Durable authority

Choose one and record it before mutation:

- `procedural`: the creation script is primary; `.blend` and `.glb` are derived.
- `native`: the `.blend` file is primary; export settings and manifest make the
  handoff reproducible.
- `hybrid`: `.blend` owns artistic source while scripts own normalization,
  inspection, and export.

Record source hashes, input hashes, tool versions, output paths, licenses, and
manual steps. Reproduction compares normalized scene and GLB semantic facts,
not volatile `.blend` bytes.

After the candidate files and GLB validation report exist, use
`scripts/3d_craft.py bind-asset` to derive `asset.json` and the scene input hash
from observed bytes. Pass the actual asset license explicitly; the command does
not infer ownership or licensing.

For rendered routes, use `init-visual-review` only after the fixed-view report
exists. The generated template begins as `UNVERIFIED` and binds the current
`.blend` plus `render-evidence.json`; it is not a pass receipt. Inspect the
images and complete reviewer identity, review time, overall note, and a
view-backed note for every critical or major identity feature. Any later render
change invalidates the assessment binding.

## Evidence language

Use `SPECIFIED`, `OBSERVED`, `INFERRED`, `HYPOTHESIZED`, and `UNVERIFIED`.
Every `OBSERVED` claim names the file, command, screenshot, or runtime receipt.
Every inference states the evidence it derives from. Never describe an unseen
back side, unmeasured FPS, unopened browser, or unrun host as observed.

## State and files

Store the active state in `run.json`; use `scene.json`, `asset.json`, and
`validation.json` for stable contracts. Evidence files are immutable per
candidate hash. If a repair changes the candidate, generate new evidence rather
than overwriting the prior receipt.

Run data defaults outside the repository. Generated assets may enter a delivery
directory only when the user chose it. Do not place screenshots, render frames,
or Blender backup files beside source code.

Evidence producers and `bind-asset` refuse to overwrite their owned outputs.
`bind-browser-evidence` applies the same rule while copying reviewed browser67
PNG bytes into run-owned evidence and deriving their hashes and dimensions.
Create a new run whenever candidate bytes, the scene contract, or an assessment
changes; do not add a force flag that erases prior provenance.

## Status semantics

- `PASS`: decisive evidence satisfies the gate.
- `FAIL`: decisive evidence contradicts the gate.
- `UNVERIFIED`: evidence was not available or not run.
- `BLOCKED`: a prerequisite prevents evaluation.

Never average a hard failure into a passing score. V0.1 reports gate status,
not a numeric score.
