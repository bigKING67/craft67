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

## Verdict — revise before approval

**[Static evidence]** The snippet does not establish reliable direct manipulation or the required Reduced Motion behavior.  
**[Design judgment]** For a calm, frequently used operations app, prioritize immediate control and clear snap-state feedback over whole-sheet scaling and prolonged settling.  
**[Unverified]** Jumping, lag, frame drops, and perceived responsiveness are risks—not observed results.

## Prioritized findings and concrete moves

### 1. P1 — Drag ownership and coordinates are incomplete
**Evidence:** `startY` is recorded but unused. Every `pointermove` writes viewport-relative `clientY` into `top`, which uses the element’s positioning context. No active-drag flag, pointer-ID ownership, capture, cancellation, or bounds are shown.

**Risk:** Hover could move the sheet; grabbing below its edge could reposition it unexpectedly; leaving the surface or a second pointer could disrupt tracking.

**Move:**
- Use explicit `idle → pending → dragging → settling` states and one active pointer ID.
- Record pointer origin and current displayed sheet position in a consistent CSS-pixel coordinate space.
- After a provisional **8–12 CSS px intent threshold**, track `initialSheetY + (currentPointerY − initialPointerY)` without easing; preserve the grab offset.
- Capture the pointer; handle `pointercancel` and lost capture, and ignore unrelated pointers.
- Prefer a dedicated drag handle with an explicit touch-action policy, preserving scrolling and controls inside the sheet.
- Apply bounded resistance beyond full/collapsed limits; remove elastic travel in Reduced Motion.

**Acceptance evidence needed:** Offset grabs, hover, boundary exits, cancellation, nested scrolling, and second-pointer tests show stable ownership and tracking.

### 2. P1 — Settling is not safely interruptible
**Evidence:** `animating` blocks only `pointerdown`; moves and releases remain active. No animation handle is retained. `fill: "forwards"` retains an animation effect without committing the target to underlying state; no cancellation cleanup is shown.

**Risk:** Repeated releases can create competing animations; displayed position, inline position, and logical state can diverge.

**Move:**
- Give one controller ownership of position, velocity, and the active animation.
- On re-grab, sample the current presentation position and velocity, cancel the previous settle, and continue from that position—not the prior target.
- Commit the final position and collapsed/half/full state, then remove the retained effect.
- Make completion and cancellation cleanup safe against stale animation callbacks.

**Acceptance evidence needed:** Re-grab and reverse at several points during settling; no position discontinuity, stale callback, or stuck interaction state.

### 3. P1 — Multiple animation mechanisms undermine direct tracking
**Evidence:** Dragging writes `top`; CSS transitions all properties for `300ms`; WAAPI also animates `top`. `:active` scales the entire sheet to `0.96`.

**Risk:** Transitioned drag updates can trail the pointer; layout-property animation can add rendering work. Whole-sheet scaling changes content and grab geometry for decorative feedback.

**Move:**
- Anchor layout and drive motion through a single `translateY` owner, with **no CSS transition on the drag translation**.
- Coalesce writes to animation frames; keep repeated layout measurements out of the move path.
- Remove whole-sheet press scaling; use immediate handle color or border feedback.
- Limit transitions to explicitly chosen feedback properties. If transforms must coexist, compose them deliberately or separate wrappers.

**Acceptance evidence needed:** Pointer/presentation traces confirm tracking; a rendering trace checks layout work and missed frames. Transform use alone does not prove smoothness.

### 4. P2 — Release behavior discards gesture momentum
**Evidence:** Target selection receives only `offsetTop`; settling always uses `480ms` and `ease-in`. No velocity samples are collected.

**Risk:** A slow drag and fast release receive identical timing; acceleration toward a fixed endpoint may make the stop feel abrupt. The duration alone is not proof of poor feel.

**Move:**
- Measure release velocity from recent timestamped samples in **CSS px/s**.
- Preserve nearest-position snapping unless momentum-based targeting is explicitly approved.
- For an experiment, calculate `projectedY = clamp(y + velocity × 0.15s, fullY, collapsedY)`; if authorized, snap nearest that bounded endpoint.
- Independently of target selection, pass bounded measured velocity into an interruptible, critically damped settle. Start tuning around a **250–300ms response scale**, not a mandatory fixed duration; avoid bounce for this product.

**Acceptance evidence needed:** Slow releases and fast flicks around both snap boundaries follow the approved target rule and decelerate coherently.

### 5. P1 — Reduced Motion and non-drag state access are not shown
**Evidence:** Neither the supplied JS nor CSS branches on Reduced Motion. Only pointer-driven state changes are shown; surrounding controls and semantics are unknown.

