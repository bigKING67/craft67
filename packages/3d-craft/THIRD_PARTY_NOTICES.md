# Third-party notices

3D-Craft V0.1 selectively absorbs workflow ideas from the upstream projects
recorded in `upstreams.lock.json`. No third-party model, image, or texture is
distributed in the candidate.

The installable Skill includes the minimum ES module runtime from Khronos
`gltf-validator@2.0.0-dev.3.10`, built from commit
`bcd52cc4ba5f333b2999a58f67cc05ddf28b4fb1`, under Apache-2.0. The copied
files are `module.mjs`, `gltf_validator.dart.js`, `package.json`, `LICENSE`, and
`NOTICES`; their original license and notices remain at
`skills/3d-craft/vendor/gltf-validator/`. Exact package integrity and local
file hashes are enforced by source validation.

Viewer development dependencies retain their own licenses in the installed npm
dependency tree. Notable dependencies include React, Three.js, React Three
Fiber, Drei, and Vite.

Before copying upstream code or assets in a future change, add its exact source
path, commit, license, local destination, and required notice here.
