# design-craft maintenance

This document is the local release and maintenance checklist for
`design-craft`.

## Maintenance rules

- Keep `upstreams/` pristine. Do not edit `upstreams/taste-skill`,
  `upstreams/impeccable`, `upstreams/emilkowalski-skills`, or
  `upstreams/jakubkrehel-skills` directly.
- Keep the installable skill lean. `README.md`, `CHANGELOG.md`, release notes,
  and maintenance docs belong at the repo root or under `docs/`, not inside
  `skills/design-craft/`.
- Keep the published Pi/npm payload narrower than the repository. The package
  may contain only `skills/design-craft`, required root metadata, and preserved
  license/notice files; never publish `upstreams/`, `evals/`, workflows, or
  repository-only scripts.
- Preserve the root MIT license plus upstream license and notice text in
  `LICENSES/`. Do not treat the design-craft MIT license as relicensing the
  Vercel design snapshots.
- Keep project-specific truth above generic visual guidance:
  live runtime behavior, scoped `AGENTS.md`, README/framework conventions, and
  optional project `PRODUCT.md` plus project `DESIGN.md` outrank the fusion
  references. PRODUCT owns product/platform facts; DESIGN remains the only
  visual/token/component/theme/motion authority.
- Treat `upstreams/taste-skill`, `upstreams/impeccable`,
  `upstreams/emilkowalski-skills`, and `upstreams/jakubkrehel-skills` as
  provenance and deliberate absorption inputs only. Do not reintroduce
  automatic upstream skill overwrites or legacy taste
  routing.
- Keep helper scripts deterministic and cheap enough to run before real
  UI/UX/design/frontend work.
- Keep the product route Web-first: ordinary desktop/browser work defaults to
  `platform=web`. Load iOS, Android, and adaptive references only when source or
  product evidence establishes a native target. Mobile Web and WebView shells
  must not turn native runtime or device evidence into a daily Web blocker.
- Keep OS support explicit: repository automation is verified on macOS/Linux,
  and the current-source Windows Git Bash portability lane has succeeded. This
  does not claim a native Windows UI runtime; WSL is a fallback, not separate
  product proof.
- Keep the deterministic source gate independent of mutable upstream remote
  heads. Remote freshness belongs to explicit release-level readiness and the
  scheduled audit.
- A GitHub comparison reaching 300 file records or omitting commits is
  incomplete evidence. The report attempts a complete forward comparison using
  existing local commit objects and labels its source `local_git`; it never
  fetches or changes a pin automatically. If recovery is unavailable, details
  retain an explicit error and `manual_review` recommendation. Review metadata
  must not advance from a partial file list.
- Keep GitHub Actions pinned to full reviewed SHAs. Dependabot may propose
  GitHub Actions or npm metadata updates, but those changes still require the
  normal validation and review gates.
- Keep package, public-repository, and workflow/native contract checks in their
  dedicated validators rather than expanding the monolithic validation shell.
- Keep comparative evidence admission under
  `tools/design_craft/evaluation/comparative/`; the script in `scripts/` is a
  stable compatibility CLI, not a second implementation.
- Keep cross-agent definition, score, run, current-source, and history
  validation under `tools/design_craft/evaluation/cross_agent/`; its script is
  likewise only the stable compatibility CLI.
- Keep maturity gates grouped by evidence lifetime: deterministic development
  gates, current-source evidence gates, and repository/release-state gates.
  `maturity/gates.py` owns only registration and compatibility exports.
- Keep route-pack semantic validation split into declarative contracts, static
  source checks, and runtime probes. Submit runtime work first, overlap static
  reads, and assemble the stable report only in `routing/semantic_audit.py`.
- Keep `operational_95` distinct from `certified_100`. These are evidence-level
  names, not composite product-quality scores. Certified requires current-source
  score v4 for all four hosts plus Simulator, Emulator, and physical-device
  evidence v3; never infer them from history or workflow definitions.
- Keep source validation non-mutating. Local installation is a separate explicit
  `publish-local` step; installer behavior and rollback are verified in isolated
  temporary roots before any release target relies on installed provenance.
