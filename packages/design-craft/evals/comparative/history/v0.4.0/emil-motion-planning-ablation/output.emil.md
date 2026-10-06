## 1. Recon summary

- **Stack signals:** React/TSX components, CSS files, Tailwind-style arbitrary animation class (`animate-[...]`), CSS custom-property motion tokens, and at least one JS animation call (`animateTo`).
- **Where motion lives:**  
  - Global tokens/keyframes: `src/styles/motion.css`  
  - Component-local CSS: `src/components/toast.css`, `src/components/Button.css`  
  - Inline utility animation: `src/components/CommandPalette.tsx`  
  - Gesture/reorder logic: `src/components/SortableQueue.tsx`
- **Existing conventions:** semantic duration/easing tokens exist:
  - `--duration-fast: 160ms`
  - `--duration-panel: 240ms`
  - `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)`
  - Local good precedent: button transitions only `transform`, uses tokens, keeps Reduced Motion feedback at `80ms`.
- **Product personality:** calm desktop operations console; motion should be crisp, causal, low-latency, and non-decorative.
- **Frequency map from evidence only:**  
  - High: command palette, queue sorting/dragging, buttons, likely popovers.  
  - Medium: toast notifications.  
  - Unknown: exact popover frequency and queue size.
- **Evidence level:** static snippets only. No runtime, computed style, trace, screen recording, accessibility-tree, device, browser, or user testing was performed.

---

## 2. Vetted priority table

| # | Priority | Category | Location | Finding | Fix summary |
|---|---:|---|---|---|---|
| 1 | High | Throughput / easing | `src/components/CommandPalette.tsx` | `animate-[palette_420ms_ease-in_both]` is long and accelerating for a keyboard-heavy surface. Static evidence supports mismatch with existing `160ms/240ms` responsive tokens. | Replace arbitrary `420ms ease-in` with tokenized opacity/transform motion, fast enough for keyboard invocation, with Reduced Motion path. |
| 2 | High | Cohesion / performance risk | `src/styles/motion.css` | `.popover { transition: all 360ms ease-in; }` uses `transition: all`, non-token duration, and `ease-in`. This can animate unintended properties and diverges from existing tokens. | Limit transition to `opacity, transform`; use existing tokens/easing; add Reduced Motion duration. |
| 3 | High | Gesture responsiveness | `src/components/SortableQueue.tsx` | Pointer movement writes on every `pointermove`, and release animation is hard-coded to `400ms` with no visible easing or Reduced Motion handling in the snippet. | Gate pointer writes with `requestAnimationFrame`, make snap animation tokenized/interruptible, and shorten Reduced Motion snap. |
| 4 | Medium | Layout-affecting animation | `src/components/toast.css` | Toast animates `top` for `500ms ease-in`. Static evidence shows non-token timing/easing and a layout-position property instead of transform. | Animate `transform` + `opacity` using `--duration-panel` / `--ease-responsive`; preserve final layout position. |
| 5 | Medium | Accessibility consistency | Multiple snippets | Reduced Motion is present in `Button.css` but not visible in popover, command palette, toast, or queue snippets. | Add per-surface Reduced Motion behavior that preserves feedback while reducing travel/duration. |
| 6 | Low | Token hygiene | Multiple snippets | Motion values are split between semantic tokens and one-off literals: `360ms`, `420ms`, `500ms`, `400ms`, `ease-in`. | Prefer existing semantic tokens; introduce new tokens only if a repeated need appears after implementation. |

---

## 3. Implementation plans

### Plan A — Tokenize high-frequency overlay motion

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

- Popovers and command palette should appear causally and finish quickly.
- Use opacity + small transform only.
- No `ease-in`, no `transition: all`, no `420ms` keyboard-blocking feel.
- Closed state should remain visually distinct if the element stays mounted.
- Reduced Motion should keep opacity feedback and minimize/remove travel.

**Project conventions to preserve**

- Reuse `--duration-fast`, `--duration-panel`, and `--ease-responsive`.
- Follow the good local precedent in `Button.css`: tokenized transition, scoped property, Reduced Motion duration around `80ms`.
- Preserve visible focus and command-palette keyboard behavior; this plan is motion-only.

**Ordered steps**

1. In `src/styles/motion.css`, replace `.popover` transition with scoped properties:
   - `opacity var(--duration-fast) var(--ease-responsive)`
   - `transform var(--duration-fast) var(--ease-responsive)`
