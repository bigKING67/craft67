# Grok adapter

Grok Build supports directory-style Skills with a `SKILL.md` entrypoint. The
canonical runtime remains `../../skills/creative-craft/`; this adapter does not
fork its professional rules.

For one shared user installation that can also be discovered by compatible
Codex environments:

```bash
python3 scripts/install_skill.py --target ~/.agents/skills
```

Verify discovery without invoking a model:

```bash
grok inspect --json | jq '.skills[] | select(.name == "creative-craft")'
```

The source path should resolve to
`~/.agents/skills/creative-craft/SKILL.md`, and `userInvocable` should be true.
The repository's optional host smoke can also exercise an isolated project
copy:

```bash
python3 scripts/host_smoke.py --json --grok-bin grok
```

The `0.3.1` candidate has discovery evidence with Grok `1.0.5`; it does not yet
claim a fresh-session creative-behavior test or Tier 1 runtime support. Reverify
after material Grok changes.

Grok image/video execution depends on host tools and explicit authorization.
Creative Craft contains no Grok Imagine adapter, credentials, or implicit
permission for networked or cost-bearing calls. Record the available tool,
actual output, model/surface identity when exposed, and unsupported capabilities
instead of inferring them from Skill discovery.