- Keep the repository as canonical source and `~/.agents/skills/design-craft`
  as an atomic installed copy. Do not replace this with a live symlink or
  background hot sync; use detect -> review/pin -> clean commit -> gates ->
  install, and use `sync-status` only to detect drift.
- Keep agent-specific install behavior in `adapters/` and scripts. Do not fork
  the canonical `skills/design-craft/` content per agent.
- Keep the Codex frontend route layer portable through the route-pack manifest
  helper. Do not copy unrelated `~/.codex` state, credentials, browser profile
  files, caches, or session logs into this repo.
- Record meaningful task evidence under `evals/`; do not claim browser
  validation unless a browser validation actually ran.
- Keep public evidence machine-neutral. Use `~`, repository-relative paths, or
  documented aliases such as `PRODUCT_REPO` and `DESIGN_CRAFT_HOME`; never
  commit named macOS, Linux, or Windows user-home paths.
- Do not add a root `DESIGN.md` to this repository. `design-craft` is a reusable
  skill/workflow system, not a product UI target. Target projects must provide
  their own `DESIGN.md` or pass an explicit style authority path for L1+ route
  checks.

## Portable validation gate

Run this on a fresh clone or another machine before trusting the package shape:

```bash
make validate-portable
```

`contracts/validation/gates.json` is the machine-readable source of truth for
this gate. `scripts/validate.sh` remains the stable cross-platform shell entry,
but owns only Git Bash normalization and the optional external Skill validator;
it must not grow another hard-coded source-check list. The portable profile
runs independent source gates through a bounded worker pool, then runs
development maturity only after every source gate passes. `make contract-tests`
selects the contract-only view from the same registry.

Test ownership is explicit in that registry: `tests/unit`, `tests/integration`,
and `tests/adversarial` run as independent source lanes. The slower installer
transaction suite lives at `tests/contract/test_installer.py`; the contracts
profile selects it directly, while portable and release profiles run it once
inside standalone-complete development maturity. Do not add it back to general
test discovery or select it twice in the same profile.

Structured validation output uses `design-craft.validation-run.v2`:
`duration_ms` is observed wall time, while `gate_duration_sum_ms` is the sum of
individual process durations and may be greater than wall time when gates run
in parallel.

It expands to portable checks only: required files, package/version
consistency, npm pack size/path hygiene, dependency-free Python/shell/JSON/Node
lint, isolated runner/comparative/native/release contract self-checks,
bundled-runtime independence, platform fixtures, L4 validators, static scanners,
100/100 source-contract completeness, and pass/fail development maturity. It
does not depend on current host/native observations, local Codex state,
installed-skill parity, native SDKs, or remote upstream freshness.

Expected result:

- Required references, scripts, notices, evals, and version files exist.
- Shell scripts pass `bash -n`.
- Python scripts compile and core validators run.
- Static smell scanners and the aggregate static review packet run against
  fixture targets.
- Cross-agent task definitions validate.
- Cross-agent active definitions and separately archived history validate;
  current Codex/Pi observations remain release-only evidence.
- iOS, Android, and adaptive valid/invalid source fixtures separate correctly.
- Portable route/detector degraded paths are explicit, and copied installed-skill
  L4 helpers run without the source repo.
- Project-neutral L4 fixtures validate in strict mode.
- Version in `VERSION` matches `package.json`.
- `npm pack --dry-run` remains within 1 MB compressed, 2 MB unpacked, and 102
  files, contains the canonical skill and required legal metadata, and excludes
  repository-only paths and user-home strings.
- Source completeness is 100 as an internal contract metric. Development
  maturity is pass/fail and does not emit a partial product-quality score.
- CI covers Python 3.11, 3.12, and 3.13 across Ubuntu/macOS and Node 22/24.
- Native runtime CI definitions and minimal fixtures validate structurally, but
  only a completed workflow run and reviewed artifact JSON count as observed
  Simulator/Emulator evidence.

## Development and release gates

Run the deterministic source gate before a version bump, commit, or route-policy
change. Publish locally only when installed parity is part of the task:

```bash
make release-gate-source
make publish-local
```

