## 1. Evidence level and design read

**Verdict: block implementation approval on the supplied design; runtime behavior remains unverified.**

Using **design-craft**, in read-only critique mode. Evidence is **static source plus product context**—no rendered evidence, pointer trace, or browser/device validation. No files were edited.

**Reading this as:** a frequently used web operations sheet for task-focused users, with calm utility styling, optimized for changing workspace exposure without losing context.

## 2. Should this motion exist?

**Yes, narrowly:** movement should explain the sheet’s position, follow the user’s hand, and resolve release into a stable state.

- During drag, position changes are direct manipulation—not an eased animation chasing the pointer.
- After release, a restrained, interruptible settle is justified.
- Remove whole-sheet press scaling, decorative bounce, and blanket transitions.
- Do not animate unrelated content, typography, or layout changes simply because `transition: all` catches them.
- State feedback and renewed input must not wait for settlement.

## 3. Prioritized finding ledger

All five are **P1 approval blockers**, based on source-contract defects or explicit accessibility requirements—not observed feel failures.

| ID | Static proof | Interaction reasoning / runtime unknown | Repair | Acceptance evidence |
|---|---|---|---|---|
| **F1 — No owned drag session** | `pointermove` always writes `top`; `startY` is unused. No active pointer, grab offset, capture, or cancellation handling is shown. | Viewport `clientY` is assigned to containing-block `top`. Movement without a drag, initial jumps, lost tracking, and scroll conflicts are risks; actual behavior depends on layout and event delivery. | M1–M2 | Trace idle movement, offset grabs, outside release, cancellation, and competing touch/scroll input. |
| **F2 — Competing motion owners** | CSS transitions all properties for 300ms; JS writes and animates `top`; `:active` scales the entire sheet to 0.96. | The transition can filter direct tracking; layout-property animation creates performance risk. Whole-sheet scaling changes the apparent grab geometry without helping the task. Neither lag nor dropped frames is measured. | M1–M2 | Computed styles and frame trace confirm one position owner, preserved geometry, and no transition-induced chase. |
| **F3 — Interruption and completion are unsafe** | `animating` rejects only pointer-down; move/up remain active. Animation handle is discarded; `fill: "forwards"` persists; only successful completion clears the flag. | This is neither reliable locking nor interruption. Filled effects may override later inline writes; overlapping finishes can corrupt ownership. Recovery from cancellation is unspecified. | M3 | Re-grab repeatedly during settlement; verify position continuity, no stale completion, and no stuck state. |
| **F4 — Release ignores gesture dynamics** | Target uses only `nearestSnapPoint(sheet.offsetTop)`; settlement is fixed at 480ms with `ease-in`. No velocity sampling or boundary mapping is shown. | Ease-in starts slowly and accelerates toward the endpoint rather than naturally decelerating. Velocity discontinuity and escape beyond bounds are risks. Nearest-position targeting itself is not automatically wrong. | M4–M7 | Compare slow releases, fast flicks, reversals, near-target releases, and both limits using position/velocity traces. |
| **F5 — Reduced Motion is absent** | No preference branch appears in either snippet despite substantial positional animation. | The supplied implementation does not establish the required reduced-travel behavior. An external override is unknown, and CSS alone would not necessarily stop JS animation. | M8 | Test preference enabled initially and changed during a settle; state remains clear without animated large travel. |

## 4. Eight concrete design moves

1. **M1 — Immediate pointer-down feedback.**  
   Highlight the drag handle or its local surface immediately; keep sheet size and content stable. Remove `.sheet:active` scaling. Preserve visible keyboard focus and distinguish “pressed” from “drag committed.”

2. **M2 — Owned, 1:1 tracking.**  
   Use an explicit `idle → pending → dragging → settling` lifecycle with one active pointer ID. Capture the accepted pointer, ignore extra contacts, and clean up on `pointercancel`/lost capture. Scope touch handling to a handle so sheet content can still scroll.  
   Keep coordinates in CSS pixels in one sheet-container space: `y = grabbedPresentationY + (pointerY - downY)`. Use a small, tested intent threshold without an arbitrary time delay. Drive a single `translateY` owner with no positional CSS transition; cache geometry outside the move hot path.

