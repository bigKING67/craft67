# DataHub special report evaluation spec

## Prompt

Use `design-craft` to refine a DataHub special report route. The report is
for business review, with sections, ECharts charts, contribution metrics,
caveats, and supporting tables. Make it feel formal, readable, and evidence-led.

## Expected route behavior

- `surface`: `dashboard` or `data-app`
- `intent`: `visual-refine`
- `scope`: `page`
- `style_authority_path`: project `DESIGN.md`
- `browser_validation_required`: `true`
- `browser_screenshot_required`: `true`
- `performance_review_required`: `true`

## Expected design-craft references

- `references/report-quality.md`
- `references/surface-playbooks.md`
- `references/performance-quality.md`
- `references/engineering-quality.md`
- `references/validation-contract.md`

## Success behavior

- Uses formal report grammar: compact header, executive summary, section
  hierarchy, chart-first evidence, quiet navigation, footnote-sized caveats.
- Keeps DataHub/project `DESIGN.md` and live data truth above generic visual
  guidance.
- Avoids giant tables as the primary narrative.
- Handles net-change labels, >100% share/contribution, and caveats quietly
  unless they are the main point.
- Browser-validates at least desktop and narrow viewport, including chart
  resize and tooltip/legend behavior.
- Captures screenshot artifact evidence for the baseline viewport and the
  changed report section when route output requires screenshots.

## Failure modes

- Turns the report into a generic SaaS landing page.
- Treats contribution edge cases as headline drama instead of methodology or
  tooltip detail.
- Verifies only with build/type-check and skips browser evidence.
