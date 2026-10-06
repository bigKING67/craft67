## Verdict

**Block — static source review only.**  
Evidence shows this is not yet a reliable direct-manipulation sheet for a calm, frequently used operations app. It can jump, track when not dragging, ignore velocity, lock during settle, animate layout properties, and lacks Reduced Motion behavior. No browser/device behavior is claimed.

## Prioritized findings

**P0 — Drag ownership is broken**  
- **Static evidence:** `pointermove` always writes `sheet.style.top`, even if no active drag began, the pointer left the element, a second pointer appears, or `animating` blocked `pointerdown`.
- **Risk:** Cursor/touch movement can reposition the sheet outside an intended gesture.
- **Fix:** Track `isDragging`, `pointerId`, pointer capture, `pointercancel`, and release cleanup.

**P0 — The sheet will likely jump under the pointer**  
- **Static evidence:** `startY` is recorded but never used; movement sets `top = event.clientY`.
- **Risk:** The sheet’s top edge snaps to the pointer instead of preserving the grab offset.
- **Fix:** Store `grabOffset = event.clientY - currentSheetY`; set position from `event.clientY - grabOffset`.

**P0 — Not Reduced Motion compliant**  
- **Static evidence:** no `prefers-reduced-motion` branch; release always travels spatially for `480ms`.
- **Product conflict:** Reduced Motion must preserve state feedback without large travel.
- **Fix:** Under Reduced Motion, snap state logically with minimal or no travel; use short opacity/color/handle/state-label feedback instead of full spatial animation.

**P1 — Uses layout animation on the gesture hot path**  
- **Static evidence:** writes and animates `top`; CSS has `transition: all 300ms`.
- **Risk:** Layout/reflow and broad transition interference, especially in data-heavy operations screens.
- **Fix:** Use compositor-friendly `transform: translateY(...)`; restrict transitions to named properties.

**P1 — Release motion is poorly matched to direct manipulation**  
- **Static evidence:** fixed `480ms`, `ease-in`, nearest target from `offsetTop`, no velocity.
- **Risk:** Ease-in delays response after release; quick flicks are ignored; settling cannot inherit momentum.
- **Fix:** Measure release velocity in CSS px/s, choose target by product-owned snap rules, and settle with an interruptible spring or equivalent.

**P1 — Interruption model is unsafe**  
- **Static evidence:** global `animating` rejects `pointerdown`; `.finished.then` has no cancellation/error path.
- **Risk:** Users cannot grab the sheet mid-flight; canceled animations may leave `animating = true`.
- **Fix:** Allow retargeting from the current presentation value; cancel/replace active animation safely; always cleanup in `finally` or equivalent.

**P2 — Transform ownership conflicts**  
- **Static evidence:** `.sheet:active { transform: scale(0.96); }`; proposed drag should also use `transform`.
- **Risk:** Press scale and drag translation can overwrite each other.
- **Fix:** Use separate layers, e.g. outer wrapper owns `translateY`, inner surface owns press scale.

**P2 — Snap/state model is implicit**  
- **Static evidence:** collapsed/half/full are only inferred through `nearestSnapPoint(sheet.offsetTop)`.
- **Risk:** No clear state feedback, no accessible state, no resilient source of truth.
- **Fix:** Maintain explicit state: `collapsed | half | full`; reflect with attributes, handle affordance, focus/keyboard behavior, and reduced-motion feedback.

## Concrete direct-manipulation moves

1. Add `isDragging`, `activePointerId`, `pointer capture`, and `pointercancel` handling.  
2. Preserve grab offset: `dragY = pointerClientY - grabOffset`, not raw `clientY`.  
3. Use `transform: translateY(var(--sheet-y))` or a single transform owner instead of `top`.  
4. Add an intent threshold around `8–12px` so taps/presses do not become drags.  
5. Clamp to collapsed/half/full bounds, with optional soft resistance beyond edges.  
6. Track recent pointer samples with timestamps; compute release velocity in CSS px/s.  
7. Keep snap-target semantics explicit: nearest current position unless momentum-based targeting is intentionally approved.  
8. If momentum is approved, select snap from a bounded projected endpoint, then settle with measured velocity.  
9. Replace `ease-in 480ms` with a short, interruptible settle; default to no bounce for this product tone.  
10. Replace `transition: all` with specific transitions, e.g. handle color, shadow, or inner press scale only.  
11. Let users interrupt the settle by grabbing the current on-screen position.  
12. For Reduced Motion, update state immediately or near-immediately and use non-travel cues: handle emphasis, state text, shadow/color change, or subtle opacity.

## Verified / unverified boundaries

**Verified by static source**
- Layout property `top` is mutated and animated.
- `transition: all` is present.
- `ease-in` and `480ms` are configured.
- `startY` is unused.
- Pointer capture, pointer identity, pointer cancel, velocity, hysteresis, bounds, and Reduced Motion branches are absent from the snippet.
- Animation cleanup is incomplete if the animation is canceled/rejected.

**Unverified**
- Actual smoothness, jank, frame rate, and device feel.
- Whether surrounding code clamps positions or supplies state elsewhere.
- Whether CSS cascade or layout context changes the observed result.
- Actual snap-point geometry.
- Browser-specific WAAPI/`offsetTop` behavior in this app.
- Touch hardware behavior and 60/120 Hz feel.

## Smallest runtime validation plan

1. **Desktop pointer pass:** drag from each state to each other state; verify no jump, no move without active drag, and correct cleanup after cancel.  
2. **Interruption pass:** release toward a snap point, grab mid-settle, reverse direction; verify no visual jump and no input lock.  
3. **Velocity pass:** compare slow drag vs quick flick; verify product-approved target selection.  
4. **Bounds pass:** drag beyond collapsed/full; verify clamp or soft resistance.  
5. **Reduced Motion pass:** enable Reduced Motion; verify state feedback remains but large spatial travel/overshoot is removed.  
6. **Performance pass:** inspect for layout work during drag under representative app load before claiming smoothness.
