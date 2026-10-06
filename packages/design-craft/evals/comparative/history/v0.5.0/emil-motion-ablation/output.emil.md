## Evidence-labeled verdict

**Verdict: not production-ready for a calm, repeated-use operations sheet.**  
Static evidence shows the implementation treats the sheet as a scripted animation, not a directly manipulated object: it locks input during animation, animates layout properties, ignores release velocity, lacks reduced-motion behavior, and provides no accessible non-pointer path between collapsed / half / full states.

---

## Prioritized findings

### P0 — Direct manipulation is broken

**Evidence:** `pointermove` sets `sheet.style.top = event.clientY + "px"`.

- The sheet jumps to the pointer’s absolute viewport Y instead of preserving the grab offset.
- Movement is not gated by an active drag flag, so any pointer move over the sheet can reposition it.
- No `setPointerCapture`, so tracking can break when the pointer leaves the element.
- No `pointercancel` / `lostpointercapture` recovery.

**Impact:** The sheet will feel slippery, jumpy, and unsafe for repeated operational use.

---

### P0 — Animation is not interruptible

**Evidence:** `if (animating) return;` and `animating = true` until `.finished`.

- Users cannot grab the sheet mid-flight.
- Reversals must wait for the previous animation to complete.
- This creates a “dead” period exactly when users expect control.

**Fix direction:** cancel or retarget the current animation on `pointerdown`; always resume from the current presented position.

---

### P0 — Uses layout properties on the hot path

**Evidence:** drag and animation mutate `top`; release reads `sheet.offsetTop`.

- `top` changes can trigger layout.
- `offsetTop` forces layout reads.
- CSS `transition: all` may accidentally animate unrelated expensive properties.
- This is risky for a data-heavy operations screen with tables, filters, drawers, and autosave UI nearby.

**Fix direction:** use `transform: translateY(...)` for sheet motion; keep layout stable.

---

### P0 — Snap decision ignores velocity

**Evidence:** `nearestSnapPoint(sheet.offsetTop)`.

- A fast upward flick near the half point should be able to settle at full.
- A slow drag should settle based mostly on position.
- Current logic treats a flick and a slow release identically.

**Fix direction:** compute release velocity from recent pointer samples, project the likely resting point, then choose collapsed / half / full from that projected endpoint.

---

### P1 — Easing is wrong for a physical sheet

**Evidence:** `{ duration: 480, easing: "ease-in" }`.

- `ease-in` starts slowly after the user releases, creating a visible seam between drag and settle.
- Fixed duration ignores distance and velocity.
- 480ms can feel heavy for repeated desk work.

**Fix direction:** use a velocity-aware spring or equivalent critically damped settle; allow slight momentum only on flicks. Calm default should be quick, controlled, and non-bouncy.

---

### P1 — CSS conflicts with gesture motion

**Evidence:** `.sheet { transition: all 300ms; }` and `.sheet:active { transform: scale(0.96); }`.

- `transition: all` can fight JS-driven movement.
- `:active` scale changes the whole sheet while dragging, which can make dense controls feel unstable.
- Scaling a large operational panel may reduce readability and precision.
- It also collides with using `transform` for vertical motion unless transforms are composed carefully.

**Fix direction:** avoid global transitions on the moving sheet; apply small press feedback only to a handle or affordance, not the whole panel.

---

### P1 — Reduced Motion requirement is unmet

**Evidence:** no `prefers-reduced-motion` handling.

- Reduced Motion must preserve state feedback without large spatial travel.
- Current behavior would still perform large sheet travel.

**Fix direction:** in reduced motion, avoid long spatial interpolation. Use near-instant state changes plus subtle opacity, border, elevation, handle color, or status text changes.

---

### P1 — Missing accessible state model

**Evidence:** no keyboard path, semantic state, focus handling, or announcements shown.

Needed for collapsed / half / full:

- keyboard controls to expand, collapse, and move between snap points;
- visible focus on handle / controls;
- state exposed through text or ARIA;
- Escape behavior if dismissible;
- focus containment only if modal;
- restoration of focus after close;
- announcements for meaningful state changes, not every drag frame.

---

### P2 — Missing bounds and rubber-band behavior

**Evidence:** `sheet.style.top = event.clientY`.

- The sheet can be dragged outside valid collapsed / full bounds.
- Hard clamping would feel frozen; no resistance model is present.

