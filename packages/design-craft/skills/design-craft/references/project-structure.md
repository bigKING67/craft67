# Project structure governance

Use this before adding, moving, deleting, or extracting frontend files.

## Inspect before creating

Run focused discovery first:

- `git status --short`
- `rg --files`
- README / `AGENTS.md`
- package scripts and framework config
- existing similar components, routes, styles, tests, and utilities

Do not ask where a file should live until the repo structure has been inspected.

## Directory rules

- Avoid generic folders: `utils`, `helpers`, `common`, `misc`, `temp`, `new`,
  `final`, `components-new`.
- Do not create parallel structures with the same responsibility.
- Place domain code near the domain.
- Shared code needs at least two real call sites with the same intent.
- Generated artifacts, logs, screenshots, coverage, caches, and dumps must not
  be mixed into source directories.
- Temporary files belong in `/tmp` or the repo's established temp location and
  should be cleaned before delivery.

## Naming rules

- File names should describe responsibility, not history.
- Avoid `newApi.ts`, `finalFix.ts`, `temp2.ts`, `utils.ts`, `helpers.ts`.
- Follow the repo's casing and extension conventions.
- Do not mix synonymous layers such as `service/services` or
  `api/client/request` unless the repo already does.

## Extraction threshold

Extract only when:

- The pattern repeats in at least two places for project code, or three places
  for design-system primitives.
- Intent matches, not just visual similarity.
- The extraction simplifies callers.
- Migration happens in the same scoped change.

## Delivery

When structure changes, report:

- Why the new path exists.
- What responsibility it owns.
- Why existing paths were not sufficient.
- Any migration or cleanup left intentionally out of scope.
