# Blind comparative judgment
Judge only the supplied outputs. Do not infer which skill produced a label. Apply the machine-readable scorecard exactly, recompute each total from criterion points, and return only JSON matching the supplied schema.

## Task prompt

# Motion-system audit and implementation planning

Audit the following static project evidence and produce an implementation-ready
motion improvement roadmap. Do not edit files, create plans on disk, or claim
browser/device validation. Do not name, cite, or reveal any skill, repository,
author, or upstream source in the response; the output will be judged blind.

Product context:

- Surface: a calm desktop operations console used throughout the workday.
- Primary users: keyboard-heavy support and revenue operators.
- Motion purpose: preserve causality and state continuity without slowing task
  throughput.
- Existing authority: `DESIGN.md` requires crisp motion, existing semantic
  tokens, visible focus, and a Reduced Motion path that preserves feedback.
- Available evidence: only the snippets below. No runtime, computed-style,
  trace, screen recording, accessibility-tree, or user test was performed.

Current excerpts:

```css
/* src/styles/motion.css */
:root {
  --duration-fast: 160ms;
  --duration-panel: 240ms;
  --ease-responsive: cubic-bezier(0.23, 1, 0.32, 1);
}

.popover {
  transform-origin: center;
  transition: all 360ms ease-in;
}
```

```tsx
// src/components/CommandPalette.tsx
export function CommandPalette({ open }: { open: boolean }) {
  return (
    <div
      data-open={open}
      className="animate-[palette_420ms_ease-in_both]"
    >
      <SearchResults />
    </div>
  );
}
```

```css
/* src/components/toast.css */
@keyframes toast-enter {
  from { top: -24px; opacity: 0; }
  to { top: 0; opacity: 1; }
}

.toast {
  animation: toast-enter 500ms ease-in forwards;
}
```

```tsx
// src/components/SortableQueue.tsx
function onPointerMove(event: PointerEvent) {
  queueRef.current?.style.setProperty("--drag-y", `${event.clientY}px`);
}

function onPointerUp() {
  setDragging(false);
  animateTo(nearestSlot(currentY), { duration: 400 });
}
```

```css
/* src/components/Button.css - existing correct local precedent */
.button {
  transition: transform var(--duration-fast) var(--ease-responsive);
}

.button:active {
  transform: scale(0.98);
}

@media (prefers-reduced-motion: reduce) {
  .button { transition-duration: 80ms; }
}
```

Return:

1. A concise recon summary: stack signals, where motion lives, existing
   conventions, product personality, frequency map, and evidence level.
2. A vetted priority table with at most six findings and no unsupported runtime
   claims.
3. At most three self-contained implementation plans. Each plan must include
   exact file paths/current excerpts, target behavior, project conventions,
   ordered steps, hard boundaries, mechanical checks, runtime/feel checks,
   Reduced Motion behavior, and a source-drift stop condition.
4. A short recommended execution order and explicitly unverified states.

Stay within 180 lines. Prefer a small set of high-leverage plans over a padded
inventory.


## Human-readable scorecard

# Comparative scorecard

Generated from `scorecard.json`; do not edit by hand.

| Criterion | Weight | Full credit |
|---|---:|---|
| Evidence honesty and recon | 15 | Maps the static motion surface and labels every runtime or feel claim as unverified. |
| Project conventions | 10 | Reuses supplied tokens and the correct local precedent instead of inventing a parallel system. |
| Purpose and frequency | 10 | Prioritizes keyboard and high-frequency restraint plus causal feedback over decoration. |
| Technical accuracy | 15 | Diagnoses property cost, origin, interruption, pointer tracking, and primitive tradeoffs without framework myths. |
| Prioritization | 10 | Vets and ranks a small set by user impact, frequency, confidence, and implementation cost. |
| Plan self-containment | 20 | Plans include exact paths and excerpts, target behavior, steps, boundaries, and drift stop conditions. |
| Verification quality | 10 | Provides targeted mechanical and runtime feel checks without claiming those checks ran. |
| Accessibility and performance | 10 | Defines Reduced Motion behavior and measured performance checks while preserving useful feedback. |
| **Total** | **100** | |


## Machine-readable scorecard

```json
{
  "schema": "design-craft.comparative-scorecard.v1",
  "total": 100,
  "criteria": [
    {
      "id": "evidence_recon",
      "label": "Evidence honesty and recon",
      "weight": 15,
      "full_credit": "Maps the static motion surface and labels every runtime or feel claim as unverified."
    },
    {
      "id": "project_conventions",
      "label": "Project conventions",
      "weight": 10,
      "full_credit": "Reuses supplied tokens and the correct local precedent instead of inventing a parallel system."
    },
    {
      "id": "purpose_frequency",
      "label": "Purpose and frequency",
      "weight": 10,
      "full_credit": "Prioritizes keyboard and high-frequency restraint plus causal feedback over decoration."
    },
    {
      "id": "technical_accuracy",
      "label": "Technical accuracy",
      "weight": 15,
      "full_credit": "Diagnoses property cost, origin, interruption, pointer tracking, and primitive tradeoffs without framework myths."
    },
    {
      "id": "prioritization",
      "label": "Prioritization",
      "weight": 10,
      "full_credit": "Vets and ranks a small set by user impact, frequency, confidence, and implementation cost."
    },
    {
      "id": "plan_self_containment",
      "label": "Plan self-containment",
      "weight": 20,
      "full_credit": "Plans include exact paths and excerpts, target behavior, steps, boundaries, and drift stop conditions."
    },
    {
      "id": "verification_quality",
      "label": "Verification quality",
      "weight": 10,
      "full_credit": "Provides targeted mechanical and runtime feel checks without claiming those checks ran."
    },
    {
      "id": "accessibility_performance",
      "label": "Accessibility and performance",
      "weight": 10,
      "full_credit": "Defines Reduced Motion behavior and measured performance checks while preserving useful feedback."
    }
  ]
}
```

