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

## Verdict — **Block pending correction**
**[Static evidence + product context]** This is not yet a dependable three-state gesture sheet. Input ownership, position tracking, interruption, and Reduced Motion need correction before timing polish. For a calm, repeatedly used operations app, prioritize immediate control and quiet state feedback—not whole-sheet press effects.

**Labels:** **[Static]** proven by the supplied snippet; **[Risk]** plausible runtime consequence, not observed; **[Move]** proposed correction.

## Prioritized findings and direct-manipulation moves

### 1. P1 — Drag ownership and grab position are missing
- **[Static]** `startY` is recorded but never used. Every `pointermove` writes viewport `clientY` into CSS `top`, with no active-drag or pointer-ID check. No capture, cancellation, or boundary handling is shown.
- **[Risk]** Hover could move the sheet; grabbing below its top could cause a jump. Coordinate-space differences, leaving the element, extra touches, and content scrolling could break tracking.
- **[Move]** Use explicit idle/pressed/dragging/settling states and one active primary pointer. On down, record the rendered sheet position and pointer position in a consistent CSS-pixel coordinate space. Apply `initialSheetY + (clientY - startY)` after a small intent threshold—start testing around 8–12 CSS px, without a threshold-crossing jump.
- **[Move]** Capture the pointer, handle `pointercancel`/lost capture, and ignore other pointers. Prefer a dedicated handle with an appropriate `touch-action` policy so content remains scrollable. Add bounded progressive resistance beyond full/collapsed limits.
- **Acceptance:** preserved grab offset, 1:1 tracking within bounds, no hover movement, and predictable release/cancellation outside the sheet.

### 2. P1 — Settling cannot be reliably interrupted or finalized
- **[Static]** `animating` rejects only `pointerdown`; move/up still run. The animation handle is discarded. `fill: "forwards"` retains an animated value without updating the underlying position; completion only resets a boolean. Cancellation rejection and stale completions are unhandled.
- **[Risk]** Re-grabs could compete with retained animations or launch overlapping settles. The visible position, inline position, and interaction state could diverge.
- **[Move]** Give position and animation a single owner. Re-grabbing must sample the current presentation position and velocity, stop the previous animation, and transfer control without jumping—not wait for completion. Finalize the selected snap into persistent position and named state, then remove the animation effect. Make cancellation cleanup ownership-aware so old callbacks cannot reset a newer gesture.
- **Acceptance:** rapid grab/release/reverse sequences remain continuous; only the current interaction can commit collapsed, half, or full.

### 3. P1 — Reduced Motion and non-drag state access are absent here
- **[Static]** No preference branch or keyboard/state controls are shown; settling always requests 480 ms of positional animation.
- **[Risk]** The supplied path does not meet the stated Reduced Motion requirement. Accessibility elsewhere in the app is unknown.
- **[Move]** Under `prefers-reduced-motion`, remove animated snap travel, elastic motion, and press scaling. Commit geometry immediately; retain an explicit selected-state label and, optionally, a brief opacity/color cue. If direct dragging remains, keep only movement directly controlled by the pointer—no momentum tail. Provide labeled keyboard-operable controls for all three states and visible focus.
- **Acceptance:** all states remain understandable and reachable without dragging or large animated travel; focus remains on a usable control.

### 4. P2 — Multiple motion mechanisms undermine direct tracking
- **[Static]** Pointer updates and WAAPI animate `top`; `transition: all 300ms` also covers position and the `:active` scale.
- **[Risk]** Transition interpolation can make dragging trail the pointer; layout-property animation can add rendering work. Whole-sheet `scale(0.96)` may visually detach content from the grabbed point. Actual lag, frame cost, and compositing are unmeasured.
- **[Move]** Use one translation owner, normally `transform: translateY(...)`, with **no transition during dragging**. Coalesce visual writes with the display clock; keep geometry reads out of the move loop. Remove `transition: all` and whole-sheet scaling. Use restrained handle feedback instead; if scale is retained anywhere, separate its transform ownership.
- **Acceptance:** pointer/rendered-position traces show direct tracking; a performance trace establishes rendering cost rather than assuming transforms guarantee smoothness.

