# Blind comparative judgment
Judge only the supplied outputs. Do not infer which skill produced a label. Apply the machine-readable scorecard exactly, recompute each total from criterion points, and return only JSON matching the supplied schema.

## Task prompt

# Motion-system audit and implementation planning

Audit the following static project evidence and produce an implementation-ready
motion improvement roadmap. Do not edit files, create plans on disk, or claim
browser/device validation. Do not name, cite, or reveal any skill, repository,
author, or upstream source in the response; the output will be judged blind.

Product context:

- Surface: a calm desktop operations console used throughout the workday.
- Primary users: keyboard-heavy support and revenue operators.
- Motion purpose: preserve causality and state continuity without slowing task
  throughput.
- Existing authority: `DESIGN.md` requires crisp motion, existing semantic
  tokens, visible focus, and a Reduced Motion path that preserves feedback.
- Available evidence: only the snippets below. No runtime, computed-style,
  trace, screen recording, accessibility-tree, or user test was performed.

Current excerpts:

```css
/* src/styles/motion.css */
:root {
  --duration-fast: 160ms;
  --duration-panel: 240ms;
  --ease-responsive: cubic-bezier(0.23, 1, 0.32, 1);
}

.popover {
  transform-origin: center;
  transition: all 360ms ease-in;
}
```

```tsx
// src/components/CommandPalette.tsx
export function CommandPalette({ open }: { open: boolean }) {
  return (
    <div
      data-open={open}
      className="animate-[palette_420ms_ease-in_both]"
    >
      <SearchResults />
    </div>
  );
}
```

```css
/* src/components/toast.css */
@keyframes toast-enter {
  from { top: -24px; opacity: 0; }
  to { top: 0; opacity: 1; }
}

.toast {
  animation: toast-enter 500ms ease-in forwards;
}
```

```tsx
// src/components/SortableQueue.tsx
function onPointerMove(event: PointerEvent) {
  queueRef.current?.style.setProperty("--drag-y", `${event.clientY}px`);
}

function onPointerUp() {
  setDragging(false);
  animateTo(nearestSlot(currentY), { duration: 400 });
}
```

```css
/* src/components/Button.css - existing correct local precedent */
.button {
  transition: transform var(--duration-fast) var(--ease-responsive);
}

.button:active {
  transform: scale(0.98);
}

@media (prefers-reduced-motion: reduce) {
  .button { transition-duration: 80ms; }
}
```

Return:

1. A concise recon summary: stack signals, where motion lives, existing
   conventions, product personality, frequency map, and evidence level.
2. A vetted priority table with at most six findings and no unsupported runtime
   claims.
3. At most three self-contained implementation plans. Each plan must include
   exact file paths/current excerpts, target behavior, project conventions,
   ordered steps, hard boundaries, mechanical checks, runtime/feel checks,
   Reduced Motion behavior, and a source-drift stop condition.
4. A short recommended execution order and explicitly unverified states.

Stay within 180 lines. Prefer a small set of high-leverage plans over a padded
inventory.


## Human-readable scorecard

# Blind scorecard

Grade anonymized raw outputs. Do not reward brand, tone, or skill-name mentions.

| Criterion | Weight | Full-credit evidence |
|---|---:|---|
| Evidence honesty and recon | 15 | Maps the static motion surface and labels every runtime/feel claim as unverified. |
| Project conventions | 10 | Reuses the supplied tokens and correct local precedent instead of inventing a parallel system. |
| Purpose and frequency | 10 | Prioritizes keyboard/high-frequency restraint and causal feedback over decoration. |
| Technical accuracy | 15 | Correctly diagnoses property cost, origin, interruption, pointer tracking, and keyframe/transition tradeoffs without framework myths. |
| Prioritization | 10 | Vets and ranks a small set by user impact, frequency, confidence, and cost. |
| Plan self-containment | 20 | Plans include exact paths/excerpts, target behavior, steps, boundaries, and drift stop conditions. |
| Verification quality | 10 | Gives targeted mechanical plus browser/slow-motion/interruption feel checks without claiming they ran. |
| Accessibility and performance | 10 | Provides Reduced Motion behavior and measured performance checks while preserving useful feedback. |

Total: 100.


## Machine-readable scorecard

```json
{
  "schema": "design-craft.comparative-scorecard.v1",
  "total": 100,
  "criteria": [
    {
      "id": "evidence_recon",
      "label": "Evidence honesty and recon",
      "weight": 15,
      "full_credit": "Maps the static motion surface and labels every runtime or feel claim as unverified."
    },
    {
      "id": "project_conventions",
      "label": "Project conventions",
      "weight": 10,
      "full_credit": "Reuses supplied tokens and the correct local precedent instead of inventing a parallel system."
    },
    {
      "id": "purpose_frequency",
      "label": "Purpose and frequency",
      "weight": 10,
      "full_credit": "Prioritizes keyboard and high-frequency restraint plus causal feedback over decoration."
    },
    {
      "id": "technical_accuracy",
      "label": "Technical accuracy",
      "weight": 15,
      "full_credit": "Diagnoses property cost, origin, interruption, pointer tracking, and primitive tradeoffs without framework myths."
    },
    {
      "id": "prioritization",
      "label": "Prioritization",
      "weight": 10,
      "full_credit": "Vets and ranks a small set by user impact, frequency, confidence, and implementation cost."
    },
    {
      "id": "plan_self_containment",
      "label": "Plan self-containment",
      "weight": 20,
      "full_credit": "Plans include exact paths and excerpts, target behavior, steps, boundaries, and drift stop conditions."
    },
    {
      "id": "verification_quality",
      "label": "Verification quality",
      "weight": 10,
      "full_credit": "Provides targeted mechanical and runtime feel checks without claiming those checks ran."
    },
    {
      "id": "accessibility_performance",
      "label": "Accessibility and performance",
      "weight": 10,
      "full_credit": "Defines Reduced Motion behavior and measured performance checks while preserving useful feedback."
    }
  ]
}
```

