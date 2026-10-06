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

1. **Diagnosis — Evidence label: static-description-only.**  
   The surface is visually polished but operationally misprioritized: it spends first-screen attention on equalized navigation, KPI cards, nested chart cards, and generic insights while delaying the exception table that directly supports the “next hour” decision flow.

2. **Blocking findings**

1. **Primary workflow is below the fold.**  
   For merchandising analysts, the exception table is the action surface, but the described hierarchy pushes it after header clutter, fragmented title rows, eight KPIs, a chart, and insight cards.

2. **All metrics are treated as equally urgent.**  
   Revenue risk, blocked SKUs, sell-through, and page views share identical card weight, size, sparkline treatment, and spacing, so the screen does not distinguish action-critical exceptions from background telemetry.

3. **The table lacks triage hierarchy.**  
   Product, issue, owner, deadline, impact, status, and action use similar weight, making it hard to scan by urgency, ownership, financial exposure, or next required action.

4. **Status and action affordances are under-specified.**  
   Small colored dots without text and three unlabeled action icons create ambiguity in a dense operations context where speed and confidence matter.

5. **Readability is below the likely threshold for sustained desktop work.**  
   12–13px low-contrast gray body text, 24-character product truncation, and inconsistent spacing undermine calm, precise scanning across real merchandising data.

3. **Secondary findings**

1. **The header over-allocates attention.**  
   Six equal nav links, search, three icon buttons, and a bright blue Create button compete with the hour-level exception workflow.

2. **The page command area is fragmented.**  
   Title, subtitle, date range, export, and refresh status occupying four separate rows weakens alignment and delays comprehension.

3. **Nested card structure adds noise without meaning.**  
   A pale card containing another chart card, followed by three more cards, increases visual effort while the “insights” copy is generic and low-value.

4. **Surface treatment is overused.**  
   Borders, 16px radii, and soft shadows on every region flatten hierarchy because every container asks for attention.

5. **Production states are missing from the specification.**  
   Empty, loading, error, keyboard-focus, narrow-laptop, and long-translation states are not described, so the design cannot yet be judged production-complete.

4. **Concrete redesign moves with acceptance criteria**

1. **Create a single command row under the header.**  
   Merge title, subtitle, date range, export, and refresh into one aligned toolbar: left side = page identity and scope; right side = date range, refresh state, export.  
   **Acceptance:** the analyst can identify page purpose, data freshness, and active time window within one horizontal scan.

2. **Reduce header dominance.**  
   Keep the navy/ink system, but make global navigation quieter: active section emphasized, inactive links lower contrast, Create button demoted unless creation is part of this screen’s primary job.  
   **Acceptance:** the brightest or strongest control on the page relates to exception review, not generic creation.

3. **Move exception triage into the first viewport.**  
   Place a compact “needs action now” table or queue directly after the command row, before the large trend chart.  
   **Acceptance:** on a common desktop laptop height, at least the table header and first several exception rows are visible without scrolling.

4. **Reframe KPIs as a priority strip, not eight equal cards.**  
   Promote only action-driving metrics such as revenue risk, blocked SKUs, overdue deadlines, and exceptions by owner; demote page views and passive trend metrics into secondary context.  
   **Acceptance:** the top metric area has no more than 3–4 primary tiles, with clear severity ordering and no identical blue sparkline treatment across unrelated measures.

5. **Replace generic insight cards with exception summaries.**  
   Remove vague text like “Monitor performance closely” and replace with specific, sourced operational prompts: “17 SKUs blocked by missing image,” “$42.8k at risk by 3pm deadline,” “Maya owns 9 overdue items.”  
   **Acceptance:** every summary names a count, owner/category, deadline, or financial impact and links to the corresponding filtered table state.

6. **Redesign the table for action scanning.**  
   Use stronger hierarchy: product name with secondary SKU/category line, issue as the primary problem label, deadline with relative urgency, financial impact in tabular figures, owner visible, status as labeled text badge, and a single explicit primary action.  
   **Acceptance:** a row can be understood without relying on color alone, icon guessing, or opening a detail view.

7. **Fix long-content handling.**  
   Allow product names to wrap to two lines or expose full names on expansion; avoid hard 24-character truncation for the primary identifier.  
   **Acceptance:** long product names, translated issue labels, and owner names remain distinguishable without hiding the action or status columns.

8. **Simplify the surface system.**  
   Reserve borders/radius/shadow for major structural containers only; use spacing, alignment, and type weight for internal grouping.  
   **Acceptance:** not every region appears as an equal card; the table and urgent exception areas carry more visual weight than decorative containers.

