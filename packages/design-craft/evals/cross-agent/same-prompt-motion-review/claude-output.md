**Mode:** `critique`, read-only. **Skill refs read:** `design-craft/SKILL.md` and `references/interaction-physics.md`. No files were edited. The route planner was not run because this is a critique of supplied code, not an L1+ build.

## 1. Evidence level and design read

**Evidence:** static only. I had the prompt and two snippets: no runtime, no trace, no computed style, no device. Static code can show how the logic is built and which branches exist. It can't show how the drag feels, how smooth it is, or how it behaves on a device. Every "feel" claim below is an unverified inference.

**Reading this as:** a draggable bottom sheet for operations staff who use it many times a day, with calm utility-grade motion, optimized for moving between `collapsed` / `half` / `full` without losing context.

## 2. Should this motion exist?

Yes, but only two parts of it:
- **Drag tracking.** This isn't really animation; it's the sheet following the finger.
- **A short settle to a snap point.** This shows the user what their release caused.

These parts should **not** animate:
- **Sheet position while dragging.** `transition: all 300ms` currently delays it.
- **Whole-sheet `scale(0.96)` on `:active`.** A large surface shrinking moves the task content around, which works against keeping context.
- **`all` properties.** Only the handle's color/opacity should transition.
- **Content inside the sheet.** No fades or staggers on state change.
- **Under Reduced Motion, the large release travel.**

## 3. Prioritized findings (ID · priority · source proof · runtime unknown)

**F1 · P0 · Input is locked, and the settle may leave the sheet stuck.**
- **Source:** `pointerdown` returns early while `animating` is true, so the sheet can't be grabbed during its 480 ms settle. This breaks the rule that gestures must be interruptible.
- **Source:** `fill: "forwards"` keeps the animation's `top` value applied after it ends. In the cascade, animation effects override inline `style.top`, so later drags probably never show.
- **Unknown:** whether the sheet visibly freezes after the first release in Chromium, Safari and Firefox.

**F2 · P0 · Tracking is not 1:1, and it's not tied to a press.**
- **Source:** `pointermove` has no pressed or captured check, so with a mouse the sheet follows plain hovering.
- **Source:** `startY` is stored but never used, so there's no grab offset and the sheet's top edge jumps to the cursor.
- **Source:** `clientY` is a viewport coordinate written into `top`, which is relative to the containing block.
- **Source:** there's no `setPointerCapture`, no 8–12 px intent threshold (so taps become drags), and no `touch-action` handling, so the browser may take over the touch for scrolling.
- **Unknown:** how big the jump is, how much scroll is stolen, and whether moving outside the sheet drops the drag.

**F3 · P0 · The release ignores how the user threw the sheet.**
- **Source:** `ease-in` over a fixed 480 ms. Motion starts at zero velocity no matter how fast the finger was moving, then speeds up into the stop. That's the reverse of a physical settle.
- **Source:** no velocity samples are recorded, and the target is the nearest snap to the current position only, so a quick flick falls back to where it started.
- **Unknown:** how the release feels and whether flick intent is lost in practice.

**F4 · P1 · The CSS fights the JS and moves layout instead of transforms.**
- **Source:** `transition: all 300ms` applies to every `style.top` write, which adds roughly 300 ms of lag behind the finger.
- **Source:** the `scale` transform and press feedback have no separate layer or composition owner.
- **Source:** animating `top` triggers layout on every frame, unlike `transform`.
- **Source:** `:active` isn't reliable on touch.
- **Unknown:** dropped frames and long tasks. These have not been measured.

**F5 · P1 · No boundaries, no Reduced Motion path, and drag is the only way to change state.**
- **Source:** there's no clamp, so the sheet can be dragged past `full` or off-screen, and there's no resistance at the edges.
- **Source:** there's no `prefers-reduced-motion` branch, so there's always a 480 ms travel.
- **Source:** there's no keyboard or semantic way to change state.
- **Unknown:** what happens at extreme viewport heights, and how a screen reader announces state.

## 4. Concrete design moves (repairs for F1–F5)

**M1 · Pointer-down feedback (F4)**
- On `pointerdown`, change the handle's color or opacity immediately (0 ms in, about 100 ms out).
- Don't scale the sheet.
- If scale is ever wanted, put it on a separate wrapper layer so it doesn't overwrite the drag `translateY`.

**M2 · 1:1 tracking (F2, F4)**
- Start only on a primary pointer and button, then call `setPointerCapture`.
- Set `grabOffset = clientY − presentationY`, with both values in the container's CSS px.
- Commit to a drag after 10 px of vertical movement. Below that, it stays a tap.
- Write `transform: translateY(y)` once per `requestAnimationFrame`.
- Set `touch-action: none` on the handle. Hand off to the scroll area inside the sheet only when that area is scrolled to the top.
- Stop tracking on `pointerup` or `pointercancel`.

