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
