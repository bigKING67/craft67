# Validation

## Commands

From `$DATAHUB_REPO`:

```bash
git diff --check -- src/app/content/live-center/_components/live-center-session-detail.tsx src/app/content/live-center/live-center.module.css
npm run -s type-check
npm run verify:frontend:preflight
npm run -s lint
npm run -s build
npm run verify:design:typography
npm run verify:design:raw-colors
npm run verify:repo:trellis-spec-compact
```

From `$DESIGN_CRAFT_HOME`:

```bash
python3 scripts/design_craft_css_smell_scan.py --target $DATAHUB_REPO/src/app/content/live-center --json
python3 scripts/design_craft_token_audit.py --target $DATAHUB_REPO/src/app/content/live-center --json
python3 scripts/design_craft_focus_audit.py --target $DATAHUB_REPO/src/app/content/live-center --json
python3 scripts/design_craft_browser_evidence.py --validate-score-json evals/product-ui-taste/before-after/datahub-live-center-review-workbench/score.before.json
python3 scripts/design_craft_browser_evidence.py --validate-score-json evals/product-ui-taste/before-after/datahub-live-center-review-workbench/score.after.json
bash scripts/validate.sh
```

## Command results

- `git diff --check`: passed.
- `npm run -s type-check`: passed.
- `npm run verify:frontend:preflight`: passed with vendor manifest/snapshot cache hit `158a8535f828`.
- `npm run -s lint`: passed.
- `npm run -s build`: passed; Vite built successfully and wrote `apps/web-vite/dist/datahub-build-manifest.json`.
- `npm run verify:design:typography`: passed; CSS Modules use font-family and typography tokens.
- `npm run verify:design:raw-colors`: passed; no non-material raw colors found.
- `npm run verify:repo:trellis-spec-compact`: passed.
- `design_craft_css_smell_scan.py`: 8 findings, all review signals. The medium findings are fixed-width/media-query review prompts; browser evidence verifies no page-level overflow.
- `design_craft_token_audit.py`: 3 info findings around shadow/inset rail usage; no hard failure.
- `design_craft_focus_audit.py`: 5 coarse file-level focus prompts; desktop browser evidence verifies selected row focus-visible. Ant Design controls retain project-level focus behavior.
- Score JSON validation: both before and after passed.
- `bash scripts/validate.sh`: passed; skill quick validation and design-craft validation passed.

## Browser validation

### Before

- Desktop TMWD viewport: 1512x823 DPR 2.
  - Final URL: `http://127.0.0.1:3000/content/live-center`.
  - `h1`: present.
  - Page-level horizontal overflow: 0.
  - Workbench: two-column, y=481.
  - Selected row count: 1.
  - Focus-visible: selected row outline `rgb(47, 110, 234) solid 2px`.
- Mobile headless Chrome viewport: 390x844 DPR 2.
  - Final URL: `http://127.0.0.1:3000/content/live-center`.
  - Page-level horizontal overflow: 0.
  - Workbench y=1008, not in first viewport.
  - Header/command/filter heights: 526/298/307.

### After

- Desktop TMWD viewport: 1512x823 DPR 2.
  - Final URL: `http://127.0.0.1:3000/content/live-center`.
  - `h1`: present.
  - Page-level horizontal overflow: 0.
  - Workbench: two-column, y=449.
  - Selected row count: 1.
  - Focus-visible: selected row outline `rgb(47, 110, 234) solid 2px`.
  - Screenshot: `~/.tmwd-browser-mcp/runtime/runs/datahub-live-center-l4/20260630T145222425Z-ec2814d7/artifacts/screenshot-viewport-datahub-live-center-after-desktop-20260630T145222428Z-a6b69728.png`
- Mobile headless Chrome viewport: 390x844 DPR 2.
  - Final URL: `http://127.0.0.1:3000/content/live-center`.
  - Page-level horizontal overflow: 0.
  - Workbench y=777, in first viewport.
  - Header/command/filter heights: 338/163/264.
  - Screenshot: `~/.tmwd-browser-mcp/runtime/runs/datahub-live-center-l4/20260630T145400Z-headless-after-mobile/artifacts/screenshot-viewport-datahub-live-center-after-mobile-headless-chrome.png`

## Result

L4 before/after evidence supports a score change from 86 to 91.

The improvement is real but bounded: hierarchy and mobile priority improved materially, while state coverage remains partial and table-local horizontal scrolling remains intentional.

## Not verified

- Real upload flow with a local video file.
- Forced empty/error states after the change.
- Active AI-running state after the change.
- Full keyboard traversal across all controls.
