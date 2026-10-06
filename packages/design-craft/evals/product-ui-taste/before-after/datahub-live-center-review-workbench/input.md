# DataHub live center review workbench

## Context

- Case ID: `datahub-live-center-review-workbench`
- Product surface: DataHub `/content/live-center`
- Product repo: `$DATAHUB_REPO`
- Primary user: content operations and ecommerce operators reviewing livestream evidence.
- Primary job: select the next livestream session, see evidence readiness, fill recording gaps, inspect minute-level order trend, and trigger/track AI analysis.
- Design read: live review operations workbench for content/ecommerce operators, with restrained DataHub enterprise-console language, optimized for closing livestream evidence gaps.
- Style authority: `$DATAHUB_REPO/DESIGN.md`, enforce mode.

`DATAHUB_REPO` and `DESIGN_CRAFT_HOME` are public, machine-neutral aliases for
the original local checkouts. `~` paths preserve historical artifact locations
without publishing the workstation username.

## Before evidence

| Artifact | Path | SHA-256 | Dimensions | Viewport |
|---|---|---|---:|---|
| before desktop viewport | `~/.tmwd-browser-mcp/runtime/runs/datahub-live-center-l4/20260630T143721691Z-ce83d279/artifacts/screenshot-viewport-datahub-live-center-before-desktop-20260630T143721693Z-014d4baf.png` | `a79713c06d20b7ab77e759a0b8175468e3259b7b45d84cdb1f659b1ce5e73a98` | 3024x1638 | 1512x823 DPR 2 |
| before mobile viewport | `~/.tmwd-browser-mcp/runtime/runs/datahub-live-center-l4/20260630T144317Z-headless-before-mobile/artifacts/screenshot-viewport-datahub-live-center-before-mobile-headless-chrome.png` | `119653d0bbcb7634a853678d2204723238742c50907906923637b3de0ce79c1f` | 780x1688 | 390x844 DPR 2 |

## After evidence

| Artifact | Path | SHA-256 | Dimensions | Viewport |
|---|---|---|---:|---|
| after desktop viewport | `~/.tmwd-browser-mcp/runtime/runs/datahub-live-center-l4/20260630T145222425Z-ec2814d7/artifacts/screenshot-viewport-datahub-live-center-after-desktop-20260630T145222428Z-a6b69728.png` | `85a78e25e470e3ef1810f52064badf3e206b14f4651657c587a8171269310a67` | 3024x1638 | 1512x823 DPR 2 |
| after mobile viewport | `~/.tmwd-browser-mcp/runtime/runs/datahub-live-center-l4/20260630T145400Z-headless-after-mobile/artifacts/screenshot-viewport-datahub-live-center-after-mobile-headless-chrome.png` | `0970600b90780d1145989557b127ecb010479039379b89c52ba106ad27718142` | 780x1688 | 390x844 DPR 2 |

## Runtime evidence

- Browser target: `http://127.0.0.1:3000/content/live-center`
- Desktop tool: `tmwd_browser.browser_screenshot_ops` on TMWD-managed tab `1903720565`.
- Mobile tool: independent `Google Chrome --headless=new` CDP run with 390x844 DPR 2 viewport and repo-external login env.
- Before desktop: no page-level horizontal overflow; workbench two-column; workbench starts at y=481; selected row count 1; selected row focus outline is 2px brand blue.
- Before mobile: no page-level horizontal overflow; workbench starts at y=1008 and is not in the first viewport; header/command/filter consume the mobile first screen.
- After desktop: no page-level horizontal overflow; workbench two-column; workbench starts at y=449; readiness strip appears before metrics in the detail panel; selected row focus outline remains 2px brand blue.
- After mobile: no page-level horizontal overflow; workbench starts at y=777 and appears in the first viewport; header, command strip, and filter panel are materially shorter.

## Not verified

- Uploading a real recording file was not exercised.
- Empty, error, and active AI-running states were not exhaustively forced after the visual polish.
- Keyboard traversal beyond the selected table-row focus check was not exhaustively walked.
