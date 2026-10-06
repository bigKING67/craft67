## Evidence-labeled verdict

**Verdict: Block for production gesture use.**  
**[Static evidence]** The snippet animates layout `top`, uses `transition: all`, locks input during settle, lacks Reduced Motion handling, and does not preserve direct-manipulation continuity. For a calm, repeated-use operations app, this will likely feel jumpy, delayed, and inaccessible unless reworked around interruptible transform-based motion.

---

## Prioritized findings

### P0 — Drag is not true direct manipulation
**[Static evidence]**
- `startY` is recorded but never used.
- `pointermove` sets `sheet.style.top = event.clientY`, so the sheet’s top edge jumps to the pointer instead of preserving the grab offset.
- `pointermove` is unguarded; it can run even when no active drag is established.

**Impact**
- The sheet can snap under the pointer, move accidentally, and fail the “object stays attached to my hand” expectation.

**Fix direction**
- Track `pointerId`, `isDragging`, `grabOffsetY = pointerY - currentSheetY`, and set position as `pointerY - grabOffsetY`.

---

### P0 — Input lockout breaks interruption
**[Static evidence]**
- `if (animating) return;` prevents grabbing the sheet while it is settling.
- The settle animation always starts from `sheet.offsetTop`, not necessarily the current presented visual value.

**Impact**
- Operators cannot reverse or correct a motion mid-flight. This is especially poor for collapsed/half/full sheets used repeatedly.

**Fix direction**
- Allow interruption: cancel/read the current presentation value, preserve current velocity, and retarget from the on-screen position without a jump.

---

### P0 — Layout animation is a performance hazard
**[Static evidence]**
- Drag and settle both mutate/animate `top`.
- `nearestSnapPoint(sheet.offsetTop)` reads layout after layout-affecting writes.
- `.sheet { transition: all 300ms; }` means pointer-driven `top` changes may be transitioned instead of tracking 1:1.

**Impact**
- High risk of layout/reflow on the gesture hot path and perceived lag, especially in a dense operations app with large tables behind or near the sheet.

**Fix direction**
- Use compositor-friendly `transform: translateY(...)` for drag and settle.
- Restrict transitions to explicit properties; avoid `transition: all`.

---

### P0 — Reduced Motion requirement is missing
**[Static evidence]**
- No `prefers-reduced-motion` branch.
- Settle uses large spatial travel with `duration: 480`.

**Impact**
- Fails the stated requirement: Reduced Motion must preserve state feedback without large spatial travel.

**Fix direction**
- In Reduced Motion, snap state immediately or with a very short non-spatial cue: handle color, shadow, border, opacity, label/state text, or a ≤80–120ms subdued transform with no overshoot.

---

### P1 — Settle motion feels backwards for user-triggered UI
**[Static evidence]**
- `duration: 480`
- `easing: "ease-in"`

**Impact**
- `ease-in` starts slowly, delaying feedback exactly when the user releases. `480ms` is heavy for a repeatedly used operations control.

**Fix direction**
- Use a responsive ease-out/spring-like settle. Default to no bounce or very low bounce. Target crisp completion, commonly around 200–350ms depending on distance and velocity.

---

### P1 — No release velocity or bounded projection
**[Static evidence]**
- Target is chosen only from `sheet.offsetTop`.
- No recent pointer history or release velocity is measured.

**Impact**
- A quick flick and a slow drag to the same release point behave identically. This may feel dead for a gesture sheet.

**Fix direction**
- Measure release velocity in CSS px/s from recent pointer samples.
- Keep target semantics explicit:
  - If the product wants nearest-position snapping, keep `nearestSnapPoint(currentY)`.
  - If momentum targeting is desired, compute a bounded projected endpoint and choose the nearest snap point to that endpoint.
- In both cases, feed measured release velocity into the settle animation.

---

### P1 — Snap bounds and overdrag behavior are absent
**[Static evidence]**
- `sheet.style.top = event.clientY` has no clamp.
- No collapsed/half/full boundary resistance.

