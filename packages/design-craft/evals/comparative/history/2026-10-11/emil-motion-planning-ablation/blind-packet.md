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

**Diagnosis:** The excerpts mix a crisp, token-based button precedent with longer, slow-starting overlay/toast motion and an incompletely evidenced drag-settle contract. Prioritize predictable state changes over decorative movement.

- **Stack signals:** React-style TSX, CSS transitions/keyframes, an arbitrary-value utility class, and an unidentified JavaScript `animateTo` API. A particular utility framework or animation library is not established.
- **Motion locations:** shared tokens/popovers in `src/styles/motion.css`; palette motion in `src/components/CommandPalette.tsx`; toast keyframes in `src/components/toast.css`; pointer tracking/settling in `src/components/SortableQueue.tsx`.
- **Conventions:** `--duration-fast: 160ms`, `--duration-panel: 240ms`, and `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)`—a strong ease-out-like response. `src/components/Button.css` demonstrates explicit property ownership, token reuse, and an 80ms Reduced Motion override. Preserve this correct local precedent.
- **Personality:** calm desktop utility; immediate keyboard response, restrained movement, visible focus, and continuity without interaction lockout.
- **Frequency map, inferred rather than measured:** palette and buttons are potentially high-frequency; popovers repeated; toasts event-driven; queue dragging task-dependent, with pointer updates constituting a hot path during use.
- **Evidence:** supplied static excerpts only; no commit identifier, complete lifecycle code, computed styles, runtime observations, or measured usage. No files were edited or plans written to disk.

## 2. Vetted priorities

Priorities are roadmap rankings, not observed release failures. No P0 is supported.

| ID / priority | Static proof | Risk and runtime unknown | Smallest correction / acceptance evidence |
|---|---|---|---|
| F1 / P1 | `CommandPalette.tsx`: unconditional `animate-[palette_420ms_ease-in_both]`; `open` only appears as `data-open` in the excerpt. | Slow-starting configuration conflicts with frequent keyboard use. Keyframes, mounting, hidden-state behavior, and actual delay are unknown. | Remove decorative entry animation; make visibility follow `open` immediately. Verify focus, Escape, typing, and repeated toggles without animation-dependent work. |
| F2 / P2 | `motion.css`: `.popover` uses `transition: all 360ms ease-in` and centered origin. | Broad property ownership and timing inconsistency; center is questionable **if anchored and scaled**. No layout cost or anchoring is proved. | Explicit properties, existing fast/responsive tokens, and trigger-relative origin only where applicable. Verify placement and rapid reversal. |
| F3 / P2 | `toast.css`: `top: -24px → 0`, opacity fade, `500ms ease-in forwards`. | Layout-property animation risk if `top` participates in positioning; no dropped frames established. Replay/stack behavior unknown. | Transition opacity and a small transform using existing tokens; retain static layout position. Verify burst arrival, dismissal, and stacking. |
| F4 / P2 | `SortableQueue.tsx`: viewport `clientY` written to `--drag-y`; release uses `nearestSlot(currentY)` and `{ duration: 400 }`. | Coordinate conversion, freshness of `currentY`, capture, cancellation, and interruption are not shown—not proven absent. | Audit ownership first; ensure presentation-value continuity and token-aligned settling while preserving nearest-slot semantics. Verify grab, release, cancellation, and re-grab. |
| F5 / P2 | Only the button excerpt shows a Reduced Motion branch. | Coverage for the other four surfaces is unproven; global overrides may exist. Shorter duration alone does not define spatial reduction. | Establish per-surface behavior in the plans below; inspect CSS and JS paths and verify preference changes with feedback retained. |

## 3. Implementation plans

### Plan A — Immediate command access and restrained popovers
**Covers:** F1, F2, F5. **Baseline:** supplied excerpts; commit unknown.

**Exact files/current excerpts**
- `src/styles/motion.css`: `--duration-fast: 160ms;`, `--duration-panel: 240ms;`, `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1);`
- Same file: `.popover { transform-origin: center; transition: all 360ms ease-in; }`
- `src/components/CommandPalette.tsx`: `<div data-open={open} className="animate-[palette_420ms_ease-in_both]">`
- Read-only precedent, `src/components/Button.css`: `transition: transform var(--duration-fast) var(--ease-responsive);`, active `scale(0.98)`, Reduced Motion `transition-duration: 80ms`.