5. **Bounded score**

**Static score band: 4/10–5/10.**  
The screen appears coherent enough to be usable and preserves a neutral operations palette, but the static evidence shows a serious mismatch between visual hierarchy and the stated job: exceptions needing action in the next hour are delayed, underweighted, and harder to scan than secondary dashboard content.

6. **Smallest validation plan that could change the verdict**

1. Check first viewport at 1366×768 and 1280×800: whether exception rows are visible without scrolling.  
2. Validate table states with representative data: long product names, high financial impact, overdue deadline, multiple owners, and translated labels.  
3. Keyboard-pass the described workflow: search/filter, move through rows, identify status, trigger row action, export, refresh.  
4. Review non-happy states: loading, empty, stale refresh, failed refresh/export, and partial table error.  
5. Check status/action comprehension without color or icons alone: labels must remain understandable in text.  
6. Confirm density and contrast under sustained-use conditions: 14px+ operational text where possible, clear focus states, and readable gray values on the navy/ink neutral system.


## Output B

## 1. Diagnosis

**Evidence: L1 contextual static — product authority plus supplied surface description only.** The screen is a credible operations dashboard visually, but it is organized like a generic metric overview instead of an exception-finding workspace for the next hour.

## 2. Blocking findings

1. **Primary job is buried below the fold.** The exception table is the core work object, but header rows, equal KPI cards, chart cards, and generic insights appear before the rows that need action.
2. **Operational priority is flattened.** Revenue risk, blocked SKUs, sell-through, and yesterday’s page views receive equal card weight and equal blue sparklines, so urgent exceptions do not separate from background telemetry.
3. **The table does not support fast triage.** Product, issue, owner, deadline, financial impact, status, and action all have similar weight; status is color-dot-only; product names truncate too early; row actions are unlabeled icons.
4. **Surface treatment creates noise instead of structure.** Nested cards, repeated borders, 16px radii, and soft shadows on every region make the screen feel over-cardified and reduce density.
5. **Production states are underdefined.** Empty, loading, error, keyboard focus, narrow-laptop, and long-translation states are not described, which is a blocker for a repeated-use operations workspace.

## 3. Secondary findings

1. **Header competes with the work.** Six equal nav links, search, three icon buttons, and a bright blue “Create” button create more first-screen competition than the primary exception flow needs.
2. **Page metadata is fragmented.** Title, subtitle, date range, export, and refresh status spread across four rows, weakening alignment and slowing orientation.
3. **Generic insight copy undermines trust.** “Monitor performance closely” does not name an affected product, threshold, impact, owner, or next action.
4. **Typography is too timid for decision data.** 12–13px low-contrast body text may be acceptable for metadata, but not for table cells that drive financial and deadline decisions.
5. **Spacing lacks a rule.** 8px–48px gaps without a clear hierarchy make related controls feel detached and unrelated regions feel equally important.

## 4. Concrete redesign moves with acceptance criteria

1. **Create a compact command band.**  
   Combine page title, scope/date range, export, and refresh status into one aligned header band below global nav.  
   **Accept when:** workspace name, date scope, refresh age, and export are visible in one scan line or two tightly aligned rows; “Create” no longer visually dominates exception triage.

2. **Move exceptions into the first viewport.**  
   Reorder the page to lead with “Exceptions needing action in the next hour,” followed by the table or a compact queue preview before historical charts.  
   **Accept when:** at a typical desktop height, the first screen exposes the exception count, top-priority rows, deadline/impact, and action path without scrolling past chart/insight cards.

3. **Replace the eight equal KPI cards with a priority hierarchy.**  
   Use one lead risk module for revenue risk / blocked SKUs, a compact support strip for sell-through and other diagnostics, and demote page views unless tied to an exception.  
   **Accept when:** urgent amber/red states are visually stronger than routine metrics; every emphasized KPI includes period, comparison, or threshold; blue sparklines are not used decoratively for all metrics.

4. **Rebuild the table around triage order.**  
   Put product identity, issue/status, deadline, financial impact, owner, and primary action in the scan path; group secondary metadata later.  
   **Accept when:** decision-bearing table text is at least 14px with readable line-height; numeric impact is right-aligned; status has text plus semantic color; long product names preserve recognition through wider cells, two-line wrapping, or an accessible full-name reveal.

