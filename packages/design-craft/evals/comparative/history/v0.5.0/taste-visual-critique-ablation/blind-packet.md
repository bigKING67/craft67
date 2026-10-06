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

1. **Diagnosis — Evidence label: static description only, unvalidated:** The surface sounds visually tidy but operationally misprioritized: it buries the next-hour exception work beneath equal-weight dashboard furniture, weak state semantics, and table affordances that slow analyst triage.

## Blocking findings

1. **The primary job is below the fold.**  
   The exception table is the real work object, but the first screen is consumed by header chrome, fragmented page metadata, eight equal KPI cards, a chart card, and generic insight cards.

2. **Risk hierarchy is flattened.**  
   Revenue risk, blocked SKUs, sell-through, and yesterday’s page views receive equal card treatment and equal blue sparklines, so urgent exception signals do not outrank diagnostic or vanity metrics.

3. **The table does not support fast triage.**  
   Product, issue, owner, deadline, financial impact, status, and action use similar weight; status is color-only dots; product names truncate too early; row actions are unlabeled icons.

4. **Decorative containers overpower decision structure.**  
   A pale card containing another chart card plus nested insight cards creates visual nesting without operational value, while borders/radius/shadows on every region make everything feel equally important.

5. **Production states are underspecified for an operations tool.**  
   Missing empty, loading, error, keyboard-focus, narrow-laptop, and long-translation states leaves the design unproven for repeated analyst use, recovery, and accessibility.

## Secondary findings

1. **Header competition is too high.**  
   Six equal nav links, global search, three icon buttons, logo, and a bright blue “Create” button make the top bar feel like a generic app shell rather than a focused merchandising workspace.

2. **Page command area lacks alignment discipline.**  
   Title, subtitle, date range, export, and refresh status across four weakly aligned rows waste vertical space and obscure scope.

3. **Typography is too timid for dense operations.**  
   12–13px low-contrast gray body text and 12px uppercase KPI labels reduce scan confidence, especially for deadlines, issue types, and financial impact.

4. **Spacing rhythm is inconsistent.**  
   Gaps from 8px to 48px without a clear scale make relationships ambiguous: related controls may feel detached while unrelated cards feel grouped.

5. **The chart and “insights” lack a decision contract.**  
   Generic copy like “Monitor performance closely” does not name the entity, threshold, owner, business impact, or next action.

## Concrete redesign moves with acceptance criteria

1. **Compress the page command band into one aligned operations header.**  
   Keep title, subtitle/scope, date range, export, and refresh status in one compact grid or two-line band; demote “Create” unless creating is part of exception resolution.  
   **Acceptance:** At 1440px wide, the analyst can read page scope, data freshness, and active date range without scanning four separate rows.

2. **Move the exception work object above the fold.**  
   Replace the current dashboard-first order with: command band → lead exception/risk summary → exception queue/table → supporting diagnostics.  
   **Acceptance:** On a standard desktop viewport, at least the table header and first actionable exception rows are visible without scrolling.

3. **Turn the eight KPI cards into a priority hierarchy.**  
   Promote next-hour revenue risk, blocked SKUs, overdue deadlines, and highest financial impact; demote page views and other diagnostics into a compact secondary strip.  
   **Acceptance:** The most urgent operational risk is visually dominant, and every prominent metric includes comparison, threshold, or “why this matters now.”

4. **Remove or rewrite generic insight cards.**  
   Keep an insight only if it names a product/category/segment, observed change, threshold breach, financial or workflow impact, and recommended owner/action.  
   **Acceptance:** No insight can be replaced with “Monitor performance closely” without losing product-specific meaning.

5. **Redesign the table as a triage queue, not a schema dump.**  
   Prioritize columns as identity → issue/severity → deadline → financial impact → owner → status → action; use stronger type for product and issue, tabular/right-aligned financial values, and clear deadline urgency.  
   **Acceptance:** A user can scan the top five rows and identify which exception to act on first without opening details.

