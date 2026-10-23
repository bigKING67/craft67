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

**[Static evidence] Not ready for repeated-use gesture interaction.** The implementation does not maintain a reliable drag lifecycle, and its CSS and animation rules can compete. For a calm operations app, prioritize predictable finger tracking and clear collapsed/half/full states over decorative motion.

## Prioritized findings

1. **P0 — Movement is not gated by an active drag.**  
   **[Code]** Every `pointermove` writes `top`, including hover movement. `animating` only guards `pointerdown`; it does not block movement or release handling. `startY` is recorded but unused.  
   **[Expected consequence]** The sheet can move without a press and jump toward the pointer because the initial grab offset is lost.

2. **P0 — Pointer ownership and interruption are missing.**  
   **[Code]** No active pointer ID, pointer capture, `pointercancel`, or lost-capture handling is shown. Any received `pointerup` can initiate a snap.  
   **[Risk]** Leaving the sheet, a second touch, or browser scroll arbitration can interrupt or corrupt a drag. The snippet does not establish how sheet dragging coexists with scrolling its content.

3. **P1 — Three motion mechanisms can conflict.**  
   **[Code]** Pointer movement writes `top`; `transition: all 300ms` can interpolate those writes; release starts a separate `top` animation. Pressing also scales the sheet.  
   **[Expected consequence]** Transitions can make the sheet trail the pointer. Scaling changes the apparent grab geometry and makes a large operational surface feel unstable. Actual behavior depends on positioning and surrounding styles.

4. **P1 — Release timing is poorly matched to settling.**  
   **[Code]** Every snap takes 480 ms with `ease-in`, regardless of distance or release speed.  
   **[Motion judgment]** A slow start followed by acceleration into a hard stop is the opposite of a calm landing. Repeated half-second waits also add friction to frequent use.

5. **P1 — Settled state and animation cleanup are incomplete.**  
   **[Code]** `fill: "forwards"` retains the animation’s visual effect, but no target position or named state is committed. The animation handle is not retained, and rejection is not handled.  
   **[Risk]** A retained animation can override subsequent inline position updates. Cancellation can reject `.finished` and leave `animating` true. Overlapping releases can also make that boolean unreliable.

6. **P1 — Snap choice lacks demonstrated intent handling.**  
   **[Code]** The shown call passes only `offsetTop` to `nearestSnapPoint`. Pointer coordinates use viewport space, while `offsetTop` uses offset-parent space.  
   **[Unverified]** Snap-point geometry, bounds, velocity policy, and resize behavior are not provided. Position-only selection may undo an intentional flick.

7. **P1 — Reduced Motion and non-drag controls are not demonstrated.**  
   **[Code]** No reduced-motion branch or explicit state controls appear in the supplied snippet.  
   **[Requirement gap]** Reduced Motion needs equivalent state feedback without large travel—not merely a slightly shorter slide.

## Concrete direct-manipulation moves

- Use one lifecycle: **idle → dragging → settling → idle**, with one active pointer and one cancellable animation.
- On a valid handle press, capture the pointer and record both pointer Y and the sheet’s current rendered position. If settling, interrupt it from that visible position rather than ignoring the user.
- During drag, apply **initial position + pointer delta**, clamped between full and collapsed bounds. Keep all geometry in one coordinate system.
- Track with `translateY` on a dedicated motion wrapper; remove positional transitions while dragging. Avoid `transition: all` and whole-sheet press scaling. Give the handle a subtle color or contrast response instead.
- Restrict drag initiation to a clear handle or header. Define touch arbitration there; preserve normal scrolling and control activation inside sheet content.
- On release, choose among the three snap states using position plus bounded release velocity/direction. Use thresholds or hysteresis to avoid ambiguous boundary decisions.
- Settle with a short, distance-aware deceleration or well-damped spring. **[Tuning proposal]** Start around 180–280 ms for ordinary snaps, with no overshoot; tune from observed behavior rather than treating that range as validated.
- Commit the final position and named state, remove the finished animation, and restore lifecycle state on completion or cancellation. Ensure an older animation cannot clear a newer interaction.
- Provide keyboard-operable controls for collapsed, half, and full. Keep focus stable and expose the current state accessibly.
- With Reduced Motion, preserve intentional pointer tracking, but make release and button-driven state changes immediate or nearly so. Use a persistent state label/selected control, optionally a brief non-spatial highlight; disable scaling and bounce.

