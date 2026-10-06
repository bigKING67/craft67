# Contributing

Keep changes scoped to Review Craft's evidence-driven engineering-review workflow.
Before proposing a change:

1. Preserve `skills/review-craft/` as the canonical runtime.
2. Add tests for contract or behavior changes.
3. Add a deterministic negative contract when a rule could encourage over-review or
   unnecessary rewrites.
4. Keep the core Skill portable: do not require subagents, forked execution, or one host's
   private orchestration features.
5. Run `uv run --locked python scripts/complexity_budget.py` and
   `python3 scripts/release_gate.py` after `uv sync --locked --group dev`.
6. Do not commit real repository findings, credentials, local paths, caches, or run artifacts.

Provider-backed quality experiments are not part of ordinary development or release
validation. The final in-repository research harness is preserved in Git at `6b8c455` for
historical inspection only. Any future model comparison requires a separately authorized,
temporary research scope and external artifacts; do not restore it as a main-branch gate.

Planned features should remain in issues or roadmap text until a real implementation,
contract, and validation path exist.