**Target and conventions**
- Palette opens/closes immediately with no travel or fade; search and focus are never deferred for motion.
- Popovers use `opacity var(--duration-fast) var(--ease-responsive)`; add an explicit transform transition only if an existing spatial state requires it. Do not introduce new scale/travel.
- Follow the supplied `DESIGN.md` requirements; retain tokens and visible focus.

**Ordered steps**
1. Inspect palette keyframes, open/closed selectors, mount ownership, focus management, and popover positioning/state selectors before editing.
2. Remove the palette animation utility. Preserve the existing semantic open/close contract; ensure closed content is neither focusable nor exposed as active content.
3. Replace popover `transition: all` with the explicit property list above. Keep positioning transforms separate from animated transforms.
4. For an anchored, scaled popover, use the positioning system’s verified trigger-relative origin. Keep `center` for genuinely centered surfaces; do not fabricate a positioning variable.
5. Preserve existing focus entry/restoration and Escape handling; remove animation-completion dependencies from those actions if present.
6. Add scoped Reduced Motion treatment: palette stays instantaneous; popover removes decorative transform motion and uses opacity-only feedback over 80ms, matching the local reduced-duration precedent.

**Hard boundaries**
- No dependency adoption, positioning migration, global token changes, button edits, new stagger, or content redesign.
- If visibility/focus ownership cannot be corrected in these files, stop and explicitly expand scope rather than inventing selectors or rewriting a primitive.

**Mechanical checks**
- Confirm the palette utility and popover `transition: all` are gone; no positioning transform is overwritten by the reduced-motion rule.
- Run the existing targeted type/lint/component tests using verified project commands; add tests for closed-state focus exclusion and immediate open/close. Scripts are not available in this evidence.

**Runtime/feel checks — future acceptance**
- Rapid shortcut toggles, immediate typing, Escape, focus restoration, and visible focus at entry.
- Popovers near each viewport edge, interrupted entry/exit, pointer-to-keyboard switching, and Reduced Motion enabled before opening and during transition.
- Accept only if no task waits for motion and closing/reopening cannot leave stale hidden or interactive states.

**Source-drift stop**
- Stop before edits if the cited class/rule/tokens differ materially, the palette already has a different lifecycle owner, or positioning/state contracts contradict the assumed edit boundary.

### Plan B — Toast feedback without animated layout offsets
**Covers:** F3, F5. **Baseline:** supplied excerpts; commit unknown.

**Exact file/current excerpts**
- `src/components/toast.css`:
```css
@keyframes toast-enter {
  from { top: -24px; opacity: 0; }
  to { top: 0; opacity: 1; }
}
.toast { animation: toast-enter 500ms ease-in forwards; }
```

**Target and conventions**
- Toasts appear with opacity plus a restrained `translateY(-8px) → translateY(0)` entrance over `var(--duration-fast)` and `var(--ease-responsive)`.
- The 8px displacement is a proposed local starting value, not an existing token. Preserve semantic timing tokens, readable feedback, and current dismissal behavior.

**Ordered steps**
1. Inspect `.toast` positioning, transform ownership, stack management, entry/mount behavior, dismissal, and supported browser targets.
2. Retain the final static layout position where applicable; remove animated `top` and the forwards-filled entry keyframe.
3. Use an opacity/transform transition with the existing mounted-entry mechanism. Use `@starting-style` only if supported by the verified browser target; otherwise require an existing presence/state hook.
4. Preserve dismissal timing and announcements independently of animation completion. Do not add an exit-presence system merely for polish.
5. Add Reduced Motion: no entrance translation, opacity-only transition over 80ms; content and dismissal remain available immediately.

**Hard boundaries**
- Edit only `src/components/toast.css`; do not change toast lifetime, announcement semantics, queue order, stack algorithms, or button styles.
- No new library or persistent `will-change`. If entry state or transform composition requires component changes, stop and authorize the exact additional file first.

**Mechanical checks**
- Confirm no toast keyframe animates `top`; verify final opacity/position without fill-mode dependence.
- Run available CSS lint/build checks; inspect selector precedence and existing toast tests. Add state tests only within an approved existing test boundary.
- Verify a safe fully visible final state even when entry animation is unavailable.

