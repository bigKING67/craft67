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

This should be a calm, precise exception workspace for merchandising analysts, but the described hierarchy promotes overview metrics and containers ahead of identifying, prioritizing, and acting on work due in the next hour.

**Evidence: static description plus product context only.** Findings below are design judgments, not observed runtime failures; unspecified states are unknown, not proven absent.

## 2. Findings

“Blocking” means blocking design acceptance for the stated primary job—not demonstrated inability to complete a task.

### Blocking
| ID | Finding and supplied evidence | Decision-flow consequence |
|---|---|---|
| B1 | **The work queue is buried.** Four context rows, eight KPIs, an area chart, and nested insights precede the below-fold exception table. | Analysts must pass secondary information before finding actionable exceptions. Exact fold depth remains unverified. |
| B2 | **Urgency has no visual priority.** Revenue risk and blocked SKUs receive the same height, 28px numbers, and blue sparklines as yesterday’s page views. | Visual prominence does not distinguish immediate exposure from background context. Existing sorting/filtering behavior is unknown. |
| B3 | **Rows obscure identity, status, and action.** Decision fields have similar weight; status uses dots alone; product names truncate at 24 characters; actions are three unlabeled icons. | Analysts must decode meaning before choosing an action and may confuse similarly named products. Accessible names and full-name disclosure are unknown. |
| B4 | **Decision-bearing text is difficult to read as specified.** Body text is 12–13px and low-contrast gray. | Repeated comparison of deadlines, owners, and impact becomes unnecessarily demanding. Actual contrast ratios require measurement. |

### Secondary
| ID | Finding and supplied evidence | Decision-flow consequence |
|---|---|---|
| S1 | **The command hierarchy is fragmented.** A crowded 64px header and bright “Create” compete with four weakly aligned page-context rows. | Global creation attracts attention before local triage; scope and freshness are harder to read together. Actual header fit is unknown. |
| S2 | **Supporting analysis lacks a decision contract.** The chart’s operational question is unspecified; “Monitor performance closely” offers no entity, evidence, or next step. | Supporting content consumes space without establishing why an analyst should act. The chart’s actual analytical value is unknown. |
| S3 | **Surface treatment overwhelms grouping.** Every region has a border, 16px radius, and shadow; gaps vary from 8px to 48px. | Nested containers create competing boundaries instead of a clear scan path. Exact rendered density is unknown. |
| S4 | **Resilience is unspecified.** Empty, loading, error, focus, narrow-laptop, and long-translation states are not described. | Confidence in data freshness, recovery, and continued access to actions is limited; no state failure is established. |

## 3. Concrete redesign moves and acceptance criteria

Retain the navy/ink neutrals, semantic amber/red, real records, and existing workflow destinations throughout; introduce no gradients, glass, or decorative illustration.

1. **Consolidate the command and context bands — S1.**  
   Keep the global header, but reduce “Create” to a secondary treatment unless creation is demonstrably essential to triage. Put title and brief context on one aligned row; group date range, export, and refresh timestamp on a second.
   **Accept when:** page context uses at most two rows at the agreed desktop width, shares the table’s alignment edges, and distinguishes reporting period from last successful refresh; all existing navigation and actions remain available.

2. **Replace eight equal cards with a compact priority summary — B2.**  
   Lead with revenue risk and blocked SKUs, with explicit scope and period. Present sell-through and page views as subordinate diagnostics; retain their values without equal visual weight. Keep sparklines only when they help interpret risk.
   **Accept when:** immediate exposure is visibly dominant without relying on color; no next-hour metric is inferred from yesterday’s totals; a reviewer can distinguish operational risk from historical context at a glance.

3. **Make the existing exception table the primary working surface — B1, B2.**  
   Place it directly after the compact summary. Expose a clearly labeled “Next hour” view using existing deadline/status data, including overdue items where appropriate; preserve an obvious all-exceptions view and existing user-selected sorts.
   **Accept when:** at 1366×768, the table heading, scope controls, column headers, and at least three real rows are visible without page scrolling; time zone and inclusion rules are explicit, and filtering does not alter underlying records.

