# Diff summary

## Files changed

Product repo: `$DATAHUB_REPO`

- `src/app/content/live-center/_components/live-center-session-detail.tsx`
- `src/app/content/live-center/live-center.module.css`

Eval repo: `$DESIGN_CRAFT_HOME`

- `evals/product-ui-taste/before-after/datahub-live-center-review-workbench/input.md`
- `evals/product-ui-taste/before-after/datahub-live-center-review-workbench/score.before.json`
- `evals/product-ui-taste/before-after/datahub-live-center-review-workbench/score.after.json`
- `evals/product-ui-taste/before-after/datahub-live-center-review-workbench/screenshots.json`
- `evals/product-ui-taste/before-after/datahub-live-center-review-workbench/diff-summary.md`
- `evals/product-ui-taste/before-after/datahub-live-center-review-workbench/validation.md`

## Design moves applied

- Dashboard/workbench card soup -> decision surface:
  - The selected-session detail panel now shows `readinessStrip` before metrics and metadata.
  - The next action and evidence readiness are the first decision object in the detail column.
- Mobile stacked but not prioritized -> mobile decision flow:
  - The page header and command strip were compressed.
  - Mobile command cards become compact rows; repeated explanatory copy is hidden at the narrow breakpoint.
  - The filter panel is denser, and the workbench moves into the first mobile viewport.
- Navigation and state semantics:
  - Selected row keeps DataHub brand blue.
  - Converted rows no longer use the same blue rail as selection; positive order text uses neutral primary text.
- Existing design-system enforcement:
  - No new raw colors.
  - Typography continues to use DataHub tokens.
  - The route remains a restrained operational workbench, not a marketing hero or media wall.

## What improved

- Mobile workbench top moved from y=1008 to y=777 in a 390x844 viewport.
- Mobile page header height dropped from 526px to 338px.
- Mobile command strip height dropped from 298px to 163px.
- Desktop workbench top moved from y=481 to y=449 while retaining the two-column workbench.
- Detail information order now leads with next action and evidence readiness before metric and metadata grids.
- Page-level horizontal overflow stayed at 0 on both desktop and mobile.

## What remains

- The Ant Design table still has contained horizontal scroll on mobile and desktop; this is table-local, not page-level overflow.
- Upload, active AI-running, empty, and error states were not exhaustively revalidated in this L4 pass.
- The route CSS module remains large; this change intentionally avoided a structural CSS split to keep the evaluation patch scoped.
