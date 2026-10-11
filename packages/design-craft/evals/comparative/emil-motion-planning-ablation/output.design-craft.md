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
