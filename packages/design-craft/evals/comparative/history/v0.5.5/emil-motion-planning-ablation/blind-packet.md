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

**Verdict from static evidence:** motion is directionally aligned with a calm operations console in one local precedent, but the current excerpts show fragmented implementation: tokenized button feedback coexists with long `ease-in` keyframes, broad `transition: all`, layout-position animation, and no visible Reduced Motion paths on the higher-impact surfaces.

- **Stack signals:** React/TSX components plus CSS modules/global CSS and utility-style arbitrary animation classes. No runtime animation library is proven by the snippets except an `animateTo(...)` call of unknown origin.
- **Where motion lives:** global motion tokens in `src/styles/motion.css`; component-local CSS in `toast.css` and `Button.css`; utility animation class in `CommandPalette.tsx`; imperative drag/settle behavior in `SortableQueue.tsx`.
- **Existing conventions:** semantic tokens exist: `--duration-fast`, `--duration-panel`, `--ease-responsive`. The button precedent correctly uses tokenized `transform`, active feedback, and a Reduced Motion duration override.
- **Product personality:** crisp, calm, low-latency operations UI. Motion should explain state continuity, not decorate or delay repeated keyboard work.
- **Frequency map:** command palette = high-frequency/keyboard-heavy; sortable drag = high-attention direct manipulation; popovers = repeated contextual UI; toasts = occasional but system-feedback critical; buttons = repeated micro-feedback.
- **Evidence level:** static snippets only. No computed styles, runtime smoothness, frame rate, interruption behavior, assistive-tech behavior, or device feel was verified.

## 2. Vetted priority table

| Priority | Evidence | Location | Finding | Smallest safe correction |
| --- | --- | --- | --- | --- |
| P1 | `animate-[palette_420ms_ease-in_both]` | `src/components/CommandPalette.tsx` | High-frequency command UI uses a long, accelerating entry and bypasses semantic tokens. Static evidence does not show a Reduced Motion branch. | Replace arbitrary keyframe class with tokenized open/closed transition using opacity + small transform, fast duration, responsive easing, and explicit reduced-motion behavior. |
| P1 | Pointer move writes `--drag-y` from `event.clientY`; release uses `animateTo(..., { duration: 400 })` | `src/components/SortableQueue.tsx` | Direct-manipulation evidence lacks explicit local coordinate space, grab offset, pointer capture, release velocity, interrupt-from-current behavior, and Reduced Motion behavior. Static evidence cannot prove feel, but the mechanics are under-specified for a draggable queue. | Rework drag state around local delta, pointer capture, measured px/s velocity, transform ownership, and an interruptible settle primitive; keep target semantics unless separately authorized. |
| P2 | `transition: all 360ms ease-in; transform-origin: center;` | `src/styles/motion.css` | Popover motion is broad, longer than existing panel token, and uses delayed-response easing. Center origin is only clearly appropriate for centered overlays, not trigger-anchored popovers. | Limit animated properties, use existing duration/easing tokens, set trigger-relative origin where applicable, and add Reduced Motion override. |
| P2 | `top: -24px` to `top: 0`; `500ms ease-in` | `src/components/toast.css` | Toast entry animates a layout-position property and uses a slow accelerating curve. Static evidence cannot prove jank, but the property and timing are risky for repeated notification feedback. | Animate `transform: translateY(...)` + `opacity` instead of `top`, shorten to tokenized panel/fast duration, use responsive easing, and add Reduced Motion. |
| P2 | Higher-impact snippets lack visible `prefers-reduced-motion` while button has it | Multiple | Reduced Motion is implemented in the button precedent but not visible for palette, popover, toast, or queue settle. | Standardize a component-level Reduced Motion rule: preserve feedback via opacity/color/static state, reduce or remove spatial travel, shorten duration to 80ms where motion remains. |
| P3 | Mixed hard-coded values: `360ms`, `420ms`, `500ms`, `400` | Multiple | Motion vocabulary is inconsistent with the semantic token precedent, making future tuning and product-wide feel harder. | Route routine UI motion through existing semantic tokens before adding any new token. |

## 3. Implementation plans

### Plan A — Tokenize transient overlay motion: popover + command palette

**Current excerpts**

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

**Target behavior**

- Popovers and command palette respond immediately, finish quickly, and preserve causality without theatrical travel.
- Command palette opening must not slow keyboard-heavy workflows.
- Motion uses existing semantic tokens and the button precedent’s Reduced Motion approach.
- Popover origin should be trigger-relative if the component is anchored; keep `center` only for genuinely centered overlays.

**Project conventions to preserve**

- Keep `--duration-fast`, `--duration-panel`, and `--ease-responsive`.
- Prefer `transform` and `opacity`.
- Preserve visible focus and DOM semantics; do not hide focusable content in a way that traps or loses focus.

**Ordered steps**