**Impact**
- The sheet can be dragged into invalid positions or hit hard stops.

**Fix direction**
- Clamp to valid snap range, or apply soft rubber-band resistance outside bounds.
- Add hysteresis so tiny pointer noise does not switch states.

---

### P1 — Animation state can get stuck
**[Static evidence]**
- `.finished.then(...)` clears `animating`, but there is no `catch`/`finally`.
- If the animation is cancelled or rejects, `animating` can remain `true`.

**Impact**
- The sheet may become permanently non-interactive after an interrupted/cancelled animation.

**Fix direction**
- Use cancellation-safe cleanup with `finally`, or remove the global lock by making animation interruptible.

---

### P2 — Transform ownership conflict is likely
**[Static evidence]**
- CSS uses `.sheet:active { transform: scale(0.96); }`.
- A proper drag implementation should likely use `transform: translateY(...)`.

**Impact**
- Press scale and drag translate will overwrite each other unless composed deliberately.

**Fix direction**
- Use separate layers:
  - outer wrapper owns `translateY`
  - inner surface owns press scale / visual feedback

---

### P2 — Accessibility state model is not represented in the snippet
**[Static evidence]**
- Pointer handlers only.
- No visible keyboard controls, ARIA state, focus handling, or semantic state announcement in the shown code.

**Impact**
- Keyboard-heavy operators need non-pointer ways to move between collapsed, half, and full states.

**Fix direction**
- Provide keyboard commands/buttons for each snap state.
- Expose current state via accessible text/state.
- Preserve focus when the sheet expands/collapses.
- Keep focus-visible styling independent of motion.

---

## Concrete direct-manipulation moves

1. Replace `top` positioning with `transform: translateY(var(--sheet-y))`.
2. On `pointerdown`, capture pointer, store `pointerId`, current visual Y, and `grabOffsetY`.
3. Do not move until an intent threshold, roughly 8–12 CSS px, unless the handle is explicitly grabbed.
4. During drag, update only transform; batch writes with `requestAnimationFrame` if needed.
5. Keep recent `{time, y}` samples and compute release velocity in CSS px/s.
6. On release, choose target from explicit product semantics: nearest current snap point or authorized projected endpoint.
7. Settle from the current presentation value with initial release velocity; allow re-grab during settle.
8. Separate transform layers so sheet translation and press feedback do not overwrite each other.
9. Replace `transition: all` with scoped transitions, e.g. handle/background/shadow only.
10. Add Reduced Motion behavior: no large travel, no bounce, immediate state change plus short color/shadow/handle feedback.

---

## Verified / unverified boundaries

**Static-verified from the provided snippet**
- Layout property `top` is used for drag and settle.
- `transition: all` is present.
- `ease-in` and `480ms` are used for settle.
- Reduced Motion is not shown.
- Pointer capture, velocity tracking, bounds, hysteresis, keyboard handling, and ARIA state are not shown.
- Input is blocked while `animating` is true.

**Unverified**
- Actual frame rate, jank, smoothness, and device feel.
- Whether other files add keyboard support, ARIA semantics, focus management, or Reduced Motion.
- Whether `nearestSnapPoint` contains clamping or state semantics.
- Whether the sheet is isolated enough that layout animation is cheap in the real page.
- Browser-specific WAAPI/CSS transition interaction in the deployed environment.

---

## Smallest runtime validation plan

1. Test collapsed → half → full and back with slow drag, quick flick, and tiny accidental movement.
2. Re-grab during settle; verify no jump and no input lockout.
3. Drag beyond top/bottom bounds; verify clamp or soft resistance.
4. Enable Reduced Motion; verify state feedback remains clear without large travel.
5. Keyboard-only pass: move among all three states, confirm focus remains visible and predictable.
6. Performance pass under realistic page load: confirm pointermove does not trigger repeated layout and the sheet tracks the pointer at display rate.
7. Cancellation pass: interrupt/cancel animation repeatedly and verify the sheet never gets stuck.
