## 1. Evidence level and score band

**Mode: design-craft `critique`, read-only. Evidence: L0 static—prose only.** Product context is supplied, but without a screenshot this does not reach L1.

**Provisional concept band: 60–74/100, “functional but ordinary.”** This is a structural/product-fit estimate, not confirmation that the dashboard functions. Equal-weight metrics and decorative content undermine operational priority. No exact score is defensible for typography, spacing, color, or interaction quality; flat hierarchy would cap the assessment at 84 even if execution proved tidy.

## 2. Design read

**Reading this as:** a restrained, dense-but-calm revenue operations console for ecommerce operators, optimized for deciding **which account or campaign needs attention in the next hour, why, and what to do next**.

The surface belongs to **Operate**, not Persuade. It should organize attention around exceptions and actionable evidence—not present an evenly weighted business overview. Density itself is not the problem; undifferentiated priority is.

## 3. Top hierarchy/product-fit issues

These are **P1 concept blockers to resolve before committing the layout**, not observed runtime failures.

| ID | Prompt evidence and product-fit concern | Runtime unknown | Repair | Acceptance evidence needed |
|---|---|---|---|---|
| F1 | **12 equal KPI cards at the top.** Their equal weight communicates equal importance and makes the operator perform the prioritization. | Actual screen occupancy, scan order, and metric semantics. | M1–M2 | Operator identifies the leading risk within a proposed three-second scan, then explains its priority. |
| F2 | **One decorative area chart.** It consumes attention without a named operational question. | Whether its data, comparisons, or drill-down provide useful diagnosis. | M4 | Every retained chart supports a specific decision and traces to the relevant records. |
| F3 | **A dense account table follows overview content.** The likely work surface is subordinate; campaign triage is not described. Density is not itself a defect. | Columns, ranking, filters, campaign coverage, and row actions. | M3 | Operator locates an account or campaign, understands its urgency, and reaches a relevant action without reconstructing priority manually. |
| F4 | **Right rail with generic tips.** Generic advice competes with entity-specific evidence and adds another attention destination. | Rail dimensions, usefulness, and any contextual behavior. | M5 | No retained tip lacks a named entity/segment, evidence, impact or urgency, and a direct next step. |

## 4. Concrete design moves

1. **M1 — Establish a compact command/context band.**  
   Show scope, reporting window, comparison basis, and data freshness; keep filters adjacent to the data they affect. Distinguish the operator’s **next-hour action horizon** from the period being measured.

2. **M2 — Replace card soup with `lead + support + action queue`.**  
   Promote one operational state, such as the highest-priority exception, rather than an oversized revenue total. Consolidate supporting KPIs into a compact strip; disclose diagnostics on demand. Every emphasized value needs a period and meaningful comparator. No marketing hero treatment.

3. **M3 — Make the task-first table the primary work object.**  
   Use an exception-focused view of the table rather than duplicating the same work in a separate queue. Order decision-bearing fields around identity, issue/status, urgency, supported business impact, owner, and next action. Provide account/campaign coverage, explain the default ranking, and retain access to all records. Use explicit verb–object actions rather than hidden row-click behavior.

4. **M4 — Turn the chart into diagnostic evidence—or remove it.**  
   Put it below or within the selected exception’s detail. Start with a question such as “When did this campaign diverge from its baseline?” Choose the encoding from the data; label units, period, comparison, and supported onset. Preserve filter context when opening the underlying records.

5. **M5 — Remove generic tips; use contextual guidance only when justified.**  
   Reclaim the rail for table width, or show selected-item context. Any retained guidance must identify the affected entity/segment, observed threshold or change, business consequence, and owner or direct action. Do not invent insight confidence or impact estimates.

6. **M6 — Apply enterprise-dense visual grammar through existing tokens.**  
   Use proximity, alignment, repetition, and typographic contrast before adding color. Prefer flat sections and subtle dividers; reserve elevation for actual layers. Right-align numeric columns and use tabular numerals. Provisional floor: decision-bearing table text at **14px/1.4**, secondary metadata at 12–13px, normal-text contrast at **4.5:1**. Use only established semantic color tokens, paired with text/status cues. These are proposed constraints, not diagnosed current defects.

7. **M7 — Define the operational state contract.**  
   Specify loading, no exceptions, no filter matches, partial/stale data, error, and permission states. Distinguish “nothing needs attention” from “data unavailable.” Keep filters and context during retries; give local recovery actions and explain unavailable actions.

8. **M8 — Preserve priority across input modes and widths.**  
   Keep the lead exception and route to action first on narrow layouts; disclose secondary columns rather than stacking all KPIs above the work. Specify keyboard order, visible focus, accessible sort/filter labels, and non-hover-only detail access. For supported touch layouts, propose 44 CSS-pixel effective targets for ratification.

## 5. Verified versus unverified

**Established from the prompt:** the audience, next-hour decision job, described module structure, and restrained/token-backed style authority. The critique assesses their conceptual relationship.

**Not independently verified:** rendered appearance, actual fold, alignment, typography, contrast, token compliance, data accuracy, ranking usefulness, campaign support, task success, responsive behavior, keyboard/focus/hover behavior, or loading/error/empty states.

No files were edited. No browser, screenshot, DOM, or runtime validation was performed. Missing evidence is **not** proof that a feature or state is absent.

## 6. Minimal validation plan before implementation

1. **Establish the baseline first.** Obtain the current artifact, target desktop viewport/fold, realistic rows, and available tokens/components. If a running surface exists, inspect its current decision path, computed typography/contrast, spacing, and token use before approving the diagnosis. Otherwise keep those checks explicitly pending.
2. **Confirm decision semantics with an operator and data owner.** Review a few recent account and campaign incidents. Agree what “needs attention” means, ranking/tie-breaking rules, available actions, freshness limits, and which impact estimates are actually supported.
3. **Walk through a low-fidelity revised decision flow.** Test urgent, routine, and ambiguous cases. Use the ledger’s acceptance criteria; observe whether the operator chooses the right entity and can explain why. Treat three-second orientation as a proposed target, not a measured result.
4. **Review the state and access specification.** Cover M7–M8 with realistic long names, missing values, no results, stale/partial data, and restricted permissions. Agree supported widths and the keyboard path before building.
5. **Gate implementation on those decisions.** Resolve or explicitly defer F1–F4 with owners. Schedule subsequent browser checks for actual desktop/narrow rendering, focus/hover, state recovery, chart-to-record accuracy, and token consistency; preimplementation review cannot certify them.
