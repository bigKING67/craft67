## 1. Sequencing + verdict

**Correct sequence:** audit evidence boundaries → harden save/error/state recovery → fix accessibility and permissions → optimize table/filter/image hot paths → tablet/responsive adjustments → motion/visual polish.

**One-line verdict:** This surface has enough static evidence of production risk that polish should wait until save failure handling, drawer accessibility, failure states, and 10,000-row rendering are hardened and measured.

---

## 2. Prioritized findings

### P0 — Silent save failure can create false confidence and unrecoverable edits

**Source evidence**
- `catch {}` swallows save errors.
- `saving` is reset without representing failure, retry, conflict, offline, timeout, or partial success.
- Additional notes explicitly say 401/403, 409, 429, 500, timeout, offline, retry, and partial batch failure states are not represented.

**Runtime hypothesis**
- Operators may believe a product was saved when it was not.
- Last-write-wins or conflict overwrites may happen if 409 handling is absent.
- Pending local edits may be lost if the drawer closes, route changes, or auth expires.

**Fix**
- Replace silent catch with explicit save state: `idle | saving | saved | failed | conflict | offline | unauthorized | rateLimited`.
- Preserve dirty draft after failure.
- Block destructive close while save is pending or require confirmation.
- Surface retry with stable error copy.
- For 409, show conflict resolution: keep mine, reload server value, or compare changed fields.
- For partial batch failure, report affected count and failed row IDs.

---

### P0 — Drawer interaction is unsafe and inaccessible

**Source evidence**
- Drawer traps neither focus nor background interaction.
- Escape closes it even while save is pending.
- Save and close are icon-only.
- `.icon-button { width: 28px; height: 28px; outline: none; }`

**Runtime hypothesis**
- Keyboard users can tab behind the drawer and activate background controls.
- Screen-reader users may not know the drawer opened or what icon-only controls do.
- Operators can accidentally dismiss the drawer during a pending save.

**Fix**
- Treat drawer as a modal or clearly non-modal panel; if modal, add focus trap, initial focus, return focus, inert/background blocking, and Escape behavior rules.
- Disable or confirm close while save is pending.
- Add accessible names to icon-only save/close controls.
- Restore visible focus using `:focus-visible`, not `outline: none`.
- Increase hit target to at least a comfortable operations size; 28px is too small for repeated desktop/tablet use.

---

### P0 — Blank loading and missing failure states obscure system status

**Source evidence**
- Initial and filter loading render a blank table body.
- Empty, auth, conflict, rate-limit, server error, timeout, offline, retry, and partial failure states are not represented.

**Runtime hypothesis**
- Operators cannot distinguish “loading,” “no results,” “not allowed,” “offline,” and “broken.”
- Filter changes may appear to delete rows temporarily.

**Fix**
- Add distinct table-body states:
  - initial loading skeleton or progress row,
  - filtering/loading state that preserves previous results when safe,
  - empty results with active filter summary,
  - unauthorized/forbidden state with permission-specific explanation,
  - retryable network/server state,
  - conflict state,
  - offline state,
  - partial batch result state.
- Keep table headers and layout stable while body state changes.

---

### P1 — Rendering all 10,000 rows and filtering on every keystroke is a hot-path risk

**Source evidence**
- `{rows.map(...)}`
- All 10,000 rows render at once.
- Filtering recalculates synchronously on every keystroke.
- Route includes bulk selection and edit drawer, which likely increase row interaction cost.

**Runtime hypothesis**
- Keystrokes may block the main thread.
- Bulk selection may trigger large re-renders.
- Drawer edits may cause unrelated rows to re-render if state is broad.
- Tablet support may be especially sensitive.

**Fix**
- Virtualize or window the table body while preserving keyboard navigation and selection semantics.
- Debounce or defer filter computation.
- Memoize derived filtered rows with correct dependencies.
- Keep selection state normalized by row ID.
- Memoize row components where useful.
- Avoid passing unstable object/function props into every row.
- Keep autosave state scoped to the edited product rather than global `saving` if multiple row/drawer states can coexist.

---

### P1 — Global `saving` state is too coarse for product-level editing

**Source evidence**
- `const [saving, setSaving] = useState(false);`
- `EditDrawer onSave={saveProduct} saving={saving}`

**Runtime hypothesis**
- One product save can disable or misrepresent unrelated actions.
- Concurrent saves, autosave, or retry behavior may become ambiguous.
- Save status may not map to the edited product after selection changes.

**Fix**
- Track save status per draft/product ID.
- Bind drawer state to a stable selected product ID and draft version.
- Ignore stale save responses if the drawer has moved to another product.
- Use request IDs or abort signals for superseded saves.

