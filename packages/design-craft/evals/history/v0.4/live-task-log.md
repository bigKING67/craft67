# Archived live task log

> Immutable pre-v0.5 archive. Current evidence must use the machine contracts
> documented in `evals/README.md`.

This file records historical task evidence for the `design-craft` workflow. It
is not a substitute for validation output; every entry states what actually ran
and what remained unverified at the time.

Historical commands use machine-neutral aliases such as `DATAHUB_REPO` and
`DESIGN_CRAFT_HOME`; set them to the relevant local checkouts before replay.

## 2026-06-24 - DataHub marketing industry-news route migration smoke

- Target:
  `$DATAHUB_REPO/src/app/marketing/industry-news`
- Purpose: verify that the workflow can route a real DataHub frontend surface
  while preserving DataHub `DESIGN.md` authority over generic visual guidance.
- Expected authority:
  `$DATAHUB_REPO/DESIGN.md`
- Route command:

  ```bash
  bash scripts/design_craft_route.sh \
    --target $DATAHUB_REPO/src/app/marketing/industry-news \
    --surface dashboard \
    --intent visual-refine \
    --scope page
  ```

- Evidence status at 2026-06-24 route-policy migration:
  - `frontend_tier`: `L2`
  - `candidate_skills`: `design-craft`, `minimalist-ui`,
    `redesign-existing-projects`
  - `preflight_status`: `pass`
  - `preflight_code`: `OK`
  - `style_authority_path`:
    `$DATAHUB_REPO/DESIGN.md`
  - `browser_validation_required`: `true`
  - `browser_screenshot_required`: `true`
  - `preferred_screenshot_tool`: `tmwd_browser.browser_screenshot_ops`
  - `directory_governance_required`: `true`
  - `performance_review_required`: `true`
- Detector smoke after local signal expansion:

  ```bash
  bash scripts/design_craft_detect.sh \
    --target $DATAHUB_REPO/src/app/marketing/industry-news \
    --full-json
  ```

  Result: upstream findings `0`; design-craft local signal findings `0`.
- Browser validation: not claimed by this log entry.
- Screenshot validation: not claimed by this log entry.

## 2026-06-30 - Product UI taste L2 browser evidence calibration

- Target:
  current Chrome tabs observed through TMWD, sampled read-only for
  `design-craft` product UI taste calibration.
- Selected cases:
  - `cpa-management-quota`
  - `cpa-usage-keeper`
  - `groland-datahub-home`
  - `groland-content-assets-live`
- Skipped cases:
  - external finance console, because it is sensitive.
  - ChatGPT conversation page, because it is private conversation content.
- Evidence status:
  - `tmwd` transport health: healthy.
  - Browser tab list: observed through `browser_tab_ops`.
  - Screenshot artifacts: captured through TMWD `browser_screenshot_ops` using
    `Page.captureScreenshot`, stored outside the repo under
    `~/.tmwd-browser-mcp/runtime/runs/frontend-craft-live-evals/`.
  - DOM/computed style: sampled with `browser_execute_js` for body, headings,
    controls, and surface summaries.
- Eval path:
  `evals/product-ui-taste/live-browser-samples/`
- Evidence level:
  L2 browser evidence.
- Browser validation:
  claimed only for viewport screenshot and DOM/computed-style observation.
- Screenshot validation:
  claimed only for the artifact path/hash/dimensions recorded in the eval case.
- Not verified:
  mobile layout, hover, focus, selected, loading, empty, error, success,
  keyboard, touch, or before/after improvement.

## 2026-06-30 - Product UI taste L3 responsive and focus evidence calibration

- Target:
  `http://localhost:3000/marketing/content-assets`
- Purpose: harden product UI taste scoring so real browser evidence can capture
  responsive fit and interaction-state caveats without inflating a page above
  its actual task hierarchy.
- Evidence status:
  - TMWD managed tab workspace: `frontend-craft-l3-evals`.
  - Desktop viewport: 1512x823 CSS px, DPR 2, no horizontal overflow.
  - Mobile viewport: 390x844 CSS px, DPR 2, no horizontal overflow.
  - Screenshot artifacts: captured through TMWD `browser_screenshot_ops` as
    viewport and clip PNG files under
    `~/.tmwd-browser-mcp/runtime/runs/frontend-craft-l3-evals/`.
  - DOM/computed style: summarized in
    `evals/product-ui-taste/groland-content-assets-l3/dom-evidence.desktop.json`
    and
    `evals/product-ui-taste/groland-content-assets-l3/dom-evidence.mobile.json`.
  - Focus sample: `上传素材` button clip captured; computed outline was
    effectively absent, so evidence is recorded as partial rather than full
    keyboard validation.
- Eval path:
  `evals/product-ui-taste/groland-content-assets-l3/`
- Evidence level:
  L3 resilient evidence.
- Browser validation:
  claimed for desktop/mobile viewport fit, priority-area clip, and focused
  primary-button sample only.
- Screenshot validation:
  claimed only for the artifact path/hash/dimensions recorded in the eval case.
- Not verified:
  hover, loading, empty, error, success, permission state, full keyboard
  navigation, touch ergonomics beyond viewport fit, or before/after improvement.