## Verified / unverified boundary

**Verified by inspection:** the supplied event guards, position writes, animation parameters, CSS rules, and missing lifecycle handling within this snippet.

**Not verified:** rendered behavior, frame rate, browser/device compatibility, surrounding accessibility support, sheet positioning, snap-point implementation, or any logic outside the snippet. No browser or device validation was performed.

## Smallest runtime validation plan

1. **One desktop browser:** hover must not move the sheet; test off-center grabs, all three snaps, release outside bounds, rapid re-grabs, and interruption during settling. Confirm no jumps or stuck states.
2. **One touch device:** test slow drags, directional flicks, cancellation, and a second touch; verify handle dragging does not break content scrolling.
3. **Reduced Motion + keyboard:** reach every state without dragging; confirm large automatic travel is absent and state/focus feedback remains clear.
4. **One short performance recording:** inspect drag and settle for frame stalls and repeated layout work. Confirm the committed position matches the visible endpoint and finished animations do not accumulate.


## Output B

## Verdict — request changes [static evidence]

The snippet does not establish reliable direct manipulation or Reduced Motion behavior. For a calm, repeatedly used operations app, prioritize immediate control, interruptible settling, and clear state feedback—not decorative sheet movement.

**Labels:** **[S]** supplied-code fact; **[R]** runtime risk, not observed; **[M]** proposed move.

## Prioritized findings and concrete moves

### 1. P1 — Drag ownership and coordinates are incomplete
- **[S]** `startY` is recorded but unused. Every `pointermove` writes viewport `clientY` directly to `top`, without an active-drag or pointer-ID check. No capture, cancellation, or boundary handling is shown.
- **[R]** Hover could move the sheet; grabbing below its edge could reposition it unexpectedly. Tracking outside the sheet and touch scrolling may conflict. Actual displacement depends on positioning CSS.
- **[M]** Use `idle → dragging → settling` ownership with one active pointer. Preserve the grab offset: `y = initialPresentationY + (clientY - initialPointerY)`, with positions in a consistent CSS-pixel coordinate space. Capture the pointer; handle `pointercancel` and lost capture; ignore extra pointers. Use a dedicated handle with an explicit touch-action policy while preserving content scrolling.
- **Acceptance:** Hover does nothing; taps remain taps; dragging from different grab points preserves offset; release outside and cancellation leave a usable state.

### 2. P1 — Settling cannot be reliably interrupted or finalized
- **[S]** `animating` guards only `pointerdown`; move/up remain active. The animation handle is discarded, `fill: "forwards"` retains the effect, and completion does not commit the target to underlying position/state. Rejection cleanup is absent.
- **[R]** Re-grabbing may produce competing ownership, masked style writes, or overlapping animations. Cancellation could leave the flag set; an older completion could clear it during a newer settle.
- **[M]** Keep one motion controller. On re-grab, sample current on-screen position and velocity, replace the settle without jumping, and hand control to the pointer. On completion, commit the exact snap position and collapsed/half/full state, then remove the animation effect. Make cleanup ownership-aware.
- **Acceptance:** Re-grab and reverse midway through a settle without discontinuity; rapid repeats cannot create stale completion effects; the next drag begins at the displayed position.

### 3. P1 — The motion configuration works against direct control
- **[S]** Dragging and settling write `top`; CSS applies `transition: all 300ms`; release uses a fixed `480ms ease-in`. The whole sheet scales to `0.96` when active.
- **[R]** CSS interpolation may make tracking trail the pointer; layout-property animation may increase rendering work. Slow-start settling and whole-sheet shrinkage risk feeling unnecessarily theatrical. No performance or feel has been measured.
- **[M]** Disable positional transitions during dragging. Drive `translateY` through one owner, batching writes on the display clock and avoiding per-frame layout reads. Replace whole-sheet scaling with immediate handle feedback; keep any separate feedback transform on a separate layer. For release, start with a non-bouncy, critically damped settle around a **0.25–0.3s response**, not a mandatory duration.
- **Acceptance:** In-range tracking stays attached to the pointer after intent recognition; press feedback does not distort content; a trace establishes rendering cost under representative app load.

