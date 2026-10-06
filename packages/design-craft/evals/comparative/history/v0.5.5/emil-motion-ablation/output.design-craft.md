## Verdict

**Block for production motion quality.** Static evidence shows a sheet that is visually movable, but not yet a reliable direct-manipulation control for a high-frequency operations app: it animates layout properties, locks input during settle, lacks velocity/interrupt handling, has transform ownership conflicts, and has no shown Reduced Motion path.

## Prioritized findings

**P0 — Drag is not true 1:1 direct manipulation.**  
- **Evidence:** `pointerdown` records `startY`, but `pointermove` ignores it and sets `sheet.style.top = event.clientY`.  
- **Impact:** The sheet can jump so its top edge follows the pointer instead of preserving the grab offset. This breaks physical continuity and makes repeated use feel imprecise.

**P0 — Interaction is non-interruptible.**  
- **Evidence:** `if (animating) return;` blocks new drags during settle; the WAAPI animation starts from `sheet.offsetTop`, not the current presentation value of an in-flight animation.  
- **Impact:** Users cannot grab and redirect the sheet mid-flight. A calm operations surface should feel responsive, not modal or locked.

**P0 — Layout-property motion is on the gesture hot path.**  
- **Evidence:** `sheet.style.top = ...`, keyframes animate `top`, and `nearestSnapPoint(sheet.offsetTop)` reads layout. CSS also has `transition: all 300ms`.  
- **Impact:** This risks layout/reflow work during every pointer move and during settle. Static code cannot prove jank, but the implementation chooses properties that are high-risk for a draggable panel.

**P1 — Release physics are missing.**  
- **Evidence:** `pointerup` chooses `nearestSnapPoint(sheet.offsetTop)` only; there is no recent pointer history, release velocity, projected endpoint, damping, or velocity handoff.  
- **Impact:** Slow drags and quick flicks resolve the same way if they end at the same position, which makes the sheet feel mechanical rather than physically responsive.

**P1 — Easing/duration are poorly matched to user-triggered settle.**  
- **Evidence:** `{ duration: 480, easing: "ease-in" }`.  
- **Impact:** `ease-in` delays the response at the moment the user releases. `480ms` may be acceptable for some drawer travel, but it is long for a repeated operational control unless distance-scaled or spring-based.

**P1 — Transform ownership conflict.**  
- **Evidence:** `.sheet:active { transform: scale(0.96); }` while the drag should ideally use `transform: translateY(...)`.  
- **Impact:** If translate and press scale are both applied to `.sheet`, one can overwrite the other unless composed deliberately or split across wrapper layers.

**P1 — Reduced Motion requirement is not met in the shown code.**  
- **Evidence:** No `prefers-reduced-motion` branch; the same spatial travel and `480ms` settle apply to all users.  
- **Impact:** The product requirement says Reduced Motion must preserve state feedback without large spatial travel. This implementation has no shown alternative feedback channel.

**P2 — Pointer capture and gesture boundaries are absent.**  
- **Evidence:** No `setPointerCapture`, intent threshold, cancellation handling, boundary resistance, or multi-pointer policy is shown.  
- **Impact:** Tracking may be lost when the pointer leaves the sheet; taps can become drags; overdrag behavior is undefined.

## Concrete direct-manipulation moves

1. **Represent sheet state as snap-state + translation, not `top`.**  
   Use snap points for `collapsed | half | full`, and render movement with `transform: translate3d(0, var(--sheet-y), 0)`.

2. **Preserve the grab offset.**  
   On pointer down, read the current presentation Y and store `grabOffset = event.clientY - currentSheetY`; on move, set `nextY = event.clientY - grabOffset`.

3. **Capture and qualify the gesture.**  
   Use pointer capture after an `8–12px` vertical intent threshold, ignore secondary pointers, and release capture on end/cancel.

4. **Remove input lockout.**  
   Do not reject pointerdown during settle. Stop/cancel the current animation, read the current visual position, and start the new drag from that value.

5. **Measure velocity separately from target selection.**  
   Track recent `{ y, time }` samples in CSS px and monotonic ms; compute release velocity in CSS px/s.

6. **Keep current snap semantics unless product signs off on momentum targeting.**  
   If existing behavior is “nearest release position,” preserve it. As a runtime hypothesis, compare against:  
   `projectedEndpoint = currentY + boundedProjection(releaseVelocity)` → clamp to snap range → nearest valid snap.

7. **Hand release velocity into settle.**  
   Use a spring or equivalent animation primitive that starts from current Y with the measured velocity. Prefer critically damped or lightly damped behavior; avoid decorative bounce for this calm operations context.

8. **Separate transform layers.**  
   Example: outer sheet owns `translateY`; inner handle/content owns press feedback like `scale(0.98)`. Avoid competing writes to the same `transform`.

9. **Replace broad transitions.**  
   Change `transition: all 300ms` to explicit properties only, e.g. `transform`, `opacity`, or state-color tokens. Do not transition layout properties accidentally.

10. **Add Reduced Motion behavior.**  
   In reduced motion, avoid large animated travel and elastic effects. Snap state should update immediately or within a very short duration, with feedback via handle color, shadow/border change, state label, opacity, or a compact `80–120ms` non-spatial transition.

## Verified / unverified boundaries

**Verified from the supplied snippet:**  
- Drag writes `top` during pointer movement.  
- Settle animates `top` with WAAPI, `480ms`, `ease-in`, `fill: "forwards"`.  
- New pointerdown is blocked while `animating` is true.  
- CSS applies `transition: all 300ms`.  
- CSS applies active-state `transform: scale(0.96)`.  
- No shown pointer capture, velocity sampling, presentation-value interruption, boundary resistance, or Reduced Motion branch.

**Not verified from static code:**  
- Actual frame rate, smoothness, input latency, or layout cost on target devices.  
- Whether surrounding code clamps sheet bounds or handles `pointercancel`.  
- Whether `nearestSnapPoint` encodes product-approved snap semantics.  
- Whether accessibility state, keyboard controls, focus management, and ARIA exist elsewhere.  
- Browser-specific WAAPI behavior, especially interaction between animated `top`, inline `top`, and `fill: forwards`.

## Smallest runtime validation plan

1. **Gesture feel pass:** slow drag, fast flick, partial drag, pointer leaving bounds, pointercancel, and mid-settle regrab. Pass if there is no jump, no dead period, and the sheet tracks the pointer with preserved grab offset.

2. **Physics pass:** log current Y, release velocity in CSS px/s, chosen target, and settle start velocity. Pass if target choice matches product semantics and settle starts continuously from the release motion.

3. **Performance pass:** profile under representative app load while dragging and settling. Pass if pointermove avoids layout thrash and stays within frame budget on the supported refresh rates.

4. **Reduced Motion pass:** enable reduced motion and repeat state changes. Pass if collapsed/half/full feedback remains clear without large animated travel or elastic movement.

5. **Accessibility interaction pass:** verify keyboard state changes, focus visibility, and non-pointer operation. Pass if the sheet can be controlled and understood without drag.
