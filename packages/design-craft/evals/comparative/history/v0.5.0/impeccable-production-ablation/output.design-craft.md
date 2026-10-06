## 1) Sequencing + verdict

**Correct sequence:** static audit → define baseline measurements → harden correctness/recovery/accessibility/failure states → measure hot paths → optimize only proven bottlenecks → polish within the existing design system.

**Verdict:** The surface is directionally salvageable, but the shown implementation is not production-hardened for a 10,000-row operations workflow because it risks data loss, inaccessible drawer actions, blank/errorless states, tablet breakage, and avoidable main-thread stalls.

---

## 2) Prioritized findings

### P0 — Save path can silently lose or obscure work
- **Static evidence:** `catch {}` swallows save failures; `saving` is global; `setSaving(false)` is not in `finally`; Escape closes the drawer while save is pending; 409/429/500/offline/timeout/partial failure states are absent.
- **Runtime hypothesis:** Operators may believe changes were saved when they were dropped, conflicted, rate-limited, or partially applied.
- **Fix:** Use explicit save states: `idle | dirty | saving | saved | failed | conflict | offline | retrying`. Surface per-product/per-field errors, not only global saving. Use `try/catch/finally`, preserve the draft on failure, block or confirm close during pending save, and handle version conflicts with reload/compare/overwrite choices.

### P0 — Drawer is not safe as an editing dialog
- **Static evidence:** Drawer traps neither focus nor background interaction; Escape closes it even during save; save/close are icon-only.
- **Runtime hypothesis:** Keyboard and screen-reader users can interact with stale background content, lose context, or close during a destructive/pending operation.
- **Fix:** Treat the drawer as a dialog/side panel: labelled title, `aria-modal` or equivalent inert background behavior, focus trap, focus return, guarded Escape, labelled buttons, pending-save close confirmation, and disabled/loading affordances that remain perceivable.

### P1 — The table has production-state gaps
- **Static evidence:** Initial/filter loading render blank body; empty, auth, conflict, rate-limit, server, timeout, offline, retry, and partial batch failure states are not represented.
- **Runtime hypothesis:** Blank states will be misread as “no products” or broken data; bulk workflows may hide partial failure.
- **Fix:** Add explicit states while preserving layout: loading skeleton or progress row, empty-results message with active filters, permission-specific locked affordance, retryable error row/banner, offline draft state, conflict resolution panel, and per-row/batch partial-result summary.

### P1 — 10,000 rows are rendered and filtered in a hot path
- **Static evidence:** `{rows.map(...)}` renders all rows; notes say all 10,000 rows render at once; filtering recalculates synchronously on every keystroke.
- **Runtime hypothesis:** Input latency, scroll jank, and long tasks are likely on common office hardware, especially with images and selection state.
- **Fix:** Window/virtualize visible rows, keep row identity stable, memoize row rendering, debounce or defer filter input, precompute searchable fields, avoid full synchronous transforms per keystroke, and measure before adding heavier architecture.

### P1 — Tablet and constrained-width behavior is brittle
- **Static evidence:** `.page { min-width: 1180px; }`; drawer is fixed `520px`; row columns are hard-coded: `64px 280px 1fr 120px 96px`.
- **Runtime hypothesis:** Tablet users may get horizontal overflow, clipped drawer content, unusable controls, or background content hidden behind the drawer.
- **Fix:** Keep desktop density, but add responsive constraints: `width: min(520px, calc(100vw - token-space))`, safe-area padding, container-aware grid columns with `minmax()`, controlled horizontal table scroll when appropriate, sticky key identifiers, and tablet-sized hit targets.

