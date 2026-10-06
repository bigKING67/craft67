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

# Blind scorecard

Grade anonymized raw outputs. Do not reward brand or skill-name mentions.

| Criterion | Weight | Full-credit evidence |
|---|---:|---|
| Evidence honesty | 15 | Labels the input as static and avoids smoothness/runtime claims. |
| Motion necessity | 10 | Separates causal feedback from decorative or unnecessary animation. |
| Direct manipulation | 15 | Catches input lockout, pointer capture, grab offset, and 1:1 tracking. |
| Interruption and presentation value | 15 | Requires interruption from the current on-screen value without jumps. |
| Velocity and projection | 15 | Preserves release velocity, units, projected endpoints, and snap selection. |
| Property/performance discipline | 10 | Rejects `top`, `transition: all`, and conflicting transform ownership. |
| Accessibility | 10 | Defines a non-vestibular Reduced Motion path with preserved feedback. |
| Actionability and scope | 10 | Gives prioritized implementation moves and a minimal runtime plan within 150 lines. |

Total: 100.


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


## Output B

## Verdict

**Not acceptable for a calm repeated-use operations sheet.**  
**Evidence:** the implementation updates `top` during pointer movement, applies `transition: all`, blocks input while animating, ignores release velocity, uses fixed-duration `ease-in`, and has no reduced-motion path. The result is likely to feel indirect, laggy, non-interruptible, and abrupt at snap completion.

---

## Prioritized findings

### P0 — Drag is not true direct manipulation
**Evidence:** `pointermove` sets `sheet.style.top = event.clientY`. `startY` is recorded but unused.  
**Effect:** the sheet top can jump to the pointer’s absolute screen Y instead of preserving the grab offset. The user is no longer “holding” the sheet; the sheet is being teleported to the pointer coordinate.  
**Fix direction:** track `grabOffset = pointerY - currentSheetY`, then set `sheetY = pointerY - grabOffset`.

### P0 — Input is locked during animation
**Evidence:** `if (animating) return;` on `pointerdown`.  
**Effect:** the user cannot grab, reverse, or correct the sheet while it is settling. This is the biggest fluidity failure.  
**Fix direction:** allow interruption. On pointerdown, cancel the current animation, read the current presented position, and continue from there.

### P0 — CSS transition fights the gesture
**Evidence:** `.sheet { transition: all 300ms; }` while JS writes `top` on every `pointermove`.  
**Effect:** drag tracking will lag behind the pointer because every move becomes a 300ms transition. `transition: all` also risks animating unrelated properties.  
**Fix direction:** no transition during active drag. Use explicit transition/spring only for non-gesture state changes.

### P1 — Uses layout properties for high-frequency motion
**Evidence:** `style.top`, `offsetTop`, and animated `top`.  
**Effect:** this can force layout work and makes the sheet harder to keep smooth. It also complicates reading the true visual position during animation.  
**Fix direction:** keep layout stable and move the sheet with `transform: translateY(...)`; read/write a single `y` motion value.

### P1 — Snap decision ignores velocity and intent
**Evidence:** `nearestSnapPoint(sheet.offsetTop)` only considers release position.  
**Effect:** a quick upward flick from below may still collapse if the release point is nearer the collapsed snap. A slow drag and a deliberate throw are treated the same.  
**Fix direction:** estimate release velocity, project the likely resting point, then choose collapsed / half / full from the projected endpoint.

### P1 — Fixed `ease-in` snap is the wrong physical shape
**Evidence:** `{ duration: 480, easing: "ease-in" }`.  
**Effect:** `ease-in` starts sluggishly after release, then accelerates into the target and stops abruptly. That creates a visible seam between finger movement and snap motion.  
**Fix direction:** use a velocity-aware spring. For a calm app, default to critically damped or near-critically-damped motion; reserve slight bounce only for clear momentum gestures.

### P1 — Filled animation can leave stale presentation state
**Evidence:** `fill: "forwards"` without storing/canceling/committing the animation.  
**Effect:** later inline `top` writes may conflict with the still-filled animation state, causing stuck positions or jumps.  
**Fix direction:** own a single animation handle; cancel/finish deliberately; commit final state to the canonical sheet state.

### P2 — Press feedback is too broad and possibly disruptive
**Evidence:** `.sheet:active { transform: scale(0.96); }`.  
**Effect:** scaling the whole sheet can make operational content wobble/shrink while the user is trying to read or act. It also conflicts with using `transform` for sheet movement.  
**Fix direction:** apply subtle feedback to the drag handle, shadow, elevation, or grip affordance instead of scaling the entire sheet.

### P2 — Missing gesture hygiene
**Evidence:** no pointer capture, no active pointer id, no drag threshold, no boundary resistance, no `touch-action` policy shown.  
**Effect:** dragging may break when the pointer leaves the element, multiple pointers can interfere, and browser scrolling may compete with the sheet.  
**Fix direction:** capture the pointer, track one active pointer, add hysteresis, coordinate with scroll areas, and rubber-band beyond full/collapsed bounds.