## Required judgment schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["results", "winner", "rationale"],
  "properties": {
    "results": {
      "type": "array",
      "minItems": 3,
      "maxItems": 3,
      "items": {
        "type": "object",
        "required": ["label", "criteria", "total", "summary"],
        "properties": {
          "label": {"enum": ["A", "B", "C"]},
          "criteria": {
            "type": "object",
            "required": [
              "evidence_recon",
              "project_conventions",
              "purpose_frequency",
              "technical_accuracy",
              "prioritization",
              "plan_self_containment",
              "verification_quality",
              "accessibility_performance"
            ],
            "additionalProperties": false,
            "properties": {
              "evidence_recon": {"type": "integer", "minimum": 0, "maximum": 15},
              "project_conventions": {"type": "integer", "minimum": 0, "maximum": 10},
              "purpose_frequency": {"type": "integer", "minimum": 0, "maximum": 10},
              "technical_accuracy": {"type": "integer", "minimum": 0, "maximum": 15},
              "prioritization": {"type": "integer", "minimum": 0, "maximum": 10},
              "plan_self_containment": {"type": "integer", "minimum": 0, "maximum": 20},
              "verification_quality": {"type": "integer", "minimum": 0, "maximum": 10},
              "accessibility_performance": {"type": "integer", "minimum": 0, "maximum": 10}
            }
          },
          "total": {"type": "integer", "minimum": 0, "maximum": 100},
          "summary": {"type": "string", "minLength": 20}
        },
        "additionalProperties": false
      }
    },
    "winner": {"enum": ["A", "B", "C"]},
    "rationale": {"type": "string", "minLength": 40}
  },
  "additionalProperties": false
}
```

## Output A

## 1. Recon summary

**Diagnosis:** the excerpts mix a crisp, token-based button precedent with longer, hard-coded entrances and a fixed-duration drag settle. Align motion ownership and state handling before tuning visual polish.

- **Stack signals:** React-style TSX, CSS transitions/keyframes, an arbitrary animation utility class, and imperative pointer handlers. The utility framework and `animateTo` implementation are not established.
- **Motion locations:** shared tokens/popovers in `src/styles/motion.css`; palette motion in `src/components/CommandPalette.tsx`; toast keyframes in `src/components/toast.css`; drag logic in `src/components/SortableQueue.tsx`.
- **Conventions:** `--duration-fast: 160ms`, `--duration-panel: 240ms`, and `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)`—a strong ease-out-like curve. `src/components/Button.css` demonstrates explicit property ownership, token reuse, and a local Reduced Motion override.
- **Authority/personality:** the supplied `DESIGN.md` requirements favor calm, crisp utility, visible focus, semantic tokens, and preserved feedback under Reduced Motion.
- **Frequency map:** palette and button interactions are likely frequent for keyboard-heavy operators; popovers are repeated contextual interactions; toasts are event-driven; sorting frequency is unknown, but pointer updates are continuous during dragging. These are planning assumptions, not measured usage.
- **Evidence level:** supplied static excerpts only; full files, commit, dependency versions, cascade, lifecycle, and animation APIs are unknown. No files were edited or plans written.

## 2. Vetted priorities

Priorities express implementation order, not demonstrated production severity. No P0 task blocker is established.

| ID / priority | Static evidence | Finding and smallest correction | Unknown / acceptance evidence |
|---|---|---|---|
| F1 / P1 | Palette uses `palette_420ms_ease-in_both`; `open` appears only as `data-open` here. | High-frequency surface has hard-coded, slow-start motion configuration; binding to open/close is not shown. Remove decorative entrance travel and timing; preserve immediate state/focus feedback. | Keyframes, mounting, hiding, and focus ownership unknown. Verify rapid keyboard open/close, typing, and focus restoration. |
| F2 / P2 | Popover uses `transition: all 360ms ease-in` and centered origin. | Broad property ownership and token divergence. Restrict transitions to actual visual properties; use fast/responsive tokens. Correct origin only if anchored scaling is confirmed. | Changed properties and anchoring unknown. Inspect computed styles and placement changes; do not infer layout cost from `all` alone. |
| F3 / P2 | Toast animates `top` and opacity over `500ms ease-in forwards`. | Layout-position property animation is a risk; duration/easing diverge from conventions. Prefer a short opacity entrance with explicit lifecycle ownership. | Positioning may make `top` effective or ineffective; dropped frames are not established. Verify stacked entry, dismissal, and interruption. |
| F4 / P2 | Pointer move writes `event.clientY`; release calls `animateTo(nearestSlot(currentY), { duration: 400 })`. | Coordinate conversion, interruption, and velocity handoff are not demonstrated. Audit those contracts before merely shortening the settle. | Capture, offset, variable consumer, and animation capabilities unknown. Verify grab continuity, release, re-grab, and cancellation. |
| F5 / P2 | Only the supplied button excerpt contains a Reduced Motion branch. | Coverage for the other surfaces is not established. Include explicit non-spatial feedback paths in each implementation. | Global overrides may already exist. Verify effective CSS and JS behavior with the preference enabled and changed live. |

**Vetted out:** centered popover origin is not inherently wrong; per-move CSS-variable writes do not prove broad recalculation; pointer capture cannot be declared absent from these handlers. Keep the supplied button precedent unchanged. No new decorative motion is warranted.

## 3. Implementation plans

All three plans are **proposed, static-only, and independently scoped**. Before implementation, inspect full cited files, applicable instructions, `DESIGN.md`, token consumers, package scripts, and existing tests. Record the current revision. Missing lifecycle/API evidence is an implementation gate—not permission to invent behavior.

### Plan A — Make palette and popover responses immediate and state-owned
**Scope:** F1, F2, and their F5 coverage.

**Exact paths/current excerpts:**
```css
/* src/styles/motion.css */
:root {
  --duration-fast: 160ms;
  --duration-panel: 240ms;
  --ease-responsive: cubic-bezier(0.23, 1, 0.32, 1);
}
.popover {
  transform-origin: center;
  transition: all 360ms ease-in;
}
```
```tsx
// src/components/CommandPalette.tsx
export function CommandPalette({ open }: { open: boolean }) {
  return (
    <div
      data-open={open}
      className="animate-[palette_420ms_ease-in_both]"
    >
      <SearchResults />
    </div>
  );
}
```
**Target/conventions:** palette toggles without entrance travel or animation delay; search and focus remain immediately usable. Popovers use explicit properties and `--duration-fast` / `--ease-responsive`; retain existing semantic styling and focus indicators.

**Ordered steps:**
1. Locate `palette` keyframes, `data-open` rules, mount/unmount ownership, hidden-state semantics, and focus restoration. Determine whether popovers are anchored and which properties actually change.
2. Remove the palette animation class, retaining `data-open` and children. Preserve the verified visibility/focus contract; do not introduce an animation-completion dependency.
3. Replace popover `all` with only the confirmed opacity/transform properties; use the existing fast/responsive tokens. Do not add scale or travel that does not already serve continuity.
4. If scaling is anchored, obtain origin from the existing placement mechanism, including flipped placement. Keep center for genuinely centered surfaces; do not fabricate a positioning-variable API.
5. Add the Reduced Motion rule described below and targeted state/interruption tests.

**Hard boundaries:** only the two cited files unless separately approved; no dependency, token-value, search, positioning-engine, focus-trap, or button changes. If missing state ownership requires another file, stop and rescope.

**Mechanical checks:** confirm the arbitrary palette animation class and popover `transition: all` are gone; verify token resolution and selectors; run the discovered typecheck, lint, relevant tests, and build scripts. Tests must cover open/closed semantics and immediate input readiness.

**Runtime/feel checks—not performed:** repeated shortcut/Escape cycles, typing immediately on open, focus return, pointer versus keyboard activation, interrupted popover toggles, and each supported placement/flip. Capture effective durations and inspect for invisible focusable content.

**Reduced Motion:** palette remains immediate. Popovers remove entrance/exit translation and scale while preserving positioning transforms; change opacity immediately and keep focus/static open-state feedback. Do not blanket-reset a transform used for placement.

**Source-drift stop:** stop if the quoted class/rule, token meanings, `open` contract, placement ownership, or documented motion authority differs materially; rebase the plan before editing.

### Plan B — Give toasts restrained, interruption-safe feedback
**Scope:** F3 and toast F5 coverage.

**Exact path/current excerpt:**
```css
/* src/components/toast.css */
@keyframes toast-enter {
  from { top: -24px; opacity: 0; }
  to { top: 0; opacity: 1; }
}
.toast {
  animation: toast-enter 500ms ease-in forwards;
}
```
**Target/conventions:** opacity-only entrance using `--duration-fast` and `--ease-responsive`; no positional entrance. Toast content and actions are available immediately, independent of animation completion.

**Ordered steps:**
1. Identify the actual toast lifecycle owner, entry/exit state selectors, positioning baseline, stacking behavior, and dismissal/announcement contracts. Its path is not supplied: resolve and explicitly add it to scope before lifecycle edits.
2. Replace the `top` keyframes and retained `forwards` animation with an opacity transition driven by the verified lifecycle state. Use an existing mounted-state mechanism; do not invent selectors or assume `@starting-style` support.
3. Keep the resting layout explicit. If `top: 0` currently supplies an essential final position, preserve that as static positioning after checking the cascade.
4. Ensure dismiss/re-entry retarget from current opacity; closed toasts cannot intercept input. Preserve existing timeout, announcement, ordering, and removal semantics.
5. Add lifecycle tests and the Reduced Motion override.

**Hard boundaries:** no new animation library, stack choreography, stagger, toast timeout changes, or blanket `will-change`. Do not alter placement transforms. If a CSS-only change cannot own lifecycle safely, stop rather than simulate it with arbitrary delays.

**Mechanical checks:** verify no `top` animation or old `toast-enter` usage remains in scope; confirm final-state opacity/position without animation; run discovered CSS/lint, component tests, and build scripts. Test removal without relying solely on `transitionend`.

**Runtime/feel checks—not performed:** single and burst arrivals, multiple stacked toasts, early dismissal during entrance, repeated triggers, action focus, long messages, and background-tab return. Use a trace before claiming a performance improvement.

**Reduced Motion:** no spatial motion and no fade delay; show/remove immediately while preserving message, action, announcement, and dismissal feedback.

**Source-drift stop:** stop if the quoted keyframes/rule, shared animation consumers, token contract, or discovered lifecycle differs from the reviewed baseline. Revalidate before replacing animation ownership.

### Plan C — Preserve drag continuity without changing reorder semantics
**Scope:** F4 and drag F5 coverage.

**Exact path/current excerpt:**
```tsx
// src/components/SortableQueue.tsx
function onPointerMove(event: PointerEvent) {
  queueRef.current?.style.setProperty("--drag-y", `${event.clientY}px`);
}
function onPointerUp() {
  setDragging(false);
  animateTo(nearestSlot(currentY), { duration: 400 });
}
```
**Target/conventions:** 1:1 pointer tracking, preserved grab offset, interruptible settling, and unchanged nearest-position slot selection. Keep direct DOM/style updates rather than adding per-frame React state updates.

**Ordered steps:**
1. Inspect pointer-down/cancel/capture handlers, `--drag-y` consumers, scrolling/coordinate spaces, `currentY` updates, and `animateTo` definition. Confirm how `setDragging(false)` affects the visual element.
2. Establish one coordinate model in CSS pixels: convert `clientY` into queue-local position, preserve grab offset, and account for scrolling. Keep the existing drag threshold/bounds; verify active-pointer capture and cleanup.
3. Give translation one owner; compose rather than overwrite other transforms. On re-grab, cancel settling and start from the current displayed position, not the previous target.
4. Measure release velocity from a short timestamped position history in CSS px/s. Keep `nearestSlot(currentY)` semantics, ensuring `currentY` is the authoritative release position.
5. Use the verified animation API to hand off measured velocity in its required units, with bounds enforced and no decorative bounce. Do not blindly replace `400` with a shorter duration; if the API lacks readable position/velocity and cancellation, stop for an approved API-level plan.
6. Preserve reorder commitment, keyboard behavior, and cancellation; add preference handling and focused tests.

**Projection decision:** do not enable momentum targeting. A separately authorized candidate is `clamp(y + v * 0.10s, minSlot, maxSlot)`, then nearest valid slot; the 100ms horizon is provisional. This diagnostic candidate must not change production target selection without product approval and runtime evidence.

**Hard boundaries:** initially `src/components/SortableQueue.tsx` only; inspect consumers/API read-only. No new dependency, automatic spring migration, pointer easing, changed reorder algorithm, speculative variable relocation, or new keyboard interaction scheme.

**Mechanical checks:** test coordinate conversion, scroll offsets, capture release/cancel, latest release position, velocity-unit conversion, unchanged nearest-slot selection, and animation cancellation. Run discovered typecheck/lint and relevant tests; verify no competing frame-time transform writers.

**Runtime/feel checks—not performed:** grab at different item offsets, slow/fast release, reversal, re-grab mid-settle, pointer leaving bounds, scrolling, cancellation, and dense queues. Record position/velocity continuity; profile before asserting frame-pacing gains.

**Reduced Motion:** retain direct 1:1 tracking because it explains manipulation; remove autonomous release travel, overshoot, and sibling movement animation. Commit the nearest slot immediately, preserving static destination feedback, focus, and existing reorder announcements.

**Source-drift stop:** stop if these handlers, `currentY` meaning, variable ownership, `animateTo` signature/capabilities, or nearest-slot semantics differ from the reviewed baseline.

## 4. Execution order and unverified states

1. **Plan A:** highest expected keyboard-frequency benefit, using existing tokens and narrow ownership.
2. **Plan B:** bounded toast correction once lifecycle ownership is resolved.
3. **Plan C:** resolve API/coordinate gates first, then implement continuity—not speculative physics.
4. Validate normal and Reduced Motion paths per plan; retain each change only after its acceptance checks pass.

**Explicitly unverified:** actual usage frequency; effective cascade/keyframes; supported browsers; focus and accessibility-tree behavior; popover anchoring; toast positioning/lifecycle; drag capture, geometry, velocity, and cancellation; keyboard sorting; live preference changes; visual feel, frame pacing, and device behavior. No runtime, browser, device, trace, recording, or user validation is claimed.


## Output B

## 1. Recon summary

- **Stack signals:** React/TSX, CSS custom properties and keyframes, a utility-style animation class, and imperative pointer/animation code. The utility compiler and `animateTo` implementation are not identified.
- **Motion locations:** shared declarations in `src/styles/motion.css`; component-local palette, toast, queue, and button behavior.
- **Existing conventions:** `--duration-fast: 160ms`, `--duration-panel: 240ms`, and `--ease-responsive`. The button demonstrates an explicit property transition, token reuse, and a local Reduced Motion override.
- **Authority:** `DESIGN.md` requires crisp motion, semantic tokens, visible focus, and reduced-motion feedback. Its full contents are not available here.
- **Product personality:** calm, precise, workday-long utility. Motion should explain a change, not delay input or demand attention.
- **Frequency map — planning assumptions, not measured:** button feedback is likely very frequent; palette use likely frequent for keyboard-heavy operators; popovers recur during inspection; toast frequency depends on operations; sorting is task-dependent but pointer updates are continuous during a drag.
- **Evidence level:** static excerpts only. Declaration-level issues are identifiable; actual rendering, lifecycle behavior, accessibility, performance, and perceived quality remain unverified.

## 2. Vetted priorities

| Priority | Finding and evidence | Intended correction |
|---|---|---|
| P1 | `.popover` uses `transition: all 360ms ease-in` and a centered origin, bypassing shared tokens. Actual transitioned properties and placement are unknown. | Explicit properties, responsive easing, token duration, placement-aware origin only if scaling is justified. |
| P1 | Palette declares `420ms ease-in`; the animation class is unconditional while `open` only appears as a data attribute. Replay, visibility, and dismissal behavior cannot be inferred. | Connect motion to verified open/close lifecycle; make keyboard readiness independent of animation completion. |
| P1 | Toast keyframes animate `top` and opacity for `500ms ease-in`. Whether `top` takes effect depends on positioning not shown. | Use transform/opacity for equivalent visual travel where appropriate; shorten using existing tokens. No performance gain is claimed without measurement. |
| P1 | No Reduced Motion branch is shown for the four audited surfaces. This does **not** establish that none exists elsewhere. | Explicitly verify and cover each path; retain focus, state, and confirmation feedback without decorative travel. |
| P2 | Queue release requests a fixed `400` duration, unlike shared CSS timing. Pointer coordinates, animation units, cancellation, and keyboard sorting are not shown. | Preserve direct manipulation; use a short, interruptible release settle after verifying coordinate and timing contracts. |

The button is a useful local precedent, not a remediation target or proof that every interaction is accessible.

## 3. Implementation plans

### Plan A — Shared rules, popovers, and command palette

**Exact paths/current excerpts**

`src/styles/motion.css`
```css
:root {
  --duration-fast: 160ms;
  --duration-panel: 240ms;
  --ease-responsive: cubic-bezier(0.23, 1, 0.32, 1);
}

