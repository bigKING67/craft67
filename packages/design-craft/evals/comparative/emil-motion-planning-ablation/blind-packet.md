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

# Comparative scorecard

Generated from `scorecard.json`; do not edit by hand.

| Criterion | Weight | Full credit |
|---|---:|---|
| Evidence honesty and recon | 15 | Maps the static motion surface and labels every runtime or feel claim as unverified. |
| Project conventions | 10 | Reuses supplied tokens and the correct local precedent instead of inventing a parallel system. |
| Purpose and frequency | 10 | Prioritizes keyboard and high-frequency restraint plus causal feedback over decoration. |
| Technical accuracy | 15 | Diagnoses property cost, origin, interruption, pointer tracking, and primitive tradeoffs without framework myths. |
| Prioritization | 10 | Vets and ranks a small set by user impact, frequency, confidence, and implementation cost. |
| Plan self-containment | 20 | Plans include exact paths and excerpts, target behavior, steps, boundaries, and drift stop conditions. |
| Verification quality | 10 | Provides targeted mechanical and runtime feel checks without claiming those checks ran. |
| Accessibility and performance | 10 | Defines Reduced Motion behavior and measured performance checks while preserving useful feedback. |
| **Total** | **100** | |


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

- **Stack signals:** React/TSX components plus CSS; motion appears through CSS custom properties, keyframes, arbitrary animation class strings, direct style mutation during drag, and an `animateTo(...)` helper.
- **Where motion lives:**  
  - Global/shared: `src/styles/motion.css`  
  - Component CSS: `src/components/toast.css`, `src/components/Button.css`  
  - Component markup/logic: `src/components/CommandPalette.tsx`, `src/components/SortableQueue.tsx`
- **Existing conventions:** semantic tokens exist for `--duration-fast`, `--duration-panel`, and `--ease-responsive`; `Button.css` is the clearest correct local precedent: transform-only feedback, tokenized timing/easing, and a Reduced Motion override that preserves response.
- **Product personality:** calm, crisp, low-friction desktop operations console. Motion should clarify cause/effect and preserve state continuity, not feel decorative or delay keyboard-heavy work.
- **Frequency map:**  
  - Very high: buttons, command palette, popovers/menus, focus-driven UI.  
  - Medium/high: sortable queue during operational triage.  
  - Medium/episodic: toast notifications, but they are status-critical.  
- **Evidence level:** static excerpts only. No runtime, computed-style, trace, screen recording, accessibility-tree, device, or user validation was performed.

---

## 2. Vetted priority table

| Priority | Finding | Static evidence | Risk | Recommendation |
|---|---|---|---|---|
| P0 | Overlay motion is slow and non-tokenized | `.popover { transition: all 360ms ease-in; }` and command palette `420ms_ease-in` | High-frequency UI may feel delayed; `transition: all` can animate unintended properties | Tokenize overlay motion, restrict to `opacity`/`transform`, use existing responsive easing, add Reduced Motion path |
| P0 | Command palette uses a long one-off animation | `animate-[palette_420ms_ease-in_both]` | Keyboard-heavy workflow can be slowed by entry motion; arbitrary timing diverges from conventions | Replace with named class/state using `--duration-panel` or faster, responsive easing, and explicit open/closed states |
| P1 | Toast animates layout property with long duration | `top: -24px` to `top: 0`, `500ms ease-in` | Layout-affecting animation and long duration are poor fit for calm status feedback | Use transform/opacity, shorten to tokenized duration, preserve immediate status visibility |
| P1 | Drag settle animation is hard-coded and lacks visible Reduced Motion handling | `animateTo(..., { duration: 400 })` | Drag release may feel sluggish; reduced-motion behavior is not shown in excerpt | Use token-aligned settle timing; reduce/snap in Reduced Motion while preserving slot confirmation |
| P2 | Reduced Motion coverage appears inconsistent | Present in `Button.css`; absent from other excerpts | Users requesting reduced motion may still receive full overlay/toast/drag motion | Apply the same local precedent to overlays, toasts, and drag settle |
| P2 | Motion vocabulary is fragmented | `160ms`, `240ms`, `360ms`, `400ms`, `420ms`, `500ms`; mixed easings | Harder to maintain a crisp product feel | Consolidate around existing semantic tokens and only add new tokens if necessary |

---

## 3. Implementation-ready plans

### Plan A — Normalize overlay motion: popover + command palette

**Exact current excerpts**

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

- Popovers and command palette should appear causally connected to the triggering action.
- Motion should be short, crisp, and limited to `opacity` and `transform`.
- Command palette should not feel like a decorative entrance animation; it should feel immediately available for keyboard input.
- Open/closed state should be explicit and inspectable through attributes/classes.
- Focus visibility must remain unaffected.

**Project conventions to follow**

- Use existing tokens: `--duration-fast`, `--duration-panel`, `--ease-responsive`.
- Follow the local Reduced Motion precedent from `Button.css`.
- Prefer transform-based motion over layout-position animation.
- Avoid `transition: all`.
- Avoid hard-coded one-off durations unless there is a documented reason.

**Ordered implementation steps**

