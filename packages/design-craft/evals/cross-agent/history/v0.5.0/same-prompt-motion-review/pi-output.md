## 1. Evidence level and design read

**Evidence level: static implementation evidence only.**  
The snippet proves property choices, timing/easing, missing branches, and event logic shown here. It does **not** prove frame rate, touch feel, computed CSS conflicts, real interruption behavior, Reduced Motion behavior, or device/browser smoothness.

**Reading this as:** a desktop web operations bottom sheet for keyboard-heavy staff, with calm utility motion, optimized for preserving task context while changing between `collapsed`, `half`, and `full`.

## 2. Should this motion exist?

**Yes, but narrowly.** Motion should exist to preserve causality between drag position and settled sheet state.

Should animate:
- The **settle from release position to snap point**, if short, interruptible, and velocity-aware.
- Small **handle-level feedback** on pointer down.

Should not animate:
- **Drag tracking itself**; it should be 1:1 with the pointer, not eased.
- `top`/layout properties.
- `transition: all`.
- Full-sheet `scale(0.96)` during active drag; it shrinks dense work content and breaks spatial confidence.
- Large spatial travel in Reduced Motion mode.

## 3. Prioritized blocking findings

### P0 — Drag is not true direct manipulation
`pointermove` sets `sheet.style.top = event.clientY`, ignoring grab offset, pointer capture, active drag state, and coordinate normalization. The sheet can jump to the pointer rather than staying attached where grabbed. That breaks “object under finger” causality.

### P0 — Animation conflicts with interaction ownership
`animating` blocks input until `.finished`, so the user cannot grab/reverse mid-settle. A gesture sheet must be interruptible from the current presentation value, not locked to a previous logical animation.

### P0 — Layout animation and `transition: all` are wrong for this hot path
The code mutates and animates `top`; CSS also says `transition: all 300ms`. This risks laggy drag tracking, layout work, and accidental animation of unrelated properties. For a repeatedly used ops surface, this is a feel-breaking performance risk.

### P1 — Settle physics are non-causal
The release uses `nearestSnapPoint(sheet.offsetTop)` plus `480ms ease-in`. There is no measured release velocity, no velocity handoff, no bounded projected endpoint, and no spring/damped response. `ease-in` is especially wrong because it delays the first visible response after release.

### P1 — Reduced Motion path is absent
The snippet has no `prefers-reduced-motion` handling. A bottom sheet can involve large vertical travel; Reduced Motion must preserve state feedback without forcing a long spatial slide.

## 4. Concrete design moves

1. **Pointer-down feedback**  
   Put feedback on the drag handle, not the whole sheet: subtle handle tint/elevation/cursor change, maybe `scaleY` or opacity for `100–160ms`. Keep content stable.

2. **1:1 tracking**  
   On drag start, store `grabOffset = pointerY - currentSheetY`; use pointer capture and track only the active `pointerId`. During drag, set `translateY(pointerY - grabOffset)` with transitions disabled.

3. **Presentation-value interruption**  
   Remove the `animating` input lock. On new pointer down, cancel the running animation, read the current on-screen/presentation `translateY`, and continue from that value with no jump.

4. **Velocity handoff**  
   Keep a short sample history using monotonic timestamps. Measure release velocity in **CSS px/s**. Feed that velocity into the settle animation as initial velocity, converting units if the chosen animation/spring API requires it.

5. **Projected endpoints**  
   Compute a bounded projected endpoint from the current presentation value and release velocity. If product semantics authorize momentum targeting, choose the nearest snap point to that endpoint; otherwise keep current nearest-snap behavior and treat projection as a testable enhancement.

6. **Soft boundaries**  
   Clamp official snap range, but apply progressive resistance beyond min/max instead of hard stops. Use an `8–12px` intent threshold so taps on sheet content do not become accidental drags.

7. **Reduced Motion**  
   In `prefers-reduced-motion`, remove elastic/bounce and large animated travel. Use instant or very short settle, e.g. ~80ms, plus non-spatial state feedback: handle state, label, shadow/color change, or snap-state announcement.

8. **Property/performance ownership**  
   Replace `top` with transform-based positioning. Remove `transition: all`; explicitly transition only safe properties. If press feedback and drag both need transforms, use separate wrapper layers or one composed transform owner.

## 5. Verified vs. unverified claims

Verified from snippet:
- Uses `top` during pointer move and WAAPI settle.
- Uses `480ms` and `ease-in`.
- Blocks pointer down while `animating`.
- Uses `transition: all 300ms`.
- Uses full-sheet `transform: scale(0.96)` on `:active`.
- Shows no Reduced Motion branch.
- Shows no pointer capture, velocity sampling, projected endpoint, soft boundary, or grab-offset logic.

Unverified:
- Actual smoothness/frame rate.
- Whether inherited CSS or framework code compensates elsewhere.
- Whether `sheet` is `fixed`, `absolute`, nested, transformed, or inside a scroller.
- Whether real touch/pointer cancellation, multi-touch, or keyboard behavior works.
- Whether `offsetTop` matches the animated presentation value in the real browser.
- Whether users expect momentum-based target selection or strict nearest-snap semantics.

## 6. Minimal validation plan before approval

1. **Desktop browser pointer test:** drag between all three snap states; verify no jump on grab, no lag during drag, and no input lockout mid-settle.  
2. **Computed-style check:** confirm only transform/opacity-safe properties animate; no `transition: all`; no layout-property animation in the drag path.  
3. **Interruption test:** release toward `full`, re-grab during settle, reverse to `half`; sheet must continue from current visible position.  
4. **Velocity test:** slow drag versus quick flick; record whether target choice and settle feel intentional.  
5. **Boundary test:** drag beyond top/bottom limits; verify resistance and recovery, not hard clipping or runaway movement.  
6. **Reduced Motion run:** enable `prefers-reduced-motion`; verify reduced spatial travel while state feedback remains clear.  
7. **Touch hardware smoke:** real trackpad/touchscreen/mobile-class touch if supported; verify pointer capture, cancellation, and multi-touch behavior.  
8. **Performance trace under app load:** test while the operations table/content is populated; confirm no obvious layout thrash or long tasks in the gesture path.
