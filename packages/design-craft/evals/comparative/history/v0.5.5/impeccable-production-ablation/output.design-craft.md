## 1) Sequence and verdict

**Correct sequence:** audit static evidence and define baseline → harden data/failure/accessibility/state recovery → measure hot paths → optimize only proven or source-obvious bottlenecks → polish motion/layout within the existing system.

**One-line verdict:** This surface is not production-ready for a 10,000-row, keyboard-heavy operations workflow because static evidence shows silent save failure, missing recovery states, unsafe drawer behavior, unbounded rendering, and unresolved accessibility/responsive contracts.

## 2) Prioritized findings

### P0 — Data integrity and recovery are unsafe
**Source evidence:**  
- `catch {}` swallows save failures.  
- `setSaving(false)` runs after failure without any error state.  
- 409 conflict, timeout, offline, retry, and partial batch failure states are explicitly absent.  
- Escape closes the drawer while save is pending.

**Runtime hypothesis:** Actual data loss depends on API semantics and whether unsaved edits are kept elsewhere, but the shown code cannot prove that failed saves are visible or recoverable.

**Fix:**  
- Replace silent catch with explicit save result state: `idle | saving | saved | failed | conflict | offline | retrying`.  
- Keep failed edits in the drawer; do not clear or close on failed save.  
- Block or confirm drawer close while saving or dirty.  
- Add conflict UI showing server value, local value, and user action: reload, overwrite if permitted, or merge.  
- For batch edits, report succeeded, failed, skipped, and retryable rows.

### P1 — Loading, empty, auth, rate-limit, server, and permission states are missing
**Source evidence:**  
- Initial and filter loading render a blank table body.  
- Empty results, 401/403, 429, 500, timeout, offline, retry, and permission-specific affordances are not represented.

**Runtime hypothesis:** Backend may return structured errors, but no UI contract is described for them.

**Fix:**  
- Initial loading: render table skeleton or stable rows shell, not blank disappearance.  
- Filter loading: keep previous results visible with “Updating…” status.  
- Empty results: show active filters, clear-filter action, and no-results explanation.  
- 401/403: show re-auth or permission explanation; hide/disable actions the user cannot perform.  
- 429: show retry-after messaging and disabled save until allowed.  
- 500/timeout/offline: show retry, preserved edits, and last successful autosave time.  
- Partial batch failure: keep selection and show per-row failure reasons.

### P1 — Drawer interaction is not safe or accessible
**Source evidence:**  
- Drawer traps neither focus nor background interaction.  
- Escape closes it while save is pending.  
- Save and close are icon-only.  
- `.icon-button { width: 28px; height: 28px; outline: none; }`.

**Runtime hypothesis:** Component internals could add ARIA labels or focus styles elsewhere, but the supplied notes say labels/focus-visible are not described.

**Fix:**  
- Treat drawer as a modal or explicitly non-modal panel; for editing, modal behavior is safer.  
- On open: move focus to drawer heading or first editable field.  
- Trap focus inside while open; restore focus to invoking row on close.  
- Prevent background row interaction while modal drawer is open.  
- Add accessible names to icon-only save/close controls.  
- Replace `outline: none` with visible `:focus-visible` styling.  
- Disable close or require confirmation during pending save/dirty state.

### P1 — 10,000-row rendering and synchronous filtering are hot-path risks
**Source evidence:**  
- `{rows.map(...)}` renders all rows.  
- Product context says 10,000-row product table.  
- Filtering recalculates synchronously on every keystroke.

**Runtime hypothesis:** Actual frame drops, input latency, and memory cost require measurement, but the source shape is a decisive scalability smell.

**Fix:**  
- Virtualize visible rows while preserving keyboard navigation and selection semantics.  
- Debounce or defer filter input work; keep typing responsive.  
- Memoize filtered/sorted row derivations with correct dependencies.  
- Avoid recreating row props and handlers unnecessarily.  
- Move expensive normalization/search indexing out of the keystroke path.  
- Keep bulk selection state independent from rendered row count.

### P1 — Tablet support conflicts with fixed desktop geometry
**Source evidence:**  
- `.page { min-width: 1180px; }`.  
- Drawer fixed at `width: 520px; height: 100vh`.  
- Grid columns are fixed-heavy: `64px 280px 1fr 120px 96px`.  
- Tablet behavior is not described.

**Runtime hypothesis:** Horizontal scrolling may be acceptable for dense tables, but critical controls must remain reachable and drawer must fit.

**Fix:**  
- Keep desktop density, but isolate horizontal overflow to the table region, not the whole page.  
- Make filters, autosave status, and primary actions remain visible above/around the scroll container.  
- Bound drawer width: `min(520px, 100vw)` or use full-screen drawer on narrower tablet widths.  
- Preserve row identity/action columns when horizontally scrolling.  
- Define tablet breakpoints for filters, drawer, and bulk-action bar.

### P2 — Hostile data is not contained
**Source evidence:**  
- Product names can be 1–200 characters.  
- Prices may be missing.  
- Translations may expand labels by 60%.  
- Some images are absent or 8MB.  
- Product names use nowrap ellipsis only.  
- Image dimensions are not reserved.

**Runtime hypothesis:** Some row components may handle fallback rendering internally, but it is not represented here.