`Makefile` is the executable authority for `release-gate-source`; do not copy
its growing dependency list back into this document. It currently includes
portable validation, lint, contract tests, package/public/workflow checks,
source scoring, route/platform checks, native archive/bundle unit tests,
comparative and cross-agent definition validation, L4/static scans, upstream
lock checks, governance contract checks, and candidate release metadata checks. Active-install parity
is intentionally checked only after the atomic installer runs, avoiding a
stale-install circular dependency.

Immutable v2/v3 cross-agent and v0.4 comparative archives are validated by the
separate `make history-audit` target. This audit remains strict, but frozen
schema/Markdown compatibility cannot satisfy or block current-source product
and release gates.

Expected result:

- Skill schema passes the repository-owned, dependency-free validator. Set
  `SKILL_CREATOR_QUICK_VALIDATE` only when an additional external compatibility
  check is required.
- Required references, scripts, notices, evals, and version files exist.
- Shell scripts pass `bash -n`.
- Python scorer compiles and runs.
- Detector smoke passes against `skills/design-craft` and keeps raw
  `--json-only` compatibility for upstream Impeccable output.
- Preferred pass wrapper, audit wrapper, critique, prototype, and system-review
  mode smokes pass.
- Motion-specific pass smoke passes and the Emil-derived motion references are
  present.
- Product UI taste-review packet smoke passes and keeps score evidence levels
  explicit.
- Product UI browser evidence helper compiles, emits a redacted TMWD DOM/style
  sampler, and validates score anti-inflation plus DOM evidence JSON.
- Static smell scanners compile and run against fixture targets.
- The aggregate static review helper returns normalized severity counts and
  interpretation prompts.
- Adapter docs exist, and init dry-runs cover Codex, Cursor, Claude, Pi, and
  generic Agent Skills-compatible installs without writing files.
- Doctor output runs without mutating files and reports required optional
  capabilities truthfully.
- The isolated Codex route-pack self-check proves manifest, export, missing-file,
  and symlink boundaries without reading operator `~/.codex` state. The strict
  host route-pack audit remains a separate operational command.
- Original developer-product seed helper smoke passes and preserves template byte parity.
- Route smoke passes against a temporary fixture project with its own
  `DESIGN.md`, preserving the contract that product targets provide their own
  design authority.
- Historical real-project L4 metadata validates in the normal local full gate.
  Certified evidence runs `make real-l4-check` against committed,
  project-neutral screenshots, so the existing-file proof is reproducible on a
  fresh checkout.
- Observed cross-agent evidence validates for the hosts that actually ran the
  same benchmark prompt. Uncollected hosts must remain explicitly unverified.
- Development maturity reports only whether every development contract passed.
  Older iOS Simulator and Android Emulator v2 artifacts remain under native
  history and cannot satisfy current release gates.
- Upstream absorption report runs without fetching or modifying submodules; the
  optional `--remote` check reports remote drift with `git ls-remote`.
- Upstream lock commits match checked-out submodule commits.
- Jakub inventory, selected source hashes, local mappings, and review boundaries
  are checked by `make jakub-absorption-check`; remote freshness uses the shared
  lock-driven report. Deferred entrypoints are not counted as absorbed.
- Taste, Impeccable, and Emil absorption matrices validate their complete
  entrypoint inventories, local coverage, cumulative state, latest reviewed
  range, and intentional rejection boundaries.
- Installed canonical skill matches the source and carries valid version,
  source commit, dirty-state, exact tree digest, install-time, and source-repo
  provenance.
- The installer uses staging, an install lock, atomic replacement, rollback,
  and bounded backup retention. The retired `frontend-craft` name is outside
  the v0.5 installer boundary: the installer does not inspect, mutate, or delete
  existing copies. Review ownership and preserve local changes before retiring
  one separately.
- Use `INSTALL_ARGS=--no-prune-backups` when a maintenance run must preserve
  every historical backup; default installs retain the newest ten per skill.

Mutable remote review is part of candidate
`release-readiness-operational` and `release-readiness-certified`, not the
deterministic source gate or final tag certification. Final certification
verifies the committed upstream review snapshot and lock parity from the tag;
it must not change outcome because an external repository advances after the
tag was created.

