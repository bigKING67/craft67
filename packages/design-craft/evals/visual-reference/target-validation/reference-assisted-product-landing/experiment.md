# Controlled target validation: reference-assisted-product-landing

## Status and claim boundary

This is a project-neutral, repository-local rendered target used to validate
the design-craft Reference Pack workflow. It is stronger than a schema-only
golden case because both variants run in a real browser, but it is not an
external product, production route, customer result, or general proof that a
reference mechanism improves every landing page.

## Pre-registered question

With product content, design authority, components, interactions, and
validation held constant, does a reviewed Reference Pack improve first-screen
focus, proof sequencing, and mobile priority without copying source identity or
reducing accessibility?

## Fixed variables

- One HTML document and one stylesheet.
- Identical product copy, metrics, workflow, links, dialog, and semantic DOM.
- Identical `PRODUCT.md`, `DESIGN.md`, tokens, controls, and state behavior.
- Variants selected only by `?variant=baseline|reference-assisted`.
- Desktop `1440x900` and mobile `390x844` browser evidence.
- Same browser runtime and capture task for both variants.

## Variant A: baseline

A competent conventional product landing composition built only from product
and design authority: concise copy and actions on the left, a proof plane on the
right, followed by workflow and final CTA.

## Variant B: reference-assisted

Uses the approved Pack only for:

- `structure`: give one proposition dominant first-screen focus and bring real
  evidence into the same viewport;
- `responsive`: recompose product proof and direct action priority on mobile
  rather than shrinking the desktop arrangement.

## Evaluation criteria

1. Product name, promise, primary action, and proof are legible in the first
   viewport.
2. The primary scan path is identifiable without reading every sentence.
3. Proof supports rather than competes with the proposition.
4. Mobile uses deliberate priority ordering and has no horizontal overflow.
5. Both variants preserve identical functionality and keyboard access.
6. The assisted variant stays within Reviewlane authority and does not resemble
   a source brand.
7. No unresolved P0/P1 visual, responsive, interaction, or accessibility issue
   is present.

## Decision rule

The hypothesis may receive a `target_validation_ref` only if the assisted
variant improves at least two pre-registered design criteria, introduces no
P0/P1 regression, preserves all content and behavior, and passes final visual
review. One local fixture cannot advance the hypothesis to
`comparative_validated` or `absorbed`.

## Negative control

The existing `beautiful-but-wrong` golden case remains the negative control:
Design Meetup is blocked as a positive `Operate` reference. No intentionally
degraded operations UI will be built merely to create a favorable comparison.
