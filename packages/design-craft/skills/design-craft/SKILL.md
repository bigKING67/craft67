---
name: design-craft
description: "设计、实现或评审 Web/桌面 UI，以及明确的 iOS/Android 原生界面。作为 UX、设计系统、动效、可访问性与视觉验证基线；不用于纯后端、数据库、算法或 CLI 任务。"
---

# Design Craft

Production-grade, web-first design engineering for product UI, UX, visual
quality, motion, design systems, frontend implementation, performance,
architecture, project quality, and directory governance. Native references are
optional and load only when source or product evidence establishes an iOS,
Android, or adaptive target.

Default to `platform=web`. A mobile viewport, PWA, WebView, or responsive page
does not by itself make a target native.

## Scope

Use this skill for user-visible product surfaces, frontend architecture,
design-system work, visual review, interaction quality, UI performance, and
frontend structure. Do not use it for backend-only, database-only,
algorithm-only, CLI-only, or copy-only tasks with no interface or layout
contract.

## Authority order and evidence

Use this authority order when guidance conflicts:

1. Live runtime behavior and browser/native evidence.
2. Scoped `AGENTS.md`, repo conventions, and current source.
3. Project `PRODUCT.md` and product/platform context.
4. Project `DESIGN.md` or equivalent style authority.
5. Local frontend route output.
6. Bundled developer-product seed templates for new or weak systems.
7. Task-relevant `design-craft` references.
8. Generic upstream guidance.

Project authority wins over generic taste rules. Source can prove code shape and
explicit branches; it cannot prove visual feel, smoothness, device behavior, or
whole-product state coverage. Use `references/validation-contract.md` for the
full evidence and completion boundary.

## Core workflow

1. Start at the task boundary.
   - **L0 local visual refinement or read:** inspect applicable instructions,
     the requested surface and goal, directly associated files, components, or
     exemplars, and only the visual authority needed for that decision
     (`DESIGN.md`, tokens, a shared component, or a verified runtime pattern).
     When changing a repository, inspect `git status --short`. Do not load an
     unrelated `PRODUCT.md`, platform target, package/build script, or distant
     route merely as a checklist. Visible work still requires the applicable
     runtime and visual-acceptance gates.
   - **L1+ frontend work, and every functional, system, architecture, or
     platform change:** inspect `git status --short`, relevant `AGENTS.md`,
     `PRODUCT.md`, `DESIGN.md`, package/build scripts, platform targets,
     tokens, components, routes, and nearby implementations. Resolve platform
     from evidence and apply the full product and style-authority contract.
2. For L1+ frontend work, run the route planner when available:
   `bash ~/.codex/tools/frontend_route_plan.sh --surface <surface> --intent <intent> --scope <scope> [--platform <auto|web|ios|android|adaptive>] [--product-context-path <abs PRODUCT.md>] [--style-authority-path <abs DESIGN.md>] --output compact-json`.
   Use enum values, not free-form task prose. Use full JSON only for contract
   audits and human output only for concise interactive inspection.
3. Treat route `candidate_skills` as candidates. Report `selected_skills` only
   for skills actually read and applied.
4. Choose the smallest mode that covers the work, then load only its routed
   references.
5. Establish the applicable visual authority before changing visual language.
   For L1+ or functional, system, architecture, and platform work, establish
   product and style authority before proceeding. Measure before selecting or
   claiming performance fixes.
6. When selecting or migrating a headless component primitive, read
   `references/component-primitive-selection.md`, resolve project authority,
   and record `keep | adopt | migrate | defer`. A healthy existing library
   defaults to `keep`; adoption or migration requires project-specific
   accessibility, compatibility, maintenance, and rollback evidence.
7. Implement the smallest complete change. Verify visible behavior in a real
   browser or native runtime when the task requires it; report only artifacts
   actually produced.
8. Before delivering visible UI work, run the lightweight system-consistency
   closeout in `references/system-review.md`; escalate to its full review when
   the task or observed regression crosses the documented trigger boundary.
9. Deliver files changed, structure impact, validation, observed runtime
   evidence, performance impact, and remaining risks. Never upgrade planned or
   static evidence into a runtime claim.

## Modes

- `shape`: product/UX brief before implementation.
- `craft`: new feature or substantial UI build.
- `critique`: read-only design-rightness and product-fit review.
- `audit`: read-only engineering and quality review.
- `prototype`: isolated divergence for one UI piece; production promotion waits
  for explicit selection.
- `system-review`: read-only visual, interaction, state, theme, and cross-surface
  consistency review with explicit sign-off.
- `polish`: refinement of an already-correct interface.
- `harden`: hostile data, recovery, accessibility, and edge states.
- `optimize`: measured UI performance work.
- `structure`: file and directory governance.
- `architecture`: frontend interfaces, state, and data-flow review.

For combined production work, use one causal order: baseline and audit,
correctness/hardening, measured optimization, visual polish, then validation.

For a combined production audit that spans resilience, accessibility,
responsive behavior, and performance, load `references/impeccable-workflow.md`,
`references/performance-quality.md`, and `references/validation-contract.md`
together. Treat an unbounded static hot path as decisive architecture risk but
keep it at P1 until target-runtime evidence proves release-blocking task
failure.

