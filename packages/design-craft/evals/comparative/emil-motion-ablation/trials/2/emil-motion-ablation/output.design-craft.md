## Verdict — **Block pending correction**
**[Static evidence + product context]** This is not yet a dependable three-state gesture sheet. Input ownership, position tracking, interruption, and Reduced Motion need correction before timing polish. For a calm, repeatedly used operations app, prioritize immediate control and quiet state feedback—not whole-sheet press effects.

**Labels:** **[Static]** proven by the supplied snippet; **[Risk]** plausible runtime consequence, not observed; **[Move]** proposed correction.

## Prioritized findings and direct-manipulation moves

### 1. P1 — Drag ownership and grab position are missing
- **[Static]** `startY` is recorded but never used. Every `pointermove` writes viewport `clientY` into CSS `top`, with no active-drag or pointer-ID check. No capture, cancellation, or boundary handling is shown.
- **[Risk]** Hover could move the sheet; grabbing below its top could cause a jump. Coordinate-space differences, leaving the element, extra touches, and content scrolling could break tracking.
- **[Move]** Use explicit idle/pressed/dragging/settling states and one active primary pointer. On down, record the rendered sheet position and pointer position in a consistent CSS-pixel coordinate space. Apply `initialSheetY + (clientY - startY)` after a small intent threshold—start testing around 8–12 CSS px, without a threshold-crossing jump.
- **[Move]** Capture the pointer, handle `pointercancel`/lost capture, and ignore other pointers. Prefer a dedicated handle with an appropriate `touch-action` policy so content remains scrollable. Add bounded progressive resistance beyond full/collapsed limits.
- **Acceptance:** preserved grab offset, 1:1 tracking within bounds, no hover movement, and predictable release/cancellation outside the sheet.

### 2. P1 — Settling cannot be reliably interrupted or finalized
- **[Static]** `animating` rejects only `pointerdown`; move/up still run. The animation handle is discarded. `fill: "forwards"` retains an animated value without updating the underlying position; completion only resets a boolean. Cancellation rejection and stale completions are unhandled.
- **[Risk]** Re-grabs could compete with retained animations or launch overlapping settles. The visible position, inline position, and interaction state could diverge.
- **[Move]** Give position and animation a single owner. Re-grabbing must sample the current presentation position and velocity, stop the previous animation, and transfer control without jumping—not wait for completion. Finalize the selected snap into persistent position and named state, then remove the animation effect. Make cancellation cleanup ownership-aware so old callbacks cannot reset a newer gesture.
- **Acceptance:** rapid grab/release/reverse sequences remain continuous; only the current interaction can commit collapsed, half, or full.

### 3. P1 — Reduced Motion and non-drag state access are absent here
- **[Static]** No preference branch or keyboard/state controls are shown; settling always requests 480 ms of positional animation.
- **[Risk]** The supplied path does not meet the stated Reduced Motion requirement. Accessibility elsewhere in the app is unknown.
- **[Move]** Under `prefers-reduced-motion`, remove animated snap travel, elastic motion, and press scaling. Commit geometry immediately; retain an explicit selected-state label and, optionally, a brief opacity/color cue. If direct dragging remains, keep only movement directly controlled by the pointer—no momentum tail. Provide labeled keyboard-operable controls for all three states and visible focus.
- **Acceptance:** all states remain understandable and reachable without dragging or large animated travel; focus remains on a usable control.

### 4. P2 — Multiple motion mechanisms undermine direct tracking
- **[Static]** Pointer updates and WAAPI animate `top`; `transition: all 300ms` also covers position and the `:active` scale.
- **[Risk]** Transition interpolation can make dragging trail the pointer; layout-property animation can add rendering work. Whole-sheet `scale(0.96)` may visually detach content from the grabbed point. Actual lag, frame cost, and compositing are unmeasured.
- **[Move]** Use one translation owner, normally `transform: translateY(...)`, with **no transition during dragging**. Coalesce visual writes with the display clock; keep geometry reads out of the move loop. Remove `transition: all` and whole-sheet scaling. Use restrained handle feedback instead; if scale is retained anywhere, separate its transform ownership.
- **Acceptance:** pointer/rendered-position traces show direct tracking; a performance trace establishes rendering cost rather than assuming transforms guarantee smoothness.

### 5. P2 — Release ignores velocity and favors slow-start motion
- **[Static]** Target selection receives only `offsetTop`; settling uses fixed `480ms ease-in`. No velocity measurement or velocity handoff exists.
- **[Risk]** Slow-start acceleration and abrupt arrival may feel disconnected from release, especially across repeated operations. The snap helper’s semantics are unknown.
- **[Move]** Measure recent pointer samples using monotonic timestamps; express velocity in CSS px/s. Settle from the current presentation position with bounded measured velocity, converted to the animation API’s units. Start with a critically damped, no-bounce spring around a 0.25–0.35 s response scale; tune rather than treating this as a fixed duration.
- **[Move]** Preserve nearest-current-position targeting unless momentum targeting is explicitly approved. A testable alternative is `projectedY = clamp(currentY + velocity * 0.15s, fullY, collapsedY)`, then choose the nearest valid snap. Projection selects a destination; it does **not** replace velocity handoff into the settle.
- **Acceptance:** slow releases and fast flicks follow the agreed target rule, with continuous release/re-grab motion and no unintended state skipping.

## Verified / unverified boundary

- **Verified by static inspection only:** the handlers, property choices, timing, and missing branches described above.
- **Unverified:** rendered geometry, snap-helper behavior, external controls/styles, focus semantics, perceived feel, touch-scroll arbitration, frame rate, and device behavior.
- No files were edited. No browser or device validation was performed.

## Smallest runtime validation plan — proposed, not executed

1. **One desktop browser + one representative touch device:** record a short interaction trace covering all three states in both directions, slow drag, flick, offset grab, boundary pull, mid-settle reversal, outside release, cancellation, and an extra pointer. Check findings 1–2 and 5 against their acceptance criteria.
2. **Same fixture with Reduced Motion enabled:** exercise each state by pointer and keyboard; verify feedback, focus, and absence of animated spatial travel. Include one content-scroll gesture to check handle/content arbitration.
3. **One normal-load performance recording:** inspect pointer-to-presentation tracking and frame work for finding 4. Provisional gates, pending product agreement: p95 tracking delay ≤ one display interval and no gesture-attributable task ≥50 ms. Record browser, device, refresh rate, and trace/video; do not approve if correctness fails or the revised motion regresses these gates.
