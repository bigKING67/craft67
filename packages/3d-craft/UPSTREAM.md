# Upstream learning and absorption

This is the maintainer entry point for learning from upstream 3D projects.
It is repository governance, not part of the installable `3d-craft` Skill and
not an install-time dependency. An Agent using `skills/3d-craft/` does not need
GitHub credentials, API keys, or access to any repository listed here.

The machine-readable source of reviewed revisions is
[`upstreams.lock.json`](upstreams.lock.json). This document explains why each
source matters, what may be learned from it, what must not be copied blindly,
and how to review future upstream changes.

## Governing rules

1. Official specifications and product documentation are API and format
   authority. Community repositories are implementation and workflow inputs.
2. A repository name in this document is not approval to install its Skill,
   plugin, MCP server, assets, dependencies, or telemetry.
3. `upstreams.lock.json` contains only sources that were actually reviewed or
   whose exact package bytes are bundled. The watchlist below is deliberately
   not populated with guessed commits.
4. Upstream changes produce a review proposal. They never merge, install, or
   alter the product automatically.
5. Prefer absorbing a mechanism and expressing it in 3D-Craft's own contracts,
   scripts, and tests. Copy files only when necessary, license-compatible, and
   recorded in `THIRD_PARTY_NOTICES.md`.
6. Never accept an upstream benchmark, version claim, security claim, or
   compatibility claim without reproducing the evidence relevant to this
   repository.
7. Updating a lock is a source-governance change. It does not authorize a
   commit, push, release, package publish, global Skill install, MCP install, or
   external service call.

## Source classes

| Class | Meaning | Recorded where |
| --- | --- | --- |
| `absorbed_reference` | Reviewed ideas were independently adapted; upstream files are not shipped. | Exact commit, paths, concepts, destinations, and tests in `upstreams.lock.json`. |
| `vendored_runtime` | Exact third-party bytes are shipped because the standalone Skill requires them. | Commit/package identity, integrity, copied paths, licenses, notices, and runtime tests. |
| `watch_only` | Potential future source; not yet a basis for product behavior. | This document only, until a fixed-revision audit is accepted. |
| `official_authority` | Normative API, format, or host documentation. | Links below and task-specific evidence; pin a revision when copied or used by a compatibility contract. |

## Reviewed and locked sources

The exact commits and file paths are intentionally kept in
`upstreams.lock.json`, so this table focuses on the local decision.

