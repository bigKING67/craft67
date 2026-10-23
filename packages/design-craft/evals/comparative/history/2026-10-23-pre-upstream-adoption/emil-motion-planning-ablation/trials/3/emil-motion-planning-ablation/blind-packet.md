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

**Diagnosis:** The supplied motion configuration diverges from the console’s crisp, token-driven convention; prioritize keyboard throughput, explicit animation ownership, and feedback-preserving Reduced Motion before adding effects.

- **Stack signals:** React-style TSX, CSS transitions/keyframes, an arbitrary animation utility class, and imperative pointer handlers. The utility compiler and `animateTo` implementation are unknown.
- **Motion locations:** shared tokens/popover rules in `src/styles/motion.css`; palette animation in `src/components/CommandPalette.tsx`; toast keyframes in `src/components/toast.css`; drag/release logic in `src/components/SortableQueue.tsx`.
- **Existing conventions:** `--duration-fast: 160ms`, `--duration-panel: 240ms`, and `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)`—a strong ease-out-like response. `src/components/Button.css` demonstrates explicit property ownership, token reuse, and an 80ms Reduced Motion override; leave it unchanged.
- **Personality:** calm, precise, workday utility. Motion should explain state changes, not become a prerequisite for interaction.
- **Frequency map:** palette and buttons are likely high-frequency keyboard/command surfaces; popovers and toasts recur during operations; queue dragging is continuous while active. Actual usage rates are unknown.
- **Evidence level:** supplied static excerpts only. `DESIGN.md` authority is supplied as a requirement, not independently inspected. No commit identifier, full component lifecycle, runtime behavior, or validation results are available.

## 2. Vetted priorities

Priorities indicate implementation attention, not confirmed runtime failures. No P0 is established.

| ID / priority | Static evidence and location | Finding / runtime unknown | Smallest safe correction and acceptance |
|---|---|---|---|
| F1 / P1 | `CommandPalette.tsx`: unconditional `animate-[palette_420ms_ease-in_both]`; `data-open={open}` | Long, slow-start configuration mismatches frequent command use. Keyframes, visibility ownership, and whether toggles replay it are unknown. | Remove decorative palette animation; make open/closed feedback immediate without delaying focus or input. Verify rapid keyboard toggles and closed-state exclusion. |
| F2 / P1 verification gate | Only `Button.css` shows a Reduced Motion branch | No preference handling is demonstrated for the other supplied motion. This does **not** prove global handling is absent. | Inspect effective preference handling before edits; supply explicit non-spatial/static feedback paths where missing. Verify normal and reduced settings. |
| F3 / P2 | `motion.css`: `transition: all 360ms ease-in`; `transform-origin: center` | Broad transition ownership and token divergence are proven. Center origin is only a concern if scaling an anchored surface. Actual changed properties are unknown. | Restrict ownership and reuse fast/responsive tokens; resolve anchoring before retaining any scale. Verify positioning remains immediate. |
| F4 / P2 | `toast.css`: animated `top`, opacity, `500ms ease-in forwards` | Layout-property animation and timing divergence are proven; layout cost depends on positioning and runtime. Dropped frames are not established. | Replace `top` animation with owned translation/opacity and fast/responsive tokens. Verify stacking, dismissal, and final position. |
| F5 / P1 investigation gate | `SortableQueue.tsx`: raw `event.clientY`; `nearestSlot(currentY)`; `duration: 400` | Coordinate conversion, freshness of `currentY`, capture, cancellation, and presentation-value interruption are not shown. No jump or stale target is proven. | Establish a single position owner and interruptible release while preserving nearest-slot semantics. Verify off-center grabs, re-grabs, and cancellation. |

**Vetted out:** no claim that `transition: all` necessarily causes layout; no claim that transforms guarantee compositing; no confirmed missing pointer capture; no automatic mandate for a spring library, momentum targeting, or centered-origin replacement.

## 3. Implementation plans

Each plan is proposed, independently scoped, and based only on the supplied excerpts. Before implementation, inspect current full files, applicable instructions, `DESIGN.md`, token imports, and existing test/build scripts. No edits or checks have been performed here.

