## 1. Recon summary

- **Stack signals:** TSX components suggest React; styling combines CSS custom properties, CSS keyframes, an arbitrary-value animation class, and an imperative `animateTo` call. The utility compiler and animation library are not established.
- **Motion locations:** shared styling in `src/styles/motion.css`; palette motion in TSX; toast motion in component CSS; queue movement in pointer handlers.
- **Existing conventions:** `--duration-fast: 160ms`, `--duration-panel: 240ms`, and `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)`. The button demonstrates property-scoped transitions, token reuse, and an `80ms` Reduced Motion override. `DESIGN.md` requires crisp motion, semantic tokens, visible focus, and preserved feedback.
- **Product personality:** quiet, responsive, workday-long utility. Motion should explain state changes, not make operators wait.
- **Frequency map — inferred, not measured:** palette potentially frequent for keyboard users; popovers recurrent; toasts event-driven and potentially repetitive; sorting task-dependent, with very frequent updates during a drag. Favor restraint on repeated actions.
- **Evidence level:** static snippets only. Definitions, consumers, lifecycle handling, focus behavior, and motion-preference coverage outside these excerpts remain unknown. No runtime or device findings are asserted.

## 2. Vetted priorities

Priorities reflect product relevance and visible implementation risk, not measured user impact.

| Priority | Finding | Evidence and qualification | Intended correction |
|---|---|---|---|
| P1 | Palette uses an outlying timing and unclear state linkage | `420ms ease-in` bypasses tokens; `open` only sets an attribute here. Keyframes, external selectors, and mounting behavior are unavailable. | State-linked, short motion; keyboard interaction never waits for it. |
| P1 | Popover transition is broad and inconsistent | `all 360ms ease-in` includes every changing animatable property; actual changed properties are unknown. Center origin may not match placement. | Explicit properties, shared timing, placement-aware origin only if scaling is retained. |
| P1 | Reduced Motion coverage is not shown for the audited surfaces | Only the button excerpt includes an override. This is a coverage gap in evidence, not proof of app-wide absence. | Verify and explicitly support each CSS and imperative path. |
| P2 | Toast entrance animates `top` with long, accelerating timing | `500ms ease-in`; positional animation can require layout work when `top` applies. No performance cost was measured. | Short opacity/transform entrance, without changing toast layout or delivery semantics. |
| P2 | Queue release uses a fixed `400ms` and has unresolved interruption behavior | Pointer movement writes viewport Y; its consumer and `currentY` synchronization are not shown. Cancellation and keyboard paths are also unknown. | Preserve direct manipulation; short, interruptible settling using the correct coordinate model. |

## 3. Implementation plans

### Plan A — Align shared and overlay motion

**Exact files/current excerpts**

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
- Keep existing token values. Use fast timing for compact popovers and panel timing for the palette, with the existing responsive easing.
- Favor opacity plus a small, bounded translation; avoid large travel and decorative scaling.
- Motion follows actual open/close changes, not search-result rerenders. Input readiness and focus must not depend on animation completion.

**Ordered steps**
1. Inspect complete files, palette keyframes, popover state/placement selectors, utility generation, and existing visibility/focus lifecycle before editing.
2. Replace `transition: all` with only properties that the established states change: preferably `opacity, transform`.
3. Remove the palette’s hardcoded animation utility; connect token-based styles to its established state mechanism. Use `data-open` only if it is the canonical state hook.
4. Preserve mount/unmount semantics. If close motion requires presence infrastructure not already available, make closing immediate rather than adding a lifecycle system.
5. Add scoped Reduced Motion overrides; verify that invisible closed content cannot remain keyboard-interactive.

**Hard boundaries**
- No token renaming, global timing retuning, search changes, new animation dependency, or generic focus-system rewrite.
- Do not overwrite transforms used by positioning. Compose through the existing mechanism or use opacity only.
- Do not introduce animation delays or defer focus until motion finishes.

**Mechanical checks**
- Confirm the old palette timing and broad popover transition are removed from these targets.
- Check stylesheet inclusion, generated utility output where applicable, selector precedence, type checks, and available tests.
- Add lifecycle tests for rapid toggles, result updates without entrance replay, and correct closed-state focusability.

**Runtime/feel checks — to perform**
- Repeated keyboard opening, typing immediately, Escape, focus return, and rapid reopening.
- Check anchor continuity and placement changes; verify no flash, positional jump, or blocked input.

**Reduced Motion**
- Remove translation/scaling; retain at most an `80ms` opacity change, consistent with the local timing precedent.
- Preserve focus indicators and immediate state changes. Override animations as well as transitions where both exist.

**Source-drift stop condition**
- Stop and revise scope if the full files differ materially, placement owns the same transform, or an existing overlay/presence primitive already controls these behaviors. Do not layer competing motion onto it.

