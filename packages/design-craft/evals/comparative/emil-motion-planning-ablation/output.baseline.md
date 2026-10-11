## 1. Recon summary

- **Stack signals:** TSX components, React-style state/ref usage, CSS custom properties, keyframes, and utility-like arbitrary animation syntax. The CSS-generation pipeline and animation library are not established.
- **Motion locations:** shared styling in `src/styles/motion.css`; component motion in `src/components/CommandPalette.tsx`, `src/components/toast.css`, and `src/components/SortableQueue.tsx`.
- **Existing conventions:** `--duration-fast: 160ms`, `--duration-panel: 240ms`, and `--ease-responsive`. `src/components/Button.css` provides a correct local precedent: explicit `transform` transitions, restrained press feedback, and an 80ms Reduced Motion path.
- **Authority and personality:** `DESIGN.md` requires crisp motion, semantic tokens, visible focus, and preserved feedback under Reduced Motion. For this calm operations surface, motion should explain changes—not make operators wait.
- **Frequency map, inferred rather than measured:** button feedback is likely frequent; palette/popover use likely repeats throughout keyboard workflows; toast frequency depends on events; dragging has continuous pointer updates followed by a discrete release.
- **Evidence level:** static excerpts only. Declared timing and properties are observable; actual visibility, focus behavior, animation playback, frame performance, and perceived latency are not.

## 2. Vetted priorities

Priorities reflect product relevance and code-level risk, not measured incident severity.

| Priority | Finding and evidence | Recommended disposition | Evidence limit |
|---|---|---|---|
| P1 | Palette declares `420ms ease-in`, bypassing existing timing/easing tokens. Its animation class is unconditional; `open` is only shown as a data attribute. | Use state-aware, token-based entrance/exit styling; keep search and focus independent of animation completion. | Keyframes, mounting, visibility rules, and focus management are absent. Cannot conclude that it animates on every toggle or delays input. |
| P1 | Popover uses `transition: all 360ms ease-in` and a centered origin. | Limit transitions to intended properties; use responsive timing. Match direction to placement if displacement is needed. | Actual changing properties and placement logic are unknown. Center origin matters only for relevant transforms. |
| P1 | Toast entrance animates `top` for `500ms ease-in`. | Use a short transform/opacity entrance without changing final positioning. | Animating positional properties creates layout-work risk; positioning and actual rendering cost are unverified. |
| P2 | Queue release specifies a fixed `400` duration; pointer movement writes `--drag-y`. | Keep direct tracking; shorten and make release settling interruptible. | Units/API semantics, coordinate conversion, CSS consumption, and pointer-to-state synchronization are unknown. |
| P1, cross-cutting | Only the button excerpt demonstrates a Reduced Motion path. | Verify coverage and implement explicit alternatives in all three plans. Preserve visible focus and state feedback. | Missing rules in excerpts do not prove the full project lacks coverage. |

## 3. Implementation plans

All checks below are **proposed acceptance checks**, not checks already performed.

### Plan A — Shared overlay motion and command palette

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

**Target behavior**
- Popover: 160ms responsive entrance; palette: 240ms responsive entrance. Use opacity plus at most 4px of translation, without scale.
- Exit, if supported by existing presence handling: 160ms responsive. Do not introduce delayed unmounting solely to obtain an exit.
- Opening, search input, dismissal, focus transfer, and focus return must not await animation completion.
- Reversals should follow the latest open state rather than queue animations.

**Project conventions**
- Reuse the three existing tokens unchanged; use explicit property lists as in the button precedent.
- Preserve the established overlay lifecycle and visible-focus styles.

**Ordered steps**
1. Locate the `palette` keyframes, `.popover` consumers, `data-open` selectors, visibility/presence handling, placement transforms, and focus logic.
2. Establish which element owns positioning versus visual motion. Avoid replacing a placement transform; use an existing inner surface or compatible transform composition.
3. Replace the popover’s `all` transition with explicit opacity/transform transitions using `--duration-fast` and `--ease-responsive`.
4. Replace the palette’s unconditional utility animation with state-aware styling using `--duration-panel` for entry and `--duration-fast` for any existing exit.
5. Define the open visual endpoint as full opacity and zero motion offset. Use placement-aware displacement for popovers; omit translation where direction is ambiguous.
6. Add Reduced Motion overrides and state-transition tests.

**Hard boundaries**
- No token-value changes, unrelated button changes, spring library, new focus trap, or search/data-flow rewrite.
- Never equate `opacity: 0` with hidden/inert; preserve semantic closure and hit-testing behavior.
- Do not animate focus outlines or override positioning transforms.

**Mechanical checks**
- Verify the old utility is removed, generated styles resolve, and neither touched overlay uses `transition: all`.
- Check open/closed endpoints, rapid toggle state handling, existing focus tests, and build/type/style checks.
- Confirm no new input or focus handler waits on a timer or animation event.

**Runtime/feel checks**
- Exercise repeated open/Escape/open sequences, immediate typing, keyboard navigation, and focus return.
- Inspect popovers in supported placements and near viewport edges; look for positional jumps, lingering hit targets, and interrupted exits.

**Reduced Motion**
- Remove translation; use at most 80ms opacity feedback, matching the local reduced-duration precedent.
- Preserve immediate focus and closure semantics, including when the preference changes while open.

