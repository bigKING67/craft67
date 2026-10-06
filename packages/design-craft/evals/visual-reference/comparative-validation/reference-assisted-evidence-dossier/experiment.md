# Separate-target comparative evaluation: reference-assisted-evidence-dossier

## Status and independence boundary

This is a separate repository-local target from the Reviewlane landing fixture.
It uses a different product, audience, content density, visual authority,
Reference Pack, and page structure. It is an independent target, but not an
independent human judge or production product route.

## Pre-registered question

With product content, design authority, semantics, controls, states, and
validation held constant, does a reviewed Reference Pack improve the connection
between an abstract promise and concrete evidence, plus mobile evidence
priority, without hiding exception context or weakening accessibility?

## Fixed variables

- One HTML document, one stylesheet, and one JavaScript file.
- Identical product copy, metrics, evidence rows, questions, and actions.
- Identical semantic DOM, keyboard order, native dialog, retry behavior, and
  state query contract.
- Identical `PRODUCT.md`, `DESIGN.md`, and Reference Pack.
- Variants selected only by `?variant=baseline|reference-assisted`.
- States selected only by `&state=default|loading|empty|error|success|long`.
- Desktop `1440x900`, intermediate `768x900`, and mobile `390x844` checks.
- Same browser runtime and capture task for both variants.

## Variant A: baseline

A competent conventional evidence-platform landing composition: proposition,
explanation, and actions lead in one column while the complete evidence dossier
appears as a neighboring product proof object.

## Variant B: reference-assisted

Uses the approved Pack only for:

- `structure`: bind the abstract proposition to concrete scope, control,
  exception, and freshness proof in the same reading field;
- `responsive`: linearize the proof summary on mobile and strengthen the direct
  request path without removing explanation or exception context.

## Evaluation criteria

1. The first viewport connects the product promise to at least three concrete
   evidence dimensions without requiring the reader to infer what the product
   produces.
2. The primary scan path is proposition -> decision posture -> concrete proof ->
   explanation/action.
3. Open exceptions remain as visible as verified evidence; the composition does
   not create false certainty.
4. Mobile intentionally reprioritizes evidence rather than uniformly shrinking
   the desktop layout.
5. Both variants preserve identical content, semantics, keyboard order,
   controls, and state behavior.
6. Default, loading, empty, error, success, and long states stay readable, and
   retry/dialog focus behavior is verified.
7. No unresolved P0/P1 visual, responsive, interaction, accessibility, or
   performance issue is introduced.
8. The assisted variant remains inside Cairn authority and does not resemble a
   source brand.

## Measurable checks

- Headline, posture, evidence summary, and primary action bounding boxes are
  recorded for desktop and mobile.
- All target viewports report `horizontal_overflow=false`.
- Resource count, transferred bytes when available, FCP, LCP, CLS, and long-task
  observations are recorded as local controlled measurements.
- Automated DOM accessibility checks cover landmarks, heading count, labels,
  focusability, dialog semantics, state announcements, and Reduced Motion.
- Browser interaction verifies dialog focus entry/restoration and error retry.

## Decision rule

The evaluation passes only if the assisted variant improves at least two of
criteria 1 through 4, preserves criteria 5 and 6, introduces no P0/P1 issue,
and passes final visual review. Passing may add a bounded comparative reference
to an already target-validated hypothesis. It does not by itself establish an
`absorbed` design rule, production value, or independent human preference.

## Negative controls

- Open exceptions cannot be removed, visually minimized, or recolored as
  verified evidence.
- No intentionally degraded baseline is permitted.
- No source screenshot, asset, copy, device mockup, QR code, or exact geometry
  may enter the target.
