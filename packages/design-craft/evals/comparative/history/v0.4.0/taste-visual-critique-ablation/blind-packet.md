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

# Blind scorecard

| Criterion | Weight | Full-credit evidence |
| --- | ---: | --- |
| Product hierarchy and decision flow | 15 | Reorders attention around next-hour exceptions and distinguishes lead, support, and historical information. |
| Anti-generic visual judgment | 15 | Identifies card soup, fake insight copy, equal emphasis, and decorative defaults without imposing a new generic aesthetic. |
| Typography, color, and surface craft | 15 | Gives specific readable type, semantic color, spacing, border, elevation, and scanability corrections under the stated authority. |
| Product fit and authority | 15 | Preserves the operations job, real data, workflows, and navy/semantic system rather than rebranding or turning the page into marketing. |
| Concrete redesign moves | 20 | Supplies prioritized implementation-ready moves and observable acceptance criteria for the header, KPI hierarchy, chart, table, states, and actions. |
| Evidence honesty | 10 | Labels static evidence, avoids invented runtime claims, and states what browser/responsive/state evidence could change the verdict. |
| Scope, prioritization, and output discipline | 10 | Stays read-only, within the requested budgets, avoids unrelated work, and distinguishes blocking from secondary polish. |

Total: 100.


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

**Evidence label: L0 static product-description evidence only.** The screen reads as a generic KPI dashboard when it needs to behave like an operations triage desk: the exception queue, risk severity, ownership, and next action are visually subordinate to chrome, equal cards, decorative charts, and nested surfaces.

## 2. Blocking findings

1. **Primary job is below the fold.**  
   The table containing product, issue, owner, deadline, financial impact, status, and action is the real work surface, but it starts after header rows, eight KPI cards, chart cards, and generic insight cards.

2. **Priority is flattened across unequal business signals.**  
   Revenue risk, blocked SKUs, sell-through, and yesterday’s page views receive the same card weight, type scale, sparkline treatment, and visual salience, so analysts cannot quickly tell what needs action in the next hour.

3. **Header and page command area consume attention without supporting triage.**  
   Six equal nav links, global search, three icon buttons, a bright blue “Create” button, and four weakly aligned title/status rows create a heavy top stack before the user reaches operational exceptions.

4. **The table does not support fast, safe decisions.**  
   Similar text weights across product, issue, owner, deadline, impact, status, and action make rows hard to scan; status dots are color-only; product names truncate too early; action icons are unlabeled.

5. **Surface treatment creates card soup instead of hierarchy.**  
   Borders, 16px radius, soft shadow, nested cards, and inconsistent gaps make every region feel equally important while adding visual noise to a dense operations workspace.

## 3. Secondary findings

1. **Text is likely too timid for an analyst workspace.**  
   12–13px low-contrast gray body copy may work for metadata, but not for primary row content, deadlines, issues, and financial impact.

2. **Generic insight copy weakens credibility.**  
   “Monitor performance closely” does not name the product, threshold, owner, impact, or recommended action, so it reads as filler rather than operational intelligence.

3. **Blue sparklines appear decorative rather than semantic.**  
   Equal blue trend lines on every KPI imply consistency where the business meaning differs; semantic amber/red should be reserved for warning and critical states.

4. **Spacing lacks a decision rhythm.**  
   8px to 48px gaps without a clear scale make relationships ambiguous: related controls feel detached, while unrelated cards feel equivalently grouped.

5. **Critical edge states are undefined.**  
   Empty, loading, error, keyboard focus, narrow-laptop, and long-translation states are not described, which is risky for a table-heavy operational surface.

## 4. Concrete redesign moves with acceptance criteria

1. **Collapse the page command area into one aligned operations bar.**  
   Combine title, subtitle/scope, date range, refresh status, and export into a single compact band under the header.  
   **Acceptance:** the first viewport shows the page purpose, current time window, data freshness, and at least the start of the exception queue.

2. **De-emphasize global chrome that does not serve hourly triage.**  
   Keep the navy/ink system, but reduce the bright “Create” button unless creation is part of this workflow; separate global navigation from page actions.  
   **Acceptance:** the strongest action above the fold is related to reviewing, filtering, exporting, refreshing, or resolving exceptions—not generic creation.

3. **Replace eight equal KPI cards with a triage hierarchy.**  
   Promote one lead risk object, such as “Revenue at risk,” “Critical blocked SKUs,” or “Exceptions due < 1h,” then use a compact supporting metric strip for secondary context.  
   **Acceptance:** an analyst can identify the top operational risk within three seconds; page views cannot visually compete with blocked revenue or missed deadlines.

