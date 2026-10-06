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
