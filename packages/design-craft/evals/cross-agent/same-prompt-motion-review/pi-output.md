## 1. Evidence level and design read

**Verdict: block implementation approval on the supplied evidence—not a claim of observed runtime failure.**

Using **design-craft, critique mode**. Evidence is **static code plus product context**; no rendered or interaction evidence. No files were edited or browser/device validation performed.

**Reading this as:** a web operations sheet for frequent daily use, with calm utility styling, optimized for changing working space without losing task context.

The interaction needs to feel owned by the user, not like a sequence that must finish before control returns.

## 2. Should this motion exist?

**Yes, selectively:** direct tracking establishes causality; a restrained release settle explains the selected snap state.

Do **not** animate:
- Pointer-following position with a CSS transition: tracking should be immediate, not eased.
- The entire sheet shrinking on press; this is a draggable workspace, not a push button.
- Unrelated properties via `transition: all`.
- Focus, task content, or controls merely because the sheet changes state.
- Large automatic travel or elastic overshoot under Reduced Motion.

A fixed **480 ms ease-in** settle is poorly matched to frequent utility interaction: its configured acceleration does not model a finger-to-sheet handoff.

## 3. Prioritized finding ledger

All five are **P1 approval blockers** in the supplied implementation. Runtime consequences remain hypotheses until tested.

| ID | Static proof | Direct-manipulation risk / runtime unknown | Repair | Acceptance evidence |
|---|---|---|---|---|
| **F1 — No coherent drag ownership** | `startY` is unused; every `pointermove` writes `clientY` to `top`; no active pointer, capture, threshold, or cancellation path is shown. | Viewport coordinates are assigned to a potentially different positioning space, without grab offset. Hover movement, jumps, lost releases, and scroll conflicts are risks. | M1–M2 | Pointer trace confirms preserved offset, ownership, cancellation, and no movement outside an accepted drag. |
| **F2 — Interruption and final state are not owned** | `animating` rejects only down; move/up remain active. Animation handle is discarded; `fill: "forwards"` persists the effect rather than committing a durable base position. Only successful completion clears the flag. | This is neither an effective lock nor safe interruption. Competing animations, stale completion, and presentation/base-state divergence are risks. | M3 | Re-grab at several settle phases; verify no positional jump, stale completion, or retained effect overriding the next drag. |
| **F3 — Position has competing animation mechanisms** | CSS transitions all properties over 300 ms; JS writes and animates `top`; active state scales the sheet to `0.96`. | Tracking may trail input; whole-content scaling weakens the apparent grab relationship. Layout-property animation adds performance risk, not proven dropped frames. | M1–M2 | Inspect computed styles and frame trace: one position owner, no tracking transition, no whole-sheet scale, bounded rendering work. |
| **F4 — Release discards motion history** | Target uses only `nearestSnapPoint(sheet.offsetTop)`; settle is 480 ms ease-in. No velocity samples or boundary treatment are shown. | Release may lose velocity continuity; unrestricted dragging may expose invalid space. Nearest-position targeting itself is not necessarily wrong. | M4–M6 | Compare slow releases, fast flicks, reversals, and edge pulls against explicitly agreed target semantics. |
| **F5 — Reduced Motion contract is absent** | No preference branch appears in the supplied JS/CSS despite substantial positional animation. | Whether another layer supplies accommodation is unknown; this excerpt does not satisfy the stated requirement. | M7–M8 | Reduced Motion run preserves state feedback and access without large automatic travel or bounce. |

## 4. Eight concrete design moves

1. **M1 — Immediate, local pointer-down feedback.**  
   Change the drag handle’s color or emphasis immediately; keep sheet size and content stable. Clear feedback on release/cancel. Preserve a distinct keyboard focus indicator rather than relying on `:active`.

2. **M2 — Establish a single 1:1 position owner.**  
   Track one primary `pointerId`; use a dedicated handle and an explicit touch/scroll policy. Capture the pointer and handle `pointercancel`/lost capture. Use CSS-pixel coordinates in one consistent space: `y = yAtDown + (pointerY - pointerYAtDown)`. Start with an 8–12 CSS px intent threshold, tuning its handoff so crossing it does not introduce a jump. Within bounds, apply direct `translateY` updates without easing; keep geometry reads outside the move loop.

