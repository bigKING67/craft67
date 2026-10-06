## 1. Recon summary

- **Stack signals:** React/TSX components plus CSS; motion appears through CSS custom properties, keyframes, arbitrary animation class strings, direct style mutation during drag, and an `animateTo(...)` helper.
- **Where motion lives:**  
  - Global/shared: `src/styles/motion.css`  
  - Component CSS: `src/components/toast.css`, `src/components/Button.css`  
  - Component markup/logic: `src/components/CommandPalette.tsx`, `src/components/SortableQueue.tsx`
- **Existing conventions:** semantic tokens exist for `--duration-fast`, `--duration-panel`, and `--ease-responsive`; `Button.css` is the clearest correct local precedent: transform-only feedback, tokenized timing/easing, and a Reduced Motion override that preserves response.
- **Product personality:** calm, crisp, low-friction desktop operations console. Motion should clarify cause/effect and preserve state continuity, not feel decorative or delay keyboard-heavy work.
- **Frequency map:**  
  - Very high: buttons, command palette, popovers/menus, focus-driven UI.  
  - Medium/high: sortable queue during operational triage.  
  - Medium/episodic: toast notifications, but they are status-critical.  
- **Evidence level:** static excerpts only. No runtime, computed-style, trace, screen recording, accessibility-tree, device, or user validation was performed.

---

## 2. Vetted priority table

| Priority | Finding | Static evidence | Risk | Recommendation |
|---|---|---|---|---|
| P0 | Overlay motion is slow and non-tokenized | `.popover { transition: all 360ms ease-in; }` and command palette `420ms_ease-in` | High-frequency UI may feel delayed; `transition: all` can animate unintended properties | Tokenize overlay motion, restrict to `opacity`/`transform`, use existing responsive easing, add Reduced Motion path |
| P0 | Command palette uses a long one-off animation | `animate-[palette_420ms_ease-in_both]` | Keyboard-heavy workflow can be slowed by entry motion; arbitrary timing diverges from conventions | Replace with named class/state using `--duration-panel` or faster, responsive easing, and explicit open/closed states |
| P1 | Toast animates layout property with long duration | `top: -24px` to `top: 0`, `500ms ease-in` | Layout-affecting animation and long duration are poor fit for calm status feedback | Use transform/opacity, shorten to tokenized duration, preserve immediate status visibility |
| P1 | Drag settle animation is hard-coded and lacks visible Reduced Motion handling | `animateTo(..., { duration: 400 })` | Drag release may feel sluggish; reduced-motion behavior is not shown in excerpt | Use token-aligned settle timing; reduce/snap in Reduced Motion while preserving slot confirmation |
| P2 | Reduced Motion coverage appears inconsistent | Present in `Button.css`; absent from other excerpts | Users requesting reduced motion may still receive full overlay/toast/drag motion | Apply the same local precedent to overlays, toasts, and drag settle |
| P2 | Motion vocabulary is fragmented | `160ms`, `240ms`, `360ms`, `400ms`, `420ms`, `500ms`; mixed easings | Harder to maintain a crisp product feel | Consolidate around existing semantic tokens and only add new tokens if necessary |

---

## 3. Implementation-ready plans

### Plan A — Normalize overlay motion: popover + command palette

**Exact current excerpts**

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

- Popovers and command palette should appear causally connected to the triggering action.
- Motion should be short, crisp, and limited to `opacity` and `transform`.
- Command palette should not feel like a decorative entrance animation; it should feel immediately available for keyboard input.
- Open/closed state should be explicit and inspectable through attributes/classes.
- Focus visibility must remain unaffected.

**Project conventions to follow**

- Use existing tokens: `--duration-fast`, `--duration-panel`, `--ease-responsive`.
- Follow the local Reduced Motion precedent from `Button.css`.
- Prefer transform-based motion over layout-position animation.
- Avoid `transition: all`.
- Avoid hard-coded one-off durations unless there is a documented reason.

**Ordered implementation steps**

1. In `src/styles/motion.css`, replace `.popover` broad transition with explicit properties:
   - `transition-property: opacity, transform;`
   - `transition-duration: var(--duration-fast)` or `var(--duration-panel)` depending on current visual size.
   - `transition-timing-function: var(--ease-responsive);`
2. Keep `transform-origin: center` only if it matches actual anchoring. If popovers are anchored to buttons/menus elsewhere, prefer an origin that reflects the trigger edge; do not guess without inspecting callers.
3. Add stateful selectors for popovers if supported by existing markup, for example `[data-open="true"]` / `[data-open="false"]`, without changing semantics.
4. In `src/components/CommandPalette.tsx`, replace the arbitrary animation class with a stable semantic class, for example:
   - `className="command-palette"`
   - Keep `data-open={open}`.
