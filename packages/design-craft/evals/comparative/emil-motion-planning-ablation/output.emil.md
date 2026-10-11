## 1. Recon summary

- **Stack signals:** React-style TSX, plain CSS, an arbitrary animation utility class, and imperative pointer handling. The utility framework and `animateTo` implementation are unknown.
- **Motion locations:** shared tokens and popover rules in `src/styles/motion.css`; palette animation in `src/components/CommandPalette.tsx`; toast keyframes in `src/components/toast.css`; drag/release logic in `src/components/SortableQueue.tsx`.
- **Existing conventions:** `--duration-fast: 160ms`, `--duration-panel: 240ms`, and `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)`. `src/components/Button.css` demonstrates property-scoped transitions and an 80ms Reduced Motion override. Preserve that correct local precedent.
- **Authority and personality:** the stated `DESIGN.md` requirements favor crisp, restrained feedback, semantic tokens, visible focus, and a Reduced Motion path that retains state information.
- **Frequency map — inferred, not measured:** palette and button interactions are likely frequent; popovers recur throughout workflows; toast frequency depends on events; sorting is task-dependent, with repeated pointer updates during each gesture.
- **Evidence level:** supplied static excerpts only. Findings distinguish declarations from possible consequences. No repository inspection, execution, or browser/device validation of this project occurred.

## 2. Vetted priorities

| Priority | Severity | Location | Supported finding | Recommended action |
|---|---|---|---|---|
| 1 | High | `src/components/CommandPalette.tsx` | Declares an unconditional 420ms `ease-in` animation class. Its relationship to `open` is not shown. | Remove decorative palette animation; make keyboard access immediate. Do not infer that input is currently blocked. |
| 2 | Medium | `src/styles/motion.css` | `.popover` uses `transition: all 360ms ease-in`, bypassing existing tokens and broadly selecting properties. | Scope transitions to opacity/transform and use the existing 160ms responsive tokens. |
| 3 | Medium | `src/components/toast.css` | Entry animates `top` over 500ms with `ease-in`. Actual layout cost depends on positioning and rendering context. | Preserve the 24px entry relationship using transform, with a 160ms responsive entrance. |
| 4 | Medium | Palette, popover, toast, queue excerpts | No Reduced Motion handling is shown for these surfaces; only the button excerpt demonstrates it. Global coverage is unknown. | Inspect effective coverage, then implement explicit local behavior without removing feedback. |
| 5 | Medium; investigation-gated | `src/components/SortableQueue.tsx` | Release requests a fixed 400-duration animation; units, cancellation, velocity handling, and CSS-variable consumers are unknown. | Verify the motion adapter and coordinate model before implementing a short, interruptible settle. |

`transform-origin: center` is **not independently a defect**: the excerpt does not establish whether the popover scales or how it is anchored. Likewise, the drag CSS variable alone does not establish expensive descendant invalidation. No additive animation is justified by this evidence.

## 3. Implementation plans

### Plan A — Make the command palette immediate

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

**Target:** opening, closing, and repeated invocation have no decorative animation or motion-dependent input delay. Search, selection, and focus remain visible and immediate.

**Conventions:** respect the stated `DESIGN.md` requirements for throughput and visible focus. Existing tokens in `src/styles/motion.css` are 160ms/240ms with `cubic-bezier(0.23, 1, 0.32, 1)`; this high-frequency surface needs no replacement animation.

**Ordered steps:**
1. Inspect the palette’s visibility, mount/unmount, focus, and animation-event wiring. Determine whether `palette` keyframes also supply essential visibility styles.
2. Remove `className="animate-[palette_420ms_ease-in_both]"`; preserve `data-open={open}` and `<SearchResults />`.
3. If visibility depends on those keyframes, stop and revise the plan rather than deleting essential state behavior. Otherwise retain the existing open/closed mechanism unchanged.

**Hard boundaries:** no result staggering, new motion library, search changes, focus redesign, or global utility/keyframe deletion.

**Mechanical checks:** confirm the animation class is absent; confirm `open` and result rendering contracts are unchanged. Run the project’s declared typecheck/lint and palette tests after discovering their actual commands; add or extend a focused test for open/closed rendering if infrastructure exists.

**Runtime/feel checks — future work:** repeatedly invoke, dismiss, and reopen by keyboard; type immediately after invocation. Verify visible initial focus, focus restoration, no closed-but-focusable palette, and no visual replay. These checks are acceptance criteria, not claims about current behavior.

**Reduced Motion:** use the same immediate state changes; retain visible focus, selection, and results feedback. No fade is required merely to preserve feedback.

**Source-drift stop:** stop if the excerpt differs materially, animation events control lifecycle, keyframes own visibility, or the open/closed contract cannot be established from source.

### Plan B — Normalize passive entrances without broad transitions

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

**Target:** retain existing lifecycle and positioning; use 160ms responsive entrances. Popovers transition only transform/opacity; toast entry translates from `-24px` to `0` at its existing final position. No decorative bounce.

**Conventions:** reuse `--duration-fast` and `--ease-responsive`, without changing their definitions. `src/components/Button.css` establishes explicit transform transitions and an 80ms Reduced Motion precedent; leave that file unchanged.

