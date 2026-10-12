## 1. Recon summary

- **Stack signals:** TSX components, CSS transitions/keyframes, an arbitrary animation utility, and imperative pointer handling. React-style code is visible; utility tooling and the implementation/library behind `animateTo` are unknown.
- **Motion locations:** shared values and popover rules in `src/styles/motion.css`; component-local palette, toast, queue, and button motion.
- **Existing conventions:** `--duration-fast: 160ms`, `--duration-panel: 240ms`, and `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)`. `src/components/Button.css` correctly demonstrates an explicit property, semantic tokens, and an 80ms Reduced Motion override. Preserve it.
- **Product personality:** calm, crisp, task-first. Motion should explain state changes, not delay focus, typing, navigation, or repeated actions.
- **Frequency map — inferred, not measured:** palette and button interactions are likely frequent; popovers recurrent; toasts event-dependent; queue sorting workflow-dependent. No daily counts are established.
- **Evidence level:** static excerpts only. `DESIGN.md` requirements are supplied context, not independently inspected. No full stylesheet cascade, animation definitions, component lifecycle, or runtime behavior is established.

## 2. Vetted priorities

Priority reflects implementation leverage and product fit, not measured runtime severity.

| # | Priority | Location | Supported finding | Recommended action |
|---|---|---|---|---|
| 1 | High | `src/components/CommandPalette.tsx` | The wrapper declares an unconditional `420ms ease-in` animation utility, separate from `data-open`. Generated CSS and keyframes are unavailable; delayed input or animation replay is not proven. | Remove decorative wrapper animation; keep opening, closing, and keyboard feedback immediate. |
| 2 | High | `src/styles/motion.css` | `.popover` uses `transition: all 360ms ease-in`, bypassing the existing motion tokens and allowing unintended properties to transition. | Explicitly transition only supported visual properties at the fast token and responsive easing. |
| 3 | Medium | `src/components/toast.css` | Entrance animates layout-affecting `top` over `500ms ease-in`. Actual layout work and dropped frames are unmeasured. | Preserve the entrance cue using transform/opacity and existing tokens. |
| 4 | Medium | `src/components/SortableQueue.tsx` | Release requests a fixed 400ms animation after clearing dragging state. Cancellation, release-position continuity, and `currentY` freshness are not shown. | Trace ownership first; implement a short, interruptible settle from the current visual position. |
| 5 | Medium | Palette, popover, toast, queue excerpts | No local Reduced Motion handling is shown for these surfaces. A global or library-level path may exist. | Verify effective coverage, then add targeted alternatives that retain state and focus feedback. |

**Not promoted to findings:** centered popover origin is only problematic if this is a trigger-anchored scaling surface. The CSS-variable write alone does not prove descendant invalidation or poor performance. No additive animation opportunities are justified by this evidence.

## 3. Implementation plans

### Plan 1 — Make the command palette immediate

**Scope and current excerpt — `src/components/CommandPalette.tsx`:**
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

**Target behavior:** remove the wrapper animation. Opening, closing, typing, and selection should not wait for decorative motion. Preserve existing visibility semantics and focus behavior; this excerpt does not establish either.

**Project conventions:** follow the supplied `DESIGN.md` requirements for crisp feedback and visible focus. Existing shared values are 160ms/240ms with `cubic-bezier(0.23, 1, 0.32, 1)`, but this high-frequency surface needs no replacement animation.

**Ordered steps:**
1. Locate the generated utility, `palette` keyframes, `[data-open]` rules, and mount/unmount ownership. Verify that keyframes do not provide the only closed-state hiding mechanism.
2. Remove `className="animate-[palette_420ms_ease-in_both]"`; preserve `data-open={open}`, children, and unrelated attributes.
3. Confirm visibility remains state-driven. If removal exposes hidden content or changes interaction semantics, stop and scope that prerequisite separately.
4. Remove an orphaned keyframe only if its exact defining file and lack of other consumers are confirmed; otherwise leave it untouched.

**Hard boundaries:** no new animation library, result stagger, focus-management rewrite, keyboard-binding change, or arbitrary close delay. Do not infer that `data-open` alone hides content.

**Mechanical checks:** review the diff for the utility removal; inspect remaining selectors for closed-state behavior and hidden-content focusability. Run existing typecheck/lint/component-test scripts after discovering their actual names; no script names are known here.

**Runtime/feel checks — future validation:** repeatedly open/close with the keyboard; type immediately on opening; navigate results; press Escape; verify focus restoration, visible focus, and no flash of closed content. Test rapid reversal and populated/empty results.

**Reduced Motion:** the same immediate state change applies. Preserve focus indicators, selection styling, and result feedback rather than substituting another animation.

**Source-drift stop:** the supplied excerpt is the baseline; no commit is known. Stop if the utility, wrapper lifecycle, or visibility ownership differs, or if safe removal requires changes in unidentified files.

### Plan 2 — Align popover and toast motion with existing tokens

**Scope and current excerpts:**
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

**Target behavior:** a popover responds over 160ms; a toast enters over 240ms, preserving the existing 24px displacement without animating `top`. These are initial acceptance targets, not validated feel measurements.

**Project conventions:** use existing tokens unchanged. Match `src/components/Button.css`’s explicit-property pattern and local `@media (prefers-reduced-motion: reduce)` treatment; use its 80ms duration for reduced opacity feedback.

**Ordered steps:**
1. Inspect complete popover open/closed rules, placement transforms, toast positioning, and any existing Reduced Motion overrides before editing.
2. Replace the popover transition with:
   ```css
   transition: transform var(--duration-fast) var(--ease-responsive),
               opacity var(--duration-fast) var(--ease-responsive);
   ```
   Include `transform` only if it belongs to the visual entrance, not positioning. If positioning owns it, use opacity alone; do not make anchor tracking lag.
