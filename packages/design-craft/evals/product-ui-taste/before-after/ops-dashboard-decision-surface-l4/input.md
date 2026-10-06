# L4 before/after eval: ops-dashboard-decision-surface-l4

## Context

- Case ID: `ops-dashboard-decision-surface-l4`
- Product surface: local fixture at `http://127.0.0.1:4175/ops-dashboard-decision-surface/`
- Primary user: operations lead
- Primary job: identify the queue that blocks handoff and assign the recovery action without decoding an equal-weight dashboard.
- Design read: Reading this as a project-neutral operations dashboard fixture for design-craft L4 calibration, with calm executive-ops UI, optimized for turning routine KPI browsing into a first-fold dispatch decision.

This is a repository-local fixture, not an external product route. The before
and after variants are served from the same HTML file and selected with:

- Before: `?variant=before`
- After: `?variant=after`

## Before evidence

| Artifact | Path | SHA-256 | Dimensions |
|---|---|---|---|
| before desktop viewport | `~/.tmwd-browser-mcp/runtime/runs/ops-dashboard-decision-surface-l4/20260701T015356Z-chrome-headless-fallback/artifacts/screenshot-viewport-ops-dashboard-decision-surface-l4-before-desktop-chrome-headless.png` | `ebbfac6ad45fa9cc93252326d8d12892a75367812cc82f7e94875805af54c34e` | 1440x900 |
| before compact viewport | `~/.tmwd-browser-mcp/runtime/runs/ops-dashboard-decision-surface-l4/20260701T015356Z-chrome-headless-fallback/artifacts/screenshot-viewport-ops-dashboard-decision-surface-l4-before-compact500-chrome-headless.png` | `cbbbf386e5867058cc322b8d8cf635a4cdd74beb6da58693aeedcd0b72f65d1c` | 500x844 |

## After evidence

| Artifact | Path | SHA-256 | Dimensions |
|---|---|---|---|
| after desktop viewport | `~/.tmwd-browser-mcp/runtime/runs/ops-dashboard-decision-surface-l4/20260701T015356Z-chrome-headless-fallback/artifacts/screenshot-viewport-ops-dashboard-decision-surface-l4-after-desktop-chrome-headless.png` | `d5f248952f11d871650997fd9e3d21774d9a9b81152b93e8c080e008e7b3fef8` | 1440x900 |
| after compact viewport | `~/.tmwd-browser-mcp/runtime/runs/ops-dashboard-decision-surface-l4/20260701T015356Z-chrome-headless-fallback/artifacts/screenshot-viewport-ops-dashboard-decision-surface-l4-after-compact500-chrome-headless.png` | `9db549501f05cb5770c6430c97f9870e1efcb34bbc2b47572cea664596129e71` | 500x844 |

## Runtime evidence

- Browser target: local static fixture served from `evals/fixtures/l4-pages`.
- Capture tool: Google Chrome headless CLI, writing repo-external PNG artifacts under `~/.tmwd-browser-mcp/runtime/runs/ops-dashboard-decision-surface-l4/`.
- Viewports: desktop `1440x900`, compact responsive `500x844`.
- Layout metrics: headless `--dump-dom` reads `data-design-craft-layout-metrics`; all four captures record `horizontal_overflow:false`.
- Interaction states: static fixture buttons and focus-visible CSS are present; no hover, keyboard traversal, async loading, empty, or error states are claimed.

## Not verified

- Exact 390px phone viewport was not used; compact responsive evidence is limited to `500x844`.
- No production app data, backend flow, authentication, network request, or real user workflow was exercised.
- No pointer interaction, keyboard traversal, hover, loading, empty, or error state screenshot was captured.
