# Coffee grinder vertical-slice evaluation

This original, procedural fixture proves the V0.1 path without third-party
images, models, or textures. It intentionally models a bounded product asset,
not a photorealistic branded appliance.

The declared dimensions are approximately 180 × 220 × 320 mm. Required
identity features are a transparent hopper, compact appliance body, forward
chute, side adjustment knob, detachable grounds cup, and visible status light.

Run outputs belong in an external 3D-Craft run directory. The source repository
keeps only the brief, contracts, and deterministic creation script.

After build, Blender inspection, and GLB validation, run `bind-asset` with this
script as `--source`, `MIT` as `--license`, and `coffee-grinder fixture` as
`--license-subject`. This creates the asset manifest and binds the copied scene
contract without manually transcribing hashes.

For rendered or assured validation, run `init-visual-review`, inspect all fixed
views, and complete its initially `UNVERIFIED` feature assessments. Accepted
browser67 observations must use the `3d-craft.browser-runtime-draft.v1` shape
documented in `skills/3d-craft/references/web3d-runtime-qa.md`. Run
`bind-browser-evidence` to verify the served GLB identity and PNG viewport,
copy accepted screenshots into `evidence/`, and create the sealed report. A
path into browser67's runtime cache is provenance, not a portable deliverable.
