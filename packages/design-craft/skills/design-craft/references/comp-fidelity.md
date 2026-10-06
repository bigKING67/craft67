# Comp fidelity measurements

Use this workflow when a supplied comp or approved reference must be compared
with a captured implementation. It produces review evidence, not a visual
verdict.

## Contents

- [Before comparison](#before-comparison)
- [Run and verify](#run-and-verify)
- [Interpret the report](#interpret-the-report)
- [Sealed-rendition orchestration](#sealed-rendition-orchestration)

## Before comparison

- Capture reference and rendered PNGs at the same exact dimensions, viewport,
  device scale, browser/runtime, font state, theme, data state, and animation
  timing. The helper never registers, resizes, or silently aligns images.
- Prefer the existing browser67 or project capture path. This helper is not a
  second browser runtime and does not navigate, authenticate, or capture.
- Define 1–24 task-owned regions in a spec conforming to
  `contracts/comp-fidelity-spec.schema.json`. Each region names its salience and
  relevant dimensions: geometry, type, material, ground, controls, or content.
- Set `changed_pixel_delta` as a measurement noise floor. Optional advisory
  thresholds are project-owned diagnostics; omitting them is valid.
- The portable POC accepts at most four million canvas pixels, four million
  cumulative region pixels, and twenty-four million generated artifact pixels.
  Split larger capture sets into separately reviewed cases instead of widening
  those safety bounds ad hoc.

## Run and verify

```bash
python3 scripts/design_craft_comp_fidelity.py compare \
  --reference /abs/reference.png \
  --rendered /abs/rendered.png \
  --spec /abs/comp-spec.json \
  --output-dir /abs/new-evidence-dir

python3 scripts/design_craft_comp_fidelity.py validate \
  --manifest /abs/new-evidence-dir/report.json \
  --reference /abs/reference.png \
  --rendered /abs/rendered.png \
  --spec /abs/comp-spec.json \
  --strict
```

The output directory must not exist. The helper reads each input once into a
bounded immutable snapshot, computes its size and hash from those same bytes,
then stages and atomically promotes the output directory. Its PNG parser
rejects malformed critical-chunk ordering and trailing payloads. Strict
validation snapshots all three inputs again and recomputes metrics and
generated artifact bytes.
It emits a full heatmap,
side-by-side image, per-region pairs and heatmaps, and `report.json` conforming
to `contracts/comp-fidelity-report.schema.json`.

## Interpret the report

- `mean_delta`, `rmse`, changed-pixel ratio, luminance shift, and edge-energy
  delta are descriptive. They can locate drift; none proves design quality.
- Alpha is ignored in color metrics after PNG decoding. The comparison uses
  8-bit sRGB byte values, not perceptual color-space distance.
- `advisory.status` reports only whether optional project thresholds were
  crossed. It is never a release decision.
- Review primary regions first, then secondary and supporting regions. Use the
  region's named dimensions to explain what differs and whether the comp,
  product authority, or implementation should change.

Final acceptance still requires human visual review plus product correctness,
responsive states, accessibility, interaction, and runtime evidence. Report
the result as `measurement_only` until those separate gates are complete.

## Sealed-rendition orchestration

Use `scripts/design_craft_sealed_rendition_gate.py` when comparison inputs come
from either an existing Shadow Lab fixed commit or a sealed JSON manifest with
a complete file inventory. This wrapper does not navigate, render a PDF, or
capture a browser. It verifies authority first and only then emits an ordered
capture plan for the external runtime.

The spec, capture-plan, and report contracts are:

- `contracts/sealed-rendition-gate-spec.schema.json`
- `contracts/sealed-rendition-capture-plan.schema.json`
- `contracts/sealed-rendition-gate-report.schema.json`
- `contracts/runtime-evidence.schema.json`

For `authority.kind=git_commit`, prepare an existing Shadow Lab and supply its
manifest. When install/build execution is material, bind the exact Shadow Lab
receipt IDs and absolute receipt paths through `authority.execution_evidence`;
the gate then hashes the receipts and their stdout/stderr, rejects nonzero or
source-mutating executions, and preserves the network enforcement mode. For
`authority.kind=sealed_manifest`, supply the immutable root,
manifest path, expected manifest schema, inventory key, and any hash-bound
anchor record groups. All operator paths are absolute; manifest file paths are
safe POSIX-relative paths so the same contract remains portable across hosts.

Run the three phases with a repo-external output root:

```bash
python3 scripts/design_craft_sealed_rendition_gate.py prepare \
  --spec /abs/sealed-gate-spec.json \
  --output-root /abs/new-evidence-root

# browser67 or the selected PDF renderer now writes each planned rendered.png.
# If runtime_evidence was requested, browser67 also writes the planned
# runtime-receipt.json after observing the contracted page and request window.

python3 scripts/design_craft_sealed_rendition_gate.py closeout \
  --plan /abs/new-evidence-root/capture-plan.json \
  --visual-decision pending \
  --visual-note "Awaiting explicit human visual review."

python3 scripts/design_craft_sealed_rendition_gate.py validate \
  --report /abs/new-evidence-root/gate-report.json \
  --strict
```

Prepare creates no output when the authority hash or inventory is wrong, so a
caller can fail before starting browser or PDF work. Closeout rechecks the
preflight snapshot before comparison, runs the existing comp-fidelity engine,
strictly validates every comparison, rechecks authority afterward, and writes
these independent statuses:

- `input_integrity`
- `capture_integrity`
- `comparison_integrity`
- `source_mutation_audit`
- `runtime_evidence` when requested by at least one browser capture
- `visual_decision = pending | pass | blocked | incomplete`

Browser runtime evidence is opt-in and fail-closed. The receipt must match the
planned viewport, DPR, theme, rendered PNG hash/dimensions, and the declared
`offline` or `loopback_only` network contract. A loopback receipt must name the
page origin and contain zero external or unknown origins. Dynamic copy may use
only the declared `wait_for_text_then_pause_animation` stabilization contract:
the selector, exact text, and bounded timeout are fixed in the spec, while the
receipt proves the observed text matched, animation was paused, and neither
source nor displayed text was changed. Arbitrary capture-time scripts are not
part of the contract.

`pass` and `blocked` visual decisions require a named reviewer. A successful
strict comparison never promotes `measurement_only` into visual acceptance.
The report permanently records `global_pixel_pass_threshold: null`: a tiny but
material content error may affect fewer pixels than benign raster variance, so
one global changed-pixel threshold is not a safe release verdict.