**Fix direction:** clamp within valid range, with progressive resistance past edges if overscroll is allowed.

---

### P2 — Error recovery is fragile

**Evidence:** `.finished.then(...)` only clears `animating` on normal completion.

- If animation is canceled or interrupted, state may desync unless cancellation is handled.
- Pointer cancellation can leave stale drag state.

**Fix direction:** centralize sheet state: `idle`, `dragging`, `settling`; handle cancel paths explicitly.

---

## Concrete direct-manipulation moves

1. **Track an active pointer only**
   - On `pointerdown`: record `pointerId`, initial sheet Y, initial pointer Y, and grab offset.
   - Call `setPointerCapture(pointerId)`.

2. **Move 1:1 with the pointer**
   - `nextY = startSheetY + (event.clientY - startPointerY)`.
   - Apply with `transform: translateY(nextYpx)`.
   - Batch writes in `requestAnimationFrame`.

3. **Preserve grab location**
   - Do not snap the sheet’s top to `event.clientY`.
   - The point the user grabbed should remain under the pointer.

4. **Track velocity**
   - Store the last few `{ y, time }` samples.
   - On release, compute px/s velocity from recent movement.

5. **Choose snap by projected endpoint**
   - `projectedY = currentY + projectedTravelFromVelocity`.
   - Pick nearest of collapsed / half / full from `projectedY`, not raw `currentY`.

6. **Settle with velocity continuity**
   - Start the settle animation from the current presented transform.
   - Pass release velocity into the settle motion.
   - Do not use `ease-in` after a drag.

7. **Make animation interruptible**
   - On new `pointerdown`, cancel or retarget any active settle animation.
   - Never block input just because the sheet is moving.

8. **Constrain and resist**
   - Valid range: full ≤ y ≤ collapsed.
   - Within range: exact tracking.
   - Beyond range: rubber-band resistance or firm clamp, depending on product feel.

9. **Separate movement from press feedback**
   - Use transform for vertical movement on the sheet.
   - Put press scale / color feedback on the drag handle only.
   - Avoid scaling the entire dense operations panel.

10. **Reduced Motion behavior**
   - Snap state immediately or within a very short duration.
   - Preserve feedback through handle state, elevation, border, opacity, label, or live status.
   - Avoid elastic travel and large animated displacement.

---

## Verified / unverified boundaries

**Verified from static code:**

- Layout property `top` is used for drag and animation.
- `offsetTop` is read on release.
- Input is locked during animation.
- Snap selection is position-only.
- Easing is fixed `ease-in`.
- CSS uses `transition: all`.
- Whole sheet scales on active press.
- No reduced-motion branch is shown.
- No keyboard or semantic state path is shown.

**Not verified:**

- Actual frame rate or jank.
- Behavior on touch hardware, pen, trackpad, or mouse.
- Interaction with page scrolling or nested scroll regions.
- Screen reader output.
- Keyboard behavior elsewhere in the app.
- Real snap point geometry.
- Whether surrounding code adds accessibility or reduced-motion handling.
- Browser-specific WAAPI / CSS interaction details in this app.

---

## Smallest runtime validation plan

1. **Pointer drag sanity**
   - Press at top, middle, and handle positions.
   - Confirm no jump on grab.
   - Confirm the grabbed point stays visually attached to the pointer.

2. **Interruptibility**
   - Release toward half/full, then immediately grab during settle.
   - Expected: sheet follows immediately from current visual position.

3. **Velocity behavior**
   - Slow drag near halfway.
   - Fast flick from same position.
   - Expected: different targets when velocity clearly implies intent.

4. **Bounds**
   - Drag past full and collapsed limits.
   - Expected: no runaway position; resistance or controlled clamp.

5. **Reduced Motion**
   - Force reduced motion.
   - Expected: no large animated travel; state change remains perceivable.

6. **Keyboard**
   - Tab to handle/control.
   - Use Enter/Space/Arrow/Escape as designed.
   - Expected: visible focus and deterministic state changes.

7. **Accessibility state**
   - Confirm collapsed / half / full is exposed through label, state text, or announcement.
   - Confirm focus is not trapped unless the sheet is modal.

8. **Performance smoke**
   - During drag, inspect whether only compositor-friendly transforms change.
   - Expected: no repeated layout reads/writes on pointermove.
