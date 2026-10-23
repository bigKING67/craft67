## 1. Recon summary

- **Stack signals:** React-style TSX with TypeScript, CSS transitions/keyframes, and an arbitrary animation utility resembling Tailwind syntax. The utility framework and `animateTo` implementation are not established.
- **Motion locations:** shared declarations in `src/styles/motion.css`; component animation in `CommandPalette.tsx` and `toast.css`; pointer-driven motion in `SortableQueue.tsx`.
- **Existing conventions:** `--duration-fast: 160ms`, `--duration-panel: 240ms`, and `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)`. `src/components/Button.css` correctly demonstrates an explicit property, semantic tokens, subtle press feedback, and an 80ms Reduced Motion override. Leave it unchanged.
- **Authority/personality:** `DESIGN.md` requires crisp motion, semantic tokens, visible focus, and preserved feedback under Reduced Motion. Favor immediate keyboard response and restrained state continuity, not decorative entrances.
- **Frequency map — inferred, not measured:** palette and buttons likely high-frequency; popovers recurrent; toast frequency depends on events; sorting frequency is unknown, but pointer updates are continuous during use.
- **Evidence level:** snippet-only static review. Timing declarations are confirmed; perceived delay, layout cost, focus behavior, animation replay, and interruption defects are not observed. No files were modified.

## 2. Vetted priorities

Priority reflects expected leverage, not measured severity.

| Priority | Location | Confirmed evidence and bounded concern | Recommended action |
|---|---|---|---|
| P1 | `src/components/CommandPalette.tsx` | Unconditional class requests `420ms ease-in`; `open` only sets an attribute in the excerpt. Keyframes and visibility rules are unavailable. Decorative entry is a poor default for this keyboard-heavy surface. | Remove the animation utility; keep opening, closing, and focus immediate. |
| P1 | `src/styles/motion.css` | `.popover` uses `transition: all 360ms ease-in`, bypassing existing tokens and allowing unintended properties to transition. | Explicit opacity/transform transitions using 160ms and the responsive token. |
| P1 | `src/components/toast.css` | Entrance animates `top` for 500ms with `ease-in`. `top` is layout-affecting when applicable; actual positioning and cost are unknown. | Keep layout position static; use a short transform/opacity entrance. |
| P1 verification gate | Palette, popover, toast, queue | No Reduced Motion handling appears in these excerpts. This does **not** establish its absence elsewhere. | Check effective coverage; ensure the planned behavior preserves feedback without autonomous travel. |
| P2 | `src/components/SortableQueue.tsx` | Release requests a fixed 400ms animation. Coordinate conversion, current-position synchronization, cancellation, and velocity handling are not shown. | Establish these contracts before changing the release controller; make re-grabbing immediate. |

**Not promoted to findings:** centered popover origin is only suspect if this is a trigger-anchored scaling surface; the CSS-variable write alone does not prove descendant invalidation or frame loss. No additive animation is justified by the supplied evidence.

## 3. Implementation plans

All checks below are instructions for future execution, **not completed validation**. File/package scripts and test locations are unavailable; use the project’s declared checks rather than inventing commands.

### Plan 1 — Make the command palette immediate

**Scope/current excerpt — `src/components/CommandPalette.tsx`:**
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

**Target:** no palette entrance/exit animation, no result stagger, no animation-dependent input or focus delay. Opening and closing retain their existing state semantics.

**Conventions:** follow `DESIGN.md` on crisp feedback and visible focus. Tokens in `src/styles/motion.css` are 160ms/240ms and `cubic-bezier(0.23, 1, 0.32, 1)`; this high-frequency action needs neither duration. Preserve `src/components/Button.css` unchanged.

**Ordered steps**
1. Inspect the full component and the rules consuming `data-open`; determine whether the utility/keyframes also supply visibility or final-state styles.
2. Remove `className="animate-[palette_420ms_ease-in_both]"`. Preserve `data-open`, children, and the existing mount/visibility mechanism.
3. If keyframes supply essential final styles, move those styles into the existing state rules before removing the utility. Do not substitute an opacity-hidden but focusable closed state.
4. Verify focus entry and return are independent of animation completion; remove a motion-only wait only if one is actually found and its scope is understood.
5. Add or extend existing tests for open, close, immediate typing, repeated toggles, and closed-state focus exclusion.

