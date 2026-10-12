# Blind comparative judgment
Judge only the supplied outputs. Do not infer which skill produced a label. Apply the machine-readable scorecard exactly, recompute each total from criterion points, and return only JSON matching the supplied schema.

## Task prompt

# Operations workspace visual critique

Critique the following static product-surface description. Do not edit files,
invent screenshots, or claim browser, DOM, responsive, accessibility-tree, or
runtime validation. Do not name, cite, or reveal any skill, repository, author,
or upstream source in the response; the output will be judged blind.

Product authority:

- Desktop Web operations workspace for merchandising analysts.
- Primary job: find the exceptions that need action in the next hour.
- Tone: calm, credible, dense, and precise; not a marketing page.
- Preserve the existing navy/ink neutral system and semantic amber/red status
  colors. No gradients, glass, or decorative illustration.
- Preserve the table's real data and current workflows rather than proposing a
  ground-up rebrand.

Current screen:

- A 64px header contains a logo, six equal navigation links, global search,
  three icon buttons, and a bright blue "Create" button.
- The page title, subtitle, date range, export action, and refresh status occupy
  four separate rows with weak alignment.
- Eight identical KPI cards use the same height, 12px uppercase labels, 28px
  numbers, gray helper copy, and equal blue sparklines. Revenue risk, blocked
  SKUs, sell-through, and yesterday's page views receive equal emphasis.
- A large pale card contains another card for an area chart; below it, three
  nested cards show generic "insights" such as "Monitor performance closely."
- The exception table starts below the fold. Product, issue, owner, deadline,
  financial impact, status, and action all use similar text weight. Status is
  shown by small colored dots without text. Long product names truncate at 24
  characters. The action column uses three unlabeled icons.
- Body text is 12-13px with low-contrast gray. Section gaps range from 8px to
  48px without a clear rhythm. Every region has a border, 16px radius, and soft
  shadow.
- Empty, loading, error, keyboard-focus, narrow-laptop, and long-translation
  states are not described.

Return:

1. One-sentence diagnosis and an evidence label.
2. At most five blocking findings and five secondary findings.
3. At most eight concrete redesign moves with acceptance criteria.
4. A bounded score or score band only if justified by the static evidence.
5. The smallest browser/responsive/state validation plan that could change the
   verdict.

Stay within 150 lines and keep the recommendations specific to this product,
its authority, and its decision flow.


## Human-readable scorecard

# Comparative scorecard

Generated from `scorecard.json`; do not edit by hand.

| Criterion | Weight | Full credit |
|---|---:|---|
| Product hierarchy and decision flow | 15 | Reorders attention around next-hour exceptions and separates lead, support, and historical information. |
| Anti-generic visual judgment | 15 | Identifies card soup, fake insight copy, equal emphasis, and decorative defaults without imposing another generic aesthetic. |
| Typography, color, and surface craft | 15 | Gives specific readable type, semantic color, spacing, border, elevation, and scanability corrections. |
| Product fit and authority | 15 | Preserves the operations job, data, workflows, and stated visual authority rather than rebranding. |
| Concrete redesign moves | 20 | Supplies prioritized implementation-ready moves and observable acceptance criteria across the full surface. |
| Evidence honesty | 10 | Labels static evidence, avoids runtime invention, and names the smallest decisive validation plan. |
| Scope, prioritization, and output discipline | 10 | Stays read-only and within the requested finding, move, and line budgets with clear priorities. |
| **Total** | **100** | |


## Machine-readable scorecard

```json
{
  "schema": "design-craft.comparative-scorecard.v1",
  "total": 100,
  "criteria": [
    {
      "id": "product_hierarchy",
      "label": "Product hierarchy and decision flow",
      "weight": 15,
      "full_credit": "Reorders attention around next-hour exceptions and separates lead, support, and historical information."
    },
    {
      "id": "anti_generic",
      "label": "Anti-generic visual judgment",
      "weight": 15,
      "full_credit": "Identifies card soup, fake insight copy, equal emphasis, and decorative defaults without imposing another generic aesthetic."
    },
    {
      "id": "visual_craft",
      "label": "Typography, color, and surface craft",
      "weight": 15,
      "full_credit": "Gives specific readable type, semantic color, spacing, border, elevation, and scanability corrections."
    },
    {
      "id": "product_fit",
      "label": "Product fit and authority",
      "weight": 15,
      "full_credit": "Preserves the operations job, data, workflows, and stated visual authority rather than rebranding."
    },
    {
      "id": "concrete_moves",
      "label": "Concrete redesign moves",
      "weight": 20,
      "full_credit": "Supplies prioritized implementation-ready moves and observable acceptance criteria across the full surface."
    },
    {
      "id": "evidence_honesty",
      "label": "Evidence honesty",
      "weight": 10,
      "full_credit": "Labels static evidence, avoids runtime invention, and names the smallest decisive validation plan."
    },
    {
      "id": "scope_discipline",
      "label": "Scope, prioritization, and output discipline",
      "weight": 10,
      "full_credit": "Stays read-only and within the requested finding, move, and line budgets with clear priorities."
    }
  ]
}
```

