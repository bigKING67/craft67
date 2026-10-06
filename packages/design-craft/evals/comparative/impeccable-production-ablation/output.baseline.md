## 1. Sequencing + verdict

**Correct sequence:** stabilize correctness and recovery first → harden failure/permission states → fix accessibility blockers → optimize the 10,000-row hot path → polish responsive/tablet layout and visual states → measure before and after each change.

**One-line verdict:** the current surface has production-blocking reliability, accessibility, and performance risks; it should be hardened in-place before further visual polish, without changing the design system or introducing a new interaction model.

---

## 2. Prioritized findings

### P0 — Must fix before production confidence

#### P0.1 Save failures are swallowed; users can lose trust/data
**Source evidence**
```tsx
try {
  await api.save(product);
} catch {}
setSaving(false);
```
- Errors are ignored.
- No retry, recovery, conflict handling, or user-visible failure state.
- Additional notes confirm 401/403, 409, 429, 500, timeout, offline, retry, and partial batch failure states are absent.

**Runtime hypothesis**
- Actual loss depends on API semantics, autosave timing, and whether upstream persists drafts, but the UI currently gives no reliable recovery path.

**Concrete fix**
- Return a typed save result: success, validation error, conflict, permission denied, rate limited, server error, timeout/offline.
- Surface inline drawer errors and row-level/batch-level save status.
- Preserve dirty values after failure.
- Add retry where safe; for 409, show conflict resolution or “reload latest / keep mine” flow.
- Do not silently clear pending state until the UI has a recoverable terminal state.

---

#### P0.2 Drawer interaction can corrupt or interrupt pending saves
**Source evidence**
- Drawer does not trap focus or block background interaction.
- Escape closes it even while save is pending.
- Save and close are icon-only.

**Runtime hypothesis**
- Severity depends on whether pending saves are cancellable/idempotent, but current behavior allows accidental close during a critical operation.

**Concrete fix**
- While saving: disable destructive close, or require confirmation if dirty/pending.
- Trap focus inside drawer when open.
- Restore focus to the invoking row/control on close.
- Prevent background row/table interaction while modal drawer is active, unless it is intentionally non-modal and designed as such.
- Add explicit labels: `aria-label="Save product"`, `aria-label="Close editor"`, visible tooltip/help text if already part of the system.

---

#### P0.3 10,000 rows render at once; synchronous filtering on every keystroke
**Source evidence**
```tsx
{rows.map((row) => <ProductRow key={row.id} row={row} />)}
```
- All rows render at once.
- Notes state filtering recalculates synchronously on every keystroke.

**Runtime hypothesis**
- Exact frame drops depend on row complexity, image loading, hardware, and table wrappers, but 10,000 full DOM rows is a decisive hot-path risk for desktop and worse for tablet.

**Concrete fix**
- Virtualize/window visible rows while preserving keyboard navigation and selection semantics.
- Memoize filtered/sorted data with correct dependencies.
- Debounce or defer filter input computation so typing remains responsive.
- Avoid recreating row callbacks/objects unnecessarily.
- Keep selection state independent from rendered-window state.
- Ensure bulk selection semantics distinguish “selected visible rows” vs “selected all matching filter.”

---

### P1 — High priority production hardening

#### P1.1 Blank loading states make the table appear broken
**Source evidence**
- Initial and filter loading render a blank table body.

**Concrete fix**
- Add table skeleton/loading rows or a clear loading state.
- Preserve previous results during filter refresh where appropriate, with “updating…” status.
- Add empty result copy with next action: clear filters, broaden search, or create/import if permitted.

---

#### P1.2 Missing error-state taxonomy for operational workflows
**Source evidence**
- Empty results, 401/403, 409, 429, 500, timeout, offline, retry, and partial batch failure states are not represented.

**Concrete fix**
- 401: session expired; prompt re-authentication.
- 403: permission-specific disabled controls and explanatory copy.
- 409: conflict banner/drawer state with recovery.
- 429: rate-limited state with retry-after messaging if available.
- 500/timeout/offline: retry + preserve unsaved edits.
- Partial batch failure: per-row result summary, export/copy failed IDs, retry failed only.

---

#### P1.3 Accessibility blockers in controls and focus states
**Source evidence**
```css
.icon-button { width: 28px; height: 28px; outline: none; }
```
- Save/close are icon-only.
- Keyboard navigation, screen-reader labels, focus-visible are not described.

**Concrete fix**
- Replace `outline: none` with `:focus-visible` styling consistent with the design system.
- Ensure icon buttons have accessible names.
- Increase hit area to at least the system’s accessible target size; if visual size remains 28px, add padding/invisible hit area.
- Ensure row actions are keyboard reachable in logical order.
- Announce autosave status through a polite live region.
- For errors, focus the first actionable error or summary after failed save.