**Risk:** The explicit no-large-travel requirement is unmet by this snippet, and drag may be the only available state-selection mechanism.

**Move:**
- In Reduced Motion, replace large animated travel and inertial settling with immediate state placement plus static selected-state feedback or a brief color/opacity change.
- To satisfy the strict no-large-travel requirement during gestures too, preview the candidate state on the handle instead of moving the large panel, then commit on release.
- Provide keyboard-operable controls for collapsed, half, and full states; expose the current selection programmatically and visibly, and preserve sensible focus when content becomes hidden.
- Respond to preference changes by stopping active travel and resolving to a valid state.

**Acceptance evidence needed:** All three states remain distinguishable and reachable with Reduced Motion and keyboard-only input, without spatial interpolation or lost focus.

## Verified / unverified boundary

- **Verified by inspection:** The code paths, properties, timings, and omissions described above, limited to the supplied snippet.
- **Not verified:** Rendered geometry, `nearestSnapPoint` internals, surrounding accessibility support, actual touch/scroll arbitration, performance, or motion feel.
- No files were edited. No browser or device validation was performed.

## Smallest runtime validation plan

1. **Desktop browser, pointer + keyboard:** Exercise all three states; offset grabs, hover, rapid releases, mid-settle reversals, cancellation, and keyboard state selection. Log pointer ID, displayed position, velocity, chosen target, and committed state.
2. **One representative touch device:** Repeat drag/re-grab tests, leave the handle bounds, add a second touch, and scroll sheet content. Record a short interaction video.
3. **Reduced Motion on, including a live toggle:** Repeat state selection and interrupt an active settle; confirm no large animated travel and persistent state/focus feedback.
4. **One performance trace under representative app load:** Inspect drag and settle for repeated layout and missed frame deadlines at the tested refresh rate. Treat roughly **16.7ms at 60Hz / 8.3ms at 120Hz** as provisional frame budgets—not measured results.

These checks provide an initial acceptance packet, not cross-browser or cross-device certification.


## Output B

## Verdict

**[Static evidence] Not ready for reliable direct manipulation.** The sheet tracks absolute pointer position rather than drag displacement, accepts movement without an active drag, and layers competing motion behaviors. The result risks jumps, lag, and state inconsistency—especially distracting in a calm app used repeatedly.

**[Unverified]** Actual rendering smoothness, touch-scroll behavior, and perceived comfort require runtime checks; no browser or device validation was performed.

## Prioritized findings

### P0 — Make gesture ownership and position coherent
- **[Code]** `startY` is recorded but never used. Setting `top = event.clientY` puts the sheet’s top edge at the pointer instead of preserving the grab offset, so the first move can jump.
- **[Code]** `pointermove` has no dragging guard or pointer-ID check. Hover movement and unrelated pointers can reposition the sheet.
- **[Code]** There is no pointer capture, `pointercancel`, or lost-capture handling. Release outside the sheet can leave the interaction incomplete.
- **[Code]** `animating` blocks only `pointerdown`; movement and release handlers remain enabled. It neither isolates the settling animation nor provides coherent interruption.

### P1 — Remove motion conflicts and commit real state
- **[Code]** `transition: all 300ms` makes ordinary `top` updates transition instead of following the pointer directly. It also subjects future style changes to unintended animation.
- **[Code]** The settling animation uses `fill: "forwards"` without committing its destination to the underlying position or clearing the effect. The displayed position and inline position can diverge; subsequent drags may be masked by the retained animation.
- **[Code]** Animating `top` changes a layout-affecting property. Prefer a translate transform; performance improvement still needs measurement.
- **[Code]** `:active` scales the whole sheet to `0.96`. That shrinks content during contact, adds an unrelated motion channel, and does not reliably represent drag ownership.
- **[Code]** No explicit collapsed/half/full state update is shown. A settled pixel position alone is insufficient for accessible state feedback and controls.

### P1 — Settle with intent, not a fixed slow acceleration
- **[Code]** Every release uses 480 ms and `ease-in`: it accelerates toward the endpoint rather than braking into rest. Tiny corrections receive the same duration as large moves.
- **[Code]** Snap selection receives position only; no release velocity or direction is supplied.
- **[Inference]** Repeated use will likely feel sluggish on short releases and insensitive to deliberate flicks. The exact feel is unverified.

### P1 — Preserve feedback under Reduced Motion
- **[Code]** No reduced-motion branch is shown for either CSS or the JavaScript animation.
- **[Requirement]** Reduced Motion should remove autonomous large-distance settling and sheet scaling, while retaining a clear collapsed/half/full indicator. Changing CSS alone will not disable the JavaScript animation.

