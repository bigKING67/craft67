## 1. Evidence level and design read

**Verdict: block implementation approval pending interaction repairs and runtime evidence.** This is a design-contract judgment, not an observed device failure.

Using **design-craft**, in read-only critique mode. Evidence is **static code plus product context**; no rendered, browser, or device evidence. No files were edited.

**Reading this as:** a repeatedly used web operations sheet, with calm utility styling, optimized for moving between three states while preserving task context.

The right mental model is “a surface I control,” not “an animation I must wait for.”

## 2. Should this motion exist?

**Yes, narrowly:** direct tracking explains the relationship between hand and sheet; a restrained release settle explains arrival at a snap state.

Do **not** animate:
- Pointer-following position through a CSS transition; direct manipulation must not chase the pointer.
- Whole-sheet press scaling: shrinking task content adds unrelated motion and changes its apparent geometry.
- Unrelated properties through `transition: all`.
- Background task content or focus merely because the sheet changes state.
- Large autonomous travel or elastic overshoot under Reduced Motion.

## 3. Prioritized findings

All five are **P1 approval blockers in the supplied implementation**. Runtime consequences remain hypotheses until tested.

| ID | Static proof | Direct-manipulation risk / unknown | Repair → acceptance evidence |
|---|---|---|---|
| **F1 — Gesture ownership and coordinates** | `startY` is unused; every `pointermove` writes viewport `clientY` into `top`. No active-pointer guard, grab offset, capture, or cancellation handling is shown. | Position can change without an owned drag; viewport and containing-block coordinates may differ; the grab point may jump. Actual geometry and touch-scroll arbitration are unknown. | Moves 1–2 → trace shows preserved grab offset, owned-pointer-only movement, and reliable outside-bounds release/cancel. |
| **F2 — Competing position owners** | `top` is written during moves, covered by `transition: all 300ms`, and animated by WAAPI with retained forward fill. Press adds `scale(0.96)`. | Transition interpolation may separate sheet from hand; filled effects may obscure later inline updates. Layout cost and actual cascade effects are unmeasured. | Moves 1–3 → computed-style and frame traces establish one position owner, no drag interpolation, and clean animation cleanup. |
| **F3 — No coherent interruption** | `animating` rejects only `pointerdown`; move/up remain ungated. Animation handles are not retained; completion only handles fulfillment. | This neither truly locks interaction nor supports re-grabbing. Repeated releases can create overlapping animations; future cancellation needs rejection-safe cleanup. | Move 3 → repeated mid-settle grabs/reversals begin at the visible position with no stale completion changing newer state. |
| **F4 — Release discards interaction physics** | Target uses nearest `offsetTop`; settle is fixed `480ms ease-in`; no velocity history, handoff, or boundary resistance is shown. | Slow-start easing risks a pause then acceleration unrelated to release momentum. Nearest-position targeting is not itself wrong; momentum targeting is not established by the brief. | Moves 4–6 → controlled slow/fast releases verify velocity continuity, authorized target rules, and bounded edge behavior. |
| **F5 — Reduced Motion is absent here** | Neither supplied CSS nor JS contains a Reduced Motion branch. | The shown implementation cannot establish the required no-large-travel alternative. App-level handling elsewhere is unknown. | Moves 7–8 → Reduced Motion and keyboard tests retain clear state feedback, task context, and reachable controls without animated large travel. |

## 4. Concrete design moves

These are proposed mechanics and tuning starting points, not validated settings.

1. **Immediate pointer-down feedback — F1/F2.**  
   Give the dedicated drag handle an immediate contrast/active-state change and appropriate cursor; remove whole-sheet scaling. Preserve content clicks and scrolling. If any decorative transform remains, isolate it from the translation owner.

2. **Owned, 1:1 tracking — F1/F2.**  
   Track one primary pointer ID. Use a consistent CSS-pixel coordinate space and `y = grabbedPresentationY + (clientY − downClientY)`, preserving the grab offset. After a small intent threshold—start testing around 8–12 CSS px—track without easing or ongoing dead zone. Capture the pointer, ignore additional pointers, and handle `pointercancel`/lost capture. Define handle-specific `touch-action` without disabling sheet-content scrolling. Drive `translateY` on the display clock; avoid layout reads in the move loop.

