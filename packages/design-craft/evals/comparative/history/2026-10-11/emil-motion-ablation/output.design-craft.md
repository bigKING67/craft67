## Verdict — block approval on static evidence

The supplied code does not establish reliable direct manipulation or Reduced Motion behavior. For a calm, repeatedly used operations app, prioritize immediate control and clear collapsed/half/full feedback over prolonged settling and whole-sheet scaling.

**Evidence labels:** **[Static]** visible in the snippet; **[Risk]** inferred outcome requiring runtime confirmation; **[Move]** proposed repair; **[Check]** acceptance evidence.

## Prioritized findings and direct-manipulation moves

### 1. P1 — Drag ownership and grab offset are missing
- **[Static]** `startY` is recorded but unused. Every `pointermove` writes viewport `clientY` directly to `top`, without an active-drag or pointer-ID guard. No capture, cancellation, or intent threshold is shown.
- **[Risk]** Hover movement could reposition the sheet; grabbing away from its top could cause a jump. Leaving its bounds, another pointer, or native scrolling could break tracking.
- **[Move]** Track one primary pointer through idle/pressed/dragging/settling states. Capture it; handle `pointercancel` and lost capture. Preserve the grab offset with `position = initialPosition + (clientY - initialClientY)` in a consistent CSS-pixel coordinate space. Start with an 8–12px intent threshold, then track 1:1 without easing. Confine gesture handling to a handle or define explicit scroll arbitration; do not disable scrolling across all sheet content.
- **[Check]** Hover and taps do not drag; grabs at different offsets preserve attachment; release outside and cancellation recover cleanly.

### 2. P1 — Settling has conflicting ownership and cannot be safely interrupted
- **[Static]** `animating` blocks only `pointerdown`; moves and releases still run. The animation handle is discarded, `fill: "forwards"` retains its effect, and no canonical settled position or cancellation cleanup is shown.
- **[Risk]** Animation and inline `top` updates could compete. Repeated releases could create overlapping animations; old completion callbacks could clear a newer animation’s flag.
- **[Move]** Give position one owner and retain the active animation. On re-grab, sample the current presentation position and velocity **before** canceling; resume from there rather than the previous target. Commit the final position and named snap state, then remove the animation effect. Guard completion by animation identity and handle cancellation rejection.
- **[Check]** Re-grab and reverse mid-settle repeatedly: no discontinuity, stale completion, stuck input, or accumulating animation effects.

### 3. P1 — Reduced Motion and non-drag state access are not demonstrated
- **[Static]** No preference branch is shown; releases always request 480ms of positional animation. Keyboard controls and state semantics are outside the supplied code.
- **[Risk]** Large travel may remain enabled for users requesting less motion; the three states may be inaccessible without dragging.
- **[Move]** Honor `prefers-reduced-motion` in both JS and CSS, including preference changes. Remove inertial travel, overshoot, and whole-sheet scaling. Commit snap changes without an animated traverse, retaining immediate handle feedback and a visible named-state indicator; an optional brief opacity/color change can confirm completion. Provide keyboard-operable collapsed/half/full controls and preserve appropriate focus. If dragging remains available, keep it directly user-controlled rather than adding trailing motion.
- **[Check]** All three states remain reachable and identifiable with keyboard and Reduced Motion enabled, without large automatic spatial travel.

### 4. P2 — Release motion does not account for gesture velocity
- **[Static]** Target selection uses `nearestSnapPoint(sheet.offsetTop)`; there is no velocity sampling. Every release uses `480ms` and `ease-in`.
- **[Risk]** Slow acceleration followed by an abrupt endpoint may feel disconnected from release, especially in repeated use. Flick intent is not represented.
- **[Move]** Measure recent position/time samples in **CSS px/s** and feed bounded release velocity into an interruptible, critically damped settle. Start tuning around a 250–300ms response scale—not a fixed completion guarantee—and avoid decorative bounce.
- **[Move]** Preserve nearest-current-position targeting unless momentum targeting is approved. A concrete experiment is `projectedY = clamp(currentY + velocity * 0.15, fullY, collapsedY)` with velocity in px/s and a 150ms horizon. Only if authorized, select the nearest valid snap to that endpoint. Velocity handoff and target selection are separate decisions. Add modest boundary resistance only in normal-motion mode.
- **[Check]** Compare slow releases and fast flicks near both snap boundaries; targets follow the agreed rule and settling preserves release continuity.

### 5. P2 — Layout animation and whole-sheet press feedback undermine restraint
- **[Static]** Dragging and settling modify `top`; CSS applies `transition: all 300ms` and scales the entire sheet to `0.96` while active.
- **[Risk]** Broad transitions could introduce tracking lag; layout-property animation could increase rendering work. Scaling an operational surface could disturb text and pointer attachment. None of these performance or perceptual outcomes is measured.
- **[Move]** Use one `translateY` owner with no transition during dragging; cache geometry outside the move loop and coalesce writes to display frames. Replace `transition: all` with narrowly scoped feedback transitions. Prefer handle color/outline feedback over sheet scaling. If scale is retained elsewhere, separate its wrapper from drag translation.
- **[Check]** Inspect computed transforms and a performance trace under representative app load; confirm direct tracking and absence of repeated gesture-driven layout work.

## Verified / unverified boundary

**Verified by inspection:** the shown event guards, property writes, duration/easing, retained fill, and absence of the described branches **within this snippet**.

**Unverified:** actual appearance, coordinate geometry, `nearestSnapPoint` behavior, surrounding accessibility support, scrolling interaction, frame timing, and perceived motion quality. No files were edited; no browser or device validation was performed.

## Smallest runtime validation plan — proposed, not executed

1. **One instrumented desktop-browser session:** exercise all three states, hover/tap, different grab offsets, outside release, cancellation, and repeated mid-settle reversals. Log pointer ID, presentation position, velocity, target, and animation ownership. Evaluate findings 1–2 and 4.
2. **In that session:** enable Reduced Motion, test keyboard state controls, then change the preference during settling. Verify finding 3 and capture a short recording of state feedback.
3. **One representative touch-device session:** check handle dragging versus content scrolling, second-touch rejection, and boundary behavior. Record browser/device and refresh rate.
4. **One short performance trace under normal app load:** evaluate finding 5. Provisional gates, subject to product ratification: input-to-presentation p95 ≤ two refresh intervals and no gesture-attributable task over 50ms. Failed correctness or motion-accessibility checks block approval; missed timing gates require profiling before acceptance.