Check whether the canonical skill copy or separate Codex route-pack has drifted:

```bash
make sync-status
make sync-status-remote
```

Operational release readiness requires a committed matching-runner benchmark
baseline, Codex/Pi current-source score v4, current comparative evaluation,
current iOS Simulator and Android Emulator evidence v3, clean worktree,
installed provenance, and live upstream review at candidate time. Cursor, Claude, and
physical-device status remain explicitly unverified.

Certified readiness strictly extends Operational with Cursor, Claude, and a
current physical-device artifact. Candidate and final evidence are separate;
only final evidence may build assets. Final verification additionally requires
main, annotated local/live tag parity, successful exact-HEAD tag-push workflows,
and the live branch/tag rulesets. Use the explicit targets:

```bash
make release-readiness-operational BENCHMARK_BASELINE=<path>
make release-tag-verify-operational BENCHMARK_BASELINE=<path>
make release-assets-build-operational \
  NATIVE_EVIDENCE_ROOT=/path/to/native-evidence \
  NATIVE_RUN_OBSERVATION=/tmp/native-run.json
make release-final-verify-operational BENCHMARK_BASELINE=<path>

make release-readiness-certified BENCHMARK_BASELINE=<path>
make release-tag-verify-certified BENCHMARK_BASELINE=<path>
NATIVE_RUN_OBSERVATION=/tmp/native-run.json \
PHYSICAL_RUN_OBSERVATION=/tmp/physical-run.json \
NATIVE_EVIDENCE_ROOT=/path/to/combined-native-evidence \
make release-assets-build-certified
make release-final-verify-certified BENCHMARK_BASELINE=<path>
```

The manual Release certification workflow has read-only repository permissions
and produces a relocatable, digest-bound artifact containing exactly four
Operational assets or seven Certified assets plus their evidence and selected
run observations. It uses only the repository-scoped Actions token to read the
exact workflow runs and artifacts; no long-lived personal access token is part
of certification. The separate publication workflow accepts the exact
certification run ID, artifact ID, and SHA-256 digest, revalidates the complete
bundle in a read-only job, then gives a dependent publication job only the same
immutable artifact ID and digest. The write-authority job rechecks the REST ZIP
digest and annotated tag target, executes no repository validation code, and
only then produces provenance attestations and the GitHub Release. Neither
workflow publishes to npm or replaces an existing version. A later Certified
claim therefore requires a new version rather than mutating an Operational
release in place.

`make github-governance-check` remains available for an explicit maintainer
audit of live branch/tag rulesets and the Actions allowlist. It uses the
operator's existing authenticated `gh` session and is intentionally outside the
release critical path because GitHub exposes those settings through
administration-level endpoints. The selected-actions contract combines action
repositories referenced directly by workflows with an explicit set of reviewed
transitive repositories loaded by composite actions. In particular,
`actions/attest-build-provenance` currently loads its `predicate` repository and
`actions/attest`; GitHub evaluates both against the allowlist independently.
Keep those dependencies narrow and explicit rather than allowing `actions/*`.

The main ruleset permits normal fast-forward pushes after local validation.
Validate still runs on `main` pushes and release tags, but its status is
post-push evidence rather than a remote precondition. Deletion and
non-fast-forward protection remain active for `main` and `v*` tags. Use a pull
request when review or isolation is valuable; do not require one for routine
maintainer-owned improvements.

## Upstream sync procedure

1. Inspect current state:

   ```bash
   git status --short
   git submodule status --recursive
   ```

2. Check remote drift without mutating submodules:

   ```bash
   python3 scripts/upstream_absorption_report.py --remote-details --fail-on-unreviewed
   ```

