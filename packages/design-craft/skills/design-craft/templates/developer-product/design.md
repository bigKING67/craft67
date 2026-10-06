---
version: 1
name: Design Craft Developer Product
theme: light
status: seed
source: original-design-craft
platform: web
color:
  canvas: "#f7f8f6"
  surface: "#ffffff"
  surface-muted: "#eef1ed"
  ink: "#171a18"
  ink-muted: "#5f665f"
  border: "#d8ddd7"
  accent: "#245f4f"
  accent-strong: "#17483c"
  accent-soft: "#dcece6"
  info: "#255fa8"
  warning: "#9a5a12"
  danger: "#a33a35"
  success: "#237047"
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

# Developer Product Design Authority

## Product read

Define this before implementation:

- **Surface:** `<dashboard | admin | docs | settings | workflow | developer tool>`
- **Audience:** `<primary user and expertise level>`
- **Primary job:** `<decision or task the screen must accelerate>`
- **Vibe:** calm, exact, capable, and operational rather than decorative.
- **Evidence priority:** live product state and task completion outrank visual novelty.

## Visual direction

Use an editorial utility layout: a small number of strongly composed regions,
clear type hierarchy, restrained surfaces, and visible task order. Avoid a page
made from equal cards. Panels exist to group a real decision, workflow, or data
relationship; they are not the default wrapper for every block.

The interface should feel intentional at first glance:

1. One dominant job or decision object.
2. Supporting context close to the object it explains.
3. Exceptions and next actions visible without scanning the whole page.
4. Secondary tools quiet until needed.

## Color roles

- `canvas` is the page field.
- `surface` is the primary reading or working plane.
- `surface-muted` groups secondary controls and low-emphasis data.
- `ink` carries primary content; `ink-muted` carries metadata.
- `border` separates only where spacing and background cannot.
- `accent` marks selection, primary action, and active navigation.
- Semantic colors communicate state, never decoration.

Do not use accent-colored text for ordinary body copy. Do not encode status by
color alone; pair it with a label, icon, shape, or position.

## Typography

Prefer the product's established typeface. Otherwise use a high-legibility
system stack:

```css
font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
  "Segoe UI", sans-serif;
```

Use four durable roles:

| Role | Size | Weight | Line height | Use |
|---|---:|---:|---:|---|
| Display | `clamp(2.25rem, 5vw, 4.75rem)` | 650-750 | 0.98-1.05 | One page thesis or decisive state |
| Heading | `1.25-1.75rem` | 620-700 | 1.15 | Region and workflow titles |
| Body | `0.95-1rem` | 400-500 | 1.5 | Explanations and task content |
| Label | `0.75-0.82rem` | 550-650 | 1.25 | Controls, metadata, table headers |

Use tabular figures for metrics. Keep display copy short enough to preserve
shape; do not force a six-line hero into an operational product.

## Layout and density

- Use a 12-column grid for wide screens and a 4-column grid for compact screens.
- Keep the primary content width between `1120px` and `1440px` unless the data
  surface needs more room.
- Use `24-32px` page gutters on desktop and `16-20px` on compact screens.
- Prefer `40-64px` between major regions and `12-24px` inside components.
- Align headings, controls, data columns, and panel edges to a shared grid.
- Dense tables may be compact; decision summaries should breathe.

Responsive adaptation changes priority, not only width. On compact screens:

1. Keep the primary decision and next action first.
2. Collapse secondary metadata behind disclosure.
3. Replace wide comparison layouts with ordered sections.
4. Preserve minimum `44px` touch targets.

## Surfaces and depth

Use flat composition first. Add elevation only for layers that actually float:
menus, popovers, dialogs, dragged objects, or sticky controls crossing content.

```css
--shadow-floating: 0 16px 50px rgb(22 31 26 / 0.12);
--shadow-focus: 0 0 0 3px rgb(36 95 79 / 0.22);
```

- Do not stack heavy shadows.
- Do not combine strong shadow, thick border, gradient, and large radius on the
  same ordinary panel.
- Use the `feature` radius only for intentionally dominant composition blocks.

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

- One visually dominant action per decision region.
- Secondary actions use quieter fill or text treatment.
- Destructive actions use specific language and a danger role only when the
  result is genuinely destructive.

### Forms

- Labels stay visible; placeholders provide examples, not identity.
- Put validation beside the field and preserve the user's input.
- Group fields by the decision they support rather than by database shape.

### Tables and lists

- Lead with the entity or decision column.
- Align numeric data and expose units, freshness, and comparison periods.
- Keep row actions stable; do not hide the only critical action on hover.
- Provide empty, loading, partial, error, long-value, and overflow behavior.

### Navigation

- Current location is visually unambiguous.
- Labels name destinations specifically.
- Global, section, and contextual navigation use distinct visual levels.

### Dialogs and drawers

- Use a dialog for a focused decision; use a drawer for contextual work that
  should preserve the underlying page.
- Restore focus on close and support Escape unless the action is intentionally
  blocking.

## Motion

Motion preserves causality and direct manipulation. It does not decorate idle
content.

- Use `120-180ms` for hover, press, and small state feedback.
- Use `180-260ms` for menus, panels, and route-local transitions.
- Animate `transform` and `opacity` by default.
- Start spatial motion from the trigger or prior on-screen position.
- Gesture-driven objects track 1:1, inherit release velocity, and remain
  interruptible.
- `prefers-reduced-motion` replaces large travel and spring overshoot with a
  short fade or immediate state change.
- Never use `transition: all`.

## Accessibility

- Text and controls meet WCAG AA contrast at minimum.
- Focus-visible treatment is at least as clear as hover.
- Keyboard order follows visual and task order.
- Icon-only controls have accessible names.
- Status changes use an appropriate live region when needed.
- Zoom, long localization strings, and 200% text do not hide primary actions.

## Voice and content

Write like an experienced operator:

- specific nouns and verbs;
- short labels;
- factual status language;
- no hype, fake urgency, or vague success messages;
- errors explain what happened, what was preserved, and the next safe action.

## Avoid

- Equal card grids without hierarchy.
- Decorative gradients as a substitute for product identity.
- Glass effects on every surface.
- Large marketing heroes inside dense operational workflows.
- Low-contrast gray-on-gray interfaces.
- Generic labels such as `Manage`, `Overview`, or `Submit` when a precise action
  is available.
- Motion claims without runtime observation.

## Acceptance checklist

- The primary job is obvious in the first viewport.
- The dominant region is structurally, not merely chromatically, dominant.
- Empty/loading/error/long-data states are defined.
- Keyboard, focus, responsive, and reduced-motion behavior are verified.
- Tokens express semantic roles and light/dark parity.
- Browser evidence and screenshots are reported only when actually captured.