**Runtime/feel checks — future acceptance**
- Single arrival, burst arrivals, long content, immediate dismissal, and arrival during dismissal; verify positioning transforms are not replaced.
- Compare ordinary and Reduced Motion paths for readable feedback and stable stacks. Use a trace before claiming any rendering-cost improvement.

**Source-drift stop**
- Stop if the quoted keyframe/rule changed, shared tokens are unavailable here, or stack positioning owns the same transform without a safe composition path.

### Plan C — Establish the queue’s direct-manipulation contract before tuning
**Covers:** F4, F5. **Baseline:** supplied excerpts; commit unknown.

**Exact file/current excerpts**
- `src/components/SortableQueue.tsx`:
```tsx
function onPointerMove(event: PointerEvent) {
  queueRef.current?.style.setProperty("--drag-y", `${event.clientY}px`);
}
function onPointerUp() {
  setDragging(false);
  animateTo(nearestSlot(currentY), { duration: 400 });
}
```

**Target and conventions**
- Track the pointer 1:1 after drag commitment, preserve grab offset, and settle from the displayed position without locking input.
- Preserve `nearestSlot(currentY)` targeting semantics. Use the project’s `--duration-panel`/`--ease-responsive` vocabulary for a fixed-duration settle, subject to verified API support and units.

**Ordered steps**
1. Trace `--drag-y` consumption, coordinate conversion, `currentY` updates, pointer-down/cancel handlers, scroll handling, and `animateTo` implementation. Determine whether `setDragging(false)` clears the displayed offset before settling.
2. Establish one transform owner; calculate local movement from the grab point in CSS pixels, accounting for container position/scroll. Maintain pointer capture and ignore unrelated pointers through completion/cancellation.
3. Sample position with monotonic timestamps to measure velocity in CSS px/s. On re-grab, cancel settling and begin from its current presentation position, not its former target.
4. Keep nearest-current-position slot selection. Audit a **non-shipping experiment** only: `projectedY = clamp(y + velocity * 0.10, minY, maxY)`; 0.10s is a provisional horizon. Do not use projection to choose a slot without separate product authorization.
5. Verify cancellation, presentation-value reads, and velocity support before modifying `animateTo`. Pass bounded measured velocity in its documented units if supported; otherwise stop for a scoped adapter decision rather than inventing options.
6. If fixed-duration settling is supported, replace 400ms with the resolved panel token and responsive easing through the existing token bridge. Keep logical commit, visual cleanup, and cancellation explicitly owned.
7. Reduced Motion retains direct pointer tracking but snaps to the selected slot immediately on release, with static selected/drop feedback and focus retained; remove autonomous settle travel and overshoot.

**Hard boundaries**
- No inertia-based targeting, bounce, library migration, keyboard-reorder redesign, or unrelated queue changes.
- Do not hard-code a second token system in JavaScript. Stop if token access or animation capability requires changes outside `src/components/SortableQueue.tsx`.

**Mechanical checks**
- Test coordinate conversion, current-position freshness, nearest-slot boundaries, capture release, cancellation, and cleanup.
- Test no stale completion callback after re-grab/unmount, plus the immediate Reduced Motion release path; run verified targeted type/lint/test commands.

**Runtime/feel checks — future acceptance**
- Grab at different offsets, drag beyond bounds, scroll during drag, release between slots, reverse direction, and re-grab mid-settle.
- Check ordinary/reduced motion and existing keyboard reorder/focus behavior; record actual presentation continuity and input availability. Measure hot-path cost before claiming smoother rendering.

**Source-drift stop**
- Stop if the handlers, `nearestSlot` rule, `currentY` meaning, transform consumer, or `animateTo` signature materially differ; unsupported presentation/velocity access is a capability gate, not permission for a speculative rewrite.

## 4. Execution order and unverified states

1. **Plan A first:** highest likely keyboard frequency and direct convention alignment.
2. **Plan B next:** bounded property/timing correction.
3. **Plan C:** begin with capability inspection; implement only after coordinate and animation ownership are established.

**Explicitly unverified:** actual motion visibility, focus/accessibility behavior, global Reduced Motion coverage, interrupted transitions, toast lifecycle/stacking, queue velocity/capture/cancellation, browser support, frame pacing, task throughput, and subjective feel. All mechanical and runtime checks above are proposed acceptance work, not completed validation.


