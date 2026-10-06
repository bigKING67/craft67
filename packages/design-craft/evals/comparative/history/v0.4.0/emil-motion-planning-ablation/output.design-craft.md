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