4. **Give supporting analysis a specific question—or remove its prominence — S2, B1.**  
   Move the area chart after the queue or into an existing diagnostic disclosure. Remove generic insight cards; retain an insight only if supported by real data naming the affected entity/segment, observed condition, impact or urgency, and a direct route to the relevant rows.
   **Accept when:** every retained chart states its question, units, and period; every insight leads to evidence or an existing action; no invented conclusions replace the generic copy.

5. **Redesign row emphasis without changing action semantics — B3.**  
   Emphasize product identity, issue, and deadline; right-align financial impact with tabular numerals. Add text to status indicators. Replace the arbitrary name limit with wrapping and keyboard-accessible full-name disclosure. Show the most relevant existing action as a labeled verb; place the others in a labeled menu.
   **Accept when:** similar long product names can be distinguished before acting; status is understandable without color; every original action remains reachable with an unambiguous label, and its target row is clear.

6. **Apply a restrained density and surface system — B4, S3.**  
   Use provisional 14px/1.4 typography for decision-bearing table/body text, retaining 12–13px only for secondary metadata. Use 8px within groups, 16px between related controls, and 24px between sections. Flatten nested cards; use row dividers, existing control radii, and at most one outlined surface per major section, with no resting content shadows.
   **Accept when:** normal text reaches at least 4.5:1 contrast; spacing follows the declared roles; borders identify actual groups rather than every wrapper; amber/red retain semantic meaning and ink/navy provide hierarchy.

7. **Specify trustworthy data and recovery states — S4.**  
   Distinguish “no exceptions,” “no filter matches,” initial loading, and failed refresh. Retain previously loaded data during refresh, labeled with its last successful timestamp; never render unknown values as zero. Keep recovery local.
   **Accept when:** each state explains what is known and offers the relevant retry or filter-reset action; failed refresh cannot masquerade as current data, and a successful row action produces clear confirmation without losing queue context.

8. **Define narrow-width, long-content, and keyboard behavior — S4, B3.**  
   Let command groups wrap intentionally; preserve decision columns rather than shrinking their text. If necessary, use a contained, keyboard-scrollable table with a clear overflow cue. Provide visible focus and meaningful names for global and row icon controls.
   **Accept when:** at 1280×720 and with roughly doubled labels, controls do not overlap or clip; full product names and all actions remain reachable; keyboard users can filter, inspect, act, dismiss menus, and recover focus without hover-only access.

## 4. Verdict and score boundary

**Verdict: redesign needed before design acceptance for next-hour triage.** The supplied evidence supports that conclusion through information order, equalized priority, row ambiguity, and text treatment.

**No numerical score assigned:** a composite score would imply precision about rendered quality and state robustness that this description cannot support.

## 5. Smallest validation plan that could change the verdict

This is a proposed plan, not completed validation.

1. **Inspect the current baseline first:** in one supported desktop browser, at 1366×768 and 1280×720, record the actual fold, visible exception rows, computed text sizes/contrast, spacing, and existing priority controls. Confirm whether the description matches the current surface.
2. **Run one representative triage task:** ask an analyst to identify the highest-priority next-hour exception, explain its issue, deadline, impact, and owner, then invoke the appropriate existing action. Observe decoding errors and unnecessary scrolling; use a provisional 30-second identification target, not a claimed benchmark.
3. **Exercise one compact state/content set:** initial loading, genuine empty queue, no filter matches, failed refresh with prior data, a long product name, and expanded translations. Repeat the triage path using only the keyboard, including menu dismissal and focus return.
4. **Reassess only against observed evidence:** baseline evidence of a visible, clearly prioritized queue and unambiguous actions could soften the verdict; hidden data, unclear freshness, lost focus, or clipped actions would strengthen it. Apply the same checks to any later redesign before accepting it.


## Output B

## 1. Diagnosis

The screen gives navigation, generic analytics, and decorative containers more prominence than actionable exceptions, undermining analysts’ ability to identify, prioritize, and resolve the next hour’s work.

**Evidence label:** Description-only critique. Findings reflect the supplied static specification; no rendered layout, interaction, accessibility, or runtime behavior has been validated.

## 2. Findings

