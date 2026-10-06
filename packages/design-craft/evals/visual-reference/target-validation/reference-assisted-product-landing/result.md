# Result: reference-assisted-product-landing

## Outcome

The controlled target meets the pre-registered decision rule. The
reference-assisted variant improves first-screen focus and mobile proof
priority without changing product content, semantic DOM, controls, data, or
design authority. It introduces no observed P0/P1 regression at the two target
viewports.

This result is sufficient to add one bounded `target_validation_ref` to the
`typographic-single-focus-entry` and
`desktop-mobile-priority-reordering` hypotheses. Both hypotheses remain
`proposed`: this local fixture is not a production route and is not the
independent comparative evaluation required for promotion.

## Controlled comparison

| Criterion | Baseline | Reference-assisted | Decision |
|---|---|---|---|
| First-screen proposition | Clear but split across a conventional two-column hero | One dominant proposition spans the desktop reading field | Improved |
| Proof sequencing | Full proof is visible on desktop; mobile proof begins at `y=634` and continues below the first viewport | Full proof stays inside the desktop first viewport and moves to `y=416` on mobile, before supporting explanation | Improved |
| Primary scan path | Copy, actions, and proof are competent peers | Proposition -> concrete release bundle -> supporting explanation/action | Improved |
| Responsive priority | Mobile stacks copy, explanation, action, then proof | Mobile deliberately places the complete proof bundle immediately after the proposition | Improved |
| Functional parity | Shared document, data, controls, and JavaScript | Shared document, data, controls, and JavaScript | Preserved |
| Authority and source identity | Reviewlane authority | Reviewlane authority; no source brand, asset, copy, imagery, or exact geometry | Preserved |

The assisted desktop composition places the proof plane from `y=505` to
`y=868` at `1440x900`. Its mobile composition places the proof plane from
`y=416` to `y=743` at `390x844`. All four captures report
`horizontal_overflow=false`.

## Evidence

Checked-in metadata:

- `screenshots.json`: tool-built `design-craft.l4-screenshots.v1` manifest with
  shared `desktop` and `mobile` keys, verified dimensions, hashes, layout
  metrics, run metadata, transport health, and scoped browser finalization.
- `reference-pack.json`: ready Pack containing exactly one `structure` and one
  `responsive` reference.
- `experiment.md`: question, fixed variables, criteria, and decision rule
  recorded before the rendered comparison.

Repo-external browser run:

```text
browser67://runs/design-craft/20260817T051534181Z-3107946c
```

| Phase | Viewport | SHA-256 | Dimensions |
|---|---|---|---|
| baseline | desktop | `e07322716f7110ed5e30ef5da8eb2fd72f3fbc63570df0eb3348f49a38f43f08` | 1440x900 |
| baseline | mobile | `cc211806041493148c1c5dbe4e05502b1c9dba3efd1d41e9b91c23686b85d203` | 390x844 |
| reference-assisted | desktop | `cc35694bb38addcb59b112b5eb52eb9ddcebba1a0a0a72c24c7945db9bb6059d` | 1440x900 |
| reference-assisted | mobile | `5042812f05cf8af2a2dce4da864bb781ab3fff5190da3f81fa8fe82d38adf236` | 390x844 |

## Interaction and accessibility observations

- The real managed browser rendered one `h1`, one native `dialog`, and no
  horizontal overflow.
- A NodeRef click opened the sample report and focused its visible close
  button.
- The first implementation left focus on a now-hidden dialog button after
  dismissal. The shared handler was corrected to restore focus after the
  dialog form submits or is cancelled. A live retest returned
  `opened=true`, `closed=true`, and `focusRestored=true`.
- A NodeRef click on `Begin with RC-18` disabled the control and exposed the
  live status `Local sample started. No data was uploaded and no account was
  created.`
- Focus traversal order, screen-reader output, contrast ratios, and automated
  accessibility tooling were not separately audited. Native semantics and
  visible focus styling are present but do not replace those checks.

## Visual review

No P0 or P1 visual issue remains in the reviewed first viewport.

P2 observations retained as boundaries rather than blockers:

- The assisted mobile first viewport intentionally defers explanatory copy
  below the proof bundle; this is useful for the fixed audience but may be
  unsuitable when regulatory or comparison context must precede evidence.
- The assisted desktop headline uses an aggressive editorial scale. It remains
  within Reviewlane authority, but should not be generalized to operational
  surfaces or copied as a universal landing-page rule.
- The external screenshot run expires under browser67 retention. The checked-in
  manifest preserves paths, dimensions, hashes, layout metrics, and run
  identity, not redistributed PNGs.

## Promotion boundary

This is target/prototype validation only. It does not establish:

- production conversion, usability, performance, or customer value;
- general superiority of large editorial typography;
- a `comparative_validated` or `absorbed` pattern;
- permission to distribute or train on third-party screenshots.

The next promotion step is an independent same-input comparative evaluation on
a separate target, followed by a real product route only when a product owner
chooses one.
