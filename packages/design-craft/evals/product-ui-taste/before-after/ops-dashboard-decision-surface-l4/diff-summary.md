# Diff summary

This L4 case adds a second project-neutral before/after fixture focused on the
`Dashboard card soup -> decision surface` move from
`references/design-move-library.md`. It does not change a production
application.

## Files and boundaries

- `evals/fixtures/l4-pages/ops-dashboard-decision-surface/index.html`
  - Adds a single static operations dashboard fixture.
  - Supports `?variant=before` and `?variant=after` from the same file, so the
    comparison isolates composition, hierarchy, and task order rather than data
    or routing differences.
  - Adds non-visual `data-design-craft-layout-metrics` metadata for dump-DOM
    evidence.
- `evals/product-ui-taste/before-after/ops-dashboard-decision-surface-l4/`
  - Adds the completed L4 case packet: input, before score, after score,
    screenshot manifest, diff summary, and validation notes.

## Before design read

The before variant is intentionally competent but unresolved:

- Centered overview headline.
- Four equal KPI cards.
- Full-width queue table sorted like a dashboard list, not a dispatch surface.
- Chart and notes panels competing with the operational queue.

This creates a clean dashboard that shows many facts but does not tell the
operations lead where to act first.

## After design move

The after variant applies a decision-surface move:

- Rewrites the headline around the blocker and the operator's next job.
- Adds a dark lead risk object with the strongest action in the first fold.
- Converts the KPI strip into one semantic risk metric plus quieter support.
- Makes the priority queue the primary work area and pairs each row with a
  recovery action.
- Keeps chart and action-rail content secondary, supporting the dispatch flow.

## Score delta

- Before: 79 / 100
- After: 92 / 100
- Delta: +13

The after score is intentionally capped at 92 because this is a generic local
fixture. It has real L4 screenshot evidence and a stronger dashboard design
move, but it does not include production data variation, exact 390px phone
capture, or complete interaction-state coverage.
