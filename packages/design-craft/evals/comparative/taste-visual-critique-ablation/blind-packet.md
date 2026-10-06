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

**Static-evidence diagnosis:** The screen is visually tidy but operationally misordered: it treats overview metrics, charts, generic insights, and exceptions as equal, while the product’s real job is to surface next-hour merchandising exceptions fast.  
**Evidence label:** Static product-surface description only; no runtime, browser, DOM, responsive, or state validation claimed.

## 2. Blocking findings

1. **Primary workflow is buried below the fold.**  
   The exception table is the action surface, but it appears after KPI cards, a chart card, and generic insights, delaying the “what needs action now?” decision.

2. **Attention hierarchy is flat where risk should dominate.**  
   Revenue risk, blocked SKUs, sell-through, and yesterday’s page views receive equal card weight, equal sparkline treatment, and similar typography, so urgent operational signals do not outrank diagnostics.

3. **The table does not support fast triage.**  
   Product, issue, owner, deadline, impact, status, and action use similar weight; status is color-dot-only; product names truncate too aggressively; actions are unlabeled icons.

4. **Command and context controls are fragmented.**  
   Title, subtitle, date range, export, and refresh status span four rows with weak alignment, while a bright “Create” button competes with the exception-response workflow.

5. **Core resilience and accessibility states are undefined.**  
   Empty, loading, error, keyboard focus, narrow-laptop, long product names, and translation expansion are not described, which is a blocker for a dense operations workspace.

## 3. Secondary findings

1. **Over-cardification weakens density.**  
   Border, radius, and shadow on every region create visual noise instead of a calm navy/ink operations surface.

2. **Nested cards make the chart area feel heavier than its decision value.**  
   A large pale card containing another chart card, followed by three more cards, overemphasizes analysis before action.

3. **Generic insight copy is not operational.**  
   “Monitor performance closely” does not name an entity, threshold, owner, impact, or next action.

4. **Spacing rhythm is inconsistent.**  
   Gaps ranging from 8px to 48px without clear grouping make the page feel assembled rather than composed.

5. **Text density is too timid for analyst use.**  
   12–13px low-contrast body text risks slowing scan speed and reducing credibility in a data-heavy workspace.

## 4. Concrete redesign moves with acceptance criteria

1. **Create a compact command band.**  
   Combine title, subtitle, date range, refresh status, and export into one aligned header band beneath the global nav.  
   **Acceptance:** Within the first page band, the analyst can see scope, time window, data freshness, and export without scanning four separate rows.

2. **Demote off-task global actions.**  
   Keep global search and nav, but reduce the visual dominance of the bright “Create” button unless creating is part of resolving exceptions.  
   **Acceptance:** The strongest action on the page supports reviewing or resolving exceptions, not starting an unrelated workflow.

3. **Move exceptions into the first viewport.**  
   Place a compact exception queue or the top rows of the table directly under the command band, ahead of broad trend content.  
   **Acceptance:** On a standard desktop workspace, the first viewport contains the highest-priority exceptions, their impact, deadline, status, and next action.

4. **Rebuild KPIs into priority tiers.**  
   Promote revenue risk, blocked SKUs, overdue/near-deadline exceptions, and financial impact; demote page views and other diagnostics into a secondary strip.  
   **Acceptance:** Critical metrics are visually distinct, include period/comparison/threshold context, and use amber/red only for semantic state.

5. **Make the table task-first.**  
   Reorder and restyle columns around decision flow: product identity, issue/status, financial impact, deadline, owner, next action.  
   **Acceptance:** Product names can wrap or expand; financial values are right-aligned; status includes text plus color; actions use labeled buttons or icon+label controls.

6. **Replace generic insights with evidence-backed exceptions.**  
   Remove generic advice cards unless each names the SKU/category, observed condition, business impact, owner or recommended action.  
   **Acceptance:** Every retained insight can answer: what changed, why it matters, who owns it, and what to do next.

