**Evidence level and design read**

- **Evidence:** static only. I used the prompt, the code above, and two files from the design-craft skill: `SKILL.md` and `references/interaction-physics.md`. Nothing ran in a browser or on a device.
- **Design read:** a bottom sheet in a web operations app. People drag it between `collapsed`, `half` and `full` many times a day. It should feel calm, follow the finger exactly, and keep the task content steady while it moves.
- **Mode:** `critique` (read-only). Platform is `web`. The route planner was not run.

**Should this motion exist?**

Yes, but only two motions are justified:
- **The drag itself:** the sheet follows the pointer 1:1. This is the user moving it, not an animation.
- **One short settle on release:** this shows the sheet landing on its new state, so cause and effect stay clear.

These parts should not animate:
- The press scale (`:active scale(0.96)`).
- `transition: all` on the sheet. It catches every property, including `top` during the drag.
- Anything inside the sheet, such as content scaling or fading.
- Bounce or overshoot in the settle.
- Any lock on input while the sheet settles.

**Findings (blocking, in priority order)**

| ID | Pri | Source proof | Runtime unknown |
|---|---|---|---|
| F1 | P0 | `pointermove` has no check for an active drag, so with a mouse the sheet follows plain hover. `startY` is stored but never used, so `top = clientY` throws away where the user grabbed and jumps the sheet's edge to the pointer. There is no `setPointerCapture`, no movement threshold, no `touch-action` and no `pointercancel` handler, so taps and scrolls inside the content get read as drags. | How badly touch scrolling and the drag fight each other on iOS and Android |
| F2 | P0 | `animating` ignores `pointerdown` for 480 ms, so the user can't catch the sheet mid-settle. Also, `fill: "forwards"` never calls `cancel()`. A filled animation overrides inline styles, so after the first release, later `style.top` writes probably have no visible effect and the sheet looks frozen. | Whether the sheet actually freezes, and what `offsetTop` reports while the fill is active |
| F3 | P1 | The release ignores the finger's speed. It uses a fixed 480 ms `ease-in` that starts slow, which is the opposite of picking up a moving finger, and the same duration applies to every distance. `nearestSnapPoint(offsetTop)` uses position only. | How it feels on a flick versus a slow drag |
| F4 | P1 | `transition: all 300ms` also applies to the inline `top` written on every move, so the sheet trails about 300 ms behind the pointer instead of tracking it. `:active scale(0.96)` shrinks the whole sheet and its task content. That is large spatial distortion with no causal purpose, and it would also overwrite any future `transform: translateY`. | Actual lag, and whether `:active` fires reliably on touch |
| F5 | P1 | Animating `top` forces a layout recalculation on every frame. There are no limits at the top or bottom, so the sheet can be dragged off-screen. There is no `prefers-reduced-motion` branch, and the 480 ms of travel is the large spatial motion Reduced Motion is meant to remove. | Dropped frames at 60 Hz and 120 Hz, and how much layout work each frame costs |

**Concrete design moves**

- **M1 Pointer-down feedback (fixes F4):** on `pointerdown`, set `data-pressed` on the grab handle. Feedback is a tint or slightly stronger elevation on the handle, applied instantly or within about 100 ms of opacity or color change. Remove the sheet scale and `transition: all`. Transition only the specific properties you need, and never the position.
- **M2 1:1 tracking (fixes F1):**
  - On `pointerdown`: call `setPointerCapture` and store `grabOffset = clientY - currentY`.
  - Commit to a drag only after 8–10 px of vertical movement, so taps stay taps.
  - While dragging: `y = clientY - grabOffset`. Write it as `transform: translateY()` once per `requestAnimationFrame` and read no layout during the move.
  - Put `touch-action: none` on the handle. Let the content area start a sheet drag only when its scroll position is at the top.
  - Handle `pointercancel` and `lostpointercapture` by settling to the nearest snap point.
