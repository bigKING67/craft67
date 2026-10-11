## 1. Recon summary

- **Stack signals**: React/TSX components, plain CSS, CSS custom properties, CSS keyframes, an arbitrary utility animation class, and imperative pointer/animation logic. No specific animation library is confirmed from the snippets.
- **Where motion lives**:
  - Global motion tokens: `src/styles/motion.css`
  - Component CSS: `src/components/toast.css`, `src/components/Button.css`
  - Component class animation: `src/components/CommandPalette.tsx`
  - Gesture logic: `src/components/SortableQueue.tsx`
- **Existing conventions**:
  - Tokens already exist: `--duration-fast: 160ms`, `--duration-panel: 240ms`, `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)`.
  - Correct local precedent exists in `Button.css`: transform-only feedback, tokenized timing/easing, and a reduced-motion branch that preserves feedback.
- **Product personality**: calm, crisp desktop operations console. Motion should clarify state and causality, not add delay or decorative softness.
- **Frequency map**:
  - Very high frequency: command palette, keyboard-driven interactions, queue sorting.
  - Medium/high frequency: popovers.
  - Occasional: toasts.
  - Existing button press feedback appears aligned with the product.
- **Evidence level**: static code excerpts only. No runtime, computed style, trace, screen recording, accessibility tree, device, or user validation was performed.

---

## 2. Priority table

| # | Severity | Category | Location | Finding | Fix summary |
|---|---|---:|---|---|---|
| 1 | HIGH | Purpose / throughput | `src/components/CommandPalette.tsx` | Command palette uses `animate-[palette_420ms_ease-in_both]`. For keyboard-heavy operators, a 420ms ease-in entrance risks delaying a primary command surface. | Remove the entrance animation from the command palette; preserve focus and state feedback without temporal delay. |
| 2 | HIGH | Gesture / performance | `src/components/SortableQueue.tsx` | Pointer move writes `--drag-y` to `queueRef`, and release uses fixed `duration: 400`. This suggests parent-level style invalidation and a non-velocity-aware snap. | Move drag updates to the active item’s `transform`; snap with an interruptible spring/velocity path, with reduced-motion shortening and removing bounce. |
| 3 | MEDIUM | Easing / performance / cohesion | `src/styles/motion.css` | `.popover` uses `transition: all 360ms ease-in` and `transform-origin: center`. `all` can animate unintended properties; `ease-in` delays response; centered origin may be wrong for trigger-anchored popovers. | Restrict transition to `transform, opacity`, use existing responsive token, shorten to tokenized duration, and use trigger-origin variables with safe fallback. |
| 4 | MEDIUM | Performance / accessibility | `src/components/toast.css` | Toast animates `top` from `-24px` to `0` over `500ms ease-in`, with no reduced-motion branch shown. | Animate `transform` and `opacity` instead of `top`; reduce duration; add reduced-motion opacity-only feedback. |
| 5 | MEDIUM | Cohesion / reduced motion | Multiple snippets | Existing correct button precedent uses tokens and reduced motion, but palette, popover, and toast use hand-authored long/ease-in motion. | Consolidate these surfaces around existing tokens and the reduced-motion pattern already present locally. |

---

## 3. Implementation plans

### Plan 1 — Remove command-palette entrance delay

**Current excerpt**

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

- Opening the command palette should be effectively immediate.
- No 420ms entrance, no `ease-in`, no delayed keyboard surface.
- Focus visibility and command result continuity must remain intact.
- Reduced Motion behavior should be identical to default: no entrance movement.

**Project conventions**

- Follow the local precedent from `src/components/Button.css`: motion must be purposeful, tokenized when present, and have a reduced-motion path.
- For this component, the correct motion budget is zero entrance animation because it is a high-frequency keyboard surface.

**Ordered steps**

1. In `src/components/CommandPalette.tsx`, remove only the arbitrary animation class:
   ```tsx
   export function CommandPalette({ open }: { open: boolean }) {
     return (
       <div data-open={open}>
         <SearchResults />
       </div>
     );
   }
   ```
2. If the real file has additional non-motion classes, preserve them and remove only:
   ```tsx
   animate-[palette_420ms_ease-in_both]
   ```
3. Search for a `palette` keyframe or animation definition.
   - If it becomes unused after this removal, delete that unused animation definition.
   - If it is used elsewhere, leave it untouched and report the remaining usage.

