## 1. Evidence level and score band

**Evidence level: L0 — prompt-only concept critique.**  
No screenshot, DOM, tokens, real data, responsive behavior, focus order, hover, loading, empty, or error states were verified.

**Score band: 60–70 / 100 — functional but ordinary.**  
The concept has recognizable dashboard ingredients, but the described hierarchy is “dashboard card soup”: many modules, little operational priority.

## 2. Design read

Reading this as: **a restrained enterprise revenue-ops command surface for ecommerce operators, dense but calm, optimized for deciding which account or campaign needs attention in the next hour.**

The dashboard should not optimize for “showing many metrics.” It should optimize for **attention routing**: what is abnormal, how material it is, who/what owns it, and what action should happen next.

## 3. Top hierarchy / product-fit issues

1. **P1 — Twelve equal KPI cards flatten priority.**  
   Equal cards make revenue, risk, pacing, anomaly, and secondary diagnostics feel equally urgent. Operators lose the “what needs attention first?” path.

2. **P1 — Decorative area chart is not earning its space.**  
   A chart without a named operational question becomes visual filler. For this user, charts should explain trend, anomaly, pacing, or variance.

3. **P1 — Dense table appears to be the real work object, but is visually demoted.**  
   If the operator acts on accounts/campaigns, the table or exception queue should be central, not buried under KPI noise.

4. **P1 — Generic tips rail mismatches enterprise ops context.**  
   “Tips” are likely perceived as low-trust unless tied to specific entities, evidence, owner, impact, and next action.

5. **P2 — Style risk: card-heavy layout can become demo-like rather than calm enterprise.**  
   A restrained console needs hierarchy through grouping, type, alignment, semantic status, and density—not equal raised surfaces everywhere.

## 4. Concrete design moves

1. **Replace KPI card soup with a lead + support hierarchy.**  
   Promote one lead operational state: e.g. “At-risk revenue in next hour,” “Campaigns pacing below threshold,” or “Accounts requiring action.” Compress remaining KPIs into a supporting metric strip.

2. **Add a top command/context band.**  
   Include scope, time window, freshness, filters, and owner/team context: “Last updated 09:42 · Today · US marketplace · Paid Social.” This prevents metric ambiguity.

3. **Introduce an exception queue above or beside the table.**  
   Show the top 5–10 accounts/campaigns needing action, ordered by severity and business impact. Each item should include entity, reason, impact, confidence/threshold, and next action.

4. **Convert the decorative chart into a diagnostic chart.**  
   Give it a question: “Where did revenue pacing diverge in the last 6 hours?” Use direct labels, threshold/reference lines, accessible semantic color, and a short takeaway.

5. **Rework the table into a task-first table.**  
   Put columns in decision order: entity, status/risk, revenue impact, pacing/variance, owner, last change, next action. Right-align numeric columns; keep filters adjacent to the table they affect.

6. **Replace generic tips with evidence-backed insight/action rail.**  
   Keep the rail only if it is contextual: “Campaign X is 18% below hourly target; budget cap hit 42 min ago; owner: Mia; action: increase cap or pause low-ROAS ad group.”

7. **Use restrained enterprise surface grammar.**  
   Prefer flat sections, subtle dividers, compact spacing, tabular numbers, semantic status tokens, and minimal elevation. Reserve strong color for warning/danger/success states.

8. **Design state coverage as part of the component contract.**  
   Define loading, empty, stale-data, partial-data, permission, API error, long-label, high-row-count, selected-row, focus-visible, and disabled states before implementation.

## 5. Verified versus unverified claims

**Verified from prompt only:**
- The intended user is an internal ecommerce revenue-ops operator.
- The primary decision horizon is the next hour.
- The concept contains 12 equal KPI cards, one decorative area chart, a dense account table, and a generic tips rail.
- The requested style authority is restrained enterprise console, dense but calm, token-backed color only.

**Not verified:**
- Actual visual quality, spacing, typography, contrast, alignment, or color-token usage.
- Whether KPI values include comparisons, thresholds, owners, or time ranges.
- Whether the area chart is truly decorative in implementation.
- Table column order, sorting, filtering, keyboard behavior, row actions, sticky headers, or virtualization.
- Hover, focus, loading, empty, error, responsive, reduced-motion, or accessibility behavior.
- Metric correctness, data freshness, source-of-truth, or duplicate/missing account handling.

## 6. Minimal validation plan before implementation

1. **Product/data validation:** confirm the top 3 operator decisions, source-of-truth metrics, refresh cadence, severity thresholds, and owner/action model.  
2. **Content validation:** test with real account/campaign names, long labels, missing owners, zero-data periods, stale data, and conflicting metric states.  
3. **Hierarchy validation:** run a 3-second review: can an operator identify the top account/campaign needing attention and why?  
4. **Dashboard state validation:** specify loading, empty, partial, stale, error, and permission-denied states for KPIs, chart, table, and rail.  
5. **Accessibility validation:** keyboard path, focus-visible states, semantic table structure, non-color-only status, contrast, and screen-reader labels.  
6. **Responsive validation:** at least desktop dense, narrow laptop, and constrained split-screen widths; verify table overflow and rail behavior.  
7. **Performance validation:** table rendering, sorting/filtering latency, chart cost, and data refresh behavior under realistic row counts.  
8. **Design-system validation:** verify all color, surface, spacing, type, status, and focus treatments use approved tokens.
