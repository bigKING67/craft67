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

- **Stack signals:** TSX components, React-style state/ref usage, CSS custom properties and keyframes, and a utility-style arbitrary animation class. The utility compiler and drag animation library are not established.
- **Motion locations:** shared definitions in `src/styles/motion.css`; component CSS for toast/button; inline animation configuration in the command palette; imperative pointer handling and release animation in the sortable queue.
- **Existing conventions:** `--duration-fast: 160ms`, `--duration-panel: 240ms`, and `--ease-responsive`. The button demonstrates property-scoped transitions, token reuse, and an `80ms` Reduced Motion override. Preserve visible focus and feedback.
- **Personality:** calm, crisp, utilitarian. Motion should explain state changes, not demand attention or delay the next command.
- **Frequency map — expected, not measured:** palette and button interactions are likely frequent; popovers recur during inspection; toast frequency depends on events; dragging generates continuous input while active, with one settle per release.
- **Evidence level:** static excerpts only. Declared timings and properties are observable; actual visibility, frame cost, interruption behavior, keyboard access, and perceived responsiveness are not.

## 2. Vetted priorities

| Priority | Finding supported by excerpts | Impact hypothesis and disposition |
|---|---|---|
| P1 | Popover uses `transition: all 360ms ease-in` and a centered origin. | Broad property coverage and delayed acceleration conflict with crisp state changes. Scope properties and use tokens; choose origin only after identifying its anchor. |
| P1 | Palette declares `420ms ease-in`; `open` is passed to `data-open`, but no state selector or keyframes are supplied. | Timing is out of convention; open/close binding cannot be established. Resolve state wiring before replacing the animation. |
| P1 | Toast animates `top` and opacity for `500ms ease-in`. | `top` is layout-affecting when positioning makes it operative; actual rendering cost is unknown. Replace positional animation with a small transform and shorten entry. |
| P1 | Queue release uses a literal `400` duration; the move handler writes `clientY` to a custom property. | Release timing is out of convention. Coordinate mapping, latest-position handling, and interruption need inspection—not a presumption that dragging is broken. |
| P1, cross-cutting | A Reduced Motion override is shown only for the button. | Coverage elsewhere is unverified. Each change must include an explicit reduced path preserving state feedback and focus. |

The button is a local convention to preserve, not an additional remediation target.

## 3. Implementation plans

### Plan A — Shared overlay motion and command palette

**Exact paths/current excerpts**

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

**Target behavior and conventions**
- Use explicit opacity/transform properties with `--duration-fast` and `--ease-responsive`; leave global token values unchanged.
- Palette entry: opacity `0 → 1`, at most `4px → 0` vertical travel. No input, focus, or result-rendering delay.
- Popover: similarly restrained motion; use an anchor-facing origin only where an existing scale effect makes origin relevant. Do not add scale merely to justify changing origin.
- Start with `160ms` for these frequent interactions; retain `--duration-panel` for existing panel-level usage.

**Ordered steps**
1. Locate `.popover` consumers, state selectors, transform owners, palette keyframes, stylesheet loading, and mount/unmount behavior.
2. Replace `transition: all` with only properties actually changed by the popover state rules.
3. Replace the palette’s literal animation class with a narrowly scoped rule in the existing loaded motion stylesheet, using the shared tokens.
4. Bind entry to the real open lifecycle. `data-open` alone must not be assumed to hide or deactivate content.
5. Preserve existing close/focus restoration semantics; use immediate close rather than inventing delayed unmount infrastructure.
6. Add a reduced override: opacity-only feedback of at most `80ms`, no travel/scale, no delayed interaction.

**Hard boundaries**
- Do not change search behavior, selection, focus ownership, dialog semantics, or global token values.
- Do not animate size, position offsets, or unrelated properties. Do not overwrite transforms owned by positioning code.
- Hidden palette content must not become focusable merely to support animation.

**Mechanical checks**
- Confirm old `360ms`/`420ms` declarations are removed from these paths; verify generated CSS and token resolution through the project’s build.
- Check selectors against actual open/closed markup; test rapid state toggles and any existing focus-return assertions.
- Verify reduced rules win the cascade without changing the final visible state.

