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

## Verdict — block approval on static evidence

The supplied code does not establish reliable direct manipulation or Reduced Motion behavior. For a calm, repeatedly used operations app, prioritize immediate control and clear collapsed/half/full feedback over prolonged settling and whole-sheet scaling.

**Evidence labels:** **[Static]** visible in the snippet; **[Risk]** inferred outcome requiring runtime confirmation; **[Move]** proposed repair; **[Check]** acceptance evidence.

## Prioritized findings and direct-manipulation moves

### 1. P1 — Drag ownership and grab offset are missing
- **[Static]** `startY` is recorded but unused. Every `pointermove` writes viewport `clientY` directly to `top`, without an active-drag or pointer-ID guard. No capture, cancellation, or intent threshold is shown.
- **[Risk]** Hover movement could reposition the sheet; grabbing away from its top could cause a jump. Leaving its bounds, another pointer, or native scrolling could break tracking.
- **[Move]** Track one primary pointer through idle/pressed/dragging/settling states. Capture it; handle `pointercancel` and lost capture. Preserve the grab offset with `position = initialPosition + (clientY - initialClientY)` in a consistent CSS-pixel coordinate space. Start with an 8–12px intent threshold, then track 1:1 without easing. Confine gesture handling to a handle or define explicit scroll arbitration; do not disable scrolling across all sheet content.
- **[Check]** Hover and taps do not drag; grabs at different offsets preserve attachment; release outside and cancellation recover cleanly.

### 2. P1 — Settling has conflicting ownership and cannot be safely interrupted
- **[Static]** `animating` blocks only `pointerdown`; moves and releases still run. The animation handle is discarded, `fill: "forwards"` retains its effect, and no canonical settled position or cancellation cleanup is shown.
- **[Risk]** Animation and inline `top` updates could compete. Repeated releases could create overlapping animations; old completion callbacks could clear a newer animation’s flag.
- **[Move]** Give position one owner and retain the active animation. On re-grab, sample the current presentation position and velocity **before** canceling; resume from there rather than the previous target. Commit the final position and named snap state, then remove the animation effect. Guard completion by animation identity and handle cancellation rejection.
- **[Check]** Re-grab and reverse mid-settle repeatedly: no discontinuity, stale completion, stuck input, or accumulating animation effects.

### 3. P1 — Reduced Motion and non-drag state access are not demonstrated
- **[Static]** No preference branch is shown; releases always request 480ms of positional animation. Keyboard controls and state semantics are outside the supplied code.
- **[Risk]** Large travel may remain enabled for users requesting less motion; the three states may be inaccessible without dragging.
- **[Move]** Honor `prefers-reduced-motion` in both JS and CSS, including preference changes. Remove inertial travel, overshoot, and whole-sheet scaling. Commit snap changes without an animated traverse, retaining immediate handle feedback and a visible named-state indicator; an optional brief opacity/color change can confirm completion. Provide keyboard-operable collapsed/half/full controls and preserve appropriate focus. If dragging remains available, keep it directly user-controlled rather than adding trailing motion.
- **[Check]** All three states remain reachable and identifiable with keyboard and Reduced Motion enabled, without large automatic spatial travel.

### 4. P2 — Release motion does not account for gesture velocity
- **[Static]** Target selection uses `nearestSnapPoint(sheet.offsetTop)`; there is no velocity sampling. Every release uses `480ms` and `ease-in`.
- **[Risk]** Slow acceleration followed by an abrupt endpoint may feel disconnected from release, especially in repeated use. Flick intent is not represented.
- **[Move]** Measure recent position/time samples in **CSS px/s** and feed bounded release velocity into an interruptible, critically damped settle. Start tuning around a 250–300ms response scale—not a fixed completion guarantee—and avoid decorative bounce.
- **[Move]** Preserve nearest-current-position targeting unless momentum targeting is approved. A concrete experiment is `projectedY = clamp(currentY + velocity * 0.15, fullY, collapsedY)` with velocity in px/s and a 150ms horizon. Only if authorized, select the nearest valid snap to that endpoint. Velocity handoff and target selection are separate decisions. Add modest boundary resistance only in normal-motion mode.
- **[Check]** Compare slow releases and fast flicks near both snap boundaries; targets follow the agreed rule and settling preserves release continuity.

