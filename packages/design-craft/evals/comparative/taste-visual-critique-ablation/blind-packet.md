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

This should be a calm, precise exception workspace for merchandising analysts, but the described hierarchy promotes general reporting and chrome above identifying, prioritizing, and acting on next-hour exceptions.

**Evidence: static description plus product context only.** No rendered surface or behavior was inspected; “blocking” below means blocking design approval for the stated job, not a demonstrated runtime failure.

## 2. Findings

### Blocking

| ID | Finding and supplied evidence | Consequence / remaining unknown |
|---|---|---|
| B1 | **The actionable queue is buried.** The exception table starts below the fold after eight KPIs, a large chart, and nested insights. | Analysts must pass reporting content before reaching their primary work. Actual fold depth and time to find an urgent exception remain unmeasured. |
| B2 | **Emphasis does not encode operational priority.** Revenue risk, blocked SKUs, sell-through, and yesterday’s page views share identical cards, 28px numbers, and equal blue sparklines. | Historical volume competes with imminent risk. Whether any existing metric specifically represents the next hour is unknown. |
| B3 | **Rows conceal meaning at the point of action.** Similar text weights, dot-only statuses, 24-character product truncation, and three unlabeled action icons weaken identification and decision-making. | Users may need repeated inspection to distinguish products, interpret status, and choose an action. Accessible names and any existing detail disclosures are unknown. |
| B4 | **Decision-bearing text is visually underpowered.** Body text is described as 12–13px and low-contrast gray. | Dense scanning becomes harder precisely where accuracy matters. Actual contrast ratios, font metrics, and scaling behavior are unknown. |
| B5 | **Prominent analysis lacks a demonstrated decision role.** The chart occupies substantial space; “Monitor performance closely” supplies neither evidence nor a next step. | These modules consume attention without helping select an exception. The chart’s data and operational usefulness remain unspecified. |

### Secondary

| ID | Finding and supplied evidence | Consequence / remaining unknown |
|---|---|---|
| S1 | **Page context is fragmented and global actions compete.** Five context/control elements occupy four weakly aligned rows; the 64px header gives six links equal emphasis alongside search, three icons, and bright “Create.” | Scope, freshness, and local actions are harder to read together. Active navigation and Create’s operational relevance are unknown. |
| S2 | **Surface treatment overwhelms grouping.** Gaps vary from 8–48px; every region has a border, 16px radius, and shadow, including nested cards. | Boundaries look equally important and consume density. Exact rendered spacing and token consistency are unknown. |
| S3 | **Resilience is unspecified, not proven absent.** Empty, loading, error, focus, narrow-laptop, and long-translation states are undescribed. | Readiness cannot be established from this brief. Their actual implementations require inspection. |

## 3. Concrete redesign moves and acceptance criteria

All moves retain real data, existing action outcomes, and navigation destinations. Preserve navy/ink neutrals and semantic amber/red; introduce no gradients, glass, decorative illustration, or rebrand.

1. **Consolidate the command/context band — S1.**  
   Put title and concise subtitle on one shared left axis; group date scope, export, and last successful refresh beside or immediately below them. Keep the 64px header, distinguish the active destination, and reduce Create’s visual prominence unless it directly serves exception handling.  
   **Accept:** At desktop width, page context uses at most two aligned rows; scope and freshness are readable together; all existing global controls remain available.

2. **Replace equal KPI cards with a compact priority summary — B2.**  
   Lead with existing revenue-risk and blocked-SKU measures; demote sell-through and yesterday’s page views to supporting context without deleting their data. Remove uniform blue sparkline emphasis; retain trends only with a clear period and analytical purpose.  
   **Accept:** Risk/blockers are visibly dominant through order and type, not decorative color; each metric states its actual scope/period; nothing is relabeled “next hour” unless the underlying data supports that scope.

3. **Make the exception table the first substantial work surface — B1.**  
   Place it immediately after the compact summary, ahead of historical analysis. Keep existing filters and sorting adjacent; expose deadline-based triage using existing data, with overdue work distinct from work due within the next hour. Preserve a route back to the full queue and existing saved views.  
   **Accept:** Proposed desktop targets of 1440×900 and 1280×720 show the table header and at least three complete rows at 100% zoom; any active urgency filter and sort are explicit, with no silently excluded records.

