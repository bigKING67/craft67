# Motion benchmark comparison

Observed on 2026-07-11 against clean `design-craft 0.5.0` source commit
`487e45d` and skill tree `2f460d2c...`.

| Host | Status | Score | Runtime |
|---|---:|---:|---|
| Codex | verified | 97 | `codex-cli 0.144.1`, `gpt-5.6-sol`, max reasoning |
| Pi | verified | 91 | `pi 0.80.3`, `deepseek/deepseek-v4-pro`, high thinking |
| Cursor | unverified | N/A | Installed CLI is not logged in |
| Claude | unverified | N/A | OAuth status exists, but usable inference is not verified |

Codex and Pi both labeled the evidence as static, called runtime behavior
unverified, rejected `transition: all`, and proposed concrete design moves.

- **Codex** was stronger on pointer lifecycle, grab-offset preservation,
  presentation-value interruption, velocity continuity, projected endpoints,
  `fill: forwards` state drift, transform-based tracking, and acceptance tests.
  Its only material deduction was a 490-line scope-control overrun.
- **Pi** found the main direct-manipulation issues and supplied a useful runtime
  plan. Its implementation samples still animate `top`, let press scale compete
  with positional transforms, and feed `px/ms` velocity into a projection
  formula defined for `px/s`. It also labels the 480ms duration conclusively
  invalid despite citing a range that includes it.
- **Cursor** is unverified because no real Cursor run was collected.
- **Claude** is unverified because no real Claude run was collected.

The comparison demonstrates current-source Codex/Pi value without claiming
identical output, browser/device behavior, or unobserved Cursor/Claude
portability.
