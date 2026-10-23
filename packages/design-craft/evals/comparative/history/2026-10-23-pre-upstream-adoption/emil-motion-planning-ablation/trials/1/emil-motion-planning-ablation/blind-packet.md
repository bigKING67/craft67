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

- **Stack signals:** React/TSX, CSS custom properties, CSS transitions/keyframes, an arbitrary animation utility, and imperative pointer handling. The utility framework and `animateTo` implementation are not established.
- **Motion locations:** shared values in `src/styles/motion.css`; palette motion in TSX; toast motion in component CSS; queue motion in pointer handlers.
- **Existing conventions:** `--duration-fast: 160ms`, `--duration-panel: 240ms`, and `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)`. The button demonstrates a scoped `transform` transition, restrained press feedback, and an 80ms Reduced Motion override.
- **Authority/personality:** preserve the existing crisp, calm, semantic-token-based system and visible focus. Motion should explain state changes, not delay keyboard work.
- **Frequency map — expected, not measured:** palette = frequent keyboard invocation; popover = repeated contextual interaction; toast = event-driven and potentially bursty; queue = continuous during a drag plus one release; button = frequent baseline feedback.
- **Evidence level:** static excerpts only. Missing selectors, keyframes, lifecycle code, positioning logic, helpers, and global accessibility rules limit conclusions. No performance, usability, or accessibility failure has been measured.

## 2. Vetted priorities

| Priority | Finding supported by excerpts | Consequence / implementation decision |
|---|---|---|
| P1 | Popover uses `transition: all 360ms ease-in` and a centered origin. | Broad transition scope and bespoke timing conflict with the local crisp-motion precedent. Scope properties; anchor the origin only if placement information is available. |
| P1 | Palette declares a 420ms ease-in animation independently of `data-open`. | Open/close coupling, replay, and hidden-state behavior are not shown. Establish lifecycle semantics before replacing the animation. |
| P1 | Toast entrance animates `top` for 500ms with ease-in. | `top` is a layout-affecting property when applicable; actual cost depends on positioning. Replace entrance travel with a dedicated transform after checking transform ownership. |
| P1 | Queue directly writes pointer Y, then requests a 400-duration settlement. | Direct tracking is worth preserving. Release timing is bespoke; units, coordinate mapping, cancellation, and interruption behavior need inspection. |
| P1, cross-cutting | Only the button excerpt shows Reduced Motion handling. | Coverage elsewhere is unestablished, not proven absent. Inspect global handling and supply explicit equivalent feedback where necessary. |

All three plans below are proposed work, not completed implementation or validation.

## 3. Implementation plans

### Plan A — Make contextual surfaces immediate, state-driven, and interruptible

**Files/current excerpts**
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

**Target behavior:** opening responds immediately; a short entrance preserves causality without gating input. Closing removes interactivity immediately. Rapid reopen reverses or restarts from the current visual state without a delayed focus change.

**Project conventions:** reuse the fast/panel durations and responsive easing; follow the button’s explicit-property precedent. Do not change shared token values.

**Ordered steps**
1. Inspect palette keyframes, utility generation, mounting/visibility rules, focus ownership, and popover placement/transform ownership.
2. Replace `all` with only the properties actually changing. Prefer opacity plus, if useful, at most 4px of entrance translation; omit translation if it conflicts with positioning.
3. Use `--duration-fast` and `--ease-responsive` for both surfaces initially. Reserve panel timing for an actual panel-sized transition, not merely its component name.
4. Replace the unconditional palette animation class with explicit open/closed styling. Attach entrance to the real opening lifecycle; define initial-render behavior deliberately.
5. Keep hidden content noninteractive and out of tab order/accessibility exposure using the existing visibility mechanism. Do not use opacity alone. Preserve focus entry/restoration without waiting for animation.
6. Prefer immediate close unless the existing presence mechanism safely supports a short exit. If retaining exit, handle interruption and unmount cleanup.

**Hard boundaries:** no overlay architecture rewrite, search behavior change, new animation dependency, or overwrite of positioning transforms. No invented placement selectors or keyframe definitions.

