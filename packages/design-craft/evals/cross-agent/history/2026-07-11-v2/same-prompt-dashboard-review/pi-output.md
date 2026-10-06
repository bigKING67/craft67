Now I have all the references needed. Here is the design-craft critique:

---

# Design-Craft Critique: Revenue Operations Dashboard

**Mode**: `critique` (read-only)
**Reference routing**: `surface-playbooks.md` (dashboard), `product-ui-taste-review.md`, `taste-score-calibration.md`, `design-move-library.md`, `foundational-visual-principles.md`, `validation-contract.md`

---

## 1. Evidence Level and Score Band

**Evidence level: L0 static** — prose description only. No screenshot, DOM, computed style, responsive run, focus walk, hover state, loading state, error state, or real-content behavior was verified. The prompt itself confirms this: *"No screenshot, DOM, responsive run, focus walk, hover state, loading state, or error state was verified."*

### Product UI Taste Score: 35 / 100

**Band**: Rough / unfinished (0–59)

**Why this score:**

| Dimension | Score | Reasoning |
|---|---|---|
| Design intent & taste direction | 4 / 10 | Stated intent ("restrained enterprise, dense but calm, token-backed") is strong and appropriate. But the described layout — 12 equal KPI cards + decorative chart + generic tips — reads as a generic SaaS template, directly contradicting the intent. |
| Task focus & attention control | 2 / 10 | The primary job is identifying which account or campaign needs attention in the next hour. Twelve equal-weight cards with no risk prioritization, no exception queue, and a decorative chart make this impossible to triage within seconds. |
| Information order & structure | 3 / 10 | Summary → detail → action flow is inverted. Flat KPI grid dominates prime real estate, the decorative chart doesn't answer a named analytical question, the decision-critical table is buried, and generic tips are disconnected from data. |
| Proximity & grouping | 4 / 10 | Twelve equal cards collapse all metric groups into one undifferentiated mass. Right-rail tips are physically separated from the data they should explain. Filters (if any exist) are likely detached from the table. |
| Alignment & grid discipline | 5 / 10 | The 12-card grid is likely geometrically aligned. The problem is semantic, not geometric. Generous extrapolation from the description. |
| Repetition & system coherence | 4 / 10 | Consistent card anatomy exists but encodes zero priority semantics. A -35% revenue anomaly card looks identical to a flat "total sessions" card. The system is coherent in shape but broken in meaning. |
| Contrast & hierarchy | 2 / 10 | **Primary failure.** Zero visual distinction between blocker, warning, neutral, and positive states across all 12 KPIs. The entire header zone is one flat visual weight. The decorative chart and generic tips dilute remaining contrast. |
| Typography, color, surface quality | 6 / 15 | Token-backed color is a redeeming signal — suggests an existing design system. The dense table may use disciplined data typography. But the "decorative" area chart and "generic tips" signal weak surface judgment. |
| Interaction polish & microcopy | 3 / 10 | Not described. "Generic tips" implies boilerplate copy with no contextual recovery language. No evidence of row actions, tooltips, loading, error, or empty states. |
| Responsive & frontend craft | 2 / 5 | Not described. A dense table + right rail structure is at high risk of horizontal overflow and broken stacking on narrow viewports. No token-audit or component-reuse evidence. |

**Anti-inflation check**: Score is capped below 84 due to flat hierarchy and card soup (per calibration rules). Score is capped below 88 due to L0 static evidence. Score is capped below 92 because interaction states are entirely unverified.

---

## 2. Design Read

**Reading this as**: revenue operations dashboard for an ecommerce operator, with a restrained enterprise console feel, **optimized for triaging which account or campaign needs attention in the next hour**, but the described layout optimizes for overview-at-a-glance rather than urgent operational decision-making — a category mismatch between the stated job and the visual structure.

The stated style authority ("restrained enterprise console, dense but calm, no marketing hero treatment, token-backed color only") is an excellent fit for the product register. The problem is not the intended aesthetic — it's that the described layout is the opposite of what this surface needs.

