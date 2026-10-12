## Verdict — revise before approval

**[Static evidence]** The snippet does not establish reliable direct manipulation or the required Reduced Motion behavior.  
**[Design judgment]** For a calm, frequently used operations app, prioritize immediate control and clear snap-state feedback over whole-sheet scaling and prolonged settling.  
**[Unverified]** Jumping, lag, frame drops, and perceived responsiveness are risks—not observed results.

## Prioritized findings and concrete moves

### 1. P1 — Drag ownership and coordinates are incomplete
**Evidence:** `startY` is recorded but unused. Every `pointermove` writes viewport-relative `clientY` into `top`, which uses the element’s positioning context. No active-drag flag, pointer-ID ownership, capture, cancellation, or bounds are shown.

**Risk:** Hover could move the sheet; grabbing below its edge could reposition it unexpectedly; leaving the surface or a second pointer could disrupt tracking.

**Move:**
- Use explicit `idle → pending → dragging → settling` states and one active pointer ID.
- Record pointer origin and current displayed sheet position in a consistent CSS-pixel coordinate space.
- After a provisional **8–12 CSS px intent threshold**, track `initialSheetY + (currentPointerY − initialPointerY)` without easing; preserve the grab offset.
- Capture the pointer; handle `pointercancel` and lost capture, and ignore unrelated pointers.
- Prefer a dedicated drag handle with an explicit touch-action policy, preserving scrolling and controls inside the sheet.
- Apply bounded resistance beyond full/collapsed limits; remove elastic travel in Reduced Motion.

**Acceptance evidence needed:** Offset grabs, hover, boundary exits, cancellation, nested scrolling, and second-pointer tests show stable ownership and tracking.

### 2. P1 — Settling is not safely interruptible
**Evidence:** `animating` blocks only `pointerdown`; moves and releases remain active. No animation handle is retained. `fill: "forwards"` retains an animation effect without committing the target to underlying state; no cancellation cleanup is shown.

**Risk:** Repeated releases can create competing animations; displayed position, inline position, and logical state can diverge.

**Move:**
- Give one controller ownership of position, velocity, and the active animation.
- On re-grab, sample the current presentation position and velocity, cancel the previous settle, and continue from that position—not the prior target.
- Commit the final position and collapsed/half/full state, then remove the retained effect.
- Make completion and cancellation cleanup safe against stale animation callbacks.

**Acceptance evidence needed:** Re-grab and reverse at several points during settling; no position discontinuity, stale callback, or stuck interaction state.

### 3. P1 — Multiple animation mechanisms undermine direct tracking
**Evidence:** Dragging writes `top`; CSS transitions all properties for `300ms`; WAAPI also animates `top`. `:active` scales the entire sheet to `0.96`.

**Risk:** Transitioned drag updates can trail the pointer; layout-property animation can add rendering work. Whole-sheet scaling changes content and grab geometry for decorative feedback.

**Move:**
- Anchor layout and drive motion through a single `translateY` owner, with **no CSS transition on the drag translation**.
- Coalesce writes to animation frames; keep repeated layout measurements out of the move path.
- Remove whole-sheet press scaling; use immediate handle color or border feedback.
- Limit transitions to explicitly chosen feedback properties. If transforms must coexist, compose them deliberately or separate wrappers.

**Acceptance evidence needed:** Pointer/presentation traces confirm tracking; a rendering trace checks layout work and missed frames. Transform use alone does not prove smoothness.

### 4. P2 — Release behavior discards gesture momentum
**Evidence:** Target selection receives only `offsetTop`; settling always uses `480ms` and `ease-in`. No velocity samples are collected.

**Risk:** A slow drag and fast release receive identical timing; acceleration toward a fixed endpoint may make the stop feel abrupt. The duration alone is not proof of poor feel.

**Move:**
- Measure release velocity from recent timestamped samples in **CSS px/s**.
- Preserve nearest-position snapping unless momentum-based targeting is explicitly approved.
- For an experiment, calculate `projectedY = clamp(y + velocity × 0.15s, fullY, collapsedY)`; if authorized, snap nearest that bounded endpoint.
- Independently of target selection, pass bounded measured velocity into an interruptible, critically damped settle. Start tuning around a **250–300ms response scale**, not a mandatory fixed duration; avoid bounce for this product.

**Acceptance evidence needed:** Slow releases and fast flicks around both snap boundaries follow the approved target rule and decelerate coherently.

### 5. P1 — Reduced Motion and non-drag state access are not shown
**Evidence:** Neither the supplied JS nor CSS branches on Reduced Motion. Only pointer-driven state changes are shown; surrounding controls and semantics are unknown.

**Risk:** The explicit no-large-travel requirement is unmet by this snippet, and drag may be the only available state-selection mechanism.

**Move:**
- In Reduced Motion, replace large animated travel and inertial settling with immediate state placement plus static selected-state feedback or a brief color/opacity change.
- To satisfy the strict no-large-travel requirement during gestures too, preview the candidate state on the handle instead of moving the large panel, then commit on release.
- Provide keyboard-operable controls for collapsed, half, and full states; expose the current selection programmatically and visibly, and preserve sensible focus when content becomes hidden.
- Respond to preference changes by stopping active travel and resolving to a valid state.

**Acceptance evidence needed:** All three states remain distinguishable and reachable with Reduced Motion and keyboard-only input, without spatial interpolation or lost focus.

## Verified / unverified boundary

- **Verified by inspection:** The code paths, properties, timings, and omissions described above, limited to the supplied snippet.
- **Not verified:** Rendered geometry, `nearestSnapPoint` internals, surrounding accessibility support, actual touch/scroll arbitration, performance, or motion feel.
- No files were edited. No browser or device validation was performed.

## Smallest runtime validation plan

1. **Desktop browser, pointer + keyboard:** Exercise all three states; offset grabs, hover, rapid releases, mid-settle reversals, cancellation, and keyboard state selection. Log pointer ID, displayed position, velocity, chosen target, and committed state.
2. **One representative touch device:** Repeat drag/re-grab tests, leave the handle bounds, add a second touch, and scroll sheet content. Record a short interaction video.
3. **Reduced Motion on, including a live toggle:** Repeat state selection and interrupt an active settle; confirm no large animated travel and persistent state/focus feedback.
4. **One performance trace under representative app load:** Inspect drag and settle for repeated layout and missed frame deadlines at the tested refresh rate. Treat roughly **16.7ms at 60Hz / 8.3ms at 120Hz** as provisional frame budgets—not measured results.

These checks provide an initial acceptance packet, not cross-browser or cross-device certification.
