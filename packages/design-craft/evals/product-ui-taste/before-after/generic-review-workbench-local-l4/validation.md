# Validation

## Fixture server

Started a local static server from the design-craft repository:

```bash
python3 -m http.server 4173 --bind 127.0.0.1 --directory evals/fixtures/l4-pages
```

Smoke checks:

```bash
curl -s -o /dev/null -w '%{http_code}\n' 'http://127.0.0.1:4173/generic-review-workbench/?variant=before'
curl -s -o /dev/null -w '%{http_code}\n' 'http://127.0.0.1:4173/generic-review-workbench/?variant=after'
```

Observed result: both returned `200`.

## Screenshot capture

Captured repo-external PNG artifacts with Google Chrome headless CLI:

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new \
  --disable-gpu \
  --hide-scrollbars \
  --no-first-run \
  --disable-background-networking \
  --force-device-scale-factor=1 \
  --window-size=1440,900 \
  --screenshot="$artifact/before-desktop.png" \
  'http://127.0.0.1:4173/generic-review-workbench/?variant=before'
```

The same capture shape was used for:

- before desktop: `1440x900`
- after desktop: `1440x900`
- before compact responsive: `500x844`
- after compact responsive: `500x844`

Observed result: all four PNG files were written under:

```text
evals/product-ui-taste/before-after/generic-review-workbench-local-l4/artifacts
```

Chrome printed shutdown / OS-integration warnings during some headless exits,
but each selected screenshot file was written and independently hashed.

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
  --validate-screenshots-json evals/product-ui-taste/before-after/generic-review-workbench-local-l4/screenshots.json \
  --strict

python3 scripts/design_craft_l4_case_validate.py \
  --case-dir evals/product-ui-taste/before-after/generic-review-workbench-local-l4 \
  --strict

python3 scripts/design_craft_l4_case_validate.py \
  --case-dir evals/product-ui-taste/before-after/generic-review-workbench-local-l4 \
  --strict \
  --require-existing-files
```

Observed result: passed.

## Broader repository validation

Run from the repository root:

```bash
bash scripts/validate.sh
git diff --check
```

Observed result: passed.

## Browser tooling notes

Chrome headless CLI produced the final screenshots because the initial MCP tool
search in this thread did not expose the L4 evidence bundle helper. Later in the
same thread, `browser_evidence_bundle_ops` became visible and was used as a
non-writing dry run with `verify_artifacts:true`.

Observed result:

- `browser_evidence_bundle_ops` returned `status:"success"`.
- All four artifact files were verified from disk.
- Shared before/after artifact keys were `desktop` and `compact500`.
- The checked PNG byte counts were `193825`, `261055`, `132038`, and `136426`.

TMWD managed tab cleanup:

- Workspace key: `design-craft-generic-l4`
- Finalizer: `browser_tab_lifecycle action=finalize_task`
- Observed result: managed tab closed and remaining count `0`.

## Not verified

- Exact 390px phone viewport evidence is not claimed. Chrome headless CLI was
  repeatable at `500x844` in this run.
- No hover, keyboard, focus ring, loading, empty, or error-state screenshot was
  captured.
- No production app route, authentication, API, or backend state was exercised.
