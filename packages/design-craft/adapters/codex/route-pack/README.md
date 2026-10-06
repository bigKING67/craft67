# Codex frontend route pack

This pack documents how to keep the local Codex frontend routing layer
auditable and portable without copying all of `~/.codex` into this repository.

`design-craft` treats the local Codex route planner and platform detector as
runtime authority for task tiering, `web|ios|android|adaptive` resolution,
skill candidates, and browser/native evidence policy. The source files still
live in the Codex home directory; this adapter provides a safe manifest/export
workflow for migration or backup.

## Manifest authority

The only file-list authority is:

```text
~/.codex/tools/frontend_route_pack_manifest.json
```

The route-pack helper selects entries with `route_pack=true`; the global
snapshot selects entries with `snapshot=true`. Every required route-pack file
must also be snapshot-covered. The helper rejects an unknown manifest schema,
duplicate or unsafe paths, symlinks or resolved paths outside the source root,
invalid field types, and a manifest that does not include itself as a required
route-pack file.

The current required route-pack core includes:

```text
AGENTS.md
rules/frontend.md
agents/worker.toml
tools/frontend_route_pack_manifest.json
tools/frontend_route_plan.sh
tools/frontend_route_core.py
tools/frontend_route_authority.py
tools/frontend_route_evidence.py
tools/frontend_route_browser.py
tools/frontend_route_browser_capture.py
tools/frontend_route_browser_capture_sanitize.py
tools/frontend_route_browser_capture_store.py
tools/frontend_route_browser_contract.py
tools/frontend_route_browser_receipt.py
tools/frontend_route_browser_receipt_core.py
tools/frontend_route_browser_receipt_reducer.py
tools/frontend_route_delivery.py
tools/frontend_route_runtime.py
tools/frontend_route_telemetry.py
tools/frontend_platform_detect.py
tools/frontend_agent_routing.json
tools/frontend_agent_routing.schema.json
tools/frontend_route_schema_validate.py
tools/frontend_worker_entry.sh
tools/frontend_worker_route_core.py
tools/frontend_worker_payload_core.py
tools/frontend_preflight_spec.json
tools/frontend_preflight.py
tools/frontend_preflight_run.sh
tools/frontend_preflight_verify.sh
tools/frontend_preflight_policy.json
tools/frontend_preflight_policy_run.sh
tools/frontend_preflight_report.sh
tools/frontend_preflight_log_summary.sh
tools/frontend_preflight_log_rotate.sh
tools/frontend_preflight_log_maintenance.sh
tools/templates/frontend-preflight-ci.yml
tools/tests/test_frontend_route_plan.sh
tools/tests/test_frontend_route_evidence.py
tools/tests/test_frontend_browser_capture.py
tools/tests/test_frontend_browser_lifecycle_receipt.py
tools/tests/test_frontend_browser_lifecycle_receipt.sh
tools/tests/test_frontend_route_telemetry.sh
tools/tests/test_frontend_route_contract.sh
tools/tests/test_frontend_delivery_contract.sh
tools/tests/test_frontend_preflight.sh
tools/tests/frontend_preflight/common.sh
tools/tests/frontend_preflight/test_gate.sh
tools/tests/frontend_preflight/test_route.sh
tools/tests/frontend_preflight/test_observability.sh
tools/tests/frontend_preflight/test_policy.sh
tools/tests/frontend_preflight/test_state_concurrency.sh
tools/tests/test_frontend_preflight_spec_sync.sh
```

`frontend_authority_init.sh` remains an optional helper. Policy, report, and log
scripts are required because the self-contained frontend verifier invokes them
unconditionally. The global `agents_quality_verify.sh` remains snapshot-covered
but is not part of this frontend-only pack because it depends on investment,
periodic-runner, prompt-stack, and global-snapshot files outside the pack.

The pack intentionally excludes credentials, browser profiles, MCP state,
session logs, caches, and unrelated Codex configuration.

## Audit current local state

```bash
python3 scripts/design_craft_codex_route_pack.py --strict
```

This prints:

- schema version
- source root
- required-file status
- missing required files, if any
- manifest schema, selected/required counts, and required snapshot coverage
- routing JSON Schema validation plus V2 semantics and stale-model checks
- split authority, browser, delivery, runtime, and telemetry module contracts
- deterministic browser lifecycle receipt contract tests with negative fixtures
- browser/runtime tool parity probes for external and local contexts
- a verified `gpt-5.6-sol/max` environment-runtime truth probe with session
  discovery disabled
- a bounded `frontend-route.compact.v1` output probe that omits the repeated
  static delivery contract
