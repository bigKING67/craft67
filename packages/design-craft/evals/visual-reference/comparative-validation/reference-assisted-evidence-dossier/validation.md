# Validation

## Route and authority

The L2 frontend route selected the repository's product/design authority and a
serial main-agent workflow:

- surface: `landing`
- platform: `web`
- product context: `PRODUCT.md`
- enforced visual authority: `DESIGN.md`
- actually applied skills: `design-craft`, `minimalist-ui`
- browser authority: `tmwd_browser`
- execution: main agent, no subagent
- native runtime: not applicable

The Reference Pack maps Lightspark only to `structure` and Nue only to
`responsive`. The fixture reimplements the bounded mechanisms in Cairn's own
content and authority; it does not copy source assets, identity, copy, data, or
geometry.

## Local runtime

The shared fixture was served from the repository:

```bash
python3 -m http.server 4178 --bind 127.0.0.1 \
  --directory evals/visual-reference/comparative-validation/reference-assisted-evidence-dossier/site
```

Variants and six states use the same HTML, CSS, and JavaScript and differ only
through `variant` and `state` query values.

## Browser evidence

- Browser67 run:
  `browser67://runs/design-craft/20260817T060232364Z-6a6a4ed2`.
- Run status: `completed`; recorded outcome: `passed`.
- Transport health: WebSocket and link both healthy; preferred transport
  WebSocket.
- Final captures: baseline/reference-assisted at `1440x900` and `390x844`.
- All four PNG dimensions and SHA-256 values were tool-verified; all four
  report `horizontal_overflow=false`.
- Assisted intermediate check: `768x900`, no horizontal overflow.
- Both variants: six mobile query states checked for overflow, headings,
  landmarks, IDs, labels, busy/recovery state, and long-label preservation.
- Dialog focus entry/restoration, retry state transition, real Tab order,
  Reduced Motion, and key contrast pairs were live checked.
- Final visual review covered the entry comparison plus assisted evidence,
  method, questions, and pilot sections.
- Scoped finalization closed and verified three managed tabs, left zero
  unkept managed tabs, and did not touch unmanaged user tabs.

The Browser67 full-page capture repeated the hero at device-pixel ratio 2 and
was excluded as a capture-tool artifact. Only exact viewport captures and the
separate below-fold section reviews support the visual conclusion.

## Static checks

Final commands:

```bash
node --check \
  evals/visual-reference/comparative-validation/reference-assisted-evidence-dossier/site/app.js

python3 skills/design-craft/scripts/design_craft_static_review.py \
  --target evals/visual-reference/comparative-validation/reference-assisted-evidence-dossier/site \
  --json --fail-on high
```

The source bundle is `44,454` decoded bytes. JavaScript syntax passed. Static
review reported `0 high`, `14 medium`, and `3 info` findings. The medium focus
signal is a cross-file scanner prompt covered by the live keyboard and dialog
checks; token-definition literals and breakpoint prompts are bounded by the
declared authority plus the `1440`, `768`, and `390` viewport evidence.

## Contract and repository gates

Final closeout commands:

```bash
make visual-reference-check
make validate
git diff --check
```

Observed result:

- `visual-reference-check`: 40 tests passed; the catalog and all positive and
  negative Packs validated; both target and comparative screenshot manifests
  passed strict validation.
- Promotion evidence contract: unit and CLI integration regressions confirm
  that one artifact cannot appear in both `target_validation_refs` and
  `comparative_eval_refs` for the same hypothesis. A distinct later comparison
  is required before `comparative_validated` or `absorbed` can pass validation.
- `validate`: 27 gates passed, including repository/tooling contracts,
  package/public-repository boundaries, workflow and upstream checks,
  unit/integration/adversarial tests, and development maturity.
- `git diff --check`: passed.

The first full validation run stopped at `public-repository` because the
tool-built manifest retained 16 absolute Browser67 paths under the local user
home. Those evidence locations were normalized to portable `browser67://`
URIs without changing hashes, dimensions, layout metrics, or run status. The
focused public-repository check then scanned 945 files successfully, and the
complete 27-gate rerun passed. No contract was weakened.

No release, publish, commit, or push is part of this validation.

## Evidence limits

- This is a controlled local target, not a production route, customer test, or
  independent human preference study.
- No screen reader, assistive-technology matrix, browser matrix, authenticated
  workflow, API, persistence, analytics, or backend was exercised.
- Repeated warm-cache background navigations did not expose paint timing.
- Performance numbers are local regression observations only.