## Output B

## 1. Recon summary

- **Stack signals:** TSX components, React-style state/ref usage, CSS custom properties, keyframes, and utility-like arbitrary animation syntax. The CSS-generation pipeline and animation library are not established.
- **Motion locations:** shared styling in `src/styles/motion.css`; component motion in `src/components/CommandPalette.tsx`, `src/components/toast.css`, and `src/components/SortableQueue.tsx`.
- **Existing conventions:** `--duration-fast: 160ms`, `--duration-panel: 240ms`, and `--ease-responsive`. `src/components/Button.css` provides a correct local precedent: explicit `transform` transitions, restrained press feedback, and an 80ms Reduced Motion path.
- **Authority and personality:** `DESIGN.md` requires crisp motion, semantic tokens, visible focus, and preserved feedback under Reduced Motion. For this calm operations surface, motion should explain changes—not make operators wait.
- **Frequency map, inferred rather than measured:** button feedback is likely frequent; palette/popover use likely repeats throughout keyboard workflows; toast frequency depends on events; dragging has continuous pointer updates followed by a discrete release.
- **Evidence level:** static excerpts only. Declared timing and properties are observable; actual visibility, focus behavior, animation playback, frame performance, and perceived latency are not.

## 2. Vetted priorities

Priorities reflect product relevance and code-level risk, not measured incident severity.

| Priority | Finding and evidence | Recommended disposition | Evidence limit |
|---|---|---|---|
| P1 | Palette declares `420ms ease-in`, bypassing existing timing/easing tokens. Its animation class is unconditional; `open` is only shown as a data attribute. | Use state-aware, token-based entrance/exit styling; keep search and focus independent of animation completion. | Keyframes, mounting, visibility rules, and focus management are absent. Cannot conclude that it animates on every toggle or delays input. |
| P1 | Popover uses `transition: all 360ms ease-in` and a centered origin. | Limit transitions to intended properties; use responsive timing. Match direction to placement if displacement is needed. | Actual changing properties and placement logic are unknown. Center origin matters only for relevant transforms. |
| P1 | Toast entrance animates `top` for `500ms ease-in`. | Use a short transform/opacity entrance without changing final positioning. | Animating positional properties creates layout-work risk; positioning and actual rendering cost are unverified. |
| P2 | Queue release specifies a fixed `400` duration; pointer movement writes `--drag-y`. | Keep direct tracking; shorten and make release settling interruptible. | Units/API semantics, coordinate conversion, CSS consumption, and pointer-to-state synchronization are unknown. |
| P1, cross-cutting | Only the button excerpt demonstrates a Reduced Motion path. | Verify coverage and implement explicit alternatives in all three plans. Preserve visible focus and state feedback. | Missing rules in excerpts do not prove the full project lacks coverage. |

## 3. Implementation plans

All checks below are **proposed acceptance checks**, not checks already performed.

### Plan A — Shared overlay motion and command palette

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

**Target behavior**
- Popover: 160ms responsive entrance; palette: 240ms responsive entrance. Use opacity plus at most 4px of translation, without scale.
- Exit, if supported by existing presence handling: 160ms responsive. Do not introduce delayed unmounting solely to obtain an exit.
- Opening, search input, dismissal, focus transfer, and focus return must not await animation completion.
- Reversals should follow the latest open state rather than queue animations.

**Project conventions**
- Reuse the three existing tokens unchanged; use explicit property lists as in the button precedent.
- Preserve the established overlay lifecycle and visible-focus styles.

**Ordered steps**
1. Locate the `palette` keyframes, `.popover` consumers, `data-open` selectors, visibility/presence handling, placement transforms, and focus logic.
2. Establish which element owns positioning versus visual motion. Avoid replacing a placement transform; use an existing inner surface or compatible transform composition.
3. Replace the popover’s `all` transition with explicit opacity/transform transitions using `--duration-fast` and `--ease-responsive`.
4. Replace the palette’s unconditional utility animation with state-aware styling using `--duration-panel` for entry and `--duration-fast` for any existing exit.
5. Define the open visual endpoint as full opacity and zero motion offset. Use placement-aware displacement for popovers; omit translation where direction is ambiguous.
6. Add Reduced Motion overrides and state-transition tests.

