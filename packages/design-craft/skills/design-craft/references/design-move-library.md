# Design move library

Use this after diagnosis, when a critique must become a concrete UI direction or
implementation plan. Moves are not style presets. Apply them under the project's
runtime behavior, `DESIGN.md`, components, data model, and product job.

## Contents

- [Treatment variants](#treatment-variants)
- [Before/after anatomy patterns](#beforeafter-anatomy-patterns)
- [Move-budget coverage](#move-budget-coverage)
- [Generic AI landing page to product-specific proof sequence](#generic-ai-landing-page--product-specific-proof-sequence)
- [Dashboard card soup to decision surface](#dashboard-card-soup--decision-surface)
- [Flat KPI grid to priority hierarchy](#flat-kpi-grid--priority-hierarchy)
- [Table as data dump to task-first table](#table-as-data-dump--task-first-table)
- [Rough form/settings to guided configuration](#rough-formsettings--guided-configuration)
- [Modal without decision to focused dialog](#modal-without-decision--focused-dialog)
- [Navigation scope mix to clear wayfinding](#navigation-scope-mix--clear-wayfinding)
- [Over-cardified list to composed content surface](#over-cardified-list--composed-content-surface)
- [Formal report page to evidence-first narrative](#formal-report-page--evidence-first-narrative)
- [Mobile stacked to mobile decision flow](#mobile-stacked-but-not-prioritized--mobile-decision-flow)
- [Decorative motion to causal motion](#decorative-motion--causal-motion)
- [Missing states to resilient product surface](#missing-states--resilient-product-surface)

## Treatment variants

Pick the product mood before applying a move. The same structure should not look
the same in every product.

- **Enterprise dense**: compact type, subtle dividers, table-first rhythm,
  semantic status color, minimal elevation.
- **Premium editorial**: larger lead object, calmer scan path, stronger
  typographic contrast, fewer simultaneous modules.
- **Developer tool**: command/status grammar, monospace or tabular metrics,
  inline logs, explicit system state, low decoration.
- **Ops command center**: blocker-first hierarchy, high-contrast exceptions,
  queue/action rail, short labels, strong state semantics.
- **Consumer playful**: friendlier copy, softer surfaces, more illustration or
  motion, but still one clear job and restrained state color.
- **Formal report**: evidence-first narrative, clear scope/date/entity header,
  print/export-safe sections, chart takeaways before raw tables.

Use these as treatment constraints, not theme presets. Project `DESIGN.md` and
runtime evidence still outrank the variant.

## Before/after anatomy patterns

- **Bad dashboard**: 12 equal KPI cards + decorative chart + table + generic
  tips. **Better**: lead risk object + supporting metric strip + exception
  queue + diagnostic chart + task-first table.
- **Bad table**: schema-order columns + buried status + detached filters.
  **Better**: identity/status/risk/impact/next-action first, metadata grouped
  later, filters adjacent to affected data.
- **Bad form**: database-order fields + generic submit + detached errors.
  **Better**: decision-grouped sections, local help/error text, verb-object
  actions, separated destructive controls.
- **Bad landing page**: centered claim + vague gradient + equal cards.
  **Better**: audience/job/outcome claim + product proof + workflow sequence +
  objection handling.
- **Bad mobile adaptation**: desktop order stacked vertically. **Better**:
  mobile top task first, advanced controls disclosed, sticky behavior audited,
  no hover-only affordances.

## Move-budget coverage

When the user caps the response at a small number of moves, spend that budget
across the broken decision chain instead of using multiple moves on adjacent
symptoms. Prefer one move for each decisive layer:

1. page command/context band;
2. lead versus supporting information hierarchy;
3. primary queue/table/work object placement;
4. chart, insight, or evidence role;
5. row/action/status scanability;
6. typography, color, and surface system;
7. empty/loading/error/permission/long-content states;
8. responsive, keyboard, and accessibility behavior.

Combine closely related repairs when needed. For example, fold a distracting
global CTA into the command-band move, and fix status labels, action labels,
and identity truncation in one task-first-table move. Do not spend a scarce move
on a secondary control while a generic insight module, unexplained chart, core
state, or primary workflow remains unaddressed.

Before finalizing, reconcile every blocking finding against the move list. Each
blocker must be removed, merged into a named move, or explicitly deferred with
a reason. A diagnosis-to-move gap is incomplete even when every individual
recommendation is tasteful.

## Generic AI landing page -> product-specific proof sequence

Problem: The page looks like a polished SaaS template rather than a product with
a point of view.

Symptoms:
- Centered hero, vague superlatives, gradient text, three equal feature cards.
- Illustration or abstract glow appears before product proof.
- CTA hierarchy is generic and the audience/job is unclear.

Design move:
- Lead with a specific product claim tied to a user job.
- Put real product UI, workflow proof, before/after evidence, or concrete
  customer scenario above generic illustration.
- Vary section composition: proof strip, workflow section, objection handling,
  use-case deep dive, then CTA.

Frontend implementation:
- Replace equal feature cards with one primary proof module and smaller
  supporting points.
- Use semantic sections and constrained line lengths.
- Use project tokens for surface, text, accent, and focus; avoid one-off
  gradient effects unless they carry brand meaning.

Acceptance criteria:
- The first screen names the audience, problem, and product outcome.
- At least one proof object appears before generic feature claims.
- Primary and secondary CTAs have distinct roles.

## Dashboard card soup -> decision surface

Problem: A dashboard has many tidy cards but no operational priority.

Symptoms:
- All KPI cards have equal size, color, and surface weight.
- Charts, tables, and filters compete for first attention.
- Critical backlog, risk, or anomaly states are visually equal to routine totals.

Design move:
- Promote one lead metric or operational state.
- Convert supporting KPIs into a compact strip.
- Put exception queue, anomaly list, or next-action panel near the top.
- Move explanatory or historical charts below the decision surface.
- Remove generic insight cards. Keep an insight only when it names the entity
  or segment, observed change/threshold, business impact, and next action or
  owner; otherwise it is decoration disguised as analysis.

Frontend implementation:
- Create a `lead + support + action queue` layout instead of an equal grid.
- Use numeric alignment, semantic status color, and restrained surfaces.
- Keep filters close to the data they affect.

Acceptance criteria:
- A user can identify the top action or risk within three seconds.
- Operational blockers appear before low-risk overview metrics.
- Every retained chart answers a named operational question, and every retained
  insight identifies evidence plus an action, owner, or decision.
- The dashboard still works with long labels, empty data, and narrow viewport.

## Flat KPI grid -> priority hierarchy

Problem: Metric presentation is tidy but does not guide interpretation.

Symptoms:
- Metrics are equal width and equal emphasis.
- Delta, time range, and benchmark are missing or visually weak.
- Positive, negative, warning, and neutral states share the same treatment.

Design move:
- Split metrics into lead, supporting, and diagnostic tiers.
- Pair values with context: comparison, period, threshold, or owner.
- Use color only for semantic state, not for decoration.

Frontend implementation:
- Use one larger lead metric card or compact summary band.
- Align numbers with tabular or mono/data type where appropriate.
- Add explicit empty/loading/error states for metric modules.

Acceptance criteria:
- The highest-risk or highest-value metric is visually dominant.
- Every emphasized number answers "compared to what?"
- Semantic state remains clear without relying only on color.

## Table as data dump -> task-first table

Problem: A table exposes rows and columns but does not support decisions.

Symptoms:
- Primary identifier is buried.
- Columns follow database order rather than user task order.
- Filters, empty states, and row actions feel detached.

Design move:
- Put decision-critical columns first.
- Group metadata and secondary attributes.
- Make row action, status, and recovery paths explicit.

Frontend implementation:
- Right-align numeric columns and keep text columns left-aligned.
- Use sticky or persistent controls only when they aid scanning.
- Add empty/loading/error states near the table, not at page bottom.

Acceptance criteria:
- Users can scan identity, status, risk, and next action without horizontal
  decoding.
- Long text and narrow screens degrade intentionally.
- Row actions are discoverable and keyboard reachable.

## Rough form/settings -> guided configuration

Problem: A form follows system fields rather than the user's mental model.

Symptoms:
- Field order mirrors database schema.
- Help and error text are detached from fields.
- Buttons use generic labels like `Submit`, `OK`, or `Confirm`.
- Dangerous or irreversible controls sit near routine settings.

Design move:
- Group fields by user decision, not storage model.
- Move helper/error text local to the relevant field.
- Separate destructive, advanced, and routine actions.
- Name actions with verb and object.

Frontend implementation:
- Use fieldsets/sections, local validation, and stable focus order.
- Add disabled, loading, error, success, and dirty-state behavior.
- Keep save behavior explicit: autosave, manual save, or per-section save.

Acceptance criteria:
- A new user can predict what each setting changes.
- Error recovery is visible next to the failed input.
- Destructive actions require clear separation and confirmation.

## Modal without decision -> focused dialog

Problem: A modal interrupts the user without a single clear decision.

Symptoms:
- Title describes UI mechanics instead of the decision.
- Multiple primary-looking actions compete.
- Escape, close, focus return, or scroll behavior is undefined.

Design move:
- Give the modal one purpose and a decision title.
- Put consequence and recovery information before action buttons.
- Make primary, secondary, and destructive actions visually distinct.

Frontend implementation:
- Trap focus, support escape/close, restore focus to trigger, and handle body
  scroll.
- Use `aria-labelledby` and `aria-describedby` where relevant.
- Keep content height bounded and scrollable without hiding action buttons.

Acceptance criteria:
- The title answers "what decision am I making?"
- Keyboard and screen-reader behavior is testable.
- Destructive and neutral actions cannot be confused.

## Navigation scope mix -> clear wayfinding

Problem: Global, local, and contextual navigation are visually mixed.

Symptoms:
- Current location is not obvious.
- Sibling pages, filters, tabs, and actions share the same style.
- Labels overlap in meaning.

Design move:
- Separate global location, local section, and contextual controls.
- Make active state visible through more than color.
- Use mutually exclusive labels and stable order.

Frontend implementation:
- Use distinct components for nav, tabs, filters, and actions.
- Preserve focus-visible and aria-current/selected semantics.
- Keep mobile navigation compressed without hiding core wayfinding.

Acceptance criteria:
- Users can answer "where am I?" and "where can I go next?"
- Active state is visible in light and dark themes.
- Keyboard order follows visual order.

## Over-cardified list -> composed content surface

Problem: Every object becomes a card, creating noisy repetition.

Symptoms:
- Border, radius, shadow, and background repeat on every item.
- The list has no focal point or density gradient.
- Secondary metadata consumes as much space as primary content.

Design move:
- Use a flat list, grouped rows, or one primary card with secondary rows.
- Reserve elevation for selection, overlay, or true hierarchy.
- Collapse repeated metadata into labels, chips, or columns.

Frontend implementation:
- Replace nested cards with section containers and row anatomy.
- Use dividers and spacing before heavy shadows.
- Define hover/selected/focus states for rows.

Acceptance criteria:
- The main content scans faster with fewer surfaces.
- Selected/clickable state remains clear.
- Density improves without reducing comprehension.

## Formal report page -> evidence-first narrative

Problem: A report page is either a table wall or a dashboard in disguise.

Symptoms:
- The period, entity, scope, and conclusion are not immediately visible.
- Charts lack takeaway labels.
- Tables dominate before executive summary or narrative.

Design move:
- Start with compact header, scope, executive summary, and key findings.
- Use charts to support explicit claims.
- Put appendix-like raw tables after narrative sections.

Frontend implementation:
- Use print/export-safe layout, stable chart sizing, and readable axis labels.
- Keep report sections semantically structured.
- Verify tooltip clipping, legend wrapping, and small viewport behavior.

Acceptance criteria:
- A reader can extract the conclusion and evidence path without interacting.
- Charts answer named questions.
- Export/print or static share mode does not break hierarchy.

## Mobile stacked but not prioritized -> mobile decision flow

Problem: The mobile layout fits the viewport but preserves desktop order
blindly.

Symptoms:
- Low-priority filters or hero content appears before the user's core action.
- Sticky elements cover content.
- Tap targets, long text, and overflow states are untested.

Design move:
- Reorder by mobile job priority.
- Collapse advanced controls behind clear disclosure.
- Keep the primary action reachable without hiding content.

Frontend implementation:
- Use responsive order intentionally, not only `flex-wrap` or source order.
- Check 320-390px widths, touch targets, sticky offsets, and keyboard focus.
- Avoid hover-only affordances.

Acceptance criteria:
- The first mobile viewport contains the top task or route to it.
- No horizontal overflow under realistic content.
- Focus and touch behavior are visible and recoverable.

## Decorative motion -> causal motion

Problem: Motion exists because it looks impressive, not because it clarifies
state.

Symptoms:
- Frequent animation on every visit or every small interaction.
- `transition-all`, layout-property animation, or scale-to-zero entry.
- Motion ignores `prefers-reduced-motion`.

Design move:
- Delete repeated decorative motion.
- Keep motion for causality, hierarchy, continuity, or feedback.
- Use short durations and physical easing only where it helps.

Frontend implementation:
- Animate transform/opacity before layout properties.
- Use origin-aware motion for popovers and menus.
- Gate hover motion for pointer devices and honor reduced motion.

Acceptance criteria:
- A user who sees the UI often is not slowed or distracted.
- Reduced-motion path removes nonessential movement.
- Motion remains interruptible for rapidly triggered UI.

## Missing states -> resilient product surface

Problem: The happy path looks designed; real states feel unfinished.

Symptoms:
- Loading, empty, error, disabled, success, focus, and long-content states are
  missing or generic.
- Error copy does not explain recovery.
- Empty state does not point to the next useful action.

Design move:
- Treat states as part of the component contract.
- Make recovery local and specific.
- Use state semantics consistently across the product.

Frontend implementation:
- Add state variants to shared components or local modules.
- Use action-object microcopy for buttons and recovery text.
- Verify keyboard focus, screen-reader labels, and responsive overflow.

Acceptance criteria:
- Every user-owned state has visible feedback and next action.
- Errors are recoverable without guessing.
- States use tokens and component variants rather than one-off styling.
