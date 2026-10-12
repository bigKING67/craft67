## 1. Recon summary

- **Stack signals:** React/TSX, CSS custom properties, CSS transitions/keyframes, an arbitrary animation utility, and imperative pointer handling. The utility framework and `animateTo` implementation are not established.
- **Motion locations:** shared values in `src/styles/motion.css`; palette motion in TSX; toast motion in component CSS; queue motion in pointer handlers.
- **Existing conventions:** `--duration-fast: 160ms`, `--duration-panel: 240ms`, and `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)`. The button demonstrates a scoped `transform` transition, restrained press feedback, and an 80ms Reduced Motion override.
- **Authority/personality:** preserve the existing crisp, calm, semantic-token-based system and visible focus. Motion should explain state changes, not delay keyboard work.
- **Frequency map — expected, not measured:** palette = frequent keyboard invocation; popover = repeated contextual interaction; toast = event-driven and potentially bursty; queue = continuous during a drag plus one release; button = frequent baseline feedback.
- **Evidence level:** static excerpts only. Missing selectors, keyframes, lifecycle code, positioning logic, helpers, and global accessibility rules limit conclusions. No performance, usability, or accessibility failure has been measured.

## 2. Vetted priorities

| Priority | Finding supported by excerpts | Consequence / implementation decision |
|---|---|---|
| P1 | Popover uses `transition: all 360ms ease-in` and a centered origin. | Broad transition scope and bespoke timing conflict with the local crisp-motion precedent. Scope properties; anchor the origin only if placement information is available. |
| P1 | Palette declares a 420ms ease-in animation independently of `data-open`. | Open/close coupling, replay, and hidden-state behavior are not shown. Establish lifecycle semantics before replacing the animation. |
| P1 | Toast entrance animates `top` for 500ms with ease-in. | `top` is a layout-affecting property when applicable; actual cost depends on positioning. Replace entrance travel with a dedicated transform after checking transform ownership. |
| P1 | Queue directly writes pointer Y, then requests a 400-duration settlement. | Direct tracking is worth preserving. Release timing is bespoke; units, coordinate mapping, cancellation, and interruption behavior need inspection. |
| P1, cross-cutting | Only the button excerpt shows Reduced Motion handling. | Coverage elsewhere is unestablished, not proven absent. Inspect global handling and supply explicit equivalent feedback where necessary. |

All three plans below are proposed work, not completed implementation or validation.

## 3. Implementation plans

### Plan A — Make contextual surfaces immediate, state-driven, and interruptible

**Files/current excerpts**
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

**Target behavior:** opening responds immediately; a short entrance preserves causality without gating input. Closing removes interactivity immediately. Rapid reopen reverses or restarts from the current visual state without a delayed focus change.

**Project conventions:** reuse the fast/panel durations and responsive easing; follow the button’s explicit-property precedent. Do not change shared token values.

**Ordered steps**
1. Inspect palette keyframes, utility generation, mounting/visibility rules, focus ownership, and popover placement/transform ownership.
2. Replace `all` with only the properties actually changing. Prefer opacity plus, if useful, at most 4px of entrance translation; omit translation if it conflicts with positioning.
3. Use `--duration-fast` and `--ease-responsive` for both surfaces initially. Reserve panel timing for an actual panel-sized transition, not merely its component name.
4. Replace the unconditional palette animation class with explicit open/closed styling. Attach entrance to the real opening lifecycle; define initial-render behavior deliberately.
5. Keep hidden content noninteractive and out of tab order/accessibility exposure using the existing visibility mechanism. Do not use opacity alone. Preserve focus entry/restoration without waiting for animation.
6. Prefer immediate close unless the existing presence mechanism safely supports a short exit. If retaining exit, handle interruption and unmount cleanup.

**Hard boundaries:** no overlay architecture rewrite, search behavior change, new animation dependency, or overwrite of positioning transforms. No invented placement selectors or keyframe definitions.

**Mechanical checks:** verify the old class and `transition: all` are removed from these targets; confirm token resolution and generated styles; test open/close/reopen, initially open, unmount, and hidden tab exclusion using the existing test setup.

**Runtime/feel checks — pending:** keyboard invoke → type immediately → Escape → reopen; inspect focus visibility/restoration, placement variants, clipping, and repeated invocation. Confirm feedback feels immediate rather than staged.

**Reduced Motion:** remove entrance translation/scale; use immediate visibility or an explicit opacity-only fade capped at the local 80ms precedent. Preserve focus and open/closed state feedback; never await animation completion for correctness.

**Source-drift stop condition:** stop if the full files use a different presence owner, competing animation system, or shared positioning transform. Re-map ownership before changing selectors or lifecycle behavior.

### Plan B — Shorten toast arrival without changing notification semantics

**File/current excerpt**
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