## Required judgment schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["results", "winner", "rationale"],
  "properties": {
    "results": {
      "type": "array",
      "minItems": 3,
      "maxItems": 3,
      "items": {
        "type": "object",
        "required": ["label", "criteria", "total", "summary"],
        "properties": {
          "label": {"enum": ["A", "B", "C"]},
          "criteria": {
            "type": "object",
            "required": [
              "evidence_recon",
              "project_conventions",
              "purpose_frequency",
              "technical_accuracy",
              "prioritization",
              "plan_self_containment",
              "verification_quality",
              "accessibility_performance"
            ],
            "additionalProperties": false,
            "properties": {
              "evidence_recon": {"type": "integer", "minimum": 0, "maximum": 15},
              "project_conventions": {"type": "integer", "minimum": 0, "maximum": 10},
              "purpose_frequency": {"type": "integer", "minimum": 0, "maximum": 10},
              "technical_accuracy": {"type": "integer", "minimum": 0, "maximum": 15},
              "prioritization": {"type": "integer", "minimum": 0, "maximum": 10},
              "plan_self_containment": {"type": "integer", "minimum": 0, "maximum": 20},
              "verification_quality": {"type": "integer", "minimum": 0, "maximum": 10},
              "accessibility_performance": {"type": "integer", "minimum": 0, "maximum": 10}
            }
          },
          "total": {"type": "integer", "minimum": 0, "maximum": 100},
          "summary": {"type": "string", "minLength": 20}
        },
        "additionalProperties": false
      }
    },
    "winner": {"enum": ["A", "B", "C"]},
    "rationale": {"type": "string", "minLength": 40}
  },
  "additionalProperties": false
}
```

## Output A

## 1. Recon summary

**Stack signals**
- Frontend surface uses TSX components plus CSS.
- Motion is currently split across:
  - global tokens in `src/styles/motion.css`
  - component-local CSS in `src/components/toast.css`
  - utility/arbitrary animation syntax in `CommandPalette.tsx`
  - imperative pointer/animation logic in `SortableQueue.tsx`

**Where motion lives**
- Semantic motion tokens exist:
  - `--duration-fast: 160ms`
  - `--duration-panel: 240ms`
  - `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)`
- Component-level motion also exists outside those tokens:
  - `.popover` uses `transition: all 360ms ease-in`
  - command palette uses `animate-[palette_420ms_ease-in_both]`
  - toast uses `top` animation for `500ms ease-in`
  - sortable queue uses imperative `animateTo(..., { duration: 400 })`

**Existing conventions**
- The button precedent is the strongest local standard:
  - transform-only interaction
  - semantic duration/easing tokens
  - explicit Reduced Motion handling
  - short active feedback: `160ms`, reduced to `80ms`
- Existing design authority requires crisp motion, semantic tokens, visible focus, and Reduced Motion paths that still preserve feedback.

**Product personality**
- Calm, all-day desktop operations console.
- Motion should clarify causality and state continuity, not feel decorative.
- Keyboard-heavy support/revenue workflows imply frequent transitions must be short, predictable, and interruptible.

**Frequency map**
| Surface | Expected frequency | Motion sensitivity |
|---|---:|---|
| Button active state | Very high | Already aligned with precedent |
| Command palette | High | Should feel instant; slow entry can tax keyboard-heavy users |
| Popovers | High | Needs crisp open/close and no broad `all` transitions |
| Toasts | Medium | Should notify without shifting layout or lingering |
| Sortable queue drag settle | Episodic but high-salience | Needs spatial continuity without sluggish snap-back |

**Evidence level**
- Static excerpt audit only.
- No runtime, computed-style, trace, screen recording, accessibility-tree, device, or user-test evidence.
- Findings are based on explicit source patterns, not observed runtime behavior.

---

## 2. Priority table

| Priority | Finding | Evidence | Risk | Recommended direction |
|---:|---|---|---|---|
| P0 | Reduced Motion coverage is inconsistent | Only `.button` excerpt shows `@media (prefers-reduced-motion: reduce)` | Users requesting reduced motion may still receive long entrance/settle animations | Add reduced paths for popover, palette, toast, and sortable settle |
| P0 | High-frequency UI uses non-tokenized slow easing | Palette `420ms ease-in`; popover `360ms ease-in`; toast `500ms ease-in`; sortable `400` | Motions may feel delayed for keyboard-heavy workflows | Move to `--duration-fast`, `--duration-panel`, `--ease-responsive` |
| P1 | `.popover` uses `transition: all` | `transition: all 360ms ease-in` | Unintended properties may animate; harder to reason about state changes | Limit to `opacity`, `transform`, possibly `visibility`/discrete state handling |
| P1 | Toast animates layout-affecting `top` | `from { top: -24px } to { top: 0 }` | Potential layout/reflow cost and less crisp motion | Use `transform: translateY(...)` plus `opacity` |
| P1 | Command palette uses arbitrary animation declaration inline | `className="animate-[palette_420ms_ease-in_both]"` | Bypasses semantic tokens and makes Reduced Motion harder to centralize | Replace with semantic class/data-state styling |
| P2 | Sortable settle duration appears fixed and long | `animateTo(nearestSlot(currentY), { duration: 400 })` | Drag release can feel sluggish, especially over short distances | Use shorter token-aligned settle duration with reduced-motion path |

---

## 3. Implementation plans

### Plan A — Normalize global motion tokens and popover behavior

**Files / current excerpts**

`src/styles/motion.css`

```css
:root {
  --duration-fast: 160ms;
  --duration-panel: 240ms;
  --ease-responsive: cubic-bezier(0.23, 1, 0.32, 1);
}

.popover {
  transform-origin: center;
  transition: all 360ms ease-in;
}
```

**Target behavior**
- Popovers open/close crisply using only `opacity` and `transform`.
- Duration aligns with existing semantic tokens.
- Reduced Motion keeps state feedback but shortens or removes spatial travel.
- No broad `transition: all`.

**Project conventions to follow**
- Reuse existing token names.
- Match the button precedent: transform-based motion, tokenized duration/easing, explicit Reduced Motion.
- Preserve visible focus behavior; do not animate focus outlines away.

**Ordered steps**
1. Keep existing root tokens unless broader project inspection shows canonical alternatives.
2. Replace `.popover` transition with explicit properties:
   - `opacity`
   - `transform`
3. Use:
   - `var(--duration-panel)` for panel/popover entry where continuity matters
   - `var(--ease-responsive)` for the easing curve
4. Add or align state selectors using existing markup conventions if present, for example:
   - `[data-open="true"]`
   - `[data-open="false"]`
   - existing open/closed classes if the real file uses them
5. Use a small transform distance/scale only if already present in surrounding code; otherwise prefer opacity plus subtle scale/translate.
6. Add Reduced Motion branch:
   - keep opacity feedback
   - reduce duration to `80ms` or equivalent local precedent
   - avoid scale/translate travel

**Hard boundaries**
- Do not introduce a new animation library.
- Do not rename existing tokens unless all usages are updated deliberately.
- Do not alter layout, z-index, focus management, or popover positioning.
- Do not use `transition: all`.

**Mechanical checks**
- Search for:
  - `transition: all`
  - `ease-in`
  - `360ms`
  - `.popover`
- Run the closest available lint/type/style check.
- Confirm CSS parses after media-query additions.

**Runtime / feel checks to perform later**
- Open/close popovers with mouse and keyboard.
- Confirm focus ring remains visible and not delayed.
- Confirm rapid repeated open/close does not feel queued or sticky.
- Confirm Reduced Motion still gives clear visibility feedback.

**Reduced Motion behavior**
- Duration: `80ms` preferred, matching the button precedent.
- Animate opacity only, or use effectively no transform travel.
- Preserve open/closed feedback; do not silently remove all state change indication.

**Source-drift stop condition**
- Stop and re-audit if `src/styles/motion.css` no longer contains the shown token block or `.popover` has moved to a component-specific implementation.
- Stop if popover state is controlled by a framework animation API rather than CSS state selectors.

---

### Plan B — Convert command palette and toast to semantic, tokenized component motion

**Files / current excerpts**

`src/components/CommandPalette.tsx`

```tsx
export function CommandPalette({ open }: { open: boolean }) {
  return (
    <div
      data-open={open}
      className="animate-[palette_420ms_ease-in_both]"
    >
      <SearchResults />
    </div>
  );
}
```

`src/components/toast.css`

```css
@keyframes toast-enter {
  from { top: -24px; opacity: 0; }
  to { top: 0; opacity: 1; }
}

