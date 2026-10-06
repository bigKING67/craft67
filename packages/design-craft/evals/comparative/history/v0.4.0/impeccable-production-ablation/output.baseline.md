## 1. Sequencing and verdict

**Correct sequence:** audit static risks → harden correctness, failure, recovery, and accessibility blockers → optimize measured hot paths → polish within the existing design system.

**One-line verdict:** This surface is not production-hardened for a 10,000-row operations workflow yet; the highest risks are silent save failure/data loss, missing recovery states, inaccessible drawer/actions, and unbounded rendering/filtering.

---

## 2. Prioritized findings: source evidence vs runtime hypotheses

### P0 — Silent save failure and unsafe pending-save behavior

**Source evidence**

```tsx
try {
  await api.save(product);
} catch {}
setSaving(false);
```

- Save errors are swallowed.
- No user-visible failed-save state.
- No retry path.
- `saving` is a single global boolean, not scoped to product, drawer, or request.
- Drawer can close via Escape while save is pending.
- 409 conflict, timeout, offline, 429, 500, and partial batch failures are explicitly not represented.

**Runtime hypotheses needing validation**

- Users may believe failed edits were saved.
- Concurrent saves may show misleading global “saving” state.
- Closing during pending save may lose local edits or hide a failed request.

**Fixes**

- Replace empty `catch {}` with explicit error classification and visible status.
- Keep local draft state until server acknowledgement.
- Prevent destructive close while save is pending, or require confirmation.
- Add retry for transient failures; do not auto-retry conflicts without user review.
- Add per-row/per-drawer save state rather than one global `saving`.
- For 409, show conflict copy with options such as reload server value, keep local draft, or review differences.
- For partial batch failure, report successful count, failed count, and failed item list.

---

### P0 — Drawer accessibility and interaction safety gaps

**Source evidence**

- Drawer traps neither focus nor background interaction.
- Escape closes it even while save is pending.
- Save and close are icon-only.
- `.icon-button { width: 28px; height: 28px; outline: none; }`

**Runtime hypotheses needing validation**

- Keyboard users may tab into background content while editing.
- Screen-reader users may not know what icon-only buttons do.
- Users may accidentally dismiss work in progress.

**Fixes**

- Use existing modal/drawer pattern if available.
- Add focus trap while drawer is open.
- Restore focus to the invoking control on close.
- Mark background content inert or otherwise prevent interaction while drawer is active.
- Add accessible names to icon-only controls.
- Do not remove visible focus indication; use `:focus-visible` styling aligned to the design system.
- Disable Escape close during active save or intercept it with a clear confirmation.
- Ensure close action communicates unsaved or pending-save consequences.

---

### P1 — Missing operational states and recovery paths

**Source evidence**

- Initial and filter loading render a blank table body.
- Empty results, 401/403, 409, 429, 500, timeout, offline, retry, and partial batch failure states are not represented.

**Runtime hypotheses needing validation**

- Blank table may be interpreted as no products.
- Operations staff may repeatedly retry, refresh, or duplicate edits.
- Permission errors may appear as broken UI instead of intentional access control.

**Fixes**

- Add distinct states:
  - Initial loading skeleton or table placeholder.
  - Filter loading/progress state that preserves previous results where safe.
  - Empty results with clear “no products match these filters” copy.
  - 401/403 permission state with role-appropriate copy and disabled affordances.
  - 409 conflict state with recovery action.
  - 429 rate-limit state with retry-after handling when available.
  - 500/timeout/offline state with retry and preserved draft.
  - Partial batch failure summary.
- Avoid collapsing all failures into one generic message.
- Keep user-entered edits recoverable after transient failures.

---

### P1 — 10,000 rows render at once and filtering is synchronous per keystroke

**Source evidence**

```tsx
{rows.map((row) => <ProductRow key={row.id} row={row} />)}
```

Additional note:

- All 10,000 rows render at once.
- Filtering recalculates synchronously on every keystroke.

**Runtime hypotheses needing validation**

- First render, filter input, bulk selection, and drawer open/close may jank.
- Memory usage may spike with image-heavy rows.
- Autosave status updates may re-render too much of the table.

**Fixes**

- Virtualize the table body or paginate/chunk rows using existing project patterns.
- Memoize derived filtered rows with correct dependencies.
- Debounce or defer filter input work without making typing feel stale.
- Memoize `ProductRow` where row props are stable.
- Avoid global state changes that re-render all rows for drawer-only saves.
- Keep selection state efficient, especially for “select all filtered” behavior.
- Measure before/after against 10,000 rows.

---

### P1 — Images can cause layout shift and upload failure ambiguity

**Source evidence**

- Image dimensions are not reserved.
- Some images are absent or 8MB.
- Image uploads are part of the route.

**Runtime hypotheses needing validation**

- Rows may shift as images load.
- Large uploads may fail slowly or block save flows.
- Missing images may render broken or uneven rows.

