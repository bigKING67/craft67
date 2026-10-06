# Image production

Image production begins with a job specification, not a decorative prompt.

Read the matching dated provider profile before using model-specific features.

Transparent v2 output requires a capable profile and PNG/WebP. Check actual
alpha, protected pixels and light/dark composites; alpha is not optical approval.

## Choose the workflow

### Generate

Use when the image is created from a brief, concept, or reference system.

### Edit

Use when a supplied image must remain recognizable and only selected elements
may change.

### Single-turn

Use for one prompt and one generation/edit decision.

### Multi-turn

Use when the work requires iterative visual conversation, several constrained
edits, or reference continuity. Maintain a revision ledger and repeat
invariants in every turn.

## Direction and framing preflight

Before spending a refinement pass, identify the high-impact choices that
define the image rather than its finish:

- shot scale: close-up, medium view, or wide/environmental view;
- subject role: dominant hero, co-equal object, or discoverable element within
  a larger scene;
- approximate subject scale in frame and the intended attention sequence;
- environment density, negative space, and spatial depth;
- whether props form a deliberate relationship through shape, scale, material,
  and placement or merely decorate the product;
- whether the supplied images contain watermarks, UI, signatures, or incidental
  text that must not transfer;
- whether a user, creative lead, or other decision owner has selected the
  direction.

Terms such as editorial, luxurious, cinematic, or object-focused are not a
direction lock by themselves. Translate them into visible relationships. When
feedback changes one of the choices above, return to composition/direction
exploration instead of treating the request as a local correction.

## Image job fields

A production-ready image job contains:

- job ID and schema version;
- intended use;
- task type;
- provider and model;
- execution mode;
- output size, quality, format, JPEG/WebP compression, background, and variant count;
- scene/background;
- subject;
- action or expression;
- composition, viewpoint, framing, and negative space;
- lighting;
- materials, medium, texture, and style;
- exact text and typography;
- reference assets and roles;
- change list;
- preserve list;
- constraints and exclusions;
- inspection checklist;
- rights and approval state.

## Prompt architecture

Use a stable, skimmable order:

```text
INTENDED USE AND OUTPUT
BACKGROUND / SCENE
SUBJECT
ACTION / EXPRESSION
COMPOSITION / CAMERA / NEGATIVE SPACE
LIGHTING
MATERIALS / MEDIUM / STYLE
EXACT TEXT / TYPOGRAPHY
REFERENCE MAP
CHANGE
PRESERVE
CONSTRAINTS / EXCLUSIONS
```

A production prompt should be precise enough to execute but not overloaded with
irrelevant adjectives.

## Specificity

Prefer concrete control:

- brushed aluminum, translucent amber liquid, uncoated paper;
- centered three-quarter product view, camera slightly above label height;
- soft directional light from upper left, restrained specular highlights;
- 18% empty space above the cap for headline;
- warm white background, no visible horizon line.

Avoid empty quality stacks:

> premium, stunning, cinematic, 8K, masterpiece, elegant, high-end

Use quality cues only when they translate into visible choices.

## Exact text

- quote exact text;
- specify capitalization, line breaks, hierarchy, alignment, and placement;
- state that no other text may appear;
- inspect spelling and glyphs after generation;
- use a separate typesetting step when pixel-accurate typography is critical.

## Reference roles

Map by asset, not by vague similarity:

```text
@Image 1 — preserve product geometry, label, cap, and liquid color.
@Image 2 — lighting direction and shadow softness only.
@Image 3 — composition and negative-space proportion only.
```

Do not ask the model to infer which parts of a reference matter.

## Edit contract

Use:

```text
CHANGE ONLY
- ...

PRESERVE EXACTLY
- ...

INTEGRATION
- reconstruct only what is revealed;
- match existing light, perspective, grain, and depth of field.

DO NOT ADD
- ...
```

For identity-, product-, packaging-, or logo-sensitive work, repeat invariants
on every edit.

## Mask-guided edits

For masked edits, declare the source and each mask's role, aligned dimensions,
format and polarity. Follow the selected Provider/Surface or compositor
contract; generation and blend masks may use different encodings. Treat a
provider mask as guidance, not an exact pixel boundary. Keep the change/preserve
contract. When unchanged pixels are a hard requirement, use a
deterministic composite, traditional retouch, or pixel restoration step and
measure change outside the intended region; do not claim that generative
inpainting alone preserved it exactly.

## Editable image projects

Use this workflow when an editable image project is part of the authorized
deliverable. A single image request can remain Quick Craft; do not require an
editor or project manifest merely to produce a concept or prompt. The optional
source-checkout tool is `integrations/image-production/cli.mjs`; see its README.
It is outside the Skill package; no GUI or segmentation.