### P2 — Reduced Motion requirement is unmet
**Evidence:** no `prefers-reduced-motion` path or alternative state feedback.  
**Effect:** collapsed → half → full can require large animated spatial travel even when the user has requested reduced motion.  
**Fix direction:** preserve state feedback with short opacity, handle, shadow, label, or content-density changes; avoid long post-release travel and remove overshoot.

---

## Concrete direct-manipulation moves

1. **Use a canonical `y` value**
   - `collapsedY`, `halfY`, `fullY`.
   - Render with `transform: translate3d(0, ypx, 0)`.
   - Avoid animating `top`.

2. **On pointerdown**
   - Cancel any active settle animation.
   - Read the current visual `y`.
   - Store `grabOffset = pointerY - currentY`.
   - Capture the pointer.
   - Start velocity history.

3. **On pointermove**
   - Ignore moves from non-active pointers.
   - After a small threshold, enter dragging mode.
   - Set `nextY = pointerY - grabOffset`.
   - Clamp or rubber-band past full/collapsed.
   - Update with `requestAnimationFrame`.
   - Update related feedback continuously: scrim opacity, handle state, shadow, state preview.

4. **On pointerup**
   - Compute release velocity from recent samples.
   - Project endpoint: `projectedY = currentY + projectedDistance(velocity)`.
   - Pick snap point from projected endpoint, not just current position.
   - Spring from current visual `y` to target using release velocity.
   - Allow the spring to be interrupted immediately.

5. **For calm repeated use**
   - Prefer no overshoot by default.
   - Use short, settled motion.
   - Make snap feedback confident but quiet.
   - Avoid playful bounce unless the user clearly flicked with momentum.

6. **For Reduced Motion**
   - During user drag: keep direct tracking, because the user controls the motion.
   - After release: minimize automatic travel.
   - Use state-preserving feedback: handle highlight, compact/full content crossfade, subtle shadow/elevation change, or state label.
   - No elastic bounce, no long slide, no large involuntary travel.

---

## Verified / unverified boundaries

**Verified from the provided snippet**
- Drag writes `top` directly.
- `startY` is unused.
- Snap uses `offsetTop`.
- Animation uses fixed `480ms ease-in`.
- Input is blocked while `animating`.
- CSS uses `transition: all 300ms`.
- Whole-sheet active scale is applied.
- No reduced-motion path is shown.

**Not verified**
- No browser or device validation was performed.
- Actual DOM structure, positioning mode, snap-point implementation, and scroll-container behavior are unknown.
- Runtime frame rate, layout cost, pointer-capture behavior, and animation conflict severity were not measured.
- Accessibility semantics and state announcements were not inspected.

---

## Smallest runtime validation plan

1. **Directness test**
   - Drag from handle and body.
   - Confirm the grabbed point stays under the pointer with no initial jump.

2. **Interruptibility test**
   - Release toward half/full.
   - Re-grab mid-animation and reverse direction.
   - Pass only if there is no lockout, jump, or velocity break.

3. **Velocity intent test**
   - Slow drag near midpoint.
   - Fast flick from the same position.
   - Pass only if landing differs according to gesture intent.

4. **Reduced Motion test**
   - Enable reduced motion.
   - Move between collapsed, half, and full.
   - Pass only if state feedback remains clear without large automatic travel or bounce.

5. **Frame-cost test**
   - Record a short drag/settle trace.
   - Pass only if movement is transform-based, avoids per-frame layout thrash, and has no long tasks on the input path.


## Output C

**Verdict — Block for gesture quality and accessibility.**  
[Static evidence] The sheet is not truly direct-manipulated: it jumps to the pointer, animates layout `top`, blocks interruption, ignores velocity, and has no Reduced Motion path. For a calm operations app used repeatedly, this will likely feel laggy, fragile, and over-animated.

## Prioritized findings

1. **P0 — Drag is not 1:1 or stable**
   - [Static evidence] `sheet.style.top = event.clientY` uses viewport pointer coordinates as layout position.
   - [Static evidence] `startY` is captured but unused.
   - Impact: the sheet’s top edge can snap under the pointer instead of preserving the grab offset.

2. **P0 — Input is locked during settle**
   - [Static evidence] `if (animating) return` prevents a new drag while the sheet is settling.
   - [Static evidence] The current animation is not interrupted from the on-screen value.
   - Impact: users cannot catch or redirect the sheet, which is essential for gesture surfaces.

3. **P0 — Layout animation on a hot gesture path**
   - [Static evidence] Pointer move writes `top`; WAAPI also animates `top`.
   - [Static evidence] CSS has `transition: all 300ms`, so pointer-driven `top` changes may be transitioned instead of tracking instantly.
   - Impact: likely delayed, janky, and layout-expensive compared with `transform`.

4. **P0 — No Reduced Motion behavior**
   - [Static evidence] No `prefers-reduced-motion` branch.
   - Product requirement: Reduced Motion must preserve state feedback without large spatial travel.
   - Impact: fails an explicit accessibility/product constraint.

