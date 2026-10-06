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


## Output B

## Verdict

**[Evidence: snippet-only]** The implementation is not suitable for a calm, repeatedly used three-state gesture sheet. It will feel jumpy, laggy, non-interruptible, and unpredictable because it treats a drag as absolute `top` assignment plus a fixed `ease-in` animation, rather than continuous direct manipulation with velocity-aware snapping.

## Prioritized findings

1. **Input is not actually bounded to a drag**
   - **[Evidence]** `pointermove` always writes `sheet.style.top`, even if no valid `pointerdown` occurred.
   - **[Impact]** Hover/move noise, multi-pointer input, or moves during an ignored animation can still reposition the sheet.

2. **The sheet will jump to the pointer**
   - **[Evidence]** `sheet.style.top = event.clientY`.
   - **[Impact]** Ignores the sheet’s starting position and the grab offset. If the user grabs the handle 40px below the top, the sheet top snaps to the pointer instead of staying attached.

3. **Animation blocks user agency**
   - **[Evidence]** `if (animating) return` on `pointerdown`.
   - **[Impact]** A user cannot grab or reverse the sheet mid-flight. In a repeated operations app, this reads as “the UI is busy” rather than calm.

4. **Release motion has the wrong physics**
   - **[Evidence]** `nearestSnapPoint(sheet.offsetTop)` ignores release velocity.
   - **Impact]** A decisive flick may still snap backward to the nearest current point. Snap choice should consider projected endpoint, not only current position.

5. **The easing is backwards for a release**
   - **[Evidence]** `{ duration: 480, easing: "ease-in" }`.
   - **[Impact]** Motion starts slowly after the finger lifts, losing the user’s velocity, then accelerates into the destination. A sheet should usually continue from release velocity and settle, not “wake up” after release.

6. **Fixed duration makes all distances feel the same**
   - **[Evidence]** `duration: 480`.
   - **[Impact]** Small corrections feel sluggish; large moves may feel abrupt. Use distance/velocity-aware spring behavior or at least distance-scaled timing.

7. **Layout properties are used for gesture motion**
   - **[Evidence]** Animates and writes `top`; reads `offsetTop`.
   - **[Impact]** Causes layout work and risks jank. Use a transform-backed position model, e.g. `translateY(...)`, with snap state stored separately.

8. **CSS conflicts with direct manipulation**
   - **[Evidence]** `.sheet { transition: all 300ms; }`.
   - **[Impact]** Every pointermove may be smoothed by CSS, so the sheet lags behind the pointer. `transition: all` can also animate unrelated properties accidentally.

9. **Whole-sheet active scale is too heavy**
   - **[Evidence]** `.sheet:active { transform: scale(0.96); }`.
   - **[Impact]** Shrinking an operational panel disturbs content, text, and controls. Press feedback should be localized to the grab handle or affordance, not the whole sheet.

10. **Reduced Motion is missing**
    - **[Evidence]** No `prefers-reduced-motion` branch.
    - **[Impact]** Users who request reduced motion still get large spatial travel. State feedback should remain, but via low-motion cues such as opacity, elevation, outline, handle state, or content crossfade.

## Concrete direct-manipulation moves

- Track a real drag session:
  - on `pointerdown`: cancel/re-target any running animation, capture pointer, record `pointerId`, `startY`, current sheet `y`, and grab offset.
  - on `pointermove`: ignore unrelated pointers; update `y = startYPosition + deltaY`.
  - on `pointerup/cancel`: release capture, compute velocity, then snap.

- Use transform, not `top`:
  - maintain `sheetY` as the source of truth.
  - render with `transform: translateY(${sheetY}px)`.
  - commit semantic state separately: `collapsed | half | full`.

- Make snapping velocity-aware:
  - keep a short history of recent pointer positions/timestamps.
  - compute release velocity.
  - project the likely resting point.
  - choose the nearest snap point to the projected point, not merely the current point.

- Make animation interruptible:
  - remove the input lockout.
  - if the user touches during settling, stop the current animation at the current visual position and let the pointer take over.
  - preserve velocity continuity when re-targeting.

