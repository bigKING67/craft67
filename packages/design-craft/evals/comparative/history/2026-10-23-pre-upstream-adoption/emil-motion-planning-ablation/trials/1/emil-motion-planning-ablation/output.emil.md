## 1. Recon summary

- **Stack signals:** React/TSX, CSS keyframes/transitions, a utility-style arbitrary animation class, and imperative pointer handling. The CSS utility processor and `animateTo` implementation are unknown.
- **Motion locations:** shared tokens/popover rules in `src/styles/motion.css`; component motion in `CommandPalette.tsx`, `toast.css`, `SortableQueue.tsx`, and `Button.css`.
- **Existing conventions:** `--duration-fast: 160ms`, `--duration-panel: 240ms`, and `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)`. The button already uses an explicit transform transition, subtle `scale(0.98)`, and an 80ms Reduced Motion override. Preserve that precedent.
- **Authority/personality:** `DESIGN.md` requires crisp, token-based motion, visible focus, and feedback under Reduced Motion. Favor quiet, immediate responses over decorative entrances, staggering, or bounce.
- **Frequency map — inferred, not measured:** command palette and button feedback are likely frequent; popovers recurring; toast frequency depends on workflow; sorting is task-dependent, with continuous updates during each drag.
- **Evidence level:** supplied static excerpts only. Findings concern declarations and exposed contracts—not observed latency, dropped frames, inaccessible states, or actual interruption behavior.

## 2. Vetted priorities

| # | Priority | Location | Supported finding and limitation | Action |
|---|---|---|---|---|
| 1 | P1 | `src/components/CommandPalette.tsx` | Declares a 420ms ease-in animation on a keyboard-oriented surface. Class is unconditional; keyframes and mounting behavior are absent, so replay on every toggle is **not established**. | Remove decorative palette animation; preserve immediate state and focus feedback. |
| 2 | P1 | `src/styles/motion.css` `.popover` | `transition: all 360ms ease-in` bypasses tokens and can animate unrelated property changes. Actual transitioned properties are unknown. | Explicit property allowlist, 160ms responsive easing. |
| 3 | P1 | `src/components/toast.css` | Entrance animates `top` over 500ms with ease-in. `top` is layout-affecting when positioning applies; actual layout cost is unmeasured. | Use a short transform/opacity entrance without changing resting layout. |
| 4 | P1 verification gate | Palette, popover, toast, queue excerpts | No local Reduced Motion path is shown for these surfaces. Global handling may exist; absence across the application is **not proven**. | Resolve effective coverage and include a preserved-feedback path in every plan. |
| 5 | P2 | `src/components/SortableQueue.tsx` | Release requests a fixed 400-duration animation; units, cancellation, and presentation-state handoff are unknown. Pointer movement writes a custom property whose consumers are absent. | Establish coordinate ownership and interruption contracts before changing the settle behavior. |

`transform-origin: center` is **not independently a defect**: anchored scaling and actual placement are unverified. Likewise, the custom-property write alone does not prove broad style invalidation. No additive animation opportunities are justified by these excerpts.

## 3. Implementation plans

All checks below are **future acceptance checks**, not completed validation. No files have been edited or plans written to disk.

### Plan 1 — Make the command palette immediate

**Scope/current evidence — `src/components/CommandPalette.tsx`:**
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

**Target:** no decorative open/close animation, result stagger, or animation-dependent input delay. Opening, typing, navigating, executing, and closing remain immediate.

**Project conventions:** honor `DESIGN.md`’s crisp feedback and visible focus. `src/components/Button.css` establishes restrained local motion; this high-frequency surface deliberately needs no duration token because it needs no animation.

**Ordered steps**
1. Inspect the actual palette keyframes, `data-open` selectors, mounting owner, and focus lifecycle. Determine whether animation currently supplies visibility or completion events.
2. Remove `className="animate-[palette_420ms_ease-in_both]"`; preserve `data-open={open}`, `SearchResults`, and component identity.
3. Preserve existing explicit open/closed visibility semantics. If they depend on animation, stop for a scoped visibility contract rather than merely deleting the class.
4. Remove obsolete palette keyframes only after confirming they have no other consumers and identifying their exact file.
5. Preserve immediate focus placement, Escape handling, focus return, selection indication, and result feedback. Do not add timeouts to coordinate these.