**Hard boundaries**
- No token-value changes, unrelated button changes, spring library, new focus trap, or search/data-flow rewrite.
- Never equate `opacity: 0` with hidden/inert; preserve semantic closure and hit-testing behavior.
- Do not animate focus outlines or override positioning transforms.

**Mechanical checks**
- Verify the old utility is removed, generated styles resolve, and neither touched overlay uses `transition: all`.
- Check open/closed endpoints, rapid toggle state handling, existing focus tests, and build/type/style checks.
- Confirm no new input or focus handler waits on a timer or animation event.

**Runtime/feel checks**
- Exercise repeated open/Escape/open sequences, immediate typing, keyboard navigation, and focus return.
- Inspect popovers in supported placements and near viewport edges; look for positional jumps, lingering hit targets, and interrupted exits.

**Reduced Motion**
- Remove translation; use at most 80ms opacity feedback, matching the local reduced-duration precedent.
- Preserve immediate focus and closure semantics, including when the preference changes while open.

**Source-drift stop condition**
- Stop if actual keyframes, lifecycle rules, positioning ownership, or existing Reduced Motion rules differ from the assumed change points. Reconcile the plan before replacing animation ownership.

### Plan B — Toast entrance without positional animation

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

**Target behavior**
- Enter from a restrained 4px upward offset to the existing resting position, with opacity from 0 to 1.
- Use `--duration-fast` and `--ease-responsive`; preserve readable content and existing notification semantics.

**Project conventions**
- Reuse existing tokens and explicit visual properties. Treat the button’s 80ms reduced path as the local timing precedent.

**Ordered steps**
1. Inspect toast positioning, resting `top`, stacking, transform ownership, dismissal, announcements, and lifetime scheduling.
2. Confirm whether the animation currently supplies the final `top: 0`; if so, move that endpoint into the appropriate static positioning rule before removing animated `top`.
3. Replace positional keyframes with translation/opacity keyframes. If stacking already owns transforms, animate a separate existing content surface or reconcile ownership first.
4. Make the base style the visible resting endpoint; avoid retaining a fill mode merely to hold final layout.
5. Add the Reduced Motion override and regression checks for entrance and dismissal.

**Hard boundaries**
- Do not change toast lifetime, announcement urgency, content, stacking order, or dismissal behavior.
- Do not add permanent `will-change`, stagger notifications, or make feedback wait for entrance completion.

**Mechanical checks**
- Confirm entrance keyframes no longer contain `top`; timing/easing reference existing tokens.
- Verify stable endpoints with animation disabled and audit transform/fill-mode interactions.
- Run available style/build checks and existing notification tests.

**Runtime/feel checks**
- Trigger single and burst notifications; dismiss during entrance; inspect stacking and any layout shift.
- Check that text becomes legible promptly and existing announcements remain correct.

**Reduced Motion**
- Use opacity-only entrance for at most 80ms; leave the toast fully visible when animation is disabled.
- Do not shorten its readable lifetime.

**Source-drift stop condition**
- Stop if `top` or transforms participate in stack management, or shared keyframes affect other surfaces. Resolve ownership and impacted consumers before modifying them.

### Plan C — Direct drag tracking and short, interruptible settling

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

**Target behavior**
- Pointer tracking remains direct, without easing or transitions.
- Release settles to the selected slot in the equivalent of `--duration-fast` with responsive easing.
- A new drag cancels the old settle and continues without jumping; committed order is not gated on visual completion.

**Project conventions**
- Reuse semantic timing/easing through the existing CSS-to-JavaScript token bridge, if present.
- Confirm animation API units before translating `160ms`; do not assume `duration` accepts milliseconds.

**Ordered steps**
1. Inspect `animateTo`, the `--drag-y` consumer, coordinate conversion, `currentY` updates, reorder commit logic, pointer cancellation, and keyboard reorder behavior.
2. Verify that the release calculation uses the latest pointer position in slot coordinates; fix any demonstrated mismatch, not an assumed one.
3. Ensure direct manipulation has no CSS transition or competing settle animation.
4. Replace the release duration with the existing fast token through the established integration; map responsive easing to the API’s supported form.
5. Implement or retain cancellation on re-grab, cancellation, and teardown; prevent stale callbacks from changing newer state.
6. Add a runtime Reduced Motion branch and tests for release, interruption, and final ordering.