1. In `src/styles/motion.css`, replace `.popover { transition: all 360ms ease-in; }` with explicit properties only, e.g. `opacity, transform`.
2. Use `var(--duration-panel)` or a shorter local duration if the popover is small; use `var(--ease-responsive)`.
3. Add open/closed state selectors if they already exist; otherwise stop and inspect the actual popover state API before inventing selectors.
4. Set `transform-origin` from an existing positioning variable if present; otherwise choose a documented default only after confirming whether `.popover` is anchored or centered.
5. In `src/components/CommandPalette.tsx`, remove the arbitrary `animate-[palette_420ms_ease-in_both]`.
6. Replace it with a stable class plus `data-open={open}` state styling in CSS or the existing style system.
7. Use opacity plus a very small vertical or scale transform for open/close; avoid large travel.
8. Add `@media (prefers-reduced-motion: reduce)` for both surfaces: no spatial travel, duration around `80ms`, opacity/static state feedback retained.

**Hard boundaries**

- Do not change command execution, search result rendering, or keyboard shortcut behavior.
- Do not introduce a new animation library for this plan.
- Do not globally redefine the meaning of existing duration/easing tokens without a broader design-system decision.

**Mechanical checks**

- Search for remaining `animate-[palette_` and `.popover` `transition: all`.
- Confirm CSS contains explicit transition properties, not `all`.
- Run the project’s existing lint/type-check/build commands after confirming available scripts.

**Runtime/feel checks to perform later**

- Keyboard-open and keyboard-close the command palette repeatedly; confirm it feels immediate and does not delay typing.
- Verify focus remains visible before, during, and after open/close.
- Inspect popover origin against its trigger for anchored variants.
- Check Reduced Motion mode: state change remains clear with minimal or no travel.

**Reduced Motion behavior**

- Command palette: opacity/state feedback only, no positional travel; duration approximately `80ms`.
- Popover: preserve appearance/disappearance feedback; remove scale/slide unless needed for causality and kept extremely short.

**Source-drift stop condition**

- Stop before editing if the command palette already moved to a different animation API, if `.popover` is not the active popover class, if motion tokens were renamed, or if anchoring/origin is controlled by a positioning library contract not visible in the excerpt.

---

### Plan B — Repair toast entry from layout animation to feedback motion

**Current excerpt**

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

**Target behavior**

- Toasts should arrive promptly as system feedback, without slow acceleration.
- Entry should avoid animating layout-position properties.
- Reduced Motion should preserve notification feedback without vestibular travel.

**Project conventions to preserve**

- Use existing semantic duration/easing tokens.
- Prefer `transform` and `opacity`.
- Keep toast placement semantics unchanged.

**Ordered steps**

1. Replace `top` movement in `@keyframes toast-enter` with `transform: translateY(-8px)` to `transform: translateY(0)`, plus opacity.
2. If `.toast` currently relies on `top: 0` for layout placement, keep that as a static positioning rule outside the keyframe.
3. Change `animation: toast-enter 500ms ease-in forwards;` to a tokenized duration, starting with `var(--duration-panel)` for entry or `var(--duration-fast)` if the toast is frequent.
4. Use `var(--ease-responsive)` instead of `ease-in`.
5. Add a `prefers-reduced-motion: reduce` block that removes vertical travel and uses a short opacity transition/animation.
6. Confirm exit motion if present elsewhere before adding new exit behavior; do not invent lifecycle semantics from the entry-only snippet.

**Hard boundaries**

- Do not change toast queueing, timeout, stacking, ARIA live-region behavior, or message copy in this plan.
- Do not add bounce or elastic motion; this is an operations console.
- Do not claim performance improvement without later measurement.

**Mechanical checks**

- Confirm `toast-enter` no longer animates `top`.
- Confirm `.toast` no longer uses `500ms ease-in`.
- Confirm a Reduced Motion rule exists for toast motion.
- Run the existing CSS/build validation available in the project.

**Runtime/feel checks to perform later**

- Trigger single and repeated toasts; confirm entry is noticeable but not sluggish.
- Verify the toast’s final position is unchanged.
- Verify screen-reader announcement timing is not delayed by visual animation.
- In Reduced Motion, confirm the toast appears clearly with minimal travel.

**Reduced Motion behavior**

- No vertical slide.
- Short opacity transition/animation, approximately `80ms`, or immediate appearance if opacity animation causes announcement or timing issues.

**Source-drift stop condition**

- Stop if toast positioning has been refactored away from `top`, if a toast lifecycle manager owns animation classes, or if there is an existing shared notification motion token not represented in the excerpt.

---

### Plan C — Make sortable queue drag physically auditable and interruptible

**Current excerpt**

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

**Target behavior**

- Dragged item tracks the pointer 1:1 after intent is established.
- Movement uses a clear local coordinate space, not raw viewport `clientY` as the final semantic value.
- Release settle starts from the current on-screen value and can accept measured release velocity.
- Existing slot-selection semantics are preserved unless product owners authorize momentum-based target selection.
- Reduced Motion removes elastic/large travel while preserving clear reorder feedback.

**Project conventions to preserve**