### 5. P2 — Release ignores velocity and favors slow-start motion
- **[Static]** Target selection receives only `offsetTop`; settling uses fixed `480ms ease-in`. No velocity measurement or velocity handoff exists.
- **[Risk]** Slow-start acceleration and abrupt arrival may feel disconnected from release, especially across repeated operations. The snap helper’s semantics are unknown.
- **[Move]** Measure recent pointer samples using monotonic timestamps; express velocity in CSS px/s. Settle from the current presentation position with bounded measured velocity, converted to the animation API’s units. Start with a critically damped, no-bounce spring around a 0.25–0.35 s response scale; tune rather than treating this as a fixed duration.
- **[Move]** Preserve nearest-current-position targeting unless momentum targeting is explicitly approved. A testable alternative is `projectedY = clamp(currentY + velocity * 0.15s, fullY, collapsedY)`, then choose the nearest valid snap. Projection selects a destination; it does **not** replace velocity handoff into the settle.
- **Acceptance:** slow releases and fast flicks follow the agreed target rule, with continuous release/re-grab motion and no unintended state skipping.

## Verified / unverified boundary

- **Verified by static inspection only:** the handlers, property choices, timing, and missing branches described above.
- **Unverified:** rendered geometry, snap-helper behavior, external controls/styles, focus semantics, perceived feel, touch-scroll arbitration, frame rate, and device behavior.
- No files were edited. No browser or device validation was performed.

## Smallest runtime validation plan — proposed, not executed

1. **One desktop browser + one representative touch device:** record a short interaction trace covering all three states in both directions, slow drag, flick, offset grab, boundary pull, mid-settle reversal, outside release, cancellation, and an extra pointer. Check findings 1–2 and 5 against their acceptance criteria.
2. **Same fixture with Reduced Motion enabled:** exercise each state by pointer and keyboard; verify feedback, focus, and absence of animated spatial travel. Include one content-scroll gesture to check handle/content arbitration.
3. **One normal-load performance recording:** inspect pointer-to-presentation tracking and frame work for finding 4. Provisional gates, pending product agreement: p95 tracking delay ≤ one display interval and no gesture-attributable task ≥50 ms. Record browser, device, refresh rate, and trace/video; do not approve if correctness fails or the revised motion regresses these gates.


## Output B

## Verdict — needs revision before shipping
**[Static evidence]** The snippet does not maintain a reliable link between the pointer and the sheet. It mixes unguarded position writes, a blanket CSS transition, and a forward-filled animation without committing the resulting position. For a frequently used, calm operations app, prioritize stable tracking, predictable settling, and interruptibility over decorative motion.

## Prioritized findings

### P0 — Drag ownership and anchoring are missing
- **[Observed]** `startY` is recorded but never used. Setting `top` to `event.clientY` places the sheet’s top at the pointer rather than preserving the grab offset; viewport coordinates may also differ from its positioning context.
- **[Observed]** `pointermove` has no active-drag or pointer-ID guard. Hovering over the sheet can change its position; another pointer can interfere.
- **[Observed]** No pointer capture, `pointercancel`, or lost-capture cleanup is shown. Releases outside the sheet can leave the interaction incomplete.
- **[Observed]** The `animating` guard only blocks `pointerdown`; movement and release handlers still run during settlement.

**Move:** On an accepted primary-pointer press, record the active pointer, pointer Y, and current rendered sheet position. Capture that pointer. Track:
`position = startPosition + (pointerY - startPointerY)`.
Ignore other pointers; explicitly clean up release, cancellation, and lost capture.

### P0 — Visual and logical positions can diverge
- **[Observed]** `fill: "forwards"` retains the animated `top`, but the target is never committed to the underlying position and the animation is never removed.
- **[Risk]** Subsequent inline writes can be masked by the retained animation. Concurrent releases can create competing animations.
- **[Observed]** Only fulfillment resets `animating`; cancellation would reject `.finished` without cleanup.

**Move:** Keep one position/state model and one owned animation. On completion, write the destination to the underlying style and remove the animation effect without a visual jump. Handle cancellation and cleanup explicitly. A new drag should interrupt settlement from the **currently rendered position**, not be ignored or jump to an old endpoint.

### P1 — The drag and settle treatments work against direct manipulation
- **[Observed]** `transition: all 300ms` applies to changes in `top` and `transform`. It can make pointer-driven updates trail the hand.
- **[Observed]** `:active` shrinks the entire sheet, including its contents, by 4%. This changes geometry during a positional gesture without communicating a snap state.
- **[Observed]** Release uses a fixed 480 ms `ease-in`: it starts slowly and accelerates toward the destination rather than visibly decelerating into rest.
- **[Risk]** Updating `top` can incur layout work; actual cost depends on the surrounding page.

