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

- **Stack signals**: React/TSX components, plain CSS, CSS custom-property motion tokens, and at least one utility-style arbitrary animation class: `animate-[palette_420ms_ease-in_both]`.
- **Where motion lives**:
  - Global tokens: `src/styles/motion.css`
  - Component CSS: `src/components/toast.css`, `src/components/Button.css`
  - Inline utility animation class: `src/components/CommandPalette.tsx`
  - Gesture/imperative animation path: `src/components/SortableQueue.tsx`
- **Existing conventions**:
  - Semantic tokens already exist: `--duration-fast`, `--duration-panel`, `--ease-responsive`
  - Correct local precedent exists in `Button.css`: transform-only transition, tokenized duration/easing, reduced-motion duration shortened to `80ms`
- **Product personality**: calm, crisp, workday operations UI. Motion should be low-latency, causal, and non-decorative.
- **Frequency map from evidence/context**:
  - Very high frequency: command palette, keyboard-driven actions, queue sorting/drag correction
  - Medium frequency: popovers, filters, table-adjacent controls
  - Occasional: toasts/status feedback
- **Evidence level**: static snippet audit only. No computed styles, runtime behavior, frame traces, accessibility tree, browser/device validation, or user testing were performed.

---

## 2. Vetted priority table

| # | Severity | Category | Location | Finding | Fix summary |
|---|---:|---|---|---|---|
| 1 | HIGH | Purpose / frequency / easing | `src/components/CommandPalette.tsx` | Command palette uses `420ms ease-in` animation. For a keyboard-heavy console, palette open/close is high-frequency and should not delay task flow. | Remove decorative entrance motion or reduce to near-instant non-spatial feedback only. |
| 2 | HIGH | Performance / easing / cohesion | `src/styles/motion.css` | `.popover` uses `transition: all 360ms ease-in;`. This is long for a popover, starts slowly, ignores tokens, and can animate unintended properties. | Limit to `transform`/`opacity`, use existing tokens, shorten duration, add reduced-motion path. |
| 3 | MEDIUM | Physicality | `src/styles/motion.css` | `.popover` has `transform-origin: center;`. For trigger-anchored popovers, center origin weakens spatial causality. Modal-style centered origin is not proven here. | Use a trigger-derived transform origin via existing/custom property fallback. |
| 4 | HIGH | Performance / accessibility | `src/components/toast.css` | Toast animates `top` over `500ms ease-in`; no reduced-motion branch is shown. This can cause layout work and delayed feedback. | Animate `transform` + `opacity`, use tokenized duration/easing, keep reduced-motion opacity feedback without vertical travel. |
| 5 | HIGH | Interruptibility / gesture feel | `src/components/SortableQueue.tsx` | Drag path writes `--drag-y` on pointer move, then settles with fixed `duration: 400`. Static evidence does not show velocity carry, spring behavior, or reduced-motion branching. | Drive transform directly on the dragged element; settle with an interruptible spring/velocity-aware path where available; reduce motion deterministically. |
| 6 | MEDIUM | Accessibility / cohesion | Multiple excerpts | Correct reduced-motion precedent exists only in `Button.css`; popover, palette, toast, and queue snippets do not show equivalent handling. | Apply the existing “preserve feedback, reduce movement/shorten duration” convention consistently. |

---

## 3. Implementation-ready plans

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

- Opening the command palette must feel immediate for keyboard-heavy use.
- Remove the `420ms ease-in` entrance animation from the palette container.
- Do not introduce replacement decorative movement.
- If visual feedback is needed, prefer instant state change plus focus visibility; do not add a new long transition.

**Project conventions**

- Follow the existing tokenized, restrained precedent from `src/components/Button.css`.
- Existing design authority favors crisp motion, semantic tokens, visible focus, and reduced-motion feedback.
- Because this component is high-frequency, the best motion improvement is deletion, not a nicer curve.

**Ordered steps**

1. In `src/components/CommandPalette.tsx`, remove `className="animate-[palette_420ms_ease-in_both]"` from the palette wrapper.
2. Keep `data-open={open}` intact if styling or tests depend on it.
3. Do not change `SearchResults`, focus behavior, keyboard handlers, or palette mounting logic.
4. Search for the `palette` keyframe/class definition only to remove dead animation code if it is solely used by this component. If it has other consumers, leave it and report the shared usage.

**Hard boundaries**

- Do not add a new animation library.
- Do not redesign the palette.
- Do not change command search behavior, focus management, or result rendering.
- Do not replace the removed animation with fade/scale unless a product owner explicitly requests it.

**Mechanical checks**

- Run the project’s existing type-check gate.
- Run the project’s existing lint gate.
- If there are component tests for command palette open/close, run only those relevant tests plus the normal focused test command.

**Runtime / feel checks for executor**

- Trigger the command palette repeatedly with the keyboard shortcut.
- Confirm the palette appears without perceptible wait.
- Confirm focus remains visible and lands where it did before.
- Toggle reduced-motion settings and confirm behavior is still usable; there should be no movement to reduce.

**Reduced Motion behavior**

