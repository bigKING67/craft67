**Verdict: withhold implementation approval.** The motion has a valid purpose, but the supplied code does not establish reliable direct manipulation or Reduced Motion behavior.

**1. Evidence level and design read**

L0 static evidence: supplied code and product context only; no rendered evidence. Reading this as a frequently used web operations sheet with a calm utility style, optimized for changing workspace extent while retaining task context.

**2. Should this animate?**

Yes: movement under the pointer explains direct manipulation; a restrained release settle can explain the selected state. Neither should delay further input.

Do not animate pointer-following position through a CSS transition. Remove whole-sheet press scaling, decorative bounce, and blanket `transition: all`. Content, focus feedback, and task actions should not wait for the settle. Reduced Motion should eliminate large autonomous travel while retaining clear state feedback.

**3. Prioritized blocking findings**

All five are P1 approval blockers for the supplied implementation, not claims of observed device failure. Repair and acceptance references point to the moves and checks below.

| ID | Static proof | Direct-manipulation / physics concern; runtime unknown | Repair → acceptance |
|---|---|---|---|
| F1 | `startY` is unused; every `pointermove` writes `clientY` into `top`. No active-pointer guard, capture, or cancellation is shown. | Grab offset is not preserved; viewport coordinates are assigned to a potentially different positioning space. Hover or unrelated pointers can reach the write. Actual jumps, escaped drags, and scroll conflicts remain unobserved. | M1–M2 → V1 |
| F2 | `transition: all 300ms`, animated `top`, and whole-sheet `scale(0.96)`. | Transitioned tracking can separate sheet position from the pointer; scaling changes the grabbed surface’s geometry. Layout animation adds performance risk. Computed transitions and frame cost are unknown. | M1–M2 → V1, V4 |
| F3 | `animating` rejects only pointer-down; move/up remain unguarded. No animation handle is retained; forwards fill has no explicit commit/cleanup. | Ownership is inconsistent during settling. Re-grabbing cannot deliberately inherit presentation position and velocity; repeated releases can create competing animations. Actual composition and stale-state effects are unverified. | M3 → V2 |
| F4 | Release uses nearest current position and a fixed `480ms ease-in`; no velocity sampling or handoff exists. | The settle restarts without the gesture’s velocity; acceleration toward the endpoint risks an abrupt arrival. Nearest-position targeting itself is not a defect: momentum targeting is not established by the product contract. | M4–M6 → V2 |
| F5 | No Reduced Motion branch appears in either snippet. | Large positional settling has no shown accessible alternative. Global overrides or other controls may exist, but are not evidenced. | M7–M8 → V3 |

**4. Concrete design moves**

1. **M1 — Immediate pointer-down feedback.** Change the handle’s color or outline immediately; retain visible keyboard focus. Remove whole-sheet scaling. Give dragging a defined handle region so pressing task content does not automatically reposition the sheet.

2. **M2 — Establish 1:1 tracking.** Use one coordinate space in CSS pixels. Store pointer ID, pointer origin, and current sheet presentation position; calculate `y = originY + pointerDeltaY`, preserving grab offset. After a provisional 8–12px intent threshold, apply position without easing or transition. Use a single transform owner, pointer capture, and explicit up/cancel/lost-capture cleanup; ignore other pointers. Define touch-action and content-scroll ownership.

3. **M3 — Interrupt from presentation values.** Keep a controller exposing current rendered position and velocity. On re-grab, sample them before stopping the old settle, rebase the drag there, and immediately give the pointer ownership. Retargeted autonomous motion inherits current velocity; held motion follows the pointer without residual drift. Commit the final position and state, clear animation effects, and prevent cancelled or stale completions from changing ownership.

4. **M4 — Hand off measured velocity.** Estimate signed release velocity from a short recent history of position and monotonic timestamps, in CSS px/s. Feed that velocity and the current presentation position into the settle, converting units if required by its API. Start with a critically damped spring and roughly 0.25–0.30s response, subject to testing; this is a tuning hypothesis, not a measured duration.

5. **M5 — Separate projection from target selection.** Preserve nearest-position selection by default. A testable momentum candidate is:
   `vBound = clamp(vRelease, -2000, 2000)` in CSS px/s;
   `yProjected = clamp(yRelease + vBound × 0.15s, yFull, yCollapsed)`.
   These are provisional bounds. Only if momentum targeting is selected should `nearestSnapPoint(yProjected)` replace the existing rule. Velocity handoff in M4 remains useful with either rule.

6. **M6 — Use soft boundaries.** Within valid bounds, retain 1:1 movement. Outside them, map signed overshoot `o` through `r(o) = L × o / (L + |o|)`, with a small, provisional cap such as `L = 24 CSS px`. Keep targets within the three valid states; recover without decorative oscillation. Test reversals and re-entry.

7. **M7 — Provide Reduced Motion behavior.** Keep deliberate pointer tracking, but disable elastic overshoot and autonomous travel. On release or discrete state selection, apply the target immediately; confirm it through a persistent state label and optional brief nonspatial feedback. Handle preference changes during an active settle.

8. **M8 — Provide equivalent discrete controls.** Offer keyboard-operable controls for collapsed, half, and full, with visible focus and an accessible current-state indication. Preserve task data, content scroll position, and focus where still visible; if collapsing hides the focused control, move focus predictably to the sheet control.

**5. Verified versus unverified**

Verified from the snippets: property choices, timings, easing, handler guards, unused grab origin, and absence of the listed lifecycle, velocity, and Reduced Motion logic **within this evidence**.

Unverified: actual lag, jumps, smoothness, effective styles, containing-block geometry, frame cost, global accessibility handling, responsive behavior, and touch feel. No files were edited; no browser or device validation was performed.

**6. Minimal validation before approval**

- **V1 — Ownership and tracking:** In a desktop browser, record pointer and rendered-position traces. Test grabs at different offsets, hover without pressing, threshold crossing, exit from bounds, cancellation, and a second pointer. Require preserved offset and 1:1 in-range displacement, with no movement from unowned pointers.
- **V2 — Release and interruption:** Test slow releases, flicks, reversals, boundary recovery, and re-grabs early/mid/late in settling across all three states. Record presentation position, velocity, and selected target. Require no positional discontinuity, stale completion, or competing animation; assess M5 separately if trialled.
- **V3 — Accessibility and context:** Run Reduced Motion, toggle it mid-settle, and exercise keyboard controls. Require no large autonomous travel or elasticity, clear final state, reachable controls, and preserved task context.
- **V4 — Responsive and device behavior:** Check desktop and narrow layouts, then real touch hardware for content scrolling, cancellation, and boundary feel. Capture a frame timeline under representative operations-app load; include 60Hz and 120Hz hardware where supported. Inspect recurring layout/paint work and missed frames before making performance claims.

Record browser/device, viewport, refresh rate, and trace/video artifacts. Approval remains pending these checks and resolution of F1–F5.