**Mechanical checks:** verify the old class and `transition: all` are removed from these targets; confirm token resolution and generated styles; test open/close/reopen, initially open, unmount, and hidden tab exclusion using the existing test setup.

**Runtime/feel checks — pending:** keyboard invoke → type immediately → Escape → reopen; inspect focus visibility/restoration, placement variants, clipping, and repeated invocation. Confirm feedback feels immediate rather than staged.

**Reduced Motion:** remove entrance translation/scale; use immediate visibility or an explicit opacity-only fade capped at the local 80ms precedent. Preserve focus and open/closed state feedback; never await animation completion for correctness.

**Source-drift stop condition:** stop if the full files use a different presence owner, competing animation system, or shared positioning transform. Re-map ownership before changing selectors or lifecycle behavior.

### Plan B — Shorten toast arrival without changing notification semantics

**File/current excerpt**
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

**Target behavior:** a toast becomes readable promptly with a restrained entrance; notification stacking and dismissal remain stable.

**Project conventions:** use `--duration-fast` and `--ease-responsive`; explicitly animate only opacity and an owned transform. Preserve existing notification semantics.

**Ordered steps**
1. Inspect toast positioning, final `top`, stacking/reflow rules, transforms, dismissal, and whether timers or handlers depend on this animation.
2. Replace the `top` keyframes with opacity `0 → 1` and a small `translateY(-4px) → translateY(0)` entrance, only where that transform is exclusively owned.
3. Set duration/easing from existing tokens. Establish the final position and visible state in normal styles so fill mode is not responsible for persistent correctness.
4. Preserve current mounting and announcement behavior; ensure removing motion does not suppress delivery, dismissal, or timer cleanup.
5. If stack placement already owns transform, use opacity-only entrance rather than adding a wrapper or replacing the placement transform without review.

**Hard boundaries:** no changes to notification priority, live-region policy, display lifetime, stack order, or automatic focus behavior. No permanent `will-change` or claim of guaranteed compositor execution.

**Mechanical checks:** verify no `top` interpolation remains in these entrance keyframes; confirm final styles work with animations disabled; test multiple arrivals, dismissal during entrance, and any animation-event-dependent cleanup.

**Runtime/feel checks — pending:** inspect single and burst arrivals, multiline content, stack repositioning, and dismissal. Check readability and distraction during keyboard work; measure performance before making performance claims.

**Reduced Motion:** opacity-only entrance capped at 80ms, or immediate appearance. Keep the message, announcement, controls, and full intended reading opportunity intact.

**Source-drift stop condition:** stop if `top: 0` currently establishes final placement, keyframes are shared with other surfaces, or animation completion controls notification lifetime. Resolve those dependencies before substitution.

### Plan C — Preserve direct drag tracking; make settlement short and cancellable

**File/current excerpt**
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

**Target behavior:** the item follows input without easing during drag; release settles once toward the valid slot. A new interaction interrupts settlement immediately.

**Project conventions:** retain the direct-manipulation path. Use fast-duration/responsive-easing semantics for release through the project’s existing JS token access mechanism, if one exists.

**Ordered steps**
1. Inspect `animateTo` duration units, easing/cancellation API, `currentY` updates, `--drag-y` consumers, coordinate conversion, pointer capture, and reorder commit semantics.
2. Verify pointer coordinates and slot coordinates share a frame, including scroll offsets and grab offset. Correct only confirmed mismatches; do not assume raw `clientY` is wrong.
3. Ensure the rendered drag property has no smoothing transition while dragging. Do not introduce a spring or per-event React state update solely for motion.
4. Replace the hard-coded release timing with the resolved fast token; convert units explicitly. Map responsive easing only after confirming the helper’s supported format.
5. Cancel existing settlement on a new drag, pointer cancellation, and unmount. Commit the destination exactly once through the existing reorder contract, independent of decorative animation completion.
6. If there is no supported token bridge, pause to agree a minimal bridge rather than duplicating `160` as an undocumented constant.

**Hard boundaries:** no reorder algorithm rewrite, speculative event throttling, new drag library, or new layout reads in `onPointerMove`. Do not imply pointer motion supplies keyboard reordering.

