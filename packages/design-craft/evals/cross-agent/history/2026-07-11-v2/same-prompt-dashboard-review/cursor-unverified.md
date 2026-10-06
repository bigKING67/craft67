# Cursor unverified

- Host: Cursor
- Version observed: `2026.07.09-a3815c0`
- Date: 2026-07-11
- Status: unverified
- Reason: Cursor Agent is now installed, but `cursor-agent status` reports
  `Not logged in`. The IDE launcher alone is not a headless Agent Skills run.
  No same-prompt Cursor output or score was collected.

Do not count Cursor as a verified cross-agent behavior host until a real Cursor
agent run records an output and score JSON for this same benchmark prompt.
