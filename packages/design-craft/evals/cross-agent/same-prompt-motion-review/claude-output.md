I'm in critique mode, read-only. I read `design-craft/SKILL.md`, `references/interaction-physics.md` and `references/validation-contract.md`. I edited no files and ran nothing in a browser or on a device.

## 1. Evidence level and design read

**Evidence: L1 contextual, static only.** I had the prompt's product context and two code snippets. I had no runtime, computed styles, traces or device runs, so every claim about feel, lag or frame rate below is a hypothesis.

Reading this as: a bottom sheet in a web operations app, used many times a day, in a calm utility style, built so people can move between collapsed, half and full without losing what they were doing.

**One-line verdict:** the gesture isn't direct manipulation yet. The handler doesn't track whether the pointer is pressed, the CSS delays the drag, the settle locks out input, and the release curve throws away the flick's speed. Don't approve the motion design as written.

## 2. Should this motion exist?

**Yes, but only two kinds:**
- **Drag tracking.** This is the user moving the sheet directly. It's zero-duration and follows the finger 1:1.
- **One short settle to a snap point.** This shows cause and effect: the sheet goes where the gesture sent it.

**These parts should not animate:**
- `transition: all 300ms` on `.sheet`. Remove it. It animates the drag itself, plus colours and layout.
- `:active { transform: scale(0.96) }` on the whole sheet. Shrinking a full-width work surface moves the content out from under the finger and isn't calm.
- `top`. Move the sheet with a single `transform: translateY` owner, not a layout property.
- Content inside the sheet when the state changes. Don't animate reflow, remount content or reset scroll.
- Bounce or overshoot. Nothing in this style asks for it, so use critical damping.

## 3. Blocking findings (priority order)

**B1 — The drag state machine is broken (P0).**
- Source: `pointermove` writes `top` without checking that a pointer is down, so on desktop the sheet follows a hovering mouse.
- `top = clientY` snaps the sheet's top edge to the finger. That drops the grab offset, and `startY` is stored but never used.
- There is no `setPointerCapture`, no `pointercancel` handler and no `touch-action`. A browser scroll can steal the gesture, or the `pointerup` can be lost outside the sheet.
- Every `pointerup`, including a simple tap on a task row, starts a 480 ms settle.
- Effect: the user loses control and the context they were working in. That is the main job this sheet exists for.

**B2 — Tracking isn't 1:1 (P0/P1).**
- Source: `transition: all 300ms` also applies to the `top` writes made during the drag, so the sheet should trail the finger by up to 300 ms on every move.
- `:active` scale and its transition change geometry while the finger is down.
- Animating `top` forces layout on every pointer event.
- Unknown until runtime: how much lag a user actually sees, and the frame cost.

**B3 — The settle can't be interrupted, and the sheet may get stuck after one gesture (P0 hypothesis).**
- Source: the `animating` flag blocks `pointerdown` during the 480 ms settle, so the user can't catch the sheet.
- `fill: "forwards"` is never cancelled. By cascade rules, animation values override inline styles. So after the first settle, later `style.top` writes are likely hidden, and `offsetTop` reads back the old target.
- Likely result: the sheet looks frozen after the first release.
- Unknown until runtime: confirm this in a real browser before treating it as fact.
- Separately, `offsetTop` and `clientY` may be in different coordinate spaces, depending on positioning and the offset parent.

**B4 — Release physics are backwards (P1).**
- Source: `ease-in` starts at zero speed and speeds up into the snap point, so a flick visibly stalls and then hits the stop hard.
- 480 ms is long for something used all day.
- Release velocity is never measured, and the target is picked from position alone.

**B5 — No boundaries, no Reduced Motion and no keyboard path (P1).**
- Source: `top` is never clamped, so the sheet can be dragged off-screen or above the viewport.
- There is no `prefers-reduced-motion` branch.
- The handle has no semantic control. Keyboard and assistive-technology users can't change the state.

## 4. Concrete design moves (one per item asked for, plus two)

**M1 — Pointer-down feedback (fixes B1, B2).**
- On `pointerdown` on the handle: call `setPointerCapture`, set `cursor: grabbing` and change the grip's colour or opacity in the same frame.
- Leave the sheet's scale and position alone.
- Only the grip colour gets a transition (about 100 ms).

**M2 — 1:1 tracking (fixes B1, B2).**
- Use explicit states: `idle → pressed → dragging → settling`.
- Commit to dragging after 8–10 CSS px of vertical movement, so taps stay taps.
- Store `grabOffset = clientY − presentationY` and write `translateY(clientY − grabOffset)` once per animation frame.
- Set `touch-action: none` on the handle.
- From the content area, start a drag only when `scrollTop === 0` and the user is pulling down. Otherwise the content scrolls.
- On `pointercancel`, settle to the nearest snap point.

