## 1. Recon summary

**Verdict from static evidence:** motion is directionally aligned with a calm operations console in one local precedent, but the current excerpts show fragmented implementation: tokenized button feedback coexists with long `ease-in` keyframes, broad `transition: all`, layout-position animation, and no visible Reduced Motion paths on the higher-impact surfaces.

- **Stack signals:** React/TSX components plus CSS modules/global CSS and utility-style arbitrary animation classes. No runtime animation library is proven by the snippets except an `animateTo(...)` call of unknown origin.
- **Where motion lives:** global motion tokens in `src/styles/motion.css`; component-local CSS in `toast.css` and `Button.css`; utility animation class in `CommandPalette.tsx`; imperative drag/settle behavior in `SortableQueue.tsx`.
- **Existing conventions:** semantic tokens exist: `--duration-fast`, `--duration-panel`, `--ease-responsive`. The button precedent correctly uses tokenized `transform`, active feedback, and a Reduced Motion duration override.
- **Product personality:** crisp, calm, low-latency operations UI. Motion should explain state continuity, not decorate or delay repeated keyboard work.
- **Frequency map:** command palette = high-frequency/keyboard-heavy; sortable drag = high-attention direct manipulation; popovers = repeated contextual UI; toasts = occasional but system-feedback critical; buttons = repeated micro-feedback.
- **Evidence level:** static snippets only. No computed styles, runtime smoothness, frame rate, interruption behavior, assistive-tech behavior, or device feel was verified.

## 2. Vetted priority table

| Priority | Evidence | Location | Finding | Smallest safe correction |
| --- | --- | --- | --- | --- |
| P1 | `animate-[palette_420ms_ease-in_both]` | `src/components/CommandPalette.tsx` | High-frequency command UI uses a long, accelerating entry and bypasses semantic tokens. Static evidence does not show a Reduced Motion branch. | Replace arbitrary keyframe class with tokenized open/closed transition using opacity + small transform, fast duration, responsive easing, and explicit reduced-motion behavior. |
| P1 | Pointer move writes `--drag-y` from `event.clientY`; release uses `animateTo(..., { duration: 400 })` | `src/components/SortableQueue.tsx` | Direct-manipulation evidence lacks explicit local coordinate space, grab offset, pointer capture, release velocity, interrupt-from-current behavior, and Reduced Motion behavior. Static evidence cannot prove feel, but the mechanics are under-specified for a draggable queue. | Rework drag state around local delta, pointer capture, measured px/s velocity, transform ownership, and an interruptible settle primitive; keep target semantics unless separately authorized. |
| P2 | `transition: all 360ms ease-in; transform-origin: center;` | `src/styles/motion.css` | Popover motion is broad, longer than existing panel token, and uses delayed-response easing. Center origin is only clearly appropriate for centered overlays, not trigger-anchored popovers. | Limit animated properties, use existing duration/easing tokens, set trigger-relative origin where applicable, and add Reduced Motion override. |
| P2 | `top: -24px` to `top: 0`; `500ms ease-in` | `src/components/toast.css` | Toast entry animates a layout-position property and uses a slow accelerating curve. Static evidence cannot prove jank, but the property and timing are risky for repeated notification feedback. | Animate `transform: translateY(...)` + `opacity` instead of `top`, shorten to tokenized panel/fast duration, use responsive easing, and add Reduced Motion. |
| P2 | Higher-impact snippets lack visible `prefers-reduced-motion` while button has it | Multiple | Reduced Motion is implemented in the button precedent but not visible for palette, popover, toast, or queue settle. | Standardize a component-level Reduced Motion rule: preserve feedback via opacity/color/static state, reduce or remove spatial travel, shorten duration to 80ms where motion remains. |
| P3 | Mixed hard-coded values: `360ms`, `420ms`, `500ms`, `400` | Multiple | Motion vocabulary is inconsistent with the semantic token precedent, making future tuning and product-wide feel harder. | Route routine UI motion through existing semantic tokens before adding any new token. |

## 3. Implementation plans

### Plan A — Tokenize transient overlay motion: popover + command palette

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

- Popovers and command palette respond immediately, finish quickly, and preserve causality without theatrical travel.
- Command palette opening must not slow keyboard-heavy workflows.
- Motion uses existing semantic tokens and the button precedent’s Reduced Motion approach.
- Popover origin should be trigger-relative if the component is anchored; keep `center` only for genuinely centered overlays.

**Project conventions to preserve**