**Hard boundaries:** no search/ranking changes, remounting changes, new animation dependency, global animation reset, or accessibility redesign. Undisclosed selector/keyframe files require an explicit scope update before editing.

**Mechanical checks:** diff confirms the arbitrary animation class is absent; tests cover closed/open/closed visibility, immediate keyboard input, Escape, and focus return. Run the project’s declared typecheck/lint/test scripts after inspecting its package configuration; commands are not supplied by this evidence.

**Runtime/feel checks:** repeatedly open, type, navigate, execute, and close; confirm no stale visible results, input gating, focus flash, or invisible focusable closed content. Test rapid reopen and empty/loading/error results.

**Reduced Motion:** identical immediate behavior; visible focus, selected-result styling, and textual status remain. Do not substitute another entrance animation.

**Source-drift stop:** stop if the excerpt differs materially, `open` has different semantics, or visibility/focus depends on animation events. Resolve those dependencies before applying this plan.

### Plan 2 — Normalize popover and toast entrances

**Scope/current evidence — `src/styles/motion.css`:**
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

**Current evidence — `src/components/toast.css`:**
```css
@keyframes toast-enter {
  from { top: -24px; opacity: 0; }
  to { top: 0; opacity: 1; }
}
.toast {
  animation: toast-enter 500ms ease-in forwards;
}
```

**Target:** 160ms responsive entrances; only explicitly owned transform/opacity properties animate. Notifications remain readable immediately, with no changes to dismissal deadlines.

**Project conventions:** reuse `var(--duration-fast)` and `var(--ease-responsive)` exactly; preserve the 240ms panel token. Follow `src/components/Button.css`’s explicit-property transition and local 80ms Reduced Motion precedent.

**Ordered steps**
1. Inspect popover open/closed selectors and toast positioning, mounting, stacking, dismissal, and transform ownership. Identify effective global Reduced Motion rules.
2. Replace the popover declaration with:
   ```css
   transition: transform var(--duration-fast) var(--ease-responsive),
               opacity var(--duration-fast) var(--ease-responsive);
   ```
   Preserve existing endpoints; omit transform from this allowlist if positioning owns it or no motion transform exists. Do not introduce scaling merely to justify an origin change.
3. Keep the center origin unless anchored scaling is confirmed. If confirmed, use the existing positioning system’s actual origin value; do not invent a provider-specific variable.
4. For a toast with no competing transform owner, replace the entrance with:
   ```css
   @keyframes toast-enter {
     from { transform: translateY(-24px); opacity: 0; }
     to { transform: translateY(0); opacity: 1; }
   }
   .toast {
     animation: toast-enter var(--duration-fast) var(--ease-responsive) backwards;
   }
   ```
   Make resting opacity/transform explicit where necessary; preserve the original resting `top: 0` through static positioning if the animation previously supplied it. Do not add positioning modes.
5. Keep this keyframe as a one-time entrance only. If toast reorder/dismiss/re-entry shares it, stop and scope a state-transition implementation against the real lifecycle.
6. Add local Reduced Motion rules: popover opacity-only transition at 80ms with responsive easing; entrance movement switches instantly to its resting value. Toast uses opacity-only keyframes from 0 to 1 at 80ms. Preserve positioning transforms.

**Hard boundaries:** only the two named files initially; no global token retiming, button changes, new dependencies, permanent `will-change`, toast timeout changes, or invented exit animation. Shared positioning transforms must not be overwritten.

**Mechanical checks:** scoped diff contains no `transition: all`, animated `top`, or original 360/500ms ease-in declarations. Verify base resting styles and media overrides; run declared lint/build/tests. Test toast removal independent of entrance completion.

**Runtime/feel checks:** open/close/reopen popovers midway; confirm current-state retargeting where the existing lifecycle permits it. Test placement flips, scroll, stacked toasts, long messages, burst arrivals, and immediate dismissal. Inspect normal speed and slowed playback for layout shifts or competing transforms; use a trace before asserting performance improvement.