**Hard boundaries**
- No inertia, bounce, spring dependency, per-pointer-event token reads, or coordinate-system rewrite without evidence.
- Preserve keyboard controls and focus; do not replace them with pointer-only interactions.
- Do not add frame batching or performance claims without examining the existing update path.

**Mechanical checks**
- Verify token conversion/API units, absence of transition lag during tracking, and latest-position targeting.
- Test rapid release/re-grab, cancellation, teardown, final slot/order, and stale completion handling.
- Test Reduced Motion selection and any existing keyboard reorder path.

**Runtime/feel checks**
- Try short/long drags, fast release, re-grab during settling, scrolling, and boundary slots.
- Check for pointer offset jumps, overshoot, delayed order changes, and lost keyboard focus.

**Reduced Motion**
- Retain direct pointer tracking: it communicates user-controlled position.
- Snap immediately on release; preserve final order, focus, and existing non-spatial confirmation.

**Source-drift stop condition**
- Stop if `animateTo` owns business-state commits, the token bridge is absent, or coordinate/transform ownership differs. Resolve that integration explicitly before changing release timing.

## 4. Execution order and unverified states

1. **Plan A:** establish token-based overlay behavior and Reduced Motion coverage for repeated keyboard workflows.
2. **Plan B:** replace toast positional entrance while preserving resting layout and notification semantics.
3. **Plan C:** address settling after inspecting animation and coordinate contracts; this has the most integration uncertainty.

**Explicitly unverified:** actual animation playback; full stylesheet coverage; mounting/unmounting; hidden-state semantics; focus and announcements; keyboard reorder support; pointer capture/cancellation; coordinate correctness; API duration units; performance; interruption behavior; Reduced Motion on real systems; and perceived speed or comfort. No browser, device, accessibility-tree, trace, or user validation was performed.


## Output C

## 1. Recon summary

- **Stack signals:** React-style TSX, plain CSS, an arbitrary animation utility class, and imperative pointer handling. The utility framework and `animateTo` implementation are unknown.
- **Motion locations:** shared tokens and popover rules in `src/styles/motion.css`; palette animation in `src/components/CommandPalette.tsx`; toast keyframes in `src/components/toast.css`; drag/release logic in `src/components/SortableQueue.tsx`.
- **Existing conventions:** `--duration-fast: 160ms`, `--duration-panel: 240ms`, and `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)`. `src/components/Button.css` demonstrates property-scoped transitions and an 80ms Reduced Motion override. Preserve that correct local precedent.
- **Authority and personality:** the stated `DESIGN.md` requirements favor crisp, restrained feedback, semantic tokens, visible focus, and a Reduced Motion path that retains state information.
- **Frequency map — inferred, not measured:** palette and button interactions are likely frequent; popovers recur throughout workflows; toast frequency depends on events; sorting is task-dependent, with repeated pointer updates during each gesture.
- **Evidence level:** supplied static excerpts only. Findings distinguish declarations from possible consequences. No repository inspection, execution, or browser/device validation of this project occurred.

## 2. Vetted priorities

| Priority | Severity | Location | Supported finding | Recommended action |
|---|---|---|---|---|
| 1 | High | `src/components/CommandPalette.tsx` | Declares an unconditional 420ms `ease-in` animation class. Its relationship to `open` is not shown. | Remove decorative palette animation; make keyboard access immediate. Do not infer that input is currently blocked. |
| 2 | Medium | `src/styles/motion.css` | `.popover` uses `transition: all 360ms ease-in`, bypassing existing tokens and broadly selecting properties. | Scope transitions to opacity/transform and use the existing 160ms responsive tokens. |
| 3 | Medium | `src/components/toast.css` | Entry animates `top` over 500ms with `ease-in`. Actual layout cost depends on positioning and rendering context. | Preserve the 24px entry relationship using transform, with a 160ms responsive entrance. |
| 4 | Medium | Palette, popover, toast, queue excerpts | No Reduced Motion handling is shown for these surfaces; only the button excerpt demonstrates it. Global coverage is unknown. | Inspect effective coverage, then implement explicit local behavior without removing feedback. |
| 5 | Medium; investigation-gated | `src/components/SortableQueue.tsx` | Release requests a fixed 400-duration animation; units, cancellation, velocity handling, and CSS-variable consumers are unknown. | Verify the motion adapter and coordinate model before implementing a short, interruptible settle. |