**Fixes**

- Reserve image dimensions or aspect-ratio boxes in rows and drawer previews.
- Provide a consistent missing-image placeholder.
- Validate upload size/type before upload.
- Show upload progress and failure reason.
- Keep product text/edit data separate from image upload failure where possible.
- Support retry/replacement for failed image upload.
- Avoid decoding/rendering full 8MB images in table rows; use thumbnails where supported.

---

### P1 — Tablet support conflicts with fixed desktop width

**Source evidence**

```css
.page { min-width: 1180px; }
.drawer { position: fixed; right: 0; width: 520px; height: 100vh; }
.product-row {
  display: grid;
  grid-template-columns: 64px 280px 1fr 120px 96px;
}
```

**Runtime hypotheses needing validation**

- Tablet users may get horizontal scrolling or clipped drawer/content.
- Fixed drawer width may consume too much of the viewport.
- Grid columns may not fit translated labels or dense data.

**Fixes**

- Preserve desktop layout, but add tablet breakpoints.
- Use `max-width: min(520px, 100vw)` or equivalent for drawer.
- Ensure drawer does not hide critical table controls without an intentional overlay model.
- Allow columns to adapt at tablet widths using existing responsive primitives.
- Define minimum supported viewport and behavior explicitly.
- Test long names, missing prices, translated labels, absent images, and bulk selection controls at tablet widths.

---

### P1 — Permission-specific affordances are unspecified

**Source evidence**

- Permission-specific affordances are not described.
- 401/403 states are missing.

**Runtime hypotheses needing validation**

- Users without edit permission may still see enabled edit/upload/save controls until API rejection.
- Bulk actions may appear available when not allowed.

**Fixes**

- Gate edit, upload, bulk selection, and save controls by permission state.
- Prefer disabled controls with explanatory copy where discovery is useful.
- Hide controls only where the workflow/design system already expects it.
- Handle server-side 403 even if client permissions are stale.

---

### P2 — Hostile data handling is incomplete

**Source evidence**

- Product names may be 1–200 characters.
- Prices may be missing.
- Translations may expand labels by 60%.
- Product name CSS only covers single-line ellipsis.

```css
.product-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
```

**Runtime hypotheses needing validation**

- Long names may hide distinguishing information.
- Missing price may be confused with zero price.
- Expanded translations may overflow buttons, filters, drawer labels, or table columns.

**Fixes**

- Add tooltip/details affordance for truncated names if supported by current design system.
- Show missing price as an explicit unavailable/blank-state token, not `0`.
- Avoid relying on icon-only or fixed-width translated labels.
- Validate drawer form labels and error text under 60% expansion.
- Ensure bulk actions and filter chips do not overflow or become ambiguous.

---

### P2 — Broad transitions risk motion discomfort and performance cost

**Source evidence**

```css
.product-row, .drawer {
  transition: all 300ms ease-in;
}
```

**Runtime hypotheses needing validation**

- `transition: all` may animate layout-affecting properties.
- Row-level transitions across many rows may increase jank.
- Reduced-motion users may get unwanted animation.

**Fixes**

- Transition only specific compositor-friendly properties, such as `transform` or `opacity`, where appropriate.
- Remove row transitions unless they communicate a meaningful state change.
- Add `prefers-reduced-motion` handling.
- Avoid animating dimensions, grid layout, or expensive paint properties on large lists.

---

### P2 — Bulk selection behavior needs state clarity at scale

**Source evidence**

- Route includes bulk selection.
- Partial batch failure states are not represented.
- 10,000 rows exist.

**Runtime hypotheses needing validation**

- “Select all visible” vs “select all filtered” may be ambiguous.
- Partial save/upload/delete failures may be hard to reconcile.
- Selection state may be lost during filtering.

**Fixes**

- Make selection scope explicit.
- Preserve selection intentionally across filters, or clear it with warning.
- Show selected count.
- For bulk operations, show pending, succeeded, failed, and retryable subsets.
- Avoid storing selection as row object references if rows are refetched or filtered.

---

### P3 — Visual polish should follow hardening, not precede it

**Source evidence**

- Existing design system/workflow must be preserved.
- Current risks are functional, accessibility, and performance-oriented.

**Runtime hypotheses needing validation**

- Minor spacing/color improvements may be useful but should not consume effort before blockers.

**Fixes**

- After P0/P1 fixes, polish:
  - Loading skeleton density.
  - Empty/error copy.
  - Focus ring consistency.
  - Drawer spacing for long labels.
  - Table truncation affordances.
  - Autosave status placement and wording.

---

## 3. Concrete hardening plan by concern

### Hostile data

- Long names: truncate in table, expose full value on focus/hover/details, preserve full value in drawer.
- Missing price: display explicit missing state; validate save behavior separately from zero.
- Translation expansion: avoid fixed text containers for labels/actions; test 60% expansion.
- Missing images: reserve dimensions and show placeholder.
- 8MB images: preflight size/type, progress, retry, and thumbnail strategy.