5. Add command palette motion styles in the existing shared motion location unless a component-local style file already owns it after inspection.
6. Use a panel-scale duration:
   - Entry: `var(--duration-panel)` maximum.
   - Exit: `var(--duration-fast)` if an exit state exists.
7. Use small-distance transform only, for example `translateY(-4px)` or subtle scale, not large travel.
8. Add a Reduced Motion media query:
   - Shorten to about `80ms`.
   - Prefer opacity/state feedback over spatial movement.
   - Preserve visible open/closed feedback.

**Hard boundaries**

- Do not alter command execution, search behavior, result ordering, focus management, or keyboard shortcuts.
- Do not introduce global animation resets.
- Do not remove visible focus indicators.
- Do not add decorative bounce, spring overshoot, blur, or large-scale movement.
- Do not assume unavailable state classes; inspect existing markup before choosing selectors.

**Mechanical checks**

- Search for remaining `transition: all` in overlay-related CSS.
- Search for `ease-in` and hard-coded overlay durations near command palette/popover code.
- Confirm `data-open` remains present and boolean-compatible.
- Run the project’s normal type/build/lint checks if available.
- Confirm no new CSS selector unintentionally targets unrelated components.

**Runtime/feel checks to perform later, not performed here**

- Keyboard-open command palette repeatedly; confirm input feels immediately available.
- Open/close common popovers; confirm cause/effect is clear but not attention-grabbing.
- Check focus ring visibility during and after transition.
- Check long command result lists are not visually delayed by parent animation.

**Reduced Motion behavior**

- Popover/command palette should still appear/disappear with clear opacity or instant state feedback.
- Duration should be materially shorter, around the existing `80ms` local precedent.
- Avoid translate/scale where possible under reduced motion.

**Source-drift stop condition**

Stop and re-audit before implementing if:
- `src/styles/motion.css` no longer owns shared motion tokens.
- `CommandPalette` no longer renders the shown wrapper or `data-open`.
- Existing styles already define `palette` keyframes with important state behavior.
- A newer design authority changes token names, durations, or Reduced Motion requirements.

---

### Plan B — Rework toast entrance to status-first, transform-based motion

**Exact current excerpt**

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

- Toasts should communicate status promptly without pulling attention for half a second.
- Entrance should preserve causality while avoiding layout-affecting animation.
- Toast should be readable quickly and should not compete with operational tasks.

**Project conventions to follow**

- Use existing motion tokens from `src/styles/motion.css`.
- Prefer `transform` and `opacity`.
- Use `--ease-responsive`.
- Add Reduced Motion behavior consistent with `Button.css`.

**Ordered implementation steps**

1. Replace keyframe movement from `top` to `transform`.
2. Keep the visual offset equivalent, but express it as:
   - `transform: translateY(-8px)` or similar short distance, not `top: -24px`.
3. Replace `500ms ease-in` with a tokenized duration:
   - Prefer `var(--duration-panel)` for a full toast entrance.
   - Use `var(--duration-fast)` if the toast is small and non-blocking.
4. Replace `ease-in` with `var(--ease-responsive)`.
5. Ensure the final keyframe leaves the toast at:
   - `transform: translateY(0);`
   - `opacity: 1;`
6. Add `@media (prefers-reduced-motion: reduce)`:
   - Shorten animation duration to around `80ms`.
   - Consider opacity-only entrance.
7. Confirm no positioning logic depends on the animated `top` value. If it does, separate layout position from animation transform.

**Hard boundaries**

- Do not change toast content, severity, timeout, stacking order, or dismissal behavior.
- Do not make status feedback slower.
- Do not remove animation entirely for all users unless design authority changes.
- Do not animate dimensions, margins, `top`, `left`, or other layout properties.

**Mechanical checks**

- Search for `toast-enter` references to avoid orphaned or duplicated keyframes.
- Search toast CSS for `top` animation or hard-coded `500ms`.
- Confirm the toast base position still comes from static layout/positioning, not from animation.
- Run CSS lint/build checks if available.

**Runtime/feel checks to perform later, not performed here**

- Trigger success, warning, and error toasts.
- Confirm the toast is readable immediately.
- Confirm stacked toasts do not jump or reflow during entrance.
- Confirm dismissal timing still feels independent from entrance timing.

**Reduced Motion behavior**

