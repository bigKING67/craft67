# System consistency toolbar golden input

This is a project-neutral textual fixture. It contains no product screenshot,
runtime claim, private path, or project-specific data.

## Review task

Review the compact toolbar as a known visual-language consistency regression.
Use the full `system-review` contract, do not assign a numeric taste score, and
finish with `pass`, `blocked`, or `incomplete`.

## Scope and authority

- Scope: one workbench toolbar and its shared compact-utility-action family.
- Style authority: compact utility actions use the shared 32 x 32 rounded-rect
  ghost shell, 6px radius, semantic border/overlay tokens, a centered 16px
  icon, visible focus, and the same state timing in both themes.
- Intentional exception: the row-selection checkbox is a separate semantic
  family. It does not need the action fill, but it shares the toolbar's target
  alignment and focus visibility.
- Contained accent treatment is reserved for a labeled primary action, not an
  icon-only utility action.

## Supplied observations

Treat these observations as fixture facts for contract testing, not as evidence
that a real browser or host-agent review ran.

| Control | Semantic role | Default | Hover / pressed | Focus | Theme evidence |
| --- | --- | --- | --- | --- | --- |
| Select rows | selection control | 32px aligned target with native checkbox indicator | authority-consistent | visible | Light only |
| Filter | compact utility action | 32px ghost, 6px radius, 16px icon | shared overlay tokens | visible | Light only |
| Add item | compact utility action | 28px contained circle with accent fill | scale-only pressed state | no visible focus | Light only |
| Refresh | compact utility action | 32px ghost, 2px radius, 14px icon | different hover duration | visible | Light only |

No Dark-theme rendering is supplied. Target-size and default border/background
assertions pass for the toolbar as a whole.