### Plan A — Immediate command access and bounded popover feedback
**Covers:** F1, F3, and the overlay portion of F2.

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
    <div
      data-open={open}
      className="animate-[palette_420ms_ease-in_both]"
    >
      <SearchResults />
    </div>
  );
}
```
**Target/conventions:** palette state changes immediately, with no travel, scale, stagger, or animation-gated input. Popovers use opacity-only feedback over `var(--duration-fast)` with `var(--ease-responsive)`; positioning changes remain immediate. Preserve semantic tokens and visible focus.

**Ordered steps**
1. Locate palette keyframes, `data-open` selectors, mounting rules, focus management, and popover open/closed selectors. Determine whether `.popover` also applies to the palette; palette must not inherit a new fade.
2. Remove the palette’s arbitrary animation class. Retain its state attribute and existing proven visibility/focus contract; if that contract is absent, stop for a functional accessibility scope decision.
3. Replace the popover transition with `transition: opacity var(--duration-fast) var(--ease-responsive)`. Preserve positioning transforms, but remove decorative state scale/travel only after identifying their owner.
4. Do not add an origin variable or guess trigger geometry. With opacity-only motion, origin is irrelevant; preserve static positioning behavior.
5. Add a scoped Reduced Motion opacity duration of `80ms`; palette remains immediate. Ensure closed content cannot receive input or focus while visually disappearing.

**Hard boundaries:** only the two named files and directly identified existing overlay state rules; stop for approval if another owner requires edits. No token-value changes, primitive migration, new dependency, result-row animation, or button changes.

**Mechanical checks:** run actual project type/lint/build scripts; inspect generated CSS for removal of the palette utility and broad popover transition; test open/closed rendering, Escape, focus restoration, and immediate result selection. No timer or `animationend` may gate commands.

**Runtime/feel checks:** repeatedly open/type/select/close and reverse popover toggles before completion. Check first-frame feedback, visible focus, no hidden focus targets, anchor positioning, and no animation restart on result updates; repeat with Reduced Motion.

**Source-drift stop:** stop if the cited class, token values, state contract, or `.popover` ownership differs materially, or if `DESIGN.md` requires a conflicting overlay treatment.

### Plan B — Tokenized toast entry without animated layout offsets
**Covers:** F4 and the toast portion of F2.

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
**Target/conventions:** one restrained entry per toast, using the existing fast/responsive tokens. Preserve the final static position, readable feedback, dismissal, and notification semantics.

**Ordered steps**
1. Inspect positioning, transform ownership, stack layout, and removal lifecycle. Confirm what `top: 0` currently establishes; migrate that final position into static styling if needed.
2. Replace entry offsets with `transform: translateY(-8px)` to `translateY(0)`, retaining opacity `0` to `1`; use `var(--duration-fast)` and `var(--ease-responsive)`.
3. Use static final styles and remove unnecessary persistent `forwards` ownership. Keep the existing keyframe mechanism only for a verified one-shot mount entry; do not introduce an exit/presence system.
4. If transforms already own stack positioning or swipe dismissal, stop before overwriting them and resolve composition with that owner.
5. Add a Reduced Motion override with `animation: none`; show the toast immediately at its final position and opacity. Preserve content, status styling, announcements, and actions.

**Hard boundaries:** `src/components/toast.css` only. No notification timer, announcement, stacking-order, or dismissal behavior changes; no `will-change`, new dependencies, or global token edits.

**Mechanical checks:** run actual style/build checks; assert the keyframes no longer animate `top`; verify token resolution, static final opacity, and reduced-mode animation removal. Check that no dismissal logic relies on this entry’s animation completion.

**Runtime/feel checks:** inspect single and stacked entries, rapid arrivals, updates to an existing toast, action activation, and dismissal during entry. Check for transform conflicts, displaced final positions, replay, and clipping. Capture a trace before making performance claims.

**Source-drift stop:** stop if keyframes are shared, existing transform ownership is discovered, lifecycle depends on entry completion, or the current positioning contract differs from the excerpt’s assumed final state.

### Plan C — Establish drag ownership before tuning release
**Covers:** F5 and the queue portion of F2.

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
**Target/conventions:** direct 1:1 tracking, preserved grab offset, no input lock during settling, and re-grab from the displayed position. Keep `nearestSlot(currentY)` target semantics. Use existing animation infrastructure, restrained non-bouncy motion, and semantic timing where a duration-based API is appropriate.

**Ordered steps**
1. Inspect pointer-down/cancel handlers, `--drag-y` consumers, coordinate spaces, `currentY` ownership, and the complete `animateTo` API. Confirm whether duration is milliseconds and whether it supports cancellation, presentation reads, and velocity.
2. Define one canonical drag position in queue-local CSS pixels. Convert viewport `clientY` using queue geometry, grab offset, and relevant scrolling; update that value and the visual write together. Handle the final pointer-up position.
3. Verify or add active-pointer capture, secondary-pointer exclusion, cancellation cleanup, and unmount cleanup. Keep React state changes at lifecycle boundaries rather than on every pointer move.
4. On re-grab, read the displayed position before cancelling the settle; establish the new grab offset from that position. Release to the existing nearest valid slot, not the previous animation target.
5. Sample position with monotonic timestamps; express release velocity in CSS px/s. Hand it to an existing capable settle primitive in its documented units, bounded to avoid overshoot outside valid slots. Do not invent unsupported `animateTo` options.
6. If only a duration-based retargetable primitive is supported, use the resolved `--duration-panel` value rather than hard-coded `400`; stop for an API decision if required interruption/velocity support is unavailable. Never pass a CSS `var()` string to a numeric API.
7. Reduced Motion keeps user-controlled tracking but commits release directly to the chosen slot, without autonomous travel or bounce. Preserve focus, selected/drop-state feedback, and existing reorder announcements.

**Hard boundaries:** `src/components/SortableQueue.tsx`; inspect but do not silently modify helper/CSS owners. No dependency installation, spring migration, changed reorder semantics, new drag threshold, or keyboard reordering redesign.

**Deferred targeting decision:** a momentum experiment could compute `clamp(position + velocity * 0.12s, minSlot, maxSlot)` using CSS pixels and CSS px/s. This is an unvalidated candidate, not implementation scope; using its nearest slot requires explicit authorization. Velocity handoff does not require changing target selection.

**Mechanical checks:** run actual type/lint/test scripts; test coordinate conversion, final-event freshness, capture cleanup, nearest-slot boundaries, animation cancellation, preference changes, and unmount. Assert no obsolete completion callback commits a superseded target.

**Runtime/feel checks:** grab near either edge, leave queue bounds, scroll during drag, reverse direction, release near slot boundaries, and immediately re-grab mid-settle. Check focus and any existing keyboard reorder path; repeat under Reduced Motion and representative data load.

**Source-drift stop:** stop if `--drag-y` is not a local translation input, `currentY` has different semantics, `animateTo` cannot satisfy the required lifecycle, or target selection/authority differs materially.

## 4. Recommended execution order and unverified states

1. **Resolve drag/API and effective Reduced Motion ownership first**—these are scope gates, not permission for speculative rewrites.
2. **Implement Plan A**, then **Plan B**: bounded changes with strong token and throughput benefits.
3. **Implement Plan C after its API gate clears.** Prioritize it earlier if later testing establishes task-breaking drag behavior.
4. Validate each plan separately; revert its scoped change if focus, input, dismissal, positioning, or reorder semantics regress.

**Explicitly unverified:** full stylesheet cascade and generated utilities; mounting/unmounting and exit behavior; palette focus/keyboard semantics; popover anchoring; toast stacking/announcement timing; drag capture, scrolling, velocity and cancellation; preference changes while active; actual usage frequency; computed durations; frame pacing, performance, and subjective feel. No browser, device, accessibility-tree, trace, recording, or user validation is claimed.


## Output B

## 1. Recon summary

- **Stack signals:** React-style TSX with TypeScript, CSS transitions/keyframes, and an arbitrary animation utility resembling Tailwind syntax. The utility framework and `animateTo` implementation are not established.
- **Motion locations:** shared declarations in `src/styles/motion.css`; component animation in `CommandPalette.tsx` and `toast.css`; pointer-driven motion in `SortableQueue.tsx`.
- **Existing conventions:** `--duration-fast: 160ms`, `--duration-panel: 240ms`, and `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)`. `src/components/Button.css` correctly demonstrates an explicit property, semantic tokens, subtle press feedback, and an 80ms Reduced Motion override. Leave it unchanged.
- **Authority/personality:** `DESIGN.md` requires crisp motion, semantic tokens, visible focus, and preserved feedback under Reduced Motion. Favor immediate keyboard response and restrained state continuity, not decorative entrances.
- **Frequency map — inferred, not measured:** palette and buttons likely high-frequency; popovers recurrent; toast frequency depends on events; sorting frequency is unknown, but pointer updates are continuous during use.
- **Evidence level:** snippet-only static review. Timing declarations are confirmed; perceived delay, layout cost, focus behavior, animation replay, and interruption defects are not observed. No files were modified.

## 2. Vetted priorities

Priority reflects expected leverage, not measured severity.

| Priority | Location | Confirmed evidence and bounded concern | Recommended action |
|---|---|---|---|
| P1 | `src/components/CommandPalette.tsx` | Unconditional class requests `420ms ease-in`; `open` only sets an attribute in the excerpt. Keyframes and visibility rules are unavailable. Decorative entry is a poor default for this keyboard-heavy surface. | Remove the animation utility; keep opening, closing, and focus immediate. |
| P1 | `src/styles/motion.css` | `.popover` uses `transition: all 360ms ease-in`, bypassing existing tokens and allowing unintended properties to transition. | Explicit opacity/transform transitions using 160ms and the responsive token. |
| P1 | `src/components/toast.css` | Entrance animates `top` for 500ms with `ease-in`. `top` is layout-affecting when applicable; actual positioning and cost are unknown. | Keep layout position static; use a short transform/opacity entrance. |
| P1 verification gate | Palette, popover, toast, queue | No Reduced Motion handling appears in these excerpts. This does **not** establish its absence elsewhere. | Check effective coverage; ensure the planned behavior preserves feedback without autonomous travel. |
| P2 | `src/components/SortableQueue.tsx` | Release requests a fixed 400ms animation. Coordinate conversion, current-position synchronization, cancellation, and velocity handling are not shown. | Establish these contracts before changing the release controller; make re-grabbing immediate. |

**Not promoted to findings:** centered popover origin is only suspect if this is a trigger-anchored scaling surface; the CSS-variable write alone does not prove descendant invalidation or frame loss. No additive animation is justified by the supplied evidence.

## 3. Implementation plans

All checks below are instructions for future execution, **not completed validation**. File/package scripts and test locations are unavailable; use the project’s declared checks rather than inventing commands.

### Plan 1 — Make the command palette immediate

**Scope/current excerpt — `src/components/CommandPalette.tsx`:**
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

**Target:** no palette entrance/exit animation, no result stagger, no animation-dependent input or focus delay. Opening and closing retain their existing state semantics.

**Conventions:** follow `DESIGN.md` on crisp feedback and visible focus. Tokens in `src/styles/motion.css` are 160ms/240ms and `cubic-bezier(0.23, 1, 0.32, 1)`; this high-frequency action needs neither duration. Preserve `src/components/Button.css` unchanged.

**Ordered steps**
1. Inspect the full component and the rules consuming `data-open`; determine whether the utility/keyframes also supply visibility or final-state styles.
2. Remove `className="animate-[palette_420ms_ease-in_both]"`. Preserve `data-open`, children, and the existing mount/visibility mechanism.
3. If keyframes supply essential final styles, move those styles into the existing state rules before removing the utility. Do not substitute an opacity-hidden but focusable closed state.
4. Verify focus entry and return are independent of animation completion; remove a motion-only wait only if one is actually found and its scope is understood.
5. Add or extend existing tests for open, close, immediate typing, repeated toggles, and closed-state focus exclusion.

**Hard boundaries:** no search, shortcut, result-order, dialog-semantics, or focus-ring redesign; no dependency additions; no global keyframe deletion without a usage check.

**Mechanical checks:** removed utility absent from this component; no replacement animation; existing typecheck/lint/tests pass. Tests should assert immediate interactivity without waiting 420ms.

**Runtime/feel checks:** open by keyboard, immediately type and navigate, dismiss with Escape, and repeat rapidly. Confirm correct focus entry/return and no flash or inaccessible closed content.

**Reduced Motion:** same immediate behavior; visible results, selection, and focus provide feedback without movement.

**Source-drift stop:** stop if the class or state contract differs, or visibility/focus depends on unavailable animation code. Resolve that dependency before editing; do not invent a new dialog lifecycle.

### Plan 2 — Normalize lightweight overlay entrances

**Scope/current excerpts — `src/styles/motion.css`:**
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

**`src/components/toast.css`:**
```css
@keyframes toast-enter {
  from { top: -24px; opacity: 0; }
  to { top: 0; opacity: 1; }
}
.toast {
  animation: toast-enter 500ms ease-in forwards;
}
```

**Target:** popovers respond over 160ms with explicitly scoped properties; toasts enter over 160ms from `translateY(-8px)` and opacity 0. Preserve placement, readability, and interaction throughout.

**Conventions:** use the existing `--duration-fast` and `--ease-responsive`, not new aliases or duplicate curves. `src/components/Button.css` demonstrates `transition: transform var(--duration-fast) var(--ease-responsive)` and the established 80ms Reduced Motion value.

**Ordered steps**
1. Inspect placement/state selectors, transform ownership, toast positioning, and any global Reduced Motion rules before changing either block.
2. Replace the popover transition with:
   ```css
   transition:
     transform var(--duration-fast) var(--ease-responsive),
     opacity var(--duration-fast) var(--ease-responsive);
   ```
3. Preserve existing open/closed endpoints. If scaling is trigger-anchored and placement metadata exists, use that system’s actual origin value; otherwise retain `center` pending evidence. Do not introduce a guessed library variable.
4. Replace toast keyframe endpoints with `transform: translateY(-8px); opacity: 0` and `transform: translateY(0); opacity: 1`. Replace its animation shorthand with `toast-enter var(--duration-fast) var(--ease-responsive) both`.
5. Keep the toast’s resting layout unchanged. If the original animation supplied essential `top: 0`, establish it statically on the appropriate positioned element. Do not overwrite a placement/stacking transform.
6. Add component-scoped Reduced Motion overrides: toast uses an opacity-only keyframe from 0 to 1 over 80ms; popover transitions only opacity over 80ms and has no decorative scale/slide difference between states.
7. Add tests for final resting styles and state changes. Retain one-shot toast keyframes unless an actual reversible lifecycle requires a separately scoped transition conversion.

**Hard boundaries:** no positioning-system rewrite, global token changes, new dependencies, toast lifetime changes, exit-delay invention, or button changes. Do not remove essential positioning transforms for Reduced Motion.

**Mechanical checks:** `.popover` no longer uses `all`; toast keyframes no longer animate `top`; both use existing timing/easing tokens; Reduced Motion rules resolve to opacity-only animation. Existing lint/build/tests pass.

**Runtime/feel checks:** open/close popovers rapidly and reverse mid-transition; inspect attachment at each supported placement. Trigger single and stacked toasts, including dismissal during entry. At normal and slowed playback, check for placement shifts, transform conflicts, text flashes, and delayed input. Profile only if performance remains a concern.

**Reduced Motion:** preserve opacity feedback at 80ms, readable content, focus, and announcements; remove decorative translation/scale rather than hiding the entire component.

**Source-drift stop:** stop if placement shares the animated transform, state selectors are unavailable, keyframe consumers differ, or toast final positioning is unclear. Identify the real motion-owning element before applying the replacement.

### Plan 3 — Make queue release interruptible without changing sorting policy

**Scope/current excerpt — `src/components/SortableQueue.tsx`:**
```tsx
function onPointerMove(event: PointerEvent) {
  queueRef.current?.style.setProperty("--drag-y", `${event.clientY}px`);
}