1. In `src/styles/motion.css`, replace `.popover` broad transition with explicit properties:
   - `transition-property: opacity, transform;`
   - `transition-duration: var(--duration-fast)` or `var(--duration-panel)` depending on current visual size.
   - `transition-timing-function: var(--ease-responsive);`
2. Keep `transform-origin: center` only if it matches actual anchoring. If popovers are anchored to buttons/menus elsewhere, prefer an origin that reflects the trigger edge; do not guess without inspecting callers.
3. Add stateful selectors for popovers if supported by existing markup, for example `[data-open="true"]` / `[data-open="false"]`, without changing semantics.
4. In `src/components/CommandPalette.tsx`, replace the arbitrary animation class with a stable semantic class, for example:
   - `className="command-palette"`
   - Keep `data-open={open}`.
5. Add command palette motion styles in the existing shared motion location unless a component-local style file already owns it after inspection.
6. Use a panel-scale duration:
   - Entry: `var(--duration-panel)` maximum.
   - Exit: `var(--duration-fast)` if an exit state exists.
7. Use small-distance transform only, for example `translateY(-4px)` or subtle scale, not large travel.
8. Add a Reduced Motion media query:
   - Shorten to about `80ms`.
   - Prefer opacity/state feedback over spatial movement.
   - Preserve visible open/closed feedback.

**Hard boundaries**

- Do not alter command execution, search behavior, result ordering, focus management, or keyboard shortcuts.
- Do not introduce global animation resets.
- Do not remove visible focus indicators.
- Do not add decorative bounce, spring overshoot, blur, or large-scale movement.
- Do not assume unavailable state classes; inspect existing markup before choosing selectors.

**Mechanical checks**

- Search for remaining `transition: all` in overlay-related CSS.
- Search for `ease-in` and hard-coded overlay durations near command palette/popover code.
- Confirm `data-open` remains present and boolean-compatible.
- Run the project’s normal type/build/lint checks if available.
- Confirm no new CSS selector unintentionally targets unrelated components.

**Runtime/feel checks to perform later, not performed here**

- Keyboard-open command palette repeatedly; confirm input feels immediately available.
- Open/close common popovers; confirm cause/effect is clear but not attention-grabbing.
- Check focus ring visibility during and after transition.
- Check long command result lists are not visually delayed by parent animation.

**Reduced Motion behavior**

- Popover/command palette should still appear/disappear with clear opacity or instant state feedback.
- Duration should be materially shorter, around the existing `80ms` local precedent.
- Avoid translate/scale where possible under reduced motion.

**Source-drift stop condition**

Stop and re-audit before implementing if:
- `src/styles/motion.css` no longer owns shared motion tokens.
- `CommandPalette` no longer renders the shown wrapper or `data-open`.
- Existing styles already define `palette` keyframes with important state behavior.
- A newer design authority changes token names, durations, or Reduced Motion requirements.

---

### Plan B — Rework toast entrance to status-first, transform-based motion

**Exact current excerpt**

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

- Toasts should communicate status promptly without pulling attention for half a second.
- Entrance should preserve causality while avoiding layout-affecting animation.
- Toast should be readable quickly and should not compete with operational tasks.

**Project conventions to follow**

- Use existing motion tokens from `src/styles/motion.css`.
- Prefer `transform` and `opacity`.
- Use `--ease-responsive`.
- Add Reduced Motion behavior consistent with `Button.css`.

**Ordered implementation steps**

1. Replace keyframe movement from `top` to `transform`.
2. Keep the visual offset equivalent, but express it as:
   - `transform: translateY(-8px)` or similar short distance, not `top: -24px`.
3. Replace `500ms ease-in` with a tokenized duration:
   - Prefer `var(--duration-panel)` for a full toast entrance.
   - Use `var(--duration-fast)` if the toast is small and non-blocking.
4. Replace `ease-in` with `var(--ease-responsive)`.
5. Ensure the final keyframe leaves the toast at:
   - `transform: translateY(0);`
   - `opacity: 1;`
6. Add `@media (prefers-reduced-motion: reduce)`:
   - Shorten animation duration to around `80ms`.
   - Consider opacity-only entrance.
7. Confirm no positioning logic depends on the animated `top` value. If it does, separate layout position from animation transform.

**Hard boundaries**

- Do not change toast content, severity, timeout, stacking order, or dismissal behavior.
- Do not make status feedback slower.
- Do not remove animation entirely for all users unless design authority changes.
- Do not animate dimensions, margins, `top`, `left`, or other layout properties.

**Mechanical checks**

- Search for `toast-enter` references to avoid orphaned or duplicated keyframes.
- Search toast CSS for `top` animation or hard-coded `500ms`.
- Confirm the toast base position still comes from static layout/positioning, not from animation.
- Run CSS lint/build checks if available.

**Runtime/feel checks to perform later, not performed here**

- Trigger success, warning, and error toasts.
- Confirm the toast is readable immediately.
- Confirm stacked toasts do not jump or reflow during entrance.
- Confirm dismissal timing still feels independent from entrance timing.

**Reduced Motion behavior**

- Toast should still appear with clear status feedback.
- Use very short opacity transition or instant placement with opacity confirmation.
- Avoid vertical travel under reduced motion.

