## 1. Sequence and verdict

**Audit → harden → optimize → polish**, with baseline measurement before changes and targeted validation at every stage:
- **Audit:** map states, permissions, data extremes, accessibility requirements, and performance baselines.
- **Harden:** make saves, failures, recovery, drawer interaction, and tablet access safe.
- **Optimize:** address row rendering, filtering, and images without breaking selection or keyboard behavior.
- **Polish:** refine spacing, truncation, motion, and status feedback using existing design-system patterns.

**Verdict:** The supplied description is not ready for production sign-off: save outcomes are unreliable, recovery states are missing, and drawer accessibility is incomplete; runtime performance and tablet usability remain unverified.

This is a read-only assessment of the supplied source facts. No detector, browser, build, profiler, accessibility-tree, network-throttle, or device run was performed.

## 2. Prioritized findings: evidence versus hypotheses

Priorities: **P0** confirmed release-blocking integrity/security issue; **P1** required hardening; **P2** important robustness/performance; **P3** polish. No P0 is conclusively established by the excerpts.

| Priority | Finding | Source evidence | Runtime hypothesis / escalation condition |
|---|---|---|---|
| P1; conditional P0 | Failed saves have no usable outcome | `catch {}` suppresses errors; `saving` returns to false regardless of success | Users may mistake an unsaved edit for a saved one. Escalate to P0 if failure clears drafts, falsely reports success, or causes irreversible loss. |
| P1 | Save status cannot represent overlapping requests | One boolean tracks every invocation | If saves overlap, the first completion can hide another pending save; request ordering could overwrite newer edits, depending on API semantics. |
| P1 | Recovery and batch outcomes are absent | No conflict, authorization, rate-limit, server, timeout, offline, retry, or partial-failure states | Staff may lose context, repeat successful operations, or be unable to recover safely. Backend behavior is not shown. |
| P1 | Drawer interaction is unsafe or ambiguous | No focus/background containment; Escape closes during a pending save; save/close are icon-only | Focus may escape a modal; closure may hide unresolved work. Actual draft persistence and accessible names are unknown. |
| P1 | Tablet fit is structurally constrained | Page minimum width is 1180px; fixed drawer is 520px wide and `100vh` tall | Narrower viewports may cause page-wide overflow or obscure controls, especially with the on-screen keyboard. |
| P1 | Accessible interaction is incomplete | 28px icon buttons, `outline: none`; keyboard behavior, labels, and focus-visible are undescribed | Controls may lack names or visible focus. Rendered semantics, overrides, spacing, and contrast require inspection. |
| P2; promote if task-blocking | Rendering and filtering have unbounded main-thread cost | All 10,000 rows render; filtering recalculates synchronously per keystroke | Input delay, slow drawer updates, and dropped frames are plausible, not measured. |
| P2 | Loading is indistinguishable from missing content | Initial and filter loading show a blank body; no empty-results state | Users may interpret loading as zero stock or a broken screen. |
| P2 | Data and media extremes are unsupported | Names up to 200 characters, missing prices/images, 60% label expansion, 8MB images, no reserved image dimensions | Ambiguous prices, inaccessible truncated names, layout shifts, and excessive transfer/decode cost are possible. |
| P3 | Motion is overly broad | Rows and drawer use `transition: all 300ms ease-in`; no reduced-motion behavior described | Layout properties may animate unintentionally. The affected properties and actual rendering cost need verification. |

## 3. Concrete fixes within the existing surface

