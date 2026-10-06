# Dashboard quality evaluation spec

## Prompt

Use `design-craft` to improve a data-heavy dashboard page with filters,
charts, KPI cards, and tables. Preserve task flow, improve hierarchy, handle
empty/loading/error states, and verify responsive behavior.

## Expected route behavior

- `surface`: `dashboard`, `admin`, `app`, or `data-app`
- `intent`: `visual-refine` or `functional`
- `scope`: `page`
- `directory_governance_required`: usually `true`
- `performance_review_required`: `true`
- `browser_validation_required`: `true`
- `browser_screenshot_required`: usually `true` for page-level visual work

## Expected design-craft references

- `references/surface-playbooks.md`
- `references/report-quality.md` when the page is report-like
- `references/engineering-quality.md`
- `references/performance-quality.md`
- `references/project-structure.md`
- `references/validation-contract.md`

## Success behavior

- Prioritizes monitoring, comparison, operation, and decision-making over visual
  drama.
- Checks table scanability, sorting/filtering affordances, row bounds, and
  loading/empty/error states.
- Checks chart scale, tooltip overflow, legend wrapping, and resize behavior.
- Reports performance assumptions for chart/table data scale.
- Reports screenshot artifact evidence when route output requires it.

## Failure modes

- Applies landing-page visual grammar to operational dashboard UI.
- Passes free-form text into route `--intent` or `--scope` instead of fixed
  enum values.
- Adds unbounded client-side render work.
- Hides data caveats inside vague copy.
- Creates shared components without repeated callers.