- Keep calm, utility-first motion.
- Prefer transform ownership for moving the dragged visual.
- Use existing duration/easing tokens only for non-gesture fallback transitions; use an interruptible primitive for true drag settle if already available.

**Ordered steps**

1. On pointer down, record pointer id, container/item bounds, initial local pointer Y, current presentation Y, and grab offset.
2. Call pointer capture after drag intent is confirmed so tracking continues outside original bounds.
3. Convert movement to local CSS pixels: `localY = event.clientY - containerRect.top`; derive `dragDeltaY` from the starting local Y and grab offset.
4. Apply movement to the dragged item or a dedicated transform wrapper, not broadly to `queueRef`, unless source inspection proves `--drag-y` only invalidates the dragged item.
5. Maintain a short position/time sample buffer using monotonic timestamps; compute release velocity in CSS px/s.
6. On pointer up/cancel, settle from the current presentation value, not from a stale logical `currentY`.
7. Preserve `nearestSlot(currentY)` as the target rule initially. Treat projected-endpoint target selection as an optional later behavior change, not part of this safe correction.
8. Replace fixed `duration: 400` with an interruptible settle configuration if the existing `animateTo` API supports current value + velocity; otherwise stop and choose the smallest compatible animation primitive already present in the project.
9. Add cancellation handling: pointer cancel, lost capture, Escape if keyboard drag exists, and cleanup of inline styles/state.
10. Add Reduced Motion branch: snap with minimal duration, no overshoot/rubber band, clear static reorder/focus feedback.

**Hard boundaries**

- Do not change queue data ordering rules, slot calculation semantics, or persistence behavior.
- Do not add momentum-based target selection without explicit approval.
- Do not introduce broad parent CSS-variable updates if the list can be large and a narrower transform owner is feasible.
- Do not block input until settle completes.

**Mechanical checks**

- Confirm pointer handlers include down/move/up/cancel cleanup paths.
- Confirm coordinate units are documented as CSS px.
- Confirm release velocity is measured from multiple samples, not guessed from one event.
- Confirm drag transform ownership does not overwrite press/focus transforms on the same element without composition.
- Run existing type-check/lint tests.

**Runtime/feel checks to perform later**

- Drag slowly, quickly, reverse direction mid-settle, release outside bounds, and interrupt while settling.
- Confirm no visual jump at drag start: grab offset is preserved.
- Confirm target slot behavior matches the previous nearest-slot contract.
- Verify Reduced Motion mode removes overshoot/large travel while preserving reorder clarity.
- Measure under representative queue size before making performance claims.

**Reduced Motion behavior**

- Keep direct pointer tracking while dragging because it is causal input feedback.
- On release, snap with no bounce/overshoot and very short duration, or commit immediately with clear static slot/focus feedback.

**Source-drift stop condition**

- Stop if `animateTo` is from a library/API with a required different contract, if `currentY` is already a derived presentation value elsewhere, if pointer capture exists outside the excerpt, or if `--drag-y` is already scoped to a single transformed item by unseen CSS.

## 4. Recommended execution order

1. **Plan A first:** it aligns the highest-frequency keyboard surface and fixes the shared overlay vocabulary.
2. **Plan B second:** small, isolated, high-confidence repair for feedback motion.
3. **Plan C third:** highest interaction complexity; implement only after inspecting the full queue component and animation API.

## Explicitly unverified states

- Actual computed styles and active selectors.
- Whether `.popover` is anchored, centered, or reused for multiple overlay types.
- Whether `palette` keyframes include transform, opacity, or other properties.
- Whether existing Reduced Motion rules exist outside the snippets.
- Whether `animateTo` is CSS, WAAPI, spring-based, or library-owned.
- Pointer capture, grab offset, cancellation, and interruption behavior in the full queue.
- Runtime smoothness, layout cost, frame pacing, device feel, accessibility tree, focus order, and screen-reader announcement timing.


## Output B

## 1) Recon summary

- **Stack signals:** React/TSX components, plain CSS, CSS custom-property motion tokens, Tailwind arbitrary animation utility, and an imperative `animateTo(...)` path for drag release. No motion library is confirmed from the snippets.
- **Where motion lives:**  
  - Global tokens: `src/styles/motion.css`  
  - Component CSS: `src/components/toast.css`, `src/components/Button.css`  
  - Inline utility class: `src/components/CommandPalette.tsx`  
  - Pointer/gesture logic: `src/components/SortableQueue.tsx`
- **Existing conventions:** Semantic duration/easing tokens exist: `--duration-fast`, `--duration-panel`, `--ease-responsive`. The button precedent correctly limits transition scope to `transform`, uses a tokenized duration/easing pair, and has a Reduced Motion duration override to `80ms`.
- **Product personality:** Calm, crisp, high-throughput desktop operations UI. Motion should clarify causality and feedback, not add latency or decoration.
- **Frequency map from product context:**  
  - **Very high frequency:** command palette, keyboard-triggered operations, button press feedback.  
  - **Likely high/medium:** sortable queue interactions if used during operations workflows.  
  - **Medium/occasional:** popovers.  
  - **Occasional:** toasts.
