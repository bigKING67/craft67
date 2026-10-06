# Review Craft

Review Craft is a portable Agent Skill for evidence-driven engineering review. It helps an
agent understand a repository, account for review coverage, validate candidate findings,
choose proportionate remediation, and preserve well-designed code instead of rewarding issue
count.

The current source version is **0.7.3**, pending formal publication. This source update
does not create a `v0.7.3` tag, GitHub Release, or npm release. For a published installation,
use an existing exact release tag or npm version rather than a moving branch.
See [CHANGELOG.md](https://github.com/bigKING67/review-craft/blob/main/CHANGELOG.md) for the 0.7.3 changes and compatibility boundary.

Version 0.7.2 rejects failed Git status reads before review or delivery evidence can claim
a clean worktree. Automatic project profiling reads only inventory-bound ordinary text
and records skipped or invalid inputs explicitly. It also refreshes selectively reviewed
upstream references without changing schemas, dependencies, or supported workflows.

Version 0.7.1 strengthens current `review-craft.run.v5` with content-bound source-span
anchors, Git-base binding for deleted source, and a coverage denominator sealed one-to-one
against the canonical inventory. It also adds evidence-backed simplification guidance,
source-bound reference-upstream governance, automatic Review Craft routing, and maintained
Node 24 CI dependencies without changing the bounded, provider-free product boundary.

## Product boundary

- `skills/review-craft/` is the only installable product.
- The same inline Skill contract is designed for Codex CLI, Claude Code, Pi, and Grok. It does
  not require subagents, agent teams, forked context, or a host-private orchestration API.
- A bounded, read-only review is the default path.
- The bundled Python runtime is optional. Use it only for an explicitly requested canonical
  review, deterministic artifact validation, authorized fix verification, or delivery
  attestation.
- Review Craft never edits a target repository. An authorized implementation uses the host's
  normal editing tools; the runtime only prepares and validates external evidence.
- Quick PRs and small diffs belong to the host's native review workflow. Visual design and
  deep security work belong to dedicated workflows.
- Review Craft does not claim that one model, host, prompt, or Skill is universally superior.

## Workflows

### Bounded review

Use the bounded path for a small, completely readable scope that needs a bounded,
evidence-backed set of findings or decisions. Several candidates may be resolved when the
checks stay narrow and relevant to that scope. It does not create canonical artifacts or a
numeric score and does not run `doctor` or `preflight` by default.

If resolving the question would materially expand its scope, narrow it or report the evidence
gap. Do not automatically upgrade the request to the canonical workflow.

Valid outcomes include `KEEP`, `CLEAN_UP`, `DEFER`, `MEASURE`, and `DOCUMENT`. A no-finding
result still needs evidence explaining why the inspected behavior is appropriate.

### Canonical review

Use the optional canonical workflow only when the user explicitly requests repository-wide
coverage, a `diff` or `focus` artifact, a deterministic score, or high-assurance evidence.
It provides:

- a Project Quality Model grounded in actual goals and non-goals;
- deterministic per-file coverage accounting;
- a candidate ledger separate from validated findings;
- independent severity and remediation priority;
- evidence-gated scoring and deterministic report generation;
- migration, compatibility, rollback, and verification gates for destructive decisions;
- immutable fix attempts and portable delivery attestations.

Canonical assurance levels remain:

- `fast`: budgeted, provisional, and capped at E2;
- `standard`: complete configured scope, validated candidates, and deterministic artifacts;
- `assured`: E3+ evidence plus independent registered verification for every finding.

### Remediation and delivery

Review findings do not authorize edits. After the user explicitly selects findings, the
runtime can bind a fix plan, capture immutable verification attempts, validate the lineage,
and attest a committed delivery. Push and GitHub Actions proof require explicit CLI options.

## Repository layout

```text
.codex-plugin/plugin.json       Codex skills-only plugin manifest
skills/review-craft/            complete portable Agent Skill and optional runtime
contracts/                      deterministic package and release policies
tests/                          runtime, safety, portability, and package contracts
benchmarks/                     deterministic runtime scale specifications
scripts/                        source validation, packaging, and release gates
```

Provider-backed model comparisons and REAL_HOST campaign infrastructure are not part of the
main repository or ordinary release gate.

## Requirements

- Any supported Agent Skills host for the bounded workflow;
- Python 3.10 or later and Git for the optional deterministic runtime;
- a writable system temporary directory for runtime artifacts;
- Node.js only for npm/Pi packaging and repository package validation.

The installed runtime has no third-party Python dependency. Repository development uses
locked tooling through `uv`.

## Install for Codex CLI

Install the complete Skill directory into one active Skill root. For a tagged release, use
the exact release tag rather than a moving branch:

```bash
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
python3 "$CODEX_HOME/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo bigKING67/review-craft \
  --path skills/review-craft \
  --ref <release-tag> \
  --dest "$HOME/.agents/skills"
```

The Codex-only root is normally `$CODEX_HOME/skills`. Do not install different versions of
`review-craft` under both `~/.agents/skills` and `~/.codex/skills`.

Invoke it explicitly:

```text
$review-craft perform a bounded evidence-driven review of this module.
```

The included `.codex-plugin/plugin.json` is an alternative Codex integration path. Plugin
installation and direct Skill-directory installation are alternatives, not cumulative
requirements.

## Install for Claude Code

Copy or symlink the complete released Skill directory to Claude Code's personal Skill root:

```bash
mkdir -p "$HOME/.claude/skills"
ln -s /absolute/path/to/review-craft/skills/review-craft \
  "$HOME/.claude/skills/review-craft"
```

Use a copy instead of a symlink when the checkout is temporary. Project-specific installation
may use `.claude/skills/review-craft/` inside the project.

Invoke it explicitly:

```text
/review-craft perform a bounded evidence-driven review of this module.
```

Review Craft uses only standard Skill metadata and relative supporting-file links. It does
not use Claude-specific `context: fork` execution.

## Install for Pi

Install the published npm package:

```text
pi install npm:@bigking67/review-craft
```

Or load the Skill directly from a trusted source checkout:

```text
pi --skill ./skills/review-craft
```

Invoke it explicitly:

```text
/skill:review-craft perform a bounded evidence-driven review of this module.
```

The npm manifest declares `pi.skills = ["skills/review-craft"]`. Pi/npm installation does
not register a second copy under a Codex or Claude Skill root.

## Install for Grok

Grok discovers the shared `~/.agents/skills` root. If Review Craft is already installed there
for Codex or Pi, do not create a second copy. Otherwise install the complete Skill directory
from the exact release tag using the Codex installation command above or another trusted
tag-pinned installer.

Confirm discovery without starting a model session:

```text
grok inspect
```

Invoke it explicitly:

```text
/review-craft perform a bounded evidence-driven review of this module.
```

## Verify the installed runtime

The complete installed directory contains:

```text
review-craft/
├── SKILL.md
├── VERSION
├── agents/
├── lib/
├── references/
├── schemas/
├── scripts/
└── templates/
```

Run `doctor` against the installed copy, not the source checkout:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 \
  "$HOME/.agents/skills/review-craft/scripts/review_craft.py" \
  doctor --json
```

For this candidate the result should include:

```json
{"ready": true, "version": "0.7.3"}
```

Adjust the path for the Codex-only or Claude installation root.

## Optional deterministic runtime

The commands below are for explicitly requested canonical work. Keep run artifacts outside
the target repository.

### Create a review

```bash
python3 skills/review-craft/scripts/review_craft.py doctor --json
python3 skills/review-craft/scripts/review_craft.py preflight --target .
```

Use an exact Git base for `diff` mode or canonical dimensions for `focus` mode:

```bash
python3 skills/review-craft/scripts/review_craft.py \
  preflight --target . --mode diff --base origin/main

python3 skills/review-craft/scripts/review_craft.py \
  preflight --target . --mode focus \
  --focus architecture,maintainability,performance
```

Generate every candidate location from the bound source instead of hand-authoring its
anchor. Reuse the returned location object unchanged in the matching finding:

```bash
python3 skills/review-craft/scripts/review_craft.py \
  anchor-location --run-dir <run-dir> --path src/example.py \
  --line-start 10 --line-end 18 --role primary
```

The command reads source without modifying the target or run artifacts. It binds the
exact raw-line span, source side, full source digest, and source line count without
storing source text in the run.

Run only configured evidence commands, then validate and finalize:

```bash
python3 skills/review-craft/scripts/review_craft.py \
  run-evidence --run-dir <run-dir> --all
python3 skills/review-craft/scripts/review_craft.py \
  validate --run-dir <run-dir>
python3 skills/review-craft/scripts/review_craft.py \
  finalize --run-dir <run-dir>
```

Do not hand-edit `report.md`; correct canonical JSON and rerun finalization.

### Verify an authorized fix

Bind the selected findings before any source edit:

```bash
python3 skills/review-craft/scripts/review_craft.py \
  prepare-fix --run-dir <sealed-run-dir> \
  --finding RC-FINDING-001 --command test
```

After the user authorizes and the host applies the scoped change, capture, assess, and
validate an immutable attempt:

```bash
python3 skills/review-craft/scripts/review_craft.py \
  capture-fix-attempt --fix-dir <fix-dir>
python3 skills/review-craft/scripts/review_craft.py \
  finalize-fix-attempt --attempt-dir <attempt-dir> \
  --assessment <assessment.json>
python3 skills/review-craft/scripts/review_craft.py \
  validate-fix-attempt --attempt-dir <attempt-dir>
python3 skills/review-craft/scripts/review_craft.py \
  list-fix-attempts --fix-dir <fix-dir>
```

Failed attempts remain immutable predecessors. A later pass may become
`VERIFIED_WITH_RETRY`; it never rewrites the first attempt.

### Verify delivery

After a verified fix has been committed, use the matching delivery path:

```bash
python3 skills/review-craft/scripts/review_craft.py \
  verify-attempt-delivery --attempt-dir <latest-verified-attempt-dir>
python3 skills/review-craft/scripts/review_craft.py \
  validate-delivery --delivery-dir <delivery-dir>
```

Local-only proof remains `PARTIAL`. `--verify-push` and `--github-run` are the only options
that authorize remote proof. GitHub Release and npm registry proof are not implemented.

## Protocol compatibility

| Workflow | Current protocol | Historical support | Write behavior |
| --- | --- | --- | --- |
| Review | `review-craft.run.v5` | sealed `run.v4` and `run.v3` validation | writes v5 only |
| Fix attempt | `review-craft.fix-attempt.v1` | n/a | immutable attempt directories |
| Legacy fix | `review-craft.fix.v1` | validation and compatibility | compatibility path only |
| Delivery | `review-craft.delivery.v2` | `delivery.v1` | writes v2 for attempt lineage |

Historical artifacts are validated under their published semantics and are never silently
upgraded or reinterpreted. See
[`protocol-lifecycle.md`](skills/review-craft/references/protocol-lifecycle.md).

Current run.v5 validation also seals the coverage denominator against the canonical source
projection: every inventory-owned field in `coverage.files` must match the live, content-
bound inventory one-to-one. Review dispositions, reasons, and evidence references remain
authorable review state. This stronger binding is not backported into frozen run.v3 or
run.v4 validation semantics.

## Development validation

Ordinary validation is deterministic and provider-free:

```bash
uv sync --locked --group dev
PYTHONDONTWRITEBYTECODE=1 uv run --locked python -m unittest discover -s tests -p 'test_*.py'
uv run --locked python scripts/validate.py
uv run --locked python scripts/complexity_budget.py
python3 scripts/package_check.py
python3 scripts/release_gate.py
npm pack --dry-run --json
```

`release_gate.py` runs complexity, tests, source and schema validation, Ruff, and one exact
installed-package E2E. It never launches Codex, Claude, Pi, a Provider, or a model.

The exact package E2E installs the tarball under an isolated temporary home, runs `doctor`,
completes canonical report finalization, validates `fast` assurance, captures an immutable
fix attempt, and verifies the target mutation boundary. CI revalidates the same package bytes
on Ubuntu, Windows, and macOS.

## Host compatibility acceptance

Static contracts prove package layout and standard metadata, not actual host invocation.
Before publishing an unqualified compatibility claim for a release candidate:

1. extract the exact same candidate package for all hosts;
2. explicitly invoke Review Craft once in Codex, Claude Code, Pi, and Grok;
3. restrict each run to read/search tools and one bounded fixture;
4. require one evidence-backed disposition and an unchanged target hash/Git state;
5. record host version, package SHA-256, date, and `PASS` or `UNVERIFIED` outside Git.

Do not compare models, repeat a matrix, or turn a timeout into a new adapter platform. If one
host cannot complete the smoke, mark that host unverified and narrow the release claim.

## Runtime scale benchmark

The deterministic benchmark remains separate from model quality:

```text
uv run --locked python scripts/benchmark_runtime.py run
uv run --locked python scripts/benchmark_runtime.py validate --result <result.json>
uv run --locked python scripts/benchmark_runtime.py compare \
  --baseline <base-result.json> --result <candidate-result.json> \
  --max-regression-percent 20
```

PR validation compares the 1k-file tier on one runner. Larger scheduled tiers are telemetry,
not cross-runner proof of a regression.

## License and provenance

Review Craft is MIT licensed. Its engineering-review design was informed by the public
Apache-2.0 project identified in `THIRD_PARTY_NOTICES.md`. Its simplification-proof
guidance selectively adapts concepts from the MIT-licensed upstreams pinned there. Review
Craft does not vendor those upstream repositories; repository-governance metadata records
the reviewed revision, source-path Git blobs, and deliberately excluded surfaces. A
`tracked` source records non-normative watch surfaces and makes no absorption or quality
claim; `selective_absorbed` records only the surfaces actually adapted into Review Craft.
Each entry covers only its listed source paths, not a complete upstream-repository audit.
Alibaba Open Code Review also informs shared eligibility decisions between fast preflight
and canonical coverage/budget validation; its filtering policy remains excluded.
Understand Anything informs absence-evidence guidance and composition tests; automated
symbol comparison, change-impact, and freshness mechanisms remain watch candidates. See the
[reference boundary](THIRD_PARTY_NOTICES.md#understand-anything) for details.
[Cloudflare security-audit-skill](https://github.com/cloudflare/security-audit-skill) is a
selectively absorbed reference upstream: candidate falsification, precise blockers, renewed
assessment after finding changes, and the distinction between structural and factual
validation inform our bounded workflow. Assured v2 content binding is independently
implemented here; the full security-audit and mandatory multi-agent workflows are excluded.
See [provenance and boundaries](THIRD_PARTY_NOTICES.md#cloudflare-security-audit-skill).
Alibaba's Git path handling also informs preservation of whitespace and protocol boundaries.
When an upstream branch advances, `contracts/upstreams.json` records the latest reviewed
revision and blobs; `THIRD_PARTY_NOTICES.md` separately preserves the original adaptation
review where it differs.
Source-checkout validation checks that lock offline. From a source checkout, check for
relevant upstream drift explicitly, outside the release gate, with:

```text
python3 scripts/check_upstreams.py --remote
```

The remote check fetches the configured branch into an isolated temporary bare repository
without checking out source. `repositoryStatus: UPDATED` with `contentStatus: CURRENT`
means the branch moved while the listed source blobs stayed pinned. Relevant new surfaces
may exist outside that list; inspect the intervening changes before declaring them unrelated.
Relevant `CURRENT` exits `0`, relevant `UPDATED` exits `1`, and an unreachable or invalid
source exits `2`.
