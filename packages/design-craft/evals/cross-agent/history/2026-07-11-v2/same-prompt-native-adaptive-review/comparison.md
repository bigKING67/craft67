# Native adaptive benchmark comparison

Observed on 2026-07-11 against clean `design-craft 0.5.0` source commit
`487e45d` and skill tree `2f460d2c...`.

| Host | Status | Score | Runtime |
|---|---:|---:|---|
| Codex | verified | 97 | `codex-cli 0.144.1`, `gpt-5.6-sol`, max reasoning |
| Pi | verified | 92 | `pi 0.80.3`, `deepseek/deepseek-v4-pro`, high thinking |
| Cursor | unverified | N/A | Installed CLI is not logged in |
| Claude | unverified | N/A | OAuth status exists, but usable inference is not verified |

Codex and Pi both resolved the platform as adaptive, treated the Evidence as
static, made simulator/emulator and hardware behavior unverified, rejected the
fixed phone canvas and broken Back behavior, and produced an intentional parity
matrix with concrete design moves.

- **Codex** was stronger on product/design authority separation, iOS versus
  Android native-trust verdicts, state recovery, exact accessibility/runtime
  boundaries, and compact/expanded validation matrices. Its deductions were
  limited to response length and some broader lifecycle architecture detail.
- **Pi** covered the major navigation, touch target, type scaling, theming,
  platform controls, motion, and adaptivity issues. It prescribed React Native
  libraries without repository evidence, overstated several runtime
  consequences, and incorrectly described 500ms as exceeding a cited 200-500ms
  range.
- **Cursor** is unverified because no real Cursor run was collected.
- **Claude** is unverified because no real Claude run was collected.

This benchmark records current-source Codex/Pi differences without treating
similar prose as the goal or claiming unobserved platform/runtime proof.