- Toast should still appear with clear status feedback.
- Use very short opacity transition or instant placement with opacity confirmation.
- Avoid vertical travel under reduced motion.

**Source-drift stop condition**

Stop and re-audit before implementing if:
- Toasts are now managed by a different component or animation system.
- The `top` keyframes are used to coordinate stack layout.
- New severity-specific toast motion exists.
- A newer authority defines different notification motion requirements.

---

### Plan C — Make sortable queue drag settle faster, tokenized, and reduced-motion aware

**Exact current excerpt**

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

- Drag should feel directly manipulated while pointer is down.
- Release should resolve quickly to the nearest slot without a sluggish settle.
- State continuity should remain clear: users should understand where the item moved.
- Reduced Motion should preserve placement feedback without long travel.

**Project conventions to follow**

- Prefer tokenized durations over hard-coded `400`.
- Use the existing responsive easing if `animateTo` accepts easing.
- Use direct manipulation during drag; do not add decorative easing while pointer is down.
- Align with the local Reduced Motion precedent: shorter motion, feedback preserved.

**Ordered implementation steps**

1. Inspect the implementation of `animateTo` before changing call shape.
2. If `animateTo` accepts CSS-like timing:
   - Use a duration equivalent to `--duration-panel` at maximum.
   - Prefer `--duration-fast` for short slot-to-slot corrections.
   - Use the responsive easing if supported.
3. If `animateTo` only accepts numbers:
   - Replace `400` with a named constant near the component, such as `QUEUE_SETTLE_DURATION_MS = 240`.
   - Add a reduced-motion constant, such as `80` or `0–80` depending on feedback needs.
4. Add a Reduced Motion detection path:
   - CSS media query if animation is CSS-driven.
   - `matchMedia("(prefers-reduced-motion: reduce)")` or existing app preference helper if JS-driven.
5. Keep pointer-move updates direct. Do not animate every pointer move.
6. Confirm `--drag-y` is consumed by transform-based styles. If it drives layout properties, plan a separate transform-only correction.
7. On pointer up, ensure the item reaches the nearest slot with a clear final state marker, such as selected/placed styling if already present.

**Hard boundaries**

- Do not change queue ordering rules.
- Do not change `nearestSlot(currentY)` logic unless a separate bug is found.
- Do not introduce inertial physics, bounce, or overshoot.
- Do not throttle pointer movement in a way that makes direct manipulation lag unless profiling proves it is needed.
- Do not assume `animateTo` supports easing or cancellation without inspecting it.

**Mechanical checks**

- Locate `animateTo` definition and all call sites before altering its API.
- Search for `--drag-y` usage and verify it maps to transform-style movement.
- Search for hard-coded drag durations.
- Confirm pointer-up still calls `setDragging(false)` at the correct time for existing styles.
- Run type checks after any signature or constant changes.

**Runtime/feel checks to perform later, not performed here**

- Drag one item a short distance and release; confirm settle is quick and understandable.
- Drag across multiple slots; confirm destination continuity.
- Cancel or release near boundaries; confirm no visual snap to an unexpected slot.
- Test repeated rapid drags for stale animation or delayed state.
- Test keyboard alternatives if the sortable queue supports them.

**Reduced Motion behavior**

- While dragging, direct pointer-following can remain because it is user-controlled.
- On release, use a very short settle or immediate placement.
- Preserve final-slot confirmation through position, focus/selection, or another non-motion cue.

**Source-drift stop condition**

Stop and re-audit before implementing if:
- `animateTo` has already been replaced or centralized.
- `--drag-y` no longer controls the dragged visual position.
- Queue sorting now has keyboard-first behavior that shares the same animation path.
- Reduced Motion is already handled by a global motion provider not shown in the excerpt.

---

## 4. Recommended execution order

1. **Plan A first:** highest frequency and most visible to keyboard-heavy operators; also establishes the shared overlay convention.
2. **Plan B second:** small, isolated, high-confidence improvement from layout animation to transform/opacity.
3. **Plan C third:** important for throughput, but requires inspecting `animateTo`, `--drag-y` consumption, and queue behavior before changing timing.

## Explicitly unverified states

- Actual computed durations, easings, transforms, and cascade order.
- Whether `palette` keyframes exist elsewhere.
- Whether `.popover` has open/closed state selectors elsewhere.
- Whether `animateTo` supports easing, cancellation, promises, or reduced-motion hooks.
- Whether `--drag-y` is consumed by transform, layout, or both.
- Actual focus behavior, keyboard flow, screen reader behavior, and accessibility tree.
- Runtime performance, paint/layout cost, device behavior, and user-perceived feel.