**Ordered steps:**
1. Inspect all `.popover` state rules, toast positioning, transform ownership, exit/stack behavior, and existing Reduced Motion overrides. Confirm shared tokens reach both surfaces.
2. Replace the popover declaration with:
   ```css
   transition: transform var(--duration-fast) var(--ease-responsive),
               opacity var(--duration-fast) var(--ease-responsive);
   ```
3. Preserve its current origin unless source confirms trigger-anchored scaling and an existing placement-origin contract. If confirmed, use that contract; do not invent a positioning-library variable.
4. Replace toast entry endpoints with `transform: translateY(-24px); opacity: 0` and `transform: translateY(0); opacity: 1`. Use `animation: toast-enter var(--duration-fast) var(--ease-responsive) forwards`.
5. Preserve the prior final positioning outside the keyframes: if `top: 0` was supplied only by the animation, establish it as static styling after verifying positioning. Do not overwrite an existing transform used for stacking.
6. Add local `prefers-reduced-motion: reduce` rules: popovers use only an 80ms opacity transition and no animated translation/scale; toast uses a separate 80ms opacity-only entry with `var(--ease-responsive)`. Keep essential positioning transforms intact.

**Hard boundaries:** only the two named CSS files; no lifecycle rewrites, timers, dismissal changes, dependency additions, global motion reset, or button edits. Do not add exit animation or convert toast lifecycle merely because entry uses keyframes.

**Mechanical checks:** confirm `.popover` has no `transition: all`; toast keyframes contain no animated `top`; durations/easing reference existing tokens. Confirm matching opacity-only overrides and no duplicate animation names. Run available stylesheet/build checks using declared project scripts.

**Runtime/feel checks — future work:** open and reverse popovers rapidly; verify positioning and focus never depend on transition completion. Trigger single and stacked toasts, dismiss during entry, and inspect at normal and slow playback. Check for jumps, transform collisions, replay, or retained `forwards` styles interfering with exits. Do not infer smoothness from property choice alone.

**Reduced Motion:** verify no decorative movement, an 80ms fade where applicable, and unchanged readability, dismissal, focus, and notification semantics.

**Source-drift stop:** stop if transforms already own positioning/stacking, `top` is externally animated, token scope differs, or state/lifecycle rules conflict with these replacements. Record the conflict and revise scope before implementing.

### Plan C — Establish a reliable drag-to-settle contract

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

**Target:** preserve pointer-to-item continuity, settle from the currently rendered position, and allow immediate re-grab without jumping. Use a restrained, interruptible 160ms responsive settle as the initial target—not an invented spring configuration.

**Conventions:** `src/styles/motion.css` defines `--duration-fast: 160ms` and `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)`. Reuse them through the existing animation adapter; do not introduce parallel constants or assume `animateTo` units/API. Preserve visible focus and existing keyboard sorting.

**Ordered steps:**
1. Trace `animateTo`, `currentY`, `nearestSlot`, pointer-down/cancel handlers, and every `--drag-y` consumer. Identify coordinate spaces, item offsets, scrolling, transform ownership, and the order of state/layout updates.
2. Confirm the adapter supports cancellation/retargeting from the rendered position and token-derived timing. If it does not, stop for a scoped adapter plan; changing `{ duration: 400 }` alone is insufficient.
3. At drag start or re-grab, cancel the settle at its current rendered position and rebase the pointer offset there. During dragging, preserve direct tracking with no trailing transition.
4. On release, capture the latest valid drag position and destination before clearing dragging state; ensure a layout change cannot reset the visual start. Keep the existing nearest-slot selection policy.
5. Settle to that destination using the shared 160ms responsive timing. Handle pointer cancellation without leaving a stale animation, drag flag, or captured pointer.
6. Under Reduced Motion, commit the release destination immediately, while preserving direct manipulation and a visible settled/drop state. Respond safely if the preference changes during a settle.

**Hard boundaries:** do not change ordering/business rules, add inertia or bounce, replace the drag framework, or rewrite CSS-variable updates without inspecting consumers. Implementation stays in the named file unless a revised plan explicitly authorizes dependencies.

**Mechanical checks:** test final-pointer sampling, cancellation, release-state ordering, and re-grab using the project’s existing test infrastructure. Confirm there is at most one active settle, shared timing is used, and Reduced Motion bypasses release interpolation. Run declared typecheck/lint commands.

**Runtime/feel checks — future work:** test slow/fast releases, re-grab mid-settle, first/last slots, scrolling, pointer cancellation, and keyboard reorder. Watch for coordinate jumps and delayed tracking at normal speed; use slow playback to inspect the handoff.

**Reduced Motion:** pointer-driven movement remains necessary direct feedback; autonomous release travel is removed. Keep final ordering, drop indication, and existing announcements observable.

**Source-drift stop:** stop if adapter semantics, coordinate ownership, token access, keyboard behavior, or required handlers cannot be verified, or if implementation requires changes outside the authorized file.

## 4. Execution order and unverified states

1. **Plan A:** highest likely throughput benefit and smallest change.
2. **Plan B:** reuse established tokens; validate positioning before replacing toast movement.
3. **Plan C:** investigate first, then implement only after its adapter and coordinate gates pass.

**Explicitly unverified:** actual interaction frequency; palette keyframes and visibility lifecycle; effective CSS and global Reduced Motion coverage; popover anchoring; toast positioning/stacking/exits; drag adapter units and interruptibility; focus behavior, announcements, keyboard parity, frame performance, and browser/device feel. No checks above have been executed, and no files or on-disk plans were created.
