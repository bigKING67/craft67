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

**[Static evidence] Not ready for repeated daily use.** The implementation does not maintain a reliable relationship between pointer movement, sheet position, and snap state. Its delayed settling and whole-sheet shrinking also work against a calm, direct manipulation feel.

Labels: **[Static]** visible in the supplied code; **[Risk]** depends on surrounding implementation; **[Recommendation]** proposed change.

## Prioritized findings

### P0 — Establish a real drag lifecycle
- **[Static]** `pointermove` updates position without checking whether a drag started. Hovering pointers can move the sheet.
- **[Static]** `startY` is recorded but never used. Setting `top` to `clientY` ignores both the initial sheet position and where the user grabbed it.
- **[Risk]** Unless the coordinate systems happen to align, the sheet jumps on movement; `clientY` is viewport-relative while `top` is relative to the positioning context.
- **[Static]** There is no active pointer ID, pointer capture, or cancellation handling. `pointerup` can settle without an accepted drag.
- **[Risk]** Leaving the sheet, browser touch scrolling, or a second pointer can interrupt or corrupt the gesture.

### P0 — Make position and animation ownership consistent
- **[Static]** `animating` blocks only `pointerdown`; movement and release handlers still run during settling. Multiple settle animations can start.
- **[Static]** A forwards-filled animation retains control of `top`, but its final value is not committed to the underlying inline position. Subsequent writes can be masked by the retained animation.
- **[Static]** `.finished` has no rejection cleanup. Introducing animation cancellation without addressing this would leave the flag stuck.
- **[Recommendation]** Keep one authoritative position, one active pointer, one active animation, and an explicit collapsed/half/full state. Interrupt settling from its current rendered position rather than ignoring a new grab.

### P1 — Remove lag and ambiguous motion
- **[Static]** `transition: all 300ms` applies to drag-time `top` changes. The sheet chases pointer updates instead of tracking them directly.
- **[Static]** The settle always takes 480 ms and uses `ease-in`: it starts slowly and accelerates toward the stop, rather than visibly braking into place.
- **[Static]** `:active` shrinks the entire sheet to 96%, including its content, without regard to whether a valid drag exists.
- **[Risk]** Repeated large-surface scaling may feel like a generic press effect rather than sheet manipulation.
- **[Recommendation]** Disable transitions during dragging; remove whole-sheet scaling. Use a subtle handle, border, or surface treatment for interaction feedback.

### P1 — Define snap intent and accessible alternatives
- **[Static]** The shown snap decision receives position only; release velocity is not explicitly supplied.
- **[Unverified]** `nearestSnapPoint` internals, bounds, scroll arbitration, state semantics, and keyboard controls are not shown.
- **[Static]** No Reduced Motion behavior appears in the supplied code. The shown release path always requests spatial animation.
- **[Recommendation]** Provide explicit controls for collapsed, half, and full states, with programmatically exposed state and predictable focus behavior.

## Concrete direct-manipulation moves

1. **Accept a deliberate grab.** Use a designated handle; accept one primary pointer and capture it. Do not hijack content controls or text selection.
2. **Preserve the grab offset.** Record pointer origin and current rendered sheet position in a consistent coordinate system. Compute `position = initialPosition + pointerDelta`.
3. **Track immediately.** Apply a bounded vertical translation with no easing or transition while dragging. Prefer `transform` over repeated `top` writes; avoid hot-path layout reads.
4. **Coordinate with scrolling.** Define `touch-action` on the handle and an explicit policy for sheet-content scrolling. Handle `pointercancel` and lost capture with cleanup and a deterministic resting state.
5. **Resolve intent predictably.** Use release position plus measured velocity to select among three bounded snaps. Slow releases choose nearby states; deliberate flicks advance directionally, with thresholds that prevent accidental skips.
6. **Settle quietly.** Use a short, distance-aware ease-out or restrained, non-oscillating spring. A roughly 180–280 ms settle is a starting hypothesis, not a validated target.
7. **Allow interruption.** Cancel the old settle, rebase to its visible position, and resume tracking without a jump. On completion, commit the final position and clear animation ownership.
8. **Respect Reduced Motion.** Keep necessary finger-following feedback, but eliminate autonomous snap travel and large-scale effects. Commit the destination immediately and signal it with an updated state label/indicator; optionally use a brief non-spatial treatment.

## Verified / unverified boundaries

**Verified by static inspection:** the event guards, coordinate assignment, unused origin, timing/easing, retained animation fill, broad transition, and active scaling described above.

