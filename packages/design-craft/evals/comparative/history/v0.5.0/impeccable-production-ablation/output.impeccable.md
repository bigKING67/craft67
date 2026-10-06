## 1. Sequencing + verdict

**Correct sequence:** static audit → production hardening for save/error/state recovery → performance optimization for 10k-row workflows → responsive/accessibility fixes → visual/motion polish within the existing system → measured rollout with rollback gates.

**Verdict:** **Not production-ready for an operations-critical inventory editor**: the surface risks silent data loss, keyboard/a11y exclusion, tablet breakage, and severe interaction latency under the stated 10,000-row workload.

---

## 2. Prioritized findings: evidence vs runtime hypotheses

### P0 — Blocking

#### P0.1 Silent save failure can cause data loss
- **Source evidence:** `catch {}` swallows `api.save(product)` failures; `setSaving(false)` runs with no error, retry, rollback, or conflict state.
- **Runtime hypothesis:** severity depends on whether autosave/draft recovery exists elsewhere, but the shown save path is unsafe.
- **Impact:** operators may believe edits were saved when they were not.

#### P0.2 Drawer can close during pending save
- **Source evidence:** notes say Escape closes the drawer even while save is pending.
- **Runtime hypothesis:** data loss risk depends on whether pending edits are persisted elsewhere.
- **Impact:** easy accidental loss or ambiguous state during repeated keyboard use.

#### P0.3 No represented recovery paths for common production failures
- **Source evidence:** empty results, 401/403, 409, 429, 500, timeout, offline, retry, and partial batch failure states are not represented.
- **Runtime hypothesis:** backend may return these correctly, but the UI contract is missing.
- **Impact:** users cannot distinguish “no data,” “still loading,” “permission denied,” “conflict,” and “failed save.”

---

### P1 — Major before release

#### P1.1 10,000 rows render synchronously
- **Source evidence:** `{rows.map(...)}` renders all rows; notes confirm all 10,000 rows render at once.
- **Runtime hypothesis:** actual latency depends on row complexity, images, and browser/device, but this is a decisive hot-path risk.
- **Impact:** slow initial render, expensive updates, keyboard lag, poor tablet behavior.

#### P1.2 Filtering recalculates on every keystroke
- **Source evidence:** notes say filtering recalculates synchronously on every keystroke.
- **Runtime hypothesis:** exact cost depends on filter complexity, but 10,000 rows makes this a likely interaction blocker.
- **Impact:** users typing filters may experience jank, dropped input, or delayed results.

#### P1.3 Global `saving` state is too coarse
- **Source evidence:** single `const [saving, setSaving] = useState(false)` controls `EditDrawer`.
- **Runtime hypothesis:** if only one drawer save can happen at a time, global state may be acceptable for the drawer, but not for table autosave/bulk operations.
- **Impact:** one save can block or misrepresent unrelated product actions; partial batch failure is hard to model.

#### P1.4 Drawer lacks modal/dialog accessibility and background isolation
- **Source evidence:** notes say drawer traps neither focus nor background interaction.
- **Runtime hypothesis:** exact screen-reader behavior depends on markup not shown.
- **Impact:** keyboard and assistive-tech users can tab behind the drawer, lose context, or trigger background actions.

#### P1.5 Icon-only save/close controls are not described as labeled
- **Source evidence:** “Save and close are icon-only”; screen-reader labels are not described.
- **Runtime hypothesis:** `aria-label` may exist in omitted markup, but the note flags it as absent/undocumented.
- **Impact:** non-visual users cannot reliably identify destructive or committing actions.

#### P1.6 Focus visibility is explicitly suppressed
- **Source evidence:** `.icon-button { ... outline: none; }`
- **Runtime hypothesis:** if a replacement `:focus-visible` style exists elsewhere, this may be mitigated; none is shown.
- **Impact:** keyboard-heavy operators lose their position in a dense workflow.

#### P1.7 Touch targets are too small for tablet support
- **Source evidence:** `.icon-button { width: 28px; height: 28px; }`
- **Runtime hypothesis:** hit area could be enlarged by padding/wrapper elsewhere, but the class itself fails the expected target size.
- **Impact:** tablet users will mis-tap critical save/close controls.

#### P1.8 Fixed desktop width blocks tablet adaptation
- **Source evidence:** `.page { min-width: 1180px; }`; drawer fixed at `520px`.
- **Runtime hypothesis:** horizontal scrolling may be intentional for dense tables, but tablet behavior is undescribed.
- **Impact:** cramped or clipped controls, unusable drawer/table pairing on narrower viewports.

