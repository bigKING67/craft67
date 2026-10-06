# Web motion implementation patterns

Use this when implementing concrete web motion after the project authority and
`motion-quality.md` have established that the motion should exist. These are
small recipes, not a replacement for the project's component library, motion
tokens, accessibility behavior, or runtime evidence.

For drag, swipe, momentum, interruption, or direct manipulation, use
`interaction-physics.md` instead of treating these CSS recipes as a gesture
engine.

## Contents

- [Press feedback](#press-feedback)
- [Anchored overlays](#anchored-overlays)
- [Tooltip groups](#tooltip-groups)
- [Interruptible enter and exit](#interruptible-enter-and-exit)
- [Percentage transforms and clip-path](#percentage-transforms-and-clip-path)
- [Crossfade repair](#crossfade-repair)
- [Transient UI lifecycle](#transient-ui-lifecycle)
- [Verification](#verification)

## Press feedback

Use subtle pointer-down feedback when it matches the component grammar. Do not
replace a visible focus state, loading state, or disabled state with motion.

```css
.pressable {
  transition: transform 140ms var(--motion-ease-out);
}

.pressable:active:not(:disabled) {
  transform: scale(0.97);
}

@media (prefers-reduced-motion: reduce) {
  .pressable {
    transition-property: color, background-color, border-color;
  }

  .pressable:active:not(:disabled) {
    transform: none;
  }
}
```

If drag translation and press scale both need `transform`, put them on separate
wrapper layers or compose them under one explicit owner. Never let one silently
replace the other.

## Anchored overlays

Popover, dropdown, menu, and tooltip motion should preserve the relationship to
the trigger. Prefer the positioning library's computed origin rather than a
hand-written guess.

```css
.popover {
  transform-origin: var(--radix-popover-content-transform-origin);
  transition:
    opacity 160ms var(--motion-ease-out),
    transform 160ms var(--motion-ease-out);
}

.popover[data-state="open"] {
  opacity: 1;
  transform: scale(1);
}

@starting-style {
  .popover[data-state="open"] {
    opacity: 0;
    transform: scale(0.96);
  }
}
```

For Base UI or another primitive, use its equivalent origin variable. Keep a
fallback only when the supported browser matrix requires one. A centered modal
is not trigger-anchored and may correctly retain a centered origin.

## Tooltip groups

The first tooltip in a group may use an intent delay to avoid accidental
activation. Once one tooltip is open, moving across adjacent triggers should
skip the remaining delay and entrance motion when the component library
supports a tooltip-provider or instant-phase contract.

```css
.tooltip[data-instant] {
  transition-duration: 0ms;
}
```

Do not reimplement tooltip semantics merely to get this animation behavior.
Keep the library's accessible name, hover/focus opening, dismissal, collision,
and pointer-rest behavior. Prefer an official `skipDelayDuration`, provider, or
instant-phase API over an application-global boolean.

## Interruptible enter and exit

Use transitions for rapidly retargeted visual state that users do not
physically grab. The browser can continue from the current interpolated value;
fixed keyframes commonly restart their declared sequence.

```css
.toast {
  opacity: 1;
  transform: translateY(0);
  transition:
    opacity 180ms var(--motion-ease-out),
    transform 180ms var(--motion-ease-out);
}

.toast[data-state="closed"] {
  opacity: 0;
  transform: translateY(25%);
}
```

Do not infer gesture-grade interruption or velocity continuity from a CSS
transition. A draggable toast or sheet still needs the presentation-value and
velocity contract in `interaction-physics.md`.

## Percentage transforms and clip-path

Transform percentages are relative to the element's own box, which is useful
when content height is unknown:

```css
.drawer[data-state="closed"] {
  transform: translateY(100%);
}
```

`clip-path: inset()` can express a reveal, hold-progress overlay, or comparison
wipe without hard-coded pixel offsets:

```css
.reveal {
  clip-path: inset(0 0 100% 0);
  transition: clip-path 240ms var(--motion-ease-in-out);
}

.reveal[data-visible="true"] {
  clip-path: inset(0 0 0 0);
}

.comparison-before {
  clip-path: inset(0 var(--comparison-inset) 0 0);
}
```

`clip-path` is a technique, not proof of compositor-only execution. Profile the
actual browser, element size, and update frequency when it is on a hot path.

## Crossfade repair

First fix state ownership, alignment, timing, and opacity overlap. If an
observed crossfade still reads as two separate objects, a very small temporary
blur can visually bridge the states:

```css
.state-layer {
  transition:
    opacity 180ms var(--motion-ease-out),
    filter 180ms var(--motion-ease-out);
}

.state-layer[data-transitioning="true"] {
  opacity: 0.7;
  filter: blur(2px);
}
```

Treat blur as a last-mile repair. `filter` may add paint/compositing cost, can
hurt text legibility, and must not conceal a broken state transition. Keep it
small and verify Safari and lower-end hardware when the surface is large.

## Transient UI lifecycle

Polished transient components handle invisible edge cases:

- Pause toast, tooltip, or undo timers while `document.visibilityState` is
  `hidden`; resume from remaining time on `visibilitychange` rather than
  expiring unseen.
- Preserve a continuous pointer hit region across animated gaps in stacked
  transient UI. A pseudo-element bridge is often safer than changing layout.
- Keep dismissal, focus restoration, announcements, and Escape behavior
  correct when an enter or exit animation is interrupted.
- Use pointer capture and the direct-manipulation contract for swipe dismissal;
  do not infer a valid drag from an animated transform alone.

## Verification

- Trigger each state repeatedly and reverse it mid-transition.
- Inspect `transform-origin` at different collision/placement sides.
- Move across a tooltip group with pointer and keyboard focus.
- Hide and restore the document while a transient timer is active.
- Toggle Reduced Motion and confirm causal feedback remains without travel.
- Use slow motion or frame-by-frame inspection for coordinated properties.
- Record runtime performance claims only after a trace or representative device
  observation; static CSS does not prove smoothness or compositing.
