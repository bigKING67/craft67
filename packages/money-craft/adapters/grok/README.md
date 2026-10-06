# Grok adapter

`.grok-plugin/plugin.json` declares the Grok plugin identity. Grok also supports
the standard `skills/` layout, so no host-specific prompt copy is maintained.

```bash
grok plugin validate /absolute/path/to/money-craft
python3 scripts/install_skill.py --host grok
```

Use a temporary `--target-root` for isolated installation tests.

