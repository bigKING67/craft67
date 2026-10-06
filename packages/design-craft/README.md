# design-craft

Web-first product design engineering, UI/UX, visual taste, motion, and
implementation-quality workflow for desktop and browser products, with
optional iOS, Android, and adaptive guidance when the target is genuinely
native.

`design-craft` is the canonical local fusion layer for high-quality product
experience work on this machine. It supersedes the former `frontend-craft`
name because the workflow now covers more than frontend code: product context,
UI/UX judgment, design-system contracts, motion craft, product taste,
implementation quality, runtime evidence, and long-term project
structure. It keeps scoped project rules, optional `PRODUCT.md`, project
`DESIGN.md`, and live runtime evidence above generic guidance, then folds in:

- anti-slop visual judgment, brief inference, and aesthetic pressure absorbed
  into `design-craft`.
- Impeccable-style audit, polish, harden, optimize, detector, and live-iteration
  loops.
- Design-system contract checks for `DESIGN.md`, token roles, light/dark parity,
  component states, focus, motion, and UI copy.
- Two-level system-consistency review: a lightweight semantic-family,
  same-state, and theme closeout for every visible UI change, plus full
  `system-review` inventories and explicit sign-off for project-level work or
  known consistency regressions.
- Optional `prototype` divergence: explore one bounded UI piece through
  genuinely different product-relevant axes on an isolated surface, verify one
  full-size interactive variant at a time, and wait for explicit selection
  before production promotion and default cleanup.
- Emil Kowalski-style motion purpose, frequency, timing/easing, physicality,
  interruptibility, gesture, performance, reduced-motion, and animation
  vocabulary checks.
- Optional iOS HIG/native-trust, Android Material 3/predictive Back/inset, and
  adaptive shared-versus-platform-specific checks, loaded only for native
  targets.
- Bundled original light/dark `DESIGN.md` seed templates for new or weakly
  specified developer-product surfaces.
- Project quality gates for architecture, performance, code elegance, validation,
  and file/directory structure governance.
- A bounded visual-reference intelligence layer that turns mutable discovery
  sources into reviewed Reference Cards and task-specific Reference Packs
  without copying third-party assets or overriding project authority.
- Repo-external Shadow Labs and comparison closeouts that bind distinct
  fixed-commit variants, shared acceptance rules, runtime evidence, and
  `absorb | adapt | reject | unverified` decisions without authorizing edits to
  the real target repository.
- A sealed-rendition gate that verifies fixed-commit or manifest authority
  before capture, emits an ordered browser/PDF contract, strictly validates
  comp evidence, audits source mutation, and keeps pixel metrics separate from
  the explicit visual decision.

The skill is intentionally personal and local-first. For dashboards, special
reports, and similar business surfaces, scoped project rules, live
runtime behavior, and project `DESIGN.md` always outrank generic visual rules.
Ordinary computer development therefore follows the Web/desktop path. Native
references exist so the same design-engineering baseline can handle a real
iOS, Android, React Native, Flutter, or Kotlin Multiplatform product without
mistaking mobile Web for native; they do not add a device requirement to daily
Web work.
The canonical package is still portable: agent-specific integration belongs in
`adapters/`, while `skills/design-craft/` remains the single source skill.
The `0.7.0` development contract defines an `operational_95` release level for
Codex/Pi and Simulator/Emulator current-source evidence, benchmark regression,
clean-checkout provenance, and repository governance. It reserves
`certified_100` for the additional Cursor, Claude, and physical-device proof.
These names are release evidence tiers, not composite product-quality scores.
Evidence Graph v2 binds behavioral evaluations to exact task-specific Skill
projections while keeping performance, native runtime, and release metadata in
separate domains. Runtime and release evidence still retain exact commit,
workflow, fixture, and artifact bindings; a domain fingerprint never replaces
those stronger identities.

## Layout

```text
design-craft/
├── AGENTS.md                    # Agent-facing repository maintenance boundaries
├── skills/design-craft/          # Only installable/published runtime product
├── adapters/                     # Thin Codex/Cursor/Claude/Pi/generic adapters
├── tools/design_craft/           # Repository governance and release tooling
├── contracts/                    # Machine-readable schemas and policy truth
├── tests/                        # Unit, contract, integration, adversarial tests
├── benchmarks/                   # Reproducible measurements and baselines
├── scripts/                      # Compatibility CLIs and platform runners
├── evals/                        # Specs, fixtures, current evidence, history
├── upstreams/                    # Pristine upstream submodules; do not edit
├── docs/                         # Architecture, operations, and security docs
├── .github/workflows/            # Validation, native, audit, and CodeQL lanes
└── VERSION                       # Local release version
```

