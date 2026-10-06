# Frontend architecture quality

Use this for new features, cross-cutting UI changes, data-flow changes,
component systems, route shells, or major refactors.

## Architecture brief

Before implementation, lock:

- User/job outcome.
- Runtime entrypoint and route ownership.
- Data sources and trust boundaries.
- State ownership: server, URL, cache, local, global.
- Component boundary and composition model.
- API or prop contracts.
- Compatibility constraints.
- Migration and rollback path.

## Decision rules

- Prefer the project architecture already in use unless there is a concrete
  failure.
- Do not create a parallel framework inside a repo.
- Shared primitives require repeated use and the same intent.
- Abstract after observing repetition, not before.
- Keep page-specific report/dashboard logic near the page until a second real
  consumer exists.
- Avoid hidden fallback paths that make errors invisible.

## Interface design

- Inputs should be typed and validated at boundaries.
- Component props should represent product concepts, not CSS internals, unless
  the component is explicitly a primitive.
- Data adapters should be narrow and testable.
- Side effects should live in well-named boundaries.
- Long-running or async flows need cancellation, loading, and error semantics.

## Migration

For nontrivial changes:

- Identify old and new paths.
- Keep diffs scoped.
- Avoid mixing visual redesign with unrelated architecture cleanup.
- Preserve existing behavior unless the change explicitly intends to alter it.
- Provide a rollback path or small commits when possible.

## Architecture review output

Summarize:

- Chosen approach and rejected alternatives.
- Interfaces affected.
- Files/directories affected.
- Performance impact.
- Compatibility/migration risks.
- Validation path.
