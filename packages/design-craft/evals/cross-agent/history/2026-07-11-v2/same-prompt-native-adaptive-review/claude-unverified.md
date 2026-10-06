# Claude unverified

Status: unverified.

Reason: Claude Code `2.1.116` reported a logged-in account, but its configured
custom API base was unreachable and this benchmark failed before inference. A
command-scoped official-endpoint override connected but returned HTTP 401 for
the existing bearer on 2026-07-11. No benchmark output or score is recorded.