- **Evidence level:** Static snippet audit only. No runtime, computed CSS, cascade, trace, accessibility tree, screen recording, device, or user validation was performed.

## 2) Vetted priority table

| # | Severity | Category | Location | Static evidence | Finding | Fix summary |
|---|---|---|---|---|---|---|
| 1 | HIGH | Purpose, duration, easing | `src/components/CommandPalette.tsx` | `animate-[palette_420ms_ease-in_both]` | A high-frequency keyboard surface has a long `420ms` `ease-in` animation. Static evidence cannot prove mount lifecycle, but any palette entrance using this class delays the moment operators are watching. | Remove the palette animation, or reduce to near-instant non-spatial feedback only if required by existing visibility logic. |
| 2 | HIGH | Gesture, interruptibility, performance | `src/components/SortableQueue.tsx` | `setProperty("--drag-y", ...)`; `animateTo(..., { duration: 400 })` | Drag motion appears driven through a parent CSS variable and release uses a fixed `400ms` tween. Static evidence does not confirm affected children or `animateTo` implementation, but the pattern is risky for direct manipulation and interruption. | Drive the dragged item with direct `transform`, carry velocity into release, use a spring-like settle where supported, and branch for Reduced Motion. |
| 3 | HIGH | Performance, easing, tokens | `src/styles/motion.css` | `.popover { transform-origin: center; transition: all 360ms ease-in; }` | `transition: all` can animate unintended properties; `360ms` exceeds the normal UI budget; `ease-in` makes entry feel late. Center origin may also be wrong for trigger-anchored popovers, though actual usage is unverified. | Limit to `transform, opacity`, use existing tokens, shorten duration, and make origin configurable instead of hard-coded center. |
| 4 | MEDIUM | Performance, accessibility | `src/components/toast.css` | keyframes animate `top`; `500ms ease-in`; no Reduced Motion branch in snippet | Toast entry animates layout-position `top`, uses long `500ms ease-in`, and lacks a visible Reduced Motion path in the provided CSS. Static evidence cannot confirm global overrides. | Use `transform: translateY(...)` + opacity, tokenized duration/easing, and reduced-motion opacity-only feedback. |
| 5 | MEDIUM | Cohesion, accessibility | Multiple snippets | Button uses tokens + Reduced Motion; other snippets use ad hoc `360ms`, `420ms`, `500ms`, `ease-in` | Motion conventions are locally correct in `Button.css` but not consistently applied to higher-impact components. | Standardize on existing semantic tokens and the `80ms` Reduced Motion precedent. |

## 3) Implementation-ready plans

### Plan 1 — Remove command-palette latency

**Files / current excerpt**

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

**Target behavior**

- Opening the command palette should not wait on a decorative entrance animation.
- The palette should appear immediately according to the existing `open` / mount / visibility model.
- No spatial animation for this high-frequency keyboard surface.
- Reduced Motion behavior is identical: immediate state change, no movement.

**Project conventions to follow**

- Prefer the local precedent from `src/components/Button.css`: tokenized, scoped motion only when it provides direct feedback.
- For this component, the better convention is deletion: high-frequency keyboard UI should not add entry latency.

**Ordered steps**

1. In `src/components/CommandPalette.tsx`, remove only the arbitrary animation class.
2. If `className` becomes empty, remove the `className` prop entirely.
3. Preserve `data-open={open}` exactly; do not change visibility, focus, mounting, or `SearchResults`.

**Target excerpt**

```tsx
// src/components/CommandPalette.tsx
export function CommandPalette({ open }: { open: boolean }) {
  return (
    <div data-open={open}>
      <SearchResults />
    </div>
  );
}
```

**Hard boundaries**

- Do not change command execution, search behavior, focus management, keyboard shortcuts, or `SearchResults`.
- Do not add a replacement animation unless existing visibility logic breaks without this class.
- Do not introduce new tokens or dependencies.

**Mechanical checks**

- Run `npm run typecheck` if defined.
- Run `npm run lint` if defined.
- Run `npm run build` if defined.
- If the project does not define these scripts, record them as unavailable rather than inventing commands.

**Runtime / feel checks for executor**

- Trigger the command palette repeatedly by keyboard.
- Confirm it appears without a visible slow entrance.
- Confirm repeated open/close does not produce a delayed or replayed animation.
- Confirm focus still lands where it did before.
- Toggle Reduced Motion and confirm behavior remains immediate.

**Reduced Motion behavior**

- No special branch needed after removing the animation.
- Preserve visible focus and state feedback through existing non-motion UI.

**Source-drift stop condition**

- Stop if the class is no longer present, if visibility depends on the animation utility, or if another file defines required `palette` keyframes that also control layout/opacity for this component. Report drift instead of improvising.

---

### Plan 2 — Tokenize popover and toast entry motion

**Files / current excerpts**

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

**Target behavior**

