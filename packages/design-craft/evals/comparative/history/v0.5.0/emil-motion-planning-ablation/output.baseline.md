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
