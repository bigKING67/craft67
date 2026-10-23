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

This should be a calm, precise workspace for merchandising analysts, but its hierarchy favors overview metrics and decorative containers over identifying, assessing, and acting on exceptions due in the next hour.

**Evidence: static description plus supplied product authority only.** No rendered surface or behavior was inspected; undescribed states are unknown, not proven absent.

## 2. Findings

“Blocking” means blocking design approval for the stated job—not a demonstrated runtime failure. Repair and acceptance criteria follow by finding ID.

### Blocking findings

| ID | Finding and supplied evidence | Decision-flow consequence | Still unknown |
|---|---|---|---|
| B1 | **Actionable work is buried.** Eight KPIs, a chart, and nested insights precede a table described as below the fold. | Analysts must pass overview content before finding urgent exceptions. | Actual viewport geometry and time to reach the first actionable row. |
| B2 | **Priority is visually flattened.** Revenue risk and blocked SKUs receive the same card height, 28px numbers, and blue sparklines as yesterday’s page views. | Operational urgency is indistinguishable from background performance. | Whether metrics share scope, freshness, or actionable drill-downs. |
| B3 | **Rows require too much interpretation.** Similar text weights, dot-only status, 24-character product truncation, and three unlabeled action icons obscure identity and next steps. | Analysts risk choosing the wrong product or action and cannot readily distinguish urgency from ownership metadata. | Accessible names, full-name disclosure, action semantics, and existing sort behavior. |
| B4 | **Decision text is hard to read.** Body copy is described as 12–13px and low-contrast gray. | Repeated scanning of deadlines, issues, and financial impact becomes unnecessarily demanding. | Actual contrast ratios, font metrics, zoom behavior, and reading performance. |

### Secondary findings

| ID | Finding and supplied evidence | Consequence | Still unknown |
|---|---|---|---|
| S1 | **Context and controls lack a common hierarchy.** Four loosely aligned page-context rows sit beneath a crowded 64px header with six equal links and a bright Create button. | Scope, freshness, navigation, and creation compete with triage. | Whether Create is frequently needed in exception resolution; header fit at narrower widths. |
| S2 | **Diagnostics consume space without a clear decision payoff.** A doubly contained area chart precedes generic advice such as “Monitor performance closely.” | Space is spent without identifying affected products or a useful next action. | What operational question the chart answers. |
| S3 | **Container styling overwhelms grouping.** Gaps vary from 8px to 48px; every region has a border, 16px radius, and shadow. | Everything appears equally separate and important, weakening the requested dense, credible tone. | Exact spacing relationships and whether any elevation represents a real layer. |
| S4 | **Resilience is unspecified.** Empty, loading, error, focus, narrow-laptop, and long-translation states are not described. | Safe recovery and continued access to the decision flow cannot be approved. | All listed state behavior; this is an evidence gap rather than a confirmed defect. |

## 3. Concrete redesign moves and acceptance criteria

1. **Consolidate the command and context area — S1.**  
   Keep the existing navigation and workflows; use a title/context row and one aligned control row for date range, export, and freshness. Give the current navigation destination a clear indicator. Retain Create but reduce its visual prominence unless its role in triage warrants emphasis.  
   **Accept when:** title, controls, summary, and table share alignment axes; scope and last successful refresh are readable together; all six destinations, search, and header actions remain reachable.

2. **Replace eight equal cards with a compact, prioritized summary — B2.**  
   Lead with revenue risk and blocked SKUs; demote sell-through and page views to supporting context without deleting their data. Replace uppercase label styling with readable sentence-case labels. Keep a sparkline only when its trend informs an operational decision, using ink rather than equal blue emphasis.  
   **Accept when:** urgent metrics are visibly stronger than historical metrics; each lead value states its period and scope; thresholds or comparisons use existing data, not invented benchmarks.

3. **Make the exception table the primary workspace — B1.**  
   Place it immediately after the compact summary, before diagnostics. Put existing filters beside it; offer a clearly scoped next-hour view using established deadline rules, including overdue items, with a visible route back to all exceptions. Preserve user-selected sorting and filters.  
   **Accept when:** at provisional desktop targets of 1440×900 and 1280×720 CSS pixels, the table header and at least three real rows are visible without page scrolling; the time window, timezone, and ordering are explicit.