.popover {
  transform-origin: center;
  transition: all 360ms ease-in;
}
```

`src/components/CommandPalette.tsx`
```tsx
export function CommandPalette({ open }: { open: boolean }) {
  return (
    <div
      data-open={open}
      className="animate-[palette_420ms_ease-in_both]"
    >
      <SearchResults />
    </div>
  );
}
```

**Target behavior / conventions**
- Popovers respond promptly; the palette preserves opening/closing causality without making search or focus wait.
- Reuse `--duration-fast` for popovers and `--duration-panel` for palette entry, with `--ease-responsive`; exit should be no longer than entry.
- Limit animation to opacity and, only where useful, a small transform. Preserve semantic tokens, visible focus, and established overlay behavior.

**Ordered steps**
1. Inspect the full styles, palette keyframes, utility configuration, overlay lifecycle, placement information, and focus implementation before changing selectors.
2. Replace popover `all` with only the properties that actually change. Remove centered scaling unless warranted; if scaling remains, derive the origin from the existing placement mechanism, including flipped placements.
3. Replace the palette’s literal timing with token-based styling using the project’s existing CSS integration. Do not invent an unverified utility syntax.
4. Tie entry to a real closed→open change. Do not replay on result updates or ordinary rerenders. Use the existing exit/presence mechanism, if any; do not add delayed unmount solely for decoration.
5. Keep logical opening, search readiness, dismissal, and focus restoration independent of animation completion. Ensure closed content cannot receive focus.

**Hard boundaries**
- No new animation dependency, global token retuning, button redesign, or focus/overlay framework rewrite.
- Do not assume `data-open` currently controls hiding. Preserve verified semantics and do not infer a dialog role from the component name.

**Mechanical checks**
- Confirm the targeted `all`, `360ms`, and `420ms` declarations are removed; inspect generated CSS for token resolution and specificity.
- Check open/close selectors, keyframe definitions, rerender behavior, closed-state focusability, and existing type/build tests.
- Test rapid open→close→open and input during entry; assert state does not depend on animation events.

**Runtime/feel checks — to perform**
- Keyboard-open, type immediately, navigate results, dismiss with Escape, and reopen rapidly.
- Verify visible focus, correct focus restoration, no stale exit hiding a reopened surface, and alignment with the actual trigger/placement.

**Reduced Motion**
- Remove translation/scale; use immediate state changes or opacity-only feedback capped at the existing 80ms local precedent.
- Preserve focus and visibility feedback. State cleanup must work even when no animation event fires.

**Source-drift stop**
- Stop and revise this plan if full definitions reveal competing animation utilities, transform ownership, a different presence contract, or conflicting focus/placement behavior; do not stack another animation on top.

### Plan B — Toast entry without layout-position animation

**Exact path/current excerpt**

`src/components/toast.css`
```css
@keyframes toast-enter {
  from { top: -24px; opacity: 0; }
  to { top: 0; opacity: 1; }
}