### Blocking
1. **The primary work queue is below the fold.** Eight equal KPIs, the chart, and generic insights precede the exception table, delaying access to the product’s core task.
2. **Urgency and consequence lack hierarchy.** Revenue risk and blocked SKUs compete with yesterday’s page views; within the table, issue, deadline, financial impact, and action have no clear emphasis. The described hierarchy does not help answer “what needs attention first?”
3. **Status and actions require guessing.** Small colored dots provide no visible status wording, and three unlabeled icons do not explain available actions. Accessible names and tooltips are unspecified, not proven absent.
4. **Product identification is compromised.** A fixed 24-character truncation can hide the differences between similar products, making confident selection harder.
5. **Dense data is presented with weak readability.** Small, low-contrast body text burdens repeated scanning of owners, deadlines, and issues. Exact contrast compliance cannot be determined from the description.

### Secondary
1. **The page controls consume unnecessary vertical space.** Four weakly aligned rows separate title, scope, actions, and freshness information that should be understood together.
2. **Header emphasis conflicts with the immediate job.** Six equally weighted links and a bright blue Create button compete with exception triage; Create may remain available without being the dominant visual cue.
3. **Generic insights occupy space without supporting a decision.** “Monitor performance closely” offers no specific exception, consequence, or next step.
4. **Container styling obscures grouping.** Nested cards, universal borders, large radii, shadows, and irregular gaps make almost every region look equally important.
5. **Important states are unspecified.** Empty, loading, error, focus, narrow-laptop, and translation behavior remain delivery risks—not confirmed defects.

## 3. Redesign moves and acceptance criteria

| # | Concrete move | Acceptance criteria |
|---|---|---|
| 1 | **Make the exception queue the first substantive section.** Put a compact priority summary above it; move the area chart and historical metrics below the queue or into an existing secondary view. | At the agreed desktop reference viewport, the initial viewport shows queue scope, column headers, and actionable rows. The chart does not precede the queue. All current data remains available. |
| 2 | **Replace eight equal cards with differentiated summaries.** Give revenue risk and blocked SKUs priority; treat sell-through and historical traffic as supporting context. Remove equal blue sparklines unless their trends inform triage. | Summary labels state their time window and scope. Historical metrics are visibly subordinate. No “next hour” total is shown unless the data supports that calculation. Amber/red retain semantic meaning rather than acting as decoration. |
| 3 | **Expose a next-hour queue view using existing deadlines and statuses.** Show the active scope and sort; prioritize overdue and imminent unresolved exceptions, with financial impact available as a secondary ordering criterion. | Analysts can distinguish overdue, due within an hour, and later work, and return to the complete queue. Missing deadlines are explicit rather than silently treated as low priority. Existing filters and workflows remain accessible. |
| 4 | **Give rows a deliberate reading order.** Make product and issue easy to identify, deadline and impact easy to compare, and owner quieter. Use aligned numeric impact values, textual statuses, and explicit deadline wording. Replace primary action icons with concise labels; retain secondary actions in a labeled menu. | Each row visibly answers “which product, what issue, when, how much, who, and what action?” Status is understandable without color. Action labels match existing operations rather than introducing new ones. |
| 5 | **Preserve product identity without fixed-character clipping.** Allocate more width to the product column and permit two-line names where needed. Provide full-name access by keyboard as well as pointer; show an existing identifier where available. | Similar long names can be distinguished before taking action. Full names are available without relying solely on hover, and no underlying product data is changed. |
| 6 | **Consolidate page framing and reduce header competition.** Align title and date scope in one compact band, with export and refresh status consistently grouped. Keep Create available but visually secondary to the queue; clearly distinguish the active navigation destination. | Scope and data freshness are visible near the queue. The current four-row preamble becomes no more than two rows at the reference desktop width, without hiding existing controls. |
| 7 | **Flatten surfaces and improve data typography.** Preserve navy/ink neutrals; use one table surface, restrained dividers, and a consistent 8px-based spacing rhythm. Target 14px for core table text, tabular numerals for financial values, and smaller text only for secondary metadata. Remove generic insight cards unless they identify a specific, data-backed action. | No card-within-card remains solely for decoration. Shadows and 16px radii are no longer universal. Normal text reaches at least 4.5:1 measured contrast; the queue remains dense without sacrificing label readability. |
| 8 | **Specify resilient queue states.** Define loading, no exceptions, no filter matches, failed refresh, keyboard focus, narrow-width overflow, and long-label behavior. Retain last-known data on refresh failure where feasible, explicitly marked stale. | Loading is distinguishable from zero results; filtered emptiness offers a reset; failure offers retry and freshness information. Focus remains visible. Narrow layouts and expanded labels do not conceal status, deadline, or action access. |