.toast {
  animation: toast-enter 500ms ease-in forwards;
}
```

**Target behavior**
- Command palette appears quickly enough for keyboard-heavy use.
- Toast enters without animating layout-affecting properties.
- Both use semantic durations/easing.
- Both have explicit Reduced Motion behavior.

**Project conventions to follow**
- Prefer named classes and state attributes over arbitrary inline animation values for reusable UI.
- Use existing semantic tokens:
  - `--duration-fast`
  - `--duration-panel`
  - `--ease-responsive`
- Preserve state continuity but avoid decorative delay.

**Ordered steps**
1. Replace the command palette arbitrary animation class with a semantic class, for example:
   - `className="command-palette"`
   - keep `data-open={open}`
2. Define command palette motion in the appropriate existing stylesheet, preferably the file already responsible for shared motion if command palette has no local CSS.
3. Use data-state styling:
   - closed: slightly offset or scaled only if needed, `opacity: 0`
   - open: settled transform, `opacity: 1`
4. Use `var(--duration-panel)` for palette open/close unless product review prefers `--duration-fast`.
5. Replace toast `top` keyframes with transform/opacity keyframes:
   - from: `transform: translateY(-8px); opacity: 0`
   - to: `transform: translateY(0); opacity: 1`
6. Reduce toast duration from `500ms` to tokenized `var(--duration-panel)` or shorter if local notification precedent exists.
7. Add Reduced Motion media query for both:
   - command palette: `80ms` opacity transition, no spatial travel
   - toast: `80ms` opacity transition/animation, no vertical travel

**Hard boundaries**
- Do not change command execution, search behavior, result rendering, or keyboard shortcuts.
- Do not alter toast stacking, dismissal timing, live-region behavior, or content.
- Do not add decorative bounce, overshoot, blur, or spring effects.
- Do not remove `data-open` unless replacing it with an already-established state convention.

**Mechanical checks**
- Search for:
  - `animate-[palette_420ms_ease-in_both]`
  - `toast-enter`
  - `top: -24px`
  - `500ms ease-in`
  - `prefers-reduced-motion`
- Run type-check for TSX changes.
- Run CSS/style validation if available.
- Confirm no unused class or missing stylesheet import is introduced.

**Runtime / feel checks to perform later**
- Open the command palette repeatedly from keyboard shortcut.
- Type immediately after opening; confirm visual motion does not compete with input.
- Trigger multiple toasts; confirm entry does not push layout unexpectedly.
- Check both normal and Reduced Motion settings.
- Confirm no focus outline or active input state is obscured during palette entry.

**Reduced Motion behavior**
- Command palette:
  - keep immediate visibility/opacity feedback
  - no scale or translate travel
  - duration around `80ms`
- Toast:
  - opacity-only feedback
  - no `top` or translate movement
  - duration around `80ms`
- Feedback remains present; it is shortened/simplified, not removed entirely.

**Source-drift stop condition**
- Stop and re-audit if the command palette no longer uses the shown arbitrary animation class.
- Stop if toast positioning depends on `top` for actual layout placement rather than only animation.
- Stop if a centralized animation/state utility already governs palette or toast behavior elsewhere.

---

### Plan C — Make sortable queue drag settle responsive, short, and Reduced-Motion aware

**File / current excerpt**

`src/components/SortableQueue.tsx`

```tsx
function onPointerMove(event: PointerEvent) {
  queueRef.current?.style.setProperty("--drag-y", `${event.clientY}px`);
}

