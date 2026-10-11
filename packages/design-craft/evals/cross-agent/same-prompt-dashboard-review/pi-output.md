## 1. Evidence level and score band

**L0 static — prose concept only.** Product context is supplied, but without a screenshot this does not reach L1 contextual evidence under design-craft’s rubric.

**Provisional concept band: 60–74/100, “functional but ordinary.”** This is a structural assessment, not proof that the dashboard functions. A precise visual score is not defensible: typography, alignment, contrast, and interaction quality are unseen. Flat hierarchy/card soup would cap the score at **84**, even with tidy execution.

Method: design-craft `critique`; read-only. No files edited or browser validation performed.

## 2. Design read

**Reading this as:** a revenue-operations decision surface for internal ecommerce operators, restrained and enterprise-dense, optimized for choosing **which account or campaign to address in the next hour, why, and what to do next**.

The intended surface mode is **Operate**, not Persuade. It should prioritize exceptions and actionable evidence—not give every available metric equal prominence. Density is appropriate; undifferentiated attention is not.

## 3. Top hierarchy/product-fit issues

These are **P1 concept-level blockers**, not verified runtime failures.

| ID | Prompt evidence | Product-fit concern / runtime unknown | Repair | Acceptance evidence needed |
|---|---|---|---|---|
| F1 | Twelve equal KPI cards at the top | Equal emphasis provides no explicit operational priority. Actual fold placement and scanning cost are unknown. | M1–M2 | Operator identifies the highest-priority issue and its rationale within a proposed three-second orientation check. |
| F2 | One decorative area chart | Screen space serves presentation rather than a named decision. Actual data semantics and drill-down behavior are unknown. | M4 | Each retained chart answers a specific operational question and traces to relevant records. |
| F3 | Dense account table follows the overview; primary job includes campaigns | The described structure does not establish a prioritized work queue or campaign decision path. Density itself is not a defect; columns, sorting, and actions are unknown. | M3 | Operator can compare account and campaign candidates, explain priority, and reach the appropriate next action. |
| F4 | Right rail contains generic tips | Generic guidance competes with entity-specific work without establishing urgency or ownership. Its actual copy and interaction are unseen. | M5 | Every retained insight contains evidence, an affected entity/segment, impact or urgency, and a direct next step. |

## 4. Concrete design moves

1. **M1 — Compact command/context band.** Show scope, reporting period, comparison basis, timezone, and data freshness; place local filters beside the data they affect. Distinguish the operator’s *next-hour action horizon* from the metric’s measurement window.

2. **M2 — Replace card soup with lead/support/diagnostic tiers.** Use a compact lead operational state such as “Needs attention,” backed by agreed thresholds—not a marketing-sized hero. Compress decision-relevant KPIs into a supporting strip; disclose the remaining diagnostics. Emphasized numbers need a period, benchmark, or threshold.

3. **M3 — Promote a task-first exception queue.** Make the primary table the working surface, with an explicit account/campaign scope. Order decision-bearing fields as identity/type, issue, urgency, impact, owner, and next action; put metadata later. Agree an explainable default ranking with operators rather than inventing an opaque risk score. Use right-aligned tabular numbers and visible verb-object actions.

4. **M4 — Make the chart diagnostic, or remove it.** A possible question is “When did this selected campaign depart from its expected range?” Choose the encoding from available data; include units, period, comparison, and supported anomaly onset. Put this evidence after the queue or within selected-item detail, not before the primary work.

5. **M5 — Remove generic tips.** Reclaim the rail unless it provides contextual evidence or selected-item detail. Retained insights must name the entity/segment, observed count or threshold, business impact or urgency, owner or next action, and a direct filter/action. Do not fabricate insight content to fill the layout.

6. **M6 — Apply enterprise-dense visual grammar.** Use a deliberate density gradient, flat grouped surfaces, subtle dividers, minimal elevation, and token-backed semantic color plus text labels. Reuse project type/spacing roles; pending actual authority, propose **14px/1.4** for decision-bearing table text and WCAG normal-text contrast. These are prospective criteria, not observed defects.

7. **M7 — Define the state contract.** Specify loading, no exceptions, no filter matches, partial/stale data, error, permission limits, and action feedback. Distinguish “nothing needs attention” from “data unavailable.” Keep filters/selection through recoverable failures; provide local retry or clear-filter actions. Unknown data must not render as zero or healthy.

8. **M8 — Preserve the decision path across input and width.** Keep identity, priority, and next action available at narrower widths; disclose secondary fields rather than stacking twelve cards first. Specify keyboard sorting/filtering, visible focus, and non-hover access to essential detail. Contain unavoidable horizontal scrolling within the data region.

M6–M8 are design requirements for validation—not additional diagnosed defects.

## 5. Verified versus unverified claims

**Established from the supplied brief**
- Audience, next-hour decision job, described module order, and restrained enterprise style authority.
- The concept gives twelve KPIs equal structural weight and explicitly includes decorative/generic modules.

**Reasoned judgments, not observed outcomes**
- F1–F4 likely weaken prioritization and product fit.
- The proposed hierarchy is better aligned with the stated job; faster or more accurate decisions remain hypotheses.

**Unverified**
- Actual appearance, fold, spacing, type, numeric alignment, color contrast, and token compliance.
- Ranking/data correctness, campaign coverage, filters, actions, and permissions.
- Responsive layout, hover/focus/keyboard behavior, loading/error/empty states, accessibility, and performance.

## 6. Minimal validation plan before implementation

1. **Establish the baseline first.** Obtain the current artifact, realistic anonymized data, target viewport/fold, and actual tokens/components. If a live version exists, inspect its computed type/contrast, spacing/token use, and current decision path. If no artifact exists, keep those checks explicitly unavailable.

2. **Validate decision semantics with operators and the data owner.** Agree what constitutes attention within an hour, how account and campaign urgency compare, which impacts are measured versus estimated, and what actions are authorized. Confirm freshness and comparison rules before choosing the lead metric.

3. **Test one proposed hierarchy against realistic scenarios.** Include competing urgent candidates, no urgent work, and stale/partial data. Ask representative operators to choose an entity, explain why, and identify the next step. Use the F1–F4 acceptance conditions; record mistakes and uncertainty, not just preference.

4. **Review the design contract before coding.** Approve the task-first columns, chart question or removal, contextual insight anatomy, state matrix, and desktop/narrow-width decision order. Review keyboard/focus intent and token mapping; do not call these implemented or browser-verified.

**Implementation readiness:** conditional on those checks. Actual responsive, interaction, accessibility, and state behavior require later runtime validation; this critique does not provide release sign-off.
