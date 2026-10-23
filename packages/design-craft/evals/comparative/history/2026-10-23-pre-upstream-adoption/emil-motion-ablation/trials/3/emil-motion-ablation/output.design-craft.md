## Verdict — request changes [static evidence]

The snippet does not establish reliable direct manipulation or Reduced Motion behavior. For a calm, repeatedly used operations app, prioritize immediate control, interruptible settling, and clear state feedback—not decorative sheet movement.

**Labels:** **[S]** supplied-code fact; **[R]** runtime risk, not observed; **[M]** proposed move.

## Prioritized findings and concrete moves

### 1. P1 — Drag ownership and coordinates are incomplete
- **[S]** `startY` is recorded but unused. Every `pointermove` writes viewport `clientY` directly to `top`, without an active-drag or pointer-ID check. No capture, cancellation, or boundary handling is shown.
- **[R]** Hover could move the sheet; grabbing below its edge could reposition it unexpectedly. Tracking outside the sheet and touch scrolling may conflict. Actual displacement depends on positioning CSS.
- **[M]** Use `idle → dragging → settling` ownership with one active pointer. Preserve the grab offset: `y = initialPresentationY + (clientY - initialPointerY)`, with positions in a consistent CSS-pixel coordinate space. Capture the pointer; handle `pointercancel` and lost capture; ignore extra pointers. Use a dedicated handle with an explicit touch-action policy while preserving content scrolling.
- **Acceptance:** Hover does nothing; taps remain taps; dragging from different grab points preserves offset; release outside and cancellation leave a usable state.

### 2. P1 — Settling cannot be reliably interrupted or finalized
- **[S]** `animating` guards only `pointerdown`; move/up remain active. The animation handle is discarded, `fill: "forwards"` retains the effect, and completion does not commit the target to underlying position/state. Rejection cleanup is absent.
- **[R]** Re-grabbing may produce competing ownership, masked style writes, or overlapping animations. Cancellation could leave the flag set; an older completion could clear it during a newer settle.
- **[M]** Keep one motion controller. On re-grab, sample current on-screen position and velocity, replace the settle without jumping, and hand control to the pointer. On completion, commit the exact snap position and collapsed/half/full state, then remove the animation effect. Make cleanup ownership-aware.
- **Acceptance:** Re-grab and reverse midway through a settle without discontinuity; rapid repeats cannot create stale completion effects; the next drag begins at the displayed position.

### 3. P1 — The motion configuration works against direct control
- **[S]** Dragging and settling write `top`; CSS applies `transition: all 300ms`; release uses a fixed `480ms ease-in`. The whole sheet scales to `0.96` when active.
- **[R]** CSS interpolation may make tracking trail the pointer; layout-property animation may increase rendering work. Slow-start settling and whole-sheet shrinkage risk feeling unnecessarily theatrical. No performance or feel has been measured.
- **[M]** Disable positional transitions during dragging. Drive `translateY` through one owner, batching writes on the display clock and avoiding per-frame layout reads. Replace whole-sheet scaling with immediate handle feedback; keep any separate feedback transform on a separate layer. For release, start with a non-bouncy, critically damped settle around a **0.25–0.3s response**, not a mandatory duration.
- **Acceptance:** In-range tracking stays attached to the pointer after intent recognition; press feedback does not distort content; a trace establishes rendering cost under representative app load.

### 4. P1 — Reduced Motion and non-drag state access are not demonstrated
- **[S]** No preference branch is shown for either CSS or the JavaScript animation. No alternative state controls or state announcement are supplied.
- **[R]** The shown path retains large spatial travel with Reduced Motion enabled. Keyboard access and state comprehension remain unknown, not proven absent throughout the app.
- **[M]** Honor `prefers-reduced-motion` in both motion owners, including preference changes. Commit state changes without animated travel, overshoot, or sheet scaling; retain a static state label and, optionally, brief handle color/opacity feedback. Provide keyboard-operable collapsed/half/full controls with visible focus. If “no large travel” also covers dragging, use gesture-threshold feedback followed by an immediate snap rather than continuous sheet translation.
- **Acceptance:** All three states remain reachable and identifiable with Reduced Motion and keyboard-only input; hidden content cannot retain inaccessible focus.

### 5. P2 — Release intent and edge behavior need an explicit contract
- **[S]** Target selection uses only `nearestSnapPoint(sheet.offsetTop)`. No velocity sampling or out-of-range resistance is shown; the helper’s internals are unknown.
- **[R]** Fast flicks and slow releases could resolve identically. Boundary behavior and snap stability cannot be inferred.
- **[M]** Measure recent release velocity in **CSS px/s** using monotonic timestamps and feed bounded velocity into the settle. Preserve nearest-current-position targeting unless momentum targeting is explicitly approved.
  - Experimental projection: `projectedY = clamp(y + v * 0.15, fullY, collapsedY)`—a provisional **150ms horizon**.
  - Only if approved, choose the nearest valid snap to that endpoint; otherwise keep projection as an experiment, separate from velocity handoff.
  - Start with an **8–12 CSS px** intent threshold; apply progressive edge resistance under normal motion, without decorative bounce.
- **Acceptance:** Slow releases, flicks, reversals, and both boundaries resolve predictably under the agreed targeting rule.

## Verified / unverified boundaries

- **Verified by inspection:** The event guards, property choices, timing values, retained fill, and missing branches **within this snippet**.
- **Unverified:** Rendered geometry, snap-helper behavior, surrounding accessibility, scroll arbitration, perceived latency, frame pacing, and browser/device behavior.
- **No files edited. No browser or device validation performed.**

## Smallest runtime validation plan — proposed, not executed

1. **One desktop browser session:** Exercise all three states, hover, off-center grabs, taps, slow drags, flicks, edge overshoot, release outside, mid-settle reversal, and rapid repeats. Log pointer ID, presentation position, velocity, target, and committed state; record a short video.
2. **Same session, Reduced Motion + keyboard:** Repeat state changes and interruption; verify no animated large travel, visible state feedback, reachable controls, and appropriate focus.
3. **One representative touch-device run:** Check handle dragging versus content scrolling, cancellation, and an extra finger. Record browser, device, and refresh rate.
4. **One short performance trace under typical app load:** Check F3’s layout/paint cost and frame pacing. Provisional gates, subject to product ratification: p95 gesture-update work below **8ms**, no gesture-attributable task over **50ms**; revise the motion approach if exceeded. These are proposed thresholds, not measured results.
