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
