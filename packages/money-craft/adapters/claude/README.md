# Claude adapter

`.claude-plugin/plugin.json` makes the repository loadable as a Claude plugin;
the canonical Skill remains under `skills/money-craft`.

```bash
claude --plugin-dir /absolute/path/to/money-craft
python3 scripts/install_skill.py --host claude
```

The first command is suitable for temporary discovery tests. The second copies
the Skill into the user host directory only when intentionally invoked.

