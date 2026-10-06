# Codex adapter

Use the canonical Agent Skill at `skills/design-craft/`.

## User-level install

```bash
bash scripts/design_craft_init_agent.sh \
  --agent codex \
  --target "$HOME" \
  --scope user
```

This installs to:

```text
$HOME/.agents/skills/design-craft
```

## Project-level install

```bash
bash scripts/design_craft_init_agent.sh \
  --agent codex \
  --target /path/to/project \
  --scope project
```

This installs to:

```text
/path/to/project/.agents/skills/design-craft
```

## Codex-specific expectations

- Use project `AGENTS.md`, live runtime behavior, and project `DESIGN.md` above
  generic `design-craft` references.
- For L1+ UI work, use the local frontend route planner when available.
- For visible UI changes, use browser validation and screenshot artifacts when
  route output requires them.
- Keep `skills/design-craft/` canonical; do not fork a Codex-only copy.

## Frontend route pack

The local frontend route planner is machine-level Codex configuration under
`~/.codex`, not part of the installable skill. Keep it auditable with the route
pack helper. Its single file-list authority is
`~/.codex/tools/frontend_route_pack_manifest.json`; do not maintain a second
hard-coded route-pack list in adapter code or documentation:

```bash
python3 scripts/design_craft_codex_route_pack.py --strict
```

Export a whitelisted migration bundle when moving machines or backing up local
route policy:

```bash
python3 scripts/design_craft_codex_route_pack.py \
  --strict \
  --export-dir /tmp/design-craft-codex-route-pack
```

See `adapters/codex/route-pack/README.md` for the tracked file list, restore
validation commands, split route-module contract, current-session runtime truth
and privacy boundary, p50/p95 telemetry workflow, and screenshot evidence
policy boundary.