**Hard boundaries:** no search, shortcut, result-order, dialog-semantics, or focus-ring redesign; no dependency additions; no global keyframe deletion without a usage check.

**Mechanical checks:** removed utility absent from this component; no replacement animation; existing typecheck/lint/tests pass. Tests should assert immediate interactivity without waiting 420ms.

**Runtime/feel checks:** open by keyboard, immediately type and navigate, dismiss with Escape, and repeat rapidly. Confirm correct focus entry/return and no flash or inaccessible closed content.

**Reduced Motion:** same immediate behavior; visible results, selection, and focus provide feedback without movement.

**Source-drift stop:** stop if the class or state contract differs, or visibility/focus depends on unavailable animation code. Resolve that dependency before editing; do not invent a new dialog lifecycle.

### Plan 2 — Normalize lightweight overlay entrances

**Scope/current excerpts — `src/styles/motion.css`:**
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

**`src/components/toast.css`:**
```css
@keyframes toast-enter {
  from { top: -24px; opacity: 0; }
  to { top: 0; opacity: 1; }
}
.toast {
  animation: toast-enter 500ms ease-in forwards;
}
```

**Target:** popovers respond over 160ms with explicitly scoped properties; toasts enter over 160ms from `translateY(-8px)` and opacity 0. Preserve placement, readability, and interaction throughout.

**Conventions:** use the existing `--duration-fast` and `--ease-responsive`, not new aliases or duplicate curves. `src/components/Button.css` demonstrates `transition: transform var(--duration-fast) var(--ease-responsive)` and the established 80ms Reduced Motion value.

**Ordered steps**
1. Inspect placement/state selectors, transform ownership, toast positioning, and any global Reduced Motion rules before changing either block.
2. Replace the popover transition with:
   ```css
   transition:
     transform var(--duration-fast) var(--ease-responsive),
     opacity var(--duration-fast) var(--ease-responsive);
   ```
3. Preserve existing open/closed endpoints. If scaling is trigger-anchored and placement metadata exists, use that system’s actual origin value; otherwise retain `center` pending evidence. Do not introduce a guessed library variable.
4. Replace toast keyframe endpoints with `transform: translateY(-8px); opacity: 0` and `transform: translateY(0); opacity: 1`. Replace its animation shorthand with `toast-enter var(--duration-fast) var(--ease-responsive) both`.
5. Keep the toast’s resting layout unchanged. If the original animation supplied essential `top: 0`, establish it statically on the appropriate positioned element. Do not overwrite a placement/stacking transform.
6. Add component-scoped Reduced Motion overrides: toast uses an opacity-only keyframe from 0 to 1 over 80ms; popover transitions only opacity over 80ms and has no decorative scale/slide difference between states.
7. Add tests for final resting styles and state changes. Retain one-shot toast keyframes unless an actual reversible lifecycle requires a separately scoped transition conversion.

**Hard boundaries:** no positioning-system rewrite, global token changes, new dependencies, toast lifetime changes, exit-delay invention, or button changes. Do not remove essential positioning transforms for Reduced Motion.

**Mechanical checks:** `.popover` no longer uses `all`; toast keyframes no longer animate `top`; both use existing timing/easing tokens; Reduced Motion rules resolve to opacity-only animation. Existing lint/build/tests pass.

**Runtime/feel checks:** open/close popovers rapidly and reverse mid-transition; inspect attachment at each supported placement. Trigger single and stacked toasts, including dismissal during entry. At normal and slowed playback, check for placement shifts, transform conflicts, text flashes, and delayed input. Profile only if performance remains a concern.

**Reduced Motion:** preserve opacity feedback at 80ms, readable content, focus, and announcements; remove decorative translation/scale rather than hiding the entire component.

