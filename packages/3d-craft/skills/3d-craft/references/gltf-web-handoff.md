# glTF and web handoff

## Export

Use a fixed Blender export configuration: GLB container, selected coordinate
conversion, applied modifiers, materials, cameras only when required, animation
only when required, extras when they carry declared semantic metadata, and no
unlicensed embedded resources.

## Validation

Khronos validation is necessary but not sufficient. Also inspect:

- node names and hierarchy;
- required material names and assignments;
- mesh and primitive counts;
- triangle count and bounding box;
- texture count, dimensions, MIME types, and color-space intent;
- animation names and duration when applicable;
- used and required extensions;
- unused resources and GLB byte size.

The V0.1 validator parses the GLB JSON chunk and reports a semantic digest.
Bind the report to the GLB SHA-256. Its audited Khronos validation runtime is
bundled under `vendor/gltf-validator/`, so an isolated Skill package does not
depend on repository-level `node_modules` or network installation.

## Web integration

Configure Draco, KTX2, or Meshopt decoders only when the asset actually uses
them. Treat exporter compression and loader support as one contract. Own
loading, error, camera framing, resize, tone mapping, color space, shadows,
interaction, and resource disposal. Record context-loss recovery as
`UNVERIFIED` in a V0.1-only receipt. The bundled viewer now contains the first
V0.2 recovery slice and can bind an optional, strict `context_loss` observation;
its second slice adds an explicit warmup/sample profile and same-renderer GLB
reload observations for resource-stability evidence. The next slice exposes a
development/test-only, tool-neutral control that returns one schema-valid
profile observation for run-owned binding, so Agents do not hand-transcribe
performance fields. These slices do not make the rest of the V0.2 roadmap
complete. Revalidate after every optimization and compare visual evidence
before accepting size gains.

Keep viewer npm dependencies and generated assets out of the installed Skill;
the audited validator runtime above is the only V0.1 exception. Copy the viewer
template into a run-owned directory, then use its nested lock:

```bash
viewer_run_dir="$(mktemp -d /tmp/3d-craft-viewer.XXXXXX)"
cp -R assets/r3f-viewer/. "$viewer_run_dir/"
cp /absolute/run/assets/asset.glb "$viewer_run_dir/public/asset.glb"
cd "$viewer_run_dir"
npm ci
VITE_ASSET_SHA256=<asset-sha256> npm run dev
```

Set `VITE_ASSET_URL` and `VITE_ASSET_SHA256` for the candidate. Set
`VITE_ASSET_NAME` and `VITE_ASSET_DESCRIPTION` when presenting a named product;
the template defaults remain asset-neutral and must not leak the bundled
coffee-grinder fixture into unrelated work. The fixture viewer preserves the
asset's observed dimensions in runtime evidence while normalizing its largest
rendered dimension for stable camera framing; application code may replace
this with an approved, product-specific camera contract.

Use `?motion=reduce` for deterministic fixture screenshots. It disables the
nonessential automatic orbit while preserving manual camera interaction and
the operating system's `prefers-reduced-motion` behavior.

`node_modules`, Vite cache, build output, TypeScript build info, and candidate
GLBs are runtime state. They must not be packaged into `skills/3d-craft/`.