**Mechanical checks:** test coordinate mapping, latest-pointer release, single commit, rapid re-grab, cancellation, and cleanup. Verify duration units and resolved tokens; inspect CSS for unwanted drag-time transitions.

**Runtime/feel checks — pending:** try short/long drags, scrolling, release near slot boundaries, and rapid re-grab. Check that tracking feels attached and release does not hold the next action. Verify existing keyboard reorder feedback and focus separately.

**Reduced Motion:** retain necessary pointer-following movement; snap to the destination on release without decorative travel. Preserve the final order, focus, and existing destination/status feedback. Reuse preference handling that responds to changes and cleans up subscriptions.

**Source-drift stop condition:** stop if the helper lacks interruption support, settlement commits order internally, or drag/slot coordinates use undocumented transforms. Resolve the contract before adjusting timing.

## 4. Execution order and verification limits

1. **Inspect ownership and global Reduced Motion handling first.** Confirm tokens, lifecycle contracts, and existing tests; do not widen scope speculatively.
2. **Execute Plan A**, prioritizing palette keyboard continuity; **then Plan B** for the smaller CSS-focused change.
3. **Execute Plan C** after resolving the helper and coordinate contracts. Validate each plan before tuning durations further.

**Explicitly unverified:** compiled utilities and keyframes; computed styles; actual focus/hidden-state semantics; global Reduced Motion coverage; announcement behavior; placement and clipping; toast stacking; drag coordinates and cancellation; keyboard reorder support; frame timing, browser/device behavior, and perceived feel. No runtime or accessibility validation is claimed.


## Output B

## 1. Recon summary

**Diagnosis:** The excerpts mix a crisp, tokenized button precedent with longer, hard-coded transient animations. The highest-leverage work is to align those transitions, make lifecycle ownership explicit, and verify drag continuity before changing its physics.

- **Stack signals:** React-style TSX, CSS transitions/keyframes, an arbitrary-value animation utility, and imperative pointer handling. The utility framework and `animateTo` implementation are unknown.
- **Motion locations:** shared tokens and popover rules in `src/styles/motion.css`; palette animation in `src/components/CommandPalette.tsx`; toast keyframes in `src/components/toast.css`; drag/release logic in `src/components/SortableQueue.tsx`.
- **Existing conventions:** `--duration-fast: 160ms`, `--duration-panel: 240ms`, and `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)`. That curve is strongly ease-out-like, not ease-in-out.
- **Local precedent:** `src/components/Button.css` explicitly transitions only `transform`, uses semantic tokens, and provides an 80ms Reduced Motion branch. Preserve it; do not treat shorter spatial animation as the universal accessibility solution.
- **Personality:** calm, utilitarian, immediate; motion should explain state changes, not require users to wait for them.
- **Frequency map, inferred rather than measured:** button feedback and command invocation are likely frequent; popovers recur during navigation; toast frequency depends on workflows; dragging is continuous while active, but session frequency is unknown.
- **Evidence:** supplied static excerpts only. No full-file inspection, commit identity, computed styles, runtime measurements, accessibility-tree inspection, or user validation. `DESIGN.md` authority is supplied by the brief, not independently inspected.

## 2. Vetted priorities

P1 denotes a high-priority implementation investigation, not a demonstrated task blocker. No P0 is supported.