.toast {
  animation: toast-enter 500ms ease-in forwards;
}
```

**Target behavior / conventions**
- A toast appears promptly and clearly without interrupting work.
- Use `--duration-fast` and `--ease-responsive`; retain existing visual hierarchy and notification semantics.

**Ordered steps**
1. Inspect toast positioning, transform usage, stacking, entry/exit lifecycle, dismissal timers, and announcement behavior.
2. Establish the correct resting position in ordinary CSS. If the current travel is effective and appropriate, replace `top: -24px → 0` with `translateY(-24px) → translateY(0)` plus the existing opacity change.
3. If `top` is currently ineffective, do not introduce 24px of new travel by default; use opacity-only entry unless spatial movement is justified.
4. Replace literal duration/easing with shared tokens. Keep resting styles explicit; retain a fill mode only if the verified lifecycle requires it.
5. Leave notification delivery and dismissal timing independent of entry completion.

**Hard boundaries**
- No changes to message priority, announcement policy, dismissal duration, or stacking algorithm.
- Do not overwrite an existing transform used for stacking or swipe dismissal; resolve ownership before implementation.

**Mechanical checks**
- Confirm entry keyframes no longer animate `top`, and base positioning still defines the intended resting location.
- Check token references, reduced-motion cascade, multiple-toast styles, and existing toast tests.
- Verify appearance does not reset the dismissal timer or duplicate an announcement.

**Runtime/feel checks — to perform**
- Exercise single and burst arrivals, dismissal during entry, actionable toasts, and stack changes.
- Check clipping, overlap, readable arrival, unchanged keyboard focus, and announcements with assistive technology.
- Inspect performance only to validate observed behavior; transform/opacity is not a guarantee of smoothness.

**Reduced Motion**
- Remove vertical travel; use immediate appearance or opacity-only feedback up to 80ms.
- Keep content, actions, and existing announcement behavior intact.

**Source-drift stop**
- Stop if unseen styles own `top`/transform, entry also controls stack layout, or the timer is coupled to animation completion. Resolve that contract before substituting properties.

### Plan C — Direct queue tracking and interruptible settling

**Exact path/current excerpt**

`src/components/SortableQueue.tsx`
```tsx
function onPointerMove(event: PointerEvent) {
  queueRef.current?.style.setProperty("--drag-y", `${event.clientY}px`);
}

