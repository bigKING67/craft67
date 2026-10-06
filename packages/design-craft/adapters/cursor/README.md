# Cursor adapter

Use the canonical Agent Skill at `skills/design-craft/`. Cursor can consume
skills in supported environments; a tiny project rule can also make the trigger
boundary explicit without duplicating the skill.

## Project skill install

```bash
bash scripts/design_craft_init_agent.sh \
  --agent cursor \
  --target /path/to/project \
  --scope project
```

This installs to:

```text
/path/to/project/.cursor/skills/design-craft
```

## Optional always-on rule

The optional rule template lives at:

```text
adapters/cursor/.cursor/rules/design-craft.mdc
```

It should stay short. The rule should only say when to use the skill and which
project authorities outrank generic design guidance. Detailed design knowledge
belongs in `skills/design-craft/references/`.

Generate both the skill and rule with:

```bash
bash scripts/design_craft_init_agent.sh \
  --agent cursor \
  --target /path/to/project \
  --scope project \
  --with-rule
```

## Cursor-specific expectations

- Prefer the canonical skill for substantial UI/UX work.
- Keep `.cursor/rules/design-craft.mdc` as an entrypoint, not a second copy of
  the system.
- Do not use design-craft for backend-only, database-only, pure algorithm, or
  non-visual refactor tasks.
- Distinguish the `cursor` IDE launcher from the headless `cursor-agent`
  executable. The launcher existing is not observed Agent Skills evidence.
- Before a benchmark, run `cursor-agent status`; record the host as unverified
  when it is not authenticated instead of fabricating an output.
