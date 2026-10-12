## 1. Sequence and verdict

**Sequence:** Audit → harden correctness, recovery, and accessibility → polish within existing design tokens and workflow → optimize against measurements → validate and release incrementally. Establish performance baselines before changes; address obvious high-cost rendering during hardening if it prevents usable operation.

**Verdict:** Not ready for production sign-off: silent save failures, incomplete recovery states, and drawer interaction gaps are source-confirmed; performance and tablet usability carry substantial unmeasured risk.

This is a read-only assessment of the supplied description. No execution, browser inspection, build, detector, profiler, accessibility-tree inspection, network throttling, or device testing occurred.

## 2. Prioritized findings

Priorities: **P0** release blocker for trustworthy editing; **P1** required production hardening; **P2** robustness/polish; **P3** measured refinement. Runtime consequences below are hypotheses, not test results.

| Priority | Finding and source evidence | Runtime hypothesis / uncertainty |
|---|---|---|
| **P0** | **Save failure is hidden.** `catch {}` discards errors; `saving` returns to `false` regardless of success. Failure and retry states are absent. | Operators may mistake completion for persistence and leave with unsaved work. Actual status wording is not shown. |
| **P1** | **Save lifecycle is not concurrency-safe.** One boolean represents every request; no sequencing, cancellation, or revision handling is shown. | If saves overlap, an earlier completion can clear pending status while another request remains active. Stale writes depend on API behavior. Escalate to P0 if lost updates are confirmed. |
| **P1** | **Recovery is incomplete.** Empty, authorization, conflict, rate-limit, server, timeout, offline, and partial-batch states are explicitly absent. | Users may repeat successful operations, lose drafts, or lack a safe path forward. Backend idempotency and authorization are unknown. |
| **P1** | **Drawer has incomplete interaction containment.** No focus or background-interaction trap; Escape closes during pending saves; save/close are icon-only. | For a modal drawer, focus can escape and background edits can occur. Closing may hide unresolved changes; icon-only controls are not necessarily unlabeled, but names require verification. |
| **P1** | **Keyboard focus protection is missing.** `.icon-button` removes outlines; focus-visible and keyboard behavior are undescribed. | Keyboard users may lose their location unless another focus indicator exists. Full keyboard operability cannot be inferred. |
| **P1** | **Tablet layout is constrained by desktop sizing.** Page minimum is `1180px`; drawer is fixed at `520px` and `100vh`. | Narrow viewports, zoom, and an on-screen keyboard may cause clipping, page-wide scrolling, or unreachable actions. Actual geometry needs testing. |
| **P1** | **Rendering and filtering scale poorly by construction.** All 10,000 rows render; filtering runs synchronously on each keystroke. | Input delay, long tasks, and excessive layout/memory are plausible, but their magnitude is unmeasured. |
| **P1** | **Loading is indistinguishable from missing content.** Initial/filter loading leaves the body blank. | Operators may interpret loading as zero inventory or repeat actions. Whether stale results remain elsewhere is unknown. |
| **P2** | **Hostile data handling is incomplete.** Names reach 200 characters; prices/images may be absent; labels expand 60%; images may be 8MB. Names use ellipsis. | Ambiguous product identification, distorted layouts, slow uploads, and placeholder shifts are likely boundary failures to test. |
| **P2** | **Image geometry is not reserved.** Source notes explicitly identify this. | Image arrival may shift rows and targets; actual layout shift depends on surrounding constraints. |
| **P2** | **Animation scope is overly broad.** Rows and drawer use `transition: all 300ms ease-in`; reduced motion is undescribed. | Layout properties may animate unnecessarily; discomfort and rendering cost depend on which properties change. |
| **P2** | **Bulk-selection scope and permission affordances are unspecified.** The workflow includes bulk selection; permission-specific behavior is not described. | Filtering, paging/windowing, or partial failure may make selection counts or allowed actions misleading. |
| **P3** | **Further render/motion tuning lacks measurements.** Component costs and changed-property traces are unavailable. | Blanket memoization or animation rewrites may add complexity without useful gains. |

