## 1. Recon summary

**Diagnosis:** The excerpts mix a crisp, tokenized button precedent with longer, hard-coded transient animations. The highest-leverage work is to align those transitions, make lifecycle ownership explicit, and verify drag continuity before changing its physics.

- **Stack signals:** React-style TSX, CSS transitions/keyframes, an arbitrary-value animation utility, and imperative pointer handling. The utility framework and `animateTo` implementation are unknown.
- **Motion locations:** shared tokens and popover rules in `src/styles/motion.css`; palette animation in `src/components/CommandPalette.tsx`; toast keyframes in `src/components/toast.css`; drag/release logic in `src/components/SortableQueue.tsx`.
- **Existing conventions:** `--duration-fast: 160ms`, `--duration-panel: 240ms`, and `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)`. That curve is strongly ease-out-like, not ease-in-out.
- **Local precedent:** `src/components/Button.css` explicitly transitions only `transform`, uses semantic tokens, and provides an 80ms Reduced Motion branch. Preserve it; do not treat shorter spatial animation as the universal accessibility solution.
- **Personality:** calm, utilitarian, immediate; motion should explain state changes, not require users to wait for them.
- **Frequency map, inferred rather than measured:** button feedback and command invocation are likely frequent; popovers recur during navigation; toast frequency depends on workflows; dragging is continuous while active, but session frequency is unknown.
- **Evidence:** supplied static excerpts only. No full-file inspection, commit identity, computed styles, runtime measurements, accessibility-tree inspection, or user validation. `DESIGN.md` authority is supplied by the brief, not independently inspected.

## 2. Vetted priorities

P1 denotes a high-priority implementation investigation, not a demonstrated task blocker. No P0 is supported.

| ID / priority | Source proof | Finding and runtime unknown | Smallest correction / acceptance |
|---|---|---|---|
| F1 / P1 | Palette has constant `animate-[palette_420ms_ease-in_both]`; `open` appears only in `data-open`. | The excerpt does not connect animation lifecycle to open/close. Other selectors or mounting behavior may do so; repeated animation and focus failure are not established. | Tie visual states to the actual lifecycle, use fast tokenized entry, and keep input/focus independent of completion. Verify reopen, Escape, and rapid toggling. |
| F2 / P1 investigation | Queue writes `event.clientY`; release uses `nearestSlot(currentY)` and `{ duration: 400 }`. | Coordinate conversion, current-value synchronization, capture, cancellation, and interruption are not shown. Neither broken tracking nor missing support is proven. | Establish one position owner and interruptible settling; preserve nearest-slot semantics. Verify grab offset, scrolling, cancellation, and re-grab. |
| F3 / P2 | Popover uses `transition: all 360ms ease-in` and centered origin. | Broad transition ownership and timing diverge from local conventions. Center origin is only wrong if placement is anchored and scale is used. | Explicit property allowlist, existing timing/easing tokens, and placement-derived origin where applicable. Verify every supported placement. |
| F4 / P2 | Toast animates `top: -24px → 0` over `500ms ease-in`. | Layout-property animation is a potential cost; positioning mode and actual frame cost are unknown. | Replace entry travel with transform plus opacity, preserve the final position, and use fast tokens. Verify stacking and collect a trace before claiming performance improvement. |
| F5 / P2 | Only the button excerpt includes a Reduced Motion branch. | Coverage for other surfaces is unproven, not demonstrably absent product-wide. | Explicit non-spatial transient feedback and immediate drag settling under reduced motion; verify both initial preference and preference changes. |

**Set aside:** button redesign, additional success flourishes, new animation dependencies, and momentum-based slot selection. None has sufficient evidence or product justification.

## 3. Implementation plans

All checks below are **future acceptance work**, not completed validation. Before each plan, inspect the named full files, applicable instructions, `DESIGN.md`, consumers, and package scripts. Record a baseline revision; do not invent build commands or animation APIs.

### Plan A — Tokenized, state-owned popovers and command palette
**Covers:** F1, F3, and overlay coverage of F5.

**Exact current evidence:**
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
**Target / conventions:** immediate operability with a 160ms entry using `--duration-fast` and `--ease-responsive`; no animation of search-result updates. Preserve visible focus and established overlay semantics.
1. Locate `palette` keyframes, animation utility configuration, `data-open` consumers, mount/unmount owner, and popover placement/state rules. Determine whether these surfaces share styling; do not assume they do.
2. Keep shared token values unchanged. Replace popover `all` with `opacity, transform` only where those properties actually change; omit transform if no spatial state exists. Use fast duration and responsive easing.
3. For scaled anchored popovers, derive origin from resolved placement, including flips. Preserve centered origin for a genuinely centered surface.
4. Replace the palette’s unconditional animation utility with explicit open/closed styling. Use opacity-only entry; close without an animated delay. Reopening must start from the currently displayed opacity rather than restarting a keyframe.
5. Ensure the closed surface is not interactive or focusable through the existing lifecycle owner. Focus entry, Escape handling, and focus return must not depend on `animationend`.
6. Add scoped Reduced Motion styling: remove entry/exit translation and scale; retain an 80ms opacity transition, static open state, and immediate visible focus.

**Hard boundaries:** no token-value changes, button edits, new dependencies, result-row choreography, overlay primitive migration, or search-behavior changes. If lifecycle ownership lies elsewhere, identify the exact additional file and approve scope before editing.
**Mechanical checks:** run declared typecheck/lint/build and relevant tests; verify generated CSS contains the intended selectors; test closed-state focus exclusion, rapid reopen, and completion without animation events.
**Runtime/feel checks:** keyboard invocation → immediate typing; Escape and repeated toggles during entry; visible focus and return; all actual anchor placements; reduced motion enabled before opening and toggled while open.
**Source-drift stop:** stop if token values, palette keyframes, `open` ownership, popover placement contract, or the cited utility/rule differ materially. Reconcile existing global Reduced Motion rules before adding overrides.