4. **Give each row an identity → urgency → impact → action reading order — B3.**  
   Emphasize product and issue, make deadlines easy to scan, and right-align financial impact with tabular numerals. Add text to existing status semantics. Replace fixed 24-character truncation with available-width wrapping and keyboard-accessible full-name disclosure. Show the main existing action as a labeled control; place remaining actions in a labeled menu.  
   **Accept:** A row communicates product, issue, deadline, impact, status, and available action without interpreting color or icons alone; full names remain retrievable without hover; all current actions and owner information remain accessible.

5. **Turn the chart and insights into optional diagnostic evidence — B5.**  
   Move the area chart below the queue in a single flat section. Name the operational question it answers; if it is only historical context, label it accordingly. Remove generic insight copy rather than inventing findings.  
   **Accept:** Each retained insight names a real entity/segment, observed count or threshold, impact or urgency, and owner/next action, with a direct route to affected records; otherwise it is omitted. Chart data remains available without nested card framing.

6. **Apply a dense, readable visual grammar — B4, S2.**  
   Use existing tokens where suitable; otherwise provisionally set decision-bearing table/body text to at least 14px/1.4, reserving 12–13px for secondary metadata. Use ink for primary text, restrained secondary gray, and semantic status color. Standardize 8px related-item, 16px group, and 24px section gaps. Replace repeated card borders with row dividers; use one container boundary per genuine group, 4–8px radii for controls/panels, and shadows only for overlays.  
   **Accept:** Normal text meets 4.5:1 contrast; critical information is not muted metadata; spacing follows named roles; no ordinary region retains the blanket border-plus-16px-radius-plus-shadow treatment.

7. **Define trustworthy data and recovery states — S3.**  
   Separate “no exceptions,” “no filter matches,” initial loading, refreshing existing data, and failed refresh. Preserve loaded rows during refresh and expose their age; provide local retry and clear-filter recovery where appropriate.  
   **Accept:** Unknown/loading values never masquerade as zero; failed updates never appear current; each empty/error state explains what happened and provides a relevant next step without resetting the analyst’s scope.

8. **Specify narrow-width, long-content, and keyboard behavior — B3, S3.**  
   At narrow laptop widths, wrap the context controls before squeezing decision text. Keep the table’s full data available through a clearly scoped horizontal scroller if necessary, rather than silently hiding columns. Allow long labels and names to expand. Define visible focus and labels for global icons, row actions, menus, and disclosures.  
   **Accept:** No page-wide horizontal overflow or clipped controls at 1280×720; table overflow remains operable; doubled-length labels preserve meaning; keyboard users can filter, inspect a full name, invoke an action, and return without losing focus.

## 4. Verdict and score

**Verdict: redesign the attention hierarchy before cosmetic polish.** The described ordering and row ambiguity conflict directly with the next-hour exception task.

**No numeric score:** the description supports this structural verdict, but not a defensible overall score for visual execution, accessibility, or resilience.

## 5. Smallest validation plan that could change the verdict

These are proposed checks, not completed validation.

1. **Inspect the current baseline first:** in the supported desktop browser, use real representative data at 1440×900 and 1280×720. Record the fold, visible rows, context alignment, and actual computed type, contrast, spacing, radius, and shadow treatments.
2. **Run one end-to-end analyst task:** identify the highest-priority next-hour exception under existing business rules, verify product/owner/impact, and invoke the appropriate existing action safely. Observe whether current sorting, disclosures, and labels materially mitigate B1–B3.
3. **Repeat the critical path with keyboard and stressed content:** use long, similar product names, doubled-length labels, and 200% zoom; inspect focus visibility, action names, overflow, and access to complete values.
4. **Exercise only the decisive state set:** initial loading, successful zero exceptions, filtered zero results, and failed refresh with previously loaded data. Check freshness, recovery, and retained scope.

The verdict could soften if the current baseline already makes urgent work visible and unambiguous through mechanisms omitted from the description. Otherwise, test the same task and conditions after the targeted redesign; a cleaner appearance alone would not resolve it.


## Output B

## 1. Diagnosis

The screen gives navigation, routine metrics, and decorative containers more prominence than urgent exceptions, making it poorly aligned with a merchandising analyst’s next-hour triage job. **Evidence: supplied static description only; no rendered or runtime validation.**