#### P1.9 `transition: all` on rows and drawer is unsafe
- **Source evidence:** `.product-row, .drawer { transition: all 300ms ease-in; }`
- **Runtime hypothesis:** actual animated properties depend on state classes, but the declaration permits layout/paint-heavy animation.
- **Impact:** jank on row updates, slow drawer motion, inaccessible motion without reduced-motion handling.

---

### P2 — Important hardening

#### P2.1 Blank table body during loading
- **Source evidence:** initial and filter loading render a blank table body.
- **Runtime hypothesis:** if surrounding chrome has status text, impact is reduced; not described.
- **Impact:** users cannot tell whether data is loading, filtered out, or broken.

#### P2.2 Hostile product data is under-modeled
- **Source evidence:** names can be 1–200 chars; prices may be missing; labels may expand 60%; images may be absent or 8MB.
- **Runtime hypothesis:** row components may already format some fields, but CSS suggests only single-line truncation for names.
- **Impact:** broken layout, hidden critical identifiers, misleading price display, image shift or slow loads.

#### P2.3 Image dimensions are not reserved
- **Source evidence:** notes say image dimensions are not reserved.
- **Runtime hypothesis:** actual CLS depends on image placement and table row height.
- **Impact:** table rows can jump during image load; repeated operations become error-prone.

#### P2.4 Permission-specific affordances are not described
- **Source evidence:** permission-specific affordances are absent from notes.
- **Runtime hypothesis:** route guards may exist elsewhere.
- **Impact:** users may see actions they cannot perform, or receive late 403 failures after effort.

---

### P3 — Polish once blockers are fixed

#### P3.1 Product names rely only on ellipsis
- **Source evidence:** `.product-name { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }`
- **Runtime hypothesis:** there may be a detail drawer or title attribute elsewhere.
- **Impact:** operators may lose distinguishing SKU/name details in dense rows.

#### P3.2 Motion timing/easing should be tuned for task UI
- **Source evidence:** `300ms ease-in` on rows/drawer.
- **Runtime hypothesis:** perceived speed depends on actual distance and hardware.
- **Impact:** state changes can feel sluggish; ease-in delays feedback at the start.

---

## 3. Concrete fixes

### Hostile data
- Preserve the existing table system, but make row cells resilient:
  - Use grid columns with `minmax()` and defined overflow behavior instead of brittle fixed widths everywhere.
  - Keep product names single-line by default, but expose full names through an accessible detail affordance, tooltip/popover, or drawer field.
  - Render missing prices as an explicit neutral state: `—`, “No price,” or permission-aware copy, not blank.
  - Support 60% label expansion by avoiding fixed-label buttons where text is expected.
  - Reserve image slots with fixed width/height or aspect ratio.
  - Use placeholders for absent images.
  - Reject or pre-process 8MB uploads with visible size/type guidance, upload progress, retry, and failure copy.

### Failure states
- Replace boolean-only loading/saving with explicit states:
  - `idle`, `initialLoading`, `filtering`, `saving`, `saved`, `error`, `offline`, `conflict`, `unauthorized`, `rateLimited`.
- Add distinct UI for:
  - empty inventory,
  - empty filter results,
  - 401/403 permission failure,
  - 409 conflict with reload/merge/discard choices,
  - 429 backoff message,
  - 500/timeout retry,
  - offline queued draft,
  - partial bulk failure with per-row outcomes.
- Never swallow errors. Surface a durable inline/banner/toast status and preserve unsaved edits.

### Responsive layout
- Remove or conditionally scope `min-width: 1180px`.
- For desktop, keep the dense table; for tablet:
  - allow horizontal table scroll inside a labeled region if density must remain,
  - keep key identifiers sticky,
  - make the drawer width responsive: `min(520px, 100vw)` or a tablet-specific full-width sheet,
  - ensure the drawer does not cover required table actions without an obvious close/back path.
- Define breakpoint behavior for filters, bulk bar, table, and drawer together; do not only shrink columns.

### Accessibility
- Use real buttons for icon actions with accessible names: “Save product,” “Close editor,” “Remove image,” etc.
- Restore visible keyboard focus with `:focus-visible`; do not rely on browser outline removal.
- Increase interactive hit areas to at least 44×44 CSS px for tablet/touch.
- Treat the drawer as a dialog-like surface:
  - focus moves into it on open,
  - focus is contained while open,
  - background is inert or otherwise non-interactive,
  - focus returns to the invoking row/control on close.