**Runtime/feel checks — to perform**
- Keyboard-open, type immediately, select, escape, and reopen rapidly; confirm no blocked input, stale animation, or focus-ring clipping.
- Check popovers at different anchor edges and after repositioning; movement should explain opening without appearing to drift.

**Source-drift stop condition**
- Stop and revise the patch if these excerpts differ, the palette has a separate presence controller, or positioning owns the same transform. Do not stack competing motion systems.

### Plan B — Toast entry without positional layout animation

**Exact path/current excerpt**

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

**Target behavior and conventions**
- Entry uses opacity plus `translateY(-4px) → translateY(0)`, over `--duration-fast` with `--ease-responsive`.
- Preserve final placement, toast lifetime, announcement timing, and immediate availability of toast actions.

**Ordered steps**
1. Inspect toast positioning, stacking, transform ownership, dismissal rules, and whether the current animation supplies an otherwise missing final `top: 0`.
2. Establish final placement in the appropriate static rule if needed; do not blindly add `top: 0` to every toast.
3. Replace animated `top` with the small transform; replace literal duration/easing with shared tokens.
4. Make resting opacity/transform explicit where necessary so animation completion or removal cannot hide the toast.
5. Add Reduced Motion keyframes with opacity only, at most `80ms`, and the same final visible state.

**Hard boundaries**
- No toast queue, timeout, live-region, action, or dismissal redesign.
- Do not reuse a transform already responsible for stack positioning. Avoid persistent fill behavior that overrides stacking transforms.
- No unconditional `will-change`; no claim of compositor execution from CSS alone.

**Mechanical checks**
- Confirm `toast-enter` no longer animates `top`; verify final placement remains defined.
- Check stylesheet imports, shared token availability, reduced override precedence, and existing timer/dismissal tests.
- Confirm entering animation does not restart on unrelated toast content updates.

**Runtime/feel checks — to perform**
- Trigger single and successive toasts; dismiss during entry and interact with actions immediately.
- Check stacking, clipping, overlapping entries, keyboard focus visibility, and announcement timing in both motion modes.

**Source-drift stop condition**
- Stop if the real toast uses transform-based stacking, shared keyframes with other consumers, or animation-completion-driven lifetime logic. Resolve those contracts before changing entry.

### Plan C — Direct drag tracking and brief, interruptible settling

**Exact path/current excerpt**

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

**Target behavior and conventions**
- Preserve direct tracking while dragging; do not add smoothing or transitions between pointer samples.
- On release, settle to the valid slot over the shared `160ms` fast duration with responsive easing, interruptible by a new drag.
- Reduced Motion: immediate settle with persistent destination/selection feedback.

**Ordered steps**
1. Inspect the `--drag-y` consumer, coordinate space, `currentY` updates, slot calculation, animation API units, cancellation support, and reorder commit timing.
2. Verify the release target uses the latest position in the same coordinate space as `nearestSlot`; correct mapping only if inspection demonstrates a mismatch.
3. Confirm active tracking is not interpolated by CSS. Preserve existing pointer capture and cancellation behavior.
4. Read/convert existing semantic motion tokens through an existing project bridge, or add a small local adapter after confirming library units/easing support. Do not duplicate `160` as an unexplained constant.
5. Cancel in-flight settling before a new drag; prevent stale completion callbacks from committing an obsolete destination.
6. Implement instant reduced settling; retain destination, selected-item, focus, and existing announcement feedback.
7. Inspect keyboard reorder parity; if absent, record a separate accessibility dependency rather than inventing controls in this motion patch.

**Hard boundaries**
- Do not alter slot ordering rules, persistence semantics, scroll behavior, or commit timing without a demonstrated correctness issue.
- Do not impose pointer-event throttling without measurement. Do not add a new animation dependency.
- No mandatory wait for visual settling before another operation.