- Popovers transition only `transform` and `opacity`.
- Popover timing uses existing semantic tokens.
- Popover origin is configurable so trigger-anchored usage can express causality; center remains only as fallback.
- Toast entry uses compositor-friendly `transform` + opacity, not `top`.
- Toast duration is shortened and tokenized.
- Reduced Motion preserves feedback with opacity-only, no position movement.

**Project conventions to follow**

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

**Ordered steps**

1. In `src/styles/motion.css`, replace the `.popover` rule with scoped transition properties.
2. Keep existing root tokens unchanged.
3. Add a Reduced Motion override for `.popover`.
4. In `src/components/toast.css`, replace `top` keyframes with `transform: translateY(...)`.
5. Replace `500ms ease-in` with `var(--duration-panel) var(--ease-responsive)`.
6. Add Reduced Motion toast keyframes that animate opacity only for `80ms`.

**Target excerpts**

```css
/* src/styles/motion.css */
.popover {
  transform-origin: var(--popover-transform-origin, center);
  transition:
    transform var(--duration-fast) var(--ease-responsive),
    opacity var(--duration-fast) var(--ease-responsive);
}

@media (prefers-reduced-motion: reduce) {
  .popover {
    transition-duration: 80ms;
  }
}
```

```css
/* src/components/toast.css */
@keyframes toast-enter {
  from {
    transform: translateY(-24px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

@keyframes toast-enter-reduced {
  from { opacity: 0; }
  to { opacity: 1; }
}

.toast {
  animation: toast-enter var(--duration-panel) var(--ease-responsive) forwards;
}

@media (prefers-reduced-motion: reduce) {
  .toast {
    animation: toast-enter-reduced 80ms var(--ease-responsive) forwards;
  }
}
```

**Hard boundaries**

- Do not rename existing tokens.
- Do not add new global duration/easing tokens unless a broader token audit is explicitly approved.
- Do not change toast markup, stacking logic, dismissal timing, or placement.
- Do not assume the popover is trigger-anchored unless the owning component confirms it. The CSS variable only creates a safe hook.

**Mechanical checks**

- Run `npm run lint` if defined.
- Run `npm run build` if defined.
- If CSS linting exists separately, run the existing CSS/stylelint command.

**Runtime / feel checks for executor**

- Open a popover and confirm no unrelated properties animate.
- In slow playback, confirm popover entry feels immediate, not delayed.
- If the popover has a trigger-origin variable set by an owner, confirm it scales from that origin; otherwise confirm fallback center did not regress centered usage.
- Trigger a toast and confirm it moves via transform without layout jump.
- Toggle Reduced Motion and confirm toast uses opacity-only feedback.

**Reduced Motion behavior**

- Popover: keep short feedback at `80ms`; do not remove all state feedback.
- Toast: opacity-only `80ms`; no vertical movement.

**Source-drift stop condition**

- Stop if `.popover` is no longer defined in `src/styles/motion.css`, if toast entry already uses transform and Reduced Motion, or if another stylesheet overrides these exact rules in a way that makes this edit ambiguous.

---

### Plan 3 — Make sortable drag direct, interruptible, and velocity-aware

**File / current excerpt**

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

**Target behavior**

- During drag, the dragged item follows the pointer through direct `transform`, not a parent CSS variable that may recalculate broader styles.
- Release motion settles to the nearest slot with velocity continuity where the existing animation API supports it.
- Fixed `400ms` tween is replaced by an interruptible spring-like settle.
- Reduced Motion keeps direct manipulation while dragging, then snaps or settles in `80ms` without bounce.

**Project conventions to follow**

- Use transform-based motion, matching the button precedent.
- Use existing semantic timing where a timed fallback is necessary: `--duration-fast` / `80ms` Reduced Motion.
- Do not add new animation dependencies.

**Ordered steps**

1. Inspect `src/components/SortableQueue.tsx` for the actual dragged item ref or element handle.
2. If only `queueRef` exists and there is no safe dragged-item ref, add a narrowly scoped dragged-item ref in this component only.
3. Track drag start position, latest pointer position, latest timestamp, and previous pointer sample.
4. Replace parent CSS variable writes with direct transform on the dragged element:

```tsx
draggedItemRef.current!.style.transform = `translate3d(0, ${dragDeltaY}px, 0)`;
```

5. On pointer up, compute release velocity from the last two pointer samples.
6. Replace fixed duration release with the existing API’s closest spring/velocity-supported form. Use this target only if supported by the existing `animateTo` implementation:

```tsx
animateTo(nearestSlot(currentY), {
  type: "spring",
  duration: 0.5,
  bounce: 0.2,
  velocity: releaseVelocity,
});
```

7. If `animateTo` does not support spring or velocity, do not fake it with a longer tween. Stop and report the API limitation.
8. Add a Reduced Motion branch for release:

```tsx
animateTo(nearestSlot(currentY), {
  duration: 80,
  bounce: 0,
});
```

Only use this exact shape if the existing API accepts these fields; otherwise use the project’s existing equivalent.

**Hard boundaries**

