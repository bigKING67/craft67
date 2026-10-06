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

## Evidence-labeled verdict

**Verdict: not production-ready for a calm repeated-use operations sheet.**  
Static evidence shows the implementation is visually plausible but fails the core requirements for a gesture sheet: direct manipulation, interruptibility, velocity-aware snapping, reduced-motion behavior, and compositor-safe performance. It will likely feel laggy, jumpy, and tiring in daily use.

## Prioritized findings

1. **Drag is not 1:1 with the grabbed sheet position** `[code]`  
   `pointermove` sets `sheet.style.top = event.clientY`, so the sheet’s top jumps to the pointer instead of preserving the grab offset. `startY` is captured but never used.

2. **Input is locked during animation** `[code]`  
   `if (animating) return` prevents grabbing the sheet mid-flight. A good sheet must be interruptible: users should be able to reverse or redirect it immediately.

3. **Motion uses layout properties instead of transforms** `[code/css]`  
   Animating `top` and reading `offsetTop` can trigger layout work. For a frequently used operations surface, the sheet should move with `transform: translateY(...)` on the compositor path.

4. **CSS transition conflicts with gesture tracking** `[css]`  
   `.sheet { transition: all 300ms; }` means every `top` update during drag may be eased instead of following the pointer. This directly undermines “finger/mouse glued to sheet” behavior.

5. **Release animation has the wrong feel** `[code]`  
   `duration: 480` + `ease-in` starts slowly and accelerates into the snap point. On release, the sheet should continue from the user’s release velocity, not pause then accelerate.

6. **Snap decision ignores velocity and intent** `[code]`  
   `nearestSnapPoint(sheet.offsetTop)` only considers final position. A flick toward full/collapsed should project momentum and choose the state the gesture is heading toward.

7. **No pointer capture or gesture ownership** `[code]`  
   The implementation does not call `setPointerCapture`, track `pointerId`, handle `pointercancel`, or ignore stray moves. The sheet can lose tracking when the pointer leaves its bounds.

8. **`fill: "forwards"` risks state mismatch** `[code]`  
   The animation may visually end at `target` while the actual layout/style state remains stale. Future reads from `offsetTop` can disagree with what the user sees.

9. **Reduced Motion is absent** `[code/css/context]`  
   There is no `prefers-reduced-motion` path. The product requirement says state feedback must remain without large spatial travel; this implementation always performs spatial movement.

10. **`transition: all` is too broad and unsafe** `[css]`  
   It can accidentally animate size, color, shadow, layout, or state changes. Gesture surfaces need explicit transitions only for intended properties.

11. **`:active { transform: scale(0.96) }` is crude feedback** `[css]`  
   Scaling the whole sheet while dragging can make dense operational content feel unstable. Feedback should be subtle and stateful, not shrink the entire work surface.

12. **No boundary behavior** `[code]`  
   Dragging past collapsed/full limits has no resistance or clamping. Hard edges or unbounded movement will feel broken.

## Concrete direct-manipulation moves

- Track `isDragging`, `pointerId`, `grabOffset`, current `y`, and recent position/time samples.
- On `pointerdown`, stop the current animation, read the live visual position, capture the pointer, and begin from that exact position.
- During drag, update `transform: translateY(...)` directly or inside `requestAnimationFrame`.
- Preserve grab offset: `nextY = event.clientY - grabOffset`.
- Apply soft rubber-band resistance beyond min/max snap bounds.
- On release, compute velocity from recent samples.
- Project the release endpoint using velocity, then choose collapsed / half / full from the projected position, not just the current position.
- Animate to the snap point with a spring-like curve or velocity-aware animation; avoid fixed-duration `ease-in`.
- Make animations interruptible: new pointerdown cancels/re-targets from the current presented value.
- Store the committed state explicitly: `collapsed | half | full`, not just a pixel value.
- Replace `.sheet { transition: all 300ms; }` with explicit, non-gesture transitions only.
- Use subtle press/drag feedback: handle highlight, shadow/material change, or tiny handle compression instead of scaling the full sheet.
- For Reduced Motion, avoid large animated travel: jump/shorten the spatial move and preserve feedback with opacity, outline, handle state, label/state announcement, or short 80–120ms non-elastic transition.

