# Claude unverified

- Host: Claude
- Date: 2026-07-12
- Status: unverified
- Reason: Claude Code `2.1.116` reports a valid OAuth login after the runner was
  repaired to retain user authentication and expose only read-only tools.
  The current-source `sonnet/high` request and prior `opus/max` attempt ended with
  `API Error: Unable to connect to API (ECONNRESET)`, so no output or run
  manifest was admitted.

Do not count Claude as verified until the controlled runner publishes a new
output/run manifest and the recorder derives a valid v3 score from that run.
