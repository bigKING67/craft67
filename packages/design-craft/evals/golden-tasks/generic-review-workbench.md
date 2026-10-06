# Golden task: Generic review workbench L4 calibration

## Purpose

Use this card to verify that `design-craft` can run a real, repository-local
before/after product UI evaluation without depending on a project-specific app.
The fixture exercises design judgment, responsive evidence, screenshot
metadata, score anti-inflation, and strict L4 case validation.

## Target

```text
evals/fixtures/l4-pages/generic-review-workbench/index.html
```

## Surface contract

- Surface: local review-operations workbench fixture
- Intent: before/after product UI taste calibration
- Scope: static page fixture plus L4 evidence packet
- Expected tier: L4 evidence case
- Expected style authority: the fixture's own warm editorial operations UI
- Browser validation: required for visible before/after evidence
- Screenshot evidence: required for desktop and compact responsive viewports
- Directory governance: required
- Score anti-inflation: required

## Local fixture command

```bash
python3 -m http.server 4173 --bind 127.0.0.1 --directory evals/fixtures/l4-pages
```

Routes:

```text
http://127.0.0.1:4173/generic-review-workbench/?variant=before
http://127.0.0.1:4173/generic-review-workbench/?variant=after
```

## Expected evidence

- `screenshots.json` uses schema `design-craft.l4-screenshots.v1`.
- Before and after share at least one artifact key.
- Desktop and compact responsive artifacts record path, SHA-256, dimensions,
  target, viewport metadata, and horizontal-overflow layout metrics.
- Before and after score JSON files both use evidence level `L4`.
- The after score is higher than the before score but remains below 95 because
  the fixture is generic and does not prove full product-specific interaction
  coverage.

## Validation commands

```bash
python3 scripts/design_craft_l4_evidence_manifest.py \
  --validate-screenshots-json evals/product-ui-taste/before-after/generic-review-workbench-local-l4/screenshots.json \
  --strict

python3 scripts/design_craft_l4_case_validate.py \
  --case-dir evals/product-ui-taste/before-after/generic-review-workbench-local-l4 \
  --strict
```

For same-machine artifact verification, also run:

```bash
python3 scripts/design_craft_l4_case_validate.py \
  --case-dir evals/product-ui-taste/before-after/generic-review-workbench-local-l4 \
  --strict \
  --require-existing-files
```

## Regression signals

Treat these as regressions:

- The fixture no longer exposes both `before` and `after` variants.
- `screenshots.json` loses shared before/after artifact keys.
- L4 case validation passes despite missing screenshot path, hash, dimensions,
  viewport metadata, or state boundaries.
- The after score reaches 95+ without product-specific visual language and
  broader interaction-state evidence.
- The case claims unverified phone, hover, keyboard, loading, empty, error,
  production routing, authentication, API, or backend behavior.
