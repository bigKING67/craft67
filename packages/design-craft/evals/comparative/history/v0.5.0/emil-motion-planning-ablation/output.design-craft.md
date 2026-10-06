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
