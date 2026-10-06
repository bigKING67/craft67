# Codex adapter

Codex is a Tier 1 host. The repository exposes `./skills/` through
`.codex-plugin/plugin.json`; the canonical runtime remains
`../../skills/creative-craft/`.

Use Codex's built-in `skill-installer` with repository
`bigKING67/creative-craft`, ref `v0.3.0`, and path `skills/creative-craft`, or:

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo bigKING67/creative-craft \
  --ref v0.3.0 \
  --path skills/creative-craft
```

`v0.3.0` is the latest published immutable tag. The installed Skill becomes
discoverable on the next turn or session.

For a local multi-host setup whose Codex runtime discovers the shared Agents
Skill root, a repository candidate can instead be installed once for Codex and
Grok:

```bash
python3 scripts/install_skill.py --target ~/.agents/skills
```

Treat this as a candidate install until its provenance resolves to a published
immutable tag. Verify Codex discovery on the next turn or session rather than
inferring it from a successful file copy.

Provider execution still depends on available host tools and explicit
authorization; Creative Craft itself includes no network adapter.

Diagnose the installed leaf runtime without repository-only files:

```bash
python3 ~/.codex/skills/creative-craft/scripts/creative_craft.py self-test --json
```

For the shared installation, run:

```bash
python3 ~/.agents/skills/creative-craft/scripts/creative_craft.py self-test --json
```

To replace an existing shared installation after reviewing its differences and
authorizing that target, use the repository installer with `--force`. It tests
the staged leaf runtime, retains the complete old directory as a timestamped
backup, atomically publishes the new directory and records source provenance.

```bash
python3 scripts/install_skill.py --target ~/.agents/skills --force
```

On 2026-10-04 the authorized local replacement updated eight content files and
added seven, yielding 90 content files identical to development source. Backup
parity, provenance binding and the installed leaf self-test passed. This is an
unreleased 0.3.2 candidate; the published installation tag above remains v0.3.0.

The actual Codex CLI 0.160.0 app-server protocol then reported this shared
`SKILL.md` as enabled at user scope, both inside the checkout and in an external
temporary working directory. The probe used the real user configuration,
`initialize` / `initialized`, then `skills/list` with `forceReload: true`; it did
not inject extra roots or start a model turn. See the [official app-server
protocol](https://learn.chatgpt.com/docs/app-server) and local receipts
`dist/shared-skill-upgrade-2026-10-04-5bda3972/installation-receipt.json` and
`host-discovery-report.json`. Resource discovery and leaf self-tests do not
prove model prompt injection or packaged Desktop behavior. The optional image
executor, its dependencies and font binaries still reside in the source
checkout, outside the shared Skill package.