**Target behavior:** a toast becomes readable promptly with a restrained entrance; notification stacking and dismissal remain stable.

**Project conventions:** use `--duration-fast` and `--ease-responsive`; explicitly animate only opacity and an owned transform. Preserve existing notification semantics.

**Ordered steps**
1. Inspect toast positioning, final `top`, stacking/reflow rules, transforms, dismissal, and whether timers or handlers depend on this animation.
2. Replace the `top` keyframes with opacity `0 → 1` and a small `translateY(-4px) → translateY(0)` entrance, only where that transform is exclusively owned.
3. Set duration/easing from existing tokens. Establish the final position and visible state in normal styles so fill mode is not responsible for persistent correctness.
4. Preserve current mounting and announcement behavior; ensure removing motion does not suppress delivery, dismissal, or timer cleanup.
5. If stack placement already owns transform, use opacity-only entrance rather than adding a wrapper or replacing the placement transform without review.

**Hard boundaries:** no changes to notification priority, live-region policy, display lifetime, stack order, or automatic focus behavior. No permanent `will-change` or claim of guaranteed compositor execution.

**Mechanical checks:** verify no `top` interpolation remains in these entrance keyframes; confirm final styles work with animations disabled; test multiple arrivals, dismissal during entrance, and any animation-event-dependent cleanup.

**Runtime/feel checks — pending:** inspect single and burst arrivals, multiline content, stack repositioning, and dismissal. Check readability and distraction during keyboard work; measure performance before making performance claims.

**Reduced Motion:** opacity-only entrance capped at 80ms, or immediate appearance. Keep the message, announcement, controls, and full intended reading opportunity intact.

**Source-drift stop condition:** stop if `top: 0` currently establishes final placement, keyframes are shared with other surfaces, or animation completion controls notification lifetime. Resolve those dependencies before substitution.

### Plan C — Preserve direct drag tracking; make settlement short and cancellable

**File/current excerpt**
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

**Target behavior:** the item follows input without easing during drag; release settles once toward the valid slot. A new interaction interrupts settlement immediately.

**Project conventions:** retain the direct-manipulation path. Use fast-duration/responsive-easing semantics for release through the project’s existing JS token access mechanism, if one exists.

**Ordered steps**
1. Inspect `animateTo` duration units, easing/cancellation API, `currentY` updates, `--drag-y` consumers, coordinate conversion, pointer capture, and reorder commit semantics.
2. Verify pointer coordinates and slot coordinates share a frame, including scroll offsets and grab offset. Correct only confirmed mismatches; do not assume raw `clientY` is wrong.
3. Ensure the rendered drag property has no smoothing transition while dragging. Do not introduce a spring or per-event React state update solely for motion.
4. Replace the hard-coded release timing with the resolved fast token; convert units explicitly. Map responsive easing only after confirming the helper’s supported format.
5. Cancel existing settlement on a new drag, pointer cancellation, and unmount. Commit the destination exactly once through the existing reorder contract, independent of decorative animation completion.
6. If there is no supported token bridge, pause to agree a minimal bridge rather than duplicating `160` as an undocumented constant.

**Hard boundaries:** no reorder algorithm rewrite, speculative event throttling, new drag library, or new layout reads in `onPointerMove`. Do not imply pointer motion supplies keyboard reordering.

**Mechanical checks:** test coordinate mapping, latest-pointer release, single commit, rapid re-grab, cancellation, and cleanup. Verify duration units and resolved tokens; inspect CSS for unwanted drag-time transitions.

**Runtime/feel checks — pending:** try short/long drags, scrolling, release near slot boundaries, and rapid re-grab. Check that tracking feels attached and release does not hold the next action. Verify existing keyboard reorder feedback and focus separately.

**Reduced Motion:** retain necessary pointer-following movement; snap to the destination on release without decorative travel. Preserve the final order, focus, and existing destination/status feedback. Reuse preference handling that responds to changes and cleans up subscriptions.

**Source-drift stop condition:** stop if the helper lacks interruption support, settlement commits order internally, or drag/slot coordinates use undocumented transforms. Resolve the contract before adjusting timing.

## 4. Execution order and verification limits

1. **Inspect ownership and global Reduced Motion handling first.** Confirm tokens, lifecycle contracts, and existing tests; do not widen scope speculatively.
2. **Execute Plan A**, prioritizing palette keyboard continuity; **then Plan B** for the smaller CSS-focused change.
3. **Execute Plan C** after resolving the helper and coordinate contracts. Validate each plan before tuning durations further.

**Explicitly unverified:** compiled utilities and keyframes; computed styles; actual focus/hidden-state semantics; global Reduced Motion coverage; announcement behavior; placement and clipping; toast stacking; drag coordinates and cancellation; keyboard reorder support; frame timing, browser/device behavior, and perceived feel. No runtime or accessibility validation is claimed.
