## 1. Recon summary

- **Stack signals:** React/TSX, CSS custom properties and keyframes, a utility-style animation class, and imperative pointer/animation code. The utility compiler and `animateTo` implementation are not identified.
- **Motion locations:** shared declarations in `src/styles/motion.css`; component-local palette, toast, queue, and button behavior.
- **Existing conventions:** `--duration-fast: 160ms`, `--duration-panel: 240ms`, and `--ease-responsive`. The button demonstrates an explicit property transition, token reuse, and a local Reduced Motion override.
- **Authority:** `DESIGN.md` requires crisp motion, semantic tokens, visible focus, and reduced-motion feedback. Its full contents are not available here.
- **Product personality:** calm, precise, workday-long utility. Motion should explain a change, not delay input or demand attention.
- **Frequency map — planning assumptions, not measured:** button feedback is likely very frequent; palette use likely frequent for keyboard-heavy operators; popovers recur during inspection; toast frequency depends on operations; sorting is task-dependent but pointer updates are continuous during a drag.
- **Evidence level:** static excerpts only. Declaration-level issues are identifiable; actual rendering, lifecycle behavior, accessibility, performance, and perceived quality remain unverified.

## 2. Vetted priorities

| Priority | Finding and evidence | Intended correction |
|---|---|---|
| P1 | `.popover` uses `transition: all 360ms ease-in` and a centered origin, bypassing shared tokens. Actual transitioned properties and placement are unknown. | Explicit properties, responsive easing, token duration, placement-aware origin only if scaling is justified. |
| P1 | Palette declares `420ms ease-in`; the animation class is unconditional while `open` only appears as a data attribute. Replay, visibility, and dismissal behavior cannot be inferred. | Connect motion to verified open/close lifecycle; make keyboard readiness independent of animation completion. |
| P1 | Toast keyframes animate `top` and opacity for `500ms ease-in`. Whether `top` takes effect depends on positioning not shown. | Use transform/opacity for equivalent visual travel where appropriate; shorten using existing tokens. No performance gain is claimed without measurement. |
| P1 | No Reduced Motion branch is shown for the four audited surfaces. This does **not** establish that none exists elsewhere. | Explicitly verify and cover each path; retain focus, state, and confirmation feedback without decorative travel. |
| P2 | Queue release requests a fixed `400` duration, unlike shared CSS timing. Pointer coordinates, animation units, cancellation, and keyboard sorting are not shown. | Preserve direct manipulation; use a short, interruptible release settle after verifying coordinate and timing contracts. |

The button is a useful local precedent, not a remediation target or proof that every interaction is accessible.

## 3. Implementation plans

### Plan A — Shared rules, popovers, and command palette

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

**Target behavior / conventions**
- Popovers respond promptly; the palette preserves opening/closing causality without making search or focus wait.
- Reuse `--duration-fast` for popovers and `--duration-panel` for palette entry, with `--ease-responsive`; exit should be no longer than entry.
- Limit animation to opacity and, only where useful, a small transform. Preserve semantic tokens, visible focus, and established overlay behavior.

**Ordered steps**
1. Inspect the full styles, palette keyframes, utility configuration, overlay lifecycle, placement information, and focus implementation before changing selectors.
2. Replace popover `all` with only the properties that actually change. Remove centered scaling unless warranted; if scaling remains, derive the origin from the existing placement mechanism, including flipped placements.
3. Replace the palette’s literal timing with token-based styling using the project’s existing CSS integration. Do not invent an unverified utility syntax.
4. Tie entry to a real closed→open change. Do not replay on result updates or ordinary rerenders. Use the existing exit/presence mechanism, if any; do not add delayed unmount solely for decoration.
5. Keep logical opening, search readiness, dismissal, and focus restoration independent of animation completion. Ensure closed content cannot receive focus.

**Hard boundaries**
- No new animation dependency, global token retuning, button redesign, or focus/overlay framework rewrite.
- Do not assume `data-open` currently controls hiding. Preserve verified semantics and do not infer a dialog role from the component name.

**Mechanical checks**
- Confirm the targeted `all`, `360ms`, and `420ms` declarations are removed; inspect generated CSS for token resolution and specificity.
- Check open/close selectors, keyframe definitions, rerender behavior, closed-state focusability, and existing type/build tests.
- Test rapid open→close→open and input during entry; assert state does not depend on animation events.

**Runtime/feel checks — to perform**
- Keyboard-open, type immediately, navigate results, dismiss with Escape, and reopen rapidly.
- Verify visible focus, correct focus restoration, no stale exit hiding a reopened surface, and alignment with the actual trigger/placement.

**Reduced Motion**
- Remove translation/scale; use immediate state changes or opacity-only feedback capped at the existing 80ms local precedent.
- Preserve focus and visibility feedback. State cleanup must work even when no animation event fires.

**Source-drift stop**
- Stop and revise this plan if full definitions reveal competing animation utilities, transform ownership, a different presence contract, or conflicting focus/placement behavior; do not stack another animation on top.