### P1 — Accessibility basics are under-specified or actively weakened
- **Static evidence:** `.icon-button { width: 28px; height: 28px; outline: none; }`; save/close are icon-only; keyboard navigation, screen-reader labels, focus-visible, and permission affordances are not described.
- **Runtime hypothesis:** Keyboard users may lose focus location; touch/tablet users may miss small targets; screen-reader users may hear unlabeled controls.
- **Fix:** Restore visible focus via `:focus-visible`, add accessible names/tooltips where needed, use semantic table/grid roles consistent with the interaction model, provide keyboard shortcuts only with discoverable help, support row selection from keyboard, and make disabled/permission states explanatory.

### P2 — Motion is broad and potentially expensive
- **Static evidence:** `.product-row, .drawer { transition: all 300ms ease-in; }`; reduced motion is not described.
- **Runtime hypothesis:** `transition: all` may animate layout/paint properties, causing jank; ease-in drawers can feel sluggish because they start slowly; reduced-motion users may get unnecessary movement.
- **Fix:** Transition only owned compositor-friendly properties such as `transform` and `opacity`; use design-system motion tokens; define interrupted/open/close states; provide reduced-motion behavior that preserves state feedback without large spatial movement.

### P2 — Hostile data can break density and trust
- **Static evidence:** product names are 1–200 chars; prices may be missing; translations expand labels by 60%; images may be absent or 8MB; image dimensions are not reserved.
- **Runtime hypothesis:** Rows may shift, labels may overflow, missing prices may look like zero, and large images may delay interaction.
- **Fix:** Reserve image aspect-ratio boxes, show absent-image placeholders, validate/compress uploads, lazy/deferred decode thumbnails, distinguish missing price from zero, use localized number/currency formatting, and test expanded labels in filters/drawer/buttons.

### P2 — Autosave and bulk selection need recovery semantics
- **Static evidence:** route includes bulk selection and autosave status, but shown state is only one global `saving` boolean.
- **Runtime hypothesis:** One row’s pending save may disable or misrepresent another row; bulk actions may not map errors back to affected rows.
- **Fix:** Track dirty/saving/error state by product id and field. Persist local drafts until acknowledged. For bulk operations, return itemized results and keep failed rows selected or grouped for retry.

### P3 — Polish issues should wait until hardening is in place
- **Static evidence:** fixed dimensions, nowrap names, icon-only controls, blank loading, broad transitions.
- **Runtime hypothesis:** The surface may feel abrupt, cramped, and fragile under real operations data.
- **Fix:** After correctness and performance are measured, polish row density, truncation affordances, inline status copy, hover/selected/focus states, and drawer transition timing using existing tokens.

---

## 3) Concrete hardening plan by area

**Hostile data**
- Product names: truncate visually but expose full value via accessible detail/tooltip pattern; ensure 1-char and 200-char names both scan well.
- Prices: render explicit “Missing price”/“Not set,” never an ambiguous blank or zero-like value.
- Translations: allow labels/actions to grow; avoid fixed-width action text where localization can expand by 60%.
- Images: reserve dimensions, use placeholders, validate size/type, compress or reject oversized uploads, show upload progress and recoverable failure.

**Failures**
- Add explicit UI branches for loading, empty, unauthorized, forbidden, conflict, rate-limit, server error, timeout, offline, retrying, and partial success.
- Map batch failures to affected rows.
- Preserve edits on failure and after refresh when feasible.
- Use retry with backoff for transient failures; do not retry conflicts blindly.

**Responsive layout**
- Replace route-level hard `min-width: 1180px` with a desktop-preferred layout plus tablet fallbacks.
- Make the drawer width clamped to viewport.
- Keep table density but allow controlled horizontal scrolling or adaptive column priority.
- Ensure drawer content remains reachable at tablet sizes and with larger text.

**Accessibility**
- Add labelled save/close buttons.
- Restore visible focus states.
- Implement drawer focus trap, inert background, Escape policy, and focus return.
- Provide keyboard row navigation/selection behavior.
- Ensure touch targets are comfortable on tablet; 28px icon buttons are likely too small unless surrounded by a larger hit area.
- Represent save/error/status changes with appropriate live-region behavior without excessive announcements.