**M3 · Presentation-value interruption (F1)**
- Remove the `animating` lock.
- On `pointerdown` during a settle, read the current on-screen value (the spring's state or the computed transform) and cancel the settle.
- Keep tracking from that exact value so there's no jump. Drop `fill: forwards`; the final position belongs in the sheet's state.

**M4 · Velocity handoff (F3)**
- Keep a pointer history of about the last 100 ms with `performance.now()` timestamps, and compute release velocity in CSS px/s.
- Settle with a spring instead of `ease-in`:
  - Start critically damped, with no bounce for a calm utility UI (damping 1.0, response about 0.3–0.4 s).
  - Allow damping 0.8 only if a strong flick should overshoot slightly.
- Feed the measured velocity into the spring, converted to whatever units the spring API expects (relative velocity = v / (target − current)).

**M5 · Projected endpoint (F3), a hypothesis until approved**
- Calculation: `projectedEndpoint = current + (v/1000)·d/(1−d)`, with d = 0.99 for a snappier result.
- Clamp the result to the [`full`, `collapsed`] range, and allow at most one state skip per release.
- Choosing the target from this projection changes the current "nearest to position" rule. The product owner has to approve that.
- Until then, keep `nearestSnapPoint(current)` and still do the velocity handoff from M4. Test projection as a separate runtime experiment.

**M6 · Soft boundaries (F5)**
- Past `full` or `collapsed`, apply resistance: `(o·D·c)/(D + c·|o|)` with c ≈ 0.55 and D = viewport height. Release springs back with no overshoot.
- The sheet can't end up outside its valid range.

**M7 · Reduced Motion (F5)**
- The drag still follows the finger 1:1, because the user is moving it, not the app.
- On release, commit to the snap point with no travel: a cross-fade of about 120–150 ms, a handle state change, and no overshoot or rubber-band bounce.
- State feedback stays through an updated label ("Half", "Full") via `aria-live="polite"`.

**M8 · Scoped CSS and a non-drag path (F4, F5)**
- Replace `transition: all` with color/opacity transitions on the handle only.
- Make the handle a `button` with `aria-label` and `aria-expanded`.
- Arrow keys or Enter step through the states using the same settle as M4, or the M7 path under Reduced Motion.
- Keep the hit target at 44 CSS px or more.

## 5. Verified vs unverified

**Verified from source (code shape only):**
- The input lock.
- `fill: "forwards"`.
- The unused `startY`.
- `pointermove` with no pressed or captured check.
- No pointer capture, no threshold, no velocity samples.
- `ease-in` over a fixed 480 ms.
- `transition: all` combined with inline `top` writes.
- `:active` scale.
- No clamp and no Reduced Motion branch.

**Inferred but not verified:**
- The sheet freezes visibly after the first settle.
- The tracking lag is about 300 ms.
- The size of the grab jump.
- The browser steals touches for scrolling.
- Frame drops from animating `top`.
- Flicks get lost.
- Whether a critically damped spring actually feels calm.

**Not claimed:** any browser, device, Reduced Motion, responsive or performance validation. None was run.

## 6. Minimal validation plan before approving the implementation

1. **Browsers and devices:**
   - Desktop Chromium and Safari with a mouse.
   - iOS Safari and Android Chrome with touch.
   - At least one 120 Hz device and one 60 Hz device. Record the refresh rate.
2. **Pointer trace:** log `pointerType`, `clientY`, the timestamp and the on-screen Y each frame.
   - Pass: on-screen Y minus (pointer Y − grab offset) stays within 1 px while dragging, and nothing moves on hover alone.
3. **Interruption:** grab the sheet mid-settle 10 times.
   - Pass: no jump over 1 px and no ignored grab.
   - Repeat drag → release → drag to rule out the F1 freeze.
4. **Release:** do slow releases and flicks (over 1000 px/s) from each state.
   - Record the measured velocity, the chosen target, and whether settle velocity is continuous at release.
   - Check M5 only behind a flag.
5. **Boundaries:** drag 200 px past `full` and past `collapsed`.
   - Pass: increasing resistance, then a spring back with no overshoot.
6. **Performance:** record a DevTools trace of a 5 s drag.
   - Provisional gates, to be confirmed: no layout work in the drag frames, no long task over 50 ms, at most 1 dropped frame per second at 60 Hz.
7. **Reduced Motion:** emulate it and also test with the OS setting on.
   - Pass: the drag is still 1:1, the release has no spatial travel, and the state label updates.
8. **Responsive and keyboard:**
   - Viewport heights 568, 800 and 1080 px, plus a scroll area inside the sheet.
   - Keyboard stepping through states, focus visibility, and a screen-reader announcement.
9. **Artifacts:** a screen recording and a trace file per run, with paths and hashes attached to the approval.