**Move:** Remove transitions during tracking and remove whole-sheet press scaling. Use a dedicated translation transform for sheet movement. Give the handle restrained color or border feedback instead. Settle with a short decelerating curve or well-damped spring; roughly 180–280 ms is a starting hypothesis, not a validated timing.

### P1 — Snap intent and bounds need an explicit policy
- **[Observed]** The call uses current position only; no release velocity is supplied. The implementation of `nearestSnapPoint` is unavailable.
- **[Unknown]** Bounds, state thresholds, resize behavior, and nested-content scrolling are not shown.

**Move:** Define collapsed, half, and full anchors within the usable viewport. Clamp drag travel initially. For slow releases, use proximity with stable thresholds; for deliberate flicks, use bounded velocity projection and a documented state-skipping policy. Separate handle dragging from content scrolling, and assign `touch-action` deliberately rather than disabling sheet scrolling wholesale.

### P1 — Reduced Motion and non-drag state controls are absent
- **[Observed]** No reduced-motion branch or alternative state controls appear in the supplied code.
- **[Requirement]** Reduced Motion must retain state feedback without a large animated trip.

**Move:** Under Reduced Motion, resolve release and button-driven changes immediately to the chosen anchor. Preserve user-controlled tracking, but remove inertial travel, bounce, and scale. Keep a persistent state label and clear expand/collapse control feedback; any optional fade should be brief and non-spatial. Provide keyboard-operable controls for all three states. Manage focus and off-screen content according to whether the sheet is modal.

## Verification boundary
- **Verified by snippet inspection only:** the event guards, unused start coordinate, coordinate assignment, animation settings, and CSS declarations above.
- **Unverified:** rendered behavior, perceived timing, frame performance, touch/scroll arbitration, snap helper behavior, accessibility semantics, and surrounding implementation.
- No files were edited. No browser or device validation was performed.

## Smallest runtime validation plan
1. **Pointer lifecycle:** Drag from different grab offsets; hover without pressing; release outside; cancel; add a second pointer; re-grab mid-settle. Pass: no jump, unauthorized movement, stuck drag, or competing settlement.
2. **State selection:** Test slow releases around both boundaries and fast releases in both directions. Pass: predictable collapsed/half/full selection and exact agreement between rendered position and stored state.
3. **Touch and layout:** On one representative touch device, test handle dragging versus content scrolling, then resize or rotate. Pass: intentional gesture ownership and reachable, bounded anchors.
4. **Reduced Motion and keyboard:** Exercise all states with the preference enabled and via controls. Pass: no large automatic travel, visible state feedback, and usable focus.
5. **One performance trace:** Record a drag and settlement with representative content. Check for repeated layout work and missed frames before tuning duration.


## Output C

## Verdict

**[Static evidence] Not ready for reliable direct manipulation.** The snippet lacks gesture ownership, offset-preserving tracking, and a clean handoff between dragging and settling.  
**[Predicted experience]** It will likely feel slippery and inconsistent rather than calm: grabbing can displace the sheet, movement can trail input, and settling cannot be reliably interrupted.

Labels: **[Evidence]** visible in the supplied code; **[Risk]** inferred consequence requiring runtime confirmation; **[Proposal]** recommended change.

## Prioritized findings

### P0 — Correctness and user control
1. **[Evidence] Movement is not gated by an active gesture.** Every `pointermove` writes `top`; `startY` is saved but unused. There is no active pointer ID, capture, or cancellation handling.  
   **[Risk]** Mouse hover can move the sheet; another pointer can interfere; leaving its bounds can lose release events.

2. **[Evidence] Tracking uses absolute viewport coordinates, not drag displacement.** `clientY` is assigned directly to `top`, whose coordinate system depends on layout.  
   **[Risk]** The sheet jumps toward the pointer and loses the original grab offset. Coordinate mismatch can compound that jump.

3. **[Evidence] The animation lock is incomplete.** `animating` blocks only `pointerdown`; moves and releases still run. No animation handle is retained.  
   **[Risk]** Input is neither genuinely blocked nor properly accepted. Repeated releases can create overlapping animations, and an older completion can clear the flag while another animation is running.

4. **[Evidence] Reduced Motion has no branch in either JS or CSS.**  
   **[Risk]** Large automatic travel remains, contrary to the stated requirement. A CSS-only override would not disable the explicit Web Animation.