**Hard boundaries**

- Do not change `SearchResults`.
- Do not change focus management, keyboard bindings, result filtering, or open-state logic.
- Do not replace this with a shorter fade unless a product owner explicitly requests motion here.
- Do not add a dependency.

**Mechanical checks**

- Search result check: no remaining `animate-[palette_420ms_ease-in_both]`.
- Search result check: any remaining `palette` animation usage is intentional and reported.
- Run the project’s existing lint/typecheck/build commands if available; no new scripts should be added.

**Runtime / feel checks for executor**

_Not performed in this audit._

- Open the command palette by keyboard shortcut.
- Confirm the surface appears without a visible entrance delay.
- Confirm focus remains visible immediately.
- Rapidly open/close several times; confirm there is no queued or restarting animation.
- Enable Reduced Motion; behavior should remain immediate and feedback should not disappear.

**Source-drift stop condition**

- If `src/components/CommandPalette.tsx` no longer contains the exact animation class, stop and report the current implementation instead of guessing.

---

### Plan 2 — Normalize popover and toast motion around transform/opacity tokens

**Current excerpts**

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

- Popovers: crisp, tokenized transform/opacity transition; no `transition: all`; no `ease-in`; origin can follow trigger-provided variables where available.
- Toasts: enter using `transform` and `opacity`, not `top`; shorter and responsive; reduced motion keeps opacity feedback and removes movement.

**Project conventions**

- Reuse existing tokens:
  ```css
  --duration-fast: 160ms;
  --duration-panel: 240ms;
  --ease-responsive: cubic-bezier(0.23, 1, 0.32, 1);
  ```
- Match the reduced-motion precedent:
  ```css
  @media (prefers-reduced-motion: reduce) {
    .button { transition-duration: 80ms; }
  }
  ```

**Ordered steps**

1. In `src/styles/motion.css`, replace the `.popover` rule with:
   ```css
   .popover {
     transform-origin: var(
       --radix-popover-content-transform-origin,
       var(--transform-origin, center)
     );
     transition:
       transform var(--duration-panel) var(--ease-responsive),
       opacity var(--duration-panel) var(--ease-responsive);
   }

   @media (prefers-reduced-motion: reduce) {
     .popover {
       transition:
         opacity 80ms var(--ease-responsive);
     }
   }
   ```
2. In `src/components/toast.css`, replace the toast keyframes with transform/opacity:
   ```css
   @keyframes toast-enter {
     from {
       transform: translate3d(0, -8px, 0);
       opacity: 0;
     }
     to {
       transform: translate3d(0, 0, 0);
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
       animation: toast-enter-reduced 120ms var(--ease-responsive) forwards;
     }
   }
   ```
3. Search for any other `.toast` rules that set `top` during entry.
   - If another rule depends on animated `top`, stop and report the conflict.
   - If `top` is only used for static placement, leave static positioning intact.

**Hard boundaries**

- Do not change toast layout, stacking, placement, content, dismiss behavior, or timers.
- Do not change popover markup or open/close state logic.
- Do not introduce `transition: all`.
- Do not invent new motion tokens unless the existing tokens are absent in the real file.
- If `.popover` is used for centered modal content rather than trigger-anchored content, stop and report before applying the transform-origin change.

**Mechanical checks**

- Search result check: no `.popover { transition: all ... }`.
- Search result check: no `toast-enter` animation of `top`.
- Search result check: no `500ms ease-in` remaining for `.toast`.
- Run existing lint/typecheck/build commands if available.

**Runtime / feel checks for executor**

_Not performed in this audit._

- Open a popover and inspect slow playback: opacity/scale or transform should respond immediately, not ease in slowly.
- Confirm the popover origin appears connected to its trigger where the component system provides an origin variable.
- Trigger a toast: it should slide a short distance from above and settle quickly.
- Enable Reduced Motion: toast should fade without vertical movement; popover should preserve opacity feedback with no movement transition.

**Source-drift stop condition**

- If either current excerpt is no longer present, stop and report the new implementation.
- If existing state selectors require a different open/closed selector structure, stop and ask for the surrounding CSS before adapting.

---

### Plan 3 — Make sortable queue drag motion direct and interruptible

**Current excerpt**

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