`skills/design-craft/` should stay lean. Repo-level documents such as this
README, the changelog, and maintenance notes belong at the repository root or in
`docs/`, not inside the installed skill folder.

This repository is not a UI target. It intentionally provides neither a root
`PRODUCT.md` nor `DESIGN.md`; target projects may add `PRODUCT.md` for
product/platform context and must provide `DESIGN.md` or an explicit
`--style-authority-path` for L1+ visual route/preflight checks.

## Install locally

Repository automation is verified on macOS and Linux. The current-source
Windows Git Bash portability lane is also part of `Validate` and has completed
successfully; this proves the repository scripts, not a native Windows UI
runtime. WSL remains a compatible fallback rather than a separate product
platform claim.

```bash
bash scripts/install_local.sh
```

The installer stages and validates the complete skill, takes an install lock,
atomically replaces the active copy, restores the previous target on failure,
records `.design-craft-install.json` version/commit/tree-digest provenance,
explicit `development | release_candidate | released` state, separate
`skill_source_dirty` and `repo_dirty` states, and retains the newest
ten backups by default. Install parity is scoped to the installed skill tree,
so unrelated benchmark WIP or later ancestor commits do not invalidate an
unchanged installation. The verifier also reconstructs the skill tree at the
recorded source commit, preventing metadata from naming an ancestor that never
contained the installed content. Certified releases still require a clean
whole repo.
It syncs:

```text
skills/design-craft -> ${DESIGN_CRAFT_SKILL_ROOT:-$HOME/.agents/skills}/design-craft
```

This checkout is the canonical source for the active
`~/.agents/skills/design-craft` copy. The installed copy is deliberately not a
symlink and there is no background watcher or automatic hot update. The safe
sync sequence is: detect upstream drift, review and pin/absorb it, commit a
clean source tree, pass the gates, then run the atomic installer. `make
sync-status` detects a stale install without modifying it; do not install a
dirty development tree merely to make the status green.

Verify source parity and install provenance:

```bash
python3 scripts/design_craft_install_verify.py \
  --source skills/design-craft \
  --installed "${DESIGN_CRAFT_SKILL_ROOT:-$HOME/.agents/skills}/design-craft" \
  --expected-name design-craft \
  --expected-version "$(cat VERSION)" \
  --require-metadata
```

Check the canonical checkout, cached/live GitHub origin, canonical install,
separate Codex route-pack authority, and reviewed external upstreams without
changing them:

```bash
make sync-status
make sync-status-remote # also checks live origin and mutable upstream heads
```

The former `frontend-craft` product surface has been removed. The installer
does not create, inspect, refresh, or delete that name. Existing copies are
outside the v0.5 runtime boundary and must be reviewed and retired separately.
See `docs/operations/v0.5-migration.md`.

Override retention with `--keep-backups <count>` or
`DESIGN_CRAFT_BACKUP_KEEP`; use `--no-prune-backups` for an explicitly
non-destructive maintenance run. `make publish-local` forwards optional
installer flags through `INSTALL_ARGS`.

## Install as a Pi package

For Pi, prefer package installation over copying into `~/.pi/agent/skills`:

```bash
pi install git:github.com/bigKING67/design-craft@<tag-or-commit>
```

For local development, use the checkout path:

```bash
export DESIGN_CRAFT_HOME=/path/to/design-craft
pi install "$DESIGN_CRAFT_HOME"
```

The `package.json` `pi.skills` manifest exposes only the canonical
`skills/design-craft` skill. This keeps `pi-67` as the Pi configuration repo
while `design-craft` remains the single source skill.

The npm package boundary is also explicit: `package.json.files` includes only
the canonical skill, root version/readme metadata, and required license/notice
files. It excludes upstream checkouts, evals, workflows, and repository-only
maintenance scripts. Verify the packed payload and size budget with:

```bash
make package-check
```

The gate caps the package at 1 MB compressed, 2 MB unpacked, and 100 files,
rejects repository-only paths, and scans packed text for user-home paths.
The broader public-repository gate also rejects workstation-specific macOS,
Linux, and Windows user-home paths anywhere outside pristine upstream
submodules:

```bash
make public-repo-check
```

GitHub Actions and npm metadata updates are tracked separately through
`.github/dependabot.yml`; action executions remain pinned to reviewed full
commit SHAs.

Security reports, trust boundaries, contribution contracts, and the detailed
threat model are documented in [`SECURITY.md`](SECURITY.md),
[`CONTRIBUTING.md`](CONTRIBUTING.md), and
[`docs/security/threat-model.md`](docs/security/threat-model.md). Code scanning
runs in the pinned `.github/workflows/codeql.yml` workflow; ownership defaults
are declared in `.github/CODEOWNERS`.