4. **Give each row a readable decision sequence — B3.**  
   Emphasize product and issue, make deadline and financial impact easy to compare, and keep owner secondary but readable. Add text to status dots using the existing status vocabulary. Replace fixed 24-character truncation with available-width wrapping plus keyboard-accessible full-name disclosure. Show a labeled existing primary action and a labeled menu for remaining actions.  
   **Accept when:** full product identity is obtainable without hover; status remains understandable without color; every existing action remains available and named; currency is right-aligned with tabular numerals; deadlines include unambiguous time context.

5. **Make diagnostics earn their space — S2.**  
   Move the area chart below the queue and remove its nested shell, retaining its real data and workflows. Title it with the operational question it actually answers. Remove generic advice; retain an insight only if supported by an affected entity or segment, an observed count or threshold, urgency or impact, and a direct path to the relevant records.  
   **Accept when:** no “monitor closely” filler remains; retained diagnostics identify evidence and a useful next step without implying unsupported causation.

6. **Apply one restrained density and readability system — B4, S3.**  
   Preserve navy/ink neutrals and semantic amber/red. Use a provisional **14px / 1.4 line-height floor** for decision-bearing table text; reserve 12–13px for secondary metadata. Use 8px related-item gaps, 16px group spacing, and 24px section spacing. Flatten content sections; use subtle row dividers, a single boundary where necessary, and shadows only for overlays. Replace blanket 16px radii with a consistent compact radius, provisionally 4–8px.  
   **Accept when:** normal text reaches at least 4.5:1 contrast; key issue/deadline text outranks helper copy; spacing follows named roles; no ordinary section combines repeated nested borders, rounded shells, and shadows. No gradients, glass, or illustration are introduced.

7. **Specify honest loading and recovery states — S4.**  
   Distinguish “no exceptions” from “no matches”; provide filter reset for the latter. During refresh, retain the last successful data with an explicit stale/updating label. On failure, show local retry and the last successful timestamp; initial loading must not resemble zero risk.  
   **Accept when:** each state communicates whether data is current, stale, unavailable, or genuinely empty; retries preserve scope and filters; failures never silently remove unresolved exceptions.

8. **Protect the same workflow on narrow laptops and by keyboard — S4, B3.**  
   Let context controls wrap deliberately; compress secondary summary content before sacrificing the queue. Permit horizontal scrolling within the table rather than the entire page, preserving access to every column and action. Define visible focus, labeled icon controls, keyboard-operable menus, and focus return.  
   **Accept when:** at 1280×720, 200% zoom, and with doubled-length labels, no controls overlap or become unreachable; keyboard users can filter, inspect full identity, and invoke the correct action; focused controls are not obscured.

## 4. Verdict and scoring boundary

**Verdict: redesign required before approving this as a next-hour exception workspace.** B1–B4 are supported directly by the description.

**No numeric score:** the evidence supports specific hierarchy and readability judgments, but not a defensible aggregate assessment of rendered quality, accessibility, or operational reliability.

## 5. Smallest validation plan that could change the verdict

This is a proposed plan, not completed validation.

1. **Inspect the current baseline first** in the supported desktop browser at 1440×900 and 1280×720, using representative real records. Check the fold, header fit, computed decision-text size and contrast, spacing, and the existing path from urgent exception to action.
2. **Run one short analyst task:** identify the highest-priority exception requiring action within the next hour, explain its deadline and financial impact, and choose the existing next action. Record wrong selections, ambiguity, and unnecessary scrolling; repeat keyboard-only.
3. **Exercise a compact state set:** initial loading, refresh failure with stale data, no exceptions, no filter matches, and a long product name with doubled-length interface labels. Test the populated view at 200% zoom; inspect focus and accessible names for the row actions and status.
4. **Reassess only the affected findings.** Clear B1–B4 only when their acceptance criteria and the analyst task pass; clear S4 only with state evidence. If the baseline contradicts the supplied description, revise the corresponding finding rather than assuming the redesign is necessary.


## Output B

## 1. Diagnosis

The described screen prioritizes general performance reporting and decorative containers over the analyst’s next-hour decision flow: identify an exception, assess urgency and impact, confirm ownership, and act.