5. **Make row actions explicit.**  
   Replace three unlabeled icons with labeled or icon+label actions such as “Assign,” “Resolve,” “Open,” or a single “Review exception” primary action with secondary actions in a menu.  
   **Accept when:** each action has visible text or an accessible name, keyboard focus, disabled/loading behavior, and a clear result after activation.

6. **Turn generic insights into operational evidence or remove them.**  
   Keep an insight only if it names the product/segment, observed threshold, financial or deadline impact, owner, and direct route into the affected rows.  
   **Accept when:** no card says only “monitor” or “review closely”; each retained insight can filter, sort, or navigate to the relevant exception set.

7. **Simplify the surface system.**  
   Use the navy/ink neutral system with flatter sections, subtle dividers, and restrained elevation; reserve shadows for overlays or selected/active surfaces.  
   **Accept when:** repeated cards do not all use border + 16px radius + shadow; section gaps follow a clear rhythm such as 12px within groups, 24px between groups, 32px between major regions; normal text meets accessible contrast.

8. **Define resilient state variants.**  
   Add designed states for loading, empty, error, stale refresh, keyboard focus, narrow laptop, long translations, and long product names.  
   **Accept when:** each state preserves the user’s place, explains what happened, offers a next action, keeps focus visible, and does not rely on color alone.

## 5. Static score band

**58–66 / 100, L1 contextual static.** The screen has a recognizable operations-dashboard structure and preserves real data/workflows, but the supplied evidence shows weak task priority, buried exceptions, over-cardification, color-only status, low-contrast dense text, and missing production states.

## 6. Smallest validation plan that could change the verdict

1. Capture the real page at desktop and narrow-laptop widths to verify whether exception rows are actually below the fold and whether critical actions remain reachable.
2. Inspect loading, empty, error, stale-refresh, and long-product-name fixtures to see whether missing states are truly absent or only omitted from the description.
3. Keyboard through global nav, filters, table rows, status, and actions to confirm focus order, visible focus, and action names.
4. Check computed contrast and accessible names for body text, status indicators, and icon actions.
5. Test representative real data with long names, translated labels, high financial values, and many exceptions to confirm table scanability and overflow behavior.


## Output C

## 1. Diagnosis

The screen currently reads like a generic analytics dashboard rather than an exception-finding workspace: the most urgent action surface is pushed below the fold, while low-priority navigation, equalized KPIs, decorative chart framing, and weak table semantics compete for attention.  
**Evidence label:** Static description only; no browser, DOM, responsive, accessibility-tree, or runtime validation performed.

---

## 2. Blocking findings

1. **Primary job is structurally buried.**  
   The exception table—the surface most aligned with “find the exceptions that need action in the next hour”—starts below the fold, while header chrome, fragmented page metadata, KPI cards, and chart cards consume the first view.

2. **Urgency hierarchy is flat where it needs to be opinionated.**  
   Revenue risk, blocked SKUs, sell-through, and yesterday’s page views receive equal card treatment, making critical operational risk visually equivalent to background telemetry.

3. **The table does not support fast triage.**  
   Product, issue, owner, deadline, financial impact, status, and action use similar weight; status is reduced to unlabeled dots; actions are unlabeled icons; long names truncate too aggressively. This weakens scan speed and confidence.

4. **Card nesting and repeated chrome reduce density without adding meaning.**  
   A pale container, nested chart card, three nested insight cards, borders, radii, and shadows on every region create visual noise in a workspace that should feel dense, calm, and precise.

5. **Critical production states are undefined.**  
   Empty, loading, error, keyboard-focus, narrow-laptop, and long-translation states are not described, so the surface cannot yet be judged robust for real operations usage.

---

## 3. Secondary findings

1. **The 64px header appears over-weighted for the task.**  
   Six equal navigation links, global search, three icon buttons, logo, and a bright blue Create button compete before the analyst reaches exceptions.

2. **Page-level controls lack a clear command structure.**  
   Title, subtitle, date range, export, and refresh status occupying four separate rows creates weak alignment and delays comprehension.

3. **Typography is too small and low-contrast for repeated operational scanning.**  
   12–13px low-contrast body text may be tiring in dense tables and increases the chance of missing deadline, owner, or impact details.

4. **Spacing rhythm is inconsistent.**  
   Gaps ranging from 8px to 48px without a clear system make the page feel assembled from independent blocks rather than one decision flow.

5. **Generic insight copy erodes credibility.**  
   Phrases like “Monitor performance closely” do not help analysts decide what to do next, by when, or with what business impact.

---

## 4. Concrete redesign moves with acceptance criteria