- Same as default: no palette entrance movement.
- Preserve non-motion feedback through visible open state and focus.

**Source-drift stop condition**

- Stop if `CommandPalette.tsx` no longer contains the provided wrapper shape or if the animation class has already been removed/replaced. Report the current code instead of improvising.

---

### Plan 2 — Normalize popover and toast CSS to tokenized transform/opacity motion

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

- Popovers:
  - Animate only `transform` and `opacity`.
  - Use existing semantic values:
    - `--duration-fast: 160ms`
    - `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)`
  - Use trigger-derived origin when available, with safe fallback.
- Toasts:
  - Replace `top` animation with `transform: translateY(...)` + `opacity`.
  - Keep feedback crisp: `240ms` max using `--duration-panel` or `160ms` if the toast is lightweight.
  - Avoid `ease-in`.
- Reduced Motion:
  - Remove vertical travel.
  - Preserve opacity feedback with a short `80ms`–`160ms` transition/animation.

**Project conventions**

- Use existing tokens from `src/styles/motion.css`.
- Mirror the correct local pattern from `src/components/Button.css`:

```css
.button {
  transition: transform var(--duration-fast) var(--ease-responsive);
}

@media (prefers-reduced-motion: reduce) {
  .button { transition-duration: 80ms; }
}
```

**Ordered steps**

1. In `src/styles/motion.css`, replace popover transition with explicit properties:

```css
.popover {
  transform-origin: var(--popover-transform-origin, center);
  transition:
    transform var(--duration-fast) var(--ease-responsive),
    opacity var(--duration-fast) var(--ease-responsive);
}
```

2. If the popover implementation already exposes a library-specific transform-origin variable, set `--popover-transform-origin` from that variable in the component/style layer. If no such variable exists in the actual code, keep the fallback and do not invent library-specific names.
3. Add reduced-motion handling near the `.popover` rule:

```css
@media (prefers-reduced-motion: reduce) {
  .popover {
    transition-duration: 80ms;
  }
}
```

4. In `src/components/toast.css`, replace the layout-position keyframes:

```css
@keyframes toast-enter {
  from {
    transform: translateY(-8px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.toast {
  animation: toast-enter var(--duration-panel) var(--ease-responsive) forwards;
}
```

5. Add reduced-motion toast behavior:

```css
@media (prefers-reduced-motion: reduce) {
  @keyframes toast-enter {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  .toast {
    animation-duration: 80ms;
  }
}
```

6. Ensure no remaining toast enter animation changes `top`, `left`, `margin`, `padding`, `height`, or `width`.

**Hard boundaries**

- Do not change toast layout, stacking, dismissal timing, or ARIA/live-region behavior.
- Do not change popover markup or positioning logic.
- Do not add new global tokens unless existing token names are insufficient after inspecting the actual file.
- Do not use `transition: all`.

**Mechanical checks**

- Run the project’s existing CSS lint/stylelint gate if present.
- Run the project’s existing frontend lint gate.
- Run the project’s existing type-check/build gate if CSS imports are build-validated.

**Runtime / feel checks for executor**

- Open and close a popover from its trigger.
  - Confirm it does not feel delayed at the start.
  - Confirm no unrelated property animates.
  - In slow-motion inspection, confirm movement/scale appears anchored to the trigger when the implementation provides an origin variable.
- Trigger a toast.
  - Confirm it enters by subtle vertical transform and opacity, not by layout `top`.
  - Confirm it completes quickly and does not linger.
- Toggle reduced-motion.
  - Popover should remain responsive with shortened motion.
  - Toast should preserve opacity feedback but drop vertical travel.

**Reduced Motion behavior**

- Popover: shorten to `80ms`, keep feedback.
- Toast: opacity-only, `80ms`, no translate/top movement.

**Source-drift stop condition**

- Stop if `.popover`, `.toast`, or `toast-enter` no longer match the provided excerpts, or if toast positioning depends on `top` as a required layout state rather than an animation-only value. Report drift before changing behavior.

---

### Plan 3 — Make sortable queue drag motion direct, interruptible, and reduced-motion aware

**Files / current excerpt**

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

- During drag, the manipulated item should follow the pointer through direct `transform` updates, not parent-level CSS-variable broadcasts.
- On release, the item should settle to `nearestSlot(currentY)` with an interruptible, velocity-aware spring if the existing animation utility supports it.
- Fixed `400ms` tweening should not be the default settle path for pointer-driven queue movement.
- Reduced Motion should snap or use a very short deterministic settle while preserving final state feedback.

**Project conventions**

- Prefer `transform` for movement.
- Use semantic duration/easing when a non-gesture fallback is required:
  - `--duration-fast: 160ms`
  - `--duration-panel: 240ms`
  - `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)`
- Follow the existing reduced-motion precedent: shorten/gentle motion rather than removing state feedback entirely.

**Ordered steps**

1. Identify the actual dragged element ref. If `queueRef` points to the entire queue rather than the active row/item, introduce or use an existing `draggedItemRef` for the active item only.
2. Replace parent CSS-variable pointer movement with direct transform on the dragged item:

```tsx
function onPointerMove(event: PointerEvent) {
  draggedItemRef.current?.style.setProperty(
    "transform",
    `translateY(${event.clientY}px)`
  );
}
```

3. If the current coordinate system requires a delta instead of viewport `clientY`, compute the existing local drag offset and use that value in `translateY(...)`. Do not change slot-selection semantics.
4. Track simple release velocity from recent pointer samples:

```tsx
const velocityY = (latestY - previousY) / Math.max(latestTime - previousTime, 1);
```

5. Replace the fixed settle call with the existing animation utility’s spring/velocity option if available:

```tsx
animateTo(nearestSlot(currentY), {
  type: "spring",
  duration: 0.5,
  bounce: 0.2,
  velocity: velocityY
});
```

6. If `animateTo` does not support spring or velocity options, do not add a new dependency. Use the closest existing interruptible primitive in the codebase. If none exists, stop and report that the utility must be extended first.
7. Add a reduced-motion branch using the project’s existing reduced-motion mechanism if present. Target behavior:
   - no spring/bounce
   - immediate snap or `80ms` max transform transition
   - final slot state remains clear

**Hard boundaries**

- Do not change queue ordering rules.
- Do not change `nearestSlot(currentY)` behavior.
- Do not add animation dependencies.
- Do not animate layout properties.
- Do not apply drag transforms to all queue children via a parent custom property.

**Mechanical checks**

- Run the existing type-check gate.
- Run queue/sortable component tests if present.
- Run lint for hooks/refs/event handlers.
- Search for remaining `--drag-y` usage and confirm it is either removed or no longer drives drag movement.

**Runtime / feel checks for executor**

- Drag an item slowly, then quickly.
  - Confirm the active item tracks the pointer directly.
  - Confirm release carries momentum subtly rather than easing from rest.
  - Confirm interrupting a settle with a new drag does not restart from an unrelated position.
- Drag near slot boundaries.
  - Confirm final slot selection is unchanged from before.
- Toggle reduced-motion.
  - Confirm release does not bounce.
  - Confirm final placement feedback remains understandable.

**Reduced Motion behavior**

- During drag: direct manipulation remains.
- On release: snap or complete within `80ms`; no bounce or momentum flourish.

**Source-drift stop condition**

- Stop if `queueRef`, `currentY`, `nearestSlot`, or `animateTo` semantics differ from the excerpt enough that the dragged element and coordinate system cannot be identified confidently. Report the mismatch instead of rewriting queue behavior.

---

## 4. Recommended execution order

1. **Plan 1 — Command palette**: highest throughput impact, smallest safe change.
2. **Plan 2 — Popover/toast CSS**: removes broad anti-patterns: `ease-in`, `transition: all`, layout animation, missing reduced-motion branches.
3. **Plan 3 — Sortable queue**: highest interaction complexity; do after simpler token/convention cleanup so the gesture work has a clearer target style.

## Explicitly unverified states

- Actual package scripts, test commands, and build tooling.
- Whether the popover is trigger-anchored, modal-like, or library-backed.
- Whether a transform-origin variable already exists in the popover implementation.
- Whether `animateTo` supports spring, velocity, cancellation, or reduced-motion branching.
- Actual frame rate, layout cost, interruption behavior, focus behavior, and accessibility-tree output.
- Real user feel on keyboard workflows, pointer dragging, reduced-motion settings, or long work sessions.


## Output B

## 1. Recon summary

- **Stack signals:** React/TSX components, global CSS tokens, component-local CSS, utility-style animation classes, and imperative pointer animation.
- **Where motion lives:**
  - Global tokens: `src/styles/motion.css`
  - Component CSS: `src/components/toast.css`, `src/components/Button.css`
  - TSX utility animation: `src/components/CommandPalette.tsx`
  - Imperative drag/release motion: `src/components/SortableQueue.tsx`
- **Existing conventions:** Semantic custom properties exist:
  - `--duration-fast: 160ms`
  - `--duration-panel: 240ms`
  - `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)`
  - Correct precedent: button uses transform-only motion, semantic tokens, and an `80ms` Reduced Motion path.
- **Product personality:** Calm, crisp, low-friction desktop operations surface. Motion should clarify causality and preserve state continuity, not perform or delay throughput.
- **Frequency map:**
  - Very high: buttons, command palette, popovers.
  - High/interruptive: toasts.
  - Medium but high-salience: sortable drag/reorder.
  - Lowest tolerance for sluggishness: keyboard-driven command/search flows.
- **Evidence level:** Static snippet audit only. No runtime behavior, computed styles, frame timing, accessibility tree, screen recording, or user testing was available.

---

## 2. Priority table

