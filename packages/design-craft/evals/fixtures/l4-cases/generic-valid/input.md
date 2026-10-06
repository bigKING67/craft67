# Generic L4 before/after eval fixture

## Context

- Case ID: generic-l4-valid
- Product surface: local review workbench
- Primary user: product reviewer
- Primary job: compare whether a UI polish pass made the decision surface easier to scan
- Design read: compact hierarchy, clearer primary work area, and documented evidence boundaries

## Before evidence

| Artifact | Path | SHA-256 | Dimensions |
|---|---|---|---|
| before desktop viewport | /tmp/design-craft-generic-before-desktop.png | aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa | 1440 x 900 |

## After evidence

| Artifact | Path | SHA-256 | Dimensions |
|---|---|---|---|
| after desktop viewport | /tmp/design-craft-generic-after-desktop.png | bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb | 1440 x 900 |

## Runtime evidence

- Browser target: local generic fixture route
- Viewports: desktop and mobile metadata recorded in score files
- Interaction states: focus and empty-state boundaries recorded as explicit state checks
- DOM/computed-style evidence: represented by fixture layout metrics, not a live product claim

## Not verified

- This fixture is synthetic and exists only to validate the case-directory schema.
