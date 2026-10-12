## 1. Recon summary

**Diagnosis:** the excerpts mix a crisp, token-based button precedent with longer, hard-coded entrances and a fixed-duration drag settle. Align motion ownership and state handling before tuning visual polish.

- **Stack signals:** React-style TSX, CSS transitions/keyframes, an arbitrary animation utility class, and imperative pointer handlers. The utility framework and `animateTo` implementation are not established.
- **Motion locations:** shared tokens/popovers in `src/styles/motion.css`; palette motion in `src/components/CommandPalette.tsx`; toast keyframes in `src/components/toast.css`; drag logic in `src/components/SortableQueue.tsx`.
- **Conventions:** `--duration-fast: 160ms`, `--duration-panel: 240ms`, and `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)`—a strong ease-out-like curve. `src/components/Button.css` demonstrates explicit property ownership, token reuse, and a local Reduced Motion override.
- **Authority/personality:** the supplied `DESIGN.md` requirements favor calm, crisp utility, visible focus, semantic tokens, and preserved feedback under Reduced Motion.
- **Frequency map:** palette and button interactions are likely frequent for keyboard-heavy operators; popovers are repeated contextual interactions; toasts are event-driven; sorting frequency is unknown, but pointer updates are continuous during dragging. These are planning assumptions, not measured usage.
- **Evidence level:** supplied static excerpts only; full files, commit, dependency versions, cascade, lifecycle, and animation APIs are unknown. No files were edited or plans written.

## 2. Vetted priorities

Priorities express implementation order, not demonstrated production severity. No P0 task blocker is established.

| ID / priority | Static evidence | Finding and smallest correction | Unknown / acceptance evidence |
|---|---|---|---|
| F1 / P1 | Palette uses `palette_420ms_ease-in_both`; `open` appears only as `data-open` here. | High-frequency surface has hard-coded, slow-start motion configuration; binding to open/close is not shown. Remove decorative entrance travel and timing; preserve immediate state/focus feedback. | Keyframes, mounting, hiding, and focus ownership unknown. Verify rapid keyboard open/close, typing, and focus restoration. |
| F2 / P2 | Popover uses `transition: all 360ms ease-in` and centered origin. | Broad property ownership and token divergence. Restrict transitions to actual visual properties; use fast/responsive tokens. Correct origin only if anchored scaling is confirmed. | Changed properties and anchoring unknown. Inspect computed styles and placement changes; do not infer layout cost from `all` alone. |
| F3 / P2 | Toast animates `top` and opacity over `500ms ease-in forwards`. | Layout-position property animation is a risk; duration/easing diverge from conventions. Prefer a short opacity entrance with explicit lifecycle ownership. | Positioning may make `top` effective or ineffective; dropped frames are not established. Verify stacked entry, dismissal, and interruption. |
| F4 / P2 | Pointer move writes `event.clientY`; release calls `animateTo(nearestSlot(currentY), { duration: 400 })`. | Coordinate conversion, interruption, and velocity handoff are not demonstrated. Audit those contracts before merely shortening the settle. | Capture, offset, variable consumer, and animation capabilities unknown. Verify grab continuity, release, re-grab, and cancellation. |
| F5 / P2 | Only the supplied button excerpt contains a Reduced Motion branch. | Coverage for the other surfaces is not established. Include explicit non-spatial feedback paths in each implementation. | Global overrides may already exist. Verify effective CSS and JS behavior with the preference enabled and changed live. |

**Vetted out:** centered popover origin is not inherently wrong; per-move CSS-variable writes do not prove broad recalculation; pointer capture cannot be declared absent from these handlers. Keep the supplied button precedent unchanged. No new decorative motion is warranted.

## 3. Implementation plans

All three plans are **proposed, static-only, and independently scoped**. Before implementation, inspect full cited files, applicable instructions, `DESIGN.md`, token consumers, package scripts, and existing tests. Record the current revision. Missing lifecycle/API evidence is an implementation gate—not permission to invent behavior.

