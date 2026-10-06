# Product UI taste case: groland content assets L3

## Purpose

Use this case to calibrate resilient product UI taste scoring with real browser
evidence across desktop, mobile, and a focused interaction-state sample.

The page was sampled from a TMWD-owned managed Chrome tab on 2026-06-30. Binary
screenshots stay outside the repo under the TMWD runtime artifact directory.

## Surface

- Target: `http://localhost:3000/marketing/content-assets`
- Title: `Groland Datahub`
- Page type: material operations dashboard.
- Audience: internal material operators and admins.
- Primary job: identify the highest-priority material backlog and start the
  next operational action.
- Desired feel: calm, precise, data-dense, trustworthy, operational.

## Evidence level

L3 resilient browser evidence.

This case includes:

- Desktop viewport screenshot at 1512x823 CSS px, DPR 2.
- Mobile viewport screenshot at 390x844 CSS px, DPR 2.
- Desktop priority-area clip.
- Focus sample clip for the primary upload button.
- Redacted DOM/computed-style summaries for desktop and mobile.

This case does **not** verify:

- Hover state.
- Loading, empty, error, success, or permission states.
- End-to-end keyboard navigation.
- Before/after improvement.

Therefore it must not be treated as L4.

## Screenshot artifacts

| Target | Artifact | SHA-256 | Dimensions |
|---|---|---|---|
| desktop viewport | `~/.tmwd-browser-mcp/runtime/runs/frontend-craft-l3-evals/20260630T091051331Z-9a95dc49/artifacts/screenshot-viewport-groland-content-assets-l3-desktop-20260630T091051332Z-2bff25ca.png` | `6c05a3c171460bf65a2132fbbe4709085d2c46fda59f0c7a5decf68b9544476a` | 3024x1646 |
| desktop priority clip | `~/.tmwd-browser-mcp/runtime/runs/frontend-craft-l3-evals/20260630T091104898Z-0b61639e/artifacts/screenshot-clip-groland-content-assets-l3-desktop-priority-clip-20260630T091104898Z-1c820202.png` | `0060f55209e9c49addcdfaf24e46b4b555e7c541e3874b6e0e9ca3934e639a59` | 2420x1220 |
| mobile viewport | `~/.tmwd-browser-mcp/runtime/runs/frontend-craft-l3-evals/20260630T091216314Z-4fc9569c/artifacts/screenshot-viewport-groland-content-assets-l3-mobile-20260630T091216314Z-73a01893.png` | `8ac950915841ce88450072ae224913f7f2dafd276b86ba1fc87b79f5cb8a3091` | 780x1688 |
| focused upload button clip | `~/.tmwd-browser-mcp/runtime/runs/frontend-craft-l3-evals/20260630T091256421Z-8362ee48/artifacts/screenshot-clip-groland-content-assets-l3-focus-clip-20260630T091256422Z-28e6e537.png` | `871235d5420d12c45e502c21248aa08379583c7007669be2a2d3d17e3f2edede` | 500x140 |

## Browser evidence summary

- Desktop viewport: 1512x823 CSS px, DPR 2, no horizontal overflow.
- Mobile viewport: 390x844 CSS px, DPR 2, no horizontal overflow.
- Mobile layout adapts to a top module select, search row, action row, hero
  card, two-column metric grid, then full-width metric cards.
- The desktop priority clip shows the hero and all first-screen metrics, but
  backlog, ready, capacity, failure, and authorization states still use very
  similar card treatment.
- Focus sample on `上传素材` is partial: computed outline is `none`; visible
  feedback is mostly the primary button border/shadow.

## Expected judgment

The page deserves credit for responsive fit and real browser polish, but it
must stay at the top of the clean-but-generic band while the main task hierarchy
is still flat and interaction-state evidence is partial.

Do not inflate the score above 84 until the highest-risk backlog becomes a
priority queue and focus-visible treatment is explicitly designed.