3. Sync exactly one upstream only when the reviewed range contains source that
   must become the pinned compatibility snapshot:

   ```bash
   bash scripts/sync_upstreams.sh \
     --name <taste-skill|impeccable|emilkowalski-skills> \
     --commit <pinned-40-character-sha>
   ```

   The helper updates only the compatibility `commit` field. Set
   `cumulative_status`, `reviewed_through_commit`,
   `behavior_absorbed_through_commit`, `latest_range_base_commit`,
   `latest_range_head_commit`, `latest_range_status`, `reviewed_at`, `notes`,
   and the compatibility aliases `reviewed_commit`, `absorbed_commit`, and
   `decision` manually after the absorption review.

   Lock schema v3 separates four truths:

   - `commit`: pinned compatibility source checked out by the submodule;
   - `reviewed_through_commit`: latest remote head actually reviewed;
   - `behavior_absorbed_through_commit`: newest upstream behavior boundary
     represented by the selective local fusion;
   - `latest_range_base_commit..latest_range_head_commit`: exact newly reviewed
     range and its explicit decision.

   Do not advance the submodule merely to silence remote drift. A reviewed
   remote head can remain ahead when its changes are provenance-only, already
   represented, or intentionally rejected.

4. Generate a local absorption report:

   ```bash
   python3 scripts/upstream_absorption_report.py
   ```

   Treat `candidate_absorb` files as review inputs, not automatic changes.
   `provenance_only` usually means notices/readmes,
   `repository_operations_only` means upstream CI or repository automation,
   and `manual_review` requires human judgment before changing the fusion layer.

   Validate all three complete inventories, local capability mappings, and
   intentional rejection boundaries separately:

   ```bash
   make upstream-absorption-check
   ```

   The contracts fail if a taste Skill, Impeccable command/runtime boundary,
   Emil Skill, auxiliary file, or implementation surface appears without an
   explicit inventory decision. Update the matching matrix under `docs/`, the
   fusion references, attribution, and `upstreams.lock.json` together after
   review.

5. Review upstream licenses and attribution if upstream content changed:

   ```bash
   git diff -- THIRD_PARTY_NOTICES.md upstreams.lock.json skills/design-craft/references/source-map.md
   ```

6. Update the fusion layer only under `skills/design-craft/`.

7. Run the deterministic source gate. Run the explicit release level only when
   current evidence and a matching benchmark baseline are available:

   ```bash
   make release-gate-source
   make release-readiness-operational BENCHMARK_BASELINE=<path>
   ```

## Version policy

- Update `VERSION` for every local release.
- Update `CHANGELOG.md` with user-visible changes.
- Use `0.x` while the workflow is still evolving quickly.
- Use `1.x` only after repeated live UI/UX/design/frontend tasks prove the
  workflow stable as the default Codex route baseline.

## Current task evidence

Do not append current status to a repository-level Markdown log. Store active
evidence in the owning evaluation domain using its JSON schema and validator:

- comparative results under `evals/comparative/`;
- host observations under `evals/cross-agent/`;
- native observations under `evals/native-runtime/`;
- stable replay inputs under `evals/golden-tasks/` or `evals/fixtures/`.

Machine evidence must identify the date, target, route and selected skills,
style authority, actual validation commands, runtime status, and artifact
hashes required by that domain. A Markdown view may be generated from the JSON
contract, but it is not a second status source. Retired narrative logs live
under `evals/history/` and cannot satisfy current release gates.

Do not use evidence notes as a substitute for verification. If browser smoke,
type-check, lint, build, or route validation did not run, record that explicitly
in the machine status.

## Golden task evidence

Use `evals/golden-tasks/` for stable task cards that should remain reproducible
across `design-craft` changes. Each card should record:

- Target path and surface.
- Route command and decisive route output.
- Candidate skills versus selected references.
- Style authority path and authority mode.
- Required validation, including browser validation when user-visible UI is in
  scope.
- Required screenshot evidence when `browser_screenshot_required=true`.
- What remains unverified.

Golden tasks should be updated only when the project reality or desired workflow
contract changes.

## Product UI taste calibration

Use `evals/product-ui-taste/` for stable screenshot or page-review calibration
cases. Each case should record:

- Product context and primary user job.
- Evidence level (`L0` through `L4`).
- Expected score or acceptable score range.
- Required findings that a good review should surface.
- False-positive guards, especially claims that cannot be made from the
  available evidence.
- Browser evidence JSON, when captured, should use
  `design-craft.browser-evidence.v1` and pass
  `skills/design-craft/scripts/design_craft_browser_evidence.py --validate-evidence-json`.
  Historical schemas are accepted only by history-specific validators. Old
  TMWD run directory names may remain in immutable history records, but current
  evidence must use the canonical schema.