### Plan A — Make palette and popover responses immediate and state-owned
**Scope:** F1, F2, and their F5 coverage.

**Exact paths/current excerpts:**
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
**Target/conventions:** palette toggles without entrance travel or animation delay; search and focus remain immediately usable. Popovers use explicit properties and `--duration-fast` / `--ease-responsive`; retain existing semantic styling and focus indicators.

**Ordered steps:**
1. Locate `palette` keyframes, `data-open` rules, mount/unmount ownership, hidden-state semantics, and focus restoration. Determine whether popovers are anchored and which properties actually change.
2. Remove the palette animation class, retaining `data-open` and children. Preserve the verified visibility/focus contract; do not introduce an animation-completion dependency.
3. Replace popover `all` with only the confirmed opacity/transform properties; use the existing fast/responsive tokens. Do not add scale or travel that does not already serve continuity.
4. If scaling is anchored, obtain origin from the existing placement mechanism, including flipped placement. Keep center for genuinely centered surfaces; do not fabricate a positioning-variable API.
5. Add the Reduced Motion rule described below and targeted state/interruption tests.

**Hard boundaries:** only the two cited files unless separately approved; no dependency, token-value, search, positioning-engine, focus-trap, or button changes. If missing state ownership requires another file, stop and rescope.

**Mechanical checks:** confirm the arbitrary palette animation class and popover `transition: all` are gone; verify token resolution and selectors; run the discovered typecheck, lint, relevant tests, and build scripts. Tests must cover open/closed semantics and immediate input readiness.

**Runtime/feel checks—not performed:** repeated shortcut/Escape cycles, typing immediately on open, focus return, pointer versus keyboard activation, interrupted popover toggles, and each supported placement/flip. Capture effective durations and inspect for invisible focusable content.

**Reduced Motion:** palette remains immediate. Popovers remove entrance/exit translation and scale while preserving positioning transforms; change opacity immediately and keep focus/static open-state feedback. Do not blanket-reset a transform used for placement.

**Source-drift stop:** stop if the quoted class/rule, token meanings, `open` contract, placement ownership, or documented motion authority differs materially; rebase the plan before editing.

### Plan B — Give toasts restrained, interruption-safe feedback
**Scope:** F3 and toast F5 coverage.

**Exact path/current excerpt:**
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
**Target/conventions:** opacity-only entrance using `--duration-fast` and `--ease-responsive`; no positional entrance. Toast content and actions are available immediately, independent of animation completion.

**Ordered steps:**
1. Identify the actual toast lifecycle owner, entry/exit state selectors, positioning baseline, stacking behavior, and dismissal/announcement contracts. Its path is not supplied: resolve and explicitly add it to scope before lifecycle edits.
2. Replace the `top` keyframes and retained `forwards` animation with an opacity transition driven by the verified lifecycle state. Use an existing mounted-state mechanism; do not invent selectors or assume `@starting-style` support.
3. Keep the resting layout explicit. If `top: 0` currently supplies an essential final position, preserve that as static positioning after checking the cascade.
4. Ensure dismiss/re-entry retarget from current opacity; closed toasts cannot intercept input. Preserve existing timeout, announcement, ordering, and removal semantics.
5. Add lifecycle tests and the Reduced Motion override.

**Hard boundaries:** no new animation library, stack choreography, stagger, toast timeout changes, or blanket `will-change`. Do not alter placement transforms. If a CSS-only change cannot own lifecycle safely, stop rather than simulate it with arbitrary delays.

**Mechanical checks:** verify no `top` animation or old `toast-enter` usage remains in scope; confirm final-state opacity/position without animation; run discovered CSS/lint, component tests, and build scripts. Test removal without relying solely on `transitionend`.

**Runtime/feel checks—not performed:** single and burst arrivals, multiple stacked toasts, early dismissal during entrance, repeated triggers, action focus, long messages, and background-tab return. Use a trace before claiming a performance improvement.

