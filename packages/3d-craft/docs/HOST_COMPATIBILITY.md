# Host compatibility

3D-Craft follows the Agent Skills directory and frontmatter conventions. It
does not configure model accounts, providers, authentication, or global host
settings. Installing the Skill is a file-discovery operation.

Maintainers may verify two independent stages:

1. **Installation and discovery** proves that a host lists or expands
   `3d-craft` from the exact candidate path. This is the required installation
   acceptance boundary.
2. **Invocation smoke** optionally proves that an already-working host returns
   a response after expanding the Skill. This is maintainer release evidence,
   not a 3d-craft setup requirement.

The Skill and its scripts must never inspect or modify host credentials or
global provider configuration. If the host cannot run an ordinary model prompt,
record the optional invocation smoke as `BLOCKED: host runtime unavailable` and
troubleshoot the host separately. A model response does not prove that the
candidate Skill was the source unless discovery or expanded-prompt evidence
identifies its exact path.

## Deterministic discovery receipt

Use the repository development tool to verify all three hosts without running
a model:

```bash
receipt_dir="$(mktemp -d /tmp/3d-craft-host-discovery.XXXXXX)"
python3 scripts/host_discovery.py \
  --skill-root "$HOME/.agents/skills/3d-craft" \
  --workspace /absolute/path/to/target-project \
  --output "$receipt_dir/host-discovery.json" \
  --json
```

The command checks only these read-only discovery surfaces:

- Codex `debug prompt-input`;
- Pi offline RPC `get_commands`;
- Grok `inspect --json`.

It requires every discovered Skill path to resolve to the supplied candidate,
records the candidate tree digest and host versions, and fails closed on a path
mismatch. A missing host is `UNVERIFIED`. Its receipt explicitly records model
invocation as `NOT_RUN`, credential access as `NOT_REQUESTED`, and configuration
mutation as `NOT_RUN`.

## Isolated project setup

Use a disposable workspace and point `.agents/skills/3d-craft` at the candidate
under test. Do not replace a global install merely to run a smoke test.

```bash
smoke_root="$(mktemp -d /tmp/3d-craft-host-smoke.XXXXXX)"
mkdir -p "$smoke_root/.agents/skills"
ln -s "$PWD/skills/3d-craft" "$smoke_root/.agents/skills/3d-craft"
```

Use `scripts/host_discovery.py` to record the candidate tree digest and host
versions. When the optional invocation smoke is run, record its command,
selected provider/model, result, and any host-runtime blocker separately. Never
write credentials to either report.

## Codex

Verify discovery with Codex's prompt-input or Skill inspection surface. For an
optional maintainer invocation smoke, invoke the project Skill as `$3d-craft`
from a host that can already run ordinary prompts. 3d-craft requires no
additional host setup.

## Pi

Pi registers this Skill as `/skill:3d-craft`. Deterministic discovery can use
RPC `get_commands`; the returned item must have `name=skill:3d-craft` and
`source=skill`.

For an optional reproducible maintainer smoke, select a provider and model that
are already configured in Pi:

```bash
pi --print --no-session --offline \
  --provider <provider> --model <model> --thinking off \
  --skill "$PWD/skills/3d-craft/SKILL.md" \
  --no-extensions --no-prompt-templates --no-context-files --no-tools \
  '/skill:3d-craft Host smoke only: identify the loaded Skill in one line.'
```

Do not rely on Pi's last-selected session model for release evidence. If an
invocation is empty or hangs, repeat the same short prompt without any Skill on
the same provider and model. An identical failure is a host-runtime blocker,
not a Skill installation failure. A different provider is a separate optional
invocation condition and must be reported as such.

## Grok

Verify that Grok resolves `.agents/skills/3d-craft/SKILL.md`, then invoke the
project command `/3d-craft` with a one-line route smoke. Record discovery and
invocation independently, as with the other hosts.

## Result language

- `PASS`: the stated stage ran and produced its receipt.
- `BLOCKED`: the optional invocation smoke could not run because the host
  runtime was unavailable.
- `UNVERIFIED`: the stage was not run or did not produce decisive evidence.

Never convert a `PASS` on one provider, model, host version, or candidate path
into a claim about another. Discovery PASS remains valid installation evidence
when the optional invocation smoke is `BLOCKED` or `UNVERIFIED`.