### P1 — Tracking and release quality
5. **[Evidence] `transition: all 300ms` includes changes to `top`.**  
   **[Risk]** Drag updates are interpolated instead of following the pointer immediately. Animating layout-affecting `top` also introduces layout work; actual frame cost is unmeasured.

6. **[Evidence] Release selects from position alone and uses `480ms ease-in`.** There is no release-velocity estimate.  
   **[Risk]** Slow drags and fast flicks at the same position get the same target. The curve begins slowly and ends without a gentle deceleration, breaking momentum continuity and making repeated use feel laborious.

7. **[Evidence] `fill: "forwards"` retains the animation effect without committing a canonical resting position or removing the effect.**  
   **[Risk]** Retained effects can mask later inline updates. Layout reads such as `offsetTop` are not a general solution for recovering the complete on-screen pose, particularly with transforms.

### P2 — Restraint and affordance
8. **[Evidence] `:active` scales the entire sheet to `0.96`.**  
   **[Risk]** Content visibly shrinks during manipulation, disturbing the spatial anchor. A broad sheet press effect can also accompany interaction with its controls. This is unnecessary motion for a frequently used operations surface.

## Concrete direct-manipulation moves

- **[Proposal] Use explicit `idle → dragging → settling` states**, one active pointer ID, primary-button filtering, pointer capture, and cleanup for `pointerup`, `pointercancel`, and `lostpointercapture`. Cancellation must not be treated as a flick.
- **[Proposal] On grab, take over from the current rendered position.** Sample the live pose before canceling the settle animation, preserve it as the new base, and record the pointer origin. Never wait for settlement to finish.
- **[Proposal] Track displacement:** `y = grabStartY + (pointerY − pointerStartY)`, with both positions expressed in one coordinate space. Use a single translation owner; remove transitions from that translation during dragging.
- **[Proposal] Render translation with `transform`,** coalescing updates to animation frames if needed. Keep geometry reads out of the per-move path. Remove whole-sheet press scaling; use an immediate handle highlight instead.
- **[Proposal] Define touch/scroll ownership.** Prefer a dedicated handle with appropriate `touch-action`; preserve native scrolling inside sheet content. If dragging from content is supported, explicitly arbitrate scroll position and vertical intent.
- **[Proposal] Bound movement between full and collapsed.** Track 1:1 within bounds; optionally add restrained resistance beyond them. Keep all three snap states reachable, with deterministic midpoint ties.
- **[Proposal] Estimate signed velocity from recent timestamped samples,** allowing it to decay after a pause. Project a bounded endpoint, choose its snap target, and pass release velocity into an interruptible, strongly damped spring. Start with no decorative bounce; tune rather than treating a fixed duration as the goal.
- **[Proposal] Finalize cleanly:** commit the resting translation and named state, remove the animation effect, and ensure canceled or stale completions cannot overwrite newer interaction state.
- **[Proposal] Reduced Motion:** retain immediate user-controlled tracking, but commit release/programmatic state changes without animated large travel, scaling, or overshoot. Confirm the destination with a persistent collapsed/half/full indicator and, optionally, a brief non-spatial highlight. Honor preference changes in JS and CSS.
- **[Proposal] Provide non-drag controls** for the three states, keyboard operation, and accessible current-state feedback. Motion must not be the only way to understand or change state.

## Verified / unverified boundaries

**Verified by inspection only:** the event logic, properties, timings, and omissions described above. No files were edited.

**Unverified:** actual rendering, frame pacing, coordinate layout, snap-point implementation, touch scrolling, browser animation interactions, accessibility markup, and any surrounding safeguards. No browser or device validation was performed.

## Smallest runtime validation plan

1. **Desktop pointer:** hover without pressing; grab at two different offsets; drag outside and release; re-grab and reverse mid-settle. Pass: no hover movement, grab jump, lockout, lost release, or stale completion.
2. **One touch device:** drag the handle, scroll content, add a second finger, and trigger cancellation. Pass: clear gesture ownership, native content scrolling, and no stuck state.
3. **Snap matrix:** slow drag, flick, and drag–pause–release in both directions around all three states. Pass: predictable targets, bounded travel, and continuous release handoff.
4. **Reduced Motion + keyboard:** exercise every state change, including changing the preference during settlement. Pass: no automatic large travel; destination, focus, and controls remain clear.
5. **One performance trace of repeated drag/re-grab cycles:** inspect frame pacing and layout work. Pass: no recurring motion-driven layout bottleneck or accumulating animation effects.
