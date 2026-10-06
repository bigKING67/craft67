# Product UI taste review

Use this when reviewing a concrete non-agent product UI for taste, clarity,
hierarchy, polish, or "why is this not 100/100 yet?" feedback.

This reference turns subjective design comments into a structured, actionable
review. It is not a replacement for project authority: live runtime evidence,
scoped project rules, `DESIGN.md`, tokens, components, and product context still
win over this generic rubric.

When the user needs concrete redesign direction, pair this with
`design-move-library.md`. When the issue is basic hierarchy, grouping,
alignment, repetition, or contrast, pair it with
`foundational-visual-principles.md`.

## Contents

- [When to use](#when-to-use)
- [Design read](#design-read)
- [Taste rules](#taste-rules)
- [Review dimensions](#review-dimensions)
- [Concrete calibration](#concrete-calibration)
- [100-point score](#100-point-score)
- [Evidence levels](#evidence-levels)
- [Severity](#severity)
- [Page-type checks](#page-type-checks)
- [Output contract](#output-contract)

## When to use

Use with `critique` when the user asks for:

- A UI score, taste score, or why a design did not get full marks.
- "Make it more premium", "not generic", "less demo-like", "more polished".
- Screenshot, Figma, component, page, dashboard, table, form, modal, settings,
  landing page, card/list, or navigation review.
- Concrete product UI design issues, not agentic planning UX.

Do not load this by default for every implementation task. Use it when a
judgment report or taste rubric will change the decision or acceptance criteria.
If context is incomplete, infer reasonable product defaults and keep moving
unless the missing answer would change the visual direction or risk profile.

## Design read

Start with one sentence:

`This should feel <tone> for <audience>, optimized for <primary job>, but <main mismatch>.`

Examples of tone: calm, precise, enterprise-grade, editorial, premium,
technical, playful, trustworthy, data-dense, minimal.

Then judge whether the visual language supports that impression. Common
mismatches: finance that feels playful, creative tools that feel corporate,
enterprise dashboards that feel demo-like, premium products with too many loud
borders/colors, productivity UI where decoration slows scanning, or data UI
without density and numeric-alignment discipline.

## Taste rules

- A tasteful interface knows what not to emphasize.
- Good design does not show less information; it shows information in the right
  order.
- White space explains relationships; it is not empty space.
- Amateur UI looks placed. Good UI looks composed.
- Consistency lets important differences stand out.
- Weak contrast feels timid; excessive contrast feels noisy.
- Composition turns a layout into a designed screen.
- Typography is the product voice.
- Expensive-looking UI usually uses less color, not more.
- Surface treatment should whisper structure, not shout decoration.
- Polish is the feeling that the interface anticipated what would happen.
- Inaccessible or edge-case-fragile design is unfinished design.

## Review dimensions

Score or comment only where relevant to the target:

1. **Design intent**: visual personality matches product category and audience.
2. **Task focus**: the main task, first focus, and primary action are obvious.
3. **Information order**: summary, details, advanced options, and actions follow
   the user's decision flow.
4. **Proximity**: related items are close; unrelated groups are separated.
5. **Alignment**: edges, baselines, control heights, numeric alignment, and
   grid axes feel composed rather than placed.
6. **Repetition**: similar meanings share type, spacing, color, radius, shadow,
   component variants, and state treatment.
7. **Contrast**: hierarchy, priority, action strength, and state changes are
   clearly different without becoming noisy.
8. **Composition**: page balance, focal point, density gradient, container
   width, and visual flow are intentional.
9. **Rhythm**: spacing and sizing create scan speed and breathing room.
10. **Typography**: type roles, scale, weight, line-height, line length, and
    numeric treatment match the job.
11. **Color**: color is restrained, semantic, accessible, and brand-consistent.
12. **Surface**: borders, shadows, radius, dividers, backgrounds, and elevation
    clarify layers without shouting decoration.
13. **Interaction polish**: hover, focus, active, selected, disabled, loading,
    empty, error, success, toast, modal, keyboard, and touch states are clear.
14. **Microcopy**: action labels, errors, empty states, success copy, and helper
    text reduce uncertainty.
15. **Accessibility**: contrast, labels, focus, keyboard, semantics, touch
    targets, color-only state, text scaling, and reduced motion are usable.
16. **Responsive and edge cases**: long text, translations, numbers, empty data,
    permissions, sticky elements, and narrow screens survive real content.
17. **Frontend craft**: tokens, layout primitives, component variants, semantic
    HTML, state models, responsive rules, and focus styles support the design.

## Concrete calibration

Use these as judgment anchors, not a substitute for the project's own tokens.

Spacing scale:

- 4px: tiny internal adjustment.
- 8px: tight relationship.
- 12px: compact component gap.
- 16px: normal component gap.
- 24px: group gap.
- 32px: section gap.
- 48px: major page gap.
- 64px or more: landing-page or editorial separation.

Type scale for product UI:

- 12px: captions and metadata.
- 14px: dense body and table text.
- 16px: standard body.
- 20px: section title.
- 24px: page title.
- 32px: hero or major title.

Color roles:

- Text primary, text secondary, text muted.
- Border subtle, border strong.
- Surface base, surface raised, background canvas.
- Primary action, primary hover.
- Danger, warning, success, info.

Surface roles:

- Flat surface: default content areas.
- Raised surface: cards, panels, popovers.
- Overlay surface: modals, dropdowns, drawers.
- Selected surface: active or chosen item.
- Muted surface: disabled or low-emphasis area.

Implementation smells that usually lower the score:

- Hardcoded spacing, color, radius, font size, or shadows where tokens exist.
- Fragile one-off margins or absolute positioning used for normal layout.
- Similar components with different anatomy or state behavior.
- Missing focus-visible, disabled, loading, empty, error, success, and long-text
  variants.
- Color-only state indication or semantic HTML omissions.

## 100-point score

Use this score for the concrete UI under review. Do not confuse it with
`scripts/design_craft_score.py --self`, which scores this workflow repo.
When the exact score is the main deliverable, also read
`taste-score-calibration.md` and label the evidence level before the score.

| Dimension | Points |
|---|---:|
| Design intent and taste direction | 10 |
| Task focus and attention control | 10 |
| Information order and structure | 10 |
| Proximity and grouping | 10 |
| Alignment and grid discipline | 10 |
| Repetition and system coherence | 10 |
| Contrast and hierarchy | 10 |
| Typography, color, and surface quality | 15 |
| Interaction polish and microcopy | 10 |
| Responsive robustness and frontend craft | 5 |

Maturity bands:

- 0-59: rough or unfinished.
- 60-74: functional but ordinary.
- 75-84: clean but generic.
- 85-92: polished and professional.
- 93-97: tasteful and refined.
- 98-100: exceptional, system-level design quality.

Use full marks only when the UI is excellent under real content, states,
accessibility, responsive behavior, and implementation discipline.

Scoring anchors:

- **10-point dimensions**: 10 means excellent and intentional; 7 means coherent
  with minor weakness; 4 means the idea exists but order or hierarchy is rough;
  1 means users cannot reliably understand the intended relationship or action.
- **15-point typography/color/surface dimension**: 15 means type, color, and
  surface all feel refined; 11 means mostly polished; 7 means functional but
  generic or rough; 3 means visually immature or inconsistent.
- **5-point responsive/frontend dimension**: 5 means robust under real content,
  devices, and implementation; 3 means mostly works with underdefined edges; 1
  means fragile layout or obvious implementation smells.

Deduct when present:

- Design intent: product-category mismatch, generic personality where the
  product needs character, decoration that does not support the job, accidental
  brand/type/surface choices.
- Task focus: weak primary action, secondary actions competing, critical
  decision information buried, decorative distraction, no clear focal point.
- Information order: summary/details not separated, advanced controls too early,
  vague labels, flat section weights, action before sufficient context.
- Proximity: related items separated, unrelated items too close, item and
  section gaps indistinguishable, detached helper/error text, ambiguous
  whitespace.
- Alignment: same-level edges drift, card padding differs, control baselines or
  heights differ, tables lack numeric/text alignment rules, too many axes.
- Repetition: inconsistent type scale, neutral shades, radius, borders, shadows,
  component variants, or states.
- Contrast: primary and secondary actions look similar, headings and body are
  too close, important data lacks emphasis, too many elements are emphasized,
  states are hard to distinguish.
- Typography/color/surface: hierarchy or tone is weak, color is noisy or
  arbitrary, heavy borders/shadows compensate for weak hierarchy, line-height or
  line length hurts reading, contrast is insufficient, radius/elevation does not
  match density.
- Interaction/microcopy: incomplete hover/focus/active/disabled states, weak
  loading/empty/error/success states, errors without recovery, vague button
  labels, distracting or missing motion.
- Responsive/frontend craft: unclear mobile behavior, long text overflow, empty
  or permission states missing, magic numbers instead of tokens, repeated
  one-off components.

## Evidence levels

Label the evidence level before the score:

- **L0 static**: screenshot, wireframe, or description only.
- **L1 contextual**: screenshot plus product/user/task context.
- **L2 browser**: browser screenshot plus DOM, computed style, or token
  evidence.
- **L3 resilient**: browser evidence across responsive sizes and important
  interaction states.
- **L4 before/after**: before/after evidence plus validation commands and
  implementation diff.

Do not claim hover, focus, loading, empty, error, keyboard, mobile, or
real-content behavior as verified unless the evidence level actually covers it.

## Severity

- **P0**: blocks understanding, task completion, accessibility, or safe use.
- **P1**: hurts hierarchy, trust, usability, or perceived quality.
- **P2**: hurts polish, consistency, or design maturity.
- **P3**: optional refinement.

## Page-type checks

- **Forms**: field order, local labels/help/errors, required/optional clarity,
  submit placement, destructive confirmation.
- **Tables**: decision-important columns first, right-aligned numbers, primary
  identifier scanability, relevant filters, empty/loading/error states.
- **Dashboards**: most important metric first, context/comparison/time range,
  charts answer questions, anomalies are distinct, detail path exists.
- **Cards/lists**: consistent anatomy, clear click behavior, title/metadata/body
  order, no over-cardification.
- **Modals**: one purpose, decision title, concise content, distinct actions,
  focus/escape/close/scroll behavior.
- **Navigation**: location is visible, labels are mutually exclusive, active
  state is clear, global/local/contextual navigation are not mixed.
- **Landing pages**: value promise, CTA hierarchy, proof sequence, generous
  rhythm, typography carries emotion, visuals support the argument.
- **Settings**: predictable categories, dangerous settings separated, toggle
  impact explained, save behavior clear, advanced options disclosed.

## Output contract

Default reviews should stop after the score, one-sentence diagnosis, design
direction, at most five blocking issues, at most five secondary issues, and the
smallest acceptance checklist. Target 150 lines or fewer.

When the user caps concrete recommendations, allocate the move budget across
the full decision chain. Do not produce two KPI/card moves while leaving a
blocking chart, generic insight copy, primary table/action problem, missing
state family, or responsive/accessibility risk without an implementing move.
Fold secondary CTA or shell refinements into the nearest structural move unless
they directly block the primary job. Before delivery, map each blocking finding
to a move or an explicit deferral.

Make visual-craft acceptance criteria observable. For each cited type,
contrast, spacing, border, radius, or elevation defect, name the affected role,
the project token or provisional measurable floor, and the expected hierarchy
change. When no stronger project authority exists, use 14px/1.4 as a provisional
floor for decision-bearing dense table text, keep 12-13px for secondary metadata
only, and require WCAG normal-text contrast. Do not accept "make typography more
readable", "improve contrast", or "tighten spacing" without these specifics.
Remove generic insight copy, or replace it with a named entity/segment, observed
count or threshold, business impact or urgency, owner or next action, and a
direct filter/action into the affected data.

Before delivery, run a coverage check against every explicit visual fact in the
input. If the review cites small type, low contrast, irregular spacing, numeric
alignment, or repeated border/radius/shadow treatment, at least one concrete
move must bind each cited defect to an observable acceptance condition; combine
related craft repairs inside one move rather than dropping them to stay under
the move budget. In the validation plan, inspect the current baseline first:
target viewport and fold, computed type/contrast, spacing/token use, and the
existing decision path. Validate a redesigned artifact only after that baseline
can support or overturn the diagnosis.

When the user explicitly asks for an exhaustive review or full scorecard, use
this expanded structure:

```markdown
Method: <single-context/degraded/dual-agent, truthfully stated>
Evidence level: L<0-4> - <what was actually checked>

## Overall Score

Score: __ / 100
Design maturity level: <band>

## One-Sentence Diagnosis

<main issue in one sentence>

## Design Direction

<intended visual direction>

## Top Issues

| Priority | Location | Category | Problem | Why It Hurts Taste | Recommendation | Acceptance Criteria |
|---|---|---|---|---|---|---|

## Detailed Review

### 1. Design Intent
### 2. Task Focus
### 3. Information Order
### 4. Proximity
### 5. Alignment
### 6. Repetition
### 7. Contrast
### 8. Composition
### 9. Rhythm
### 10. Typography
### 11. Color
### 12. Surface
### 13. Interaction Polish
### 14. Microcopy
### 15. Accessibility
### 16. Responsive and Edge Cases
### 17. Design Craft

## Redesign Recommendation

<page structure, hierarchy, spacing, typography, color, surface, component, state strategy>

## Concrete Before / After Suggestions

Before:
- <specific current issue>

After:
- <specific implementation-level improvement>

## Frontend Implementation Notes

- Tokens to add or reuse.
- Components or variants to standardize.
- Layout primitives to use.
- CSS smells to remove.
- Static scanner findings to address, if `design_craft_css_smell_scan.py`,
  `design_craft_focus_audit.py`, or `design_craft_token_audit.py` was used.
- Responsive and state behavior to cover.

## Acceptance Checklist

- [ ] Intended product feeling is clear.
- [ ] Primary task is obvious within 3 seconds.
- [ ] First visual focus is correct.
- [ ] Primary action dominates secondary actions without noise.
- [ ] Information follows user decision order.
- [ ] Related items are grouped; unrelated groups are separated.
- [ ] Layout has stable alignment axes.
- [ ] Similar components use the same rules.
- [ ] Typography hierarchy is clear.
- [ ] Color is restrained, semantic, and accessible.
- [ ] Surface treatment is subtle and consistent.
- [ ] Spacing creates rhythm and breathing room.
- [ ] Interactive states are visible and polished.
- [ ] Empty, loading, error, and success states are designed.
- [ ] Microcopy explains actions and recovery.
- [ ] UI remains accessible.
- [ ] UI works with real content and responsive layouts.
- [ ] Design tokens replace unjustified magic numbers.
- [ ] Components are reusable and maintainable.
```

Compress the detailed review when the target is small. Never hide a P0/P1 behind
decorative polish.
