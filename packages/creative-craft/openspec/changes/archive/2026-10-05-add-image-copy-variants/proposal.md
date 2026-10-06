# Apply shared copy to saved image layouts

## Why
The accepted next step is to edit copy once and export all three saved layouts. Historical revisions must remain immutable.

## What changes
Add `copy-variants <project> <input.json>`. Input names a new output directory, selected revision/digest pairs and shared text object updates. Each layout becomes a self-contained editable snapshot (r1), receives the same text-only edit (r2), and exports through the existing renderer. A manifest binds source revisions and output digests. All layouts must succeed; ordinary failure/cancellation removes only this invocation's new output. The source project is read-only. An existing destination is never replaced.

## Scope and authorization
User accepted this specific next step with “继续”. No dependencies, persistent source schema, model calls, global config, install or release changes. Snapshot histories start anew; source ancestry remains in the original project and is linked by digest. This is bounded local execution, not crash-atomic publication or protection against hostile concurrent filesystem replacement. Rollback is removal of this entry point; existing projects are unaffected.