---

#### P1.4 Motion and transition choices are risky
**Source evidence**
```css
.product-row, .drawer { transition: all 300ms ease-in; }
```

**Concrete fix**
- Do not transition `all`; restrict to transform/opacity/color where intentional.
- Avoid animating layout-affecting properties on rows.
- Add reduced-motion handling:
```css
@media (prefers-reduced-motion: reduce) {
  .product-row,
  .drawer {
    transition: none;
  }
}
```

---

#### P1.5 Tablet support conflicts with fixed minimum page width
**Source evidence**
```css
.page { min-width: 1180px; }
```
- Product context requires tablet support.

**Runtime hypothesis**
- A horizontal table may be intentional, but fixed min-width without described overflow, sticky controls, or drawer behavior is likely poor on tablets.

**Concrete fix**
- Preserve desktop table layout, but define tablet behavior explicitly:
  - controlled horizontal scroll region for table, not whole page;
  - sticky key columns/actions if already supported by the system;
  - drawer width via `min(520px, 100vw)` or tablet-specific layout;
  - filters wrap/collapse predictably;
  - no content hidden behind the fixed drawer.

---

### P2 — Important polish and hostile-data resilience

#### P2.1 Product names, translations, and missing values can break layout
**Source evidence**
```css
.product-name { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
```
- Names can be 1–200 characters.
- Translations may expand labels by 60%.
- Prices may be missing.

**Concrete fix**
- Keep ellipsis in dense rows, but provide full name access via title/tooltip/details pattern already used by the system.
- Ensure columns tolerate long localized labels.
- Use stable missing-price display: em dash, “Not set”, or validation state depending on business meaning.
- Do not rely on color alone for missing/invalid values.

---

#### P2.2 Image handling can cause layout shift and slow interactions
**Source evidence**
- Some images are absent or 8MB.
- Image dimensions are not reserved.

**Concrete fix**
- Reserve image dimensions/aspect ratio in rows and drawer.
- Use placeholder/fallback for absent images.
- Validate file size/type before upload.
- Show upload progress, failure, retry, and remove/replace states.
- Avoid loading full-size images in table rows; use thumbnails where available.

---

#### P2.3 Global `saving` state is too coarse for row/drawer/bulk workflows
**Source evidence**
```tsx
const [saving, setSaving] = useState(false);
<EditDrawer onSave={saveProduct} saving={saving} />
```

**Runtime hypothesis**
- If only one drawer save can happen at a time, global state may be acceptable, but it is insufficient for bulk save and row-specific status.

**Concrete fix**
- Track save state by operation and product ID where needed:
  - drawer save pending;
  - row autosave pending/saved/error;
  - bulk operation pending/partial/success/error.
- Prevent stale responses from overwriting newer edits.
- Include request IDs or updated-at/version checks.

---

### P3 — Lower priority refinements

#### P3.1 Row grid may be too rigid for variable content
**Source evidence**
```css
.product-row {
  display: grid;
  grid-template-columns: 64px 280px 1fr 120px 96px;
}
```

**Concrete fix**
- Keep the existing grid model, but review min/max behavior:
  - use `minmax(0, 1fr)` for flexible text columns;
  - ensure action columns do not collapse;
  - align numeric columns consistently;
  - test longest names, missing prices, absent images, and localized labels.

---

#### P3.2 Autosave status needs clearer user feedback
**Source evidence**
- Autosave status exists in product context, but source only shows a single `saving` flag and no failure representation.

**Concrete fix**
- Show status lifecycle: unsaved changes → saving → saved timestamp → failed/retry.
- Avoid permanent spinners.
- Make status perceivable to assistive tech without being noisy.

---

## 3. Concrete hardening plan by area

### Hostile data
- Long names: truncate in table, expose full value accessibly.
- Missing prices: explicit placeholder and validation state.
- Expanded translations: avoid fixed-label assumptions; allow wrapping where labels are not tabular data.
- Missing images: stable fallback thumbnail.
- 8MB images: validate, compress/server-transform if available, show progress and recoverable failure.

### Failures
- Add explicit UI states for loading, empty, permission denied, conflict, rate limit, server error, timeout, offline, retry, and partial batch failure.
- Keep user edits in memory after failure.
- Log/report errors through existing app mechanisms, but do not expose raw technical messages to operators.
- Make retry idempotent or clearly scoped.