function onPointerUp() {
  setDragging(false);
  animateTo(nearestSlot(currentY), { duration: 400 });
}
```

**Target behavior / conventions**
- The dragged item follows input directly, then settles briefly into its committed destination.
- Use `--duration-fast` and responsive easing for ordinary settling through the existing animation interface; verify units and supported easing first.
- Sorting state and keyboard feedback must not wait for decorative settling.

**Ordered steps**
1. Trace `--drag-y`, `currentY`, pointer capture/cancellation, coordinate conversion, slot calculation, and `animateTo` ownership/API.
2. Confirm release uses the latest pointer position in the same coordinate system as `nearestSlot`. Preserve any existing pickup offset and scroll compensation.
3. Keep direct tracking free of eased transitions. Cancel an in-flight settle when a new drag begins; do not add smoothing that makes the item trail input.
4. Resolve shared timing/easing through the existing JS token bridge. If none exists, define a scoped adapter after inspecting project conventions; do not maintain a second hardcoded token table.
5. Commit the reorder independently of visual completion. Make stale completion callbacks harmless; preserve existing cancellation semantics.
6. Inspect keyboard sorting. If absent, scope an explicit companion accessibility task rather than claim pointer tuning solves keyboard access.

**Hard boundaries**
- No sorting algorithm rewrite, spring dependency, unconditional frame-loop refactor, or invented `animateTo` options.
- Do not change raw coordinates until their consumers are understood.

**Mechanical checks**
- Test latest-position release, coordinate conversion, interruption, cancellation, and state updates without completion callbacks.
- Verify duration units, token conversion, Reduced Motion preference handling, and removal of the literal `400`.
- Cover keyboard reorder/focus behavior where implemented; document any missing path.

**Runtime/feel checks — to perform**
- Check rapid drags, immediate re-grab, edge slots, scrolling, pointer cancellation, and keyboard reorder.
- Look for release jumps, trailing motion, stale callbacks, focus loss, and any throughput delay.

**Reduced Motion**
- Retain direct input-coupled tracking; remove autonomous settling and decorative neighbor travel.
- Snap to the committed slot while retaining destination indication, visible focus, and existing reorder feedback.

**Source-drift stop**
- Stop if `currentY` is derived elsewhere, the animation API has different timing units, or another layer owns reorder completion/transforms. Update the plan before changing behavior.

## 4. Execution order and unverified states

1. **Inspect contracts first**, then implement Plan A without changing shared token values.
2. **Implement Plan B** as a small, isolated correction.
3. **Implement Plan C** after establishing coordinate, interruption, and keyboard contracts.
4. Run mechanical checks, then the listed runtime/feel checks in normal and Reduced Motion modes.

**Explicitly unverified:** generated/computed CSS, hidden-state behavior, palette keyframes and replay, focus semantics, toast positioning and announcements, drag coordinates and cancellation, keyboard sorting, animation API units, performance, and perceived timing. No browser, device, accessibility-tree, trace, recording, or user validation has been performed.


## Output C

## 1. Recon summary

- **Stack signals:** TSX components, CSS transitions/keyframes, an arbitrary animation utility, and imperative pointer handling. React-style code is visible; utility tooling and the implementation/library behind `animateTo` are unknown.
- **Motion locations:** shared values and popover rules in `src/styles/motion.css`; component-local palette, toast, queue, and button motion.
- **Existing conventions:** `--duration-fast: 160ms`, `--duration-panel: 240ms`, and `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)`. `src/components/Button.css` correctly demonstrates an explicit property, semantic tokens, and an 80ms Reduced Motion override. Preserve it.
- **Product personality:** calm, crisp, task-first. Motion should explain state changes, not delay focus, typing, navigation, or repeated actions.
- **Frequency map — inferred, not measured:** palette and button interactions are likely frequent; popovers recurrent; toasts event-dependent; queue sorting workflow-dependent. No daily counts are established.
- **Evidence level:** static excerpts only. `DESIGN.md` requirements are supplied context, not independently inspected. No full stylesheet cascade, animation definitions, component lifecycle, or runtime behavior is established.

## 2. Vetted priorities

Priority reflects implementation leverage and product fit, not measured runtime severity.

| # | Priority | Location | Supported finding | Recommended action |
|---|---|---|---|---|
| 1 | High | `src/components/CommandPalette.tsx` | The wrapper declares an unconditional `420ms ease-in` animation utility, separate from `data-open`. Generated CSS and keyframes are unavailable; delayed input or animation replay is not proven. | Remove decorative wrapper animation; keep opening, closing, and keyboard feedback immediate. |
| 2 | High | `src/styles/motion.css` | `.popover` uses `transition: all 360ms ease-in`, bypassing the existing motion tokens and allowing unintended properties to transition. | Explicitly transition only supported visual properties at the fast token and responsive easing. |
| 3 | Medium | `src/components/toast.css` | Entrance animates layout-affecting `top` over `500ms ease-in`. Actual layout work and dropped frames are unmeasured. | Preserve the entrance cue using transform/opacity and existing tokens. |
| 4 | Medium | `src/components/SortableQueue.tsx` | Release requests a fixed 400ms animation after clearing dragging state. Cancellation, release-position continuity, and `currentY` freshness are not shown. | Trace ownership first; implement a short, interruptible settle from the current visual position. |
| 5 | Medium | Palette, popover, toast, queue excerpts | No local Reduced Motion handling is shown for these surfaces. A global or library-level path may exist. | Verify effective coverage, then add targeted alternatives that retain state and focus feedback. |

**Not promoted to findings:** centered popover origin is only problematic if this is a trigger-anchored scaling surface. The CSS-variable write alone does not prove descendant invalidation or poor performance. No additive animation opportunities are justified by this evidence.

## 3. Implementation plans

### Plan 1 — Make the command palette immediate

**Scope and current excerpt — `src/components/CommandPalette.tsx`:**
```tsx
export function CommandPalette({ open }: { open: boolean }) {
  return (
    <div
      data-open={open}
      className="animate-[palette_420ms_ease-in_both]"
    >
      <SearchResults />
    </div>
  );
}
```

**Target behavior:** remove the wrapper animation. Opening, closing, typing, and selection should not wait for decorative motion. Preserve existing visibility semantics and focus behavior; this excerpt does not establish either.

**Project conventions:** follow the supplied `DESIGN.md` requirements for crisp feedback and visible focus. Existing shared values are 160ms/240ms with `cubic-bezier(0.23, 1, 0.32, 1)`, but this high-frequency surface needs no replacement animation.

**Ordered steps:**
1. Locate the generated utility, `palette` keyframes, `[data-open]` rules, and mount/unmount ownership. Verify that keyframes do not provide the only closed-state hiding mechanism.
2. Remove `className="animate-[palette_420ms_ease-in_both]"`; preserve `data-open={open}`, children, and unrelated attributes.
3. Confirm visibility remains state-driven. If removal exposes hidden content or changes interaction semantics, stop and scope that prerequisite separately.
4. Remove an orphaned keyframe only if its exact defining file and lack of other consumers are confirmed; otherwise leave it untouched.

**Hard boundaries:** no new animation library, result stagger, focus-management rewrite, keyboard-binding change, or arbitrary close delay. Do not infer that `data-open` alone hides content.

**Mechanical checks:** review the diff for the utility removal; inspect remaining selectors for closed-state behavior and hidden-content focusability. Run existing typecheck/lint/component-test scripts after discovering their actual names; no script names are known here.

**Runtime/feel checks — future validation:** repeatedly open/close with the keyboard; type immediately on opening; navigate results; press Escape; verify focus restoration, visible focus, and no flash of closed content. Test rapid reversal and populated/empty results.

**Reduced Motion:** the same immediate state change applies. Preserve focus indicators, selection styling, and result feedback rather than substituting another animation.

**Source-drift stop:** the supplied excerpt is the baseline; no commit is known. Stop if the utility, wrapper lifecycle, or visibility ownership differs, or if safe removal requires changes in unidentified files.

### Plan 2 — Align popover and toast motion with existing tokens

**Scope and current excerpts:**
```css
/* src/styles/motion.css */
:root {
  --duration-fast: 160ms;
  --duration-panel: 240ms;
  --ease-responsive: cubic-bezier(0.23, 1, 0.32, 1);
}