- Keep `--duration-fast`, `--duration-panel`, and `--ease-responsive`.
- Prefer `transform` and `opacity`.
- Preserve visible focus and DOM semantics; do not hide focusable content in a way that traps or loses focus.

**Ordered steps**

1. In `src/styles/motion.css`, replace `.popover { transition: all 360ms ease-in; }` with explicit properties only, e.g. `opacity, transform`.
2. Use `var(--duration-panel)` or a shorter local duration if the popover is small; use `var(--ease-responsive)`.
3. Add open/closed state selectors if they already exist; otherwise stop and inspect the actual popover state API before inventing selectors.
4. Set `transform-origin` from an existing positioning variable if present; otherwise choose a documented default only after confirming whether `.popover` is anchored or centered.
5. In `src/components/CommandPalette.tsx`, remove the arbitrary `animate-[palette_420ms_ease-in_both]`.
6. Replace it with a stable class plus `data-open={open}` state styling in CSS or the existing style system.
7. Use opacity plus a very small vertical or scale transform for open/close; avoid large travel.
8. Add `@media (prefers-reduced-motion: reduce)` for both surfaces: no spatial travel, duration around `80ms`, opacity/static state feedback retained.

**Hard boundaries**

- Do not change command execution, search result rendering, or keyboard shortcut behavior.
- Do not introduce a new animation library for this plan.
- Do not globally redefine the meaning of existing duration/easing tokens without a broader design-system decision.

**Mechanical checks**

- Search for remaining `animate-[palette_` and `.popover` `transition: all`.
- Confirm CSS contains explicit transition properties, not `all`.
- Run the project’s existing lint/type-check/build commands after confirming available scripts.

**Runtime/feel checks to perform later**

- Keyboard-open and keyboard-close the command palette repeatedly; confirm it feels immediate and does not delay typing.
- Verify focus remains visible before, during, and after open/close.
- Inspect popover origin against its trigger for anchored variants.
- Check Reduced Motion mode: state change remains clear with minimal or no travel.

**Reduced Motion behavior**

- Command palette: opacity/state feedback only, no positional travel; duration approximately `80ms`.
- Popover: preserve appearance/disappearance feedback; remove scale/slide unless needed for causality and kept extremely short.

**Source-drift stop condition**

- Stop before editing if the command palette already moved to a different animation API, if `.popover` is not the active popover class, if motion tokens were renamed, or if anchoring/origin is controlled by a positioning library contract not visible in the excerpt.

---

### Plan B — Repair toast entry from layout animation to feedback motion

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

- Toasts should arrive promptly as system feedback, without slow acceleration.
- Entry should avoid animating layout-position properties.
- Reduced Motion should preserve notification feedback without vestibular travel.

**Project conventions to preserve**

- Use existing semantic duration/easing tokens.
- Prefer `transform` and `opacity`.
- Keep toast placement semantics unchanged.

**Ordered steps**

1. Replace `top` movement in `@keyframes toast-enter` with `transform: translateY(-8px)` to `transform: translateY(0)`, plus opacity.
2. If `.toast` currently relies on `top: 0` for layout placement, keep that as a static positioning rule outside the keyframe.
3. Change `animation: toast-enter 500ms ease-in forwards;` to a tokenized duration, starting with `var(--duration-panel)` for entry or `var(--duration-fast)` if the toast is frequent.
4. Use `var(--ease-responsive)` instead of `ease-in`.
5. Add a `prefers-reduced-motion: reduce` block that removes vertical travel and uses a short opacity transition/animation.
6. Confirm exit motion if present elsewhere before adding new exit behavior; do not invent lifecycle semantics from the entry-only snippet.

**Hard boundaries**

- Do not change toast queueing, timeout, stacking, ARIA live-region behavior, or message copy in this plan.
- Do not add bounce or elastic motion; this is an operations console.
- Do not claim performance improvement without later measurement.

**Mechanical checks**

- Confirm `toast-enter` no longer animates `top`.
- Confirm `.toast` no longer uses `500ms ease-in`.
- Confirm a Reduced Motion rule exists for toast motion.
- Run the existing CSS/build validation available in the project.

**Runtime/feel checks to perform later**

- Trigger single and repeated toasts; confirm entry is noticeable but not sluggish.
- Verify the toast’s final position is unchanged.
- Verify screen-reader announcement timing is not delayed by visual animation.
- In Reduced Motion, confirm the toast appears clearly with minimal travel.

**Reduced Motion behavior**

- No vertical slide.
- Short opacity transition/animation, approximately `80ms`, or immediate appearance if opacity animation causes announcement or timing issues.

**Source-drift stop condition**