| ID / priority | Source proof | Finding and runtime unknown | Smallest correction / acceptance |
|---|---|---|---|
| F1 / P1 | Palette has constant `animate-[palette_420ms_ease-in_both]`; `open` appears only in `data-open`. | The excerpt does not connect animation lifecycle to open/close. Other selectors or mounting behavior may do so; repeated animation and focus failure are not established. | Tie visual states to the actual lifecycle, use fast tokenized entry, and keep input/focus independent of completion. Verify reopen, Escape, and rapid toggling. |
| F2 / P1 investigation | Queue writes `event.clientY`; release uses `nearestSlot(currentY)` and `{ duration: 400 }`. | Coordinate conversion, current-value synchronization, capture, cancellation, and interruption are not shown. Neither broken tracking nor missing support is proven. | Establish one position owner and interruptible settling; preserve nearest-slot semantics. Verify grab offset, scrolling, cancellation, and re-grab. |
| F3 / P2 | Popover uses `transition: all 360ms ease-in` and centered origin. | Broad transition ownership and timing diverge from local conventions. Center origin is only wrong if placement is anchored and scale is used. | Explicit property allowlist, existing timing/easing tokens, and placement-derived origin where applicable. Verify every supported placement. |
| F4 / P2 | Toast animates `top: -24px → 0` over `500ms ease-in`. | Layout-property animation is a potential cost; positioning mode and actual frame cost are unknown. | Replace entry travel with transform plus opacity, preserve the final position, and use fast tokens. Verify stacking and collect a trace before claiming performance improvement. |
| F5 / P2 | Only the button excerpt includes a Reduced Motion branch. | Coverage for other surfaces is unproven, not demonstrably absent product-wide. | Explicit non-spatial transient feedback and immediate drag settling under reduced motion; verify both initial preference and preference changes. |

**Set aside:** button redesign, additional success flourishes, new animation dependencies, and momentum-based slot selection. None has sufficient evidence or product justification.

## 3. Implementation plans

All checks below are **future acceptance work**, not completed validation. Before each plan, inspect the named full files, applicable instructions, `DESIGN.md`, consumers, and package scripts. Record a baseline revision; do not invent build commands or animation APIs.

### Plan A — Tokenized, state-owned popovers and command palette
**Covers:** F1, F3, and overlay coverage of F5.

**Exact current evidence:**
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
**Target / conventions:** immediate operability with a 160ms entry using `--duration-fast` and `--ease-responsive`; no animation of search-result updates. Preserve visible focus and established overlay semantics.
1. Locate `palette` keyframes, animation utility configuration, `data-open` consumers, mount/unmount owner, and popover placement/state rules. Determine whether these surfaces share styling; do not assume they do.
2. Keep shared token values unchanged. Replace popover `all` with `opacity, transform` only where those properties actually change; omit transform if no spatial state exists. Use fast duration and responsive easing.
3. For scaled anchored popovers, derive origin from resolved placement, including flips. Preserve centered origin for a genuinely centered surface.
4. Replace the palette’s unconditional animation utility with explicit open/closed styling. Use opacity-only entry; close without an animated delay. Reopening must start from the currently displayed opacity rather than restarting a keyframe.
5. Ensure the closed surface is not interactive or focusable through the existing lifecycle owner. Focus entry, Escape handling, and focus return must not depend on `animationend`.
6. Add scoped Reduced Motion styling: remove entry/exit translation and scale; retain an 80ms opacity transition, static open state, and immediate visible focus.

**Hard boundaries:** no token-value changes, button edits, new dependencies, result-row choreography, overlay primitive migration, or search-behavior changes. If lifecycle ownership lies elsewhere, identify the exact additional file and approve scope before editing.
**Mechanical checks:** run declared typecheck/lint/build and relevant tests; verify generated CSS contains the intended selectors; test closed-state focus exclusion, rapid reopen, and completion without animation events.
**Runtime/feel checks:** keyboard invocation → immediate typing; Escape and repeated toggles during entry; visible focus and return; all actual anchor placements; reduced motion enabled before opening and toggled while open.
**Source-drift stop:** stop if token values, palette keyframes, `open` ownership, popover placement contract, or the cited utility/rule differ materially. Reconcile existing global Reduced Motion rules before adding overrides.

### Plan B — Short, non-layout toast entry
**Covers:** F4 and toast coverage of F5.

**Exact current evidence:**
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
**Target / conventions:** a short arrival cue without delaying reading, announcements, dismissal, or actions. Use `--duration-fast` and `--ease-responsive`; preserve existing toast placement and semantics.
1. Inspect positioning mode, base `top`, transform ownership, stacked-toast rules, dismissal lifecycle, and any existing accessibility overrides.
2. Remove `top` from keyframes. Where the existing `top: 0` endpoint controls positioning, move that resting value into the appropriate base rule; do not add positioning or alter layout for statically positioned toasts.
3. Use `translateY(-8px) → translateY(0)` plus `opacity: 0 → 1` over the fast token. Explicitly retain final opacity/transform in the base state so animation fill is not responsible for resting geometry.
4. Preserve any existing transform composition. If positioning already owns transform, stop for an explicit composition decision rather than overwriting it.
5. Under Reduced Motion, use separate opacity-only entry keyframes over 80ms; remove decorative entry displacement without removing transforms required for positioning.

