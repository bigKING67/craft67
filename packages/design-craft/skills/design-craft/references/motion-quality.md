# Motion quality

Use this when a task touches animation, transitions, hover/press feedback,
toasts, popovers, drawers, gestures, page transitions, perceived performance, or
when the user says motion feels weird, slow, flashy, dizzy, or janky.

For direct manipulation, drag/swipe, interruptible sheets, momentum, or
rubber-banding, also read `interaction-physics.md`.
For a whole-codebase motion inventory and implementation-plan workflow, read
`motion-audit-planning.md` instead of expanding a single-interaction review.
For concrete web recipes such as anchored overlays, tooltip groups,
`@starting-style`, percentage transforms, clip-path reveals, and transient UI
lifecycle handling, also read `motion-patterns.md`.

This is a local `design-craft` fusion of Emil Kowalski-style design engineering
motion rules with the existing project-authority workflow. It is not a universal
animation aesthetic. Live runtime behavior, scoped project rules, product
context, and `DESIGN.md` still win.

## Contents

- [Should this animate?](#first-question-should-this-animate)
- [Timing and easing](#timing-and-easing)
- [Physicality](#physicality)
- [Interruptibility](#interruptibility)
- [Gesture craft](#gesture-craft)
- [Performance](#performance)
- [Accessibility](#accessibility)
- [Review format](#review-format)
- [Debugging checklist](#debugging-checklist)

## First question: should this animate?

Motion needs a reason. Valid reasons:

- Spatial consistency: preserve where something came from or where it goes.
- State indication: show a clear state change.
- Explanation: make a concept understandable.
- Feedback: confirm the interface heard an input.
- Jarring-change prevention: avoid abrupt add/remove/swap behavior.

Frequency decides restraint:

| Frequency | Decision |
| --- | --- |
| 100+ times/day, keyboard shortcuts, command palette toggles | Default to no travel or delay; keep only immediate causal feedback when it improves comprehension. |
| Tens/day, hover effects, list navigation | Usually remove or sharply reduce decorative motion. |
| Occasional, modals, drawers, toasts | Standard animation. |
| Rare or first-time, onboarding, feedback, celebrations | Delight is allowed. |

If the purpose is only "looks cool" and the user will see it often, delete or
reduce the motion.

## Timing and easing

Default UI motion should feel responsive, not cinematic.

| Element | Duration |
| --- | --- |
| Button or press feedback | `100-160ms` |
| Tooltip or small popover | `125-200ms` |
| Dropdown or select | `150-250ms` |
| Modal or drawer | `200-500ms` |
| Marketing or explanatory motion | Can be longer when it does not block use |

Rules:

- Most UI animations should stay under `300ms`.
- Use strong `ease-out` for entering, exiting, and user-triggered response.
- Use `ease-in-out` for objects moving or morphing on screen.
- Use `ease` for simple hover/color changes.
- Use `linear` only for constant motion such as spinners, progress, or marquees.
- Avoid `ease-in` for UI interactions; it delays the moment users watch most.

Useful custom curves:

```css
--ease-out: cubic-bezier(0.23, 1, 0.32, 1);
--ease-in-out: cubic-bezier(0.77, 0, 0.175, 1);
--ease-drawer: cubic-bezier(0.32, 0.72, 0, 1);
```

Do not invent curves from scratch when a known curve fits. Tune to the product
personality: a professional dashboard should be crisp; a playful tool can carry
more bounce.

## Physicality

- Avoid `scale(0)` for ordinary product UI entrances. Start around
  `scale(0.9-0.97)` plus opacity unless a project-authorized expressive motion
  language and runtime evidence justify a different treatment.
- Popovers, dropdowns, and tooltips should scale from their trigger, not the
  center. Use framework transform-origin variables when available.
- Modals are the exception: centered overlays can keep `transform-origin:
  center`.
- Pressable elements should usually have subtle active feedback, such as
  `transform: scale(0.97)` over about `160ms`.
- Group entrances should stagger by `30-80ms` only when the sequence helps
  comprehension; never block interaction while a stagger plays.

## Interruptibility

Rapidly-triggered UI should retarget smoothly.

- Prefer CSS transitions for dynamic add/remove/toggle UI that users do not
  physically grab; transitions can retarget simple visual state.
- Avoid keyframes for toasts, toggles, and anything users can trigger rapidly;
  keyframes tend to restart from zero.
- Use springs or equivalent native interactive animation for drag, velocity,
  gesture reversal, and any object that can be grabbed mid-flight.
- Start an interrupted interaction from the presentation/on-screen value and
  preserve current velocity. Never jump from the previous logical target.
- Keep bounce subtle (`0.1-0.3`) and avoid it in serious, data-dense surfaces.
- Use `@starting-style` for entry animation when browser support allows; use a
  mounted/data attribute fallback only when needed.

## Gesture craft

- Respond on pointer/touch down and track continuously after the intent
  threshold.
- Preserve the grab offset so the object does not snap under the finger.
- Dismiss by velocity as well as distance; a quick flick should count.
- When the product's interaction semantics are momentum-based, choose snap
  targets from a bounded projected endpoint rather than only the release point.
  Otherwise preserve the project-owned target-selection rule and treat
  projection as a separately authorized behavior change, not automatic polish.
  In either case, make the proposed calculation auditable: state velocity units,
  projection horizon/decay, clamping, and the separation between computing an
  endpoint and using it to choose a target.
- Apply damping or friction beyond natural boundaries instead of hard stops.
- Capture pointer events once a drag starts.
- Ignore additional touch points after the initial drag begins.
- Test gesture motion on a real device when the result depends on touch feel.
- Treat `8-12px`/pt/dp as a starting hysteresis range, not a universal magic
  number; tune with the platform and target size.

## Performance

- Prefer animating `transform` and `opacity`.
- Avoid animating layout properties such as `width`, `height`, `margin`,
  `padding`, `top`, and `left`, especially on repeated elements.
- Avoid `transition: all` and broad Tailwind `transition-all` on large surfaces
  or hot paths.
- Use `will-change` sparingly; remove it if it does not improve measured
  smoothness.
- Avoid updating a CSS variable on a parent to drive child transforms in large
  trees; it can trigger broad style recalculation.
- Predetermined motion should prefer CSS or WAAPI. JS/rAF-driven motion and
  animation libraries are appropriate for dynamic, gesture-driven, or
  interruptible cases, but measure under load when smoothness matters.
- Never make content inaccessible or invisible until JavaScript animation starts.

## Accessibility

- Honor `prefers-reduced-motion`. Reduced motion means gentler and less
  positional movement, not necessarily zero change; opacity/color transitions
  that aid comprehension can remain.
- Gate hover motion with `@media (hover: hover) and (pointer: fine)` so touch
  devices do not get sticky hover behavior.
- Keep focus-visible states clear even when hover/press motion is reduced.
- On iOS/Android, read the system Reduce Motion/Remove animations setting;
  Reduced Transparency and increased contrast remain separate requirements.

## Evidence language

Static source can prove property choice, input ownership, timing configuration,
missing branches, and whether work is structurally unbounded. It cannot prove
that motion *will feel* laggy, jumpy, smooth, heavy, or responsive. Until a
pointer trace, computed-style inspection, browser performance capture, or
representative device run observes the effect, describe those outcomes as
risks or hypotheses and name the decisive runtime check. Do not pair a
definitive feel claim with a later disclaimer that feel was unverified.

## Review format

For a normal motion review, lead with one verdict, no more than five blocking
findings, and no more than eight concrete moves. Target 150 lines or fewer;
expand into a full property-by-property audit only when requested.

Use:

| Before | After | Why |
| --- | --- | --- |
| `transition: all 300ms` | `transition: transform 180ms var(--ease-out)` | Limit animated properties and keep the response crisp. |
| `scale(0)` entry | `scale(0.95)` plus opacity | Elements should not appear from nothing. |
| `ease-in` dropdown | strong `ease-out` | Users need immediate response at the start. |

Then give a verdict:

- **Block**: feel-breaking regression, motion that delays a high-frequency or
  keyboard action, unjustified `scale(0)`, `ease-in` UI response, costly
  layout-property animation on a hot path, or missing reduced-motion behavior
  on meaningful movement.
- **Approve**: purpose is clear, frequency is appropriate, timing/easing are
  within bounds, motion is interruptible where needed, performance risk is
  controlled, and accessibility is handled.

## Debugging checklist

- Slow motion: temporarily increase duration 2-5x or use DevTools animation
  inspector.
- Frame-by-frame: inspect easing, transform-origin, opacity/transform sync, and
  color crossfades.
- Under load: test while the page is loading or while data-heavy views render.
- Real devices: verify drawers, swipe, and touch gestures on hardware when
  possible.
