# Taste score calibration

Use this with `product-ui-taste-review.md` when the user asks for a numeric UI
taste score, "why not 100", or a before/after taste delta.

This reference calibrates the score. It does not replace live evidence, project
`DESIGN.md`, scoped rules, or the detailed product UI rubric.

## Evidence levels

- **L0 static**: one screenshot, screenshot crop, wireframe, or prose
  description. Score visual order and obvious UI taste only. Do not verify
  hover, focus, loading, error, empty, responsive, keyboard, or real-content
  behavior.
- **L1 contextual**: screenshot plus product context, target user, primary job,
  and known data semantics. Score confidence is higher, but states are still
  unverified.
- **L2 browser**: browser screenshot plus DOM/computed-style or token evidence.
  You may judge actual spacing, type, color, and rendered state more firmly.
- **L3 resilient**: browser evidence across desktop/mobile and key interaction
  states. You may score responsive, focus, loading, empty, and error behavior.
- **L4 before/after**: L3 evidence plus before/after screenshots, validation
  commands, and implementation diff. Use for claimed quality improvement.

Always label the evidence level before the score.

## Score bands

| Score | Band | Calibration |
|---:|---|---|
| 0-59 | Rough / unfinished | Users cannot reliably understand, trust, or complete the main task. |
| 60-74 | Functional but ordinary | Basic task flow works, but hierarchy, spacing, copy, states, or system rules are rough. |
| 75-84 | Clean but generic | The UI is usable and tidy, but product judgment is weak, hierarchy is flat, or components feel assembled. |
| 85-92 | Polished and professional | Clear hierarchy, coherent system, good density, and credible product fit; still has visible refinement gaps. |
| 93-97 | Tasteful and refined | Strong product judgment, resilient states, disciplined implementation, and refined type/color/surface details. |
| 98-100 | Exceptional | System-level design quality under real content, states, accessibility, responsive behavior, and implementation evidence. |

## Common anchors

- **72-78**: generic AI landing page with attractive color but weak message,
  overused gradients, vague CTA hierarchy, and no proof sequence.
- **78-84**: clean admin dashboard with good grid alignment but flat priority,
  card soup, generic surfaces, and weak risk/status emphasis.
- **84-88**: solid product table or form with clear anatomy and states, but
  some copy, density, or responsive gaps.
- **88-92**: mature enterprise or data surface with strong task hierarchy,
  compact metrics, clear status semantics, accessible states, and disciplined
  component rules.
- **93-96**: refined surface where composition, typography, color, surface,
  states, content, and frontend implementation all reinforce the product job.

## Anti-inflation rules

- Do not score above 84 when the main issue is a flat hierarchy or card soup.
- Do not score above 88 from a static screenshot if interaction states,
  responsive behavior, and real-content edge cases are important but unverified.
- Do not score above 92 without evidence that empty/loading/error/focus/mobile
  states are designed and implemented.
- Do not score above 95 unless the UI has a strong product-specific visual
  language, not only clean spacing and consistent components.
- Do not assign 98-100 without L4-style evidence or an explicitly narrow static
  visual-slice scope.

## Score explanation format

Use this compact explanation when a full table is unnecessary:

```markdown
Evidence level: L<0-4> - <what was verified>
Product UI taste score: __ / 100
Band: <band>
Why this score:
- + <main strength>
- - <main deduction>
- - <main deduction>
Not scored as verified:
- <states or evidence not checked>
```