---

### P1 — Permission-specific affordances are missing

**Source evidence**
- Permission-specific affordances are not described.
- 401/403 states are not represented.

**Runtime hypothesis**
- Users may see controls they cannot use.
- Failed save attempts may be mistaken for product errors instead of access limits.

**Fix**
- Disable or hide restricted actions according to product policy.
- Explain why an action is unavailable.
- Use 401 for session recovery and 403 for permission explanation.
- Prevent bulk actions from starting if selected rows include unauthorized items, or clearly split allowed/blocked results.

---

### P2 — Hostile product data can break layout and comprehension

**Source evidence**
- Product names may be 1–200 characters.
- Prices may be missing.
- Translations may expand labels by 60%.
- Some images are absent or 8MB.
- `.product-name { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }`
- Fixed row grid: `64px 280px 1fr 120px 96px`.

**Runtime hypothesis**
- Important product distinctions may be hidden by truncation.
- Missing prices may look like loading or zero.
- Expanded translations may collide with fixed columns.
- Large images may delay interaction or cause memory/network pressure.

**Fix**
- Keep truncation but provide accessible full-name disclosure where appropriate.
- Use stable missing-value treatments such as “Not set” or an em dash with accessible label.
- Reserve image dimensions and show absent-image placeholders.
- Validate/upload-compress 8MB images with progress and recoverable errors.
- Test long names, missing fields, long localized labels, and dense numeric values in the existing table layout.
- Allow critical columns to shrink/wrap according to priority instead of relying only on fixed widths.

---

### P2 — Tablet support is contradicted by fixed minimum width

**Source evidence**
- `.page { min-width: 1180px; }`
- Desktop-first with tablet support is required.

**Runtime hypothesis**
- Tablets may require horizontal scrolling or clipped drawer/table content.
- Fixed 520px drawer may dominate smaller tablet widths.

**Fix**
- Keep desktop layout intact, but define tablet behavior:
  - table horizontal scroll with sticky key columns, or
  - reduced column set with details in drawer, or
  - drawer width using `min()`, `max()`, and viewport constraints.
- Ensure filters, bulk actions, and drawer controls remain reachable at tablet widths.
- Do not introduce a new mobile workflow unless required; this is tablet accommodation, not redesign.

---

### P2 — Motion is broad, potentially expensive, and ignores reduced motion

**Source evidence**
- `.product-row, .drawer { transition: all 300ms ease-in; }`
- Reduced motion is not described.

**Runtime hypothesis**
- `transition: all` may animate layout-affecting properties.
- Row transitions across thousands of elements may add jank.
- Motion may be uncomfortable or misleading for users with reduced-motion preferences.

**Fix**
- Replace `transition: all` with explicit properties, preferably `transform` and `opacity` for drawer movement.
- Avoid transitions on every row by default.
- Add `prefers-reduced-motion` handling that preserves state feedback without unnecessary movement.
- Use faster, calmer easing for operations work; avoid sluggish ease-in on frequent interactions.

---

### P2 — Image dimensions are not reserved

**Source evidence**
- Image dimensions are not reserved.
- Some images are absent or 8MB.

**Runtime hypothesis**
- Rows may shift as images load.
- Large assets may harm initial render, scrolling, and memory.

**Fix**
- Reserve fixed image slots in the row grid.
- Add placeholders and broken-image fallback.
- Use thumbnail URLs for table rows.
- Lazy-load offscreen images if compatible with virtualization.
- Validate upload size/type and show upload progress/error states.

---

### P3 — Visual polish should focus on clarity, not redesign

**Source evidence**
- Existing design system and workflow must be preserved.
- Production hardening/polish task, not redesign or new dependency pitch.

**Runtime hypothesis**
- Adding decorative treatment before state/performance fixes could hide real production problems.

**Fix**
- Preserve current layout and component vocabulary.
- Improve hierarchy through spacing, labels, stable status placement, and clear disabled/error states.
- Keep autosave feedback close to the edited object.
- Avoid decorative gradients, new card systems, or broad visual resets.

---

## 3. Concrete fixes by area

### Hostile data
- Long names: stable truncation, accessible full value, no row-height explosions.
- Missing prices: explicit missing state, not blank or zero.
- Expanded translations: test 60% longer labels in filters, drawer actions, bulk toolbar, and table headers.
- Absent images: reserved placeholder.
- 8MB images: upload validation, compression/resizing path, progress, retry, and failure copy.
- Unknown/malformed fields: safe fallback rendering and logging hooks.

