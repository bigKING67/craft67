- [x] Implement bounded text-only variants and CLI entry using existing edit/render checks.
- [x] Verify identical shared copy, distinct layout preservation, editable outputs and source immutability.
- [x] Verify failure cleanup, stale bindings, locked/missing objects, existing destination and cancellation.
- [x] Exercise all three real GROLAND layouts and document evidence and usage.

Evidence: `dist/image-copy-variants-2026-10-05/README.md`; 94/94 image tests and strict change validation passed. Real CLI exports retain all product pixels and change only headline boxes across three layouts.
