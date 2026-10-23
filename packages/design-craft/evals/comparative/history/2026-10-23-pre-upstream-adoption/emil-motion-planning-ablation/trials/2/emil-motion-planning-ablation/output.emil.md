## 1. Recon summary

- **Stack signals:** React-style TSX, CSS transitions/keyframes, a utility-style arbitrary animation class, and imperative pointer handling. A utility framework and the implementation of `animateTo` are not confirmed.
- **Motion locations:** shared tokens and popovers in `src/styles/motion.css`; palette animation in `src/components/CommandPalette.tsx`; toast entrance in `src/components/toast.css`; drag/release logic in `src/components/SortableQueue.tsx`.
- **Existing conventions:** `--duration-fast: 160ms`, `--duration-panel: 240ms`, and `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)`. `src/components/Button.css` already uses a property-specific transition, restrained press feedback, and an 80ms Reduced Motion override. Preserve it.
- **Authority/personality:** the supplied description of `DESIGN.md` calls for crisp, token-based motion, visible focus, and Reduced Motion feedback. This console needs quiet causality, not decorative choreography.
- **Frequency map, inferred rather than measured:** palette and button interactions likely recur frequently; popovers recur during operational workflows; toast frequency depends on events; queue sorting depends on role. No daily counts are established.
- **Evidence level:** static excerpts only. Missing keyframes, mounting behavior, positioning logic, animation helpers, and global overrides limit conclusions. No runtime or accessibility validation was performed.

## 2. Vetted priorities

Priorities express implementation leverage, not measured user impact.

| Priority | Location | Supported finding | Recommended action |
|---|---|---|---|
| P1 | `src/components/CommandPalette.tsx` | The class declares a 420ms ease-in animation independently of `open`. Its keyframes and lifecycle are absent; replay on every toggle is not established. | Remove decorative palette animation; preserve immediate visibility, focus, and keyboard feedback. |
| P1 | `src/styles/motion.css` | `.popover` declares `transition: all 360ms ease-in`, overriding the available timing vocabulary and allowing unintended property transitions. | Restrict properties and use the 160ms responsive tokens. |
| P1 | `src/components/toast.css` | Entrance animates layout-position property `top` over 500ms with ease-in. Actual layout cost depends on positioning; dropped frames are not established. | Replace the positional animation with transform/opacity using the 240ms panel token. |
| P2 | `src/components/SortableQueue.tsx` | Release requests a fixed 400ms animation. Cancellation, continuity, velocity handling, and `currentY` freshness are not shown. | Shorten settling and explicitly implement interruption-safe ownership, after inspecting the helper. |
| P2 | All four target surfaces | No Reduced Motion handling appears in their excerpts; only the button demonstrates it. Global coverage may exist. | Verify effective coverage; add local paths where absent, preserving nonspatial feedback. |

**Not promoted to findings:** centered popover origin is only wrong if an anchored scaling reveal exists; CSS-variable drag writes alone do not establish expensive descendant updates or jank. No additive animation is justified by this evidence.

## 3. Implementation plans

### Plan 1 — Make command-palette access immediate

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

**Target:** no animated delay on palette opening, closing, searching, or keyboard navigation. Visibility and focus change in the same interaction cycle; results do not stagger.

**Project conventions:** honor the supplied `DESIGN.md` requirements for crisp feedback and visible focus. Existing tokens in `src/styles/motion.css` are 160ms/240ms and `cubic-bezier(0.23, 1, 0.32, 1)`; this high-frequency surface deliberately needs no replacement animation.

**Ordered steps**
1. Inspect the complete component, `palette` keyframes, `[data-open]` rules, and its mounting/focus owner. Determine whether animation currently supplies visibility or hiding.
2. Remove `animate-[palette_420ms_ease-in_both]`; remove the empty `className` if appropriate. Preserve `data-open`, content, and component API.
3. Keep visibility under the established open-state mechanism. If animation owns visibility, stop and expand the plan before removing it.
4. Verify the existing focus owner focuses the input on open, restores focus on close, and excludes closed content from navigation. Do not introduce a second focus manager.

**Hard boundaries:** no new dependency, search behavior changes, result staggering, focus-outline suppression, or speculative dialog rewrite. Do not remove shared keyframes without proving they are unused.

**Mechanical checks:** confirm the palette has no animation class or inherited open/close motion; run existing typecheck/lint and palette tests using documented project scripts. Add regression coverage for open/close visibility and focus if the existing harness supports it; do not invent script names.

**Runtime/feel checks, to perform:** repeatedly open/type/Escape/reopen with the keyboard. Input must accept typing immediately, focus must remain visible, and closed results must not remain interactive. Check pointer opening too.

**Reduced Motion:** use the same immediate path. Visible content, focus, selection, and result changes provide feedback without travel or fades.

**Source-drift stop:** stop if the excerpt no longer matches, the keyframes have functional responsibilities, or visibility/focus changes require files beyond this component. Report the newly discovered owner and revise scope first.

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

**Target:** popover transitions use an explicit opacity/transform allowlist at 160ms; toast enters from `translateY(-24px)` to `translateY(0)` with opacity 0→1 over 240ms. Both use `var(--ease-responsive)`. Preserve toast final placement.

**Project conventions:** reuse the three existing tokens without renaming or changing their global values. Follow `src/components/Button.css`: property-specific transitions and a local 80ms Reduced Motion override. Leave button behavior unchanged.

