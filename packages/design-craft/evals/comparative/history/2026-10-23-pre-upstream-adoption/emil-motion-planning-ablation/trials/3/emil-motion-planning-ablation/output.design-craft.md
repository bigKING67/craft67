## 1. Recon summary

**Diagnosis:** The supplied motion configuration diverges from the console’s crisp, token-driven convention; prioritize keyboard throughput, explicit animation ownership, and feedback-preserving Reduced Motion before adding effects.

- **Stack signals:** React-style TSX, CSS transitions/keyframes, an arbitrary animation utility class, and imperative pointer handlers. The utility compiler and `animateTo` implementation are unknown.
- **Motion locations:** shared tokens/popover rules in `src/styles/motion.css`; palette animation in `src/components/CommandPalette.tsx`; toast keyframes in `src/components/toast.css`; drag/release logic in `src/components/SortableQueue.tsx`.
- **Existing conventions:** `--duration-fast: 160ms`, `--duration-panel: 240ms`, and `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)`—a strong ease-out-like response. `src/components/Button.css` demonstrates explicit property ownership, token reuse, and an 80ms Reduced Motion override; leave it unchanged.
- **Personality:** calm, precise, workday utility. Motion should explain state changes, not become a prerequisite for interaction.
- **Frequency map:** palette and buttons are likely high-frequency keyboard/command surfaces; popovers and toasts recur during operations; queue dragging is continuous while active. Actual usage rates are unknown.
- **Evidence level:** supplied static excerpts only. `DESIGN.md` authority is supplied as a requirement, not independently inspected. No commit identifier, full component lifecycle, runtime behavior, or validation results are available.

## 2. Vetted priorities

Priorities indicate implementation attention, not confirmed runtime failures. No P0 is established.

| ID / priority | Static evidence and location | Finding / runtime unknown | Smallest safe correction and acceptance |
|---|---|---|---|
| F1 / P1 | `CommandPalette.tsx`: unconditional `animate-[palette_420ms_ease-in_both]`; `data-open={open}` | Long, slow-start configuration mismatches frequent command use. Keyframes, visibility ownership, and whether toggles replay it are unknown. | Remove decorative palette animation; make open/closed feedback immediate without delaying focus or input. Verify rapid keyboard toggles and closed-state exclusion. |
| F2 / P1 verification gate | Only `Button.css` shows a Reduced Motion branch | No preference handling is demonstrated for the other supplied motion. This does **not** prove global handling is absent. | Inspect effective preference handling before edits; supply explicit non-spatial/static feedback paths where missing. Verify normal and reduced settings. |
| F3 / P2 | `motion.css`: `transition: all 360ms ease-in`; `transform-origin: center` | Broad transition ownership and token divergence are proven. Center origin is only a concern if scaling an anchored surface. Actual changed properties are unknown. | Restrict ownership and reuse fast/responsive tokens; resolve anchoring before retaining any scale. Verify positioning remains immediate. |
| F4 / P2 | `toast.css`: animated `top`, opacity, `500ms ease-in forwards` | Layout-property animation and timing divergence are proven; layout cost depends on positioning and runtime. Dropped frames are not established. | Replace `top` animation with owned translation/opacity and fast/responsive tokens. Verify stacking, dismissal, and final position. |
| F5 / P1 investigation gate | `SortableQueue.tsx`: raw `event.clientY`; `nearestSlot(currentY)`; `duration: 400` | Coordinate conversion, freshness of `currentY`, capture, cancellation, and presentation-value interruption are not shown. No jump or stale target is proven. | Establish a single position owner and interruptible release while preserving nearest-slot semantics. Verify off-center grabs, re-grabs, and cancellation. |

**Vetted out:** no claim that `transition: all` necessarily causes layout; no claim that transforms guarantee compositing; no confirmed missing pointer capture; no automatic mandate for a spring library, momentum targeting, or centered-origin replacement.

## 3. Implementation plans