### Failures

- Replace silent `catch` with typed errors and user-visible states.
- Add states for 401/403, 409, 429, 500, timeout, offline, retry, and partial batch failure.
- Preserve drafts on failure.
- Scope saving/error state to the edited product or operation.
- Make autosave status honest: saving, saved, failed, offline, retrying, conflict.

### Responsive layout

- Keep desktop-first table.
- Define tablet breakpoint behavior.
- Constrain drawer to viewport.
- Avoid hard `min-width: 1180px` as the only tablet behavior.
- Validate grid columns with long names, missing prices, translations, and drawer open.

### Accessibility

- Add accessible names for icon-only buttons.
- Restore visible focus via `:focus-visible`.
- Trap drawer focus and prevent background interaction.
- Restore focus on drawer close.
- Add keyboard navigation expectations for rows, filters, selection, save, close, and upload.
- Respect reduced motion.
- Make loading, error, saving, and conflict states perceivable to assistive tech.

### State recovery

- Keep local draft until confirmed saved.
- Block or confirm close during pending save/dirty state.
- Distinguish failed save from failed image upload.
- Add retry paths that do not duplicate operations.
- Handle stale data/conflicts explicitly.
- Keep prior table results visible during filter refresh where safe.

### Performance

- Virtualize or otherwise window the 10,000-row table.
- Memoize filtering and row rendering.
- Debounce/defer expensive filter recalculation.
- Avoid whole-table re-render from drawer-only save state.
- Reserve image dimensions.
- Remove broad transitions from large row sets.
- Measure large-list render, filter latency, memory, and interaction responsiveness.

---

## 4. Static detector-like signals: decisive vs needing context

### Decisive from the supplied source/facts

- `catch {}` is a correctness and observability defect for saves.
- Rendering `rows.map` for 10,000 rows is an unbounded rendering risk.
- Blank table during loading is an ambiguous state.
- Missing error/conflict/offline/retry states are production hardening gaps.
- Icon-only save/close without labels is an accessibility gap.
- `outline: none` without replacement focus styling is an accessibility gap.
- Drawer without focus trap/background isolation is unsafe for keyboard and assistive-tech use.
- Escape close during pending save is a data-loss risk.
- `transition: all` on rows/drawer is too broad.
- Fixed `min-width: 1180px` conflicts with tablet support unless an intentional horizontal-scroll model exists.
- Unreserved image dimensions create layout-shift risk.

### Needs project/runtime context before final implementation choice

- Whether to use virtualization, pagination, server-side filtering, or an existing table primitive.
- Exact tablet breakpoints and whether horizontal scroll is an accepted workflow.
- Existing design-system components for drawer, toast, alert, skeleton, focus ring, upload, and table.
- API error schema, retry semantics, conflict resolution contract, and idempotency support.
- Permission model and whether affordances should be hidden or disabled.
- Autosave timing, draft persistence requirements, and close/discard policy.
- Actual row height variability, image loading path, and thumbnail availability.
- Browser/device support targets and acceptable performance budgets.

---

## 5. Measurement-first validation plan with rollback and acceptance conditions

### Baseline before changes

- Record current behavior for:
  - Initial load with 10,000 rows.
  - Filtering latency per keystroke.
  - Drawer open/close interaction.
  - Save success, failed save, timeout, offline, 409, 429, and 500 responses.
  - Bulk operation partial failure.
  - Missing image, large image, missing price, 200-character name, translated labels.
  - Keyboard-only drawer flow and focus return.
  - Tablet viewport behavior.
- Do not rely on static inspection alone for final sign-off.

### Acceptance conditions

- Failed saves are visible, recoverable, and do not appear successful.
- Dirty/pending edits cannot be silently lost by Escape or close.
- Drawer focus is contained while open and restored on close.
- Icon-only actions have accessible names and visible focus.
- Loading, empty, permission, conflict, rate-limit, server-error, timeout, offline, retry, and partial-failure states are represented.
- 10,000-row table remains responsive under agreed interaction budgets.
- Filtering does not block typing beyond agreed latency budget.
- Images do not cause disruptive layout shift.
- Tablet layout is usable within the declared supported viewport range.
- Reduced-motion preference is respected.
- Permission-restricted users see accurate affordances and server 403 is handled.

### Rollback conditions

- New save handling increases data-loss risk or hides failures.
- Virtualization/pagination breaks selection, keyboard navigation, or row identity.
- Responsive changes break the desktop operations workflow.
- Accessibility changes trap users or prevent expected close/recovery paths.
- Error-state work introduces generic messages that obscure conflict, permission, or partial-failure recovery.
- Performance optimization reduces correctness, observability, or recoverability.

Applied quality, frontend, and performance guardrails; no browser, build, profiler, detector, accessibility-tree, network, or device run is claimed.