**Not verified:** rendered appearance, frame rate, actual touch/scroll behavior, browser compatibility, assistive-technology behavior, or surrounding safeguards. No browser or device validation was performed.

## Smallest runtime validation plan

- **One desktop browser, mouse + keyboard:** test all three states, hover without grabbing, off-handle clicks, release outside, rapid re-grab during settling, and explicit state controls. Pass: no unintended movement, jumps, blocked interactions, or stale state.
- **One physical touch device:** test handle drag versus content scroll, slow release versus flick, a second touch, and cancellation. Pass: predictable ownership, bounded snaps, and no stuck drag.
- **Reduced Motion enabled:** repeat state changes and releases. Pass: no autonomous large spatial travel; destination and focus remain clear.
- **One short performance recording:** drag and settle through all states. Check pointer-to-sheet lag, repeated layout work, dropped frames, and retained animations after repeated interactions.


## Output B

## Verdict

**[Static evidence] Not ready for repeated-use direct manipulation.** The snippet lacks gesture ownership, mixes positioning and animation systems, and provides no Reduced Motion handling.  
**[Predicted experience]** Likely to feel detached and inconsistent rather than calm: grabbing can jump, dragging can lag, and settling cannot be reliably interrupted.

Labels below: **[Observed]** means visible in the supplied code; **[Risk]** means a runtime consequence requiring validation; **[Proposal]** means a recommended change.

## Prioritized findings

### P0 — Gesture correctness and user control

- **[Observed] No active-drag or pointer-ID guard.** Every delivered `pointermove` writes position—even mouse hover—and every delivered `pointerup` initiates settling. Returning from `pointerdown` does not disable the other handlers.
- **[Observed] Grab position is discarded.** `startY` is recorded but unused. `clientY` is viewport-relative; CSS `top` uses the element’s positioning context.
  **[Risk]** The sheet jumps toward the pointer instead of preserving where it was grabbed. Exact behavior depends on omitted positioning CSS.
- **[Observed] No explicit capture, cancellation, or lost-capture handling.**
  **[Risk]** Leaving the sheet, browser gesture takeover, or a second pointer can leave interaction state inconsistent. Touch implicit capture may help in some cases; it is not a complete lifecycle.
- **[Observed] Interruption is neither supported nor consistently blocked.** `animating` rejects a new start while moves and releases remain enabled. No animation handle is retained.
  **[Risk]** Overlapping settles and stale completion callbacks can race.

### P1 — Motion ownership and release behavior

- **[Observed] Three effects compete:** inline `top`, CSS `transition: all 300ms`, and a filled Web Animation on `top`.
  **[Risk]** CSS interpolation introduces tracking lag; a finished animation’s retained effect can mask later inline position changes. Completion does not commit the target into a durable position model.
- **[Observed] Release uses position alone and always takes 480ms with `ease-in`.** No release velocity is sampled or transferred.
  **[Risk]** A flick and a careful placement receive the same treatment; the settle begins slowly, accelerates toward the endpoint, then stops abruptly. This is poorly matched to frequent operational work.
- **[Observed] `top` is repeatedly written and `offsetTop` read.**
  **[Risk]** Layout work may affect smoothness. This is a performance concern, not measured jank.

### P1 — Reduced Motion and state access

- **[Observed] No preference branch exists in the supplied JS or CSS.** Disabling CSS transitions alone would not disable `sheet.animate()`.
- **[Observed] No non-drag controls or accessible state feedback are shown.** Their absence from the whole app cannot be inferred.
  **[Proposal]** Provide keyboard-operable controls for collapsed, half, and full states, with a persistent, accessible current-state indication.

### P2 — Unnecessary whole-surface feedback

- **[Observed] `:active` scales the entire sheet to `0.96`.**
  **[Risk]** Content and the apparent grab location move under the pointer; pressing child controls may also shrink the surface.
  **[Proposal]** Remove whole-sheet scaling. Use an immediate, restrained handle highlight instead.

## Concrete direct-manipulation moves

1. **Establish one position owner.** Maintain numerical `y`, active pointer ID, gesture phase, settled state, and a cancellable settle controller. Render translation through `transform`; do not transition the drag position.
2. **Grab the visible position.** On an eligible primary-pointer press, sample the current rendered position, cancel the settle without losing that position, record pointer origin, and capture the pointer.
3. **Track displacement, not absolute pointer coordinates:**  
   `y = grabbedY + (event.clientY - pointerDownY)`.  
   Update immediately, or coalesce to one write per animation frame without adding easing.