.popover {
  transform-origin: center;
  transition: all 360ms ease-in;
}
```
```css
/* src/components/toast.css */
@keyframes toast-enter {
  from { top: -24px; opacity: 0; }
  to { top: 0; opacity: 1; }
}

.toast {
  animation: toast-enter 500ms ease-in forwards;
}
```

**Target behavior:** a popover responds over 160ms; a toast enters over 240ms, preserving the existing 24px displacement without animating `top`. These are initial acceptance targets, not validated feel measurements.

**Project conventions:** use existing tokens unchanged. Match `src/components/Button.css`’s explicit-property pattern and local `@media (prefers-reduced-motion: reduce)` treatment; use its 80ms duration for reduced opacity feedback.

**Ordered steps:**
1. Inspect complete popover open/closed rules, placement transforms, toast positioning, and any existing Reduced Motion overrides before editing.
2. Replace the popover transition with:
   ```css
   transition: transform var(--duration-fast) var(--ease-responsive),
               opacity var(--duration-fast) var(--ease-responsive);
   ```
   Include `transform` only if it belongs to the visual entrance, not positioning. If positioning owns it, use opacity alone; do not make anchor tracking lag.
3. Preserve `transform-origin: center` unless trigger anchoring and scaling are confirmed. If confirmed, use the positioning system’s documented origin value after identifying it; do not invent a library-specific variable.
4. Keep the toast’s final layout position equivalent to `top: 0`; change entrance frames to `translateY(-24px)`/opacity 0 → `translateY(0)`/opacity 1. Use `animation: toast-enter var(--duration-panel) var(--ease-responsive) forwards`.
5. Verify toast transforms are not already owned by stacking, positioning, or dismissal. If they are, stop rather than overwrite them or introduce unscoped wrapper markup.
6. Add reduced-motion rules: popover opacity-only transition at 80ms with `var(--ease-responsive)`; toast opacity-only keyframes at 80ms with that easing. Any popover entrance displacement/scale must become its final visual value immediately, preserving positioning transforms.

**Hard boundaries:** no global reset, token retuning, dependency, new exit choreography, toast lifetime change, or button changes. Retain toast entry keyframes unless actual lifecycle requirements demonstrate a need for retargetable transitions.

**Mechanical checks:** confirm `.popover` no longer uses `transition: all`; toast entrance no longer animates `top`; final positioning is preserved; all normal durations/easing reference existing tokens. Verify reduced rules win the cascade. Run available CSS lint and component tests using discovered scripts.

**Runtime/feel checks — future validation:** open/close popovers rapidly and move/scroll their anchors; verify no placement lag, origin mismatch, or lost focus. Trigger single and stacked toasts, including dismissal during entry; inspect normal speed and slowed playback for jumps. Profile before making performance claims.

**Reduced Motion:** no decorative travel or scale; brief opacity feedback remains. Toast content, announcements, lifetime, and popover focus behavior remain unchanged.

**Source-drift stop:** stop if these declarations differ, token values changed, transforms have competing owners, or toast positioning cannot preserve the existing final layout within these two files. Resolve ownership before applying the proposed declarations.

### Plan 3 — Make queue release continuous and interruptible

**Scope and current excerpt — `src/components/SortableQueue.tsx`:**
```tsx
function onPointerMove(event: PointerEvent) {
  queueRef.current?.style.setProperty("--drag-y", `${event.clientY}px`);
}

