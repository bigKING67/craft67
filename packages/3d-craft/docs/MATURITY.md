# Maturity

## Current status: locally sealed candidate

The product code at commit
`7dcf96a2704eda53199dec1259639323a47ac62a` implements the narrow
product/prop vertical slice across Blender, GLB, an R3F viewer, browser runtime
evidence, and evidence-bound validation. Local acceptance has exercised:

- current Codex Skill frontmatter validation;
- source, unit, schema-contract, and viewer type/build checks;
- deterministic package construction with two-build SHA-256 parity;
- the complete release gate from a clean detached worktree at that exact
  commit, with `release_eligible=true` and local package SHA-256
  `6a7f33b08a67bad602970a7c1bde10652aa816c4590ef23b38723dd51c02e97c`;
- validation of an independently extracted package, including execution of its
  bundled Khronos validator against a minimal GLB and an isolated doctor
  capability probe;
- isolated, non-global local installation;
- two clean coffee-grinder Blender builds with matching normalized scene and
  GLB semantic digests;
- live Blender failure propagation: an uncaught automation error returned `0`
  without a policy flag and returned `2` with the now-required
  `--python-exit-code 2`;
- contract-framed six-view rendering for both the 32 cm fixture and an
  independent 2 m generic product root without fixture-name assumptions;
- the coffee-grinder browser runtime through GLB byte/hash verification, 100%
  node-name coverage, visible RAF progression, remount/dispose, and desktop
  performance evidence;
- the production Viewer dependency boundary: a 5.98 KB application entry and
  196.26 KB initial JavaScript path before the async AssetScene/R3F/Three
  runtime, with the pinned Three r185 chunk held under an explicit 800 KB
  regression ceiling;
- production browser readiness after a verified 1440x900 viewport transaction,
  including GLB HTTP success, populated 15-object/13-mesh/5-material metrics,
  expected 188x224x320 mm dimensions, and a live WebGL context;
- visible browser67 visual evidence bound to candidate GLB SHA-256
  `1c2fbd8291ac9b5285fa1a15a95327ecf791af741f7c8408211e5ead3093396c`:
  the final 1440x900 desktop sample has no page overflow and keeps the complete
  evidence rail and asset in frame, while the final 390px-wide full-page sample
  keeps the complete asset in the responsive Canvas. Both captures verified
  `visibilityState=visible`, exact requested viewport metrics, PNG dimensions,
  and automatic viewport-override cleanup;
- causal browser interaction evidence: a pointer orbit moved the camera,
  reset-camera restored it with zero measured position error, remount/dispose
  counters advanced, a clean reload returned to `ready`, and the served GLB
  bytes matched the candidate hash;
- copied, run-owned desktop and mobile screenshots under the external assured
  run at `~/Library/Application Support/3d-craft/runs/coffee-grinder/v01-seal-20260904`,
  with all eight routed gates and 21 delivery files passing validation;
- separate Skill discovery and invocation smokes for Codex, Pi, and Grok.

On 2026-09-04, the exact installable Skill tree from commit
`346fba0616ea574c3f7080511dd7d46f2e8f6159` was also installed to the canonical
user-global path `~/.agents/skills/3d-craft`. The 36 source and installed files
matched byte-for-byte, source and Codex Skill validation passed, and discovery
from the independent `resume` workspace passed on Codex 0.153.2, Pi 0.80.6, and
Grok 1.0.5. The installation provenance tree digest was
`211ea7211e56153ee3ce5acfd51b5ec02f5a223455d75202408de27f0fe50dcd`.
This establishes local macOS global-install and discovery parity only; no model
invocation, credential access, or provider configuration was part of that
acceptance.

These checks establish a locally sealed candidate, not a published release.
Evidence is valid only for the exact commit, host versions, providers, Blender
build, browser runtime, and artifacts recorded by the corresponding receipt.
The browser report retains one non-blocking Three.js deprecation warning, and
mobile capture remains layout evidence rather than physical-device GPU proof.

## Post-seal working-tree verification

The uncommitted browser-evidence binder refinement was exercised separately in
`~/Library/Application Support/3d-craft/runs/coffee-grinder/v01-binder-20260904`.
That fresh run bound a cache-bypassed browser fetch to candidate GLB SHA-256
`120e6ab9e2ef56a06cb9d01a92a2b77c179c2513f0db03a6d6e976660225bf8d`,
copied visually reviewed 1440x900 desktop and 390px mobile screenshots into the
run, rejected a hidden readiness screenshot as `INVALID SAMPLE`, and passed all
eight routed gates. Native orbit input changed the camera, reset restored it,
remount/dispose advanced, a clean reload returned to `ready`, and a clean
three-second console observation contained no errors and one non-blocking
Three.js `Clock` deprecation warning.

