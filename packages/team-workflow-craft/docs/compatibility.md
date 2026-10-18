# Host compatibility

Team Workflow Craft packages one portable Agent Skill directory. The artifact
contains `SKILL.md`, its runtime `scripts/`, references/assets when present,
and injected `VERSION` and `LICENSE`. It does not contain a link back to the
craft67 checkout. Each host installation is a separate, explicit project-local
copy; an artifact being built or installed does not prove a host loaded it in a
current session.

| Host | `install.py --project` destination | Explicit invocation | Native discovery on macOS, 2026-10-16 |
| --- | --- | --- | --- |
| Codex 0.162.1 | `.agents/skills/team-workflow-craft/` | `$team-workflow-craft` | `PASS`: native prompt-input catalog resolves to the project installation. |
| Claude Code 2.1.296 | `.claude/skills/team-workflow-craft/` | `/team-workflow-craft` | `PASS`: native initialization lists the command with project scope. |
| Pi 1.1.0 | `.agents/skills/team-workflow-craft/` | `/skill:team-workflow-craft` | `PASS`: native RPC lists the skill and exact project source path. |

The destinations are project-relative. The installer has no default target and
rejects global installation paths. It never updates a host profile, account,
settings file, hook, or running session.

## Session acceptance: `resume` from a teammate's branch (0.2.0, 2026-10-18)

A synthetic project committed the Codex and Claude skill copies (members install
nothing). Alice prepared `pr:8`, verified, handed off, committed the task
directory, then made one more commit, so her evidence no longer matched the
code. Each host started a fresh, read-only, non-interactive session in its own
`git clone -b alice/subtract` with no `.team-workflow/local/`, and got the same
prompt: report the previous handoff's next step, which acceptance criteria are
open and why, and the first thing to do.

| Host | Command | Result |
| --- | --- | --- |
| Claude Code 2.1.296 | `claude -p`, tools limited to the skill CLI plus Read/Glob/Grep | `PASS`: loaded the project skill, ran `resume` first (6 turns) |
| Codex 0.163.0 | `codex exec --sandbox read-only --ephemeral` | `PASS`: read `SKILL.md`, ran `resume` and the `verify` preview |
| Pi 1.1.0 | `pi -p --no-session --tools read,bash` | `PASS`: read `SKILL.md`, ran `resume` and the `verify` preview |

All three quoted the handoff's next step, reported AC-1 as pending because the
evidence was recorded for older code (not a failed test), AC-2 as needing human
review, and named `verify: unit` as the first step. No clone was modified.
Artifact: `team-workflow-craft-0.2.0.zip`, SHA-256
`1e9fe3d4b8f6aaa656d221113334324e684c94643466ed32cc3b8c9d2e9430ea`, macOS 27 arm64.

The first round failed in all three hosts: `base_ref = "main"` did not resolve in
a branch-only clone that has `origin/main` but no local `main`. The models worked
around it, but the tool was wrong. `resolve_base` now falls back to the single
remote-tracking branch, reports `base_ref_resolved`, and `doctor --local` checks
it. After the passing round, check states that have records for older code were
renamed from `missing` to `stale` because one model read `missing` as "never
ran"; this changes labels only.

Limits: one synthetic task with synthetic identities and the hosts' default
models. This does not replace a real multi-member pilot with real platform
accounts, PRs and review.

## Discovery acceptance and limits

The above checks used macOS 27.0.1 arm64, temporary Git projects, and the same
v0.1.3 ZIP with SHA-256
`665eef181d93c2844cb843075152bbfd977bdc20b8b53168d9ee1d40c745aa65`.
Each installation came from the fixed artifact, not a link to the source tree.
The temporary projects and probe processes were removed after the checks.

The probes exercised the installed host loaders without sending a model task:

- Codex: `codex debug prompt-input '$team-workflow-craft'`. The native catalog
  uses root aliases; resolve the listed skill path through its root mapping and
  compare it with the project installation. The literal user mention alone is
  not discovery evidence. This debug command is specific to the tested version.
- Claude Code: a stream-JSON `initialize` control request returned
  `team-workflow-craft` with a `(project)` description. The probe used an isolated
  config directory, project-only settings, disabled hooks, an empty strict MCP
  configuration, and no user prompt. It did **not** use `--bare`: that mode skips
  normal skill auto-discovery. [Claude Code programmatic usage](https://code.claude.com/docs/en/headless#start-faster-with-bare-mode)
- Pi: native RPC `get_commands` returned `skill:team-workflow-craft` with
  `source: skill`, project scope and the installed `SKILL.md` path;
  `get_messages` returned an empty conversation. The probe used isolated agent
  state, offline mode, and disabled extensions/MCP, with no `prompt` request.

These are **metadata discovery** results. Full Skill-body invocation, model-led
`doctor` / `prepare` / `verify` / `handoff`, real cross-person handoff and other
OS/host versions remain `UNVERIFIED`. They do not certify the user's existing
sessions or other members' installations. No paid model task, company code, or
company platform credentials were supplied to these probes. Package runtime
checks and real platform API acceptance remain separate evidence.

Native Windows verification is intentionally incomplete in v0.1: the runner
cannot certify process-tree completion and records
`incomplete / process_tree_completion_unverified` rather than `passed`.
Use a POSIX development/CI environment for the complete verification workflow;
native Windows installation, discovery and process-tree support require a
separate platform acceptance pass. POSIX group checks do not certify commands
that deliberately daemonize or escape their process group.

## What the checked paths mean

OpenAI’s current guidance describes repo-local skills under `.agents/skills/`,
with `SKILL.md` plus optional scripts, references, and assets. It also describes
progressive loading, so a file path is not proof that an already-running Codex
session has discovered the Skill. [OpenAI: Build skills](https://learn.chatgpt.com/docs/build-skills)

Claude Code documents project skills at `.claude/skills/<name>/SKILL.md` and
direct invocation as `/<name>`. Claude Code’s own discovery, configuration, and
session state remain outside this package. [Claude Code: Extend Claude with
skills](https://code.claude.com/docs/en/skills)

Pi documents `.agents/skills/` as a supported project location and
`/skill:name` as the explicit command. It scans locations at startup, so a
real Pi acceptance check must inspect the startup diagnostics or invoke the
skill after installation. [Pi skills documentation](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/skills.md)

## Fixed artifact contract

`python3 scripts/build.py --output-dir <directory>` writes only to the
specified directory:

```text
team-workflow-craft-<VERSION>.zip
team-workflow-craft-<VERSION>.zip.manifest.json
```

The JSON sidecar is `team-workflow-craft.artifact.v1`. It records the artifact
filename, artifact SHA-256, archive prefix, version, and SHA-256/size for every
runtime source file. Python bytecode caches are excluded. The ZIP has a fixed entry order, timestamps, permissions, and
compression settings for reproducible builds with the same Python/zlib toolchain.

`python3 scripts/install.py --artifact <zip> --project <project> --host
<codex|claude|pi>` is a dry run unless `--apply` is present. `--target
<skill-path>` is available for an exact non-global target. Installation checks
the ZIP and sidecar, rejects traversal, symlinks, unexpected or missing files,
and only permits a byte-for-byte identical known installation to be reused. A
drifted or unknown target is never overwritten. A known, unchanged older
installation needs both `--allow-upgrade` and `--apply`; the installer stages
the new directory before replacing the known target.

The generated `.twc-install.json` is an installation marker. It identifies the
artifact and manifest digests, but does not claim the artifact was released,
the host loaded it, or a session invoked it.