- Stop if toast positioning has been refactored away from `top`, if a toast lifecycle manager owns animation classes, or if there is an existing shared notification motion token not represented in the excerpt.

---

### Plan C — Make sortable queue drag physically auditable and interruptible

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

- Dragged item tracks the pointer 1:1 after intent is established.
- Movement uses a clear local coordinate space, not raw viewport `clientY` as the final semantic value.
- Release settle starts from the current on-screen value and can accept measured release velocity.
- Existing slot-selection semantics are preserved unless product owners authorize momentum-based target selection.
- Reduced Motion removes elastic/large travel while preserving clear reorder feedback.

**Project conventions to preserve**

- Keep calm, utility-first motion.
- Prefer transform ownership for moving the dragged visual.
- Use existing duration/easing tokens only for non-gesture fallback transitions; use an interruptible primitive for true drag settle if already available.

**Ordered steps**

1. On pointer down, record pointer id, container/item bounds, initial local pointer Y, current presentation Y, and grab offset.
2. Call pointer capture after drag intent is confirmed so tracking continues outside original bounds.
3. Convert movement to local CSS pixels: `localY = event.clientY - containerRect.top`; derive `dragDeltaY` from the starting local Y and grab offset.
4. Apply movement to the dragged item or a dedicated transform wrapper, not broadly to `queueRef`, unless source inspection proves `--drag-y` only invalidates the dragged item.
5. Maintain a short position/time sample buffer using monotonic timestamps; compute release velocity in CSS px/s.
6. On pointer up/cancel, settle from the current presentation value, not from a stale logical `currentY`.
7. Preserve `nearestSlot(currentY)` as the target rule initially. Treat projected-endpoint target selection as an optional later behavior change, not part of this safe correction.
8. Replace fixed `duration: 400` with an interruptible settle configuration if the existing `animateTo` API supports current value + velocity; otherwise stop and choose the smallest compatible animation primitive already present in the project.
9. Add cancellation handling: pointer cancel, lost capture, Escape if keyboard drag exists, and cleanup of inline styles/state.
10. Add Reduced Motion branch: snap with minimal duration, no overshoot/rubber band, clear static reorder/focus feedback.

**Hard boundaries**

- Do not change queue data ordering rules, slot calculation semantics, or persistence behavior.
- Do not add momentum-based target selection without explicit approval.
- Do not introduce broad parent CSS-variable updates if the list can be large and a narrower transform owner is feasible.
- Do not block input until settle completes.

**Mechanical checks**

- Confirm pointer handlers include down/move/up/cancel cleanup paths.
- Confirm coordinate units are documented as CSS px.
- Confirm release velocity is measured from multiple samples, not guessed from one event.
- Confirm drag transform ownership does not overwrite press/focus transforms on the same element without composition.
- Run existing type-check/lint tests.

**Runtime/feel checks to perform later**

- Drag slowly, quickly, reverse direction mid-settle, release outside bounds, and interrupt while settling.
- Confirm no visual jump at drag start: grab offset is preserved.
- Confirm target slot behavior matches the previous nearest-slot contract.
- Verify Reduced Motion mode removes overshoot/large travel while preserving reorder clarity.
- Measure under representative queue size before making performance claims.

**Reduced Motion behavior**

- Keep direct pointer tracking while dragging because it is causal input feedback.
- On release, snap with no bounce/overshoot and very short duration, or commit immediately with clear static slot/focus feedback.

**Source-drift stop condition**

- Stop if `animateTo` is from a library/API with a required different contract, if `currentY` is already a derived presentation value elsewhere, if pointer capture exists outside the excerpt, or if `--drag-y` is already scoped to a single transformed item by unseen CSS.

## 4. Recommended execution order

1. **Plan A first:** it aligns the highest-frequency keyboard surface and fixes the shared overlay vocabulary.
2. **Plan B second:** small, isolated, high-confidence repair for feedback motion.
3. **Plan C third:** highest interaction complexity; implement only after inspecting the full queue component and animation API.

## Explicitly unverified states

- Actual computed styles and active selectors.
- Whether `.popover` is anchored, centered, or reused for multiple overlay types.
- Whether `palette` keyframes include transform, opacity, or other properties.
- Whether existing Reduced Motion rules exist outside the snippets.
- Whether `animateTo` is CSS, WAAPI, spring-based, or library-owned.
- Pointer capture, grab offset, cancellation, and interruption behavior in the full queue.
- Runtime smoothness, layout cost, frame pacing, device feel, accessibility tree, focus order, and screen-reader announcement timing.