## 4. Score

**No numeric score assigned.** The description supports a clear structural verdict—**the hierarchy needs revision before acceptance for next-hour triage**—but not a defensible measurement of usability or visual execution.

## 5. Smallest validation plan that could change the verdict

Use one populated fixture with an overdue exception, one due within an hour, a high-impact later exception, and similar long product names.

1. **Two viewport checks:** one agreed desktop size, such as 1440×900, and one narrow laptop size, such as 1280×720. Check initial queue visibility, readable columns, full-name access, and reachable actions.
2. **One short task with a merchandising analyst:** “Find the exception you would act on in the next hour, explain why, and open its existing action.” Observe whether urgency, impact, and action are understood without guessing or detouring through analytics.
3. **One keyboard pass:** navigate scope controls, table actions, and any overflow menu; verify visible focus, meaningful control names, and full-name access.
4. **One compact state sweep:** loading → populated, no exceptions, no filter matches, and failed refresh with stale data; repeat the narrow layout with expanded translated labels. Measure text and focus contrast in the rendered surface.

**Verdict-changing evidence:** the queue is immediately discoverable, the analyst can justify a priority from visible data, and product identity, status, and actions remain clear across those checks. A tidier card system alone would not change the verdict.


## Output C

## 1. Diagnosis

The screen prioritizes retrospective reporting and generic creation over next-hour exception triage, burying the actionable queue while obscuring urgency, product identity, and available actions.

**Evidence label: description-only critique.** Findings below derive from the supplied static description; no rendered appearance, measured contrast, interaction behavior, or accessibility implementation has been validated.

## 2. Findings

### Blocking findings
Blocking here means materially obstructing the stated decision flow, not a proven runtime defect.

1. **The work queue is below the fold.** Eight KPIs, a chart, and nested insights precede the exceptions; analysts must pass reporting content before identifying what needs action.
2. **Operational urgency has no visual priority.** Revenue risk and blocked SKUs look equivalent to yesterday’s page views; within the table, deadlines and impact receive no meaningful emphasis. The surface does not support “what first?”
3. **Status requires color interpretation.** Small dots without text do not communicate explicit state or reliably distinguish operational meanings. Semantic amber/red should reinforce labels, not replace them.
4. **Identification and action are ambiguous.** Fixed 24-character truncation can conceal distinguishing product details, while three unlabeled action icons require guessing. This creates wrong-item and wrong-action risk.
5. **Essential reading is unnecessarily difficult.** Described low-contrast, 12–13px body text undermines repeated scanning of issues, owners, and deadlines. Exact contrast compliance cannot be determined from this description.

### Secondary findings

1. **The header competes with triage.** Six equally emphasized destinations and a bright “Create” button give navigation and creation prominence unrelated to the immediate job; the 64px height itself is reasonable.
2. **Four metadata rows waste attention and height.** Weak alignment separates page context, date scope, export, and freshness instead of making them a coherent control area.
3. **Chart and insight framing adds little decision value.** Nested containers consume space, while “Monitor performance closely” supplies neither a specific exception nor a next step.
4. **Universal decoration flattens hierarchy.** Borders, 16px radii, shadows, and inconsistent 8–48px gaps make every region compete rather than distinguish controls, context, and work.
5. **Operational states remain unspecified.** Empty, loading, error, focus, narrow-laptop, and translation behavior are evidence gaps, not confirmed missing implementations.

## 3. Concrete redesign moves and acceptance criteria

1. **Put the exception queue immediately after compact page context and an operational summary.**
   Move the chart and remaining reporting metrics below the table or into an existing secondary reporting area.
   **Accept when:** at a proposed 1366×768 CSS-pixel viewport, table controls, column headings, and at least five normal-height exception rows are visible without page scrolling; all existing data and reporting workflows remain reachable.

