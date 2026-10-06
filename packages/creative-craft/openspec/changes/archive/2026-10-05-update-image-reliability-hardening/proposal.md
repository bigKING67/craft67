# Image production reliability hardening

## Why

A review of the optional image module found paths that could lose a paid Provider result, corrupt a project through an output directory placed inside it, reject large but valid photos, and leave unrecoverable candidate state after a killed process.

## What Changes

- Persist an unvalidated receipt when post-request validation fails; `provider-recover` validates and promotes it and stages the retained output without another request. Late timeout/cancel after a complete response no longer discards the result.
- Refuse render/preview/copy-variants/compare outputs inside the project by directory identity, not path text.
- Bound normalized render rasters by a shared `renderBytes` limit instead of the 20 MB source limit.
- Report damaged candidate entries in `candidate-list`; add explicit, audited `candidate-unlock`; report interrupted creates as incomplete.
- fsync written files and their directory in the shared content store.
- Explicit Python version failure, `CREATIVE_CRAFT_PYTHON`, and rejection of code fences in compiled job text.
- QA accuracy: independent crop slicing, decoded-pixel (encoding-only) no-change check for replacements, documented text-fit basis; render encodes only drawn rasters.

## Impact

`integrations/image-production` and the shared `integrations/local-production/content-store.mjs` (fsync only). No canonical schema, dependency or Skill package change. Existing projects and receipts remain readable; creating into an existing directory now fails with `Project already exists` before importing assets.
