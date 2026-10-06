# Validation

## Route and authority

The L2 frontend route passed with:

- surface: `landing`
- platform: `web`
- product context: `PRODUCT.md`
- enforced visual authority: `DESIGN.md`
- selected skills: `design-craft`, `frontend-skill`, `minimalist-ui`
- execution: main agent, serial, no subagent
- required runtime: `tmwd_browser`
- required visual review: before/after screenshots

## Local runtime

The controlled target was served from the repository:

```bash
python3 -m http.server 4177 --bind 127.0.0.1 \
  --directory evals/visual-reference/target-validation/reference-assisted-product-landing/site
```

Variant routes:

```text
http://127.0.0.1:4177/?variant=baseline
http://127.0.0.1:4177/?variant=reference-assisted
```

Both variants use the same `index.html`, `styles.css`, and `app.js`.

## Browser evidence

- Transport health: healthy.
- Responsive capture transport: forced `tmwd_link`. The default WebSocket
  route timed out during CDP viewport work and its link fallback then found the
  debugger already attached; switching to one explicit link batch removed the
  race.
- Verified viewports and PNG dimensions: `1440x900` and `390x844` for both
  phases.
- Shared manifest keys: `desktop`, `mobile`.
- External run: `20260817T051534181Z-3107946c`, status `completed`.
- Scoped finalization: one managed tab closed, close verified, zero unkept tabs
  remaining, no unmanaged user tab touched.

The interaction-state selector screenshot timed out and is not claimed. The
dialog itself was instead verified through NodeRef interaction and live DOM
state. Four successful viewport PNGs remain the visual evidence.

## Static checks

```bash
node --check \
  evals/visual-reference/target-validation/reference-assisted-product-landing/site/app.js

python3 skills/design-craft/scripts/design_craft_static_review.py \
  --target evals/visual-reference/target-validation/reference-assisted-product-landing/site \
  --json --fail-on high
```

Observed result:

- JavaScript syntax passed.
- Static review reported zero high-severity findings and zero focus risks.
- Medium signals were token-definition literals and responsive-width review
  prompts; live `1440x900` and `390x844` evidence confirmed no overflow.

## Contract and repository gates

Run after the target packet, catalog refs, tests, and required-file registry
were complete:

```bash
make visual-reference-check
make validate
git diff --check
```

Observed result:

- `visual-reference-check`: 32 tests passed; catalog, positive/negative golden
  Packs, target Pack, and strict screenshot manifest validation passed.
- `validate`: 27 gates passed, including lint, repository/tooling contracts,
  package boundary, public-repository checks, unit/integration/adversarial tests,
  and development maturity.
- `git diff --check`: passed.

The first `make validate` attempt stopped at `package-boundary` because a
preceding direct unittest command had generated three `__pycache__` files under
the packaged skill. Those test residuals were removed, and
`visual-reference-check` now runs Python with
`PYTHONDONTWRITEBYTECODE=1`. The clean rerun passed all 27 gates. No product
logic or package contract was weakened to obtain the pass.

No release, publish, commit, or push is part of this validation.

## Not verified

- No production application, authentication, API, database, analytics, or
  real customer workflow was exercised.
- No automated a11y suite, screen reader, performance trace, or browser matrix
  was run.
- The reference-assisted result is not an independent comparative-eval run and
  cannot promote a hypothesis beyond `proposed`.
