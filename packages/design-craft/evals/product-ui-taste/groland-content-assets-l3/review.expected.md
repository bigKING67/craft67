# Expected review: groland content assets L3

Method: single-context browser review with TMWD managed-tab evidence, responsive
viewport checks, selector/clip screenshots, and redacted DOM/computed-style
summaries.

Evidence level: L3 - desktop/mobile browser evidence plus a focused primary
button sample.

Not verified: hover, selected, loading, empty, error, success, permission,
full keyboard navigation, touch ergonomics beyond viewport fit, or before/after
quality delta.

## Overall Score

Score: 84 / 100

Band: clean but generic

## One-Sentence Diagnosis

The page is responsive, aligned, and operationally useful, but the first-screen
metric system still flattens backlog priority and the focus evidence is only
partial, keeping it below a polished-and-professional score.

## Design Direction

The direction should remain calm, precise, data-dense, and enterprise-grade,
but the first screen should behave more like a material operations priority
queue than a uniformly surfaced metric catalog.

## Top Issues

| Priority | Location | Category | Problem | Why It Hurts Taste | Recommendation | Acceptance Criteria |
|---|---|---|---|---|---|---|
| P1 | First-screen metrics | Task focus | Critical backlog metrics and low-risk overview metrics have nearly equal weight. | Operators cannot identify the next highest-value action within three seconds. | Promote script generation, video ID binding, authorization confirmation, and failures into a priority queue above overview cards. | Top three operational risks appear before or visually above generic totals/capacity. |
| P1 | Metric card system | Information order | The grid is tidy but produces card soup across unrelated metric types. | Good responsive fit does not equal good decision order. | Split metrics into priority tasks, production health, and supporting inventory. | Each group has a distinct heading, status role, and visual weight. |
| P1 | Focus sample | Accessibility / interaction polish | Focused upload button has computed outline `none`; visible feedback relies on the primary button's existing shadow/border. | Keyboard users may not receive an unmistakable focus-visible state. | Add a consistent focus-visible ring token for buttons, nav items, search, and dropdown controls. | Programmatic and keyboard focus show a 2px+ visible ring with sufficient contrast and no layout shift. |
| P2 | Mobile first screen | Composition | The mobile layout fits without horizontal overflow, but the hero remains tall and pushes priority tasks downward. | Responsive layout preserves the desktop hierarchy instead of re-prioritizing mobile attention. | Shorten mobile hero copy and move top backlog status above or into the hero. | On 390px width, the first viewport shows the main CTA plus at least one priority backlog cue. |
| P2 | Copy | Microcopy | Operator-facing labels still expose internal terms such as `asset_id`, `TOS`, `preview`, and `视频ID`. | The UI feels closer to system fields than an intentionally designed operations cockpit. | Use business-state labels and move implementation terms to helper text/tooltips. | Metric titles read as tasks or states; internal identifiers are secondary. |

## Detailed Review

### Strengths

- Desktop and mobile browser evidence show no horizontal overflow.
- The page has a coherent light surface system, stable rounded cards, and clear
  numeric formatting.
- Mobile adapts controls and metric cards rather than simply shrinking the
  desktop grid.
- Primary upload action is visible in both desktop and mobile views.

### Deductions

- The highest-risk backlog states are not visually separated from overview and
  capacity metrics.
- The desktop priority area still depends on too many equal cards.
- The mobile first screen is readable but not decisively task-first.
- Focus evidence is partial; do not claim complete keyboard accessibility from
  the current sample.
- Loading, empty, error, success, and permission states were not checked.

## Frontend Implementation Notes

- Add `PriorityBacklogPanel` above the generic metric grid.
- Split the current metric tiles into semantic variants: `blocked`, `warning`,
  `ready`, `capacity`, `failed`, and `muted`.
- Define a reusable focus-visible token, for example:
  `--focus-ring: 0 0 0 3px rgba(47, 110, 234, 0.28)`.
- Use responsive ordering, not only responsive columns: mobile should surface
  the main operational backlog before the full metric catalog.
- Keep the calm light DataHub visual language; the fix is hierarchy and state
  semantics, not more color or heavier shadows.

## Acceptance Checklist

- [ ] Desktop and mobile remain free of horizontal overflow.
- [ ] The first visual focus is the highest-priority backlog, not the full grid.
- [ ] Priority, readiness, capacity, and failure metrics use different visual roles.
- [ ] The primary CTA remains visible but does not replace task prioritization.
- [ ] Focus-visible is unmistakable on buttons, links, search, and dropdowns.
- [ ] Loading, empty, error, success, and permission states are explicitly tested.
- [ ] Internal implementation terms are demoted or explained.