Treat every explicit output cap as a hard contract. For a cap of 200 lines or
fewer, draft to at most 75 percent of the cap and use one ledger with no more
than eight findings. Each finding records priority, source proof, runtime
unknown, concrete repair, and acceptance evidence once; later requested
sections reference those finding IDs instead of repeating their details. Before
returning, count newline-delimited lines and cut repetition until the draft is
inside budget.

Do not omit a numerically specified defect while compressing. When no project
authority overrides it, a Web tablet target smaller than 44 CSS pixels needs an
explicit effective-target repair. A performance plan without an existing
budget must propose provisional, ratification-bound numeric gates for the
relevant hot path, such as input/filter p95, maximum long task, mounted-row
bound, CLS, memory, and base-to-head regression, with an explicit rollback
condition. Never claim those provisional gates were measured.

## Helpers

Resolve helper paths from the Skill directory actually loaded in this task,
not from the target project's working directory. Set `DESIGN_CRAFT_RUNTIME`
to that absolute directory (the one containing this `SKILL.md`); invoke
`python3 "$DESIGN_CRAFT_RUNTIME/scripts/<helper>.py"` or
`bash "$DESIGN_CRAFT_RUNTIME/scripts/<helper>.sh"`. Pass the target through
the helper's documented arguments. Do not guess a global install location or
switch from reviewed source to an installed copy silently. Repository-only
maintenance commands are explicitly separated in `references/validation-contract.md`.

Use the smallest relevant bundled helper when available:

- Route and pass: `scripts/design_craft_route.sh`,
  `scripts/design_craft_pass.sh`, `scripts/design_craft_audit.sh`.
- Design authority and motion plans: `scripts/design_craft_seed_design.sh`,
  `scripts/design_craft_motion_plan.py`.
- Review signals: `scripts/design_craft_detect.sh`,
  `scripts/design_craft_taste_review.sh`,
  `scripts/design_craft_static_review.py`,
  `scripts/design_craft_css_smell_scan.py`,
  `scripts/design_craft_focus_audit.py`, and
  `scripts/design_craft_token_audit.py`.
- Evidence: `scripts/design_craft_l4_eval_case.sh`,
  `scripts/design_craft_l4_capture.py`, and
  `scripts/design_craft_browser_evidence.py`.
- Visual references: `scripts/design_craft_reference.py` for bounded source
  ingestion, contract validation, and task-specific Reference Packs;
  `scripts/design_craft_shadow_lab.py` for disposable fixed-commit snapshots
  when a real target repository must remain source-read-only; and
  `scripts/design_craft_shadow_compare.py` for hash-bound, multi-direction
  closeout without production promotion; and
  `scripts/design_craft_comp_fidelity.py` for exact-coordinate, measurement-only
  comp comparisons after an existing capture path produces PNG evidence; and
  `scripts/design_craft_sealed_rendition_gate.py` for hash-first capture plans,
  strict comparison closeout, source mutation audit, optional hash-bound
  Shadow/browser runtime receipts, and an explicit visual decision when a fixed
  Git snapshot or sealed manifest is the input authority.
- Platform and host checks: `scripts/design_craft_platform_scan.py`,
  `scripts/design_craft_codex_route_pack.py`, and
  `scripts/design_craft_score.py`.
- Source-repo upstream review: `scripts/upstream_absorption_report.py`.

If automation is unavailable, continue with the relevant references and report
the skipped automation, risk, and next command instead of failing the design
task solely because a helper is missing.

## Reference routing

Read only references required by the current task.

### Product and visual direction

- Visual direction and anti-slop judgment: `references/visual-judgment.md`.
- Hierarchy, proximity, alignment, repetition, contrast, and Gestalt reasoning:
  `references/foundational-visual-principles.md`.
- Product users, purpose, positioning, platform, and accessibility context:
  `references/product-context.md`.
- Product correctness, agency, familiarity, wayfinding, and feedback:
  `references/product-design-principles.md`.
- Subjective briefs such as "too AI", flat color, weak copy, poor mobile,
  jank, or messy structure: `references/intent-map.md`.
- Surface-specific landing, dashboard, persistent-agent workspace, data-viz,
  report, and mobile Web viewport/input rules:
  `references/surface-playbooks.md`.
- Supplied or selected design-image implementation:
  `references/image-reference-implementation.md`.
- Requested web concept images or section comps:
  `references/web-image-direction.md`; generation is optional, not a UI prerequisite.
- Discovery-source references, Reference Cards/Packs, pattern promotion, and
  Shadow Labs: `references/reference-workflow.md`.
- Approved comp versus captured implementation measurements:
  `references/comp-fidelity.md`; use only after both images share a controlled
  coordinate and capture context. The same reference defines sealed-rendition
  orchestration when capture must fail closed before browser or PDF work.

### Design systems and concrete redesign

- Tokens, `DESIGN.md`, themes, states, focus, motion, and UI copy:
  `references/design-system-contract.md`.
- Product UI taste review and acceptance criteria:
  `references/product-ui-taste-review.md`; add
  `references/taste-score-calibration.md` when scoring is central.