4. **Resolve scrolling deliberately.** Prefer a dedicated drag handle with an appropriate `touch-action` policy; preserve content scrolling and button interaction. If content can initiate dragging, define scroll-edge handoff and a small intent threshold.
5. **Bound the gesture.** Track 1:1 between collapsed and full; beyond them, use restrained progressive resistance. Define safe outcomes for `pointercancel` and lost capture; always clear ownership.
6. **Choose the snap from intent.** Estimate velocity from a short timestamped sample history, discard stale velocity after a pause, and use a bounded projected endpoint to select among the three states. Add hysteresis near boundaries to avoid accidental state changes.
7. **Settle calmly.** Use a velocity-aware, strongly damped spring with little or no overshoot. Treat tuning as provisional—not a universal duration. A new grab starts from the current presentation position; a retargeted settle carries current velocity.
8. **Finalize cleanly.** Commit the exact snap position and semantic state, release animation effects, and ignore stale callbacks. Handle cancellation/rejection without leaving a busy flag stuck.
9. **Reduced Motion:** keep deliberate dragging directly attached to input, but remove automatic long-travel settling, bounce, and scaling. Commit the selected snap immediately, optionally using a brief non-spatial indicator fade. Offer state buttons so no large drag is required. Apply preference changes to active JS motion too; do not erase the transform needed to represent the state.

## Verified / unverified boundaries

**Verified by static inspection:** the handlers, animation options, CSS rules, and missing safeguards described above. No files were edited.

**Unverified:** actual geometry, `nearestSnapPoint()` behavior, surrounding accessibility/scroll logic, browser animation interactions, frame cost, and perceived comfort. **No browser or device validation was performed.**

## Smallest runtime validation plan

Use one desktop mouse/keyboard browser and one real touch device, each with Reduced Motion off and on:

1. **Ownership:** hover without pressing; grab at different handle positions; leave bounds; cancel; add a second touch. Pass: no unsolicited motion, initial jump, or stuck gesture.
2. **Release/interruption:** slow drag, flick, pause then release, and reverse mid-settle across all three states. Pass: predictable snaps, continuous handoff, immediate re-grab, no stale completion jump.
3. **Scroll/accessibility:** scroll sheet content, activate child controls, and select all states by keyboard. Pass: no accidental drag, stable focus, clear state feedback.
4. **Reduced Motion:** repeat transitions and change the preference mid-settle. Pass: no automatic large spatial travel or bounce; state remains obvious and usable.
5. **One short performance trace:** record dragging plus interruption. Inspect layout work, missed frames, and competing effects; judge responsiveness from that evidence rather than assuming `transform` alone guarantees it.


## Output C

## Verdict — revise before shipping
**[Static evidence + product context]** The supplied code does not establish reliable direct manipulation or Reduced Motion behavior. For a calm, repeatedly used operations app, prioritize immediate tracking, interruptible settling, and unmistakable state feedback—not whole-sheet press effects.

Labels: **[S]** supplied-source fact; **[R]** runtime risk, not observed; **[M]** proposed move.

## Prioritized findings and direct-manipulation moves

### 1. P1 — Drag ownership and grab position are missing
- **[S]** `startY` is assigned but unused. Every `pointermove` writes `clientY` to `top`, without checking whether a drag started or which pointer owns it. Viewport coordinates are used as layout coordinates.
- **[R]** Hover could move the sheet; grabbing away from its top could cause a jump. Actual geometry depends on omitted positioning CSS.
- **[M]** Track one primary pointer and an explicit `idle / dragging / settling` state. Store the current sheet position and pointer origin in one coordinate space; apply `position = originPosition + pointerDelta`. Preserve the grab offset through a small intent threshold, initially 8–12 CSS px.
- **[M]** Capture the pointer; handle `pointercancel` and lost capture; ignore additional pointers. Prefer a dedicated handle with scoped touch-action rules so scrolling and controls inside the sheet remain usable.
- **Acceptance:** No movement on hover or taps; tracking preserves the initial offset, including outside the sheet; cancellation leaves a usable state.