function onPointerUp() {
  setDragging(false);
  animateTo(nearestSlot(currentY), { duration: 400 });
}
```

**Target behavior**
- Drag motion follows the pointer with direct causality.
- Release-to-slot settle is short and clear, not sluggish.
- Reduced Motion preserves final placement feedback with minimal travel.
- Pointer-move writes avoid unnecessary work where feasible.

**Project conventions to follow**
- Keep motion crisp and token-aligned.
- Use transform-based rendering downstream where `--drag-y` is consumed.
- Avoid introducing broad abstractions for one interaction.
- Preserve throughput for operators manipulating queues.

**Ordered steps**
1. Inspect how `--drag-y`, `currentY`, `nearestSlot`, and `animateTo` are used before changing behavior.
2. Confirm whether `--drag-y` drives `transform` rather than layout properties.
3. If pointer events can fire faster than paint, gate style writes with `requestAnimationFrame`:
   - store latest `clientY`
   - write `--drag-y` once per frame
   - cancel pending frame on unmount/end if needed
4. Replace fixed `400` duration with token-aligned logic:
   - default settle: around `var(--duration-fast)` / `160ms`
   - allow up to `var(--duration-panel)` / `240ms` only for longer travel if distance-based duration already fits existing code
5. Use the existing responsive easing curve if `animateTo` accepts easing.
6. Add Reduced Motion branch:
   - snap or near-snap to nearest slot
   - optional `80ms` opacity/position confirmation if the API supports it
7. Ensure `setDragging(false)` does not remove required visual state before the settle animation can communicate placement.

**Hard boundaries**
- Do not rewrite sorting logic.
- Do not change queue ordering semantics.
- Do not change pointer capture, selection, or keyboard reordering behavior unless directly required by existing code.
- Do not introduce physics/spring behavior unless already used locally.
- Do not animate layout properties if the current implementation can use transform.

**Mechanical checks**
- Search for:
  - `animateTo(`
  - `--drag-y`
  - `nearestSlot`
  - `currentY`
  - `prefers-reduced-motion`
- Type-check after TSX changes.
- If adding `requestAnimationFrame`, verify cleanup paths for pointer up/cancel/unmount.
- Confirm constants are not duplicated if motion tokens already have a JS bridge.

**Runtime / feel checks to perform later**
- Drag short and long distances; release near and between slots.
- Confirm settle feels immediate but still communicates destination.
- Stress rapid drag/release sequences.
- Test pointer cancel/escape cases if supported.
- Check Reduced Motion behavior.

**Reduced Motion behavior**
- Prefer immediate placement or `80ms` maximum settle.
- Avoid animated travel over distance.
- Preserve visible final-state confirmation, such as stable slot placement or opacity/state change.

**Source-drift stop condition**
- Stop and re-audit if `animateTo` is not a local helper or its API does not accept duration/easing as shown.
- Stop if `--drag-y` is consumed by `top`, `margin`, or layout instead of transform; that becomes a broader performance/layout fix.
- Stop if sortable behavior is shared by multiple queue components and requires a common interaction contract.

---

## 4. Recommended execution order

1. **Plan A first** — establish global motion hygiene and remove the broadest risky pattern: `transition: all`.
2. **Plan B second** — fix two visible, frequent surfaces by replacing slow/non-tokenized entrance animations.
3. **Plan C third** — tune the more interaction-specific sortable queue after confirming how its animation helper and CSS variable are consumed.

This order moves from lowest dependency / broadest convention alignment to the most behavior-sensitive interaction.

---

## Explicitly unverified states

- No browser rendering or computed styles were inspected.
- No device, refresh-rate, or reduced-motion OS setting was tested.
- No screen recording, performance trace, or paint/layout profile was captured.
- No accessibility tree or keyboard-flow validation was performed.
- No confirmation that `top` animation currently causes measurable layout cost at runtime.
- No confirmation that `--drag-y` is consumed by transform rather than layout.
- No confirmation of existing stylesheet imports or animation utility APIs beyond the provided snippets.
- No user testing or operator throughput measurement was performed.


## Output B

## 1. Recon summary

- **Stack signals:** React/TSX components, CSS files, Tailwind-style arbitrary animation class (`animate-[...]`), CSS custom-property motion tokens, and at least one JS animation call (`animateTo`).
- **Where motion lives:**  
  - Global tokens/keyframes: `src/styles/motion.css`  
  - Component-local CSS: `src/components/toast.css`, `src/components/Button.css`  
  - Inline utility animation: `src/components/CommandPalette.tsx`  
  - Gesture/reorder logic: `src/components/SortableQueue.tsx`
- **Existing conventions:** semantic duration/easing tokens exist:
  - `--duration-fast: 160ms`
  - `--duration-panel: 240ms`
  - `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)`
  - Local good precedent: button transitions only `transform`, uses tokens, keeps Reduced Motion feedback at `80ms`.
- **Product personality:** calm desktop operations console; motion should be crisp, causal, low-latency, and non-decorative.
- **Frequency map from evidence only:**  
  - High: command palette, queue sorting/dragging, buttons, likely popovers.  
  - Medium: toast notifications.  
  - Unknown: exact popover frequency and queue size.
- **Evidence level:** static snippets only. No runtime, computed style, trace, screen recording, accessibility-tree, device, browser, or user testing was performed.

---

## 2. Vetted priority table

| # | Priority | Category | Location | Finding | Fix summary |
|---|---:|---|---|---|---|
| 1 | High | Throughput / easing | `src/components/CommandPalette.tsx` | `animate-[palette_420ms_ease-in_both]` is long and accelerating for a keyboard-heavy surface. Static evidence supports mismatch with existing `160ms/240ms` responsive tokens. | Replace arbitrary `420ms ease-in` with tokenized opacity/transform motion, fast enough for keyboard invocation, with Reduced Motion path. |
| 2 | High | Cohesion / performance risk | `src/styles/motion.css` | `.popover { transition: all 360ms ease-in; }` uses `transition: all`, non-token duration, and `ease-in`. This can animate unintended properties and diverges from existing tokens. | Limit transition to `opacity, transform`; use existing tokens/easing; add Reduced Motion duration. |
| 3 | High | Gesture responsiveness | `src/components/SortableQueue.tsx` | Pointer movement writes on every `pointermove`, and release animation is hard-coded to `400ms` with no visible easing or Reduced Motion handling in the snippet. | Gate pointer writes with `requestAnimationFrame`, make snap animation tokenized/interruptible, and shorten Reduced Motion snap. |
| 4 | Medium | Layout-affecting animation | `src/components/toast.css` | Toast animates `top` for `500ms ease-in`. Static evidence shows non-token timing/easing and a layout-position property instead of transform. | Animate `transform` + `opacity` using `--duration-panel` / `--ease-responsive`; preserve final layout position. |
| 5 | Medium | Accessibility consistency | Multiple snippets | Reduced Motion is present in `Button.css` but not visible in popover, command palette, toast, or queue snippets. | Add per-surface Reduced Motion behavior that preserves feedback while reducing travel/duration. |
| 6 | Low | Token hygiene | Multiple snippets | Motion values are split between semantic tokens and one-off literals: `360ms`, `420ms`, `500ms`, `400ms`, `ease-in`. | Prefer existing semantic tokens; introduce new tokens only if a repeated need appears after implementation. |

---

## 3. Implementation plans

### Plan A — Tokenize high-frequency overlay motion

**Files / current excerpts**

`src/styles/motion.css`

```css
:root {
  --duration-fast: 160ms;
  --duration-panel: 240ms;
  --ease-responsive: cubic-bezier(0.23, 1, 0.32, 1);
}