## Required judgment schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["results", "winner", "rationale"],
  "properties": {
    "results": {
      "type": "array",
      "minItems": 3,
      "maxItems": 3,
      "items": {
        "type": "object",
        "required": ["label", "criteria", "total", "summary"],
        "properties": {
          "label": {"enum": ["A", "B", "C"]},
          "criteria": {
            "type": "object",
            "required": [
              "product_hierarchy",
              "anti_generic",
              "visual_craft",
              "product_fit",
              "concrete_moves",
              "evidence_honesty",
              "scope_discipline"
            ],
            "additionalProperties": false,
            "properties": {
              "product_hierarchy": {"type": "integer", "minimum": 0, "maximum": 15},
              "anti_generic": {"type": "integer", "minimum": 0, "maximum": 15},
              "visual_craft": {"type": "integer", "minimum": 0, "maximum": 15},
              "product_fit": {"type": "integer", "minimum": 0, "maximum": 15},
              "concrete_moves": {"type": "integer", "minimum": 0, "maximum": 20},
              "evidence_honesty": {"type": "integer", "minimum": 0, "maximum": 10},
              "scope_discipline": {"type": "integer", "minimum": 0, "maximum": 10}
            }
          },
          "total": {"type": "integer", "minimum": 0, "maximum": 100},
          "summary": {"type": "string", "minLength": 20}
        },
        "additionalProperties": false
      }
    },
    "winner": {"enum": ["A", "B", "C"]},
    "rationale": {"type": "string", "minLength": 40}
  },
  "additionalProperties": false
}
```

## Output A

## 1. Diagnosis

The described screen prioritizes retrospective reporting and decorative containers over finding, evaluating, and acting on exceptions due within the next hour.

**Evidence label: description-only critique.** Findings below concern the supplied specification; rendered appearance, implementation, and interaction behavior remain unverified.

## 2. Blocking findings

1. **The primary work queue is below the fold.** Eight KPIs, a nested chart, and generic insights precede the exception table, delaying access to the product’s main job.
2. **Urgency has no clear visual priority.** Revenue risk and blocked SKUs look equivalent to yesterday’s page views; within the table, deadlines and financial impact compete equally with routine metadata. Analysts must reconstruct priority themselves.
3. **Status and actions require interpretation.** Colored dots without text do not communicate explicit status, and three unlabeled action icons obscure what will happen. This creates avoidable uncertainty at the decision point.
4. **Product identification is compromised.** Truncation at 24 characters can conceal distinguishing product or variant information, increasing the risk of acting on the wrong item.
5. **Reading density is achieved through small, faint text rather than efficient structure.** The specified 12–13px low-contrast body text makes sustained comparison harder; actual contrast compliance cannot be determined without color values.

## 3. Secondary findings

1. **Page context is fragmented.** Four weakly aligned rows separate title, scope, export, and freshness information that analysts need to interpret together.
2. **The global header competes with exception handling.** Equal navigation emphasis and a bright “Create” button draw attention away from the immediate task. The 64px height itself is not the problem.
3. **Generic insights consume space without supporting a decision.** “Monitor performance closely” identifies neither an exception nor a useful next step.
4. **Surface treatment erases hierarchy.** Universal borders, 16px radii, shadows, and inconsistent gaps make every region appear equally important.
5. **Operational resilience is unspecified.** Empty, loading, error, focus, narrow-laptop, and translation states are evidence gaps—not demonstrated implementation failures.

## 4. Concrete redesign moves and acceptance criteria

1. **Make the exception queue the first substantive section.**
   - Place a compact page toolbar and operational summary above it; move the chart and supporting analysis below.
   - **Acceptance:** At 1366×768 and 1280×720, the initial viewport shows the table header and at least three typical real-data rows, including their actions. All existing data and chart workflows remain reachable.

2. **Expose the next-hour decision scope.**
   - Provide a clearly labeled view for overdue and next-hour exceptions, using existing deadline and status rules; preserve access to the full queue and existing filters.
   - Show the active ordering. Use deadline urgency first and financial impact as a tie-breaker only after confirming that rule with operations.
   - **Acceptance:** Analysts can distinguish overdue, due-soon, later, and missing-deadline records; no unknown deadline silently becomes “not urgent.” Time zone and scope are explicit.

3. **Replace eight equal cards with a compact, ranked summary.**
   - Lead with existing revenue-risk and blocked-SKU metrics; subordinate sell-through and page views without deleting them.
   - Remove uniform sparklines from the immediate triage area unless they explain a relevant change.
   - **Acceptance:** Every prominent metric states its period and scope; any metric linked to the queue reconciles with that queue’s records and existing aggregation rules. No invented totals or altered definitions.

4. **Establish a table reading hierarchy.**
   - Give product identity and issue the strongest text emphasis; make deadline urgency prominent, right-align financial impact with tabular numerals, and keep owner quieter but readable.
   - Replace fixed-character truncation with width-aware wrapping and keyboard-accessible full-name disclosure.
   - **Acceptance:** Similar-prefix product names can be distinguished before action; full names and all seven existing fields remain available. Deadlines expose an exact timestamp, not only relative wording.

5. **Make status and action meaning explicit.**
   - Pair existing amber/red semantics with actual status text. Give the primary existing row action its verb label; retain other actions in a labeled menu if necessary.
   - **Acceptance:** Status remains understandable without color. Each existing action remains available with an unambiguous name, original permissions, and original confirmation behavior; no new workflow is implied.

6. **Consolidate context and reduce chrome.**
   - Align title and concise context with date range, export, and last successful refresh in one compact toolbar, allowing deliberate wrapping.
   - Retain all navigation destinations, clearly identify the active section, and make “Create” secondary on this surface.
   - Replace nested chart cards with one section; remove generic insights unless backed by a specific condition and useful destination.
   - **Acceptance:** Scope and freshness can be read together; failed refreshes never appear as successful updates. No existing navigation or export behavior is lost.

7. **Use a restrained density system.**
   - Preserve navy/ink neutrals and semantic amber/red. Target 14px essential table text, readable secondary text, and 8/16/24px spacing roles.
   - Use row separators and section boundaries instead of universal shadows; reserve elevation for overlays. No font replacement or rebrand is necessary.
   - **Acceptance:** Normal text reaches at least 4.5:1 contrast; controls and focus indicators meet applicable contrast requirements. Density targets are met without clipping or shrinking essential content.

8. **Specify operational and constrained-layout states.**
   - Distinguish “no exceptions” from “no filter matches”; provide clear-filter recovery, layout-stable loading, and contextual errors with retry.
   - Retain last successful data where safe and mark it stale. At narrow widths, contain horizontal scrolling within the table rather than hiding fields.
   - **Acceptance:** Loading or failure never masquerades as zero risk; filters survive retry. Keyboard focus remains visible and returns appropriately after menus or actions. Long translations do not conceal controls or product identity.

## 5. Verdict and score

**Verdict: substantial task-hierarchy revision needed before visual sign-off.**

No numeric score is justified: the description supports clear prioritization defects, but not a defensible rating of rendered quality, usability, or accessibility.

## 6. Smallest validation plan that could change the verdict

All checks below are proposed, not performed.

- **One primary supported desktop browser, two viewports:** 1366×768 and 1280×720, using representative real records, including long product names. Check initial queue visibility, column readability, toolbar wrapping, and access to every action.
- **One keyboard-only task at 200% zoom:** Find a next-hour exception, inspect its full identity, open an existing action, cancel, and return to the queue. Check focus visibility, order, clipping, and name/status semantics.
- **One compact state fixture set:** Initial loading, no exceptions, no matches, refresh failure with stale data, and row-action failure. Repeat the narrow layout with approximately doubled label lengths.
- **One task walkthrough with a merchandising analyst:** Ask them to identify the next exception to handle, explain why, and enter the correct existing workflow. Observe hesitation around urgency, ownership, impact, identity, and freshness.

The verdict improves only if these checks demonstrate that the queue supports accurate next-hour prioritization and action without losing existing data or workflows; cleaner containers alone would not change it.


## Output B

## 1. Diagnosis

The screen gives navigation, reporting, and decoration more prominence than urgent exceptions, making it harder for merchandising analysts to identify what needs action in the next hour.

**Evidence label:** Static-description review only; the hierarchy problems below are supported by the supplied description, but interaction behavior, rendered contrast, and task performance are unverified.

## 2. Blocking findings

1. **The primary work queue is below the fold.** Four rows of page metadata, eight equally prominent KPIs, and a chart stack precede the exception table. Analysts must pass reporting content before reaching actionable work.
2. **Urgency has no visual priority.** Revenue risk and blocked SKUs receive the same treatment as yesterday’s page views; within the table, deadline, financial impact, and issue compete with every other field. The described hierarchy does not distinguish immediate intervention from background monitoring.
3. **Status and actions require interpretation.** Small colored dots provide no status text, and three unlabeled action icons give no visible explanation of their consequences. This is a serious ambiguity at the point of decision.
4. **Product identification is compromised.** Truncating names at 24 characters can hide the variant or distinguishing suffix needed to select the correct SKU. No alternative identification or full-name access is described.
5. **Dense content is visually underpowered.** Low-contrast 12–13px body text makes a consequential queue harder to scan. This supports a legibility concern, not a measured contrast-compliance verdict.

## 3. Secondary findings

1. **Header emphasis conflicts with the primary job.** Six equal navigation links and a bright “Create” button compete with exception handling; creation is not established as the dominant task.
2. **Page context is fragmented.** Title, date range, export, and refresh information span four weakly aligned rows, consuming space and separating context from its controls.
3. **Container styling obscures structure.** Repeated borders, shadows, large radii, and nested cards give every region similar importance.
4. **Insights offer no operational decision support.** “Monitor performance closely” identifies neither an affected product nor a deadline, consequence, or next step.
5. **Readiness cannot be assessed for key states.** Empty, loading, error, focus, narrow-laptop, and translation behavior are unspecified. Their absence from the description is an evidence gap, not proof of broken implementation.

## 4. Concrete redesign moves and acceptance criteria

| # | Move | Acceptance criteria |
|---|---|---|
| 1 | **Make the exception queue the main surface.** Put a compact page toolbar and a short priority summary above it; move the chart and secondary metrics below the queue or into an existing reporting destination. | At the agreed desktop viewport, table headings and actionable rows appear without scrolling. Analysts encounter the queue before the area chart or generic insights. |
| 2 | **Establish an explicit next-hour view.** Use existing deadline and status data to offer clearly labeled urgency filters and a visible sort. Preserve access to all exceptions and existing workflows. | “Due within 1 hour” and “Overdue” have unambiguous definitions; active filters and sort are visible and resettable. Undated items remain discoverable. If deadlines lack time-of-day precision, show that limitation rather than inventing hour-level urgency. |
| 3 | **Replace eight equal KPI cards with a compact priority summary.** Emphasize revenue risk and blocked SKUs; demote historical traffic and other contextual metrics. Remove equal blue sparklines unless they materially explain a decision. | Every prominent metric has a scope and time basis. Queue-scoped metrics reconcile with the active view; broader metrics are explicitly labeled. Only operationally urgent measures receive amber/red emphasis. |
| 4 | **Rebuild table hierarchy without changing its real records.** Prioritize product identity, issue, deadline, and impact; retain owner, status, and actions. Replace dots with concise status text, optionally supported by color. | At a glance, a row answers “which product, what is wrong, when is it due, what is at risk, who owns it?” Status remains understandable without color. All existing data fields remain available. |
| 5 | **Make identification and actions explicit.** Replace fixed character truncation with width-aware wrapping or expansion; expose an existing product/SKU identifier where available. Label the principal existing action and put remaining actions behind a labeled menu. | Similar long product names can be distinguished without guessing. Full names are available by pointer and keyboard, not hover alone. Each action’s label describes the existing operation; no workflow is silently removed or changed. |
| 6 | **Compress and align the chrome.** Align title and essential context with date range, export, and freshness information. Reduce “Create” to a secondary treatment unless its task frequency justifies dominance. | Page context occupies one compact toolbar, with an optional brief subtitle line. Refresh status stays adjacent to the data context. All current navigation and controls remain reachable. |
| 7 | **Use restrained operational typography and structure.** Preserve navy/ink and semantic amber/red; use roughly 14px table text, stronger primary text, tabular numerals, an 8px spacing base, and row separators instead of nested card shells. Remove generic insight cards unless they can cite real exceptions. | Normal text meets 4.5:1 contrast when measured. No gradients, glass, or decorative imagery are introduced. Shadows and radii no longer define every region. Any retained insight names the affected scope and links to relevant existing work. |
| 8 | **Specify failure, focus, and constrained-width behavior.** Define queue loading, successful empty results, filtered-empty results, refresh failure, and full failure; plan column overflow and label expansion. | Loading never reads as zero exceptions. Errors never resemble an empty queue. Retained stale data shows its freshness and failure state. Focus is visible; long labels do not overlap; narrow layouts preserve access to every field and action. |

## 5. Verdict and score

**Verdict: material redesign needed for next-hour triage, not a rebrand.**

**Static task-hierarchy score: 2/5** — where 1 means the primary task is obscured and 5 means it is directly supported. Relevant exception data already exists, but its placement and undifferentiated presentation work against the stated job. This is not an overall usability, accessibility, or implementation score.

## 6. Smallest validation plan that could change the verdict

No browser or runtime validation was performed for this critique.

- **Two desktop widths:** Inspect at the team’s standard desktop size and a narrow laptop size, provisionally 1440×900 and 1280×720. Check initial queue visibility, readable columns, full-name access, and action reachability.
- **One real-data triage task:** Ask a merchandising analyst to find an exception requiring action within an hour, explain its urgency and financial impact, identify its owner, and initiate the appropriate existing action. Include similar long product names and an overdue item. Observe searching, hesitation, and wrong selections.
- **One keyboard pass:** Traverse filters, rows, full-name disclosure, and actions; check visible focus, understandable labels, and return of focus after menus or dialogs.
- **One compact state matrix:** Inspect loading, no exceptions, no filter matches, and refresh failure with stale data. At narrow width, add the longest realistic product names and expanded translated labels. Measure actual text contrast.

The verdict improves only if analysts can reach and correctly interpret urgent work without ambiguity; successful rendering alone would not resolve the decision-flow problem.


## Output C

## 1. Diagnosis

This should be a calm, precise workspace for merchandising analysts to find next-hour exceptions, but its equal-weight summaries and decorative containers prioritize general monitoring over identifying and acting on urgent rows.

**Evidence: static description plus product context only.** No rendered interface or behavior was inspected; “blocking” below means blocking design acceptance for the stated job, not proven runtime failure.

## 2. Findings

### Blocking findings

| ID | Finding and supplied evidence | Decision-flow consequence | Unverified boundary |
|---|---|---|---|
| B1 | **Actionable work is buried.** Four introductory rows, eight KPIs, a nested chart, and three insight cards precede a table described as below the fold. | Analysts encounter reporting before the exceptions they must resolve. | Actual fold position at supported desktop sizes. |
| B2 | **Priority is visually flattened.** Revenue risk, blocked SKUs, sell-through, and yesterday’s page views share identical cards, number sizes, and blue sparklines. | Yesterday’s activity competes with imminent business exposure; the display does not explain what matters now. | Existing metric definitions, filtering, and urgency ordering. |
| B3 | **Rows obscure identity, urgency, and action.** Similar text weights, color-only status dots, 24-character product truncation, and three unlabeled action icons. | Analysts must decode status, distinguish products, and infer actions before acting—an avoidable risk in time-sensitive work. | Accessible names, full-name disclosure, keyboard access, and actual action behavior. |
| B4 | **Decision-bearing text is underpowered.** Body text is described as 12–13px and low-contrast gray. | Dense information becomes harder to scan precisely; financial impact and deadlines need stronger legibility than metadata. | Measured contrast and rendered type metrics; no conformance failure is established. |

### Secondary findings

| ID | Finding and supplied evidence | Consequence | Unverified boundary |
|---|---|---|---|
| S1 | **The shell competes with the task.** A 64px header holds six equal navigation links, search, three icon buttons, and bright “Create”; page controls have weak alignment across four rows. | Global creation receives more emphasis than exception triage, while local scope and freshness are disconnected. | Whether creation is actually frequent in the exception workflow. |
| S2 | **Containers substitute for information structure.** Card-inside-card chart, generic advice, 8–48px gaps, and universal borders, 16px radii, and shadows. | Visual density increases without increasing useful operational information. | Whether the chart answers a specific exception-investigation question. |
| S3 | **Resilience is unspecified.** Empty, loading, error, focus, narrow-laptop, and long-translation states are not described. | Operational readiness cannot be accepted from the supplied specification. | These states may exist; omission is not evidence of implementation absence. |

## 3. Concrete redesign moves and acceptance criteria

Retain the navy/ink neutrals, semantic amber/red, real table data, and existing workflow destinations. No gradients, glass, illustration, or rebrand.

1. **Put the exception queue first — B1.**  
   Order the page: compact title/scope controls → compact operational summary → exception table → supporting analysis.  
   **Accept when:** at proposed test sizes of 1440×900 and 1280×720, the initial view shows table headers and at least three complete exception rows; no chart or insight card intervenes.

2. **Rank summaries by next-hour relevance — B2.**  
   Give revenue risk and blocked SKUs precedence; subordinate sell-through and yesterday’s page views without deleting their data. Remove equally prominent sparklines unless their trends inform a decision.  
   **Accept when:** each emphasized metric identifies its scope and time window; where filtering is supported, it opens the corresponding existing rows. Do not relabel aggregate risk as “next-hour risk” without supporting data.

3. **Make each row answer “which, why, by when, how much, who, what next?” — B3.**  
   Strengthen product identity and issue; make deadlines scannable, financial impact right-aligned with tabular numerals, and owner secondary but readable. Add text to statuses using existing terminology. Replace icon-only actions with one named existing primary action and a labeled menu for remaining actions.  
   **Accept when:** status is understandable without color; similar product names remain distinguishable; full names are available by keyboard, not only hover; every existing action remains reachable with an explicit name.

4. **Restore decision-text legibility — B4.**  
   Use a provisional 14px/1.4 floor for table content and essential controls; reserve 12–13px for nonessential metadata. Use ink for decision-bearing text rather than muted gray.  
   **Accept when:** normal text meets 4.5:1 contrast, essential control boundaries and focus indicators meet applicable 3:1 requirements, and urgency remains distinguishable without making every cell bold.

5. **Compress and align the shell — S1, B1.**  
   Keep navigation and search available; give the current section a clear active state. Consolidate title/subtitle and date/export/refresh into two aligned rows. Reduce “Create” to secondary emphasis unless its role in urgent exception handling is established.  
   **Accept when:** title, summaries, and table share a left edge; scope and refresh timestamp are visible together; search, navigation, export, and creation retain their current destinations.

6. **Flatten supporting analysis and remove empty advice — S2.**  
   Use one chart surface below the queue, without a nested card. Remove “Monitor performance closely”; replace it only with data-backed entity/segment, observed exception, impact or urgency, and a direct path to affected rows.  
   **Accept when:** every retained insight identifies actionable evidence; the chart answers a named investigation question. Use existing spacing tokens or provisionally 8px within groups, 16px between related controls, and 24px between sections; reserve shadows for overlays, use table dividers, and eliminate repeated 16px rounded wrappers.

7. **Specify operational states and laptop behavior — S3.**  
   Distinguish “no exceptions” from “no filter matches”; provide reset filters, stable loading structure, retryable errors, and an explicit last-successful-refresh indicator when showing stale data. Define visible keyboard focus and text expansion.  
   **Accept when:** loading is never presented as zero exceptions; errors never imply fresh data; keyboard users can complete existing row actions with visible focus; at 1280×720 and with 40% expanded labels, controls remain usable and table overflow stays local rather than hiding columns or creating page-wide overflow.

## 4. Score

**No numerical score assigned.** The description supports a clear verdict—**revise before design acceptance for next-hour triage**—but not a defensible aggregate score for rendering, accessibility, or interaction quality. The strongest evidence concerns information order and hierarchy.

## 5. Smallest validation plan that could change the verdict

*Proposed only; none of these checks has been performed.*

1. **Inspect the current baseline first:** one supported desktop browser at 1440×900 and 1280×720, using representative real data. Check fold position, computed type/contrast, spacing, and the path from urgent exception to existing action.
2. **Run one short analyst task:** identify the highest-priority next-hour exception, explain its deadline and impact, identify its owner, and start the appropriate action. Record hesitation, wrong-row selection, and icon interpretation.
3. **Run a compact resilience pass:** keyboard-only traversal; long near-identical product names; expanded translations; loading; no data; no filter matches; refresh failure with stale data.

If the current surface already exposes urgent rows, supports accurate prioritization, and provides clear named actions, downgrade the relevant blockers. If it confirms buried work, ambiguous identity, or unsafe freshness cues, retain the verdict; verify any redesign against the same data and task.
