# Expected findings

At minimum, a strong result should identify:

- `animating` blocks interruption and contradicts direct manipulation.
- Pointer capture, grab offset, movement threshold, and pointer cancellation are
  missing.
- Updating and animating `top` creates layout work; positional motion should use
  a single transform owner.
- `transition: all` conflicts with imperative animation and animates unrelated
  properties.
- `fill: forwards` can leave logical and presentation state divergent.
- Nearest-point snapping ignores release velocity and projected intent.
- Release velocity units must match the projection/spring API.
- Reduced Motion needs a gentler state transition, not missing feedback.
- Runtime proof requires pointer traces, interruption/reversal, frame timing,
  narrow viewport, keyboard/focus, Reduced Motion, and real touch input.
