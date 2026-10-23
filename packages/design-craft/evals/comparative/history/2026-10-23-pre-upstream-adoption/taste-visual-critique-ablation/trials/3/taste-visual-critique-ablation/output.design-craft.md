## 1. Diagnosis

This should be a calm, precise workspace for merchandising analysts, but its hierarchy favors overview metrics and decorative containers over identifying, assessing, and acting on exceptions due in the next hour.

**Evidence: static description plus supplied product authority only.** No rendered surface or behavior was inspected; undescribed states are unknown, not proven absent.

## 2. Findings

“Blocking” means blocking design approval for the stated job—not a demonstrated runtime failure. Repair and acceptance criteria follow by finding ID.

### Blocking findings

| ID | Finding and supplied evidence | Decision-flow consequence | Still unknown |
|---|---|---|---|
| B1 | **Actionable work is buried.** Eight KPIs, a chart, and nested insights precede a table described as below the fold. | Analysts must pass overview content before finding urgent exceptions. | Actual viewport geometry and time to reach the first actionable row. |
| B2 | **Priority is visually flattened.** Revenue risk and blocked SKUs receive the same card height, 28px numbers, and blue sparklines as yesterday’s page views. | Operational urgency is indistinguishable from background performance. | Whether metrics share scope, freshness, or actionable drill-downs. |
| B3 | **Rows require too much interpretation.** Similar text weights, dot-only status, 24-character product truncation, and three unlabeled action icons obscure identity and next steps. | Analysts risk choosing the wrong product or action and cannot readily distinguish urgency from ownership metadata. | Accessible names, full-name disclosure, action semantics, and existing sort behavior. |
| B4 | **Decision text is hard to read.** Body copy is described as 12–13px and low-contrast gray. | Repeated scanning of deadlines, issues, and financial impact becomes unnecessarily demanding. | Actual contrast ratios, font metrics, zoom behavior, and reading performance. |

### Secondary findings

| ID | Finding and supplied evidence | Consequence | Still unknown |
|---|---|---|---|
| S1 | **Context and controls lack a common hierarchy.** Four loosely aligned page-context rows sit beneath a crowded 64px header with six equal links and a bright Create button. | Scope, freshness, navigation, and creation compete with triage. | Whether Create is frequently needed in exception resolution; header fit at narrower widths. |
| S2 | **Diagnostics consume space without a clear decision payoff.** A doubly contained area chart precedes generic advice such as “Monitor performance closely.” | Space is spent without identifying affected products or a useful next action. | What operational question the chart answers. |
| S3 | **Container styling overwhelms grouping.** Gaps vary from 8px to 48px; every region has a border, 16px radius, and shadow. | Everything appears equally separate and important, weakening the requested dense, credible tone. | Exact spacing relationships and whether any elevation represents a real layer. |
| S4 | **Resilience is unspecified.** Empty, loading, error, focus, narrow-laptop, and long-translation states are not described. | Safe recovery and continued access to the decision flow cannot be approved. | All listed state behavior; this is an evidence gap rather than a confirmed defect. |

## 3. Concrete redesign moves and acceptance criteria

1. **Consolidate the command and context area — S1.**  
   Keep the existing navigation and workflows; use a title/context row and one aligned control row for date range, export, and freshness. Give the current navigation destination a clear indicator. Retain Create but reduce its visual prominence unless its role in triage warrants emphasis.  
   **Accept when:** title, controls, summary, and table share alignment axes; scope and last successful refresh are readable together; all six destinations, search, and header actions remain reachable.

2. **Replace eight equal cards with a compact, prioritized summary — B2.**  
   Lead with revenue risk and blocked SKUs; demote sell-through and page views to supporting context without deleting their data. Replace uppercase label styling with readable sentence-case labels. Keep a sparkline only when its trend informs an operational decision, using ink rather than equal blue emphasis.  
   **Accept when:** urgent metrics are visibly stronger than historical metrics; each lead value states its period and scope; thresholds or comparisons use existing data, not invented benchmarks.

