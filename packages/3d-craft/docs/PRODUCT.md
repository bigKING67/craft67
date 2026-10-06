# 3D-Craft product contract

## Product statement

3D-Craft turns a product or prop brief into a reproducible Blender asset, a
validated GLB, a working web viewer, and an evidence-backed delivery record.
It is an Agent production system, not a prompt collection or a claim that code
which merely runs is finished 3D work.

## Users and primary job

The primary users are coding agents and the developers supervising them. Their
job is to create, inspect, hand off, or repair a bounded 3D asset while keeping
authority, evidence, uncertainty, and runtime capability explicit.

## V0.1 promise

V0.1 supports product and prop assets with one complete path:

1. route and establish authoring authority;
2. define the scene and quality contract;
3. create or inspect a Blender asset;
4. render fixed-view evidence and complete a candidate-bound identity review;
5. export and validate GLB;
6. load the asset in a React Three Fiber viewer;
7. inspect the real browser runtime through browser67;
8. issue a validation report bound to evidence and hashes.

The canonical evaluation fixture is an original tabletop coffee grinder. V0.1
does not promise reference-image reconstruction, characters, animation,
simulation, games, WebGPU, or external generative 3D services.

## Completion boundary

Success requires the applicable hard gates to pass. Source presence, a clean
build, or an Agent assertion does not prove visual or runtime quality. When a
capability is unavailable, the corresponding result is `UNVERIFIED`; it is not
silently inferred.

V0.1 is a private local candidate. Commit, push, tag, public release, registry
publish, deployment, and global installation are separate actions.
