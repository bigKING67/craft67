# Codex adapter

The canonical Skill is `skills/money-craft`; `.codex-plugin/plugin.json` points
Codex at the repository `skills/` directory. For a shared user install used by
Codex, Pi, and Grok:

```bash
python3 scripts/install_skill.py --host agents
```

Use `--target-root` for an isolated acceptance test. The installer never writes
credentials and refuses to replace an existing Skill unless `--force` is set.