**State recovery**
- Use per-row dirty state and save queues.
- Keep drafts until server acknowledgement.
- Detect stale versions for 409 conflicts.
- Prevent accidental close during pending writes or require confirmation.
- Distinguish saved, saving, failed, offline, and conflict states in the autosave indicator.

**Performance**
- Virtualize/window rows for the 10,000-row path.
- Defer filtering work with debouncing, `useDeferredValue`, indexed search fields, or worker/server filtering if measurement justifies it.
- Memoize derived rows and row components.
- Avoid passing unstable object/function props into every row.
- Reserve image space and defer thumbnail work.
- Avoid `transition: all`; animate transform/opacity only.

---

## 4) Static signal reconciliation

**Decisive within the supplied source**
- `catch {}` proves save errors are swallowed in the shown function.
- `rows.map(...)` plus the note that all 10,000 rows render proves an unbounded render path in the supplied implementation.
- Missing represented states are decisive because the source notes explicitly say they are absent.
- Drawer focus/background behavior is decisive because the notes explicitly say traps are absent.
- `transition: all 300ms ease-in` proves broad transition configuration.
- `min-width: 1180px`, fixed drawer width, and fixed grid columns prove rigid layout rules where these CSS rules apply.

**Strong static risks, but need project/runtime context**
- `outline: none` is only definitely bad if no replacement `:focus-visible` style exists elsewhere.
- 28px icon buttons are likely insufficient, but final judgment depends on surrounding hit area and design-system target rules.
- Fixed drawer width may be acceptable on large desktop, but tablet support requires viewport testing.
- `transition: all` is a performance risk; actual jank needs runtime measurement.
- Blank table body severity depends on duration and surrounding status indicators, but it is still a production UX gap.
- ProductRow internals could add semantics, labels, memoization, or image sizing; the snippet does not prove their absence unless covered by the notes.

**Requires runtime/project evidence**
- Actual frame rate, long tasks, scroll smoothness, input latency, memory pressure, layout shift, and image decode cost.
- Real screen-reader output and keyboard order.
- API semantics for conflicts, rate limits, partial failure, and idempotency.
- Permission model and whether affordances should be hidden, disabled, or explained.
- Existing design-system tokens for spacing, focus, motion, density, and responsive breakpoints.

---

## 5) Measurement-first validation plan

**Baseline before changes**
- Record row count, image mix, device class, browser, network profile, and filter query sizes.
- Measure initial render, filter keystroke latency, scroll smoothness, drawer open/close responsiveness, memory usage, and image layout shift.
- Capture save behavior for success, timeout, offline, 409, 429, 500, and partial batch failure.
- Audit keyboard path: filters → rows → selection → drawer → save/close → focus return.
- Check tablet-width layout, larger text, translated labels, missing prices, absent images, and 8MB uploads.

**Acceptance conditions**
- No silent save failure; every failed/conflicted/pending state is visible and recoverable.
- Closing during pending save is blocked or confirmed, and drafts are preserved.
- 10,000-row filtering and scrolling stay within agreed interaction-latency budgets on target hardware.
- No full blank table body during known loading/error states.
- Drawer is keyboard and screen-reader operable.
- Tablet layout remains usable without hidden primary actions.
- Images do not cause meaningful layout shift or block core editing.

**Rollback conditions**
- Virtualization breaks row selection, keyboard navigation, scroll position recovery, or screen-reader semantics.
- Save-state changes increase data-loss risk or obscure conflict resolution.
- Responsive changes reduce desktop operator density without a measured need.
- Motion changes introduce layout animation, vestibular discomfort, or slower perceived interaction.

**Release gate**
- Ship hardening first, then optimization if measurements confirm the hot path, then polish. Do not accept a visual-only pass while save recovery, drawer accessibility, explicit failure states, and 10,000-row performance remain unresolved.