### 4. P1 — Reduced Motion and non-drag state access are not demonstrated
- **[S]** No preference branch is shown for either CSS or the JavaScript animation. No alternative state controls or state announcement are supplied.
- **[R]** The shown path retains large spatial travel with Reduced Motion enabled. Keyboard access and state comprehension remain unknown, not proven absent throughout the app.
- **[M]** Honor `prefers-reduced-motion` in both motion owners, including preference changes. Commit state changes without animated travel, overshoot, or sheet scaling; retain a static state label and, optionally, brief handle color/opacity feedback. Provide keyboard-operable collapsed/half/full controls with visible focus. If “no large travel” also covers dragging, use gesture-threshold feedback followed by an immediate snap rather than continuous sheet translation.
- **Acceptance:** All three states remain reachable and identifiable with Reduced Motion and keyboard-only input; hidden content cannot retain inaccessible focus.

### 5. P2 — Release intent and edge behavior need an explicit contract
- **[S]** Target selection uses only `nearestSnapPoint(sheet.offsetTop)`. No velocity sampling or out-of-range resistance is shown; the helper’s internals are unknown.
- **[R]** Fast flicks and slow releases could resolve identically. Boundary behavior and snap stability cannot be inferred.
- **[M]** Measure recent release velocity in **CSS px/s** using monotonic timestamps and feed bounded velocity into the settle. Preserve nearest-current-position targeting unless momentum targeting is explicitly approved.
  - Experimental projection: `projectedY = clamp(y + v * 0.15, fullY, collapsedY)`—a provisional **150ms horizon**.
  - Only if approved, choose the nearest valid snap to that endpoint; otherwise keep projection as an experiment, separate from velocity handoff.
  - Start with an **8–12 CSS px** intent threshold; apply progressive edge resistance under normal motion, without decorative bounce.
- **Acceptance:** Slow releases, flicks, reversals, and both boundaries resolve predictably under the agreed targeting rule.

## Verified / unverified boundaries

- **Verified by inspection:** The event guards, property choices, timing values, retained fill, and missing branches **within this snippet**.
- **Unverified:** Rendered geometry, snap-helper behavior, surrounding accessibility, scroll arbitration, perceived latency, frame pacing, and browser/device behavior.
- **No files edited. No browser or device validation performed.**

## Smallest runtime validation plan — proposed, not executed

1. **One desktop browser session:** Exercise all three states, hover, off-center grabs, taps, slow drags, flicks, edge overshoot, release outside, mid-settle reversal, and rapid repeats. Log pointer ID, presentation position, velocity, target, and committed state; record a short video.
2. **Same session, Reduced Motion + keyboard:** Repeat state changes and interruption; verify no animated large travel, visible state feedback, reachable controls, and appropriate focus.
3. **One representative touch-device run:** Check handle dragging versus content scrolling, cancellation, and an extra finger. Record browser, device, and refresh rate.
4. **One short performance trace under typical app load:** Check F3’s layout/paint cost and frame pacing. Provisional gates, subject to product ratification: p95 gesture-update work below **8ms**, no gesture-attributable task over **50ms**; revise the motion approach if exceeded. These are proposed thresholds, not measured results.


## Output C

## Verdict

**[Static evidence] Not ready for reliable direct manipulation.** The main problems are gesture ownership, coordinate handling, and competing motion controls—not simply an easing choice. **[Expected effect, untested]** Together these risk jumps, delayed tracking, and unreliable re-grabs: costly friction in a repeatedly used, calm operations app.

Labels below distinguish **Observed** code facts, **Expected** consequences, and **Proposed** changes.

## Prioritized findings

### P0 — Fix gesture correctness and ownership
- **[Observed]** `startY` is recorded but unused. Every move assigns viewport `clientY` directly to CSS `top`, whose coordinate space depends on layout.
  **[Expected]** The sheet can jump toward the pointer and lose the original grab offset.
- **[Observed]** Moves and releases have no active-drag or pointer-ID guard. Mouse hover can write position; an unrelated release can initiate a snap.
- **[Observed]** No pointer capture, cancellation handling, or touch/scroll arbitration appears.
  **[Expected]** Leaving the sheet, browser gesture takeover, or a second pointer can disrupt the interaction.
- **[Proposed]** Own one pointer; accept appropriate primary-button input; capture it; handle `pointercancel` and `lostpointercapture` with an explicit cleanup policy. Use a dedicated drag handle, preserving ordinary scrolling and controls inside the sheet.