## 2. Findings

### Blocking
1. **The action queue is below the fold.** Eight equally prominent KPIs, a chart, and generic insights precede the exception table—the primary surface for deciding what needs action now.
2. **Urgency has no clear hierarchy.** Revenue risk and blocked SKUs compete equally with yesterday’s page views; within the table, issue, deadline, impact, and action lack sufficient differentiation.
3. **Status and actions require decoding.** Small color-only dots do not explicitly communicate status, and three unlabeled action icons obscure the available next steps. Their accessible names are unknown.
4. **Product identification is unnecessarily constrained.** Truncation at 24 characters can hide distinguishing variant or product details, increasing ambiguity when assigning or resolving an exception.
5. **Core reading is visually underpowered.** The described 12–13px low-contrast body text undermines sustained scanning of a dense operational queue. Exact contrast compliance cannot be determined from the description.

### Secondary
1. **Header competition:** six equal navigation links and a bright blue “Create” action claim attention without an established relationship to exception triage.
2. **Fragmented context:** four weakly aligned rows separate title, time scope, export, and freshness information that should be understood together.
3. **Unhelpful interpretation:** “Monitor performance closely” offers neither a specific exception nor a decision or next step.
4. **Excessive enclosure:** nested cards, universal shadows, and 16px radii make every region compete as a separate object rather than supporting a coherent workspace.
5. **Unspecified resilience:** empty, loading, error, focus, narrow-laptop, and translation states remain evidence gaps—not demonstrated failures.

## 3. Redesign moves and acceptance criteria

| # | Concrete move | Acceptance criteria |
|---|---|---|
| 1 | **Put the exception queue immediately after compact page context and a short triage summary.** Move the chart and supporting analysis below it; preserve access to existing reporting workflows. | At the agreed desktop and narrow-laptop reference sizes, the table header and at least three exception rows are visible without vertical scrolling. No real table fields or actions are removed. |
| 2 | **Replace eight equal KPI cards with a ranked summary.** Emphasize revenue risk and blocked SKUs; give sell-through and traffic a quieter supporting position. Remove equal blue sparklines unless their trends inform triage. | No more than three metrics receive primary emphasis. Each metric states its period and scope. Any metric that filters the queue visibly identifies the resulting filter and offers a clear reset. |
| 3 | **Make next-hour triage explicit.** Offer clearly named time-scope controls and a visible sort, using existing deadline and financial-impact data rather than inventing a risk model. | Analysts can isolate overdue and next-hour items, see the active scope, and return to the full queue. Deadline ordering and impact tie-breaking are explicit; missing deadlines remain discoverable rather than silently excluded. Existing saved views are preserved. |
| 4 | **Rebuild row hierarchy around identification, urgency, and decision.** Make product and issue readily scannable, deadline and impact prominent, and owner supporting. Add status text; retain amber/red for their existing semantic meanings. | Every status is understandable without color. Impact values use consistent currency formatting and alignment. Full product names are available on keyboard focus or through the existing detail workflow—not hover alone—and distinguishing product information remains visible where available. |
| 5 | **Expose the next action in words.** Use the existing primary row action as a labeled control; place less frequent actions in a labeled “More actions” menu. | Visible labels describe what each action does. Every current action remains reachable; keyboard users can open, operate, and dismiss the menu with focus returning predictably. No new action semantics are invented. |
| 6 | **Consolidate context and quiet global chrome.** Align title/subtitle, date range, export, and refresh status in one compact heading zone. Retain navigation and Create, but reduce their competition with triage. | Date scope and last successful refresh are visible together. Export scope is explicit. Create remains easy to locate without being the strongest accent on the page; the active navigation destination is distinguishable. |
| 7 | **Flatten the visual system and strengthen reading.** Preserve navy/ink neutrals, use one main table surface, remove redundant card wrappers and shadows, and adopt a consistent spacing scale. Start table body text at 14px, reserving smaller text for secondary metadata. | Normal text meets 4.5:1 contrast when measured. Gaps follow a documented rhythm such as 8/16/24/32px. Semantic amber/red is not reused decoratively. Insight copy names a supported issue and useful next step, or is removed. |
| 8 | **Specify operational states before sign-off.** Distinguish no exceptions, no filter matches, initial loading, refresh failure, and unavailable data; define focus and constrained-width behavior. | A refresh failure preserves previously loaded data with a stale-data notice and retry. Loading preserves table geometry. Filter-empty states offer reset. At narrow widths and with expanded labels, product identity, urgency, and the primary action remain usable; any table overflow is deliberate and keyboard reachable. |