That warning was traced to `@react-three/fiber` 9.7.0 constructing
`THREE.Clock`; Three.js deprecated that class in r183. On 2026-09-04 the npm
stable tags still resolved to R3F 9.7.0, Drei 10.7.8, and Three.js 0.185.1, so
there was no newer stable R3F line to adopt. The viewer does not suppress the
warning, patch `node_modules`, downgrade Three.js, or move to the R3F 10 alpha
line merely to produce a clean report. It remains an explicit P2 compatibility
issue until a stable upstream migration is available and revalidated.

This verification was initially produced from a dirty working tree, so it does
not by itself extend the immutable release provenance of commit
`fe5b05c6ec6a8cea781ef72aeeb22938a30beec2`. Binder release provenance exists
only when a later external release attestation names an exact clean commit;
this narrative does not self-certify that transition.

## V0.2 working-tree slice: WebGL context recovery

On 2026-09-04, the first V0.2 slice added a real WebGL context-loss lifecycle to
the bundled R3F viewer. Asset loading state and GPU context state are separate,
so an asynchronous GLB callback cannot overwrite `context-lost` with a false
`ready`. Camera controls pause during interruption, the UI exposes authored
`context-lost` and `restoring` states, Three.js performs its native renderer
reset, and a background-safe microtask returns the application to its asset
state without waiting on a throttled browser RAF.

The browser-runtime v1 receipt accepts an optional strict `context_loss`
observation. Existing V0.1 receipts remain valid; a supplied `PASS` must prove
extension support, at least one loss and restore, visible readiness, and fresh
RAF progress after restoration, while a supplied `FAIL` prevents the
`web_runtime` gate from passing.

Live browser67 0.11.2 evidence used the coffee-grinder GLB at SHA-256
`120e6ab9e2ef56a06cb9d01a92a2b77c179c2513f0db03a6d6e976660225bf8d`.
The exact current working tree observed one loss and one restore, returned to
`healthy + ready`, advanced 57 frames after restoration, preserved 15 objects,
13 meshes, 5 materials, and 10,118 triangles, then passed a remount/dispose
check with 2 mounts, 1 remount, and 1 disposal. Two 1440x900 samples were
accepted only with `visibilityState=visible`; two hidden intermediate captures
were retained as `INVALID SAMPLE`, not promoted to visual evidence. A separate
background test kept the target at `visibilityState=hidden` with its RAF counter
fixed at 303 before, during, and after the cycle; the snapshot still returned
from `context-lost` to `ready` with a healthy context. The durable local receipt
is outside the repository at
`~/Library/Application Support/3d-craft/runs/v02-context-loss-20260904/context-loss-observation.json`
(SHA-256 `911af2c2a0e80ab0caeded4d52072dc24e4435f68ff584e8fcebd4136802ef24`).

The implementation was subsequently committed as
`7dcf96a2704eda53199dec1259639323a47ac62a`. A clean detached release gate for
that exact commit passed source validation, unit and contract tests, Viewer
typecheck/build, reproducible packaging, isolated package validation, isolated
glTF runtime, and the isolated Doctor glTF capability probe. Its local package
SHA-256 is `6a7f33b08a67bad602970a7c1bde10652aa816c4590ef23b38723dd51c02e97c`.
This is still not remote CI, a tag, a published release, or a claim that all of
V0.2 is complete.

## V0.2 working-tree slice: explicit performance and resource stability

The second V0.2 slice replaces ambiguous rolling-frame claims with a bounded
performance state machine. The development Viewer freezes the actual page
viewport, DPR, and visibility; performs a 3,000 ms warmup followed by at least
10,000 ms of sampling; records monotonic timestamps, sample count, frame
p50/p95, and peak renderer counters; and invalidates the run if visibility,
viewport, DPR, or Viewer readiness changes. Resource stability reloads only the
owned GLB subtree in the same Canvas/WebGLRenderer and records one sample only
after geometry and texture counters remain unchanged for six frames.

