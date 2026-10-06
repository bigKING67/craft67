# Design system contract

Use this when a project has a `DESIGN.md`, design tokens, theme files,
CSS variables, Tailwind theme values, reusable UI components, light/dark mode,
or when the task changes visual foundations rather than one isolated style.

If the project also has `PRODUCT.md`, keep its product/platform/user facts
separate. `DESIGN.md` remains the visual authority; see
`product-context.md` for the boundary.

This reference is about system discipline, not a specific aesthetic. It should
help preserve the product's own visual language instead of making every project
look like one upstream design system.

## Contents

- [Default seed](#default-seed)
- [Authority](#authority)
- [Recommended DESIGN.md shape](#recommended-designmd-shape)
- [Token layers](#token-layers)
- [Theme parity](#theme-parity)
- [Typography roles](#typography-roles)
- [Layout rhythm](#layout-rhythm)
- [Component state matrix](#component-state-matrix)
- [Motion](#motion)
- [Voice and content](#voice-and-content)
- [Audit checklist](#audit-checklist)

## Default seed

For a new project or a weakly specified developer-product surface, start from
the bundled original design-craft templates:

- `templates/developer-product/design.md`
- `templates/developer-product/design.dark.md`

Use them as the default initial `DESIGN.md` pair for SaaS, dashboard, admin,
infra, docs, tooling, and other developer-facing product surfaces. If the
project already has a credible `DESIGN.md`, token system, brand guide, or strong
runtime style, keep the project authority first and use the seed templates as a
comparison baseline for missing token layers, states, focus, motion, and copy.

Use `scripts/design_craft_seed_design.sh --target <project-dir>` when the
right move is to create the initial pair directly. The helper refuses to
overwrite existing `DESIGN.md` or `DESIGN.dark.md` unless `--force` is explicit.

## Authority

- Live runtime behavior and scoped project rules outrank this reference.
- `PRODUCT.md` governs product intent, platform, users, positioning, and
  accessibility requirements. `DESIGN.md` governs visual/tokens/components.
- Implemented tokens and shared components are evidence. If docs and code
  conflict, verify the current runtime before deciding whether docs are stale.
- Do not create a parallel style authority. Evolve the existing one when the
  user approves a system change.
- The bundled developer-product templates are allowed as the default seed when no stronger
  project style authority exists. Once a project-specific system exists, prefer
  adapting it over repeatedly re-applying the seed.
- If `design_craft_route.sh` reports `developer_product_seed_applicable: true`,
  treat that as a prompt to create or compare against the seed, not as
  permission to ignore live runtime style.

## Recommended DESIGN.md shape

A strong `DESIGN.md` is both machine-readable and readable by agents. It does
not need to repeat the `PRODUCT.md` audience, purpose, or platform contract:

- Front matter or a structured block for tokens:
  - colors
  - typography
  - spacing
  - radii
  - elevation
  - motion
  - component variants
- Platform-specific token mappings when native platforms intentionally resolve
  one semantic role differently, such as system materials or elevation.
- Markdown rationale for:
  - product feel and audience
  - color semantics
  - typography roles
  - layout rhythm
  - component behavior
  - motion policy
  - voice and content rules
  - do and don't rules

Light and dark themes should use identical semantic token names with different
values. Components should consume semantic tokens, not branch on
theme-specific literal colors. Native implementations may map a shared
semantic role to iOS system colors/materials or Material color/elevation roles;
shared names do not require identical platform values.

## Token layers

Keep token roles separate:

- Surface: page, section, card, popover, overlay.
- Text: primary, secondary, muted, disabled, inverse.
- Border and overlay: divider, hairline, default border, hover border, active
  border, hover overlay.
- State and accent: focus, link, success, warning, danger, info.
- Data: chart series, positive/negative deltas, neutral deltas, categorical
  ramps, sequential ramps.

Avoid swapping surface tokens for text gray tokens or using one gray scale for
every role. Hard-coded visual values are acceptable only when the project has
no token layer yet or when the change explicitly creates one.

## Theme parity

For light/dark work:

- Keep token names stable across themes.
- Define hover, active, disabled, focus, and border states for both themes.
- Check focus rings against both backgrounds.
- Do not rely on simple color inversion; re-balance surface contrast, borders,
  muted text, and accent intensity per theme.
- Components should not need `if dark` logic for basic colors when token parity
  can solve the problem.

For Web page shells, give the document canvas an explicit background from the
active page-surface token when overscroll or an uncovered viewport can expose
it. A painted app wrapper is not the document canvas. Transparent `html` can
inherit the body's canvas paint under browser rules; do not diagnose every
transparent root as a visible defect. Verify initial load and theme switching
in the target browser. Keep an existing `theme-color` in sync where supported;
do not disable platform overscroll merely to conceal a mismatched background.

## Typography roles

Choose typography by role before choosing size:

- Heading: page and section hierarchy; tighter line-height, stronger weight,
  and intentional tracking when needed.
- Label: navigation, form labels, table headers, metadata, chips, control text;
  optimized for single-line scanning.
- Copy: body, helper text, empty states, error explanations; optimized for
  multi-line reading.
- Mono/data: code, IDs, metrics, logs, tabular figures, compact data values.

Avoid three adjacent type sizes that visually collapse into the same hierarchy.
For dashboards and reports, data typography must be as intentional as prose.

Treat optical detail as part of the role contract:

- Prefer platform/system UI fonts for controls unless the brand has a specific
  reason to replace them. System faces already carry platform legibility and
  text-scaling behavior.
- When a variable font supports optical sizing, enable
  `font-optical-sizing: auto` and verify that the actual font file exposes an
  optical-size axis.
- Set tracking by role and size rather than applying one letter-spacing to the
  whole product. Large display text often needs slightly tighter tracking;
  small labels must not be compressed until letterforms merge.
- Set leading inversely with scale: display type is usually tighter, while body
  copy needs more line height. Recheck scripts with tall ascenders, descenders,
  or different shaping behavior instead of inheriting a Latin-only value.
- Use relative units and responsive layout so browser text zoom, iOS Dynamic
  Type, and Android font scaling do not clip labels or make actions unreachable.
- Use tabular figures for changing metrics, timers, and aligned numeric columns
  when the selected font supports them.

For icons that appear off-center, inspect the actual glyph/viewBox and visual
mass at the intended size before changing alignment. A temporary blurred view
can help locate that mass; remove the diagnostic filter afterward. Keep any
correction scoped to that icon and variant, preserving the control's hit area,
focus ring and label spacing. Recheck relevant sizes and RTL/mirrored variants;
a playback triangle's offset is not a universal icon-centering token.

## Layout rhythm

Prefer a small spacing scale over ad hoc gaps:

- Use a base scale, usually 4px or the project's established equivalent.
- Use smaller gaps inside a group, medium gaps between groups, and larger gaps
  between sections.
- Cards should have consistent padding tiers for compact, standard, and hero
  contexts.
- Use spacing and borders for hierarchy before adding heavy shadows.
- Responsive layouts should preserve grouping and priority, not merely stack all
  children in source order.

When nested rounded surfaces are meant to follow the same circular contour,
derive the inner radius from the outer radius minus the actual edge-to-edge
inset, clamped at zero. Measure corresponding edges: parent border plus padding
can both contribute. Use this as a geometric starting point within project
tokens, not a requirement to round every child. Unequal insets, elliptical or
noncircular corners, and children that do not reach the corner need individual
inspection. Check the rendered gap at narrow sizes as well as the nominal size.

When pale image edges disappear into their surface, consider a tokenized inner
edge that does not change layout. Inspect representative images in each theme
before choosing its color or opacity; it is not a mandatory frame for all media.
For linked or focusable media, keep the decorative edge separate from the
keyboard focus treatment. An overlay must not intercept input, and an inset
shadow on the image itself must not be assumed to paint above replaced image
content: verify the chosen outline or wrapper technique in the target browser.

## Component state matrix

Shared interactive components should define the relevant states:

- default
- hover
- active
- disabled
- loading or pending
- focus-visible
- error, invalid, or destructive when applicable
- empty and success states when the component owns feedback

Button and input variants should specify size, height, padding, radius,
typography, icon spacing, and state transitions. Do not leave keyboard focus as
an afterthought; every interactive element needs a visible `:focus-visible`
state.

For native components, replace web-only hover/focus language with the actual
platform state contract: pressed, selected, disabled, loading, invalid,
VoiceOver/TalkBack value, keyboard/D-pad focus where supported, Dynamic
Type/font-scale resilience, and minimum `44pt` iOS / `48dp` Android targets.

## Motion

Motion should clarify state, hierarchy, or causality.

- Prefer instant or very short transitions for simple state changes.
- Use slightly longer transitions for popovers, menus, overlays, and dialogs.
- Animate transform and opacity before layout properties.
- Avoid blanket `transition-all` on large surfaces or hot paths.
- Honor `prefers-reduced-motion` for nonessential motion.
- On native platforms honor Reduce Motion / Remove animations through the
  platform accessibility setting and use platform-consistent transitions.
- Do not hide content until JavaScript-triggered reveal effects run.

## Voice and content

UI copy is part of the system:

- Buttons and menu actions should name the action and object, such as
  `Create Project` or `Delete Member`.
- Avoid weak generic labels such as `OK`, `Confirm`, `Submit`, and bare verbs
  when a specific action is known.
- Errors should state what happened and what to do next.
- Toasts should name the thing that changed and avoid filler like
  `successfully`.
- Empty states should point to the first useful action.
- Loading states should describe the in-progress action.
- Preserve the product's vocabulary across menus, dialogs, settings, and
  toasts. Match nearby copy and localization conventions; adjust tone to the
  consequence without inventing a new voice for a local edit.
- Describe a toggle's enabled behavior, so the disabled behavior is easy to
  infer. Prefer `Send read receipts` to a negative label that reverses twice.
- Localize complete messages with the project's plural/select mechanism;
  do not concatenate translated fragments around a count or name. Casing and
  word order follow the target language, not an English-only template.
- Keep persistent instructions outside empty states that disappear when data
  arrives. Distinguish a new collection from a search with no matches; the
  latter should identify the active query/filter and provide a useful exit.
- Link labels should identify their destination independently. Placeholders
  show examples or formats and never replace persistent field labels.
- Error guidance must match the actual failed condition and an available
  recovery action. Do not invent validation restrictions or blame a network
  connection without evidence; recurring mistakes may require interaction fixes.

Source inspection can verify terminology, templates, and action bindings.
Translation fit, truncation, and assistive announcements require the relevant
rendered or accessibility evidence from `validation-contract.md`.

## Audit checklist

When the task touches design-system concerns, check:

- Was the project style authority enforced, evolved, inferred, or not
  applicable?
- Did the change add unexplained literal colors, spacing, radii, shadows, font
  sizes, or timing values?
- Do light and dark themes keep token parity?
- Are focus-visible, disabled, loading, error, and empty states covered where
  relevant?
- Does UI copy follow the project voice and avoid generic placeholders?
- Did the change improve the system rather than create a one-off exception?
- Did shared semantic roles preserve platform-correct iOS/Android behavior
  rather than force identical pixels?