## 4. Bounded assessment

**Static verdict: substantial revision needed before visual sign-off.** Confidence is high in the hierarchy problem because the primary queue is explicitly below the fold and urgent information receives equal emphasis with routine metrics. A numerical score would imply unsupported precision; actual task speed, contrast, keyboard operation, and responsive quality remain unverified.

## 5. Smallest validation plan that could change the verdict

Use one representative build in a supported desktop browser with real-length product names, varied deadlines, and existing workflows:

1. **Two viewport checks:** 1440×900 and 1280×720. Confirm initial queue visibility, column readability, full-name access, and action reachability.
2. **One short task with two merchandising analysts:** find the highest-impact exception due within an hour, identify its owner/status, and initiate the appropriate existing action. Observe hesitation, misidentification, and detours; do not substitute a visual preference vote.
3. **One keyboard pass:** traverse filters, product details, and row actions; verify visible focus, meaningful control names, and menu focus return. Measure the actual text and control contrast.
4. **One compact state fixture:** exercise loading, no exceptions, no matches, and failed refresh; then repeat the narrow-laptop check with long product names and expanded translated labels.

The verdict could improve if the revised first view supports accurate triage without detours and these checks preserve context and actions. Static polish alone would not establish that.


## Output C

## 1. Diagnosis

The described workspace prioritizes general reporting over exception triage, burying the actionable queue while making urgency, product identity, and next actions unnecessarily difficult to distinguish.

**Evidence label: description-only critique.** Findings below derive from the supplied static specification; actual rendering, behavior, contrast ratios, and task performance remain unverified.

## 2. Findings

### Blocking findings
“Blocking” here means obstructing the primary decision flow, not a verified runtime failure.

1. **The work queue comes after the overview.** Eight KPIs, an area chart, and nested insights push exceptions below the fold. Analysts must pass reporting content before finding what needs action within an hour.
2. **Priority is visually flattened.** Revenue risk and blocked SKUs have the same treatment as yesterday’s page views; within the table, deadline and impact receive no stronger emphasis than supporting information. The screen offers little guidance on what to inspect first.
3. **Status and action require interpretation.** Color-only dots do not state the condition; three unlabeled action icons do not explain the available operations. This undermines confident triage even before keyboard or assistive-technology behavior is considered.
4. **Product identification is compromised.** A fixed 24-character truncation can hide the distinguishing part of a product name. No full-name recovery is described, creating a risk of acting on the wrong item.
5. **Decision text is difficult to read as specified.** Small, low-contrast body text affects repeated scanning of issues, owners, and deadlines. Exact contrast failure cannot be established without actual colors.

### Secondary findings

1. **Context is fragmented across four rows.** Title, scope, export, and freshness should establish one coherent operating context, not compete for vertical space.
2. **Global chrome competes with local work.** Six equal navigation links and a bright Create button give unrelated destinations and creation disproportionate prominence. The 64px header height itself is reasonable.
3. **Insights consume space without reducing uncertainty.** “Monitor performance closely” identifies neither an affected exception nor a concrete next step.
4. **Containers overwhelm grouping.** Repeated borders, large radii, shadows, and nested cards make every region look equally important; inconsistent gaps further weaken relationships.
5. **Operational resilience is unspecified.** Missing descriptions of loading, empty, error, focus, narrow-laptop, and translation states are evidence gaps, not proof those states are absent.

## 3. Redesign moves and acceptance criteria

Keep the existing navy/ink neutrals, amber/red meanings, real data, and workflows. No rebrand, gradients, glass, or decorative assets.

