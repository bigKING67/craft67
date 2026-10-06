# pbakaus/impeccable absorption matrix

This document records the deliberate fusion and runtime boundary for
`https://github.com/pbakaus/impeccable` through reviewed remote commit
`695df68a5860da4d25cd629fc3727ec8f3c0991b`. The compatibility submodule stays
pinned at `80e4dd0d581fcdb42be62252b7bc07dcd2238330`; selected behavior from the
newer reviewed range is represented by original local modules and contracts,
not copied upstream runtime or generated files.

## Contents

- [Inventory truth](#inventory-truth)
- [Status vocabulary](#status-vocabulary)
- [Command taxonomy](#command-taxonomy)
- [Detector and platform coverage](#detector-and-platform-coverage)
- [Latest reviewed range](#latest-reviewed-range)
- [Runtime and packaging boundary](#runtime-and-packaging-boundary)
- [Current conclusion](#current-conclusion)

## Inventory truth

The pinned compatibility snapshot exposes one canonical source Skill, metadata
for twenty-three public commands plus the umbrella Skill, native platform
references, a detector, generated multi-host copies, and a substantial
live-browser/manual-edit/provider/package runtime. `design-craft` executes only
the stable source detector entrypoint. It absorbs general workflow, judgment,
selected detector correctness, native quality guidance, production hardening,
and bounded reference-fidelity review. It deliberately does not vendor or call
a second browser runtime, hook, forced reviewer, or provider/package system
beside browser67 and the host's existing execution contracts.

## Status vocabulary

- `absorbed`: represented in local instructions, references, scripts,
  templates, or validation.
- `partial`: the general behavior is local, while branded command syntax or a
  specialized runtime remains upstream-only.
- `missing-high-value`: a valuable capability is absent and blocks a complete
  absorption claim.
- `intentionally-rejected`: copying would duplicate runtime infrastructure,
  widen trust boundaries, or conflict with local authority.
- `provenance-only`: retained for traceability without local behavior.

## Command taxonomy

| Upstream command | Status | Local expression |
| --- | --- | --- |
| `/shape` | absorbed | `shape` mode and product/design brief |
| `/craft` | absorbed | `craft` mode and bounded implementation/verification passes |
| `/critique` | absorbed | bounded read-only product/visual judgment |
| `/audit` | absorbed | accessibility, responsive, performance, theming, and anti-pattern audit |
| `/polish` | absorbed | final-state visual and interaction refinement |
| `/harden` | absorbed | hostile data, failures, i18n, overflow, permission, and offline states |
| `/adapt` | absorbed | viewport/context adaptation plus native/adaptive routing |
| `/optimize` | absorbed | measurement-first performance diagnosis |
| `/extract` | absorbed | repeated-use-first token/component extraction |
| `/document` | absorbed | project-approved `DESIGN.md` evolution |
| `/live` | absorbed | browser iteration as a capability; browser67 supplies the runtime |
| `/init` | partial | `PRODUCT.md`/`DESIGN.md` discovery and safe seed helpers replace branded initialization |
| `/onboard` | partial | product context and project authority discovery are local |
| `/animate` | partial | motion-quality, pattern, planning, and runtime-evidence references are local |
| `/layout` | partial | hierarchy, grid, responsive, and surface playbooks are local |
| `/typeset` | partial | typography roles, optical sizing, line length, and hierarchy are local |
| `/colorize` | partial | semantic color roles and contrast are local; arbitrary recoloring is not a baseline mode |
| `/clarify` | partial | information hierarchy, copy, and decision-flow repairs are local |
| `/delight` | partial | causal feedback and restrained product delight are local |
| `/bolder` | partial | stronger hierarchy is supported without a universal intensity transform |
| `/quieter` | partial | reduced noise and surface restraint are supported without a universal style transform |
| `/overdrive` | partial | high-expression work requires explicit style authority rather than an automatic extreme mode |
| `/distill` | partial | repeated patterns can become design-system contracts after evidence of reuse |
| `/impeccable` | partial | the umbrella workflow is fused into `design-craft`; upstream branding and runtime remain separate |

## Detector and platform coverage

| Capability | Status | Local target |
| --- | --- | --- |
| Mechanical pre-scan and deterministic anti-pattern signals | absorbed | `design_craft_detect.sh` invokes `upstreams/impeccable/skill/scripts/detect.mjs` when the source checkout is available, preserves JSON findings even when upstream exits `2`, and redacts URL userinfo before any JSON mode emits data |
| Style-carrier, comment-safe, linked-stylesheet, `rounded-none`, retired single-font, YAML-escape, and Blade-suffix correctness | absorbed | compatibility pin `80e4dd0`; selected behavior is proven by function-level `test_impeccable_detector_contract.py` coverage and `evals/fixtures/impeccable-detector/` |
| Source detector capability disclosure | absorbed | default and `--full-json` output distinguish `available`, `available_regex_fallback`, and `unavailable`; raw `--json-only` intentionally has no wrapper metadata |
| Detector/design-system reconciliation | absorbed | `impeccable-workflow.md`, project authority order, explicit exceptions |
| Reference-first salient-element inventory and fidelity classification | absorbed | `system-review.md`: direct reference inspection before builder summary; match/adaptation/missing/contradicted/unapproved-added matrix |
| Post-fix verdict | absorbed | original finding IDs return as resolved/partial/unresolved without a new defect hunt |
| Browser-native selection/caret/focus/underline/numeral/scrollbar surfaces | partial | focus is required; other surfaces follow project/browser authority and defaults are not automatic defects |
| Degraded/single-context evidence honesty | absorbed | critique method provenance and no-false-delegation rules |
| iOS audit/adapt guidance | absorbed | `ios-quality.md`, platform scanner and fixtures |
| Android audit/adapt guidance | absorbed | `android-quality.md`, platform scanner and fixtures |
| Adaptive parity | absorbed | `adaptive-quality.md`, shared-versus-platform-specific contracts |
| Hostile-data hardening and measurement-first optimization | absorbed | `impeccable-workflow.md`, engineering and performance references |
| Workspace-owned design/product authority | absorbed with calibration | `authority.py` stops implicit inheritance at the nearest Git or recognized project boundary, rejects symlinked authority/metadata, bounds metadata reads, and fails closed when workspace ownership cannot be proved |
| Safe single-file stylesheet context | absorbed with calibration | `detector_policy.py` resolves bounded package-local CSS, strips query/fragment syntax, reports ambiguous root-relative paths, and rejects project escapes and symlink traversal; detector stdout and stderr URL credentials are redacted |
| Comp-fidelity evidence | absorbed with calibration | `comp-fidelity.md` and `design_craft_comp_fidelity.py` use one immutable snapshot per input for parsing, size, and hash; strict PNG/artifact validation produces exact-coordinate per-region measurements with a permanent `measurement_only` verdict |

## Pending engine migration assessment (2026-09-05)

Disposition: **defer engine adoption; keep the compatibility pin**. This is a
bounded compatibility assessment, not a completed review of the new runtime.
The lock's reviewed and absorbed boundaries remain unchanged.

Examined range: `695df68a5860da4d25cd629fc3727ec8f3c0991b` through
`8dac6ae7e020c43ab10ce9b41939f6fd42627b96`: 14 commits and 4,156 file records
from a local forward Git comparison with rename detection disabled. The
GitHub compare response contained only 300 records; that partial response is
not sufficient inventory evidence. The report now detects that boundary and
can recover the full range from existing local objects without fetching or
changing the checkout.

Assessment coverage and decisions:

- The 14 changed canonical `skill/SKILL.src.md` / `skill/reference/*` documents
  were compared at token level. Their changes replace Node script invocations
  with engine verbs and describe the binary launcher. No additional local
  design-method change was selected from those deltas.
- The new tree deletes `skill/scripts/detect.mjs` and
  `cli/engine/detect-antipatterns.mjs`. The local
  `skills/design-craft/scripts/design_craft_detect.sh` still discovers the
  former JS entrypoint. Updating the pin alone would remove that candidate;
  it would not adapt the wrapper to the Rust detector. Existing unavailable
  and fallback behavior must remain explicit.
- `skill/scripts/impeccable` introduces binary discovery, an engine handshake,
  a versioned cache, and a download fallback. These are upstream runtime
  mechanisms, not automatically authorized local dependencies or host writes.
- [Signed bundle verification](https://github.com/pbakaus/impeccable/commit/8dac6ae7e020c43ab10ce9b41939f6fd42627b96)
  was inspected as a future distribution reference: authenticate before
  extraction, bind assets to one release, and reuse the verified file handle.
  It was not implemented locally. The current local installer stages and
  verifies repository source; it does not consume that upstream remote ZIP.
- The full Rust engine, generated provider trees, extension runtime, and
  release chain were not built or independently validated. Inventory coverage
  does not imply behavioral or security review of all 4,156 records.

Local validation: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest
tests.unit.test_impeccable_detector_contract` passed all 14 tests against the
unchanged `80e4dd0d581fcdb42be62252b7bc07dcd2238330` pin. This is current-pin
source/contract evidence, not proof of new-engine compatibility or performance.

Reconsider adoption only for a concrete local need. An authorized migration
would first compare detector output/exit behavior, unavailable-runtime handling,
platform support, distribution trust, and rollback against the current wrapper.
Keep browser67 and project authority intact; do not advance review metadata
merely to clear a remote freshness alert.

## Latest reviewed range

The latest range after `4c5243fcd42d39c1fc281adcaf10be0913095f74`
through `695df68a5860da4d25cd629fc3727ec8f3c0991b` was reviewed on
2026-09-04 and is `selective_absorbed`:

| Capability | Status | Local target or boundary |
| --- | --- | --- |
| State-transition convergence | absorbed with calibration | `engineering-quality.md` requires every route into the same state to converge on one required finalization boundary; `validation-contract.md` exercises applicable normal, recovery/resume, observer, and hot-replacement paths |
| Async construction and teardown ownership | absorbed with calibration | Local contracts require an `AbortSignal`, generation token, or epoch across meaningful `await` boundaries, a final ownership check before resource publication, and release of orphan DOM/browser resources |
| Repeated-instance resolution and cleanup-set symmetry | absorbed with calibration | Local contracts prefer stable identity and semantic validity over first-match DOM lookup, capture the changed instance set, and restore or release that same set |
| Upstream live-browser, HMR, session, shader, provider, and hook implementation | intentionally-rejected | browser67 and project tools retain runtime authority; upstream selectors, state machine, resource objects, and provider copies are not imported |
| Regression tests, live-E2E harness changes, and sixteen generated provider copies | provenance-only | Reviewed as supporting or generated surfaces; they do not become local runtime or package code |

The range changed 21 paths across six commits: one canonical live-browser
implementation, four test or harness files, and sixteen generated provider
copies. The selected local behavior comes from behavior-bearing commit
`524fb8c9500e16a00fa2d55b5ee2d8ca787e2b36`; later commit `3b0f467` only
strengthens upstream regression guards, and `695df68` synchronizes generated
provider output. The compatibility pin remains `80e4dd0`.

### Previous reviewed range

The previous range after `b0594c72d18006b5865c70eb3a97e8b04064e600`
through `4c5243fcd42d39c1fc281adcaf10be0913095f74` was reviewed on
2026-09-04 and is `selective_absorbed`:

| Capability | Status | Local target or boundary |
| --- | --- | --- |
| Runtime-unavailable incumbent visual evidence | absorbed with calibration | `reference-workflow.md` and `validation-contract.md` allow repository-owned committed visual-regression goldens or screenshot fixtures only after exact target, provenance, freshness, current-source, viewport, theme, and variant reconciliation; visible hypotheses do not become a browser/native pass |
| Brief-pinned constraint and direction authority | absorbed | Existing `visual-judgment.md` already keeps product truth and explicit brief constraints authoritative while allowing deliberate visual-world replacement |
| Development direction metadata outside production output | absorbed | Existing `prototype-workflow.md` already separates direction exploration from production implementation and requires prototype residue removal before delivery |
| Critique snapshot lifecycle and persisted runtime state | partial | Evidence provenance and bounded critique are local; a second persistent critique/runtime state machine remains outside the package |
| Roboto/system-stack, flat-hierarchy, gray-on-color, advisory, and URL detector corrections | partial | Useful upstream engine corrections were reviewed, but this absorption does not import parser dependencies or claim correctness beyond the pinned detector and disclosed regex fallback |
| Live-browser, HMR, provider, hook, and image-generation runtime | intentionally-rejected | These duplicate browser67 or host runtime ownership and widen the trust boundary |
| Generated host copies, fixtures, harness artifacts, and package output | provenance-only | Reviewed as downstream/generated surfaces; not vendored into the canonical Skill package |

The reviewed range changed 863 files, dominated by generated provider and
harness copies. The selected local behavior comes from upstream commit
`6fe900dbb47a649ffd54044d4ac16ce04618ddbe`; the compatibility pin remains
`80e4dd0d581fcdb42be62252b7bc07dcd2238330`.

### Earlier reviewed range

The previous range after `f88b2837a7d7c3182e46307bbbb091a1ed547571`
through `b0594c72d18006b5865c70eb3a97e8b04064e600` was reviewed on
2026-08-29 and is `selective_absorbed`:

| Capability | Status | Local target or boundary |
| --- | --- | --- |
| Monorepo-aware `DESIGN.md` and product-context ownership | absorbed with calibration | Original bounded fail-closed `authority.py` resolver, route/platform integration, negation/flow-YAML/malformed-config/symlink fixtures, and no implicit home-level authority |
| Detector URL-userinfo redaction and safe root-relative linked stylesheets | absorbed with calibration | Original `detector_policy.py` plus stdout/stderr redaction, package-local asset roots, query/fragment, ambiguity, boundary-escape, and symlink fixtures |
| Comp comparison, heatmaps, per-region reports, and artifact integrity | absorbed with calibration | Dependency-free `comp_fidelity.py`, CLI, schemas, immutable input snapshots, strict PNG state machine, bounded artifact metadata/I/O, recomputed metrics, and explicit no-registration/no-resize policy |
| Broader parser/cascade/detector engine corrections | partial | The package keeps dependency-free local safeguards and the disclosed upstream regex fallback; it does not claim full upstream parser parity |
| Agent-driven comp reconstruction, mandatory image generation, and automatic thresholds | intentionally-rejected | Existing project/browser authority owns capture and implementation; thresholds are optional project advisories, and human visual review remains separate |
| Live/provider/hooks/generated copies and package runtime | intentionally-rejected | These duplicate browser67 or host runtime and widen the trust boundary |

The compatibility pin stays at `80e4dd0`; only the reviewed and selected-
behavior boundaries advance. No upstream runtime or generated copy is vendored.

### Earlier behavior-bearing range

The earlier range after `ae5e95101a6979e7f7973a4ff57680b3c7adc1ec`
through `5c5553b1d7f9e89bb833f9179cea681742a17720` was reviewed on
2026-08-17 and is `partial`:

| Capability | Status | Local target or boundary |
| --- | --- | --- |
| Reduced-motion alternatives and platform-specific capture evidence | absorbed | Local motion and native quality contracts already require intentional reduced-motion behavior, real simulator/emulator or device evidence, and explicit hardware limits. |
| Capture validity, comp fidelity, bounded review passes, and scoped verdicts | absorbed with calibration | Local visual acceptance separates screenshot validity, rendered comparison, original findings, and exact verdict scope without importing a mandatory reviewer runtime. |
| Shadow interpolation, layout-transition, ground-color, occlusion, image-backed contrast, scoped-ignore, and selector-compilation detector fixes | partial | These are useful canonical engine corrections, but the installed package uses the disclosed regex fallback because parser dependencies are not vendored. The compatibility pin does not advance without local executable fixtures for the selected engine boundary. |
| Critique snapshot/routing and direction/comps workflow changes | partial | Evidence-led critique and direction-first composition already exist locally. Upstream question UI, persisted runtime, fixed routing mechanics, and provider-specific orchestration remain outside the package. |
| Live/provider/browser-session, hook, asset-generation, and generated host copies | intentionally-rejected | These duplicate browser67 or host runtime ownership and would create a second session/evidence authority. |
| Universal detector bans or automatic runtime claims | intentionally-rejected | Static findings remain contextual signals; source presence does not prove browser, native, performance, or installed-host behavior. |

### Cumulative selected boundary

The cumulative absorption state remains `selective_absorbed` through the
selected behavior boundary `524fb8c9500e16a00fa2d55b5ee2d8ca787e2b36`:

| Capability | Status | Local target or boundary |
| --- | --- | --- |
| Explicit brief authority and evidence-based visual authority | absorbed | `visual-judgment.md` |
| Refinement preserves; redesign replaces the visual world without replacing product truth | absorbed | `visual-judgment.md`, existing-redesign playbook |
| Per-surface `Persuade`, `Operate`, `Read`, and `Experience` modes | absorbed | `surface-playbooks.md` |
| Direction-first craft floor and applicable-denominator critique scoring | absorbed | `impeccable-workflow.md` |
| At-most-two batched rendered-verification passes | absorbed | `SKILL.md`; per-tweak screenshot loops remain outside the default workflow |
| Radial halo/spotlight glow, kicker, meaningless section number, fake cursor/pulse, shape-assembled illustration, and aphoristic-copy signals | absorbed | `visual-judgment.md`; treated as contextual signals, not universal bans |
| Random concept seeds, mandatory context loader and no-argument menu | intentionally-rejected | local routing and project discovery remain deterministic and task-led |
| Live/browser/provider/hooks/doctor runtime, asset generation, full detector/vendor bundle, generated provider copies | intentionally-rejected | browser67, host tools, and existing repository governance own these boundaries |
| `fc3dc50..bdaa5a4` live overlay/resume changes, TanStack adapters, deferred source writes, resolution caching, injection/progress coordination, tests, and generated providers | intentionally-rejected | The tail changes only the upstream live/provider runtime; no selected `design-craft` behavior was imported |
| Universal category, font, framework, and library prescriptions | intentionally-rejected | project authority and observed performance/accessibility evidence win |
| Promotional or "award-winning" tone | intentionally-rejected | local output remains factual and evidence-led |
| Workspace-aware authority, credential-safe detector output, and bounded local stylesheet context | absorbed | original local resolver and detector-policy modules with focused regression tests |
| Exact-coordinate comp comparison | absorbed with calibration | measurement-only hashes, heatmaps, side-by-side and region artifacts; human/product/runtime verdicts remain separate |
| Runtime-unavailable committed visual baseline | absorbed with calibration | Repository-owned goldens or screenshot fixtures require exact target, provenance, freshness, current-source, viewport, theme, and variant reconciliation; useful visible evidence does not turn an unavailable runtime into a pass |
| Lifecycle transitions, async teardown, and repeated-instance cleanup | absorbed with calibration | Original local engineering and validation contracts require transition-side-effect convergence, invalidation before async resource publication, stable instance identity, and cleanup over the same captured set |

The compatibility pin remains at the selected canonical detector snapshot, not
the reviewed remote head. New selected behavior is cleanly implemented in the
local dependency-free layer; unselected parser and runtime/provider behavior
remains outside the package.

## Runtime and packaging boundary

The following surfaces are `intentionally-rejected` from the baseline package:

- upstream `live-server`, browser injection, browser session, overlay, and
  manual-edit runtimes, because browser67 and project tools already own that
  trust and lifecycle boundary;
- upstream asset-producer/manual-edit agents and forced delegation policy;
- generated provider output, extension/store artifacts, site output,
  dependencies, and OpenAI/Claude plugin packaging;
- GitHub sheriff automation, which is repository operations rather than product
  design behavior.

The pristine submodule remains available for provenance and selective manual
use. `design-craft` calls only the detector path as an optional source-level
signal. The full static HTML/CSS engine resolves `htmlparser2`, `css-select`,
`css-tree`, and `domutils`; when they are absent, the wrapper runs the regex
fallback and marks the result degraded instead of claiming full engine parity.
Function-level selected-behavior tests, source pinning, and raw detector JSON do
not establish installed-host parity. Design Craft never claims live/browser
evidence unless the corresponding local tool actually ran.

## Current conclusion

The later `695df68..f2c7051` range, through
`f2c7051853848826aac2f4646581d62a732155ad`, was screened on 2026-09-19 and deliberately
deferred; see [the bounded adoption review](impeccable-release-review-2026-09-19.md).
That review does not extend the behavioral completeness claim below.

`missing-high-value`: none within the selected fusion boundary through remote
head `695df68a5860da4d25cd629fc3727ec8f3c0991b`, reviewed on 2026-09-04.

The cumulative state is selective absorption. General workflow, brief and
change-scope authority, surface modes, native quality, detector discipline and
correctness, workspace-owned authority, credential-safe output, reference-first
fidelity, measurement-only comp evidence, runtime-unavailable committed visual
baselines, post-fix verdicts, mechanical craft verification, hardening, and
evidence honesty are local. Lifecycle transition convergence, cancellation-safe
async resource ownership, and symmetric repeated-instance cleanup are now also
explicit local contracts. The duplicative live/provider/package/hook runtime,
forced delegation, universal visual bans, and prescriptive ecosystem choices
remain intentionally outside the product.

Current independent blind evidence is recorded in
`evals/comparative/impeccable-production-ablation/`: `design-craft` 100,
focused Impeccable upstream 97, no-skill baseline 96.