- Do not change queue ordering rules, nearest-slot math, selection state, persistence, keyboard reordering, or ARIA behavior.
- Do not introduce a new gesture library.
- Do not move animation state into global state.
- Do not animate layout properties such as `top`, `margin`, or `height`.
- Do not apply transforms to the whole queue unless the UI intentionally drags the entire queue.

**Mechanical checks**

- Run `npm run typecheck` if defined.
- Run `npm run lint` if defined.
- Run relevant component/unit tests if a test script exists.
- Build if a build script exists.

**Runtime / feel checks for executor**

- Drag slowly: item should remain directly under the pointer with no visible lag.
- Drag quickly and release: item should continue naturally toward the nearest slot rather than stopping then tweening.
- Interrupt by dragging again during settle: motion should retarget from the current visual position, not restart from the original slot.
- In slow playback, confirm only `transform` changes during drag/release.
- Toggle Reduced Motion: dragging still follows the pointer, release has no bounce and resolves quickly.

**Reduced Motion behavior**

- User-controlled drag movement remains because it is direct manipulation.
- Programmatic release motion is shortened to `80ms` or snapped through the existing API’s closest reduced-motion equivalent.
- No bounce in Reduced Motion.

**Source-drift stop condition**

- Stop if `onPointerMove`, `onPointerUp`, `queueRef`, `currentY`, `nearestSlot`, or `animateTo` differ materially from the excerpt, or if the animation API shape cannot be verified from local code.

## 4) Recommended execution order

1. **Plan 1 — Command palette:** highest throughput impact, smallest safe edit.
2. **Plan 2 — Popover/toast CSS:** broad cohesion and performance cleanup using existing conventions.
3. **Plan 3 — Sortable queue:** highest interaction complexity; do after simpler token and CSS fixes because it needs API verification and feel review.

## Explicitly unverified states

- Actual package manager and available scripts.
- Whether `CommandPalette` mounts/unmounts or only toggles `data-open`.
- Definition and cascade behavior of the `palette` keyframes.
- Whether `.popover` is trigger-anchored, centered, reused, or overridden elsewhere.
- Whether global Reduced Motion handling exists outside the snippets.
- `animateTo` implementation, supported options, and interruption behavior.
- Actual drag element structure, queue virtualization, and child style recalculation cost.
- Runtime frame rate, layout/paint/composite traces, computed styles, focus behavior, accessibility tree, and user-perceived feel.


## Output C

## 1. Recon summary

**Stack signals:** React/TSX components, CSS modules/files, global CSS tokens, utility-style arbitrary animation class, and imperative pointer-driven animation.

**Where motion currently lives:**
- `src/styles/motion.css`: semantic motion tokens and `.popover` transition.
- `src/components/CommandPalette.tsx`: inline utility animation class.
- `src/components/toast.css`: keyframe animation.
- `src/components/SortableQueue.tsx`: pointer move style mutation and JS `animateTo`.
- `src/components/Button.css`: existing good precedent for semantic token use and Reduced Motion.

**Existing conventions from evidence:**
- Semantic tokens exist: `--duration-fast`, `--duration-panel`, `--ease-responsive`.
- Preferred local precedent: `transform` transition, `var(...)` tokens, and `@media (prefers-reduced-motion: reduce)` shortening to `80ms`.
- Current inconsistencies: raw durations, `ease-in`, `transition: all`, positional animation via `top`, and missing visible Reduced Motion branches in several snippets.

**Product personality:** calm desktop operations console. Motion should clarify cause/effect and preserve continuity, not add decorative delay.

**Frequency map:**
- **Continuous / high-frequency:** `SortableQueue` drag.
- **Frequent operator action:** `CommandPalette`.
- **Frequent feedback:** toast.
- **Contextual support UI:** popover.
- **Low-amplitude precedent:** button press.

**Evidence level:** static snippet audit only. No runtime, computed-style, accessibility-tree, performance trace, screen recording, browser, or device validation was performed.

---

## 2. Priority table

| Priority | Finding | Static evidence | Risk to product | Recommended plan |
|---:|---|---|---|---|
| P0 | Motion lacks one consistent semantic contract across surfaces | Raw `360ms`, `420ms`, `500ms`, `400`; mixed `ease-in` and token easing | Operators may experience uneven pacing across repeated workflows | Plan 1 |
| P0 | `.popover` uses `transition: all` | `transition: all 360ms ease-in;` | May animate unintended properties and create noisy or fragile UI changes | Plan 1 |
| P1 | Command palette uses an arbitrary one-off animation with no shown close/reduced path | `className="animate-[palette_420ms_ease-in_both]"` | A frequent keyboard surface may feel delayed or inconsistent | Plan 2 |
| P1 | Toast animates layout-affecting `top` and uses slow raw timing | `from { top: -24px; ... }`, `500ms ease-in` | Feedback motion may be more expensive and slower than needed | Plan 2 |
| P1 | Drag snap uses raw JS duration and no shown Reduced Motion branch | `animateTo(..., { duration: 400 })` | Direct manipulation may feel detached from pointer release, especially in repeated queue work | Plan 3 |
| P2 | Reduced Motion is present only in the button precedent | Button has `80ms`; other snippets do not show equivalent branches | Accessibility requirement is inconsistently implemented in visible evidence | Plans 1–3 |