4. **Move the exception table above the chart module.**  
   Treat the table as the primary work object and the chart as supporting diagnosis.  
   **Acceptance:** at 1440×900 and narrow-laptop heights, users can see table headers and multiple exception rows without scrolling past generic insight cards.

5. **Redesign table row anatomy for triage scanning.**  
   Order and weight columns by decision flow: product identity, issue/severity, financial impact, deadline/SLA, owner, status, action. Use stronger weight for issue, deadline, and impact.  
   **Acceptance:** each row can be scanned for “what is broken, how costly, who owns it, when due, what do I do” without decoding equal-weight text.

6. **Make status and actions explicit, not icon/color-only.**  
   Replace bare colored dots with labeled status pills or text-plus-color treatments; replace three unlabeled icons with visible action labels or an action menu with accessible names.  
   **Acceptance:** status remains understandable without color; each action is identifiable by text, tooltip, or menu label before activation.

7. **Simplify surfaces and establish a dense spacing/type system.**  
   Use fewer shadows, fewer nested cards, subtler dividers, and a consistent spacing scale; reserve raised treatment for true hierarchy or overlays. Raise primary table/body text to a more legible dense-product size.  
   **Acceptance:** repeated borders/radii/shadows no longer define every section; type roles clearly distinguish page title, section label, metric value, row primary text, metadata, and helper copy.

8. **Define operational states as part of the design, not afterthoughts.**  
   Specify loading skeletons, stale-data warning, empty exceptions, partial-error table state, keyboard focus, long product names, translated labels, and narrow-laptop behavior.  
   **Acceptance:** every critical module has empty/loading/error/focus/overflow handling, and long product names reveal enough identity through wrapping, expansion, tooltip, or secondary identifier.

## 5. Score band

**Static score band: 55–65 / 100.**  
Justification: the surface has the right raw ingredients—nav, KPIs, chart, table, status colors, export/refresh—but the static evidence shows the main workflow is buried, hierarchy is flat, actions are ambiguous, color-only status is risky, and edge states are undefined. I would not score it higher without evidence that the table, focus states, responsive layout, and real states work well in runtime.

## 6. Smallest validation plan that could change the verdict

1. **Desktop visual check:** one browser pass at a common desktop viewport, e.g. 1440×900, to verify whether the exception table is actually visible above the fold and whether hierarchy matches the static description.  
2. **Narrow-laptop check:** one pass around 1280×720 or similar to test whether header, command rows, KPI cards, and chart push the table out of reach.  
3. **Table interaction check:** keyboard through table rows, status controls, and action icons/menus to confirm focus visibility, labels, and activation order.  
4. **State check:** force or mock loading, empty exceptions, table error, stale refresh, long product names, and long translated labels.  
5. **Contrast/content check:** inspect primary table text, muted helper text, status treatments, and semantic amber/red usage against the navy/ink neutral system.


## Output B

1. **Diagnosis [static-description evidence]:** The screen reads as a generic reporting dashboard instead of an exception-first operations workspace, because attention is spent on navigation, equalized KPIs, nested cards, and chrome while the urgent exception table starts below the fold.

## Blocking findings

1. **Primary workflow is physically deprioritized.**  
   The table containing product, issue, owner, deadline, financial impact, status, and action is the actual decision surface, but it appears below the fold after KPI cards, a chart, and generic insight cards.

2. **Urgency hierarchy is flattened.**  
   Revenue risk, blocked SKUs, sell-through, and yesterday’s page views receive equal card size, type scale, and blue sparkline treatment, so “act in the next hour” signals are not visually separable from background metrics.

3. **The command/header area fragments attention.**  
   A 64px global header plus four separate rows for title, subtitle, date range, export, and refresh status creates weak alignment and delays the analyst from reaching exceptions.

4. **The exception table lacks operational legibility.**  
   Similar text weight across all columns, 24-character truncation, color-only status dots, and three unlabeled action icons make it hard to identify severity, ownership, deadline, and next action quickly.

5. **Surface treatment adds noise without meaning.**  
   Borders, 16px radius, and soft shadows on every region create excessive container emphasis, especially with nested cards, making the workspace feel heavier but not more precise.

## Secondary findings

1. **Generic insight copy is not decision-grade.**  
   Phrases like “Monitor performance closely” do not identify a product, cause, threshold, owner, or recommended action.

