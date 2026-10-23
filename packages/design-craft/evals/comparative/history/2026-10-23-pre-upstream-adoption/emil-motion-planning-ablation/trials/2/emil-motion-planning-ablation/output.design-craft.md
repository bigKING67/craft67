## 1. Recon summary

**Diagnosis:** The supplied motion rules diverge from the existing responsive tokens; the highest-leverage work is to align transient feedback, make overlay motion state-owned, and verify drag continuity before changing its physics.

- **Stack signals:** React-style TSX, CSS transitions/keyframes, a utility-style arbitrary animation class, and an imperative `animateTo` call. Framework, utility compiler, positioning system, and animation library are unconfirmed.
- **Motion locations:** Shared values and popover rules in `src/styles/motion.css`; palette animation in `src/components/CommandPalette.tsx`; toast keyframes in `src/components/toast.css`; pointer/release handling in `src/components/SortableQueue.tsx`.
- **Conventions:** `--duration-fast: 160ms`, `--duration-panel: 240ms`, and `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)`. This curve is strongly ease-out-like, not ease-in-out.
- **Local precedent:** `src/components/Button.css` explicitly transitions `transform`, uses semantic tokens, and supplies an 80ms Reduced Motion override. Preserve it; its specific press behavior is not a prescription for overlay travel.
- **Personality:** Calm, crisp desktop utility. Motion should explain a change, not delay input, focus, or repeated commands.
- **Frequency map—hypotheses, not measured usage:** Palette and button interactions are potentially high-frequency; popovers repeat during navigation; toasts are event-driven and may burst; drag events are high-frequency while a gesture is active, but reorder usage is unknown.
- **Evidence:** Supplied excerpts only. No full-file inspection, commit identifier, runtime checks, or validation results. The requirements attributed to `DESIGN.md` are accepted as supplied.

## 2. Vetted priorities

P1 means first implementation attention, not a demonstrated release blocker. No P0 is supported.

| ID / priority | Static evidence | Finding and runtime unknown | Smallest correction / acceptance evidence |
|---|---|---|---|
| M1 / P1 | Palette has an unconditional `palette_420ms_ease-in_both` class; `open` is exposed separately. | The shown animation declaration is not state-gated and bypasses tokens. Keyframes, mounting, visibility, and replay behavior are unknown. | State-owned, tokenized opacity transition; test immediate typing, rapid reversal, hidden-state focus exclusion, and focus restoration. |
| M2 / P1 verification gate | Drag writes `event.clientY`; release calls `nearestSlot(currentY)` with `duration: 400`. | Coordinate conversion, `currentY` freshness, capture, cancellation, presentation-value restart, and velocity handoff are not shown—not proven absent. | Establish those contracts first; preserve nearest-position targeting. Verify grab offset, 1:1 tracking, re-grab, cancellation, and keyboard parity. |
| M3 / P2 | Popover uses `transition: all 360ms ease-in` and centered origin. | Broad property ownership and timing mismatch are explicit. Whether center is inappropriate depends on placement and animated properties. | Explicit property list and fast responsive tokens; use trigger-relative origin only for verified anchored spatial motion. Test every supported placement. |
| M4 / P2 | Toast animates `top: -24px → 0` and opacity over `500ms ease-in`. | Layout-property animation is a risk, not evidence of dropped frames; positioning may determine whether `top` has any effect. | Move entrance offset to an owned transform with fast responsive timing; trace before making performance claims. |
| M5 / P2 | Only the button excerpt contains a Reduced Motion branch. | Coverage for the other surfaces is unverified; a global override could exist. Shorter spatial motion alone is not the target fallback. | Explicit scoped fallbacks: opacity/static feedback for overlays and toasts; direct drag tracking with immediate release placement. Test preference changes while active. |

**Vetted out:** No claim of layout thrashing from `transition: all`, guaranteed compositing from transforms, broken drag coordinates, or repeated palette playback. No new bounce, stagger, momentum targeting, or button rewrite is justified.

