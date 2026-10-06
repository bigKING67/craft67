# Cross-agent benchmark evals

Use this directory to compare how Codex, Cursor, Claude, Pi, or another
Agent Skills-compatible client applies `design-craft` to the same prompt.

The goal is not identical prose. The goal is stable behavior:

- Reads or respects project style authority.
- Selects the relevant references without loading everything.
- Avoids generic redesign over project context.
- Produces an evidence-labeled design read or critique.
- Separates verified from unverified claims.
- Gives executable design moves when asked for implementation direction.
- Does not over-modify unrelated code.

Template directories are scaffolding only; they are not completed benchmarks.

Validate active benchmark task definitions with:

```bash
python3 scripts/design_craft_cross_agent_validate.py --root evals/cross-agent
```

The validator checks active `same-prompt-*` task directories, not `_template/`.

Observed benchmark outputs are intentionally host-specific. A host only counts
as observed after it runs the same prompt and records an output plus current
score JSON. `evidence-status.json` is the machine truth for each active host;
`comparison.md` is deterministically generated from that JSON and must remain
byte-identical, so it is a display artifact rather than a second truth source.
Markdown unverified notes are accepted only in immutable history. A partial
output/score pair, an `observed` status without artifacts, or artifacts paired
with `pending`/`unverified` status is rejected.

The score-v2, score-v3, and released `v0.5.0` score-v4 Codex/Pi tranches are
preserved under `history/`. They remain historical baseline evidence only and
are excluded from active release validation because the Skill, scorecard,
runner, version, or score contract has changed. Do not restore historical
outputs to active directories or edit their hashes; rerun the controlled host
against the final clean commit instead.

Validate the recorded runs with:

```bash
python3 scripts/design_craft_cross_agent_validate.py \
  --observed-task evals/cross-agent/same-prompt-dashboard-review
python3 scripts/design_craft_cross_agent_validate.py \
  --observed-task evals/cross-agent/same-prompt-motion-review
python3 scripts/design_craft_cross_agent_validate.py \
  --observed-task evals/cross-agent/same-prompt-native-adaptive-review
```

Require specific hosts when collecting a release-evidence tranche:

```bash
python3 scripts/design_craft_cross_agent_validate.py \
  --observed-task evals/cross-agent/same-prompt-native-adaptive-review \
  --require-host codex \
  --require-host pi \
  --require-host cursor \
  --require-host claude
```

Current evidence requires score schema v5, run-manifest schema v3, the machine
JSON scorecard, a clean task behavior domain, and a current runner/adapter
contract hash. The runner materializes only the task's Evidence Graph v2
projection in the isolated host workspace; version and release metadata remain
forensic provenance rather than behavior-current-source inputs. `make
cross-agent-four-host-check` additionally requires all
four hosts for the Certified release level and stops on the first failure:

```bash
python3 scripts/design_craft_cross_agent_validate.py \
  --observed-task evals/cross-agent/same-prompt-native-adaptive-review \
  --require-host codex \
  --require-host pi \
  --require-host cursor \
  --require-host claude
```

Capture the exact prompt and read-only invocation first:

```bash
python3 scripts/design_craft_cross_agent_run.py \
  --task-dir evals/cross-agent/same-prompt-motion-review \
  --host codex \
  --model <model> \
  --reasoning-profile <profile> \
  --skill-root skills/design-craft
```

The runner resolves the task binding in
`contracts/evaluation/evidence-graph.json`, copies that exact projection into a
repo-external isolated project skill path, records the canonical source tree,
behavior fingerprint, projected tree hash, and redacted path, runs the host
read-only, verifies a content-level source-worktree fingerprint, and only then
transactionally publishes `<host>-output.md` plus `run.<host>.json`. Do not
point a certified run at a stale user-level install.

Then create v5 score JSON with `scripts/design_craft_cross_agent_record.py` and
the generated `run.<host>.json`. Copy `_template/criteria.json`, assign each
criterion an earned value within its
scorecard weight, and preserve the exact `<host>-output.md`. The recorder
computes the score and records hashes for the prompt, JSON scorecard, output, run
manifest, behavior projection, full source tree, and runner/adapter contract
plus the source commit, version, model, reasoning profile, host version, and
runner OS. Canonical repo
paths use `$DESIGN_CRAFT_HOME`; installed host paths use a home-relative form.
Set that host to `observed` in `evidence-status.json` only after the complete
pair is admitted. Do not backfill v5 fields onto an older full-tree run.

Validate immutable history independently:

```bash
python3 scripts/design_craft_cross_agent_validate.py \
  --history-root evals/cross-agent/history
```

`make history-audit` checks both cross-agent and comparative archives. It is a
strict archival-integrity audit, but it is intentionally separate from current
portable, development-maturity, and release-source gates.