6. **Make status and actions explicit.**  
   Replace color-only dots with labeled status chips using navy/ink neutrals plus semantic amber/red; replace three unlabeled icons with one visible verb-object action and a labeled overflow for secondary actions.  
   **Acceptance:** Status remains understandable without color, and each row action is understandable from text, tooltip, and keyboard focus label.

7. **Reduce surface noise while preserving the existing neutral system.**  
   Use flat table and panel surfaces with subtle dividers; reserve shadows/elevation for overlays or active layers; standardize radius and border use.  
   **Acceptance:** Containers clarify grouping without making every module look like an equally important card.

8. **Define hard states for real operations data.**  
   Specify loading skeletons, empty results, partial/error states, stale refresh, long product names, long translations, disabled actions, and keyboard focus-visible treatment.  
   **Acceptance:** The same layout remains usable with long names, no exceptions, failed refresh, and keyboard-only navigation.

## Score band

**45–55 / 100 based on static evidence.**  
The screen has credible raw ingredients—real data, dense table workflow, restrained navy/ink plus semantic status colors—but the described hierarchy, table affordances, over-cardification, low contrast, and missing states materially undermine the primary job of finding next-hour exceptions.

## Smallest validation plan that could change the verdict

1. **Viewport check:** Evaluate only 1440×900 and narrow-laptop 1280×720 layouts for whether exception rows appear before scrolling and whether the command band wraps cleanly.  
2. **Keyboard path:** Tab through header, search/date/export/refresh, table rows, status/action controls; confirm visible focus and discoverable action names.  
3. **State fixtures:** Review loading, empty exceptions, refresh error, stale data, long product names, long translations, and disabled row actions.  
4. **Contrast/readability spot check:** Verify body text, helper text, status chips, deadline urgency, and financial impact against the calm navy/ink system.  
5. **Decision-speed test:** With representative data, ask whether the top exception, owner, deadline, impact, and next action are identifiable within three seconds.


## Output B

## 1. Diagnosis

The surface currently reads like a generic analytics dashboard instead of a next-hour exception triage workspace, because the strongest visual weight is spent on navigation, equalized KPIs, nested cards, and a delayed table rather than on urgent merchandise exceptions.  
**Evidence label:** Static description only; no browser, DOM, responsive, runtime, or accessibility-tree validation.

---

## 2. Blocking findings

1. **Primary workflow is below the fold.**  
   The exception table is the core decision surface, but it starts below the fold after KPI cards, chart containers, and generic insight cards. This delays the analyst’s main job: finding what needs action in the next hour.

2. **Urgency hierarchy is flattened.**  
   Revenue risk, blocked SKUs, sell-through, and page views receive equal card treatment. For this product, financial risk, blocked inventory, expiring deadlines, and operational ownership should visually outrank informational metrics.

3. **The table does not support fast triage.**  
   Product, issue, owner, deadline, financial impact, status, and action all use similar weight, so the analyst must read every cell instead of scanning for severity, deadline, and impact.

4. **Status and actions are under-specified.**  
   Small colored dots without text and three unlabeled action icons create ambiguity. In an operations workspace, status and next action need to be explicit, especially for keyboard-heavy repeated use.

5. **Information density is high but precision is low.**  
   Low-contrast 12–13px body text, aggressive truncation at 24 characters, inconsistent gaps, and repeated borders/shadows make the screen busy without making decisions faster.

---

## 3. Secondary findings

1. **The 64px header is overloaded.**  
   Six equal nav links, search, three icon buttons, logo, and a bright Create button compete with the workspace content. “Create” may be visually too dominant if exception handling is the primary task.

2. **Page metadata is fragmented.**  
   Title, subtitle, date range, export, and refresh status across four rows weakens alignment and consumes vertical space before the real work begins.

3. **Cards are overused as a default container.**  
   Every region having border, radius, and shadow reduces contrast between primary and secondary surfaces and creates unnecessary visual noise.