function onPointerUp() {
  setDragging(false);
  animateTo(nearestSlot(currentY), { duration: 400 });
}
```

**Target:** preserve the grab offset and direct pointer tracking; settle from the current displayed position; re-grabbing cancels settling immediately. Keep `nearestSlot(currentY)` as the destination policy—no velocity-projected slot changes.

**Conventions:** respect `DESIGN.md` on crisp response, visible focus, and Reduced Motion. Shared durations are 160ms/240ms; easing is `cubic-bezier(0.23, 1, 0.32, 1)`. Prefer an existing controller over another animation dependency.

**Ordered steps**
1. Trace `animateTo`, `currentY`, `--drag-y`, the actual dragged element, pointer capture, scrolling, and commit timing. Establish coordinate space, duration units, cancellation API, and transform ownership.
2. Ensure pointer-down records the pointer-to-item offset and the displayed position. While dragging, update the existing motion owner directly from pointer displacement in that same coordinate space; do not add smoothing or a CSS transition to pointer tracking.
3. Keep current position synchronized with the rendered drag position before calling `nearestSlot`. Preserve existing sorting and persistence semantics.
4. Cancel any active settle on re-grab, cancellation, or unmount. Start subsequent motion from the displayed value, never the previous target.
5. Replace the fixed 400ms settle with the existing controller’s supported interruptible transition: target 160ms using the shared responsive curve. Resolve tokens through the existing project bridge; do not assume the helper accepts CSS strings or a particular option name.
6. If the controller cannot sample/cancel/retarget, stop and specify its required extension before implementation. Do not silently swap libraries or build an unreviewed spring engine.
7. Read and subscribe to `prefers-reduced-motion` using the project’s existing mechanism; cancel settling and apply the destination immediately when reduction is active.

**Hard boundaries:** no reorder-algorithm changes, momentum projection, bounce, new drag thresholds, persistence changes, or accessibility redesign. Preserve existing keyboard reorder and announcement paths; do not claim they exist from this excerpt.

**Mechanical checks:** test coordinate conversion with a nonzero grab offset and scrolling; latest-position slot selection; cancellation before restart; cleanup on unmount; immediate Reduced Motion settlement. Verify 400ms is removed only from this release path and existing typecheck/lint/tests pass.

**Runtime/feel checks:** drag slowly, release between slots, re-grab mid-settle, reverse direction, scroll, and cancel. Confirm no initial jump, input lockout, stale completion, or disagreement between visual and committed order. Inspect normal and slowed playback on a desktop pointer setup.

**Reduced Motion:** retain user-controlled tracking; eliminate autonomous settling travel. Final order, focus/selection, and existing status feedback remain available immediately.

**Source-drift stop:** stop if helper capabilities, units, motion ownership, or coordinate contracts cannot be established, or cancellation affects persistence. Those are implementation prerequisites, not proven defects.

## 4. Execution order and unverified states

1. **Plan 1:** highest expected leverage for keyboard throughput; smallest intended scope.
2. **Plan 2:** align overlays with existing tokens and remove the confirmed layout-property animation.
3. **Plan 3:** execute after its controller/coordinate inspection gate; uncertainty is higher.

**Explicitly unverified:** actual usage frequency; utility/keyframe generation; effective styles and global Reduced Motion coverage; mount/exit lifecycles; focus and accessibility-tree behavior; popover anchoring; toast stacking/announcements; drag coordinates, cancellation, and keyboard sorting; rendering performance; browser compatibility; device feel. No browser, device, trace, recording, or user validation was performed.


## Output C

## 1. Recon summary

- **Stack signals:** TSX components suggest React; styling combines CSS custom properties, CSS keyframes, an arbitrary-value animation class, and an imperative `animateTo` call. The utility compiler and animation library are not established.
- **Motion locations:** shared styling in `src/styles/motion.css`; palette motion in TSX; toast motion in component CSS; queue movement in pointer handlers.
- **Existing conventions:** `--duration-fast: 160ms`, `--duration-panel: 240ms`, and `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)`. The button demonstrates property-scoped transitions, token reuse, and an `80ms` Reduced Motion override. `DESIGN.md` requires crisp motion, semantic tokens, visible focus, and preserved feedback.
- **Product personality:** quiet, responsive, workday-long utility. Motion should explain state changes, not make operators wait.
- **Frequency map — inferred, not measured:** palette potentially frequent for keyboard users; popovers recurrent; toasts event-driven and potentially repetitive; sorting task-dependent, with very frequent updates during a drag. Favor restraint on repeated actions.
- **Evidence level:** static snippets only. Definitions, consumers, lifecycle handling, focus behavior, and motion-preference coverage outside these excerpts remain unknown. No runtime or device findings are asserted.

## 2. Vetted priorities

Priorities reflect product relevance and visible implementation risk, not measured user impact.

| Priority | Finding | Evidence and qualification | Intended correction |
|---|---|---|---|
| P1 | Palette uses an outlying timing and unclear state linkage | `420ms ease-in` bypasses tokens; `open` only sets an attribute here. Keyframes, external selectors, and mounting behavior are unavailable. | State-linked, short motion; keyboard interaction never waits for it. |
| P1 | Popover transition is broad and inconsistent | `all 360ms ease-in` includes every changing animatable property; actual changed properties are unknown. Center origin may not match placement. | Explicit properties, shared timing, placement-aware origin only if scaling is retained. |
| P1 | Reduced Motion coverage is not shown for the audited surfaces | Only the button excerpt includes an override. This is a coverage gap in evidence, not proof of app-wide absence. | Verify and explicitly support each CSS and imperative path. |
| P2 | Toast entrance animates `top` with long, accelerating timing | `500ms ease-in`; positional animation can require layout work when `top` applies. No performance cost was measured. | Short opacity/transform entrance, without changing toast layout or delivery semantics. |
| P2 | Queue release uses a fixed `400ms` and has unresolved interruption behavior | Pointer movement writes viewport Y; its consumer and `currentY` synchronization are not shown. Cancellation and keyboard paths are also unknown. | Preserve direct manipulation; short, interruptible settling using the correct coordinate model. |

## 3. Implementation plans

### Plan A — Align shared and overlay motion

**Exact files/current excerpts**

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
- Keep existing token values. Use fast timing for compact popovers and panel timing for the palette, with the existing responsive easing.
- Favor opacity plus a small, bounded translation; avoid large travel and decorative scaling.
- Motion follows actual open/close changes, not search-result rerenders. Input readiness and focus must not depend on animation completion.

**Ordered steps**
1. Inspect complete files, palette keyframes, popover state/placement selectors, utility generation, and existing visibility/focus lifecycle before editing.
2. Replace `transition: all` with only properties that the established states change: preferably `opacity, transform`.
3. Remove the palette’s hardcoded animation utility; connect token-based styles to its established state mechanism. Use `data-open` only if it is the canonical state hook.
4. Preserve mount/unmount semantics. If close motion requires presence infrastructure not already available, make closing immediate rather than adding a lifecycle system.
5. Add scoped Reduced Motion overrides; verify that invisible closed content cannot remain keyboard-interactive.

**Hard boundaries**
- No token renaming, global timing retuning, search changes, new animation dependency, or generic focus-system rewrite.
- Do not overwrite transforms used by positioning. Compose through the existing mechanism or use opacity only.
- Do not introduce animation delays or defer focus until motion finishes.

**Mechanical checks**
- Confirm the old palette timing and broad popover transition are removed from these targets.
- Check stylesheet inclusion, generated utility output where applicable, selector precedence, type checks, and available tests.
- Add lifecycle tests for rapid toggles, result updates without entrance replay, and correct closed-state focusability.

**Runtime/feel checks — to perform**
- Repeated keyboard opening, typing immediately, Escape, focus return, and rapid reopening.
- Check anchor continuity and placement changes; verify no flash, positional jump, or blocked input.

**Reduced Motion**
- Remove translation/scaling; retain at most an `80ms` opacity change, consistent with the local timing precedent.
- Preserve focus indicators and immediate state changes. Override animations as well as transitions where both exist.

**Source-drift stop condition**
- Stop and revise scope if the full files differ materially, placement owns the same transform, or an existing overlay/presence primitive already controls these behaviors. Do not layer competing motion onto it.

### Plan B — Make toast arrival brief and layout-independent

**Exact file/current excerpt**

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
- A toast appears at its final layout position with a subtle upward-origin arrival: proposed `translateY(-8px)` to `translateY(0)` plus opacity.
- Use `--duration-fast` and `--ease-responsive`; arrival should acknowledge an event without drawing prolonged attention.

**Ordered steps**
1. Inspect base positioning, stack layout, transform ownership, exit rules, and timer semantics.
2. Ensure the nonanimated rule expresses the intended final position; removing the keyframe’s `top: 0` must not relocate the toast.
3. Replace animated `top` with transform/opacity, using existing transform composition if needed. If composition is unavailable, use opacity only.
4. Apply shared tokens. Prefer a stable base state and backwards fill for entrance rather than retaining an unnecessary forwards-filled animation.
5. Add a scoped Reduced Motion keyframe/override and regression coverage for repeated arrivals.

**Hard boundaries**
- Do not change dismissal duration, announcement behavior, message priority, stack ordering, or actionable-toast focus.
- Do not add `will-change`, stack-reflow choreography, or exit animation without separate evidence of need.

**Mechanical checks**
- Verify `toast-enter` no longer animates `top`, and shared tokens are in scope.
- Confirm the final position and opacity remain correct after animation ends; verify Reduced Motion wins in the cascade.
- Run available style/build checks and toast lifecycle tests.

**Runtime/feel checks — to perform**
- Check one toast, bursts, multiline content, actionable content, and dismissal during entrance.
- Inspect for clipping, stack displacement, transform conflicts, and excessive repeated movement. Profile only if a performance claim is needed.

**Reduced Motion**
- Use opacity-only entrance of at most `80ms`; preserve the message, announcement, action availability, and full dismissal policy.

**Source-drift stop condition**
- Stop if `top` participates in stack placement, another layer owns transforms, or a toast primitive supplies its own motion. Reconcile ownership before replacing keyframes.

### Plan C — Keep queue dragging direct; shorten release settling

**Exact file/current excerpt**

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
- Preserve immediate pointer tracking; do not add easing to each pointer update.
- Settle to the valid slot using the existing fast token and responsive easing, provided the animation API supports them.
- Re-grab or cancellation interrupts settling without a jump. Logical order and keyboard feedback do not wait for a visual animation.

**Ordered steps**
1. Trace `--drag-y`, `currentY`, `nearestSlot`, pointer capture, scroll offsets, and `animateTo` implementation. Establish coordinate space, units, cancellation, and commit timing.
2. Verify release uses the latest pointer position. Correct synchronization only if the complete implementation shows a mismatch.
3. Replace `400` through the existing token-to-JavaScript bridge. If none exists, add a narrow conversion at the component boundary after confirming API units; do not duplicate a new timing scale.
4. Cancel an active settle before a new drag; continue from its current visual position using the library’s supported mechanism.
5. Preserve or verify pointer-cancel cleanup and keyboard reorder behavior. Keep any broader accessibility redesign separately scoped.

**Hard boundaries**
- No new sorting algorithm, speculative throttling, spring/bounce behavior, or animation library migration.
- Do not substitute viewport coordinates for local offsets without mapping them.
- Do not clear drag styles before capturing the visual start position if doing so would break continuity.

**Mechanical checks**
- Test latest-position release, target selection, cancellation, re-grab, unmount cleanup, and token/API unit conversion.
- Verify preference changes reach the imperative path and no stale animation completion callback overwrites newer order.

**Runtime/feel checks — to perform**
- Fast and slow drags, release near boundaries, scrolled containers, immediate re-grab, pointer cancellation, and keyboard reorder.
- Check pointer attachment, release continuity, correct final order, visible focus, and absence of an input lock during settling.

**Reduced Motion**
- Retain pointer-attached movement needed for direct manipulation; snap to the final slot without release travel.
- Preserve destination/order feedback and existing keyboard announcements. Do not rely on a CSS media query alone for imperative animation.

**Source-drift stop condition**
- Stop if the API uses different duration units, the drag system already owns cancellation/token mapping, or coordinate/state ownership differs from the excerpt. Resolve that contract before implementation.

## 4. Execution order and unverified states

1. **Plan A:** establish consistent overlay timing and preference handling without altering token values.
2. **Plan B:** deliver the small, isolated toast correction.
3. **Plan C:** implement after coordinate, state, and animation API contracts are understood.

**Explicitly unverified:** actual animation playback, palette keyframes, hidden-state semantics, focus management, token availability, transform ownership, toast positioning/announcements, drag correctness, keyboard sorting, cancellation, global Reduced Motion coverage, performance, and perceived feel. All runtime checks above are proposed acceptance checks—not completed validation.
