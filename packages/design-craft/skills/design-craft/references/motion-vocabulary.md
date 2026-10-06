# Motion vocabulary

Use this when the user describes an animation vaguely and wants the right term,
for example "the popover grows out of the button", "the iOS pull past the edge
thing", "the cards appear one by one", or "an image turns into a card".

This reference is for naming and prompting. Do not turn a naming question into
an implementation plan unless the user asks for implementation.

## Contents

- [Output rule](#output-rule)
- [Glossary](#glossary)
- [Disambiguation examples](#disambiguation-examples)

## Output rule

Lead with the best term:

```markdown
**Stagger** — Animate several items one after another with a small delay between each, creating a cascade.
```

If several terms could fit, list the best match first and give one or two close
alternates with how they differ.

## Glossary

### Entrances and exits

- **Fade in / Fade out** — Element appears or disappears by changing opacity.
- **Slide in** — Element enters by sliding in from off-screen.
- **Scale in** — Element grows from smaller to full size, often paired with a fade.
- **Pop in** — Element appears with a slight overshoot.
- **Reveal** — Content is uncovered gradually, often with `clip-path` or a mask.
- **Enter / Exit** — The animation when an element is added to or removed from the screen.

### Sequencing and timing

- **Keyframes** — Defined animation points that the browser fills between.
- **Interpolation / Tween** — Generated in-between frames between start and end values.
- **Stagger** — Animate several items one after another with a small delay between each, creating a cascade.
- **Orchestration** — Deliberately timing multiple animations so they feel like one coordinated motion.
- **Delay** — Time before animation starts.
- **Duration** — How long animation takes.
- **Fill mode** — Whether the first or last frame persists before/after an animation.
- **Stepped animation** — Discrete-frame animation such as a countdown timer.

### Movement and transforms

- **Translate** — Move along the X or Y axis.
- **Scale** — Make bigger or smaller.
- **Rotate** — Spin around a point.
- **Skew** — Slant along an axis.
- **3D tilt / Flip** — Rotate in 3D space with `rotateX` or `rotateY`.
- **Perspective** — How strong the 3D depth effect appears.
- **Transform origin** — The anchor point a transform grows or rotates from.
- **Origin-aware animation** — An element animates out of its trigger, such as a popover growing from the button that opened it.

### State transitions

- **Crossfade** — One element fades out as another fades in at the same spot.
- **Continuity transition** — A change that visually connects before and after states.
- **Morph** — One shape smoothly turns into another.
- **Shared element transition** — An element travels and transforms from one position into another, such as a thumbnail expanding into a card.
- **Layout animation** — Size or position changes animate to a new layout instead of snapping.
- **Accordion / Collapse** — A section expands/collapses height to show or hide content.
- **Direction-aware transition** — Forward/back navigation animates in opposite directions.

### Scroll and navigation

- **Scroll reveal** — Elements fade or slide into place as they enter the viewport.
- **Scroll-driven animation** — Animation progress is tied to scroll position.
- **Parallax** — Background and foreground move at different speeds to create depth.
- **Page transition** — Animation during route/page navigation.
- **View transition** — Browser or app transition that morphs between states/pages.

### Interaction feedback

- **Hover effect** — Visual change when cursor moves over an element.
- **Press / Tap feedback** — Subtle scale or state change when clicked/tapped.
- **Hold to confirm** — A progress effect fills while the user holds a button.
- **Drag** — Move an element by grabbing it.
- **Drag to reorder** — Drag a list item while others shift.
- **Swipe to dismiss** — Drag an element off-screen to close it.
- **Rubber-banding** — Resistance and snap-back when dragging past a boundary.
- **Shake / Wiggle** — Side-to-side error or rejection signal.
- **Ripple** — Circle expands from tap point to confirm a press.

### Easing and springs

- **Easing** — How speed changes over time.
- **Ease-out** — Starts fast and ends slow; default for most UI response.
- **Ease-in** — Starts slow and ends fast; usually avoided for UI interactions.
- **Ease-in-out** — Slow, fast, slow; useful for movement already on screen.
- **Linear** — Constant speed; use for spinners, progress, marquees.
- **Cubic-bezier** — Custom easing curve.
- **Asymmetric easing** — Acceleration/deceleration differ for a livelier feel.
- **Spring** — Physics-based motion using tension, mass, damping, or bounce.
- **Stiffness / Tension** — How strongly a spring pulls toward its target;
  higher values usually feel snappier.
- **Damping** — How quickly a spring settles; lower damping permits more
  overshoot and oscillation.
- **Mass** — How heavy the animated value behaves; more mass resists changes in
  velocity.
- **Bounce** — Spring overshoot used to add a restrained physical or playful
  response.
- **Perceptual duration** — The time at which a spring appears finished even
  though very small settling may continue.
- **Momentum** — Motion carries velocity after drag or interruption.
- **Velocity** — Speed plus direction at an instant, commonly handed from a
  gesture into its release animation.
- **Interruptible animation** — Motion can redirect mid-flight instead of finishing first.

### Looping and ambient motion

- **Marquee** — Content travels continuously through a repeating viewport.
- **Loop** — An animation repeats a fixed number of times or indefinitely.
- **Alternate / Yoyo** — A loop reverses direction each cycle instead of
  jumping to the first frame.
- **Orbit** — An element circles another element or focal point.
- **Pulse** — Repeating scale or opacity change used to draw attention.
- **Float** — Gentle continuous drift that makes an object feel suspended.
- **Idle animation** — Subtle autonomous motion while an element is waiting for
  interaction.

### Effects and polish

- **Blur** — Softens/masks imperfect transitions.
- **Clip-path** — Clips a shape for reveals, masks, and before/after sliders.
- **Mask** — Hides/reveals with a shape or gradient, often softer than clip-path.
- **Before / after slider** — Draggable divider wipes between two overlaid images.
- **Line drawing** — SVG path appears as if traced by a pen.
- **Text morph** — Text changes character by character.
- **Skeleton / Shimmer** — Placeholder with moving sheen while content loads.
- **Number ticker** — Digits roll or count to a value.
- **Tabular numbers** — Fixed-width digits so values do not shift.
- **Typewriter** — Text appears one character at a time.

### Performance concepts

- **Frame rate / FPS** — Frames drawn per second; 60fps is the common baseline.
- **Jank** — Visible stutter from dropped frames.
- **Dropped frame** — Browser misses a draw deadline.
- **Compositing** — GPU moves/fades an element without layout/paint.
- **will-change** — Hint that an element will animate soon.
- **Layout thrashing** — Layout reads/writes or layout-property animations force repeated recalculation.

### Animation principles

- **Purposeful animation** — Motion explains state, relationship, continuity,
  or feedback instead of decorating by default.
- **Anticipation** — A small preparatory movement hints at the action that will
  follow.
- **Follow-through** — Secondary parts continue and settle after the primary
  movement, adding weight.
- **Squash and stretch** — Shape deformation communicates weight, impact, speed,
  or flexibility.
- **Perceived performance** — Motion changes how fast a response feels without
  changing the underlying work duration.
- **Frequency of use** — Repeated interactions need shorter, subtler motion than
  rare or explanatory moments.
- **Spatial consistency** — Enter, change, and exit paths preserve where an
  object came from and where it goes.
- **Hardware acceleration** — Browser/runtime execution that can update an
  eligible visual property without repeating full layout and paint; it must be
  observed rather than inferred from one property name.
- **Reduced Motion** — A user preference and behavior contract that removes or
  reduces vestibular travel while preserving necessary feedback.

## Disambiguation examples

- "Grows out of the button" -> **Origin-aware animation**, not generic scale-in.
- "One image turns into another" -> **Morph** if the shape changes; **crossfade**
  if they fade over each other; **shared element transition** if it moves from
  one layout position to another.
- "Cards appear one by one" -> **Stagger**.
- "iOS pull too far and snap back" -> **Rubber-banding**.
- "Page connects the old card to the new page" -> **Shared element transition**
  or **view transition**, depending on whether browser View Transitions API is
  involved.
