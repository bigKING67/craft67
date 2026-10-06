# Impeccable-style workflow fusion

Use this for command selection and quality passes inspired by Impeccable while
remaining inside this user's local Codex workflow.

## Contents

- [Mode selection](#mode-selection)
- [Shape brief](#shape-brief)
- [Direction and craft floor](#direction-and-craft-floor)
- [Critique pass](#critique-pass)
- [Audit dimensions](#audit-dimensions)
- [Prototype pass](#prototype-pass)
- [System review pass](#system-review-pass)
- [Polish pass](#polish-pass)
- [Harden pass](#harden-pass)
- [Optimize pass](#optimize-pass)
- [Detector usage](#detector-usage)

## Mode selection

- `shape`: plan UX/UI before code. Use when the feature is vague, the audience
  or job is unclear, or multiple design directions are plausible.
- `craft`: full build flow. Use for new pages, new major components, or new
  feature surfaces that require discovery, implementation, and browser
  iteration.
- `critique`: evaluate whether the UI feels right. Use for heuristic review
  when code changes are not yet requested.
- `audit`: measurable quality check. Use for accessibility, responsiveness,
  performance, theming, and anti-patterns.
- `prototype`: explicit, isolated divergence for one UI piece before a user or
  explicitly delegated selection; follow `prototype-workflow.md`.
- `system-review`: read-only system-consistency review. Use for whole-product or
  multi-page work, shared visual/interaction systems, or a known consistency
  regression; follow `system-review.md`.
- `polish`: final refinement on a functionally complete UI.
- `harden`: real-world resilience: error states, loading states, long text,
  empty states, i18n, permissions, offline, overflow, slow networks.
- `adapt`: make a good design work in another viewport or context.
- `optimize`: performance diagnosis and fixes; measure first.
- `extract`: consolidate repeated UI patterns into tokens/components only
  after repeated real use.
- `document`: capture or update `DESIGN.md` only when the user approves style
  authority evolution.
- `live`: iterate in browser when visual choice is hard to judge from source.

## Shape brief

For nontrivial design work, capture:

- Purpose: what the surface exists to do.
- User: who is using it and under what pressure.
- Content/data: realistic data ranges, empty states, edge cases.
- Primary decision/action: what must become easier.
- Constraints: accessibility, brand, framework, device, deadline.
- Anti-references: what the design must avoid.

Do not over-interview. Ask only if a missing answer changes implementation.

## Direction and craft floor

Settle the brief, authority, surface mode, and visual direction before editing.
Then apply the craft floor to the built result rather than treating the
checklist as a direction generator:

- verify real contrast, spacing rhythm, type hierarchy and overflow;
- verify responsive composition, working controls, keyboard focus, and
  hover/disabled/loading/empty/error states;
- verify factual copy, brief coverage, motion purpose, and reduced-motion
  behavior;
- refuse generic scaffolds and decorative signals listed in
  `visual-judgment.md` unless the brief deliberately earns them.

The floor is mechanical acceptance, not the creative ceiling. A project brief
or committed visual world outranks a generic detector preference.

## Critique pass

Use `critique` for a read-only judgment pass before implementation or when a UI
"feels off" but the fix is not yet obvious. It should produce:

- A one-line design read: surface, audience, vibe, primary job.
- Product-fit verdict: what decision or action is clearer or still buried.
- Visual-fit verdict: hierarchy, density, typography, color intent, motion.
- Generic-output verdict: AI tells, nested-card soup, fake polish, vague copy.
- Top P0/P1/P2/P3 issues and the recommended next mode.

If the user asks for a score, why the UI is not full marks, or a concrete
product UI review, read `product-ui-taste-review.md` and use its 100-point
output contract. Keep that score scoped to the reviewed UI, not this
`design-craft` repo.

For a heuristic score, mark a dimension `n/a` when it genuinely cannot apply
to the selected surface. Report `score / applicable maximum`; never keep a
fixed denominator after excluding dimensions. Name every excluded dimension so
two runs with different denominators are not presented as a like-for-like
trend.

For a full unanchored critique of a viewable target, include method provenance
in the first line:

- `Method: dual-agent (A: <id> · B: <id>)` when independent design review and
  detector/browser evidence were actually delegated.
- `DEGRADED: single-context (<reason>)` when the review could not use isolated
  assessment contexts but still continues.

Do not claim dual-agent, browser overlay, or detector evidence unless those
steps actually ran. For lightweight inline critiques, say the assessment was
single-context instead of silently implying independent review.

Do not turn critique into implementation unless the user asks for changes.

## Audit dimensions

Score mentally or explicitly across:

1. Accessibility: contrast, labels, semantics, keyboard, focus, reduced motion.
2. Performance: Web Vitals, render hot paths, assets, bundle, animation cost.
3. Theming: token use, dark/light parity, hard-coded colors, radius/shadow
   drift.
4. Responsive: layout, overflow, touch targets, mobile viewport behavior.
5. Anti-patterns: generic AI tells, over-decoration, nested cards, poor
   hierarchy.

Severity:

- P0: blocks release or data/task completion.
- P1: should fix in this change if in scope.
- P2: schedule soon; acceptable with explicit risk.
- P3: polish backlog.

Static performance shape can prove unbounded work without proving experienced
latency. Unless the source itself guarantees task failure at the stated scale,
keep an unmeasured render/filter/asset hot path at P1 and promote it to P0 only
after target-runtime evidence shows a release-blocking regression.

## Prototype pass

Use `prototype` only for an explicit exploration request. Keep production code
unchanged while building an isolated surface, default to three genuinely
different product-relevant axes, show one realistic interactive variant at a
time, and verify the applicable runtime before asking for a selection. Do not
copy an upstream picker visual/runtime contract. Promotion and cleanup follow
`prototype-workflow.md` after explicit user selection or explicit delegated
selection authority.

## System review pass

Use `system-review` when a critique of one screenshot or an audit of isolated
properties cannot establish project-level consistency. It inventories the
declared surfaces, semantic component families, interaction patterns,
applicable states, and themes, then reviews visual, interaction, and motion
systems through one finding ledger.

Every visible UI change still receives the lightweight completion gate from
`system-review.md`; the full mode is an escalation, not a replacement for clear
scope. It finishes with `pass`, `blocked`, or `incomplete` and never invents a
second numeric score.

When an approved reference exists, inventory its salient elements directly
before reading any builder-authored summary and use the fidelity matrix in
`system-review.md`. After fixes, score the original findings as `resolved`,
`partial`, or `unresolved`; a successful recapture is evidence input, not a
visual verdict, and the verification pass must not reopen an unrelated hunt.

## Polish pass

Polish only after the UI works. Check:

- Alignment and spacing.
- Typography hierarchy and line lengths.
- Token consistency and contrast.
- Hover/focus/active/disabled/loading/error/success states.
- Motion easing and reduced-motion fallback.
- Copy voice and placeholder removal.

Do not turn polish into a redesign unless the user asked for redesign.

## Harden pass

Use realistic hostile data:

- 1, 20, 60, 200 character names/titles.
- Missing optional fields.
- Empty lists and first-run states.
- 4xx/5xx/network timeout.
- Permission denied and unauthenticated.
- Long translations and RTL if layout risk is high.
- Large numbers, long currency formats, and 1000+ item lists.

Fix with flexible layout, overflow handling, tooltips/disclosures where useful,
clear error UI, bounded lists, pagination/virtualization, and explicit states.

### Component scenario inspection

When a hardening request needs rendered edge-state evidence for a component,
reuse an existing story or isolated preview before building a local harness.
Review-only authorization permits inspection of existing surfaces; creating or
editing a harness needs implementation or exploration scope. Scope the unit
from the request and component inputs rather than starting a whole-app sweep.

Plan cases from reachable inputs, recording the applicable axis and why omitted
axes do not apply. The hostile-data values above are examples, not mandatory
loads or permission to exceed product limits:

| Input or condition | Applicable cases |
| --- | --- |
| External text or translations | Empty, typical, long, unbreakable; supported scripts, emoji or mixed direction where relevant. |
| Repeated items | Zero, one, typical and the supported upper bound; use local fixtures, not live traffic. |
| Available space | Narrow and wide containers, plus flex/grid sibling pressure where used. |
| Defined states | Loading, error, disabled and recovery paths the real component supports. |
| Supported environment | Actual themes, viewport breakpoints, zoom, keyboard/input and reduced motion relevant to the request. |

Import the real component with its fonts, tokens and necessary providers. Keep
its server/client boundary intact; do not convert a server component into a
client component to make a harness compile. Feed explicit local fixtures,
isolate service/storage effects, and keep harness wiring out of production
imports, navigation and shipping bundles. Use the existing isolated preview or
Shadow Lab boundary when a scratch route would otherwise enter production.

Label each case and place a short observed-failure note beside the affected
instance. Container widths test container behavior only: they do not exercise
viewport media queries, viewport units, browser zoom or device input. Exercise
those through the actual runtime and verify the resulting conditions. Use
real interactions for focus, hover and recovery rather than a styled imitation.

Follow the established browser/native ownership and `validation-contract.md`.
Report each planned case as observed pass, observed failure or unverified,
with the exercised condition and evidence. A generated page, source prediction
or URL handed to the user is not an observed pass. Keep performance claims
separate from visual overflow observations. Recheck failing cases after a fix
and broaden only when shared behavior or new evidence warrants it.

Deliver the preview/artifact location, coverage, observed failures and owning
component or rule. Retain only what the project's preview policy or the user
requires, state cleanup ownership, and stop task-owned processes when their
inspection purpose ends; do not keep a server alive merely to preserve a report.

## Optimize pass

Measure or establish a baseline first. Then target:

- LCP: images, fonts, render-blocking assets, server latency.
- INP: expensive handlers, unnecessary renders, heavy effects.
- CLS: missing dimensions, late content, unstable layout.
- Bundle: unused imports, oversized libraries, missing splitting.
- Animations: layout properties, paint-heavy effects, overuse of `will-change`.

Roll back changes that do not improve the target metric or simplify the code.

## Detector usage

If the source repo is available, the upstream detector can be run manually from
the project root:

```bash
node upstreams/impeccable/skill/scripts/detect.mjs --json <target>
```

In normal user projects, prefer local project validation first. Treat detector
findings as signals, not law. Project `DESIGN.md` can intentionally allow
patterns that generic detector rules dislike; document such exceptions.

The source-repo detector compatibility pin includes focused correctness fixes:

- page-level CSS patterns scan actual style carriers rather than comments,
  prose, or code samples;
- comment-safe broken-image scanning does not hide later real JSX;
- local linked stylesheets remain visible through query strings and fragments;
- `rounded-none` does not create a false rounded-border-accent finding;
- the single-font rule remains retired because one family can still create
  hierarchy through size, weight, width, and optical treatment;
- quoted YAML scalar escapes in `DESIGN.md` parse predictably;
- Blade compound suffixes such as `.blade.php` remain scannable without
  broadening traversal to unrelated module extensions.

These selected behaviors are pinned by local fixtures under
`evals/fixtures/impeccable-detector` and function-level source tests. Those
tests prove the selected source functions; they do not prove that the full
static HTML/CSS detector CLI is executable in the current host.

The full source-checkout static engine additionally resolves `htmlparser2`,
`css-select`, `css-tree`, and `domutils`. Design Craft does not install or
vendor those packages. When they are absent, `design_craft_detect.sh` still
runs the upstream regex scan but reports
`upstream_detector_status: available_regex_fallback`, `degraded: true`, and
`optional static HTML/CSS parser dependencies unavailable` in human output and
the equivalent fields in `--full-json`. The raw-compatible `--json-only` mode
contains only upstream output and therefore cannot disclose wrapper capability;
use default or `--full-json` output when capability provenance matters.
An `available` status means the wrapper found an invocable detector and no
known source-checkout parser gap. When that source static engine exists, its
dependency probe passed; the status still does not prove that a particular HTML
target or every static rule was exercised.

The upstream `kicker-above-heading` result is still only a contextual signal
here, not an absolute ban: semantic need, brand/editorial authority, repetition,
and the rendered hierarchy decide whether an eyebrow or kicker is a defect.

The source checkout uses its locked detector first. An installed host may fall
back to a separately installed Impeccable detector and can therefore expose an
older rule set; source-pin and function-level verification must not be reported
as installed-host detector parity or full static-engine runtime parity.
