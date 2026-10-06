# Pi adapter

Use the canonical Agent Skill at `skills/design-craft/`.

Pi installations may load skills from project or user skill directories. This
adapter keeps `design-craft` portable while avoiding a Pi-only fork.

## Recommended Pi package install

For Pi, prefer installing this repository as a package instead of copying the
skill into `~/.pi/agent/skills`. This keeps `~/.pi/agent` free to be an
in-place `pi-67` checkout while this repository remains the single source for
`design-craft`.

```bash
pi install git:github.com/bigKING67/design-craft@<tag-or-commit>
```

During active local development, install the local checkout as the package
source:

```bash
export DESIGN_CRAFT_HOME=/path/to/design-craft
pi install "$DESIGN_CRAFT_HOME"
```

The package manifest exposes:

```text
skills/design-craft
```

The author's local machine may set `DESIGN_CRAFT_HOME` to the active checkout.
Do not rely on an example absolute path from another machine.

## Direct user-level copy install

Use this only when you intentionally want to copy the skill into a host-specific
skill root. If `~/.pi/agent` is itself a Git checkout, this can dirty that
checkout and is not the recommended Pi path.

```bash
bash scripts/design_craft_init_agent.sh \
  --agent pi \
  --target "$HOME" \
  --scope user
```

This installs to:

```text
$HOME/.pi/agent/skills/design-craft
```

## Project-level install

```bash
bash scripts/design_craft_init_agent.sh \
  --agent pi \
  --target /path/to/project \
  --scope project
```

This installs to:

```text
/path/to/project/.pi/skills/design-craft
```

## Package note

If distributing as a Pi package, package metadata should point to the canonical
`skills/design-craft/` folder and should not duplicate the references. Keep
agent-specific instructions in this adapter.

## Pi-specific expectations

- Keep capability claims truthful to the current Pi runtime and tool namespace.
- If browser or screenshot tools are unavailable, report that validation was not
  performed instead of claiming it.
- Use project rules and `DESIGN.md` above generic references.