3. **M3 — Interrupt from presentation state.**  
   On re-grab, sample the animator’s current on-screen position and velocity **before** cancelling it; preserve that position as the new drag origin, not the old snap target. Direct pointer control then takes precedence. Retargeted autonomous motion inherits current velocity.  
   Retain the animation handle, persist final position in owned state, remove obsolete effects, and guard completion/cancellation by generation so stale callbacks cannot finalize a newer gesture.

4. **M4 — Measure and hand off release velocity.**  
   Keep a short timestamped sample history, provisionally about 80–120ms. Estimate signed vertical velocity in **CSS px/s** using monotonic timestamps; handle pauses and discard implausible spikes. Feed the bounded measured velocity into the settle API, converting units explicitly if required. Do not restart every settle at zero velocity.

5. **M5 — Separate projection from target policy.**  
   Preserve nearest-current-position targeting unless momentum-based snap selection is explicitly approved. An auditable experiment is:  
   `projectedY = clamp(yRelease + clamp(vRelease, -vMax, vMax) * 0.15, yFull, yCollapsed)`  
   Here velocity is CSS px/s and the provisional projection horizon is **0.15s**; `vMax` is a documented, device-tested safety cap. Only if momentum targeting is authorized should `nearestSnapPoint(projectedY)` choose the state. Otherwise projection remains an experiment, while M4 still supplies velocity continuity.

6. **M6 — Restrained settle, not a fixed cinematic duration.**  
   Replace 480ms `ease-in` with a position/velocity-aware, critically damped spring; roughly 0.3s response is a tuning starting point, not a guaranteed duration. Constrain overshoot for this utility surface. Near-zero remaining distance should finish promptly, and input stays available throughout.

7. **M7 — Soft limits without losing context.**  
   Track 1:1 inside valid bounds. Beyond either limit, progressively resist displacement, for example `sign(o) * L * abs(o) / (L + abs(o))`, with overshoot `o` and a small tunable limit `L` in CSS pixels. Keep essential content reachable; release or cancellation resolves to a valid state. Recalculate snap geometry safely on resize.

8. **M8 — Reduced Motion plus equivalent controls.**  
   Keep user-controlled tracking, but remove elastic overshoot and autonomous large-distance travel. On release or button activation, commit the destination immediately, optionally using brief handle/color feedback and a persistent state label. Apply the preference to JS as well as CSS, including mid-animation changes. Provide keyboard/non-drag controls for all three states; preserve focus and announce committed state, not every move.

## 5. Verified versus unverified

**Verified by inspection:** the supplied property choices, durations, easing, missing session guards, unused grab origin, lack of velocity handling, and absence of a Reduced Motion branch in these snippets.

**Not verified:** rendered scaling, actual jumps or lag, frame rate, compositing, effective CSS overrides, snap geometry, content-scroll behavior, focus retention, responsive reachability, accessibility elsewhere in the app, or real-device touch feel.

These are proposed repairs and acceptance criteria—not implemented or validated improvements.

## 6. Minimal validation before approval

- **Browser interaction recording:** exercise all three states in both directions; include idle pointer movement, offset grabs, fast reversal, repeated mid-settle grabs, outside release, second touch, and cancellation. Log pointer ID, position, presentation position, velocity, target, and lifecycle state. Use this to close F1/F3/F4.
- **Computed-style and frame capture:** inspect CSS/WAAPI ownership during dragging and settlement. Test under representative operations-app load; check layout work and missed frames rather than assuming transforms guarantee smoothness. Close F2.
- **Responsive/context pass:** desktop and narrow touch layouts, resize/orientation change, long scrollable sheet content, and focused form controls. Verify snap bounds, reachable controls, and preserved task/scroll context.
- **Accessibility pass:** Reduced Motion on/off and toggled mid-settle; keyboard access to each state; stable focus, clear state feedback, and no large autonomous travel in the reduced mode. Close F5.
- **Physical touch pass:** at least one representative real device; include 60Hz and 120Hz hardware if both are supported release targets. Verify handle-versus-scroll arbitration and boundary resistance. Capture video/trace with browser, device, and refresh rate recorded.

**Approval remains blocked until the repairs are implemented and these checks provide evidence against the finding IDs. No browser or device checks were performed for this review.**
