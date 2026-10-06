# Golden task: DataHub marketing industry-news

## Purpose

Use this card to verify that `design-craft` routes a real DataHub page through
the local Codex frontend workflow while keeping DataHub product context,
`DESIGN.md`, and live runtime behavior above generic visual rules.

Set `DATAHUB_REPO` to the local DataHub checkout before replaying commands.
The environment variable keeps this public evidence card machine-neutral.

## Target

```text
$DATAHUB_REPO/src/app/marketing/industry-news
```

## Surface contract

- Surface: `dashboard`
- Intent: `visual-refine`
- Scope: `page`
- Expected tier: `L2`
- Expected style authority:
  `$DATAHUB_REPO/DESIGN.md`
- Expected authority mode: `enforce`
- Browser validation: required for any visible UI change.
- Screenshot evidence: required for page-level visual changes when route output
  sets `browser_screenshot_required=true`.
- Directory governance: required.
- Performance review: required.

## Route command

```bash
bash scripts/design_craft_route.sh \
  --target $DATAHUB_REPO/src/app/marketing/industry-news \
  --surface dashboard \
  --intent visual-refine \
  --scope page
```

## Expected route evidence

- `frontend_tier`: `L2`
- `candidate_skills`: includes `design-craft`
- `preflight_status`: `pass`
- `preflight_code`: `OK`
- `style_authority_path`:
  `$DATAHUB_REPO/DESIGN.md`
- `browser_validation_required`: `true`
- `browser_screenshot_required`: `true`
- `preferred_screenshot_tool`: `tmwd_browser.browser_screenshot_ops`
- `directory_governance_required`: `true`
- `performance_review_required`: `true`

## Detector command

```bash
bash scripts/design_craft_detect.sh \
  --target $DATAHUB_REPO/src/app/marketing/industry-news \
  --full-json
```

Expected current smoke result: upstream findings `0`; local design-craft signal
findings `0`.

## Selected design-craft references

For a real implementation pass, read at minimum:

- `references/validation-contract.md`
- `references/surface-playbooks.md`
- `references/report-quality.md`
- `references/performance-quality.md`
- `references/project-structure.md`
- `references/engineering-quality.md`

Do not read `references/visual-judgment.md` as a license to override DataHub's
dashboard grammar. Use it only for anti-slop checks after the DataHub
`DESIGN.md` and runtime page behavior are understood.

## Validation expectation

If this task changes UI, a complete run should include:

1. Route command above.
2. Relevant DataHub type/lint/build/test command for the touched surface.
3. Real browser validation on the target route.
4. TMWD screenshot artifact evidence when `browser_screenshot_required=true`:
   baseline `viewport`, plus `selector` or `clip` for the changed section.
5. DOM or screenshot evidence for:
   - no unwanted horizontal overflow;
   - readable dashboard/report density;
   - project typography/color/component contracts preserved;
   - loading, empty, long-content, and responsive states when impacted.

## Current evidence status

As of 2026-06-24, this golden card is backed by route smoke plus detector smoke
against the target path. Browser validation is intentionally not claimed here.

## Regression signals

Treat these as regressions:

- The route no longer discovers DataHub `DESIGN.md`.
- `frontend_tier` drops below `L2` for this page-level visual-refine task.
- `browser_validation_required` becomes false.
- `browser_screenshot_required` becomes false for this page-level visual task.
- Generic visual guidance overrides DataHub dashboard/report contracts.
- Candidate skills are reported as selected skills without the references being
  read and applied.