---

## 3. Implementation plans

### Plan 1 — Establish a shared motion contract and remove unsafe generic transitions

**Exact file paths / current excerpts**

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

`src/components/Button.css`

```css
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

**Target behavior**
- All common motion uses semantic tokens.
- Popovers animate only intended properties, likely `opacity` and `transform`.
- Reduced Motion remains perceptible but shorter, matching the existing `80ms` precedent.
- No component depends on `transition: all`.

**Project conventions to preserve**
- Keep existing token names.
- Reuse `--duration-fast`, `--duration-panel`, and `--ease-responsive`.
- Follow the button precedent: transform-based motion and `80ms` Reduced Motion.
- Preserve visible focus behavior; do not add motion that competes with focus indication.

**Ordered steps**
1. In `src/styles/motion.css`, add a shared reduced duration token, for example:
   - `--duration-reduced: 80ms;`
2. Replace `.popover` transition with explicit properties:
   - `transition: opacity var(--duration-fast) var(--ease-responsive), transform var(--duration-fast) var(--ease-responsive);`
3. Keep `transform-origin: center` unless product review shows a better causal anchor.
4. Add a local Reduced Motion branch for `.popover`:
   - shorten duration to `var(--duration-reduced)`.
   - avoid large scale/translate distances if any exist elsewhere.
5. Do not convert unrelated components in the same patch unless they directly use these shared tokens.

**Hard boundaries**
- Do not introduce a new animation library.
- Do not rename existing tokens without a compatibility pass.
- Do not remove focus styles or alter keyboard behavior.
- Do not globally disable all animation in Reduced Motion; preserve concise feedback.

**Mechanical checks**
- Search for `transition: all`.
- Search for raw timing values near motion declarations: `360ms`, `420ms`, `500ms`, `400`.
- Search for `ease-in` in motion contexts.
- Confirm `.popover` no longer transitions unspecified properties.

**Runtime / feel checks to perform later**
- Open and close popovers repeatedly.
- Verify the motion feels crisp and does not delay selection or dismissal.
- Confirm focus ring remains visible before, during, and after transition.
- Check Reduced Motion mode still gives brief state feedback.

**Reduced Motion behavior**
- Use `80ms` or `var(--duration-reduced)`.
- Keep opacity/transform feedback.
- Avoid long travel, bounce, overshoot, or decorative staging.

**Source-drift stop condition**
- Before implementation, verify the quoted `.popover` and token block still match. If the file has already been refactored or tokens changed, stop and re-audit the current motion contract before patching.

---

### Plan 2 — Normalize entry/exit motion for command palette and toast

**Exact file paths / current excerpts**

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

**Target behavior**
- Command palette and toast use tokenized, transform/opacity-based motion.
- Frequent surfaces enter quickly enough for keyboard-heavy operators.
- Toast feedback moves without animating `top`.
- Reduced Motion preserves feedback with shorter duration and reduced distance.
- Open/closed state is expressed through stateful classes or data attributes, not a permanent one-shot arbitrary animation.

**Project conventions to preserve**
- Use semantic durations and `--ease-responsive`.
- Prefer CSS classes/data attributes over one-off arbitrary animation strings for reusable surfaces.
- Preserve existing component API: `CommandPalette({ open })`.
- Keep toast semantics and placement unchanged unless verified separately.

**Ordered steps**
1. Replace the command palette arbitrary animation class with a named class, for example:
   - `className="command-palette"`
   - retain `data-open={open}`.
2. Define CSS for:
   - `.command-palette[data-open="true"]`
   - `.command-palette[data-open="false"]`
3. Use `opacity` and a small `transform`, such as translate/scale, tied to `var(--duration-panel)` or `var(--duration-fast)` depending on desired prominence.
4. Avoid `ease-in`; use `var(--ease-responsive)`.
5. Update `toast-enter` to use transform:
   - `from { transform: translateY(-8px); opacity: 0; }`
   - `to { transform: translateY(0); opacity: 1; }`
6. Change `.toast` animation duration from raw `500ms` to a semantic token, likely `var(--duration-fast)` for feedback or `var(--duration-panel)` if the toast is large.
7. Add Reduced Motion branches for both surfaces:
   - duration `var(--duration-reduced)` or `80ms`.
   - reduce travel distance.
   - keep opacity feedback.
8. If an exit animation is needed, implement it explicitly rather than relying only on mount/unmount behavior. If the component unmounts immediately today, do not claim exit support without changing lifecycle.

**Hard boundaries**
- Do not change search behavior, result rendering, or keyboard shortcuts.
- Do not alter toast queueing, dismissal timing, or ARIA behavior unless separately audited.
- Do not introduce decorative bounce, blur, spring overshoot, or long staged animation.
- Do not claim exit animation support unless mount/unmount timing is implemented and tested.

**Mechanical checks**
- Search for `animate-[` on command palette-like surfaces.
- Search for `@keyframes` blocks that animate `top`, `left`, `right`, `bottom`, `width`, or `height`.
- Search for `500ms ease-in` and `420ms ease-in`.
- Confirm command palette motion is controlled by `data-open`.
- Confirm toast keyframes no longer modify `top`.

**Runtime / feel checks to perform later**
- Open command palette with keyboard repeatedly; it should feel immediate, not theatrical.
- Close it via keyboard and pointer; state continuity should remain clear.
- Trigger multiple toasts; motion should not compete with task focus.
- Validate Reduced Motion mode still communicates appearance/dismissal.

**Reduced Motion behavior**
- Command palette: short opacity/very small transform transition, around `80ms`.
- Toast: short opacity transition with minimal or no translate distance.
- No long slide-in, no delayed feedback, no complete loss of state indication.

**Source-drift stop condition**
- Verify `CommandPalette.tsx` still uses `data-open={open}` and the arbitrary animation class before changing it. Verify `toast.css` still owns `toast-enter`. If either surface has moved or lifecycle changed, stop and re-scope.

---

### Plan 3 — Make queue drag motion direct, bounded, and preference-aware

**Exact file path / current excerpt**

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

**Target behavior**
- During drag, visual position tracks the pointer directly.
- On release, snap motion is brief, causal, and tokenized.
- Reduced Motion uses a very short snap while still showing state resolution.
- The implementation avoids unnecessary React renders during pointer movement.

**Project conventions to preserve**
- Keep imperative style updates for high-frequency pointer movement if they prevent render churn.
- Use existing semantic duration/easing tokens where the animation API supports them.
- Prefer transform-based position updates downstream from `--drag-y`.
- Preserve current queue ordering and nearest-slot semantics.

**Ordered steps**
1. Confirm where `--drag-y` is consumed in CSS before changing pointer math.
2. Ensure the visual drag layer uses `transform` derived from `--drag-y`, not layout properties.
3. Replace raw `duration: 400` with a named duration source:
   - if `animateTo` accepts milliseconds only, map `--duration-panel` to a shared JS constant, for example `MOTION_PANEL_MS = 240`.
   - if it accepts CSS variables or options with easing, use the shared responsive easing equivalent.
4. Reduce snap duration from `400` toward the panel token range unless product feel testing proves a longer snap is necessary.
5. Add a Reduced Motion branch:
   - if `prefers-reduced-motion: reduce`, snap in roughly `80ms` or resolve immediately with a brief opacity/position confirmation.
6. Keep pointer-move updates outside React state unless state is needed for accessibility or ordering.
7. If the component does not already capture the pointer, consider adding pointer capture only after checking existing pointer lifecycle code; do not infer from this snippet alone.

**Hard boundaries**
- Do not change item ordering logic without separate tests.
- Do not add inertia, bounce, or overshoot for an operations queue.
- Do not route every pointer move through React state.
- Do not assume `currentY` correctness from this snippet; verify its source before modifying snap behavior.
- Do not add Reduced Motion behavior that makes the final slot change invisible.

**Mechanical checks**
- Search for `--drag-y` usage.
- Search for `animateTo(` call sites and raw duration options.
- Confirm drag styling uses `transform`, not `top` or margin changes.
- Confirm a Reduced Motion detection path exists in JS or is added in a small shared helper.
- Confirm any JS motion constants stay aligned with CSS token values.

**Runtime / feel checks to perform later**
- Drag slowly and quickly across slots; item should remain under the pointer.
- Release near slot boundaries; snap should feel decisive and not lag behind intent.
- Repeat drag actions; no accumulating delay should be apparent.
- Test keyboard reordering separately if supported.
- Test Reduced Motion mode for short, understandable slot resolution.

**Reduced Motion behavior**
- Use a short snap around `80ms`, or immediate placement plus brief non-spatial confirmation.
- Remove any long travel, easing flourish, overshoot, or inertia.
- Preserve the causal relationship between release and final slot.

**Source-drift stop condition**
- Before implementation, verify `onPointerMove`, `onPointerUp`, `animateTo`, `nearestSlot`, `currentY`, and `--drag-y` are still structured as shown. If the drag model has changed, stop and re-audit the current queue interaction first.

---

## 4. Recommended execution order

1. **Plan 1 first:** establish shared token behavior and remove `transition: all`.
2. **Plan 2 second:** normalize frequent entry/feedback surfaces using the shared contract.
3. **Plan 3 third:** tune direct manipulation once the common duration and Reduced Motion decisions are stable.

## Explicitly unverified states

- Actual computed styles and cascade order.
- Whether command palette has an exit animation or immediate unmount.
- Whether toast placement depends on `top` for layout.
- Whether `--drag-y` is consumed via transform or layout properties.
- Pointer capture, cancellation, keyboard drag alternatives, and screen reader behavior.
- Real perceived timing, frame stability, and interaction latency.
- Reduced Motion behavior outside the button precedent.
- Focus management, focus visibility during animation, and accessibility-tree output.
