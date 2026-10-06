## 1) Correct sequencing + verdict

**Sequence:** audit current behavior → patch data-loss and blocked-task risks → add failure/empty/loading state coverage → harden drawer accessibility and save recovery → optimize 10,000-row rendering/filtering/images → polish responsive/tablet behavior → validate with measurements and staged rollback.

**Verdict:** The surface is structurally salvageable without redesign, but it is **not production-hardened for a 10,000-row operations workflow** until save failure visibility, recovery states, drawer accessibility, and list performance are fixed.

---

## 2) Prioritized findings

### P0 — Data loss and invisible save failure risk

**Source evidence**
- `catch {}` silently swallows save errors.
- `setSaving(false)` is outside `finally`; if unexpected control flow changes later, state can desync.
- Global `saving` state applies to the drawer, not a specific product/save request.
- Notes say `409 conflict`, `429`, `500`, timeout, offline, retry, and partial batch failures are not represented.
- Escape closes the drawer even while save is pending.

**Runtime hypotheses to verify**
- Whether unsaved edits are lost on drawer close.
- Whether concurrent saves can race and show stale success/failure.
- Whether autosave status reflects per-field, per-product, or global route state.

**Risk**
- Operators may believe changes saved when they failed.
- Pending edits can be discarded.
- Conflict resolution is absent for inventory data where stale writes are likely.

---

### P0 — Drawer interaction is not production-accessible

**Source evidence**
- Drawer traps neither focus nor background interaction.
- Save and close are icon-only.
- `.icon-button { outline: none; }`
- Escape closes even while save is pending.
- Screen-reader labels and keyboard navigation are not described.

**Runtime hypotheses to verify**
- Whether the drawer has `role="dialog"` / accessible name.
- Whether tab order reaches background table while drawer is open.
- Whether focus returns to the invoking row/action after close.

**Risk**
- Keyboard and assistive-technology users can lose context or activate background controls accidentally.
- Icon-only critical actions may be undiscoverable or unlabeled.

---

### P0 — 10,000-row rendering and synchronous filtering are a hot-path failure

**Source evidence**
- `{rows.map(...)}` renders every row.
- Product context says 10,000-row table.
- Filtering recalculates synchronously on every keystroke.
- Image dimensions are not reserved.

**Runtime hypotheses to verify**
- Actual `ProductRow` cost, image count, cell complexity, and selection behavior.
- Whether filter input blocks typing under realistic data.
- Whether image loading causes layout shift.

**Risk**
- Slow keystrokes, long commits, memory pressure, poor tablet performance, and broken repeated-use ergonomics.

---

### P1 — Blank loading and missing state coverage creates operational ambiguity

**Source evidence**
- Initial and filter loading render a blank table body.
- Empty results, auth errors, conflicts, rate limits, server errors, timeout, offline, retry, and partial batch failures are not represented.

**Runtime hypotheses to verify**
- Whether global route shell has any error boundary.
- Whether permissions are enforced visually or only after action failure.

**Risk**
- Users cannot distinguish “no products,” “still loading,” “not allowed,” and “system failed.”
- Repeated retries or duplicate edits become likely.

---

### P1 — Responsive/tablet behavior conflicts with stated support

**Source evidence**
- `.page { min-width: 1180px; }`
- Drawer is fixed at `width: 520px; height: 100vh; right: 0`.
- Tablet behavior is not described.
- Translations may expand labels by 60%.

**Runtime hypotheses to verify**
- Actual supported tablet widths and orientations.
- Whether horizontal scroll is intentional for the table.
- Whether drawer overlaps critical row context.

**Risk**
- Tablet users may face clipped filters, inaccessible actions, or unusable drawer/table combinations.

---

### P1 — Motion implementation is too broad and may harm usability/performance

**Source evidence**
- `.product-row, .drawer { transition: all 300ms ease-in; }`
- Reduced motion is not described.

**Runtime hypotheses to verify**
- Which properties actually animate.
- Whether row hover/selection/filtering causes layout/property transitions.
- Whether the design system already has motion tokens.

**Risk**
- `transition: all` can animate layout-affecting properties, making dense table work feel laggy.
- No reduced-motion accommodation for users who request it.

---

### P1 — Hostile product data is under-modeled

