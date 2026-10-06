# Report quality

Use this for dashboard exports, static reports, special reports, formal
business-review pages, and evidence-heavy report surfaces where reading order
and evidence quality matter more than landing-page drama.

## Contents

- [Chart or report intent](#chart-or-report-intent)
- [Report grammar](#report-grammar)
- [Chart selection](#chart-selection)
- [Multi-chart composition](#multi-chart-composition)
- [Encoding integrity](#encoding-integrity)
- [Tables](#tables)
- [Navigation and hierarchy](#navigation-and-hierarchy)
- [Report-surface defaults](#report-surface-defaults)
- [ECharts and responsive checks](#echarts-and-responsive-checks)

## Chart or report intent

- A chart request stays a chart request. Analysis alone does not imply a
  complete report, dashboard, cover, executive summary, or appendix.
- Use full report grammar only when the requested outcome is a structured
  narrative deliverable, such as a review pack, evidence dossier, or export.
- Distinguish an operational dashboard product surface from a static or
  exported report. They may share evidence, but not necessarily reading order,
  density, navigation, or interaction.
- If scope is ambiguous, choose the smallest deliverable that answers the
  stated question and make any broader report assumption explicit.

## Report grammar

Reports should feel like a clear analyst deliverable:

1. Cover or compact header: what period, market, channel, or entity is covered.
2. Executive summary: 3-5 decisive points, not a generic hero.
3. Evidence sections: one question per section.
4. Chart-first narrative: charts carry comparisons, trends, mix, and anomalies.
5. Supporting detail: tables, caveats, and methodology only where they earn
   their weight.
6. Appendix or disclosure: dense rows, definitions, and edge caveats.

Do not use generic SaaS landing patterns as the default: giant gradient hero,
decorative cards, testimonial rhythm, animated section banners, or oversized
marketing CTAs.

## Chart selection

- Translate the analytical question and data shape before naming a chart:
  comparison or rank, change over time, composition, distribution,
  relationship or flow, and anomaly or status are different jobs.
- Prefer the simplest familiar form that preserves the important comparison.
  Project `DESIGN.md`, business truth, installed chart libraries, and runtime
  constraints outrank external templates or galleries.
- For an ambiguous or high-consequence choice, compare two or three candidates
  on encoding truth, label density, expected reading time, and whether
  interaction is genuinely needed. Do not force candidate theater for an
  obvious simple choice.
- Record the rejected tradeoff only when it helps a reviewer verify the choice;
  do not turn routine chart selection into process overhead.

## Multi-chart composition

- Count charts by independent conclusions, not columns, metrics, chart types,
  or template slots.
- Prefer one primary chart per conclusion. Delete a second chart when it merely
  restates the same ranking, trend, or composition without a different job.
- Combine overview, evidence, and detail only when each layer answers a
  different question. Keep exact rows in a table when they support audit or
  lookup rather than inventing another chart.

## Encoding integrity

- Length-encoded bars use a zero baseline. Diverging bars cross a visible zero;
  a deliberately transformed or indexed view must name the transformation and
  must not imply raw magnitude.
- Area-encoded circles or bubbles map values to area, so radius scales by the
  square root of the value. Do not map value directly to radius.
- Treemaps require a meaningful hierarchy and non-negative weights. Do not
  force negative or missing values into area.
- In choropleths, geographic area is not a value encoding. State whether fill
  represents a rate, count, share, or indexed value and disclose normalization
  when population or exposure changes the interpretation.
- Treat negative, zero, missing, and greater-than-100-percent values explicitly
  in domains, labels, totals, and caveats; never silently clamp or drop them.
- Color must not be the only cue for series, direction, state, or selection.
  Add labels, position, shape, texture, or text where the distinction matters.
- Tooltips, drill-down, search, or hover details must resolve to real queryable
  records. Do not fabricate precision or interaction for aggregate marks whose
  underlying records are unavailable.
- Prefer direct labels or restrained legends for top series.
- Keep table detail below the chart or behind expansion when the chart answers
  the main question.
- Make units, baseline, date range, and filters visible near the chart.

## Tables

Use tables when the user must scan exact rows, compare many entities, audit
inputs, or export operational detail.

Avoid:

- Giant tables as the main story.
- Repeating the same metric in chart, card, and table without a different job.
- Unbounded table height inside report sections.
- Dense numeric columns without units, alignment, or sorting cues.

## Navigation and hierarchy

- Use quiet TOC or sticky section markers for long reports.
- Keep headings short and decision-oriented.
- Avoid over-carded layouts; sections can be separated by typography and space.
- Put caveats in footnote-sized copy, hover/title, or methodology blocks when
  secondary.
- Preserve print/export readability if reports are likely to be shared.

## Report-surface defaults

- Business truth and project `DESIGN.md` outrank generic visual rules.
- Use formal-report density: compact header, readable charts, restrained cards.
- Net-change labels should be quiet; keep noisy contribution math in tooltip or
  details when it distracts from the main story.
- If share/contribution exceeds 100%, explain in hover/title or methodology
  rather than making it a headline unless it is the point.
- For channel/material/ROI reports, prioritize trend, contribution, top movers,
  and exceptions over decorative summaries.

## ECharts and responsive checks

- Ensure charts resize after container, tab, drawer, or route changes.
- Verify canvas/SVG does not overflow at narrow width.
- Check tooltip clipping, legend wrapping, axis label rotation, and empty data.
- For hidden tabs or accordions, trigger resize after reveal.
- Browser validation should inspect at least one desktop and one narrow viewport
  when chart layout changed.
- When route output requires screenshot evidence, capture a baseline viewport
  plus a selector/clip artifact for the changed report section.
