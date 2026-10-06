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
