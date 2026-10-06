# Roadmap

## V0.1 — product/prop vertical slice

Blender 5.2.1 LTS, deterministic headless build, six-view evidence, GLB
validation, R3F viewer, browser67 runtime QA, portable Codex/Pi/Grok discovery,
and a single original coffee-grinder fixture.

## V0.2 — web 3D engineering

Vanilla Three.js, richer interaction, animation lifecycle, context-loss
recovery, performance profiling, and optional Three.js/Chrome tool adapters.

The first slice adds real `WEBGL_lose_context` recovery to the R3F viewer,
visible `context-lost` and `restoring` states, resource-lifecycle observability,
and an optional strict `context_loss` browser-evidence extension. The second
slice adds a bounded 3-second warmup plus 10-second sample, measured frame
p50/p95 and renderer peaks, and at least three sequential same-renderer GLB
reloads for geometry/texture stability. The third working-tree slice adds a
tool-neutral Viewer control that performs the whole sequence and a linked,
schema-valid profile observation that the existing browser evidence binder can
seal without hand-transcribing metrics. These slices do not yet complete
Vanilla Three.js, richer interaction, animation lifecycle, optional tool
adapters, or physical target-device profiling.

## V0.3 — reference reconstruction

Multi-view registration, contour metrics, identity-feature ledgers, hidden-side
uncertainty, reference contracts, and bounded repair loops.

## V0.4 — mechanical motion and procedural assets

Pivots, sockets, constraints, Geometry Nodes, animation evidence, and Blender-
to-web clip parity.

## Explicitly deferred

Characters, full rigging, hair, complex simulation, games, WebGPU, NeRF,
Gaussian splats, photogrammetry, asset marketplaces, and external generative
3D services remain out of scope until evidence from real users justifies a
profile.