.popover {
  transform-origin: center;
  transition: all 360ms ease-in;
}
```

`src/components/CommandPalette.tsx`

```tsx
export function CommandPalette({ open }: { open: boolean }) {
  return (
    <div
      data-open={open}
      className="animate-[palette_420ms_ease-in_both]"
    >
      <SearchResults />
    </div>
  );
}
```

**Target behavior**

- Popovers and command palette should appear causally and finish quickly.
- Use opacity + small transform only.
- No `ease-in`, no `transition: all`, no `420ms` keyboard-blocking feel.
- Closed state should remain visually distinct if the element stays mounted.
- Reduced Motion should keep opacity feedback and minimize/remove travel.

**Project conventions to preserve**

- Reuse `--duration-fast`, `--duration-panel`, and `--ease-responsive`.
- Follow the good local precedent in `Button.css`: tokenized transition, scoped property, Reduced Motion duration around `80ms`.
- Preserve visible focus and command-palette keyboard behavior; this plan is motion-only.

**Ordered steps**

1. In `src/styles/motion.css`, replace `.popover` transition with scoped properties:
   - `opacity var(--duration-fast) var(--ease-responsive)`
   - `transform var(--duration-fast) var(--ease-responsive)`
2. Keep or adjust `transform-origin` only if it matches the popover’s anchor. If the trigger/anchor origin is not available from static CSS, keep `center` rather than inventing placement logic.
3. Add `[data-open="true"]` / `[data-open="false"]` states for popover only if the existing markup already uses `data-open`; otherwise do not broaden scope.
4. Replace the command-palette arbitrary animation with a named class, for example `commandPaletteMotion`, defined in `src/styles/motion.css`.
5. In `CommandPalette.tsx`, change only the class assignment, preserving `data-open={open}` and children.
6. Define command-palette motion around:
   - open: `opacity: 1; transform: translateY(0) scale(1)`
   - closed: `opacity: 0; transform: translateY(-4px) scale(0.985)`
   - transition: `opacity var(--duration-fast) var(--ease-responsive), transform var(--duration-fast) var(--ease-responsive)`
7. Add Reduced Motion media rule:
   - transition duration: `80ms`
   - remove transform travel: `transform: none` for both open and closed states, while preserving opacity feedback.

**Hard boundaries**

- Do not change command search behavior, focus management, keyboard shortcuts, or mounting/unmounting semantics.
- Do not add a new animation library.
- Do not introduce new global tokens unless a second implemented surface requires the same new value.
- Do not claim the origin is wrong without inspecting actual popover placement.

**Mechanical checks**

- Search touched files for `420ms`, `360ms`, `ease-in`, and `transition: all`; none should remain for these two surfaces unless unrelated.
- Confirm all new CSS uses existing tokens.
- Run the project’s closest lint/type-check command.
- Confirm `prefers-reduced-motion: reduce` exists for the new/changed selectors.

**Runtime / feel checks to perform after implementation**

- Open/close command palette repeatedly from keyboard; it should feel immediate, not theatrical.
- Check rapid toggling; no queued animation should visibly fight the latest state.
- Open popovers from pointer and keyboard if applicable; motion should clarify origin without delaying selection.
- Use slow-motion/devtools animation inspection if available to confirm opacity/transform only.

**Reduced Motion behavior**

- Keep feedback through opacity.
- Remove positional travel and scale.
- Use `80ms` duration, matching the local button precedent.

**Source-drift stop condition**

- Stop and refresh the plan if `CommandPalette.tsx` no longer contains `data-open={open}` or the arbitrary `animate-[palette_420ms_ease-in_both]`, or if `.popover` no longer contains `transition: all 360ms ease-in`.

---

### Plan B — Convert toast entrance to transform-based token motion

**File / current excerpt**

`src/components/toast.css`

```css
@keyframes toast-enter {
  from { top: -24px; opacity: 0; }
  to { top: 0; opacity: 1; }
}

.toast {
  animation: toast-enter 500ms ease-in forwards;
}
```

**Target behavior**

- Toasts should enter clearly but not linger.
- Avoid animating `top`; use `transform` and `opacity`.
- Use existing semantic timing/easing.
- Reduced Motion should preserve appearance feedback without spatial travel.

**Project conventions to preserve**

- Use existing motion tokens from `src/styles/motion.css`.
- Match the crisp, calm console personality.
- Keep the toast’s final layout position equivalent to the current `top: 0` end state.

**Ordered steps**

1. Replace keyframes with transform-based motion:
   - from: `transform: translateY(-8px); opacity: 0;`
   - to: `transform: translateY(0); opacity: 1;`
2. Replace animation timing:
   - `animation: toast-enter var(--duration-panel) var(--ease-responsive) forwards;`
3. Ensure the resting `.toast` layout still positions the toast where `top: 0` previously ended. If positioning rules live elsewhere, do not move them into this file unless necessary.
4. Add a Reduced Motion media rule:
   - keyframe or override should remove `translateY`
   - duration should be `80ms`
   - opacity feedback should remain.
5. Optional only if consistent with existing CSS style: add `will-change: transform, opacity` to `.toast`, but avoid leaving it on long-lived idle elements if toasts persist for a long time.

**Hard boundaries**

- Do not change toast queueing, dismissal, stacking, timers, or ARIA/live-region behavior.
- Do not alter toast copy, severity styling, or placement.
- Do not add a spring/JS animation library for this CSS-only surface.

**Mechanical checks**

- Confirm `top` is no longer animated inside `@keyframes toast-enter`.
- Confirm `500ms` and `ease-in` are removed from `src/components/toast.css`.
- Confirm `prefers-reduced-motion: reduce` exists in this file or an imported global equivalent covers `.toast`.
- Run the closest CSS/lint/build/type-check command available.

**Runtime / feel checks to perform after implementation**

- Trigger a single toast; it should be noticeable but finish quickly.
- Trigger multiple toasts; stacking should not jump or reflow unexpectedly.
- Trigger a toast while using keyboard focus elsewhere; focus visibility should not be obscured or delayed.
- In Reduced Motion mode, verify the toast still appears with clear feedback.

**Reduced Motion behavior**

- Duration: `80ms`.
- No vertical travel.
- Opacity may transition from `0` to `1`.

**Source-drift stop condition**

- Stop and refresh the plan if `toast-enter` no longer animates `top`, if `.toast` no longer owns the entrance animation, or if toast positioning has moved to another file.

---

### Plan C — Make queue drag updates lightweight and snap motion interruptible

**File / current excerpt**

`src/components/SortableQueue.tsx`

```tsx
function onPointerMove(event: PointerEvent) {
  queueRef.current?.style.setProperty("--drag-y", `${event.clientY}px`);
}