Validate workflow pins, concurrency/timeouts, native fixture manifests, real
iOS deep-link routing and system-confirmation recovery, Android dialog
recovery, and compile-smoke coverage independently. The dedicated
dependency-free lint and contract-test lanes are also runnable locally:

```bash
make lint
make contract-tests
make workflow-check
```

## Agent adapters

Install the same canonical skill into a host-specific location:

```bash
bash scripts/design_craft_init_agent.sh --agent codex --target /path/to/project --scope project --dry-run
bash scripts/design_craft_init_agent.sh --agent cursor --target /path/to/project --scope project --with-rule --dry-run
bash scripts/design_craft_init_agent.sh --agent claude --target /path/to/project --scope project --dry-run
bash scripts/design_craft_init_agent.sh --agent pi --target /path/to/project --scope project --dry-run
bash scripts/design_craft_init_agent.sh --agent generic --target /path/to/project --scope project --dry-run
```

Adapter notes live under:

```text
adapters/codex/
adapters/cursor/
adapters/claude/
adapters/pi/
adapters/generic/
```

Run a portability check without modifying files:

```bash
bash scripts/design_craft_doctor.sh --target . --json
```

Audit or export the local Codex frontend route tools as a whitelisted migration
bundle. This does not copy arbitrary `~/.codex` state; it records only the
route planner, inherited frontend worker, frontend rules, preflight contract,
and related tests selected by the single
`~/.codex/tools/frontend_route_pack_manifest.json` authority. The strict audit
also validates manifest/snapshot coverage, the routing JSON Schema, split
worker Python cores, browser/runtime tool parity, V2 delegation semantics,
dedicated authority/browser/delivery/runtime/telemetry modules, and redacted
runtime model/reasoning profiles against the bundled Codex model catalog. Current
Codex session evidence reads only the latest `turn_context.model/effort`, while
strict audits disable session discovery and route telemetry writes. Privacy-safe
route history exposes p50/p95/max latency and bounded routing distributions.
GPT-5.6 `ultra` is actively probed as a denied unapproved runtime conflict
because it includes automatic task delegation; explicit main-owned frontend
overrides stop at `max`:

```bash
python3 scripts/design_craft_codex_route_pack.py --strict
python3 scripts/design_craft_codex_route_pack.py \
  --strict \
  --export-dir /tmp/design-craft-codex-route-pack
```

Route-pack details live under `adapters/codex/route-pack/`.

## Default design seed

For new or weakly specified developer-product, SaaS, dashboard, admin, infra,
docs, and tooling surfaces, start from the bundled original templates:

```text
skills/design-craft/templates/developer-product/design.md
skills/design-craft/templates/developer-product/design.dark.md
```

When a project already has a credible `DESIGN.md`, token system, brand guide, or
strong runtime visual language, use these files as the comparison baseline
rather than replacing project authority blindly.

Seed a project directly with:

```bash
bash skills/design-craft/scripts/design_craft_seed_design.sh --target /path/to/project
```

The helper refuses to overwrite an existing `DESIGN.md` or `DESIGN.dark.md`
unless `--force` is explicit.

## Product and platform authority

`PRODUCT.md` is optional and owns product facts:

- register, platform, users, purpose, positioning, and accessibility

`DESIGN.md` remains the only visual authority:

- typography, color, spacing, components, themes, iconography, and motion

Platform resolution is deterministic:

```text
explicit --platform
> nearest PRODUCT.md ## Platform
> codebase detection
> default web
```

`surface=mobile` is not a native signal. Capacitor, Cordova, and HTML WebView
shells remain `web`; React Native/Expo, Flutter, KMP, and repositories with
real iOS plus Android targets resolve to `adaptive`. Missing `PRODUCT.md`
does not block existing projects; the route reports inferred source,
confidence, signals, and contradictions.

## Validate

Portable gate for a fresh clone or another machine:

```bash
make validate-portable
```

Deterministic source gate and development maturity:

```bash
make release-gate-source
make maturity-development
```

Equivalent direct commands:

```bash
bash scripts/validate.sh --portable
python3 scripts/design_craft_active_scope_validate.py --root .
python3 scripts/design_craft_score.py --self
python3 scripts/design_craft_maturity.py --profile development
bash skills/design-craft/scripts/design_craft_pass.sh --target . --mode audit --skip-route
```

The source scorer's 100 is contract completeness only. Maturity v2 does not
calculate a partial composite score: every required gate either passes or the
selected profile fails. `development` verifies source, runtime, package,
workflow, evaluation-definition, installer, and governance contracts without
promoting historical evidence to current proof. Portable CI exercises Ubuntu,
macOS, and Windows with the declared Node/Python matrix rather than treating one
runtime as cross-platform proof.