**Source evidence**
- Product names may be 1–200 characters.
- Prices may be missing.
- Labels may expand by 60%.
- Some images are absent or 8MB.
- Name truncation exists, but no tooltip/details behavior is described.

**Runtime hypotheses to verify**
- Whether missing prices are allowed, pending, invalid, or hidden by permissions.
- Whether long product names need copy/search affordances.
- Whether uploaded image processing is client-side, server-side, or both.

**Risk**
- Ambiguous cells, broken layout, unreadable localized labels, slow image handling, and mistaken edits.

---

### P2 — Bulk selection and permission-specific affordances are unspecified

**Source evidence**
- Product context includes bulk selection.
- Permission-specific affordances are not described.
- Partial batch failure states are absent.

**Runtime hypotheses to verify**
- Whether selection persists across filters/pages.
- Whether unauthorized bulk actions are hidden, disabled with reason, or fail after click.
- Whether partial success can map failures back to rows.

**Risk**
- Operators may perform unintended bulk edits or be unable to recover from mixed outcomes.

---

### P2 — State recovery and offline resilience are incomplete

**Source evidence**
- Autosave status exists in product context, but source shows only `saving`.
- Timeout/offline/retry states are absent.

**Runtime hypotheses to verify**
- Whether drafts are kept locally.
- Whether navigation guards exist.
- Whether retry is idempotent.

**Risk**
- Lost work during network instability or session expiry.

---

### P3 — Visual polish gaps are mostly symptoms of missing states

**Source evidence**
- Icon-only actions, no focus-visible, no reserved image dimensions, fixed drawer width, blank loading.

**Runtime hypotheses to verify**
- Existing design-system tokens/components may already provide better primitives.

**Risk**
- The interface may feel brittle and unfinished even if core flows work.

---

## 3) Concrete fixes

### Hostile data

- Render missing prices as an explicit state, not blank: “No price,” “Pending,” “Restricted,” or “Invalid,” depending on domain meaning.
- Keep name truncation, but add accessible full-name exposure via row details, title/description pattern, or drawer context.
- Use resilient cell layouts: `minmax(0, 1fr)`, no content-driven table expansion, and localized label stress testing.
- Reserve image dimensions with fixed aspect-ratio placeholders.
- For absent images, show a stable placeholder with accessible text.
- For 8MB images, enforce upload limits, progress, cancel, failure messaging, and server/client validation feedback.

### Failures and recovery

- Replace `catch {}` with typed error handling.
- Use `try/catch/finally`.
- Track save state per product or per edit session, not only one global boolean.
- Represent:
  - loading skeleton or progress row,
  - empty filtered result,
  - unauthorized/forbidden state,
  - conflict state with reload/compare/discard options,
  - rate-limit state with retry-after messaging,
  - offline/timeout state with retry,
  - partial batch failure with row-level mapping.
- Prevent drawer close while saving, or require an explicit “discard pending changes” confirmation.
- Make retry idempotent and safe for duplicate submissions.
- Preserve local draft state until confirmed saved.

### Responsive layout

- Keep the desktop-first table, but remove the hard assumption that the page is always at least `1180px`.
- Define supported tablet breakpoints explicitly.
- At narrower widths, choose one intentional behavior:
  - horizontal table scroll with sticky key columns/actions, or
  - condensed columns with drawer taking more screen width.
- Use `max-width`, `clamp()`, or tokenized drawer sizes instead of fixed-only `520px`.
- Account for dynamic viewport height on tablets instead of relying only on `100vh`.
- Verify translated labels at +60% expansion.

### Accessibility

- Drawer should be a real modal or non-modal panel by design, not an accidental hybrid.
- If modal:
  - trap focus inside,
  - mark/inert background content,
  - restore focus to the opening control,
  - provide accessible name/description,
  - support Escape only when safe.
- Add accessible labels to icon-only save/close buttons.
- Restore visible focus styling; avoid `outline: none` unless replaced by a strong `:focus-visible` style.
- Ensure row actions and selection are keyboard reachable.
- Provide clear disabled states and reasons for permission-limited actions.
- Announce save status and errors through an appropriate live region without excessive noise.

### Performance

