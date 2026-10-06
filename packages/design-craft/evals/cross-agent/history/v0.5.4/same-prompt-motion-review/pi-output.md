## 1. Evidence level and design read

**Evidence level: static-only, snippet-scoped.** The prompt proves the shown implementation choices, but does **not** prove real smoothness, frame rate, touch feel, computed style precedence, or Reduced Motion runtime behavior.

**Reading this as:** a high-frequency desktop web operations sheet for task-preserving state changes, with calm utility motion optimized for direct manipulation and context continuity.

## 2. Should this motion exist?

**Yes, but only as causal motion.**
- **Should exist:** immediate pointer-down affordance, 1:1 drag tracking, short interruptible settle between `collapsed` / `half` / `full`.
- **Should not animate:** arbitrary `top` layout movement, `transition: all`, global sheet `scale(0.96)` during drag, long ease-in settle, and large spatial travel under Reduced Motion.
- **Motion goal:** preserve “my hand moved this sheet here,” not add personality.

## 3. Prioritized blocking findings

### P0 — Drag is not actually gated to a drag gesture
**Evidence:** `pointermove` always runs `sheet.style.top = ...`; no `dragging` flag, intent threshold, pointer capture, or pointer-id ownership.  
**Why it blocks:** merely moving a pointer over the sheet can reposition it. That destroys operational trust and task context.

### P0 — Tracking is not 1:1 direct manipulation
**Evidence:** `pointerdown` stores `startY`, but it is unused; `pointermove` sets `top` directly to `event.clientY`.  
**Why it blocks:** the sheet can jump so its top aligns to the pointer instead of preserving the grab offset. The object is not “held”; it is teleported.

### P0 — Settle animation is non-interruptible in the wrong direction
**Evidence:** `if (animating) return` blocks `pointerdown` during settle.  
**Why it blocks:** a gesture sheet must be catchable mid-flight from its current presentation value. Lockout makes the UI feel like a modal animation, not a manipulated surface.

### P1 — Motion uses expensive/conflicting property ownership
**Evidence:** JS and WAAPI animate `top`; CSS applies `transition: all 300ms`; active state applies `transform: scale(0.96)`.  
**Why it matters:** `top` risks layout work; `transition: all` can accidentally animate every pointermove; sheet-level scale changes the object being dragged instead of giving precise handle feedback.

### P1 — Settle physics are backwards for a high-frequency utility surface
**Evidence:** `duration: 480`, `easing: "ease-in"`, target selected only from `nearestSnapPoint(sheet.offsetTop)`, no velocity history, no Reduced Motion branch.  
**Why it matters:** ease-in delays response at release; 480ms is heavy for repeated operations; quick flicks have no velocity handoff; Reduced Motion users may still get large travel.

## 4. Concrete design moves

1. **Pointer-down feedback:** give the drag handle immediate, subtle feedback only: e.g. handle color/height/opacity or `scaleY`, not full-sheet `scale(0.96)`. Keep it under ~100–160ms and preserve focus-visible styling.

2. **Gesture ownership:** on valid pointer down, set `dragging = true`, store `pointerId`, call `setPointerCapture(pointerId)`, record `grabOffset = pointerY - currentSheetY`, and ignore other pointers.

3. **1:1 tracking:** after an 8–12px intent threshold, update `translateY(currentY)` from `event.clientY - grabOffset`; avoid `top` during the gesture. Disable CSS transitions while dragging.

4. **Presentation-value interruption:** if the sheet is settling and the user presses it, cancel/read the active animation, derive the current on-screen `translateY`, preserve current velocity if available, and start the new drag from that value with no jump.

5. **Velocity handoff:** keep a short sample history using monotonic timestamps; compute release velocity in **CSS px/s**. Feed that measured velocity into the settle animation/spring as initial velocity, converting units if the chosen API requires relative velocity.

6. **Projected endpoints:** keep current product semantics unless momentum targeting is authorized. Candidate: compute bounded projected endpoint from current presentation value + release velocity, clamp to valid sheet range, then choose nearest snap point only if momentum-based targeting is approved.

7. **Soft boundaries:** clamp hard logical states, but apply rubber-band resistance beyond min/max during drag; avoid elastic bounce on settle for this calm operations surface unless real testing proves it improves control.

8. **Reduced Motion:** replace large animated travel with immediate or very short state change, e.g. snap to target with ≤80–120ms opacity/handle/status change. Preserve state feedback: label/state indicator updates, handle affordance, and focus continuity.

## 5. Verified versus unverified claims

**Verified from static snippet**
- `pointermove` is not gated by a dragging state.
- `startY` is stored but unused in shown code.
- The sheet animates `top` with WAAPI.
- CSS uses `transition: all 300ms`.
- Active state scales the whole `.sheet`.
- `pointerdown` is ignored while `animating`.
- No Reduced Motion branch appears in the provided evidence.
- No velocity tracking or pointer capture appears in the provided evidence.

**Unverified / runtime-dependent**
- Actual frame rate, layout cost, and jank severity.
- Whether other code outside the snippet compensates for dragging state, Reduced Motion, or focus behavior.
- Whether `offsetTop` reflects the animated presentation value consistently across the intended browsers.
- Touch feel on real hardware.
- Responsive behavior across viewport heights.
- Keyboard/focus behavior for the sheet states.

## 6. Minimal browser/device validation plan before approval

1. **Desktop Chrome/Edge pointer test:** verify pointer down, threshold, grab-offset preservation, pointer capture, drag outside bounds, release to each snap point, and mid-settle interruption with no jump.

2. **Touch hardware test:** validate the same flow on a real touch device or trackpad/touchscreen laptop; record whether flick velocity changes settle behavior as designed.

3. **Reduced Motion run:** enable `prefers-reduced-motion: reduce`; confirm no large spatial travel, no elastic overshoot, and state feedback remains visible.

4. **Performance trace:** profile drag and settle under realistic app load; confirm no repeated layout thrash from `top`/`offsetTop`, no long tasks in pointermove, and stable 60Hz target minimum.

5. **Accessibility smoke:** keyboard access to sheet states, visible focus, screen-reader state announcement if state changes are meaningful, and no loss of focus/context after snap.
