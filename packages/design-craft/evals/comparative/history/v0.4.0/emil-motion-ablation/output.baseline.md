## Evidence-labeled verdict

**Verdict: Not ready for a calm, repeated-use operations app.**  
**Evidence:** The implementation makes the sheet follow absolute pointer coordinates, animates layout `top`, uses a fixed ease-in 480ms snap, conflicts with CSS `transition: all`, and has no Reduced Motion path.  
**Expected feel:** direct, interruptible, bounded, quiet, and state-aware across collapsed / half / full.

---

## Prioritized findings

### P0 — Drag is not actually stateful or bounded
**Evidence:** `startY` is recorded but never used; `pointermove` always writes `sheet.style.top = event.clientY`.  
**Impact:** The sheet can jump to the finger’s viewport coordinate instead of preserving the grabbed offset. It can also move when no drag is active.  
**Fix direction:** Track `dragging`, initial sheet position, pointer delta, and clamp movement between valid snap bounds.

### P0 — Missing pointer capture / cancellation handling
**Evidence:** Only `pointerdown`, `pointermove`, and `pointerup` are handled.  
**Impact:** If the pointer leaves the sheet, the drag may desync. `pointercancel`, lost capture, multi-touch, and interrupted gestures are not handled.  
**Fix direction:** Use `setPointerCapture`, release capture, and handle `pointercancel` / `lostpointercapture`.

### P0 — Reduced Motion requirement is unmet
**Evidence:** Snap animation always travels spatially for `480ms` with `ease-in`.  
**Impact:** Users requesting reduced motion still get large movement.  
**Fix direction:** Preserve state feedback with minimal spatial travel: immediate snap or very short settle, plus non-spatial cues such as handle highlight, state label change, opacity/outline, or subtle elevation.

### P1 — Animating `top` is layout-heavy and less direct
**Evidence:** JS writes `style.top`; animation uses `{ top: ... }`; `offsetTop` is repeatedly read.  
**Impact:** This can force layout work and produce jank, especially during repeated daily use.  
**Fix direction:** Keep layout positions stable and animate `transform: translateY(...)`; read geometry once per gesture.

### P1 — Fixed `ease-in` snap feels wrong
**Evidence:** Snap uses `{ duration: 480, easing: "ease-in" }`.  
**Impact:** Ease-in accelerates toward the destination, often feeling like the sheet is being pulled away rather than settling. 480ms is likely too slow for frequent operational workflows.  
**Fix direction:** Use a short ease-out / spring-like settle. Duration should adapt to distance and velocity, with a calm cap.

### P1 — Gesture release ignores velocity and intent
**Evidence:** `nearestSnapPoint(sheet.offsetTop)` uses only current position.  
**Impact:** A deliberate flick toward full/closed may be ignored if the release point is closer to another state.  
**Fix direction:** Pick snap target using projected position: current position + velocity influence, with thresholds and hysteresis.

### P1 — Animation is not interruptible enough
**Evidence:** `if (animating) return;` blocks new gestures during snap.  
**Impact:** Users cannot correct an accidental snap until the animation finishes. This feels sluggish and non-direct.  
**Fix direction:** Allow interruption: cancel the current animation, commit current visual position, then start dragging from there.

### P1 — CSS conflicts with JS motion
**Evidence:** `.sheet { transition: all 300ms; }` and JS also animates `top`.  
**Impact:** Transitions can double-animate or animate unintended properties. `transition: all` can cause surprising motion when any style changes.  
**Fix direction:** Remove `transition: all`; transition only deliberate properties, e.g. `transform`, `opacity`, `box-shadow`.

### P2 — `:active { transform: scale(0.96); }` is mismatched to sheet behavior
**Evidence:** The whole sheet scales while the gesture also moves it.  
**Impact:** Scaling a large panel can feel jumpy, toy-like, and spatially noisy in a calm operations app. It may also visually detach the sheet from edges.  
**Fix direction:** Apply feedback to the drag handle or header only: slight handle darkening, elevation change, or grip compression.