### 5. P2 — Layout animation and whole-sheet press feedback undermine restraint
- **[Static]** Dragging and settling modify `top`; CSS applies `transition: all 300ms` and scales the entire sheet to `0.96` while active.
- **[Risk]** Broad transitions could introduce tracking lag; layout-property animation could increase rendering work. Scaling an operational surface could disturb text and pointer attachment. None of these performance or perceptual outcomes is measured.
- **[Move]** Use one `translateY` owner with no transition during dragging; cache geometry outside the move loop and coalesce writes to display frames. Replace `transition: all` with narrowly scoped feedback transitions. Prefer handle color/outline feedback over sheet scaling. If scale is retained elsewhere, separate its wrapper from drag translation.
- **[Check]** Inspect computed transforms and a performance trace under representative app load; confirm direct tracking and absence of repeated gesture-driven layout work.

## Verified / unverified boundary

**Verified by inspection:** the shown event guards, property writes, duration/easing, retained fill, and absence of the described branches **within this snippet**.

**Unverified:** actual appearance, coordinate geometry, `nearestSnapPoint` behavior, surrounding accessibility support, scrolling interaction, frame timing, and perceived motion quality. No files were edited; no browser or device validation was performed.

## Smallest runtime validation plan — proposed, not executed

1. **One instrumented desktop-browser session:** exercise all three states, hover/tap, different grab offsets, outside release, cancellation, and repeated mid-settle reversals. Log pointer ID, presentation position, velocity, target, and animation ownership. Evaluate findings 1–2 and 4.
2. **In that session:** enable Reduced Motion, test keyboard state controls, then change the preference during settling. Verify finding 3 and capture a short recording of state feedback.
3. **One representative touch-device session:** check handle dragging versus content scrolling, second-touch rejection, and boundary behavior. Record browser/device and refresh rate.
4. **One short performance trace under normal app load:** evaluate finding 5. Provisional gates, subject to product ratification: input-to-presentation p95 ≤ two refresh intervals and no gesture-attributable task over 50ms. Failed correctness or motion-accessibility checks block approval; missed timing gates require profiling before acceptance.


## Output B

## Verdict — revise before shipping
**[Static evidence]** The implementation does not maintain a reliable pointer-to-sheet relationship, and its release animation conflicts with its CSS motion rules. For a calm, frequently used operations app, prioritize immediate tracking, predictable settling, and restrained state feedback—not extra movement.

## Prioritized findings

### P0 — Gesture ownership and position are incorrect
- **[Code]** `startY` is recorded but never used. Assigning `event.clientY` directly to `top` snaps the sheet’s edge to the pointer instead of preserving the initial grab offset. It also mixes viewport coordinates with the sheet’s positioning coordinate system.
- **[Code]** Every `pointermove` writes position, even without an active drag. The `animating` guard only blocks `pointerdown`; it does not block moves or releases.
- **[Code]** There is no active pointer ID, pointer capture, cancellation handling, or gesture cleanup. Releases can start animations without a valid drag; overlapping releases can make the boolean inaccurate.
- **[Risk]** Leaving the sheet, browser scrolling, or an interrupted touch may leave the interaction in an inconsistent state.

### P1 — Tracking and settling use competing motion mechanisms
- **[CSS]** `transition: all 300ms` makes position changes eligible for interpolation during dragging, rather than immediate tracking.
- **[Code]** `top` is a layout-affecting property. Updating it at pointer-event frequency can add layout work; actual cost depends on the surrounding page.
- **[Code]** `480ms ease-in` starts settling slowly and reaches the endpoint without a gentle deceleration. That is a poor default for frequent, calm interactions.
- **[Code]** `fill: "forwards"` retains the animation’s presentation, but the final target is not committed to the inline position. Retained effects can mask subsequent writes; cancellation and rejected `finished` promises are not handled.
- **[CSS]** `:active` shrinks the entire sheet, including its content. This is unrelated to the vertical gesture and introduces another transition on press and release.

### P1 — Snap intent and motion preferences are incomplete
- **[Code]** Release selects only by position. A deliberate quick flick and a slow placement at the same location receive the same target.
- **[Not shown]** Bounds, snap-point definitions, viewport changes, explicit collapsed/half/full state, and keyboard controls are absent from the excerpt.
- **[Not shown]** No Reduced Motion policy preserves state feedback while removing large automatic travel.