---

## 3. Top Hierarchy / Product-Fit Issues

### P0 — Flat KPI hierarchy blocks the primary job

The dashboard's core purpose is operator triage: *which account or campaign needs attention in the next hour?* Twelve equal KPI cards cannot answer that question within three seconds. Every metric — whether it's on fire or flat — gets the same size, color, and surface weight. An operator must decode all twelve values and mentally rank them. This is the single highest-cost failure.

**Design-craft principle**: *If everything is emphasized, nothing is important.* (foundational-visual-principles: Attention)

### P0 — No exception queue or risk surface exists

The operator needs to see: what's broken right now, what's trending toward broken, and what needs a decision before the hour ends. The described layout has no exception queue, no anomaly surface, no watched-account list, no alert panel. The account table is the closest thing to a decision surface, but it's buried below the decorative chart and lacks priority sorting in the described structure.

### P1 — The area chart is described as "decorative"

A chart that exists for visual fill rather than answering a named analytical question is a direct violation of data-viz grammar (surface-playbooks: "Pick the chart from the analytical question, not decoration"). It consumes prime real estate between the KPI header and the table, displacing what should be the operator's primary decision surface.

**Design-craft principle**: *Economy — remove visual decisions that do not clarify task, structure, state, or brand.*

### P1 — Right-rail tips are generic and disconnected

"Generic tips" in a right rail is an anti-pattern in two ways:
- **Proximity violation**: tips live far from the data they're meant to contextualize.
- **Microcopy weakness**: generic tips don't tell the operator what to do with the specific numbers on this dashboard at this moment.

### P2 — Table is "dense" without task-first column order

The account table is the likely decision surface (scan accounts, identify issues, take action), but "dense" without further description suggests columns may follow database schema order rather than operator task order: identity → status → risk → impact → next action.

---

## 4. Concrete Design Moves

Using design-craft vocabulary and the **dashboard card soup → decision surface** move from `design-move-library.md`.

### Move 1: Promote a lead risk object above the fold

**Current**: 12 equal KPI cards across the top.

**Recommended**: Replace with a **lead risk object** — a single, visually dominant module that surfaces the highest-priority operational state. This could be:
- The single worst-performing account or campaign by revenue deviation
- An aggregate "attention score" with drill-down
- The number of accounts currently below threshold

Below the lead object, convert the remaining KPIs into a **compact supporting metric strip** (3 rows × 4 columns at most, or a single-row band with inline deltas). This respects the need for density while establishing clear hierarchy.

**Treatment variant**: *Ops command center* — blocker-first hierarchy, high-contrast exceptions, short labels, strong state semantics.

### Move 2: Replace the decorative chart with an exception queue

**Current**: A decorative area chart sits between KPIs and the table.

**Recommended**: Replace with an **exception queue or anomaly panel** — a scannable list of accounts/campaigns that are outside threshold, ranked by deviation severity. Each row shows: entity name, metric-at-risk, deviation delta, time window, and a single next-action affordance.

If a trend chart is genuinely needed for diagnostics, tuck it below the exception queue or make it a secondary panel that the operator expands on demand. It should answer a named question (e.g., "Is the revenue dip accelerating or recovering?"), not exist for decoration.

### Move 3: Restructure the table for task-first scanning

**Current**: "Dense account table."

**Recommended**: Reorder columns for the operator's decision flow:
- **Column 1**: Account/campaign identity (primary scan key)
- **Column 2**: Status — a semantic indicator (on-track / warning / critical / paused) using token-backed status color, not decoration
- **Column 3**: Risk metric — the number that drives attention, right-aligned
- **Column 4**: Impact — revenue, budget, or opportunity cost, right-aligned
- **Column 5**: Next action — inline button or link (investigate, adjust, escalate)

Group secondary metadata (contact, region, channel, created date) into a collapsible detail row or later columns. Right-align all numeric columns. Add explicit empty/loading/error states near the table, not at page bottom.

### Move 4: Replace the right rail with contextual inline help

