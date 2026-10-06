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