### P2 — Fill-forwards can leave stale state
**Evidence:** `sheet.animate(..., { fill: "forwards" }).finished.then(...)` does not explicitly write the final style.  
**Impact:** The visual state may live in the animation effect rather than the element style. Later `offsetTop` or style reads can be misleading.  
**Fix direction:** On finish, write the canonical snap state to style/state, then cancel/clear the animation effect.

### P2 — No state model for collapsed / half / full
**Evidence:** The code computes a target but does not persist semantic state.  
**Impact:** Product state, accessibility announcements, restoration, and Reduced Motion feedback have no stable source of truth.  
**Fix direction:** Maintain a `currentState` enum and derive visual position from it.

---

## Concrete direct-manipulation moves

1. **Use a gesture state machine**
   - `idle → dragging → settling → idle`
   - Allow `settling → dragging` by interrupting the animation.

2. **Track delta, not absolute pointer position**
   - On down: record `pointerStartY` and `sheetStartY`.
   - On move: `nextY = clamp(sheetStartY + event.clientY - pointerStartY, fullY, collapsedY)`.

3. **Move with transforms**
   - Use `transform: translateY(...)`.
   - Avoid reading `offsetTop` during active movement.

4. **Clamp to valid range**
   - Prevent dragging past full/collapsed bounds, or use tiny resisted overscroll if desired.

5. **Choose snap target by intent**
   - Combine position, velocity, and direction.
   - Add hysteresis so small accidental moves do not change state.

6. **Use calm settling motion**
   - Prefer ease-out or spring-like deceleration.
   - Scale duration to distance, with a short maximum.
   - Avoid fixed long duration for every snap.

7. **Support Reduced Motion**
   - If reduced motion is requested:
     - Snap state immediately or with a very short fade/elevation change.
     - Avoid large animated travel.
     - Preserve clear feedback via handle state, label, shadow, or state announcement.

8. **Remove broad CSS transitions**
   - Replace `transition: all 300ms` with explicit, narrow transitions.
   - Avoid whole-sheet `scale()` while dragging.

9. **Handle gesture lifecycle**
   - Use pointer capture.
   - Handle `pointercancel`.
   - Ignore secondary pointers.
   - Clean up animation promises safely.

10. **Respect scroll interaction**
   - If the sheet contains scrollable content, decide when vertical movement scrolls content versus drags the sheet.
   - Common pattern: drag from handle/header, scroll inside body unless at scroll boundary.

---

## Verified / unverified boundaries

**Verified by static inspection**
- `startY` is unused.
- `pointermove` writes absolute `clientY` to `top`.
- The code animates `top`.
- The code uses fixed `480ms` `ease-in`.
- CSS uses `transition: all`.
- CSS scales the active sheet.
- No Reduced Motion branch is present.
- No pointer capture, cancel handling, velocity, clamping, or semantic state is visible.

**Unverified**
- Actual browser behavior.
- Device/touch feel.
- Frame rate or layout cost.
- Accessibility behavior.
- Interaction with internal scrolling.
- Real snap point math inside `nearestSnapPoint`.
- Visual design fit with the rest of the app.

---

## Smallest runtime validation plan

1. **Gesture correctness**
   - Drag from collapsed to half/full.
   - Release near boundaries.
   - Move pointer outside sheet during drag.
   - Cancel gesture mid-drag.
   - Try a second drag during snap animation.

2. **Intent detection**
   - Slow drag short distance.
   - Fast flick upward/downward.
   - Release exactly between snap points.
   - Confirm hysteresis prevents accidental state changes.

3. **Reduced Motion**
   - Enable reduced-motion setting.
   - Confirm state changes remain clear without large animated travel.

4. **Performance**
   - Record one drag and one snap.
   - Check for layout thrash, dropped frames, and long tasks.

5. **Scroll conflict**
   - Drag from handle.
   - Scroll sheet content.
   - Test dragging when internal scroll is at top and bottom.

6. **Accessibility/state**
   - Confirm collapsed / half / full state is programmatically represented.
   - Confirm keyboard path can change states.
   - Confirm visible state feedback is not motion-only.