For an explicitly installed local candidate, check
`~/.local/share/creative-craft/image-runtime.json` for `root` and `cli`.
Verify the referenced CLI against its `cli_sha256` before execution and read
the adjacent `PHOTO-WORKFLOW.md`. Otherwise use the explicit executor path or
current checkout. This optional locator is local data, not authorization to
install, call a model or modify settings.

### Shared copy across saved layouts

For “change the title once and re-export all saved sizes”, use the optional
source executor's `copy-variants <project> <input.json>`. Verify that the checkout
supports this command and read its `PHOTO-WORKFLOW.md`; the installed Skill does
not bundle the executor or dependencies. If unavailable, report the prerequisite.
Do not install globally or claim execution based on Skill discovery.

Read each intended layout revision and bind its returned `sha256`. Input contains
`output` (a new directory outside the source project), `variants` (unique `name`,
`revision`, `sha256` entries) and shared `updates` (`id`, exact `text` entries).
Choose revisions from the user's project, not example revision numbers. Every
updated ID must be an unlocked text object in every layout. Only text changes;
do not unlock products, resize photos or regenerate imagery for a copy-only edit.

Each output has an editable `project/` (r1 source snapshot, r2 shared copy) and
`export/`; root `manifest.json` binds source and output digests. Preserve complete
project folders. This explicitly creates derived projects; original history stays
unchanged and updates do not continuously synchronize between projects. An
unchanged historical re-export still uses `render --revision`.

If any layout fails, the batch removes its new output on ordinary error or
normal cancellation. Do not shorten approved copy or change typography to hide
overflow; resolve it within the user's constraints. Forced termination may leave
an incomplete directory. Check the complete manifest, per-layout receipts and
actual images before reporting success; distinguish source readiness from host
execution and visual approval. Copy/prompt-only requests need no execution.

### Starting from a whole photo

Only after explicit user permission, `crop-photo <new-output> <input.json>`
can trim a specified rectangle before layout. Read the source guide for the
original SHA-256 binding and EXIF-oriented sRGB coordinates. Preflight first;
authorization fields record permission, never infer it. Keep the crop directory
(original, normalized image, cropped PNG, receipt) with the editable project.
Use the cropped PNG as source; inspect product edges and shadows. Pixel equality
applies to the retained region, not the full photo or product completeness.

Use `create-photo` for a **new** editable composition when the user wants to
retain the entire opaque photograph, including its background, and add separate
text. Confirm the change/preserve intent: retaining the photo is different from
extracting a product or changing the scene behind a translucent bottle.

Locate an available source checkout using the current workspace or an explicit
executor path; verify `integrations/image-production/cli.mjs` and read its
`PHOTO-WORKFLOW.md` before execution. That guide and executor are not bundled in
the installed Skill. Skill discovery alone does not prove execution readiness.
If the checkout, dependencies or bound font are unavailable, report the missing
prerequisite and provide a usable brief; do not claim a project was created or
silently install/change global settings. For copy/prompt-only requests, deliver
the requested creative work directly.

Use the local photo brief with required `project_id`, absolute local `source`
and exact `headline`; `brand`, `caption`, `title` and canvas dimensions are
optional. This brief is input to the optional CLI, not a canonical Image Job.
For the reusable ivory/gold layouts, add `template: "brand-detail"` (4:5)
or `"xiaohongshu-cover"` (3:4), with `brand` and no `caption`. Verify support
and read the source guide. Photos stay native-sized inside proportional slots;
oversized photos fail, smaller photos are not enlarged. Explicit canvas overrides
must retain the template ratio. Preserve exact copy and inspect each new asset;
template names are purposes, not platform certification or brand approval.
An optional `background: "#RRGGBB"` sets the canvas; pick it from the reported
`layout.photo_edges` so a photo's own backdrop does not leave a visible box.
From the verified executor directory:

```sh
node cli.mjs create-photo /absolute/new-project /absolute/photo-brief.json --dry-run
node cli.mjs create-photo /absolute/new-project /absolute/photo-brief.json
node cli.mjs render /absolute/new-project /absolute/new-export
```

Preflight checks native photo dimensions, opacity, glyphs and actual text fit
before publishing; it does not write a project or call a model. Resolve a fit
failure within the user's constraints: preserve exact copy and required output
dimensions, and ask if satisfying both would require changing the requested
photo treatment. Do not silently resize/crop the photo, shorten approved copy
or switch to generation. The guide documents explicit canvas limits.