## Concrete direct-manipulation moves

1. **Establish one position model.** Track active pointer ID, starting pointer coordinate, starting sheet position, current position, and logical snap state.
2. **Acquire deliberately.** Start from a drag handle, accept the primary pointer, capture it, and ignore unrelated moves. Keep content scrolling separate; scope touch gesture policy to the handle rather than disabling scrolling across the sheet.
3. **Follow 1:1.** During drag, use  
   `position = clamp(startPosition + pointerY - startPointerY, full, collapsed)`.  
   Render with translation and no transition. Begin with hard bounds; avoid decorative resistance until basic behavior is proven.
4. **Allow interruption.** On a new grab, read the current rendered position, cancel the settle, and continue from that position without a jump. Handle animation cancellation without leaving stale flags or rejected promises.
5. **Resolve intent on release.** Use position plus a bounded velocity projection to choose among the three stops. Tune flick thresholds explicitly; a short slow move should not unexpectedly skip a state.
6. **Brake into rest.** Use one settling mechanism with a non-overshooting, decelerating curve. Start tuning around **180–280 ms**, shortening near-target moves; these are proposed values, not validated timings.
7. **Finish cleanly.** Commit the exact destination, remove the animation effect, and update logical state. Define cancellation/lost-capture behavior so every exit leaves a valid state.
8. **Keep feedback quiet and accessible.** Replace whole-sheet scaling with a subtle handle treatment. Provide labeled controls for all three states and keyboard operation; expose the settled state without announcing every drag frame.
9. **Reduce spatial motion.** Under Reduced Motion, keep user-controlled tracking immediate if dragging is retained, but commit the selected stop without animated travel. Use a persistent state label or selected control for feedback; make non-drag controls equally usable.

## Verified / unverified boundary

- **Verified by snippet inspection:** the handler gaps, unused drag origin, absolute positioning, timing settings, retained animation effect, broad transition, and active scaling.
- **Not established:** surrounding state logic, snap-point implementation, accessibility elsewhere, scroll policy elsewhere, actual layout cost, or behavior on any browser/device. Missing from this snippet does not prove missing from the full app.

## Smallest runtime validation plan

Use **one desktop browser with mouse/keyboard and one touch device**, covering:

1. **Ownership:** hover, grab away from the top edge, release outside, cancel, and add a second pointer. Pass: only the owning drag moves the sheet; no jump or stuck state.
2. **Snapping and interruption:** slow releases around each boundary, a flick in each direction, and a re-grab mid-settle. Pass: predictable targets, continuous position, exact final state.
3. **Touch scrolling:** scroll sheet content, then drag the handle. Pass: each gesture has one intended owner.
4. **Reduced Motion and controls:** select all three states with drag, keyboard, and labeled controls. Pass: no autonomous large travel or scaling, and state remains evident.
5. **One performance recording:** inspect a drag and settle with realistic content. Pass: no recurring motion-induced layout work or visible frame stalls. Report measured behavior separately from subjective timing preference.


## Output C

## Verdict

**[Static evidence] This is not yet reliable direct manipulation.** Input ownership, coordinates, and animation lifecycle need fixing before tuning the feel. **[Expected effect—not observed]** The sheet may jump, trail the pointer, resist interruption, and snap against flick intent—poor fits for a calm, frequently used operations app.

Labels below distinguish **Evidence** in the supplied code, **Risk** inferred from it, and **Recommendation** requiring validation.

## Prioritized findings

| Priority | Finding |
|---|---|
| **P0 — Gesture ownership** | **Evidence:** Every `pointermove` writes position, including mouse hover; no active-drag flag or pointer-ID check exists. No capture, cancellation, or lost-capture handling is shown. **Risk:** Accidental movement, competing pointers, and missed releases outside the sheet. |
| **P0 — Coordinate integrity** | **Evidence:** `startY` is unused; viewport-relative `clientY` is assigned directly to CSS `top`, which uses the positioning context. **Risk:** The first move loses the grab offset and can jump; coordinate mismatch depends on surrounding layout. |
| **P0 — Conflicting motion owners** | **Evidence:** `transition: all 300ms` covers positional changes while JavaScript writes `top`; release separately animates `top`. **Risk:** Drag updates chase a transitioning position instead of tracking directly. Actual interactions depend on computed styles and layout. |
| **P0 — Interruption and cleanup** | **Evidence:** `animating` blocks only down events—not moves or releases. Animation handles are discarded; `fill: "forwards"` retains the final effect without synchronizing inline position. **Risk:** Overlapping settles, stale completion callbacks, and retained effects masking subsequent writes. Cancellation would also reject `.finished` without cleanup. |
| **P0 — Reduced Motion requirement** | **Evidence:** Neither code block contains a reduced-motion branch. **Risk:** Users receive the same large spatial settle and press scale. A CSS-only override would not disable the JavaScript animation. |
| **P1 — Release behavior** | **Evidence:** Target selection receives position only; settling uses fixed 480ms `ease-in`. **Risk:** No explicit velocity-aware targeting or handoff; the sheet restarts slowly and reaches its target without a gentle deceleration. Flicks and careful placement receive the same treatment. |
| **P1 — Unnecessary surface motion** | **Evidence:** Pressing scales the entire sheet to `0.96`. **Risk:** Content and controls shrink during interaction, disturbing the grab relationship without explaining state. |
| **P1 — Rendering cost** | **Evidence:** Motion writes/animates `top` and reads `offsetTop`. **Risk:** Layout work rather than compositor-friendly translation; actual frame cost is unmeasured. |