- **M3 Interruption from the on-screen value (fixes F2):**
  - Delete the `animating` flag.
  - On `pointerdown` during a settle: stop the spring and read the value currently shown on screen (the spring's own `y`, or the computed transform). Recompute `grabOffset` from that value and keep dragging without a jump.
  - Never use `fill: "forwards"` for a value you then keep through a fill. Store the final `y` as the sheet's real state.
- **M4 Measured velocity (fixes F3):** keep the last ~100 ms of `(event.timeStamp, y)` samples, in CSS pixels. On release, compute velocity in CSS px/s from the oldest and newest samples in that window. Optionally add `getCoalescedEvents()` samples.
- **M5 Velocity handoff (fixes F3):** settle with a spring set to damping 1.0 (no bounce, matching the calm style) and a response of about 0.3–0.4 s. Its starting velocity is the measured release velocity. WAAPI keyframes can't take a starting velocity, so drive the spring yourself on `requestAnimationFrame` writing `transform`, or use a spring primitive that supports it. Duration then follows from distance and speed instead of being fixed.
- **M6 Projected endpoint (conditional):** the default stays `nearestSnapPoint(current)`, because the product hasn't said that a flick should choose the state. As a separately approved experiment:
  - `projectedEndpoint = current + (v/1000)·d/(1−d)`, with `d ≈ 0.99` for a snappy feel.
  - Clamp the result to the `[full, collapsed]` range.
  - Snap to the point nearest that endpoint.
  - Never skip from `full` straight to `collapsed` on one flick unless the product approves it.
- **M7 Soft boundaries (fixes F5):** past the `full` and `collapsed` limits, apply resistance: `(o·H·0.55)/(H + 0.55·|o|)`, where `o` is the overshoot and `H` is the viewport height. Release from there with the same damping-1.0 spring, which returns the sheet without bounce. Add hysteresis so the sheet doesn't flicker between two states near the halfway point.
- **M8 Reduced Motion (fixes F5):** keep the drag 1:1, because the user is driving it. On release, place the sheet at the target immediately, or within about 120 ms with no overshoot. Confirm the new state without travel: the handle tint changes, and an `aria-live` region announces "Sheet: half". Keyboard and button controls for changing state should use the same no-travel path.

**Verified vs. unverified**

- **Verified from the source code:**
  - No drag-active check in `pointermove`.
  - `startY` is never used.
  - No pointer capture, threshold, `touch-action` or `pointercancel` handling.
  - The `animating` lock is there.
  - `fill: "forwards"` is never cancelled.
  - Fixed 480 ms `ease-in` on `top`.
  - `transition: all` together with `:active scale`.
  - No Reduced Motion branch.
  - No limits on the drag.
- **Inferred from the WAAPI and CSS specs, not observed:**
  - The frozen sheet after the first settle (F2).
  - The roughly 300 ms trailing during drag (F4).
  - A layout recalculation every frame from animating `top` (F5).
- **Unverified (no runtime):** how the drag feels, smoothness, behavior at 60 Hz and 120 Hz, touch-scroll conflicts, and how stable the content stays during the drag. The M5–M7 spring and projection constants are starting points and still need tuning.

**Validation plan before approving implementation**

1. **Devices:** desktop Chrome and Safari with mouse and trackpad, a real iOS Safari device at 120 Hz, and a mid-range Android Chrome device at 60 Hz.
2. **Hover:** moving the mouse without pressing never moves the sheet (F1).
3. **Grab offset:** grab the handle 40 px below its top edge. The offset stays constant through the drag, checked against a logged pointer trace.
4. **Interruption:** grab the sheet mid-settle. Frame-by-frame video shows no jump (under 1 px) and the drag continues immediately (F2). Repeating 10 drags in a row never freezes the sheet.
5. **Velocity:** log release velocity in px/s. Over 20 trials each of a slow drag and a flick, the settle's starting speed matches the release speed and nothing reverses direction (F3, M5).
6. **Targets:** record which state each release lands in under the current rule. Run the projection rule (M6) only as an A/B experiment the product approves.
7. **Limits:** dragging past `full` or `collapsed` gives resistance, and release returns the sheet without overshoot (M7).
8. **Performance:** a Chrome Performance trace during a 2 s drag shows no layout or style recalculation on each frame and no long tasks over 50 ms. These are provisional gates to be agreed, not measured.
9. **Reduced Motion:** with Reduced Motion turned on (in DevTools and on the OS), the drag is still 1:1, the sheet doesn't travel on release, and the state change is still visible and announced (M8).
10. **Content stability:** content inside the sheet keeps its scroll position and focus through every state change.

Approval needs saved trace and video artifacts with file paths. Until those exist, the interaction stays unverified.
