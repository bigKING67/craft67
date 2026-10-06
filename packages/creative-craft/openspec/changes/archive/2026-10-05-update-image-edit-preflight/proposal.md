# Check text fit before publishing image edits

## Why
The reusable photo entry validates text layout before creation, but ordinary edits can currently pass dry-run and publish an overflowing title. Export then fails, leaving the latest revision unusable. This continues the approved image workflow improvement scope.

## What changes
- Reuse the existing render text measurement for edit dry-run and publication, after the complete batch and before asset/revision writes.
- Check visible text; reject overflow and text boxes narrower than a glyph. Keep explicit unlock-only operations available to repair locked legacy layouts.
- Preserve render-time checks, general `create` compatibility, revision/lock contracts and exact approved copy. No new dependencies, schema, model calls or automatic text resizing.
- Update the workflow guide and Skill reference; verify rejection, recovery and an actual GROLAND CLI edit/undo flow.

## Impact
Image executor and its tests/docs only. Rollback restores the prior edit behavior; stored document format is unchanged. No install, release or global configuration changes.
