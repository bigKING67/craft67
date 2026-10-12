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

The screen gives historical metrics, generic commentary, and global creation equal or greater prominence than actionable exceptions, undermining analysts’ ability to decide what needs attention in the next hour.

**Evidence label: Static-description assessment.** Findings are grounded only in the supplied description; rendered geometry, interaction behavior, contrast compliance, and state handling are unverified.

## 2. Blocking findings

| Finding | Evidence and operational consequence |
|---|---|
| **The primary work queue is displaced.** | The exception table starts below the fold, after KPIs, a chart, and generic insights. Analysts must pass supporting material before reaching the work they came to do. |
| **The summary does not distinguish urgency from background performance.** | Eight identical KPIs give revenue risk and blocked SKUs the same emphasis as yesterday’s page views. Equal sparklines add visual activity without establishing next-hour priorities. |
| **The table lacks a triage hierarchy.** | Issue, deadline, financial impact, status, and action have similar weight. The described presentation makes it difficult to distinguish imminent, costly exceptions from lower-priority work. |
| **Status and actions require interpretation.** | Small color-only dots and three unlabeled action icons do not visibly explain condition or consequence. Analysts must infer meaning at the point of decision; accessible names are unknown. |
| **Product identification is unnecessarily constrained.** | Truncation at 24 characters can conceal distinguishing product or variant information, increasing the risk of acting on the wrong item. |

## 3. Secondary findings

1. **Header emphasis is misallocated.** Six equal navigation links and a bright blue “Create” compete with the workspace’s operational purpose; creation is not established as the primary task.
2. **Page context is fragmented.** Four weakly aligned rows separate title, reporting period, export, and freshness, increasing scanning effort and consuming useful vertical space.
3. **Containment overwhelms hierarchy.** Nested cards, universal borders, 16px radii, and shadows make supporting content look as important as the work queue.
4. **Typography and spacing impede dense reading.** Described low-contrast 12–13px body text and irregular 8–48px gaps weaken legibility and grouping. Actual contrast ratios cannot be determined.
5. **State coverage is unspecified.** Empty, loading, error, focus, narrow-laptop, and translation behavior need validation; their absence from the description is not evidence that they are absent from the product.

## 4. Concrete redesign moves and acceptance criteria

| Move | Acceptance criteria |
|---|---|
| **1. Put the exception queue directly after compact page context and a short triage summary.** Move the chart and historical KPIs below it or into an existing secondary view; remove generic insights unless they identify an exception and a useful next step. | At the agreed desktop reference viewport, table headers and at least three actionable rows appear without scrolling. “Monitor performance closely” no longer occupies prime workspace space. |
| **2. Replace eight equal KPI cards with an operational hierarchy.** Emphasize existing revenue-risk and blocked-SKU measures; add a next-hour exception count only if current deadline and status data support it. Retain sell-through and page views as secondary context. | Each leading summary has an explicit scope and time basis. Any clickable count opens the matching existing table filter and reconciles with its rows. No unsupported metric or invented urgency is introduced. |
| **3. Make the table’s priority rule explicit.** Offer a visible “Next hour” view using existing deadlines and statuses, with overdue work included and clearly distinguished. Order by deadline urgency, then financial impact within urgency groups. Preserve access to all exceptions and current filters. | The active scope, sort, time zone, and treatment of missing deadlines are visible or readily inspectable. A next-hour filter cannot silently exclude overdue items. |
| **4. Strengthen row-level decisions without changing the data.** Give product and issue a clear reading hierarchy, make deadlines explicit, right-align financial impact, and show text status labels alongside semantic color. Replace unlabeled actions with the actual workflow verbs, using labeled overflow for secondary actions. | An analyst can identify the item, problem, deadline, impact, owner, status, and available next step without interpreting an icon or color alone. Existing actions remain available with unchanged consequences. |
| **5. Restore product identity.** Remove the fixed 24-character cutoff; allocate a flexible product column, permit controlled wrapping, and provide access to the full name. Show an existing SKU or variant identifier where available. | Similar products remain distinguishable in the row. Full names are available by keyboard as well as pointer; essential identity does not depend solely on hover. |
| **6. Consolidate navigation and page controls.** Keep the 64px header, clearly mark the active destination, and reduce “Create” to secondary emphasis unless its task frequency warrants otherwise. Align title/subtitle with date range and export; place refresh status beside the data context it describes. | Page context fits into at most two aligned rows at the reference width. Reporting range and next-hour deadline scope are not conflated. Search, navigation, creation, and export retain their workflows. |
| **7. Flatten the visual system.** Preserve navy/ink neutrals and amber/red semantics. Use one surface per section, restrained table rules, and a consistent 8/16/24px spacing rhythm; reserve shadows for overlays. Use roughly 14px primary table/body text, with smaller text limited to secondary metadata. | No card exists solely to contain another card. Routine content does not compete with warnings through bright color or shadow. Measured normal-text contrast meets 4.5:1; semantic colors retain their meaning. |
| **8. Define compact operational states.** Distinguish “no exceptions” from “no filter matches”; preserve table geometry during loading; show retry and last-successful-refresh information on failure. Specify visible focus and narrow-width overflow. | Stale data is never presented as freshly updated. Empty results offer the appropriate next step. Keyboard focus remains visible and unobscured, and constrained widths preserve access to identity, deadlines, and actions. |

