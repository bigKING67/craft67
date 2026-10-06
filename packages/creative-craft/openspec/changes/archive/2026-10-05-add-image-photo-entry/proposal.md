# Reusable photo project entry

## Why

The verified GROLAND workflow preserves a flat product photo, adds independent text, and supports revision-based edits and undo. Reusing it currently requires hand-authoring every canvas object or copying an asset-specific experiment.

## What Changes

- Add `create-photo <project> <brief.json> [--dry-run]` to the optional source-checkout image CLI. A project ID, absolute local photo path and headline create an ordinary editable image project; brand, caption, title and canvas dimensions are optional.
- Keep the entire opaque photo at native oriented dimensions, locked, below a fixed text header. Reject undersized canvases, transparency, missing glyphs and text overflow before publishing the project.
- Reuse raster import, font binding, document validation, creation and Satori layout. Dry-run produces a plan without file writes. Rendering and later editing use existing commands.
- Add focused regression tests, a short reusable guide/example, and a real-product pixel-preservation acceptance record.

## Impact

Only the optional `integrations/image-production` module and this proposal. No dependencies, canonical schema changes, model requests, global config, video changes, install, commit or push. This first recipe retains the whole photograph and its original background; asset-specific matting and border synthesis remain outside the entry.

## Authorization

2026-10-05: the user explicitly selected “继续打磨 image 工程：把验证过的流程整理成可复用入口（推荐）”. This records the accepted local implementation scope; ordinary implementation details do not introduce another approval step.