Live testing exposed and fixed two false-pass risks. First, a two-frame sample
could capture the base scene before the reloaded asset reached the renderer,
producing a misleading negative geometry delta; passing deltas are now
nonnegative and samples are mount-generation aware. Second, React 19
StrictMode may perform two development-effect cleanups for one reload, so the
durable invariant is exactly one new mount and at least one new disposal per
cycle, not exactly one disposal.

The browser receipt and scene contract now carry optional strict performance
extensions. Once an approved `budgets.performance_profile` is declared,
missing profile or resource evidence is `UNVERIFIED`; failed, malformed,
mismatched, or over-budget evidence is `FAIL`. Legacy V0.1 scenes without the
nested budget remain readable, but do not inherit the stronger claim.

Live browser67 evidence ran on the npm-current stable CLI and extension version
0.11.2. The final visible 1512x823, DPR 2 observation completed a 3,001.6 ms
warmup and 10,008.6 ms sample with 1,201 frames: frame p50 was 8.30 ms, p95 was
9.20 ms, and renderer peaks were 17 draw calls, 10,118 triangles, 15
geometries, and one texture. Three sequential same-renderer reloads produced
four settled samples with 15 geometries and one texture throughout, yielding
zero geometry and texture deltas; each StrictMode reload recorded two cleanup
events. A fresh cache-bypassed fetch returned 196,188 bytes with candidate GLB
SHA-256 `120e6ab9e2ef56a06cb9d01a92a2b77c179c2513f0db03a6d6e976660225bf8d`.

The schema-valid local browser draft is outside the repository at
`~/Library/Application Support/3d-craft/runs/v02-performance-20260904/browser-runtime-draft.json`
(SHA-256 `bd530aaff0bacf28fc309bcb0ed0ea402caee3bf431c2799bd28fae7a5195734`).
Its visually reviewed 3024x1646 PNG is stored beside it as
`browser-performance-visible.png` (SHA-256
`ccf7f7275b6de015950a9b5bc4baa1e714a582ed358c588c308206fe9eac5600`).
A preceding hidden screenshot with contradictory dimensions remains recorded
as `INVALID SAMPLE`.

This live draft intentionally retains `responsive_layout=UNVERIFIED`; mobile
layout and physical-mobile GPU timing were not retested, and context-loss
recovery was not repeated in this slice. The natural host viewport also differs
from the coffee-grinder fixture's approved 1440x900, DPR 1 profile, so this is
not a fresh full-run gate for that fixture. The implementation and this
narrative are uncommitted working-tree changes and have no clean-package,
remote-CI, tag, release, or publication provenance yet.

## V0.2 working-tree slice: profile orchestration and linked evidence

The third V0.2 slice removes manual timing, polling, renderer-field mapping,
and resource-delta transcription from the normal Agent path. A separate
development/test-only `window.__THREE_D_CRAFT_TEST__` control runs the explicit
profile and three same-renderer asset reloads, then returns one immutable
`3d-craft.web-profile-observation.v1` object. It does not mutate the frozen
runtime snapshot and remains absent as a production API. The browser draft can
link that exact JSON, while `bind-browser-evidence` validates it, rejects dual
inline/linked authority, verifies candidate and desktop page identity, copies
the observation into run-owned evidence, and makes later hash tampering fail
the browser gates.

Local source validation, all 44 Python tests, both Node contract tests, Viewer
typecheck/build, and whitespace checks pass. The production build transforms
575 modules; the largest pinned Three.js chunk remains 768.28 kB under the
existing 800 kB build ceiling. These are working-tree results, not clean-commit
or remote-CI provenance.

Live verification used the npm-current browser67 0.11.2 runtime with matching
extension source identity in a dedicated managed Agent Window. The background
tab remained `visibilityState=hidden`, so the strict profile correctly had no
eligible snapshot. After one bounded foreground interval, two consecutive
one-call profiles completed. The saved second observation used a real
1512x823, DPR 2 page, a 3,000 ms warmup, at least 10,000 ms of sampling, and
1,200 frames. It measured frame p50 8.30 ms, p95 10.10 ms, 17 peak draw calls,
10,118 triangles, 15 geometries, and one texture. Three sequential reloads
produced four samples with exactly one additional mount and two StrictMode
cleanups per cycle; geometry and texture deltas were both zero. A bounded
console observation contained zero errors and the one already documented R3F
`THREE.Clock` warning.