**Hard boundaries:** changes confined to `src/components/toast.css` unless scope is explicitly reopened. No lifetime changes, announcement changes, new wrappers/dependencies, bounce, exit animation, or stack-reordering feature.
**Mechanical checks:** verify `top` is absent from entry keyframes; check token availability, base endpoint, cascade, and Reduced Motion keyframes; run declared CSS/build checks and relevant toast tests.
**Runtime/feel checks:** single toast, bursts, multiline content, actionable toast, immediate dismissal, and existing exits; confirm no endpoint jump or positioning regression. Compare baseline/changed traces before making any frame-cost claim.
**Source-drift stop:** stop if the current keyframes, positioning contract, transform owner, or token availability differ from these prerequisites. Reconcile an existing reduced-motion implementation rather than layering conflicting animation rules.

### Plan C — Explicit drag ownership and interruptible nearest-slot settle
**Covers:** F2 and drag coverage of F5. This plan has a required API/coordinate discovery gate.

**Exact current evidence:**
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
**Target / conventions:** direct 1:1 dragging with preserved grab offset, followed by a restrained settle from the displayed position. Keep `nearestSlot(currentY)` selection semantics; target 160ms settling using existing tokens where the API supports them.
1. Resolve the `--drag-y` consumer, `currentY` writer, pointer-down/cancel handlers, scrolling coordinate system, and complete `animateTo` signature. Record duration units and cancellation/current-value capabilities.
2. Establish a single coordinate space in CSS pixels. Convert pointer coordinates relative to the drag container, including scrolling, and preserve initial grab offset. Synchronize the displayed position and release position from one owner.
3. Verify or add pointer capture and cancellation cleanup. During direct dragging, disable interpolation on the pointer-owned translation; do not add smoothing lag.
4. On re-grab, capture the current displayed position before cancelling settlement and initialize the new grab offset from it. On release, preserve the displayed transform across `setDragging(false)`, then settle to the nearest valid slot.
5. Replace the hard-coded 400 only through the existing animation API and established CSS-token bridge. If no bridge exists, explicitly scope a local conversion with verified units rather than inventing helper capabilities or duplicating token values.
6. Inspect velocity support separately: measure release velocity in CSS px/s if needed; hand it off only through a verified API with bounded, non-overshooting behavior. If unsupported, retain a positional settle and record velocity continuity as unverified.
7. Under Reduced Motion, retain direct pointer tracking, immediately commit the nearest slot on release, and preserve static selection/insertion feedback and visible keyboard focus. Preference changes must cancel active decorative settling.

**Hard boundaries:** no animation-library migration, new dependency, bounce, input lock, persistence change, or keyboard reorder redesign. Do not silently expand beyond `src/components/SortableQueue.tsx` and identified motion consumers.
**Projection gate:** a future momentum proposal would compute `clamp(position + velocity × horizonSeconds, validBounds)` in CSS pixels before nearest-slot selection. It requires separate authorization; this plan does **not** replace nearest-current-position targeting.
**Mechanical checks:** run declared type/lint/tests; add deterministic tests for coordinate conversion, grab offset, nearest-slot bounds, stale-position prevention, cancellation, re-grab, and zero-animation reduced-motion completion.
**Runtime/feel checks:** slow/fast drags, container scrolling, out-of-bounds pointer movement, first/last slots, release then immediate re-grab, cancellation, and existing keyboard reorder/focus behavior. Record observations; do not infer smoothness from transform usage.
**Source-drift stop:** stop if `--drag-y` is already converted downstream, `currentY` has a different meaning, slot selection differs, or `animateTo` cannot expose/cancel its current presentation. Resolve ownership/API scope before editing.