**Reduced Motion:** verify no entrance translation/scale remains, placement stays correct, and readable toast content, focus, dismissal controls, and any existing announcements survive. Switching preference while open must not leave intermediate styles.

**Source-drift stop:** stop if selectors differ, tokens are unavailable, transform ownership conflicts, or implementation requires undisclosed lifecycle/positioning edits. Resolve exact owner paths before expanding scope.

### Plan 3 — Make queue settling interruptible without changing sorting semantics

**Scope/current evidence — `src/components/SortableQueue.tsx`:**
```tsx
function onPointerMove(event: PointerEvent) {
  queueRef.current?.style.setProperty("--drag-y", `${event.clientY}px`);
}

function onPointerUp() {
  setDragging(false);
  animateTo(nearestSlot(currentY), { duration: 400 });
}
```

**Target:** direct pointer tracking, a continuous release-to-settle handoff, and immediate re-grab from the displayed position. Preserve `nearestSlot(currentY)` selection; do not introduce momentum-based destination changes.

**Project conventions:** honor `DESIGN.md`’s restrained motion and preserved feedback. Reuse the existing animation mechanism if capable. `--duration-fast: 160ms` and `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)` remain CSS conventions, not guessed options for an unknown JS API.

**Ordered steps**
1. Resolve `animateTo`, duration units, `currentY` updates, `--drag-y` consumers, animated element identity, pointer capture, cancellation, and reorder commit timing. Record exact owner paths before expanding beyond this file.
2. Establish one coordinate contract: pointer positions converted into the existing queue coordinate space, preserving grab offset and scroll behavior. Keep logical position and rendered drag position synchronized.
3. On grab during settling, sample the presentation position before cancelling the prior animation. Start direct tracking there, with no transition lag or snap to the old target.
4. On release, compute the existing nearest-slot target from the latest drag position. Start settling from the displayed position; ensure `setDragging(false)` cannot first reset that position.
5. Use the existing engine’s documented interruptible spring support if available: critically damped, no decorative bounce, starting response target 0.4s, carrying measured release velocity in verified API units. Response is not a fixed completion deadline.
6. If that capability is unavailable, stop for an explicit implementation decision; do not invent spring options for `animateTo`, add a dependency, or assume shortening the tween solves interruption.
7. Handle pointer cancellation, lost capture, unmount, and superseded completion callbacks. Preserve existing commit/cancel semantics and keyboard reorder behavior.

**Hard boundaries:** no changed sort destinations, flick projection, new reorder gestures, rubber-banding, decorative sibling stagger, or business-state commits tied to animation completion. Do not replace the custom-property channel merely on an assumed performance problem.

**Mechanical checks:** test coordinate conversion and grab offset; latest-position release; re-grab mid-settle; stale completion cancellation; cleanup; existing keyboard reorder. Confirm duration/velocity units against the real API and run declared typecheck/lint/tests.

**Runtime/feel checks:** drag slowly and quickly, reverse direction, release near slot boundaries, re-grab during settling, scroll while dragging, and cancel outside the queue. Confirm no handoff jump or input lock. Check actual supported pointer devices; do not infer smoothness from source.

**Reduced Motion:** retain direct, user-controlled tracking; skip autonomous spring travel and place the item at its committed slot immediately. Preserve visible focus, destination/selection indication, and existing reorder announcements. Preference changes during settling must cancel and resolve deterministically.

**Source-drift stop:** stop if the excerpt differs materially, coordinates or animation ownership remain unresolved, or the engine cannot support the specified interruption contract. This plan is gated—not a drop-in API patch.

## 4. Execution order and unverified states

1. **Plan 1:** highest likely interaction frequency and smallest motion change.
2. **Plan 2:** reuse existing tokens; verify positioning ownership before transform edits.
3. **Plan 3:** resolve the gesture/animation contract first, then implement and validate.

**Explicitly unverified:** actual usage frequency; animation/keyframe resolution; effective cascade and Reduced Motion coverage; palette visibility/focus semantics; popover anchoring; toast positioning/stacking; drag coordinates, units, capture, cancellation, and velocity support; browser compatibility; rendering cost; accessibility-tree behavior; and perceived feel. No browser, device, trace, or user validation was performed.