**Current**: Right rail with generic tips.

**Recommended**: Eliminate the right rail entirely. Move contextual guidance inline:
- Tooltip or hover text on at-risk metrics explaining the threshold and recommended action
- A compact "what to do next" text block directly below the exception queue (not in a detached side rail)
- Recovery language that references the specific data on screen, not generic best practices

This recovers horizontal space for the table (critical for a dense ops surface) and fixes the proximity problem.

### Move 5: Establish status semantics and monotone surfaces

The style authority says "token-backed color only." Enforce this:
- **Status tokens only**: green for on-track, amber for approaching threshold, red for below threshold, neutral for informational. No decorative color on cards, borders, or backgrounds.
- **Surface treatment**: flat or minimally raised surfaces with subtle dividers, not heavy card shadows. The "restrained enterprise console" feel comes from quiet surfaces and semantic color, not elevation.
- **Typography**: use the project's token scale. Metrics should be data-font (tabular figures) at a larger size, with comparison context (delta, period, threshold) at caption size directly below. No decorative type treatments.

### Layout target

```
┌──────────────────────────────────────────────────────┐
│  Lead Risk Object (dominant, 1 module)               │
│  "3 accounts below 15% margin threshold this hour"   │
├──────────────────────────────────────────────────────┤
│  Supporting Metric Strip (compact, 1-row band)       │
│  [Revenue ▼3%] [Margin 22%] [ACoS ▲5%] [ROAS 3.2x]  │
├──────────────────────────────────────────────────────┤
│  Exception Queue (scannable list, ranked by severity)│
│  ● Account A  -18% rev  |  Investigate               │
│  ● Campaign X +42% ACoS |  Adjust bids                │
│  ○ Account C  -7% margin|  Monitor                    │
├──────────────────────────────────────────────────────┤
│  Account Table (task-first columns, full width)       │
│  Identity | Status | Risk | Impact | Next Action      │
├──────────────────────────────────────────────────────┤
│  Diagnostic Chart (collapsed, "Show trend" toggle)   │
└──────────────────────────────────────────────────────┘
```

---

## 5. Verified Versus Unverified Claims

| Claim | Status | Evidence |
|---|---|---|
| "Restrained enterprise console, dense but calm" | **Unverified** — stated intent, but described layout contradicts it | Prompt text only |
| "Token-backed color only" | **Unverified** — claimed but no token file, CSS variable audit, or computed-style evidence | Prompt text only |
| "12 equal KPI cards at the top" | **Verified** — this is the structural description being critiqued | Prompt text |
| "One decorative area chart" | **Verified** — confirms this is decoration, not analytical tool | Prompt text |
| "Dense account table" | **Partially verified** — the word "dense" is given, but column order, alignment, sorting, filtering, and state behavior are all unverified | Prompt text |
| "Right rail with generic tips" | **Verified** — confirms the proximity and microcopy anti-pattern | Prompt text |
| Hover states exist and are polished | **Unverified** | Not described |
| Focus-visible states exist | **Unverified** | Not described |
| Loading, empty, error states exist | **Unverified** | Not described |
| Responsive behavior on narrow viewports | **Unverified** | Not described |
| Table supports sorting, filtering, row actions | **Unverified** | Not described |
| Color contrast meets accessibility minimums | **Unverified** | No token or computed-style evidence |
| KPI cards show deltas, time ranges, or thresholds | **Unverified** | Not described |
| Chart has labeled axes, legend, tooltips, or handles empty data | **Unverified** | Not described |

**Summary**: Of the 17 review dimensions in the taste rubric, only structural layout (proximity of top-level sections) and stated intent can be judged from L0 evidence. All interaction states, responsive behavior, typography specifics, color values, accessibility, and microcopy are entirely unverified.

---

## 6. Minimal Validation Plan Before Implementation

Per `validation-contract.md`, the minimal command ladder for a dashboard redesign would be type-check + lint + build + browser smoke. But the prompt says *"do not edit files."* The validation plan below describes what must be verified before any implementation work begins — it is a pre-implementation audit plan, not a post-build QA checklist.