**Source-drift stop condition**
- Stop if actual keyframes, lifecycle rules, positioning ownership, or existing Reduced Motion rules differ from the assumed change points. Reconcile the plan before replacing animation ownership.

### Plan B — Toast entrance without positional animation

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

**Target behavior**
- Enter from a restrained 4px upward offset to the existing resting position, with opacity from 0 to 1.
- Use `--duration-fast` and `--ease-responsive`; preserve readable content and existing notification semantics.

**Project conventions**
- Reuse existing tokens and explicit visual properties. Treat the button’s 80ms reduced path as the local timing precedent.

**Ordered steps**
1. Inspect toast positioning, resting `top`, stacking, transform ownership, dismissal, announcements, and lifetime scheduling.
2. Confirm whether the animation currently supplies the final `top: 0`; if so, move that endpoint into the appropriate static positioning rule before removing animated `top`.
3. Replace positional keyframes with translation/opacity keyframes. If stacking already owns transforms, animate a separate existing content surface or reconcile ownership first.
4. Make the base style the visible resting endpoint; avoid retaining a fill mode merely to hold final layout.
5. Add the Reduced Motion override and regression checks for entrance and dismissal.

**Hard boundaries**
- Do not change toast lifetime, announcement urgency, content, stacking order, or dismissal behavior.
- Do not add permanent `will-change`, stagger notifications, or make feedback wait for entrance completion.

**Mechanical checks**
- Confirm entrance keyframes no longer contain `top`; timing/easing reference existing tokens.
- Verify stable endpoints with animation disabled and audit transform/fill-mode interactions.
- Run available style/build checks and existing notification tests.

**Runtime/feel checks**
- Trigger single and burst notifications; dismiss during entrance; inspect stacking and any layout shift.
- Check that text becomes legible promptly and existing announcements remain correct.

**Reduced Motion**
- Use opacity-only entrance for at most 80ms; leave the toast fully visible when animation is disabled.
- Do not shorten its readable lifetime.

**Source-drift stop condition**
- Stop if `top` or transforms participate in stack management, or shared keyframes affect other surfaces. Resolve ownership and impacted consumers before modifying them.

### Plan C — Direct drag tracking and short, interruptible settling

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

**Target behavior**
- Pointer tracking remains direct, without easing or transitions.
- Release settles to the selected slot in the equivalent of `--duration-fast` with responsive easing.
- A new drag cancels the old settle and continues without jumping; committed order is not gated on visual completion.

**Project conventions**
- Reuse semantic timing/easing through the existing CSS-to-JavaScript token bridge, if present.
- Confirm animation API units before translating `160ms`; do not assume `duration` accepts milliseconds.

**Ordered steps**
1. Inspect `animateTo`, the `--drag-y` consumer, coordinate conversion, `currentY` updates, reorder commit logic, pointer cancellation, and keyboard reorder behavior.
2. Verify that the release calculation uses the latest pointer position in slot coordinates; fix any demonstrated mismatch, not an assumed one.
3. Ensure direct manipulation has no CSS transition or competing settle animation.
4. Replace the release duration with the existing fast token through the established integration; map responsive easing to the API’s supported form.
5. Implement or retain cancellation on re-grab, cancellation, and teardown; prevent stale callbacks from changing newer state.
6. Add a runtime Reduced Motion branch and tests for release, interruption, and final ordering.

**Hard boundaries**
- No inertia, bounce, spring dependency, per-pointer-event token reads, or coordinate-system rewrite without evidence.
- Preserve keyboard controls and focus; do not replace them with pointer-only interactions.
- Do not add frame batching or performance claims without examining the existing update path.

**Mechanical checks**
- Verify token conversion/API units, absence of transition lag during tracking, and latest-position targeting.
- Test rapid release/re-grab, cancellation, teardown, final slot/order, and stale completion handling.
- Test Reduced Motion selection and any existing keyboard reorder path.

**Runtime/feel checks**
- Try short/long drags, fast release, re-grab during settling, scrolling, and boundary slots.
- Check for pointer offset jumps, overshoot, delayed order changes, and lost keyboard focus.

**Reduced Motion**
- Retain direct pointer tracking: it communicates user-controlled position.
- Snap immediately on release; preserve final order, focus, and existing non-spatial confirmation.

**Source-drift stop condition**
- Stop if `animateTo` owns business-state commits, the token bridge is absent, or coordinate/transform ownership differs. Resolve that integration explicitly before changing release timing.

## 4. Execution order and unverified states

1. **Plan A:** establish token-based overlay behavior and Reduced Motion coverage for repeated keyboard workflows.
2. **Plan B:** replace toast positional entrance while preserving resting layout and notification semantics.
3. **Plan C:** address settling after inspecting animation and coordinate contracts; this has the most integration uncertainty.

**Explicitly unverified:** actual animation playback; full stylesheet coverage; mounting/unmounting; hidden-state semantics; focus and announcements; keyboard reorder support; pointer capture/cancellation; coordinate correctness; API duration units; performance; interruption behavior; Reduced Motion on real systems; and perceived speed or comfort. No browser, device, accessibility-tree, trace, or user validation was performed.
