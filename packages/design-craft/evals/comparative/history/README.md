# Historical comparative evidence

Historical comparative runs are immutable evidence for the exact variant
trees, runner contract, blind packet, judge, and scorecard used at collection
time. They are never searched as active cases and cannot satisfy a
current-source release gate.

Validate their internal hashes and declared historical bindings with:

```bash
python3 scripts/design_craft_comparative_validate.py \
  --history-root evals/comparative/history
```

History validation does not claim that an archived run used today's Skill
tree. Current certification requires new runs in the active case directories.

`v0.5.0/` preserves the four ablations admitted by the `v0.5.0` Operational 95
release. Active directories retain definitions only until a complete new
`v0.5.1` run is collected.

`v0.5.5/` preserves the final run/result-v3 full-tree ablations used by the
failed `v0.5.5` Operational candidate. They remain valid for that exact
full-tree execution, but cannot be transcribed into run/result-v4 causal
projection evidence.
