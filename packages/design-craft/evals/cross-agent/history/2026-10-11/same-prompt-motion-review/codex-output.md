**Verdict: withhold implementation approval.** Motion has a useful role here, but the supplied code does not establish reliable gesture ownership, interruption, or Reduced Motion behavior.

Reading this as a repeatedly used web operations surface, with a calm utility character, optimized for moving between three sheet states while preserving task context.

Evidence level: **L0 static**, with product context. This review uses only the supplied code and prompt; no files were edited and no browser/device validation was performed.

**Should this animate?**

Yes: immediate pointer attachment and a restrained release settle can explain the relationship between `collapsed`, `half`, and `full`. Motion should remain subordinate to input.

Do not tween pointer tracking, scale the entire working surface on press, animate unrelated properties through `transition: all`, or delay task access until settling finishes. Reduced Motion should remove large autonomous travel and elastic effects while retaining clear state feedback.

**Prioritized finding ledger**

All five are P1 approval blockers for this supplied implementation, not claims of observed runtime failure. Repairs and acceptance checks are referenced below.

| ID | Static proof | Direct-manipulation risk / runtime unknown | Repair → acceptance |
|---|---|---|---|
| F1 — Gesture ownership | `pointermove` writes without an active-drag check; `startY` is unused. No pointer-ID ownership, capture, or cancellation appears. | Hover or unrelated pointers could move the sheet; a release outside the surface could lose lifecycle completion. Actual event delivery is unverified. | M1–M2 → V1 |
| F2 — Pointer attachment | Viewport `clientY` is assigned directly to `top`, without grab offset or containing-block conversion. CSS declares `transition: all 300ms` and whole-sheet `scale(0.96)`. | Position could jump toward the pointer, trail it, or change apparent attachment during scaling. `top` adds layout-work risk; no frame cost was measured. | M1–M2 → V1, V4 |
| F3 — Interruption and state ownership | `animating` rejects pointer-down initialization but does not guard move/up. The animation handle is discarded; `fill: "forwards"` remains, with no explicit final-position commit or cancellation cleanup. | A new gesture could compete with a retained animation effect or stale state. The guard does not provide coherent interruption. | M3 → V2 |
| F4 — Release physics | Settle uses fixed `480ms`, `ease-in`, and nearest-current-position targeting. No velocity samples or velocity handoff appear. | Slow initial response and accelerating arrival risk breaking continuity with the gesture. Nearest-position targeting itself is legitimate; momentum targeting is not established by the brief. | M4–M6 → V2 |
| F5 — Reduced Motion | Neither the CSS nor JavaScript shows a Reduced Motion branch. | The supplied path provides no alternative to large settling travel. Any application-level compensation is unknown. | M7–M8 → V3 |

**Eight concrete design moves**

1. **M1 — Local pointer-down feedback.** Give the drag handle an immediate pressed color or outline; remove whole-sheet scaling. Keep content controls and scrolling distinct from the drag affordance.

2. **M2 — Establish 1:1 tracking.** Own one pointer ID, capture it, and handle up, cancel, and lost capture. Use one coordinate space in CSS pixels: `y = presentationYAtDown + (pointerY − pointerYAtDown)`. After a small intent threshold, track without easing or transitions; preserve displacement accumulated across that threshold. Drive translation through one transform owner, with geometry measured outside the move hot path.

3. **M3 — Grab the presentation value.** Retain a controller exposing current position and velocity. On re-grab, sample that state before cancelling the settle, establish the new grab offset, and let the pointer take ownership immediately. For autonomous retargets, carry velocity forward. Commit the final position and named state, remove finished effects, and prevent stale completion callbacks from overwriting newer gestures.

4. **M4 — Hand off measured velocity.** Estimate release velocity from a short timestamped position history, in **CSS px/s**, including pauses before release. Initialize the settle at the current presentation position with that velocity in the solver’s units. Use a critically damped, non-bouncy response; roughly 200–300ms response is a tuning hypothesis, not a fixed completion deadline or verified optimum.

5. **M5 — Separate projection from target selection.** Candidate experiment: `projectedY = clamp(y + clamp(v, −2000, 2000) × 0.15, minSnapY, maxSnapY)`, using px/s and a 0.15-second horizon. These are provisional bounds. Preserve nearest-current-position targeting for now; choose the nearest snap to `projectedY` only if momentum-based targeting becomes the product contract. Velocity handoff remains useful either way.

6. **M6 — Add soft outer boundaries.** Keep tracking 1:1 inside the valid range. Outside it, apply bounded resistance, for example `displayY = boundary + overshoot / (1 + abs(overshoot) / 64)` in CSS pixels. The 64px limit is provisional. Release toward a valid snap without decorative rebound; define deterministic recovery for cancellation.

7. **M7 — Provide a Reduced Motion path.** Preserve unsmoothed movement directly controlled by the pointer, but remove autonomous travel, elastic overshoot, and scale feedback. On release or discrete state selection, commit the target immediately and indicate the resulting state with a static label or brief non-spatial highlight. Honor the preference in the JavaScript settle controller as well as CSS.

8. **M8 — Preserve non-drag operation and context.** Offer keyboard-operable controls for all three named states, using the same state controller. Keep focus, entered data, and relevant scroll context stable; communicate the selected state without announcing every drag frame.

**Verified versus unverified**

Verified here means source inspection only: the handlers, property choices, timing, easing, guard placement, and absent branches listed in F1–F5.

Unverified: actual jumps, lag, smoothness, animation precedence in the rendered page, layout cost, touch-scroll arbitration, responsive snap geometry, focus behavior, and Reduced Motion output. The moves above are proposed behavior, not completed fixes.

**Minimal validation before approval**

- **V1 — Pointer ownership and attachment:** In a browser, record pointer coordinates and rendered sheet position. Test multiple grab offsets, hover, taps, boundary crossing, release outside, cancellation, second-pointer input, and scrolling inside the sheet. Confirm preserved offset and 1:1 in-range displacement after intent.
- **V2 — Physics and interruption:** Record slow drags, flicks, paused releases, reversals, and re-grabs early/mid/late in settling across all three states. Confirm no position discontinuity, inspect velocity continuity, and log release position, velocity, candidate projection, and selected target.
- **V3 — Accessibility and geometry:** Exercise Reduced Motion, keyboard state changes, focus/context preservation, desktop and narrow layouts, and viewport resizing. Confirm no autonomous large travel in Reduced Motion.
- **V4 — Device and performance:** Repeat decisive gestures on representative real touch hardware, including content-scroll conflicts; capture a frame timeline under representative app load. Record browser, device, refresh rate, and trace/video artifacts. Check 60/120Hz where supported and relevant.

Approval remains pending those runtime checks and resolution of F1–F5.