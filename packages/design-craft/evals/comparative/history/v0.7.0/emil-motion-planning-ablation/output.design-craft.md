## 1. Recon summary

Reading this as: a calm desktop operations console for keyboard-heavy operators, optimized for throughput, continuity, and low-friction state feedback.

- **Stack signals:** React/TSX components, CSS modules/global CSS, CSS custom properties, Tailwind-style arbitrary animation class, imperative pointer handling, and an `animateTo(...)` helper.
- **Where motion lives:** shared motion tokens in `src/styles/motion.css`; component-local CSS in `toast.css` and `Button.css`; inline utility animation in `CommandPalette.tsx`; imperative drag/settle logic in `SortableQueue.tsx`.
- **Existing conventions:** semantic duration/easing tokens exist; `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)` is a strong responsive ease-out-like curve; `Button.css` is the best local precedent: transform-only, tokenized duration/easing, subtle scale, and a Reduced Motion branch that preserves feedback.
- **Product personality:** crisp, quiet, utilitarian, non-cinematic. Motion should explain causality, not decorate.
- **Frequency map:**
  - Very high: command palette, buttons, keyboard-triggered overlays.
  - High / direct manipulation: sortable queue drag and settle.
  - Medium: popovers.
  - Occasional but visible: toasts.
- **Evidence level:** static snippets only. No runtime feel, computed style, browser performance, accessibility tree, keyboard flow, screen recording, device, or user testing was performed.

## 2. Vetted priority table

| ID | Priority | Evidence | Finding | Smallest safe correction |
|---|---:|---|---|---|
| F1 | P1 | `CommandPalette.tsx`: `animate-[palette_420ms_ease-in_both]` | High-frequency keyboard surface uses a long arbitrary animation and `ease-in`, which delays the start of visible response by design. No Reduced Motion branch is shown. | Replace with tokenized open/closed state styles using opacity/very small transform, about `120–180ms`, responsive easing, and a reduced-motion path with no travel. |
| F2 | P1 | `motion.css`: `.popover { transform-origin: center; transition: all 360ms ease-in; }` | Popover motion has broad property ownership, slow timing, `ease-in`, center origin, and no shown Reduced Motion branch. For trigger-anchored overlays this weakens causality. | Limit to `opacity, transform`; use trigger/placement origin when available; use existing responsive token; add reduced-motion no-travel feedback. |
| F3 | P1 | `toast.css`: keyframes animate `top` from `-24px` to `0`, `500ms ease-in` | Toast entrance animates a layout property and is long/late-starting. Keyframes may restart from the declared start on repeated transient state changes. No Reduced Motion path is shown. | Move to `transform: translateY(...)` + opacity, shorten to tokenized timing, use ease-out-like response, and remove travel under Reduced Motion. |
| F4 | P1/P2 | `SortableQueue.tsx`: pointer move sets `--drag-y` on `queueRef`; release uses `animateTo(nearestSlot(currentY), { duration: 400 })` | Direct manipulation path has static risks: parent-level CSS variable updates may affect a broad subtree; release settle is fixed-duration and does not show presentation-value interruption, measured velocity, pointer capture, or grab-offset handling. Static evidence cannot prove gesture feel. | Keep current target semantics unless explicitly changed; move hot-path writes to the dragged item or a narrow owner; coalesce frame writes; settle from current presentation value with measured velocity if supported. |
| F5 | P2 | Tokens exist, but components use `360ms`, `420ms`, `500ms`, `ease-in`, and arbitrary animation strings | Motion vocabulary is fragmented despite existing semantic tokens and a correct button precedent. | Centralize overlay/transient/direct-manipulation timing guidance around existing tokens before adding new values. |

## 3. Implementation-ready plans

### Plan A — Retune high-frequency overlays: command palette + popover

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
<div
  data-open={open}
  className="animate-[palette_420ms_ease-in_both]"
>
  <SearchResults />