## 4. Score

**No numerical score is justified.** The description supports a **blocking hierarchy and decision-clarity verdict**, but not a calibrated score for the rendered interface or its behavior.

## 5. Smallest validation plan that could change the verdict

- **Two viewport checks in one supported desktop browser:** 1440×900 and 1280×720 at 100% zoom. Check the first visible table rows, header crowding, column readability, and access to full product names and actions. These are test targets, not observed results.
- **One representative analyst task:** Using real or approved representative rows, ask an analyst to find the highest-impact exception due within an hour, identify its owner, and reach the correct existing action. Include an overdue item and two similar long product names. Record errors, hesitation, and whether the priority rule is understood.
- **One keyboard pass:** Traverse search, scope/filter controls, sort, product detail, and row actions; confirm visible focus, meaningful action names, and no trap.
- **One compact state matrix:** Inspect loading, zero exceptions, zero filter matches, and refresh failure with stale data; repeat the narrow-width check with long names and expanded translated labels. Measure primary-text contrast once.

These checks could reduce the severity of identification, legibility, and state concerns—or expose additional blockers. They would not by themselves resolve the described placement of the work queue beneath secondary content.


## Output B

## 1. Diagnosis

The described workspace prioritizes reporting and visual containers over urgent exception triage, making it harder for merchandising analysts to identify what needs action, by when, and with what financial consequence.

**Evidence label: description-only assessment.** Findings follow from the supplied static description; actual rendering, behavior, contrast ratios, and accessibility remain unverified.

## 2. Findings

### Blocking findings
Here, “blocking” means blocking confidence in the primary decision flow, not a demonstrated runtime defect.

1. **The actionable queue is below the fold.** Eight KPIs, a large chart, and generic insights precede the exception table. Analysts must pass retrospective context before reaching the work that matters in the next hour.
2. **Urgency has no clear visual priority.** Revenue risk and blocked SKUs receive the same treatment as yesterday’s page views; deadlines and financial impact have little emphasis within rows. The hierarchy does not distinguish “act now” from “observe.”
3. **Status and actions require interpretation.** Color-only dots lack visible status names, and three unlabeled action icons make users infer consequences. This obstructs confident scanning and execution; accessible names are unknown.
4. **Product identification is weakened.** Fixed truncation at 24 characters can conceal the distinguishing part of similar product names, creating a risk of acting on the wrong item.
5. **Reading density is achieved through small, faint text.** The described 12–13px low-contrast body copy makes sustained scanning harder, particularly for owners, deadlines, and issue details. An actual contrast failure cannot be established without colors.