| Priority | Finding | Evidence | Risk | Recommended fix |
|---:|---|---|---|---|
| P0 | Motion is bypassing semantic tokens in multiple places | `420ms`, `500ms`, `400`, `ease-in` hardcoded | Inconsistent feel; harder Reduced Motion compliance | Replace hardcoded durations/easing with existing semantic tokens or JS constants derived from them |
| P0 | Reduced Motion is only shown for button precedent | Button has media query; other snippets do not | Users requesting reduced motion may still get full animated movement | Add component-specific reduced paths that keep state feedback but shorten/simplify motion |
| P1 | `.popover` uses `transition: all 360ms ease-in` | `transition: all` | Accidental animation of layout/color properties; sluggish closing/opening feel | Limit to `transform, opacity`; use `--duration-panel` and `--ease-responsive` |
| P1 | Command palette enter animation is long and hardcoded | `animate-[palette_420ms_ease-in_both]` | Keyboard-heavy flow may feel delayed; lacks local state clarity | Move to named class with tokenized duration/easing and `data-open` states |
| P1 | Toast animates `top` for `500ms` | `from { top: -24px }` | Layout-affecting animation and slow interruptive feedback | Use `transform: translateY(...)` + opacity; shorten to fast/panel duration |
| P2 | Sortable release uses hardcoded imperative duration | `animateTo(..., { duration: 400 })` | Reorder may feel detached from pointer; no visible Reduced Motion branch | Tokenize duration, use responsive easing, shorten release, add reduced path |

---

## 3. Implementation plans

### Plan A — Normalize high-frequency overlay motion

**Files / current excerpts**

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

**Target behavior**

- Popovers and command palette open quickly, feel directly caused by the user action, and avoid lingering.
- Motion uses transform/opacity only.
- Closing should not feel slower than opening.
- Command palette should remain optimized for keyboard-heavy use: visible immediately, animated only enough to preserve spatial continuity.

**Project conventions to follow**

- Use existing semantic tokens: `--duration-fast`, `--duration-panel`, `--ease-responsive`.
- Follow the button precedent: transform-based motion, tokenized transition, explicit Reduced Motion path.
- Avoid `transition: all`.
- Avoid hardcoded utility animation durations when a local class can express state clearly.

**Ordered steps**

1. In `src/styles/motion.css`, replace `.popover` transition with property-limited motion:

   ```css
   .popover {
     transform-origin: center;
     transition:
       transform var(--duration-panel) var(--ease-responsive),
       opacity var(--duration-panel) var(--ease-responsive);
   }
   ```

2. If `.popover` already has open/closed state selectors elsewhere, wire those states to small transform/opacity deltas only.
   - Example target pattern:
     - closed: `opacity: 0; transform: scale(0.98) translateY(-2px);`
     - open: `opacity: 1; transform: scale(1) translateY(0);`

3. Replace the command palette arbitrary animation class with a named class, for example:

   ```tsx
   <div
     data-open={open}
     className="command-palette"
   >
   ```

4. Add command palette CSS in the existing appropriate style location for that component.
   - Use `data-open="true"` / `data-open="false"` states.
   - Use `--duration-panel` and `--ease-responsive`.
   - Keep movement minimal: opacity plus a small `translateY` or scale delta.

5. Add a Reduced Motion branch:

   ```css
   @media (prefers-reduced-motion: reduce) {
     .popover,
     .command-palette {
       transition-duration: 80ms;
     }
   }
   ```

6. If the command palette currently relies on keyframes named `palette`, verify whether those keyframes are used elsewhere before removal.

**Hard boundaries**

- Do not introduce decorative bounce, spring, overshoot, blur, or large travel.
- Do not slow the command palette beyond `--duration-panel`.
- Do not animate layout properties.
- Do not remove focus visibility or keyboard affordances.

**Mechanical checks**

- Search for remaining `transition: all` in touched files.
- Search for remaining `animate-[palette_420ms_ease-in_both]`.
- Run the project’s closest static checks: type check, lint, and CSS/build check if available.

**Runtime / feel checks to perform later**

- Open/close command palette repeatedly by keyboard.
- Verify the first result is usable without waiting for the animation to finish.
- Confirm popover open/close feels crisp and not delayed.
- Confirm focus indicator remains visible during and after motion.

**Reduced Motion behavior**

- Preserve open/close state feedback.
- Use `80ms` transition duration.
- Prefer opacity-only or very small transform deltas.
- No long keyframed entrance.

**Source-drift stop condition**

- Stop and re-evaluate if `src/styles/motion.css` no longer contains the shown `.popover` rule, or if `CommandPalette.tsx` no longer uses the shown `animate-[palette_420ms_ease-in_both]` class.

---

### Plan B — Convert toast motion to composited, faster feedback

**File / current excerpt**

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

- Toasts should appear promptly, clarify that a system event occurred, and avoid distracting operators from the active task.
- Entrance should be short, smooth, and composited.
- Motion should not depend on animating `top`.

**Project conventions to follow**

- Use semantic durations and easing.
- Follow transform/opacity precedent from the button.
- Use Reduced Motion that preserves feedback without full movement.

**Ordered steps**

1. Replace the keyframe with transform-based motion:

   ```css
   @keyframes toast-enter {
     from {
       transform: translateY(-8px);
       opacity: 0;
     }
     to {
       transform: translateY(0);
       opacity: 1;
     }
   }
   ```

2. Replace hardcoded duration/easing:

   ```css
   .toast {
     animation: toast-enter var(--duration-fast) var(--ease-responsive) forwards;
   }
   ```