- L3 cases must include at least two responsive viewports plus state checks; a
  responsive layout that still preserves weak hierarchy should not inflate the
  score.

Keep binary screenshots out of the repo unless the image itself is required for
reproducibility, is project-neutral, and has clear provenance.

For live browser cases, capture first into the TMWD repo-external run directory.
Commit only deliberately reviewed project-neutral images needed for durable
certification; otherwise retain path, SHA-256, dimensions, collection time,
evidence level, and a redacted visual/DOM summary.

## L4 before/after evidence

Use `evals/product-ui-taste/before-after/` only for real implementation
improvement evidence. The `_template/` directory is scaffolding and must not be
counted as a completed L4 case.

A completed L4 case must include:

- Before and after screenshot artifact path, SHA-256 hash, and dimensions.
- Before and after scores with `evidence_level: "L4"`.
- Diff summary naming actual changed files or implementation boundaries.
- Validation commands and observed results.
- Explicit unverified states.

Active project-neutral completed cases:

- `generic-review-workbench-local-l4`
- `ops-dashboard-decision-surface-l4`

Validate them with
`skills/design-craft/scripts/design_craft_l4_case_validate.py --strict` before
citing either as completed before/after evidence. The generic workbench case is
the durable `--require-existing-files` release proof; the operations case may
retain external capture provenance.

## Cross-agent benchmarks

Use `evals/cross-agent/` to compare how Codex, Cursor, Claude, Pi, or another
Agent Skills-compatible client applies the same `design-craft` prompt.

Do not claim cross-agent stability until real outputs are recorded. Template
cases define prompts and scorecards only. Legacy v2 dashboard, gesture-motion,
and native-adaptive Codex/Pi artifacts are historical baseline evidence.
Current evidence must use isolated run-manifest v2 plus score schema v4,
binding the current Skill, prompt, `scorecard.json`, output, runner/adapter
contract, host version, and worktree fingerprints. `evidence-status.json` is the
active host-state truth source; `comparison.md` is generated from it and must
remain byte-identical. Codex/Pi satisfy the desktop profile when current;
Cursor/Claude remain independent optional release-certification hosts. Record
blocked active runs as `pending` or `unverified` with a reason in JSON; explicit
Markdown unverified notes are accepted only in immutable history.
Host/model/command fields are derived from the controlled run, not trusted from
manual recorder flags.

## Codex route-pack portability

The local frontend route planner, platform detector, route config, frontend
rule, preflight contract, and route tests live under `~/.codex`. They are
runtime policy, not skill contents. Use the route-pack helper to make that
policy auditable. The file-list authority is
`~/.codex/tools/frontend_route_pack_manifest.json`; the helper and global
snapshot must derive their scopes from that manifest rather than maintaining
parallel lists:

```bash
make codex-route-pack-host-check
# Equivalent direct command:
python3 scripts/design_craft_codex_route_pack.py --strict --json
```

`make codex-route-pack-check` is the repository-owned portable contract and
uses only isolated fixtures. It belongs in source and release-candidate gates;
the host check above intentionally audits operator `CODEX_HOME` state and must
remain separate from clean-runner certification.

For migration or backup, export only the whitelisted bundle:

```bash
python3 scripts/design_craft_codex_route_pack.py \
  --strict \
  --export-dir /tmp/design-craft-codex-route-pack
```

After restoring to another Codex home, run the validation commands listed in
`adapters/codex/route-pack/README.md`. Do not treat the manifest alone as proof
that the restored route planner works. A strict audit must also pass routing
JSON Schema validation, split authority/browser/delivery/runtime/telemetry
module checks, telemetry self-checks, browser-lifecycle-receipt contract tests,
browser/runtime tool-parity probes, a
verified `gpt-5.6-sol/max` environment-runtime probe, and the unapproved GPT-5.6
`ultra` runtime-conflict denial probe. Strict probes set
`FRONTEND_ROUTE_TELEMETRY_LOG_ENABLED=0` and
`FRONTEND_RUNTIME_SESSION_DISCOVERY=0`; audit runs must not write production
telemetry or read the caller's session JSONL.