## 4. Execution order and unverified states

1. **Plan A first:** highest likely keyboard-workflow leverage; establishes restrained transient-state conventions.
2. **Plan B next:** bounded CSS change with explicit geometry and accessibility checks.
3. **Plan C discovery in parallel, implementation after its gate:** elevate immediately if runtime checks reveal lost input, jumps, or incorrect reorder outcomes.

**Explicitly unverified:** actual invocation frequency; final computed timings; palette visibility and focus lifecycle; popover anchoring/flipping; toast positioning, stacking and announcement timing; drag coordinate ownership, capture, velocity and cancellation; Reduced Motion coverage and preference changes; frame pacing, compositing, device behavior, and perceived feel. No files were edited or plans written to disk.


## Output C

## 1. Recon summary

- **Stack signals:** React/TSX, CSS keyframes/transitions, a utility-style arbitrary animation class, and imperative pointer handling. The CSS utility processor and `animateTo` implementation are unknown.
- **Motion locations:** shared tokens/popover rules in `src/styles/motion.css`; component motion in `CommandPalette.tsx`, `toast.css`, `SortableQueue.tsx`, and `Button.css`.
- **Existing conventions:** `--duration-fast: 160ms`, `--duration-panel: 240ms`, and `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)`. The button already uses an explicit transform transition, subtle `scale(0.98)`, and an 80ms Reduced Motion override. Preserve that precedent.
- **Authority/personality:** `DESIGN.md` requires crisp, token-based motion, visible focus, and feedback under Reduced Motion. Favor quiet, immediate responses over decorative entrances, staggering, or bounce.
- **Frequency map — inferred, not measured:** command palette and button feedback are likely frequent; popovers recurring; toast frequency depends on workflow; sorting is task-dependent, with continuous updates during each drag.
- **Evidence level:** supplied static excerpts only. Findings concern declarations and exposed contracts—not observed latency, dropped frames, inaccessible states, or actual interruption behavior.

## 2. Vetted priorities

| # | Priority | Location | Supported finding and limitation | Action |
|---|---|---|---|---|
| 1 | P1 | `src/components/CommandPalette.tsx` | Declares a 420ms ease-in animation on a keyboard-oriented surface. Class is unconditional; keyframes and mounting behavior are absent, so replay on every toggle is **not established**. | Remove decorative palette animation; preserve immediate state and focus feedback. |
| 2 | P1 | `src/styles/motion.css` `.popover` | `transition: all 360ms ease-in` bypasses tokens and can animate unrelated property changes. Actual transitioned properties are unknown. | Explicit property allowlist, 160ms responsive easing. |
| 3 | P1 | `src/components/toast.css` | Entrance animates `top` over 500ms with ease-in. `top` is layout-affecting when positioning applies; actual layout cost is unmeasured. | Use a short transform/opacity entrance without changing resting layout. |
| 4 | P1 verification gate | Palette, popover, toast, queue excerpts | No local Reduced Motion path is shown for these surfaces. Global handling may exist; absence across the application is **not proven**. | Resolve effective coverage and include a preserved-feedback path in every plan. |
| 5 | P2 | `src/components/SortableQueue.tsx` | Release requests a fixed 400-duration animation; units, cancellation, and presentation-state handoff are unknown. Pointer movement writes a custom property whose consumers are absent. | Establish coordinate ownership and interruption contracts before changing the settle behavior. |

`transform-origin: center` is **not independently a defect**: anchored scaling and actual placement are unverified. Likewise, the custom-property write alone does not prove broad style invalidation. No additive animation opportunities are justified by these excerpts.

## 3. Implementation plans

All checks below are **future acceptance checks**, not completed validation. No files have been edited or plans written to disk.

### Plan 1 — Make the command palette immediate

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

**Target:** no decorative open/close animation, result stagger, or animation-dependent input delay. Opening, typing, navigating, executing, and closing remain immediate.

**Project conventions:** honor `DESIGN.md`’s crisp feedback and visible focus. `src/components/Button.css` establishes restrained local motion; this high-frequency surface deliberately needs no duration token because it needs no animation.

