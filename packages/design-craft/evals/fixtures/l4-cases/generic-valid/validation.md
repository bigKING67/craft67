# Validation

## Commands

```bash
python3 scripts/design_craft_l4_evidence_manifest.py --validate-screenshots-json evals/fixtures/l4-cases/generic-valid/screenshots.json --strict
python3 scripts/design_craft_browser_evidence.py --validate-score-json evals/fixtures/l4-cases/generic-valid/score.before.json
python3 scripts/design_craft_browser_evidence.py --validate-score-json evals/fixtures/l4-cases/generic-valid/score.after.json
python3 scripts/design_craft_l4_case_validate.py --case-dir evals/fixtures/l4-cases/generic-valid --strict
```

## Browser validation

- Target: local generic fixture route
- Viewport artifact: desktop before and after metadata only
- Selector/clip artifact: not required for this fixture
- DOM/computed-style evidence: layout metrics are represented in `screenshots.json`

## Result

- The case directory should pass strict validation without requiring local screenshot files to exist.

## Not verified

- No real product route or production browser state is claimed by this fixture.