### Plan B — Short, non-layout toast entry
**Covers:** F4 and toast coverage of F5.

**Exact current evidence:**
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
**Target / conventions:** a short arrival cue without delaying reading, announcements, dismissal, or actions. Use `--duration-fast` and `--ease-responsive`; preserve existing toast placement and semantics.
1. Inspect positioning mode, base `top`, transform ownership, stacked-toast rules, dismissal lifecycle, and any existing accessibility overrides.
2. Remove `top` from keyframes. Where the existing `top: 0` endpoint controls positioning, move that resting value into the appropriate base rule; do not add positioning or alter layout for statically positioned toasts.
3. Use `translateY(-8px) → translateY(0)` plus `opacity: 0 → 1` over the fast token. Explicitly retain final opacity/transform in the base state so animation fill is not responsible for resting geometry.
4. Preserve any existing transform composition. If positioning already owns transform, stop for an explicit composition decision rather than overwriting it.
5. Under Reduced Motion, use separate opacity-only entry keyframes over 80ms; remove decorative entry displacement without removing transforms required for positioning.

**Hard boundaries:** changes confined to `src/components/toast.css` unless scope is explicitly reopened. No lifetime changes, announcement changes, new wrappers/dependencies, bounce, exit animation, or stack-reordering feature.
**Mechanical checks:** verify `top` is absent from entry keyframes; check token availability, base endpoint, cascade, and Reduced Motion keyframes; run declared CSS/build checks and relevant toast tests.
**Runtime/feel checks:** single toast, bursts, multiline content, actionable toast, immediate dismissal, and existing exits; confirm no endpoint jump or positioning regression. Compare baseline/changed traces before making any frame-cost claim.
**Source-drift stop:** stop if the current keyframes, positioning contract, transform owner, or token availability differ from these prerequisites. Reconcile an existing reduced-motion implementation rather than layering conflicting animation rules.

### Plan C — Explicit drag ownership and interruptible nearest-slot settle
**Covers:** F2 and drag coverage of F5. This plan has a required API/coordinate discovery gate.

**Exact current evidence:**
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
**Target / conventions:** direct 1:1 dragging with preserved grab offset, followed by a restrained settle from the displayed position. Keep `nearestSlot(currentY)` selection semantics; target 160ms settling using existing tokens where the API supports them.
1. Resolve the `--drag-y` consumer, `currentY` writer, pointer-down/cancel handlers, scrolling coordinate system, and complete `animateTo` signature. Record duration units and cancellation/current-value capabilities.
2. Establish a single coordinate space in CSS pixels. Convert pointer coordinates relative to the drag container, including scrolling, and preserve initial grab offset. Synchronize the displayed position and release position from one owner.
3. Verify or add pointer capture and cancellation cleanup. During direct dragging, disable interpolation on the pointer-owned translation; do not add smoothing lag.
4. On re-grab, capture the current displayed position before cancelling settlement and initialize the new grab offset from it. On release, preserve the displayed transform across `setDragging(false)`, then settle to the nearest valid slot.
5. Replace the hard-coded 400 only through the existing animation API and established CSS-token bridge. If no bridge exists, explicitly scope a local conversion with verified units rather than inventing helper capabilities or duplicating token values.
6. Inspect velocity support separately: measure release velocity in CSS px/s if needed; hand it off only through a verified API with bounded, non-overshooting behavior. If unsupported, retain a positional settle and record velocity continuity as unverified.
7. Under Reduced Motion, retain direct pointer tracking, immediately commit the nearest slot on release, and preserve static selection/insertion feedback and visible keyboard focus. Preference changes must cancel active decorative settling.

**Hard boundaries:** no animation-library migration, new dependency, bounce, input lock, persistence change, or keyboard reorder redesign. Do not silently expand beyond `src/components/SortableQueue.tsx` and identified motion consumers.
**Projection gate:** a future momentum proposal would compute `clamp(position + velocity × horizonSeconds, validBounds)` in CSS pixels before nearest-slot selection. It requires separate authorization; this plan does **not** replace nearest-current-position targeting.
**Mechanical checks:** run declared type/lint/tests; add deterministic tests for coordinate conversion, grab offset, nearest-slot bounds, stale-position prevention, cancellation, re-grab, and zero-animation reduced-motion completion.
**Runtime/feel checks:** slow/fast drags, container scrolling, out-of-bounds pointer movement, first/last slots, release then immediate re-grab, cancellation, and existing keyboard reorder/focus behavior. Record observations; do not infer smoothness from transform usage.
**Source-drift stop:** stop if `--drag-y` is already converted downstream, `currentY` has a different meaning, slot selection differs, or `animateTo` cannot expose/cancel its current presentation. Resolve ownership/API scope before editing.

## 4. Execution order and unverified states

1. **Plan A first:** highest likely keyboard-workflow leverage; establishes restrained transient-state conventions.
2. **Plan B next:** bounded CSS change with explicit geometry and accessibility checks.
3. **Plan C discovery in parallel, implementation after its gate:** elevate immediately if runtime checks reveal lost input, jumps, or incorrect reorder outcomes.

**Explicitly unverified:** actual invocation frequency; final computed timings; palette visibility and focus lifecycle; popover anchoring/flipping; toast positioning, stacking and announcement timing; drag coordinate ownership, capture, velocity and cancellation; Reduced Motion coverage and preference changes; frame pacing, compositing, device behavior, and perceived feel. No files were edited or plans written to disk.