## Verified / unverified boundaries

**Verified from static code:**

- Uses `top` for drag and animation.
- Uses `offsetTop` for snap calculation.
- Blocks pointerdown while `animating`.
- Does not use pointer capture.
- Does not use velocity.
- Does not implement Reduced Motion.
- Applies `transition: all`.
- Applies full-sheet active scale.

**Not verified without runtime/device testing:**

- Actual frame rate or dropped frames.
- Whether CSS transition visibly lags every pointermove in the target browser.
- Exact mismatch behavior of `offsetTop` after `fill: "forwards"`.
- Touch, pen, mouse, trackpad, and high-refresh behavior.
- Screen reader, keyboard, focus, and announcement behavior.
- Whether snap points match the real collapsed / half / full layout.

## Smallest runtime validation plan

1. **Interrupt test:** start a snap animation, immediately grab the moving sheet, confirm it follows without waiting.  
2. **Grab-offset test:** press near the handle and lower content area; confirm no jump on first move.  
3. **Velocity test:** slowly drag vs. flick upward/downward; confirm target state follows intent.  
4. **Reduced Motion test:** enable reduced motion; confirm no large spatial travel while state feedback remains clear.  
5. **Performance smoke:** record a drag; confirm movement stays on transform/compositor path with no layout-heavy per-frame work.  
6. **Pointer robustness:** drag outside sheet bounds, cancel, release off-element; confirm state remains consistent.


## Output B

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


## Output C

## Verdict

**Block for production motion quality.** Static evidence shows a sheet that is visually movable, but not yet a reliable direct-manipulation control for a high-frequency operations app: it animates layout properties, locks input during settle, lacks velocity/interrupt handling, has transform ownership conflicts, and has no shown Reduced Motion path.

## Prioritized findings

**P0 — Drag is not true 1:1 direct manipulation.**  
- **Evidence:** `pointerdown` records `startY`, but `pointermove` ignores it and sets `sheet.style.top = event.clientY`.  
- **Impact:** The sheet can jump so its top edge follows the pointer instead of preserving the grab offset. This breaks physical continuity and makes repeated use feel imprecise.

**P0 — Interaction is non-interruptible.**  
- **Evidence:** `if (animating) return;` blocks new drags during settle; the WAAPI animation starts from `sheet.offsetTop`, not the current presentation value of an in-flight animation.  
- **Impact:** Users cannot grab and redirect the sheet mid-flight. A calm operations surface should feel responsive, not modal or locked.

**P0 — Layout-property motion is on the gesture hot path.**  
- **Evidence:** `sheet.style.top = ...`, keyframes animate `top`, and `nearestSnapPoint(sheet.offsetTop)` reads layout. CSS also has `transition: all 300ms`.  
- **Impact:** This risks layout/reflow work during every pointer move and during settle. Static code cannot prove jank, but the implementation chooses properties that are high-risk for a draggable panel.

**P1 — Release physics are missing.**  
- **Evidence:** `pointerup` chooses `nearestSnapPoint(sheet.offsetTop)` only; there is no recent pointer history, release velocity, projected endpoint, damping, or velocity handoff.  
- **Impact:** Slow drags and quick flicks resolve the same way if they end at the same position, which makes the sheet feel mechanical rather than physically responsive.

**P1 — Easing/duration are poorly matched to user-triggered settle.**  
- **Evidence:** `{ duration: 480, easing: "ease-in" }`.  
- **Impact:** `ease-in` delays the response at the moment the user releases. `480ms` may be acceptable for some drawer travel, but it is long for a repeated operational control unless distance-scaled or spring-based.

**P1 — Transform ownership conflict.**  
- **Evidence:** `.sheet:active { transform: scale(0.96); }` while the drag should ideally use `transform: translateY(...)`.  
- **Impact:** If translate and press scale are both applied to `.sheet`, one can overwrite the other unless composed deliberately or split across wrapper layers.

**P1 — Reduced Motion requirement is not met in the shown code.**  
- **Evidence:** No `prefers-reduced-motion` branch; the same spatial travel and `480ms` settle apply to all users.  
- **Impact:** The product requirement says Reduced Motion must preserve state feedback without large spatial travel. This implementation has no shown alternative feedback channel.