## 3. Concrete hardening and polish

### Save integrity and recovery
- Replace the boolean-only model with explicit `dirty`, `saving`, `saved`, and `error` states; distinguish validation and conflict failures.
- Show “Saved” only after an acknowledged successful revision. Keep dirty values and error context on failure.
- Serialize saves per product or coalesce queued edits; track revisions/request identity so stale responses cannot overwrite newer state.
- Coordinate with the API for version checks and idempotency where supported. Client response guards alone cannot prevent stale server writes.
- Define pending-save close behavior: keep drafts and visible save status if closing is allowed, or warn/block dismissal with an accessible explanation.
- Use the same policy for Escape, close, route changes, and other dismissals; do not silently discard edits.
- Keep drafts through recoverable failures. Persist locally only if data sensitivity and retention rules permit; do not promise offline durability without it.
- For uncertain outcomes after timeout/disconnection, reconcile server state before replaying non-idempotent actions.

### Loading, failures, and bulk actions
- Distinguish initial loading, refreshing, no inventory, and no filter matches. Offer clear/reset filters for the latter.
- Use stable loading geometry and a named busy region. During refresh, retain results only with clear stale/busy treatment and safe action rules.
- **401:** preserve the draft while offering reauthentication; **403:** explain the restriction and prevent unavailable actions.
- **409:** retain local edits, retrieve the current server version, and offer review/reconciliation rather than silent overwrite.
- **429:** respect `Retry-After`; **500/timeout:** show a persistent contextual error and controlled retry.
- **Offline:** indicate unsaved status; bound any automatic retry with backoff and stop conditions. Connectivity indicators alone do not establish API reachability.
- For batch results, show succeeded/failed counts and row-level reasons. Retry only eligible failures; never silently replay successes.
- Store selection by stable product ID, not row position or mounted DOM. State whether “select all” means visible rows or all matching results.
- Define what happens to selection when filters change; show hidden-selection counts and revalidate permissions before bulk execution.
- Keep server-side authorization authoritative; UI permission affordances improve clarity but are not a security boundary.

### Hostile data and uploads
- Let grid children shrink with `min-width: 0`; use `minmax(0, 1fr)` for flexible tracks.
- Keep ellipsis where appropriate, but expose the full product name through keyboard-, pointer-, and touch-accessible detail—not a hover-only tooltip.
- Test long unbroken strings, one-character names, punctuation, and 60% label expansion; allow labels/actions to wrap without overlap.
- Render missing prices explicitly as unavailable, never as zero. Preserve locale-aware currency formatting and applicable validation rules.
- Supply a stable missing/broken-image placeholder and reserve image space using dimensions or aspect ratio.
- Define upload type, size, and pixel-dimension limits; validate client-side for feedback and server-side for enforcement.
- Provide upload progress, cancellation, failure, and retry. Preserve the existing image until replacement succeeds.
- Treat large uploads separately from row thumbnails; use appropriately sized delivery assets where the existing pipeline supports them.

### Responsive layout and accessibility
- Replace the global minimum-width constraint with a fluid page shell; contain necessary horizontal scrolling within the table region.
- Preserve column relationships and operationally important fields rather than converting the editor into a new card workflow.
- Bound drawer width by the viewport, for example `min(520px, 100%)`; provide internal scrolling, reachable actions, and dynamic-viewport sizing with fallback.
- Verify drawer behavior with tablet portrait/landscape, browser zoom, safe areas, and the on-screen keyboard.
- Establish whether the drawer is modal. If modal: name the dialog, set modal semantics, contain focus, make the background inert, and restore focus on close.
- If intentionally nonmodal, provide deliberate keyboard transitions and safe background interaction rather than adding a trap indiscriminately.
- Use native buttons with accessible names for icon controls; restore a clearly visible `:focus-visible` style.
- Check actual hit regions and spacing: `28px` is not automatically a WCAG target-size failure, but larger touch-friendly targets are preferable for tablet use.
- Use appropriate table headers and labeled selection controls. Adopt grid semantics only if the complete grid keyboard interaction is implemented.
- Announce saves/errors through a restrained status/live region; do not announce every keystroke or rely on color alone.
- Restrict transitions to intentional properties, favor transform/opacity where suitable, and honor reduced motion.

