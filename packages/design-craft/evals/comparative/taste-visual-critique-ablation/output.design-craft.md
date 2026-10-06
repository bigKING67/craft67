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