### Secondary findings
1. **Page context is fragmented.** Four weakly aligned rows separate title, date range, export, and freshness information while consuming vertical space.
2. **Global controls compete with local work.** Six equally weighted navigation links and a bright “Create” button provide little prioritization for exception handling. The 64px header height itself is reasonable.
3. **Containers obscure structure.** Nested cards, universal borders, large radii, and shadows assign visual importance to almost everything.
4. **Insights provide no decision support.** “Monitor performance closely” identifies neither affected items nor a reason or next step; equal blue sparklines similarly fail to communicate relative relevance.
5. **Operational resilience is unspecified.** Empty, loading, error, focus, narrow-laptop, and translation states are evidence gaps, not confirmed missing implementations.

## 3. Concrete redesign moves

Preserve the navy/ink system, existing amber/red meanings, real records, metric definitions, and action workflows. No gradients, glass, decorative imagery, or rebrand is needed.

| Move | Acceptance criteria |
|---|---|
| **1. Put the exception queue first.** Order the page as compact context → operational summary → exception table → supporting analysis. | At a proposed 1366×768 desktop test size, the table header and at least three complete rows are visible without scrolling. No chart or insight block precedes the queue. |
| **2. Make the next-hour scope explicit.** Provide a clearly labeled view for overdue and next-60-minute exceptions, with an obvious route back to all exceptions. Use existing deadline data and business rules. | The view states its scope and time zone; overdue items remain included. Sort order is visible and reversible, with deadline urgency first and financial impact as a tie-breaker unless established rules dictate otherwise. Records with unknown deadlines remain discoverable rather than silently excluded. |
| **3. Replace eight equal cards with a compact, ranked summary.** Give revenue risk and blocked SKUs priority; demote sell-through and page views to supporting analysis. | All eight metrics remain accessible with unchanged values and definitions. Each displayed metric identifies its reporting period and scope; historical totals cannot be mistaken for next-hour queue totals. Sparklines remain only where their trend informs a decision. |
| **4. Give rows a decision hierarchy.** Emphasize product identity, issue, and deadline; right-align financial impact using tabular figures; keep owner and status readable. Replace fixed character truncation with flexible width and wrapping. | Every existing column remains available. Full product names are retrievable by keyboard and pointer, not hover alone. Deadline presentation distinguishes overdue from upcoming and exposes an exact timestamp; monetary units remain explicit. |
| **5. Label status and actions.** Add status text beside existing semantic colors. Show the most relevant existing row action with its verb; place remaining actions in a labeled menu where appropriate. | Status is understandable without color. Each existing action retains its permissions, confirmation behavior, and outcome. Controls have visible or accessible names, and action meaning is available without guessing an icon. |
| **6. Consolidate context and quiet the header.** Align title and concise subtitle with date range/export controls; place refresh status alongside the scope it describes. Keep “Create” available but visually secondary here. | Page context uses no more than two compact rows at the desktop test size. Current navigation is distinguishable; all six destinations, search, utilities, and Create remain reachable. Freshness is labeled with a timestamp, not implied by the reporting date range. |
| **7. Flatten surfaces and establish readable density.** Use one table surface, restrained separators, 8/16/24px spacing roles, and approximately 14px primary table text in the existing typeface. Move the chart below the queue and remove unsupported insight filler. | No nested chart cards or routine panel shadows remain; elevation is reserved for overlays. Body text meets 4.5:1 contrast when measured. Any retained insight names a data-backed condition and links to affected records; otherwise omit it. |
| **8. Specify operational states without changing workflows.** Separate “no exceptions” from “no filter matches”; distinguish first load from refresh; show failures and stale data explicitly. | Filter-empty offers reset; initial failure offers retry; refresh failure preserves last-known data with its timestamp and a stale warning. Pending and failed row actions communicate their outcome, prevent duplicate submission, and preserve context and keyboard focus. |

## 4. Verdict and score boundary

**Verdict: substantial hierarchy revision needed before this can be endorsed as a next-hour operations workspace.**

