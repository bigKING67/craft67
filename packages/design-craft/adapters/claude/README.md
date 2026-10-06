# Claude adapter

Use the canonical Agent Skill at `skills/design-craft/`.

Claude Code supports personal and project skills with the same core shape:
`SKILL.md` plus optional supporting files such as `references/`, `scripts/`, and
`assets/`.

## User-level install

```bash
bash scripts/design_craft_init_agent.sh \
  --agent claude \
  --target "$HOME" \
  --scope user
```

This installs to:

```text
$HOME/.claude/skills/design-craft
```

## Project-level install

```bash
bash scripts/design_craft_init_agent.sh \
  --agent claude \
  --target /path/to/project \
  --scope project
```

This installs to:

```text
/path/to/project/.claude/skills/design-craft
```

## Claude-specific expectations

- Treat `design-craft` as a product UI/design-quality workflow, not a backend
  default.
- If local Codex-only helpers such as route planner or TMWD screenshot tools are
  unavailable, fall back to reference-driven review and report skipped
  automation.
- Keep browser/screenshot claims evidence-backed.
- Run `claude auth status` and a minimal headless control prompt before a
  benchmark. A configured custom API base, proxy failure, or rejected bearer is
  a host preflight failure, not a design-craft observed output.