- an unauthorized GPT-5.6 `ultra` runtime-conflict denial probe
- a privacy-safe telemetry self-check that remains isolated from inherited test
  context
- PRODUCT.md/codebase platform detection and native-runtime evidence boundaries
- redacted runtime model/profile compatibility from `config.toml`
- bundled model-catalog compatibility for configured reasoning levels

For machine-readable evidence:

```bash
python3 scripts/design_craft_codex_route_pack.py --strict --json
```

The JSON manifest records file paths, size, SHA-256, executable bit, whether
each file is required, and a redacted `semantic_validation` result. It reads
only model/profile fields from `config.toml`; credentials, MCP settings,
provider URLs, browser state, and unrelated configuration are never exported.
Strict route probes also disable route telemetry writes and current-session
discovery, so an audit neither pollutes production latency history nor reads the
caller's session JSONL.

## Route output modes

### Consolidated design capabilities

The canonical Skill owns the reusable design guidance. The host route must
not require the retired independent `image-to-code`, `imagegen-frontend-web`,
`gpt-taste`, `high-end-visual-design`, or `full-output-enforcement` installations.
Keep `design-craft` in `candidate_skills` and expose only relevant internal
paths in `design_craft_conditional_references`:

| Requested work | Internal reference |
| --- | --- |
| Implement a supplied/selected image | `references/image-reference-implementation.md` |
| Generate web concept images | `references/web-image-direction.md` |
| Editorial/tactile or expressive promotion | `references/visual-judgment.md` |
| Motion-led promotion | `references/motion-quality.md` |

Existing `--style high-end` and `--style gpt-taste` values remain compatible
direction aliases, not external Skill names. An internal direction must be
explicitly carried through preflight with the design-craft baseline; it cannot
bypass DESIGN authority or coexist ambiguously with an external style preset.
Ordinary UI work does not load image references, and image-only work does not
imply implementation. Complete output is a host delivery requirement, not an
automatic design mode. Other specialized Skills are outside this retirement.

The route implementation remains host-owned under `~/.codex`; this contract
and the canonical Skill references are repository-owned. Update the scoped host
route/preflight files and tests, verify them, and export the whitelisted pack
for recovery. Do not maintain a second copy of the whole host implementation
inside the Skill. A Skill install alone neither updates host policy nor removes
old installations. Verify both before retiring exact old installation targets.

Use the smallest output that matches the consumer:

```bash
bash ~/.codex/tools/frontend_route_plan.sh ... --output compact-json
bash ~/.codex/tools/frontend_route_plan.sh ... --output human
bash ~/.codex/tools/frontend_route_plan.sh ... --output json
```

`compact-json` is the normal agent-context format. It returns current route,
authority, runtime, execution, quality, validation, and telemetry decisions plus
versioned contract references. `human` is for interactive inspection. Full
`json` remains available for contract audits and compatibility consumers.

Reference-image evidence is an explicit route axis:

```bash
bash ~/.codex/tools/frontend_route_plan.sh ... \
  --has-reference-image 1 \
  --evidence-mode <comp-fidelity|sealed-rendition>
```

`comp-fidelity` routes measurement over existing comparable captures and does
not request a capture runtime or imply visual acceptance. `sealed-rendition`
routes a web capture plan, hash-bound artifacts, strict closeout, and a final
named-reviewer decision. Neither mode defines a global pixel pass threshold.

## Export a migration bundle

Write a whitelisted copy outside the repo:

```bash
python3 scripts/design_craft_codex_route_pack.py \
  --strict \
  --export-dir /tmp/design-craft-codex-route-pack
```

The export writes:

```text
/tmp/design-craft-codex-route-pack/
├── AGENTS.md
├── agents/worker.toml
├── rules/frontend.md
├── tools/frontend_route_pack_manifest.json
├── tools/frontend_route_core.py
├── tools/frontend_worker_route_core.py
├── tools/frontend_worker_payload_core.py
├── tools/frontend_agent_routing.schema.json
├── tools/frontend_route_schema_validate.py
├── tools/...
└── codex-route-pack.manifest.json
```

Use `--dry-run` before writing:

```bash
python3 scripts/design_craft_codex_route_pack.py \
  --export-dir /tmp/design-craft-codex-route-pack \
  --dry-run
```

## Validate after restore

After restoring the bundle into another Codex home, run:

```bash
bash ~/.codex/tools/frontend_preflight_verify.sh
```

