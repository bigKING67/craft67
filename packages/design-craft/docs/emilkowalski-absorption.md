# Emil Kowalski five-skill compatibility and prototype absorption matrix

This document records the deliberate absorption boundary for
`https://github.com/emilkowalski/skills` through reviewed remote commit
`85e8e2363b713506e1d5b6e07a0eb2da66be1bc3`. The compatibility submodule
stays pinned at `7bb7061b5cf7de15ea1aeaf00fbd9e6592a20fce`.

## Contents

- [Inventory truth](#inventory-truth)
- [Status vocabulary](#status-vocabulary)
- [Skill-level matrix](#skill-level-matrix)
- [Latest-range entrypoints](#latest-range-entrypoints)
- [Auxiliary-file matrix](#auxiliary-file-matrix)
- [Intentionally rejected rules](#intentionally-rejected-rules)
- [Current conclusion](#current-conclusion)

## Inventory truth

The pinned compatibility snapshot contains:

- five `SKILL.md` entrypoints;
- three auxiliary Markdown references;
- no `scripts/`, `assets/`, `templates/`, `agents/`, package source, or runtime
  component library under the five Skill directories.

Therefore, "copy more source" means adapting Markdown rules and small CSS/JS
examples. It does not mean vendoring an upstream implementation library that is
not present. The reviewed remote history adds `find-animation-opportunities`,
`pick-ui-library`, `prototype`, `animate`, `ask-sonner`, `animate-expo`, and
`write-swift`; all receive an explicit decision below. The pristine
compatibility source remains available under `upstreams/emilkowalski-skills/`;
the installed Skill receives only the high-value fusion layer.

## Status vocabulary

- `absorbed`: the capability is represented in local instructions, references,
  scripts, templates, or validation.
- `partial`: a useful subset is local, while contextual or lower-value material
  remains upstream-only.
- `missing-high-value`: a valuable capability is still absent and should block
  an "absorption complete" claim.
- `intentionally-rejected`: copying would reduce correctness, conflict with
  authority/runtime evidence, or impose an inappropriate operating policy.
- `provenance-only`: retained for traceability but not used as local behavior.

Library applicability is separate from this upstream status vocabulary. Base UI
may be conditionally supported as a project-selected primitive while the
opinionated `pick-ui-library` entrypoint and a Base UI-only universal
prescription remain `intentionally-rejected`.

## Skill-level matrix

### `emil-design-eng`

| Capability | Status | Local target | Decision |
| --- | --- | --- | --- |
| Motion purpose, frequency, easing, duration, physicality, interruption, accessibility | absorbed | `motion-quality.md` | Kept as calibrated starting points under project authority. |
| Concrete press, anchored overlay, tooltip-group, enter/exit, clip-path, and crossfade recipes | absorbed | `motion-patterns.md` | Added as implementation patterns with browser/performance caveats. |
| Component defaults, low-friction APIs, invisible edge cases, interactive documentation | absorbed | `engineering-quality.md`, `motion-patterns.md` | Adapted from the Sonner lessons without turning memorable naming into a universal rule. |
| Optical sizing, role-specific tracking and leading, text scaling | absorbed | `design-system-contract.md` | Added to the typography contract instead of motion guidance. |
| Animation vocabulary | absorbed | `motion-vocabulary.md` | Expanded to include spring parameters, ambient motion, and animation principles. |
| Mandatory promotional initial response | intentionally-rejected | none | Host/user intent controls the first response; the Skill must not advertise a course before doing work. |
| Absolute framework/GPU assertions | intentionally-rejected | `motion-audit-planning.md` | Local rules distinguish source risk from measured jank/compositing. |

### `apple-design`

| Capability | Status | Local target | Decision |
| --- | --- | --- | --- |
| Pointer-down response, 1:1 tracking, grab offset, capture | absorbed | `interaction-physics.md` | Includes coordinate-space and transform-ownership checks missing upstream. |
| Presentation-value interruption, velocity handoff, projection, snap selection | absorbed | `interaction-physics.md` | Preserves velocity units and runtime verification boundaries. |
| Springs, damping/response, rubber-banding, hysteresis | absorbed | `interaction-physics.md` | Values remain starting points, not universal constants. |
| Product purpose, agency, responsibility, familiarity, flexibility, simplicity, craft, delight | absorbed | `product-design-principles.md` | Converted into operational product tests. |
| Optical typography and multimodal causal feedback | absorbed | `design-system-contract.md`, `product-design-principles.md`, platform references | Applied where the platform supports the behavior. |
| Translucent materials and decorative depth recipes | partial | `visual-judgment.md`, iOS/Android references | Kept contextual; global glass/backdrop-filter rules would conflict with product authority and performance evidence. |
| Exact Apple-like appearance as a default aesthetic | intentionally-rejected | none | Platform behavior may be authoritative; visual imitation is not. |

### `review-animations`

| Capability | Status | Local target | Decision |
| --- | --- | --- | --- |
| Purpose/frequency/timing/origin/interruption/accessibility review bar | absorbed | `motion-quality.md` | Preserves the high craft bar. |
| `Before | After | Why` review format and explicit verdict | absorbed | `motion-quality.md` | Used for normal motion review with bounded findings. |
| Static detector signals for transition-all, ease-in, scale-zero, origin, duration, layout properties, hover, Reduced Motion | absorbed | `design_craft_detect.sh` | Signals require contextual confirmation before becoming findings. |
| "Default to flagging" tone and automatic hard blocks | intentionally-rejected | none | Evidence and user impact decide severity; aggressive tone is not quality. |
| Static code as proof of dropped frames/GPU execution/device feel | intentionally-rejected | `motion-audit-planning.md` | Runtime claims require trace/browser/device evidence. |

### `improve-animations`

| Capability | Status | Local target | Decision |
| --- | --- | --- | --- |
| Recon, stack/token/frequency map, eight-dimension audit | absorbed | `motion-audit-planning.md` | Adds authority and evidence checkpoints. |
| Re-read/vet findings, prioritize by leverage, separate missed opportunities | absorbed | `motion-audit-planning.md` | Uses user impact x frequency x confidence / cost. |
| Self-contained source-stamped plans | absorbed | `templates/motion-plan/plan.md`, `design_craft_motion_plan.py` | Deterministic scaffold plus drift stop conditions. |
| Execute/reconcile lifecycle | absorbed | `motion-audit-planning.md` | Supports proposed/in-progress/complete/stale/retired states. |
| Mandatory subagent fan-out | intentionally-rejected | none | Host capability, current authorization, task size, and project rules govern delegation. |
| Permanent read-only refusal after the user asks to implement | intentionally-rejected | none | Audit-only requests remain read-only; explicit implementation requests can proceed through normal quality gates. |

### `animation-vocabulary`

| Capability | Status | Local target | Decision |
| --- | --- | --- | --- |
| Reverse lookup and concise disambiguation | absorbed | `motion-vocabulary.md` | Keeps naming questions concise and implementation-neutral. |
| Entrances, timing, transforms, state, scroll, interaction, easing, effects, performance | absorbed | `motion-vocabulary.md` | Core glossary retained. |
| Spring parameter terms, looping/ambient motion, anticipation/follow-through/squash-stretch principles | absorbed | `motion-vocabulary.md` | Filled the previous low-cost vocabulary gap. |
| Requirement to quote upstream wording verbatim | intentionally-rejected | none | Local phrasing may be clearer, more concise, and license-attributed without forcing verbatim output. |

## Latest-range entrypoints

| Upstream entrypoint or change | Status | Local target or boundary | Decision |
| --- | --- | --- | --- |
| `find-animation-opportunities` | absorbed | `motion-quality.md`, `motion-audit-planning.md`, `motion-vocabulary.md` | Purpose, frequency, speed, function, missed-opportunity, explicit rejection, and bounded-output rules are already represented locally. The local workflow can report that no candidate survives rather than manufacturing motion. |
| `pick-ui-library` | intentionally-rejected | project dependency authority | Its curated list is a personal library preference, not a stable cross-framework design baseline. Existing dependencies, project constraints, bundle/performance evidence, accessibility, and maintenance cost decide library selection. |
| `prototype` | absorbed | `prototype-workflow.md`, `prototype` mode, project-neutral golden contract | Keep one-piece scope, named divergence axes, realistic interactive context, isolated non-production exploration, one full-size variant at a time, explicit selection before promotion, and default cleanup. |
| Fixed picker markup, dark-glass CSS, URL/query wiring, and keyboard implementation | intentionally-rejected | project/framework/CSP/host authority | The harness is accessible infrastructure, not a universal visual system or runtime contract. |
| Base UI primitive-specific application | partial | `component-primitive-selection.md`, `motion-patterns.md` | Positively supported when project authority selects Base UI: use its real focus, overlay, state, positioning, and motion contracts through project wrappers. This does not authorize a universal migration. |
| Radix UI to Base UI-only prescription | intentionally-rejected | framework-neutral component guidance | `design-craft` supports both when project authority selects them; an upstream wording replacement does not justify ecosystem churn. |
| Earlier README and library-link corrections | provenance-only | pristine upstream history | These edits do not add product behavior. |
| `da80201` README update | provenance-only | pristine upstream history | The follow-up documents the new entrypoint but adds no further behavior. |
| `animate` construction skill (`de33dbe..78761e1`) | absorbed with calibration | `motion-quality.md`, `motion-patterns.md`, `motion-audit-planning.md`, `motion-vocabulary.md` | The ordered purpose/frequency gate, cheapest-fit tool choice, interruption and exit behavior, reduced-motion alternative, pointer gating, and bounded feel checks already exist locally. Absolute frequency, property, easing, GPU, and library prescriptions remain contextual rather than universal. |
| `ask-sonner` (`e48aeea..78761e1`) | provenance-only | project dependency authority | This is operational documentation for one React toast library. It becomes relevant only when the target project already selects Sonner; it is not a cross-framework design baseline and adds no package runtime here. |
| `78761e1` README and `.gitattributes` follow-up | provenance-only | pristine upstream history | Repository presentation and line-ending policy add no product behavior. |
| `animate-expo` (`78761e1..d23d7f8`) | partial | `react-native-expo-motion.md`, adaptive platform route | UI/worklet ownership, gesture interruption, causal haptics, Reduced Motion, and release-build device verification are selectively absorbed only when dependencies prove React Native/Expo. Upstream absolute library, performance, duration, and platform prescriptions remain contextual. |
| Expo recipe and README additions | provenance-only | pristine upstream history | Examples and discovery metadata do not become a package runtime or a default Web reference. |
| `write-swift` | intentionally-rejected | separate Swift implementation authority | A general Swift coding and repository-editing entrypoint expands beyond this web-first UI/UX Skill. Native visual and interaction quality remains covered by the scoped iOS/adaptive references without importing a broad implementation agent. |

## Auxiliary-file matrix

| Upstream file | Status | Local target |
| --- | --- | --- |
| `improve-animations/AUDIT.md` | absorbed | `motion-quality.md`, `motion-audit-planning.md`, detector rules |
| `improve-animations/PLAN-TEMPLATE.md` | absorbed | `templates/motion-plan/plan.md`, `design_craft_motion_plan.py` |
| `review-animations/STANDARDS.md` | absorbed with calibration | `motion-quality.md`, `motion-patterns.md`, `motion-audit-planning.md` |

## Intentionally rejected rules

The local fusion does not copy these as universal truth:

- `transition: all` is a broad ownership risk, but static text alone does not
  prove layout, paint, or dropped frames.
- Transform use does not by itself prove GPU compositing; a full transform
  string does not automatically move a JavaScript-driven animation off the
  main thread.
- `ease-in`, animation above 300 ms, layout-property animation, blur, or
  keyframes require context. They are review signals rather than automatic
  runtime conclusions.
- Keyboard/high-frequency actions normally remove travel and delay, but may
  preserve immediate causal state feedback.
- Reduced Motion is a behavior contract, not simply a shorter duration or a
  blanket removal of all feedback.
- Native haptics, web vibration, translucency preferences, and high-refresh
  behavior must be verified on a platform that actually supports them.

## Current conclusion

### Mobile Web selective update — 2026-09-19

Compared `d23d7f88a2e21c9e4b1418c7abe420f5c1052ba7` through
`85e8e2363b713506e1d5b6e07a0eb2da66be1bc3`: GitHub compare reports a forward
range of two commits, both present, and 16 changed files, below the file cap.
Reviewed the complete new 311-line `skills/mobile-native/SKILL.md` and the
remaining file deltas. The final mobile source SHA-256 is
`888b7651d66d66dbac4e72b7c554638eb19bd971d686d6cbdf030a5ef3788f55`.

| Changed scope | Disposition | Reason / destination |
| --- | --- | --- |
| `mobile-native` | partial | Original guidance in the Mobile Web section of `surface-playbooks.md` uses the existing surface playbook route. Web/PWA stays Web. |
| Twelve existing Skill entrypoints | intentionally-rejected | Eleven add an initial-response block; emil-design-eng removes its course mention. No underlying implementation guidance changed in those deltas. Existing capability decisions remain intact. |
| `performance-cheatsheet.md` | partial | Transform/opacity, bounded rendering and explicit transitions overlap existing guidance. Fixed blur thresholds and universal render/GPU remedies are not imported. |
| `README.md`, empty `.pl` | provenance-only | Navigation/empty metadata; no local runtime change. |

Technical calibration uses the official sources linked from the new section:
keyboard viewport policy is browser-dependent, safe-area padding preserves
normal spacing, touch-action values grant browser gestures, and click remains
the semantic activation boundary. Global overscroll/highlight/selection resets,
fixed typography, default LAN exposure and the claim that no listed condition
can be emulated are excluded. Device-specific acceptance still needs the
affected device; emulation remains useful for its actual, bounded conditions.

Validation is source/contract-only for this increment. No product UI or fixture
was changed to manufacture a mobile-device pass. The earlier Craft component
screenshots remain historical evidence for their hash-bound input; they do not
validate this new section or its loading by an independent agent. No physical
phone, software keyboard, Safari browser bar or PWA install was exercised.

Source checks on 2026-09-19: the strict Emil absorption check and Skill quick
validator passed. An initial standalone-reference layout exceeded the existing
102-entry package limit. The guidance was moved intact into the existing
surface playbook; no package limit was raised. The resulting portable run
passed all 25 gates, including source tests and development maturity.

### Cumulative boundary

`missing-high-value`: none within the selected fusion boundary through remote
head `85e8e2363b713506e1d5b6e07a0eb2da66be1bc3`, reviewed on 2026-09-19.

The cumulative state is now `selective_absorbed`, not an unqualified full-copy
claim. High-value behavior from the five pinned Skills, the motion opportunity
gate, the reviewed prototype workflow, the calibrated `animate` construction
sequence, project-authorized Base UI-specific application, and conditional
React Native/Expo motion contract are local. The Sonner-specific API guide,
general `write-swift` entrypoint, fixed picker visual/runtime, opinionated library
picker, Base UI-only universal prescription, promotional text, aggressive
review posture, host-policy conflicts, decorative recipes, and technically
overbroad claims remain `intentionally-rejected`, `partial`, or
`provenance-only` according to the matrix above.

Historical independent blind evidence is recorded in two cases. These scores
pre-date the mobile Web guidance and do not validate the current Skill tree:

- `emil-motion-ablation`: `design-craft` 98, focused Emil upstream 96,
  no-skill baseline 91.
- `emil-motion-planning-ablation`: `design-craft` 95, focused Emil upstream 76,
  no-skill baseline 80.