### Phase 1: Static evidence (before any code change)

1. **Capture an L2 baseline**: Take a viewport screenshot of the current dashboard at a standard desktop resolution (1440×900). This moves evidence from L0 to L2 and enables before/after comparison. Use `browser_screenshot_ops target:"viewport"` if TMWD is available.

2. **Token audit**: Run `design_craft_token_audit.py` (or manual review) against the project's CSS variables / Tailwind config / design-token file. Confirm:
   - Semantic status tokens exist (critical, warning, neutral, positive, info)
   - Surface tokens exist (base, raised, overlay) and are not over-decorated
   - Typography scale includes a data/metric role with tabular figures
   - Spacing scale is defined (4/8/12/16/24/32px minimum)
   - No hard-coded colors outside the token system

3. **Table column audit**: Inspect the actual table column order. Document whether it follows database schema order or task-first order. Check numeric alignment (are numbers right-aligned?).

4. **Component inventory**: Catalog how many distinct KPI card variants exist. If there is exactly one variant, confirm the system has no mechanism to express risk priority.

### Phase 2: Interaction and state discovery (before redesign)

5. **Responsive check**: Resize the viewport to 375px and 768px widths. Document:
   - Does the right rail collapse, stack below, or overflow?
   - Does the 12-card grid reflow or produce horizontal scroll?
   - Does the table have horizontal overflow or responsive column hiding?
   - Are touch targets ≥ 44 CSS px?

6. **State audit**: Manually inspect or use `design_craft_focus_audit.py`:
   - Loading states for KPI cards, chart, and table
   - Empty states (no accounts, no campaigns, zero data)
   - Error states (API failure, permission denied)
   - Focus-visible on table rows, filter controls, and any action buttons
   - Hover states on interactive elements

7. **Chart question audit**: For the area chart, ask: "What analytical question does this chart answer?" If the answer is "it looks nice" or no one can name the question, it's confirmed decorative.

### Phase 3: Product-context validation

8. **Operator interview** (one session, 20 minutes): Show the current dashboard to one actual operator and ask:
   - "In the first 5 seconds, what do you look at?"
   - "How do you decide which account to investigate next?"
   - "What numbers do you wish were more visible?"
   - This confirms or refutes the hypothesis that the flat KPI grid fails the triage job.

### Phase 4: Implementation gates (post-redesign)

9. **Before/after evidence (L4)**: Capture viewport screenshots before and after the redesign. Run type-check, lint, and build. Document the diff.

10. **Acceptance checklist** (from `product-ui-taste-review.md`):
    - [ ] Operator can identify the top risk within 3 seconds of loading
    - [ ] Operational blockers appear before low-risk overview metrics
    - [ ] No decorative elements remain that don't serve a named analytical question
    - [ ] Status semantics use token-backed color, not decoration
    - [ ] Table columns follow task-first order (identity → status → risk → impact → action)
    - [ ] Right rail is eliminated; contextual guidance is inline
    - [ ] Empty, loading, and error states exist for all data-dependent modules
    - [ ] Dashboard works at 375px without horizontal overflow
    - [ ] All interactive elements have visible focus-visible states

---

## Summary

This dashboard concept suffers from a category mismatch between the stated product job (operator triage within the hour) and the visual structure (flat overview dashboard). The layout matches the canonical "bad dashboard" anti-pattern from the design-move-library almost exactly: 12 equal KPI cards + decorative chart + table + generic tips. The primary redesign direction is to convert the surface from an overview dashboard into a decision surface with a lead risk object, exception queue, task-first table, and eliminated decorative elements — all within the existing "restrained enterprise console, token-backed color only" style authority, which is a strong and appropriate visual constraint.

**Score**: 35 / 100 (L0 static)
**Primary diagnosis**: Flat hierarchy makes operator triage impossible within the decision window.
**Recovery path**: Lead risk object → compact metric strip → exception queue → task-first table → contextual inline help.
