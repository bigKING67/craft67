## 1. Evidence level and design read

**Evidence level:** Static-source critique only. I can verify explicit code paths and declared CSS, but not perceived smoothness, frame rate, browser behavior, touch feel, computed styles, pointer traces, or Reduced Motion behavior.

**Design read:** Reading this as a high-frequency web operations bottom sheet for task workers, with calm utility motion, optimized for preserving context while dragging between `collapsed`, `half`, and `full`.

**Verdict:** **Block for approval.** The current motion undermines direct manipulation: it delays tracking, locks input, animates layout properties, lacks interruption, and has no Reduced Motion path.

---

## 2. Should this motion exist?

**Yes, but only as causal motion:**

- **Should exist**
  - Immediate pointer-down feedback on the drag handle/sheet affordance.
  - 1:1 sheet tracking while dragging.
  - A short settle to the chosen snap point after release.
  - State feedback when the sheet reaches `collapsed`, `half`, or `full`.

- **Should not animate**
  - Every pointer-move via `transition: all`.
  - Layout `top` changes as the main animation path.
  - Whole-sheet `scale(0.96)` while active.
  - Input lockout during the settle animation.
  - Large spatial travel under Reduced Motion.

---

## 3. Prioritized blocking findings

1. **Pointer movement is not 1:1.**  
   `transition: all 300ms` means `sheet.style.top = ...` may animate during drag instead of staying attached to the pointer. Direct manipulation should feel physically attached, not trailing behind.

2. **The sheet snaps its top edge to the pointer.**  
   `sheet.style.top = event.clientY` ignores grab offset and `startY` is unused. If the user grabs the handle 40px below the sheet top, the sheet top jumps to the finger. That breaks causality.

3. **Input is locked during animation.**  
   `if (animating) return` blocks pointer-down while the sheet is settling. A draggable sheet must be interruptible from the current on-screen presentation value, not wait 480ms.

4. **Settle animation has wrong physical shape.**  
   `duration: 480` with `ease-in` starts slowly when the user expects immediate response after release. For UI response, this feels delayed and heavy. A sheet settle should usually be spring-like or strong ease-out, with velocity handoff.

5. **Layout animation and broad CSS create performance and ownership risk.**  
   Animating `top`, reading `offsetTop`, using `fill: "forwards"`, and declaring `transition: all` create likely layout work and competing animation ownership. Static code cannot prove jank, but this is the wrong mechanism for a hot gesture path.

---

## 4. Concrete design moves

1. **Pointer-down feedback**  
   Give immediate, subtle feedback on the handle or sheet chrome: handle darkens, elevation increases slightly, cursor changes, or a `1–2px` lift. Avoid scaling the entire sheet.

2. **1:1 tracking**  
   After an `8–12px` intent threshold, capture the pointer and update a single transform value:  
   `translateY(currentY)` in CSS pixels. Do not use `transition` during active drag.

3. **Preserve grab offset**  
   On pointer-down, record:  
   `grabOffset = pointerClientY - sheetPresentationY`.  
   During drag:  
   `nextY = pointerClientY - grabOffset`.

4. **Presentation-value interruption**  
   If the sheet is settling and the user grabs it, cancel the running animation and start from the current visual position, not the last logical snap point. No `animating` input lockout.

5. **Velocity handoff**  
   Track recent pointer samples with monotonic timestamps and compute release velocity in **CSS px/s**. The settle animation should inherit that velocity instead of restarting from zero.

6. **Projected endpoints**  
   Keep current nearest-snap semantics unless product behavior authorizes momentum targeting. As a candidate: compute a bounded projected endpoint from current presentation `Y + projectedDistance`, clamp to sheet bounds, then choose the nearest valid snap point only if momentum-based targeting is approved.

7. **Soft boundaries**  
   At `full` and `collapsed` limits, use progressive resistance instead of hard stops. A rubber-band curve can show the limit without letting the sheet detach from the finger.

8. **Reduced Motion**  
   Preserve direct drag feedback, but remove inertia, overshoot, long settle travel, and elastic effects. On release, snap quickly or nearly instantly to the state, with small non-spatial feedback such as handle color, shadow, label/state change, or short opacity transition.

---

## 5. Verified vs unverified claims

**Verified from static code**

- Pointer-down is ignored while `animating` is true.
- `startY` is recorded but not used in the shown code.
- Pointer-move writes `top` directly from `event.clientY`.
- Pointer-up animates `top` to `nearestSnapPoint(sheet.offsetTop)`.
- Settle duration is `480ms`.
- Settle easing is `ease-in`.
- WAAPI uses `fill: "forwards"`.
- CSS declares `transition: all 300ms`.
- Active state scales the sheet to `0.96`.
- No visible `prefers-reduced-motion` branch is present in the evidence.

**Unverified / runtime hypotheses**

- Actual jank, frame drops, or layout thrash severity.
- Whether `transition: all` conflicts with WAAPI in the computed cascade.
- Whether `fill: forwards` causes stale layout state in the real browser flow.
- Real touch feel on mobile hardware.
- Pointer capture behavior outside the sheet bounds.
- Responsiveness across viewport sizes.
- Reduced Motion behavior in an actual browser setting.
- Whether `nearestSnapPoint` encodes product-approved snap semantics.

---

## 6. Minimal validation plan before implementation approval

1. **Desktop browser pointer test**
   - Drag from handle and body.
   - Confirm no jump on grab.
   - Confirm 1:1 tracking.
   - Confirm drag continues outside original sheet bounds via pointer capture.

2. **Interruption test**
   - Release toward a snap point.
   - Re-grab mid-settle.
   - Confirm no lockout and no visual jump.

3. **Velocity and target test**
   - Slow drag near midpoint.
   - Fast flick toward each state.
   - Confirm target selection matches the approved product rule.

4. **Boundary test**
   - Pull beyond `full` and `collapsed`.
   - Confirm resistance, no hard visual break, and clean return.

5. **Reduced Motion run**
   - Enable `prefers-reduced-motion`.
   - Confirm state feedback remains clear without long travel, overshoot, or elastic motion.

6. **Performance check**
   - Inspect animation path for transform-only movement during drag and settle.
   - Check under a representative operations workload, not an empty page.

Rules/skill used: `design-craft`, frontend rule, motion-quality reference, interaction-physics reference.