### 2. P1 — Settling has no reliable interruption or finalization
- **[S]** `animating` blocks only `pointerdown`; moves and releases remain active. The animation handle is discarded. `fill: "forwards"` retains an animated value without committing it to the underlying inline position. Completion handles fulfillment only.
- **[R]** Re-grabs, overlapping releases, or cancellation could produce competing visual owners, masked drag writes, or stale completion state.
- **[M]** Give one controller ownership of presentation position, velocity, and animation. On re-grab, sample the current on-screen position and velocity before canceling—not the previous target. Continue from that presentation state without a jump.
- **[M]** On settle completion, commit the final position and named state (`collapsed`, `half`, `full`), then clear the animation. Handle cancellation/rejection and prevent an obsolete completion callback from finalizing a newer gesture.
- **Acceptance:** Re-grabbing and reversing at any point remains continuous; repeated interaction ends with one consistent visual and logical state.

### 3. P1 — Reduced Motion is not implemented in the snippet
- **[S]** Neither the JavaScript animation nor CSS includes a reduced-motion branch. Keyboard or non-drag state controls are not shown.
- **[R]** Users requesting reduced motion may still receive large animated travel. Whole-product accessibility cannot be determined from this excerpt.
- **[M]** Check `prefers-reduced-motion` in both motion paths. Remove animated snap travel, inertia, elastic overshoot, and whole-sheet scaling; apply the selected geometry immediately with a static state indicator or brief opacity/color feedback.
- **[M]** Keep essential user-controlled tracking direct, without adding autonomous travel. Provide keyboard-operable controls for all three states, with visible focus and an accessible indication of the selected state.
- **Acceptance:** Every state remains reachable and identifiable with Reduced Motion enabled and without dragging.

### 4. P2 — Release timing ignores gesture momentum
- **[S]** Every release uses `480ms` and `"ease-in"`. Target selection uses position only; no velocity samples are recorded.
- **[R]** A slow-starting settle that accelerates toward its endpoint may feel disconnected from release, especially during repeated use. This is not a measured feel judgment.
- **[M]** Measure recent movement using monotonic timestamps, reporting velocity in CSS px/s. Feed bounded release velocity into an interruptible, critically damped settle; roughly 0.25–0.35s response is a tuning starting point, not a fixed-duration requirement.
- **[M]** Preserve nearest-current-position targeting unless momentum-based selection is approved. A concrete experiment is `projectedY = clamp(currentY + velocity * 0.15s, fullY, collapsedY)`; only under approved momentum semantics select the nearest snap to that endpoint. Projection and velocity handoff are separate decisions.
- **Acceptance:** Slow releases and fast flicks follow the agreed snap rule; velocity handoff is continuous, with no decorative bounce or overshoot.

### 5. P2 — Motion properties compete with direct tracking
- **[S]** Dragging and settling write `top`; CSS declares `transition: all 300ms`. Pressing scales the entire sheet to `0.96`. No boundary treatment is shown.
- **[R]** Transitions may trail pointer updates; layout-property animation may add rendering work. Scaling the content may disturb apparent attachment and readability. Actual lag and frame cost are unverified.
- **[M]** Use one `translateY` owner for drag and settle; disable transitions on the tracking property. Restrict any remaining transitions to explicitly chosen feedback properties. Replace whole-sheet scale with immediate handle feedback.
- **[M]** Cache geometry outside the move hot path and batch writes to the display frame. Use bounded, progressive resistance beyond full/collapsed limits in normal motion mode. If scale is retained anywhere, separate its wrapper from translation ownership.
- **Acceptance:** Tracking has no easing tail; content stays visually stable; a trace shows no recurring layout work attributable to sheet-position writes.

## Evidence boundary
**Verified by static inspection:** the handlers, property choices, numeric timings, and missing guards/branches described above **in this excerpt**.

**Unverified:** actual positioning, snap-point definitions, surrounding accessibility controls, touch/scroll arbitration, visual continuity, rendering performance, and perceived feel. No files were edited; no browser or device validation was performed.

## Smallest runtime validation plan — proposed, not run
1. **One desktop browser session:** exercise all three states, hover/tap, grabs at different offsets, slow releases, fast flicks, and repeated mid-settle reversals. Record pointer position, presentation position, velocity, selected target, and final state.
2. **One representative touch-device session:** test leaving bounds, a second finger, cancellation, and scrolling/activating controls inside the sheet. Confirm findings 1–2 and boundary behavior.
3. **Repeat a short state cycle with Reduced Motion and keyboard only:** confirm finding 3, including visible state feedback and focus preservation.
4. **Capture one short screen recording and performance trace under representative app load:** assess findings 4–5. Record browser/device and refresh rate; inspect continuity and layout cost rather than inferring smoothness from screenshots.