**Source-drift stop:** stop if placement shares the animated transform, state selectors are unavailable, keyframe consumers differ, or toast final positioning is unclear. Identify the real motion-owning element before applying the replacement.

### Plan 3 — Make queue release interruptible without changing sorting policy

**Scope/current excerpt — `src/components/SortableQueue.tsx`:**
```tsx
function onPointerMove(event: PointerEvent) {
  queueRef.current?.style.setProperty("--drag-y", `${event.clientY}px`);
}

function onPointerUp() {
  setDragging(false);
  animateTo(nearestSlot(currentY), { duration: 400 });
}
```

**Target:** preserve the grab offset and direct pointer tracking; settle from the current displayed position; re-grabbing cancels settling immediately. Keep `nearestSlot(currentY)` as the destination policy—no velocity-projected slot changes.

**Conventions:** respect `DESIGN.md` on crisp response, visible focus, and Reduced Motion. Shared durations are 160ms/240ms; easing is `cubic-bezier(0.23, 1, 0.32, 1)`. Prefer an existing controller over another animation dependency.

**Ordered steps**
1. Trace `animateTo`, `currentY`, `--drag-y`, the actual dragged element, pointer capture, scrolling, and commit timing. Establish coordinate space, duration units, cancellation API, and transform ownership.
2. Ensure pointer-down records the pointer-to-item offset and the displayed position. While dragging, update the existing motion owner directly from pointer displacement in that same coordinate space; do not add smoothing or a CSS transition to pointer tracking.
3. Keep current position synchronized with the rendered drag position before calling `nearestSlot`. Preserve existing sorting and persistence semantics.
4. Cancel any active settle on re-grab, cancellation, or unmount. Start subsequent motion from the displayed value, never the previous target.
5. Replace the fixed 400ms settle with the existing controller’s supported interruptible transition: target 160ms using the shared responsive curve. Resolve tokens through the existing project bridge; do not assume the helper accepts CSS strings or a particular option name.
6. If the controller cannot sample/cancel/retarget, stop and specify its required extension before implementation. Do not silently swap libraries or build an unreviewed spring engine.
7. Read and subscribe to `prefers-reduced-motion` using the project’s existing mechanism; cancel settling and apply the destination immediately when reduction is active.

**Hard boundaries:** no reorder-algorithm changes, momentum projection, bounce, new drag thresholds, persistence changes, or accessibility redesign. Preserve existing keyboard reorder and announcement paths; do not claim they exist from this excerpt.

**Mechanical checks:** test coordinate conversion with a nonzero grab offset and scrolling; latest-position slot selection; cancellation before restart; cleanup on unmount; immediate Reduced Motion settlement. Verify 400ms is removed only from this release path and existing typecheck/lint/tests pass.

**Runtime/feel checks:** drag slowly, release between slots, re-grab mid-settle, reverse direction, scroll, and cancel. Confirm no initial jump, input lockout, stale completion, or disagreement between visual and committed order. Inspect normal and slowed playback on a desktop pointer setup.

**Reduced Motion:** retain user-controlled tracking; eliminate autonomous settling travel. Final order, focus/selection, and existing status feedback remain available immediately.

**Source-drift stop:** stop if helper capabilities, units, motion ownership, or coordinate contracts cannot be established, or cancellation affects persistence. Those are implementation prerequisites, not proven defects.

## 4. Execution order and unverified states

1. **Plan 1:** highest expected leverage for keyboard throughput; smallest intended scope.
2. **Plan 2:** align overlays with existing tokens and remove the confirmed layout-property animation.
3. **Plan 3:** execute after its controller/coordinate inspection gate; uncertainty is higher.

**Explicitly unverified:** actual usage frequency; utility/keyframe generation; effective styles and global Reduced Motion coverage; mount/exit lifecycles; focus and accessibility-tree behavior; popover anchoring; toast stacking/announcements; drag coordinates, cancellation, and keyboard sorting; rendering performance; browser compatibility; device feel. No browser, device, trace, recording, or user validation was performed.
