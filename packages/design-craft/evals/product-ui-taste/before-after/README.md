# Product UI taste before/after evals

Use this directory for real L4 cases only: before/after evidence, implementation
diff, validation commands, and explicit unverified states.

Do not count a case as L4 until it has:

- Before screenshot artifact path, SHA-256 hash, and dimensions.
- After screenshot artifact path, SHA-256 hash, and dimensions.
- Before and after product UI taste scores with evidence level `L4`.
- Diff summary naming the actual changed files or implementation boundaries.
- Validation commands and observed results.
- Unverified states, if any.

Screenshot metadata belongs in `screenshots.json` using
`design-craft.l4-screenshots.v1`. Keep PNG files outside the repository and
store only artifact paths, SHA-256 hashes, dimensions, viewport metadata, and
optional layout metrics in the manifest.

Validate scaffold manifests while filling them:

```bash
python3 scripts/design_craft_l4_evidence_manifest.py \
  --validate-screenshots-json evals/product-ui-taste/before-after/<case>/screenshots.json
```

Once a case is claimed as real L4 evidence, use strict validation:

```bash
python3 scripts/design_craft_l4_evidence_manifest.py \
  --validate-screenshots-json evals/product-ui-taste/before-after/<case>/screenshots.json \
  --strict
```

The `_template/` directory is schema scaffolding only. It is not evidence and
must not be cited as a completed before/after improvement.

Keep active examples project-neutral. Historical project-specific cases may
remain for provenance, but current README examples, validation gates, and score
checks should point at generic fixtures unless a user explicitly scopes a new
project case.

Completed project-neutral fixture examples:

```bash
python3 scripts/design_craft_l4_case_validate.py \
  --case-dir evals/product-ui-taste/before-after/generic-review-workbench-local-l4 \
  --strict

python3 scripts/design_craft_l4_case_validate.py \
  --case-dir evals/product-ui-taste/before-after/ops-dashboard-decision-surface-l4 \
  --strict
```

- `generic-review-workbench-local-l4`: generic review workbench layout polish
  with local fixture screenshots and responsive metadata.
- `ops-dashboard-decision-surface-l4`: dashboard card-soup to decision-surface
  move, using a local operations dashboard fixture with before/after viewport
  evidence.