3. If `--duration-fast` feels too abrupt for stacked toasts during later validation, use `--duration-panel`, but do not exceed the existing panel token.

4. Add Reduced Motion:

   ```css
   @media (prefers-reduced-motion: reduce) {
     @keyframes toast-enter {
       from { opacity: 0; }
       to { opacity: 1; }
     }

     .toast {
       animation-duration: 80ms;
     }
   }
   ```

5. If toast exit motion exists outside the snippet, align it to the same principles: transform/opacity only, fast duration, no layout animation.

**Hard boundaries**

- Do not animate `top`, `left`, `right`, `bottom`, height, margin, or padding for toast entrance.
- Do not extend toast entrance to `500ms`.
- Do not add decorative easing, bounce, or overshoot.
- Do not change toast placement or stacking behavior without separate review.

**Mechanical checks**

- Search `src/components/toast.css` for `top:` inside keyframes.
- Search for `500ms ease-in` in toast styles.
- Run CSS/build validation if available.

**Runtime / feel checks to perform later**

- Trigger one toast and several consecutive toasts.
- Verify the toast is noticeable but not attention-grabbing.
- Confirm no visible layout jump occurs around the toast container.
- Confirm text remains readable throughout the entrance.

**Reduced Motion behavior**

- Toast still fades in so feedback is preserved.
- Movement is removed or minimized.
- Duration is `80ms`.

**Source-drift stop condition**

- Stop and re-evaluate if `toast-enter` already animates transform/opacity, if `.toast` no longer uses `toast-enter`, or if toast stacking/positioning is controlled by another component not shown here.

---

### Plan C — Make sortable queue drag/release feel direct and tokenized

**File / current excerpt**

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

- During drag, the item tracks the pointer directly.
- Release motion should quickly settle to the nearest slot and preserve causality.
- Duration and easing should align with existing motion tokens.
- Reduced Motion should keep reorder feedback but avoid long glide animations.

**Project conventions to follow**

- Prefer transform-driven movement.
- Avoid hardcoded motion values when semantic tokens exist.
- Keep direct manipulation responsive.
- Preserve keyboard and pointer accessibility paths.

**Ordered steps**

1. Introduce local motion constants near the component or shared motion helper if one already exists:

   ```tsx
   const SORT_RELEASE_DURATION_MS = 240;
   const SORT_RELEASE_DURATION_REDUCED_MS = 80;
   ```

   Use `240` to mirror `--duration-panel`.

2. If the animation helper accepts easing, pass the responsive easing equivalent:

   ```tsx
   animateTo(nearestSlot(currentY), {
     duration: SORT_RELEASE_DURATION_MS,
     easing: [0.23, 1, 0.32, 1],
   });
   ```

3. Add a Reduced Motion branch using `window.matchMedia("(prefers-reduced-motion: reduce)")`, guarded for environments where `window` may be unavailable.

   ```tsx
   const prefersReducedMotion =
     typeof window !== "undefined" &&
     window.matchMedia("(prefers-reduced-motion: reduce)").matches;
   ```

4. Use the reduced duration on pointer release:

   ```tsx
   animateTo(nearestSlot(currentY), {
     duration: prefersReducedMotion
       ? SORT_RELEASE_DURATION_REDUCED_MS
       : SORT_RELEASE_DURATION_MS,
   });
   ```

5. Review whether `event.clientY` should be stored as an absolute viewport coordinate or converted to a local delta.
   - If CSS expects a transform delta, compute relative movement from the drag start position instead of writing raw viewport `clientY`.

6. If pointermove updates are causing excessive style writes during later profiling, batch the CSS variable update with `requestAnimationFrame`.
   - Keep only the latest pointer value.
   - Cancel the frame on pointer up/cancel.

7. Ensure `pointercancel` follows the same cleanup path as `pointerup`.

**Hard boundaries**

- Do not add inertia, elastic overshoot, or decorative physics.
- Do not increase release duration beyond `240ms` without user testing.
- Do not change sort semantics, nearest-slot logic, or keyboard reorder behavior in the same change.
- Do not assume the animation helper supports easing/interruption without checking its API.

**Mechanical checks**

- Search for other `animateTo(... duration: 400 ...)` patterns related to drag/reorder.
- Confirm TypeScript accepts the animation options shape before adding easing.
- Verify pointer handlers clean up any scheduled frame or captured pointer state.
- Confirm no server-side execution path directly touches `window`.

**Runtime / feel checks to perform later**

- Drag slowly, drag quickly, release between slots, and cancel drag.
- Confirm the item does not lag behind the pointer.
- Confirm release is fast enough to preserve throughput.
- Confirm reduced-motion mode still communicates the final slot.
- Confirm keyboard reorder, if present, remains understandable.

**Reduced Motion behavior**

- Release duration should be `80ms`.
- Avoid long glide motion.
- Preserve final placement feedback through immediate/short settling and clear selected/focused state.

**Source-drift stop condition**

