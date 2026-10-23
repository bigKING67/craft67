## Verdict

**[Static evidence] Not ready for repeated daily use.** The implementation does not maintain a reliable relationship between pointer movement, sheet position, and snap state. Its delayed settling and whole-sheet shrinking also work against a calm, direct manipulation feel.

Labels: **[Static]** visible in the supplied code; **[Risk]** depends on surrounding implementation; **[Recommendation]** proposed change.

## Prioritized findings

### P0 — Establish a real drag lifecycle
- **[Static]** `pointermove` updates position without checking whether a drag started. Hovering pointers can move the sheet.
- **[Static]** `startY` is recorded but never used. Setting `top` to `clientY` ignores both the initial sheet position and where the user grabbed it.
- **[Risk]** Unless the coordinate systems happen to align, the sheet jumps on movement; `clientY` is viewport-relative while `top` is relative to the positioning context.
- **[Static]** There is no active pointer ID, pointer capture, or cancellation handling. `pointerup` can settle without an accepted drag.
- **[Risk]** Leaving the sheet, browser touch scrolling, or a second pointer can interrupt or corrupt the gesture.

### P0 — Make position and animation ownership consistent
- **[Static]** `animating` blocks only `pointerdown`; movement and release handlers still run during settling. Multiple settle animations can start.
- **[Static]** A forwards-filled animation retains control of `top`, but its final value is not committed to the underlying inline position. Subsequent writes can be masked by the retained animation.
- **[Static]** `.finished` has no rejection cleanup. Introducing animation cancellation without addressing this would leave the flag stuck.
- **[Recommendation]** Keep one authoritative position, one active pointer, one active animation, and an explicit collapsed/half/full state. Interrupt settling from its current rendered position rather than ignoring a new grab.

### P1 — Remove lag and ambiguous motion
- **[Static]** `transition: all 300ms` applies to drag-time `top` changes. The sheet chases pointer updates instead of tracking them directly.
- **[Static]** The settle always takes 480 ms and uses `ease-in`: it starts slowly and accelerates toward the stop, rather than visibly braking into place.
- **[Static]** `:active` shrinks the entire sheet to 96%, including its content, without regard to whether a valid drag exists.
- **[Risk]** Repeated large-surface scaling may feel like a generic press effect rather than sheet manipulation.
- **[Recommendation]** Disable transitions during dragging; remove whole-sheet scaling. Use a subtle handle, border, or surface treatment for interaction feedback.

### P1 — Define snap intent and accessible alternatives
- **[Static]** The shown snap decision receives position only; release velocity is not explicitly supplied.
- **[Unverified]** `nearestSnapPoint` internals, bounds, scroll arbitration, state semantics, and keyboard controls are not shown.
- **[Static]** No Reduced Motion behavior appears in the supplied code. The shown release path always requests spatial animation.
- **[Recommendation]** Provide explicit controls for collapsed, half, and full states, with programmatically exposed state and predictable focus behavior.

## Concrete direct-manipulation moves

1. **Accept a deliberate grab.** Use a designated handle; accept one primary pointer and capture it. Do not hijack content controls or text selection.
2. **Preserve the grab offset.** Record pointer origin and current rendered sheet position in a consistent coordinate system. Compute `position = initialPosition + pointerDelta`.
3. **Track immediately.** Apply a bounded vertical translation with no easing or transition while dragging. Prefer `transform` over repeated `top` writes; avoid hot-path layout reads.
4. **Coordinate with scrolling.** Define `touch-action` on the handle and an explicit policy for sheet-content scrolling. Handle `pointercancel` and lost capture with cleanup and a deterministic resting state.
5. **Resolve intent predictably.** Use release position plus measured velocity to select among three bounded snaps. Slow releases choose nearby states; deliberate flicks advance directionally, with thresholds that prevent accidental skips.
6. **Settle quietly.** Use a short, distance-aware ease-out or restrained, non-oscillating spring. A roughly 180–280 ms settle is a starting hypothesis, not a validated target.
7. **Allow interruption.** Cancel the old settle, rebase to its visible position, and resume tracking without a jump. On completion, commit the final position and clear animation ownership.
8. **Respect Reduced Motion.** Keep necessary finger-following feedback, but eliminate autonomous snap travel and large-scale effects. Commit the destination immediately and signal it with an updated state label/indicator; optionally use a brief non-spatial treatment.

## Verified / unverified boundaries

**Verified by static inspection:** the event guards, coordinate assignment, unused origin, timing/easing, retained animation fill, broad transition, and active scaling described above.

**Not verified:** rendered appearance, frame rate, actual touch/scroll behavior, browser compatibility, assistive-technology behavior, or surrounding safeguards. No browser or device validation was performed.

## Smallest runtime validation plan

- **One desktop browser, mouse + keyboard:** test all three states, hover without grabbing, off-handle clicks, release outside, rapid re-grab during settling, and explicit state controls. Pass: no unintended movement, jumps, blocked interactions, or stale state.
- **One physical touch device:** test handle drag versus content scroll, slow release versus flick, a second touch, and cancellation. Pass: predictable ownership, bounded snaps, and no stuck drag.
- **Reduced Motion enabled:** repeat state changes and releases. Pass: no autonomous large spatial travel; destination and focus remain clear.
- **One short performance recording:** drag and settle through all states. Check pointer-to-sheet lag, repeated layout work, dropped frames, and retained animations after repeated interactions.