**Source-drift stop condition**

Stop and re-audit before implementing if:
- Toasts are now managed by a different component or animation system.
- The `top` keyframes are used to coordinate stack layout.
- New severity-specific toast motion exists.
- A newer authority defines different notification motion requirements.

---

### Plan C — Make sortable queue drag settle faster, tokenized, and reduced-motion aware

**Exact current excerpt**

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

- Drag should feel directly manipulated while pointer is down.
- Release should resolve quickly to the nearest slot without a sluggish settle.
- State continuity should remain clear: users should understand where the item moved.
- Reduced Motion should preserve placement feedback without long travel.

**Project conventions to follow**

- Prefer tokenized durations over hard-coded `400`.
- Use the existing responsive easing if `animateTo` accepts easing.
- Use direct manipulation during drag; do not add decorative easing while pointer is down.
- Align with the local Reduced Motion precedent: shorter motion, feedback preserved.

**Ordered implementation steps**

1. Inspect the implementation of `animateTo` before changing call shape.
2. If `animateTo` accepts CSS-like timing:
   - Use a duration equivalent to `--duration-panel` at maximum.
   - Prefer `--duration-fast` for short slot-to-slot corrections.
   - Use the responsive easing if supported.
3. If `animateTo` only accepts numbers:
   - Replace `400` with a named constant near the component, such as `QUEUE_SETTLE_DURATION_MS = 240`.
   - Add a reduced-motion constant, such as `80` or `0–80` depending on feedback needs.
4. Add a Reduced Motion detection path:
   - CSS media query if animation is CSS-driven.
   - `matchMedia("(prefers-reduced-motion: reduce)")` or existing app preference helper if JS-driven.
5. Keep pointer-move updates direct. Do not animate every pointer move.
6. Confirm `--drag-y` is consumed by transform-based styles. If it drives layout properties, plan a separate transform-only correction.
7. On pointer up, ensure the item reaches the nearest slot with a clear final state marker, such as selected/placed styling if already present.

**Hard boundaries**

- Do not change queue ordering rules.
- Do not change `nearestSlot(currentY)` logic unless a separate bug is found.
- Do not introduce inertial physics, bounce, or overshoot.
- Do not throttle pointer movement in a way that makes direct manipulation lag unless profiling proves it is needed.
- Do not assume `animateTo` supports easing or cancellation without inspecting it.

**Mechanical checks**

- Locate `animateTo` definition and all call sites before altering its API.
- Search for `--drag-y` usage and verify it maps to transform-style movement.
- Search for hard-coded drag durations.
- Confirm pointer-up still calls `setDragging(false)` at the correct time for existing styles.
- Run type checks after any signature or constant changes.

**Runtime/feel checks to perform later, not performed here**

- Drag one item a short distance and release; confirm settle is quick and understandable.
- Drag across multiple slots; confirm destination continuity.
- Cancel or release near boundaries; confirm no visual snap to an unexpected slot.
- Test repeated rapid drags for stale animation or delayed state.
- Test keyboard alternatives if the sortable queue supports them.

**Reduced Motion behavior**

- While dragging, direct pointer-following can remain because it is user-controlled.
- On release, use a very short settle or immediate placement.
- Preserve final-slot confirmation through position, focus/selection, or another non-motion cue.

**Source-drift stop condition**

Stop and re-audit before implementing if:
- `animateTo` has already been replaced or centralized.
- `--drag-y` no longer controls the dragged visual position.
- Queue sorting now has keyboard-first behavior that shares the same animation path.
- Reduced Motion is already handled by a global motion provider not shown in the excerpt.

---

## 4. Recommended execution order

1. **Plan A first:** highest frequency and most visible to keyboard-heavy operators; also establishes the shared overlay convention.
2. **Plan B second:** small, isolated, high-confidence improvement from layout animation to transform/opacity.
3. **Plan C third:** important for throughput, but requires inspecting `animateTo`, `--drag-y` consumption, and queue behavior before changing timing.

## Explicitly unverified states

- Actual computed durations, easings, transforms, and cascade order.
- Whether `palette` keyframes exist elsewhere.
- Whether `.popover` has open/closed state selectors elsewhere.
- Whether `animateTo` supports easing, cancellation, promises, or reduced-motion hooks.
- Whether `--drag-y` is consumed by transform, layout, or both.
- Actual focus behavior, keyboard flow, screen reader behavior, and accessibility tree.
- Runtime performance, paint/layout cost, device behavior, and user-perceived feel.


## Output B

## 1. Recon summary

Reading this as: a calm desktop operations console for keyboard-heavy operators, optimized for throughput, continuity, and low-friction state feedback.

- **Stack signals:** React/TSX components, CSS modules/global CSS, CSS custom properties, Tailwind-style arbitrary animation class, imperative pointer handling, and an `animateTo(...)` helper.
- **Where motion lives:** shared motion tokens in `src/styles/motion.css`; component-local CSS in `toast.css` and `Button.css`; inline utility animation in `CommandPalette.tsx`; imperative drag/settle logic in `SortableQueue.tsx`.
- **Existing conventions:** semantic duration/easing tokens exist; `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)` is a strong responsive ease-out-like curve; `Button.css` is the best local precedent: transform-only, tokenized duration/easing, subtle scale, and a Reduced Motion branch that preserves feedback.
- **Product personality:** crisp, quiet, utilitarian, non-cinematic. Motion should explain causality, not decorate.
- **Frequency map:**
  - Very high: command palette, buttons, keyboard-triggered overlays.
  - High / direct manipulation: sortable queue drag and settle.
  - Medium: popovers.
  - Occasional but visible: toasts.
