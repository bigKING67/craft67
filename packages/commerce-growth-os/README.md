# Consumer Brand Commerce and Marketing Skill Pack

This repository is the canonical source for a modular consumer-brand Commerce and Marketing skill suite. It builds eight independently discoverable, self-contained Agent Skills shared by Pi and Codex from one governed monorepo.

Runtime and tooling require Python 3.10 or newer. Deterministic CI runs on the minimum supported Python 3.10 and current stable Python 3.14.

## Skills

| Skill | Responsibility |
| --- | --- |
| `commerce-growth-os` | Cross-domain Commerce diagnosis and orchestration |
| `commerce-commercial-strategy` | Unit economics, assortment, pricing, budget, creator, and channel decisions |
| `commerce-operations` | Store, live, campaign, service, refund, and execution SOPs |
| `commerce-analytics` | Metric contracts, funnels, attribution, cohorts, anomalies, and reviews |
| `consumer-marketing-os` | Integrated annual, launch, and cross-Marketing orchestration |
| `brand-strategy-communications` | Brand platform, PR, spokespersons, sponsorships, partnerships, and crisis |
| `content-creative-social-marketing` | Content systems, creators, social platforms, briefs, scripts, and creative QA |
| `growth-performance-lifecycle-marketing` | Paid growth, search, experiments, CRM, retention, and lifecycle |

Platform and category knowledge are overlays, not independently discoverable Skills.

## Architecture

```text
skills/       Skill source entrypoints and domain-private resources
shared/       Canonical contracts, category invariants, platform overlays, and currentness registry
eval/         Deterministic fixtures plus live selection, execution, and judge cases
tooling/      Build, validation, evaluation, installation, and release tools
scripts/      Stable task entrypoints and explicitly marked compatibility wrappers
skill-pack.json
```

Dependency direction is one-way:

```text
orchestrator -> specialist -> shared contract/overlay
```

Specialists do not read sibling Skill directories or parent-relative runtime paths. The builder materializes only declared resources into each self-contained bundle.

## Ownership rules

- Commercial Strategy owns economics, price, assortment, and budget constraints.
- Brand Strategy owns positioning, PR, spokespersons, sponsorships, long-term partnership/licensing rights, reputation, and exit.
- Content/Social owns organic content, creator briefs, creative direction, scripts, and KOL/KOC content usage rights.
- Growth owns paid media, search, experiments, CRM, retention, and marginal scale decisions.
- Operations owns platform execution, service, refunds, and operating cadence.
- Analytics owns metric definitions, evidence quality, attribution limits, and diagnosis.
- Category overlays contain only category-specific invariants.
- Platform overlays are partitioned by professional domain.
- Current platform claims require current authoritative verification.

One rule must have one canonical owner. Do not copy a framework into multiple Skills or overlays.

## Validate

Run the complete deterministic gate:

```bash
bash scripts/validate.sh
```

The gate validates:

- Eight self-contained bundles
- Bundle reference links and domain isolation
- Dependency-free, repository-owned Skill schema validation
- Static routing-hint compatibility matrix and manifest/tag release contract
- Structured Judge, private live-evidence writer, official-source reachability, atomic release, and offline verifier self-tests
- Fourteen Commerce Golden Answers with universal and domain-specific contracts
- Eight Marketing Golden Answers
- Source registry, unit economics, and transactional installer regressions

Run saved-answer suites directly:

```bash
bash scripts/run_eval.sh eval/golden-answers
bash scripts/run_eval.sh eval/marketing/golden-answers eval/marketing/cases.json
```

`scripts/smoke_eval.sh` is retained for one compatibility window and prints a deprecation warning before delegating to `scripts/validate.sh`; the complete deterministic gate is already fast enough that a second, divergent smoke contract would add maintenance cost without useful feedback.

## Build and install

Preview the owned installation targets:

```bash
bash scripts/install.sh --dry-run
```

Install the complete pack to the canonical root:

```bash
bash scripts/install.sh
```

The default canonical active registry is `~/.agents/skills`. Do not maintain a
second active copy of this pack under `~/.codex/skills`; Codex also discovers
the shared registry used by Pi.

Build without installing:

```bash
bash scripts/install.sh --build-only --output /tmp/consumer-brand-skill-pack
```

Install one Skill or use another root:

