# Design authority: Reviewlane

## Brand & Product Context

Reviewlane is a controlled, project-neutral release-review fixture for frontend
leads and design engineers. Its single job is to help a reviewer understand the
offer, inspect a concrete review bundle, and either start a review or open the
sample report.

The visual thesis is a calm editorial release desk: warm paper, precise dark
type, one electric-blue action color, and product evidence treated as the visual
anchor rather than as decorative dashboard chrome.

The fixed content sequence for both experiment variants is:

1. Hero: brand, one release-oriented promise, actions, and concrete proof.
2. Support: the three-step review workflow.
3. Detail: the same evidence bundle expressed as a readable release decision.
4. Final CTA: start with one release candidate.

The interaction thesis is equally restrained:

- A restrained hero entrance establishes reading order without delaying input.
- Evidence rows clarify their grouping on hover and keyboard focus.
- A native sample-report dialog preserves focus and dismisses without a route
  change.

## Typography System

- UI and body: `SF Pro Display`, `Helvetica Neue`, `Arial`, system sans-serif.
- Editorial display: `Iowan Old Style`, `Baskerville`, `Times New Roman`, serif.
- Technical metadata: `SFMono-Regular`, `SF Mono`, `Menlo`, monospace.
- Product name is compact and assertive; the headline carries the main scale.
- Hero headline: `clamp(3.5rem, 8vw, 8rem)`, line-height `0.88` to `0.96`.
- Section headline: `clamp(2rem, 4vw, 4.5rem)`, line-height `0.95` to `1.05`.
- Body: `1rem` to `1.125rem`, line-height `1.55` to `1.7`.
- Metadata: `0.72rem` to `0.8rem`, uppercase only for short labels.
- Body measure stays between 46 and 64 characters where possible.

## Color Palette

The palette is warm monochrome with one scarce action color:

- `--paper`: `#f3f0e9`
- `--paper-raised`: `#fbfaf7`
- `--ink`: `#151515`
- `--ink-muted`: `#6a685f`
- `--line`: `#cbc6bb`
- `--accent`: `#2f5bea`
- `--accent-ink`: `#ffffff`
- `--positive`: `#1f7a55`
- `--attention`: `#a5521b`

Use `--accent` only for the primary action, keyboard focus, and the selected
decision state. `--positive` and `--attention` are semantic status colors, not
decorative accents. No gradients, neon, glass effects, or additional accent
colors.

## Motion Language

- Entrance duration: 420–620ms with `cubic-bezier(0.16, 1, 0.3, 1)`.
- Hover/focus transitions: 120–180ms.
- Animate only opacity and transforms; use `IntersectionObserver` for below-fold
  reveals rather than scroll listeners.
- No looping decoration, parallax, auto-advance, ambient blobs, or scroll
  hijacking.
- `prefers-reduced-motion: reduce` removes transforms, animation, and smooth
  scrolling while preserving every state change.

## Component Grammar

- Base spacing unit: 4px.
- Major section spacing: 88–144px desktop, 64–96px mobile.
- Buttons use a compact 4–6px rounded rectangle, no pill geometry, and no box
  shadow. Primary actions use the single blue accent; secondary actions remain
  paper-toned with a 1px border.
- Content sections remain primarily cardless and use dividers, spacing, and
  typographic contrast instead of repeated containers.
- Product evidence uses one bordered plane with internal dividers. Do not turn
  every metric or workflow step into a floating card.
- The evidence plane may use only an ultra-diffuse shadow below 0.05 opacity.
- Status labels may use compact pill geometry because they are metadata, never
  primary controls or large containers.
- The native report dialog uses the same type, border, and action grammar as the
  page; it must expose a visible close control and restore focus when dismissed.

## Cross-page Consistency Rules

- Both variants use the same HTML content, semantic order, design tokens,
  actions, native dialog, and product data. Only composition and responsive
  priority may differ.
- Desktop target: `1440x900`; mobile target: `390x844`.
- Navigation loses secondary links before the primary action.
- Do not uniformly shrink the desktop composition. The reference-assisted
  variant may reorder product proof relative to supporting explanation, but it
  may not remove content or functionality.
- No horizontal overflow at either target viewport.
- Design Meetup may contribute only a single-focus entry and early real
  evidence. Locket may contribute only responsive proof prioritization and a
  stronger direct mobile action.
- Do not transfer third-party typography, color, imagery, identity, device
  mockups, event artwork, social fragments, copy, or exact geometry. This file
  remains the visual authority for both variants.

## Acceptance Checklist

- [ ] Both query variants render the exact fixed content from `PRODUCT.md`.
- [ ] One `h1`, one primary action, and one working sample-report dialog exist.
- [ ] Keyboard focus is visible and the native dialog restores focus on close.
- [ ] Desktop `1440x900` and mobile `390x844` have no horizontal overflow.
- [ ] The initial viewport communicates offer, evidence, and next action.
- [ ] Product evidence is the visual anchor rather than decorative chrome.
- [ ] Mobile priority is intentionally recomposed, not uniformly shrunk.
- [ ] Motion respects `prefers-reduced-motion` and never delays interaction.
- [ ] No gradients, generic card mosaic, stock imagery, copied identity, or
      copied third-party geometry is present.
- [ ] Baseline and reference-assisted screenshots receive an explicit visual
      critique before any evidence is linked from the pilot catalog.