**Mechanical checks**
- Test coordinate conversion and latest-position selection; verify duration units and token parsing.
- Test release, cancellation, rapid re-grab, stale completion suppression, and reduced-mode settling.
- Confirm transforms/custom properties have one clear owner during tracking and settling.

**Runtime/feel checks — to perform**
- Drag slowly and rapidly, release near slot boundaries, re-grab mid-settle, and test scrolled containers.
- Check keyboard reorder where available, focus continuity, and destination feedback with Reduced Motion enabled.

**Source-drift stop condition**
- Stop if `animateTo` has different duration semantics, another controller owns settling, or `currentY` uses an undocumented coordinate space. Establish those contracts before tuning motion.

## 4. Execution order and unverified states

1. **Plan A:** establish scoped, token-based overlay behavior and the reduced-motion pattern.
2. **Plan B:** apply the same conventions to a contained entry animation.
3. **Plan C:** follow after coordinate, cancellation, and animation API contracts are understood.

**Explicitly unverified:** effective CSS cascade, palette visibility and keyframes, mount/unmount behavior, toast positioning and announcements, drag coordinate correctness, keyboard reorder support, focus restoration, Reduced Motion coverage, rendering performance, and perceived timing. All runtime/feel checks above are proposed acceptance checks—not completed validation.


## Output B

## 1. Recon summary

**Diagnosis:** The supplied motion rules diverge from the existing responsive tokens; the highest-leverage work is to align transient feedback, make overlay motion state-owned, and verify drag continuity before changing its physics.

- **Stack signals:** React-style TSX, CSS transitions/keyframes, a utility-style arbitrary animation class, and an imperative `animateTo` call. Framework, utility compiler, positioning system, and animation library are unconfirmed.
- **Motion locations:** Shared values and popover rules in `src/styles/motion.css`; palette animation in `src/components/CommandPalette.tsx`; toast keyframes in `src/components/toast.css`; pointer/release handling in `src/components/SortableQueue.tsx`.
- **Conventions:** `--duration-fast: 160ms`, `--duration-panel: 240ms`, and `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)`. This curve is strongly ease-out-like, not ease-in-out.
- **Local precedent:** `src/components/Button.css` explicitly transitions `transform`, uses semantic tokens, and supplies an 80ms Reduced Motion override. Preserve it; its specific press behavior is not a prescription for overlay travel.
- **Personality:** Calm, crisp desktop utility. Motion should explain a change, not delay input, focus, or repeated commands.
- **Frequency map—hypotheses, not measured usage:** Palette and button interactions are potentially high-frequency; popovers repeat during navigation; toasts are event-driven and may burst; drag events are high-frequency while a gesture is active, but reorder usage is unknown.
- **Evidence:** Supplied excerpts only. No full-file inspection, commit identifier, runtime checks, or validation results. The requirements attributed to `DESIGN.md` are accepted as supplied.

## 2. Vetted priorities

P1 means first implementation attention, not a demonstrated release blocker. No P0 is supported.

| ID / priority | Static evidence | Finding and runtime unknown | Smallest correction / acceptance evidence |
|---|---|---|---|
| M1 / P1 | Palette has an unconditional `palette_420ms_ease-in_both` class; `open` is exposed separately. | The shown animation declaration is not state-gated and bypasses tokens. Keyframes, mounting, visibility, and replay behavior are unknown. | State-owned, tokenized opacity transition; test immediate typing, rapid reversal, hidden-state focus exclusion, and focus restoration. |
| M2 / P1 verification gate | Drag writes `event.clientY`; release calls `nearestSlot(currentY)` with `duration: 400`. | Coordinate conversion, `currentY` freshness, capture, cancellation, presentation-value restart, and velocity handoff are not shown—not proven absent. | Establish those contracts first; preserve nearest-position targeting. Verify grab offset, 1:1 tracking, re-grab, cancellation, and keyboard parity. |
| M3 / P2 | Popover uses `transition: all 360ms ease-in` and centered origin. | Broad property ownership and timing mismatch are explicit. Whether center is inappropriate depends on placement and animated properties. | Explicit property list and fast responsive tokens; use trigger-relative origin only for verified anchored spatial motion. Test every supported placement. |
| M4 / P2 | Toast animates `top: -24px → 0` and opacity over `500ms ease-in`. | Layout-property animation is a risk, not evidence of dropped frames; positioning may determine whether `top` has any effect. | Move entrance offset to an owned transform with fast responsive timing; trace before making performance claims. |
| M5 / P2 | Only the button excerpt contains a Reduced Motion branch. | Coverage for the other surfaces is unverified; a global override could exist. Shorter spatial motion alone is not the target fallback. | Explicit scoped fallbacks: opacity/static feedback for overlays and toasts; direct drag tracking with immediate release placement. Test preference changes while active. |