- Add boundary behavior:
  - clamp between full and collapsed positions.
  - if dragged past limits, apply progressive resistance rather than a hard stop.
  - on release, settle back to the nearest valid state.

- Replace global CSS transitions:
  - remove `transition: all`.
  - use targeted transitions only for non-gesture properties such as shadow, opacity, or handle color.
  - avoid transform conflicts between press feedback and sheet translation; use nested elements if needed.

- Calm app motion defaults:
  - use critically damped or near-critically damped settling by default.
  - reserve bounce/overshoot only for strong flicks, and keep it subtle.
  - avoid dramatic scale changes on large surfaces.

- Reduced Motion behavior:
  - do not animate large vertical travel.
  - update to the chosen state with minimal or no spatial tween.
  - preserve feedback through a short opacity/elevation/outline change, a handle state change, or a content crossfade.
  - disable overshoot and rubbery visual travel in that mode.

## Verified / unverified boundaries

- **Verified from code:** absolute pointer-to-`top` mapping, fixed `ease-in` animation, global transition, whole-sheet active scale, missing reduced-motion handling.
- **Inferred risk:** layout jank from `top`/`offsetTop`, drag lag from `transition: all`, poor flick behavior from missing velocity projection.
- **Not verified here:** runtime frame rate, actual snap-point math, browser-specific pointer behavior, touch-device behavior, visual appearance, accessibility tree, or reduced-motion behavior in a real environment.

## Smallest runtime validation plan

1. **State math tests**
   - snap target from position only.
   - snap target from projected velocity.
   - collapsed / half / full boundaries.
   - reduced-motion branch preserves final state.

2. **Pointer interaction smoke**
   - drag from handle without jump.
   - drag outside sheet bounds after pointer capture.
   - interrupt a settling animation and reverse direction.
   - flick upward/downward and confirm target follows intent.

3. **Motion quality checks**
   - no CSS transition lag during drag.
   - no large travel animation when reduced motion is enabled.
   - no unexpected transform conflict between sheet movement and press feedback.

4. **Accessibility minimum**
   - keyboard controls can move between collapsed, half, and full.
   - state is exposed to assistive tech.
   - focus is not lost when the sheet changes state.


## Output C

## Verdict

**Block — static source review only.**  
Evidence shows this is not yet a reliable direct-manipulation sheet for a calm, frequently used operations app. It can jump, track when not dragging, ignore velocity, lock during settle, animate layout properties, and lacks Reduced Motion behavior. No browser/device behavior is claimed.

## Prioritized findings

**P0 — Drag ownership is broken**  
- **Static evidence:** `pointermove` always writes `sheet.style.top`, even if no active drag began, the pointer left the element, a second pointer appears, or `animating` blocked `pointerdown`.
- **Risk:** Cursor/touch movement can reposition the sheet outside an intended gesture.
- **Fix:** Track `isDragging`, `pointerId`, pointer capture, `pointercancel`, and release cleanup.

**P0 — The sheet will likely jump under the pointer**  
- **Static evidence:** `startY` is recorded but never used; movement sets `top = event.clientY`.
- **Risk:** The sheet’s top edge snaps to the pointer instead of preserving the grab offset.
- **Fix:** Store `grabOffset = event.clientY - currentSheetY`; set position from `event.clientY - grabOffset`.

**P0 — Not Reduced Motion compliant**  
- **Static evidence:** no `prefers-reduced-motion` branch; release always travels spatially for `480ms`.
- **Product conflict:** Reduced Motion must preserve state feedback without large travel.
- **Fix:** Under Reduced Motion, snap state logically with minimal or no travel; use short opacity/color/handle/state-label feedback instead of full spatial animation.

**P1 — Uses layout animation on the gesture hot path**  
- **Static evidence:** writes and animates `top`; CSS has `transition: all 300ms`.
- **Risk:** Layout/reflow and broad transition interference, especially in data-heavy operations screens.
- **Fix:** Use compositor-friendly `transform: translateY(...)`; restrict transitions to named properties.

