# Forward test log

> Immutable pre-v0.5 archive. This narrative is not current release evidence.

Date: 2026-06-24

Scope: independent read-only subagent passes against the local
`design-craft` skill. These runs evaluated planning behavior and skill
selection quality only; they did not implement a live frontend task.

## Runs

### Landing page

- Agent: `019ef78d-2812-7eb2-bb1f-3de0bc2c6c12`
- Result: pass.
- Evidence:
  - Produced a concise design read.
  - Treated the task as L2 and enforced project `DESIGN.md` authority.
  - Separated route `candidate_skills` from actually selected skills.
  - Required desktop and mobile browser validation before claiming completion.
  - Required screenshot artifacts before claiming screenshot validation.
  - Flagged generic SaaS patterns, motion/contrast/performance risk, and
    placeholder-content quality.

### Dashboard quality

- Agent: `019ef78d-40f5-7980-a3b3-db4ba69fab50`
- Result: pass with route-command correction needed.
- Evidence:
  - Read dashboard work as an operator/analyst workflow, not a marketing page.
  - Focused on filters, KPIs, charts, tables, states, responsiveness, and
    performance.
  - Required real browser validation.
  - Required screenshot evidence when the route asks for it.
- Correction:
  - Do not pass free-form prose into route `--intent` or `--scope`; those
    arguments must use fixed enum values.

### DataHub special report

- Agent: `019ef78d-6423-7373-b8dc-553cfafdbc73`
- Result: strong pass.
- Evidence:
  - Prioritized DataHub `DESIGN.md`, static report contracts, and runtime truth
    above generic visual taste.
  - Applied formal analyst-report grammar, chart-first evidence, quiet TOC,
    footnote-sized caveats, and supporting tables.
  - Called out ECharts resize/tooltip/legend/narrow viewport checks.
  - Noted special-report risks such as contribution metric noise, shares above
    100%, protected-route login smoke, and managed-tab cleanup.
- Note:
  - For report-like DataHub work, prefer route `--surface dashboard` or
    `--surface data-app` over broad `--surface app` when the task evidence
    supports that choice.

### Frontend architecture

- Agent: `019ef78d-7e6f-76d0-b591-d15f56f69419`
- Result: pass with route-command correction needed.
- Evidence:
  - Mapped route shell/layout, data source, adapter, query/cache, state owner,
    component tree, side effects, and error boundaries.
  - Preserved current architecture first and required concrete evidence before
    shared abstractions or migrations.
  - Included fallback observability, migration/rollback, browser checks, and
    route/data/state validation.
- Correction:
  - `--intent architecture` is invalid. Use a valid intent such as
    `functional`; keep architectural notes in the plan or summary, not route
    argument values.

## Cross-run findings

- The skill reliably preserved the intended authority order:
  live/runtime evidence, repo instructions, project `DESIGN.md`, route planner,
  local references, then upstream taste/impeccable guidance.
- Dashboard, report, and architecture tasks correctly avoided landing-page
  visual grammar when the product surface required operational density.
- The main remaining weakness is route-command hygiene: route arguments must
  stay fixed enums, while natural-language notes belong in the plan or delivery
  summary.
- These forward tests support v1 pre-release confidence, but final v1 should
  still require one real implementation task log with live validation evidence.