For a release-oriented view, report the independent quality domains without
turning them into another aggregate score. A release profile remains
`incomplete` until its current evidence and matching benchmark baseline exist:

```bash
python3 -m tools.design_craft quality \
  --level operational_95 \
  --baseline <committed-matching-runner-baseline> \
  --json
```

Release levels are explicit. `operational_95` requires Codex, Pi, current-source
iOS Simulator and Android Emulator evidence, a current comparative evaluation,
benchmark regression, a clean checkout, installed provenance, and live upstream
review. Cursor, Claude, and physical-device status remain explicitly unverified.
`certified_100` strictly adds those two hosts and physical-device evidence. The
numbers name release evidence levels; they are not repository-wide quality
scores.

## Common commands

Route a frontend task through the local Codex route planner:

```bash
bash skills/design-craft/scripts/design_craft_route.sh \
  --target /path/to/project \
  --surface mobile \
  --intent visual-refine \
  --scope page \
  --platform auto \
  --product-context-path /path/to/project/PRODUCT.md
```

Detect platform or run conservative native/adaptive static checks:

```bash
python3 skills/design-craft/scripts/design_craft_platform_scan.py \
  --target /path/to/project \
  --platform auto \
  --mode scan \
  --json
```

Static platform findings are review evidence only. They do not prove an iOS
Simulator, Android Emulator, or real-device run.

Run a critique/audit/prototype/system-review/polish/harden/optimize/structure/
architecture pass:

```bash
bash skills/design-craft/scripts/design_craft_pass.sh \
  --target /path/to/project \
  --mode critique
```

Every visible UI change uses the lightweight closeout in
[`system-review.md`](skills/design-craft/references/system-review.md). Run the
full mode for whole-product or multi-page reviews,
design/visual/interaction/motion system changes, or a known visual-language
consistency regression:

```bash
bash skills/design-craft/scripts/design_craft_pass.sh \
  --target /path/to/project \
  --mode system-review
```

Both gates end with `pass`, `blocked`, or `incomplete`. Screenshot attachment,
geometry checks, default computed styles, scanner output, and successful tests
remain supporting evidence rather than visual acceptance.

When a task selects or migrates a headless component library, use the
framework-neutral
[`component-primitive-selection.md`](skills/design-craft/references/component-primitive-selection.md)
contract. A healthy existing project authority defaults to `keep`; Base UI is a
supported conditional choice, not the universal answer. `adopt` or `migrate`
requires project-specific blocker, compatibility, migration, validation, and
rollback evidence. One shared primitive library is architecture consistency,
not proof that the visual system is consistent.

Use `prototype` only for explicit multi-direction exploration. It keeps
exploration out of production code, rejects color/copy-only pseudo-variants,
and stops at `ready_for_selection` until the user selects or explicitly
delegates a winner:

```bash
bash skills/design-craft/scripts/design_craft_pass.sh \
  --target /path/to/project \
  --mode prototype
```

The harness is project/framework/CSP-aware infrastructure; Design Craft does
not impose a fixed picker visual, route, query, or wiring contract.

`skills/design-craft/scripts/` is the only runtime source; repository-root
forwarding wrappers are intentionally not maintained.

Run a motion-specific review pass:

```bash
bash skills/design-craft/scripts/design_craft_pass.sh \
  --target /path/to/project \
  --mode motion
```

Create a stable product UI taste-review packet before scoring a screenshot or
page:

```bash
bash skills/design-craft/scripts/design_craft_taste_review.sh \
  --target /path/to/screenshot-or-project \
  --context "dashboard for internal operators" \
  --evidence-level L0
```

Product UI taste calibration cases live under `evals/product-ui-taste/`. Static
cases use L0/L1 evidence; live browser cases should record TMWD screenshot
artifact paths, SHA-256 hashes, dimensions, DOM/computed-style summaries, and
the states that were not verified. L3 cases must include responsive viewport
evidence and explicit interaction-state checks; responsive fit alone is not
proof of better task hierarchy.

Create a real L4 before/after eval scaffold:

```bash
bash skills/design-craft/scripts/design_craft_l4_eval_case.sh \
  --case-id generic-review-workbench-local-l4 \
  --surface "http://127.0.0.1:4173/generic-review-workbench/" \
  --primary-user "review operations teammates"
```

The generated case is not evidence by itself. Fill real screenshot metadata,
before/after scores, implementation diff, validation commands, and unverified
states before counting it as L4.

Completed project-neutral fixture examples remain the portable public examples.
The repo may also retain historical real-project L4 provenance; those cases are
validated by the local full gate and must keep their project-specific claims
bounded to the recorded artifacts.

