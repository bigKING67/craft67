## 1. Recon summary

**Stack signals**
- Frontend surface uses TSX components plus CSS.
- Motion is currently split across:
  - global tokens in `src/styles/motion.css`
  - component-local CSS in `src/components/toast.css`
  - utility/arbitrary animation syntax in `CommandPalette.tsx`
  - imperative pointer/animation logic in `SortableQueue.tsx`

**Where motion lives**
- Semantic motion tokens exist:
  - `--duration-fast: 160ms`
  - `--duration-panel: 240ms`
  - `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)`
- Component-level motion also exists outside those tokens:
  - `.popover` uses `transition: all 360ms ease-in`
  - command palette uses `animate-[palette_420ms_ease-in_both]`
  - toast uses `top` animation for `500ms ease-in`
  - sortable queue uses imperative `animateTo(..., { duration: 400 })`

**Existing conventions**
- The button precedent is the strongest local standard:
  - transform-only interaction
  - semantic duration/easing tokens
  - explicit Reduced Motion handling
  - short active feedback: `160ms`, reduced to `80ms`
- Existing design authority requires crisp motion, semantic tokens, visible focus, and Reduced Motion paths that still preserve feedback.

**Product personality**
- Calm, all-day desktop operations console.
- Motion should clarify causality and state continuity, not feel decorative.
- Keyboard-heavy support/revenue workflows imply frequent transitions must be short, predictable, and interruptible.

**Frequency map**
| Surface | Expected frequency | Motion sensitivity |
|---|---:|---|
| Button active state | Very high | Already aligned with precedent |
| Command palette | High | Should feel instant; slow entry can tax keyboard-heavy users |
| Popovers | High | Needs crisp open/close and no broad `all` transitions |
| Toasts | Medium | Should notify without shifting layout or lingering |
| Sortable queue drag settle | Episodic but high-salience | Needs spatial continuity without sluggish snap-back |

**Evidence level**
- Static excerpt audit only.
- No runtime, computed-style, trace, screen recording, accessibility-tree, device, or user-test evidence.
- Findings are based on explicit source patterns, not observed runtime behavior.

---

## 2. Priority table

| Priority | Finding | Evidence | Risk | Recommended direction |
|---:|---|---|---|---|
| P0 | Reduced Motion coverage is inconsistent | Only `.button` excerpt shows `@media (prefers-reduced-motion: reduce)` | Users requesting reduced motion may still receive long entrance/settle animations | Add reduced paths for popover, palette, toast, and sortable settle |
| P0 | High-frequency UI uses non-tokenized slow easing | Palette `420ms ease-in`; popover `360ms ease-in`; toast `500ms ease-in`; sortable `400` | Motions may feel delayed for keyboard-heavy workflows | Move to `--duration-fast`, `--duration-panel`, `--ease-responsive` |
| P1 | `.popover` uses `transition: all` | `transition: all 360ms ease-in` | Unintended properties may animate; harder to reason about state changes | Limit to `opacity`, `transform`, possibly `visibility`/discrete state handling |
| P1 | Toast animates layout-affecting `top` | `from { top: -24px } to { top: 0 }` | Potential layout/reflow cost and less crisp motion | Use `transform: translateY(...)` plus `opacity` |
| P1 | Command palette uses arbitrary animation declaration inline | `className="animate-[palette_420ms_ease-in_both]"` | Bypasses semantic tokens and makes Reduced Motion harder to centralize | Replace with semantic class/data-state styling |
| P2 | Sortable settle duration appears fixed and long | `animateTo(nearestSlot(currentY), { duration: 400 })` | Drag release can feel sluggish, especially over short distances | Use shorter token-aligned settle duration with reduced-motion path |

---

## 3. Implementation plans

### Plan A — Normalize global motion tokens and popover behavior

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

**Target behavior**
- Popovers open/close crisply using only `opacity` and `transform`.
- Duration aligns with existing semantic tokens.
- Reduced Motion keeps state feedback but shortens or removes spatial travel.
- No broad `transition: all`.

**Project conventions to follow**
- Reuse existing token names.
- Match the button precedent: transform-based motion, tokenized duration/easing, explicit Reduced Motion.
- Preserve visible focus behavior; do not animate focus outlines away.

**Ordered steps**
1. Keep existing root tokens unless broader project inspection shows canonical alternatives.
2. Replace `.popover` transition with explicit properties:
   - `opacity`
   - `transform`
