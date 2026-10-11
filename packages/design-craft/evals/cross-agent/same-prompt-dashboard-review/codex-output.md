**1. Evidence level and score band**

**L0 static — prose description only.** Product context is supplied, but without a screenshot this does not reach design-craft’s L1 contextual level.

**Provisional concept band: 60–74/100, “functional but ordinary.”** This is a directional assessment of the described hierarchy, not confirmation that the dashboard functions. Familiar metrics and a table provide a plausible foundation; equal emphasis, a decorative chart, and generic tips weaken its operational purpose. Typography, visual polish, accessibility, and implementation quality remain unscored.

**2. Design read**

Reading this as a revenue operations console for ecommerce operators, with a restrained, dense-but-calm enterprise character, optimized for **choosing which account or campaign needs attention in the next hour, understanding why, and opening the relevant action**.

The intended decision sequence is: **scope and freshness → priority exception → supporting evidence → next action**. The described composition foregrounds overview metrics instead.

**3. Top hierarchy and product-fit issues, with concrete repairs**

These are four **P1 concept blockers to design approval**, not verified runtime failures. Dense data itself is appropriate for this audience.

| ID | Prompt evidence and product-fit concern | Runtime unknown | Concrete design move | Acceptance evidence required |
|---|---|---|---|---|
| F1 | **12 equal KPI cards at the top.** Equal visual weight offers no clear distinction between urgent exceptions and routine totals. | Actual fold, card size, contents, and operator scan behavior. | **M1 — Flat KPI grid → priority hierarchy.** Use a compact lead operational state, such as items requiring attention, with a supporting metric strip. Move diagnostic metrics into detail. Every emphasized value needs its period and comparison or threshold. | In a brief exposure test, operators identify the priority state first and explain what its comparison means. |
| F2 | **Dense account table after overview content.** The main work object is subordinate; the description does not establish how campaign-level problems become actionable. | Existing sort, columns, filters, drill-down, and campaign access. | **M2 — Dashboard card soup → decision surface.** Promote an exception queue, preferably as a prioritized view of the existing table. Rank using agreed urgency and business impact, show the reason, and retain an “All accounts” route. **M3 — Task-first table.** Put identity, issue/status, impact, urgency, owner, and next action before secondary metadata; support a direct campaign detail path. | Operators select the correct account or campaign in representative scenarios, explain its rank, and reach its detail without losing filter context. |
| F3 | **One decorative area chart.** Its stated role provides no evidence for the next-hour decision. An area chart is not inherently unsuitable. | Metric, aggregation, axes, comparison, and data linkage. | **M4 — Decorative chart → diagnostic evidence.** Remove it unless it answers a named question, such as “When did this campaign diverge from expected pacing?” If retained, place it after the queue or inside selected-item detail, with units, period, comparison, and queryable supporting records. | A reviewer can name the decision the chart informs and trace its displayed values to the relevant records. |
| F4 | **Right rail with generic tips.** Advice lacks the entity-specific evidence required for operational triage and competes with working space. | Rail width, tip content, contextual behavior, and whether operators use it. | **M5 — Generic insights → contextual next action.** Remove generic tips. Retain a rail only for selected-item evidence: named entity, observed change or threshold, impact or urgency, owner or next action, and a direct link into affected data. | Every retained insight identifies its evidence and leads to the relevant filtered data or action; otherwise it is omitted. |

**4. Remaining concrete moves**

These complete the eight-move budget. They are design requirements for unresolved areas, not claims of observed defects.

- **M6 — Enterprise-dense system treatment.** Add a compact context band for scope, reporting window, timezone, and last refresh. Use existing token roles for text, surfaces, dividers, focus, and semantic status; reinforce priority through placement and type before color. Keep numbers right-aligned with tabular numerals. Acceptance: scope is explicit, statuses remain understandable without color, and all proposed treatments map to approved tokens. No marketing hero treatment.
- **M7 — Resilient product surface.** Specify loading, no exceptions, no filter results, stale/partial data, error, permission, and action-feedback states. Distinguish “nothing needs attention” from “data unavailable”; keep recovery beside the affected module. Acceptance: each state explains what is known and the available next step without presenting unavailable values as zero.
- **M8 — Responsive decision flow and accessible interaction.** Preserve priority, identity, issue, and action at supported narrow widths; disclose secondary columns intentionally. Define keyboard order, visible focus, named controls, and non-hover access to chart details and row actions. Acceptance: the same triage task remains completable by keyboard and at the smallest supported viewport.

**5. Verified versus unverified**

**Established from the brief:** the audience, next-hour decision task, four described layout elements, and restrained enterprise style authority. Those facts support the structural concerns above.

**Inferred:** equal KPI emphasis and non-actionable modules likely slow prioritization. Their actual effect on task performance requires observation.

**Unverified:** rendered hierarchy, fold, typography, spacing, contrast, token compliance, table semantics, chart accuracy, responsive behavior, hover/focus, keyboard access, loading/error states, and performance. Unmentioned features are not assumed absent. **No files were edited and no browser validation was performed.**

**6. Minimal validation plan before implementation**

1. **Establish the baseline first.** Obtain the current screenshot or wireframe at the intended desktop size and smallest supported width. If a running surface exists, inspect its fold, computed type/contrast, spacing/token use, and current account-to-campaign decision path. Use this evidence to confirm or overturn F1–F4.
2. **Agree the triage semantics with operators.** Define what “needs attention in the next hour” means, including urgency, impact, ownership, data freshness, comparison windows, and ranking ties. Assemble representative cases with an agreed priority and next step.
3. **Evaluate a lightweight proposed artifact.** Test M1–M5 with representative operators and the same cases. Check first attention after roughly three seconds, correct prioritization, explanation of evidence, and access to the next action. Record errors and time against the baseline; do not treat aesthetic preference as task success.
4. **Approve the state and interaction specification.** Review M6–M8 using realistic long labels, large values, stale data, empty results, and errors. Confirm token mappings and intended keyboard/narrow-layout behavior. These are pre-implementation design checks; browser, accessibility, and data-binding verification remain required once an implementation exists.