7. **Flatten the surface system.**  
   Preserve the navy/ink neutral palette and semantic amber/red, but reduce nested cards, repeated shadows, and universal 16px radii. Use dividers, alignment, and spacing before elevation.  
   **Acceptance:** Primary regions feel grouped without every module looking equally raised; shadows appear only where elevation or focus is meaningful.

8. **Define operational states and hostile-content behavior.**  
   Specify loading, empty, error, stale data, disabled action, keyboard focus, long translation, long product name, and narrow-laptop layouts.  
   **Acceptance:** The table remains usable with long names, missing owners, many rows, narrow width, and failed refresh; all row actions remain keyboard reachable and visibly focused.

## 5. Static-only score band

**58–66 / 100, static evidence only.**  
Justification: the screen has a recognizable dashboard structure and preserves real data/workflows, but the primary exception workflow is below the fold, hierarchy is flat, table actions are under-specified, status relies on color alone, and key states/responsive behavior are not defined.

## 6. Smallest validation plan that could change the verdict

1. **Desktop first-viewport check:** verify at common analyst laptop sizes whether the exception queue/table is actually visible without scrolling.  
2. **Narrow-laptop check:** test the command band, KPI strip, chart, and table at reduced width for wrapping, clipping, and action visibility.  
3. **State pass:** exercise loading, empty, error, stale refresh, long product names, long translations, and high-row-count table data.  
4. **Keyboard pass:** tab through search, date range, export, refresh, table rows, status controls, and row actions; confirm visible focus and non-icon-only action names.  
5. **Decision-flow timing check:** ask whether an analyst can identify the top exception, owner, deadline, impact, and next action from the first viewport within a few seconds.


## Output B

## 1. Diagnosis

The screen is visually calm but operationally misprioritized: it presents a merchandising triage workspace as a generic analytics dashboard, delaying the exception queue that should drive next-hour action.  
**Evidence label:** Static description only.

---

## 2. Blocking findings

1. **Primary decision surface is below the fold.**  
   The exception table is the analyst’s main action queue, but the current layout spends the first viewport on header chrome, fragmented controls, equal KPI cards, charting, and generic insights.

2. **Urgency hierarchy is flattened.**  
   Revenue risk, blocked SKUs, sell-through, and yesterday’s page views receive equal card treatment, so the screen does not clearly distinguish “act now” signals from background context.

3. **Table rows are not optimized for fast exception triage.**  
   Product, issue, owner, deadline, financial impact, status, and action use similar weight, making it harder to scan for severity, accountability, and next step.

4. **Status and actions are under-specified.**  
   Small colored dots without text and three unlabeled action icons require interpretation, which is risky in an operations workflow where analysts need confidence under time pressure.

5. **Header and page controls consume too much vertical and cognitive space.**  
   Six equal nav links, global search, three icon buttons, a bright “Create” button, and four separate page-title/control rows dilute the work area before the analyst reaches exceptions.

---

## 3. Secondary findings

1. **Nested card structure adds visual noise without added meaning.**  
   A pale card containing another chart card plus three more insight cards creates hierarchy by decoration rather than by operational relevance.

2. **Generic insight copy weakens credibility.**  
   Statements like “Monitor performance closely” do not help a merchandising analyst decide what to do in the next hour.

3. **Typography is too small and low contrast for dense decision-making.**  
   12–13px gray body text may work for metadata, but not for issue descriptions, deadlines, financial impact, or action labels.

4. **Spacing lacks a system.**  
   Gaps ranging from 8px to 48px without a clear rhythm make regions feel assembled rather than intentionally sequenced.

5. **Surface styling is over-applied.**  
   Every region having border, 16px radius, and soft shadow makes all containers compete equally and reduces the contrast between primary and secondary areas.

---

## 4. Concrete redesign moves with acceptance criteria

1. **Reframe the first viewport around “exceptions needing action.”**  
   Move the exception table or a priority exception queue above the chart.  
   **Acceptance criteria:** At a standard desktop workspace size, the analyst can see the page title, critical filters, summary risk indicators, and at least the first several exception rows without scrolling.

