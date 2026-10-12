## 1. Recon summary

- **Stack signals:** TSX components, React-style state/ref usage, CSS custom properties and keyframes, and a utility-style arbitrary animation class. The utility compiler and drag animation library are not established.
- **Motion locations:** shared definitions in `src/styles/motion.css`; component CSS for toast/button; inline animation configuration in the command palette; imperative pointer handling and release animation in the sortable queue.
- **Existing conventions:** `--duration-fast: 160ms`, `--duration-panel: 240ms`, and `--ease-responsive`. The button demonstrates property-scoped transitions, token reuse, and an `80ms` Reduced Motion override. Preserve visible focus and feedback.
- **Personality:** calm, crisp, utilitarian. Motion should explain state changes, not demand attention or delay the next command.
- **Frequency map — expected, not measured:** palette and button interactions are likely frequent; popovers recur during inspection; toast frequency depends on events; dragging generates continuous input while active, with one settle per release.
- **Evidence level:** static excerpts only. Declared timings and properties are observable; actual visibility, frame cost, interruption behavior, keyboard access, and perceived responsiveness are not.

## 2. Vetted priorities

| Priority | Finding supported by excerpts | Impact hypothesis and disposition |
|---|---|---|
| P1 | Popover uses `transition: all 360ms ease-in` and a centered origin. | Broad property coverage and delayed acceleration conflict with crisp state changes. Scope properties and use tokens; choose origin only after identifying its anchor. |
| P1 | Palette declares `420ms ease-in`; `open` is passed to `data-open`, but no state selector or keyframes are supplied. | Timing is out of convention; open/close binding cannot be established. Resolve state wiring before replacing the animation. |
| P1 | Toast animates `top` and opacity for `500ms ease-in`. | `top` is layout-affecting when positioning makes it operative; actual rendering cost is unknown. Replace positional animation with a small transform and shorten entry. |
| P1 | Queue release uses a literal `400` duration; the move handler writes `clientY` to a custom property. | Release timing is out of convention. Coordinate mapping, latest-position handling, and interruption need inspection—not a presumption that dragging is broken. |
| P1, cross-cutting | A Reduced Motion override is shown only for the button. | Coverage elsewhere is unverified. Each change must include an explicit reduced path preserving state feedback and focus. |

The button is a local convention to preserve, not an additional remediation target.

## 3. Implementation plans

### Plan A — Shared overlay motion and command palette

**Exact paths/current excerpts**

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

**Target behavior and conventions**
- Use explicit opacity/transform properties with `--duration-fast` and `--ease-responsive`; leave global token values unchanged.
- Palette entry: opacity `0 → 1`, at most `4px → 0` vertical travel. No input, focus, or result-rendering delay.
- Popover: similarly restrained motion; use an anchor-facing origin only where an existing scale effect makes origin relevant. Do not add scale merely to justify changing origin.
- Start with `160ms` for these frequent interactions; retain `--duration-panel` for existing panel-level usage.

**Ordered steps**
1. Locate `.popover` consumers, state selectors, transform owners, palette keyframes, stylesheet loading, and mount/unmount behavior.
2. Replace `transition: all` with only properties actually changed by the popover state rules.
3. Replace the palette’s literal animation class with a narrowly scoped rule in the existing loaded motion stylesheet, using the shared tokens.
4. Bind entry to the real open lifecycle. `data-open` alone must not be assumed to hide or deactivate content.
5. Preserve existing close/focus restoration semantics; use immediate close rather than inventing delayed unmount infrastructure.
6. Add a reduced override: opacity-only feedback of at most `80ms`, no travel/scale, no delayed interaction.

**Hard boundaries**
- Do not change search behavior, selection, focus ownership, dialog semantics, or global token values.
- Do not animate size, position offsets, or unrelated properties. Do not overwrite transforms owned by positioning code.
- Hidden palette content must not become focusable merely to support animation.

**Mechanical checks**
- Confirm old `360ms`/`420ms` declarations are removed from these paths; verify generated CSS and token resolution through the project’s build.
- Check selectors against actual open/closed markup; test rapid state toggles and any existing focus-return assertions.
- Verify reduced rules win the cascade without changing the final visible state.

**Runtime/feel checks — to perform**
- Keyboard-open, type immediately, select, escape, and reopen rapidly; confirm no blocked input, stale animation, or focus-ring clipping.
- Check popovers at different anchor edges and after repositioning; movement should explain opening without appearing to drift.

**Source-drift stop condition**
- Stop and revise the patch if these excerpts differ, the palette has a separate presence controller, or positioning owns the same transform. Do not stack competing motion systems.

### Plan B — Toast entry without positional layout animation