3. Use:
   - `var(--duration-panel)` for panel/popover entry where continuity matters
   - `var(--ease-responsive)` for the easing curve
4. Add or align state selectors using existing markup conventions if present, for example:
   - `[data-open="true"]`
   - `[data-open="false"]`
   - existing open/closed classes if the real file uses them
5. Use a small transform distance/scale only if already present in surrounding code; otherwise prefer opacity plus subtle scale/translate.
6. Add Reduced Motion branch:
   - keep opacity feedback
   - reduce duration to `80ms` or equivalent local precedent
   - avoid scale/translate travel

**Hard boundaries**
- Do not introduce a new animation library.
- Do not rename existing tokens unless all usages are updated deliberately.
- Do not alter layout, z-index, focus management, or popover positioning.
- Do not use `transition: all`.

**Mechanical checks**
- Search for:
  - `transition: all`
  - `ease-in`
  - `360ms`
  - `.popover`
- Run the closest available lint/type/style check.
- Confirm CSS parses after media-query additions.

**Runtime / feel checks to perform later**
- Open/close popovers with mouse and keyboard.
- Confirm focus ring remains visible and not delayed.
- Confirm rapid repeated open/close does not feel queued or sticky.
- Confirm Reduced Motion still gives clear visibility feedback.

**Reduced Motion behavior**
- Duration: `80ms` preferred, matching the button precedent.
- Animate opacity only, or use effectively no transform travel.
- Preserve open/closed feedback; do not silently remove all state change indication.

**Source-drift stop condition**
- Stop and re-audit if `src/styles/motion.css` no longer contains the shown token block or `.popover` has moved to a component-specific implementation.
- Stop if popover state is controlled by a framework animation API rather than CSS state selectors.

---

### Plan B — Convert command palette and toast to semantic, tokenized component motion

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
- Command palette appears quickly enough for keyboard-heavy use.
- Toast enters without animating layout-affecting properties.
- Both use semantic durations/easing.
- Both have explicit Reduced Motion behavior.

**Project conventions to follow**
- Prefer named classes and state attributes over arbitrary inline animation values for reusable UI.
- Use existing semantic tokens:
  - `--duration-fast`
  - `--duration-panel`
  - `--ease-responsive`
- Preserve state continuity but avoid decorative delay.

**Ordered steps**
1. Replace the command palette arbitrary animation class with a semantic class, for example:
   - `className="command-palette"`
   - keep `data-open={open}`
2. Define command palette motion in the appropriate existing stylesheet, preferably the file already responsible for shared motion if command palette has no local CSS.
3. Use data-state styling:
   - closed: slightly offset or scaled only if needed, `opacity: 0`
   - open: settled transform, `opacity: 1`
4. Use `var(--duration-panel)` for palette open/close unless product review prefers `--duration-fast`.
5. Replace toast `top` keyframes with transform/opacity keyframes:
   - from: `transform: translateY(-8px); opacity: 0`
   - to: `transform: translateY(0); opacity: 1`
6. Reduce toast duration from `500ms` to tokenized `var(--duration-panel)` or shorter if local notification precedent exists.
7. Add Reduced Motion media query for both:
   - command palette: `80ms` opacity transition, no spatial travel
   - toast: `80ms` opacity transition/animation, no vertical travel

**Hard boundaries**
- Do not change command execution, search behavior, result rendering, or keyboard shortcuts.
- Do not alter toast stacking, dismissal timing, live-region behavior, or content.
- Do not add decorative bounce, overshoot, blur, or spring effects.
- Do not remove `data-open` unless replacing it with an already-established state convention.

**Mechanical checks**
- Search for:
  - `animate-[palette_420ms_ease-in_both]`
  - `toast-enter`
  - `top: -24px`
  - `500ms ease-in`
  - `prefers-reduced-motion`
- Run type-check for TSX changes.
- Run CSS/style validation if available.
- Confirm no unused class or missing stylesheet import is introduced.

**Runtime / feel checks to perform later**
- Open the command palette repeatedly from keyboard shortcut.
- Type immediately after opening; confirm visual motion does not compete with input.
- Trigger multiple toasts; confirm entry does not push layout unexpectedly.
- Check both normal and Reduced Motion settings.
- Confirm no focus outline or active input state is obscured during palette entry.

**Reduced Motion behavior**
- Command palette:
  - keep immediate visibility/opacity feedback
  - no scale or translate travel
  - duration around `80ms`
