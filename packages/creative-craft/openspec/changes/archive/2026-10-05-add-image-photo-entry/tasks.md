## Implementation and acceptance

- [x] Add validated native-size photo layout and `create-photo` with read-only dry-run.
- [x] Reuse existing publication and text layout checks without changing ordinary create/edit behavior.
- [x] Document a minimal brief, prerequisites, create/render/edit/undo commands and limits.
- [x] Verify CLI rejection/no-write behavior, exact pixels, original-byte retention and ordinary project roundtrips.
- [x] Run the image module regression suite and strict OpenSpec validation.
- [x] Create and inspect a fresh GROLAND project through the public entry; record exact source-region comparison and remaining visual limits.

Evidence: `dist/image-photo-entry-2026-10-05-b3ac4b47/README.md`. Local module tests: 84/84 pass (6 new recipe cases). OpenSpec strict validation passes using the already-cached CLI; no installation. Actual source photograph: 1,572,516 normalized RGBA pixels unchanged in initial, text-edited and restored exports. This is a starter layout with a visible original-photo boundary, not formal creative approval.