**Evidence label: description-only assessment.** Findings below derive from the supplied static description; rendered behavior, measured contrast, and implementation accessibility remain unverified.

## 2. Findings

### Blocking
1. **The primary work is below the fold.** Eight KPIs, a chart, and generic insights precede the exception table, delaying access to the work this workspace exists to support.
2. **Urgency has no clear visual priority.** Revenue risk and blocked SKUs look equivalent to yesterday’s page views; deadlines, impact, and ownership blend into other table text. The described hierarchy does not help analysts distinguish “act now” from “review later.”
3. **Status and actions require interpretation.** Color-only dots do not state status, and three unlabeled action icons conceal their consequences. Accessible names may exist, but the description provides no evidence of them; visible ambiguity remains either way.
4. **Product identification is compromised.** Truncating names at 24 characters can hide the differences between similar products. No full-name recovery is described, creating a risk of acting on the wrong item.
5. **Decision-critical text is difficult to scan.** Small, low-contrast body text and nearly uniform table weights weaken sustained comparison of issues, owners, deadlines, and financial impact. Exact contrast compliance cannot be determined here.

### Secondary
1. **Page context is fragmented.** Four weakly aligned rows separate title, reporting period, export, and freshness, consuming height and obscuring their relationships.
2. **The header competes with triage.** Six equal links and a bright “Create” button give global destinations and creation undue prominence relative to exception handling; retain them, but reduce competition.
3. **Containers obscure grouping.** Borders, shadows, large radii, and nested cards make every region appear equally important while spending space on framing.
4. **Charts and insights lack a stated decision contribution.** Equal blue sparklines suggest equivalent significance; “Monitor performance closely” provides neither a specific exception nor a next step.
5. **Operational resilience is unspecified.** Empty, loading, error, focus, narrow-laptop, and translation states are evidence gaps, not demonstrated failures.

## 3. Concrete redesign moves and acceptance criteria

| # | Move | Acceptance criteria |
|---|---|---|
| 1 | **Put the exception queue first.** Order the page as compact context, triage summary, exception table, then supporting analysis. | At a proposed 1366×768 reference viewport, the table header and at least three normal-height rows are visible without scrolling. The chart remains accessible below the queue; no records or workflows are removed. |
| 2 | **Replace eight equal cards with a compact, ranked summary.** Lead with revenue risk and blocked SKUs; give sell-through and page views quieter supporting placement. | All eight real metrics remain available with their existing definitions and periods. Only metrics that inform immediate intervention receive primary emphasis. Retain sparklines only where their time window and trend help explain a decision. |
| 3 | **Expose next-hour triage without silently changing business rules.** Provide a clearly labeled overdue/next-hour view using existing deadlines and status definitions, alongside the full queue. | Analysts can distinguish overdue, due within 60 minutes, and missing-deadline records. Time zone, active filters, and sort direction are explicit. Preserve existing default behavior until a changed priority order is approved; do not invent a composite urgency score. |
| 4 | **Give the table a decision hierarchy.** Emphasize product and issue, make deadlines readily scannable, align financial impact numerically, and keep ownership explicit. | All seven existing columns remain available. Amounts retain currency and precision with right-aligned tabular figures. Missing owners are labeled rather than blank. Product names are not arbitrarily capped at 24 characters; wrapping or keyboard-accessible disclosure exposes the complete name before action. |
| 5 | **Make status and action meanings visible.** Pair existing amber/red semantics with status text; label the principal existing row action and place secondary actions in a labeled menu if necessary. | Status is understandable without color. Every existing action remains reachable and retains its permissions and confirmation behavior. Labels describe actual operations rather than guessed replacements; menus and controls have visible keyboard focus. |
| 6 | **Consolidate page chrome.** Keep the 64px header, distinguish the active destination, quiet “Create,” and align page context into a title row plus compact controls row. | Date range, export, and last-successful refresh time are easy to locate together. Reporting period and next-hour deadline scope are visibly distinct. All six destinations, search, and existing controls remain reachable without overlap or clipped labels at narrow-laptop widths. |
| 7 | **Flatten the visual system and improve legibility.** Preserve navy/ink neutrals and semantic amber/red; replace nested cards with headings and separators. Start with 14px table/body text, 12px secondary metadata, and a 4/8/12/16/24px spacing scale. | Routine regions do not combine border, shadow, and 16px rounding; shadows are reserved for overlays. Normal text measures at least 4.5:1 contrast. No gradients, glass, illustrations, or font rebrand are introduced. Generic insights are removed unless they can identify a real issue and link to its existing workflow. |
| 8 | **Specify trustworthy operational states.** Distinguish initial loading, refreshing existing data, no exceptions, no filter matches, and failure. | Loading never masquerades as zero exceptions. Refresh failure retains prior data with a stale-data label and retry. Empty filtered results offer filter recovery. Failed actions preserve context and offer recovery; refresh does not unexpectedly move focus or reorder the row being acted on. Long labels remain readable without hiding actions. |