## Concrete direct-manipulation moves
1. **Own the gesture.** Use a dedicated drag handle; accept an eligible primary pointer, record its ID, capture it, and track explicit `idle / dragging / settling` phases. Handle `pointercancel` and lost capture with deterministic cleanup. Keep content scrolling separate; scope touch-action rules to the handle.
2. **Preserve the grab offset.** Record the rendered starting position and pointer Y. During drag, use `startPosition + (currentY − startY)` in one coordinate system, clamped between full and collapsed.
3. **Track without delay.** Position with `translateY`; disable position transitions while dragging. Keep gesture position in JS rather than repeatedly reading layout. Coalesce writes to animation frames if needed.
4. **Settle from intent.** Combine release position with a short, recent velocity sample. Use conservative, tuned flick thresholds and clear snap boundaries; keep slow releases nearest-position based.
5. **Use one motion owner.** Remove `transition: all` and whole-sheet active scaling. Let one controller own the translation. Commit the final position, clear the animation effect, and handle interruption and cancellation safely.
6. **Allow re-grabbing.** On a new drag during settling, take the current rendered position as the new origin, cancel the settle, and continue without a jump.
7. **Keep settling quiet.** Start with a short, distance-aware ease-out, roughly **180–280ms as a tuning hypothesis**, not a validated specification. Avoid bounce and overshoot.
8. **Separate state from motion.** Maintain explicit collapsed/half/full state and expose keyboard-operable state controls with a visible current-state cue. Give the handle a restrained pressed/focus treatment.
9. **Respect Reduced Motion.** Preserve direct finger tracking, but remove the large animated release/programmatic journey: commit the selected snap immediately, retaining a state label or selected-control cue. A brief non-spatial emphasis is optional.

## Verified / unverified boundaries
- **[Verified by inspection]** The unused start coordinate, ungated move/release handlers, animation settings, retained fill, broad transition, and active scaling are present.
- **[Unverified]** Actual smoothness, browser-specific animation interaction, scroll arbitration, snap geometry, surrounding accessibility, and device behavior.
- This is a static critique only; no browser or device validation was performed.

## Smallest runtime validation plan
Use one instrumented browser session with a mouse and keyboard, plus one real touch device:
1. **Tracking:** drag from different grab offsets; confirm no jump, lag, movement on hover, or response to a second pointer.
2. **Lifecycle:** release outside the handle, cancel a gesture, and re-grab mid-settle; confirm continuous position, clean state, and no unhandled rejection.
3. **Snaps:** slowly release near each boundary, then flick in both directions; confirm all three targets and deterministic bounds after a viewport resize.
4. **Access and preferences:** reach every state by keyboard; repeat with Reduced Motion enabled, confirming no large automatic travel and persistent state feedback.
5. **Performance:** record one drag-and-settle trace; check layout work and frame consistency before tuning timing.


## Output C

## Verdict

**[Static evidence] Not ready for a repeatedly used gesture sheet.** The code lacks a reliable drag lifecycle, mixes coordinate systems, and does not support continuous interruption or Reduced Motion.

**[Design judgment]** For a calm operations app, prioritize accurate tracking, predictable state changes, and quiet settling—not whole-sheet scaling or conspicuous bounce.

Labels below distinguish **observed code**, **inferred effects**, and **proposed behavior**.

## Prioritized findings

### P0 — Correctness and user control

1. **[Observed] Movement is not gated by an active drag.**
   Every `pointermove` writes `top`; `startY` is recorded but never used. There is no active pointer ID, capture, or cancellation handling.
   **[Inferred]** Mouse hover can reposition the sheet; leaving its bounds can lose the release; another pointer can interfere.

2. **[Observed] Pointer position is treated as sheet position.**
   `clientY` is viewport-relative; CSS `top` and `offsetTop` use layout positioning contexts. The grab offset is discarded.
   **[Inferred]** The sheet can jump toward the pointer and be mispositioned in an offset container. Exact behavior depends on omitted layout CSS.

3. **[Observed] The animation lock is incomplete and prevents a clean re-grab.**
   `animating` blocks only `pointerdown`; movement and release still run. The animation handle is not retained.
   **[Inferred]** Input may fight the running animation or start overlapping settles rather than take control. One completion can clear the boolean while another animation remains active.

4. **[Observed] No Reduced Motion path is shown.**
   Both the 480 ms spatial animation and whole-sheet press scaling remain enabled.
   **[Requirement gap]** State feedback needs a non-travel alternative, not merely a faster slide.

### P1 — Motion quality and state ownership

5. **[Observed] Three motion mechanisms compete.**
   Inline `top`, `transition: all 300ms`, and a filled Web Animation all affect presentation.
   **[Inferred]** CSS interpolation can make dragging trail the pointer. Finished `fill: "forwards"` effects can continue overriding subsequent inline positions; no explicit state commit or effect cleanup is shown.

