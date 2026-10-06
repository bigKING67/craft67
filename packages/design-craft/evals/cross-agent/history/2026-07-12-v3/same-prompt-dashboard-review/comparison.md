# Current comparison

| Host | Status | Score | Requested runtime | Evidence |
| --- | --- | ---: | --- | --- |
| Codex | verified | 96 | `gpt-5.6-sol` / `max` | `codex-output.md`, `run.codex.json`, `score.codex.json` |
| Pi | verified | 100 | `codex/gpt-5.5` / `high` | `pi-output.md`, `run.pi.json`, `score.pi.json` |
| Cursor | unverified | - | unavailable | `cursor-agent status` returns `Not logged in`. |
| Claude | unverified | - | `sonnet/high` current attempt | OAuth is valid, but the controlled request ended with `ECONNRESET`; no output or run manifest was admitted. |

These are current-source v3 scores bound to Skill source commit `f04e105` and
recorded on 2026-07-12. Historical Codex/Pi
v2 evidence remains under
`evals/cross-agent/history/2026-07-11-v2/same-prompt-dashboard-review/` and is
not used for current certification.
