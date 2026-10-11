## Evidence-labeled verdict

**Verdict: Not acceptable for a calm, repeatedly used three-state sheet.**  
**Static evidence:** the implementation moves `top` directly from `event.clientY`, animates `top` with `ease-in`, has global `transition: all`, uses `:active` scale, and has no reduced-motion branch.  
**Likely user impact:** jumpy drag start, accidental movement, sluggish/unnatural settling, conflicting animations, layout cost, weak snap intent, and non-compliant reduced-motion behavior.

---

## Prioritized findings

### P0 — Drag is not actually gated to an active gesture
**Evidence:** `pointermove` always runs and sets `sheet.style.top`, even if no valid `pointerdown` occurred or if `animating` blocked the down event.  
**Impact:** stray pointer movement can reposition the sheet; animation state can be corrupted.

### P0 — The sheet jumps because position is absolute to the pointer
**Evidence:** `sheet.style.top = event.clientY`. `startY` is recorded but unused.  
**Impact:** if the user grabs the sheet below its top edge, the sheet top snaps to the finger/mouse Y instead of preserving grab offset.

### P0 — Reduced Motion requirement is unmet
**Evidence:** release always animates spatial travel for `480ms`.  
**Impact:** users requesting reduced motion still get large positional movement between collapsed, half, and full states.

### P1 — Motion easing is backwards for settling
**Evidence:** `easing: "ease-in"`.  
**Impact:** the sheet accelerates into the destination instead of decelerating into rest, which feels abrupt and less calm.

### P1 — CSS and JS animation conflict
**Evidence:** `.sheet { transition: all 300ms; }` plus JS `sheet.animate(...)` and pointer-driven `top` writes.  
**Impact:** drag updates may be implicitly transitioned; unrelated properties animate; state can feel laggy or inconsistent.

### P1 — Animating `top` is a poor direct-manipulation primitive
**Evidence:** both drag and snap mutate/animate `top`.  
**Impact:** `top` affects layout; repeated drag frames can cause unnecessary layout work. `transform: translateY(...)` is a better fit.

### P1 — Snap decision ignores velocity, direction, and hysteresis
**Evidence:** `nearestSnapPoint(sheet.offsetTop)` only uses current position.  
**Impact:** a decisive upward flick near the half point may still collapse; small jitter around thresholds may switch states unpredictably.

### P1 — Animation state is not committed robustly
**Evidence:** `fill: "forwards"` is used, but no explicit final style/state assignment is shown.  
**Impact:** visual state and layout state can diverge after animation, interruption, or future measurements.

### P2 — Whole-sheet active scale is visually noisy
**Evidence:** `.sheet:active { transform: scale(0.96); }`.  
**Impact:** scaling the entire sheet during a drag can make content pulse, reduce perceived stability, and conflict with transform-based translation.

### P2 — Missing bounds and scroll arbitration
**Evidence:** no clamp, no resistance, no distinction between dragging the handle and scrolling sheet content.  
**Impact:** the sheet can move beyond valid states; scrollable content may fight the sheet gesture.

---

## Concrete direct-manipulation moves

1. **Track real drag state**
   - On `pointerdown`: set `dragging = true`, capture pointer, cancel any running snap animation.
   - Store `startPointerY` and `startSheetY`.
   - On `pointermove`: ignore unless `dragging`.

2. **Move by delta, not absolute pointer position**
   - Compute `nextY = startSheetY + event.clientY - startPointerY`.
   - Clamp between full and collapsed positions.
   - Optionally add mild resistance outside bounds, but never allow permanent overshoot.

3. **Use transform for motion**
   - Represent the sheet position as `translateY(y)`.
   - Avoid mutating `top` during drag.
   - Remove `transition: all`; use explicit transitions only for non-gesture states.

4. **Separate press feedback from sheet movement**
   - Do not scale the whole sheet.
   - If feedback is needed, apply a subtle handle change: opacity, background, outline, or small handle compression.

5. **Choose snap target from projected intent**
   - Track recent pointer samples.
   - On release, compute velocity.
   - Use projected position, direction, and hysteresis to choose collapsed / half / full.
   - Example behavior:
     - slow release: nearest state with hysteresis
     - fast upward release: advance toward fuller state
     - fast downward release: advance toward more collapsed state

6. **Use calm settling motion**
   - Prefer decelerating easing, e.g. an ease-out curve or spring-like settle without bounce.
   - Scale duration by distance, with a practical cap.
   - For repeated operations, favor roughly `160–280ms` over a fixed `480ms`.

7. **Commit final state explicitly**
   - At animation finish, set the canonical state and final transform.
   - Clear animation references.
   - Handle cancellation and interruption predictably.

8. **Add Reduced Motion behavior**
   - If reduced motion is requested:
     - update directly to the target state, or use a very short non-spatial cue;
     - avoid large animated travel;
     - preserve feedback with state label, handle color, outline, opacity, or content affordance.
   - The state should still be obvious without relying on movement.

9. **Protect repeated-use calmness**
   - Avoid bounce, overshoot, playful scale, and long travel.
   - Make collapsed / half / full stops feel predictable and quiet.
   - Keep thresholds stable so users can build muscle memory.

---

## Verified / unverified boundaries

**Verified from static code only**
- Pointer movement is not gated by a `dragging` flag.
- `startY` is unused.
- `top` is directly written during pointer move.
- Release animation always runs for `480ms`.
- Easing is `ease-in`.
- CSS applies `transition: all`.
- CSS scales the active sheet.
- No reduced-motion branch is present in the provided code.

**Not verified**
- Actual browser behavior.
- Device/touch feel.
- Frame rate or layout cost.
- Exact behavior of `nearestSnapPoint`.
- Whether surrounding code handles bounds, accessibility, pointer capture, scroll locking, or state persistence.

---

## Smallest runtime validation plan

1. **Gesture correctness**
   - Start dragging from top, middle, and handle area.
   - Confirm no jump on first move.
   - Confirm pointer movement outside active drag does not move the sheet.

2. **Snap intent**
   - Test slow releases near each threshold.
   - Test fast upward and downward flicks.
   - Confirm hysteresis prevents threshold jitter.

3. **Animation integrity**
   - Interrupt a snap with a new drag.
   - Confirm the sheet starts from its current visual position.
   - Confirm final visual position and stored state match.

4. **Reduced Motion**
   - Enable reduced motion.
   - Move between collapsed, half, and full.
   - Confirm state feedback remains clear without large animated travel.

5. **Repeated-use feel**
   - Perform 20–30 open/half/collapse cycles.
   - Check for fatigue signals: lag, bounce, overshoot, excessive duration, or distracting scale.