2. **Offer a clearly labeled next-hour triage view using existing fields.**
   Include actionable overdue items and items due within the next hour; expose the active scope. Propose deadline ascending, with financial impact descending as a tie-breaker, subject to existing business priority rules. Preserve the current all-exceptions view and saved preferences.
   **Accept when:** analysts can distinguish overdue from upcoming items, see the active sort, and return to the full queue in one action; no invented severity score or silent exclusion is introduced.

3. **Replace eight equal KPI cards with a compact, ranked summary.**
   Give revenue risk and blocked SKUs prominence; demote yesterday’s page views and other retrospective metrics. Remove equal blue sparklines unless each trend supports a triage decision.
   **Accept when:** primary metrics have explicit scope and period, retain their real values, and cannot be mistaken for next-hour totals if they cover a broader interval.

4. **Rebuild table hierarchy without dropping columns.**
   Emphasize product identity and issue; make deadlines conspicuous, with absolute time/time zone and a relative cue where useful. Right-align financial impact with tabular numerals. Keep owner and status legible but subordinate.
   **Accept when:** long names are no longer cut at a fixed character count; full identity is available through wrapping or keyboard-accessible disclosure; all seven existing fields remain available, and deadline precision is preserved.

5. **Make status and row actions explicit.**
   Pair existing status values with text and their current semantic amber/red treatment. Give the principal existing action a visible verb label; place secondary actions in a labeled menu if needed, retaining existing permissions and confirmations.
   **Accept when:** status is understandable without color, action meaning is available without hover, and every existing action remains reachable with pointer and keyboard.

6. **Consolidate the page controls and quiet global chrome.**
   Align title and concise context with date range, export, and refresh information in one compact band, allowing a second row where necessary. Keep “Create” available but reduce its visual dominance; distinguish the active navigation destination.
   **Accept when:** scope and last successful refresh are readable together, navigation remains available without collisions, and global creation no longer outweighs queue actions.

7. **Use a restrained, readable operations surface.**
   Preserve navy/ink neutrals and semantic amber/red. Start with 14px essential table text, sentence-case labels, and measured contrast; use an 8/16/24px spacing rhythm. Replace nested cards with section headings and row dividers; reserve shadows for overlays. Remove generic advice, retaining only evidence-backed insights that identify affected items and a relevant existing action.
   **Accept when:** normal text reaches at least 4.5:1 contrast, essential controls and focus indicators meet applicable contrast requirements, no nested chart card remains, and every retained insight has a specific operational referent. No gradients, glass, or decorative imagery are added.

8. **Specify trustworthy states and constrained-width behavior.**
   Distinguish “no exceptions” from “no filter matches”; separate initial loading from background refresh. On refresh failure, retain and clearly mark last-known data with its timestamp and retry control. Allow translated controls to reflow; contain any necessary horizontal scrolling within the table.
   **Accept when:** failed loading never appears as zero risk, refresh does not unexpectedly discard queue context, focus remains visible and unobscured, and long labels never hide or overlap actions.

## 4. Verdict

**Material revision required for the stated triage job.** The below-fold queue and explicitly ambiguous status/action presentation justify that verdict from static evidence alone.

No numeric score: a number would imply precision about rendered quality and behavior that this description cannot support.

## 5. Smallest validation plan that could change the verdict

These are proposed checks, not completed validation.

- **Browser and viewport:** use the team’s supported desktop browser at **1366×768**, then **1024×768**, plus one **200% zoom** pass. Check initial queue visibility, control collisions, full-name access, table scrolling, and action reachability.
- **One representative task:** with real authorized data containing overdue and next-hour exceptions, ask an analyst to identify the first item to address, explain why, identify its owner, and enter its existing action flow without committing a destructive change. Failure to establish priority or distinguish products sustains the blocking verdict.
- **One keyboard pass:** traverse queue scope, sort, product disclosure, row action, and secondary menu. Check visible focus, names, logical order, escape behavior, and focus return.
- **One compact state set:** exercise initial loading, background-refresh failure, true empty, filter-empty, and the longest supported translation with long product names. Confirm stale-data labeling and recovery without lost context.
- **Targeted measurements:** measure essential text, status, and focus contrast in the rendered surface.

A successful task pass and resolved identification/status/action blockers could soften the verdict; narrow-width or state failures could strengthen it. Undescribed behavior alone should not be treated as a demonstrated failure.