Inspect the exported image for hierarchy, exact copy, photo boundaries and
preserved product detail. The photo object is locked and its pixels are placed
1:1 after orientation/sRGB normalization; original encoded bytes are also kept.
Separate that engineering check from visual approval. Keep the complete project
with its assets/font/revisions so later changes remain possible. For subsequent
edits, read the existing revision and object IDs and use `edit`; do not rebuild
the project. `edit --dry-run` and actual edits check the final batch's visible
text with the export layout engine before saving assets or a revision. Overflow
or a box narrower than a glyph rejects the batch without changing the project;
correct it within the user's copy/layout constraints and retry preflight. An
isolated explicit unlock skips layout measurement so locked legacy text can be
repaired. Render and inspect the result for visual quality after every edit.

For several output ratios, read the source guide's multi-size workflow and edit
the same project's canvas and object geometry, preserving copy, IDs, assets and
font. Distinguish ratio from exact pixel dimensions: if a native photo cannot
fit, do not silently crop, scale or change the requested output size. Resolve
that constraint with the user. Authorized photo moves require isolated unlock,
layout edit and relock; a failed middle step can leave it unlocked, so read the
current state and restore the lock before delivery. Undo to a different locked
photo position needs the same explicit unlock/restore/relock sequence. Export
each completed variant separately with its bound revision and inspect it.
To re-export a saved layout without changing the current project, first read
that revision and use `render <project> <new-output> --revision <n>` (or
`preview` for a reduced inspection image). Choose a new output directory outside
the project and verify the receipt's selected revision/digest. Do not unlock or
revert merely to export history; omitting the option exports the current revision.

Transparent layers or arbitrary layouts use the general object `create`/`edit`
workflow below. Background replacement or raster retouch requires a separate
selection/mask/compositing workflow; `create-photo` does not supply a matte.

### Object and raster edits

Distinguish two kinds of work:

- **Object composition:** keep real product assets, exact copy, logos and
  layout as separately addressable objects when they must be changed later.
  Preserve template source, parameters, asset references and fonts alongside
  the rendered output.
- **Raster editing:** keep the source image, candidate bytes, selection/masks,
  crop/coordinate mapping and accepted revision. A generated scene may remain
  one raster layer; do not promise that its subjects are independently editable.

Read the current project revision and affected object IDs before proposing a
bounded change. Agent and human edits use the same supported operations. Submit
against that revision; if it changed, re-read and reassess rather than overwrite
the human's work. Locked objects cannot be altered by the edit batch. Validate
the batch, inspect its diff, apply it as one reversible change, and inspect the
actual composite at the intended size. A valid document does not prove correct
text, safe areas, product fidelity, or visual quality.

For local raster edits, specify four separate boundaries: model context,
generation mask, protected region, and final blend mask. Record their coordinate
space and scaling. Object segmentation proposes a selection; it does not prove
a correct alpha matte for transparent products, reflections or fine edges.
Inspect and refine the boundary when needed.
Flat translucent photos retain the baked-in backdrop; verify a matte before
changing what shows through.

Generation results enter the project as candidates. Preserve their actual bytes
and base revision, compare against the accepted composition, then accept or
discard according to the task's authorized decision policy. A candidate made
from an older revision must be reassessed before acceptance; arrival alone
cannot replace the current image. A failed or canceled generation leaves the
accepted project intact. Store outputs and parameters for recovery; seed and
prompt alone do not guarantee identical provider regeneration.

When exact protection is required, enforce it in compositing and check changes
outside the allowed blend region in a fixed color space on lossless working
pixels. Compare before lossy export; JPEG differences are not direct evidence
of unauthorized editing. For an authorized product move or resize, verify the
source asset and allowed transform separately from fixed canvas pixel regions.
New aspect ratios require layout and crop inspection, not just image scaling.

## Iteration ladder

1. low-cost composition draft;
2. direction selection;
3. identity/product fidelity pass;
4. text and detail pass;
5. local corrections;
6. final-size generation or upscale when appropriate;
7. delivery validation.

A high-resolution first pass may waste cost when the route is still uncertain.

## Inspection

Check actual outputs for:

- objective and proposition;
- subject and product fidelity;
- anatomy and object geometry;
- label, logo, and exact text;
- composition and safe area;
- lighting, material, reflection, shadow, and transparency;
- accidental objects, text, watermarks, or duplicated details;
- crop and requested dimensions;
- visual consistency across variants;
- rights and delivery state.

## Retry diagnosis

Change the smallest causal variable:

- wrong subject: strengthen identity/reference role;
- product drift: expand preserve contract and reduce competing references;
- wrong composition: state positions, scale, framing, and negative space;
- weak hierarchy: simplify elements and clarify focal order;
- text error: shorten copy, isolate exact text, or typeset afterward;
- style drift: state medium/material rules and remove conflicting style cues;
- local defect: use a localized edit rather than full regeneration.
- direction shift: stop local edits and return to route or art-direction
  selection.

Record the failed output and diagnosis. Do not erase unsuccessful lineage.