2. Keep or adjust `transform-origin` only if it matches the popover’s anchor. If the trigger/anchor origin is not available from static CSS, keep `center` rather than inventing placement logic.
3. Add `[data-open="true"]` / `[data-open="false"]` states for popover only if the existing markup already uses `data-open`; otherwise do not broaden scope.
4. Replace the command-palette arbitrary animation with a named class, for example `commandPaletteMotion`, defined in `src/styles/motion.css`.
5. In `CommandPalette.tsx`, change only the class assignment, preserving `data-open={open}` and children.
6. Define command-palette motion around:
   - open: `opacity: 1; transform: translateY(0) scale(1)`
   - closed: `opacity: 0; transform: translateY(-4px) scale(0.985)`
   - transition: `opacity var(--duration-fast) var(--ease-responsive), transform var(--duration-fast) var(--ease-responsive)`
7. Add Reduced Motion media rule:
   - transition duration: `80ms`
   - remove transform travel: `transform: none` for both open and closed states, while preserving opacity feedback.

**Hard boundaries**

- Do not change command search behavior, focus management, keyboard shortcuts, or mounting/unmounting semantics.
- Do not add a new animation library.
- Do not introduce new global tokens unless a second implemented surface requires the same new value.
- Do not claim the origin is wrong without inspecting actual popover placement.

**Mechanical checks**

- Search touched files for `420ms`, `360ms`, `ease-in`, and `transition: all`; none should remain for these two surfaces unless unrelated.
- Confirm all new CSS uses existing tokens.
- Run the project’s closest lint/type-check command.
- Confirm `prefers-reduced-motion: reduce` exists for the new/changed selectors.

**Runtime / feel checks to perform after implementation**

- Open/close command palette repeatedly from keyboard; it should feel immediate, not theatrical.
- Check rapid toggling; no queued animation should visibly fight the latest state.
- Open popovers from pointer and keyboard if applicable; motion should clarify origin without delaying selection.
- Use slow-motion/devtools animation inspection if available to confirm opacity/transform only.

**Reduced Motion behavior**

- Keep feedback through opacity.
- Remove positional travel and scale.
- Use `80ms` duration, matching the local button precedent.

**Source-drift stop condition**

- Stop and refresh the plan if `CommandPalette.tsx` no longer contains `data-open={open}` or the arbitrary `animate-[palette_420ms_ease-in_both]`, or if `.popover` no longer contains `transition: all 360ms ease-in`.

---

### Plan B — Convert toast entrance to transform-based token motion

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

- Toasts should enter clearly but not linger.
- Avoid animating `top`; use `transform` and `opacity`.
- Use existing semantic timing/easing.
- Reduced Motion should preserve appearance feedback without spatial travel.

**Project conventions to preserve**

- Use existing motion tokens from `src/styles/motion.css`.
- Match the crisp, calm console personality.
- Keep the toast’s final layout position equivalent to the current `top: 0` end state.

**Ordered steps**

1. Replace keyframes with transform-based motion:
   - from: `transform: translateY(-8px); opacity: 0;`
   - to: `transform: translateY(0); opacity: 1;`
2. Replace animation timing:
   - `animation: toast-enter var(--duration-panel) var(--ease-responsive) forwards;`
3. Ensure the resting `.toast` layout still positions the toast where `top: 0` previously ended. If positioning rules live elsewhere, do not move them into this file unless necessary.
4. Add a Reduced Motion media rule:
   - keyframe or override should remove `translateY`
   - duration should be `80ms`
   - opacity feedback should remain.
5. Optional only if consistent with existing CSS style: add `will-change: transform, opacity` to `.toast`, but avoid leaving it on long-lived idle elements if toasts persist for a long time.

**Hard boundaries**

- Do not change toast queueing, dismissal, stacking, timers, or ARIA/live-region behavior.
- Do not alter toast copy, severity styling, or placement.
- Do not add a spring/JS animation library for this CSS-only surface.

**Mechanical checks**

- Confirm `top` is no longer animated inside `@keyframes toast-enter`.
- Confirm `500ms` and `ease-in` are removed from `src/components/toast.css`.
- Confirm `prefers-reduced-motion: reduce` exists in this file or an imported global equivalent covers `.toast`.
- Run the closest CSS/lint/build/type-check command available.

**Runtime / feel checks to perform after implementation**

- Trigger a single toast; it should be noticeable but finish quickly.
- Trigger multiple toasts; stacking should not jump or reflow unexpectedly.
- Trigger a toast while using keyboard focus elsewhere; focus visibility should not be obscured or delayed.
- In Reduced Motion mode, verify the toast still appears with clear feedback.

