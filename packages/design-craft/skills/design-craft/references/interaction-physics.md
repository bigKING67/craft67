# Interaction physics

Use this for drag, swipe, sheet, drawer, carousel, scrubber, reordering,
momentum, rubber-band, interruptible transition, or direct-manipulation work.
For ordinary hover/color transitions, `motion-quality.md` is sufficient.

## Contents

- [Direct response](#direct-response)
- [Presentation-value interruption](#presentation-value-interruption)
- [Spring language](#spring-language)
- [Velocity handoff and projection](#velocity-handoff-and-projection)
- [Soft boundaries and hysteresis](#soft-boundaries-and-hysteresis)
- [Performance and accessibility](#performance-and-accessibility)
- [Verification packet](#verification-packet)

## Direct response

- Show press feedback on pointer/touch down, not only on click/up.
- Keep manipulated content attached 1:1 to the pointer after the gesture passes
  a small intent threshold.
- Preserve the grab offset; never jump the object center under the finger.
- Use pointer capture or the native gesture equivalent so tracking continues
  outside the original bounds.
- Track a short time/position history so release velocity is measured rather
  than guessed from one event.
- State the coordinate space and units. For web examples, keep samples in CSS
  pixels with monotonic timestamps and report release velocity in CSS px/s;
  use points/s or dp/s only when the platform API uses those units.
- If drag translation and press feedback both write `transform`, give them
  separate wrapper layers or one explicit composed-transform owner. Do not let
  `translateY(...)` silently replace `scale(...)`, or vice versa.

## Presentation-value interruption

Gesture-driven motion must be interruptible:

- never lock input until a transition completes
- retarget from the current on-screen presentation value, not the previous
  logical target
- carry current velocity into the new target instead of restarting at zero
- decompose independent axes when their velocities differ

CSS transitions are acceptable for simple state changes that do not need to be
grabbed. A draggable sheet, scrubber, or thrown object needs a spring/animation
primitive that can read current position and velocity.

## Spring language

Reason in designer-facing parameters:

- **damping ratio**: `1.0` is critically damped with no overshoot; lower values
  add bounce.
- **response**: approximate time scale of the spring, not a fixed duration.

Starting points:

| Interaction | Damping | Response |
| --- | --- | --- |
| Reposition or settle | `1.0` | `0.4s` |
| Rotation or momentum response | `0.8` | `0.4s` |
| Drawer or sheet | `0.8` | `0.3s` |

Default to no bounce. Add subtle overshoot only when the user's gesture carried
momentum or the product's motion language explicitly calls for it.

## Velocity handoff and projection

The release animation starts at the finger's measured velocity. If an API uses
relative velocity:

```text
relativeVelocity = gestureVelocity / (target - current)
```

Use a projected endpoint to choose a snap target only when the product contract,
existing behavior, or runtime evidence establishes momentum-based targeting.
Do not silently replace a project-owned nearest-current-position, threshold, or
discrete slot rule merely because projection can feel more physical. When the
semantic contract is unknown, preserve target selection in an implementation
plan and list projection as a separately authorized hypothesis.

Do not omit the projection chain merely because target selection is
conditional. In a critique or audit, state the mechanical candidate with its
units and bounds:

1. measure release velocity in CSS px/s, pt/s, or dp/s;
2. compute a bounded projected endpoint from the current presentation value;
3. if momentum targeting is authorized, choose the nearest valid snap point to
   that endpoint; otherwise retain the existing target rule and use the
   projection only as a runtime experiment.

For an authorized momentum-based interaction:

```text
projection(v, d) = (v / 1000) * d / (1 - d)
projectedEndpoint = current + projection(releaseVelocity, 0.998)
target = nearestSnapPoint(projectedEndpoint)
```

Use `d` near `0.998` for scroll-like momentum or closer to `0.99` for a
snappier result. Clamp unsafe projections and keep destructive actions behind a
clear commitment threshold.

Velocity handoff and target selection are separate decisions. A settle can
start from the current presentation value and inherit bounded velocity while
still using the project's existing target-selection rule.

Naming a projected endpoint alone never satisfies velocity handoff. Measure the
release velocity with explicit units, choose the target under product-owned
semantics, then feed the measured velocity into the settle using the animation
API's required units.

## Soft boundaries and hysteresis

- Require roughly `8-12px`/pt/dp of movement before committing a drag
  direction so taps remain taps.
- Use progressive resistance beyond a boundary instead of a hard stop.
- Allow cancel-by-dragging-away and re-entry for press interactions.
- Resolve plausible gestures in parallel until intent is clear, then cancel
  losers without adding an arbitrary delay.

One useful rubber-band function is:

```text
(overshoot * dimension * constant) /
(dimension + constant * abs(overshoot))
```

Start `constant` near `0.55` and tune with real interaction evidence.

## Performance and accessibility

- Drive frame updates with the platform display clock and compositor-friendly
  properties or native transforms.
- Keep synchronous work, layout measurement, and allocation out of the gesture
  hot path.
- Test on 60 Hz and 120 Hz hardware when interaction feel is release-critical.
- Reduced Motion removes large travel, parallax, elastic overshoot, and looping
  motion while preserving causal feedback through short cross-fades, color,
  scale, or static state change.
- Reduced Transparency and increased contrast need independent material
  alternatives; they are not implied by Reduced Motion.

## Verification packet

For a gesture interaction record:

- pointer/touch-down feedback
- 1:1 tracking and grab-offset preservation
- interruption without a visual jump
- release velocity and projected endpoint behavior
- boundary resistance and cancellation
- Reduced Motion result
- runtime tool, device/simulator/browser, refresh rate when known
- screenshot/video/trace artifact path and hash when captured

Static source checks cannot prove gesture feel. If no suitable runtime is
available, report the interaction as unverified rather than "correct."