- Stop and re-evaluate if `animateTo` no longer accepts a duration object, if drag positioning is no longer controlled by `--drag-y`, or if the component already has a central motion utility not shown in the excerpt.

---

## 4. Recommended execution order

1. **Plan A first:** fixes the shared overlay pattern and the highest-frequency keyboard flow.
2. **Plan B second:** removes layout-affecting toast motion and shortens interruptive feedback.
3. **Plan C third:** improves direct manipulation after confirming the animation helper API and current drag coordinate model.

## Explicitly unverified states

- Actual computed CSS and final cascade order.
- Whether command palette keyframes are defined elsewhere.
- Whether `.popover` has existing open/closed state selectors.
- Whether `animateTo` supports easing, interruption, cancellation, or reduced-duration options.
- Actual frame rate, layout cost, input latency, and paint/composite behavior.
- Accessibility tree, focus order, screen reader behavior, and keyboard reorder behavior.
- Real Reduced Motion behavior in the running app.
- Visual feel on production data, long result lists, stacked toasts, or dense queue states.


## Output C

## 1. Recon summary

Reading this as: a calm desktop operations console for keyboard-heavy operators, optimized for fast repeated actions with motion that preserves causality without adding delay.

- **Stack signals:** React/TSX components, CSS files, CSS custom-property motion tokens, utility-class animation syntax, pointer-driven drag logic.
- **Where motion lives:** global motion tokens in `src/styles/motion.css`, component CSS keyframes in `src/components/toast.css`, component-local transition precedent in `src/components/Button.css`, inline utility animation in `src/components/CommandPalette.tsx`, imperative gesture settle in `src/components/SortableQueue.tsx`.
- **Existing conventions:** semantic tokens exist: `--duration-fast`, `--duration-panel`, `--ease-responsive`. A correct local precedent uses transform-only motion, tokenized duration/easing, and a Reduced Motion override to `80ms`.
- **Product personality:** crisp, restrained, utility-first, low-fatigue; no evidence supports cinematic or decorative motion.
- **Frequency map:**  
  - High frequency: command palette, buttons, sortable queue drag/reorder.  
  - Medium frequency: popovers.  
  - Occasional but attention-sensitive: toasts.  
- **Evidence level:** static snippets only. No runtime smoothness, computed styles, accessibility tree, frame trace, browser behavior, device feel, or user testing was performed.

## 2. Vetted priority table

| Priority | Evidence | Location | Finding | Smallest safe correction |
|---|---|---|---|---|
| P1 | `animate-[palette_420ms_ease-in_both]` on a keyboard-heavy surface | `src/components/CommandPalette.tsx` | Command palette motion is long, ease-in, and locally hard-coded instead of tokenized. Static evidence suggests delayed perceived response risk; runtime feel is unverified. | Replace with short tokenized transform/opacity transition or keyframe using `var(--duration-fast)` / `var(--ease-responsive)` and a Reduced Motion branch. |
| P1 | `animateTo(nearestSlot(currentY), { duration: 400 })` after pointer drag | `src/components/SortableQueue.tsx` | Direct manipulation settle lacks visible velocity handoff, interruption rules, pointer capture, grab-offset, and Reduced Motion evidence in the snippet. | Preserve current nearest-slot semantics, but add measured release velocity, current-presentation start, interruptibility, and Reduced Motion non-elastic settle. |
| P2 | `transition: all 360ms ease-in; transform-origin: center;` | `src/styles/motion.css` | Popover has broad property ownership, slower-than-token timing, ease-in response, and center origin that may be wrong for anchored UI. | Limit to `opacity, transform`; use semantic tokens; set trigger-aware origin if component positioning provides it; add Reduced Motion. |
| P2 | `top` keyframe over `500ms ease-in` | `src/components/toast.css` | Toast animates layout position and uses slow ease-in without visible Reduced Motion path. Static evidence supports performance/accessibility risk, not actual jank. | Move with `transform: translateY(...)` plus opacity; shorten to panel/fast token range; Reduced Motion removes vertical travel. |
| P2 | Tokens exist, but several components bypass them | Multiple excerpts | Motion vocabulary is fragmented: `160ms`, `240ms`, `360ms`, `400ms`, `420ms`, `500ms`, `ease-in`, and utility literals coexist. | Consolidate common overlay/toast/command durations around existing tokens before inventing new ones. |

## 3. Implementation plans

### Plan A — Tokenize and shorten high-frequency command palette motion

**Files / current excerpts**

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

`src/styles/motion.css`

```css
:root {
  --duration-fast: 160ms;
  --duration-panel: 240ms;
  --ease-responsive: cubic-bezier(0.23, 1, 0.32, 1);
}
```

`src/components/Button.css` precedent:

```css
.button {
  transition: transform var(--duration-fast) var(--ease-responsive);
}

@media (prefers-reduced-motion: reduce) {
  .button { transition-duration: 80ms; }
}
```

**Target behavior**

- Command palette appears immediately enough for keyboard-heavy use.
- Motion explains state change with minimal travel: opacity plus small transform only.
- Uses existing semantic tokens and the local `80ms` Reduced Motion precedent.
- No decorative delay before search results feel available.