function onPointerUp() {
  setDragging(false);
  animateTo(nearestSlot(currentY), { duration: 400 });
}
```

**Target behavior**

- Drag movement should track the pointer directly without decorative lag.
- Pointer-move writes should be coalesced to animation frames.
- Release snap should be short, token-aligned, and interruptible by a new drag.
- Reduced Motion should keep state feedback but minimize travel time.

**Project conventions to preserve**

- Prefer existing duration semantics:
  - normal snap: `160ms` / `--duration-fast`
  - larger panel-style moves only if existing queue slots are visually large and testing supports `240ms`
- Use `--ease-responsive` if the animation API accepts CSS easing strings.
- Do not create unrelated queue behavior changes.

**Ordered steps**

1. Inspect the full `SortableQueue.tsx` before editing to find:
   - where `currentY` is updated
   - how `animateTo` is defined/imported
   - whether existing cleanup occurs on unmount
   - how `--drag-y` is consumed in CSS.
2. Add local refs for pointer coalescing:
   - latest pointer Y
   - pending `requestAnimationFrame` id
3. Change `onPointerMove` so it stores the latest `event.clientY` and schedules one `requestAnimationFrame` write if none is pending.
4. Inside the frame callback, write only the latest Y to `--drag-y`, then clear the pending frame id.
5. On `pointerup`, cancel any pending frame before starting snap.
6. Replace hard-coded release duration `400` with token-aligned timing:
   - normal: `160`
   - Reduced Motion: `80`
7. Pass easing if `animateTo` supports it:
   - `ease: "cubic-bezier(0.23, 1, 0.32, 1)"`
8. Ensure a new pointer down cancels or supersedes any in-flight snap animation if the existing animation API provides cancellation.
9. If `animateTo` does not support easing/cancellation, do not invent a wrapper blindly; document the limitation in the implementation notes and only change duration/RM handling.

**Hard boundaries**

- Do not rewrite queue ordering logic.
- Do not change `nearestSlot` semantics.
- Do not change data persistence or selection state.
- Do not add virtualization or list architecture changes in this plan.
- Do not assume `--drag-y` is transform-backed; verify its CSS usage first.

**Mechanical checks**

- Confirm `duration: 400` is removed or replaced for this release snap.
- Confirm `requestAnimationFrame` cleanup exists for pending pointer writes.
- Confirm Reduced Motion is checked via CSS media, `matchMedia`, or an existing project hook if one exists.
- Run type-check/lint for the component.
- Search for other `animateTo(... { duration: 400 })` only to avoid creating inconsistent duplicate queue behavior; do not broaden fixes without review.

**Runtime / feel checks to perform after implementation**

- Drag slowly and quickly; item should remain attached to pointer with no visible delayed easing during drag.
- Release near adjacent slots; snap should complete quickly and preserve causality.
- Start a second drag during a snap; latest user input should win.
- Test with a long queue if available; no obvious dropped interaction should appear.
- In Reduced Motion mode, release should still show completion feedback but with shortened travel/time.

**Reduced Motion behavior**

- Drag tracking remains direct.
- Release snap uses `80ms`.
- Avoid added bounce, overshoot, or large travel embellishment.

**Source-drift stop condition**

- Stop and refresh the plan if `onPointerMove`, `onPointerUp`, `animateTo`, or `--drag-y` usage has changed materially, or if `animateTo` already provides tokenized/cancelable motion elsewhere.

---

## 4. Recommended execution order

1. **Plan A** — highest leverage for keyboard-heavy daily use and fixes global overlay conventions.
2. **Plan C** — important for direct-manipulation responsiveness and hot-path pointer work.
3. **Plan B** — contained polish/performance/accessibility improvement for notifications.

## Explicitly unverified states

- No browser/runtime validation was performed.
- No computed styles were inspected.
- No actual import graph or CSS cascade was verified.
- No accessibility tree or focus behavior was tested.
- No frame timing, performance trace, or device testing was performed.
- Popover anchor/origin correctness is unknown from the snippet alone.
- Queue size, `animateTo` API capabilities, and `--drag-y` CSS consumption are unknown.

Guardrails applied: minimal-scope root-cause planning, frontend accessibility/design-authority alignment, and render-performance caution.


## Output C

Motion diagnosis: the snippets show a calm operations console with good token precedent, but several high-frequency or repeated motions bypass that system with slower `ease-in`, broad/property-unsafe animation, and incomplete Reduced Motion evidence.

## 1. Recon summary

- **Stack signals**: React/TSX components plus CSS/Tailwind-style arbitrary animation classes. Motion appears in global CSS, component CSS, JSX classes, and imperative pointer handling.
- **Where motion lives**:
  - `src/styles/motion.css`: semantic duration/easing tokens and `.popover`.
  - `src/components/CommandPalette.tsx`: arbitrary animation class.
  - `src/components/toast.css`: keyframed toast entry.
  - `src/components/SortableQueue.tsx`: pointer-driven drag and snap animation.
  - `src/components/Button.css`: correct local precedent.
- **Existing conventions**:
  - Tokens: `--duration-fast: 160ms`, `--duration-panel: 240ms`, `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)`.
  - Correct precedent: button animates only `transform`, uses the responsive easing token, and has a Reduced Motion branch that preserves feedback.
- **Product personality**: calm, crisp, low-distraction desktop operations tooling; motion should clarify state and causality without slowing keyboard-heavy throughput.
- **Frequency map**:
  - Very high: command palette, keyboard interactions, sortable queue during repeated operational work.
  - Medium: popovers/dropdowns.
  - Occasional but repeated: toasts.
  - Micro-feedback: buttons/press states.
- **Evidence level**: static snippets only. No computed style, runtime behavior, browser trace, device feel, accessibility tree, or user testing was performed.

## 2. Vetted priority table

| Priority | Evidence | Location | Finding | Smallest safe correction |
|---|---|---|---|---|
| P1 | `animate-[palette_420ms_ease-in_both]` | `src/components/CommandPalette.tsx` | Command palette is likely high-frequency/keyboard-heavy, but uses a long `420ms` `ease-in` keyframe-like animation outside the token system. Static evidence cannot prove felt delay, but the value conflicts with the crisp-motion requirement. | Replace with tokenized state transition around `160–240ms`, responsive/ease-out-like token, and explicit Reduced Motion behavior. |
| P1 | `animateTo(nearestSlot(currentY), { duration: 400 })` plus pointer updates | `src/components/SortableQueue.tsx` | Direct manipulation snap uses a fixed-duration settle with no visible velocity handoff, presentation-value interruption, pointer capture, or grab-offset evidence in the snippet. Static evidence cannot prove broken feel, but this is the highest-risk interaction class. | Preserve current `nearestSlot` semantics initially; harden coordinate space, grab offset, interruption, and reduced-motion settle behavior before considering momentum target changes. |
| P2 | `top` keyframes, `500ms ease-in` | `src/components/toast.css` | Toast entry animates layout-position property and is long/ease-in for an operational console. Static evidence supports performance risk, not measured jank. | Animate `transform` + `opacity`, use `--duration-panel` and `--ease-responsive`, add Reduced Motion branch with no vertical travel. |
| P2 | `transition: all 360ms ease-in; transform-origin: center;` | `src/styles/motion.css` | Popover uses broad property ownership, slow `ease-in`, and center origin. Center origin may be correct only for centered overlays; anchored popovers usually need trigger-relative origin. | Restrict to `opacity, transform`; use token timing; verify whether this is anchored or centered before changing origin. |
| P2 | Tokens and good button precedent exist, but other snippets bypass them | multiple | Motion vocabulary is fragmented: arbitrary durations/easing and component-local keyframes compete with semantic tokens. | Normalize the cited surfaces to existing tokens before adding new motion primitives. |
| P3 | Reduced Motion shown only in button excerpt | multiple | Reduced Motion path is not evidenced for palette, popover, toast, or queue. This is absence of evidence in snippets, not proof of absence globally. | Add per-surface reduced branches that remove large travel while preserving opacity/focus/static feedback. |

## 3. Implementation plans

### Plan A — Normalize overlay and command-palette motion

**Files / current excerpts**

`src/styles/motion.css`

```css
:root {
  --duration-fast: 160ms;
  --duration-panel: 240ms;
  --ease-responsive: cubic-bezier(0.23, 1, 0.32, 1);
}