## Concrete direct-manipulation moves

1. **Give position one owner.** Maintain explicit `idle → dragging → settling` states, one active pointer ID, one current position, and one animation handle. Keep the semantic snap state separate from intermediate position.

2. **Preserve the grab.** On eligible primary-pointer down, sample the currently displayed position, stop the existing settle without changing that position, then record pointer origin and sheet origin. During drag:
   ```js
   y = originSheetY + (event.clientY - originPointerY);
   ```
   Use one consistent coordinate system and render with `translateY`; no positional CSS transition during tracking.

3. **Own the gesture deliberately.** Prefer a dedicated handle; capture the pointer and ignore unrelated pointers. Define `pointerup`, `pointercancel`, and `lostpointercapture` cleanup. Apply an appropriate `touch-action` policy to the handle, not indiscriminately to scrollable sheet content. Preserve taps and content scrolling; introduce only a small intent threshold if needed.

4. **Make interruption continuous.** Re-grabbing must work during every settle. Start from the live displayed position—not the previous snap target. Retarget autonomous motion with current velocity; when dragging resumes, pointer movement owns position immediately. Ignore stale completion callbacks and handle cancellation explicitly.

5. **Let release express intent.** Estimate velocity from a short timestamped sample history, accounting for a pause before release. Select among collapsed, half, and full using a bounded projected endpoint, direction, and modest snap hysteresis. Slow placement should favor nearby states; intentional flicks should advance predictably.

6. **Settle quietly.** Start with a critically damped, velocity-aware spring: no decorative bounce, no fixed input lockout. Treat a roughly 0.3–0.4s response as a tuning starting point, not a verified duration. Use gentle, bounded edge resistance; never allow momentum to carry the surface offscreen.

7. **Replace whole-sheet scaling.** Give the handle immediate, restrained color or contrast feedback. Keep content stable. Commit the final position to the canonical state and remove the finished animation effect.

8. **Provide equivalent reduced-motion feedback.** Detect the preference in JavaScript as well as CSS. Keep user-controlled tracking immediate, but eliminate automatic long-distance travel, overshoot, and scaling: commit the snap immediately, optionally using a brief local opacity/color cue. Provide explicit, keyboard-operable state controls so dragging is unnecessary; visibly and accessibly identify the selected state.

## Verified / unverified boundary

- **Verified by static inspection only:** The control flow, property writes, timing parameters, and missing mechanisms listed above in the supplied excerpt.
- **Unverified:** Surrounding CSS, positioning context, `nearestSnapPoint` internals, external accessibility handling, touch-scroll arbitration, actual visual jumps, latency, and frame performance.
- **No files were edited. No browser or device validation was performed.**

## Smallest runtime validation plan

1. **One desktop browser + one physical touch device:** Exercise slow drags and directional flicks between all three states. Pass: preserved grab offset, immediate tracking, predictable targets, no hover movement.
2. **Interrupt and cancel:** Re-grab/reverse early and late in a settle; leave bounds, cancel a gesture, and introduce a second pointer. Pass: no jump, stuck state, competing animation, or unhandled rejection.
3. **Check touch arbitration:** Scroll content, tap controls, then drag the handle. Pass: each action owns only its intended behavior.
4. **Enable Reduced Motion and use keyboard controls:** Reach all three states. Pass: no automatic large spatial travel or scale, clear state feedback, retained focus.
5. **Record one drag → flick → re-grab sequence:** Inspect frame timing and layout work on representative hardware. Pass: no recurring motion-induced layout or missed-frame pattern; assess responsiveness at normal speed as well as frame-by-frame.