### Save integrity, failures, and recovery
- Replace the boolean-only model with explicit **clean, dirty, saving, saved, and error/conflict** states, scoped to the relevant product and revision.
- Report “Saved” only after a confirmed response for that revision; retain edits made while an earlier revision is saving.
- Serialize/coalesce autosaves per product, or use the existing API’s revision/version checks. Ignoring stale responses alone does not prevent stale server writes.
- Preserve the draft on failure. Show a persistent inline error and a clear retry path; do not depend only on transient notifications.
- Define pending-save closure behavior: keep the save/draft alive outside the drawer, or explain why closure is temporarily unavailable. Never silently discard work.
- Confirm discard only when work would actually be lost; successful durable autosaves should not trigger unnecessary prompts.
- Handle failures by meaning:
  - **401:** retain the draft through the approved reauthentication flow.
  - **403:** explain the denied operation and offer an allowed exit; do not retry automatically.
  - **409:** preserve local input, retrieve the latest revision, and provide review/reapply using existing conflict conventions.
  - **429:** respect `Retry-After`, back off, and avoid retry storms.
  - **500/timeout/offline:** preserve work and explain the uncertain outcome; reconcile before retrying mutations that might already have committed.
- Use idempotency support where available; do not assume a client timeout means the server rejected the save.
- For partial batches, show per-item outcomes and counts. Retry only failed eligible items; never silently repeat successful ones.
- Keep selection keyed by stable IDs, not row positions. Clearly distinguish selected visible rows from all matching rows and retain understandable scope across filters.
- Reflect permissions in edit/upload/bulk affordances while retaining server-side authorization. No client-side permission defect proves a backend security flaw.
- If reload recovery is needed, use approved, scoped, expiring draft storage rather than indiscriminately persisting inventory data.

### Hostile data and uploads
- Preserve column alignment while allowing bounded wrapping or truncation. Make full names available through keyboard and touch-accessible existing patterns, not hover alone.
- Show a localized “Not set” for absent prices, distinct from zero; format valid amounts with the correct currency and locale.
- Test long unbroken strings, 200-character names, expanded translations, and applicable bidirectional text. Let grid children shrink with `min-width: 0`.
- Reserve thumbnail space with explicit dimensions or aspect ratio; supply stable absent/broken-image placeholders.
- Use appropriately sized thumbnail assets rather than transferring full 8MB originals for table cells.
- Validate upload type, size, and decodeability on both appropriate client and server boundaries; show limits before selection.
- Represent upload progress, failure, retry, and cancellation. Distinguish uploaded media from media actually attached to a saved product.
- Render names as text; treat client validation as usability support, not a security boundary.

### Loading, empty states, and layout
- Differentiate initial loading, refreshing/filtering, no inventory, no matches, and load failure.
- During refresh, retain prior rows only with an explicit updating indicator; do not present old rows as current results.
- Keep skeletons/placeholders dimensionally stable and avoid announcing each placeholder to assistive technology.
- Replace page-wide fixed minimum sizing with a flexible shell and a deliberately bounded horizontal table-scroll region.
- Preserve the operational columns and table workflow; do not convert everything into cards or silently hide essential data.
- Cap drawer width to the viewport, use a dynamic viewport-height strategy with fallback, and provide internal scrolling with reachable actions.
- Verify tablet portrait/landscape, zoom, long translations, and the on-screen keyboard. Horizontal table scrolling must not force unrelated controls offscreen.

### Accessibility and motion
- Decide whether the existing drawer is modal. If modal, use a labelled dialog, appropriate initial focus, focus containment, inert background, and focus restoration.
- If intentionally nonmodal, do not trap focus or declare modality; provide predictable navigation between editor and table.
- Give save, close, selection, upload, and bulk controls accessible names. Use visible labels where ambiguity warrants them.
- Restore a clearly visible `:focus-visible` style using design tokens; do not remove outlines without an equivalent.
- Prefer approximately 44px touch hit areas for frequent tablet actions while preserving compact icon visuals.
- Preserve native table/header relationships where appropriate. An ARIA grid is not a shortcut: it requires a complete, documented keyboard interaction model.
- Label row checkboxes meaningfully; expose select-all’s mixed state and selection scope.
- Announce save progress/results politely without repeating on every keystroke; associate errors with their affected controls.
- Transition only intended properties. Prefer transform/opacity for drawer motion where suitable, and honor reduced-motion preferences.

