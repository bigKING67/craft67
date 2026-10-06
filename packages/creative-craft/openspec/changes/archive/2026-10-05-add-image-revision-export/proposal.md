# Export historical image layouts through the CLI

## Why
The verified multi-size workflow retains each layout in project revisions. The rendering API already supports a selected revision, but the CLI only exports the current revision. Re-exporting a saved layout should not require changing the active document or its locks.

## What changes
Expose the existing read-only renderer option as `render|preview <project> <new-output> --revision <positive-integer>`. Omission keeps current-revision behavior. Reject malformed, nonexistent or extra arguments before output creation. Preserve the selected revision and digest in the existing receipt.

## Scope
Continues the authorized image-only reusable workflow improvement. CLI, tests and related guidance only; no renderer/schema/dependency changes, model calls, install or release. Removing the optional flag restores the previous CLI; stored projects are unchanged.
