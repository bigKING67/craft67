## 1. Evidence level and score band

**Evidence level: L0 static / prose-only concept review.**  
No screenshot, DOM, token audit, responsive run, focus walk, hover/loading/error state, or browser evidence was provided.

**Score band: 68–78 / 100 — functional but ordinary to clean but generic.**  
Reason: the described structure sounds usable, but the hierarchy is likely flat and not optimized for an operator deciding “what needs attention in the next hour.” I would not score this above 84 without resolving the card-soup hierarchy and verifying real states/content.

---

## 2. Design read

Reading this as: **an enterprise ecommerce revenue-ops command dashboard for hourly operators, restrained and dense, optimized for triage: identify the highest-risk account/campaign, understand why, and take the next action quickly.**

The dashboard should behave less like an analytics overview and more like an **exception queue with supporting evidence**.

---

## 3. Top hierarchy / product-fit issues

1. **Flat KPI card soup blocks triage**
   - Source proof: 12 equal KPI cards at the top.
   - Risk: equal weight implies equal urgency.
   - Repair: split metrics into lead, supporting, and diagnostic tiers.

2. **Decorative chart consumes attention without an operational question**
   - Source proof: “one decorative area chart.”
   - Risk: chart becomes visual filler, not decision evidence.
   - Repair: chart must answer a named question: trend break, pacing risk, anomaly, spend/revenue divergence, etc.

3. **Primary work object is buried**
   - Source proof: dense account table sits below KPI/chart structure.
   - Risk: operator must hunt before knowing which account/campaign needs action.
   - Repair: promote an exception queue or prioritized table near the top.

4. **Generic tips rail is likely low-trust**
   - Source proof: right rail with generic tips.
   - Risk: generic advice competes with actual account/campaign evidence.
   - Repair: replace with contextual next actions, owner, threshold, or “why flagged.”

5. **Revenue-ops semantics are under-specified**
   - Source proof: no verified metric definitions, thresholds, filters, or row actions.
   - Risk: the UI may look dense but not be operationally accountable.
   - Repair: define source-of-truth metrics, alert criteria, status taxonomy, and action outcomes.

---

## 4. Concrete design moves

1. **Card soup → decision surface**
   - Replace 12 equal KPI cards with:  
     **lead risk object + compact metric strip + exception queue**.
   - Example lead: “7 campaigns need action in next hour · projected revenue at risk $42k.”

2. **Flat KPI grid → priority hierarchy**
   - Use metric tiers:
     - Lead: revenue-at-risk, pacing gap, blocked spend, conversion drop.
     - Support: ROAS, spend, revenue, margin, budget pacing.
     - Diagnostic: CPC, CVR, AOV, inventory/fulfillment constraints.
   - Every emphasized metric should answer: **compared to what?**

3. **Decorative chart → diagnostic evidence**
   - Convert area chart into a chart with a job:
     - revenue/spend pacing against target,
     - anomaly window,
     - account segment comparison,
     - campaign drop-off funnel.
   - Add direct labels, threshold markers, and a short takeaway.

4. **Dense table → task-first table**
   - First columns should support scanning:
     **Account/Campaign · Status/Risk · Impact · Cause · Next action · Owner/SLA**.
   - Numeric columns should be right-aligned; status must not rely on color alone.

5. **Generic tips rail → action rail**
   - Replace tips with contextual modules:
     - “Needs approval”
     - “Budget cap likely”
     - “Creative fatigue detected”
     - “Inventory constraint”
     - “No action: monitoring”
   - Each item needs evidence, impact, owner, and action.

6. **Introduce calm enterprise hierarchy**
   - Restrained surfaces, subtle dividers, compact type, token-backed semantic color.
   - Avoid marketing-style hero treatment, decorative gradients, or loud cards.

7. **Own dashboard states**
   - Required states: loading, stale data, empty queue, partial data, metric error, permission-limited rows, long account names, zero/negative deltas.

8. **Make filters operational**
   - Keep time range, channel, account owner, severity, and status filters close to the queue/table they affect.
   - Show active filter chips and “last refreshed” timestamp.

---

## 5. Verified vs. unverified claims

**Verified from prompt only**
- Internal ecommerce revenue-ops dashboard.
- Primary user is an operator making near-hourly attention decisions.
- Current concept has 12 equal KPI cards, decorative area chart, dense table, and generic tips rail.
- Intended style is restrained enterprise console with token-backed color.

**Not verified**
- Actual visual quality, spacing, typography, color, contrast, or token usage.
- Whether the chart is truly decorative in implementation.
- Real table columns, row density, sorting/filtering behavior, or row actions.
- Metric source of truth, thresholds, freshness, duplicate/missing data, or mapping correctness.
- Accessibility: keyboard flow, focus states, labels, color-only status, reduced motion.
- Responsive behavior, sticky headers, overflow, hover states, loading/error/empty states.
- Performance with large account/campaign datasets.

---

## 6. Minimal validation plan before implementation

1. **Metric/data audit**
   - Define source-of-truth for revenue, spend, ROAS, margin, pacing, alerts, and account ownership.
   - Check missing, duplicate, ambiguous, filtered, and stale records.

2. **Decision-path test**
   - With realistic data, confirm an operator can identify the top account/campaign needing attention in under 3 seconds.

3. **Table/content stress test**
   - Validate long account names, many campaigns, zero values, negative deltas, missing owner, and permission-limited rows.

4. **State inventory**
   - Design and verify loading, empty, error, stale-data, partial-data, disabled, and long-content states.

5. **Accessibility pass**
   - Keyboard navigation, focus-visible, semantic table structure, labels, contrast, and non-color status cues.

6. **Responsive/layout check**
   - Desktop primary, then narrower enterprise laptop widths; verify chart/table overflow and right-rail behavior.

7. **Token/design-system review**
   - Confirm color, spacing, type, radius, elevation, status, and focus treatments use existing enterprise tokens.

8. **Browser validation later**
   - Required before claiming implementation quality, but **not performed for this benchmark**.

Mode used: **design-craft critique**. No files edited; no browser validation claimed.