- Disable or confirm close/Escape while save is pending.
- Announce autosave status changes through a polite live region.
- Provide keyboard paths for filters, table rows, bulk selection, drawer save/cancel, and image upload.
- Add reduced-motion handling for drawer/row transitions.

### State recovery
- Track dirty state per product, not only global saving.
- Maintain local draft state until save confirmation.
- Add retry with idempotency where backend supports it.
- For conflicts, show what changed and let the user reload, overwrite, or merge.
- For batch operations, report successful, failed, skipped, and pending rows separately.
- Preserve filter, selection, scroll position, and open drawer context across recoverable failures.

### Performance
- Virtualize/window the 10,000-row table using existing project patterns where available.
- Memoize filtered/sorted rows with correct dependencies.
- Debounce or defer filter input work so typing remains responsive.
- Avoid re-rendering every row when `saving` changes; scope save state to the edited product/drawer.
- Keep row components stable with memoized props/callbacks where appropriate.
- Lazy-load thumbnails and reserve dimensions.
- Replace `transition: all` with specific properties, typically `transform`, `opacity`, or color only.
- Add reduced-motion CSS:
  - disable drawer slide/row transitions or shorten to near-instant,
  - preserve state feedback through copy/icon/status changes.

---

## 4. Static detector-like signals: decisive vs context-dependent

### Decisive from the provided source
- `catch {}` with no user-visible error path is unsafe.
- Rendering `{rows.map(...)}` for 10,000 rows is a decisive scalability smell.
- Synchronous filtering on every keystroke is a hot-path risk.
- `outline: none` on icon buttons is an accessibility failure unless replaced elsewhere.
- 28×28 icon buttons are too small for tablet touch targets.
- `transition: all` on rows/drawer is an unsafe motion/performance pattern.
- Fixed `min-width: 1180px` conflicts with stated tablet support.
- Blank loading, absent error states, absent conflict/offline/retry/partial failure states are production hardening gaps.
- Missing drawer focus trap/background isolation is a major modal interaction gap.

### Needs project/runtime context before final severity
- Whether `ProductRow` is memoized or internally expensive.
- Whether the real table has semantic roles, headers, row selection labels, and keyboard behavior.
- Whether design tokens already provide focus rings, motion durations, z-index, and responsive primitives.
- Whether route-level auth/permissions already prevent some 401/403 paths.
- Whether upload processing compresses/rejects 8MB images before rendering.
- Whether autosave has draft persistence outside the shown snippet.
- Exact latency, memory, layout shift, and interaction delay numbers.

---

## 5. Measurement-first validation plan with rollback and acceptance

### Baseline before changes
- Create representative fixtures:
  - 10,000 rows,
  - 200-character names,
  - missing prices,
  - 60% longer labels,
  - absent images,
  - 8MB image cases,
  - 401/403/409/429/500/timeout/offline responses,
  - partial bulk failure.
- Measure initial render, filter keystroke latency, drawer open/close latency, save feedback timing, image layout shift, and row count in the DOM.
- Record keyboard-only task completion for: filter, select bulk rows, open drawer, edit, save, upload image, recover from failed save.

### Acceptance conditions
- No failed save can appear as successful.
- Pending save cannot be lost through Escape/close without an explicit safe outcome.
- 10,000-row route remains responsive during filtering and selection.
- DOM row count is bounded by windowing rather than all 10,000 visible rows.
- Filtering does not block typing perceptibly under the target dataset.
- Drawer focus is contained, background is non-interactive, and focus returns correctly.
- All icon-only controls have accessible names and visible focus.
- Touch targets meet tablet requirements.
- Loading, empty, forbidden, conflict, rate-limit, timeout, offline, retry, and partial failure states are visible and actionable.
- Images reserve space; table layout does not jump during thumbnail loading.
- Reduced-motion users still receive clear state feedback.

### Rollback conditions
- Filter latency or drawer latency regresses beyond agreed baseline.
- Virtualization breaks row selection, keyboard navigation, or scroll restoration.
- Autosave changes increase failed/duplicate saves.
- Conflict handling blocks normal saves or loses drafts.
- Responsive drawer/table changes hide critical bulk or save actions.
- Accessibility fixes trap users, lose focus return, or block assistive-tech navigation.

### Rollout approach
- Ship hardening behind narrow flags where practical: save-state recovery, virtualization, responsive drawer behavior.
- Roll out first to internal/staff accounts with production-like data volume.
- Monitor save failures, retry counts, conflict rates, upload failures, and client-side error reports.
- Keep a one-step fallback for table virtualization and drawer behavior until metrics and support feedback are stable.