No numerical score is warranted: the description supports a strong judgment about task alignment, but not a calibrated score for visual execution or overall usability. State and accessibility readiness remain unresolved.

## 5. Smallest validation plan that could change the verdict

These are proposed checks, not completed validation.

1. **One task in the primary supported browser, at 1366×768.** Have a merchandising analyst find the highest-priority next-hour exception, identify its owner, deadline, and impact, then begin the correct existing action. Record time, wrong selections, and interpretation pauses. Confirm the queue’s initial visibility and agreement with the established priority rules.
2. **One narrow-laptop pass at 1024×768, plus a 200% zoom check.** Use actual longest product names and a long-label translation fixture. Check navigation, filters, name retrieval, and action access; any necessary horizontal scrolling should be confined to the table, with no inaccessible columns or clipped controls.
3. **One keyboard-only task path.** Traverse scope/filter controls, table sorting, full-name disclosure, row actions, and return focus. Inspect relevant control names, table headers, visible focus, and measured text/status contrast.
4. **One compact state matrix.** Exercise initial loading, no exceptions, no matches, initial failure, refresh failure with stale data, and row-action pending/failure. Verify truthful freshness, recoverability, retained context, and no duplicate action.

Successful task performance could soften the predicted severity; ambiguous selection, hidden urgency, inaccessible actions, or misleading freshness would strengthen the blocking verdict.


## Output C

## 1. Diagnosis

The described screen prioritizes dashboard furniture over urgent exception handling, making analysts work to find, assess, and act on the items that matter in the next hour.

**Evidence label: description-only critique.** Findings below concern the supplied layout and content; actual rendering, interaction, accessibility, and task completion remain unverified.

## 2. Findings

“Blocking” means a barrier to endorsing this design for its stated job—not a verified runtime failure.

### Blocking

| ID | Finding | Static evidence and consequence |
|---|---|---|
| B1 | **The actionable queue comes too late.** | Four context rows, eight KPI cards, and nested chart/insight cards precede a table explicitly described as below the fold. Analysts encounter reporting before work requiring action. |
| B2 | **Urgency has no clear visual hierarchy.** | Revenue risk and blocked SKUs receive the same treatment as yesterday’s page views; table fields have similar weight. Neither the summary nor the queue clearly answers “what needs attention first?” |
| B3 | **Status and actions require interpretation.** | Small colored dots carry status without text, and three unlabeled icons carry row actions. This weakens scanability and action confidence; accessible names and tooltips are unknown. |
| B4 | **Product identification and comparison are fragile.** | Names truncate at 24 characters, while body text is 12–13px low-contrast gray. Similar products may become indistinguishable, and deadlines, ownership, and impact are harder to compare. Full-name access and measured contrast are unknown. |

### Secondary

| ID | Finding | Static evidence and consequence |
|---|---|---|
| S1 | **Global controls compete with the local job.** | Six equally emphasized navigation links and a bright Create button offer no described prioritization for exception triage. Their actual frequency of use is unknown; removal is not justified. |
| S2 | **Surface styling obscures grouping.** | Universal borders, 16px radii, shadows, nested cards, and gaps ranging from 8px to 48px create competing boundaries. Generic insights consume space without supplying a decision or action. |
| S3 | **Operational resilience is unspecified.** | Empty, loading, error, focus, narrow-laptop, and long-translation states are not described. This is an evidence gap—not proof they are missing—but it prevents confidence in daily use. |

## 3. Redesign moves and acceptance criteria

Retain the navy/ink system, semantic amber/red, real table data, and existing workflows. No rebrand or decorative effects are needed.