3. **M3 — Interrupt from presentation, not the old target.**  
   On re-grab, sample the currently displayed position and current animation velocity **before** stopping the settle. Seed the drag baseline from that position; do not let inertia move the sheet away from a held pointer. Use an interruptible motion primitive with readable position/velocity. On completion, commit the exact snap position and logical state, clear effects, and invalidate stale callbacks; clean up on cancellation too.

4. **M4 — Hand measured velocity into the settle.**  
   Record a short recent position/time history using monotonic timestamps; estimate signed release velocity in **CSS px/s**, with downward positive. Bound outliers and feed velocity into the spring in its required units—not merely into target selection. Start with critical damping (`ζ = 1`) and roughly `0.25–0.30 s` response, as tuning hypotheses rather than validated values. Avoid bounce for this utility surface.

5. **M5 — Make projection explicit but conditional.**  
   Candidate experiment: `projectedY = clamp(yRelease + velocity * 0.15, yFull, yCollapsed)`, where position is CSS px and `0.15` is a **150 ms projection horizon**. Only if momentum-based targeting is authorized, select `nearestSnapPoint(projectedY)`. Otherwise retain nearest-current-position targeting, using the presentation position. Projection is a target-selection policy; velocity handoff in M4 remains necessary either way.

6. **M6 — Add restrained soft boundaries.**  
   Preserve 1:1 tracking inside the legal range; outside it, progressively resist motion. A candidate bounded mapping for overshoot `o` is `r = sign(o) * L * abs(o) / (L + abs(o))`, with provisional cap `L = 24 CSS px`. Release back to a valid snap, without a decorative rebound. Tune with touch evidence; prevent edge exposure from hiding essential controls.

7. **M7 — Give Reduced Motion a separate release path.**  
   Preserve intentional finger tracking, but remove momentum travel, rubber-banding, and spring overshoot. Commit the selected snap without interpolated large travel; retain immediate handle feedback and a persistent state label, optionally with a brief non-spatial color/opacity change. Respect preference changes during an active settle.

8. **M8 — Make state changes usable without dragging.**  
   Offer keyboard-operable controls for `collapsed`, `half`, and `full`, with an accessible current-state indication. Keep focus, inputs, and content scroll context stable; avoid remounting the task on snap. Under Reduced Motion these controls change geometry immediately rather than launching travel.

## 5. Verified versus unverified

**Verified from the excerpt:** the event guards and omissions listed in F1–F5, unused `startY`, property choices, explicit durations/easing, forwards fill, and active scale.

**Unverified:** actual computed positioning, cascade overrides, perceived lag/jumps, visual continuity, frame rate, layout cost, touch scrolling, responsive snap geometry, focus behavior, and any accessibility handling outside the excerpt.

The repairs are design/engineering proposals, **not tested fixes**. No whole-product accessibility or performance conclusion follows from this snippet alone.

## 6. Minimal validation plan before approval

- **Browser interaction trace — F1–F4:** record pointer position, displayed sheet position, velocity, selected target, and logical state. Exercise all three snaps, off-center grabs, no-button movement, slow drag, flick, reversal, and repeated mid-settle re-grabs.
- **Lifecycle and touch — F1–F2:** on a representative real touch device, test leaving bounds, second touch, cancellation, nested content scrolling, and release outside the handle. Require reliable recovery with no stuck ownership.
- **Computed style and performance — F3:** inspect actual transition/animation ownership and record a frame timeline under representative operations-app load. Test 60 Hz and 120 Hz where supported; look for recurring missed frame budgets and gesture-driven layout work. Do not infer compositor success from `transform` alone.
- **Edges and geometry — F4:** test both boundaries, desktop and narrow viewport, resize/orientation changes, and long scrollable content. Confirm snap points and essential controls remain valid.
- **Accessibility and context — F5:** run Reduced Motion, including toggling it mid-settle; test keyboard state controls and focus continuity. Confirm no large automatic travel and no loss of entered data or task position.

Retain trace/video artifacts with browser, device, viewport, and refresh-rate details. **Approval remains blocked until the five findings are resolved and their acceptance checks are observed.**
