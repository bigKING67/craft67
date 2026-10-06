# Expected review: material ops home

Method: DEGRADED: single-context (static screenshot review; no browser, DOM, or
responsive evidence)
Evidence level: L0 - static screenshot only

## Overall Score

Score: 82 / 100
Design maturity level: clean but generic

## One-Sentence Diagnosis

The page is clean and aligned, but the metric grid gives backlog, completion,
capacity, and failure states almost the same weight, so it feels like a tidy
admin dashboard rather than a task-first material operations cockpit.

## Design Direction

The direction should be calm, precise, data-dense, and operational, with the
highest-risk material tasks visibly prioritized over low-risk overview metrics.

## Top Issues

| Priority | Location | Category | Problem | Why It Hurts Taste | Recommendation | Acceptance Criteria |
|---|---|---|---|---|---|---|
| P1 | Metric grid | Task focus | Twelve tiles are visually equal even though some represent critical backlog and others are overview or capacity. | Operators cannot identify the top action within three seconds. | Split into priority queue, production progress, and storage/source overview. | The top three tasks are visible before low-risk metrics. |
| P1 | Authorization/script/video-ID metrics | Contrast | Large backlog numbers do not receive semantic status treatment. | Risk severity is hidden by uniform black numbers and white cards. | Add warning/status badges, action affordances, and priority order. | Backlog and failure states are visually stronger than ready/capacity states. |
| P2 | Hero | Composition | The hero uses a large area for two actions and generic explanatory copy. | The most valuable first-screen area does not carry enough decision value. | Compress the hero or embed the top backlog summary and primary next action. | First-screen vertical space is reduced or carries task-priority information. |
| P2 | Copy | Microcopy | Labels expose internal terms such as asset_id, preview, and TOS. | The UI feels like system fields surfaced directly to operators. | Use task language as titles and move internal terms to helper text or tooltips. | Card titles describe business state; implementation terms become secondary. |
| P2 | Surface system | Repetition | Many near-identical cards create mild card soup. | The page is tidy but generic and lacks mature information choreography. | Reduce low-priority card surface strength and group related metrics. | Card count or card visual weight drops without losing information. |

## Frontend Implementation Notes

- Create separate component anatomy for `PriorityTaskPanel`, `MetricGroup`,
  `MetricTile`, `WorkflowChecklist`, and `NextActionPanel`.
- Add semantic status variants: `ready`, `warning`, `blocked`, `failed`, and
  `muted`.
- Use tabular numbers and one formatter for thousands separators and units.
- Keep the sidebar active state slightly quieter than the main CTA.
- Do not mark responsive, hover, focus, loading, empty, or error states as
  verified until browser evidence exists.

## Acceptance Checklist

- [ ] First focus is the highest-priority material task, not the sidebar.
- [ ] The primary action is visible next to the highest-priority decision.
- [ ] Backlog, failure, ready, and capacity metrics use different visual roles.
- [ ] Internal implementation terms are demoted or explained.
- [ ] Numeric formatting is consistent across all tiles.
- [ ] Static screenshot limitations are stated in the review.