```bash
bash scripts/install.sh --skill commerce-analytics
bash scripts/install.sh --install-root /path/to/skills --skill commerce-growth-os
```

Verify installed content against fresh bundles:

```bash
python3 tooling/installation/verify_install.py
```

Run the local maintenance Doctor:

```bash
python3 tooling/validation/skill_pack_doctor.py
```

The Doctor reports version, canonical parity, duplicate discovery roots, stale staging/backup paths, Codex CLI version, and repository state. The manifest treats `~/.codex/skills` as a secondary discovery root so legacy copies can be detected and removed after canonical parity passes. Content-identical duplicates are warnings; mismatched duplicates are errors.

The installer does not prune unrelated Skills. It stages all selected bundles, backs up owned targets, activates the full set, and rolls back on failure.

Installation is single-writer and journaled. Installer/journal schema v2 binds the transaction to pack name/version, installer version, a unique transaction ID, Manifest-owned Skill names, and each staged tree digest. Recovery validates the complete journal before changing any file; legacy schema-v1 journals fail closed rather than being guessed or migrated in place. A concurrent writer, stale staging/backup path, user-controlled ancestor symlink, special file, unfinished journal, or stale `.consumer-skill-pack.install.lock` fails closed. `KeyboardInterrupt` and other in-process interruptions receive best-effort rollback. After a process kill or host crash, first use the Doctor and system process state to confirm that no installer is running, then recover only the pack-owned transaction paths:

```bash
bash scripts/install.sh --recover-only --force-stale-lock
```

Pre-commit recovery restores the old targets; committed recovery keeps the new targets and finishes backup cleanup. A post-commit cleanup failure therefore leaves the new version active, returns non-zero, preserves its journal and backup, and requires `--recover-only` instead of claiming a complete success. SIGKILL and power-loss behavior is recovered from filesystem state and the journal; it cannot be rolled back inside the terminated process.

## Live evaluation

Real live evaluation is intentionally separate from normal CI.

For a staged three-domain pilot, use the [minimal live acceptance plan](eval/live-acceptance.md) and its [argument manifest](eval/live-acceptance-plan.json). These are preparation artifacts, not an execution authorization: the proposed cap is 13 model calls, and host loading evidence plus an explicit model/cost budget remain prerequisites. A valid no-Skill control is not yet available.

The manifest `routing_terms` and `tooling/validation/check_routing.py` are deterministic compatibility hints; they are not proof of Codex runtime selection. The live selection layer is a `description-routing-probe`: an isolated model reports the minimal Skill set it would choose from installed descriptions. It records `auto_activation_verified=false`; it is not a Codex runtime activation receipt.

`routing_terms` remains in schema v2 for repository-external Pi/provider compatibility. Do not remove it until those consumers are checked and migrated; routing confidence comes from the probe plus explicit-Skill execution, not from keyword presence alone.

```bash
python3 tooling/evaluation/run_forward_routing_eval.py --output eval/answers/forward-routing.json
```

Run one bounded selection -> explicit-Skill execution -> semantic-judge regression:

```bash
bash scripts/run_quality_regression.sh \
  --case-id full_commerce_plan \
  --max-model-calls 3 \
  --max-total-seconds 600
```

Run the complete 22-selection / 9-execution / 9-positive-judge / 10-negative-calibration suite only when the model-call and time budget are acceptable:

```bash
bash scripts/run_quality_regression.sh \
  --model gpt-5.6-sol \
  --reasoning-effort high \
  --timeout 900 \
  --max-model-calls 50 \
  --max-total-seconds 7200 \
  --inter-call-delay 5
```

The fixed structured-Judge fixtures separately contain 12 positive answers across all eight domains and ten negative answers. Positive fixture coverage is a deterministic contract check; it does not establish live Judge accuracy. The standalone Judge accepts `--model MODEL --reasoning-effort high`; the default effort remains `medium`, and the requested effort is recorded in the evidence metadata.

`--reasoning-effort` applies to selection, execution, generated-answer Judge, and negative calibration; it is recorded in the plan and metadata. Its default remains `medium`.

