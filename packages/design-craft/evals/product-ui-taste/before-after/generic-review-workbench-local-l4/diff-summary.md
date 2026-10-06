# Diff summary

This L4 case adds a generic local before/after fixture and records real
repo-external screenshot evidence for both variants. It does not change a
production application.

## Files and boundaries

- `evals/fixtures/l4-pages/generic-review-workbench/index.html`
  - Adds a single static review-workbench fixture.
  - Supports `?variant=before` and `?variant=after` from the same file, so the
    comparison isolates hierarchy and composition rather than routing or data
    differences.
  - Adds non-visual `data-design-craft-layout-metrics` metadata for dump-DOM
    evidence.
- `evals/product-ui-taste/before-after/generic-review-workbench-local-l4/`
  - Adds the completed L4 case packet: input, before score, after score,
    screenshot manifest, diff summary, and validation notes.

## Before design read

The before variant is intentionally competent but unresolved:

- Full-width hero overview.
- Full-width summary card repeating the lead count.
- Four equal metric cards.
- Work rows and next actions start after the overview stack.

This creates an overview-first page where the review operator can see the
ingredients but must infer the next decision.

## After design move

The after variant applies a decision-surface move:

- Rewrites the headline around the operator's unresolved decision.
- Pairs the hero copy with a dark priority summary object.
- Promotes one lead metric and makes the remaining metrics supporting signals.
- Brings priority rows and next actions into the first desktop fold.
- Preserves the same warm editorial fixture palette and avoids introducing a
  separate product brand system.

## Score delta

- Before: 80 / 100
- After: 91 / 100
- Delta: +11

The after score is intentionally capped at 91 because this is a generic local
fixture. It has real L4 screenshot evidence and a clearer design move, but it
does not include product-specific visual language, exact 390px phone capture,
or complete interaction-state coverage.
