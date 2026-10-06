## 1. Evidence level and score band

**Evidence level: L0 static / prompt-only.**  
No screenshot, DOM, runtime behavior, responsive behavior, focus path, hover, loading, empty, or error states were verified.

**Score band: 60–72 / functional but ordinary.**  
This is a concept-level score for information architecture and product fit, not visual polish. If implemented literally, the dashboard likely falls into “dashboard card soup”: tidy, dense, but weak at telling the operator what needs attention now.

## 2. Design read

Reading this as: **an enterprise revenue-ops command surface for ecommerce operators, dense but calm, optimized for deciding which account or campaign needs attention in the next hour.**

The dashboard should optimize for **triage speed**: identify the highest-impact exception, understand why it matters, compare against thresholds, and move directly into the next action.

## 3. Top hierarchy / product-fit issues

1. **P0/P1 — No operational priority**
   - Twelve equal KPI cards make routine totals and urgent exceptions visually equivalent.
   - The first read should answer: “What should I look at now?”

2. **P1 — KPI grid is metric-first, not decision-first**
   - A flat KPI grid exposes data but does not establish lead, supporting, and diagnostic tiers.
   - Missing implied context: compared to what, over what period, against which threshold, owned by whom.

3. **P1 — Decorative chart wastes prime dashboard space**
   - A generic area chart is not enough for this job unless it explains a risk, anomaly, trend break, pacing issue, or forecast miss.
   - In ops mode, charts must answer a named operational question.

4. **P1 — Dense table risks becoming a data dump**
   - The table may contain the truth, but if identity, risk, impact, status, and next action are not the first scan path, operators lose time decoding rows.

5. **P1 — Generic tips rail conflicts with enterprise credibility**
   - A right rail of generic tips feels like dashboard filler.
   - For this user, the rail should either become an actionable exception queue / investigation panel or be removed.

## 4. Concrete design moves

1. **Convert “dashboard card soup” into a decision surface**
   - Use a `lead + support + action queue` structure.
   - Top zone: one lead operational state, e.g. “Revenue at risk next hour,” “Campaigns pacing below threshold,” or “Accounts requiring action.”

2. **Replace 12 equal KPI cards with metric tiers**
   - 1 lead metric/state.
   - 4–6 compact supporting metrics.
   - Remaining diagnostics move into expandable sections, table columns, or detail views.
   - Every metric needs period, comparison, and threshold context.

3. **Create an exception queue above or beside the table**
   - Show top accounts/campaigns needing attention, sorted by urgency or revenue impact.
   - Row anatomy: entity, issue, impact, confidence/status, owner/SLA, next action.

4. **Make the chart diagnostic, not decorative**
   - Rename it around a question: “Where did pacing diverge?” or “Which channel caused the revenue gap?”
   - Add threshold lines, annotations, segment comparison, direct labels, and tooltip content tied to action.
   - If it cannot drive a decision, demote or remove it.

5. **Rework the account table into a task-first table**
   - First columns: account/campaign identity, status/risk, impact, trend/pacing, next action.
   - Secondary metadata moves right or into row expansion.
   - Use right-aligned tabular numbers, sticky header, clear sort state, and filters adjacent to the table.

6. **Replace the generic tips rail with an action/diagnostic rail**
   - Acceptable rail content: selected-row details, recommended action with evidence, owner handoff, recent changes, suppression reason, or escalation path.
   - Unacceptable: generic advice not tied to an entity, threshold, or business impact.

7. **Use restrained enterprise visual hierarchy**
   - Token-backed neutral surfaces, subtle dividers, compact spacing rhythm, semantic status color only.
   - Avoid marketing-style hero treatment, decorative gradients, loud shadows, and arbitrary accent colors.
   - Use color to distinguish warning/critical/success/neutral states, not to decorate KPIs.

8. **Design state coverage before implementation**
   - Define loading, stale data, partial data, empty, error, permission-limited, long account names, extreme numbers, and no-alert states.
   - Reduced-motion and keyboard focus states should preserve status feedback without relying on animation.

## 5. Verified versus unverified claims

**Verified from prompt**
- Surface is an internal ecommerce revenue-ops dashboard.
- Primary user is an operator deciding what needs attention in the next hour.
- Current concept includes 12 equal KPI cards, a decorative area chart, dense account table, and right rail with generic tips.
- Style target is restrained enterprise console, dense but calm, token-backed color only.
- No runtime, screenshot, DOM, responsive, focus, hover, loading, or error evidence exists.

**Unverified / must not be claimed**
- Actual visual quality, spacing, typography, contrast, color usage, or token compliance.
- Whether the table is keyboard-accessible or screen-reader usable.
- Whether KPI values have thresholds, comparisons, freshness, or semantic states.
- Whether the chart has labels, tooltips, accessible colors, or meaningful scales.
- Whether the layout works at narrower desktop widths or with long labels.
- Whether loading, empty, error, stale-data, or permission states exist.

## 6. Minimal validation plan before implementation

1. **Decision-path test**
   - Give operators 3–5 realistic dashboard states.
   - Validate whether they can identify the top account/campaign needing action within 3 seconds and explain why.

2. **Data hierarchy audit**
   - For every KPI/chart/table column, map: decision supported, threshold/comparison, owner, next action.
   - Remove or demote items that do not support triage.

3. **Real-content stress pass**
   - Test long account names, many campaigns, zero alerts, extreme revenue values, stale data, partial API failure, and permission-limited rows.

4. **Accessibility and keyboard plan**
   - Verify focus order, table navigation, visible focus, non-color-only status, labels, sort/filter semantics, and reduced-motion behavior.

5. **Responsive desktop validation**
   - Check at least wide desktop, standard laptop, and constrained split-screen widths.
   - Critical actions and the exception queue must remain reachable; overflow should be isolated to the data table, not the whole page.
