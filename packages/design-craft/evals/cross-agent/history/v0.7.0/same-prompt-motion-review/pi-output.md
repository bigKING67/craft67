## 1. Evidence level and design read

**Evidence level:** L0 static review only. Source proves configured properties, missing branches, timing/easing choices, and interaction ownership gaps. It does **not** prove actual feel, smoothness, frame rate, device behavior, or Reduced Motion runtime behavior.

**Reading this as:** a web operations bottom sheet for repeat daily use, with calm utility motion, optimized for preserving task context while moving between `collapsed`, `half`, and `full`.

**Verdict:** **Block implementation approval** until the gesture is made direct, interruptible, bounded, and Reduced-Motion-safe.

---

## 2. Should this motion exist?

**Yes, but only as causal motion:**

- **Should exist:** direct 1:1 drag tracking, state-settle motion to the chosen snap point, small pointer-down acknowledgment, and clear state feedback.
- **Should not animate:** decorative sheet scaling, `transition: all`, eased pointer tracking, layout `top` changes during drag, and a long `ease-in` settle that delays visible response.
- **Reduced Motion:** must still communicate `collapsed / half / full`, but avoid large spatial travel, bounce, and elastic motion.

---

## 3. Prioritized blocking findings

**F1 — Drag is not direct manipulation.**  
Source: `pointermove` sets `sheet.style.top = event.clientY` with no active-drag flag, no intent threshold, no grab offset, and no pointer capture.  
Risk: the sheet can jump under the pointer, lose tracking outside bounds, and move even when a drag was not actually established.  
Repair: track `isDragging`, active pointer id, grab offset, and use pointer capture after threshold.

**F2 — Pointer tracking is likely eased by CSS instead of 1:1.**  
Source: `.sheet { transition: all 300ms; }` plus JS updates to `top`.  
Risk: every drag update may be transitioned, making the sheet chase the finger rather than stay attached.  
Repair: remove broad transition; during drag, no transition on position. Use compositor transform for frame updates.

**F3 — Settle motion is non-interruptible and uses the wrong response shape.**  
Source: `animating` blocks `pointerdown`; WAAPI animates `top` for `480ms` with `ease-in`.  
Risk: users cannot re-grab mid-flight; `ease-in` delays response at the moment causality matters most; 480ms is heavy for repeated operations work.  
Repair: interrupt from current presentation value, retarget from current position, and settle with a short spring or drawer-like ease-out/ease-in-out.

**F4 — Release ignores velocity and projected intent.**  
Source: target is `nearestSnapPoint(sheet.offsetTop)` only.  
Risk: a quick intentional flick may be treated the same as a slow release at the same coordinate.  
Repair: measure recent pointer samples in CSS px/s; keep nearest-position semantics only if product-owned, but add an authorized projected-endpoint path for momentum targeting.

**F5 — Accessibility and performance contracts are missing.**  
Source: no `prefers-reduced-motion`; animates layout property `top`; uses `transition: all`; active state scales the whole sheet.  
Risk: unnecessary layout work, possible visual instability, and no reduced-motion alternative for large travel.  
Repair: transform-based motion, explicit animated properties, and a Reduced Motion branch with short/non-spatial feedback.

---

## 4. Concrete design moves

1. **Pointer-down feedback:** acknowledge grab immediately with a subtle handle/content affordance, not full-sheet `scale(0.96)`. Example: handle color/opacity or 1–2px lift; keep content geometry stable.

2. **1:1 tracking:** after an `8–12px` intent threshold, set `isDragging = true`, capture the pointer, preserve `grabOffsetY`, and update `translateY(currentPointerY - grabOffsetY)` with no transition.

3. **Single transform owner:** avoid fighting `top` and `transform`. Use a sheet wrapper for translation and, if needed, an inner handle layer for press feedback.

4. **Presentation-value interruption:** if the user grabs during settle, cancel the running animation, read the current on-screen position, and start the drag from that value with no jump.

5. **Velocity handoff:** keep a short pointer history with monotonic timestamps; compute release velocity in CSS px/s; feed bounded velocity into the settle animation rather than restarting from zero.

6. **Projected endpoints:** if momentum targeting is approved, compute a clamped projected endpoint from current position + release velocity, then choose nearest valid snap point to that projection. If not approved, keep current nearest-snap semantics but still use velocity for the settle feel.

7. **Soft boundaries:** clamp valid snap range, but apply progressive resistance beyond `collapsed`/`full` instead of hard stops; remove bounce by default for this calm operations context.

8. **Reduced Motion:** disable large travel, overshoot, rubber-band, and long settle. Preserve state feedback with immediate position change or very short opacity/handle/status change, plus clear final state indication.

---

## 5. Verified vs. unverified claims

**Verified from static evidence:**

- `transition: all 300ms` is present.
- `top` is mutated on `pointermove`.
- release animation uses `top`, `480ms`, `ease-in`, and `fill: "forwards"`.
- `animating` blocks `pointerdown`.
- no visible Reduced Motion branch is shown.
- `startY` is assigned but not used in the shown code.
- no pointer capture, active pointer id, velocity sampling, or grab-offset logic is shown.

**Unverified / must remain hypotheses:**

- actual jank, frame rate, layout cost, and smoothness.
- whether `transition: all` definitely affects every runtime drag frame.
- exact behavior of `offsetTop` during/after WAAPI `fill: forwards`.
- real touch feel on trackpad, mouse, stylus, or mobile browser.
- responsive geometry, snap-point correctness, scroll conflict, and nested content behavior.
- Reduced Motion behavior in a browser, because no run was performed.

---

## 6. Minimal browser/device validation plan before approval

1. **Desktop browser pointer run:** drag collapsed → half → full and back; verify no jump, no eased tracking, no lost pointer when leaving sheet bounds.  
2. **Interruption run:** release toward a snap point, re-grab mid-settle, reverse direction; verify no lockout and no visual jump.  
3. **Velocity run:** compare slow release vs. quick flick from same approximate position; verify target-selection semantics match product intent.  
4. **Boundary run:** over-drag above full and below collapsed; verify resistance, clamping, and no content/context loss.  
5. **Reduced Motion run:** enable `prefers-reduced-motion`; verify state feedback remains clear without large travel or bounce.  
6. **Performance trace:** inspect main-thread work during drag; confirm transform/compositor path and no repeated layout-heavy hot path.  
7. **Touch hardware check:** validate on a real touch device or representative browser touch emulation only as a fallback.  
8. **Responsive check:** verify snap positions and reachable controls at narrow and desktop widths.
