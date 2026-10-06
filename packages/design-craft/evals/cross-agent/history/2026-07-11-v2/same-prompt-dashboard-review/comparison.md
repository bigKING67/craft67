# Same-prompt dashboard review comparison

## Summary

Observed on 2026-07-11 against clean `design-craft 0.5.0` source commit
`487e45d` and skill tree `2f460d2c...`. Codex and Pi have current-source v2
records; Cursor and Claude remain explicitly unverified.

| Host | Status | Score | Notes |
|---|---:|---:|---|
| Codex | verified | 96 | `codex-cli 0.144.1`, `gpt-5.6-sol`, max reasoning; strongest on decision hierarchy and verification boundaries, with a material scope-control deduction. |
| Pi | verified | 93 | `pi 0.80.3`, `deepseek/deepseek-v4-pro`, high thinking; strong exception-first redesign, but its exact L0 score and a few omission-based claims were overconfident. |
| Cursor | unverified | N/A | `cursor-agent` is installed but not logged in; no current-source output exists. |
| Claude | unverified | N/A | CLI reports OAuth state, but a usable inference response has not been verified; no current-source output exists. |

## Common behavior

- Both verified hosts treated the task as L0 prompt-only evidence.
- Both diagnosed the 12-card KPI grid as card soup rather than a decision
  surface.
- Both rejected the decorative chart and generic right rail as weak operational
  fit.
- Both proposed executable design moves: lead/support/action queue, task-first
  table, diagnostic chart, contextual rail, and semantic state color.
- Both avoided claiming browser, responsive, focus, loading, empty, or error
  behavior as verified.
- Codex used the stronger score-band and prompt-attested/unverified split, but
  expanded to 491 lines. Pi was shorter, while its exact `35/100` score from
  prose-only evidence and several absent-versus-undescribed claims reduced its
  evidence and verification scores.

## Boundary

This comparison supports current-source Codex/Pi dashboard behavior only. It
does not certify Cursor or Claude, rendered dashboard quality, browser states,
responsive behavior, accessibility, or production implementation quality.