Create a project-neutral L4 screenshot capture plan. Prefer the TMWD evidence
bundle helper when the active agent exposes it; this wrapper gives a repeatable
Chrome-headless fallback and writes only repo-external PNG artifacts plus
`screenshots.json` metadata:

```bash
python3 skills/design-craft/scripts/design_craft_l4_capture.py \
  --case-id generic-review-workbench-local-l4 \
  --before-url 'http://127.0.0.1:4173/generic-review-workbench/?variant=before' \
  --after-url 'http://127.0.0.1:4173/generic-review-workbench/?variant=after' \
  --viewport desktop=1440x900 \
  --viewport compact500=500x844 \
  --dry-run
```

Remove `--dry-run` and pass `--manifest <case>/screenshots.json` only when the
URLs are safe to capture and PNG artifacts should be written outside the repo.

Emit a redacted DOM/computed-style sampler for TMWD `browser_execute_js`, or
validate captured product UI evidence and score anti-inflation rules:

```bash
python3 skills/design-craft/scripts/design_craft_browser_evidence.py --print-js
python3 skills/design-craft/scripts/design_craft_browser_evidence.py \
  --validate-score-json evals/product-ui-taste/before-after/generic-review-workbench-local-l4/score.after.json
python3 skills/design-craft/scripts/design_craft_browser_evidence.py \
  --validate-score-json evals/product-ui-taste/before-after/generic-review-workbench-local-l4/score.before.json
python3 skills/design-craft/scripts/design_craft_l4_evidence_manifest.py \
  --validate-screenshots-json evals/product-ui-taste/before-after/generic-review-workbench-local-l4/screenshots.json \
  --strict
```

Validate a completed L4 before/after case directory before citing its metadata:

```bash
python3 skills/design-craft/scripts/design_craft_l4_case_validate.py \
  --case-dir evals/product-ui-taste/before-after/<case> \
  --strict
```

To claim that referenced PNG artifacts are available, add
`--require-existing-files`. The certified release path runs
`make real-l4-check` against the committed, project-neutral generic workbench
artifacts, so this part of certification is reproducible outside the original
capture machine. `make historical-l4-metadata-check` separately validates older
real-project metadata without claiming its private artifacts still exist.

Current project-neutral completed L4 cases are:

- `generic-review-workbench-local-l4`: a local review-workbench fixture with
  committed before/after viewport screenshots and responsive metadata.
- `ops-dashboard-decision-surface-l4`: a local operations dashboard fixture
  that demonstrates the `Dashboard card soup -> decision surface` design move.
- `evals/fixtures/l4-pages/gesture-sheet-interaction/`: deterministic
  direct-manipulation fixture with observed browser trace assertions and a
  repo-external viewport PNG recorded in `validation.json`.

Historical real-project L4 provenance is retained for local verification:

- One historical real application workbench before/after case records
  desktop/mobile screenshot metadata, validation commands, and bounded
  unverified states. `make historical-l4-metadata-check` validates the durable
  metadata. Public release certification no longer depends on those private
  artifact paths; the durable generic case is the existing-file proof.

Run the cross-agent dashboard benchmark validators:

```bash
python3 scripts/design_craft_cross_agent_validate.py --root evals/cross-agent
python3 scripts/design_craft_cross_agent_validate.py \
  --observed-task evals/cross-agent/same-prompt-dashboard-review
python3 scripts/design_craft_cross_agent_validate.py \
  --observed-task evals/cross-agent/same-prompt-motion-review
python3 scripts/design_craft_cross_agent_validate.py \
  --observed-task evals/cross-agent/same-prompt-native-adaptive-review
```

Legacy v2/v3 Codex/Pi dashboard, gesture-motion, and native-adaptive artifacts
are historical baseline evidence only. Current evidence requires an isolated
run-manifest v2 plus score schema v4 bound to the current Skill tree. Codex and
Pi can satisfy the normal desktop profile independently; Cursor and Claude are
additional release-certification hosts and remain explicitly unverified when
their local authentication or API transport cannot complete. Historical
self-contained snapshots live under `evals/cross-agent/history/2026-07-11-v2/`.

Run the host first, then score only the transactionally published output and
its run manifest. Fill a criteria JSON copied from
`evals/cross-agent/_template/criteria.json`:

```bash
python3 scripts/design_craft_cross_agent_run.py \
  --task-dir evals/cross-agent/same-prompt-motion-review \
  --host codex \
  --model <model> \
  --reasoning-profile <profile> \
  --skill-root skills/design-craft

python3 scripts/design_craft_cross_agent_record.py \
  --task-dir evals/cross-agent/same-prompt-motion-review \
  --agent codex \
  --skill-root skills/design-craft \
  --run-manifest evals/cross-agent/same-prompt-motion-review/run.codex.json \
  --criteria-json /path/to/criteria.json
```