### Responsive layout
- Replace whole-page fixed-width behavior with bounded table overflow.
- Use `width: min(520px, 100vw)` or equivalent for drawer.
- Ensure tablet filter controls wrap without covering table actions.
- Keep bulk actions visible when rows are selected.
- Verify no drawer/table overlap hides primary actions.

### Accessibility
- Add accessible names to icon-only controls.
- Restore visible focus states with `:focus-visible`.
- Trap drawer focus and restore focus on close.
- Block or manage background interaction while drawer is active.
- Prevent accidental close during pending save or dirty state.
- Add reduced-motion handling.
- Provide keyboard path for filters, row selection, bulk actions, drawer fields, save, and close.
- Announce save/error status with appropriate live-region behavior.

### State recovery
- Do not swallow save errors.
- Preserve dirty form state and failed row IDs.
- Distinguish local edits, in-flight saves, confirmed saves, conflicts, and failed saves.
- Add stale-response protection.
- Support retry failed-only for batch operations.
- Confirm destructive close with unsaved changes.

### Performance
- Window/virtualize the 10,000-row table.
- Memoize filtered rows.
- Debounce/defer filter computation.
- Avoid transitioning `all`.
- Reserve image dimensions.
- Lazy-load thumbnails outside the initial viewport if compatible with virtualization.
- Keep row components memoized where props are stable.
- Avoid deriving selection state by scanning 10,000 rows on every render; use sets/maps and derived counts.

---

## 4. Static signal reconciliation

### Decisive static signals
These are strong enough to act on without runtime proof:

- `catch {}` around save: user-visible failure handling is missing.
- `rows.map(...)` for all rows: no visible windowing for 10,000 rows.
- `transition: all`: unsafe for performance and unintended animation.
- `outline: none`: focus visibility risk.
- Fixed `.page { min-width: 1180px; }` conflicts with stated tablet support unless explicitly contained.
- Drawer lacks focus trap/background management per notes.
- Escape closes during pending save per notes.
- Blank loading and missing error states per notes.
- Image dimensions not reserved per notes.

### Needs project/runtime context
These should be verified against actual app behavior before final severity/implementation choice:

- Whether the table already sits inside a controlled horizontal scroller.
- Whether global `saving` is acceptable because only one save can ever occur.
- Whether server-side filtering/pagination exists outside the shown snippet.
- Whether API saves are idempotent, cancellable, versioned, or conflict-aware.
- Whether existing design-system components already provide tooltips, dialogs, live regions, and upload states.
- Whether 8MB image handling is client-only, server-transformed, or CDN-backed.
- Whether permission-specific affordances are controlled elsewhere in the route.

---

## 5. Measurement-first validation plan

No production hardening should be accepted only by code inspection. Validate in small changes with rollback points.

### Baseline to capture before changes
- Initial table render time with 10,000 rows.
- Typing latency while filtering.
- Long task count during filter input.
- Memory footprint after loading table and opening drawer.
- Save success/failure behavior for success, 409, 429, 500, timeout, and offline simulations.
- Keyboard-only completion path: filter → select row → edit → save → close.
- Tablet viewport layout screenshots/recordings.
- Image layout shift with absent image and large image cases.

### Acceptance conditions
- Filtering remains responsive under the expected 10,000-row dataset.
- Initial and filter loading never show an unexplained blank body.
- Save failures are visible, recoverable, and preserve edits.
- Conflict and partial batch failures identify affected products.
- Drawer focus is contained while open and restored on close.
- Escape/close cannot discard pending or dirty work without protection.
- All icon-only actions have accessible names.
- Focus states are visible for keyboard users.
- Reduced-motion users do not receive unnecessary transitions.
- Tablet layout has no hidden primary actions or unusable horizontal page scroll.
- Image placeholders reserve space and avoid visible layout jumps.
- Bulk selection remains correct with filtering and virtualization.

### Rollback conditions
- Virtualization breaks selection, row keyboard navigation, or screen-reader semantics.
- Filter optimization returns stale or incorrect results.
- New save-state handling blocks legitimate workflows or causes duplicate saves.
- Drawer focus management prevents access to required non-drawer controls when the intended pattern is non-modal.
- Responsive changes disrupt the established desktop workflow.
- Error handling exposes sensitive backend details or creates noisy false failures.

### Recommended rollout order
1. Save/error recovery and drawer close protection.
2. Loading/empty/error/permission states.
3. Accessibility fixes for labels, focus, drawer behavior, and reduced motion.
4. Table performance: memoized filtering, deferred input, virtualization/windowing.
5. Image dimension reservation and upload failure states.
6. Tablet layout containment and final visual polish.

This keeps the current workflow intact while addressing the highest production risks first.