### Failures
- Represent 401, 403, 409, 429, 500, timeout, offline, and partial batch failure distinctly.
- Never swallow save errors.
- Preserve user edits after failed save.
- Provide retry where safe.
- Use conflict-specific recovery instead of generic “failed.”
- Keep previous table results visible during filter refetch unless stale visibility is unsafe.

### Responsive layout
- Replace fixed-only `min-width: 1180px` with a defined tablet strategy.
- Constrain drawer width to viewport.
- Ensure filters and bulk controls do not overflow.
- Preserve table readability with sticky identifiers or controlled horizontal scroll.
- Validate pointer target sizes for tablet use.

### Accessibility
- Drawer: role/name, focus trap if modal, initial focus, return focus, background inertness.
- Icon buttons: accessible names and visible focus.
- Keyboard: row navigation, selection, drawer open/close, save/cancel, filter traversal.
- Status: autosave and error messages announced without stealing focus.
- Motion: reduced-motion mode.
- Contrast and focus-visible states must be preserved by the design system.

### State recovery
- Draft state survives save failure, auth refresh, retry, and drawer accidental close attempts.
- Save requests are tied to product ID and draft version.
- Stale responses cannot overwrite newer edits.
- Pending uploads survive transient network failure where feasible.
- Bulk operations report exact successes/failures.

### Performance
- Window 10,000-row rendering.
- Defer/debounce filter work.
- Memoize derived rows.
- Normalize row and selection state.
- Reserve image dimensions and use thumbnails.
- Avoid broad state updates that re-render every row.
- Limit animation to the drawer and targeted state changes.

---

## 4. Static detector-like signals: decisive vs context-dependent

### Decisive from the provided source
- Empty `catch {}` is a production hardening failure.
- Blank table body for loading is an insufficient state model.
- Missing explicit error/empty/auth/conflict/rate-limit/offline states is a production gap.
- `outline: none` without replacement focus styling is an accessibility risk.
- Icon-only save/close without described labels is an accessibility risk.
- No drawer focus trap/background blocking is unsafe if the drawer functions as a modal editor.
- `transition: all` is too broad for predictable production motion.
- Rendering all 10,000 rows at once is a known performance risk.
- Synchronous filtering on each keystroke is a hot-path risk.
- Fixed `min-width: 1180px` conflicts with tablet support unless a separate tablet strategy exists.

### Needs project/runtime context
- Exact frame drops, input latency, memory use, and scroll performance.
- Whether `ProductRow` is lightweight enough to delay virtualization urgency.
- Whether the drawer is intended to be modal or non-modal.
- Whether accessible names exist deeper inside reusable components.
- Actual focus order and screen-reader announcements.
- Whether API already performs conflict detection, retries, or idempotency.
- Whether images are already served as thumbnails by infrastructure.
- Actual tablet breakpoints, supported devices, and operator hardware.
- Whether permissions are encoded in product data, session data, or route guards.

---

## 5. Measurement-first validation plan with rollback/acceptance

### Baseline before changes
- Record current 10,000-row initial render time, filter keystroke latency, scroll smoothness, memory, and image load behavior.
- Record save flows for success, failure, timeout, offline, 401/403, 409, 429, and 500 using controlled responses.
- Record keyboard path through filters, table, bulk selection, drawer, save, cancel, and close.
- Record tablet-width layout behavior.
- Record reduced-motion behavior.

### Acceptance conditions
- Save failures are visible, recoverable, and never reported as success.
- Dirty edits are preserved across retryable failures.
- Conflict handling prevents silent overwrite.
- Drawer focus behavior is deterministic and keyboard-safe.
- Icon-only controls have accessible names and visible focus.
- Loading, empty, auth, offline, server error, rate-limit, timeout, conflict, and partial batch states are represented.
- 10,000-row table remains responsive during scroll and filtering within agreed product latency budgets.
- Image slots do not cause layout shift.
- Tablet layout keeps primary actions reachable.
- Reduced-motion mode removes nonessential movement while preserving status feedback.

### Rollback conditions
- Virtualization breaks selection, keyboard navigation, or screen-reader access.
- Save-state changes introduce duplicate saves or stale overwrites.
- Drawer focus management traps users or blocks required background workflow.
- Tablet changes degrade the primary desktop workflow.
- Image handling blocks valid uploads without clear recovery.
- Error-state handling hides actionable product data.

### Rollout approach
- Ship save/error-state hardening first behind the existing workflow.
- Then add drawer accessibility and close-pending safeguards.
- Then optimize rendering/filtering with measured before/after results.
- Then handle tablet and hostile-data polish.
- Keep changes reversible and avoid new dependencies unless measurement proves the existing stack cannot meet the target.