| Move | Concrete change | Acceptance criteria |
|---|---|---|
| **1 — Put the queue first** · B1 | Combine title/subtitle and date/export/refresh into two aligned rows. Follow with a compact operational summary and the exception table; move the chart and supporting analysis below the queue. | At a proposed 1366×768 desktop test viewport, the table header and at least three real exception rows appear without scrolling. Date scope and last successful refresh remain visible. |
| **2 — Establish next-hour priority** · B2 | Give existing revenue-risk and blocked-SKU metrics precedence; demote page views and broad performance metrics to secondary reporting. Provide an explicit “Due in the next hour” view, with overdue items distinguishable. Preserve access to all records. | The active scope and sort are visible. With analyst-approved rules, overdue items precede upcoming deadlines, with financial impact breaking ties. Metric labels identify their time scope; no new unsupported calculation is implied. |
| **3 — Make row decisions explicit** · B2, B3 | Emphasize issue and deadline; keep owner readable and align financial impact numerically. Pair each status with a text label. Show the existing most-used action by name and place remaining actions in a labeled menu. | A row answers “what is wrong, when, who owns it, what is at risk, and what can I do?” without interpreting color or guessing icons. Every current action remains available; labels match its actual effect. |
| **4 — Restore readable identity** · B4 | Replace fixed character truncation with width-aware names, allowing two lines where useful and an explicit full-name reveal. Use approximately 14px for core table text, reserving smaller type for secondary metadata. | Two products sharing the first 24 characters remain distinguishable. Full names are available by keyboard as well as pointer. Normal-size text reaches at least 4.5:1 contrast; density is checked against Move 1 rather than shrinking text to fit. |
| **5 — Quiet, don’t dismantle, the header** · S1 | Keep navigation, search, and Create in their existing workflows, but make the current section clear and reduce Create’s visual emphasis unless creation is demonstrably central to triage. Give icon controls clear names and discoverable labels. | In a short scan test, analysts identify the exception queue before Create. Search and creation remain easy to find, and no existing destination or capability is lost. |
| **6 — Flatten the reporting chrome** · S2 | Remove card-inside-card framing. Use one restrained table container, row separators, and a consistent 8/16/24px spacing rhythm. Remove generic insight copy; retain only observations grounded in available data that lead to an existing filtered view or action. | Every remaining boundary denotes a meaningful group. Shadows are reserved for overlays, not every region. Every insight states a specific condition and a useful next step; otherwise it does not occupy the primary workspace. |
| **7 — Specify recovery and constrained layouts** · S3 | Define distinct no-exceptions, no-filter-matches, initial-loading, refresh-failure, and action-failure states. Keep usable prior data on refresh failure with a stale-data notice. Define visible focus, long-label wrapping, and table-only horizontal overflow for constrained widths. | Empty states distinguish “nothing needs action” from “nothing matches.” Failures offer retry without silently clearing scope or losing the selected item. Keyboard focus stays visible; long labels do not conceal controls; overflow does not push the whole page sideways. |

## 4. Verdict and scoring boundary

**Verdict: substantial hierarchy revision needed before visual polish.** The description supports this judgment because the primary work is explicitly below the fold and its status/action cues are ambiguous.

**No numeric score assigned:** a number would imply more precision about visual execution and usability than this description permits.

## 5. Smallest validation plan that could change the verdict

These are proposed checks, not completed validation.

1. **Two desktop sizes, one supported browser:** inspect 1440×900 and 1280×720 with representative real rows, including long names and high-impact overdue items. Check first-screen queue visibility, readable density, and contained overflow; repeat the narrow case at 200% zoom with expanded translated labels.
2. **One triage task with two merchandising analysts:** ask each to find the highest-priority next-hour exception, identify its owner and impact, then initiate the existing appropriate action. Use a provisional target of 30 seconds with no status or action misinterpretation; confirm the priority rule with them.
3. **One keyboard and semantics pass:** traverse scope controls, sorting, a full product name, the primary row action, and the action menu. Check focus visibility, accessible names, table relationships, and contrast.
4. **One compact state exercise:** trigger initial loading, no exceptions, no filter matches, refresh failure with retained data, and row-action failure. Verify distinct messages, recoverability, and preserved context.

Successful task performance and clear, operable row cues could reduce the blocking severity. Attractive styling alone would not.