The exact schema-valid observation is outside the repository at
`~/Library/Application Support/3d-craft/runs/v02-profile-orchestrator-20260904/web-profile-observation.json`
(SHA-256 `bc6c939c34736b2e33f487c03606491306d40d0c23af4874a59a98886a17fb20`).
The visually reviewed 3024x1646 viewport image is beside it as
`browser-profile-visible.png` (SHA-256
`ef29ac89556ed5b445c991a91fd02335b5a84f6d03457d058d4a0424e8b42fa5`).
Two preceding screenshots remain explicitly invalid: one was captured while
hidden, and one reported a 1512x823, DPR 2 page but produced a 3024x1618 PNG.
Only an atomic set, verify, capture, and clear transaction produced matching
3024x1646 evidence. The exact managed tab was then finalized with one verified
close; user tabs were not adopted or closed.

This observation used candidate GLB SHA-256
`1c2fbd8291ac9b5285fa1a15a95327ecf791af741f7c8408211e5ead3093396c`,
but it was not sealed into a fresh complete 3D-Craft run. Its natural viewport
also differs from the coffee-grinder scene's approved 1440x900, DPR 1 budget.
It therefore proves the new orchestration and linked-observation contract, not
a new full fixture PASS, mobile layout, physical-device performance, or V0.2
completion.

## Approved-viewport profile observation (2026-09-07)

A dedicated browser67 0.11.4 Agent tab exercised the current working-tree
Viewer at the coffee-grinder budget's exact 1440x900, DPR 1 viewport. One
debugger batch set the viewport, verified page dimensions, awaited the profile,
and cleared the override. The immutable observation passed its JSON schema:
3,000 ms warmup, 10,000 ms sample, 1,200 frames, frame p50 8.30 ms and p95
9.20 ms, with 17 draw calls, 10,118 triangles, 15 geometries, and one texture.
Three same-renderer reloads yielded zero geometry and texture deltas. A fresh
HTTP 200 fetch returned 196,188 bytes matching candidate SHA-256
`1c2fbd8291ac9b5285fa1a15a95327ecf791af741f7c8408211e5ead3093396c`.

The visible 1440x900 desktop PNG passed viewport/bitmap checks and visual
inspection: the complete asset and evidence rail remain in frame without
horizontal overflow. The observation is stored outside the repository at
`~/Library/Application Support/3d-craft/runs/v02-approved-profile-20260907/web-profile-observation.json`
(SHA-256 `38afbde31847dfa3afa4e75274c4dbd551e556abf7bbd221ab1977a47cb998a1`).

The subsequent mobile capture was hidden and remains `INVALID SAMPLE`;
bounded console observation timed out and remains `UNVERIFIED`. This run
reused the existing sealed GLB rather than rebuilding the complete Blender
fixture. It therefore establishes approved-viewport performance and desktop
evidence only, not a fresh complete fixture gate or V0.2 completion. The exact
Agent tab was closed with verification and no remaining unkept task tabs.

## Fresh complete profile run (2026-09-07)

The current working-tree slice subsequently passed all eight routed gates in
the new external run
`~/Library/Application Support/3d-craft/runs/coffee-grinder/v02-full-20260907`.
Two Blender 5.2.1 factory-startup builds produced matching normalized scene
and GLB semantic digests. The candidate GLB SHA-256 is
`8779a6ea0895f69368195ed4086f786d18e5615768914cdd7d2a04df3c09be2b`.
Structure inspection, six-view identity review, lookdev inspection, and
Khronos validation passed before browser evidence was bound.

The dedicated browser67 0.11.4 tab observed a visible 1440x900, DPR 1 profile:
3,000 ms warmup, 10,000 ms sampling, 1,201 frames, p95 9.30 ms, 17 draw
calls, and 10,118 rendered triangles. Three same-renderer asset reloads had
zero geometry/texture deltas. The served GLB hash matched, node coverage was
100%, and bounding-box drift was below 0.000003%. Visible desktop and mobile
captures verified their requested viewport/DPR and PNG dimensions; visual
review found the complete asset and controls in frame without horizontal
overflow. The mobile full-page PNG is 390x1313 for a 390x844 CSS viewport.

Separate raw browser receipts record a real context loss and restore with 28
fresh frames after recovery, pointer-driven orbit movement, exact camera
reset, and ready state after a cache-bypassed reload. A bounded console
observation returned zero errors and the known `THREE.Clock` warning, with
listeners removed and debugger release verified. The binder sealed the profile
and both screenshots into run-owned evidence; `reports/validation.json`
reports `PASS` across authority, reproduction, scene integrity, identity,
glTF, cross-runtime, web-runtime, and delivery, with 22 delivery files.

