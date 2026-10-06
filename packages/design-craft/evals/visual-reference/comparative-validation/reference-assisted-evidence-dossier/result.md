# Result: reference-assisted-evidence-dossier

## Outcome

The pre-registered controlled comparison passes. On the separate Cairn target,
the reference-assisted variant strengthens the promise-to-evidence scan path
and deliberately moves complete evidence ahead of explanation on mobile. It
preserves the same content, semantic DOM, controls, states, exception count,
and design authority, with no observed P0/P1 issue.

This is repository-local prototype evidence. It is an independent target from
the earlier Reviewlane fixture, but not an independent human judgment or a
production product route.

## Controlled comparison

| Criterion | Baseline | Reference-assisted | Decision |
|---|---|---|---|
| Promise to evidence | Proposition, support, action, and a neighboring dossier are all visible, but read as two competent peers | Proposition establishes the question; decision posture and the ruled dossier become the next evidence field | Improved |
| Primary scan path | Proposition -> explanation/action, with proof beside it on desktop and after it on mobile | Proposition -> posture/proof -> explanation/action | Improved |
| Exception visibility | `3 open` appears with the dossier evidence | The same `3 open` value and decision treatment remain visible; no certainty was invented | Preserved |
| Mobile priority | Proof begins at `y=647.10` and continues beyond the `844px` viewport | Complete proof moves to `y=413.50` through `y=760.92`, before explanation and action | Improved |
| Functional and state parity | Shared document, controls, JavaScript, and six query states | Shared document, controls, JavaScript, and six query states | Preserved |
| Authority and source boundary | Cairn authority | Cairn authority; no source copy, asset, identity, data, or exact geometry | Preserved |

Both final desktop and mobile phases report
`horizontal_overflow=false`. The assisted intermediate `768x900` check also
reports no overflow. At mobile size, both variants passed `default`, `loading`,
`empty`, `error`, `success`, and `long` state checks with one `h1`, one `main`,
no duplicate IDs, no unnamed controls, and the complete long label retained.

## Interaction and accessibility evidence

- Native-dialog entry focus lands on `Close sample dossier`; closing returns
  focus to `Open sample dossier`. A live failure in the initial close path was
  fixed and retested in the same managed browser run.
- Error retry enters `loading` with `aria-busy=true`, then returns to `default`
  with the recovery control hidden and status restored.
- Real Tab traversal reached skip link, header navigation, commercial action,
  dossier action, method action, and the first native disclosure control in
  logical order.
- The DOM audit found one `h1`, expected landmarks, two live regions, no
  duplicate IDs, and no unnamed visible controls.
- Reduced Motion produced visible content with no transform, automatic scroll
  behavior, and zero active animations.
- Seven key text/token pairs measured from `4.67:1` to `12.87:1`. This is a
  bounded token check, not a full automated contrast audit.
- No screen-reader or other assistive-technology session was run.

## Performance observation

Three repeated warm-cache local navigations per variant reported `CLS=0`, zero
long tasks, two resources, 167 DOM nodes, and no overflow. Median observed DCL
was `191.9ms` for baseline and `192.9ms` for assisted; median load was
`241.8ms` and `242.1ms` respectively. Paint timing was unavailable in the
background navigation series, so this is only local regression evidence, not
production performance evidence.

## Visual review

The final desktop/mobile comparison and assisted evidence, method, questions,
and pilot sections were visually inspected. The ruled dossier, mineral-paper
palette, restrained status colors, editorial hierarchy, and native disclosure
grammar remain internally consistent. No P0/P1 visual issue remains.

Retained P2 boundaries:

- Assisted mobile defers explanation and the primary action below the first
  viewport. Apply the mechanism only when concrete evidence should precede
  immediate conversion or when required context is not being hidden.
- Cairn's editorial display scale is suitable for this persuasive surface, not
  a universal rule for operational interfaces.
- External PNGs remain under Browser67 retention. The repository preserves
  verified paths, hashes, dimensions, layout metrics, and run identity rather
  than redistributing screenshots.

## Evidence

- `screenshots.json`: strict `design-craft.l4-screenshots.v1` manifest for four
  final captures, healthy transport, completed run, and scoped cleanup.
- `browser-checks.json`: viewports, states, interaction, accessibility,
  performance, and visual-review observations.
- `reference-pack.json`: the ready structure/responsive Pack.
- `experiment.md`: question, fixed variables, negative controls, criteria, and
  decision rule recorded before comparison.
- Browser run:
  `browser67://runs/design-craft/20260817T060232364Z-6a6a4ed2`.

## Promotion boundary

The evidence supports two deliberately different promotions:

1. `proof-led-trust-sequencing` gains this result as its first bounded
   `target_validation_ref` and advances only to `project_validated`. It had no
   target-validation prerequisite before this experiment, so the same result
   is not double-counted as comparative evidence.
2. `desktop-mobile-priority-reordering` already had target validation on the
   separate Reviewlane fixture. This pre-registered Cairn comparison becomes a
   `comparative_eval_ref`, advancing it to `comparative_validated`.

`typographic-single-focus-entry` remains `proposed`; this experiment did not
isolate typography as the causal variable. No hypothesis becomes `absorbed`.
The result does not establish production conversion, customer value, browser
matrix coverage, assistive-technology compatibility, or general human
preference.
