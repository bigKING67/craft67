# L4 before/after eval: generic-review-workbench-local-l4

## Context

- Case ID: `generic-review-workbench-local-l4`
- Product surface: local fixture at `http://127.0.0.1:4173/generic-review-workbench/`
- Primary user: review operations teammates
- Primary job: prioritize unresolved review evidence without card-stack ambiguity
- Design read: Reading this as a generic review-operations workbench fixture for design-craft L4 calibration, with warm editorial ops UI, optimized for turning unresolved evidence into a prioritized decision surface.

This is a repository-local fixture, not an external product route. The before
and after variants are served from the same HTML file and selected with:

- Before: `?variant=before`
- After: `?variant=after`

## Before evidence

| Artifact | Path | SHA-256 | Dimensions |
|---|---|---|---|
| before desktop viewport | `artifacts/screenshot-viewport-generic-review-workbench-before-desktop-headless-chrome.png` | `db939b6b342a9833b1ec9d133c5aa1d8a6c4f87d02cdae7b9ffd723182de4da3` | 1440x900 |
| before compact viewport | `artifacts/screenshot-viewport-generic-review-workbench-before-compact500-headless-chrome.png` | `7d5b355b47622fa44fd0df1016fed43347c0ac09b29f322279ae7c467b303017` | 500x844 |

## After evidence

| Artifact | Path | SHA-256 | Dimensions |
|---|---|---|---|
| after desktop viewport | `artifacts/screenshot-viewport-generic-review-workbench-after-desktop-headless-chrome.png` | `96827d97a94041db18711e9502fe1978194e55cf270a20462ad9a9b33ffa2ee9` | 1440x900 |
| after compact viewport | `artifacts/screenshot-viewport-generic-review-workbench-after-compact500-headless-chrome.png` | `5fdf66b1ebde14a7612445919c9f2600ddd831a645f73b01be7d068a58121afa` | 500x844 |

## Runtime evidence

- Browser target: local static fixture served from `evals/fixtures/l4-pages`.
- Capture tool: Google Chrome headless CLI. The reviewed, project-neutral PNGs
  are committed under this case's `artifacts/` directory for durable replay.
- Viewports: desktop `1440x900`, compact responsive `500x844`.
- Layout metrics: headless `--dump-dom` reads `data-design-craft-layout-metrics`; all four captures record `horizontal_overflow:false`.
- Interaction states: static fixture button state is visible; no hover, keyboard traversal, async loading, empty, or error states are claimed.

## Not verified

- Exact 390px phone viewport was not used because this local Chrome headless CLI run reports a minimum effective width of 500px for repeatable dump/screenshot evidence.
- No production app data, backend flow, authentication, network request, or real user workflow was exercised.
- No pointer interaction, keyboard focus traversal, hover, loading, empty, or error state screenshot was captured.
