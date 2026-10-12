# Expected findings

- Treat all excerpts as static evidence and avoid observed smoothness claims.
- Reuse `--duration-fast`, `--duration-panel`, and `--ease-responsive` where they
  fit instead of introducing an unrelated token family.
- Remove or sharply reduce Command Palette motion because it is keyboard-heavy
  and repeatedly triggered.
- Replace popover `transition: all`, wrong origin, and delayed `ease-in` response.
- Replace toast layout-property keyframes with an interruptible transform/opacity
  strategy and a Reduced Motion alternative.
- Keep Sortable Queue tracking attached to the pointer, avoid parent CSS-variable
  fan-out, preserve presentation value and release velocity, and validate on a
  real pointer/touch runtime.
- Produce a small number of source-stamped, independently executable plans with
  exact boundaries and stop-on-drift behavior.