**Ordered steps**
1. Inspect popover state selectors and placement ownership, toast positioning/stacking/dismissal, and effective Reduced Motion overrides. Confirm transform ownership before editing.
2. Replace popover `transition: all 360ms ease-in` with `transition: opacity var(--duration-fast) var(--ease-responsive), transform var(--duration-fast) var(--ease-responsive)`. If transform belongs to placement rather than reveal, omit it instead of animating positioning updates.
3. Retain current popover visual endpoints. Do not add scaling merely to justify changing `transform-origin`; change origin only in a separately scoped anchored-scale fix.
4. Replace toast `top` keyframes with the target transform/opacity endpoints; use `animation: toast-enter var(--duration-panel) var(--ease-responsive) forwards`.
5. Preserve the old final layout position statically: if positioned `top: 0` was supplied only by the animation, establish it in the base rule. Stop if this conflicts with the stack positioner.
6. Add local Reduced Motion rules: popover transitions opacity only for 80ms; toast uses an opacity-only 0→1 entrance for 80ms with the same easing and fill behavior. Keep final placement available independently of animation.

**Hard boundaries:** only the two listed CSS files; no new library, global token changes, stacking rewrite, additional stagger, or guessed placement-library variables. Do not overwrite transforms used by a positioner, drag, or stack.

**Mechanical checks:** inspect the diff for removal of `transition: all` and animated `top`; verify token references and local media-query coverage. Run existing stylesheet/build checks and relevant component tests. Confirm no positioning rule relies on removed animation output.

**Runtime/feel checks, to perform:** open/close/reopen popovers rapidly; test all supported placements and repositioning. Check single and stacked toast arrivals and dismissal during entry. At normal speed and slowed playback, look for jumps, overwritten transforms, focus loss, or invisible interactive elements.

**Reduced Motion:** no animated positional entrance; 80ms opacity feedback remains. Verify computed behavior with the preference enabled, including any existing global overrides.

**Source-drift stop:** stop if excerpts differ, transform ownership conflicts, keyframes are shared, or mount/dismiss behavior requires component changes. Do not silently replace the lifecycle with a new presence system.

### Plan 3 — Make queue release short and interruptible

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

**Target:** direct pointer tracking remains unlagged. Release settles to the existing nearest-slot target over 160ms using `cubic-bezier(0.23, 1, 0.32, 1)`. A new drag interrupts settling from its current rendered position, without snapping back. This is a bounded settle, not an inertial fling.

**Project conventions:** resolve `--duration-fast` and `--ease-responsive` from the established token mechanism; their supplied values are 160ms and the curve above. Follow existing animation APIs and Reduced Motion preference infrastructure; do not guess `animateTo` options.

**Ordered steps**
1. Inspect `animateTo`, pointer-down/cancel handling, `currentY` updates, `--drag-y` consumers, and coordinate conversion. Identify animation ownership, cancellation support, and timing units.
2. If the helper already supports easing and cancellation, retain its API and replace the 400ms release with the token-based 160ms settle. Otherwise stop and scope the helper change explicitly.
3. Ensure release reads the latest drag position in the same coordinate system as `nearestSlot`. Preserve existing slot selection and commit semantics.
4. On re-grab, capture the current visual offset, cancel the prior settle, and initialize drag offset from that position. Prevent obsolete completion callbacks from committing stale state.
5. Ensure pointer cancellation/unmount clears animation ownership. Keep pointer tracking free of CSS easing; do not alter the custom-property approach without evidence of a problem.
6. Branch on the current Reduced Motion preference: commit the target immediately without a settling tween, while preserving direct manipulation and existing destination/selection feedback.

**Hard boundaries:** no physics dependency, invented spring parameters, fling behavior, reorder algorithm changes, or speculative performance rewrite. No blanket removal of keyboard focus or status feedback.

**Mechanical checks:** use existing tests to cover latest-position release, coordinate conversion, cancellation, stale completion prevention, rapid re-grab, and immediate Reduced Motion completion. Verify duration units and absence of a transition that eases pointer tracking; run documented typecheck/lint scripts.

**Runtime/feel checks, to perform:** drag slowly and quickly, release near slot boundaries, re-grab during settling, cancel a drag, and test scrolling during drag. Confirm stable pointer offset, one final order commit, visible destination feedback, and unchanged keyboard reordering if supported.

**Reduced Motion:** pointer-driven motion remains under user control; autonomous settling is removed. Final order and visible focus/selection must still communicate the result. If existing feedback is insufficient, stop and scope that work rather than adding an unreviewed effect.

**Source-drift stop:** stop if the excerpt differs, timing units are not milliseconds, the helper lacks required controls, coordinate ownership is unclear, or implementation requires edits outside this file.

## 4. Execution order and unverified states

1. **Plan 1:** highest likely frequency, smallest intended change.
2. **Plan 2:** shared timing consistency and removal of layout-position animation.
3. **Plan 3:** execute after resolving animation-helper and coordinate contracts; it has the largest evidence gap.

**Explicitly unverified:** actual usage frequency; compiled styles and token availability; palette keyframes and focus lifecycle; popover anchoring; toast stacking and positioning; drag helper semantics, coordinates, and interruption behavior; effective Reduced Motion coverage; assistive-technology behavior; browser/device performance and subjective feel.

No files were edited or plans written to disk. All runtime checks above are future acceptance checks, not completed validation.