`transform-origin: center` is **not independently a defect**: the excerpt does not establish whether the popover scales or how it is anchored. Likewise, the drag CSS variable alone does not establish expensive descendant invalidation. No additive animation is justified by this evidence.

## 3. Implementation plans

### Plan A — Make the command palette immediate

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

**Target:** opening, closing, and repeated invocation have no decorative animation or motion-dependent input delay. Search, selection, and focus remain visible and immediate.

**Conventions:** respect the stated `DESIGN.md` requirements for throughput and visible focus. Existing tokens in `src/styles/motion.css` are 160ms/240ms with `cubic-bezier(0.23, 1, 0.32, 1)`; this high-frequency surface needs no replacement animation.

**Ordered steps:**
1. Inspect the palette’s visibility, mount/unmount, focus, and animation-event wiring. Determine whether `palette` keyframes also supply essential visibility styles.
2. Remove `className="animate-[palette_420ms_ease-in_both]"`; preserve `data-open={open}` and `<SearchResults />`.
3. If visibility depends on those keyframes, stop and revise the plan rather than deleting essential state behavior. Otherwise retain the existing open/closed mechanism unchanged.

**Hard boundaries:** no result staggering, new motion library, search changes, focus redesign, or global utility/keyframe deletion.

**Mechanical checks:** confirm the animation class is absent; confirm `open` and result rendering contracts are unchanged. Run the project’s declared typecheck/lint and palette tests after discovering their actual commands; add or extend a focused test for open/closed rendering if infrastructure exists.

**Runtime/feel checks — future work:** repeatedly invoke, dismiss, and reopen by keyboard; type immediately after invocation. Verify visible initial focus, focus restoration, no closed-but-focusable palette, and no visual replay. These checks are acceptance criteria, not claims about current behavior.

**Reduced Motion:** use the same immediate state changes; retain visible focus, selection, and results feedback. No fade is required merely to preserve feedback.

**Source-drift stop:** stop if the excerpt differs materially, animation events control lifecycle, keyframes own visibility, or the open/closed contract cannot be established from source.

### Plan B — Normalize passive entrances without broad transitions

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

**Target:** retain existing lifecycle and positioning; use 160ms responsive entrances. Popovers transition only transform/opacity; toast entry translates from `-24px` to `0` at its existing final position. No decorative bounce.

**Conventions:** reuse `--duration-fast` and `--ease-responsive`, without changing their definitions. `src/components/Button.css` establishes explicit transform transitions and an 80ms Reduced Motion precedent; leave that file unchanged.

**Ordered steps:**
1. Inspect all `.popover` state rules, toast positioning, transform ownership, exit/stack behavior, and existing Reduced Motion overrides. Confirm shared tokens reach both surfaces.
2. Replace the popover declaration with:
   ```css
   transition: transform var(--duration-fast) var(--ease-responsive),
               opacity var(--duration-fast) var(--ease-responsive);
   ```
3. Preserve its current origin unless source confirms trigger-anchored scaling and an existing placement-origin contract. If confirmed, use that contract; do not invent a positioning-library variable.
4. Replace toast entry endpoints with `transform: translateY(-24px); opacity: 0` and `transform: translateY(0); opacity: 1`. Use `animation: toast-enter var(--duration-fast) var(--ease-responsive) forwards`.
5. Preserve the prior final positioning outside the keyframes: if `top: 0` was supplied only by the animation, establish it as static styling after verifying positioning. Do not overwrite an existing transform used for stacking.
6. Add local `prefers-reduced-motion: reduce` rules: popovers use only an 80ms opacity transition and no animated translation/scale; toast uses a separate 80ms opacity-only entry with `var(--ease-responsive)`. Keep essential positioning transforms intact.

**Hard boundaries:** only the two named CSS files; no lifecycle rewrites, timers, dismissal changes, dependency additions, global motion reset, or button edits. Do not add exit animation or convert toast lifecycle merely because entry uses keyframes.

