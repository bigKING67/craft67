# Frontend architecture evaluation spec

## Prompt

Use `design-craft` to review or implement a frontend architecture change:
route ownership, data adapters, component boundaries, state ownership, and file
layout must remain coherent and maintainable.

## Expected route behavior

- `surface`: `app`, `admin`, `dashboard`, or `data-app`
- `intent`: `functional`
- `scope`: `page` or `multi-page`
- `directory_governance_required`: `true`
- `performance_review_required`: depends on data/render path

## Expected design-craft references

- `references/architecture-quality.md`
- `references/engineering-quality.md`
- `references/project-structure.md`
- `references/performance-quality.md` when hot paths are affected
- `references/validation-contract.md`

## Success behavior

- Identifies runtime entrypoint, route ownership, data sources, trust
  boundaries, state ownership, API/prop contracts, migration, and rollback.
- Preserves existing architecture unless a concrete failure justifies change.
- Avoids parallel source trees, generic utility folders, and premature shared
  abstractions.
- Reports changed interfaces and validation path.

## Failure modes

- Mixes visual redesign with unrelated architecture cleanup.
- Uses non-enum route values such as `--intent architecture` or a prose
  `--scope` string.
- Creates a new framework inside the repo.
- Hides errors behind silent fallback paths.
- Claims performance improvement without baseline or hot-path reasoning.
