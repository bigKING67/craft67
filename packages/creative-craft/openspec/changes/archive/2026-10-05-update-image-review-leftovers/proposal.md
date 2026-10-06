# Image production review leftovers

## Why

Remaining review findings: macOS temp paths (`/tmp`, `/var`) were rejected as symlinks; a revision conflict found just before the Provider POST permanently consumed the job ID although nothing was sent; adapter models/profile dates were hard-coded beside the provider profiles; CLI `read` accepted non-decimal revisions and module-load failures were not JSON; the revision cap failed with a vague message.

## What Changes

- Resolve OS-owned aliases directly under the filesystem root before the per-component symlink check.
- Delete the job directory and release the claim when a run fails with zero client POST attempts.
- Derive adapter models from `providers/*.json` profiles that enable the optional adapter.
- Strict decimal revision for `read`; CLI loads modules inside its JSON error handler; explicit revision-limit error.

## Impact

`integrations/image-production` only. No schema, dependency or package change.