**Mechanical checks:** confirm `.popover` has no `transition: all`; toast keyframes contain no animated `top`; durations/easing reference existing tokens. Confirm matching opacity-only overrides and no duplicate animation names. Run available stylesheet/build checks using declared project scripts.

**Runtime/feel checks — future work:** open and reverse popovers rapidly; verify positioning and focus never depend on transition completion. Trigger single and stacked toasts, dismiss during entry, and inspect at normal and slow playback. Check for jumps, transform collisions, replay, or retained `forwards` styles interfering with exits. Do not infer smoothness from property choice alone.

**Reduced Motion:** verify no decorative movement, an 80ms fade where applicable, and unchanged readability, dismissal, focus, and notification semantics.

**Source-drift stop:** stop if transforms already own positioning/stacking, `top` is externally animated, token scope differs, or state/lifecycle rules conflict with these replacements. Record the conflict and revise scope before implementing.

### Plan C — Establish a reliable drag-to-settle contract

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

**Target:** preserve pointer-to-item continuity, settle from the currently rendered position, and allow immediate re-grab without jumping. Use a restrained, interruptible 160ms responsive settle as the initial target—not an invented spring configuration.

**Conventions:** `src/styles/motion.css` defines `--duration-fast: 160ms` and `--ease-responsive: cubic-bezier(0.23, 1, 0.32, 1)`. Reuse them through the existing animation adapter; do not introduce parallel constants or assume `animateTo` units/API. Preserve visible focus and existing keyboard sorting.

**Ordered steps:**
1. Trace `animateTo`, `currentY`, `nearestSlot`, pointer-down/cancel handlers, and every `--drag-y` consumer. Identify coordinate spaces, item offsets, scrolling, transform ownership, and the order of state/layout updates.
2. Confirm the adapter supports cancellation/retargeting from the rendered position and token-derived timing. If it does not, stop for a scoped adapter plan; changing `{ duration: 400 }` alone is insufficient.
3. At drag start or re-grab, cancel the settle at its current rendered position and rebase the pointer offset there. During dragging, preserve direct tracking with no trailing transition.
4. On release, capture the latest valid drag position and destination before clearing dragging state; ensure a layout change cannot reset the visual start. Keep the existing nearest-slot selection policy.
5. Settle to that destination using the shared 160ms responsive timing. Handle pointer cancellation without leaving a stale animation, drag flag, or captured pointer.
6. Under Reduced Motion, commit the release destination immediately, while preserving direct manipulation and a visible settled/drop state. Respond safely if the preference changes during a settle.

**Hard boundaries:** do not change ordering/business rules, add inertia or bounce, replace the drag framework, or rewrite CSS-variable updates without inspecting consumers. Implementation stays in the named file unless a revised plan explicitly authorizes dependencies.

**Mechanical checks:** test final-pointer sampling, cancellation, release-state ordering, and re-grab using the project’s existing test infrastructure. Confirm there is at most one active settle, shared timing is used, and Reduced Motion bypasses release interpolation. Run declared typecheck/lint commands.

**Runtime/feel checks — future work:** test slow/fast releases, re-grab mid-settle, first/last slots, scrolling, pointer cancellation, and keyboard reorder. Watch for coordinate jumps and delayed tracking at normal speed; use slow playback to inspect the handoff.

**Reduced Motion:** pointer-driven movement remains necessary direct feedback; autonomous release travel is removed. Keep final ordering, drop indication, and existing announcements observable.

**Source-drift stop:** stop if adapter semantics, coordinate ownership, token access, keyboard behavior, or required handlers cannot be verified, or if implementation requires changes outside the authorized file.

## 4. Execution order and unverified states

1. **Plan A:** highest likely throughput benefit and smallest change.
2. **Plan B:** reuse established tokens; validate positioning before replacing toast movement.
3. **Plan C:** investigate first, then implement only after its adapter and coordinate gates pass.

**Explicitly unverified:** actual interaction frequency; palette keyframes and visibility lifecycle; effective CSS and global Reduced Motion coverage; popover anchoring; toast positioning/stacking/exits; drag adapter units and interruptibility; focus behavior, announcements, keyboard parity, frame performance, and browser/device feel. No checks above have been executed, and no files or on-disk plans were created.
