# Expected prototype plan

## Scope and boundary

- One UI piece: the post-search result-summary panel inside a desktop command
  palette.
- Exploration writes only an isolated prototype surface and local fixtures.
- Production palette files and shared primitives remain untouched until the
  user selects a direction.

## Direction contract

| Direction | Primary divergence axis | Product hypothesis | Invariants | Cost / risk |
| --- | --- | --- | --- | --- |
| Triage Queue | Interaction model: warning-first queue with progressive disclosure | Frequent users resolve risk faster when exceptional items lead and details open in place | Same results, actions, tokens, keyboard/focus, themes, long-path handling | Adds disclosure state and more keyboard destinations |
| Change Ledger | Information architecture: grouped file ledger with persistent summary | Users trust the operation when changes, skips, and warnings remain visible as one scannable record | Same results, actions, tokens, keyboard/focus, themes, long-path handling | Highest density and vertical cost |
| Guided Decision | Disclosure strategy: one recommended next step followed by inspectable evidence | Occasional users act with less hesitation when the panel sequences decision then proof | Same results, actions, tokens, keyboard/focus, themes, long-path handling | Hides detail one step deeper and must avoid over-directing experts |

The axes are interaction model, information architecture, and disclosure strategy.
They are not color, copy, icon, or decoration variants.

## Harness contract

- Use the project's framework-equivalent isolated preview surface; do not assume
  a fixed route, query string, picker CSS, or production wiring.
- Show one direction at full usable size in the same realistic command-palette
  context. Switching is immediate and keyboard operable.
- Every direction implements inspect, apply, dismiss, warning disclosure,
  visible focus, long paths, both themes, and Reduced Motion behavior.
- Use the same local fixture for all directions and make no remote or persistent
  writes.

## Stop condition

This plan stops before implementation. A completed runtime round would next
verify all three directions and finish `ready_for_selection`; production
promotion cannot start before explicit user selection or previously delegated
selection authority.