- **Evidence level:** static snippets only. No runtime feel, computed style, browser performance, accessibility tree, keyboard flow, screen recording, device, or user testing was performed.

## 2. Vetted priority table

| ID | Priority | Evidence | Finding | Smallest safe correction |
|---|---:|---|---|---|
| F1 | P1 | `CommandPalette.tsx`: `animate-[palette_420ms_ease-in_both]` | High-frequency keyboard surface uses a long arbitrary animation and `ease-in`, which delays the start of visible response by design. No Reduced Motion branch is shown. | Replace with tokenized open/closed state styles using opacity/very small transform, about `120–180ms`, responsive easing, and a reduced-motion path with no travel. |
| F2 | P1 | `motion.css`: `.popover { transform-origin: center; transition: all 360ms ease-in; }` | Popover motion has broad property ownership, slow timing, `ease-in`, center origin, and no shown Reduced Motion branch. For trigger-anchored overlays this weakens causality. | Limit to `opacity, transform`; use trigger/placement origin when available; use existing responsive token; add reduced-motion no-travel feedback. |
| F3 | P1 | `toast.css`: keyframes animate `top` from `-24px` to `0`, `500ms ease-in` | Toast entrance animates a layout property and is long/late-starting. Keyframes may restart from the declared start on repeated transient state changes. No Reduced Motion path is shown. | Move to `transform: translateY(...)` + opacity, shorten to tokenized timing, use ease-out-like response, and remove travel under Reduced Motion. |
| F4 | P1/P2 | `SortableQueue.tsx`: pointer move sets `--drag-y` on `queueRef`; release uses `animateTo(nearestSlot(currentY), { duration: 400 })` | Direct manipulation path has static risks: parent-level CSS variable updates may affect a broad subtree; release settle is fixed-duration and does not show presentation-value interruption, measured velocity, pointer capture, or grab-offset handling. Static evidence cannot prove gesture feel. | Keep current target semantics unless explicitly changed; move hot-path writes to the dragged item or a narrow owner; coalesce frame writes; settle from current presentation value with measured velocity if supported. |
| F5 | P2 | Tokens exist, but components use `360ms`, `420ms`, `500ms`, `ease-in`, and arbitrary animation strings | Motion vocabulary is fragmented despite existing semantic tokens and a correct button precedent. | Centralize overlay/transient/direct-manipulation timing guidance around existing tokens before adding new values. |

## 3. Implementation-ready plans

### Plan A — Retune high-frequency overlays: command palette + popover

**Current excerpts**

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
<div
  data-open={open}
  className="animate-[palette_420ms_ease-in_both]"
>
  <SearchResults />
