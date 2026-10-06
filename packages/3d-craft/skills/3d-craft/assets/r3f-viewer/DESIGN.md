# 3D-Craft Viewer visual authority

## Design read

An evidence-oriented 3D inspection bench for Agent developers and 3D engineers,
with a calm editorial-industrial tone, optimized for verifying one asset and
its runtime status without competing with the model.

## Principles

- The 3D object is the visual subject; interface chrome stays quiet.
- Use warm neutral surfaces, dark graphite type, one restrained safety-orange
  accent, and no gradients or decorative glass effects.
- Present asset identity, ready/error state, renderer facts, and interaction
  help as readable instrumentation rather than a dashboard wall.
- Desktop is a two-region composition: a narrow evidence rail and a large
  canvas. Mobile stacks the summary above a viewport that remains useful.
- Loading, ready, interrupted, restoring, and error are first-class authored
  states. A lost GPU context must never leave the interface claiming `ready`.

## Typography

- Use the system sans stack for interface prose and `ui-monospace` for asset
  measurements, counters, hashes, and status values.
- Keep the title compact and sentence case; do not use oversized marketing
  typography.

## Color

- canvas: `#e9e7e1`
- panel: `#f6f4ee`
- ink: `#171816`
- muted: `#676960`
- line: `#c9c8c0`
- accent: `#e45c2a`
- success: `#2e7554`
- danger: `#b53d32`
- radius: 2px for panels, pill radius only for status labels

## Components

- Evidence rail: title, concise brief, lifecycle status, and metric rows.
- Canvas viewport: the asset, a subtle floor grid, and a reset-camera control.
- Status label: always pairs color with readable `loading`, `ready`,
  `context-lost`, `restoring`, or `error` copy.
- Recovery notice: uses the existing safety-orange role, pauses camera controls,
  and remains visually secondary to the asset when rendering is healthy.
- Diagnostic notice: displays the asset URL and observable error without
  covering the entire viewport.

## Motion and interaction

- State transitions run for 160–220ms; there is no ambient UI animation.
- Canvas accepts pointer orbit and wheel zoom; a reset-camera control is
  keyboard accessible.
- Respect `prefers-reduced-motion`; disable automatic model drift when set.

## Layout and responsive behavior

- Minimum interactive target: 44 CSS pixels.
- Keep status copy visible without hover. Focus rings use the accent color.
- At widths below 720px, stack content and keep the canvas at least 52svh.
- Never hide runtime errors behind an empty canvas. Show a concise error and the
  asset URL while retaining diagnostic details in the console contract.

## Acceptance

The final sample must be captured from a visible browser67-managed tab after
the observability contract reports `ready` and RAF progress. A stale capture or
DOM/3D disagreement is not valid visual evidence.
