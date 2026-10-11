# Expected findings

- Judge whether motion should exist before tuning it.
- Flag `transition-all`, layout-property animation, scale-to-zero, or missing
  reduced-motion path where present.
- Separate causality/continuity motion from decoration.
- Flag the `animating` input lock, missing pointer capture/grab offset,
  `top`-based per-frame layout work, and target choice from release position
  without velocity projection.
- Require presentation-value interruption, measured release velocity, velocity
  handoff, projected snap target, hysteresis, and rubber-band resistance.
- Avoid claiming runtime timing or performance without browser evidence.
