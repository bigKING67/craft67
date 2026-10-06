---
version: 1
name: Design Craft Developer Product
theme: dark
status: seed
source: original-design-craft
platform: web
color:
  canvas: "#111412"
  surface: "#181c19"
  surface-muted: "#202621"
  ink: "#f1f4f0"
  ink-muted: "#a9b1aa"
  border: "#343b35"
  accent: "#79c5ac"
  accent-strong: "#a1dbc8"
  accent-soft: "#203b32"
  info: "#84b8f4"
  warning: "#e4ae67"
  danger: "#ef8f87"
  success: "#7ac89b"
radius:
  control: 8
  panel: 14
  feature: 22
space:
  unit: 4
  compact: 8
  control: 12
  section: 24
  region: 40
motion:
  fast: 120
  standard: 180
  deliberate: 260
---

# Developer Product Dark Design Authority

## Product read

Use the same product purpose, audience, information order, and component
semantics as the light authority. Dark mode is not a separate visual concept;
it is a calibrated material and contrast variant for the same product.

- **Surface:** `<dashboard | admin | docs | settings | workflow | developer tool>`
- **Audience:** `<primary user and expertise level>`
- **Primary job:** `<decision or task the screen must accelerate>`
- **Vibe:** calm, precise, low-glare, and operational.

## Dark-mode principles

1. Preserve hierarchy with luminance and spacing, not many glowing borders.
2. Keep large backgrounds near-neutral; reserve chroma for actions and states.
3. Raised surfaces are slightly lighter than the canvas.
4. Text is off-white rather than pure white to reduce glare.
5. Borders remain visible without outlining every region.

## Color roles

- `canvas` is the deepest page field.
- `surface` is the main working plane.
- `surface-muted` groups secondary tools and low-emphasis data.
- `ink` carries primary content; `ink-muted` carries metadata.
- `border` separates only where spacing or surface contrast is insufficient.
- `accent` marks selection and primary action.
- Semantic colors communicate state and retain readable text contrast.

Do not apply opacity to an entire disabled component if doing so makes text or
state illegible. Use explicit disabled tokens.

## Typography

Use the same family, scale, weight, and role names as light mode:

```css
font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
  "Segoe UI", sans-serif;
```

| Role | Size | Weight | Line height | Use |
|---|---:|---:|---:|---|
| Display | `clamp(2.25rem, 5vw, 4.75rem)` | 650-750 | 0.98-1.05 | One decisive state |
| Heading | `1.25-1.75rem` | 620-700 | 1.15 | Region and workflow titles |
| Body | `0.95-1rem` | 400-500 | 1.5 | Explanations and task content |
| Label | `0.75-0.82rem` | 550-650 | 1.25 | Controls and metadata |

Use tabular figures for metrics. Avoid thin font weights on dark surfaces.

## Layout and density

Light and dark themes share layout metrics:

- 12-column wide grid; 4-column compact grid.
- `1120-1440px` primary content width unless data density requires more.
- `24-32px` desktop gutters; `16-20px` compact gutters.
- `40-64px` major region gaps; `12-24px` component gaps.
- Shared baselines for headings, controls, table cells, and panel edges.

Compact layouts reprioritize content instead of shrinking the desktop canvas.
Keep the decision and action first, disclose secondary metadata, and preserve
`44px` touch targets.

## Surfaces and depth

Dark interfaces need less shadow and more controlled surface separation:

```css
--shadow-floating: 0 18px 54px rgb(0 0 0 / 0.42);
--shadow-focus: 0 0 0 3px rgb(121 197 172 / 0.28);
```

- Avoid pure-black panels inside a near-black page unless the contrast marks a
  genuinely dominant region.
- Do not add luminous outlines to every card.
- Use elevation only for real floating layers.
- Keep overlays and scrims strong enough to preserve focus without erasing the
  underlying task context.

## Component contract

Every interactive component defines:

```text
default
hover where hover exists
pressed
focus-visible
selected or current
disabled
loading where asynchronous
error where failure is possible
```

### Buttons

- One dominant action per decision region.
- Primary fill uses `accent`; text contrast is verified.
- Secondary and tertiary actions remain distinguishable from disabled states.

### Forms

- Labels stay visible.
- Inputs are distinguishable from the surrounding surface before focus.
- Focus, error, autofill, disabled, and read-only states have explicit tokens.
- Validation stays beside the field and preserves input.

### Tables and lists

- Lead with the decision or entity column.
- Use subtle row separation; avoid a bright grid around every cell.
- Align figures and expose units, freshness, and comparison periods.
- Keep critical row actions available without hover.

### Navigation

- Current location is clear through position, weight, and accent.
- Global, section, and contextual navigation use distinct levels.
- Selected states are not confused with hover states.

### Dialogs and drawers

- Dialogs support focused decisions; drawers preserve contextual work.
- Scrims, focus traps, Escape behavior, and focus restoration are verified.
- Nested floating surfaces maintain a clear elevation order.

## Motion

Use the same causal motion policy as light mode:

- `120-180ms` for small feedback.
- `180-260ms` for menus and local panels.
- Prefer `transform` and `opacity`.
- Start motion from the trigger or current on-screen value.
- Gesture interactions track 1:1, carry velocity, and remain interruptible.
- Avoid simultaneous large movement and large luminance flashes.
- Reduced Motion removes large travel, parallax, and spring overshoot.
- Never use `transition: all`.

## Accessibility

- Verify contrast in the rendered dark theme, not by reusing light-theme ratios.
- Focus-visible treatment is clear on every surface role.
- Keyboard and reading order match the visible task flow.
- Icons and semantic colors have text or accessible-name equivalents.
- High-contrast and reduced-transparency preferences do not remove hierarchy.
- Zoom, long strings, and 200% text preserve the primary action.

## Voice and content

Use specific, calm operational language:

- concrete nouns and verbs;
- no glow-themed marketing language merely because the UI is dark;
- errors state the failure, preserved state, and next safe action;
- success messages name what changed.

## Avoid

- Pure black and pure white across large regions.
- Neon accents on every interactive element.
- Glowing borders as the only hierarchy mechanism.
- Transparent surfaces over busy content without contrast control.
- Equal card stacks, generic gradients, and decorative motion.
- Hidden actions that appear only on hover.
- Runtime smoothness or accessibility claims without observation.

## Acceptance checklist

- Light and dark modes share semantic tokens and component behavior.
- The primary job remains obvious in the first viewport.
- Surface elevation and contrast communicate hierarchy without glare.
- Empty/loading/error/long-data states are defined.
- Keyboard, focus, responsive, dark-theme, and reduced-motion behavior are
  verified.
- Browser evidence and screenshots are reported only when actually captured.