3. **Presentation-value interruption and single ownership — F2/F3.**  
   Replace the boolean gate with explicit idle/dragging/settling ownership. On re-grab, sample current displayed position and animation velocity **before** cancelling; transfer the position into the drag model without a discontinuity. Once grabbed, the pointer owns motion—do not add residual drift. On non-drag retargets, carry current velocity forward. Commit final position/state, remove obsolete effects, and make cancellation/stale callbacks ownership-safe.

4. **Measured velocity handoff — F4.**  
   Estimate release velocity from a short recent history using monotonic timestamps, in **CSS px/s**; filter noisy samples and bound outliers. Feed that velocity and current presentation position into the settle, converting to the animation API’s units. Prefer a critically damped spring, initially testing roughly 0.25–0.35s response, without decorative bounce. This is a response scale, not a mandatory fixed duration.

5. **Explicit, conditional projected endpoints — F4.**  
   Preserve nearest-current-position targeting unless product owners authorize momentum-based selection. For an experiment, define downward-positive `v`, `vBound = clamp(v, −2000, 2000)` CSS px/s, then `projectedY = clamp(y + vBound × 0.15s, fullY, collapsedY)`. These bounds/horizon are provisional. **Only if authorized**, choose the nearest valid snap to `projectedY`; otherwise use the existing target rule. Projection selects a destination; it does not replace velocity handoff.

6. **Soft boundaries — F4.**  
   Keep interior tracking 1:1. Beyond either endpoint, progressively compress signed overshoot `o`, for example `r = o × D × 0.55 / (D + 0.55 × |o|)`, where `D` is a positive sheet/viewport dimension in CSS px. Render boundary plus `r`, then settle to a valid endpoint. Tune to small, non-playful resistance; avoid excessive stretch or hiding essential controls.

7. **Reduced Motion without lost feedback — F5.**  
   Check `prefers-reduced-motion` in both styling and the JS animation controller, including preference changes. Keep user-controlled tracking causal, but remove elastic excursion, momentum coasting, and animated snap travel: commit the chosen state immediately, optionally with a brief non-spatial handle/status change. If enabled mid-settle, resolve immediately rather than completing the journey.

8. **State and context independent of motion — F5.**  
   Provide keyboard-operable controls for collapsed/half/full, a visible state indication, and appropriate accessible naming/state feedback—not per-frame announcements. Preserve task data, content scroll position, and focus where still visible; if collapsing hides the focused control, move focus deliberately to the sheet control.

## 5. Verified versus unverified

**Verified from the supplied text:** handler structure, property choices, `300ms` transition, `480ms ease-in`, scale value, retained fill, and absence of the listed safeguards **in these snippets**.

**Unverified:** actual jumps or perceived delay, computed positioning/cascade, snap geometry, frame rate, layout/compositing cost, velocity continuity, content-scroll conflicts, responsive behavior, accessible semantics elsewhere, and real-device feel.

No pointer trace, computed-style inspection, performance recording, Reduced Motion run, responsive run, or device test was performed. No runtime validation is claimed.

## 6. Minimal validation before approval

Run these checks on the revised candidate, retaining a baseline where practical:

- **Browser interaction trace — F1–F4:** slow drags, fast flicks both ways, reversals, off-center grabs, snap-midpoint releases, both boundaries, outside-sheet release, cancellation, extra pointers, and repeated re-grabs during settling. Log pointer ID, pointer/sheet positions, velocity, target, and ownership.
- **Computed styles and performance — F2/F3:** confirm no drag transition, no obsolete filled animations, and no competing transform owners. Record representative operations-app load. Provisional gates to ratify: p95 input-to-presentation ≤2 refresh intervals and no interaction-attributable main-thread task >50ms; failure keeps approval blocked.
- **Responsive and hardware:** check desktop and narrow web layouts, resize/orientation changes, and reachable snap states. Test a representative real touch device for handle/content-scroll arbitration; cover 60Hz and 120Hz where supported targets warrant it.
- **Accessibility and context — F5:** Reduced Motion on before interaction and toggled mid-settle; keyboard-only state changes; focus/state announcements; preservation of task data and scroll context. Confirm no large animated travel in the reduced path.
- **Approval record:** capture traces/video plus browser, device, viewport, and refresh rate where known. Resolve F1–F5 against those checks; screenshots alone cannot establish gesture quality.
