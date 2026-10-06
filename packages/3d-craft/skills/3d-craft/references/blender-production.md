# Blender production

## Supported baseline

V0.1 targets Blender 5.2.1 LTS and uses `blender --background
--factory-startup --python-exit-code 2` for deterministic automation. Reject a
major/minor mismatch unless the task explicitly accepts compatibility risk.
The explicit Python exit code is mandatory: Blender otherwise may log an
uncaught automation exception while returning process exit code `0`.

## Build order

1. clear the factory scene;
2. establish meters, Z-up source coordinates, frame rate, and color management;
3. create named root, component, camera, and light objects;
4. apply transforms intentionally and place the required origin/pivots;
5. build primary volumes before bevels and small details;
6. create named materials with Web-compatible Principled BSDF inputs;
7. save the authoritative `.blend`;
8. inspect, render, export, and validate without manual hidden steps.

The asset root must declare custom property `3d_craft_profile` as
`product-asset` or `prop`. Component meshes should declare
`3d_craft_component` with the corresponding scene-contract component ID. The
inspector scopes dimensions, topology, materials, and textures to descendants
of the declared root; do not rely on fixture-specific object-name prefixes.

## Inspection floor

Record Blender version, scene units, object hierarchy, dimensions, object and
mesh counts, triangle count, unapplied transforms, material assignments,
missing external files, non-manifold edges, custom normals, UV layers,
modifiers, cameras, lights, armatures, and animation clips.

Unapplied transforms are not automatically wrong, but they must be intentional
and compatible with export. Set `topology_policy` to `closed` for watertight
product assets or `open-allowed` when intentional sheet geometry is part of the
brief. Non-manifold edges fail inspection only under the closed policy; they
remain reported under either policy.

## Render evidence

Use fixed front, back, left, right, top, and perspective cameras. Derive their
framing from the immutable scene-contract dimensions and origin policy, never
from fixture-specific numbers or the current candidate bounds. A
`declared-custom` origin must provide `framing_center`. Store the scene-contract
hash, camera transforms, lens or orthographic scale, resolution, renderer,
color transform, file hash, and candidate asset hash. Structural evidence
favors flat, readable materials. Look-development evidence uses EEVEE with
fixed lights. Reuse the same scene contract when comparing a repair so the
camera does not move between candidates.

## Reproduction

Run the canonical procedural fixture twice from `--factory-startup`. Compare a
normalized manifest of names, types, hierarchy, transforms, dimensions,
materials, triangle counts, and GLB semantic digest. `.blend` byte equality is
not required because Blender files may contain volatile metadata.
