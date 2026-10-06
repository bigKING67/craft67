# Design authority: media detail inspection

## Product context

This is an original, offline Web component fixture for design engineers testing
four narrowly scoped interface details. It is not a production product or an
upstream demo replica. No requests, accounts, media playback or persistence.

## Typography and color

Use system sans typography, a neutral paper surface and a restrained blue focus
color. Light and dark modes share semantic CSS variables. Media is an original
inline SVG in an img element, with deliberately pale edges. No external fonts,
images, runtime libraries or animation. Labels explain the test rather than
claiming production defects. Controls remain native buttons with visible focus.

## Motion and interaction

State changes are immediate. Use native keyboard activation and a local live
status message. Theme and comparison controls reflect their state through
aria-pressed. No hover motion or audio is introduced.

## Component geometry

Keep content, DOM, component dimensions, spacing and actions identical between
before/after. Only the root background, inner media radius, media edge overlay
and triangle's internal optical offset may differ. Baseline deliberately uses
a white root, equal inner/outer radii and no media edge. This is seeded evidence.

Outer radius 24px, border 2px, padding 10px give a 12px circular inner radius.
These are fixture geometry, not universal tokens. The 24-unit play glyph has
vertices (6,5), (6,19), (18,12); its area centroid is at x=10, so a 2-unit shift
can be evaluated without changing the 48px button target. Keep the square stop
glyph centered with no offset. Both icons remain decorative with text labels.

## Acceptance

Compare desktop 1100x850 and mobile 390x844 in light and dark themes. Root
background and theme-color follow the active surface in after mode. Image
decoration does not change layout or intercept clicks. Nested circular gaps
are consistent; focus remains visible and Enter/Space activation works. Check
200% text-size simulation separately from browser zoom. No horizontal overflow
or obscured controls in the supported fixture cases. A rendered static frame
does not prove Safari rubber-band behavior, browser chrome or touch hardware.
