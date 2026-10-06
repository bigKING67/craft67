# Validation contract

Use this before calling frontend work complete.

## Contents

- [Minimal command ladder](#minimal-command-ladder)
- [Route planner argument hygiene](#route-planner-argument-hygiene)
- [Browser validation](#browser-validation)
- [Screenshot evidence](#screenshot-evidence)
- [Visual review completion](#visual-review-completion)
- [Prototype validation](#prototype-validation)
- [Native runtime validation](#native-runtime-validation)
- [Design-system validation](#design-system-validation)
- [Evidence boundaries](#evidence-boundaries)
- [Output and finding budgets](#output-and-finding-budgets)
- [Route summary fields](#route-summary-fields)
- [Quality score](#quality-score)
- [Cross-agent validation](#cross-agent-validation)
- [Unverified work](#unverified-work)

## Minimal command ladder

Pick the smallest command set that covers the change:

- Type-only or props change: type-check.
- Styling/component change: type-check plus lint if available.
- Build-system or route change: type-check, lint, build.
- Data behavior: relevant unit/integration tests plus type-check.
- Visual/report/dashboard work: type/lint/build as relevant plus browser smoke.
- Native UI work only when the resolved target is `ios`, `android`, or
  `adaptive`: platform build/static checks plus simulator/emulator or real
  device validation when the toolchain exists. Native gates are not part of an
  ordinary Web/desktop task.
- Performance work: baseline and after measurement when possible.

Prefer project scripts in `package.json`. Do not invent commands when the repo
has established ones.

For installed or source Skill runtime checks, resolve `DESIGN_CRAFT_RUNTIME`
to the absolute loaded Skill directory as described in `SKILL.md`. Invoke the
following `scripts/...` paths through that root, using `bash` for `.sh` and
`python3` for `.py`; pass the target explicitly rather than relying on cwd:

- `scripts/design_craft_route.sh --target <repo> --surface <surface> --intent <intent> --scope <scope>`
- `scripts/design_craft_platform_scan.py --target <repo> --platform auto --json`
  for platform inference and conservative native source findings.
- `scripts/design_craft_pass.sh --target <repo> --mode <critique|audit|prototype|system-review|polish|motion|harden|optimize|structure|architecture>`
  as the preferred neutral pass wrapper.
- `scripts/design_craft_audit.sh --target <repo> --mode <critique|audit|prototype|system-review|polish|motion|harden|optimize|structure|architecture>`
  as the compatibility entrypoint behind the pass wrapper.
- `scripts/design_craft_detect.sh --target <path>` for upstream Impeccable
  findings plus local design-craft review signals. Default and `--full-json`
  output disclose whether the upstream detector is `available`,
  `available_regex_fallback`, or `unavailable`; the fallback is degraded because
  optional static HTML/CSS parser dependencies are absent. Use `--json-only`
  only when raw upstream detector compatibility is required, because raw output
  intentionally omits wrapper capability metadata. `available` means the
  wrapper found an invocable detector and no known source-checkout parser gap;
  when that source static engine is present, its dependency probe passed. This
  does not by itself prove that a particular HTML target or every static rule
  was exercised.
- `scripts/design_craft_seed_design.sh --target <project-dir>` when a new or
  weak developer-product surface needs the bundled original `DESIGN.md`
  pair as its initial design-system authority.
- `scripts/design_craft_taste_review.sh --target <screenshot-or-project>`
  when a product UI taste score or screenshot critique needs a stable review
  packet before implementation.
- `scripts/design_craft_browser_evidence.py --print-js` to emit a redacted
  DOM/computed-style sampler for TMWD `browser_execute_js`.
- `scripts/design_craft_browser_evidence.py --validate-score-json <path>` and
  `--validate-evidence-json <path>` to guard product UI score inflation and
  captured browser evidence schema.
- `scripts/design_craft_css_smell_scan.py --target <path>`,
  `scripts/design_craft_focus_audit.py --target <path>`, and
  `scripts/design_craft_token_audit.py --target <path>` to collect static UI
  smell signals. Treat these as review prompts, not automatic design verdicts.
- `scripts/design_craft_static_review.py --target <path> --json` when a single
  normalized static review packet is easier to attach to an agent handoff.

The following maintenance commands require the design-craft **source repository
root** as cwd. They are not part of an installed Skill's `scripts/` directory.
Do not try to run them from the target project or infer a sibling source checkout:

- `scripts/design_craft_doctor.sh --target <path>` for local portability and
  optional capability checks.
- `scripts/design_craft_codex_route_pack.py --strict` to audit the local Codex
  frontend route planner, frontend rule, preflight contract, and route tests as
  a whitelisted migration manifest.
- `scripts/design_craft_cross_agent_validate.py --root evals/cross-agent` for
  benchmark task definitions, and `--observed-task <task-dir>` only after real
  agent outputs have been recorded.
- `scripts/design_craft_init_agent.sh --agent <codex|cursor|claude|pi|generic>
  --target <path> --dry-run` before installing the canonical skill into another
  host agent.
- `scripts/design_craft_score.py --self`
- `scripts/design_craft_maturity.py --profile development` for the repository
  development baseline. Its route-pack gate uses an isolated portable self-check
  and does not read operator `~/.codex` state. Run the explicit `--strict`
  route-pack command above when auditing an installed Codex host. Release
  maintainers use `--profile operational_95` or `--profile certified_100` with a
  committed matching-runner `--baseline`. Those names are evidence tiers with
  all-required gates, not composite quality scores. `design_craft_score.py`
  measures source completeness only.
- `scripts/upstream_absorption_report.py --remote` when checking whether pinned
  upstreams have newer remote heads before absorption work.
- `scripts/validate.sh`

## Route planner argument hygiene

Route planner arguments must use fixed enum values:

- `--surface`: `auto`, `dashboard`, `app`, `admin`, `data-app`, `landing`,
  `promo`, `homepage`, `marketing`, `mobile`, or `brand`.
- `--intent`: `auto`, `functional`, `visual-refine`, `redesign`, `new-page`,
  `high-motion`, `brand`, `mobile-flow`, or `reference-only`.
- `--scope`: `auto`, `micro`, `component`, `section`, `page`, or
  `multi-page`.
- `--platform`: `auto`, `web`, `ios`, `android`, or `adaptive`.
- `--product-context-path`: absolute path to optional `PRODUCT.md`.

Do not pass natural-language task descriptions as route argument values. Record
those notes in the plan or delivery summary instead.

### Existing-project authority and preflight diagnosis

Use the project's existing `DESIGN.md` or explicitly selected style authority
without changing its direction. When an isolated evaluation has no such
document, first inspect actual tokens, shared components, typography and
interaction conventions. Record that existing baseline in a Markdown file
inside the isolated lab, with source paths and Typography, Color, Motion and
Components sections. This is a record of evidence, not permission to redesign
or to add a document to the original read-only project. Missing evidence must
stay explicit; a generic seed does not prove an existing baseline.

For `STYLE_AUTHORITY_MISSING`, distinguish these causes in order:

1. The explicit absolute path exists and is a readable regular file.
2. The authority satisfies the active preflight's Markdown structure. The
   current Codex contract requires typography, color, motion/interaction and
   component section headings; a raw CSS/Stylus file alone does not meet it.
3. The route's applicability, intent and evidence requirements are satisfied.

When compact output hides the cause, inspect the existing full route output
(`--output json`) and underlying preflight diagnostic. Fix the input or state
the evidence gap; do not disable the gate, add empty headings just to pass, or
alter global route-pack files. A structurally valid document is not proof of
visual quality, and portable fallback readiness is not global-host parity.

## Browser validation

Use browser validation for:

- User-visible pages and components.
- Interactions, forms, navigation, uploads/downloads.
- Login-state or protected routes.
- Responsive behavior.
- Charts, reports, dashboards, canvas/SVG sizing.
- Motion, focus, hover, or keyboard behavior.

Default flow:

1. Start or identify the dev server.
2. Open the route in a managed browser tab when possible.
3. Check desktop and a narrow mobile viewport for layout overflow when visual
   changes are involved.
4. Inspect DOM/computed style only when needed to prove a specific condition.
5. Finalize managed tabs unless the user asked to keep them.

### Chart and report checks

When chart or report behavior changes, validate the rendered result against the
source data, not only against the expected layout:

- Trace displayed values, units, filters, aggregation, and rounding from source
  records to marks and labels.
- Verify zero baselines for length-encoded bars, visible zero crossings for
  diverging values, square-root radius scaling for area encodings,
  non-negative hierarchical weights for treemaps, and explicit normalized
  meaning for choropleth fills.
- Exercise negative, zero, missing, single-value, dense, extreme, and
  greater-than-100-percent inputs when those states are possible.
- Confirm color is not the only cue and that legends, direct labels, tooltips,
  focus, keyboard access, and Reduced Motion remain usable where applicable.
- Confirm tooltips and drill-down resolve to real queryable records instead of
  fabricated detail or precision.
- Check desktop and narrow layouts, long-label wrapping, empty states, tooltip
  clipping, and resize after a hidden container becomes visible.

Static schema, syntax, or catalog validation cannot prove visual correctness,
responsive layout, accessible interaction, data-binding truth, or runtime
performance. Report those boundaries separately.

### Lifecycle and repeated-instance checks

When changed UI owns state transitions, async resources, or repeated live
instances:

- Exercise every route into the same state that exists in the changed flow,
  including normal interaction, recovery/resume, observer callbacks, and hot
  replacement where applicable. Verify identical required finalization,
  progress, interaction, and notification side effects.
- Pause async setup at meaningful resource-creating `await` boundaries, then
  trigger teardown, unmount, replacement, or rapid reinvocation. Verify stale
  work cannot publish after losing ownership and that orphan DOM, canvas,
  WebGL, object URLs, observers, and handles are released.
- When repeated instances are possible, exercise at least two candidates,
  including an empty or stale first match when realistic. Verify stable
  identity or semantic ownership selects the active instance, and that batch
  rollback or cleanup restores the same captured instance set it changed.

Static source or source-shape tests can prove these guards exist, but they do
not prove browser timing, teardown ordering, or resource release. Keep runtime
behavior unverified unless the applicable browser or native path actually ran.

## Screenshot evidence

Use screenshot evidence when route output sets `browser_screenshot_required` or
when the visual decision depends on actual rendered style. Do not request
screenshots for every frontend change. Follow the route screenshot policy:

- `screenshot_evidence_level=none`: no screenshot artifact required, typical
  for micro copy, font, spacing, or color tweaks.
- `screenshot_evidence_level=optional`: capture only if rendered ambiguity,
  visual regression risk, or state coverage remains after code/browser checks.
- `screenshot_evidence_level=required`: produce screenshot artifact evidence,
  typical for section/page layout, redesign, new page, reference fidelity,
  responsive, state-heavy, mobile, or high-motion work.

When screenshots or rendered inspection are required, prefer at most two
batched verification passes: capture the necessary desktop, mobile, and state
set together; apply material fixes as one batch; then run one confirmation
pass. Do not start a per-tweak screenshot loop unless the user explicitly
requests live visual iteration.

Preferred flow with TMWD:

1. Use `browser_tab_lifecycle` with `action:"select_or_create"` and a stable
   `workspace_key` for the project or surface.
2. Use `browser_wait` for `selector`, `dom_stable`, or `network_idle` before
   capturing; do not use fixed sleeps as readiness proof.
3. Use `browser_screenshot_ops target:"viewport"` for baseline visual QA.
4. Use `target:"selector"` or `target:"clip"` for focused changed sections.
5. Use `target:"full_page"` only for bounded pages and pass an explicit
   `max_pixels`.
6. Report artifact `path`, `sha256`, `dimensions`, and `target`. Do not paste
   base64 or claim screenshot validation when no artifact was produced.
7. Finalize the managed tab with `browser_tab_lifecycle action:"finalize_task"`
   unless the user asked to keep it.

If `tmwd_browser` is unavailable, report the skipped reason, residual risk, and
the exact command/tool that should capture the artifact next. For L4
before/after evals, `scripts/design_craft_l4_capture.py --dry-run` may produce a
TMWD-first capture plan, and the non-dry-run Chrome-headless fallback may write
repo-external PNG artifacts plus `screenshots.json`; neither path verifies
interaction states unless separate state evidence is captured.

## Visual review completion

Every visible UI change must complete the lightweight consistency gate in
`system-review.md` before delivery. This is required even when the change is too
small to justify a full project-system inventory. The gate identifies the
semantic component family and project exemplar, compares sibling or equivalent
controls in the same applicable states, covers project themes when applicable,
and ends with `pass`, `blocked`, or `incomplete`.

When an approved comp, screenshot, or reference is authoritative, inspect it
directly and inventory its salient elements before reading the builder's
summary. Classify each applicable element as `match`,
`acceptable_adaptation`, `missing`, `contradicted`, or
`added_without_approval`. An adaptation must cite accessibility, responsive,
product, platform, safety, or explicit user-approval evidence.

Run the full `system-review` mode for whole-product or multi-page work,
design/visual/interaction/motion system changes, cross-family changes, explicit
system-level requests, or a known visual-language consistency regression. Do
not use the full mode merely to make a micro change look more rigorously tested.

When the host route exposes staged visual-review fields, consume them directly:

- `visual_review_mode=baseline_only` requires the baseline stage;
- `visual_review_mode=before_after` requires baseline and final stages;
- `visual_review_mode=final_only` requires the final stage;
- `final_visual_review_required=true` makes the final Design Craft closeout
  mandatory after rendered capture and before delivery;
- `visual_review_blocks_delivery=true` keeps unresolved P0/P1 findings from
  being reported as complete.

Screenshot attachment is not visual review. DOM geometry, target size, default
computed styles, scanner output, and test success are supporting evidence, not
system-consistency acceptance. A required state, theme, platform, or surface
that lacks decisive evidence keeps the status `incomplete`; a confirmed
unresolved P0/P1 keeps it `blocked`.

After fixes, revisit the original finding IDs and label each `resolved`,
`partial`, or `unresolved` from the same decisive routes, viewports, states,
themes, and references. A recapture or builder summary cannot by itself prove
resolution, and verification must not restart an unbounded defect hunt.

For web controls, visible keyboard focus remains mandatory. Text selection,
caret, underline offset, tabular numerals, and scrollbar styling are reviewed
when the project authority or changed surface owns them; browser defaults are
not automatic defects and universal custom styling is not required.

## Prototype validation

The `prototype` mode follows `prototype-workflow.md`. A plan or static golden
fixture can validate the workflow contract but cannot prove a runnable variant.
Before reporting `ready_for_selection`, verify every candidate in the
applicable browser/native runtime with the same realistic content and context,
one full-size evaluation view at a time, decisive interactions, keyboard/input
and focus behavior, required themes/viewports/states, and Reduced Motion.

Keep prototype exploration files separate from production files. Production
promotion requires explicit user selection or prior explicit delegated
selection, then the normal implementation ladder plus the lightweight
system-consistency closeout. Report cleanup as verified only after inspecting
the prototype route/story/preview/import boundary.

## Native runtime validation

For `ios`, `android`, or `adaptive`, static source scan is a floor rather than a
runtime verdict. Skip this section for `web`; a mobile viewport or WebView shell
does not create a native validation requirement.

Report route fields:

- `runtime_validation_required`
- `runtime_validation_kind`
- `native_validation_required`
- `preferred_runtime_tool`

iOS validation should distinguish `xcodebuild` compile/test, Simulator
(`simctl`) behavior, and real-hardware truth. Android validation should
distinguish Gradle compile/test, Emulator/`adb` behavior, and real-hardware
truth. Adaptive validation reports both platforms independently.

If the local machine lacks a simulator/emulator toolchain, run the conservative
platform fixture/source checks and report exactly:

- `iOS Simulator: unverified locally`, when iOS is in scope.
- `Android Emulator: unverified locally`, when Android is in scope.

Do not turn a static scan or CI fixture into an observed native runtime claim.

## Design-system validation

Use design-system validation when:

- A project `DESIGN.md` exists or is changed.
- Theme files, CSS variables, design tokens, Tailwind theme values, or shared UI
  component styles are changed.
- Light/dark mode, focus styles, motion primitives, form states, toast/error UI,
  or empty states are changed.
- A visual polish changes colors, typography, spacing, radii, shadows, or motion.

Check and report:

- Whether the design-system contract was enforced, evolved, inferred from code,
  or not applicable.
- Whether the bundled developer-product seed templates were used as the initial
  baseline, and whether the project had a stronger style authority.
- New hard-coded colors, arbitrary spacing, arbitrary radii, arbitrary shadows,
  font sizes, or timing values, and why they are justified.
- Light/dark token parity for the touched tokens and states.
- Visible `:focus-visible` for touched interactive elements.
- When a Web tablet target has no project standard, use 44 CSS pixels as a
  provisional comfort floor for effective interactive target size and label it
  for project ratification; project and native platform authority still wins.
- Disabled, loading, error, empty, and success states where the changed surface
  owns those states.
- UI copy quality for actions, errors, toasts, empty states, and loading labels;
  avoid weak labels such as `OK`, `Confirm`, `Submit`, `Success`, and
  `Something went wrong` when a specific action or recovery step is known.
- Static scanner findings, when used, with clear severity and target path. Do
  not present scanner findings as proof of visual quality without browser or
  runtime evidence.

## Evidence boundaries

- Live browser/native behavior outranks static inference. A screenshot proves
  rendered appearance, not hidden interaction states; source proves only the
  supplied code and explicit branches.
- When the required runtime cannot start, a committed visual-regression golden
  or screenshot fixture may be used only as a runtime-unavailable fallback
  after its exact target, repository provenance, freshness against current
  tokens/CSS/components/assets, viewport, theme, and variant are reconciled.
  This can support visible-layout hypotheses, but the task must remain
  `incomplete` and no browser/native success may be claimed.
- Contextual static signals such as fixed geometry, removed outlines, global
  booleans, easing, and shared transforms are review risks until complete
  ownership or runtime evidence rules out compensating behavior. Describe the
  failure condition as a hypothesis when the call path is incomplete.
- Do not infer perceived lag, smoothness, frame rate, compositing, layout shift,
  device feel, workload size, row count, concurrency, or usage frequency
  without measurement or explicit product/source evidence.
- A responsive repair must replace every cited fixed-width, minimum-width,
  column, drawer, or overflow blocker. Keep critical actions reachable and
  isolate unavoidable overflow to the data region.
- A loading, empty, error, permission, conflict, offline, partial, or recovery
  state is covered only when the result names what renders, what the user can
  do, what context survives, and how the behavior is verified.
- Direct-manipulation claims additionally follow
  `interaction-physics.md`; static source cannot prove gesture feel or velocity
  continuity.

## Output and finding budgets

Treat every explicit line, word, section, or item limit as a hard contract.
Draft to roughly 75 percent of the cap, count newline-delimited lines when a
line limit exists, and remove repeated prose or low-severity detail before
omitting required states or exceeding the limit.

Use one finding ledger for multi-section reviews. Record the source fact,
runtime hypothesis, implementation behavior, recovery action, and acceptance
once; later sections should reference the finding instead of restating it.
When the cap is 200 lines or fewer, use at most eight ledger entries unless an
exact larger count is required, and reserve at least one quarter of the budget
for detector reconciliation and validation.

For an uncapped critique or audit, default to one-sentence diagnosis, at most
five blocking and five secondary findings, at most eight concrete moves, and
the smallest validation plan that can change the decision. Target 150 lines or
fewer unless the user explicitly requests an exhaustive report.

## Route summary fields

Use `--output compact-json` for normal agent handoff/context ingestion and
`--output json` only when the complete static delivery contract is required.
Use `--output human` for interactive inspection. When route planner is used,
report:

- `frontend_tier`
- `design_tier` (must equal `frontend_tier` under `frontend-route-v2`)
- `platform`, `platform_source`, and `platform_confidence`
- `product_context_path`
- `candidate_skills`
- `selected_skills`
- `execution_mode` and `subagent_required`
- `style_authority_path`, source, mode, and revision policy
- `design_system_contract`
- `preflight_status` and `preflight_code`
- `browser_validation_required`
- `browser_screenshot_required`
- `visual_review_mode`
- `baseline_visual_review_required`
- `final_visual_review_required`
- `visual_review_contract`
- `visual_review_blocks_delivery`
- `preferred_screenshot_tool`
- `screenshot_validation_plan`
- `directory_governance_required`
- `performance_review_required`
- `runtime_validation_required`, `runtime_validation_kind`,
  `native_validation_required`, and `preferred_runtime_tool`
- `developer_product_seed_applicable` and reason; legacy route payloads may also
  expose `vercel_geist_seed_applicable` as a compatibility alias

Never say a subagent was enabled unless it actually spawned. Never say browser
validation passed unless a browser tool verified the target.
Never say screenshot validation passed unless `browser_screenshot_ops` or an
equivalent browser screenshot tool produced artifact path/hash/dimensions.
Never say visual review passed from screenshot presence alone; report the
executed review stage, consistency sign-off, unresolved blockers, and missing
evidence.

## Quality score

`scripts/design_craft_score.py` reports **source completeness**. It answers
whether the intended source contracts and references exist; it can reach 100
without proving installation or runtime behavior.

`scripts/design_craft_maturity.py` reports **operational maturity**. It gates
runtime scripts, source/install parity, reviewed upstreams, CI, observed evals,
degraded route/detector behavior, and native runtime evidence. A score above 90
requires forward evals and real task evidence, not only file presence.

Operational maturity is profile-specific:

- `desktop` covers the daily computer-based Web/frontend workflow and can reach
  100 without iOS/Android runtime or Cursor/Claude evidence.
- `portable` and normal release readiness use a 95-point boundary while keeping
  optional host/native proof visible rather than silently promoting it.
- certified release maturity 100 requires all four current-source host runs and
  current-source iOS Simulator, Android Emulator, and physical-device evidence.

Do not use the certification profile to declare ordinary Web development
incomplete, and do not use the desktop profile to claim native release proof.

The 100-point score in `product-ui-taste-review.md` is different: it grades one
specific UI surface. When reporting both, name them explicitly as
`design-craft source score` versus `product UI taste score`.

For product UI taste reviews, also report the evidence level:

- `L0 static`: screenshot, wireframe, or prose only.
- `L1 contextual`: screenshot plus product/user/task context.
- `L2 browser`: browser screenshot plus DOM/computed style or token evidence.
- `L3 resilient`: responsive and important interaction states checked.
- `L4 before/after`: before/after evidence plus validation commands and diff.

Do not claim states or responsive behavior as verified when the evidence level
does not cover them.

L3/L4 product UI score cases must include `responsive_viewports` and
`state_checks` in their `score.json`. If flat hierarchy or card soup remains the
main visible issue, do not score above 84 just because the layout fits multiple
viewports.

The `evals/product-ui-taste/before-after/_template/` files are scaffolding only.
They are not real L4 evidence and must not be cited as a completed improvement.

## Cross-agent validation

When validating adapter portability, use:

- `scripts/design_craft_init_agent.sh --agent <agent> --target <temp-dir>
  --scope project --dry-run`
- `scripts/design_craft_doctor.sh --target . --json`
- `scripts/design_craft_cross_agent_validate.py --observed-task <task-dir>`
  only after real agent outputs are collected.

Do not claim Cursor, Claude, Pi, Codex, or another host behaves consistently
until that host has actually run the same benchmark prompt and its output is
recorded.

For the 0.3.0 dashboard benchmark, only Codex and Pi have recorded same-prompt
outputs. Cursor and Claude are explicit unverified hosts for that benchmark.

## Unverified work

If validation cannot run, state:

- Exact command or browser check that was skipped.
- Reason.
- Risk.
- Suggested next command.

Do not turn an unverified assumption into "done".