The live planner may verify the current runtime from the latest session
`turn_context`, but only `model`, `effort`, `turn_id`, and `current_date` are
read. Prompt/message/tool payloads remain outside the contract, and evidence
paths are relative to `CODEX_HOME`. `config.toml` values are candidates, not
proof of the active turn.

Review production route latency and distributions separately:

```bash
python3 ~/.codex/tools/frontend_route_telemetry.py \
  --include-rotated \
  --context prod \
  --min-events 50 \
  --max-p95-ms 1000 \
  --json
```

The default privacy-safe log rotates at 2 MB with seven retained files. Use a
non-production context for fixtures and keep general route tests plus release
route smoke telemetry-off; `test_frontend_route_telemetry.sh` owns telemetry
behavior coverage. New writes use `frontend-route.telemetry-event.v2`, which
records `planned_execution_mode` and `actual_subagent_state` without the legacy
`execution_mode` field. Summary v2 must continue reading mixed v1/v2 history in
place, report source-schema counts, and never rewrite or delete legacy events.

Route lifecycle contracts must also keep policy separate from runtime truth:
`planned_browser_lifecycle` and legacy `browser_lifecycle` are plans, while the
planner's `actual_browser_lifecycle_state.state` remains `not_started` or
`not_applicable`. Only browser67 outcomes and a scoped `finalize_task` delivery
summary can support a separate runtime created/adopted/released/closed receipt;
the planner payload is not automatically updated after browser work. Use
`frontend_route_browser_receipt.py` to bind a saved route digest to ordered
`tmwd_browser/browser_tab_lifecycle` arguments and `browser67.tool-outcome.v3`
results. Its `frontend-route.browser-lifecycle-receipt.v2` output keeps
`receipt_valid` separate from `runtime_complete`, binds Browser Instance scope
through privacy-safe references, rejects ambiguous or cross-instance evidence,
rejects dry-run or `scope=all` as completion evidence, and never copies URLs,
titles, tab IDs, adoption tokens, or lease IDs.

Keep scope normalization aligned with live browser67: `workspace_key` takes
precedence and yields `scope=workspace`; a simultaneous `task_id` is an
additional filter/correlation field. Task-only scope omits `workspace_key`.
Normalize live camelCase `close_scope.workspaceKey/taskId` to canonical
snake_case, and keep explicit-call/live-scope mismatches fail closed.

Do not describe the receipt adapter as automatic host cleanup. The global
Codex config registers a `PostToolUse` matcher only for the exact
`mcp__tmwd_browser__browser_tab_lifecycle` tool. Capture is observational: it
binds a privacy-safe route view to session/turn, sanitizes the completed call in
memory, and atomically replaces one repo-external state file. It cannot dispatch
`finalize_task` through the active Codex MCP client, so scoped finalization
remains explicit. Never retain raw hook payloads or match every `tmwd_browser`
tool. A frontend route-pack restore does not install or trust this Hook and does
not schedule retention; follow the targeted host-integration procedure in
`adapters/codex/route-pack/README.md` without exporting the complete
`config.toml` or Hook trust state. Configuration alone is not live evidence
until a new Codex session reviews/trusts the Hook and verifies a real lifecycle
entry plus explicit scoped finalization.

Capture status uses `frontend-route.browser-capture-status.v2`. Health counters
are historical evidence only when `health_persisted=true` and
`health_status=persisted`; zero defaults with uninitialized health are not proof
of an error-free history. Retention removes incomplete state after 7 days and
complete state after 30 days, caps retained incomplete states at 1,000, and caps
complete receipts at 100. The wider global periodic runner may own that schedule
on a full installation; a standalone route-pack restore must schedule `--prune`
separately and verify the scheduler rather than inferring it from unit tests.

The stable `test_frontend_preflight.sh` entry is a thin parallel orchestrator.
Its isolated gate, route, observability, policy, and state/concurrency suites
live under `tools/tests/frontend_preflight/`; keep those files in the route-pack
manifest and snapshot inventory whenever the suite structure changes.

## Release checklist

Before committing a release:

1. `git status --short`
2. `make validate-portable`
3. `make lint && make contract-tests`
4. `make release-gate-source`
5. Confirm source completeness 100/100 is reported only as contract
   completeness and `maturity-development` passes every required gate.
6. Route smoke on the fixture (`make route-smoke`) or on at least one real
   project path with its own `DESIGN.md` when route behavior changed.
7. Review the upstream absorption report when upstream commits or detector rules changed.
8. Confirm product UI taste calibration and completed L4 case validation still pass
   when taste scoring changed.
9. Run the install parity/provenance check:
   `make install-verify`
   This checks the installed skill tree and skill-scoped dirty state. Separate
   `repo_dirty` provenance remains visible for audit, while the release
   certification gate independently requires the whole worktree to be clean.
   The recorded source commit must also contain the exact installed skill tree;
   ancestor status alone is not sufficient provenance.
10. Confirm the retired alias is absent from active source and run the
    installer migration tests. See `docs/operations/v0.5-migration.md`.
11. Confirm no repo docs were added inside `skills/design-craft/` except the
    machine-readable `VERSION` and `COMPATIBILITY.json` contracts.
12. Generate a benchmark baseline only from a clean, scoped commit and run the
    same scale at least twice before admitting
    `benchmarks/baselines/v<VERSION>-<runner-id>.json`.
13. Run the selected candidate gate with that exact baseline and a repo-external
    current native evidence directory:
    `make release-readiness-operational BENCHMARK_BASELINE=<path>` or
    `make release-readiness-certified BENCHMARK_BASELINE=<path>`.
14. Keep Cursor, Claude, and physical-device status explicitly unverified for
    Operational. Certified must instead provide all three; no gate may infer
    success from absence.
15. Dispatch `.github/workflows/native-runtime.yml`, download the iOS and
    Android artifacts into separate roots, and verify their hashes and
    assertions with the current-source validator. Do not merge those roots
    before building the Certified native bundle.
    Runtime identifiers must be hashed, and the decisive Android before/after
    accessibility trees must be present in the JSON artifact-role set.
16. For Certified only, capture a physical Android device locally or through
    the environment-approved `.github/workflows/physical-device.yml`; never
    hand-author `real-device-observed.json`.
17. Commit and merge with scoped history. Date the changelog, create an
    annotated tag, and wait for the exact tag-push Validate and Native workflows.
18. Before downloading final artifacts, persist the selected Native tag-run
    observation. Certified must also persist the explicitly approved physical
    workflow observation. Both observations must be completed/successful,
    current-HEAD, exact workflow/repository/run-attempt bindings; Native must be
    the latest successful tag run and physical-device must be a `main`
    `workflow_dispatch` run. Then run `release-tag-verify-operational` or
    `release-tag-verify-certified` on main with the matching baseline. Candidate
    evidence cannot build assets.
19. Build and verify exactly four Operational assets or seven Certified assets.
    Certified builds require `NATIVE_RUN_OBSERVATION`,
    `PHYSICAL_RUN_OBSERVATION`, `NATIVE_IOS_SOURCE`, `NATIVE_ANDROID_SOURCE`,
    and `NATIVE_REAL_DEVICE_ROOT`; the builder does not redownload artifacts.
    The package digest must match the SPDX SBOM and manifest, and the outer
    release manifest must match every inner native evidence digest, artifact
    record, workflow binding, and selected run. Asset replacement is staged and
    rolls back on publish failure.
20. Trigger `.github/workflows/release-certify.yml` with its explicit
    confirmation. Record the completed run ID, uploaded artifact ID, and the
    artifact's `sha256:<digest>` output. Certification uses only repository
    read permissions and has no publication or attestation permission.
21. Trigger `.github/workflows/release-publish.yml` with that exact run ID,
    artifact ID, digest, tag, level, and explicit publication confirmation. Do
    not publish to npm and do not replace an existing release.
22. Run `release-final-verify-operational` or
    `release-final-verify-certified` to re-download the published asset set and
    verify tag, workflow, manifest, SBOM, and attestation inputs. Run
    `make github-governance-check` separately when auditing live repository
    administration policy.