- Virtualize the 10,000-row table or otherwise window rendered rows.
- Keep row heights predictable if possible.
- Memoize filtered results with correct dependencies.
- Debounce or defer filtering so typing stays responsive.
- Avoid passing unstable props/callbacks into every row if they trigger mass rerenders.
- Lazy-load/decode images and reserve dimensions to avoid layout shift.
- Avoid `transition: all`; animate only transform/opacity where needed.
- Add reduced-motion handling:
  ```css
  @media (prefers-reduced-motion: reduce) {
    .product-row,
    .drawer {
      transition: none;
    }
  }
  ```
- Use design-system motion tokens if available.

---

## 4) Static detector-like signals: decisive vs context-dependent

### Decisive from the provided source/facts

- Rendering all rows with `rows.map(...)` is incompatible with a 10,000-row hot path unless there is hidden virtualization inside `ProductRow`, which is not shown.
- `catch {}` is a decisive reliability smell for save flows.
- Missing explicit loading/error/empty/conflict/offline states is decisive because the notes confirm absence.
- `outline: none` on icon buttons is a decisive accessibility risk unless replaced elsewhere.
- Icon-only save/close without described labels is a decisive accessibility risk.
- No focus trap/background control for the drawer is decisive if the drawer behaves as a modal editing surface.
- `transition: all` is a decisive polish/performance risk.
- Fixed `min-width: 1180px` conflicts with unspecified tablet support.
- Unreserved image dimensions are a decisive layout-stability risk.

### Needs project/runtime context before final severity

- Whether `ProductRow` is memoized or internally lightweight.
- Whether the route is behind a wider error boundary.
- Whether the design system injects focus styles, labels, modal behavior, or reduced-motion rules globally.
- Whether the table intentionally uses horizontal scroll on tablet.
- Whether save is manual, autosave, optimistic, or transactional.
- Whether conflicts are possible in the backend write model.
- Whether images are uploaded directly, preprocessed, chunked, or transformed server-side.
- Whether permissions are route-level, row-level, or action-level.
- Actual performance thresholds on target staff hardware/tablets.

---

## 5) Measurement-first validation plan

### Baseline before changes

- Record static acceptance expectations for:
  - load state,
  - empty state,
  - save success/failure,
  - conflict,
  - offline/timeout,
  - unauthorized,
  - partial batch failure,
  - long name,
  - missing price,
  - absent/large image,
  - tablet width,
  - keyboard-only drawer flow.
- Define target data set: 10,000 rows, long names, missing prices, mixed image states, translated labels.
- Establish measurable budgets:
  - filter input remains responsive,
  - drawer open/close does not trigger table-wide expensive work,
  - row selection remains responsive,
  - image loading does not shift layout,
  - save failure is visible and recoverable.

### Validation after fixes

- Confirm saving uses typed failure states and always exits pending state.
- Confirm drawer cannot accidentally discard pending edits.
- Confirm focus enters drawer, stays there when modal, and returns correctly.
- Confirm icon actions have accessible names and visible focus.
- Confirm reduced-motion mode removes or minimizes nonessential motion.
- Confirm 10,000-row route renders only a bounded visible row set if virtualized.
- Confirm filtering is deferred/debounced/memoized and does not block typing.
- Confirm tablet widths have an intentional layout, not accidental clipping.
- Confirm all listed failure states have copy, action, and recovery path.
- Confirm bulk partial failure maps errors to affected rows.

### Rollback conditions

- Roll back if virtualization breaks row height, keyboard navigation, selection persistence, or screen-reader order.
- Roll back if save hardening introduces duplicate submissions or blocks legitimate close/navigation forever.
- Roll back if responsive changes reduce desktop operator density without a clear tablet benefit.
- Roll back if motion changes remove necessary state feedback rather than only reducing excess animation.
- Roll back if error-state additions mask backend failures instead of exposing actionable recovery.

### Acceptance conditions

- No silent save failures.
- No accidental close/discard during pending save.
- Keyboard and assistive-technology users can complete edit/save/close flows.
- 10,000-row filtering and selection remain responsive on target hardware.
- Loading, empty, auth, conflict, retryable, offline, and partial-failure states are represented.
- Tablet behavior is explicitly supported within agreed breakpoints.
- Existing design system and workflow are preserved; changes are hardening and polish, not a redesign.