**Reduced Motion:** no spatial motion and no fade delay; show/remove immediately while preserving message, action, announcement, and dismissal feedback.

**Source-drift stop:** stop if the quoted keyframes/rule, shared animation consumers, token contract, or discovered lifecycle differs from the reviewed baseline. Revalidate before replacing animation ownership.

### Plan C — Preserve drag continuity without changing reorder semantics
**Scope:** F4 and drag F5 coverage.

**Exact path/current excerpt:**
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
**Target/conventions:** 1:1 pointer tracking, preserved grab offset, interruptible settling, and unchanged nearest-position slot selection. Keep direct DOM/style updates rather than adding per-frame React state updates.

**Ordered steps:**
1. Inspect pointer-down/cancel/capture handlers, `--drag-y` consumers, scrolling/coordinate spaces, `currentY` updates, and `animateTo` definition. Confirm how `setDragging(false)` affects the visual element.
2. Establish one coordinate model in CSS pixels: convert `clientY` into queue-local position, preserve grab offset, and account for scrolling. Keep the existing drag threshold/bounds; verify active-pointer capture and cleanup.
3. Give translation one owner; compose rather than overwrite other transforms. On re-grab, cancel settling and start from the current displayed position, not the previous target.
4. Measure release velocity from a short timestamped position history in CSS px/s. Keep `nearestSlot(currentY)` semantics, ensuring `currentY` is the authoritative release position.
5. Use the verified animation API to hand off measured velocity in its required units, with bounds enforced and no decorative bounce. Do not blindly replace `400` with a shorter duration; if the API lacks readable position/velocity and cancellation, stop for an approved API-level plan.
6. Preserve reorder commitment, keyboard behavior, and cancellation; add preference handling and focused tests.

**Projection decision:** do not enable momentum targeting. A separately authorized candidate is `clamp(y + v * 0.10s, minSlot, maxSlot)`, then nearest valid slot; the 100ms horizon is provisional. This diagnostic candidate must not change production target selection without product approval and runtime evidence.

**Hard boundaries:** initially `src/components/SortableQueue.tsx` only; inspect consumers/API read-only. No new dependency, automatic spring migration, pointer easing, changed reorder algorithm, speculative variable relocation, or new keyboard interaction scheme.

**Mechanical checks:** test coordinate conversion, scroll offsets, capture release/cancel, latest release position, velocity-unit conversion, unchanged nearest-slot selection, and animation cancellation. Run discovered typecheck/lint and relevant tests; verify no competing frame-time transform writers.

**Runtime/feel checks—not performed:** grab at different item offsets, slow/fast release, reversal, re-grab mid-settle, pointer leaving bounds, scrolling, cancellation, and dense queues. Record position/velocity continuity; profile before asserting frame-pacing gains.

**Reduced Motion:** retain direct 1:1 tracking because it explains manipulation; remove autonomous release travel, overshoot, and sibling movement animation. Commit the nearest slot immediately, preserving static destination feedback, focus, and existing reorder announcements.

**Source-drift stop:** stop if these handlers, `currentY` meaning, variable ownership, `animateTo` signature/capabilities, or nearest-slot semantics differ from the reviewed baseline.

## 4. Execution order and unverified states

1. **Plan A:** highest expected keyboard-frequency benefit, using existing tokens and narrow ownership.
2. **Plan B:** bounded toast correction once lifecycle ownership is resolved.
3. **Plan C:** resolve API/coordinate gates first, then implement continuity—not speculative physics.
4. Validate normal and Reduced Motion paths per plan; retain each change only after its acceptance checks pass.

**Explicitly unverified:** actual usage frequency; effective cascade/keyframes; supported browsers; focus and accessibility-tree behavior; popover anchoring; toast positioning/lifecycle; drag capture, geometry, velocity, and cancellation; keyboard sorting; live preference changes; visual feel, frame pacing, and device behavior. No runtime, browser, device, trace, recording, or user validation is claimed.