2. **Small, low-contrast body text weakens dense scanning.**  
   12–13px gray text may be too quiet for a high-density analyst tool where numbers, deadlines, and status labels must compete for attention.

3. **Spacing lacks a system.**  
   Gaps from 8px to 48px without a clear rhythm make sections feel assembled rather than intentionally prioritized.

4. **The bright blue “Create” button is likely over-emphasized.**  
   For an exceptions workspace, creation may be less urgent than filtering, assigning, escalating, exporting, or refreshing.

5. **Critical non-happy states are undefined.**  
   Empty, loading, error, keyboard-focus, narrow-laptop, and long-translation states are all absent from the description, which is risky for an operations surface.

## Concrete redesign moves with acceptance criteria

1. **Move to an exception-first information order.**  
   Place the exception queue directly under the page command bar, with summary metrics above or beside it only if they explain prioritization.  
   **Accept when:** the first viewport contains the command bar, priority filters, table header, and at least the first few exception rows on a standard laptop viewport.

2. **Collapse the four title/control rows into one precise command strip.**  
   Use one aligned row or compact two-row grid: title + subtitle on the left; date range, last refreshed state, refresh, and export on the right.  
   **Accept when:** all page-level controls share one baseline system and no control floats as a disconnected row.

3. **Replace eight equal KPI cards with a risk hierarchy.**  
   Elevate only metrics tied to immediate action, such as revenue risk, blocked SKUs, deadline breaches, and unresolved owner queues; demote page views and broader performance metrics.  
   **Accept when:** an analyst can identify the top operational risk metric within three seconds without reading all eight cards.

4. **Make status and deadline readable without color dependence.**  
   Replace dot-only statuses with compact labeled chips such as “Blocked,” “At risk,” “Due <1h,” or “Escalated,” preserving amber/red semantics.  
   **Accept when:** every row’s state is understandable in grayscale and the most urgent rows are visually distinct.

5. **Redesign the table as the main decision surface.**  
   Use stronger hierarchy for product, issue, deadline, and financial impact; use tabular figures; allow product names to wrap to two lines or reveal full names on expansion; keep owner and action scannable.  
   **Accept when:** product identity, issue type, dollar impact, deadline, and next action are all visible without guessing from icons.

6. **Replace icon-only actions with explicit operations actions.**  
   Use text buttons or icon+label actions such as “Assign,” “Escalate,” “Resolve,” “Open,” or “Snooze,” depending on the real workflow.  
   **Accept when:** no primary row action depends on an unlabeled icon.

7. **Remove decorative nesting and generic insight cards.**  
   Keep the chart only if it explains exception volume, financial exposure, or SLA breach trend; replace generic insights with actionable filters or queue summaries.  
   **Accept when:** every card either changes the table view, explains current exception priority, or supports a concrete workflow.

8. **Normalize density, type, and surfaces.**  
   Use fewer shadows, tighter inner radii than outer containers, consistent 4/8px spacing increments, body text closer to 14px where possible, and higher-contrast ink/gray values.  
   **Accept when:** borders and shadows identify structural hierarchy rather than appearing on every region equally.

## Bounded score

**Static evidence score band: 4–5 / 10.**  
The described screen has the right domain ingredients and preserves real workflows, but the static evidence shows the primary decision surface is buried, urgency is flattened, statuses/actions are under-specified, and operational states are missing.

## Smallest validation plan that could change the verdict

1. **Desktop first-viewport check:** verify at 1366×768 and 1280×720 whether the exception table, priority controls, and first actionable rows are visible without scrolling.  
2. **Narrow-laptop check:** verify the same flow around 1024–1180px wide, especially header compression, table column priority, and action visibility.  
3. **State check:** inspect loading, empty, error, stale-refresh, long product name, long owner name, and long translated label states.  
4. **Keyboard/focus check:** tab through search, filters, table rows, status controls, and row actions to confirm visible focus and non-icon-only action names.  
5. **Color-dependence check:** review statuses in grayscale or with color removed to confirm amber/red are supportive, not the only source of meaning.


## Output C

1. **Diagnosis — Static evidence only:** The screen is structurally credible but mis-prioritizes the analyst’s next-hour exception workflow by spending prime space on equal-weight navigation, KPIs, charts, and generic insight cards while pushing the actionable exception table below the fold.

2. **Blocking findings**

- **Action surface is below the fold.**  
  The primary job is to find exceptions needing action in the next hour, but the exception table starts below the fold after header rows, eight KPI cards, a chart card, and generic insight cards.