This verifier owns the restored frontend pack's complete test chain. It still
uses the target host's valid Codex runtime/configuration and installed skills as
external runtime prerequisites, but has no investment, periodic-runner,
prompt-stack, or global-snapshot file dependency. Do not run the global
`agents_quality_verify.sh` as a frontend restore gate; it is valid only after
the wider Codex governance stack has also been restored.

### Host capture integration is separate

Restoring the portable code does **not** configure or trust a Hook, prove that a
Hook is active, or schedule retention. Do not export or overwrite the target
host's complete `config.toml` or Hook trust state. Instead, merge only this
targeted fragment, replacing both placeholders with trusted absolute paths on
the target host:

```toml
[[hooks.PostToolUse]]
matcher = "^mcp__tmwd_browser__browser_tab_lifecycle$"

[[hooks.PostToolUse.hooks]]
type = "command"
command = "PYTHONDONTWRITEBYTECODE=1 /absolute/path/to/python3 /absolute/path/to/.codex/tools/frontend_route_browser_capture.py --ingest-hook"
timeout = 2
statusMessage = "Recording browser lifecycle receipt"
```

The exact matcher observes lifecycle calls only; it does not intercept every
`tmwd_browser` tool and cannot invoke `finalize_task`. After changing the Hook,
start a new Codex session, review/trust it there, and establish live evidence:

1. Run the route planner for a browser67 route and confirm the capture binding
   is `bound`.
2. Complete a real managed lifecycle entry call and confirm an observation was
   captured with `receipt_valid=true` while `runtime_complete=false`.
3. Explicitly call scoped `finalize_task`, then confirm the receipt is valid,
   `runtime_complete=true`, and its lifecycle state is `finalized`.
4. Confirm browser67 reports no managed-tab residue and capture health reports
   no errors.

`frontend_route_browser_capture.py --status` emits
`frontend-route.browser-capture-status.v2`. Treat health counters as persisted
history only when `health_persisted=true` and `health_status=persisted`. When the
health file has not been initialized, zero counters are synthesized status
defaults, not evidence of a healthy history.

Retention is also host integration. Schedule this command separately if the
wider global periodic runner is not installed:

```bash
PYTHONDONTWRITEBYTECODE=1 /absolute/path/to/python3 \
  /absolute/path/to/.codex/tools/frontend_route_browser_capture.py --prune
```

The prune contract removes incomplete state after 7 days and complete state
after 30 days, retains at most 1,000 incomplete states, and retains at most 100
complete receipts. Unit tests, configured Hook text, and synthesized zero health
alone are never live capture or retention-scheduler proof.

## Runtime truth and privacy boundary

Runtime model/reasoning resolution uses this evidence order:

```text
paired CODEX_EFFECTIVE_MODEL / CODEX_EFFECTIVE_REASONING
> current CODEX_THREAD_ID session's latest turn_context model/effort
> config.toml candidate values, explicitly unverified
```

Session discovery reads only `turn_context` records and only the `model`,
`effort`, `turn_id`, and `current_date` fields. Route output discloses only a
Codex-home-relative evidence path and marks `contains_prompt_data=false`; it
does not return prompts, messages, tool payloads, or absolute home paths.

## Route telemetry boundary

The planner appends privacy-safe `frontend-route.telemetry-event.v2` events to
`~/.codex/logs/frontend_route_telemetry.jsonl` by default. New events separate
`planned_execution_mode` from `actual_subagent_state` and do not contain the
ambiguous legacy `execution_mode` field. Events contain only bounded enums,
booleans, counts, and millisecond timings. They do not contain task prose,
source code, PRODUCT/DESIGN paths, tokens, credentials, or session content. The
default log rotates at 2 MB with seven retained files.

Use `FRONTEND_ROUTE_TELEMETRY_CONTEXT=prod|test|ci` to isolate histories and
`FRONTEND_ROUTE_TELEMETRY_LOG_ENABLED=0` for probes or tests that should not
write. Summarize production latency and quality with:

```bash
python3 ~/.codex/tools/frontend_route_telemetry.py \
  --include-rotated \
  --context prod \
  --min-events 50 \
  --max-p95-ms 1000 \
  --json
```

`frontend-route.telemetry-summary.v2` reads mixed v1/v2 history without
rewriting or deleting legacy events. It normalizes v1 `execution_mode` into the
planned field, derives the bounded actual state from `agents_spawned`, and
reports source-schema counts so legacy coverage remains auditable. The summary
reports p50/p95/max durations, route/tier/platform/tool/runtime source and
planned/actual distributions, parse/ignored-schema counts, and the privacy
marker. The general route test and release route smoke disable telemetry; the
dedicated telemetry test owns append, mixed-version compatibility, context,
rotation, summary, and self-check coverage.
Do not use a smaller sample to claim production stability; before 50 events,
report latency as provisional observation only.