## 4. Verdict and score

**Verdict: the described hierarchy needs revision before it can be considered fit for next-hour triage.**

No numeric score is warranted: the description supports a strong judgment about task hierarchy and ambiguity, but not a calibrated score for rendered quality, accessibility, or workflow reliability.

## 5. Smallest validation plan that could change the verdict

These are proposed checks, not completed validation.

1. **One real-data triage walkthrough in the supported desktop browser:** at 1366×768, ask an analyst to find an exception needing action within the next hour, explain its impact, identify its owner, and initiate the correct existing action. Confirm that prioritization matches operational rules and that no product or icon interpretation requires guessing.
2. **One narrow-laptop pass:** repeat at 1280×720 with a long product name and expanded translation strings; then spot-check 200% zoom. Check header collisions, full-name access, readable deadlines, and access to every column and action. Any horizontal scrolling should be contained to the table, not the whole page.
3. **One keyboard and contrast pass:** traverse search, queue controls, a product disclosure, and row actions; verify meaningful control names, visible unobscured focus, and return focus after menus or dialogs. Measure text and status-label contrast.
4. **One compact state sweep:** exercise initial loading, no exceptions, no filter matches, refresh failure with stale data, and action failure. Confirm that “nothing to do” cannot be confused with “data unavailable,” and that retry preserves working context.

The verdict could improve if those checks demonstrate fast, unambiguous triage with preserved workflows; visual polish alone would not resolve the core hierarchy problem.


## Output C

## 1. Diagnosis

The described screen gives navigation, historical metrics, and generic commentary more prominence than actionable exceptions, undermining the analyst’s next-hour triage task. **Evidence: static description only; no rendered or behavioral validation.**

## 2. Blocking findings

1. **The primary work queue starts below the fold.** Eight KPI cards and a large chart/insight region precede the exception table, delaying access to the products needing intervention.
2. **Urgency has no meaningful hierarchy.** Revenue risk and blocked SKUs receive the same treatment as yesterday’s page views; within the table, deadline, financial impact, and issue are visually indistinguishable from supporting fields.
3. **Status and actions are ambiguous.** Colored dots without text require interpretation, while three unlabeled action icons make the intervention path unclear. Accessible names or tooltips are not described and cannot be assumed.
4. **Product identity is curtailed.** A fixed 24-character truncation can hide the variant or distinguishing suffix needed to act on the correct product; no way to recover the full name is described.
5. **Dense information is difficult to read as specified.** Small, low-contrast body text impairs sustained scanning of owners, deadlines, and issues. Exact contrast compliance cannot be established from the description.

## 3. Secondary findings

1. **The page introduction is fragmented.** Four weakly aligned rows separate scope, date range, export, and freshness—the context needed to trust the queue.
2. **Container styling overwhelms information structure.** Repeated borders, rounded corners, shadows, and nested cards give nearly every region the same importance.
3. **The chart and insights have unclear decision value.** “Monitor performance closely” identifies neither an exception nor a next action.
4. **Global chrome competes with triage.** Six equal navigation links and a bright Create button are prominent without evidence that creation is the dominant task here.
5. **Operational states are unspecified.** Empty, loading, error, focus, narrow-laptop, and translation behavior remain unknown—not demonstrated failures, but material gaps before approval.

## 4. Concrete redesign moves and acceptance criteria