- **Hierarchy treats unequal business signals as equal.**  
  Revenue risk, blocked SKUs, sell-through, and yesterday’s page views receive the same KPI treatment, which obscures urgency and financial consequence.

- **Exception table lacks decision clarity.**  
  Product, issue, owner, deadline, financial impact, status, and action all use similar weight, making it hard to scan for “what is broken, how costly is it, who owns it, and what must happen next.”

- **Status and actions are under-specified.**  
  Small colored dots without text and three unlabeled action icons require interpretation, which is risky in an operations workspace where speed and confidence matter.

- **Layout fragmentation reduces trust and speed.**  
  Title, subtitle, date range, export, and refresh status occupy four weakly aligned rows, while every region uses borders, radius, and shadows, creating visual noise instead of operational precision.

3. **Secondary findings**

- **Header is too dominant for the task.**  
  Six equal nav links, global search, three icon buttons, and a bright blue Create button compete with exception triage; “Create” may not be a primary merchandising analyst action on this surface.

- **Generic insight cards dilute authority.**  
  Copy such as “Monitor performance closely” does not help decide the next action and feels less credible than surfaced exception evidence.

- **Text size and contrast appear fragile.**  
  12–13px low-contrast gray body text may undermine dense scanning, especially for deadlines, product names, and financial impact.

- **Product identification is weakened.**  
  Truncating long product names at 24 characters risks hiding distinguishing SKU or variant information needed for correct action.

- **Spacing and container treatment lack a system.**  
  Gaps ranging from 8px to 48px and universal bordered/shadowed cards reduce rhythm and make importance harder to infer.

4. **Concrete redesign moves with acceptance criteria**

- **Move exception triage into the first viewport.**  
  Acceptance: on a standard desktop workspace, the first visible content after the header includes the exception table header and at least the first several exception rows, without relying on chart scrolling.

- **Compress the page command area into one aligned control row.**  
  Acceptance: title, subtitle or scope, date range, export, and refresh status are grouped into a single predictable header band with clear left/right alignment and no more than two vertical rows.

- **Reduce KPIs to a priority strip focused on action.**  
  Acceptance: show only the metrics that change exception priority, such as revenue at risk, blocked SKUs, overdue deadlines, and unresolved critical issues; demote page views and non-urgent trend metrics to secondary context.

- **Replace equal KPI cards with ranked severity treatment.**  
  Acceptance: revenue risk and blocked/overdue exceptions receive stronger typographic emphasis than informational metrics, while preserving navy/ink neutrals and semantic amber/red for status.

- **Remove or demote the generic insight-card stack.**  
  Acceptance: no card contains generic advice; each insight must name a specific exception cluster, financial exposure, owner group, or deadline window, or be removed from the primary view.

- **Redesign the table for triage scanning.**  
  Acceptance: issue, deadline, financial impact, and status have stronger hierarchy than lower-priority metadata; rows support scanning by severity, deadline, and owner without opening details.

- **Make status and actions explicit.**  
  Acceptance: each status includes text plus semantic color, e.g. “Blocked,” “At risk,” “Due soon”; each action has a visible label or labeled button such as “Assign,” “Resolve,” “Escalate,” or “View.”

- **Establish a restrained density system.**  
  Acceptance: body text uses a legible minimum size and contrast for operational reading; spacing follows a small set of repeatable increments; borders/shadows are reserved for grouping, not applied uniformly to every region.

5. **Bounded score**

**Score band: 55–65 / 100 based on static evidence.**  
The surface has a plausible enterprise structure and preserves a restrained neutral/status palette, but it materially fails the stated job because the primary action table is delayed, hierarchy is flat, and critical labels/actions are ambiguous.

6. **Smallest validation plan that could change the verdict**

- **Desktop viewport check:** confirm whether the exception table is visible without scrolling on the target analyst viewport; if it is not, the blocking fold finding stands.  
- **Narrow-laptop check:** verify whether the header, KPI strip, and table remain usable without hiding critical columns or increasing truncation.  
- **State check:** review static designs for empty, loading, error, refresh-stale, and no-results states to confirm whether analysts can trust the surface during operational uncertainty.  
- **Interaction-label check:** verify that status dots and action icons have visible, persistent labels or equivalent explicit text in the designed surface.  
- **Long-content check:** test long product names, translated labels, high currency values, and multiple owners to see whether triage-critical information remains readable.