This supersedes the prior mobile/console gaps for this new candidate only.
Physical mobile GPU timing remains unverified. The exact task tab was closed
with verification and no remaining unkept tabs. These are local working-tree
results, not clean-commit, remote-CI, publication, or complete V0.2-roadmap
provenance.

The subsequent pre-commit review reproduced a linked-evidence validation gap:
changing both report-level and inline p95 values while leaving the sealed
observation untouched still passed. The validator now checks the linked
content and reconciles measured fields plus asset/page identity. Regression
coverage rejects report-only metric, timing, resource, and URL drift as well
as hash-valid malformed, failed, or page-mismatched linked observations.
All 44 Python tests and both Node contract tests pass. Revalidation with the
fixed validator is recorded separately in `reports/validation-r1-fixed.json`:
the existing real run still passes all eight gates, with its 17 evidence files
unchanged. This corrects the validation gap without replacing measured data.

## 2026-09-07 existing-application case: 3D resume

The installed Skill's 39 files were rechecked against source commit
`9f8262eae7792792cae074fcd2b9f21b37564ec4` and matched byte-for-byte.
That baseline has a clean local release-candidate attestation with eight
checks passing, `release_eligible=true`, and ZIP SHA-256
`3238bd6042dd7c52c8d419e3e20ca6ed210e9639fbf5e8137b2dbdef7f6121d2`.
This is local candidate/install evidence, not a published release.

A separate assisted application case used the existing `67-3d-resume` project.
Commit `a41646bf5c1640d9735a35dac16ad5a5034c376c` changes only
`web/src/App.tsx` and `web/src/scene/Scene.tsx`: bilingual hero copy, bounded
eye rotation including convergence, elapsed-time follow/return damping, and
pointer-exit/blur recovery with cancellation on re-entry. The current files
were checked against that commit during closeout.

Recorded evidence includes lint/build success, visible browser67 desktop and
390px narrow-layout captures in both languages, synthetic pointer response,
return and interrupted-return observations, and an initial-scroll inspection.
The final return sample was approximately 0.05 degrees from its sampled neutral
orientation. This is total quaternion distance, not a per-axis angle or FPS
measurement. Browser tasks were finalized without closing user-owned tabs.

Classification: **assisted existing-Web3D maintenance**, not a canonical
3D-Craft gate run or independent fresh-session evaluation. The session used
project instructions, global routing, design-craft, 3d-craft, browser67, and
substantial prior context; success cannot be attributed to the installed
Skill alone. Its character asset was not authored, rigged, or re-exported.
This case does not expand V0.1's character/animation production boundary.
Blender/GLB source parity, physical touch-device behavior, high-refresh
hardware, strict performance profiling, and production deployment remain
unverified for this case. Generic product/prop route parameters must not be
treated as proof that this character asset satisfied the supported profile.

The local evidence index is
`~/Library/Application Support/3d-craft/evaluations/resume-case-20260907/index.json`.
It preserves copies of the original receipts and hash-verified screenshots.
Source binding is retrospective: the original browser receipts did not seal
the application commit identity. Raw artifacts and personal content stay
outside this repository and the installable Skill.

The case identified a guidance gap around final transform limits, time-based
damping, and pointer lifecycle. These checks are now documented in the existing
Web3D runtime reference without adding a planner, probe API, schema, or runtime
dependency. The new guidance was not present during the original case; it
requires separate source/package validation and installation.

## Not yet established

- remote CI results for the candidate commit;
- tag, GitHub Release, registry publication, or public package parity;
- Windows or Linux host acceptance;
- physical mobile-device GPU frame timing;
- physical target-device evidence for the new Viewer split, including cold-load
  paint timing, cache reuse, and mobile GPU frame timing. Current bundle and
  browser observations prove the dependency boundary and semantic readiness,
  not an end-user performance improvement;
- the deferred V0.2+ profiles listed in `ROADMAP.md`.

Commit, push, tag, release, publish, and global installation remain separate
authorization boundaries. A local candidate gate must report
`release_eligible=false` whenever the source has no commit or the worktree is
dirty. Detached proofs apply only to their recorded commits, including
`7dcf96a2704eda53199dec1259639323a47ac62a` and the later
`9f8262eae7792792cae074fcd2b9f21b37564ec4` candidate above. Subsequent source
or documentation changes require a new clean gate before inheriting a
release-eligible provenance claim.