**Exact path/current excerpt**

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

**Target behavior and conventions**
- Entry uses opacity plus `translateY(-4px) → translateY(0)`, over `--duration-fast` with `--ease-responsive`.
- Preserve final placement, toast lifetime, announcement timing, and immediate availability of toast actions.

**Ordered steps**
1. Inspect toast positioning, stacking, transform ownership, dismissal rules, and whether the current animation supplies an otherwise missing final `top: 0`.
2. Establish final placement in the appropriate static rule if needed; do not blindly add `top: 0` to every toast.
3. Replace animated `top` with the small transform; replace literal duration/easing with shared tokens.
4. Make resting opacity/transform explicit where necessary so animation completion or removal cannot hide the toast.
5. Add Reduced Motion keyframes with opacity only, at most `80ms`, and the same final visible state.

**Hard boundaries**
- No toast queue, timeout, live-region, action, or dismissal redesign.
- Do not reuse a transform already responsible for stack positioning. Avoid persistent fill behavior that overrides stacking transforms.
- No unconditional `will-change`; no claim of compositor execution from CSS alone.

**Mechanical checks**
- Confirm `toast-enter` no longer animates `top`; verify final placement remains defined.
- Check stylesheet imports, shared token availability, reduced override precedence, and existing timer/dismissal tests.
- Confirm entering animation does not restart on unrelated toast content updates.

**Runtime/feel checks — to perform**
- Trigger single and successive toasts; dismiss during entry and interact with actions immediately.
- Check stacking, clipping, overlapping entries, keyboard focus visibility, and announcement timing in both motion modes.

**Source-drift stop condition**
- Stop if the real toast uses transform-based stacking, shared keyframes with other consumers, or animation-completion-driven lifetime logic. Resolve those contracts before changing entry.

### Plan C — Direct drag tracking and brief, interruptible settling

**Exact path/current excerpt**

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

**Target behavior and conventions**
- Preserve direct tracking while dragging; do not add smoothing or transitions between pointer samples.
- On release, settle to the valid slot over the shared `160ms` fast duration with responsive easing, interruptible by a new drag.
- Reduced Motion: immediate settle with persistent destination/selection feedback.

**Ordered steps**
1. Inspect the `--drag-y` consumer, coordinate space, `currentY` updates, slot calculation, animation API units, cancellation support, and reorder commit timing.
2. Verify the release target uses the latest position in the same coordinate space as `nearestSlot`; correct mapping only if inspection demonstrates a mismatch.
3. Confirm active tracking is not interpolated by CSS. Preserve existing pointer capture and cancellation behavior.
4. Read/convert existing semantic motion tokens through an existing project bridge, or add a small local adapter after confirming library units/easing support. Do not duplicate `160` as an unexplained constant.
5. Cancel in-flight settling before a new drag; prevent stale completion callbacks from committing an obsolete destination.
6. Implement instant reduced settling; retain destination, selected-item, focus, and existing announcement feedback.
7. Inspect keyboard reorder parity; if absent, record a separate accessibility dependency rather than inventing controls in this motion patch.

**Hard boundaries**
- Do not alter slot ordering rules, persistence semantics, scroll behavior, or commit timing without a demonstrated correctness issue.
- Do not impose pointer-event throttling without measurement. Do not add a new animation dependency.
- No mandatory wait for visual settling before another operation.

**Mechanical checks**
- Test coordinate conversion and latest-position selection; verify duration units and token parsing.
- Test release, cancellation, rapid re-grab, stale completion suppression, and reduced-mode settling.
- Confirm transforms/custom properties have one clear owner during tracking and settling.

**Runtime/feel checks — to perform**
- Drag slowly and rapidly, release near slot boundaries, re-grab mid-settle, and test scrolled containers.
- Check keyboard reorder where available, focus continuity, and destination feedback with Reduced Motion enabled.

**Source-drift stop condition**
- Stop if `animateTo` has different duration semantics, another controller owns settling, or `currentY` uses an undocumented coordinate space. Establish those contracts before tuning motion.

## 4. Execution order and unverified states

1. **Plan A:** establish scoped, token-based overlay behavior and the reduced-motion pattern.
2. **Plan B:** apply the same conventions to a contained entry animation.
3. **Plan C:** follow after coordinate, cancellation, and animation API contracts are understood.

**Explicitly unverified:** effective CSS cascade, palette visibility and keyframes, mount/unmount behavior, toast positioning and announcements, drag coordinate correctness, keyboard reorder support, focus restoration, Reduced Motion coverage, rendering performance, and perceived timing. All runtime/feel checks above are proposed acceptance checks—not completed validation.