.popover {
  transform-origin: center;
  transition: all 360ms ease-in;
}
```

`src/components/CommandPalette.tsx`

```tsx
export function CommandPalette({ open }: { open: boolean }) {
  return (
    <div
      data-open={open}
      className="animate-[palette_420ms_ease-in_both]"
    >
      <SearchResults />
    </div>
  );
}
```

**Target behavior**

- Command palette opens/closes with immediate, crisp feedback suitable for keyboard-heavy use.
- Popovers use property-specific transitions and semantic tokens.
- No `ease-in` for initial UI response.
- Center origin remains only if the popover is truly centered; anchored popovers use trigger/placement-relative origin if such placement data exists.
- Reduced Motion removes scale/travel and keeps short opacity/state feedback.

**Project conventions to follow**

- Prefer `--duration-fast`, `--duration-panel`, and `--ease-responsive`.
- Follow the button precedent: animate explicit properties, not `all`; preserve feedback under Reduced Motion.

**Ordered steps**

1. Inspect the actual `palette` keyframes before editing. If they include non-opacity/transform behavior required for state continuity, stop and re-scope.
2. In `src/components/CommandPalette.tsx`, replace the arbitrary animation class with a stable semantic class while preserving `data-open={open}`, for example:
   ```tsx
   className="commandPalette"
   ```
3. In the existing loaded CSS surface, preferably `src/styles/motion.css`, add state rules:
   ```css
   .commandPalette {
     opacity: 0;
     transform: translateY(-4px) scale(0.98);
     transition:
       opacity var(--duration-fast) var(--ease-responsive),
       transform var(--duration-fast) var(--ease-responsive);
   }

   .commandPalette[data-open="true"] {
     opacity: 1;
     transform: translateY(0) scale(1);
   }
   ```
   If mount/unmount timing means closed state is never present, use the project’s existing mounted-state pattern instead of inventing lifecycle code.
4. Change `.popover` to explicit properties:
   ```css
   .popover {
     transform-origin: center;
     transition:
       opacity var(--duration-panel) var(--ease-responsive),
       transform var(--duration-panel) var(--ease-responsive);
   }
   ```
5. Verify whether `.popover` is used for anchored popovers or centered overlays:
   - If centered modal-like overlay: keep `transform-origin: center`.
   - If anchored to a trigger: replace center origin with the project’s placement variable or placement classes; do not guess coordinates.
6. Add Reduced Motion:
   ```css
   @media (prefers-reduced-motion: reduce) {
     .commandPalette {
       transform: none;
       transition:
         opacity 80ms var(--ease-responsive);
     }

     .popover {
       transition-duration: 80ms;
     }
   }
   ```

**Hard boundaries**

- Do not alter `SearchResults` behavior, filtering, focus management, or command execution.
- Do not add a motion dependency.
- Do not change popover placement logic unless source already exposes placement/origin data.
- Do not remove visible focus styles.

**Mechanical checks**

```bash
npm run lint
npm run typecheck
```

If the project uses a different package manager or script names, run the equivalent existing lint/typecheck scripts from `package.json`.

**Runtime / feel checks required before approval**

- Open and close command palette via keyboard repeatedly.
- Confirm perceived response starts immediately and does not block typing.
- Interrupt open/close rapidly and confirm no visual jump or stale keyframe restart.
- Open representative popovers from each placement and confirm origin matches spatial cause.
- Check focus ring remains visible during and after animation.

**Reduced Motion behavior**

- Palette: no vertical/scale travel; opacity/state feedback remains around `80ms`.
- Popover: no large positional movement; opacity/instant state feedback remains.
- Focus visibility must not depend on motion.

**Source-drift stop condition**

Stop before editing if:
- `palette` keyframes are no longer represented by the provided arbitrary class,
- `src/styles/motion.css` is not globally loaded for these components,
- `.popover` is used for centered modals and anchored popovers with no way to distinguish them,
- token names or button precedent have changed materially.

---

### Plan B — Repair toast entry to be transform-based and tokenized

**File / current excerpt**

`src/components/toast.css`

```css
@keyframes toast-enter {
  from { top: -24px; opacity: 0; }
  to { top: 0; opacity: 1; }
}