2. **Collapse the four page-control rows into one command bar.**  
   Combine title, subtitle, date range, export, refresh status, and last-updated metadata into a single aligned header block beneath the global nav.  
   **Acceptance criteria:** Page-level controls occupy one horizontal band, with primary filters left-aligned and secondary actions grouped to the right.

3. **Reduce KPI cards from eight equal tiles to a prioritized triage strip.**  
   Promote only action-driving metrics: revenue at risk, blocked SKUs, expiring deadlines, and owner coverage. Demote page views and passive analytics into secondary context.  
   **Acceptance criteria:** Urgent operational metrics use stronger type, semantic amber/red indicators, and explicit labels; passive metrics are visually quieter.

4. **Replace equal blue sparklines with meaningful status encoding.**  
   Use sparklines only where trend changes the decision; otherwise use deltas, thresholds, or breach counts. Preserve navy/ink neutrals and amber/red semantics.  
   **Acceptance criteria:** A red or amber visual state always maps to a specific operational condition, not decorative emphasis.

5. **Redesign the exception table for scan order.**  
   Establish visual hierarchy: product and issue as the row anchor, deadline and impact as urgency signals, owner as accountability, status as text badge, action as explicit command.  
   **Acceptance criteria:** A reader can identify “what is wrong,” “how costly,” “who owns it,” and “what to do next” from each row without relying on icon interpretation alone.

6. **Stop truncating product names at 24 characters.**  
   Allow two-line product names, preserve meaningful identifiers, and use tooltip or expandable detail only as a backup.  
   **Acceptance criteria:** Long product names remain distinguishable in-row, especially when similar SKUs share prefixes.

7. **Replace unlabeled icon actions with labeled primary actions.**  
   Use concise verbs such as “Assign,” “Snooze,” “Resolve,” “Open,” or “Escalate,” depending on the real workflow. Keep icons optional and secondary.  
   **Acceptance criteria:** The main action in each row is readable as text; destructive or irreversible actions are visually distinct and not hidden behind identical icon buttons.

8. **Simplify surfaces and spacing into a denser operations rhythm.**  
   Remove unnecessary nested cards, reduce shadows, vary radii by hierarchy, and use a consistent 4/8px spacing scale.  
   **Acceptance criteria:** Primary work areas rely on alignment, contrast, and typography rather than every region receiving the same bordered card treatment.

---

## 5. Score band

**Static evidence score band: 45–55 / 100.**  
Justification: the screen appears coherent and restrained enough to avoid a full failure, but it misses the product’s core decision flow by burying the exception table, flattening urgency, and using ambiguous status/action treatments.

---

## 6. Smallest validation plan that could change the verdict

1. **First-viewport check:** Verify at desktop and narrow-laptop widths whether critical exceptions are visible without scrolling.  
2. **Triage task check:** Ask a merchandising analyst to identify the top three exceptions to act on in under one minute.  
3. **Table comprehension check:** Confirm that status, deadline, owner, financial impact, and row action are understandable without hover or icon guessing.  
4. **State check:** Review loading, empty, error, long product name, long translation, and no-results states for the table and KPI area.  
5. **Keyboard/focus check:** Confirm that search, filters, table rows, and row actions have visible focus order and readable labels.


## Output C

## 1. Diagnosis — evidence label

**Diagnosis:** The screen over-prioritizes generic dashboard furniture and equal-weight metrics, pushing the urgent exception queue below the fold and making next-hour action harder to identify.  
**Evidence label:** Static product-surface description only.

---

## 2. Blocking findings

1. **Primary workflow is buried.**  
   The exception table starts below the fold even though the product’s main job is to surface action-needed exceptions within the next hour.

2. **Urgency hierarchy is weak.**  
   Revenue risk, blocked SKUs, sell-through, and page views receive equal KPI treatment, so operational risk is not visually separated from background monitoring.