3. **Make the exception table the primary workspace — B1.**  
   Place it immediately after the compact summary, before diagnostics. Put existing filters beside it; offer a clearly scoped next-hour view using established deadline rules, including overdue items, with a visible route back to all exceptions. Preserve user-selected sorting and filters.  
   **Accept when:** at provisional desktop targets of 1440×900 and 1280×720 CSS pixels, the table header and at least three real rows are visible without page scrolling; the time window, timezone, and ordering are explicit.

4. **Give each row a readable decision sequence — B3.**  
   Emphasize product and issue, make deadline and financial impact easy to compare, and keep owner secondary but readable. Add text to status dots using the existing status vocabulary. Replace fixed 24-character truncation with available-width wrapping plus keyboard-accessible full-name disclosure. Show a labeled existing primary action and a labeled menu for remaining actions.  
   **Accept when:** full product identity is obtainable without hover; status remains understandable without color; every existing action remains available and named; currency is right-aligned with tabular numerals; deadlines include unambiguous time context.

5. **Make diagnostics earn their space — S2.**  
   Move the area chart below the queue and remove its nested shell, retaining its real data and workflows. Title it with the operational question it actually answers. Remove generic advice; retain an insight only if supported by an affected entity or segment, an observed count or threshold, urgency or impact, and a direct path to the relevant records.  
   **Accept when:** no “monitor closely” filler remains; retained diagnostics identify evidence and a useful next step without implying unsupported causation.

6. **Apply one restrained density and readability system — B4, S3.**  
   Preserve navy/ink neutrals and semantic amber/red. Use a provisional **14px / 1.4 line-height floor** for decision-bearing table text; reserve 12–13px for secondary metadata. Use 8px related-item gaps, 16px group spacing, and 24px section spacing. Flatten content sections; use subtle row dividers, a single boundary where necessary, and shadows only for overlays. Replace blanket 16px radii with a consistent compact radius, provisionally 4–8px.  
   **Accept when:** normal text reaches at least 4.5:1 contrast; key issue/deadline text outranks helper copy; spacing follows named roles; no ordinary section combines repeated nested borders, rounded shells, and shadows. No gradients, glass, or illustration are introduced.

7. **Specify honest loading and recovery states — S4.**  
   Distinguish “no exceptions” from “no matches”; provide filter reset for the latter. During refresh, retain the last successful data with an explicit stale/updating label. On failure, show local retry and the last successful timestamp; initial loading must not resemble zero risk.  
   **Accept when:** each state communicates whether data is current, stale, unavailable, or genuinely empty; retries preserve scope and filters; failures never silently remove unresolved exceptions.

8. **Protect the same workflow on narrow laptops and by keyboard — S4, B3.**  
   Let context controls wrap deliberately; compress secondary summary content before sacrificing the queue. Permit horizontal scrolling within the table rather than the entire page, preserving access to every column and action. Define visible focus, labeled icon controls, keyboard-operable menus, and focus return.  
   **Accept when:** at 1280×720, 200% zoom, and with doubled-length labels, no controls overlap or become unreachable; keyboard users can filter, inspect full identity, and invoke the correct action; focused controls are not obscured.

## 4. Verdict and scoring boundary

**Verdict: redesign required before approving this as a next-hour exception workspace.** B1–B4 are supported directly by the description.

**No numeric score:** the evidence supports specific hierarchy and readability judgments, but not a defensible aggregate assessment of rendered quality, accessibility, or operational reliability.

## 5. Smallest validation plan that could change the verdict

This is a proposed plan, not completed validation.

1. **Inspect the current baseline first** in the supported desktop browser at 1440×900 and 1280×720, using representative real records. Check the fold, header fit, computed decision-text size and contrast, spacing, and the existing path from urgent exception to action.
2. **Run one short analyst task:** identify the highest-priority exception requiring action within the next hour, explain its deadline and financial impact, and choose the existing next action. Record wrong selections, ambiguity, and unnecessary scrolling; repeat keyboard-only.
3. **Exercise a compact state set:** initial loading, refresh failure with stale data, no exceptions, no filter matches, and a long product name with doubled-length interface labels. Test the populated view at 200% zoom; inspect focus and accessible names for the row actions and status.
4. **Reassess only the affected findings.** Clear B1–B4 only when their acceptance criteria and the analyst task pass; clear S4 only with state evidence. If the baseline contradicts the supplied description, revise the corresponding finding rather than assuming the redesign is necessary.