.toast {
  animation: toast-enter 500ms ease-in forwards;
}
```

**Target behavior**

- Toasts appear promptly without layout-property animation.
- Motion communicates arrival but does not feel ceremonial.
- Reduced Motion preserves visibility feedback without vertical travel.

**Project conventions to follow**

- Use existing semantic duration/easing tokens.
- Match the button precedent: explicit animated properties and a Reduced Motion branch.

**Ordered steps**

1. Confirm `.toast` positioning does not rely on animated `top` to establish final layout. If `top` is the only final positioning rule, split static position from animated transform.
2. Replace keyframes with transform + opacity:
   ```css
   @keyframes toast-enter {
     from {
       transform: translateY(-8px);
       opacity: 0;
     }
     to {
       transform: translateY(0);
       opacity: 1;
     }
   }

   .toast {
     animation: toast-enter var(--duration-panel) var(--ease-responsive) forwards;
   }
   ```
3. If toast dismissal exists elsewhere, align exit behavior to the same property set: `opacity` and `transform`, not `top`.
4. Add Reduced Motion:
   ```css
   @media (prefers-reduced-motion: reduce) {
     @keyframes toast-enter {
       from { opacity: 0; }
       to { opacity: 1; }
     }

     .toast {
       animation-duration: 80ms;
     }
   }
   ```

**Hard boundaries**

- Do not change toast queueing, timeout duration, role/live-region behavior, or message content.
- Do not introduce `will-change` unless a trace later shows benefit.
- Do not alter fixed/absolute positioning semantics beyond replacing animated travel.

**Mechanical checks**

```bash
npm run lint
npm run typecheck
```

Add or update any existing component/style snapshot only if the project already snapshots CSS class output.

**Runtime / feel checks required before approval**

- Trigger single and consecutive toasts.
- Verify entry is prompt and does not visually push surrounding layout.
- Verify overlapping or queued toasts keep correct stacking.
- Inspect under normal and Reduced Motion settings.

**Reduced Motion behavior**

- No vertical travel.
- Short opacity fade remains so operators still receive arrival feedback.
- Live-region or focus behavior, if present, remains unchanged.

**Source-drift stop condition**

Stop before editing if:
- `.toast` already has a newer Reduced Motion rule elsewhere,
- toast positioning has moved to another file,
- `top` animation is tied to a deliberate stacking algorithm rather than entry motion,
- token names differ from the supplied `motion.css` excerpt.

---

### Plan C — Harden sortable queue drag and settle behavior

**File / current excerpt**

`src/components/SortableQueue.tsx`

```tsx
function onPointerMove(event: PointerEvent) {
  queueRef.current?.style.setProperty("--drag-y", `${event.clientY}px`);
}

function onPointerUp() {
  setDragging(false);
  animateTo(nearestSlot(currentY), { duration: 400 });
}
```

**Target behavior**

- Dragged item tracks pointer 1:1 in the correct local coordinate space.
- Drag does not jump on pickup because grab offset is preserved.
- Release settle starts from the current on-screen value and can be interrupted.
- Existing `nearestSlot(currentY)` target-selection semantics are preserved unless product authority explicitly approves momentum-based targeting.
- Reduced Motion removes elastic/large travel while preserving clear drop feedback.

**Project conventions to follow**

- Preserve crisp operational throughput.
- Do not add bounce by default in a serious data-dense surface.
- Use transform-driven motion for drag visuals.
- Keep direct manipulation separate from press/focus transforms if both exist.

**Ordered steps**

1. Audit the full component before editing:
   - where `currentY` is set,
   - how `--drag-y` is consumed,
   - whether pointer capture is used,
   - whether there is a grab offset,
   - whether `animateTo` can read current presentation value and accept interruption/velocity.
2. Normalize coordinate space:
   - Convert `event.clientY` to queue-local or item-local coordinates using the container rect.
   - Store `grabOffsetY` on pointer down.
   - Set `--drag-y` to the local dragged position, not raw viewport `clientY`, unless CSS consumption explicitly expects viewport coordinates.
3. Add pointer capture after drag intent is established:
   ```ts
   event.currentTarget.setPointerCapture(event.pointerId)
   ```
   Release capture on pointer up/cancel where supported.
4. Track a short pointer history using monotonic timestamps and CSS pixel positions. Compute release velocity in CSS px/s.
5. Preserve target selection first:
   ```ts
   const target = nearestSlot(currentY)
   ```
   Use measured velocity only for settle handoff if `animateTo` supports it. Do not switch to projected-endpoint slot selection without explicit approval.
6. Replace fixed `duration: 400` with the project’s interruptible animation primitive if available. Desired settle: no bounce, roughly `240–400ms` depending on distance, starting from current presentation value.
7. If `animateTo` is not interruptible or cannot start from current presentation value, stop and create a smaller prerequisite task for the animation primitive instead of patching around it.
8. Add Reduced Motion branch:
   - no elastic overshoot,
   - shorter settle or immediate placement,
   - static selected/drop state feedback remains.

**Hard boundaries**

- Do not change queue ordering rules, slot calculation, persistence, server mutation, keyboard reorder behavior, or accessibility labels.
- Do not add momentum-based target selection unless separately authorized.
- Do not animate layout properties for dragged rows if transform composition is available.
- Do not let drag translation overwrite existing press/focus transform; use wrapper layers or composed transform ownership.

**Mechanical checks**

```bash
npm run lint
npm run typecheck
```

If tests exist for sortable behavior, run the targeted queue test file as well.

**Runtime / feel checks required before approval**

- Pointer down: item should not jump under the pointer.
- Drag: item tracks 1:1 after intent threshold.
- Leave bounds: capture keeps drag alive until release/cancel.
- Interrupt: re-grab during settle starts from visible position without jump.
- Release: nearest-slot behavior remains semantically unchanged.
- Long queue: no obvious broad style recalculation or layout thrash; use a trace if queue size can be large.

**Reduced Motion behavior**

- Drag remains directly attached to the pointer.
- Release uses immediate or very short non-elastic settle.
- Drop confirmation remains visible through static placement, opacity/color, or focus/state styling.

**Source-drift stop condition**

Stop before editing if:
- `--drag-y` is intentionally defined in viewport coordinates,
- `animateTo` API has changed or cannot be inspected,
- `nearestSlot(currentY)` no longer controls target selection,
- the component already has separate pointer-capture/grab-offset logic outside the excerpt,
- keyboard reordering shares the same animation path and would be affected.

## 4. Recommended execution order

1. **Plan A** first: fixes the highest-frequency keyboard surface and global popover convention.
2. **Plan B** second: small, low-risk cleanup with clear token/performance benefits.
3. **Plan C** third: highest interaction complexity; should be implemented only after inspecting the full component and animation primitive.

## Explicitly unverified states

- Actual `palette` keyframes and whether the command palette mounts/unmounts.
- Whether `src/styles/motion.css` is globally loaded for all cited components.
- Actual popover anchoring, placement variables, and whether `.popover` also covers centered overlays.
- Toast positioning, stacking model, dismissal animation, and live-region behavior.
- Sortable queue pointer capture, grab offset, transform ownership, keyboard accessibility, `animateTo` API, and `currentY` source.
- Computed styles, frame pacing, layout shift, smoothness, browser/device feel, accessibility tree, and user impact under real workload.

Method guardrails applied: static-evidence-only review, existing design authority, frontend accessibility discipline, and performance-risk labeling without runtime claims.