</div>
```

**Target behavior**

- Command palette opens with immediate causal feedback suitable for keyboard use.
- Popovers preserve trigger relationship where the positioning primitive exposes an origin.
- No broad `transition: all`.
- No `ease-in` for interactive entrance.
- Reduced Motion preserves state feedback without spatial travel.

**Project conventions**

- Use `--duration-fast`, `--duration-panel`, and `--ease-responsive`.
- Follow the local button precedent: transform-only where motion is needed, short timing, Reduced Motion branch.
- Keep visible focus unaffected.

**Ordered steps**

1. In `src/styles/motion.css`, add or reuse semantic overlay styles rather than arbitrary animation strings.
2. Replace `.popover` with explicit properties, for example:
   - `transition: opacity var(--duration-fast) var(--ease-responsive), transform var(--duration-fast) var(--ease-responsive);`
   - `transform-origin: var(--popover-transform-origin, center);`
3. If the actual popover primitive exposes a placement-origin variable, map it into `--popover-transform-origin`; otherwise keep the fallback and document that origin is unresolved.
4. Replace `CommandPalette.tsx` arbitrary animation with stable state styling keyed by `data-open`.
5. Use a minimal open transform only if needed, e.g. opacity plus `translateY(-2px)` or `scale(0.98–0.99)`, not large travel.
6. Add `@media (prefers-reduced-motion: reduce)` so command palette/popover either use opacity-only `80ms` feedback or immediate state change with focus still visible.

**Hard boundaries**

- Do not change command search behavior, result ordering, focus trapping, keyboard shortcuts, or dismissal semantics.
- Do not introduce a new animation library.
- Do not add decorative bounce, stagger, blur, or long panel motion.
- Do not remove focus-visible styling.

**Mechanical checks**

- Run the project’s existing type-check for `CommandPalette.tsx`.
- Run the existing lint/style check for TSX/CSS if present.
- Run the smallest existing build or component test gate that covers shared styles.

**Runtime / feel checks to perform later**

- Toggle command palette rapidly by keyboard and ensure no delayed response or visual restart feels blocking.
- Open/close popovers from multiple placements if placement collision is supported.
- Confirm focus remains visible during and after open/close.
- Check normal and Reduced Motion modes.

**Reduced Motion behavior**

- Remove transform travel.
- Preserve feedback via instant visibility or short opacity/color transition.
- Do not hide content until a long animation completes.

**Source-drift stop condition**

- Stop before editing if `CommandPalette.tsx` no longer uses `data-open` or the cited arbitrary animation.
- Stop if `.popover` has been replaced by a component-scoped primitive with a different state/origin contract.
- Stop if the motion tokens in `src/styles/motion.css` were renamed or superseded by a newer authority.

---

### Plan B — Repair toast entrance as transient, non-layout motion

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

- Toast appears promptly without animating `top`.
- Motion is short, readable, and calm.
- Repeated toast creation does not depend on a long keyframe restart for basic feedback.
- Reduced Motion removes vertical travel while preserving noticeability.

**Project conventions**

- Prefer transform and opacity.
- Prefer existing timing/easing tokens.
- Keep transient UI functional: dismissal, pause/resume timers, Escape behavior, and announcements must not regress if they exist.

**Ordered steps**

1. Replace `top` keyframe movement with `transform: translateY(...)` and opacity.
2. Prefer state-based transition if the toast system has open/closed state attributes; otherwise use a shorter keyframe only for mount entrance.
3. Initial target:
   - duration: `var(--duration-fast)` or a nearby tokenized `160–200ms`;
   - easing: `var(--ease-responsive)`;
   - travel: small, e.g. `translateY(-25%)` or `translateY(-8px)`, depending on actual layout.
4. Add a Reduced Motion branch:
   - `transform: none`;
   - short opacity transition or immediate visible state.
5. If exit animation exists elsewhere, align enter/exit vocabulary so enter does not use layout while exit uses transform, or vice versa.
6. If toast timers exist, verify they are not coupled to the old `500ms` animation duration.

**Hard boundaries**

- Do not change toast copy, severity styling, stacking rules, timer duration, or announcement semantics unless the current code explicitly couples them to animation.
- Do not animate `top`, `left`, margin, padding, width, or height for the entrance.
- Do not introduce swipe dismissal unless already present.

**Mechanical checks**

- Run existing CSS lint/style check if present.
- Run existing component/unit tests for toast lifecycle if present.
- Run the smallest existing build gate because this touches component styling.

**Runtime / feel checks to perform later**

- Trigger one toast, several stacked toasts, and rapid repeated toasts.
- Confirm no visual gap breaks pointer access to dismiss controls.
- Hide and restore the document if toast timers exist.
- Verify normal and Reduced Motion modes.

**Reduced Motion behavior**

- No vertical travel.
- Opacity or static state change remains so the user receives feedback.
- Focus/announcement behavior, if present, must remain independent of animation.

**Source-drift stop condition**

- Stop if `toast.css` no longer contains `toast-enter` or `.toast` no longer owns entrance motion.
- Stop if a toast library now owns lifecycle state and exposes official animation hooks.
- Stop if timer or announcement code is found to depend on the old `500ms` duration.

---

### Plan C — Make sortable queue drag settle interruptible and narrowly owned

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

- Drag tracking remains attached to the pointer after intent is clear.
- Hot-path style writes are scoped to the dragged item or a narrow transform owner, not the entire queue unless proven safe.
- Release settles from the current on-screen position.
- Existing target-selection semantics, `nearestSlot(currentY)`, are preserved unless product owners explicitly authorize momentum-based slot selection.
- Reduced Motion removes large elastic travel but keeps clear reorder feedback.

**Project conventions**

- Keep calm, non-bouncy motion for operations work.
- Use transform ownership rather than layout movement where possible.
- Preserve throughput: drag should not lock input until animation completes.

**Ordered steps**

1. Inspect the full `SortableQueue.tsx` drag model before editing:
   - pointer down ownership;
   - grab offset;
   - pointer capture;
   - current coordinate space;
   - how `currentY` is updated;
   - what `animateTo` can read: current presentation value, cancel, velocity, spring, duration.
2. Move per-frame writes from `queueRef` to the dragged row or a dedicated transform layer if the CSS variable currently affects descendants broadly.
3. Coalesce pointer updates through the display frame if the current code writes synchronously on every pointer event.
4. Preserve `nearestSlot(currentY)` as the target rule for the first implementation.
5. Track recent pointer samples with monotonic timestamps and compute release velocity in CSS px/s.
6. If `animateTo` supports velocity/spring:
   - start from current presentation value;
   - pass bounded release velocity;
   - use critically damped or near-critically damped settle, no decorative bounce.
7. If `animateTo` only supports duration:
   - shorten only after runtime check;
   - ensure interruption cancels/restarts from current rendered position rather than logical origin.
8. Add or preserve Reduced Motion behavior:
   - no elastic overshoot;
   - short snap or immediate settle;
   - static slot/placeholder feedback remains.

**Hard boundaries**

- Do not change reorder semantics, slot calculation, data mutation timing, keyboard reordering, or persistence behavior.
- Do not switch from nearest-slot targeting to projected momentum targeting without explicit approval.
- Do not add a new gesture/physics dependency unless existing primitives cannot support interruption and velocity.
- Do not let press scale and drag translation compete for the same `transform` owner.

**Mechanical checks**

- Run existing type-check for `SortableQueue.tsx`.
- Run existing tests for reorder behavior if present.
- Add or update unit coverage for target selection only if the project already tests this interaction layer.
- Run the smallest existing build gate.

**Runtime / feel checks to perform later**

- Drag slowly, drag quickly, reverse direction mid-drag, release near slot boundaries.
- Start a second drag while a settle animation is in progress.
- Confirm pointer capture by moving outside the row bounds during drag.
- Verify keyboard reorder behavior still works if supported.
- Check normal and Reduced Motion modes.
- Performance claims require a browser trace or equivalent runtime evidence; none exists yet.

**Reduced Motion behavior**

- Keep direct manipulation during the drag.
- Remove bounce/elasticity and minimize settle travel after release.
- Preserve a clear final slot/placeholder state.

**Source-drift stop condition**

- Stop if `onPointerMove`, `onPointerUp`, `queueRef`, `--drag-y`, `nearestSlot`, or `animateTo` signatures have materially changed.
- Stop if `animateTo` is owned by a shared animation utility with constraints not visible in the snippet.
- Stop if current source already includes pointer capture, velocity handoff, or Reduced Motion handling outside the excerpt.

## 4. Recommended execution order

1. **Plan A first:** highest frequency and easiest to align with existing tokens.
2. **Plan B second:** removes layout-property transient motion and normalizes timing.
3. **Plan C third:** highest interaction complexity; should wait until full source inspection and runtime checks are available.

## Explicitly unverified states

- Actual rendered timing, smoothness, frame pacing, and compositing.
- Computed `transform-origin` for popovers.
- Whether the command palette currently blocks focus or input during animation.
- Toast stacking, timers, announcements, exit animation, and interruption behavior.
- Sortable queue pointer capture, grab offset, keyboard reordering, current-value interruption, velocity support, and large-list performance.
- Reduced Motion behavior beyond the shown button precedent.
- Browser, device, accessibility-tree, screen-reader, and user-test outcomes.