### Plan B — Toast entry without layout-position animation

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

**Target behavior / conventions**
- A toast appears promptly and clearly without interrupting work.
- Use `--duration-fast` and `--ease-responsive`; retain existing visual hierarchy and notification semantics.

**Ordered steps**
1. Inspect toast positioning, transform usage, stacking, entry/exit lifecycle, dismissal timers, and announcement behavior.
2. Establish the correct resting position in ordinary CSS. If the current travel is effective and appropriate, replace `top: -24px → 0` with `translateY(-24px) → translateY(0)` plus the existing opacity change.
3. If `top` is currently ineffective, do not introduce 24px of new travel by default; use opacity-only entry unless spatial movement is justified.
4. Replace literal duration/easing with shared tokens. Keep resting styles explicit; retain a fill mode only if the verified lifecycle requires it.
5. Leave notification delivery and dismissal timing independent of entry completion.

**Hard boundaries**
- No changes to message priority, announcement policy, dismissal duration, or stacking algorithm.
- Do not overwrite an existing transform used for stacking or swipe dismissal; resolve ownership before implementation.

**Mechanical checks**
- Confirm entry keyframes no longer animate `top`, and base positioning still defines the intended resting location.
- Check token references, reduced-motion cascade, multiple-toast styles, and existing toast tests.
- Verify appearance does not reset the dismissal timer or duplicate an announcement.

**Runtime/feel checks — to perform**
- Exercise single and burst arrivals, dismissal during entry, actionable toasts, and stack changes.
- Check clipping, overlap, readable arrival, unchanged keyboard focus, and announcements with assistive technology.
- Inspect performance only to validate observed behavior; transform/opacity is not a guarantee of smoothness.

**Reduced Motion**
- Remove vertical travel; use immediate appearance or opacity-only feedback up to 80ms.
- Keep content, actions, and existing announcement behavior intact.

**Source-drift stop**
- Stop if unseen styles own `top`/transform, entry also controls stack layout, or the timer is coupled to animation completion. Resolve that contract before substituting properties.

### Plan C — Direct queue tracking and interruptible settling

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

**Target behavior / conventions**
- The dragged item follows input directly, then settles briefly into its committed destination.
- Use `--duration-fast` and responsive easing for ordinary settling through the existing animation interface; verify units and supported easing first.
- Sorting state and keyboard feedback must not wait for decorative settling.

**Ordered steps**
1. Trace `--drag-y`, `currentY`, pointer capture/cancellation, coordinate conversion, slot calculation, and `animateTo` ownership/API.
2. Confirm release uses the latest pointer position in the same coordinate system as `nearestSlot`. Preserve any existing pickup offset and scroll compensation.
3. Keep direct tracking free of eased transitions. Cancel an in-flight settle when a new drag begins; do not add smoothing that makes the item trail input.
4. Resolve shared timing/easing through the existing JS token bridge. If none exists, define a scoped adapter after inspecting project conventions; do not maintain a second hardcoded token table.
5. Commit the reorder independently of visual completion. Make stale completion callbacks harmless; preserve existing cancellation semantics.
6. Inspect keyboard sorting. If absent, scope an explicit companion accessibility task rather than claim pointer tuning solves keyboard access.

**Hard boundaries**
- No sorting algorithm rewrite, spring dependency, unconditional frame-loop refactor, or invented `animateTo` options.
- Do not change raw coordinates until their consumers are understood.

**Mechanical checks**
- Test latest-position release, coordinate conversion, interruption, cancellation, and state updates without completion callbacks.
- Verify duration units, token conversion, Reduced Motion preference handling, and removal of the literal `400`.
- Cover keyboard reorder/focus behavior where implemented; document any missing path.

**Runtime/feel checks — to perform**
- Check rapid drags, immediate re-grab, edge slots, scrolling, pointer cancellation, and keyboard reorder.
- Look for release jumps, trailing motion, stale callbacks, focus loss, and any throughput delay.

**Reduced Motion**
- Retain direct input-coupled tracking; remove autonomous settling and decorative neighbor travel.
- Snap to the committed slot while retaining destination indication, visible focus, and existing reorder feedback.

**Source-drift stop**
- Stop if `currentY` is derived elsewhere, the animation API has different timing units, or another layer owns reorder completion/transforms. Update the plan before changing behavior.

## 4. Execution order and unverified states

1. **Inspect contracts first**, then implement Plan A without changing shared token values.
2. **Implement Plan B** as a small, isolated correction.
3. **Implement Plan C** after establishing coordinate, interruption, and keyboard contracts.
4. Run mechanical checks, then the listed runtime/feel checks in normal and Reduced Motion modes.

**Explicitly unverified:** generated/computed CSS, hidden-state behavior, palette keyframes and replay, focus semantics, toast positioning and announcements, drag coordinates and cancellation, keyboard sorting, animation API units, performance, and perceived timing. No browser, device, accessibility-tree, trace, recording, or user validation has been performed.
