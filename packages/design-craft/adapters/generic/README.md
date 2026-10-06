# Generic Agent Skills adapter

Use this for Agent Skills-compatible clients that understand a directory with:

```text
SKILL.md
references/
scripts/
templates/
agents/
```

Install the canonical skill by copying or symlinking:

```text
skills/design-craft/
```

into the client's skill directory as:

```text
design-craft/
```

## Contract

- `SKILL.md` is the entrypoint and should stay concise.
- Long guidance belongs in `references/`.
- Automation belongs in `scripts/` and must be optional: if a script is missing
  or unsupported by the host agent, continue manually and report skipped
  automation.
- The host project's runtime, rules, and `DESIGN.md` outrank generic references.