**Fix:**  
- Product names: keep one-line table truncation with tooltip/details in drawer; never let names push action columns away.  
- Prices: render explicit “Missing price” or em dash with validation state, not blank.  
- Translations: test labels at +60%; avoid fixed-width action text where labels expand.  
- Images: reserve dimensions/aspect ratio; lazy-load thumbnails; show absent-image fallback.  
- Reject or process 8MB uploads with visible compression/progress/error state.

### P2 — Motion choices are broad and may harm performance/accessibility
**Source evidence:**  
- `.product-row, .drawer { transition: all 300ms ease-in; }`.  
- Reduced motion is not described.

**Runtime hypothesis:** Actual animation smoothness needs runtime inspection, but `transition: all` is a strong static risk.

**Fix:**  
- Transition only intended properties, preferably `transform` and `opacity` for drawer entrance.  
- Do not animate layout-affecting table properties.  
- Use shorter, clearer easing for operational feedback; avoid slow ease-in delays on exits.  
- Add reduced-motion path that removes large movement while preserving state feedback.

### P2 — Autosave status is too coarse
**Source evidence:**  
- Single `saving` boolean is passed to `EditDrawer`.  
- Save failures are swallowed.  
- Autosave status exists in product context but not represented as durable state.

**Runtime hypothesis:** The single boolean proves coarse ownership, not necessarily all concurrency behavior; overlapping saves need project context.

**Fix:**  
- Track per-product save status and last saved timestamp.  
- Distinguish saving, saved, failed, offline queued, and conflict.  
- Prevent stale responses from overwriting newer edits.  
- If autosave batches, expose queue depth and partial failures.

### P3 — Visual polish should follow hardening, not mask it
**Source evidence:**  
- Existing design system/workflow must be preserved.  
- Several missing states and data contracts precede visual refinement.

**Runtime hypothesis:** Actual visual hierarchy cannot be fully judged from the snippet alone.

**Fix:**  
- After state/performance fixes, polish density, row scanning, focus rings, status placement, and drawer transitions using existing tokens.  
- Do not introduce decorative layouts, new component paradigms, or new dependencies as the first move.

## 3) Concrete fix coverage by area

- **Hostile data:** bounded text, explicit missing values, i18n expansion checks, reserved image boxes, upload size/progress/error handling.  
- **Failures:** typed error states for auth, permission, conflict, rate limit, server, timeout, offline, retry, and partial batch failure.  
- **Responsive layout:** table-contained overflow, reachable controls, bounded drawer, tablet-specific drawer/filter behavior.  
- **Accessibility:** focus trap/restoration, labeled icon buttons, visible focus, keyboard row navigation, reduced motion, permission-aware disabled states.  
- **State recovery:** dirty-state guard, pending-save close protection, preserved failed edits, retry queue, conflict resolution.  
- **Performance:** virtualization, deferred filtering, memoized derived data, stable row props, reserved image dimensions, measured render/input budgets.

## 4) Static detector-like signal reconciliation

**Decisive from supplied static evidence:**  
- Empty `catch {}` means save errors are swallowed in the shown save path.  
- Missing represented states are decisive because the prompt explicitly says they are absent.  
- Rendering `rows.map` for all rows is decisive for unvirtualized rendering in the shown component.  
- `min-width: 1180px`, fixed drawer width, fixed grid columns, `transition: all`, and `outline: none` are real static CSS risks.  
- Notes that focus trap, background interaction blocking, tablet behavior, screen-reader labels, focus-visible, and reduced motion are not described are decisive gaps in the supplied scope.

**Needs project/runtime context before final severity or implementation choice:**  
- Actual input latency, scroll FPS, memory pressure, layout shift, and animation smoothness.  
- Whether row internals already provide ARIA labels, fallbacks, or keyboard shortcuts.  
- Whether horizontal scrolling is an accepted table pattern for this product.  
- Whether API provides retry-after, conflict payloads, idempotency keys, or offline queue support.  
- Whether the drawer is intended to be modal or a persistent side panel.  
- Whether the single `saving` boolean creates real concurrency bugs across multiple save paths.

## 5) Measurement-first validation plan

**Baseline before changes:**  
- Record render time, input latency while filtering, scroll responsiveness, memory, and image layout shift with 10,000 representative rows.  
- Capture state matrix coverage: loading, empty, 401/403, 409, 429, 500, timeout, offline, retry, partial batch failure.  
- Audit keyboard path: filters → table rows → bulk actions → drawer → save/close → focus restore.  
- Verify tablet viewport behavior for table overflow, drawer width, and action reachability.

**Acceptance conditions:**  
- Failed save is visible, recoverable, and does not falsely appear saved.  
- Dirty or saving drawer cannot be accidentally dismissed without protection.  
- All named failure states render actionable UI while preserving user context.  
- 10,000-row filtering remains responsive under representative data.  
- Only visible rows render, without breaking selection or keyboard navigation.  
- Icon-only controls have accessible names and visible focus.  
- Drawer focus behavior is deterministic.  
- Reduced-motion users still receive status feedback without large motion.  
- Tablet users can reach filters, rows, bulk actions, drawer actions, and autosave status.

**Rollback conditions:**  
- Virtualization breaks selection, row focus, screen-reader navigation, or bulk actions.  
- Error-state handling hides recoverable edits or causes duplicate saves.  
- Drawer focus trap blocks legitimate background workflow if the product requires non-modal editing.  
- Responsive changes make dense desktop scanning materially worse.  
- Motion changes obscure state transitions or violate reduced-motion behavior.
