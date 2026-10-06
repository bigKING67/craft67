# Expected component primitive decisions

## Scenario A

- `current_library`: `Radix UI`
- `authority_source`: package, source, and project wrappers
- `decision`: `keep`
- `migration_cost`: `not_applicable`
- `visual_system_impact`: `localized` unless the shared-family inventory proves
  a wider regression
- Required action: repair the shared compact-action component, variant, tokens,
  focus-visible state, and Dark-theme parity; run the system-consistency
  closeout against sibling same-state exemplars.
- Rejected action: do not propose a Base UI migration from a visual mismatch
  when no primitive-level blocker is confirmed.

## Scenario B

- `current_library`: `none`
- `authority_source`: `none`
- `decision`: `defer`
- Required action: compare the relevant candidate versions for semantic/ARIA
  coverage, keyboard/focus, overlay/portal, forms, SSR/hydration, animation
  hooks, bundle/performance, maintenance, and wrapper cost.
- Base UI is an allowed `adopt` result if project-specific evidence supports it;
  it is not the predetermined answer.
- The decision may move from `defer` to `adopt` only after the missing evidence
  is recorded.

## Scenario C

- `current_library`: `Base UI`
- `authority_source`: package, source, and project wrappers
- `decision`: `keep`
- `visual_system_impact`: `localized`
- Required action: use the installed Base UI version's real origin/positioning
  contract through the project wrapper, preserve project tokens, and verify
  focus, dismissal, keyboard, Reduced Motion, and rendered origin behavior.
- Rejected action: do not replace project authority with copied demo CSS or
  generic pseudo-attributes.

## Cross-scenario verdict

Primitive-library consistency cannot substitute for visual-system consistency.
Library installation, shared imports, or a preferred-library recommendation is
not visual acceptance and cannot independently justify migration or sign-off.
