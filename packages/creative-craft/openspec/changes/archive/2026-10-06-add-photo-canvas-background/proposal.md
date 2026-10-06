# Photo canvas background and edge report

## Why

Real-material acceptance (GROLAND, CHANEL) showed that a photo's own backdrop leaves a visible box when the canvas color differs. Fixing it required a follow-up `set_canvas` edit, and callers had no measured basis for choosing the color.

## What Changes

- Optional `background: "#RRGGBB"` in the `create-photo` brief for default and template layouts; defaults unchanged (`#ffffff`, templates `#f5f2eb`).
- `layout.photo_edges` reports mean color and max channel spread of each one-pixel photo border in dry-run and create results. Nothing is sampled or applied automatically and no photo pixels are extended.

## Impact

`integrations/image-production` photo entry and docs; one sentence in the Skill image reference. Existing briefs and projects unchanged.