**M3 — Interrupt from the on-screen position (fixes B3).**
- Remove the `animating` lock.
- On `pointerdown` during a settle: read the sheet's current on-screen position from your own spring state (or from the computed transform), stop the animation, commit that value, and keep dragging from there with no visual jump.
- Use a spring loop you own, which keeps position and velocity, instead of `element.animate` with `fill: forwards`.

**M4 — Velocity handoff (fixes B4).**
- Keep a buffer of pointer samples from the last ~100 ms (`event.timeStamp`, CSS px).
- On release, compute velocity in CSS px/s and clamp it to a provisional ±4000 px/s, which the project should confirm.
- Feed that velocity into the settle spring: damping 1.0 (no overshoot, per the calm style), response about 0.3 s.

**M5 — Projected endpoints (needs a product decision).**
- The current rule is "nearest snap point to where the sheet is". Don't change it silently.
- Mechanical candidate: `projected = currentY + (v/1000)·d/(1−d)` with `d = 0.99`, which is about 0.099·v px (≈200 px at 2000 px/s). Clamp it between the full and collapsed positions, then pick the nearest snap point.
- Propose this to the product owner as an experiment. A flick from half to full is plausibly what users mean, but that's unconfirmed. M4's velocity handoff applies either way.

**M6 — Soft boundaries (fixes B5).**
- Past the full position or below collapsed, apply resistance: `(o·D·c)/(D + c·|o|)`, with `c ≈ 0.55` and `D` = viewport height.
- On release past a boundary, spring back with damping 1.0.

**M7 — Reduced Motion and keyboard (fixes B5).**
- Drag stays 1:1, because the user is driving the movement.
- The settle becomes an instant position change plus a ≤150 ms change in the handle's state indicator and a light cross-fade.
- No rubber-band stretch past the ends: clamp hard.
- Make the handle a `button` with `aria-expanded`, or a `slider` with `aria-valuetext="Half"`. Arrow keys and Enter step between states, and the state change is announced politely.

**M8 — Keep task context (fixes B1, B2).**
- Use compositor-only `transform`.
- Keep the content mounted, its scroll position and the focused element across all three states.
- Don't reflow content while dragging; resize it once after the settle if needed.

## 5. Verified vs. unverified

**Supported by the source alone:**
- `pointermove` has no pressed check.
- The grab offset is dropped and `startY` is unused.
- There is no pointer capture, no `pointercancel` and no `touch-action`.
- The `animating` lock blocks `pointerdown`.
- The settle uses `ease-in` for 480 ms with `fill: forwards`.
- `.sheet` has `transition: all` and an `:active` scale.
- `top` is the animated property, and positions are never clamped.
- There's no Reduced Motion branch and no keyboard path.

**Unverified (hypotheses that need a runtime check):**
- The sheet gets stuck after the first settle because of the forwards fill.
- How much lag users perceive from the 300 ms transition.
- The jump when the grab offset is lost, as it looks in practice.
- Pointer events being stolen by scroll on touch devices.
- Mismatched coordinate spaces between `offsetTop` and `clientY`.
- Frame rate, compositing and smoothness at 60 Hz or 120 Hz.
- Whether the projection constant feels right for this task.

I'm making no claim about browser, device, Reduced Motion or responsive behaviour.

## 6. Minimal validation before approval

1. **Desktop Chrome and Safari, current code.**
   - Hover without pressing and check whether the sheet follows (B1).
   - Drag, release, then drag again and check whether it moves (B3).
   - Record a Performance trace of one drag and look for layout on each move and how far the sheet trails the pointer (B2).
2. **A real touch device (iOS Safari and Android Chrome).**
   - Drag from the handle and from scrolled content, and check for `pointercancel` or scroll stealing.
   - Do a slow drag and a fast flick, with screen recordings at 60 Hz and 120 Hz where available.
3. **After the M1–M8 fixes, using the same setup:**
   - Grab the sheet mid-settle and confirm there's no jump. Use a frame-by-frame recording.
   - Log release velocity in px/s against the chosen target, for both slow drags and flicks.
   - Drag past full and past collapsed and confirm the resistance and the spring back.
   - Turn on Reduced Motion at the OS level and confirm there's no large travel and the state change is still visible.
   - Keyboard-only: Tab to the handle, step through all three states and check the screen-reader announcement.
   - Narrow mobile viewport and desktop: confirm the snap points line up with the content and the task row stays in place across states.
4. **Approval gate:** M5 (projected endpoints) needs a product decision. Record each artifact's path and hash. Report any run that's missing as unverified, not as passed.