- During drag, only the active dragged item updates its `transform`.
- Do not drive child movement by writing a parent-level CSS variable on every pointer move.
- Release motion should account for interruption and velocity rather than always tweening for `400ms`.
- Reduced Motion should keep snap feedback but shorten it and remove bounce.

**Project conventions**

- Prefer transform-only motion, matching the existing button precedent.
- Use existing semantic durations where applicable:
  - direct press/feedback: `--duration-fast`
  - panel/settling motion: around `240ms`
- For gesture settling, use an interruptible spring only if the existing `animateTo` helper supports spring-like options.

**Ordered steps**

1. Inspect the real `SortableQueue.tsx` for the active row/item element.
   - If there is already a ref for the dragged item, use it.
   - If only `queueRef` exists and there is no single active item target, stop and report; do not rewrite the queue architecture.
2. Replace parent CSS variable movement:
   ```tsx
   queueRef.current?.style.setProperty("--drag-y", `${event.clientY}px`);
   ```
   with direct active-item transform movement, using the project’s actual dragged-item ref name:
   ```tsx
   draggedItemRef.current?.style.setProperty(
     "transform",
     `translate3d(0, ${event.clientY}px, 0)`
   );
   ```
   If the real code tracks a delta rather than absolute `clientY`, use the existing delta variable instead of introducing absolute positioning behavior.
3. Track pointer velocity using existing pointer events:
   ```tsx
   const elapsedMs = Math.max(event.timeStamp - lastPointerTimeRef.current, 1);
   const velocityY = (event.clientY - lastPointerYRef.current) / elapsedMs;

   lastPointerYRef.current = event.clientY;
   lastPointerTimeRef.current = event.timeStamp;
   ```
4. Change `onPointerUp` to accept the pointer event if the surrounding event wiring supports it:
   ```tsx
   function onPointerUp(event: PointerEvent) {
     setDragging(false);

     const prefersReducedMotion =
       window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;

     animateTo(
       nearestSlot(currentY),
       prefersReducedMotion
         ? { duration: 80, bounce: 0 }
         : { type: "spring", duration: 0.5, bounce: 0.2, velocity: velocityY }
     );
   }
   ```
5. If `animateTo` does not support `type`, `bounce`, or `velocity`, do not invent a physics engine. Use the closest existing interruptible/spring API if present; otherwise stop and report the helper limitation.

**Hard boundaries**

- Do not change queue ordering rules, hit testing, slot calculation, persistence, or item data shape.
- Do not add a new animation dependency.
- Do not animate `top`, `left`, margins, padding, width, or height for dragging.
- Do not apply transforms to the entire queue container.
- Do not continue if the active dragged element cannot be targeted directly.

**Mechanical checks**

- Search result check: no pointer-move path writes `--drag-y` to `queueRef`.
- Search result check: release path no longer uses only `{ duration: 400 }`.
- Typecheck should pass after changing `onPointerUp` signature and velocity refs.
- Existing drag/reorder tests, if any, should continue to pass.

**Runtime / feel checks for executor**

_Not performed in this audit._

- Drag a queue item slowly: it should track the pointer without moving unrelated rows through a parent variable.
- Release near a slot: it should settle into place without a fixed-duration mechanical glide.
- Re-grab during settle: motion should retarget rather than restart from zero.
- Enable Reduced Motion: drag tracking remains direct; release snap is short and non-bouncy.

**Source-drift stop condition**

- If the current excerpt is not present, or if `animateTo` is not local/inspectable enough to confirm supported options, stop and report the current implementation before editing.

---

## 4. Recommended execution order

1. **Plan 1 — Command palette**: highest throughput impact, smallest scope.
2. **Plan 2 — Popover/toast normalization**: fixes repeated CSS anti-patterns and aligns with existing tokens.
3. **Plan 3 — Sortable queue**: highest interaction complexity; execute after simpler motion conventions are clean.

## Explicitly unverified states

- Actual computed styles and whether any other CSS overrides these snippets.
- Whether `.popover` is always trigger-anchored or sometimes used for centered modal-like content.
- Exact `palette` keyframe definition and whether it is reused elsewhere.
- Toast stacking behavior, dismissal timing, and whether JS controls mount/unmount.
- `animateTo` API capabilities and whether it supports spring, velocity, or interruption.
- Accessibility tree, focus order, keyboard behavior, frame timing, and Reduced Motion behavior in a real browser/device.