4. **The chart area appears insufficiently purposeful.**  
   A large pale card containing another chart card, followed by generic “insights,” does not sound tied to exception resolution or prioritization.

5. **Missing state descriptions create risk.**  
   Empty, loading, error, keyboard-focus, narrow-laptop, and long-translation states are not defined, so the design cannot yet be trusted for production operations use.

---

## 4. Concrete redesign moves with acceptance criteria

1. **Move the exception table into the first viewport.**  
   Acceptance criteria: at 1366×768, the analyst can see the page header, compact priority summary, table header, and at least 3–5 exception rows without scrolling.

2. **Replace eight equal KPI cards with a priority strip.**  
   Acceptance criteria: top summary shows only decision-critical metrics first, such as `Critical exceptions`, `Revenue at risk`, `Blocked SKUs`, and `Due within 1 hour`; secondary metrics like page views are demoted or moved below the table.

3. **Consolidate page title, date range, export, and refresh into one command row.**  
   Acceptance criteria: title and subtitle align left; date range, refresh timestamp, export, and any filter controls align right or in a single predictable toolbar; no more than two rows before the priority content begins.

4. **Redesign the table around triage order.**  
   Acceptance criteria: row scan order makes severity, product, issue, deadline, impact, owner, status, and action immediately clear; financial impact and deadline receive stronger weight than owner or generic metadata.

5. **Replace color-only status dots with labeled status badges.**  
   Acceptance criteria: every status includes text plus semantic color, for example `Blocked`, `At risk`, `Due soon`, `Assigned`, `Resolved`; amber and red remain reserved for operational severity, not decoration.

6. **Replace unlabeled icon actions with explicit primary actions.**  
   Acceptance criteria: the main action per row is a text button or icon+label such as `Review`, `Assign`, `Resolve`, or `Open`; secondary actions can sit in an overflow menu with accessible names and visible focus.

7. **Reduce nested card chrome and establish a spacing/type rhythm.**  
   Acceptance criteria: primary table container is visually strongest; secondary modules use lighter dividers instead of repeated shadows; body text is at least 14px where practical; spacing follows a consistent 8px-based rhythm.

8. **Make long operational content survivable.**  
   Acceptance criteria: product names support two-line wrapping or an expanded detail affordance; issue text remains meaningful under truncation; long translations do not break row height unpredictably or hide the decision-critical fields.

---

## 5. Bounded score

**Score band: 45–55 / 100 based on static evidence.**  
The screen has recognizable enterprise-dashboard structure and likely contains useful data, but the described hierarchy conflicts with the product’s stated job. The largest penalty is that exception handling—the primary workflow—is visually and spatially secondary.

---

## 6. Smallest validation plan that could change the verdict

1. **First-viewport check:** verify at 1366×768 and 1440×900 whether urgent exception rows are visible without scrolling.  
2. **Keyboard path check:** tab through header, filters, table rows, status, and actions; confirm visible focus and no unlabeled controls.  
3. **State check:** review static variants for loading, empty, error, stale refresh, bulk selection, and no-critical-exceptions states.  
4. **Long-content check:** test long product names, long issue labels, long owner names, and translated labels.  
5. **Contrast/readability check:** confirm 12–13px gray text, badges, links, and disabled states meet readable contrast for dense operational use.  
6. **Triage timing check:** ask whether an analyst can identify top three next-hour exceptions, owner, deadline, financial impact, and next action in under 30 seconds.


## Output C

## 1. Diagnosis

**Diagnosis [static description only]:** The surface uses the right sober palette, but its hierarchy is inverted: generic navigation, equal KPI cards, nested chart chrome, and vague insights consume the decision area while the exception table—the analyst’s next-hour action queue—starts below the fold.

## 2. Blocking findings

1. **Primary workflow is buried.**  
   The exception table is below the fold, so the screen delays the core job: finding urgent merchandising exceptions.

2. **All signals have equal visual priority.**  
   Revenue risk, blocked SKUs, sell-through, and yesterday’s page views receive the same card treatment, number scale, and sparkline emphasis, flattening operational urgency.

