## 1. Diagnosis

This should be a calm, precise workspace for merchandising analysts to find next-hour exceptions, but its equal-weight summaries and decorative containers prioritize general monitoring over identifying and acting on urgent rows.

**Evidence: static description plus product context only.** No rendered interface or behavior was inspected; “blocking” below means blocking design acceptance for the stated job, not proven runtime failure.

## 2. Findings

### Blocking findings

| ID | Finding and supplied evidence | Decision-flow consequence | Unverified boundary |
|---|---|---|---|
| B1 | **Actionable work is buried.** Four introductory rows, eight KPIs, a nested chart, and three insight cards precede a table described as below the fold. | Analysts encounter reporting before the exceptions they must resolve. | Actual fold position at supported desktop sizes. |
| B2 | **Priority is visually flattened.** Revenue risk, blocked SKUs, sell-through, and yesterday’s page views share identical cards, number sizes, and blue sparklines. | Yesterday’s activity competes with imminent business exposure; the display does not explain what matters now. | Existing metric definitions, filtering, and urgency ordering. |
| B3 | **Rows obscure identity, urgency, and action.** Similar text weights, color-only status dots, 24-character product truncation, and three unlabeled action icons. | Analysts must decode status, distinguish products, and infer actions before acting—an avoidable risk in time-sensitive work. | Accessible names, full-name disclosure, keyboard access, and actual action behavior. |
| B4 | **Decision-bearing text is underpowered.** Body text is described as 12–13px and low-contrast gray. | Dense information becomes harder to scan precisely; financial impact and deadlines need stronger legibility than metadata. | Measured contrast and rendered type metrics; no conformance failure is established. |

### Secondary findings

| ID | Finding and supplied evidence | Consequence | Unverified boundary |
|---|---|---|---|
| S1 | **The shell competes with the task.** A 64px header holds six equal navigation links, search, three icon buttons, and bright “Create”; page controls have weak alignment across four rows. | Global creation receives more emphasis than exception triage, while local scope and freshness are disconnected. | Whether creation is actually frequent in the exception workflow. |
| S2 | **Containers substitute for information structure.** Card-inside-card chart, generic advice, 8–48px gaps, and universal borders, 16px radii, and shadows. | Visual density increases without increasing useful operational information. | Whether the chart answers a specific exception-investigation question. |
| S3 | **Resilience is unspecified.** Empty, loading, error, focus, narrow-laptop, and long-translation states are not described. | Operational readiness cannot be accepted from the supplied specification. | These states may exist; omission is not evidence of implementation absence. |

## 3. Concrete redesign moves and acceptance criteria

Retain the navy/ink neutrals, semantic amber/red, real table data, and existing workflow destinations. No gradients, glass, illustration, or rebrand.

1. **Put the exception queue first — B1.**  
   Order the page: compact title/scope controls → compact operational summary → exception table → supporting analysis.  
   **Accept when:** at proposed test sizes of 1440×900 and 1280×720, the initial view shows table headers and at least three complete exception rows; no chart or insight card intervenes.

2. **Rank summaries by next-hour relevance — B2.**  
   Give revenue risk and blocked SKUs precedence; subordinate sell-through and yesterday’s page views without deleting their data. Remove equally prominent sparklines unless their trends inform a decision.  
   **Accept when:** each emphasized metric identifies its scope and time window; where filtering is supported, it opens the corresponding existing rows. Do not relabel aggregate risk as “next-hour risk” without supporting data.

3. **Make each row answer “which, why, by when, how much, who, what next?” — B3.**  
   Strengthen product identity and issue; make deadlines scannable, financial impact right-aligned with tabular numerals, and owner secondary but readable. Add text to statuses using existing terminology. Replace icon-only actions with one named existing primary action and a labeled menu for remaining actions.  
   **Accept when:** status is understandable without color; similar product names remain distinguishable; full names are available by keyboard, not only hover; every existing action remains reachable with an explicit name.

4. **Restore decision-text legibility — B4.**  
   Use a provisional 14px/1.4 floor for table content and essential controls; reserve 12–13px for nonessential metadata. Use ink for decision-bearing text rather than muted gray.  
   **Accept when:** normal text meets 4.5:1 contrast, essential control boundaries and focus indicators meet applicable 3:1 requirements, and urgency remains distinguishable without making every cell bold.

5. **Compress and align the shell — S1, B1.**  
   Keep navigation and search available; give the current section a clear active state. Consolidate title/subtitle and date/export/refresh into two aligned rows. Reduce “Create” to secondary emphasis unless its role in urgent exception handling is established.  
   **Accept when:** title, summaries, and table share a left edge; scope and refresh timestamp are visible together; search, navigation, export, and creation retain their current destinations.

6. **Flatten supporting analysis and remove empty advice — S2.**  
   Use one chart surface below the queue, without a nested card. Remove “Monitor performance closely”; replace it only with data-backed entity/segment, observed exception, impact or urgency, and a direct path to affected rows.  
   **Accept when:** every retained insight identifies actionable evidence; the chart answers a named investigation question. Use existing spacing tokens or provisionally 8px within groups, 16px between related controls, and 24px between sections; reserve shadows for overlays, use table dividers, and eliminate repeated 16px rounded wrappers.

7. **Specify operational states and laptop behavior — S3.**  
   Distinguish “no exceptions” from “no filter matches”; provide reset filters, stable loading structure, retryable errors, and an explicit last-successful-refresh indicator when showing stale data. Define visible keyboard focus and text expansion.  
   **Accept when:** loading is never presented as zero exceptions; errors never imply fresh data; keyboard users can complete existing row actions with visible focus; at 1280×720 and with 40% expanded labels, controls remain usable and table overflow stays local rather than hiding columns or creating page-wide overflow.

## 4. Score

**No numerical score assigned.** The description supports a clear verdict—**revise before design acceptance for next-hour triage**—but not a defensible aggregate score for rendering, accessibility, or interaction quality. The strongest evidence concerns information order and hierarchy.

## 5. Smallest validation plan that could change the verdict

*Proposed only; none of these checks has been performed.*

1. **Inspect the current baseline first:** one supported desktop browser at 1440×900 and 1280×720, using representative real data. Check fold position, computed type/contrast, spacing, and the path from urgent exception to existing action.
2. **Run one short analyst task:** identify the highest-priority next-hour exception, explain its deadline and impact, identify its owner, and start the appropriate action. Record hesitation, wrong-row selection, and icon interpretation.
3. **Run a compact resilience pass:** keyboard-only traversal; long near-identical product names; expanded translations; loading; no data; no filter matches; refresh failure with stale data.

If the current surface already exposes urgent rows, supports accurate prioritization, and provides clear named actions, downgrade the relevant blockers. If it confirms buried work, ambiguous identity, or unsafe freshness cues, retain the verdict; verify any redesign against the same data and task.
