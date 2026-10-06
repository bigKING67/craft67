# Claude unverified

- Host: Claude Code
- Date: 2026-07-11
- Status: unverified
- Reason: Claude Code `2.1.116` reported a logged-in account, but its configured
  custom API base was unreachable and repeatedly failed before inference.
  A command-scoped official-endpoint override connected but returned HTTP 401
  for the existing bearer. No benchmark output or score was collected.

Do not count Claude as a verified cross-agent behavior host until a real Claude
run records an output and score JSON for this same benchmark prompt.