**P2 — Pointer capture and gesture boundaries are absent.**  
- **Evidence:** No `setPointerCapture`, intent threshold, cancellation handling, boundary resistance, or multi-pointer policy is shown.  
- **Impact:** Tracking may be lost when the pointer leaves the sheet; taps can become drags; overdrag behavior is undefined.

## Concrete direct-manipulation moves

1. **Represent sheet state as snap-state + translation, not `top`.**  
   Use snap points for `collapsed | half | full`, and render movement with `transform: translate3d(0, var(--sheet-y), 0)`.

2. **Preserve the grab offset.**  
   On pointer down, read the current presentation Y and store `grabOffset = event.clientY - currentSheetY`; on move, set `nextY = event.clientY - grabOffset`.

3. **Capture and qualify the gesture.**  
   Use pointer capture after an `8–12px` vertical intent threshold, ignore secondary pointers, and release capture on end/cancel.

4. **Remove input lockout.**  
   Do not reject pointerdown during settle. Stop/cancel the current animation, read the current visual position, and start the new drag from that value.

5. **Measure velocity separately from target selection.**  
   Track recent `{ y, time }` samples in CSS px and monotonic ms; compute release velocity in CSS px/s.

6. **Keep current snap semantics unless product signs off on momentum targeting.**  
   If existing behavior is “nearest release position,” preserve it. As a runtime hypothesis, compare against:  
   `projectedEndpoint = currentY + boundedProjection(releaseVelocity)` → clamp to snap range → nearest valid snap.

7. **Hand release velocity into settle.**  
   Use a spring or equivalent animation primitive that starts from current Y with the measured velocity. Prefer critically damped or lightly damped behavior; avoid decorative bounce for this calm operations context.

8. **Separate transform layers.**  
   Example: outer sheet owns `translateY`; inner handle/content owns press feedback like `scale(0.98)`. Avoid competing writes to the same `transform`.

9. **Replace broad transitions.**  
   Change `transition: all 300ms` to explicit properties only, e.g. `transform`, `opacity`, or state-color tokens. Do not transition layout properties accidentally.

10. **Add Reduced Motion behavior.**  
   In reduced motion, avoid large animated travel and elastic effects. Snap state should update immediately or within a very short duration, with feedback via handle color, shadow/border change, state label, opacity, or a compact `80–120ms` non-spatial transition.

## Verified / unverified boundaries

**Verified from the supplied snippet:**  
- Drag writes `top` during pointer movement.  
- Settle animates `top` with WAAPI, `480ms`, `ease-in`, `fill: "forwards"`.  
- New pointerdown is blocked while `animating` is true.  
- CSS applies `transition: all 300ms`.  
- CSS applies active-state `transform: scale(0.96)`.  
- No shown pointer capture, velocity sampling, presentation-value interruption, boundary resistance, or Reduced Motion branch.

**Not verified from static code:**  
- Actual frame rate, smoothness, input latency, or layout cost on target devices.  
- Whether surrounding code clamps sheet bounds or handles `pointercancel`.  
- Whether `nearestSnapPoint` encodes product-approved snap semantics.  
- Whether accessibility state, keyboard controls, focus management, and ARIA exist elsewhere.  
- Browser-specific WAAPI behavior, especially interaction between animated `top`, inline `top`, and `fill: forwards`.

## Smallest runtime validation plan

1. **Gesture feel pass:** slow drag, fast flick, partial drag, pointer leaving bounds, pointercancel, and mid-settle regrab. Pass if there is no jump, no dead period, and the sheet tracks the pointer with preserved grab offset.

2. **Physics pass:** log current Y, release velocity in CSS px/s, chosen target, and settle start velocity. Pass if target choice matches product semantics and settle starts continuously from the release motion.

3. **Performance pass:** profile under representative app load while dragging and settling. Pass if pointermove avoids layout thrash and stays within frame budget on the supported refresh rates.

4. **Reduced Motion pass:** enable reduced motion and repeat state changes. Pass if collapsed/half/full feedback remains clear without large animated travel or elastic movement.

5. **Accessibility interaction pass:** verify keyboard state changes, focus visibility, and non-pointer operation. Pass if the sheet can be controlled and understood without drag.
