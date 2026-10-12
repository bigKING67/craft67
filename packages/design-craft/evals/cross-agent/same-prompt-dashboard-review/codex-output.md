**1. Evidence level and score band**

**L0 static: prose only.** Product context strengthens the diagnosis, but without a screenshot this does not reach L1 contextual evidence.

**Provisional band: 60–74, “functional but ordinary.”** This describes the concept’s apparent maturity, not verified functionality. Equal emphasis, decorative visualization, and generic advice weaken operational priority. A precise score would imply unsupported knowledge of visual execution.

**2. Design read**

Reading this as an **Operate** surface for ecommerce operators: restrained, dense, and calm, optimized for identifying **which account or campaign needs attention in the next hour, why, and what to do next**.

The hierarchy should follow that decision: urgent exception → supporting evidence → affected entity → next action.

**3–4. Blocking findings and concrete moves**

These are **P1 concept findings**, not observed runtime failures. Each finding includes its repair and proposed acceptance evidence.

| Finding | Prompt evidence and product-fit issue | Runtime unknown | Concrete move | Acceptance evidence |
|---|---|---|---|---|
| **F1 — Flat attention hierarchy** | Twelve equal KPI cards lead the page. Equal visual weight gives routine totals the same apparent importance as urgent conditions. | Actual fold, dimensions, scan time, and metric semantics. | **M1: Flat KPI grid → priority hierarchy.** Use a compact lead operational state plus a supporting metric strip; disclose remaining diagnostics. Show scope, period, comparison, and freshness beside decision-bearing values. | An operator identifies the leading risk within a provisional three-second scan and explains its comparison basis. |
| **F2 — Decorative evidence** | The area chart is explicitly decorative; it occupies attention without answering an operational question. | Data, scales, labels, and drill-down behavior. | **M2: Decorative chart → diagnostic chart.** Retain it only for a named question, such as when a selected campaign departed from expected pacing. Show units, comparison, and supported onset annotations; otherwise remove it. | Operators can explain which decision the chart changes; displayed values trace to the same scope as the queue. |
| **F3 — Primary work object is subordinate** | The dense account table follows overview modules. Density itself is appropriate, but the described order favors monitoring over triage; campaign access is unspecified. | Columns, sorting, filters, row actions, and campaign detail path. | **M3: Table → task-first exception queue.** Promote it directly beneath the compact summary. Prioritize entity, issue, urgency/impact, owner, and next action; group secondary metadata later. Agree an explainable default ranking and preserve filters through drill-down. | With representative cases, operators find the priority account or campaign, explain its rank, and reach its diagnostic/action path without losing context. |
| **F4 — Advice lacks operational specificity** | Generic tips occupy a dedicated right rail without identifying affected work. | Whether any tip already links to evidence or an entity. | **M4: Generic tips → contextual evidence.** Remove the rail or use it for the selected entity’s observed threshold/change, business impact, owner, and direct next step. | Every retained item names affected data and leads to the relevant filtered view or supported action. |

Three additional moves define implementation requirements; they are **not claims of existing defects**:

- **M5 — Enterprise-dense treatment:** Use flat grouped surfaces, subtle dividers, minimal elevation, and project tokens. Reserve semantic color for status, paired with text or icons. Right-align numeric columns with tabular numerals. Provisionally use at least 14px/1.4 for decision-bearing table text and 4.5:1 normal-text contrast, pending project authority.
- **M6 — State contract:** Distinguish “no exceptions” from “no data.” Specify loading, stale/partial data, errors, permissions, and long content. Errors retain scope and provide local retry; stale data displays its timestamp; unavailable actions explain why.
- **M7 — Responsive and keyboard continuity:** Keep priority entity, reason, and action reachable at narrow widths; disclose secondary columns and contain unavoidable horizontal scrolling within the table. Define visible focus, logical keyboard order, and alternatives to hover-only information.

**5. Verified versus unverified**

**Established by the prompt:** audience, next-hour decision, four structural modules, and enterprise/token constraints. The hierarchy critique is an inference from those facts.

**Unverified:** rendered appearance, actual task completion, typography, contrast, token compliance, data correctness, responsive behavior, keyboard/focus/hover, loading/error/empty states, and performance. No files were edited and no browser validation was performed.

**6. Minimal validation before implementation**

1. **Inspect the baseline first:** obtain the current artifact and representative data. Confirm target viewport/fold, existing decision path, and—if a running baseline exists—computed type, contrast, spacing, and token use.
2. **Confirm decision semantics with operators:** agree urgency, impact, ranking, metric periods, freshness limits, and available actions. Use normal, urgent, stale, and ambiguous examples.
3. **Evaluate the proposed structure:** walk representative operators through F1–F4 acceptance tasks using a lightweight prototype. Record priority choice, explanation, and action discovery; treat the three-second scan as a proposed target, not a measured result.
4. **Approve state and access specifications:** review M5–M7 at desktop and narrow widths, including long labels and recovery paths. Schedule real browser, keyboard, contrast, and data-binding checks for implementation acceptance; static review cannot satisfy them.