**Reduced Motion behavior**

- Duration: `80ms`.
- No vertical travel.
- Opacity may transition from `0` to `1`.

**Source-drift stop condition**

- Stop and refresh the plan if `toast-enter` no longer animates `top`, if `.toast` no longer owns the entrance animation, or if toast positioning has moved to another file.

---

### Plan C — Make queue drag updates lightweight and snap motion interruptible

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

- Drag movement should track the pointer directly without decorative lag.
- Pointer-move writes should be coalesced to animation frames.
- Release snap should be short, token-aligned, and interruptible by a new drag.
- Reduced Motion should keep state feedback but minimize travel time.

**Project conventions to preserve**

- Prefer existing duration semantics:
  - normal snap: `160ms` / `--duration-fast`
  - larger panel-style moves only if existing queue slots are visually large and testing supports `240ms`
- Use `--ease-responsive` if the animation API accepts CSS easing strings.
- Do not create unrelated queue behavior changes.

**Ordered steps**

1. Inspect the full `SortableQueue.tsx` before editing to find:
   - where `currentY` is updated
   - how `animateTo` is defined/imported
   - whether existing cleanup occurs on unmount
   - how `--drag-y` is consumed in CSS.
2. Add local refs for pointer coalescing:
   - latest pointer Y
   - pending `requestAnimationFrame` id
3. Change `onPointerMove` so it stores the latest `event.clientY` and schedules one `requestAnimationFrame` write if none is pending.
4. Inside the frame callback, write only the latest Y to `--drag-y`, then clear the pending frame id.
5. On `pointerup`, cancel any pending frame before starting snap.
6. Replace hard-coded release duration `400` with token-aligned timing:
   - normal: `160`
   - Reduced Motion: `80`
7. Pass easing if `animateTo` supports it:
   - `ease: "cubic-bezier(0.23, 1, 0.32, 1)"`
8. Ensure a new pointer down cancels or supersedes any in-flight snap animation if the existing animation API provides cancellation.
9. If `animateTo` does not support easing/cancellation, do not invent a wrapper blindly; document the limitation in the implementation notes and only change duration/RM handling.

**Hard boundaries**

- Do not rewrite queue ordering logic.
- Do not change `nearestSlot` semantics.
- Do not change data persistence or selection state.
- Do not add virtualization or list architecture changes in this plan.
- Do not assume `--drag-y` is transform-backed; verify its CSS usage first.

**Mechanical checks**

- Confirm `duration: 400` is removed or replaced for this release snap.
- Confirm `requestAnimationFrame` cleanup exists for pending pointer writes.
- Confirm Reduced Motion is checked via CSS media, `matchMedia`, or an existing project hook if one exists.
- Run type-check/lint for the component.
- Search for other `animateTo(... { duration: 400 })` only to avoid creating inconsistent duplicate queue behavior; do not broaden fixes without review.

**Runtime / feel checks to perform after implementation**

- Drag slowly and quickly; item should remain attached to pointer with no visible delayed easing during drag.
- Release near adjacent slots; snap should complete quickly and preserve causality.
- Start a second drag during a snap; latest user input should win.
- Test with a long queue if available; no obvious dropped interaction should appear.
- In Reduced Motion mode, release should still show completion feedback but with shortened travel/time.

**Reduced Motion behavior**

- Drag tracking remains direct.
- Release snap uses `80ms`.
- Avoid added bounce, overshoot, or large travel embellishment.

**Source-drift stop condition**

- Stop and refresh the plan if `onPointerMove`, `onPointerUp`, `animateTo`, or `--drag-y` usage has changed materially, or if `animateTo` already provides tokenized/cancelable motion elsewhere.

---

## 4. Recommended execution order

1. **Plan A** — highest leverage for keyboard-heavy daily use and fixes global overlay conventions.
2. **Plan C** — important for direct-manipulation responsiveness and hot-path pointer work.
3. **Plan B** — contained polish/performance/accessibility improvement for notifications.

## Explicitly unverified states

- No browser/runtime validation was performed.
- No computed styles were inspected.
- No actual import graph or CSS cascade was verified.
- No accessibility tree or focus behavior was tested.
- No frame timing, performance trace, or device testing was performed.
- Popover anchor/origin correctness is unknown from the snippet alone.
- Queue size, `animateTo` API capabilities, and `--drag-y` CSS consumption are unknown.

Guardrails applied: minimal-scope root-cause planning, frontend accessibility/design-authority alignment, and render-performance caution.