**Ordered steps**
1. Inspect the actual palette keyframes, `data-open` selectors, mounting owner, and focus lifecycle. Determine whether animation currently supplies visibility or completion events.
2. Remove `className="animate-[palette_420ms_ease-in_both]"`; preserve `data-open={open}`, `SearchResults`, and component identity.
3. Preserve existing explicit open/closed visibility semantics. If they depend on animation, stop for a scoped visibility contract rather than merely deleting the class.
4. Remove obsolete palette keyframes only after confirming they have no other consumers and identifying their exact file.
5. Preserve immediate focus placement, Escape handling, focus return, selection indication, and result feedback. Do not add timeouts to coordinate these.

**Hard boundaries:** no search/ranking changes, remounting changes, new animation dependency, global animation reset, or accessibility redesign. Undisclosed selector/keyframe files require an explicit scope update before editing.

**Mechanical checks:** diff confirms the arbitrary animation class is absent; tests cover closed/open/closed visibility, immediate keyboard input, Escape, and focus return. Run the project’s declared typecheck/lint/test scripts after inspecting its package configuration; commands are not supplied by this evidence.

**Runtime/feel checks:** repeatedly open, type, navigate, execute, and close; confirm no stale visible results, input gating, focus flash, or invisible focusable closed content. Test rapid reopen and empty/loading/error results.

**Reduced Motion:** identical immediate behavior; visible focus, selected-result styling, and textual status remain. Do not substitute another entrance animation.

**Source-drift stop:** stop if the excerpt differs materially, `open` has different semantics, or visibility/focus depends on animation events. Resolve those dependencies before applying this plan.

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

**Target:** 160ms responsive entrances; only explicitly owned transform/opacity properties animate. Notifications remain readable immediately, with no changes to dismissal deadlines.

**Project conventions:** reuse `var(--duration-fast)` and `var(--ease-responsive)` exactly; preserve the 240ms panel token. Follow `src/components/Button.css`’s explicit-property transition and local 80ms Reduced Motion precedent.

**Ordered steps**
1. Inspect popover open/closed selectors and toast positioning, mounting, stacking, dismissal, and transform ownership. Identify effective global Reduced Motion rules.
2. Replace the popover declaration with:
   ```css
   transition: transform var(--duration-fast) var(--ease-responsive),
               opacity var(--duration-fast) var(--ease-responsive);
   ```
   Preserve existing endpoints; omit transform from this allowlist if positioning owns it or no motion transform exists. Do not introduce scaling merely to justify an origin change.
3. Keep the center origin unless anchored scaling is confirmed. If confirmed, use the existing positioning system’s actual origin value; do not invent a provider-specific variable.
4. For a toast with no competing transform owner, replace the entrance with:
   ```css
   @keyframes toast-enter {
     from { transform: translateY(-24px); opacity: 0; }
     to { transform: translateY(0); opacity: 1; }
   }
   .toast {
     animation: toast-enter var(--duration-fast) var(--ease-responsive) backwards;
   }
   ```
   Make resting opacity/transform explicit where necessary; preserve the original resting `top: 0` through static positioning if the animation previously supplied it. Do not add positioning modes.
5. Keep this keyframe as a one-time entrance only. If toast reorder/dismiss/re-entry shares it, stop and scope a state-transition implementation against the real lifecycle.
6. Add local Reduced Motion rules: popover opacity-only transition at 80ms with responsive easing; entrance movement switches instantly to its resting value. Toast uses opacity-only keyframes from 0 to 1 at 80ms. Preserve positioning transforms.

**Hard boundaries:** only the two named files initially; no global token retiming, button changes, new dependencies, permanent `will-change`, toast timeout changes, or invented exit animation. Shared positioning transforms must not be overwritten.

**Mechanical checks:** scoped diff contains no `transition: all`, animated `top`, or original 360/500ms ease-in declarations. Verify base resting styles and media overrides; run declared lint/build/tests. Test toast removal independent of entrance completion.