The recorder derives host version, requested model/profile, command, runner OS,
copied skill path/tree, and worktree fingerprints from the controlled manifest;
deprecated CLI fields are assertions only. It recomputes the headline score
from criterion-earned points and binds the output, prompt, scorecard, version,
source commit, skill tree, run manifest, and runner/adapter contract hashes.
See `evals/cross-agent/README.md` for the full four-host procedure.

`--observed-task` fails when no host has a complete output/score pair. Use
`--root` to validate pending/unverified active definitions. Archived v2/v3
evidence is checked separately with `make history-audit`; archive compatibility
does not satisfy or block the current-source release gate.

Run static UI smell scanners. These are review signals, not a replacement for
design judgment or browser evidence:

```bash
python3 skills/design-craft/scripts/design_craft_static_review.py --target /path/to/project --json
python3 skills/design-craft/scripts/design_craft_css_smell_scan.py --target /path/to/project
python3 skills/design-craft/scripts/design_craft_focus_audit.py --target /path/to/project
python3 skills/design-craft/scripts/design_craft_token_audit.py --target /path/to/project
```

`design_craft_static_review.py` normalizes the three scanner outputs into one
handoff-friendly JSON packet with severity counts, top findings, and design
interpretation prompts.

Run the detector. Default text output includes pinned Impeccable findings plus
local design-craft review signals; `--json-only` remains raw upstream JSON for
compatibility, and `--full-json` emits the combined payload. Default and full
JSON output also distinguish `available`, `available_regex_fallback`, and
`unavailable`. The regex fallback still emits
useful findings, but it is explicitly degraded when the optional static
HTML/CSS parser packages are absent; raw `--json-only` output cannot carry that
wrapper metadata.

```bash
bash skills/design-craft/scripts/design_craft_detect.sh --target /path/to/project
```

Review pinned upstream drift and absorption candidates without fetching:

```bash
make upstream-report
```

Check remote drift with commit titles, changed paths, and an absorption
recommendation without changing submodule checkouts:

```bash
python3 scripts/upstream_absorption_report.py --remote-details
```

Verify the reviewed inventory, cumulative absorption state, latest-range
decision, local capability mapping, and explicit rejection boundary for all
four upstreams:

```bash
make upstream-absorption-check
```

The human-readable matrices are:

- `docs/taste-skill-absorption.md`
- `docs/impeccable-absorption.md`
- `docs/emilkowalski-absorption.md`
- [Jakub Krehel review](docs/jakubkrehel-candidate-review.md): fixed-revision
  screening and selected writing/component-scenario adaptations. Its registered
  submodule participates in freshness checks; remaining entrypoints are deferred
  candidates, not additional adopted behavior.

The taste and Emil Skill trees contain instructions and snippets rather than a
component/runtime source library. Impeccable includes a substantial live and
provider runtime; its matrix records why design-craft absorbs the workflow,
detector, hardening, and native quality behavior without vendoring that second
browser/package boundary.

Score source completeness and evaluate explicit all-required maturity profiles
separately. Release profiles require a committed, matching-runner benchmark
baseline and current evidence; they are expected to fail when that evidence is
not present:

```bash
python3 scripts/design_craft_score.py --self --json
python3 scripts/design_craft_maturity.py --profile development --json
python3 scripts/design_craft_maturity.py --profile operational_95 --baseline <path> --json
python3 scripts/design_craft_maturity.py --profile certified_100 --baseline <path> --json
```

## Upstream policy

The upstream repositories are kept as pinned submodules:

- `upstreams/taste-skill`
- `upstreams/impeccable`
- `upstreams/emilkowalski-skills`
- `upstreams/jakubkrehel-skills`

Do not edit upstream files directly. Update the fusion layer under
`skills/design-craft/`, update attribution when needed, and record upstream
commit changes in `upstreams.lock.json`.

Runtime routing should use `design-craft` as the baseline. The upstream
`taste-skill`, `impeccable`, and `emilkowalski-skills` checkouts are retained
only for provenance and deliberate manual absorption, not as automatic updaters
or legacy route sources.

Refresh upstreams with:

```bash
bash scripts/sync_upstreams.sh \
  --name emilkowalski-skills \
  --commit <pinned-40-character-sha>
```

The sync helper advances one explicit submodule and only the compatibility
`commit` field. It never advances `reviewed_through_commit`,
`behavior_absorbed_through_commit`, `latest_range_*`, their legacy aliases, or
the decision metadata. The pinned commit may intentionally lag a reviewed
remote head when upstream changes are provenance-only, already represented, or
deliberately rejected. Before absorbing upstream changes, run:

```bash
python3 scripts/upstream_absorption_report.py --remote-details --fail-on-unreviewed
```

Run `make upstream-absorption-check` for every reviewed update. New Skill or
command entrypoints, auxiliary references, detector/runtime surfaces, or
non-Markdown implementation files are treated as review drift rather than
silently ignored.

## Licensing

Original design-craft code and documentation are distributed under the MIT
License in `LICENSE`. Required upstream license and notice text is preserved in
`LICENSES/` and summarized in `THIRD_PARTY_NOTICES.md`. Historical Vercel
snapshot provenance remains documented, but the current package ships original
design-craft developer-product templates instead of redistributing the verbatim
snapshots; see `LICENSES/VERCEL-DESIGN-NOTICE.md`.

## Release governance

Before treating the current source and local install as stable, run:

```bash
make validate-portable
make release-gate-source
make publish-local
```

Before tagging an Operational release, provide the committed benchmark baseline
for the current runner and a repo-external native evidence directory:

```bash
DESIGN_CRAFT_NATIVE_EVIDENCE_ROOT=/path/to/native-evidence \
make release-readiness-operational \
  BENCHMARK_BASELINE=benchmarks/baselines/v0.5.0-<runner-id>.json
```

The equivalent Certified target is:

```bash
DESIGN_CRAFT_NATIVE_EVIDENCE_ROOT=/path/to/native-evidence \
make release-readiness-certified \
  BENCHMARK_BASELINE=benchmarks/baselines/v0.5.0-<runner-id>.json
```

After the dated changelog, reviewed main merge, annotated tag, and successful
tag-push `Validate` plus `Native runtime evidence` runs, verify final metadata
and workflow identity. Final evidence, not candidate evidence, is required to
build assets:

```bash
make release-tag-verify-operational \
  BENCHMARK_BASELINE=benchmarks/baselines/v0.5.0-<runner-id>.json
make release-assets-build-operational \
  NATIVE_EVIDENCE_ROOT=/path/to/native-evidence \
  NATIVE_RUN_OBSERVATION=/tmp/native-run.json
make release-assets-verify-operational
```

Operational has exactly four assets: package, checksum, release manifest, and
SPDX SBOM. Certified has exactly seven, adding the self-contained native bundle,
checksum, and native manifest. Operational records the exact native workflow
run and the 90-day artifact-retention boundary; it does not claim permanent
self-contained native proof. Certified asset construction additionally uses
persisted observations for the exact native tag run and the explicitly approved
physical-device run, plus three separate, already downloaded evidence roots.
Both observations must be created before any artifact download, and final
release evidence must bind byte-for-byte to those selected runs. Keeping the
Simulator, Emulator, and physical-device roots separate prevents artifact-name
collisions and avoids downloading the same GitHub run twice:

```bash
python3 -m tools.design_craft release run-observation \
  --kind native --run-id <tag-run-id> --output /tmp/native-run.json
python3 -m tools.design_craft release run-observation \
  --kind physical --run-id <physical-run-id> --output /tmp/physical-run.json
python3 -m tools.design_craft release evidence-bindings \
  --level certified_100 \
  --evidence dist/evidence/certified_100-final.json \
  --evidence-root /path/to/combined-native-evidence \
  --native-observation /tmp/native-run.json \
  --physical-observation /tmp/physical-run.json
make release-assets-build-certified \
  CERTIFIED_FINAL_EVIDENCE=dist/evidence/certified_100-final.json \
  NATIVE_EVIDENCE_ROOT=/path/to/combined-native-evidence \
  NATIVE_RUN_OBSERVATION=/tmp/native-run.json \
  PHYSICAL_RUN_OBSERVATION=/tmp/physical-run.json \
  NATIVE_IOS_SOURCE=/path/to/native-runtime-ios-<tag-run-id> \
  NATIVE_ANDROID_SOURCE=/path/to/native-runtime-android-<tag-run-id> \
  NATIVE_REAL_DEVICE_ROOT=/path/to/native-runtime-physical-<run-id>
```

Final certification and publication are separate trust boundaries.
`.github/workflows/release-certify.yml` has read-only repository permissions,
uses only the repository-scoped Actions token, and uploads a relocatable
certification artifact containing final evidence, selected run observations,
native evidence records, and the exact four- or seven-asset set. It cannot
attest or publish a GitHub Release. Certification verifies immutable tag,
workflow-run, benchmark, artifact, and digest bindings without requiring a
long-lived personal access token. Live ruleset and Actions-policy inspection is
available separately through `make github-governance-check` for maintainers; it
is not a release-blocking dependency.