### P0 — Make settling interruptible and single-owner
- **[Observed]** `animating` blocks only `pointerdown`; moves and releases remain enabled. It neither safely locks interaction nor supports interruption.
- **[Observed]** The animation handle is discarded. `fill: "forwards"` retains an animated value without committing the final position to the underlying style. There is no cancellation/rejection cleanup.
  **[Expected]** Subsequent style writes can be masked by the filled animation; overlapping completions can clear the boolean at the wrong time.
- **[Proposed]** Use explicit `idle → dragging → settling` states and one motion controller. Re-grabbing must start at the **currently displayed position**, stop the previous settle without jumping, and immediately return control to the pointer. Commit settled position and remove the old animation effect; guard stale callbacks.

### P1 — Remove tracking lag and competing effects
- **[Observed]** `transition: all 300ms` includes `top` and the active-state transform. Drag updates are therefore subject to a transition rather than direct tracking.
- **[Observed]** Position uses `top`; `:active` also shrinks the whole sheet to `0.96`.
  **[Expected]** Layout work may increase, while shrinking a large working surface shifts content and weakens the sense of a stable grip.
- **[Proposed]** Position through a single `translateY` channel with **no positional transition while dragging**. Remove whole-sheet press scaling; give immediate, restrained feedback on the handle instead. Scope any remaining transitions to named properties. Transform use is a performance opportunity, not proof of smoothness.

### P1 — Preserve release intent, then settle quietly
- **[Observed]** The shown snap call receives position only; no release velocity is tracked or handed off. A fixed 480ms `ease-in` starts slowly and accelerates toward its endpoint rather than easing into rest.
- **[Expected]** A flick can feel discarded, and a small correction can take disproportionately long.
- **[Proposed]** Select among collapsed, half, and full using position **plus bounded velocity projection**. Use a velocity-aware, interruptible spring with critical or near-critical damping: no decorative bounce by default. Treat response tuning as a runtime question, not a universal duration.

### P1 — Supply an explicit Reduced Motion path
- **[Observed]** Neither snippet checks the motion preference.
- **[Proposed]** Disable inertial travel, overshoot, and whole-sheet scaling. For strict avoidance of large travel, keep the sheet stationary during gesture preview, indicate the candidate state on the handle/state control, then commit geometry immediately on release. A brief opacity or color cue can confirm the change without sliding.
- Provide explicit **Collapsed / Half / Full** controls usable by keyboard and pointer; preserve focus and expose the selected state. A CSS media query alone will not disable the JavaScript animation.

## Concrete direct-manipulation sequence

1. **Grab:** accept the owning pointer, capture the live sheet position, interrupt settling, and record pointer origin plus recent timestamped positions.
2. **Track:** compute `y = grabbedSheetY + (pointerY − grabbedPointerY)` in one consistent coordinate space. Keep tracking 1:1 within bounds; use restrained progressive resistance beyond the endpoints.
3. **Disambiguate:** use a small movement threshold to separate taps from drags without introducing a jump when dragging begins. Set touch behavior on the handle before the gesture starts; do not disable scrolling across the entire sheet.
4. **Release:** estimate velocity from a short recent sample window, ignoring stale motion after a pause. Project a bounded endpoint and choose a valid snap, with hysteresis near boundaries.
5. **Settle:** start from current position and release velocity. Permit immediate re-grab and reversal. Commit exactly one final state.
6. **Cancel:** release ownership, clear samples, and restore or settle to a defined valid state; never treat cancellation as an intentional flick.

## Verified / unverified boundary

**Verified by static inspection only:** the handlers, properties, timing, guards, and missing mechanisms described above.

**Unverified:** actual layout/containing block, snap-helper behavior, surrounding accessibility and scroll handling, browser animation interactions, frame pacing, perceived feel, and device behavior. No files were edited; no browser or device validation was performed.

## Smallest runtime validation plan

- **Desktop mouse:** hover without pressing; grab at different offsets; leave the bounds while dragging; re-grab and reverse halfway through settling. Pass: no hover movement, jumps, lost ownership, or stale completion.
- **One touch device:** slow drag, fast flick, pause-then-release, second touch, cancellation, and scroll inside sheet content. Exercise all three states. Pass: predictable targets and no unintended scroll takeover.
- **Reduced Motion + keyboard:** change among all states and interrupt an in-progress settle when the preference changes. Pass: no large animated travel, clear state feedback, retained focus, and no drag-only functionality.
- **One performance trace:** record drag → release → re-grab. Inspect actual frame pacing and layout work; tune spring response only after correctness passes.