Each plan is proposed, independently scoped, and based only on the supplied excerpts. Before implementation, inspect current full files, applicable instructions, `DESIGN.md`, token imports, and existing test/build scripts. No edits or checks have been performed here.

### Plan A — Immediate command access and bounded popover feedback
**Covers:** F1, F3, and the overlay portion of F2.

**Exact paths/current excerpts**
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
**Target/conventions:** palette state changes immediately, with no travel, scale, stagger, or animation-gated input. Popovers use opacity-only feedback over `var(--duration-fast)` with `var(--ease-responsive)`; positioning changes remain immediate. Preserve semantic tokens and visible focus.

**Ordered steps**
1. Locate palette keyframes, `data-open` selectors, mounting rules, focus management, and popover open/closed selectors. Determine whether `.popover` also applies to the palette; palette must not inherit a new fade.
2. Remove the palette’s arbitrary animation class. Retain its state attribute and existing proven visibility/focus contract; if that contract is absent, stop for a functional accessibility scope decision.
3. Replace the popover transition with `transition: opacity var(--duration-fast) var(--ease-responsive)`. Preserve positioning transforms, but remove decorative state scale/travel only after identifying their owner.
4. Do not add an origin variable or guess trigger geometry. With opacity-only motion, origin is irrelevant; preserve static positioning behavior.
5. Add a scoped Reduced Motion opacity duration of `80ms`; palette remains immediate. Ensure closed content cannot receive input or focus while visually disappearing.

**Hard boundaries:** only the two named files and directly identified existing overlay state rules; stop for approval if another owner requires edits. No token-value changes, primitive migration, new dependency, result-row animation, or button changes.

**Mechanical checks:** run actual project type/lint/build scripts; inspect generated CSS for removal of the palette utility and broad popover transition; test open/closed rendering, Escape, focus restoration, and immediate result selection. No timer or `animationend` may gate commands.

**Runtime/feel checks:** repeatedly open/type/select/close and reverse popover toggles before completion. Check first-frame feedback, visible focus, no hidden focus targets, anchor positioning, and no animation restart on result updates; repeat with Reduced Motion.

**Source-drift stop:** stop if the cited class, token values, state contract, or `.popover` ownership differs materially, or if `DESIGN.md` requires a conflicting overlay treatment.

### Plan B — Tokenized toast entry without animated layout offsets
**Covers:** F4 and the toast portion of F2.

**Exact path/current excerpt**
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
**Target/conventions:** one restrained entry per toast, using the existing fast/responsive tokens. Preserve the final static position, readable feedback, dismissal, and notification semantics.

**Ordered steps**
1. Inspect positioning, transform ownership, stack layout, and removal lifecycle. Confirm what `top: 0` currently establishes; migrate that final position into static styling if needed.
2. Replace entry offsets with `transform: translateY(-8px)` to `translateY(0)`, retaining opacity `0` to `1`; use `var(--duration-fast)` and `var(--ease-responsive)`.
3. Use static final styles and remove unnecessary persistent `forwards` ownership. Keep the existing keyframe mechanism only for a verified one-shot mount entry; do not introduce an exit/presence system.
4. If transforms already own stack positioning or swipe dismissal, stop before overwriting them and resolve composition with that owner.
5. Add a Reduced Motion override with `animation: none`; show the toast immediately at its final position and opacity. Preserve content, status styling, announcements, and actions.

**Hard boundaries:** `src/components/toast.css` only. No notification timer, announcement, stacking-order, or dismissal behavior changes; no `will-change`, new dependencies, or global token edits.

**Mechanical checks:** run actual style/build checks; assert the keyframes no longer animate `top`; verify token resolution, static final opacity, and reduced-mode animation removal. Check that no dismissal logic relies on this entry’s animation completion.

**Runtime/feel checks:** inspect single and stacked entries, rapid arrivals, updates to an existing toast, action activation, and dismissal during entry. Check for transform conflicts, displaced final positions, replay, and clipping. Capture a trace before making performance claims.

**Source-drift stop:** stop if keyframes are shared, existing transform ownership is discovered, lifecycle depends on entry completion, or the current positioning contract differs from the excerpt’s assumed final state.