**P1 — Release motion is poorly matched to direct manipulation**  
- **Static evidence:** fixed `480ms`, `ease-in`, nearest target from `offsetTop`, no velocity.
- **Risk:** Ease-in delays response after release; quick flicks are ignored; settling cannot inherit momentum.
- **Fix:** Measure release velocity in CSS px/s, choose target by product-owned snap rules, and settle with an interruptible spring or equivalent.

**P1 — Interruption model is unsafe**  
- **Static evidence:** global `animating` rejects `pointerdown`; `.finished.then` has no cancellation/error path.
- **Risk:** Users cannot grab the sheet mid-flight; canceled animations may leave `animating = true`.
- **Fix:** Allow retargeting from the current presentation value; cancel/replace active animation safely; always cleanup in `finally` or equivalent.

**P2 — Transform ownership conflicts**  
- **Static evidence:** `.sheet:active { transform: scale(0.96); }`; proposed drag should also use `transform`.
- **Risk:** Press scale and drag translation can overwrite each other.
- **Fix:** Use separate layers, e.g. outer wrapper owns `translateY`, inner surface owns press scale.

**P2 — Snap/state model is implicit**  
- **Static evidence:** collapsed/half/full are only inferred through `nearestSnapPoint(sheet.offsetTop)`.
- **Risk:** No clear state feedback, no accessible state, no resilient source of truth.
- **Fix:** Maintain explicit state: `collapsed | half | full`; reflect with attributes, handle affordance, focus/keyboard behavior, and reduced-motion feedback.

## Concrete direct-manipulation moves

1. Add `isDragging`, `activePointerId`, `pointer capture`, and `pointercancel` handling.  
2. Preserve grab offset: `dragY = pointerClientY - grabOffset`, not raw `clientY`.  
3. Use `transform: translateY(var(--sheet-y))` or a single transform owner instead of `top`.  
4. Add an intent threshold around `8–12px` so taps/presses do not become drags.  
5. Clamp to collapsed/half/full bounds, with optional soft resistance beyond edges.  
6. Track recent pointer samples with timestamps; compute release velocity in CSS px/s.  
7. Keep snap-target semantics explicit: nearest current position unless momentum-based targeting is intentionally approved.  
8. If momentum is approved, select snap from a bounded projected endpoint, then settle with measured velocity.  
9. Replace `ease-in 480ms` with a short, interruptible settle; default to no bounce for this product tone.  
10. Replace `transition: all` with specific transitions, e.g. handle color, shadow, or inner press scale only.  
11. Let users interrupt the settle by grabbing the current on-screen position.  
12. For Reduced Motion, update state immediately or near-immediately and use non-travel cues: handle emphasis, state text, shadow/color change, or subtle opacity.

## Verified / unverified boundaries

**Verified by static source**
- Layout property `top` is mutated and animated.
- `transition: all` is present.
- `ease-in` and `480ms` are configured.
- `startY` is unused.
- Pointer capture, pointer identity, pointer cancel, velocity, hysteresis, bounds, and Reduced Motion branches are absent from the snippet.
- Animation cleanup is incomplete if the animation is canceled/rejected.

**Unverified**
- Actual smoothness, jank, frame rate, and device feel.
- Whether surrounding code clamps positions or supplies state elsewhere.
- Whether CSS cascade or layout context changes the observed result.
- Actual snap-point geometry.
- Browser-specific WAAPI/`offsetTop` behavior in this app.
- Touch hardware behavior and 60/120 Hz feel.

## Smallest runtime validation plan

1. **Desktop pointer pass:** drag from each state to each other state; verify no jump, no move without active drag, and correct cleanup after cancel.  
2. **Interruption pass:** release toward a snap point, grab mid-settle, reverse direction; verify no visual jump and no input lock.  
3. **Velocity pass:** compare slow drag vs quick flick; verify product-approved target selection.  
4. **Bounds pass:** drag beyond collapsed/full; verify clamp or soft resistance.  
5. **Reduced Motion pass:** enable Reduced Motion; verify state feedback remains but large spatial travel/overshoot is removed.  
6. **Performance pass:** inspect for layout work during drag under representative app load before claiming smoothness.
