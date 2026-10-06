# Reverse Craft repository guidance

## Product boundary

Reverse Craft is one installable Agent Skill with internal professional modules.
Do not add nested `SKILL.md` files: `skills/reverse-craft/SKILL.md` is the only
public discovery surface.

The runtime is dependency-free Python 3.10+ and travels inside the Skill folder.
Keep generated case data outside the source tree under
`${REVERSE_CRAFT_HOME:-~/.reverse-craft}/runs` unless a caller explicitly selects
another root.

## Runtime truth

For JavaScript/browser reversing, browser67 remains the canonical browser and
MCP runtime. Reverse Craft may detect and orchestrate its `js-reverse` tools but
must not copy its session, tab, hook, or evidence runtime into this repository.

## Safety and evidence

- Treat challenge targets as authorized sandbox assets while keeping task scope explicit.
- Inspect before mutation and preserve originals; derived artifacts use separate paths.
- Every finding must cite evidence IDs; every path must cite finding IDs.
- `doctor` and `setup plan` are read-only. `setup apply` requires a saved plan,
  the plan SHA-256, and `--yes`.
- Never store credentials, cookies, tokens, or raw secrets in fixtures or logs.

## Repository work

- Use scoped staging and commits; never `git add -A`.
- Do not vendor GPL/AGPL components. Record upstream mechanism provenance in
  `THIRD_PARTY_NOTICES.md` and `skills/reverse-craft/references/provenance.json`.
- Run `npm run check:all` before delivery. Run real Codex/Pi and browser67 gates
  only when those hosts/runtimes are available; report them separately.

