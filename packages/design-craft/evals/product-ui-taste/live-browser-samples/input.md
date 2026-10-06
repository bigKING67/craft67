# Product UI taste case: live browser samples

## Purpose

Use this grouped case to calibrate product UI taste scores with real browser
evidence, not only static screenshot descriptions.

The pages were sampled from the user's already-open Chrome tabs on 2026-06-30
with TMWD in read-only mode. Sensitive or personal tabs were skipped.

## Scope

Selected tabs:

- `http://127.0.0.1:8317/management.html#/quota`
  - Title: `CLI Proxy API Management Center`
  - Case: `cpa-management-quota`
- `http://127.0.0.1:8080/`
  - Title: `CPA USAGE KEEPER`
  - Case: `cpa-usage-keeper`
- `http://localhost:3000/`
  - Title: `Groland Datahub`
  - Case: `groland-datahub-home`
- `http://localhost:3000/marketing/content-assets`
  - Title: `Groland Datahub`
  - Case: `groland-content-assets-live`

Skipped tabs:

- `console.volcengine.com/finance/saving-plan`: finance console; skipped as
  sensitive for UI calibration.
- `chatgpt.com/...`: private conversation; skipped.

## Evidence level

L2 browser evidence.

This case includes:

- TMWD browser transport health.
- Current Chrome tab list.
- Viewport PNG screenshot artifacts produced by TMWD `browser_screenshot_ops`
  (`Page.captureScreenshot`) outside the repo.
- DOM and computed-style sampling for body, headings, controls, and surfaces.

This case does **not** verify:

- Mobile layout.
- Hover, focus, selected, loading, empty, error, success, keyboard, or touch
  states.
- Before/after improvement.

Therefore it must not be treated as L3 or L4.

## Screenshot artifact policy

Binary screenshots are intentionally not committed. The artifacts are stored
under `~/.tmwd-browser-mcp/runtime/runs/frontend-craft-live-evals/` and carry
TTL metadata. The eval records path, hash, dimensions, and visual summary so the
case remains useful after artifact expiry.

## Evidence artifacts

| Case | Target | Artifact | SHA-256 | Dimensions |
|---|---|---|---|---|
| `cpa-management-quota` | viewport | `~/.tmwd-browser-mcp/runtime/runs/frontend-craft-live-evals/20260630T085647879Z-35aaccd5/artifacts/screenshot-viewport-cpa-management-quota-20260630T085647881Z-6aaf31e6.png` | `0b306daf2d8a335472642a78f21a736fd6c83cfb68f28fbfb54e23813f6e198c` | 3024x1646 |
| `cpa-usage-keeper` | viewport | `~/.tmwd-browser-mcp/runtime/runs/frontend-craft-live-evals/20260630T085713075Z-5b2bd89c/artifacts/screenshot-viewport-cpa-usage-keeper-20260630T085713077Z-7cebc462.png` | `bf0800788469cb0d60a6dbb163f0b74bad67e1ce3e2f32ab0d062e4cf13f453c` | 3024x1646 |
| `groland-datahub-home` | viewport | `~/.tmwd-browser-mcp/runtime/runs/frontend-craft-live-evals/20260630T085751470Z-41920ff3/artifacts/screenshot-viewport-groland-datahub-home-20260630T085751470Z-673a26a8.png` | `316ecd4221d81797a22e0d70cacf9a13f3d8e561ee02ea60600cb1e770570e82` | 3024x1646 |
| `groland-content-assets-live` | viewport | `~/.tmwd-browser-mcp/runtime/runs/frontend-craft-live-evals/20260630T085800644Z-b8f5c653/artifacts/screenshot-viewport-groland-content-assets-20260630T085800645Z-81bf45a2.png` | `6c05a3c171460bf65a2132fbbe4709085d2c46fda59f0c7a5decf68b9544476a` | 3024x1646 |

## Browser / DOM evidence summary

### cpa-management-quota

- Dark admin quota surface with a fixed left navigation and a quota detail card.
- Viewport: 1512x823 CSS px, DPR 2.
- Body computed style: dark canvas around `rgb(21, 20, 18)`, light text.
- Main issue visible in browser: the quota card uses strong visual polish, but
  the main content area leaves a large empty right side and high quota usage is
  still shown as green progress, weakening risk semantics.

### cpa-usage-keeper

- Dark analytics dashboard with header controls, tab chips, filter controls,
  metric cards, and sparklines.
- Viewport: 1512x823 CSS px, DPR 2.
- Body computed style: dark canvas around `rgb(21, 20, 18)`, light text.
- Sample cards use 12px radius, elevated dark surfaces, and large numeric
  values.
- Main issue visible in browser: strong metric hierarchy and visual identity,
  but heavy card treatment and low-contrast secondary labels can make the dense
  dashboard feel slightly theatrical.

### groland-datahub-home

- Light enterprise data hub home page with top navigation, hero, CTAs, feature
  panel, and capability cards.
- Viewport: 1512x823 CSS px, DPR 2.
- Body computed style: neutral canvas around `rgb(245, 245, 245)`, system UI
  font, 48px hero heading.
- Main issue visible in browser: clear and polished, but the first screen reads
  more like a generic product gateway than a sharp operational control surface.

### groland-content-assets-live

- Light material-operations dashboard with left sidebar, search/CTA bar, hero,
  metric grid, checklist, and next-action panel.
- Viewport: 1512x823 CSS px, DPR 2.
- Body computed style: neutral canvas around `rgb(245, 245, 245)`, system UI
  font, 30px page heading.
- Main issue visible in browser: clean alignment and real data, but twelve
  metric tiles still give backlog, risk, completion, and capacity too similar a
  visual role.