function onPointerUp() {
  setDragging(false);
  animateTo(nearestSlot(currentY), { duration: 400 });
}
```

**Target behavior:** maintain direct pointer tracking; settle from the current rendered offset to the selected slot using `--duration-fast` (currently 160ms) and `--ease-responsive` (`cubic-bezier(0.23, 1, 0.32, 1)`). A new drag must take ownership immediately without snapping to a stale start or destination.

**Project conventions:** consume shared motion values through an existing CSS/JS bridge if available. Preserve the button precedent’s explicit transform ownership. Do not introduce a parallel duration scale or a speculative spring dependency.

**Ordered steps:**
1. Trace `currentY`, `--drag-y` consumers, `nearestSlot`, `setDragging`, and `animateTo`. Establish viewport versus local coordinates, scroll handling, duration units, transform ownership, and cancellation capabilities.
2. Ensure release reads the latest drag sample in the same coordinate space as slot selection. Capture the current rendered position before state changes can reset drag styling.
3. Start settling from that position; apply the shared fast duration and responsive easing through the verified API. Keep visual-position ownership until completion; commit logical order once through the existing mechanism.
4. On a new pointer-down, cancel the active settle while retaining its rendered position, then rebase the grab offset there. Ignore stale completion callbacks.
5. Preserve or complete existing pointer-cancel cleanup without inventing reorder semantics. If cancellation, current-position sampling, or token access requires unknown modules, stop and identify that prerequisite first.

**Hard boundaries:** preserve slot-selection rules, logical ordering, pointer capture, scrolling, and keyboard sorting. No new inertia, bounce, dismissal threshold, or unrelated event-system rewrite. Do not replace the CSS variable solely on an unmeasured performance assumption.

**Mechanical checks:** verify API duration units and easing syntax. Add tests for latest-sample release, coordinate conversion, re-grab during settle, cancellation, and stale completion callbacks using the existing test setup. Confirm only one motion owner writes the relevant transform.

**Runtime/feel checks — future validation:** release slowly and quickly; re-grab immediately and midway through settling; sort in a scrolled queue; cancel a drag. Check for release jumps, pointer-offset changes, double commits, and stale destination snaps. Validate keyboard sorting separately.

**Reduced Motion:** retain direct manipulation while the pointer is held; snap to the selected slot on release with no animated travel. Preserve destination/selection styling, focus, and existing reorder announcements. Cancel an active settle if the preference changes to reduce.

**Source-drift stop:** stop if handlers differ, coordinate spaces remain ambiguous, or `animateTo` cannot support cancellation/current-position handoff. Its missing implementation prevents prescribing a trustworthy drop-in API call from these excerpts alone.

## 4. Execution order and remaining uncertainty

1. **Plan 1:** smallest likely change, highest expected keyboard-workflow leverage.
2. **Plan 2:** restore token consistency and explicit property ownership.
3. **Plan 3:** first resolve the unknown animation and coordinate contracts; do not ship a duration-only fix as a continuity fix.

**Explicitly unverified:** actual interaction frequency; generated utility CSS; palette visibility/focus lifecycle; popover placement/origin; toast stacking and dismissal; queue velocity, coordinates, and cancellation; global Reduced Motion coverage; accessibility semantics; browser compatibility; frame performance; and subjective feel. All runtime checks above are acceptance work to perform, not validation already completed.