Maintainers can push locally verified, scoped commits directly to `main`.
Validate runs after the push as asynchronous evidence instead of blocking the
fast-forward update. The repository still rejects deletion and force-pushes on
`main` and immutable `v*` tags. Pull requests remain useful for external or
high-risk changes, but are not mandatory for routine maintainer work.

`.github/workflows/release-publish.yml` accepts an explicit successful
certification run ID, artifact ID, and `sha256:<digest>`. It re-observes the run
and artifact in a read-only verification job, downloads the exact artifact ID,
checks the REST ZIP against the supplied digest, and validates source commit,
annotated tag, release level, every bundled digest, native run binding, and exact
asset allowlist. Only a dependent publication job receives attestation and
`contents: write`; that job executes no repository validation code and releases
only the same immutable artifact ZIP after rechecking its digest and tag target.
Neither workflow publishes to npm, and an existing GitHub Release is never
replaced in place. An Operational release can only become Certified in a new
version. After publication, use `make release-final-verify-operational` or
`make release-final-verify-certified` to revalidate the published asset set.

The gate split is documented in `docs/maintenance.md`. The portable gate checks
package shape, syntax, bundled runtime independence, platform fixtures,
validators, static scanners, project-neutral L4 fixtures, source completeness,
and development maturity without local install-state assumptions. Local publish
adds an atomic install and installed-skill provenance/parity. Release profiles
add current observed evidence, benchmark regression, a clean worktree, live
upstream review, and final remote/tag/workflow checks without using history
artifacts as substitutes.

Probe native SDK/runtime availability and validate real evidence separately:

```bash
python3 scripts/design_craft_native_runtime_validate.py --probe --json
python3 scripts/design_craft_native_runtime_validate.py --validate --require ios --require android --require-real-device --require-current-source --json
```

`.github/workflows/native-runtime.yml` runs a real iOS Simulator fixture and a
real Android Emulator fixture on manual dispatch and release tags. It builds,
installs, launches, captures runtime artifacts, exercises the Android control
and a real iOS `simctl openurl` transition against the running app with a cold
deep-link fallback, pinned AXe semantic confirmation, and a screenshot-derived
coordinate fallback for Simulator system dialogs. The iOS assertion requires
both the app's URL-receipt event and its interaction marker. The workflow hashes
the evidence and validates the generated JSON before upload. Downloaded
artifacts must still be reviewed before `ios-observed.json` and
`android-observed.json` are admitted as durable evidence. A separate physical
device run must provide `real-device-observed.json`; workflow existence is not
itself runtime proof. `.github/workflows/physical-device.yml` only defines a
manual, environment-approved self-hosted capture lane. It is not certification
until that exact run's current-source artifact validates.

The release bundle validator packages all three evidence JSON files and their
declared artifacts only. It rejects undeclared files, duplicate members,
links/devices, path traversal, non-normalized archive metadata, stale source
hashes, oversized archives/members, and a run other than the latest completed
successful `v<VERSION>` tag push. It separately requires the physical evidence
to bind to an explicitly selected successful `main` workflow-dispatch run. Unit
and integration tests verify byte-identical double builds, bounded extraction,
single-inspection validation, CLI exit codes, and exact outer/inner evidence,
workflow, and per-artifact binding.

Runtime evidence stores only a SHA-256-derived runtime identifier. Raw
Simulator UDIDs, iOS device identifiers, and Android serials must not be
committed. Each runtime kind has required assertion names and artifact roles;
the validator parses decisive accessibility XML, verifies PNG signatures, and
binds every artifact by path, byte count, and SHA-256. Normal `Validate` runs
compile-only iOS and Android fixture jobs so deterministic build failures are
caught before the release-only runtime workflow.

Capture a connected, authorized physical Android device into a repo-external
evidence directory with:

```bash
bash scripts/native_runtime_device_android.sh \
  --serial <adb-serial> \
  --evidence-dir /tmp/design-craft-android-device
```

The raw serial is used only for the live ADB session; the recorded JSON contains
its SHA-256-derived identifier. Review the output before admitting it to the
repo-external release evidence directory. Current evidence is not committed back
into the source tree because its source-commit binding would otherwise be
cyclic.

Route smoke uses a temporary fixture project with its own `DESIGN.md`, because
`design-craft` itself is a reusable skill system rather than a product UI target:

```bash
make route-smoke
```

## Versioning

This repo uses local semantic versioning:

- `0.x`: personal pre-1.0 workflow, allowed to evolve quickly.
- `1.x`: stable default design-craft workflow for this machine.
- Patch releases: validation, documentation, detector, or maintenance fixes.

Current version is stored in `VERSION`; notable changes are tracked in
`CHANGELOG.md`.