## Browser lifecycle truth boundary

`planned_browser_lifecycle` is the route policy for browser67 ownership,
explicit adoption, workspace/task scoping, and finalization. The legacy
`browser_lifecycle` field remains an alias of that plan; neither field proves a
tab was created, adopted, released, or closed. Route-planner output sets
`actual_browser_lifecycle_state.state` to `not_started` for browser67 routes and
`not_applicable` for other runtimes. The planner payload is immutable planning
output and is not automatically updated after browser work. Runtime delivery
must report a separate actual receipt from browser67 outcome evidence,
including ownership, workspace/task scope, entry or adoption result, and the
scoped `finalize_task` delivery summary.

The portable host adapter is:

```bash
python3 ~/.codex/tools/frontend_route_browser_receipt.py \
  --route /path/to/saved-route.json \
  --observations /path/to/browser-lifecycle-observations.json
```

The observation document uses
`frontend-route.browser-lifecycle-observations.v2` and binds the canonical
route SHA-256, expected workspace/task scope, ordered call arguments, and the
exact `browser67.tool-outcome.v3` result. The adapter emits
`frontend-route.browser-lifecycle-receipt.v2`. V2 additionally binds Browser
Instance scope through privacy-safe references and fails closed on ambiguous
or cross-instance evidence. `receipt_valid` means the
binding and evidence normalized without ambiguity; `runtime_complete` is a
separate decision and requires a non-dry-run scoped finalizer with verified
closes, no remaining unkept tabs, and an exact cleanup delivery summary.
`inspect_adoption` alone remains read-only, an adopted tab must be released
without close, and a later entry/adoption makes an earlier finalize receipt
stale. The receipt omits URLs, titles, tab IDs, adoption tokens, and lease IDs.
Browser67 request IDs are represented only by bounded SHA-256 references, not
copied verbatim.

Browser67 derives cleanup scope from identifiers: when `workspace_key` is
present the live scope is `workspace`, while `task_id` remains an additional
filter/correlation field. Task-only scope requires omitting `workspace_key`.
The receipt normalizes live `close_scope.workspaceKey/taskId` into canonical
snake_case and fails closed when an explicit call scope disagrees with the live
scope.

The adapter is a normalizer, not a cleanup dispatcher. When the host integration
above is separately configured and trusted, its exact `PostToolUse` matcher
observes only `mcp__tmwd_browser__browser_tab_lifecycle`.
`frontend_route_browser_capture.py` binds the planner's privacy-safe route view
to the current session/turn, sanitizes the completed lifecycle call in memory,
and atomically replaces one repo-external capture state. It never persists raw
hook payloads, URLs, titles, tab IDs, adoption tokens, lease IDs, or raw request
IDs. The Hook records results but cannot invoke `finalize_task` through Codex's
active MCP client, so the main agent must still run scoped finalization
explicitly. Root `capture-health.json`, when persisted, contains only the last
safe error code/epoch and aggregate error, missing-binding, and
dropped-observation counters.

## Screenshot policy boundary

The route pack owns the operational screenshot decision:

```text
screenshot_evidence_level = none | optional | required
```

Global rules should state the principle. The route planner should decide the
actual evidence level from task surface, intent, scope, reference fidelity,
responsive risk, motion risk, and page-level visual impact.

## Platform and runtime boundary

The route pack resolves platform in this order:

```text
explicit --platform
> nearest PRODUCT.md ## Platform
> codebase detection
> default web
```

`surface=mobile` does not imply native. Web shells remain `web`; React
Native/Expo, Flutter, KMP, and real iOS plus Android targets resolve to
`adaptive`. Route output exposes `platform_source`, confidence, signals,
contradictions, `runtime_validation_kind`, `native_validation_required`, and
`preferred_runtime_tool`. Static scan/fixture success is never simulator,
emulator, or device proof.

## Model and delegation boundary

The route pack validates these V2 invariants:

- the main agent owns every tier by default
- route files use `agent_model=inherit` instead of pinning a model version
- tier alone never sets `subagent_required=true`
- parallel work requires at least two independent tasks, bounded write scopes,
  clear benefit, and user or project authorization
- unavailable delegation falls back to `continue_main_and_report`
- `worker.toml` inherits model and reasoning from the parent/runtime profile
- explicit reasoning overrides support `low` through `max`; GPT-5.6 `ultra`
  remains runtime-profile-only because its model-catalog semantics include
  automatic task delegation
- configured runtime models and reasoning levels exist in the bundled Codex
  model catalog