## 3. Implementation plans

### Plan A — State-owned palette and popover feedback
**Covers:** M1, M3, and overlay coverage in M5. Evidence baseline: supplied snippets; commit unknown.

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
    <div data-open={open} className="animate-[palette_420ms_ease-in_both]">
      <SearchResults />
    </div>
  );
}
```
**Target/conventions:** Immediate interaction and visible focus; restrained opacity feedback using `--duration-fast` and `--ease-responsive`. Preserve existing mounting, positioning, and accessibility ownership.
1. Inspect actual palette keyframes, generated CSS, open/closed selectors, overlay primitive, and mounting contract. Identify who owns focus, hidden state, exit retention, and placement transforms.
2. Replace the arbitrary palette animation with a named component class in the existing shared motion stylesheet; tie opacity targets to the existing `data-open` state. Use 160ms responsive transitions, with no new scale, translation, or result-list animation.
3. Keep closed content noninteractive and excluded from focus/accessibility navigation through the established primitive. Opening must not wait for animation; do not add an exit delay or custom focus trap.
4. Replace popover `all` with `opacity`; include `transform` only if existing state rules prove an intentional reveal transform that is separate from positioning. Use fast responsive tokens.
5. For verified anchored scale/reveal motion, consume the actual positioning system’s resolved origin, including collision changes. Preserve center for genuinely centered surfaces; do not invent a library variable.
6. Add scoped Reduced Motion rules: opacity-only, 80ms feedback; remove decorative transform changes while preserving any transforms needed for placement.

**Hard boundaries:** No token-value changes, dependency additions, primitive migration, positioning rewrite, search logic changes, or edits to `src/components/Button.css`. If the mounting contract cannot support transitions, resolve that contract before implementing—not with guessed lifecycle code.
**Mechanical checks:** Use the project’s actual typecheck, lint, and focused test commands after discovering them. Check generated selectors; assert palette animation-class removal, explicit popover transition properties, token use, and closed-state focus exclusion.
**Runtime/feel checks—planned:** Repeated keyboard open/type/Escape cycles; reversal mid-transition; result updates without entrance replay; focus restoration; anchored placements and collision flips; normal and Reduced Motion, including mid-transition preference changes.
**Source-drift stop:** Stop if cited classes, state attributes, tokens, authority, or primitive ownership differ materially, or if existing keyframes encode behavior beyond presentation.

### Plan B — Short, bounded toast entrance
**Covers:** M4 and toast coverage in M5. Evidence baseline: supplied snippet; commit unknown.

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
**Target/conventions:** Preserve the existing entrance direction and 24px distance initially, but use transform/opacity over `--duration-fast` with `--ease-responsive`. No new exit choreography.
1. Inspect toast positioning, base `top`, stack layout, transform ownership, dismissal, and animation-event consumers. Confirm the final static position without animation.
2. Replace keyframe `top` values with `translateY(-24px)` and `translateY(0)`, retaining opacity endpoints. Establish final positioning in the static rule only if the existing animation currently supplies it.
3. Replace `500ms ease-in` with the fast/responsive tokens. Ensure retained animation fill cannot override dismissal or stack transforms; do not combine competing transform owners.
4. Add a separate opacity-only Reduced Motion entrance at 80ms. Ensure its final opacity remains visible and it introduces no decorative translation.

**Hard boundaries:** Scope edits to `src/components/toast.css`; preserve content, live-region semantics, dismissal availability, timeout length, stacking, and undo behavior. No blanket `will-change` or claimed compositor promotion. If a wrapper or event-consumer edit is needed, stop and expand scope explicitly.
**Mechanical checks:** Confirm `toast-enter` no longer animates `top`; verify token resolution and Reduced Motion cascade; test final visibility, dismissal during entry, and any existing animation-completion contract using discovered project commands.
**Runtime/feel checks—planned:** Single toast, rapid arrivals, stacked and multiline content, dismissal during entry, keyboard access, and hidden-tab return. Confirm notifications do not steal focus or delay action; collect a trace before asserting reduced layout work.
**Source-drift stop:** Stop if positioning differs from the excerpt’s implied endpoint, another transform owner exists, animation names drive lifecycle behavior, or shared tokens/Reduced Motion rules have changed.

### Plan C — Verify and harden drag continuity without changing reorder semantics
**Covers:** M2 and drag coverage in M5. Evidence baseline: supplied snippet; commit unknown.

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
**Target/conventions:** Pointer-attached movement, interruption from the displayed position, bounded non-bouncy settling, and unchanged nearest-current-position slot selection. This is a contract-gated implementation, not permission to invent `animateTo` options.
1. Inspect pointer-down/cancel/lost-capture handlers, `--drag-y` consumer, `currentY` updates, scroll coordinates, slot calculation, keyboard reorder, and the actual `animateTo` signature and cancellation API.
2. Establish one coordinate space in CSS pixels. Capture the active pointer, preserve grab offset, and keep the displayed position and release position synchronized. Preserve existing drag-intent thresholds; add none speculatively.
3. Cancel an in-flight settle on re-grab and start from its presentation position. Audit transform ownership and the timing of `setDragging(false)` so state changes cannot reset the visual position before settling.
4. Measure recent position/time samples with monotonic timestamps; express release velocity in CSS px/s. Preserve `nearestSlot(currentY)` semantics using the verified current position, and pass bounded velocity in the supported animation API’s units.
5. Use existing token resolution for a duration-based settle: `--duration-panel` is the initial 240ms target, not a copied magic number. If the established primitive is spring-based, retain its verified configuration mechanism and tune a non-bouncy response; do not mislabel response time as duration.
6. Keep projection separate: a candidate is `clamp(y + v × horizonSeconds, firstSlot, lastSlot)` with bounded horizon and valid-slot clamping. Do **not** use it for target selection without separate authorization and runtime evidence.
7. Reduced Motion retains necessary 1:1 direct manipulation but removes autonomous release travel/overshoot: commit the nearest slot immediately, retaining static destination feedback, focus, and existing reorder announcements.

**Hard boundaries:** No inertia-based target change, new dependency, queue-data redesign, gesture-threshold change, or keyboard-contract change. If the current engine cannot expose/cancel presentation motion or accept velocity safely, stop for an explicit adapter/API decision rather than guessing.
**Mechanical checks:** Focused tests for coordinate conversion and scroll offset, latest release position, nearest-slot boundaries, cancellation, re-grab, velocity units, cleanup, and immediate Reduced Motion settlement; run discovered type/lint/test commands.
**Runtime/feel checks—planned:** Grab at different row offsets; slow and fast releases; leave bounds; scroll during drag; cancel; re-grab during settle; repeated and keyboard reorder; toggle Reduced Motion during drag/settle. Check 60/120Hz only where available; record actual conditions.
**Source-drift stop:** Stop if handler semantics, slot rules, coordinate ownership, token access, or `animateTo` API differ from the baseline or contradict the planned continuity contract.

## 4. Execution order and unverified states

1. **Revalidate evidence and authority**, especially overlay lifecycle and drag API contracts.
2. **Plan A first:** Highest likely keyboard-throughput leverage; resolve Reduced Motion alongside normal behavior.
3. **Plan B next:** Small, isolated correction with clear static acceptance checks.
4. **Plan C after its API gate:** Investigate early, but do not substitute faster timing for correct direct manipulation.

**Explicitly unverified:** Actual usage frequency; palette keyframes and mounting; popover anchoring; computed styles and global overrides; focus/accessibility-tree behavior; toast timing/stacking; drag capture, coordinates, velocity and interruption; browser compatibility; frame pacing; perceived feel; all Reduced Motion states. No files were edited, no plans were written to disk, and no browser/device or mechanical validation was performed.
