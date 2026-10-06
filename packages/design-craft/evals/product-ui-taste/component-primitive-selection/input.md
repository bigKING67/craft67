# Component primitive selection fixture

This is a project-neutral textual fixture. It contains three independent
architecture decisions and no hidden preference for a component library.

## Scenario A: existing Radix project

An established React product uses Radix UI through shared project wrappers.
A compact toolbar action was locally restyled and now disagrees with sibling
actions in default, focus-visible, and Dark-theme states. No keyboard, focus,
overlay, SSR, performance, or maintenance blocker has been observed in Radix.
The request is to fix the visual-language regression.

## Scenario B: new project without authority

A new React product has no primitive dependency or architecture decision. It
needs dialog, menu, combobox, and tooltip behavior with keyboard support, SSR,
Reduced Motion, a bounded bundle, and long-term maintenance. The available
evidence does not yet compare relevant Base UI, Radix UI, React Aria, or other
candidate versions in this product stack.

## Scenario C: existing Base UI project

An established product already imports Base UI through project wrappers. A
trigger-anchored popover scales from the center even though the installed Base
UI version exposes origin/positioning data. The task is to correct motion while
preserving the project's tokens, focus behavior, dismissal behavior, and
Reduced Motion contract.

For each scenario, record authority, `keep | adopt | migrate | defer`, the
decisive evidence, visual-system impact, and the next implementation boundary.
