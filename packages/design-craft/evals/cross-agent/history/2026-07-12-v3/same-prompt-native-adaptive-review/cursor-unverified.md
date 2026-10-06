# Cursor unverified

- Host: Cursor
- Date: 2026-07-12
- Status: unverified
- Reason: Cursor Agent `2026.07.09-a3815c0` is installed, but the current
  `cursor-agent status` result is `Not logged in`. A controlled current-source
  run cannot start until the user completes Cursor login.

Do not count Cursor as verified until the controlled runner publishes a new
output/run manifest and the recorder derives a valid v3 score from that run.
