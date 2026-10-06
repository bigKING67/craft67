# Visual judgment

Use this when the task is visual, brand-facing, report-like, or asks for a UI
that should not look generated.

This is `design-craft`'s fused visual judgment layer. It preserves the useful
anti-slop and brief-inference ideas absorbed from upstream taste guidance, but
it is not a legacy skill entrypoint and must stay subordinate to live runtime
truth, scoped project rules, and project `DESIGN.md`.

## Contents

- [Design read first](#design-read-first)
- [Authority and change scope](#authority-and-change-scope)
- [Anti-default discipline](#anti-default-discipline)
- [Three operating dials](#three-operating-dials)
- [Typography](#typography)
- [Color](#color)
- [Layout and material](#layout-and-material)
- [Motion](#motion)
- [Optional expressive directions](#optional-expressive-directions)
- [Final visual self-check](#final-visual-self-check)

## Design read first

Infer before styling:

- Surface: landing, portfolio, app, dashboard, report, form, mobile flow,
  data-viz, marketing section, component.
- Audience: buyer, operator, analyst, executive, developer, consumer,
  recruiter, internal user.
- Job: understand, decide, compare, configure, act, monitor, explore, convert.
- Mood and risk: calm, premium, utilitarian, editorial, playful, trustworthy,
  high-density, accessibility-critical.
- Existing assets: tokens, fonts, brand colors, components, screenshots,
  charts, current design language.

State the read once. If two very different reads are plausible, ask one
question. Do not ask if repo evidence makes the answer obvious.

## Authority and change scope

- The brief wins. Honor explicit aesthetics, materials, fonts, eras, palettes,
  and anti-references unless they violate a higher project or platform rule.
  Redirecting a clear brief toward personal taste is a design failure.
- Visual authority is observed evidence, not a filename check. Missing
  `DESIGN.md` does not make an existing product greenfield when its tokens,
  components, assets, and live UI already establish a coherent world.
- Refinement preserves the incumbent identity, behavior, factual copy, and
  everything outside scope. Ask before replacing claims or product truth.
- Redesign may replace the visual world, but it still preserves product truth,
  content, function, native affordances, and explicit constraints. Do not hide
  a partial redesign inside a polish task.

## Anti-default discipline

Reject these defaults unless the brief and project system explicitly require
them:

- Purple/blue gradient hero as a generic "AI" signal.
- Centered hero plus three identical feature cards.
- Glassmorphism everywhere.
- Zero-offset radial halos or colored glow used as generic depth.
- Over-rounded cards, wide soft shadows, decorative stripes.
- Tiny uppercase eyebrow or repeated kicker on every section.
- Decorative `01 / 02 / 03` labels when sequence carries no meaning.
- Gradient text for emphasis.
- Monotonous equal card grids.
- Fake blinking cursors, ambient pulses, or attention loops without state.
- Placeholder people, fake testimonials, lorem ipsum, "Jane Doe" data.
- Hand-rolled sketch SVGs or generic shape-assembled illustrations as a
  fallback for real visual assets.
- Repeated aphoristic copy cadence that substitutes slogans for product truth.
- Motion applied uniformly to every section without content reason.

Replace default scaffolds with content structure: stronger hierarchy, better
copy grouping, real data, mixed layouts, proof, and visual rhythm.

## Three operating dials

Use the dials as internal guidance, not user-facing ceremony:

- `DESIGN_VARIANCE`: 1 symmetrical/systemic, 10 expressive/asymmetric.
- `MOTION_INTENSITY`: 1 static, 10 cinematic.
- `VISUAL_DENSITY`: 1 sparse/editorial, 10 cockpit/data-heavy.

Defaults by surface:

- Landing/brand: variance 7, motion 5, density 3.
- Portfolio/editorial: variance 7, motion 5, density 3.
- Dashboard/admin: variance 3, motion 2, density 7.
- Special report/data story: variance 4, motion 2, density 5.
- Mobile task flow: variance 3, motion 2, density 5.
- Regulated/accessibility-critical: variance 2, motion 1, density 5.

For existing projects, match the current system first, then improve the weakest
dimension.

## Typography

- Body text should usually be at least 16px with line-height around 1.45 to
  1.7, adjusted to font and density.
- Long prose should sit around 55 to 75 characters per line.
- Headings need clear scale, weight, and line-height differences; avoid three
  sizes that visually read as the same.
- Use `text-wrap: balance` for display headings when supported; use
  `text-wrap: pretty` for long prose when available.
- Do not add a random serif word inside a sans heading just for decoration.
- Do not default to Inter unless the project already uses it or neutrality is
  the actual goal.

## Color

- Preserve committed tokens and brand colors before inventing a new palette.
- Verify contrast, especially muted text on tinted backgrounds.
- Body copy must be readable; elegance is not an excuse for low contrast.
- Use color roles intentionally: background, surface, ink, muted, accent,
  success, warning, danger, chart series.
- Data products need chart-safe color ramps and enough separation for adjacent
  series.

## Layout and material

- Use spacing to group related content before reaching for cards.
- Cards are a tool, not the default answer. Avoid nested cards.
- Prefer CSS Grid for 2D layout and flex for 1D flow.
- Align to an actual grid or content rhythm; do not center everything.
- Use shadows only where elevation or focus is meaningful.
- Responsive layout must be designed, not merely stacked.

## Motion

- Motion must clarify hierarchy, state, or causality.
- Avoid layout-property animations on hot paths.
- Use transform/opacity for common transitions.
- Every nontrivial motion needs a reduced-motion fallback.
- Do not hide content by default waiting for JS-triggered reveal.

## Optional expressive directions

Use these only when the brief or approved design evolution calls for them;
they are internal options, not additional Skill dependencies or default styles.

- Editorial/tactile: photography, serif/sans contrast, deliberate whitespace,
  paper or quiet neutrals can build hierarchy. Glass, metal, diffused shadows,
  and overlapping media are optional materials, not proof of premium quality.
  Preserve contrast and measure expensive blur/compositing when actually used.
- For a meaningful nested shell, relate inner and outer radii and keep
  highlights restrained. Remove overlap or rotation on narrow screens when it
  collides with content; use depth only when it explains grouping.
- Motion-led promotion: choose a narrative composition and expressive type
  from content, not simulated randomness. AIDA, pinned stories, staggered
  reveals, accordions, and card stacks are options, never a required quota.
  Keep the first viewport readable without prescribed line counts or heights.
- Prefer the existing motion stack. A style choice alone does not justify a
  new dependency. Preserve static content, keyboard/touch access, Reduced
  Motion, interruption, and lifecycle cleanup through the motion references.

Verify font availability and rights; do not assume premium assets exist.
Flat surfaces, ordinary cards, and centered layouts remain valid when the
project or content supports them. Do not broaden a polish task into redesign.

## Final visual self-check

Before shipping, ask:

- Could a reviewer call this "AI-generated" from common visual tells?
- Does the first screen tell the user what matters within two seconds?
- Does every decorative element earn its place?
- Does the density fit the job and audience?
- Are all major states visible or intentionally handled?