| # | Redesign move | Acceptance criteria |
|---|---|---|
| 1 | **Make the exception queue the main surface.** Put a compact summary directly above it; move the chart and supplementary metrics below the queue or behind an existing-compatible disclosure. | At the agreed desktop viewport, the table heading, controls, column headers, and multiple real exception rows are visible without scrolling. No existing data or workflow is removed. |
| 2 | **Establish a next-hour triage view.** Offer an explicit due-within-an-hour filter, keeping overdue items visible and distinct. Support sorting by deadline and financial impact rather than introducing an opaque priority score. | Using existing deadline and status data, an analyst can isolate the next-hour queue in one action, see the active criteria, and return to all exceptions. Time zone and overdue treatment are explicit. |
| 3 | **Replace the eight-card wall with a compact operational summary.** Give revenue risk and blocked SKUs priority; retain sell-through and page views as secondary context without equal sparklines. | Only metrics directly useful to triage occupy the primary strip. Each has a clear scope and period; summaries either match the queue’s filters or clearly state a different scope. |
| 4 | **Rebuild table hierarchy around identification, urgency, and intervention.** Emphasize product and issue, align financial amounts consistently, show precise deadlines, add status text, and replace ambiguous icons with a named primary action plus labeled secondary options. | Every row exposes product identity, issue, deadline, impact, status, and an understandable next action. Full product names are available by keyboard as well as pointer, not only hover; status meaning does not depend on color. Preserve real values, owners, and existing action semantics. |
| 5 | **Consolidate the page context and quiet global chrome.** Use an aligned title/scope row and a compact controls row for date range, export, and freshness. Retain Create and global navigation, but reduce their emphasis relative to the queue. | Scope, reporting period, and last successful refresh can be read together. Controls remain available without four separate introductory rows; the current navigation location is distinguishable. |
| 6 | **Flatten the visual system while preserving its identity.** Keep navy/ink neutrals and semantic amber/red; remove nested card shells, use subtle table dividers, and reserve stronger boundaries for meaningful groups. Adopt a small spacing scale and readable table text. | No card exists solely to wrap another card. Repeated gaps follow a defined scale such as 8/16/24px; core table text targets 14px with comfortable line height. Measured normal-text contrast meets 4.5:1, with no gradients, glass, or decorative graphics. |
| 7 | **Make supporting analysis actionable or subordinate it.** Keep the area chart as secondary context; replace generic insights only where existing data supports a specific issue, scope, and route into affected rows. | Each retained insight identifies what needs attention and links or filters to supporting records. Unsupported advice is removed, not replaced with invented analytics. |
| 8 | **Specify states that preserve operational trust.** Distinguish no exceptions from no filter matches; separate initial loading from refresh; retain usable prior data on refresh failure with a stale-data warning. Define focus, narrow-width, and long-label behavior. | Empty states explain scope and next steps; failures expose retry and last successful refresh. Keyboard focus is visible and unobscured. At narrow widths, explicit table scrolling or controlled column adaptation preserves access to identity, urgency, and actions. |

## 5. Verdict and scoring

**Verdict: redesign required before visual approval for the stated triage job.** The described hierarchy and table ambiguity justify that conclusion. A numeric score would imply unsupported precision: actual geometry, color values, interaction affordances, and state behavior have not been observed.

## 6. Smallest validation plan that could change the verdict

- **Two viewport checks:** inspect the same real-data queue at the agreed desktop size and a narrow laptop size, for example 1440×900 and 1280×720. Confirm first-screen queue visibility, readable columns, and access to full names and actions.
- **One realistic triage task:** ask a merchandising analyst to identify the highest-impact exception due within an hour, confirm its owner and status, and open the correct existing action. Observe whether metrics, truncation, or icon interpretation cause detours or mistakes.
- **One keyboard pass:** navigate scope controls, queue filters, a long product name, and row actions; confirm visible focus, meaningful control names, and access to any overflow.
- **One compact state/content fixture:** exercise loading, no exceptions, no filter matches, refresh failure with stale data, and longest supported translations/product names. Measure actual text and status contrast.

Approval could change if these checks demonstrate a prominent, unambiguous queue and a reliable intervention path; a polished chart or cleaner cards alone would not change the verdict.