| Repository | Relationship | Learn or retain | Local use | Do not import |
| --- | --- | --- | --- | --- |
| [`ifBars/blender-agent-studio`](https://github.com/ifBars/blender-agent-studio) | `absorbed_reference` | Graybox-to-polish stages, deterministic authority, fixed multiview evidence, baseline/Skill/tool separation. | Blender production workflow, inspection, rendering evidence, coffee-grinder eval. | Its public multi-Skill surface, benchmark conclusions, or MCP as a mandatory runtime. |
| [`RobLe3/cc-blender-skill`](https://github.com/RobLe3/cc-blender-skill) | `absorbed_reference` | Bounded repair loops and reference-reconstruction mechanisms. | Repair/security rules now; reference identity gates remain a V0.3 target. | Thirty-Skill chain loading, unlimited repair, or arbitrary Python execution as a default. |
| [`EnzeD/r3f-skills`](https://github.com/EnzeD/r3f-skills) | `absorbed_reference` | Version-pinned examples, type checking, Chromium rendering, and remount verification. | R3F viewer fixture and Web runtime QA. | Eleven public entry Skills or examples that are not verified against 3D-Craft's pinned stack. |
| [`img2threejs/img2threejs`](https://github.com/img2threejs/img2threejs) | `absorbed_reference` | State machine, identity-feature ledger, hidden-region uncertainty, fail-closed stages. | Run/scene contracts now; reference reconstruction remains a V0.3 target. | Claims that a single image establishes unseen geometry, or an unbounded autonomous loop. |
| [`KhronosGroup/glTF-Validator`](https://github.com/KhronosGroup/glTF-Validator) | `vendored_runtime` | Normative glTF 2.0 validation runtime. | Audited ES module bytes bundled inside the standalone Skill. | Unpinned registry bytes, omitted license/notices, or silent validator fallback. |

## Watchlist: learn selectively before locking

These repositories are useful research leads, not current 3D-Craft sources.
Before any absorption, review a fixed commit, its license, only the relevant
paths, current local requirements, and a failing or missing local test that the
change would address.

| Repository | Candidate learning scope | Earliest profile | Current disposition |
| --- | --- | --- | --- |
| [`ra100/blender-claude-plugin`](https://github.com/ra100/blender-claude-plugin) | Blender Python, Geometry Nodes, Shader Nodes, modifiers, scene/render API compatibility. | Blender API references after V0.1. | `watch_only`; use as a technical cross-check, not a workflow director. |
| [`arjun988/blender-skills`](https://github.com/arjun988/blender-skills) | Task taxonomy and future profile coverage. | Future profiles. | `watch_only`; do not install or mirror the full Skill collection. |
| [`TMHSDigital/Blender-Developer-Tools`](https://github.com/TMHSDigital/Blender-Developer-Tools) | Blender add-on, `bpy`, debugging, and developer-tool workflows. | Developer tooling only. | `watch_only`; not an art-direction or asset-production authority. |
| [`DmitriyGolub/threejs-devtools-mcp`](https://github.com/DmitriyGolub/threejs-devtools-mcp) | Scene-tree, material, animation, renderer, and memory inspection capability semantics. | Web3D V0.2. | `watch_only`; future optional adapter, never core logic. |
| [`ahujasid/blender-mcp`](https://github.com/ahujasid/blender-mcp) | Power-adapter capability surface and arbitrary-Python threat model. | Optional Blender power adapter. | `watch_only`; explicit authorization and telemetry review required before use. |
| [`greensock/gsap-skills`](https://github.com/greensock/gsap-skills) | Timeline, ScrollTrigger, React lifecycle, and motion-performance guidance. | Web motion V0.2+. | `watch_only`; load only for motion work and verify against the project's GSAP version. |
| [`majidmanzarpour/threejs-game-skills`](https://github.com/majidmanzarpour/threejs-game-skills) | Deterministic game loop, smoke tests, visual regression, and bot playtests. | Deferred game profile. | `watch_only`; games remain outside the current product boundary. |
| [`MengTo/Skills`](https://github.com/MengTo/Skills) | WebGL composition and creative-web patterns. | Optional visual research. | `watch_only`; inspiration only, never API or performance authority. |

## Official authorities

Use the official source first when a community example conflicts with an API,
format, or host contract:

- [Blender Python API](https://docs.blender.org/api/current/) and
  [Blender Manual](https://docs.blender.org/manual/en/latest/)
- [Khronos glTF 2.0 Specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html)
- [Three.js documentation](https://threejs.org/docs/) and
  [React Three Fiber documentation](https://r3f.docs.pmnd.rs/)
- [Agent Skills specification](https://agentskills.io/specification)
- [Chrome DevTools for agents](https://developer.chrome.com/docs/devtools/agents/get-started)

For 3D-Craft browser execution, browser67 remains the default runtime boundary.
Chrome DevTools material may inform browser-level checks, but it does not
replace browser67 or authorize adopting a user-owned tab or profile.

## Freshness: compare relevant content, not repository noise

Many upstreams are active repositories. A new default-branch HEAD may change
documentation, CI, packaging, or unrelated Skills without changing any source
that 3D-Craft learned from. Therefore the default freshness strategy for a
reviewed Git upstream is `target-path-git-blob`:

```text
locked commit + source_paths
→ candidate revision + the same paths
→ compare Git blob IDs
→ classify the change
```

The classifications are:

- `CURRENT`: candidate revision is the locked commit.
- `HEAD_ONLY_CHANGED`: repository HEAD moved, but every tracked source path is
  byte-identical. No absorption work is required.
- `TARGET_PATH_CHANGED`: at least one tracked path was removed or changed. A
  focused review is required.
- `UNVERIFIED`: the checkout, origin, revision, locked commit, or tracked paths
  cannot be proven. Do not advance the lock.

This comparison intentionally does not discover every new file added upstream.
Before a planned profile expansion or milestone release, manually inspect the
upstream tree and release notes to decide whether `source_paths` itself needs a
reviewed expansion. Path-scoped freshness is a noise filter, not a substitute
for periodic source discovery.

For a vendored npm runtime, the source of truth is the exact package version,
npm integrity, copied-file hashes, license/notices, and isolated runtime test.
A Git HEAD comparison is not sufficient package provenance.

## Offline upstream-difference check

The repository script performs no network access, installs nothing, and does
not read credentials. Give it a separately cloned checkout containing both the
locked commit and the candidate revision:

```bash
audit_root="$(mktemp -d /tmp/3d-craft-upstream.XXXXXX)"
git clone --filter=blob:none \
  https://github.com/ifBars/blender-agent-studio.git \
  "$audit_root/blender-agent-studio"
git -C "$audit_root/blender-agent-studio" fetch origin \
  b1cefdd1bcc1b7bf40423259a5c6fa154e2259f4 --depth=1
python3 scripts/upstream_diff.py \
  --repo ifBars/blender-agent-studio \
  --checkout "$audit_root/blender-agent-studio" \
  --revision HEAD \
  --json
```

Exit code `0` means `CURRENT` or `HEAD_ONLY_CHANGED`, `3` means relevant paths
changed and need review, and `2` means the comparison is unverified. The script
does not update `upstreams.lock.json`; that remains a deliberate maintainer
decision after review and local validation.

## Absorption workflow

When the script reports `TARGET_PATH_CHANGED`:

1. Freeze the candidate commit and confirm the checkout's `origin` matches the
   expected GitHub repository.
2. Review license and notice changes before code, prompts, assets, or examples.
3. Read only changed tracked paths first. Expand scope only when an imported
   symbol, referenced document, or changed behavior requires it.
4. Classify each candidate item as `absorb`, `adapt`, `reject`, or
   `unverified`. Record the reason; popularity and upstream freshness are not
   reasons by themselves.
5. Map accepted behavior to the smallest local contract, reference, script, or
   test. Do not create another public Skill entry merely to mirror upstream.
6. Run the narrow regression first, then source validation and the relevant
   Blender/GLB/Web gate. Claims without runtime evidence remain `UNVERIFIED`.
7. Update `upstreams.lock.json` only after the candidate commit, paths,
   license, absorbed concepts, local destinations, and validation cases are
   truthful for the resulting source tree.
8. Update `THIRD_PARTY_NOTICES.md` and `LICENSES/` whenever bytes are copied.
9. Keep benchmark results separated as baseline, Skill-only, and Skill+tools;
   preserve failed samples and block hard-gate regressions.

## Acceptance checklist

An upstream update is ready for an ordinary scoped source change only when:

- the repository, exact commit, relevant paths, and license are verified;
- the local need is demonstrated independently of the upstream proposal;
- copied bytes, if any, have integrity and notice coverage;
- local behavior is expressed in 3D-Craft terminology and product boundaries;
- focused tests pass and no hard gate regresses;
- `python3 scripts/validate_source.py` passes;
- changed claims name their actual evidence and remaining unverified scope.

Commit, push, tag, release, registry publication, global installation, and MCP
configuration remain separately authorized actions.