### Plan C — Establish drag ownership before tuning release
**Covers:** F5 and the queue portion of F2.

**Exact path/current excerpt**
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
**Target/conventions:** direct 1:1 tracking, preserved grab offset, no input lock during settling, and re-grab from the displayed position. Keep `nearestSlot(currentY)` target semantics. Use existing animation infrastructure, restrained non-bouncy motion, and semantic timing where a duration-based API is appropriate.

**Ordered steps**
1. Inspect pointer-down/cancel handlers, `--drag-y` consumers, coordinate spaces, `currentY` ownership, and the complete `animateTo` API. Confirm whether duration is milliseconds and whether it supports cancellation, presentation reads, and velocity.
2. Define one canonical drag position in queue-local CSS pixels. Convert viewport `clientY` using queue geometry, grab offset, and relevant scrolling; update that value and the visual write together. Handle the final pointer-up position.
3. Verify or add active-pointer capture, secondary-pointer exclusion, cancellation cleanup, and unmount cleanup. Keep React state changes at lifecycle boundaries rather than on every pointer move.
4. On re-grab, read the displayed position before cancelling the settle; establish the new grab offset from that position. Release to the existing nearest valid slot, not the previous animation target.
5. Sample position with monotonic timestamps; express release velocity in CSS px/s. Hand it to an existing capable settle primitive in its documented units, bounded to avoid overshoot outside valid slots. Do not invent unsupported `animateTo` options.
6. If only a duration-based retargetable primitive is supported, use the resolved `--duration-panel` value rather than hard-coded `400`; stop for an API decision if required interruption/velocity support is unavailable. Never pass a CSS `var()` string to a numeric API.
7. Reduced Motion keeps user-controlled tracking but commits release directly to the chosen slot, without autonomous travel or bounce. Preserve focus, selected/drop-state feedback, and existing reorder announcements.

**Hard boundaries:** `src/components/SortableQueue.tsx`; inspect but do not silently modify helper/CSS owners. No dependency installation, spring migration, changed reorder semantics, new drag threshold, or keyboard reordering redesign.

**Deferred targeting decision:** a momentum experiment could compute `clamp(position + velocity * 0.12s, minSlot, maxSlot)` using CSS pixels and CSS px/s. This is an unvalidated candidate, not implementation scope; using its nearest slot requires explicit authorization. Velocity handoff does not require changing target selection.

**Mechanical checks:** run actual type/lint/test scripts; test coordinate conversion, final-event freshness, capture cleanup, nearest-slot boundaries, animation cancellation, preference changes, and unmount. Assert no obsolete completion callback commits a superseded target.

**Runtime/feel checks:** grab near either edge, leave queue bounds, scroll during drag, reverse direction, release near slot boundaries, and immediately re-grab mid-settle. Check focus and any existing keyboard reorder path; repeat under Reduced Motion and representative data load.

**Source-drift stop:** stop if `--drag-y` is not a local translation input, `currentY` has different semantics, `animateTo` cannot satisfy the required lifecycle, or target selection/authority differs materially.

## 4. Recommended execution order and unverified states

1. **Resolve drag/API and effective Reduced Motion ownership first**—these are scope gates, not permission for speculative rewrites.
2. **Implement Plan A**, then **Plan B**: bounded changes with strong token and throughput benefits.
3. **Implement Plan C after its API gate clears.** Prioritize it earlier if later testing establishes task-breaking drag behavior.
4. Validate each plan separately; revert its scoped change if focus, input, dismissal, positioning, or reorder semantics regress.

**Explicitly unverified:** full stylesheet cascade and generated utilities; mounting/unmounting and exit behavior; palette focus/keyboard semantics; popover anchoring; toast stacking/announcement timing; drag capture, scrolling, velocity and cancellation; preference changes while active; actual usage frequency; computed durations; frame pacing, performance, and subjective feel. No browser, device, accessibility-tree, trace, recording, or user validation is claimed.