3. **Table does not support fast triage.**  
   Product, issue, owner, deadline, financial impact, status, and action use similar weight, making it difficult to scan for “what is broken, how costly, who owns it, and what to do next.”

4. **Actions and statuses are ambiguous.**  
   Status dots without text and unlabeled action icons require interpretation, increasing decision friction in a time-sensitive operations surface.

5. **Layout consumes attention with redundant framing.**  
   Nested cards, repeated borders, radius, and shadows create visual noise while the most actionable data is delayed and under-emphasized.

---

## 3. Secondary findings

1. **Header is too evenly distributed.**  
   Six equal navigation links plus search, icons, and a bright Create button compete with the workspace task rather than receding behind exception handling.

2. **Page controls lack a command bar.**  
   Title, subtitle, date range, export, and refresh status across four rows create weak alignment and unnecessary vertical cost.

3. **KPI card language is too generic.**  
   Gray helper copy and identical sparklines do not distinguish “needs action now” from “observe later.”

4. **Text density is present but not precise.**  
   12–13px low-contrast body text may fit more content but undermines scan reliability for owners, deadlines, and financial impact.

5. **State design is incomplete.**  
   Empty, loading, error, focus, narrow-laptop, and long-translation states are unspecified, which is risky for an operations tool used under time pressure.

---

## 4. Concrete redesign moves with acceptance criteria

1. **Move the exception table into the first viewport.**  
   Acceptance: On the default desktop canvas, the table header and at least the first 5–8 exception rows are visible without scrolling.

2. **Replace the eight equal KPI cards with a prioritized risk strip.**  
   Acceptance: Top row contains no more than 4 primary operational signals: revenue at risk, blocked SKUs, overdue/next-hour deadlines, and owner coverage; secondary metrics such as page views move below or into a compact details panel.

3. **Create a single aligned page command bar.**  
   Acceptance: Title, date range, refresh timestamp, export, and any primary page action sit on one coherent horizontal grid with one dominant page title and no more than two rows total.

4. **Make the table the decision engine.**  
   Acceptance: Columns are visually weighted in this order: issue severity, product, deadline, financial impact, owner, status, action; deadline and financial impact have stronger typographic emphasis than neutral metadata.

5. **Replace dot-only statuses with labeled semantic badges.**  
   Acceptance: Every status includes text plus color, using existing amber/red semantics for warning and critical states; status remains understandable without relying on color alone.

6. **Convert icon-only actions into explicit task actions.**  
   Acceptance: Each row has one primary text action such as “Assign,” “Resolve,” “Escalate,” or “Review,” with secondary actions behind a labeled overflow control.

7. **Reduce decorative containers and normalize spacing.**  
   Acceptance: Remove nested card-within-card structures; use borders or shadows sparingly, not both everywhere; section spacing follows a small set of repeated steps such as 8, 16, 24, and 32px.

8. **Preserve long product and localization readability.**  
   Acceptance: Product names support at least two-line wrapping or an expandable cell; truncation does not hide the distinguishing SKU/product detail needed for triage.

---

## 5. Bounded score

**Score band: 4–5 / 10 based on static evidence.**  
Justification: The screen appears credible and structured, but the primary operational task is below the fold, urgency is flattened, table affordances are ambiguous, and key states are unspecified. It is not a ground-up failure, but it does not yet behave like a next-hour exception workspace.

---

## 6. Smallest validation plan that could change the verdict

1. **Default desktop viewport check:** Confirm whether exception rows are visible without scrolling and whether the command area consumes excessive vertical space.  
2. **Narrow-laptop check:** Test whether the table keeps product, issue, deadline, impact, status, and action usable without hiding critical triage fields.  
3. **State pass:** Review empty, loading, error, and stale-refresh states for the exception table and KPI strip.  
4. **Keyboard pass:** Confirm visible focus order through search, filters, table rows, status controls, and row actions.  
5. **Long-content pass:** Test long product names, long owner names, translated labels, and high financial-impact values in the table.