3. **Page command area lacks alignment and compression.**  
   Title, subtitle, date range, export, and refresh status spread across four rows, creating friction before the analyst reaches actionable data.

4. **Exception rows are not decision-ready.**  
   Product, issue, owner, deadline, financial impact, status, and action use similar weight; status relies on dots without text; product names truncate too early; actions are unlabeled icons.

5. **Visual chrome competes with data density.**  
   Borders, 16px radii, soft shadows, nested cards, and inconsistent gaps make the workspace feel heavier and less precise than the product authority requires.

## 3. Secondary findings

1. **Header has too many equal destinations.**  
   Six equal nav links plus search, icon buttons, and a bright “Create” button dilute the workspace context.

2. **The blue “Create” button likely overstates its importance.**  
   For this surface, triage and exception resolution appear more important than creation.

3. **Generic insight copy undermines credibility.**  
   “Monitor performance closely” does not name a product, risk, owner, threshold, or recommended action.

4. **Low-contrast 12–13px body text is risky for dense operations use.**  
   Analysts need sustained readability, especially for deadlines, impact, and issue descriptions.

5. **Critical states are unspecified.**  
   Empty, loading, error, keyboard focus, narrow-laptop, and long-translation cases are absent, so the design is not yet production-complete.

## 4. Concrete redesign moves with acceptance criteria

1. **Move the exception queue into the first viewport.**  
   Acceptance: at a standard laptop height, analysts can see the page context, primary filters, and the first actionable exception rows without scrolling.

2. **Replace eight equal KPI cards with a prioritized exception summary strip.**  
   Acceptance: revenue risk, blocked SKUs, nearing-deadline exceptions, and unresolved high-impact issues receive primary emphasis; page views and secondary metrics are visually demoted or moved into supporting context.

3. **Compress the title/actions area into a single operational command bar.**  
   Acceptance: title, exception count, date range, refresh age, export, and filter controls align on one row or one compact two-row grid with clear left-to-right priority.

4. **Rebuild the table hierarchy around triage decisions.**  
   Acceptance: issue type, deadline, financial impact, and status are visually stronger than owner and secondary metadata; numbers use tabular alignment; deadlines and impact can be scanned down the column.

5. **Replace dot-only statuses with labeled semantic badges.**  
   Acceptance: every status has text plus color; amber/red remain reserved for operational risk; the status remains understandable without relying on color alone.

6. **Make product names recoverable instead of prematurely hidden.**  
   Acceptance: long product names support two-line wrapping or show SKU/category as secondary metadata; truncation does not remove the distinguishing part of the item name.

7. **Convert icon-only actions into explicit row actions.**  
   Acceptance: the primary row action is labeled, secondary actions have accessible visible or adjacent labels where space allows, and destructive/escalation actions are visually distinct.

8. **Reduce card nesting and normalize spacing.**  
   Acceptance: one dominant page surface, minimal nested borders, restrained shadows, a consistent 8px spacing rhythm, and tighter radii for inner controls than outer containers.

## 5. Bounded score

**Static product-fit score: 4–5 / 10.**  
Justification: the palette direction and dense workspace intent are compatible with the brief, but the described hierarchy, table treatment, generic insight layer, and missing states directly obstruct the “find exceptions needing action in the next hour” workflow.

## 6. Smallest validation plan that could change the verdict

1. **First-viewport check:** at common desktop and narrow-laptop sizes, confirm whether the analyst can see urgent exceptions without scrolling.  
2. **State matrix:** review loading, empty, error, stale-refresh, long product names, long translations, and dense-result states.  
3. **Keyboard pass:** verify visible focus order through search, filters, table rows, and row actions.  
4. **Table comprehension test:** using real data, ask whether status, deadline, impact, and next action are identifiable within a few seconds per row.  
5. **Responsive density check:** ensure the layout does not collapse into excessive wrapping or hide critical columns on narrow laptops.
