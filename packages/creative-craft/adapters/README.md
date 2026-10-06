# Host adapters

`skills/creative-craft/` is the canonical runtime.

Host adapters may add installation notes, tool routing, or host-specific
execution, but they must not fork the skill's professional rules.

Tier 1 in `0.2.0` means package/discovery and isolated installation are tested
for Pi and Codex. Claude and Cursor adapters remain documentation-only and must
not be described as runtime-verified.

Version `0.3.0` keeps Pi and Codex as the runtime-verified Tier 1 hosts. The
`0.3.1` candidate adds Grok format/discovery verification without promoting it
to Tier 1. It does not upgrade the documentation-only Claude, Cursor, or generic
adapters to runtime-verified support.

A host adapter should declare:

- supported host/version;
- installation target;
- available image/video tools;
- whether network and cost-bearing actions require confirmation;
- artifact locations;
- unsupported capabilities;
- validation performed.

Use the generic installer with an explicit destination:

```bash
python3 scripts/install_skill.py --target /path/to/host/skills
```

For a local multi-host setup where each Agent discovers the shared Agents Skill
root, keep one canonical installation:

```bash
python3 scripts/install_skill.py --target ~/.agents/skills
```

The installer uses same-filesystem staging, validates the copied runtime,
writes install provenance, atomically replaces the destination, and retains a
backup during `--force` upgrades.

Do not hardcode private home directories or copy unrelated host state.
