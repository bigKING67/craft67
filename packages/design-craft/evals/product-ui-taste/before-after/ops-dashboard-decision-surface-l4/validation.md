# Validation

## Fixture server

Started a local static server from the design-craft repository:

```bash
python3 -m http.server 4175 --bind 127.0.0.1 --directory evals/fixtures/l4-pages
```

Smoke checks:

```bash
curl -s -o /dev/null -w '%{http_code}\n' 'http://127.0.0.1:4175/ops-dashboard-decision-surface/?variant=before'
curl -s -o /dev/null -w '%{http_code}\n' 'http://127.0.0.1:4175/ops-dashboard-decision-surface/?variant=after'
```

Observed result: both returned `200`.

## Screenshot capture

Captured repo-external PNG artifacts with Google Chrome headless CLI through
the design-craft L4 capture helper:

```bash
python3 scripts/design_craft_l4_capture.py \
  --case-id ops-dashboard-decision-surface-l4 \
  --before-url 'http://127.0.0.1:4175/ops-dashboard-decision-surface/?variant=before' \
  --after-url 'http://127.0.0.1:4175/ops-dashboard-decision-surface/?variant=after' \
  --viewport desktop=1440x900 \
  --viewport compact500=500x844 \
  --manifest evals/product-ui-taste/before-after/ops-dashboard-decision-surface-l4/screenshots.json
```

Observed result: all four PNG files were written under:

```text
~/.tmwd-browser-mcp/runtime/runs/ops-dashboard-decision-surface-l4/20260701T015356Z-chrome-headless-fallback/artifacts
```

Chrome emitted nonfatal stderr during headless capture, but each selected
screenshot file was written, PNG dimensions were read, and SHA-256 hashes were
recorded in `screenshots.json`.

## Layout metrics

Headless dump-DOM evidence read the fixture's non-visual
`data-design-craft-layout-metrics` marker for each viewport.

Observed layout metrics:

- before desktop: `inner_width=1440`, `scroll_width=1440`, `horizontal_overflow=false`
- after desktop: `inner_width=1440`, `scroll_width=1440`, `horizontal_overflow=false`
- before compact500: `inner_width=500`, `scroll_width=500`, `horizontal_overflow=false`
- after compact500: `inner_width=500`, `scroll_width=500`, `horizontal_overflow=false`

## design-craft validators

Run from the repository root:

```bash
python3 scripts/design_craft_l4_evidence_manifest.py \
  --validate-screenshots-json evals/product-ui-taste/before-after/ops-dashboard-decision-surface-l4/screenshots.json \
  --strict \
  --require-existing-files

python3 scripts/design_craft_l4_case_validate.py \
  --case-dir evals/product-ui-taste/before-after/ops-dashboard-decision-surface-l4 \
  --strict \
  --require-existing-files
```

Observed result: passed.

## Not verified

- Exact 390px phone viewport evidence is not claimed. Chrome headless CLI was
  repeatable at `500x844` in this run.
- No hover, keyboard traversal, pointer interaction, loading, empty, or error
  state screenshot was captured.
- No production app route, authentication, API, or backend state was exercised.