- Lightweight visible-change consistency and full project-system review:
  `references/system-review.md`.
- Base UI, Radix UI, React Aria, Ark UI, other headless primitives, and
  project-owned equivalents: `references/component-primitive-selection.md`.
- Isolated multi-direction exploration before production promotion:
  `references/prototype-workflow.md`.
- Concrete redesign moves and blocker-to-move coverage:
  `references/design-move-library.md`.
- Impeccable-style critique/audit/polish/harden/optimize flow:
  `references/impeccable-workflow.md`.
- New or weak developer-product systems:
  `templates/developer-product/design.md` and
  `templates/developer-product/design.dark.md`.

### Motion and direct manipulation

- Motion principles, accessibility, and anti-patterns:
  `references/motion-quality.md`.
- Web implementation recipes and transient UI lifecycle:
  `references/motion-patterns.md`.
- Whole-codebase motion recon and executable planning:
  `references/motion-audit-planning.md`.
- Drag, swipe, sheets, interruption, velocity, projection, and springs:
  `references/interaction-physics.md`.
- React Native/Expo animation ownership, gestures, haptics, and release-build
  evidence: `references/react-native-expo-motion.md`; load it only when project
  dependencies or native targets prove that runtime.
- Motion naming and reverse lookup: `references/motion-vocabulary.md`.

### Engineering, performance, and structure

- Components, state, types, APIs, and observable errors:
  `references/engineering-quality.md`.
- Measured Web Vitals, render hot paths, charts, tables, and assets:
  `references/performance-quality.md`.
- Interfaces, data flow, migrations, and compatibility:
  `references/architecture-quality.md`.
- File placement and shared-abstraction rules:
  `references/project-structure.md`.
- Evidence-heavy reports, exports, and business-review surfaces:
  `references/report-quality.md`.

### Platform, validation, and provenance

- iOS/iPadOS: `references/ios-quality.md`.
- Android: `references/android-quality.md`.
- Cross-platform adaptation: `references/adaptive-quality.md`.
- Validation commands, browser/native evidence, screenshots, route fields,
  output limits, and unverified work: `references/validation-contract.md`.
- Upstream provenance and pinned source commits: `references/source-map.md`.

For broad "make this frontend excellent" work, start with
`references/visual-judgment.md`,
`references/product-ui-taste-review.md`, and
`references/validation-contract.md`. Add other references only when the task
actually needs their domain. Native tasks additionally load product context,
the matching platform reference, and interaction physics when gestures exist.

## Design read

Before major visual work, state one concise design read:

`Reading this as: <surface> for <audience>, with <vibe>, optimized for <primary job>.`

Ask one focused question only when the missing answer materially changes the
implementation and cannot be inferred from repository or product evidence.

## Quality gates

Do not call the work done until relevant gates pass or are explicitly reported
as unverified:

- Visual: clear hierarchy and density, responsive composition, accessible
  contrast, and no generic AI tells.
- Product: preserves the user's job and information architecture, with owned
  loading, empty, error, long-data, permission, and recovery states.
- Design system: respects token roles, style authority, theme parity, focus,
  component states, semantic-family exemplars, sibling same-state consistency,
  and specific UI copy.
- Accessibility: keyboard, focus, labels, semantics, contrast, target size, and
  Reduced Motion match the platform and input mode.
- Engineering: clear boundaries, justified abstractions, dependency checks,
  explicit state ownership, observable failures, and an evidence-bound
  primitive decision when library selection or migration is in scope.
- Performance: measurement-first reasoning, bounded render/data work, no layout
  thrashing, and appropriate bundle, chart, table, image, and motion choices.
- Architecture: interfaces and data flow are explicit; migrations and
  compatibility risks are named.
- Structure: files follow project conventions; shared modules have real repeated
  callers; avoid generic `utils`, `helpers`, `common`, or `misc` dumping grounds.
- Validation: targeted type/lint/test/build plus browser or native evidence when
  visible behavior requires it. Screenshot success requires an actual artifact
  when route output sets `browser_screenshot_required`; the artifact does not
  itself constitute visual review.

For direct manipulation, responsive geometry, static-evidence boundaries,
scoring, state coverage, and output budgets, follow the routed reference rather
than duplicating its full contract here.

## Delivery contract

For frontend implementation, report only fields that apply:

- route command, `frontend_tier`/`design_tier`, platform source/confidence, and
  product context;
- `candidate_skills` versus actual `selected_skills`;
- style authority and design-system contract;
- applicable primitive decision (`keep | adopt | migrate | defer`), decisive
  project evidence, migration boundary, and rollback status;
- files changed and directory/architecture impact;
- targeted validation and actual browser/native/screenshot artifacts;
- required baseline/final visual-review stages and `pass`, `blocked`, or
  `incomplete` consistency sign-off when visible UI is in scope;
- performance impact, unresolved risks, and unverified hosts/devices.

Respect explicit response-size limits. Use
`references/validation-contract.md` and task-specific review references for
finding budgets, evidence boundaries, and compact output structure. Keep the
final response concise, decision-oriented, and honest about anything not
verified.