**Project conventions**

- Use `--duration-fast` for frequent/keyboard UI.
- Use `--ease-responsive` instead of `ease-in`.
- Preserve visible state via `data-open`.
- Match the Reduced Motion precedent from `Button.css`.

**Ordered steps**

1. Replace the arbitrary utility animation on the palette wrapper with a stable class, for example `className="command-palette"`, while keeping `data-open={open}`.
2. Add or update the component stylesheet used by the command palette. If no component stylesheet exists, prefer colocated CSS following existing component style conventions.
3. Implement closed/open states using only `opacity` and `transform`, for example:
   - closed: `opacity: 0; transform: translateY(-4px) scale(0.98);`
   - open: `opacity: 1; transform: translateY(0) scale(1);`
   - transition: `opacity var(--duration-fast) var(--ease-responsive), transform var(--duration-fast) var(--ease-responsive);`
4. Add Reduced Motion:
   - remove scale/travel or reduce to no positional movement;
   - keep opacity feedback at `80ms`.
5. If the component must unmount on close elsewhere, verify the exit state still has a lifecycle path before relying on CSS transitions.

**Hard boundaries**

- Do not change `SearchResults` data loading, filtering, focus management, or keyboard shortcut semantics.
- Do not add an animation dependency.
- Do not introduce new timing/easing tokens unless existing tokens cannot satisfy the behavior after runtime review.

**Mechanical checks**

- Run existing project checks only if present: type-check, lint, component tests, and build.
- Confirm no unresolved class/CSS import errors.
- Search for remaining `animate-[palette_420ms_ease-in_both]` references and remove only this palette usage unless another caller is confirmed equivalent.

**Runtime / feel checks to perform later**

- Open/close the palette repeatedly with the keyboard.
- Verify first search result and input focus are not delayed by animation lifecycle.
- Interrupt open with immediate close and close with immediate open; no visual jump should occur.
- Confirm the palette does not animate from an unrelated origin.

**Reduced Motion behavior**

- No scale or vertical travel.
- Preserve state feedback with an opacity transition around `80ms`, or immediate visibility if the product’s Reduced Motion policy prefers no fade for command UI.

**Source-drift stop condition**

Stop before editing if `CommandPalette` no longer uses `data-open`, no longer owns the animated wrapper, the palette animation is centralized elsewhere, or `DESIGN.md`/motion tokens have changed the approved duration/easing vocabulary.

---

### Plan B — Repair overlay and toast motion primitives

**Files / current excerpts**

`src/styles/motion.css`

