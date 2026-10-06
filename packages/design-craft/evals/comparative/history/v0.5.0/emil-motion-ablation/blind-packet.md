# Blind comparative judgment
Judge only the supplied outputs. Do not infer which skill produced a label. Apply the machine-readable scorecard exactly, recompute each total from criterion points, and return only JSON matching the supplied schema.

## Task prompt

# Gesture-sheet motion critique

Critique this static gesture-sheet implementation. Do not edit files and do not
claim browser or device validation.
Do not name, cite, or reveal any skill, repository, author, or upstream source
in the response; the output will be judged blind.

```js
let animating = false;

sheet.addEventListener("pointerdown", (event) => {
  if (animating) return;
  startY = event.clientY;
});

sheet.addEventListener("pointermove", (event) => {
  sheet.style.top = `${event.clientY}px`;
});

sheet.addEventListener("pointerup", () => {
  animating = true;
  const target = nearestSnapPoint(sheet.offsetTop);
  sheet.animate(
    [{ top: `${sheet.offsetTop}px` }, { top: `${target}px` }],
    { duration: 480, easing: "ease-in", fill: "forwards" },
  ).finished.then(() => {
    animating = false;
  });
});
```

```css
.sheet { transition: all 300ms; }
.sheet:active { transform: scale(0.96); }
```

Product context: a calm web operations app used repeatedly during the day. The
sheet has collapsed, half, and full states. Reduced Motion must preserve state
feedback without large spatial travel.

Return a concise evidence-labeled verdict, prioritized findings, concrete
direct-manipulation moves, verified/unverified boundaries, and the smallest
runtime validation plan. Stay within 150 lines.


## Human-readable scorecard

# Comparative scorecard

Generated from `scorecard.json`; do not edit by hand.

| Criterion | Weight | Full credit |
|---|---:|---|
| Evidence honesty | 15 | Labels the input as static and avoids smoothness or runtime claims. |
| Motion necessity | 10 | Separates causal feedback from decorative or unnecessary animation. |
| Direct manipulation | 15 | Catches input lockout, pointer capture, grab offset, and one-to-one tracking. |
| Interruption and presentation value | 15 | Requires interruption from the current on-screen value without jumps. |
| Velocity and projection | 15 | Preserves release velocity, units, projected endpoints, and snap selection. |
| Property and performance discipline | 10 | Rejects layout-property motion, transition-all, and conflicting transform ownership. |
| Accessibility | 10 | Defines a non-vestibular Reduced Motion path with preserved feedback. |
| Actionability and scope | 10 | Gives prioritized implementation moves and a minimal runtime plan within the output budget. |
| **Total** | **100** | |


## Machine-readable scorecard

```json
{
  "schema": "design-craft.comparative-scorecard.v1",
  "total": 100,
  "criteria": [
    {
      "id": "evidence_honesty",
      "label": "Evidence honesty",
      "weight": 15,
      "full_credit": "Labels the input as static and avoids smoothness or runtime claims."
    },
    {
      "id": "motion_necessity",
      "label": "Motion necessity",
      "weight": 10,
      "full_credit": "Separates causal feedback from decorative or unnecessary animation."
    },
    {
      "id": "direct_manipulation",
      "label": "Direct manipulation",
      "weight": 15,
      "full_credit": "Catches input lockout, pointer capture, grab offset, and one-to-one tracking."
    },
    {
      "id": "interruption",
      "label": "Interruption and presentation value",
      "weight": 15,
      "full_credit": "Requires interruption from the current on-screen value without jumps."
    },
    {
      "id": "velocity_projection",
      "label": "Velocity and projection",
      "weight": 15,
      "full_credit": "Preserves release velocity, units, projected endpoints, and snap selection."
    },
    {
      "id": "performance",
      "label": "Property and performance discipline",
      "weight": 10,
      "full_credit": "Rejects layout-property motion, transition-all, and conflicting transform ownership."
    },
    {
      "id": "accessibility",
      "label": "Accessibility",
      "weight": 10,
      "full_credit": "Defines a non-vestibular Reduced Motion path with preserved feedback."
    },
    {
      "id": "actionability",
      "label": "Actionability and scope",
      "weight": 10,
      "full_credit": "Gives prioritized implementation moves and a minimal runtime plan within the output budget."
    }
  ]
}
```

