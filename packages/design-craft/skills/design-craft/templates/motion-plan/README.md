# Motion plan template

Use `plan.md` for one self-contained animation or interaction-motion change.
The plan is an execution contract, not evidence that the change was implemented.

Prefer the scaffold helper:

```bash
python3 scripts/design_craft_motion_plan.py \
  --target /path/to/project \
  --title "Retarget the sheet from its presentation value" \
  --severity P1 \
  --category interruptibility
```

The helper writes under `plans/motion/` by default and stamps the current Git
commit when available. Replace every angle-bracket instruction with real
source-backed content before asking another agent to execute the plan.