5. **P1 — Wrong easing and duration for a released sheet**
   - [Static evidence] `duration: 480`, `easing: "ease-in"`.
   - Impact: `ease-in` makes the start feel slow after release; 480ms is too indulgent for a repeated operations workflow unless distance-dependent and justified.

6. **P1 — Snap targeting ignores velocity and hysteresis**
   - [Static evidence] `nearestSnapPoint(sheet.offsetTop)` only uses current position.
   - Impact: a fast flick and a slow drag ending at the same point behave identically; collapsed/half/full transitions may feel unresponsive.

7. **P1 — Missing pointer ownership and cancellation handling**
   - [Static evidence] No `setPointerCapture`, `pointercancel`, `lostpointercapture`, pointer id tracking, or multi-touch guard.
   - Impact: drag can break when the pointer leaves the sheet or another pointer enters.

8. **P2 — Press feedback conflicts with sheet motion**
   - [Static evidence] `.sheet:active { transform: scale(0.96); }`
   - Impact: if position later moves to `transform: translateY(...)`, scale and translate will compete unless split across wrapper layers. Scaling the whole sheet during drag also feels heavy for a calm tool.

## Concrete direct-manipulation moves

1. **Use an explicit state machine**
   - `idle → dragging → settling`
   - Track `pointerId`, `dragStartY`, `sheetStartY`, `grabOffset`, current snap state, and current visual position.

2. **Preserve grab offset**
   - On pointer down: measure current sheet Y in the same coordinate space as pointer `clientY`.
   - During drag: `nextY = event.clientY - grabOffset`, not `event.clientY`.

3. **Capture the pointer**
   - Call `setPointerCapture(event.pointerId)` once drag intent is accepted.
   - Ignore other pointers until release/cancel.

4. **Move with compositor-friendly transforms**
   - Keep layout `top`/`bottom` stable.
   - Drive position with `transform: translateY(...)`.
   - Remove `transition: all`; only transition intentional properties.

5. **Separate transform ownership**
   - Outer layer: `translateY` for sheet position.
   - Inner/handle layer: subtle press scale or color feedback.
   - Avoid one rule overwriting another transform.

6. **Make settling interruptible**
   - Do not block pointer down during animation.
   - On new pointer down, sample current presentation position, cancel the animation, and start dragging from that visible value.

7. **Measure release velocity**
   - Keep recent pointer samples with monotonic timestamps.
   - Use CSS px/s.
   - Preserve existing snap semantics unless product explicitly wants momentum targeting.
   - If momentum targeting is authorized: compute a bounded projected endpoint, clamp it, then choose the nearest collapsed/half/full snap point.

8. **Use calmer settle motion**
   - Prefer a damped spring-like settle: no or minimal bounce, roughly `0.3–0.4s` response.
   - If using fixed easing, use strong `ease-out`/drawer easing, not `ease-in`.
   - Duration should scale with distance and stop feeling cinematic.

9. **Add hysteresis and boundaries**
   - Require roughly `8–12px` before treating movement as drag.
   - Clamp to valid sheet bounds.
   - Use soft resistance beyond collapsed/full instead of hard jumps.

10. **Reduced Motion path**
   - Disable large travel, momentum, and elastic effects.
   - Snap state immediately or near-immediately.
   - Preserve feedback via non-spatial cues: handle highlight, state label, subtle opacity/color change, focus placement, or scrim change.

## Verified / unverified boundaries

**Verified from static code**
- Animates `top`.
- Uses `transition: all`.
- Uses `ease-in` and 480ms settle.
- Has no visible Reduced Motion branch.
- Has no pointer capture/cancel handling.
- Does not preserve grab offset.
- Does not measure velocity.
- Locks out pointer down while `animating`.

**Not verified**
- Actual frame rate, dropped frames, or perceived smoothness.
- Browser-specific interaction between CSS transitions and WAAPI in this exact DOM.
- Whether surrounding CSS/layout makes `clientY` and `offsetTop` accidentally align.
- Whether `nearestSnapPoint` contains thresholds, clamping, or product-specific state rules.
- Touch-device feel, trackpad behavior, scroll conflict, and 60Hz/120Hz performance.

## Smallest runtime validation plan

1. **Desktop pointer sanity**
   - Drag from handle and body.
   - Verify no jump on grab.
   - Verify pointer remains captured when leaving sheet bounds.
   - Verify release settles to collapsed/half/full.

2. **Interruption**
   - Release toward half/full, then grab mid-animation.
   - Expected: no lockout, no visual jump, continues from current visible position.

3. **Velocity behavior**
   - Compare slow drag vs quick flick ending near the same Y.
   - Expected: behavior matches the intended product snap contract.

4. **Reduced Motion**
   - Enable `prefers-reduced-motion`.
   - Move between collapsed/half/full.
   - Expected: state change remains clear without large animated travel, bounce, or long glide.

5. **Performance smoke**
   - Record one drag under normal app load.
   - Expected: no layout-thrashing hot path from `top`, no delayed trailing caused by transitions.