### Performance without a redesign
- Measure row-render and filter costs before choosing implementation details.
- Window the table or use workflow-compatible paging; prefer existing project capabilities rather than adding a dependency by default.
- Preserve selection, row identity, scroll position, keyboard focus, and meaningful row information when rows mount/unmount.
- Avoid expensive filtering on every character: precompute searchable fields, reduce redundant work, and use a measured debounce or scheduling strategy.
- Keep input feedback immediate. Scheduling updates does not by itself make a monolithic synchronous filter cheap.
- Memoize rows/calculations only when traces show avoidable work; keep props stable where this produces a measurable benefit.
- Reserve image dimensions, lazy-load offscreen thumbnails, and verify image decoding and upload preview cleanup.

## 4. Static signals: decisive versus contextual

**Decisive from the supplied source**
- Save errors are swallowed; required failure states are absent.
- All rows are rendered and filters run synchronously per keystroke.
- Page/drawer sizing is rigid; image space is not reserved.
- Outline removal and broad transitions are present.
- These facts justify corrective work or targeted validation, but not invented timing, accessibility, or data-loss measurements.

**Require project/runtime context**
- Icon-only controls can be accessible if correctly named; missing labels are not proven by appearance.
- Outline removal fails users if no equivalent focus treatment exists; inspect all applicable styles.
- A focus trap is required for modal behavior, not every drawer.
- A 28px target is a usability concern, not an automatic standards failure.
- Ellipsis is acceptable if essential information remains accessible.
- `transition: all` is a risk signal, not proof of layout thrashing.
- Ten thousand rows is a strong scaling warning, not a measured latency result.
- Fixed dimensions may be intentional within a supported viewport contract; they must still be reconciled with tablet and zoom requirements.
- Missing permission UI does not prove missing server authorization; lack of shown concurrency protection does not prove the API lacks version checks.

## 5. Measurement-first validation and release gates

1. **Establish a baseline before changes.** Use representative 10,000-row data plus boundary fixtures: long names, missing values, expanded labels, absent/large images, and mixed permissions.
2. **Agree budgets in advance.** Record route readiness, filter input-to-paint latency, commit/render duration, long tasks, DOM size, memory, layout shift, and save acknowledgement time.
3. **Separate client and network costs.** Proposed starting gates: filter response p95 ≤200ms on an agreed tablet profile, no filter-related task >50ms, and no image-induced target movement. Calibrate these against actual operational requirements.
4. **Exercise deterministic failure cases.** Test every listed response/state, delayed and out-of-order saves, rapid repeated edits, close/reopen, navigation, reconnect, session expiry, and mixed batch outcomes.
5. **Validate integrity as a hard gate.** No false “Saved,” lost newer edit, silent conflict overwrite, duplicated successful batch action, or discarded failed draft.
6. **Inspect keyboard and assistive behavior manually.** Verify names, headers, focus visibility/order/return, modal containment where applicable, status announcements, and virtualized navigation.
7. **Test the supported layout matrix.** Desktop/tablet orientations, 200%/400% zoom, touch, software keyboard, reduced motion, and expanded translations; no unreachable essential action or unintended page-wide overflow.
8. **Compare before/after traces.** Accept optimization only if it improves the agreed bottleneck without degrading selection, focus, recovery, or supported-device performance.
9. **Release in reversible slices.** Separate save/recovery, drawer/layout, and rendering changes; use existing rollout controls and privacy-safe telemetry for failures, retries, conflicts, and latency.
10. **Rollback triggers:** any integrity/accessibility hard-gate failure, broken bulk semantics, or budget breach. Roll back the responsible slice to a known-safe state; if none exists, pause affected editing rather than restoring silent failure.

**Acceptance:** all P0/P1 issues resolved and verified, measured budgets met on supported hardware, and remaining P2/P3 work explicitly owned and scheduled.
