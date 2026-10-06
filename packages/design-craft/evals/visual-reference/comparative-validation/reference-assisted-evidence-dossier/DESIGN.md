# Design authority: Cairn

## Brand and product context

Cairn is a controlled evidence-dossier fixture. Its job is to help a skeptical
decision maker connect a product claim to bounded evidence, understand what is
still open, and choose whether to inspect a sample or request a pilot.

The visual thesis is a quiet forensic publication: mineral paper, deep blue
ink, rust for unresolved decisions, acid green only for verified evidence, and
a restrained editorial rhythm anchored by a ruled evidence ledger. The page
must feel authored and accountable, not like a generic analytics dashboard.

Both variants share this content sequence:

1. Header: identity, page anchors, and commercial action.
2. Entry: proposition, support, actions, decision posture, and evidence summary.
3. Evidence ledger: scope, change impact, and exception ownership.
4. Method: map the claim, bind evidence, name the decision.
5. Questions: three native disclosure controls.
6. Final action: request a bounded pilot.

## Typography system

- UI and body: `Avenir Next`, `Helvetica Neue`, `Arial`, sans-serif.
- Editorial display: `Iowan Old Style`, `Palatino Linotype`, `Book Antiqua`,
  serif.
- Evidence metadata: `SFMono-Regular`, `SF Mono`, `Menlo`, monospace.
- Hero headline: `clamp(3.25rem, 7vw, 7.5rem)`, line-height `0.88` to `0.98`.
- Section headline: `clamp(2rem, 4vw, 4.25rem)`, line-height `0.96` to `1.08`.
- Body: `1rem` to `1.125rem`, line-height `1.55` to `1.72`.
- Metadata: `0.68rem` to `0.78rem`; uppercase is limited to short evidence
  labels.
- Long copy should remain within 48 to 68 characters where possible.

## Color palette

- `--paper`: `#ece9df`
- `--paper-raised`: `#f7f5ee`
- `--ink`: `#14243a`
- `--ink-muted`: `#5f6871`
- `--line`: `#b9b6aa`
- `--line-strong`: `#7f817b`
- `--rust`: `#ad4f2b`
- `--rust-dark`: `#75331d`
- `--verified`: `#b8f43d`
- `--verified-ink`: `#17230a`
- `--focus`: `#2558d8`

The rust tone identifies open decisions and primary commercial intent. Acid
green is reserved for verified evidence. Blue focus is reserved for keyboard
focus. No gradients, glass effects, neon glow, or decorative color families.

## Component grammar

- Base spacing unit: 4px.
- Major section spacing: 88 to 136px desktop, 64 to 96px mobile.
- The primary evidence object is one ruled dossier, not a card mosaic.
- Evidence summaries use plain cells separated by lines; no floating metric
  cards or shadows.
- Buttons use compact rectangular geometry with a 2px maximum radius.
- Status marks include an icon or word, never color alone.
- FAQ uses native `details` and `summary` controls.
- The native dialog repeats the same paper, line, type, and status grammar.
- Long labels wrap without truncating the attributable source or exception.

## Motion language

- Entrance duration: 360 to 520ms using `cubic-bezier(0.2, 0.75, 0.2, 1)`.
- Hover and focus transitions: 120 to 160ms.
- Only opacity and transform may animate.
- No looping decoration, parallax, auto-advance, cursor follower, or scroll
  hijacking.
- `prefers-reduced-motion: reduce` removes all transitions, transforms, and
  smooth scrolling while retaining every state change.

## Variant contract

- Both variants use the same `index.html`, `styles.css`, and `app.js`.
- Both variants use the same semantic DOM, content, tokens, controls, state
  parser, dialog, and retry behavior.
- `baseline` is a competent conventional split entry: proposition and actions
  lead, with evidence presented as a neighboring dossier.
- `reference-assisted` may change only information composition, typographic
  emphasis, and responsive priority.
- On desktop, the assisted variant should bind the proposition to concrete
  evidence in one reading field rather than presenting two competent peers.
- On mobile, the assisted variant should surface the evidence summary before
  detailed explanation while keeping logical keyboard order intact.
- Desktop target: `1440x900`; mobile target: `390x844`.
- No horizontal overflow at target or intermediate widths.

## Reference boundary

- Lightspark contributes only the mechanism of surrounding an abstract product
  proposition with concrete proof and linearizing proof on mobile.
- Nue contributes only the mechanism of replacing a desktop-oriented
  conversion path with a direct mobile action and connecting a human decision
  to restrained measurable evidence.
- Do not transfer financial or medical language, product screenshots, people,
  QR codes, glowing fragments, colors, identity, source copy, or exact geometry.
- Peekpaper remains discovery metadata, never visual authority.

## Acceptance checklist

- [ ] Both variants render the fixed inventory from `PRODUCT.md`.
- [ ] Exactly one visible `h1`, one `main`, one native dialog, and visible focus.
- [ ] Default, loading, empty, error, success, and long states remain usable.
- [ ] Dialog focus enters predictably and returns to the invoking control.
- [ ] Error retry announces loading and restored default state.
- [ ] Desktop `1440x900`, mobile `390x844`, and intermediate `768x900` have no
      horizontal overflow.
- [ ] Offer, concrete evidence, and next action are legible in the first desktop
      and mobile viewport.
- [ ] Assisted composition improves at least two pre-registered criteria without
      hiding explanatory or exception context.
- [ ] Reduced Motion removes entrance motion without hiding content.
- [ ] No third-party asset, brand identity, copy, or exact composition appears.
- [ ] A final screenshot critique identifies unresolved P0/P1/P2 findings.
