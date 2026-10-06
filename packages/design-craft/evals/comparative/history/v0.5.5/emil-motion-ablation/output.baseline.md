## Evidence-labeled verdict

**Verdict: Not production-ready for a calm repeated-use operations sheet.**  
**[Static evidence]** The implementation moves the sheet with `top`, animates with `top`, uses `transition: all`, applies `ease-in` over `480ms`, lacks reduced-motion handling, lacks pointer capture/cancel handling, and does not model the three sheet states explicitly. It will likely feel laggy, non-direct, and hard to trust during repeated daily use.

---

## Prioritized findings

### P0 — Drag is not actually stateful or bounded
**[Static evidence]**
```js
startY = event.clientY;
```
is recorded but never used, and `pointermove` always runs:

```js
sheet.style.top = `${event.clientY}px`;
```

**Issue:** Any pointer move over the sheet can reposition it, even without an active drag state. The sheet jumps to the pointer’s viewport Y instead of preserving the offset between finger/cursor and sheet position.

**Impact:** Direct manipulation feels broken: the sheet may jump, drift, or move unintentionally.

---

### P0 — Uses `top`, causing layout work during drag and animation
**[Static evidence]**
```js
sheet.style.top = `${event.clientY}px`;
sheet.offsetTop
sheet.animate([{ top: ... }, { top: ... }])
```

**Issue:** `top` changes layout. `offsetTop` forces layout reads. During pointer movement this can cause jank, especially in an operations app with dense tables or drawers nearby.

**Impact:** Reduced responsiveness, possible dropped frames, and higher main-thread cost.

---

### P0 — Reduced Motion requirement is unmet
**[Static evidence]** No `prefers-reduced-motion` handling and no alternate state feedback.

**Issue:** The sheet always performs spatial travel over `480ms`.

**Impact:** Violates the stated requirement: “Reduced Motion must preserve state feedback without large spatial travel.”

---

### P1 — Motion curve and duration are inappropriate for direct manipulation
**[Static evidence]**
```js
{ duration: 480, easing: "ease-in" }
```

**Issue:** `ease-in` starts slowly after release, which makes the sheet feel like it hesitates. `480ms` is long for a high-frequency operations control.

**Impact:** The sheet will feel heavy and delayed rather than responsive and calm.

---

### P1 — Animation is not safely interruptible
**[Static evidence]**
```js
if (animating) return;
...
.finished.then(() => {
  animating = false;
});
```

**Issue:** New drags are blocked while animating. There is no cancellation path, no `pointercancel`, no `lostpointercapture`, and no rejected `.finished` handling.

**Impact:** The sheet can feel stuck or ignore the operator during repeated interactions.

---

### P1 — CSS transition conflicts with imperative animation
**[Static evidence]**
```css
.sheet { transition: all 300ms; }
```

**Issue:** `transition: all` may animate unrelated properties and can conflict with JS-driven `top` changes or state changes.

**Impact:** Unpredictable timing, accidental animations, and harder performance control.

---

### P1 — `:active` scale is a poor sheet affordance
**[Static evidence]**
```css
.sheet:active { transform: scale(0.96); }
```

**Issue:** Scaling the whole sheet during active press can make content appear to shrink, shift, or blur. It also competes with the sheet’s positional motion.

**Impact:** Feels decorative rather than operational; may reduce perceived stability.

---

### P2 — Snap behavior lacks velocity and intent
**[Static evidence]**
```js
const target = nearestSnapPoint(sheet.offsetTop);
```

**Issue:** Snap is based only on final position. It does not account for drag velocity, direction, thresholds, or hysteresis.

**Impact:** Fast intentional flicks may snap to the wrong state; small accidental movements may overcommit.

---

### P2 — No explicit collapsed / half / full state model
**[Static evidence]** State is inferred from `offsetTop`; no `data-state`, enum, ARIA state, or source of truth.

**Issue:** Visual state, accessibility state, persistence, and recovery are not represented.

**Impact:** Harder to restore state, announce state, test behavior, or coordinate with filters/table/drawer UI.

---

## Concrete direct-manipulation moves

