## Verdict

**[Static evidence] Not ready for reliable direct manipulation.** The main problems are gesture ownership, coordinate handling, and competing motion controls—not simply an easing choice. **[Expected effect, untested]** Together these risk jumps, delayed tracking, and unreliable re-grabs: costly friction in a repeatedly used, calm operations app.

Labels below distinguish **Observed** code facts, **Expected** consequences, and **Proposed** changes.

## Prioritized findings

### P0 — Fix gesture correctness and ownership
- **[Observed]** `startY` is recorded but unused. Every move assigns viewport `clientY` directly to CSS `top`, whose coordinate space depends on layout.
  **[Expected]** The sheet can jump toward the pointer and lose the original grab offset.
- **[Observed]** Moves and releases have no active-drag or pointer-ID guard. Mouse hover can write position; an unrelated release can initiate a snap.
- **[Observed]** No pointer capture, cancellation handling, or touch/scroll arbitration appears.
  **[Expected]** Leaving the sheet, browser gesture takeover, or a second pointer can disrupt the interaction.
- **[Proposed]** Own one pointer; accept appropriate primary-button input; capture it; handle `pointercancel` and `lostpointercapture` with an explicit cleanup policy. Use a dedicated drag handle, preserving ordinary scrolling and controls inside the sheet.

### P0 — Make settling interruptible and single-owner
- **[Observed]** `animating` blocks only `pointerdown`; moves and releases remain enabled. It neither safely locks interaction nor supports interruption.
- **[Observed]** The animation handle is discarded. `fill: "forwards"` retains an animated value without committing the final position to the underlying style. There is no cancellation/rejection cleanup.
  **[Expected]** Subsequent style writes can be masked by the filled animation; overlapping completions can clear the boolean at the wrong time.
- **[Proposed]** Use explicit `idle → dragging → settling` states and one motion controller. Re-grabbing must start at the **currently displayed position**, stop the previous settle without jumping, and immediately return control to the pointer. Commit settled position and remove the old animation effect; guard stale callbacks.

### P1 — Remove tracking lag and competing effects
- **[Observed]** `transition: all 300ms` includes `top` and the active-state transform. Drag updates are therefore subject to a transition rather than direct tracking.
- **[Observed]** Position uses `top`; `:active` also shrinks the whole sheet to `0.96`.
  **[Expected]** Layout work may increase, while shrinking a large working surface shifts content and weakens the sense of a stable grip.
- **[Proposed]** Position through a single `translateY` channel with **no positional transition while dragging**. Remove whole-sheet press scaling; give immediate, restrained feedback on the handle instead. Scope any remaining transitions to named properties. Transform use is a performance opportunity, not proof of smoothness.

### P1 — Preserve release intent, then settle quietly
- **[Observed]** The shown snap call receives position only; no release velocity is tracked or handed off. A fixed 480ms `ease-in` starts slowly and accelerates toward its endpoint rather than easing into rest.
- **[Expected]** A flick can feel discarded, and a small correction can take disproportionately long.
- **[Proposed]** Select among collapsed, half, and full using position **plus bounded velocity projection**. Use a velocity-aware, interruptible spring with critical or near-critical damping: no decorative bounce by default. Treat response tuning as a runtime question, not a universal duration.

### P1 — Supply an explicit Reduced Motion path
- **[Observed]** Neither snippet checks the motion preference.
- **[Proposed]** Disable inertial travel, overshoot, and whole-sheet scaling. For strict avoidance of large travel, keep the sheet stationary during gesture preview, indicate the candidate state on the handle/state control, then commit geometry immediately on release. A brief opacity or color cue can confirm the change without sliding.
- Provide explicit **Collapsed / Half / Full** controls usable by keyboard and pointer; preserve focus and expose the selected state. A CSS media query alone will not disable the JavaScript animation.

## Concrete direct-manipulation sequence

1. **Grab:** accept the owning pointer, capture the live sheet position, interrupt settling, and record pointer origin plus recent timestamped positions.
2. **Track:** compute `y = grabbedSheetY + (pointerY − grabbedPointerY)` in one consistent coordinate space. Keep tracking 1:1 within bounds; use restrained progressive resistance beyond the endpoints.
3. **Disambiguate:** use a small movement threshold to separate taps from drags without introducing a jump when dragging begins. Set touch behavior on the handle before the gesture starts; do not disable scrolling across the entire sheet.
4. **Release:** estimate velocity from a short recent sample window, ignoring stale motion after a pause. Project a bounded endpoint and choose a valid snap, with hysteresis near boundaries.
5. **Settle:** start from current position and release velocity. Permit immediate re-grab and reversal. Commit exactly one final state.
6. **Cancel:** release ownership, clear samples, and restore or settle to a defined valid state; never treat cancellation as an intentional flick.

## Verified / unverified boundary

**Verified by static inspection only:** the handlers, properties, timing, guards, and missing mechanisms described above.

**Unverified:** actual layout/containing block, snap-helper behavior, surrounding accessibility and scroll handling, browser animation interactions, frame pacing, perceived feel, and device behavior. No files were edited; no browser or device validation was performed.

## Smallest runtime validation plan

- **Desktop mouse:** hover without pressing; grab at different offsets; leave the bounds while dragging; re-grab and reverse halfway through settling. Pass: no hover movement, jumps, lost ownership, or stale completion.
- **One touch device:** slow drag, fast flick, pause-then-release, second touch, cancellation, and scroll inside sheet content. Exercise all three states. Pass: predictable targets and no unintended scroll takeover.
- **Reduced Motion + keyboard:** change among all states and interrupt an in-progress settle when the preference changes. Pass: no large animated travel, clear state feedback, retained focus, and no drag-only functionality.
- **One performance trace:** record drag → release → re-grab. Inspect actual frame pacing and layout work; tune spring response only after correctness passes.