**Vetted out:** No claim of layout thrashing from `transition: all`, guaranteed compositing from transforms, broken drag coordinates, or repeated palette playback. No new bounce, stagger, momentum targeting, or button rewrite is justified.

## 3. Implementation plans

### Plan A — State-owned palette and popover feedback
**Covers:** M1, M3, and overlay coverage in M5. Evidence baseline: supplied snippets; commit unknown.

**Exact paths/current excerpts**
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
    <div data-open={open} className="animate-[palette_420ms_ease-in_both]">
      <SearchResults />
    </div>
  );
}
```
**Target/conventions:** Immediate interaction and visible focus; restrained opacity feedback using `--duration-fast` and `--ease-responsive`. Preserve existing mounting, positioning, and accessibility ownership.
1. Inspect actual palette keyframes, generated CSS, open/closed selectors, overlay primitive, and mounting contract. Identify who owns focus, hidden state, exit retention, and placement transforms.
2. Replace the arbitrary palette animation with a named component class in the existing shared motion stylesheet; tie opacity targets to the existing `data-open` state. Use 160ms responsive transitions, with no new scale, translation, or result-list animation.
3. Keep closed content noninteractive and excluded from focus/accessibility navigation through the established primitive. Opening must not wait for animation; do not add an exit delay or custom focus trap.
4. Replace popover `all` with `opacity`; include `transform` only if existing state rules prove an intentional reveal transform that is separate from positioning. Use fast responsive tokens.
5. For verified anchored scale/reveal motion, consume the actual positioning system’s resolved origin, including collision changes. Preserve center for genuinely centered surfaces; do not invent a library variable.
6. Add scoped Reduced Motion rules: opacity-only, 80ms feedback; remove decorative transform changes while preserving any transforms needed for placement.

**Hard boundaries:** No token-value changes, dependency additions, primitive migration, positioning rewrite, search logic changes, or edits to `src/components/Button.css`. If the mounting contract cannot support transitions, resolve that contract before implementing—not with guessed lifecycle code.
**Mechanical checks:** Use the project’s actual typecheck, lint, and focused test commands after discovering them. Check generated selectors; assert palette animation-class removal, explicit popover transition properties, token use, and closed-state focus exclusion.
**Runtime/feel checks—planned:** Repeated keyboard open/type/Escape cycles; reversal mid-transition; result updates without entrance replay; focus restoration; anchored placements and collision flips; normal and Reduced Motion, including mid-transition preference changes.
**Source-drift stop:** Stop if cited classes, state attributes, tokens, authority, or primitive ownership differ materially, or if existing keyframes encode behavior beyond presentation.

### Plan B — Short, bounded toast entrance
**Covers:** M4 and toast coverage in M5. Evidence baseline: supplied snippet; commit unknown.

**Exact path/current excerpt**
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
**Target/conventions:** Preserve the existing entrance direction and 24px distance initially, but use transform/opacity over `--duration-fast` with `--ease-responsive`. No new exit choreography.
1. Inspect toast positioning, base `top`, stack layout, transform ownership, dismissal, and animation-event consumers. Confirm the final static position without animation.
2. Replace keyframe `top` values with `translateY(-24px)` and `translateY(0)`, retaining opacity endpoints. Establish final positioning in the static rule only if the existing animation currently supplies it.
3. Replace `500ms ease-in` with the fast/responsive tokens. Ensure retained animation fill cannot override dismissal or stack transforms; do not combine competing transform owners.
4. Add a separate opacity-only Reduced Motion entrance at 80ms. Ensure its final opacity remains visible and it introduces no decorative translation.

**Hard boundaries:** Scope edits to `src/components/toast.css`; preserve content, live-region semantics, dismissal availability, timeout length, stacking, and undo behavior. No blanket `will-change` or claimed compositor promotion. If a wrapper or event-consumer edit is needed, stop and expand scope explicitly.
**Mechanical checks:** Confirm `toast-enter` no longer animates `top`; verify token resolution and Reduced Motion cascade; test final visibility, dismissal during entry, and any existing animation-completion contract using discovered project commands.
**Runtime/feel checks—planned:** Single toast, rapid arrivals, stacked and multiline content, dismissal during entry, keyboard access, and hidden-tab return. Confirm notifications do not steal focus or delay action; collect a trace before asserting reduced layout work.
**Source-drift stop:** Stop if positioning differs from the excerpt’s implied endpoint, another transform owner exists, animation names drive lifecycle behavior, or shared tokens/Reduced Motion rules have changed.

### Plan C — Verify and harden drag continuity without changing reorder semantics
**Covers:** M2 and drag coverage in M5. Evidence baseline: supplied snippet; commit unknown.

**Exact path/current excerpt**
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
**Target/conventions:** Pointer-attached movement, interruption from the displayed position, bounded non-bouncy settling, and unchanged nearest-current-position slot selection. This is a contract-gated implementation, not permission to invent `animateTo` options.
1. Inspect pointer-down/cancel/lost-capture handlers, `--drag-y` consumer, `currentY` updates, scroll coordinates, slot calculation, keyboard reorder, and the actual `animateTo` signature and cancellation API.
2. Establish one coordinate space in CSS pixels. Capture the active pointer, preserve grab offset, and keep the displayed position and release position synchronized. Preserve existing drag-intent thresholds; add none speculatively.
3. Cancel an in-flight settle on re-grab and start from its presentation position. Audit transform ownership and the timing of `setDragging(false)` so state changes cannot reset the visual position before settling.
4. Measure recent position/time samples with monotonic timestamps; express release velocity in CSS px/s. Preserve `nearestSlot(currentY)` semantics using the verified current position, and pass bounded velocity in the supported animation API’s units.
5. Use existing token resolution for a duration-based settle: `--duration-panel` is the initial 240ms target, not a copied magic number. If the established primitive is spring-based, retain its verified configuration mechanism and tune a non-bouncy response; do not mislabel response time as duration.
6. Keep projection separate: a candidate is `clamp(y + v × horizonSeconds, firstSlot, lastSlot)` with bounded horizon and valid-slot clamping. Do **not** use it for target selection without separate authorization and runtime evidence.
7. Reduced Motion retains necessary 1:1 direct manipulation but removes autonomous release travel/overshoot: commit the nearest slot immediately, retaining static destination feedback, focus, and existing reorder announcements.

**Hard boundaries:** No inertia-based target change, new dependency, queue-data redesign, gesture-threshold change, or keyboard-contract change. If the current engine cannot expose/cancel presentation motion or accept velocity safely, stop for an explicit adapter/API decision rather than guessing.
**Mechanical checks:** Focused tests for coordinate conversion and scroll offset, latest release position, nearest-slot boundaries, cancellation, re-grab, velocity units, cleanup, and immediate Reduced Motion settlement; run discovered type/lint/test commands.
**Runtime/feel checks—planned:** Grab at different row offsets; slow and fast releases; leave bounds; scroll during drag; cancel; re-grab during settle; repeated and keyboard reorder; toggle Reduced Motion during drag/settle. Check 60/120Hz only where available; record actual conditions.
**Source-drift stop:** Stop if handler semantics, slot rules, coordinate ownership, token access, or `animateTo` API differ from the baseline or contradict the planned continuity contract.

## 4. Execution order and unverified states

1. **Revalidate evidence and authority**, especially overlay lifecycle and drag API contracts.
2. **Plan A first:** Highest likely keyboard-throughput leverage; resolve Reduced Motion alongside normal behavior.
3. **Plan B next:** Small, isolated correction with clear static acceptance checks.
4. **Plan C after its API gate:** Investigate early, but do not substitute faster timing for correct direct manipulation.

**Explicitly unverified:** Actual usage frequency; palette keyframes and mounting; popover anchoring; computed styles and global overrides; focus/accessibility-tree behavior; toast timing/stacking; drag capture, coordinates, velocity and interruption; browser compatibility; frame pacing; perceived feel; all Reduced Motion states. No files were edited, no plans were written to disk, and no browser/device or mechanical validation was performed.


## Output C

## 1. Recon summary

- **Stack signals:** React-style TSX, CSS transitions/keyframes, a utility-style arbitrary animation class, and imperative pointer handling. A utility framework and the implementation of `animateTo` are not confirmed.
- **Motion locations:** shared tokens and popovers in `src/styles/motion.css`; palette animation in `src/components/CommandPalette.tsx`; toast entrance in `src/components/toast.css`; drag/release logic in `src/components/SortableQueue.tsx`.
- **Existing conventions:** `--duration-fast: 160ms`, `--duration-panel: 240ms`, and `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)`. `src/components/Button.css` already uses a property-specific transition, restrained press feedback, and an 80ms Reduced Motion override. Preserve it.
- **Authority/personality:** the supplied description of `DESIGN.md` calls for crisp, token-based motion, visible focus, and Reduced Motion feedback. This console needs quiet causality, not decorative choreography.
- **Frequency map, inferred rather than measured:** palette and button interactions likely recur frequently; popovers recur during operational workflows; toast frequency depends on events; queue sorting depends on role. No daily counts are established.
- **Evidence level:** static excerpts only. Missing keyframes, mounting behavior, positioning logic, animation helpers, and global overrides limit conclusions. No runtime or accessibility validation was performed.

## 2. Vetted priorities

Priorities express implementation leverage, not measured user impact.

| Priority | Location | Supported finding | Recommended action |
|---|---|---|---|
| P1 | `src/components/CommandPalette.tsx` | The class declares a 420ms ease-in animation independently of `open`. Its keyframes and lifecycle are absent; replay on every toggle is not established. | Remove decorative palette animation; preserve immediate visibility, focus, and keyboard feedback. |
| P1 | `src/styles/motion.css` | `.popover` declares `transition: all 360ms ease-in`, overriding the available timing vocabulary and allowing unintended property transitions. | Restrict properties and use the 160ms responsive tokens. |
| P1 | `src/components/toast.css` | Entrance animates layout-position property `top` over 500ms with ease-in. Actual layout cost depends on positioning; dropped frames are not established. | Replace the positional animation with transform/opacity using the 240ms panel token. |
| P2 | `src/components/SortableQueue.tsx` | Release requests a fixed 400ms animation. Cancellation, continuity, velocity handling, and `currentY` freshness are not shown. | Shorten settling and explicitly implement interruption-safe ownership, after inspecting the helper. |
| P2 | All four target surfaces | No Reduced Motion handling appears in their excerpts; only the button demonstrates it. Global coverage may exist. | Verify effective coverage; add local paths where absent, preserving nonspatial feedback. |

**Not promoted to findings:** centered popover origin is only wrong if an anchored scaling reveal exists; CSS-variable drag writes alone do not establish expensive descendant updates or jank. No additive animation is justified by this evidence.

## 3. Implementation plans

### Plan 1 — Make command-palette access immediate

**Scope/current evidence — `src/components/CommandPalette.tsx`:**
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

**Target:** no animated delay on palette opening, closing, searching, or keyboard navigation. Visibility and focus change in the same interaction cycle; results do not stagger.

**Project conventions:** honor the supplied `DESIGN.md` requirements for crisp feedback and visible focus. Existing tokens in `src/styles/motion.css` are 160ms/240ms and `cubic-bezier(0.23, 1, 0.32, 1)`; this high-frequency surface deliberately needs no replacement animation.

**Ordered steps**
1. Inspect the complete component, `palette` keyframes, `[data-open]` rules, and its mounting/focus owner. Determine whether animation currently supplies visibility or hiding.
2. Remove `animate-[palette_420ms_ease-in_both]`; remove the empty `className` if appropriate. Preserve `data-open`, content, and component API.
3. Keep visibility under the established open-state mechanism. If animation owns visibility, stop and expand the plan before removing it.
4. Verify the existing focus owner focuses the input on open, restores focus on close, and excludes closed content from navigation. Do not introduce a second focus manager.

**Hard boundaries:** no new dependency, search behavior changes, result staggering, focus-outline suppression, or speculative dialog rewrite. Do not remove shared keyframes without proving they are unused.

**Mechanical checks:** confirm the palette has no animation class or inherited open/close motion; run existing typecheck/lint and palette tests using documented project scripts. Add regression coverage for open/close visibility and focus if the existing harness supports it; do not invent script names.

**Runtime/feel checks, to perform:** repeatedly open/type/Escape/reopen with the keyboard. Input must accept typing immediately, focus must remain visible, and closed results must not remain interactive. Check pointer opening too.

**Reduced Motion:** use the same immediate path. Visible content, focus, selection, and result changes provide feedback without travel or fades.

**Source-drift stop:** stop if the excerpt no longer matches, the keyframes have functional responsibilities, or visibility/focus changes require files beyond this component. Report the newly discovered owner and revise scope first.

### Plan 2 — Normalize popover and toast entrances

**Scope/current evidence — `src/styles/motion.css`:**
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

**Current evidence — `src/components/toast.css`:**
```css
@keyframes toast-enter {
  from { top: -24px; opacity: 0; }
  to { top: 0; opacity: 1; }
}