- Toast:
  - opacity-only feedback
  - no `top` or translate movement
  - duration around `80ms`
- Feedback remains present; it is shortened/simplified, not removed entirely.

**Source-drift stop condition**
- Stop and re-audit if the command palette no longer uses the shown arbitrary animation class.
- Stop if toast positioning depends on `top` for actual layout placement rather than only animation.
- Stop if a centralized animation/state utility already governs palette or toast behavior elsewhere.

---

### Plan C — Make sortable queue drag settle responsive, short, and Reduced-Motion aware

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
- Drag motion follows the pointer with direct causality.
- Release-to-slot settle is short and clear, not sluggish.
- Reduced Motion preserves final placement feedback with minimal travel.
- Pointer-move writes avoid unnecessary work where feasible.

**Project conventions to follow**
- Keep motion crisp and token-aligned.
- Use transform-based rendering downstream where `--drag-y` is consumed.
- Avoid introducing broad abstractions for one interaction.
- Preserve throughput for operators manipulating queues.

**Ordered steps**
1. Inspect how `--drag-y`, `currentY`, `nearestSlot`, and `animateTo` are used before changing behavior.
2. Confirm whether `--drag-y` drives `transform` rather than layout properties.
3. If pointer events can fire faster than paint, gate style writes with `requestAnimationFrame`:
   - store latest `clientY`
   - write `--drag-y` once per frame
   - cancel pending frame on unmount/end if needed
4. Replace fixed `400` duration with token-aligned logic:
   - default settle: around `var(--duration-fast)` / `160ms`
   - allow up to `var(--duration-panel)` / `240ms` only for longer travel if distance-based duration already fits existing code
5. Use the existing responsive easing curve if `animateTo` accepts easing.
6. Add Reduced Motion branch:
   - snap or near-snap to nearest slot
   - optional `80ms` opacity/position confirmation if the API supports it
7. Ensure `setDragging(false)` does not remove required visual state before the settle animation can communicate placement.

**Hard boundaries**
- Do not rewrite sorting logic.
- Do not change queue ordering semantics.
- Do not change pointer capture, selection, or keyboard reordering behavior unless directly required by existing code.
- Do not introduce physics/spring behavior unless already used locally.
- Do not animate layout properties if the current implementation can use transform.

**Mechanical checks**
- Search for:
  - `animateTo(`
  - `--drag-y`
  - `nearestSlot`
  - `currentY`
  - `prefers-reduced-motion`
- Type-check after TSX changes.
- If adding `requestAnimationFrame`, verify cleanup paths for pointer up/cancel/unmount.
- Confirm constants are not duplicated if motion tokens already have a JS bridge.

**Runtime / feel checks to perform later**
- Drag short and long distances; release near and between slots.
- Confirm settle feels immediate but still communicates destination.
- Stress rapid drag/release sequences.
- Test pointer cancel/escape cases if supported.
- Check Reduced Motion behavior.

**Reduced Motion behavior**
- Prefer immediate placement or `80ms` maximum settle.
- Avoid animated travel over distance.
- Preserve visible final-state confirmation, such as stable slot placement or opacity/state change.

**Source-drift stop condition**
- Stop and re-audit if `animateTo` is not a local helper or its API does not accept duration/easing as shown.
- Stop if `--drag-y` is consumed by `top`, `margin`, or layout instead of transform; that becomes a broader performance/layout fix.
- Stop if sortable behavior is shared by multiple queue components and requires a common interaction contract.

---

## 4. Recommended execution order

1. **Plan A first** — establish global motion hygiene and remove the broadest risky pattern: `transition: all`.
2. **Plan B second** — fix two visible, frequent surfaces by replacing slow/non-tokenized entrance animations.
3. **Plan C third** — tune the more interaction-specific sortable queue after confirming how its animation helper and CSS variable are consumed.

This order moves from lowest dependency / broadest convention alignment to the most behavior-sensitive interaction.

---

## Explicitly unverified states

- No browser rendering or computed styles were inspected.
- No device, refresh-rate, or reduced-motion OS setting was tested.
- No screen recording, performance trace, or paint/layout profile was captured.
- No accessibility tree or keyboard-flow validation was performed.
- No confirmation that `top` animation currently causes measurable layout cost at runtime.
- No confirmation that `--drag-y` is consumed by transform rather than layout.
- No confirmation of existing stylesheet imports or animation utility APIs beyond the provided snippets.
- No user testing or operator throughput measurement was performed.
