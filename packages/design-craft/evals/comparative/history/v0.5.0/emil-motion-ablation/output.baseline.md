## Verdict

**High risk for a calm, repeatedly used operations surface.**  
**Evidence basis:** static code/CSS only. The implementation likely feels jumpy, blocks interruption, creates layout work during drag, ignores Reduced Motion, and lacks accessible non-pointer equivalents.

## Prioritized findings

1. **Direct manipulation is not anchored to the user’s grab point**
   - **Evidence:** `startY = event.clientY` is stored but never used; `pointermove` sets `sheet.style.top = event.clientY`.
   - **Impact:** the sheet can jump so its top aligns with the pointer instead of preserving the offset where the user grabbed it.
   - **Priority:** P0.

2. **Drag updates layout properties on every pointer move**
   - **Evidence:** `sheet.style.top = ...`; `sheet.offsetTop` read before animation.
   - **Impact:** repeated layout/reflow risk, worse on large operational pages with tables, filters, or drawers.
   - **Priority:** P0.

3. **Movement is not gated by active drag state**
   - **Evidence:** `pointermove` always mutates the sheet, even without a valid `pointerdown`.
   - **Impact:** accidental movement, hover/pointer noise, broken behavior after canceled gestures.
   - **Priority:** P0.

4. **No pointer capture or cancel handling**
   - **Evidence:** no `setPointerCapture`, `lostpointercapture`, `pointercancel`, or cleanup path.
   - **Impact:** dragging outside the sheet can leave stale state or missed releases.
   - **Priority:** P0.

5. **Reduced Motion requirement is unmet**
   - **Evidence:** fixed `duration: 480`, large spatial `top` animation, `.sheet { transition: all 300ms; }`.
   - **Impact:** users requesting reduced motion still receive full travel; state feedback is not preserved in a quieter way.
   - **Priority:** P0.

6. **Animation curve fights perceived control**
   - **Evidence:** `easing: "ease-in"`.
   - **Impact:** snap starts slowly and accelerates away from the user, which can feel like loss of control. Sheet snaps usually need responsive deceleration/ease-out or spring-like settling.
   - **Priority:** P1.

7. **480ms is likely too slow for repeated operations**
   - **Evidence:** fixed 480ms snap.
   - **Impact:** creates accumulated waiting and sluggishness across repeated daily use.
   - **Priority:** P1.

8. **`transition: all` can conflict with gesture animation**
   - **Evidence:** `.sheet { transition: all 300ms; }` plus WAAPI `sheet.animate(...)`.
   - **Impact:** unrelated properties may animate unexpectedly; `top` changes during drag may be transitioned depending cascade/computed state.
   - **Priority:** P1.

9. **Final visual state may diverge from DOM style state**
   - **Evidence:** WAAPI uses `fill: "forwards"` but does not commit final `top`/state after finishing.
   - **Impact:** future reads, layout, and accessibility state may disagree with what is painted.
   - **Priority:** P1.

10. **Animation is not interruptible**
   - **Evidence:** `if (animating) return;`; no cancel/re-target path.
   - **Impact:** users cannot reverse course mid-snap, which weakens direct manipulation.
   - **Priority:** P1.

11. **Snap logic lacks velocity, thresholds, hysteresis, and state semantics**
   - **Evidence:** `nearestSnapPoint(sheet.offsetTop)` only.
   - **Impact:** flicks, small drags, and intentional state changes may resolve incorrectly.
   - **Priority:** P1.

12. **Active scale can distort content and compound motion**
   - **Evidence:** `.sheet:active { transform: scale(0.96); }`.
   - **Impact:** text/buttons shrink under the pointer; scale may conflict with translate-based movement if later added.
   - **Priority:** P2.

13. **Accessibility contract is absent from snippet**
   - **Evidence:** no keyboard path, state labels, focus management, or semantic state updates shown.
   - **Impact:** collapsed/half/full states may be pointer-only and silent to assistive tech.
   - **Priority:** P0 if not implemented elsewhere; otherwise unverified.

## Concrete direct-manipulation moves

- Use **transform-based position**, not `top`:
  - `translateY(var(--sheet-y))` or inline `transform: translate3d(0, ypx, 0)`.
- On `pointerdown`:
  - store `pointerId`, `startY`, current sheet Y, current state;
  - call `setPointerCapture`;
  - cancel any running animation;
  - disable transition while dragging;
  - add temporary `will-change: transform`.
- On `pointermove`:
  - ignore events unless actively dragging with the captured pointer;
  - compute `nextY = clamp(startSheetY + event.clientY - startY, fullY, collapsedY)`;
  - update via `requestAnimationFrame`;
  - avoid layout reads in the move loop.
- On `pointerup` / `pointercancel`:
  - compute velocity from recent samples;
  - project intent slightly, then resolve to collapsed/half/full using thresholds and hysteresis;
  - animate from current transform to target transform;
  - commit final state in real style/data state after completion.
- Make snap animation feel controlled:
  - use shorter duration, distance-aware duration, or spring-like settling;
  - prefer ease-out/responsive easing over `ease-in`;
  - allow interruption during snap.
- Reduced Motion:
  - avoid large animated travel;
  - jump or use very short transform duration;
  - preserve state feedback with label change, handle position, elevation/border emphasis, opacity/summary reveal, or focus-visible state.
- Replace `:active { scale(0.96) }` with calmer feedback:
  - handle highlight, slight shadow/elevation change, border/token change, or small non-spatial affordance.
- Provide non-pointer controls:
  - visible drag handle as a button;
  - keyboard: Enter/Space cycle or toggle, Arrow/Page move between states, Home/End full/collapsed, Escape collapse/close where appropriate;
  - update accessible name/state text such as “Sheet: half expanded”.
- Preserve operational calm:
  - avoid bounce/overshoot unless extremely subtle;
  - keep state continuity clear;
  - ensure focus does not jump unexpectedly when moving between collapsed/half/full.

## Verified / unverified boundaries

**Verified from static snippet**
- Uses `top` during drag and animation.
- Reads `offsetTop`.
- Uses fixed 480ms `ease-in`.
- Uses `transition: all 300ms`.
- Stores but does not use `startY`.
- Does not show pointer capture, cancel handling, Reduced Motion, keyboard support, or state announcement.

**Unverified**
- Actual snap point math.
- Real CSS cascade and layout containment.
- Whether accessibility is implemented elsewhere.
- Actual device behavior on touch, pen, trackpad, or screen reader.
- Real performance cost on the product page.
- Browser-specific WAAPI behavior in the deployed environment.

## Smallest runtime validation plan

1. **Interaction smoke**
   - Drag from handle, content, and edge.
   - Release near each snap boundary.
   - Drag outside the sheet before release.
   - Interrupt a snap mid-animation.

2. **Reduced Motion check**
   - Enable reduced motion.
   - Confirm no large spatial travel.
   - Confirm state feedback remains visible and understandable.

3. **Keyboard check**
   - Reach handle by Tab.
   - Move collapsed ↔ half ↔ full without pointer.
   - Confirm focus order remains predictable.

4. **Performance check**
   - Record one drag on a populated page.
   - Look for layout recalculation during move.
   - Confirm transform-only updates and no long tasks.

5. **State correctness check**
   - After each snap, verify visual position, internal state, focus behavior, and accessible state text agree.
