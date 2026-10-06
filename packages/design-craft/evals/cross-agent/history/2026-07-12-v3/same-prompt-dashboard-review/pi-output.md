Method: design-craft critique, read-only. No files edited. No browser, DOM, screenshot, responsive, focus, hover, loading, or error-state validation was performed.

## 1. Evidence level and score band

**Evidence level:** L0 static / prose-only concept with product context.  
Not L1 because no screenshot or rendered artifact was provided.

**Estimated score band:** **68–78 / 100** — functional but ordinary to low “clean but generic.”  
If the execution is visually tidy, it could land near the upper end, but with **12 equal KPI cards + decorative chart + generic tips**, it should not be scored above the low 80s until hierarchy, states, responsive behavior, and real-content behavior are verified.

## 2. Design read

Reading this as: **an internal revenue-ops command dashboard for ecommerce operators, restrained enterprise console, optimized for deciding which account or campaign needs attention in the next hour.**

The dashboard should behave less like a reporting overview and more like an **operational triage surface**: “What changed, what matters, who owns it, what do I do next?”

## 3. Top hierarchy / product-fit issues

1. **P1 — KPI card soup blocks prioritization**  
   Twelve equal cards imply twelve equal decisions. For an hourly operator, that creates scanning work instead of directing attention to the highest-risk revenue/account/campaign issue.

2. **P1 — Decorative chart is not earning its space**  
   A generic area chart may look dashboard-like, but unless it answers a named question—trend break, spend/revenue divergence, anomaly window, pacing risk—it competes with the real triage task.

3. **P1 — Dense table is likely the true work surface but appears demoted**  
   If the operator acts on accounts/campaigns, the table should be the decision engine: identity, status, risk, impact, owner, and next action should scan immediately.

4. **P1 — Right rail “tips” sounds generic, not operational**  
   Generic tips are weak for revenue ops. The rail should either become an exception/action queue or be removed. Insight copy must name entity, threshold, business impact, and next action.

5. **P2 — Restrained enterprise style may be undermined by equal surfaces**  
   Enterprise density needs hierarchy discipline: subtle dividers, numeric alignment, semantic status color, and token-backed state treatment—not repeated cards with equal border/radius/shadow weight.

## 4. Concrete design moves

1. **Convert dashboard card soup into a decision surface**  
   Replace the 12-card grid with:  
   - one lead operational state, e.g. “Revenue at risk next hour,” “Accounts breaching target,” or “Campaigns requiring action”;  
   - a compact supporting KPI strip;  
   - an exception queue above or beside the table.

2. **Create lead / support / diagnostic metric tiers**  
   Give only 1–2 metrics dominant treatment. Supporting KPIs become compact, tabular, and comparable. Diagnostic metrics sit closer to the table or filters they explain.

3. **Attach every metric to context**  
   Each important number should answer: compared to what? period? threshold? owner? severity?  
   Avoid naked totals. Use deltas, benchmarks, pacing, or SLA/risk thresholds.

4. **Replace the decorative area chart with an analytical chart**  
   Chart title should be a question or finding, not a label. Example: “Which campaigns are driving today’s revenue gap?” or “Spend rose while ROAS fell after 10:00.”  
   If it cannot produce a decision, move it below the fold or remove it.

5. **Make the table task-first**  
   Put columns in operator decision order:  
   `Account/Campaign → Status/Risk → Impact $ → Cause/Signal → Owner → Next action → Last updated`  
   Right-align numeric columns; keep identifiers left-aligned; use compact row rhythm and visible selected/focus states.

6. **Turn the right rail into an action/exception rail**  
   Replace generic tips with prioritized items: entity, evidence, impact, owner, action.  
   Example: “Campaign A overspent 18% vs pacing; projected margin loss $4.2k; pause or lower bid by 12:00.”

7. **Use token-backed semantic emphasis only**  
   Color should mean status: danger, warning, success, neutral, info. No decorative gradients or arbitrary KPI colors. Surface treatment should whisper hierarchy: subtle borders/dividers over heavy shadows.

8. **Define the state contract before implementation**  
   Design loading, empty, stale-data, partial-data, permission-limited, error, long-name, zero-value, and high-severity states for KPI modules, chart, table, and action rail.

## 5. Verified versus unverified claims

**Verified from prompt only:**
- Surface is an internal ecommerce revenue-operations dashboard.
- Primary user is an operator choosing which account/campaign needs attention in the next hour.
- Current concept includes 12 equal KPI cards, decorative area chart, dense account table, and generic right-rail tips.
- Desired style is restrained enterprise console, dense but calm, token-backed color only.
- No screenshot, DOM, responsive, interaction, loading, or error evidence was provided.

**Unverified / not claimed:**
- Actual visual quality, spacing, type scale, contrast, color use, and alignment.
- Whether the KPI cards are readable or token-backed.
- Whether the chart has correct scales, labels, legends, tooltips, or responsive behavior.
- Whether the table supports sorting, filtering, keyboard use, sticky headers, row actions, or long content.
- Hover, focus-visible, selected, disabled, loading, empty, error, and success states.
- Accessibility, responsive behavior, browser performance, or real-data robustness.

## 6. Minimal validation plan before implementation

1. **Confirm the top operator decision**  
   In one sentence: “In the next hour, the operator must decide ___.” Use this to choose the lead metric and exception queue.

2. **Use representative real data**  
   Validate with real account/campaign names, long labels, zero/negative values, stale data, missing owners, high-risk rows, and normal low-risk rows.

3. **Produce one desktop wireframe or screenshot candidate**  
   Check first-glance hierarchy: can a reviewer identify the top risk/action within 3 seconds?

4. **Define data semantics and thresholds**  
   Confirm what counts as danger/warning/neutral, what delta period matters, and which metric is the source of truth.

5. **Validate table scan path**  
   Test whether identity, risk, impact, owner, and next action are visible without horizontal decoding.

6. **Check design-system fit**  
   Confirm all color, spacing, type, radius, border, and status treatments come from tokens or approved component variants.

7. **Run browser validation only after implementation**  
   Required checks: desktop, narrow viewport, keyboard/focus path, hover/selected states, loading/empty/error states, chart tooltip/legend behavior, and table overflow.

Key design-craft references applied: dashboard/admin playbook, product UI taste calibration, card-soup-to-decision-surface moves, task-first table, and validation contract.