.toast {
  animation: toast-enter 500ms ease-in forwards;
}
```

**Target:** popover transitions use an explicit opacity/transform allowlist at 160ms; toast enters from `translateY(-24px)` to `translateY(0)` with opacity 0→1 over 240ms. Both use `var(--ease-responsive)`. Preserve toast final placement.

**Project conventions:** reuse the three existing tokens without renaming or changing their global values. Follow `src/components/Button.css`: property-specific transitions and a local 80ms Reduced Motion override. Leave button behavior unchanged.

**Ordered steps**
1. Inspect popover state selectors and placement ownership, toast positioning/stacking/dismissal, and effective Reduced Motion overrides. Confirm transform ownership before editing.
2. Replace popover `transition: all 360ms ease-in` with `transition: opacity var(--duration-fast) var(--ease-responsive), transform var(--duration-fast) var(--ease-responsive)`. If transform belongs to placement rather than reveal, omit it instead of animating positioning updates.
3. Retain current popover visual endpoints. Do not add scaling merely to justify changing `transform-origin`; change origin only in a separately scoped anchored-scale fix.
4. Replace toast `top` keyframes with the target transform/opacity endpoints; use `animation: toast-enter var(--duration-panel) var(--ease-responsive) forwards`.
5. Preserve the old final layout position statically: if positioned `top: 0` was supplied only by the animation, establish it in the base rule. Stop if this conflicts with the stack positioner.
6. Add local Reduced Motion rules: popover transitions opacity only for 80ms; toast uses an opacity-only 0→1 entrance for 80ms with the same easing and fill behavior. Keep final placement available independently of animation.

**Hard boundaries:** only the two listed CSS files; no new library, global token changes, stacking rewrite, additional stagger, or guessed placement-library variables. Do not overwrite transforms used by a positioner, drag, or stack.

**Mechanical checks:** inspect the diff for removal of `transition: all` and animated `top`; verify token references and local media-query coverage. Run existing stylesheet/build checks and relevant component tests. Confirm no positioning rule relies on removed animation output.

**Runtime/feel checks, to perform:** open/close/reopen popovers rapidly; test all supported placements and repositioning. Check single and stacked toast arrivals and dismissal during entry. At normal speed and slowed playback, look for jumps, overwritten transforms, focus loss, or invisible interactive elements.

**Reduced Motion:** no animated positional entrance; 80ms opacity feedback remains. Verify computed behavior with the preference enabled, including any existing global overrides.

**Source-drift stop:** stop if excerpts differ, transform ownership conflicts, keyframes are shared, or mount/dismiss behavior requires component changes. Do not silently replace the lifecycle with a new presence system.

### Plan 3 — Make queue release short and interruptible

**Scope/current evidence — `src/components/SortableQueue.tsx`:**
```tsx
function onPointerMove(event: PointerEvent) {
  queueRef.current?.style.setProperty("--drag-y", `${event.clientY}px`);
}

