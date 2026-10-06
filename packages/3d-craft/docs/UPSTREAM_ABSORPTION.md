# Upstream absorption policy

The canonical maintainer guide is [`../UPSTREAM.md`](../UPSTREAM.md). It lists
the reviewed sources, future watchlist, official authorities, content-scoped
freshness model, offline difference command, and full absorption checklist.
This page keeps the short architectural policy close to the rest of the product
documentation.

Upstreams are research inputs, not install-time dependencies or wholesale Skill
bundles. Every reviewed source is pinned in `upstreams.lock.json` with an exact
commit, license, source paths, absorbed concepts, and local validation cases.

The V0.1 weighting is architectural, not a code-copy ratio:

- Blender Agent Studio: reproducible production and evidence loop;
- cc-blender-skill: reference-reconstruction concepts reserved for V0.3;
- r3f-skills: version-aware examples and browser verification;
- img2threejs: state machine and identity-feature ledger reserved for V0.3;
- official Blender, glTF, and Three.js documentation: API authority.

One narrow exception is deliberately bundled: the audited ES module runtime
from `gltf-validator@2.0.0-dev.3.10`. Without those files, the installable Skill
would appear valid while its GLB gate failed outside the development checkout.
The exact npm integrity, upstream commit, copied paths, local hashes, Apache-2.0
license, notices, and isolated-package runtime test are all mandatory.

An upstream update produces a reviewable difference report. It never merges
automatically. For Git sources, freshness is based on the blobs at the locked
`source_paths`, not default-branch movement alone. Copied code or assets require
license mapping and a notice; absorbed ideas are independently expressed and
covered by local tests.