6. **[Observed] Release uses position alone and a fixed `ease-in`.**
   No release velocity reaches snap selection or animation.
   **[Inferred]** Flicks and slow drags at the same position get the same target. The settle starts slowly and accelerates into its endpoint rather than decelerating naturally; 480 ms applies regardless of distance.

7. **[Observed] Position is animated through `top`.**
   **[Risk]** This can require layout work, unlike a transform-based path. Actual frame cost cannot be established from the snippet.

8. **[Observed] Pressing scales the entire sheet to `0.96`.**
   **[Design judgment]** Shrinking operational content weakens the sense of a stable surface and disturbs the grab relationship. A restrained handle highlight is more appropriate.

## Concrete direct-manipulation moves

**[Proposed] Use one position owner and an explicit lifecycle:** idle → pending gesture → dragging → settling.

- **On press:** accept the intended pointer/button; retain its ID. Sample the current rendered position before stopping any settle, preserve that position, and record `startPointerY` and `startSheetY`.
- **Establish intent:** use a small vertical movement threshold. Prefer a dedicated drag handle; keep content scrolling and interactive controls separate. Scope `touch-action` to the gesture surface rather than disabling scrolling across the sheet.
- **During drag:** capture the pointer and calculate  
  `y = startSheetY + (pointerY - startPointerY)`.  
  Render through `translateY`, with no positional CSS transition. Track recent timestamped positions for release velocity.
- **At limits:** keep tracking 1:1 inside the full–collapsed range; apply modest progressive resistance outside it. Do not let the sheet disappear beyond usable bounds.
- **On release:** use a bounded velocity projection to choose among collapsed, half, and full. Slow releases choose nearby states; intentional flicks favor their direction. Define state-skipping deliberately and add hysteresis to prevent midpoint indecision.
- **Settle:** carry release velocity into an interruptible, strongly damped spring. Start with no decorative bounce; tune for prompt settling rather than imposing the same duration on every journey.
- **On re-grab:** take over from the visible position immediately, without jumping to the old target. Preserve velocity when retargeting autonomous motion; pointer tracking takes priority during direct control.
- **On completion/cancellation:** commit the actual state and position, remove obsolete effects, release capture, and clear ownership. Handle `pointercancel` and lost capture with a safe settle—not a synthetic flick. Guard stale completion callbacks.
- **Press feedback:** highlight the handle immediately; remove whole-sheet scaling and replace `transition: all` with narrowly scoped feedback properties.

### Reduced Motion

**[Proposed]** Respect the preference in both CSS and the JavaScript settle path, including changes during a running animation.

- Keep user-controlled dragging directly attached to the pointer; remove automatic momentum travel, elastic overshoot, and scale feedback.
- On release or explicit state selection, apply the destination without an interpolated spatial journey. Use an optional brief opacity change or static state indicator to confirm the result.
- Provide keyboard-operable controls for all three states so dragging a large surface is not required.
- Preserve focus and expose the selected state in text/programmatic semantics; do not rely on movement or color alone.

## Verified / unverified boundaries

**Verified by inspection:** the handler logic, animation settings, CSS declarations, and missing handling **within the supplied snippet**.

**Unverified:** surrounding layout, snap-point calculations, scroll arbitration elsewhere, accessibility wiring, actual visual jumps, frame performance, and subjective feel. No files were edited; no browser or device validation was performed.

## Smallest runtime validation plan

**[Proposed—not performed]** Use one desktop browser with mouse/keyboard and one real touch device, with Reduced Motion off and on.

1. **Tracking:** hover, grab at different offsets, drag beyond the handle, then release. Pass: no hover movement, no grab jump, reliable capture, and 1:1 in-range tracking.
2. **State choice:** slow-release near each midpoint and flick both directions. Pass: all three states are reachable, targets follow the documented rule, and no boundary chatter occurs.
3. **Interruption/recovery:** reverse mid-settle, repeat rapidly, cancel a pointer, and introduce a second touch. Pass: no lockout, jump, stale completion, or orphaned drag.
4. **Integration/accessibility:** scroll sheet content, activate its controls, and select every state by keyboard under Reduced Motion. Pass: scrolling remains usable, focus is stable, and feedback survives without automatic large travel.
5. **One performance trace:** record a drag and settle with representative content. Check positional continuity and layout/frame work before claiming smoothness.