| # | Concrete move | Acceptance criteria |
|---|---|---|
| 1 | **Make exceptions the first substantial content region.** Order the page: compact context, concise priority summary, exception queue, supporting analysis. Move the chart below the queue without removing its existing functions. | At a proposed 1366×768 desktop target, table headings and at least five typical rows are visible without page scrolling. Existing chart access and table workflows remain available. |
| 2 | **Replace eight equal cards with a compact, ranked summary.** Lead with revenue risk and blocked SKUs; place sell-through and page views in secondary reporting. Remove repetitive sparklines unless their trends affect a decision. | Every headline metric has a clear scope and period. Any metric-to-table link uses the same underlying scope, with no invented totals or implied causal relationships. All existing metrics remain reachable. |
| 3 | **Expose a next-hour queue view.** Using existing deadline and status data, offer an explicit “Due within 1 hour” filter that includes overdue unresolved items. Propose deadline-first sorting, with financial impact as a tie-breaker, for analyst confirmation. | Active filters, sort order, result count, timezone, and time boundary are visible. Undated items remain discoverable; users can return to the full queue. No opaque priority score is introduced. |
| 4 | **Give rows a decision hierarchy.** Make product and issue the reading anchor; emphasize deadline and financial impact; keep owner quieter but readable. Right-align financial values with tabular numerals. Add text to existing status colors. Replace icon-only actions with explicit labels, using a labeled overflow menu only where necessary. | Each row answers “which item, what problem, by when, how much, who owns it, what can I do?” without interpreting color or hovering. Every current action retains its permissions and behavior; no destructive operation becomes easier to trigger accidentally. |
| 5 | **Restore product identity and readable density.** Replace character-count truncation with a wider product column and controlled wrapping. Provide full text through keyboard-accessible expansion or the existing detail view. Start with 14px decision text in the current typeface. | Similar product names remain distinguishable using existing identifying data. Full names are available without pointer-only hover. Normal text meets a measured 4.5:1 contrast target; density is not achieved by fading critical information. |
| 6 | **Compress the context and quiet the header.** Align title and concise scope on the left, date range/export on the right, and last successful refresh alongside them or on one secondary line. Reduce Create’s visual prominence while retaining access. | Context occupies no more than two rows at the desktop target. Selected date range and data freshness are visibly distinct. All six navigation destinations, search, and current utilities remain reachable. |
| 7 | **Flatten surfaces and remove non-actionable prose.** Use one table surface, restrained separators, and an 8/16/24px spacing rhythm. Reserve shadows for overlays; use tighter, consistent control radii. Remove generic insights or replace them only with evidence-backed exception links. | No card exists solely to surround another card. Each retained insight names the condition and affected scope and leads to relevant records; otherwise it is omitted. Amber/red remain semantic, not decorative. |
| 8 | **Specify compact operational states and constrained-width behavior.** Distinguish no exceptions from no filter matches; preserve last-known data on refresh failure with a stale warning and retry. Define initial loading, action failure, focus, and long-label behavior. | Loading never implies zero risk. Failed actions never appear successful. Refresh preserves filters and focus. At narrow widths, controls remain reachable and any horizontal scrolling is confined to the table, with product identity retained. Translated labels do not overlap or disappear. |

## 4. Verdict and score

**Verdict: needs targeted hierarchy and table-clarity redesign before it can credibly support next-hour triage.**

No numeric score is warranted: the description establishes substantial task-fit problems, but cannot support a defensible rating of rendered quality, interaction reliability, or accessibility.

## 5. Smallest validation plan that could change the verdict

These are proposed checks, not completed validation.

1. **One supported desktop browser, two sizes:** inspect 1366×768 and a 1024×768 narrow-laptop view using representative existing records, including long product names. Check initial queue visibility, column readability, control access, and overflow.
2. **One end-to-end triage task:** ask a merchandising analyst to identify an unresolved exception due within an hour, explain its deadline and impact, confirm its identity, and enter the correct existing action flow. Wrong-item selection or reliance on guessing icons sustains the blocking verdict.
3. **One keyboard and zoom pass:** traverse filters, sorting, product details, and row actions at normal scale and 200% zoom. Check visible focus, meaningful control names, full-name access, and focus return; measure text/status contrast.
4. **A small state fixture set:** exercise initial loading, no exceptions, no filter matches, failed refresh with stale data, and failed row action. Repeat the narrow view with expanded translated labels. Confirm that uncertainty is never presented as “all clear.”

The verdict improves only if analysts can reach and correctly interpret the urgent queue without identity or action ambiguity, and the state checks preserve that confidence. Visual polish alone would not change it.