## Required judgment schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["results", "winner", "rationale"],
  "properties": {
    "results": {
      "type": "array",
      "minItems": 3,
      "maxItems": 3,
      "items": {
        "type": "object",
        "required": ["label", "criteria", "total", "summary"],
        "properties": {
          "label": {"enum": ["A", "B", "C"]},
          "criteria": {
            "type": "object",
            "required": [
              "evidence_honesty",
              "motion_necessity",
              "direct_manipulation",
              "interruption",
              "velocity_projection",
              "performance",
              "accessibility",
              "actionability"
            ],
            "additionalProperties": false,
            "properties": {
              "evidence_honesty": {"type": "integer", "minimum": 0, "maximum": 15},
              "motion_necessity": {"type": "integer", "minimum": 0, "maximum": 10},
              "direct_manipulation": {"type": "integer", "minimum": 0, "maximum": 15},
              "interruption": {"type": "integer", "minimum": 0, "maximum": 15},
              "velocity_projection": {"type": "integer", "minimum": 0, "maximum": 15},
              "performance": {"type": "integer", "minimum": 0, "maximum": 10},
              "accessibility": {"type": "integer", "minimum": 0, "maximum": 10},
              "actionability": {"type": "integer", "minimum": 0, "maximum": 10}
            }
          },
          "total": {"type": "integer", "minimum": 0, "maximum": 100},
          "summary": {"type": "string", "minLength": 20}
        },
        "additionalProperties": false
      }
    },
    "winner": {"enum": ["A", "B", "C"]},
    "rationale": {"type": "string", "minLength": 40}
  },
  "additionalProperties": false
}
```

## Output A

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


## Output B

## Evidence-labeled verdict

**Verdict: Block for production gesture use.**  
**[Static evidence]** The snippet animates layout `top`, uses `transition: all`, locks input during settle, lacks Reduced Motion handling, and does not preserve direct-manipulation continuity. For a calm, repeated-use operations app, this will likely feel jumpy, delayed, and inaccessible unless reworked around interruptible transform-based motion.

---

## Prioritized findings

### P0 — Drag is not true direct manipulation
**[Static evidence]**
- `startY` is recorded but never used.
- `pointermove` sets `sheet.style.top = event.clientY`, so the sheet’s top edge jumps to the pointer instead of preserving the grab offset.
- `pointermove` is unguarded; it can run even when no active drag is established.

**Impact**
- The sheet can snap under the pointer, move accidentally, and fail the “object stays attached to my hand” expectation.

**Fix direction**
- Track `pointerId`, `isDragging`, `grabOffsetY = pointerY - currentSheetY`, and set position as `pointerY - grabOffsetY`.

---

### P0 — Input lockout breaks interruption
**[Static evidence]**
- `if (animating) return;` prevents grabbing the sheet while it is settling.
- The settle animation always starts from `sheet.offsetTop`, not necessarily the current presented visual value.

**Impact**
- Operators cannot reverse or correct a motion mid-flight. This is especially poor for collapsed/half/full sheets used repeatedly.

**Fix direction**
- Allow interruption: cancel/read the current presentation value, preserve current velocity, and retarget from the on-screen position without a jump.

---

### P0 — Layout animation is a performance hazard
**[Static evidence]**
- Drag and settle both mutate/animate `top`.
- `nearestSnapPoint(sheet.offsetTop)` reads layout after layout-affecting writes.
- `.sheet { transition: all 300ms; }` means pointer-driven `top` changes may be transitioned instead of tracking 1:1.

**Impact**
- High risk of layout/reflow on the gesture hot path and perceived lag, especially in a dense operations app with large tables behind or near the sheet.

**Fix direction**
- Use compositor-friendly `transform: translateY(...)` for drag and settle.
- Restrict transitions to explicit properties; avoid `transition: all`.

---

### P0 — Reduced Motion requirement is missing
**[Static evidence]**
- No `prefers-reduced-motion` branch.
- Settle uses large spatial travel with `duration: 480`.

**Impact**
- Fails the stated requirement: Reduced Motion must preserve state feedback without large spatial travel.

**Fix direction**
- In Reduced Motion, snap state immediately or with a very short non-spatial cue: handle color, shadow, border, opacity, label/state text, or a ≤80–120ms subdued transform with no overshoot.

---

### P1 — Settle motion feels backwards for user-triggered UI
**[Static evidence]**
- `duration: 480`
- `easing: "ease-in"`

**Impact**
- `ease-in` starts slowly, delaying feedback exactly when the user releases. `480ms` is heavy for a repeatedly used operations control.

**Fix direction**
- Use a responsive ease-out/spring-like settle. Default to no bounce or very low bounce. Target crisp completion, commonly around 200–350ms depending on distance and velocity.

---

### P1 — No release velocity or bounded projection
**[Static evidence]**
- Target is chosen only from `sheet.offsetTop`.
- No recent pointer history or release velocity is measured.

**Impact**
- A quick flick and a slow drag to the same release point behave identically. This may feel dead for a gesture sheet.

**Fix direction**
- Measure release velocity in CSS px/s from recent pointer samples.
- Keep target semantics explicit:
  - If the product wants nearest-position snapping, keep `nearestSnapPoint(currentY)`.
  - If momentum targeting is desired, compute a bounded projected endpoint and choose the nearest snap point to that endpoint.
- In both cases, feed measured release velocity into the settle animation.

---

### P1 — Snap bounds and overdrag behavior are absent
**[Static evidence]**
- `sheet.style.top = event.clientY` has no clamp.
- No collapsed/half/full boundary resistance.

**Impact**
- The sheet can be dragged into invalid positions or hit hard stops.

**Fix direction**
- Clamp to valid snap range, or apply soft rubber-band resistance outside bounds.
- Add hysteresis so tiny pointer noise does not switch states.

---

### P1 — Animation state can get stuck
**[Static evidence]**
- `.finished.then(...)` clears `animating`, but there is no `catch`/`finally`.
- If the animation is cancelled or rejects, `animating` can remain `true`.

**Impact**
- The sheet may become permanently non-interactive after an interrupted/cancelled animation.

**Fix direction**
- Use cancellation-safe cleanup with `finally`, or remove the global lock by making animation interruptible.

---

### P2 — Transform ownership conflict is likely
**[Static evidence]**
- CSS uses `.sheet:active { transform: scale(0.96); }`.
- A proper drag implementation should likely use `transform: translateY(...)`.

**Impact**
- Press scale and drag translate will overwrite each other unless composed deliberately.

**Fix direction**
- Use separate layers:
  - outer wrapper owns `translateY`
  - inner surface owns press scale / visual feedback

---

### P2 — Accessibility state model is not represented in the snippet
**[Static evidence]**
- Pointer handlers only.
- No visible keyboard controls, ARIA state, focus handling, or semantic state announcement in the shown code.

**Impact**
- Keyboard-heavy operators need non-pointer ways to move between collapsed, half, and full states.

**Fix direction**
- Provide keyboard commands/buttons for each snap state.
- Expose current state via accessible text/state.
- Preserve focus when the sheet expands/collapses.
- Keep focus-visible styling independent of motion.

---

## Concrete direct-manipulation moves

1. Replace `top` positioning with `transform: translateY(var(--sheet-y))`.
2. On `pointerdown`, capture pointer, store `pointerId`, current visual Y, and `grabOffsetY`.
3. Do not move until an intent threshold, roughly 8–12 CSS px, unless the handle is explicitly grabbed.
4. During drag, update only transform; batch writes with `requestAnimationFrame` if needed.
5. Keep recent `{time, y}` samples and compute release velocity in CSS px/s.
6. On release, choose target from explicit product semantics: nearest current snap point or authorized projected endpoint.
7. Settle from the current presentation value with initial release velocity; allow re-grab during settle.
8. Separate transform layers so sheet translation and press feedback do not overwrite each other.
9. Replace `transition: all` with scoped transitions, e.g. handle/background/shadow only.
10. Add Reduced Motion behavior: no large travel, no bounce, immediate state change plus short color/shadow/handle feedback.

---

## Verified / unverified boundaries

**Static-verified from the provided snippet**
- Layout property `top` is used for drag and settle.
- `transition: all` is present.
- `ease-in` and `480ms` are used for settle.
- Reduced Motion is not shown.
- Pointer capture, velocity tracking, bounds, hysteresis, keyboard handling, and ARIA state are not shown.
- Input is blocked while `animating` is true.

**Unverified**
- Actual frame rate, jank, smoothness, and device feel.
- Whether other files add keyboard support, ARIA semantics, focus management, or Reduced Motion.
- Whether `nearestSnapPoint` contains clamping or state semantics.
- Whether the sheet is isolated enough that layout animation is cheap in the real page.
- Browser-specific WAAPI/CSS transition interaction in the deployed environment.

---

## Smallest runtime validation plan

1. Test collapsed → half → full and back with slow drag, quick flick, and tiny accidental movement.
2. Re-grab during settle; verify no jump and no input lockout.
3. Drag beyond top/bottom bounds; verify clamp or soft resistance.
4. Enable Reduced Motion; verify state feedback remains clear without large travel.
5. Keyboard-only pass: move among all three states, confirm focus remains visible and predictable.
6. Performance pass under realistic page load: confirm pointermove does not trigger repeated layout and the sheet tracks the pointer at display rate.
7. Cancellation pass: interrupt/cancel animation repeatedly and verify the sheet never gets stuck.


## Output C

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