The supplemental `eval/structured-judge/economics-regression-cases.json` pairs two verbatim failed live answers with two edited positive controls for order-population scope and revenue/refund/target-profit accounting. Its contract is part of repository validation. Run it explicitly with `run_structured_judge.py --cases eval/structured-judge/economics-regression-cases.json --model MODEL --reasoning-effort high --max-model-calls 4 --output /path/to/new-report.json`; it does not change the default 50-call suite. Edited controls test Judge discrimination, not fresh Skill generation. Original failure hashes are `a81fe551e4fa99c1784f1299af87cb3173b9f9fa89e1d8d4ebca54ad22307e80` and `06f9175a4ef4c821e02af7b088506d752e471a15850bc52658bc2edb37d7c34e`.

The default full-suite guard is 50 model calls and 3,600 seconds; the current fixture-derived worst case is exactly 50 calls (22 + 9 + 9 + 10) at one judge attempt per case. Execution generation usually dominates elapsed time, so the full command above explicitly allows 900 seconds per call, 7,200 seconds overall, and five seconds of provider pacing between calls. A narrow `--case-id` run defaults to selection, execution, and positive judge only; it does not silently spend calls on the full negative-calibration suite.

Every live model call uses a neutral temporary working directory, sends the prompt on stdin, ignores user configuration and rules (therefore user-configured MCP servers), and requests an ephemeral read-only Codex sandbox. This isolates mutable user configuration and repository context; it is not an OS-level proof that the built-in model runtime has no read-only tool surface. On timeout or Python cancellation, the runner terminates the invocation's POSIX process group (or Windows process tree) before returning. The default main-thread CLI also unwinds on SIGTERM and exits with status 143 after cleanup; embedded callers retain responsibility for their custom signal handlers. SIGKILL, host crashes, and intentionally detached processes remain outside this cleanup boundary.

Live selection and execution support only the manifest's default discovery root. A non-default `--install-root` fails before verifier or model calls because that argument cannot redirect Codex runtime Skill discovery. Custom roots remain supported by build/install/parity tools. Installation parity and a non-empty generated answer do not prove that the requested Skill loaded: live metadata and execution results record `runtime_skill_loading_verified=false` until a host loading receipt is available.

The execution adapter now requests JSONL events and includes a payload-free `execution_events` summary in explicit execution results. Event counts and token usage are diagnostic only; even a claimed `skill.loaded` event cannot establish loading under this adapter. See the [host capability audit](eval/host-loading-evidence.md) for the verified protocol boundary.

An opt-in POSIX-only App Server execution adapter is available with `run_execution_eval.py --backend app-server --model MODEL`, or `run_quality_regression.py --execution-backend app-server --model MODEL`. It sends an explicit Skill input and records a `skill_input_receipt`, but acceptance is not an injected-content attestation. It uses a fresh temporary `CODEX_HOME` and does not reuse saved login files; one local-proxy real turn has passed with `gpt-5.6-sol` and observed `high`; other providers and environments remain unverified. Use `--reasoning-effort high` on the standalone execution entry to request that effort explicitly. See the [host capability audit](eval/host-loading-evidence.md) before using it.

If authentication is routed through a non-default provider, `--ignore-user-config` intentionally removes that provider too. Re-declare only its non-secret transport fields with repeated `--codex-config` arguments, for example `model_provider`, `model_providers.<id>.name`, `base_url`, `wire_api`, `requires_openai_auth`, and `supports_websockets`. The runner allowlists those keys, rejects credentials or userinfo-bearing URLs, and records the key list plus an override-set SHA-256; API keys/tokens must remain in Codex auth or the process environment and must never be passed on the command line.

The execution layer invokes each installed Skill explicitly. The judge hashes the actual answer files, and the calibration layer requires known bad answers to be rejected. Selection, execution, judge, and calibration evidence records active Bundle tree digests, discovery roots, prompt/answer/input hashes, raw structured selection/judge responses, per-layer requested and observed models, duration, and exact selected case IDs. `--inter-call-delay` is applied before every model call except the first, including repeated and boundary judge attempts; no delay is added after the final call. Use `--selection-model`, `--execution-model`, and `--judge-model` when the layers need different models; `--model` is the common fallback. Active-install parity fails before any model call when source and installed Bundles differ.

Each non-dry run creates a unique private `eval/answers/quality-regression/run-<timestamp>-<random>/` directory. The run directory is mode `0700`, artifacts are mode `0600`, generated answers are write-once within the run, and `checkpoint.json` is atomically refreshed after every case so an interrupted run remains diagnosable. An explicitly supplied `--output-dir` must be a new empty real directory and cannot traverse a symlink ancestor.