```css
.popover {
  transform-origin: center;
  transition: all 360ms ease-in;
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

`src/styles/motion.css` tokens:

```css
--duration-fast: 160ms;
--duration-panel: 240ms;
--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1);
```

**Target behavior**

- Popovers and toasts feel crisp and causal, not delayed.
- Animated properties are explicit and primarily `transform`/`opacity`.
- Toast entrance no longer animates `top`.
- Reduced Motion keeps feedback while removing spatial travel.

**Project conventions**

- Prefer semantic tokens over literal `360ms`, `500ms`, and `ease-in`.
- Follow the button precedent: transform-specific transitions and `80ms` Reduced Motion.
- Use existing `--duration-panel` for occasional transient UI unless runtime feel shows `--duration-fast` is better.

**Ordered steps**

1. Change `.popover` from `transition: all 360ms ease-in` to explicit properties:
   ```css
   transition:
     opacity var(--duration-fast) var(--ease-responsive),
     transform var(--duration-fast) var(--ease-responsive);
   ```
   Use `--duration-panel` only if the actual popover is large enough to need a slightly longer entrance.
2. Replace `transform-origin: center` only if the implementation exposes trigger placement. Use a trigger-relative origin such as `top left`, `top right`, or a placement variable. If no placement evidence exists, keep origin unchanged and mark origin tuning for runtime inspection.
3. Rewrite `toast-enter` to use transform:
   ```css
   @keyframes toast-enter {
     from { transform: translateY(-24px); opacity: 0; }
     to { transform: translateY(0); opacity: 1; }
   }
   ```
4. Change `.toast` to use tokenized timing/easing:
   ```css
   animation: toast-enter var(--duration-panel) var(--ease-responsive) forwards;
   ```
5. Add Reduced Motion:
   ```css
   @media (prefers-reduced-motion: reduce) {
     .popover {
       transition-duration: 80ms;
     }

     @keyframes toast-enter {
       from { opacity: 0; }
       to { opacity: 1; }
     }

     .toast {
       animation-duration: 80ms;
     }
   }
   ```

**Hard boundaries**

- Do not alter toast stacking, dismissal timers, ARIA/live-region behavior, or placement logic without separate evidence.
- Do not add `will-change` preemptively.
- Do not claim performance improvement until measured; this plan only removes a known static risk.

**Mechanical checks**

- Run existing style lint / lint / build checks if present.
- Search for `.popover` and `.toast` consumers to ensure no caller depends on animating `top` or unrelated properties through `transition: all`.
- Confirm no other keyframe writes `top` for this toast entrance.

**Runtime / feel checks to perform later**

- Trigger single and repeated toasts.
- Verify stacked toasts do not jump when one enters.
- Open popovers from each supported placement; origin should visually match the trigger.
- Interrupt popover open/close quickly; transition should retarget without restarting from an unrelated state.

**Reduced Motion behavior**

- Popover: no scale/travel if those states exist; opacity or immediate state change remains.
- Toast: fade only around `80ms`; no vertical slide.

**Source-drift stop condition**

Stop before editing if `.popover` is a global class used for centered modals, if toast positioning requires `top` for layout rather than animation, if existing tokens are renamed, or if a component library already owns overlay motion through another API.

---

### Plan C — Make sortable queue settle interruptible without changing slot semantics

**Files / current excerpt**

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

- Drag follows the pointer continuously without visual snap.
- Release settles from the current on-screen value.
- Release velocity is measured and passed into the settle animation when the animation API supports it.
- Existing target selection remains `nearestSlot(currentY)` unless product authority explicitly approves momentum-based target selection.
- Reduced Motion removes elastic or large animated settle while preserving clear reorder feedback.

**Project conventions**

- Keep direct manipulation transform-based where possible.
- Use semantic motion tokens for non-gesture transitions, but use an interruptible animation primitive for drag settle if available.
- Respect calm operations-console personality: no playful bounce by default.

**Ordered steps**

1. Pre-implementation inspection:
   - find where `--drag-y` is consumed;
   - confirm whether it drives `transform`, layout, or child styles;
   - inspect `animateTo` API for support of current value, cancellation, and initial velocity.
2. On pointer down/start:
   - capture the pointer if the component owns pointer events;
   - record pointer id;
   - record grab offset between pointer coordinate and item position;
   - cancel any in-flight settle animation and read the current presentation value.
3. On pointer move:
   - use a component-relative coordinate, not raw `event.clientY`, unless the consumer explicitly expects viewport coordinates;
   - update only the dragged item or the narrowest transform owner, not a broad queue parent, if current CSS allows;
   - keep a short history of `{ y, time }` samples using monotonic time.
4. On pointer up/cancel:
   - compute release velocity in CSS px/s from recent samples;
   - keep target selection as `nearestSlot(currentY)`;
   - start the settle from the current presentation value and pass release velocity into `animateTo` if supported, converting units if the API requires relative velocity.
5. If momentum-based slot choice is later authorized, compute a bounded projected endpoint separately, clamp it to valid queue bounds, then choose nearest slot to that projected endpoint. Do not include this behavior by default.
6. Add cancellation paths for pointer cancel, lost capture, escape/cancel action if the component already supports keyboard drag semantics.

**Hard boundaries**

- Do not change queue ordering rules, slot calculation, selection state, persistence, or keyboard reordering behavior.
- Do not replace the animation library or add a new dependency unless the current `animateTo` cannot cancel/read/set velocity and no native alternative exists.
- Do not introduce overshoot/bounce by default.
- Do not widen style invalidation by moving drag state higher in the DOM.

**Mechanical checks**

- Run existing type-check and tests if present.
- Add or update unit tests around `nearestSlot` only if tests already cover queue placement logic; avoid changing semantics.
- If velocity math is factored out, test units explicitly: CSS px/s in, expected bounded value out.
- Verify pointer event cleanup removes listeners/capture on unmount.

**Runtime / feel checks to perform later**

- Drag slowly, release near slot boundaries, and confirm nearest-slot behavior is preserved.
- Flick and release; settle should inherit motion direction without choosing a different slot unless authorized.
- Interrupt an in-flight settle by grabbing again; no jump to stale logical target.
- Drag outside original bounds; pointer capture should preserve tracking.
- Test under a large queue state if available, because static evidence cannot prove hot-path cost.

**Reduced Motion behavior**

- Drag remains direct while the pointer is down.
- Release uses a short non-elastic settle or immediate snap with clear static feedback.
- No rubber-band, overshoot, parallax, or long travel after release.

**Source-drift stop condition**

Stop before editing if `--drag-y` is not the actual visual drag mechanism, if `animateTo` has no cancellation/current-value/velocity API and no local wrapper exists, if queue coordinates are intentionally viewport-based, or if product rules already define momentum-based targeting.

## 4. Recommended execution order

1. **Plan A first:** highest-frequency keyboard surface; small scope; reinforces token use.
2. **Plan B second:** consolidates shared overlay/toast primitives and removes broad/static risks.
3. **Plan C third:** highest interaction complexity; should wait until the animation API and coordinate ownership are inspected.

## Explicitly unverified states

- Actual palette open/close feel, focus timing, and interrupt behavior.
- Whether `.popover` is anchored, centered, or shared with modal-like surfaces.
- Whether toast `top` animation causes measurable layout or frame issues.
- How `--drag-y` is consumed and whether it affects a broad subtree.
- `animateTo` capabilities, cancellation semantics, and velocity units.
- Browser/device Reduced Motion behavior.
- Computed styles, accessibility tree, frame rate, layout shift, and user-perceived smoothness.