**Runtime/feel checks:** open/close/reopen popovers midway; confirm current-state retargeting where the existing lifecycle permits it. Test placement flips, scroll, stacked toasts, long messages, burst arrivals, and immediate dismissal. Inspect normal speed and slowed playback for layout shifts or competing transforms; use a trace before asserting performance improvement.

**Reduced Motion:** verify no entrance translation/scale remains, placement stays correct, and readable toast content, focus, dismissal controls, and any existing announcements survive. Switching preference while open must not leave intermediate styles.

**Source-drift stop:** stop if selectors differ, tokens are unavailable, transform ownership conflicts, or implementation requires undisclosed lifecycle/positioning edits. Resolve exact owner paths before expanding scope.

### Plan 3 — Make queue settling interruptible without changing sorting semantics

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

**Target:** direct pointer tracking, a continuous release-to-settle handoff, and immediate re-grab from the displayed position. Preserve `nearestSlot(currentY)` selection; do not introduce momentum-based destination changes.

**Project conventions:** honor `DESIGN.md`’s restrained motion and preserved feedback. Reuse the existing animation mechanism if capable. `--duration-fast: 160ms` and `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)` remain CSS conventions, not guessed options for an unknown JS API.

**Ordered steps**
1. Resolve `animateTo`, duration units, `currentY` updates, `--drag-y` consumers, animated element identity, pointer capture, cancellation, and reorder commit timing. Record exact owner paths before expanding beyond this file.
2. Establish one coordinate contract: pointer positions converted into the existing queue coordinate space, preserving grab offset and scroll behavior. Keep logical position and rendered drag position synchronized.
3. On grab during settling, sample the presentation position before cancelling the prior animation. Start direct tracking there, with no transition lag or snap to the old target.
4. On release, compute the existing nearest-slot target from the latest drag position. Start settling from the displayed position; ensure `setDragging(false)` cannot first reset that position.
5. Use the existing engine’s documented interruptible spring support if available: critically damped, no decorative bounce, starting response target 0.4s, carrying measured release velocity in verified API units. Response is not a fixed completion deadline.
6. If that capability is unavailable, stop for an explicit implementation decision; do not invent spring options for `animateTo`, add a dependency, or assume shortening the tween solves interruption.
7. Handle pointer cancellation, lost capture, unmount, and superseded completion callbacks. Preserve existing commit/cancel semantics and keyboard reorder behavior.

**Hard boundaries:** no changed sort destinations, flick projection, new reorder gestures, rubber-banding, decorative sibling stagger, or business-state commits tied to animation completion. Do not replace the custom-property channel merely on an assumed performance problem.

**Mechanical checks:** test coordinate conversion and grab offset; latest-position release; re-grab mid-settle; stale completion cancellation; cleanup; existing keyboard reorder. Confirm duration/velocity units against the real API and run declared typecheck/lint/tests.

**Runtime/feel checks:** drag slowly and quickly, reverse direction, release near slot boundaries, re-grab during settling, scroll while dragging, and cancel outside the queue. Confirm no handoff jump or input lock. Check actual supported pointer devices; do not infer smoothness from source.

**Reduced Motion:** retain direct, user-controlled tracking; skip autonomous spring travel and place the item at its committed slot immediately. Preserve visible focus, destination/selection indication, and existing reorder announcements. Preference changes during settling must cancel and resolve deterministically.

**Source-drift stop:** stop if the excerpt differs materially, coordinates or animation ownership remain unresolved, or the engine cannot support the specified interruption contract. This plan is gated—not a drop-in API patch.

## 4. Execution order and unverified states

1. **Plan 1:** highest likely interaction frequency and smallest motion change.
2. **Plan 2:** reuse existing tokens; verify positioning ownership before transform edits.
3. **Plan 3:** resolve the gesture/animation contract first, then implement and validate.

**Explicitly unverified:** actual usage frequency; animation/keyframe resolution; effective cascade and Reduced Motion coverage; palette visibility/focus semantics; popover anchoring; toast positioning/stacking; drag coordinates, units, capture, cancellation, and velocity support; browser compatibility; rendering cost; accessibility-tree behavior; and perceived feel. No browser, device, trace, or user validation was performed.
