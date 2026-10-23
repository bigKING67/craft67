## Verdict

**[Static evidence] Not ready for repeated-use direct manipulation.** The snippet lacks gesture ownership, mixes positioning and animation systems, and provides no Reduced Motion handling.  
**[Predicted experience]** Likely to feel detached and inconsistent rather than calm: grabbing can jump, dragging can lag, and settling cannot be reliably interrupted.

Labels below: **[Observed]** means visible in the supplied code; **[Risk]** means a runtime consequence requiring validation; **[Proposal]** means a recommended change.

## Prioritized findings

### P0 — Gesture correctness and user control

- **[Observed] No active-drag or pointer-ID guard.** Every delivered `pointermove` writes position—even mouse hover—and every delivered `pointerup` initiates settling. Returning from `pointerdown` does not disable the other handlers.
- **[Observed] Grab position is discarded.** `startY` is recorded but unused. `clientY` is viewport-relative; CSS `top` uses the element’s positioning context.
  **[Risk]** The sheet jumps toward the pointer instead of preserving where it was grabbed. Exact behavior depends on omitted positioning CSS.
- **[Observed] No explicit capture, cancellation, or lost-capture handling.**
  **[Risk]** Leaving the sheet, browser gesture takeover, or a second pointer can leave interaction state inconsistent. Touch implicit capture may help in some cases; it is not a complete lifecycle.
- **[Observed] Interruption is neither supported nor consistently blocked.** `animating` rejects a new start while moves and releases remain enabled. No animation handle is retained.
  **[Risk]** Overlapping settles and stale completion callbacks can race.

### P1 — Motion ownership and release behavior

- **[Observed] Three effects compete:** inline `top`, CSS `transition: all 300ms`, and a filled Web Animation on `top`.
  **[Risk]** CSS interpolation introduces tracking lag; a finished animation’s retained effect can mask later inline position changes. Completion does not commit the target into a durable position model.
- **[Observed] Release uses position alone and always takes 480ms with `ease-in`.** No release velocity is sampled or transferred.
  **[Risk]** A flick and a careful placement receive the same treatment; the settle begins slowly, accelerates toward the endpoint, then stops abruptly. This is poorly matched to frequent operational work.
- **[Observed] `top` is repeatedly written and `offsetTop` read.**
  **[Risk]** Layout work may affect smoothness. This is a performance concern, not measured jank.

### P1 — Reduced Motion and state access

- **[Observed] No preference branch exists in the supplied JS or CSS.** Disabling CSS transitions alone would not disable `sheet.animate()`.
- **[Observed] No non-drag controls or accessible state feedback are shown.** Their absence from the whole app cannot be inferred.
  **[Proposal]** Provide keyboard-operable controls for collapsed, half, and full states, with a persistent, accessible current-state indication.

### P2 — Unnecessary whole-surface feedback

- **[Observed] `:active` scales the entire sheet to `0.96`.**
  **[Risk]** Content and the apparent grab location move under the pointer; pressing child controls may also shrink the surface.
  **[Proposal]** Remove whole-sheet scaling. Use an immediate, restrained handle highlight instead.

## Concrete direct-manipulation moves

1. **Establish one position owner.** Maintain numerical `y`, active pointer ID, gesture phase, settled state, and a cancellable settle controller. Render translation through `transform`; do not transition the drag position.
2. **Grab the visible position.** On an eligible primary-pointer press, sample the current rendered position, cancel the settle without losing that position, record pointer origin, and capture the pointer.
3. **Track displacement, not absolute pointer coordinates:**  
   `y = grabbedY + (event.clientY - pointerDownY)`.  
   Update immediately, or coalesce to one write per animation frame without adding easing.
4. **Resolve scrolling deliberately.** Prefer a dedicated drag handle with an appropriate `touch-action` policy; preserve content scrolling and button interaction. If content can initiate dragging, define scroll-edge handoff and a small intent threshold.
5. **Bound the gesture.** Track 1:1 between collapsed and full; beyond them, use restrained progressive resistance. Define safe outcomes for `pointercancel` and lost capture; always clear ownership.
6. **Choose the snap from intent.** Estimate velocity from a short timestamped sample history, discard stale velocity after a pause, and use a bounded projected endpoint to select among the three states. Add hysteresis near boundaries to avoid accidental state changes.
7. **Settle calmly.** Use a velocity-aware, strongly damped spring with little or no overshoot. Treat tuning as provisional—not a universal duration. A new grab starts from the current presentation position; a retargeted settle carries current velocity.
8. **Finalize cleanly.** Commit the exact snap position and semantic state, release animation effects, and ignore stale callbacks. Handle cancellation/rejection without leaving a busy flag stuck.
9. **Reduced Motion:** keep deliberate dragging directly attached to input, but remove automatic long-travel settling, bounce, and scaling. Commit the selected snap immediately, optionally using a brief non-spatial indicator fade. Offer state buttons so no large drag is required. Apply preference changes to active JS motion too; do not erase the transform needed to represent the state.

## Verified / unverified boundaries

**Verified by static inspection:** the handlers, animation options, CSS rules, and missing safeguards described above. No files were edited.

**Unverified:** actual geometry, `nearestSnapPoint()` behavior, surrounding accessibility/scroll logic, browser animation interactions, frame cost, and perceived comfort. **No browser or device validation was performed.**

## Smallest runtime validation plan

Use one desktop mouse/keyboard browser and one real touch device, each with Reduced Motion off and on:

1. **Ownership:** hover without pressing; grab at different handle positions; leave bounds; cancel; add a second touch. Pass: no unsolicited motion, initial jump, or stuck gesture.
2. **Release/interruption:** slow drag, flick, pause then release, and reverse mid-settle across all three states. Pass: predictable snaps, continuous handoff, immediate re-grab, no stale completion jump.
3. **Scroll/accessibility:** scroll sheet content, activate child controls, and select all states by keyboard. Pass: no accidental drag, stable focus, clear state feedback.
4. **Reduced Motion:** repeat transitions and change the preference mid-settle. Pass: no automatic large spatial travel or bounce; state remains obvious and usable.
5. **One short performance trace:** record dragging plus interruption. Inspect layout work, missed frames, and competing effects; judge responsiveness from that evidence rather than assuming `transform` alone guarantees it.