1. **Move the exception queue into the first viewport.**  
   - Acceptance: At a 1440×900 desktop viewport, the page title, key command row, top exception summary, and first 5–8 exception rows are visible without scrolling.  
   - Acceptance: The first viewport answers: “What is broken, how much is at risk, who owns it, and what should happen next?”

2. **Collapse page metadata into one aligned command bar.**  
   - Combine title, subtitle, date range, export, and refresh status into a single structured header below the global nav.  
   - Acceptance: Page title aligns left; date range, refresh timestamp, and export sit on the same horizontal command line or one predictable second line on narrower laptops.  
   - Acceptance: Refresh status uses quiet text unless stale, failed, or actively loading.

3. **Re-rank KPIs by operational urgency.**  
   - Promote only the metrics that affect next-hour action: revenue risk, blocked SKUs, overdue exceptions, and deadline breaches.  
   - Demote supporting metrics like yesterday’s page views into a secondary strip or table-adjacent context.  
   - Acceptance: Critical KPIs use semantic amber/red emphasis only when thresholds are crossed; non-critical KPIs remain neutral ink/navy.  
   - Acceptance: Sparklines are removed unless they explain a decision trend; no equal blue sparklines across unrelated metrics.

4. **Replace generic insight cards with exception drivers.**  
   - Remove “Monitor performance closely” style copy.  
   - Use specific operational statements such as “12 blocked SKUs have deadlines within 60 minutes” or “Top vendor delay accounts for $42k at risk.”  
   - Acceptance: Every insight names a count, impact, owner/source, or action path.  
   - Acceptance: No insight card is present if it cannot change prioritization.

5. **Flatten the visual container system.**  
   - Reserve borders, radius, and shadow for true grouping or elevated interaction surfaces.  
   - Acceptance: Main regions use quiet separation through spacing, headings, and hairline dividers; nested card-within-card patterns are removed.  
   - Acceptance: Radius and shadow are not repeated on every region; the screen retains the existing navy/ink neutral palette.

6. **Redesign the exception table for triage hierarchy.**  
   - Make product and issue the primary scan pair; financial impact and deadline the secondary urgency pair; owner and status supporting; action explicit.  
   - Acceptance: Status is shown as text badge plus color, not dot-only: for example, “Blocked,” “At risk,” “Due soon,” “Resolved.”  
   - Acceptance: Action column uses labeled actions or icon+label buttons, such as “Assign,” “Escalate,” “Resolve,” not three unlabeled icons.  
   - Acceptance: Long product names preserve enough identifying information through two-line wrapping, middle truncation, or an expandable detail—not fixed 24-character truncation only.

7. **Increase readability while preserving density.**  
   - Use at least 14px for dense body/table text where possible, with stronger contrast for operational fields.  
   - Acceptance: Deadlines, financial impact, blocked status, and owner are distinguishable by weight, placement, or badge treatment without relying only on color.  
   - Acceptance: Section spacing follows a predictable rhythm, such as 8/16/24/32px, with no arbitrary 48px gaps unless separating major page zones.

8. **Define production states before visual sign-off.**  
   - Acceptance: Table has specified loading skeleton, empty state, partial-data warning, failed-refresh error, stale-data state, keyboard-focus state, narrow-laptop layout, and long-translation behavior.  
   - Acceptance: Each state preserves the analyst’s ability to understand whether there are actionable exceptions and whether the data is trustworthy.

---

## 5. Bounded score

**Static product-surface score: 4/10–5/10.**

Justification: the palette direction and dense operations intent can be preserved, but the static description shows a major mismatch between task priority and layout order, weak urgency hierarchy, inaccessible status/action encoding, and missing production states. The score could rise if the actual implementation already solves keyboard focus, responsive behavior, and table states, but those are not evidenced here.

---

## 6. Smallest validation plan that could change the verdict

1. **First-viewport check:**  
   Test 1440×900 and 1280×720/768 desktop-laptop sizes. Confirm whether actionable exception rows appear without scrolling.

2. **Triage scan check:**  
   With realistic data, ask whether an analyst can identify the top three next-hour exceptions, owner, deadline, and financial impact within 10–15 seconds.

3. **State check:**  
   Review loading, empty, failed-refresh, stale-data, long-product-name, and long-translation states for the KPI area and exception table.

4. **Keyboard check:**  
   Verify visible focus order through search, date range, export, refresh, table rows, status controls, and row actions.

5. **Narrow-laptop check:**  
   Confirm that header controls, command bar, KPIs, and table remain usable without hiding urgency, truncating critical fields, or forcing excessive horizontal scanning.
