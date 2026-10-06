# Historical cross-agent evidence

Historical snapshots are immutable evidence for the exact prompt, scorecard,
Skill tree, and runner contract used at collection time. They are excluded
from active release validation and cannot satisfy current-source gates.

`2026-07-11-v2/` preserves the former Codex/Pi outputs, v2 scores,
comparisons, unverified Cursor/Claude notes, and the matching old prompt,
scorecard, and expected findings for all three benchmark tasks. Do not update
their hashes to match a newer active prompt; run the active case again instead.

`2026-07-12-v3/` preserves the later score-v3/run-v2 tranche that was current
before the scorecard JSON and score-v4 contracts were introduced. `v0.5.0/`
preserves the score-v4/run-v2 Codex and Pi tranche admitted by the `v0.5.0`
Operational 95 release. Validate all archived tranches separately with:

`v0.5.4/` preserves the final score-v4/run-v2 Codex and Pi tranche collected
against the `0.5.4` behavior source. It is archived before the Evidence Graph
v2 projection transition and cannot be relabeled as score-v5 evidence.

```bash
python3 scripts/design_craft_cross_agent_validate.py \
  --history-root evals/cross-agent/history
```