Static Golden Answers remain calibration fixtures. The following command proves only that the rubric/schema can distinguish those fixtures; it does not prove current Skill-generated answer quality:

```bash
python3 tooling/evaluation/run_structured_judge.py --output eval/answers/structured-judge.json
```

Audit public official-source entry-point reachability without storing page bodies, credentials, or authenticated state:

```bash
python3 tooling/evaluation/audit_source_registry.py \
  shared/currentness/currentness-official-sources.md \
  --output eval/answers/official-source-reachability.json \
  --fail-on never
```

The reachability artifact always records `content_freshness_verified=false` and `capability_currentness_verified=false`. A reachable URL does not prove a feature, policy, fee, eligibility rule, or backend field is current; answer-level official/backend evidence is still required.

`eval/answers/` is ignored. Live evidence is local unless explicitly promoted to a release artifact. Normal pull-request CI is deterministic and does not spend model calls.

## Release

`skill-pack.json` defines:

- Manifest schema version
- Pack semantic version
- Minimum compatible installer version
- Skill source, routing terms, and materialized resources

Validate a release or tag:

```bash
python3 tooling/validation/check_release.py
python3 tooling/validation/check_release.py --tag v2.2.0
```

Build a release archive only from a clean commit and a passing full quality-regression artifact produced from that exact commit:

```bash
bash scripts/build_release.sh \
  eval/answers/quality-regression/run-<timestamp>-<random>/quality-regression.json
```

The command reruns deterministic validation, performs an isolated real install and parity check, and stages a deterministic three-file artifact set under `dist/`. Archive, versioned attestation, and checksum are fully written and fsynced, verified locally, then published together by one same-filesystem directory rename to `dist/v2.2.0/`. Before packaging, the gate requires an unlocked completed checkpoint, a colocated exact answer-file set, one explicit model shared by all release-quality layers, and recomputes canonical prompt/answer/response hashes, structured scores, pass decisions, medians, votes, durations, call counts, and result/checkpoint parity. An existing version directory, stale same-version staging directory, output-root symlink, partial or internally inconsistent quality results, substituted cases/rubrics/schemas/calibration answers, dirty-source evidence, stale Git SHA, Manifest hash mismatch, or installation mismatch fails closed without overwriting an existing release. The quality run remains local self-attested evidence: these checks make casual or inconsistent forgery fail, but do not cryptographically prove that an external model provider executed the calls.

Verify the final artifact set without network access or the original repository state:

```bash
python3 tooling/build/verify_release.py dist/v2.2.0
```

The verifier requires exactly the archive, its two-entry SHA-256 file, and the versioned attestation; rechecks archive/attestation binding, tar prefix, normalized metadata, safe member types, per-Skill `SKILL.md`, and canonical Bundle tree hashes without extracting the archive. New attestations explicitly record `quality_evidence_trust=self-attested-local` and `quality_execution_authenticity_verified=false`. This proves artifact-set integrity and internal provenance consistency, not publisher identity, external model execution, or the unavailable contents of the quality-evidence file. `dist/` remains local/ignored until an explicit release action is authorized.

GitHub CI validates source pushes, pull requests, and tag/version parity on Python 3.10 and 3.14, performs a real install under `${RUNNER_TEMP}`, and verifies installed parity without touching a user's Skill registry. A tag is a source-version marker, not proof that a release archive was produced. Archive/checksum/attestation generation remains the explicit local release command above until an authorized trusted release runner and artifact-upload workflow exist. A separate scheduled/manual workflow audits official-source entry-point reachability and uploads bounded evidence.

This repository currently has no public reuse license. Selecting a license is an owner/legal decision and is intentionally not inferred by tooling.

## Adding a new domain

Do not create an empty Skill for organizational symmetry. A new Skill requires:

1. A distinct user intent and trigger boundary.
2. An independent workflow, owner, and output contract.
3. Knowledge that cannot remain a shared overlay or specialist reference.
4. At least four representative evaluation cases.
5. Positive and negative routing evidence.
6. A self-contained bundle with no sibling runtime dependency.

Future Product, Supply Chain, and `consumer-brand-os` Skills should be added only after these gates are satisfied.