function onPointerUp() {
  setDragging(false);
  animateTo(nearestSlot(currentY), { duration: 400 });
}
```

**Target:** direct pointer tracking remains unlagged. Release settles to the existing nearest-slot target over 160ms using `cubic-bezier(0.23, 1, 0.32, 1)`. A new drag interrupts settling from its current rendered position, without snapping back. This is a bounded settle, not an inertial fling.

**Project conventions:** resolve `--duration-fast` and `--ease-responsive` from the established token mechanism; their supplied values are 160ms and the curve above. Follow existing animation APIs and Reduced Motion preference infrastructure; do not guess `animateTo` options.

**Ordered steps**
1. Inspect `animateTo`, pointer-down/cancel handling, `currentY` updates, `--drag-y` consumers, and coordinate conversion. Identify animation ownership, cancellation support, and timing units.
2. If the helper already supports easing and cancellation, retain its API and replace the 400ms release with the token-based 160ms settle. Otherwise stop and scope the helper change explicitly.
3. Ensure release reads the latest drag position in the same coordinate system as `nearestSlot`. Preserve existing slot selection and commit semantics.
4. On re-grab, capture the current visual offset, cancel the prior settle, and initialize drag offset from that position. Prevent obsolete completion callbacks from committing stale state.
5. Ensure pointer cancellation/unmount clears animation ownership. Keep pointer tracking free of CSS easing; do not alter the custom-property approach without evidence of a problem.
6. Branch on the current Reduced Motion preference: commit the target immediately without a settling tween, while preserving direct manipulation and existing destination/selection feedback.

**Hard boundaries:** no physics dependency, invented spring parameters, fling behavior, reorder algorithm changes, or speculative performance rewrite. No blanket removal of keyboard focus or status feedback.

**Mechanical checks:** use existing tests to cover latest-position release, coordinate conversion, cancellation, stale completion prevention, rapid re-grab, and immediate Reduced Motion completion. Verify duration units and absence of a transition that eases pointer tracking; run documented typecheck/lint scripts.

**Runtime/feel checks, to perform:** drag slowly and quickly, release near slot boundaries, re-grab during settling, cancel a drag, and test scrolling during drag. Confirm stable pointer offset, one final order commit, visible destination feedback, and unchanged keyboard reordering if supported.

**Reduced Motion:** pointer-driven motion remains under user control; autonomous settling is removed. Final order and visible focus/selection must still communicate the result. If existing feedback is insufficient, stop and scope that work rather than adding an unreviewed effect.

**Source-drift stop:** stop if the excerpt differs, timing units are not milliseconds, the helper lacks required controls, coordinate ownership is unclear, or implementation requires edits outside this file.

## 4. Execution order and unverified states

1. **Plan 1:** highest likely frequency, smallest intended change.
2. **Plan 2:** shared timing consistency and removal of layout-position animation.
3. **Plan 3:** execute after resolving animation-helper and coordinate contracts; it has the largest evidence gap.

**Explicitly unverified:** actual usage frequency; compiled styles and token availability; palette keyframes and focus lifecycle; popover anchoring; toast stacking and positioning; drag helper semantics, coordinates, and interruption behavior; effective Reduced Motion coverage; assistive-technology behavior; browser/device performance and subjective feel.

No files were edited or plans written to disk. All runtime checks above are future acceptance checks, not completed validation.