### Plan B — Make toast arrival brief and layout-independent

**Exact file/current excerpt**

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
- A toast appears at its final layout position with a subtle upward-origin arrival: proposed `translateY(-8px)` to `translateY(0)` plus opacity.
- Use `--duration-fast` and `--ease-responsive`; arrival should acknowledge an event without drawing prolonged attention.

**Ordered steps**
1. Inspect base positioning, stack layout, transform ownership, exit rules, and timer semantics.
2. Ensure the nonanimated rule expresses the intended final position; removing the keyframe’s `top: 0` must not relocate the toast.
3. Replace animated `top` with transform/opacity, using existing transform composition if needed. If composition is unavailable, use opacity only.
4. Apply shared tokens. Prefer a stable base state and backwards fill for entrance rather than retaining an unnecessary forwards-filled animation.
5. Add a scoped Reduced Motion keyframe/override and regression coverage for repeated arrivals.

**Hard boundaries**
- Do not change dismissal duration, announcement behavior, message priority, stack ordering, or actionable-toast focus.
- Do not add `will-change`, stack-reflow choreography, or exit animation without separate evidence of need.

**Mechanical checks**
- Verify `toast-enter` no longer animates `top`, and shared tokens are in scope.
- Confirm the final position and opacity remain correct after animation ends; verify Reduced Motion wins in the cascade.
- Run available style/build checks and toast lifecycle tests.

**Runtime/feel checks — to perform**
- Check one toast, bursts, multiline content, actionable content, and dismissal during entrance.
- Inspect for clipping, stack displacement, transform conflicts, and excessive repeated movement. Profile only if a performance claim is needed.

**Reduced Motion**
- Use opacity-only entrance of at most `80ms`; preserve the message, announcement, action availability, and full dismissal policy.

**Source-drift stop condition**
- Stop if `top` participates in stack placement, another layer owns transforms, or a toast primitive supplies its own motion. Reconcile ownership before replacing keyframes.

### Plan C — Keep queue dragging direct; shorten release settling

**Exact file/current excerpt**

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
- Preserve immediate pointer tracking; do not add easing to each pointer update.
- Settle to the valid slot using the existing fast token and responsive easing, provided the animation API supports them.
- Re-grab or cancellation interrupts settling without a jump. Logical order and keyboard feedback do not wait for a visual animation.

**Ordered steps**
1. Trace `--drag-y`, `currentY`, `nearestSlot`, pointer capture, scroll offsets, and `animateTo` implementation. Establish coordinate space, units, cancellation, and commit timing.
2. Verify release uses the latest pointer position. Correct synchronization only if the complete implementation shows a mismatch.
3. Replace `400` through the existing token-to-JavaScript bridge. If none exists, add a narrow conversion at the component boundary after confirming API units; do not duplicate a new timing scale.
4. Cancel an active settle before a new drag; continue from its current visual position using the library’s supported mechanism.
5. Preserve or verify pointer-cancel cleanup and keyboard reorder behavior. Keep any broader accessibility redesign separately scoped.

**Hard boundaries**
- No new sorting algorithm, speculative throttling, spring/bounce behavior, or animation library migration.
- Do not substitute viewport coordinates for local offsets without mapping them.
- Do not clear drag styles before capturing the visual start position if doing so would break continuity.

**Mechanical checks**
- Test latest-position release, target selection, cancellation, re-grab, unmount cleanup, and token/API unit conversion.
- Verify preference changes reach the imperative path and no stale animation completion callback overwrites newer order.

**Runtime/feel checks — to perform**
- Fast and slow drags, release near boundaries, scrolled containers, immediate re-grab, pointer cancellation, and keyboard reorder.
- Check pointer attachment, release continuity, correct final order, visible focus, and absence of an input lock during settling.

**Reduced Motion**
- Retain pointer-attached movement needed for direct manipulation; snap to the final slot without release travel.
- Preserve destination/order feedback and existing keyboard announcements. Do not rely on a CSS media query alone for imperative animation.

**Source-drift stop condition**
- Stop if the API uses different duration units, the drag system already owns cancellation/token mapping, or coordinate/state ownership differs from the excerpt. Resolve that contract before implementation.

## 4. Execution order and unverified states

1. **Plan A:** establish consistent overlay timing and preference handling without altering token values.
2. **Plan B:** deliver the small, isolated toast correction.
3. **Plan C:** implement after coordinate, state, and animation API contracts are understood.

**Explicitly unverified:** actual animation playback, palette keyframes, hidden-state semantics, focus management, token availability, transform ownership, toast positioning/announcements, drag correctness, keyboard sorting, cancellation, global Reduced Motion coverage, performance, and perceived feel. All runtime checks above are proposed acceptance checks—not completed validation.
