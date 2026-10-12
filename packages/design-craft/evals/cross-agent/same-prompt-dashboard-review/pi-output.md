## 1. Evidence level and score band

**L0 static — prose concept only.** Product context is supplied, but without a screenshot this does not reach design-craft’s L1 contextual evidence level.

**Provisional band: 60–74, “functional but ordinary,” for the described concept—not verified functionality.** The structure provides reporting ingredients but weak operational prioritization. An exact score would imply unsupported precision; visual finish and interaction quality remain unscored. Flat hierarchy/card soup prevents a defensible score above 84.

## 2. Design read

**Reading this as:** a revenue-operations decision surface for internal ecommerce operators, with a restrained, dense-but-calm enterprise tone, optimized for deciding **which account or campaign needs attention in the next hour, why, and what to do next**.

This is an **Operate** surface, not a presentation of business health. Optimize for time to a justified intervention—not the number of metrics visible.

## 3. Top hierarchy/product-fit issues

These are **P1 concept blockers**, not observed runtime failures. Density itself is not a defect.

| ID | Prompt evidence | Product-fit concern | Runtime unknown | Repair |
|---|---|---|---|---|
| F1 | 12 equally weighted KPI cards lead the page. | Equal treatment implies equal importance; operators must construct priority themselves. | Actual first fixation, fold, and scan time. | M1–M2 |
| F2 | Area chart is described as decorative. | It consumes attention without supporting an operational decision. Area charts are not inherently wrong; an absent question is. | Data meaning, encoding, and diagnostic utility. | M4 |
| F3 | Dense account table follows overview content; the task includes campaigns. | The main work object is subordinate, and the campaign decision path is unspecified. | Existing sorting, columns, campaign drill-down, and actions. | M3 |
| F4 | Right rail contains generic tips. | Generic guidance competes with entity-specific evidence and next actions. | Whether tips have measurable operational value. | M5 |

## 4. Concrete design moves

1. **M1 — Establish a compact command/context band.**  
   Show scope, reporting period, timezone, and last successful refresh. Distinguish the reporting window from the “next hour” action horizon. Keep table-specific filters beside the table.  
   **Acceptance:** operators can identify which population and period every emphasized value describes.

2. **M2 — Replace card soup with lead/support/diagnostic tiers.**  
   Promote one compact operational summary, such as “Needs attention,” using an agreed definition. Reduce supporting KPIs to a short metric strip; disclose the remainder. Pair emphasized values with comparison or threshold context. Use no oversized hero treatment.  
   **Acceptance for F1:** the highest-priority work is identifiable within a provisional three-second scan, without interpreting all 12 KPIs.

3. **M3 — Promote a task-first exception queue/table.**  
   Make the existing table the primary work surface rather than adding another competing list. Order information by identity → reason/status → urgency/impact → owner → next action. Explain the default ranking and allow override. Provide a clear account/campaign switch or supported campaign drill-down. Preserve filters on return from detail.  
   **Acceptance for F3:** an operator can select either entity type, explain its priority, inspect evidence, and reach a named next action without losing context.

4. **M4 — Turn decoration into diagnostic evidence—or remove it.**  
   Retain a chart only for a named question, such as “When did this campaign diverge from its expected range?” Position it after the queue or inside entity detail. Choose encoding from available data; expose units, comparison, and anomaly onset where supported.  
   **Acceptance for F2:** the chart supports a specific decision, and its marks resolve to real underlying records.

5. **M5 — Remove generic tips; use contextual guidance only when justified.**  
   Reclaim the rail for the work surface, or make it a selected-entity detail panel. Retained guidance must name an entity/segment, observed condition or threshold, business impact/urgency, owner or next action, and a direct route to affected data.  
   **Acceptance for F4:** no guidance survives merely to fill space; every item changes or supports a decision.

6. **M6 — Apply enterprise-dense visual grammar.**  
   Use proximity, alignment, and typographic contrast before extra containers or color. Prefer flat sections, subtle token-backed dividers, minimal elevation, right-aligned numeric columns, and tabular numerals. Use semantic color plus text labels—not color alone.  
   **Acceptance:** map roles to actual project tokens; provisionally use at least 14px/1.4 for decision-bearing table text and 4.5:1 normal-text contrast. These are proposed checks, not diagnosed defects.

7. **M7 — Specify trustworthy state families.**  
   Loading must not resemble zero revenue; “no exceptions” must differ from “no data” and “no filter matches.” Stale/partial/error states should expose freshness and scope, preserve filters, and provide local retry; permission states should explain the available path. Confirm actions only after success.  
   **Acceptance:** review each state’s rendering, recovery action, and preserved context. Their current absence is not established.

8. **M8 — Preserve priority across input modes and widths.**  
   Keep critical identity, reason, and action visible on narrower layouts; disclose secondary fields rather than stacking 12 cards first. Provide keyboard-reachable actions, visible focus, non-hover-only evidence, and semantic table/sort labels.  
   **Acceptance:** no hidden critical action or page-level overflow at agreed widths; provisionally use 44 CSS-pixel effective touch targets where touch is supported.

## 5. Verified versus unverified

- **Established from the prompt:** audience, next-hour decision job, four structural elements, and restrained/token-backed style authority.
- **Inferred:** those structural choices likely weaken prioritization. Findings F1–F4 are concept judgments requiring validation.
- **Unverified:** actual layout, typography, contrast, token compliance, data accuracy, ranking usefulness, responsive behavior, accessibility, hover/focus, loading/error states, and performance.
- **Work performed:** read-only design-craft critique. No files edited; no browser, screenshot, DOM, or usability validation claimed.

## 6. Minimal validation plan before implementation

1. **Inspect the baseline first.** Obtain the current artifact at the operators’ actual viewport and fold. If a runtime exists, inspect computed typography/contrast, spacing/token use, and the present decision path. If this is only a concept, retain those gaps explicitly.
2. **Validate decision semantics with operators and the data owner.** Use representative account and campaign cases to agree urgency, impact, comparison windows, freshness limits, ownership, and permitted actions. Confirm that proposed ranking inputs exist.
3. **Walk through the revised hierarchy with realistic records.** Ask operators which entity they would address next, why, and what action follows. Use the three-second priority scan as a provisional target; require correct reasoning and a discoverable action, not speed alone.
4. **Approve a state/input acceptance matrix.** Cover M7–M8, long names, missing/negative values where valid, and dense datasets. Name supported widths and token/component exemplars. Record browser, keyboard, contrast, and data-binding checks as implementation acceptance gates—not pre-verified outcomes.

**Decision:** resolve F1–F4 and ratify the decision model before visual polish or production implementation.