1. **Use transform-based positioning**
   - Replace `top` mutation with `transform: translateY(...)`.
   - Keep snap points as numeric translate values.
   - Avoid layout reads during drag.

2. **Track an explicit drag session**
   - On `pointerdown`: set `dragging = true`, store `startPointerY`, `startSheetY`, and call `setPointerCapture(event.pointerId)`.
   - On `pointermove`: ignore unless `dragging`.
   - Compute `nextY = clamp(startSheetY + event.clientY - startPointerY, fullY, collapsedY)`.

3. **Separate drag movement from settle animation**
   - During drag: no CSS transition.
   - On release: animate from current transform to target transform.
   - Use `requestAnimationFrame` or a single compositor-friendly transform write per frame.

4. **Make the settle animation responsive**
   - Prefer a shorter duration, roughly `180–260ms` depending on distance.
   - Use an ease-out or responsive curve, not `ease-in`.
   - Distance-aware timing should avoid long travel feeling sluggish.

5. **Make animation interruptible**
   - Store the active animation object.
   - On a new pointerdown, cancel the current animation and continue from the current visual position.
   - Handle `pointercancel`, `lostpointercapture`, and rejected animation promises.

6. **Snap by intent, not only position**
   - Use both position and velocity.
   - Slow drag: snap to nearest collapsed / half / full point.
   - Fast flick: bias toward the direction of travel.
   - Add small hysteresis around each state to avoid jitter.

7. **Add explicit state**
   - Maintain `state = "collapsed" | "half" | "full"`.
   - Reflect it with `data-state`.
   - Use that state for styling, persistence, keyboard actions, and announcements.

8. **Replace whole-sheet active scaling**
   - Do not scale the entire sheet.
   - Use subtle handle feedback instead: handle color, elevation, or a small handle compression.
   - Keep content spatially stable.

9. **Implement Reduced Motion behavior**
   - Under reduced motion, avoid large animated travel.
   - Snap immediately or use a very short transform transition.
   - Preserve feedback with state label changes, handle emphasis, shadow/outline change, or a brief non-spatial opacity/color cue.

10. **Constrain CSS transitions**
   - Replace `transition: all 300ms` with explicit properties only.
   - Example: transition only `box-shadow`, `background-color`, or handle affordance properties.
   - Do not globally transition layout or transform during active dragging.

---

## Verified / unverified boundaries

### Verified from static code
- The implementation mutates `top` during drag.
- The implementation animates `top` on release.
- `startY` is unused.
- `pointermove` is not gated by an active drag flag.
- No reduced-motion branch is present.
- `transition: all` is present.
- The sheet scales on `:active`.
- Animation blocks new pointerdown while `animating` is true.

### Not verified
- Actual frame rate or jank on target hardware.
- Whether `nearestSnapPoint()` handles collapsed / half / full correctly.
- Whether surrounding layout isolates the sheet from table reflow.
- Keyboard support, ARIA behavior, focus management, or screen reader announcements.
- Real touch behavior on mobile/tablet browsers.
- Behavior with nested scroll content inside the sheet.

---

## Smallest runtime validation plan

1. **Pointer interaction**
   - Drag from collapsed to half and full.
   - Confirm no initial jump.
   - Confirm the sheet follows the pointer with stable offset.
   - Confirm pointer leaving the handle/sheet does not break the drag.

2. **Snap behavior**
   - Test slow drags near each threshold.
   - Test fast upward and downward flicks.
   - Confirm intended collapsed / half / full state is reached.

3. **Interruptibility**
   - Start a snap animation, then immediately drag again.
   - Confirm the sheet responds without waiting for the previous animation to finish.

4. **Reduced Motion**
   - Enable reduced motion.
   - Trigger all state changes.
   - Confirm there is no large animated travel, while state feedback remains visible.

5. **Performance smoke**
   - Drag repeatedly over dense page content.
   - Check for visible jank, delayed pointer following, or layout shifts.

6. **Accessibility smoke**
   - Operate the sheet with keyboard.
   - Confirm visible focus, reachable controls, and understandable collapsed / half / full state feedback.