### Performance
- Measure first, then bound rendered rows through existing windowing facilities or the least disruptive established paging pattern; do not add a dependency by default.
- Preserve logical row counts, headers, focus, selection, and assistive-technology navigation when windowing. Never recycle a focused row without a safe handoff.
- Separate urgent input updates from expensive filtering; debounce or defer as appropriate, and avoid stale filter results replacing newer ones.
- Cache expensive derivations by their actual inputs. Consider existing server filtering only if its semantics and API support fit the workflow.
- Profile row rerenders before memoizing. Stable props and state isolation may prevent save-status changes from rerendering the full list.
- Lazy-load offscreen thumbnails, request suitable sizes, and release temporary upload preview resources.

## 4. Static signals: decisive versus contextual

**Decisive in the supplied material**
- Save errors are swallowed; success and failure have no distinct representation in the shown state.
- Rendering work scales with the entire 10,000-row array; filtering is synchronous by the supplied note.
- Fixed page/drawer dimensions impose real constraints; image space is not reserved.
- Loading and failure-state coverage is explicitly incomplete.
- `outline: none` removes that outline; `transition: all` indiscriminately opts changed animatable properties into transitions.

**Require project or runtime context**
- A 28px target is not automatically a WCAG minimum-target failure: applicable criteria, spacing, and exceptions matter. It can still be poor tablet ergonomics.
- Icon-only controls are not inherently unnamed; accessible-name markup is not shown.
- Missing focus trapping is a modal-dialog defect, not a universal drawer defect.
- Ellipsis is not inherently inaccessible; full-text access and actual accessible names must be checked.
- `100vh` and fixed widths are risk signals, not proof that every supported viewport fails.
- Ten thousand rows do not establish a specific latency; virtualization is not automatically accessible or necessary in every implementation.
- Broad transitions do not prove layout thrashing; inspect what actually changes.
- Absent permission affordances do not demonstrate missing server authorization.

## 5. Measurement-first validation and rollout

1. **Record a baseline before changes:** use a fixed 10,000-row dataset with long names, missing prices/media, expanded labels, and upload extremes on agreed desktop and tablet profiles.
2. **Measure representative tasks:** initial usable table, filter-to-result latency, input responsiveness, drawer open/edit/save, bulk actions, scrolling, layout shift, image bytes, DOM size, and memory after repeated use.
3. **Inspect interaction paths:** keyboard-only traversal, visible focus, dialog entry/exit, selection semantics, accessible names, save announcements, zoom, reduced motion, and tablet touch/keyboard reachability.
4. **Exercise deterministic failure cases:** overlapping saves, out-of-order responses, timeout after server commit, offline/reconnect, every listed HTTP failure, partial batch success, and close/reopen while dirty or saving.
5. **Agree budgets before implementation:** suggested field targets are p75 INP ≤200ms, CLS ≤0.1, and LCP ≤2.5s where applicable; route-specific filter/save targets must distinguish client work from backend latency.
6. **Acceptance:** no false “Saved,” silent draft loss, duplicate mutation on retry, stale overwrite, or selection-scope error in the test matrix; all critical actions remain reachable and understandable.
7. **Performance acceptance:** demonstrate improvement against the same baseline without regressing correctness, accessibility, supported tablet behavior, or agreed latency/memory budgets.
8. **Roll out incrementally:** separate correctness/state fixes, rendering changes, and visual polish into reversible releases; use existing rollout controls and non-sensitive telemetry.
9. **Rollback triggers:** increased failed/duplicate saves, conflict-related loss, focus/selection regressions, inaccessible actions, or breached performance budgets. Disable the responsible change while retaining independently validated integrity fixes.
10. **Sign-off:** require recorded measurements and recovery-test results. Static cleanup alone is not proof of production readiness.