</div>
```

**Target behavior**

- Command palette opens with immediate causal feedback suitable for keyboard use.
- Popovers preserve trigger relationship where the positioning primitive exposes an origin.
- No broad `transition: all`.
- No `ease-in` for interactive entrance.
- Reduced Motion preserves state feedback without spatial travel.

**Project conventions**

- Use `--duration-fast`, `--duration-panel`, and `--ease-responsive`.
- Follow the local button precedent: transform-only where motion is needed, short timing, Reduced Motion branch.
- Keep visible focus unaffected.

**Ordered steps**

1. In `src/styles/motion.css`, add or reuse semantic overlay styles rather than arbitrary animation strings.
2. Replace `.popover` with explicit properties, for example:
   - `transition: opacity var(--duration-fast) var(--ease-responsive), transform var(--duration-fast) var(--ease-responsive);`
   - `transform-origin: var(--popover-transform-origin, center);`
3. If the actual popover primitive exposes a placement-origin variable, map it into `--popover-transform-origin`; otherwise keep the fallback and document that origin is unresolved.
4. Replace `CommandPalette.tsx` arbitrary animation with stable state styling keyed by `data-open`.
5. Use a minimal open transform only if needed, e.g. opacity plus `translateY(-2px)` or `scale(0.98–0.99)`, not large travel.
6. Add `@media (prefers-reduced-motion: reduce)` so command palette/popover either use opacity-only `80ms` feedback or immediate state change with focus still visible.

**Hard boundaries**

- Do not change command search behavior, result ordering, focus trapping, keyboard shortcuts, or dismissal semantics.
- Do not introduce a new animation library.
- Do not add decorative bounce, stagger, blur, or long panel motion.
- Do not remove focus-visible styling.

**Mechanical checks**

- Run the project’s existing type-check for `CommandPalette.tsx`.
- Run the existing lint/style check for TSX/CSS if present.
- Run the smallest existing build or component test gate that covers shared styles.

**Runtime / feel checks to perform later**

- Toggle command palette rapidly by keyboard and ensure no delayed response or visual restart feels blocking.
- Open/close popovers from multiple placements if placement collision is supported.
- Confirm focus remains visible during and after open/close.
- Check normal and Reduced Motion modes.

**Reduced Motion behavior**

- Remove transform travel.
- Preserve feedback via instant visibility or short opacity/color transition.
- Do not hide content until a long animation completes.

**Source-drift stop condition**

- Stop before editing if `CommandPalette.tsx` no longer uses `data-open` or the cited arbitrary animation.
- Stop if `.popover` has been replaced by a component-scoped primitive with a different state/origin contract.
- Stop if the motion tokens in `src/styles/motion.css` were renamed or superseded by a newer authority.

---

### Plan B — Repair toast entrance as transient, non-layout motion

**Current excerpt**

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

**Target behavior**

- Toast appears promptly without animating `top`.
- Motion is short, readable, and calm.
- Repeated toast creation does not depend on a long keyframe restart for basic feedback.
- Reduced Motion removes vertical travel while preserving noticeability.

**Project conventions**

- Prefer transform and opacity.
- Prefer existing timing/easing tokens.
- Keep transient UI functional: dismissal, pause/resume timers, Escape behavior, and announcements must not regress if they exist.

**Ordered steps**

1. Replace `top` keyframe movement with `transform: translateY(...)` and opacity.
2. Prefer state-based transition if the toast system has open/closed state attributes; otherwise use a shorter keyframe only for mount entrance.
3. Initial target:
   - duration: `var(--duration-fast)` or a nearby tokenized `160–200ms`;
   - easing: `var(--ease-responsive)`;
   - travel: small, e.g. `translateY(-25%)` or `translateY(-8px)`, depending on actual layout.
4. Add a Reduced Motion branch:
   - `transform: none`;
   - short opacity transition or immediate visible state.
5. If exit animation exists elsewhere, align enter/exit vocabulary so enter does not use layout while exit uses transform, or vice versa.
6. If toast timers exist, verify they are not coupled to the old `500ms` animation duration.

**Hard boundaries**

- Do not change toast copy, severity styling, stacking rules, timer duration, or announcement semantics unless the current code explicitly couples them to animation.
- Do not animate `top`, `left`, margin, padding, width, or height for the entrance.
- Do not introduce swipe dismissal unless already present.

**Mechanical checks**

- Run existing CSS lint/style check if present.
- Run existing component/unit tests for toast lifecycle if present.
- Run the smallest existing build gate because this touches component styling.

**Runtime / feel checks to perform later**

- Trigger one toast, several stacked toasts, and rapid repeated toasts.
- Confirm no visual gap breaks pointer access to dismiss controls.
- Hide and restore the document if toast timers exist.
- Verify normal and Reduced Motion modes.

**Reduced Motion behavior**

- No vertical travel.
- Opacity or static state change remains so the user receives feedback.
- Focus/announcement behavior, if present, must remain independent of animation.

**Source-drift stop condition**

- Stop if `toast.css` no longer contains `toast-enter` or `.toast` no longer owns entrance motion.
- Stop if a toast library now owns lifecycle state and exposes official animation hooks.
- Stop if timer or announcement code is found to depend on the old `500ms` duration.

---

### Plan C — Make sortable queue drag settle interruptible and narrowly owned

**Current excerpt**

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

**Target behavior**

- Drag tracking remains attached to the pointer after intent is clear.
- Hot-path style writes are scoped to the dragged item or a narrow transform owner, not the entire queue unless proven safe.
- Release settles from the current on-screen position.
- Existing target-selection semantics, `nearestSlot(currentY)`, are preserved unless product owners explicitly authorize momentum-based slot selection.
- Reduced Motion removes large elastic travel but keeps clear reorder feedback.

**Project conventions**

- Keep calm, non-bouncy motion for operations work.
- Use transform ownership rather than layout movement where possible.
- Preserve throughput: drag should not lock input until animation completes.

**Ordered steps**

1. Inspect the full `SortableQueue.tsx` drag model before editing:
   - pointer down ownership;
   - grab offset;
   - pointer capture;
   - current coordinate space;
   - how `currentY` is updated;
   - what `animateTo` can read: current presentation value, cancel, velocity, spring, duration.
2. Move per-frame writes from `queueRef` to the dragged row or a dedicated transform layer if the CSS variable currently affects descendants broadly.
3. Coalesce pointer updates through the display frame if the current code writes synchronously on every pointer event.
4. Preserve `nearestSlot(currentY)` as the target rule for the first implementation.
5. Track recent pointer samples with monotonic timestamps and compute release velocity in CSS px/s.
6. If `animateTo` supports velocity/spring:
   - start from current presentation value;
   - pass bounded release velocity;
   - use critically damped or near-critically damped settle, no decorative bounce.
7. If `animateTo` only supports duration:
   - shorten only after runtime check;
   - ensure interruption cancels/restarts from current rendered position rather than logical origin.
8. Add or preserve Reduced Motion behavior:
   - no elastic overshoot;
   - short snap or immediate settle;
   - static slot/placeholder feedback remains.

**Hard boundaries**

- Do not change reorder semantics, slot calculation, data mutation timing, keyboard reordering, or persistence behavior.
- Do not switch from nearest-slot targeting to projected momentum targeting without explicit approval.
- Do not add a new gesture/physics dependency unless existing primitives cannot support interruption and velocity.
- Do not let press scale and drag translation compete for the same `transform` owner.

**Mechanical checks**

- Run existing type-check for `SortableQueue.tsx`.
- Run existing tests for reorder behavior if present.
- Add or update unit coverage for target selection only if the project already tests this interaction layer.
- Run the smallest existing build gate.

**Runtime / feel checks to perform later**

- Drag slowly, drag quickly, reverse direction mid-drag, release near slot boundaries.
- Start a second drag while a settle animation is in progress.
- Confirm pointer capture by moving outside the row bounds during drag.
- Verify keyboard reorder behavior still works if supported.
- Check normal and Reduced Motion modes.
- Performance claims require a browser trace or equivalent runtime evidence; none exists yet.

**Reduced Motion behavior**

- Keep direct manipulation during the drag.
- Remove bounce/elasticity and minimize settle travel after release.
- Preserve a clear final slot/placeholder state.

**Source-drift stop condition**

- Stop if `onPointerMove`, `onPointerUp`, `queueRef`, `--drag-y`, `nearestSlot`, or `animateTo` signatures have materially changed.
- Stop if `animateTo` is owned by a shared animation utility with constraints not visible in the snippet.
- Stop if current source already includes pointer capture, velocity handoff, or Reduced Motion handling outside the excerpt.

## 4. Recommended execution order

1. **Plan A first:** highest frequency and easiest to align with existing tokens.
2. **Plan B second:** removes layout-property transient motion and normalizes timing.
3. **Plan C third:** highest interaction complexity; should wait until full source inspection and runtime checks are available.

## Explicitly unverified states

- Actual rendered timing, smoothness, frame pacing, and compositing.
- Computed `transform-origin` for popovers.
- Whether the command palette currently blocks focus or input during animation.
- Toast stacking, timers, announcements, exit animation, and interruption behavior.
- Sortable queue pointer capture, grab offset, keyboard reordering, current-value interruption, velocity support, and large-list performance.
- Reduced Motion behavior beyond the shown button precedent.
- Browser, device, accessibility-tree, screen-reader, and user-test outcomes.


## Output C

## 1. Recon summary

- **Stack signals**: React/TSX components, plain CSS, CSS custom properties, CSS keyframes, an arbitrary utility animation class, and imperative pointer/animation logic. No specific animation library is confirmed from the snippets.
- **Where motion lives**:
  - Global motion tokens: `src/styles/motion.css`
  - Component CSS: `src/components/toast.css`, `src/components/Button.css`
  - Component class animation: `src/components/CommandPalette.tsx`
  - Gesture logic: `src/components/SortableQueue.tsx`
- **Existing conventions**:
  - Tokens already exist: `--duration-fast: 160ms`, `--duration-panel: 240ms`, `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)`.
  - Correct local precedent exists in `Button.css`: transform-only feedback, tokenized timing/easing, and a reduced-motion branch that preserves feedback.
- **Product personality**: calm, crisp desktop operations console. Motion should clarify state and causality, not add delay or decorative softness.
- **Frequency map**:
  - Very high frequency: command palette, keyboard-driven interactions, queue sorting.
  - Medium/high frequency: popovers.
  - Occasional: toasts.
  - Existing button press feedback appears aligned with the product.
- **Evidence level**: static code excerpts only. No runtime, computed style, trace, screen recording, accessibility tree, device, or user validation was performed.

---

## 2. Priority table

| # | Severity | Category | Location | Finding | Fix summary |
|---|---|---:|---|---|---|
| 1 | HIGH | Purpose / throughput | `src/components/CommandPalette.tsx` | Command palette uses `animate-[palette_420ms_ease-in_both]`. For keyboard-heavy operators, a 420ms ease-in entrance risks delaying a primary command surface. | Remove the entrance animation from the command palette; preserve focus and state feedback without temporal delay. |
| 2 | HIGH | Gesture / performance | `src/components/SortableQueue.tsx` | Pointer move writes `--drag-y` to `queueRef`, and release uses fixed `duration: 400`. This suggests parent-level style invalidation and a non-velocity-aware snap. | Move drag updates to the active item’s `transform`; snap with an interruptible spring/velocity path, with reduced-motion shortening and removing bounce. |
| 3 | MEDIUM | Easing / performance / cohesion | `src/styles/motion.css` | `.popover` uses `transition: all 360ms ease-in` and `transform-origin: center`. `all` can animate unintended properties; `ease-in` delays response; centered origin may be wrong for trigger-anchored popovers. | Restrict transition to `transform, opacity`, use existing responsive token, shorten to tokenized duration, and use trigger-origin variables with safe fallback. |
| 4 | MEDIUM | Performance / accessibility | `src/components/toast.css` | Toast animates `top` from `-24px` to `0` over `500ms ease-in`, with no reduced-motion branch shown. | Animate `transform` and `opacity` instead of `top`; reduce duration; add reduced-motion opacity-only feedback. |
| 5 | MEDIUM | Cohesion / reduced motion | Multiple snippets | Existing correct button precedent uses tokens and reduced motion, but palette, popover, and toast use hand-authored long/ease-in motion. | Consolidate these surfaces around existing tokens and the reduced-motion pattern already present locally. |

---

## 3. Implementation plans

### Plan 1 — Remove command-palette entrance delay

**Current excerpt**

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

- Opening the command palette should be effectively immediate.
- No 420ms entrance, no `ease-in`, no delayed keyboard surface.
- Focus visibility and command result continuity must remain intact.
- Reduced Motion behavior should be identical to default: no entrance movement.

**Project conventions**

- Follow the local precedent from `src/components/Button.css`: motion must be purposeful, tokenized when present, and have a reduced-motion path.
- For this component, the correct motion budget is zero entrance animation because it is a high-frequency keyboard surface.

**Ordered steps**

1. In `src/components/CommandPalette.tsx`, remove only the arbitrary animation class:
   ```tsx
   export function CommandPalette({ open }: { open: boolean }) {
     return (
       <div data-open={open}>
         <SearchResults />
       </div>
     );
   }
   ```
2. If the real file has additional non-motion classes, preserve them and remove only:
   ```tsx
   animate-[palette_420ms_ease-in_both]
   ```
3. Search for a `palette` keyframe or animation definition.
   - If it becomes unused after this removal, delete that unused animation definition.
   - If it is used elsewhere, leave it untouched and report the remaining usage.

**Hard boundaries**

- Do not change `SearchResults`.
- Do not change focus management, keyboard bindings, result filtering, or open-state logic.
- Do not replace this with a shorter fade unless a product owner explicitly requests motion here.
- Do not add a dependency.

**Mechanical checks**

- Search result check: no remaining `animate-[palette_420ms_ease-in_both]`.
- Search result check: any remaining `palette` animation usage is intentional and reported.
- Run the project’s existing lint/typecheck/build commands if available; no new scripts should be added.

**Runtime / feel checks for executor**

_Not performed in this audit._

- Open the command palette by keyboard shortcut.
- Confirm the surface appears without a visible entrance delay.
- Confirm focus remains visible immediately.
- Rapidly open/close several times; confirm there is no queued or restarting animation.
- Enable Reduced Motion; behavior should remain immediate and feedback should not disappear.

**Source-drift stop condition**

- If `src/components/CommandPalette.tsx` no longer contains the exact animation class, stop and report the current implementation instead of guessing.

---

### Plan 2 — Normalize popover and toast motion around transform/opacity tokens

**Current excerpts**

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

- Popovers: crisp, tokenized transform/opacity transition; no `transition: all`; no `ease-in`; origin can follow trigger-provided variables where available.
- Toasts: enter using `transform` and `opacity`, not `top`; shorter and responsive; reduced motion keeps opacity feedback and removes movement.

**Project conventions**

- Reuse existing tokens:
  ```css
  --duration-fast: 160ms;
  --duration-panel: 240ms;
  --ease-responsive: cubic-bezier(0.23, 1, 0.32, 1);
  ```
- Match the reduced-motion precedent:
  ```css
  @media (prefers-reduced-motion: reduce) {
    .button { transition-duration: 80ms; }
  }
  ```

**Ordered steps**

1. In `src/styles/motion.css`, replace the `.popover` rule with:
   ```css
   .popover {
     transform-origin: var(
       --radix-popover-content-transform-origin,
       var(--transform-origin, center)
     );
     transition:
       transform var(--duration-panel) var(--ease-responsive),
       opacity var(--duration-panel) var(--ease-responsive);
   }

   @media (prefers-reduced-motion: reduce) {
     .popover {
       transition:
         opacity 80ms var(--ease-responsive);
     }
   }
   ```
2. In `src/components/toast.css`, replace the toast keyframes with transform/opacity:
   ```css
   @keyframes toast-enter {
     from {
       transform: translate3d(0, -8px, 0);
       opacity: 0;
     }
     to {
       transform: translate3d(0, 0, 0);
       opacity: 1;
     }
   }

   @keyframes toast-enter-reduced {
     from { opacity: 0; }
     to { opacity: 1; }
   }

   .toast {
     animation: toast-enter var(--duration-panel) var(--ease-responsive) forwards;
   }

   @media (prefers-reduced-motion: reduce) {
     .toast {
       animation: toast-enter-reduced 120ms var(--ease-responsive) forwards;
     }
   }
   ```
3. Search for any other `.toast` rules that set `top` during entry.
   - If another rule depends on animated `top`, stop and report the conflict.
   - If `top` is only used for static placement, leave static positioning intact.

**Hard boundaries**

- Do not change toast layout, stacking, placement, content, dismiss behavior, or timers.
- Do not change popover markup or open/close state logic.
- Do not introduce `transition: all`.
- Do not invent new motion tokens unless the existing tokens are absent in the real file.
- If `.popover` is used for centered modal content rather than trigger-anchored content, stop and report before applying the transform-origin change.

**Mechanical checks**

- Search result check: no `.popover { transition: all ... }`.
- Search result check: no `toast-enter` animation of `top`.
- Search result check: no `500ms ease-in` remaining for `.toast`.
- Run existing lint/typecheck/build commands if available.

**Runtime / feel checks for executor**

_Not performed in this audit._

- Open a popover and inspect slow playback: opacity/scale or transform should respond immediately, not ease in slowly.
- Confirm the popover origin appears connected to its trigger where the component system provides an origin variable.
- Trigger a toast: it should slide a short distance from above and settle quickly.
- Enable Reduced Motion: toast should fade without vertical movement; popover should preserve opacity feedback with no movement transition.

**Source-drift stop condition**

- If either current excerpt is no longer present, stop and report the new implementation.
- If existing state selectors require a different open/closed selector structure, stop and ask for the surrounding CSS before adapting.

---

### Plan 3 — Make sortable queue drag motion direct and interruptible

**Current excerpt**

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

- During drag, only the active dragged item updates its `transform`.
- Do not drive child movement by writing a parent-level CSS variable on every pointer move.
- Release motion should account for interruption and velocity rather than always tweening for `400ms`.
- Reduced Motion should keep snap feedback but shorten it and remove bounce.

**Project conventions**

- Prefer transform-only motion, matching the existing button precedent.
- Use existing semantic durations where applicable:
  - direct press/feedback: `--duration-fast`
  - panel/settling motion: around `240ms`
- For gesture settling, use an interruptible spring only if the existing `animateTo` helper supports spring-like options.

**Ordered steps**

1. Inspect the real `SortableQueue.tsx` for the active row/item element.
   - If there is already a ref for the dragged item, use it.
   - If only `queueRef` exists and there is no single active item target, stop and report; do not rewrite the queue architecture.
2. Replace parent CSS variable movement:
   ```tsx
   queueRef.current?.style.setProperty("--drag-y", `${event.clientY}px`);
   ```
   with direct active-item transform movement, using the project’s actual dragged-item ref name:
   ```tsx
   draggedItemRef.current?.style.setProperty(
     "transform",
     `translate3d(0, ${event.clientY}px, 0)`
   );
   ```
   If the real code tracks a delta rather than absolute `clientY`, use the existing delta variable instead of introducing absolute positioning behavior.
3. Track pointer velocity using existing pointer events:
   ```tsx
   const elapsedMs = Math.max(event.timeStamp - lastPointerTimeRef.current, 1);
   const velocityY = (event.clientY - lastPointerYRef.current) / elapsedMs;

   lastPointerYRef.current = event.clientY;
   lastPointerTimeRef.current = event.timeStamp;
   ```
4. Change `onPointerUp` to accept the pointer event if the surrounding event wiring supports it:
   ```tsx
   function onPointerUp(event: PointerEvent) {
     setDragging(false);

     const prefersReducedMotion =
       window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;

     animateTo(
       nearestSlot(currentY),
       prefersReducedMotion
         ? { duration: 80, bounce: 0 }
         : { type: "spring", duration: 0.5, bounce: 0.2, velocity: velocityY }
     );
   }
   ```
5. If `animateTo` does not support `type`, `bounce`, or `velocity`, do not invent a physics engine. Use the closest existing interruptible/spring API if present; otherwise stop and report the helper limitation.

**Hard boundaries**

- Do not change queue ordering rules, hit testing, slot calculation, persistence, or item data shape.
- Do not add a new animation dependency.
- Do not animate `top`, `left`, margins, padding, width, or height for dragging.
- Do not apply transforms to the entire queue container.
- Do not continue if the active dragged element cannot be targeted directly.

**Mechanical checks**

- Search result check: no pointer-move path writes `--drag-y` to `queueRef`.
- Search result check: release path no longer uses only `{ duration: 400 }`.
- Typecheck should pass after changing `onPointerUp` signature and velocity refs.
- Existing drag/reorder tests, if any, should continue to pass.

**Runtime / feel checks for executor**

_Not performed in this audit._

- Drag a queue item slowly: it should track the pointer without moving unrelated rows through a parent variable.
- Release near a slot: it should settle into place without a fixed-duration mechanical glide.
- Re-grab during settle: motion should retarget rather than restart from zero.
- Enable Reduced Motion: drag tracking remains direct; release snap is short and non-bouncy.

**Source-drift stop condition**

- If the current excerpt is not present, or if `animateTo` is not local/inspectable enough to confirm supported options, stop and report the current implementation before editing.

---

## 4. Recommended execution order

1. **Plan 1 — Command palette**: highest throughput impact, smallest scope.
2. **Plan 2 — Popover/toast normalization**: fixes repeated CSS anti-patterns and aligns with existing tokens.
3. **Plan 3 — Sortable queue**: highest interaction complexity; execute after simpler motion conventions are clean.

## Explicitly unverified states

- Actual computed styles and whether any other CSS overrides these snippets.
- Whether `.popover` is always trigger-anchored or sometimes used for centered modal-like content.
- Exact `palette` keyframe definition and whether it is reused elsewhere.
- Toast stacking behavior, dismissal timing, and whether JS controls mount/unmount.
- `animateTo` API capabilities and whether it supports spring, velocity, or interruption.
- Accessibility tree, focus order, keyboard behavior, frame timing, and Reduced Motion behavior in a real browser/device.
