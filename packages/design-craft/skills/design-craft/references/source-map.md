# Source map

This project keeps upstream repositories as pristine submodules under
`upstreams/`. The installed skill is a curated fusion layer; do not edit
upstream files directly.

## Contents

- [Upstreams](#upstreams)
- [External design references](#external-design-references)
- [Mutable visual discovery sources](#mutable-visual-discovery-sources)
- [Local calibration artifacts](#local-calibration-artifacts)
- [Maintenance rule](#maintenance-rule)
- [Attribution rule](#attribution-rule)

## Upstreams

Mutable remote review state is repository governance metadata recorded in
`upstreams.lock.json` and the matching absorption matrices under `docs/`. The
installed Skill records only pinned compatibility and selected-behavior
boundaries, so provenance-only upstream changes do not invalidate behavioral
evidence for an otherwise unchanged Skill tree.

### Leonxlnx/taste-skill

- URL: `https://github.com/Leonxlnx/taste-skill`
- License: MIT
- Canonical provenance path: `upstreams/taste-skill`
- Pinned compatibility commit:
  `b17742737e796305d829b3ad39eda3add0d79060`
- Selected-behavior boundary:
  `06d6028b5c623016c59ce8536f578e5a1127b499`
- Cumulative status: `selective_absorbed`; behavior through the initial
  `06d6028b5c623016c59ce8536f578e5a1127b499` snapshot is represented in the
  local visual-judgment, product-taste, design-move, and design-system layers.
- Local consolidation also selects supplied-image implementation and opt-in
  web concept-image direction into `image-reference-implementation.md` and
  `web-image-direction.md`. Editorial/tactile and motion-led options live in
  `visual-judgment.md`; these no longer require independent Taste Skill
  installations. This local selection does not advance the remote review pin.
- Contract: `docs/taste-skill-absorption.md`, validated by
  `scripts/design_craft_taste_absorption.py` in the canonical repository.
- Primary material to inspect:
  - `skills/taste-skill/SKILL.md`
  - `skills/redesign-skill/SKILL.md`
  - `skills/minimalist-skill/SKILL.md`
  - `skills/gpt-tasteskill/SKILL.md`
  - `skills/image-to-code-skill/SKILL.md`
  - `skills/stitch-skill/SKILL.md`

Use this upstream for brief inference, anti-slop judgment, visual hierarchy,
motion discipline, redesign protocol, design-system selection, and final
preflight thinking.

### pbakaus/impeccable

- URL: `https://github.com/pbakaus/impeccable`
- License: Apache-2.0
- Canonical provenance path: `upstreams/impeccable`
- Pinned compatibility commit:
  `80e4dd0d581fcdb42be62252b7bc07dcd2238330`
- Selected-behavior boundary:
  `524fb8c9500e16a00fa2d55b5ee2d8ca787e2b36`
- Cumulative status: `selective_absorbed` for the command taxonomy,
  brief/change-scope authority, surface modes, craft floor, applicable scoring,
  detector/native guidance and correctness, reference-first fidelity,
  post-fix verdicts, hardening, measurement, evidence contracts, and bounded
  rendered-verification passes, lifecycle-transition convergence,
  cancellation-safe async resource ownership, stable repeated-instance cleanup,
  workspace-owned authority, credential-safe detector output, bounded linked
  stylesheets, and measurement-only comp fidelity evidence. Runtime-unavailable
  review may also use a repository-owned committed visual-regression baseline
  after exact target, freshness, theme/variant, and source reconciliation,
  without upgrading it to live browser or native evidence.
- Contract: `docs/impeccable-absorption.md`, validated by
  `scripts/design_craft_impeccable_absorption.py` in the canonical repository.
- Detector evidence boundary: local function-level fixtures prove selected
  behavior at the compatibility pin. Full source-checkout static HTML/CSS
  execution additionally requires `htmlparser2`, `css-select`, `css-tree`, and
  `domutils`; the wrapper reports `available_regex_fallback` and degraded output
  when those packages are absent. This is separate from installed-host parity.
- Stable boundary: random concept selection, forced delegation, upstream
  live/provider/hooks runtime, generated provider copies, promotional tone,
  forced reviewers/delegation, absolute visual bans, and universal ecosystem
  prescriptions remain outside the baseline.
- Primary material to inspect:
  - `skill/SKILL.src.md`
  - `skill/scripts/command-metadata.json`
  - `skill/reference/*.md`
  - `skill/scripts/detect.mjs`
  - `cli/engine/engines/`
  - `cli/engine/rules/checks.mjs`

Use this upstream for command taxonomy, audit/polish/harden/optimize/live
iteration patterns, deterministic detector checks, design context files, and
production-readiness flows.

### emilkowalski/skills

- URL: `https://github.com/emilkowalski/skills`
- License: MIT
- Canonical provenance path: `upstreams/emilkowalski-skills`
- Pinned compatibility commit:
  `7bb7061b5cf7de15ea1aeaf00fbd9e6592a20fce`
- Selected-behavior boundary:
  `85e8e2363b713506e1d5b6e07a0eb2da66be1bc3`
- Cumulative status: `selective_absorbed`; the motion-opportunity gate,
  calibrated prototype workflow, project-authorized Base UI-specific
  application, and conditional React Native/Expo motion ownership and evidence
  contract are local. Conditional mobile Web viewport, keyboard, safe-area and
  touch/scroll guidance lives in the Mobile Web section of `surface-playbooks.md`;
  it never selects a native target. The opinionated library picker, general Swift writer, fixed picker
  visual/runtime, and Base UI-only universal prescription are intentionally
  rejected.
- Stable selected behavior: original design-craft references cover
  product-design principles, Apple-style direct manipulation,
  presentation-value interruption, spring response/damping, velocity handoff,
  momentum projection, rubber-banding, accessibility variants, and optical
  typography.
- Stable boundary: absolute heuristics and primitive selection remain calibrated
  by project authority and runtime evidence. Base UI may be applied when selected
  by the project; opinionated universal library substitution, fixed picker
  markup/CSS/wiring, and README-only provenance do not enter the installed
  behavior layer.
- Primary material to inspect:
  - `skills/emil-design-eng/SKILL.md`
  - `skills/apple-design/SKILL.md`
  - `skills/review-animations/SKILL.md`
  - `skills/review-animations/STANDARDS.md`
  - `skills/improve-animations/SKILL.md`
  - `skills/improve-animations/AUDIT.md`
  - `skills/improve-animations/PLAN-TEMPLATE.md`
  - `skills/animation-vocabulary/SKILL.md`
  - reviewed remote `skills/prototype/SKILL.md` and `PICKER.md` at `70744e3`
  - reviewed remote `skills/mobile-native/SKILL.md` at `85e8e23`

Use this upstream for motion purpose, frequency-based animation decisions,
easing and duration standards, origin-aware physicality, interruptibility,
gesture craft, animation performance, reduced-motion behavior, strict motion
reviews, codebase-wide audit-to-plan workflows, and animation vocabulary. Do
not absorb standalone tone, fixed prototype chrome, or unqualified
framework/performance claims; keep the local `design-craft` voice evidence-led,
measured, and project-aware.
In the canonical source repository, see `docs/emilkowalski-absorption.md` for
the capability-level status matrix, including deliberate rejections and
contextual partial coverage.

## External design references

### Gustavo Fior Craft — selected interface details

- Source: https://github.com/gustavo-fior/craft
- Fixed reviewed revision: `1758451bc13c15f7b0c04fc4f22b673852425bbc`.
- Selected concept paths: `content/layout/html-background.mdx`,
  `content/layout/nested-border-radius.mdx`, `content/color/image-outlines.mdx`,
  and `content/typography/optical-alignment.mdx`.
- Local destination: original guidance in `design-system-contract.md` under
  theme parity, typography roles and layout rhythm.
- License observation: README declares MIT, but this revision contains no
  standalone license/notice file. No upstream text, snippets, fonts, images,
  components or generated Skill are redistributed.

This is a fixed reference, not a managed submodule, runtime dependency or
automatic freshness feed. The upstream launch list exposes seven concepts;
other article files are not evidence of launched Skill coverage. Project
tokens and verified rendering govern values. Optical-alignment prose and its
sample disagree on horizontal direction, so no fixed icon offset is adopted.
Sound, chart animation, decorative texture and upstream host instructions are
outside this selection. The canonical repository records paths and source
digests in `docs/gustavo-fior-craft-reference.md`.

### Jakub Krehel skills — selected writing and hardening guidance

- Source: https://github.com/jakubkrehel/skills
- Fixed reviewed revision: `267330e1adfc66a718fb65fa6918c1f06d0a689e`.
- Selected paths: `skills/better-writing/SKILL.md`, `skills/break/SKILL.md`
  and `skills/break/scenarios.md`.
- Local adaptations: voice/content in `design-system-contract.md` and
  component scenario inspection in `impeccable-workflow.md`.
- License/attribution: MIT, copyright 2026 Jakub Krehel; preserved in the
  package's third-party notices and MIT upstream license.

This fixed selective reference is registered as a pristine submodule at
`upstreams/jakubkrehel-skills` for freshness checks. Registration does not
expand the selected instructional behavior. Exact global visual recipes,
one-look browser limits, universal client-component conversion and upstream
host orchestration are excluded. Local product authority and runtime evidence
continue to govern; source incorporation does not prove a real-project run.

### Lieflat Charts — restricted external data-visualization reference

- URL: `https://github.com/larashero3-dotcom/lieflat-charts`
- Reviewed reference commit: `475c9b67ead1f3d63bda73a94b9bf339e9d5c0b6`
- Review date: 2026-09-04.
- License: PolyForm Noncommercial License 1.0.0.
- Role: external reference only; not an upstream submodule, code dependency,
  template authority, or package payload.
- Local behavior adaptation:
  - `references/surface-playbooks.md`
  - `references/report-quality.md`
  - `references/validation-contract.md`

The fixed commit was reviewed for chart-versus-report intent, analytical
question and data-shape selection, encoding integrity, multi-chart composition,
and queryable interaction. The local guidance is original, project-neutral,
and subordinate to project `DESIGN.md`, business truth, installed libraries,
and runtime evidence. No source, templates, catalogs, tokens, media, or runtime
are redistributed from this reference. Personal noncommercial use of the
standalone project is a separate license decision from redistribution in this
MIT-licensed package.

### Vercel design references and clean-room replacement

- URLs:
  - `https://vercel.com/design.md`
  - `https://vercel.com/design.dark.md`
- Review note: inspected as public design-system references on 2026-06-24.
- Historical package paths:
  - `templates/vercel-geist/design.md`
  - `templates/vercel-geist/design.dark.md`
- Current original templates:
  - `templates/developer-product/design.md`
  - `templates/developer-product/design.dark.md`
- Workflow absorption:
  - `references/design-system-contract.md`

The Vercel endpoints were reviewed as design-system research. The current
package no longer redistributes their verbatim snapshots. It ships an original
design-craft developer-product pair with structured semantic tokens, matched
light/dark roles, component states, motion limits, focus rules, and UI copy
discipline.

Use `scripts/design_craft_seed_design.sh` to copy the original pair into a
target project as `DESIGN.md` and `DESIGN.dark.md`. The route wrapper reports
`developer_product_seed_applicable` so a new or weak developer-product surface does
not rely on an implicit style-authority guess.

When a project already has a credible `DESIGN.md`, token system, brand guide, or
strong runtime visual language, keep the project authority first and use the
developer-product templates as a comparison baseline for missing system pieces.

## Mutable visual discovery sources

### Peekpaper

- URL: `https://peekpaper.com/`
- Structured data contract: `https://peekpaper.com/llms.txt`
- Source policy: `https://peekpaper.com/robots.txt`
- Local workflow: `references/reference-workflow.md`
- Portable adapter: `lib/design_craft/peekpaper.py`
- CLI: `scripts/design_craft_reference.py`

Peekpaper is a mutable visual discovery source, not an upstream repository,
design authority, code dependency, engineering proof source, asset library, or
training corpus. Use official issue JSON for bounded discovery and cite the
canonical Peekpaper post page plus the origin URL. Do not redistribute its
screenshots or retain internal ranking, selection-reason, capture-id, or CDN
fields.

Individual works remain candidates or exemplars. Repeated observations become
pattern hypotheses only through the Reference Card and catalog contracts, and
promotion still requires origin runtime evidence, target validation, and a
comparative evaluation. Recheck mutable source samples before reuse.

## Local calibration artifacts

- `references/product-context.md`: original PRODUCT.md/DESIGN.md authority
  separation and platform-resolution contract.
- `references/product-design-principles.md`: curated product-correctness,
  agency, familiarity, feedback, simplicity, and craft principles.
- `references/interaction-physics.md`: curated direct-manipulation,
  interruption, spring, velocity, projection, hysteresis, and rubber-band
  contract.
- `references/react-native-expo-motion.md`: conditional ownership, gesture,
  haptic, Reduced Motion, and release-build evidence contract for dependency-
  proven React Native/Expo targets.
- `references/comp-fidelity.md`, `scripts/design_craft_comp_fidelity.py`, and
  `scripts/design_craft_sealed_rendition_gate.py`: exact-coordinate,
  hash-bound screenshot measurements plus sealed-input orchestration that keep
  measurement integrity explicitly separate from human visual acceptance;
  optional runtime receipts bind Shadow execution and browser network/capture
  facts without promoting them into visual acceptance.
- `references/motion-patterns.md`: original web implementation recipes for
  press feedback, anchored overlays, tooltip groups, interruptible state,
  percentage transforms, clip-path, crossfade repair, and transient lifecycle.
- `references/ios-quality.md`, `references/android-quality.md`, and
  `references/adaptive-quality.md`: original platform-specific audit and
  evidence boundaries built from the reviewed upstream principles.
- `scripts/design_craft_platform_scan.py`: conservative platform inference and
  native/adaptive static scan wrapper; static results are not runtime proof.
- `references/product-ui-taste-review.md`: product UI taste rubric, output
  contract, page-type checks, and acceptance criteria.
- `references/taste-score-calibration.md`: evidence levels, score bands, and
  anti-inflation rules for numeric taste scores.
- `references/foundational-visual-principles.md`: original compact visual
  principle layer for attention, proximity, alignment, repetition, contrast,
  figure/ground, similarity, continuity, closure, and economy.
- `references/design-move-library.md`: original action library that translates
  recurring critique patterns into concrete UI moves and acceptance criteria.
- `references/system-review.md`: original two-level consistency contract for
  semantic component families, project exemplars, sibling same-state
  comparison, surface and interaction inventories, state/theme coverage, one
  finding ledger, and `pass | blocked | incomplete` sign-off.
- `references/prototype-workflow.md`: local calibration of the reviewed Emil
  prototype idea into a framework-neutral, authority-preserving exploration,
  explicit selection, promotion, and cleanup contract.
- `references/reference-workflow.md`: original source-independent Reference
  Card, catalog, Pack, rights, target-fit, evidence, and pattern-promotion
  contract, with a bounded Peekpaper discovery adapter.
- `evals/product-ui-taste/prototype-divergence/`: project-neutral golden
  contract proving distinct product-relevant axes and the no-promotion-before-
  selection boundary without claiming rendered UI evidence.
- `evals/fixtures/impeccable-detector/`: local positive/negative detector
  correctness fixtures for style carriers, comments, versioned stylesheets,
  rounded-none, retired single-font behavior, YAML escapes, and Blade suffixes.
- `evals/product-ui-taste/system-consistency-toolbar/`: project-neutral golden
  fixture for detecting an inconsistent compact-toolbar component family
  without redistributing a product screenshot or project data.
- `evals/product-ui-taste/material-ops-home/`: first screenshot-derived
  calibration case for a clean but generic operations dashboard.
- `evals/product-ui-taste/live-browser-samples/`: L2 browser evidence
  calibration set from real TMWD-observed Chrome tabs; screenshot binaries stay
  outside the repo and the eval records artifact path, hash, dimensions, and
  redacted DOM/style summaries.
- `evals/product-ui-taste/before-after/generic-review-workbench-local-l4/`:
  generic L4 before/after calibration case with desktop/compact screenshot
  metadata, strict case validation, and TMWD evidence-bundle dry-run
  verification against repo-external PNG artifacts.
- `scripts/design_craft_taste_review.sh`: deterministic packet generator for
  product UI taste reviews; it does not replace the agent's judgment.
- `scripts/design_craft_browser_evidence.py`: emits the redacted
  `design-craft.browser-evidence.v1` browser sampler and validates product UI
  score anti-inflation rules.
- `scripts/design_craft_css_smell_scan.py`,
  `scripts/design_craft_focus_audit.py`, and
  `scripts/design_craft_token_audit.py`: original static scanners that provide
  review signals for CSS smells, focus-state risks, and token bypasses.
- `adapters/`: original thin host adapters for installing the canonical skill
  into Codex, Cursor, Claude, Pi, or a generic Agent Skills-compatible client.
- `evals/product-ui-taste/before-after/`: L4 before/after evidence scaffold;
  the template is not itself completed evidence.
- `evals/cross-agent/`: cross-agent benchmark scaffold for comparing how host
  agents apply the same design-craft prompt.

## Maintenance rule

When updating upstreams:

1. Run `scripts/upstream_absorption_report.py --remote` when you need to know
   whether a remote head changed without mutating submodules. The pinned
   compatibility commit may intentionally lag repository review metadata.
2. Run `scripts/sync_upstreams.sh --name <name> --commit <40-char-sha>` only
   after selecting an explicit commit; the helper never advances review or
   absorption metadata automatically.
3. Run `scripts/upstream_absorption_report.py --remote --fail-on-unreviewed`
   to block unreviewed remote drift, then run the local report to classify files as
   `candidate_absorb`, `provenance_only`, or `manual_review` without fetching or
   editing submodules.
4. Inspect upstream changelogs and key skill/command files.
5. Update this source map only when the pinned compatibility commit or selected
   behavior boundary changes. Provenance-only reviews must not change the
   installed Skill tree.
6. Record every mutable review range and decision in `upstreams.lock.json` and
   the matching absorption matrix, then update the strict validator when local
   behavior coverage changes.
7. Never overwrite `skills/design-craft` automatically from upstream.

## Attribution rule

If substantial text, code, scripts, or detector rules are copied into this
project, keep attribution in `THIRD_PARTY_NOTICES.md` and preserve applicable
license headers where required. Prefer original fusion rules that cite the
upstream idea rather than blind copy-paste.