3. Preserve `transform-origin: center` unless trigger anchoring and scaling are confirmed. If confirmed, use the positioning system’s documented origin value after identifying it; do not invent a library-specific variable.
4. Keep the toast’s final layout position equivalent to `top: 0`; change entrance frames to `translateY(-24px)`/opacity 0 → `translateY(0)`/opacity 1. Use `animation: toast-enter var(--duration-panel) var(--ease-responsive) forwards`.
5. Verify toast transforms are not already owned by stacking, positioning, or dismissal. If they are, stop rather than overwrite them or introduce unscoped wrapper markup.
6. Add reduced-motion rules: popover opacity-only transition at 80ms with `var(--ease-responsive)`; toast opacity-only keyframes at 80ms with that easing. Any popover entrance displacement/scale must become its final visual value immediately, preserving positioning transforms.

**Hard boundaries:** no global reset, token retuning, dependency, new exit choreography, toast lifetime change, or button changes. Retain toast entry keyframes unless actual lifecycle requirements demonstrate a need for retargetable transitions.

**Mechanical checks:** confirm `.popover` no longer uses `transition: all`; toast entrance no longer animates `top`; final positioning is preserved; all normal durations/easing reference existing tokens. Verify reduced rules win the cascade. Run available CSS lint and component tests using discovered scripts.

**Runtime/feel checks — future validation:** open/close popovers rapidly and move/scroll their anchors; verify no placement lag, origin mismatch, or lost focus. Trigger single and stacked toasts, including dismissal during entry; inspect normal speed and slowed playback for jumps. Profile before making performance claims.

**Reduced Motion:** no decorative travel or scale; brief opacity feedback remains. Toast content, announcements, lifetime, and popover focus behavior remain unchanged.

**Source-drift stop:** stop if these declarations differ, token values changed, transforms have competing owners, or toast positioning cannot preserve the existing final layout within these two files. Resolve ownership before applying the proposed declarations.

### Plan 3 — Make queue release continuous and interruptible

**Scope and current excerpt — `src/components/SortableQueue.tsx`:**
```tsx
function onPointerMove(event: PointerEvent) {
  queueRef.current?.style.setProperty("--drag-y", `${event.clientY}px`);
}

function onPointerUp() {
  setDragging(false);
  animateTo(nearestSlot(currentY), { duration: 400 });
}
```

**Target behavior:** maintain direct pointer tracking; settle from the current rendered offset to the selected slot using `--duration-fast` (currently 160ms) and `--ease-responsive` (`cubic-bezier(0.23, 1, 0.32, 1)`). A new drag must take ownership immediately without snapping to a stale start or destination.

**Project conventions:** consume shared motion values through an existing CSS/JS bridge if available. Preserve the button precedent’s explicit transform ownership. Do not introduce a parallel duration scale or a speculative spring dependency.

**Ordered steps:**
1. Trace `currentY`, `--drag-y` consumers, `nearestSlot`, `setDragging`, and `animateTo`. Establish viewport versus local coordinates, scroll handling, duration units, transform ownership, and cancellation capabilities.
2. Ensure release reads the latest drag sample in the same coordinate space as slot selection. Capture the current rendered position before state changes can reset drag styling.
3. Start settling from that position; apply the shared fast duration and responsive easing through the verified API. Keep visual-position ownership until completion; commit logical order once through the existing mechanism.
4. On a new pointer-down, cancel the active settle while retaining its rendered position, then rebase the grab offset there. Ignore stale completion callbacks.
5. Preserve or complete existing pointer-cancel cleanup without inventing reorder semantics. If cancellation, current-position sampling, or token access requires unknown modules, stop and identify that prerequisite first.

**Hard boundaries:** preserve slot-selection rules, logical ordering, pointer capture, scrolling, and keyboard sorting. No new inertia, bounce, dismissal threshold, or unrelated event-system rewrite. Do not replace the CSS variable solely on an unmeasured performance assumption.

**Mechanical checks:** verify API duration units and easing syntax. Add tests for latest-sample release, coordinate conversion, re-grab during settle, cancellation, and stale completion callbacks using the existing test setup. Confirm only one motion owner writes the relevant transform.

**Runtime/feel checks — future validation:** release slowly and quickly; re-grab immediately and midway through settling; sort in a scrolled queue; cancel a drag. Check for release jumps, pointer-offset changes, double commits, and stale destination snaps. Validate keyboard sorting separately.

**Reduced Motion:** retain direct manipulation while the pointer is held; snap to the selected slot on release with no animated travel. Preserve destination/selection styling, focus, and existing reorder announcements. Cancel an active settle if the preference changes to reduce.

**Source-drift stop:** stop if handlers differ, coordinate spaces remain ambiguous, or `animateTo` cannot support cancellation/current-position handoff. Its missing implementation prevents prescribing a trustworthy drop-in API call from these excerpts alone.

## 4. Execution order and remaining uncertainty

1. **Plan 1:** smallest likely change, highest expected keyboard-workflow leverage.
2. **Plan 2:** restore token consistency and explicit property ownership.
3. **Plan 3:** first resolve the unknown animation and coordinate contracts; do not ship a duration-only fix as a continuity fix.

**Explicitly unverified:** actual interaction frequency; generated utility CSS; palette visibility/focus lifecycle; popover placement/origin; toast stacking and dismissal; queue velocity, coordinates, and cancellation; global Reduced Motion coverage; accessibility semantics; browser compatibility; frame performance; and subjective feel. All runtime checks above are acceptance work to perform, not validation already completed.
