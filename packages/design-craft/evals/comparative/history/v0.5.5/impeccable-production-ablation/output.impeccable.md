## 1) Sequencing + verdict

**Correct sequence:** audit → harden failure/data-integrity paths → optimize table/filter/image hot paths → adapt tablet/responsive structure → accessibility pass → final polish/motion/copy pass.

**One-line verdict:** Static evidence shows this inventory editor is not production-ready for operations use: the biggest risks are silent save failure/data loss, inaccessible drawer/actions, and unbounded 10,000-row rendering.

---

## 2) Prioritized findings

### P0 — Data integrity and recovery blockers

**P0.1 Silent save failure**
- **Source evidence:** `catch {}` swallows `api.save(product)` failures; `saving` resets with no error state.
- **Runtime hypothesis:** Operators may believe edits were saved when they were not, especially during timeout/offline/429/500 cases.
- **Fix:** Use explicit save state: `idle | saving | saved | error | conflict | retrying`. Surface error copy near the affected product/drawer, preserve dirty draft, offer retry, and log/report failures through existing app mechanisms.

**P0.2 Conflict and partial failure states are absent**
- **Source evidence:** 409 conflict, partial batch failure, timeout, offline, retry are explicitly not represented.
- **Runtime hypothesis:** Bulk edits/autosave can overwrite newer product data or leave mixed persisted/unpersisted rows with no operator guidance.
- **Fix:** Add conflict resolution state: “server changed this product,” compare local/server values, allow keep mine / use latest / review fields. For batch operations, show per-row success/failure and allow retry failed only.

**P0.3 Drawer can close during pending save**
- **Source evidence:** Escape closes the drawer even while save is pending; drawer has no recovery behavior described.
- **Runtime hypothesis:** In-progress edits can be lost or appear lost during autosave latency.
- **Fix:** Guard close while dirty/saving. Escape should either be disabled during critical save or open a discard/keep editing confirmation. Preserve draft state on close, route change, offline, and failed save.

---

### P1 — Accessibility, keyboard, and task completion risks

**P1.1 Drawer is not a proper modal/dialog interaction**
- **Source evidence:** Drawer traps neither focus nor background interaction; fixed drawer overlays page.
- **Runtime hypothesis:** Keyboard and screen-reader users can tab into background rows while editing, lose context, or trigger table actions behind the drawer.
- **Fix:** Use dialog semantics or equivalent: labelled drawer title, focus trap, restore focus to opener, inert/disabled background interaction, predictable Escape behavior, and announced save/error states.

**P1.2 Icon-only save/close controls are not accessible enough**
- **Source evidence:** Save and close are icon-only; `.icon-button` is `28px × 28px`; `outline: none`.
- **Runtime hypothesis:** Fails touch target expectations on tablet, removes visible keyboard focus, and may be unnamed to assistive tech.
- **Fix:** Keep existing visual system, but add accessible names, visible focus-visible ring, disabled/loading states, tooltip/label where appropriate, and tablet hit area of at least 44px while preserving compact desktop density.

**P1.3 Blank loading and missing error states block operational clarity**
- **Source evidence:** Initial/filter loading render blank table body; empty, 401/403, 429, 500, timeout, offline, retry states absent.
- **Runtime hypothesis:** Operators cannot distinguish loading, no results, permission denial, rate limiting, or broken data.
- **Fix:** Add state-specific table bodies: skeleton rows for loading, empty results with filter reset, permission-specific message/actions, offline banner, retry affordance, and row-level/batch-level failure summaries.

**P1.4 Desktop-only layout breaks tablet support**
- **Source evidence:** `.page { min-width: 1180px; }`; drawer fixed at `520px`; tablet behavior not described.
- **Runtime hypothesis:** Tablet users get horizontal scrolling, clipped drawer/table content, or inaccessible controls.
- **Fix:** Define tablet breakpoint behavior without redesigning workflow: table container may scroll horizontally with sticky key columns; drawer width should be `min(520px, 100vw)` or a tokenized responsive width; filters should wrap/collapse predictably.

**P1.5 Motion is unsafe and too broad**
- **Source evidence:** `.product-row, .drawer { transition: all 300ms ease-in; }`; reduced motion not described.
- **Runtime hypothesis:** Animating `all` can animate layout/width/height unintentionally, hurt responsiveness, and violate reduced-motion expectations.
- **Fix:** Restrict transitions to `transform`, `opacity`, or specific color/background properties. Use 150–250ms state motion. Add `prefers-reduced-motion: reduce` fallback that preserves state feedback without sliding/large movement.

---

### P2 — Performance and hostile-data resilience

**P2.1 All 10,000 rows render at once**
- **Source evidence:** `{rows.map(...)}` renders every row; source notes all 10,000 rows render at once.
- **Runtime hypothesis:** Slow initial render, long commits, memory pressure, poor keyboard/filter latency.
- **Fix:** Window/virtualize the table using existing stack if available, or implement a bounded visible-row window. Preserve selection, keyboard navigation, sticky headers, row height measurement, and screen-reader expectations.

**P2.2 Filtering recalculates synchronously on every keystroke**
- **Source evidence:** Source notes synchronous recalculation on every keystroke.
- **Runtime hypothesis:** Filter input may lag and block interaction.
- **Fix:** Memoize derived filtered rows, debounce or defer expensive filtering, normalize searchable fields once, and avoid rebuilding large objects per keystroke. Keep input responsive before table results update.

**P2.3 Images cause layout shift and heavy upload risk**
- **Source evidence:** Image dimensions are not reserved; images may be absent or 8MB.
- **Runtime hypothesis:** Rows jump as images load; uploads consume bandwidth/memory and fail late.
- **Fix:** Reserve image aspect-ratio/slots, show absent-image placeholder, lazy-load offscreen images, validate file type/size before upload, show upload progress/error/retry, and avoid decoding large images on the main thread when possible.

**P2.4 Hostile product data is under-specified**
- **Source evidence:** Names can be 1–200 chars; prices may be missing; translations expand labels by 60%.
- **Runtime hypothesis:** Truncated names may hide critical differences; missing prices may render as broken cells; translated labels may overflow controls.
- **Fix:** Add explicit missing-price display, accessible full-name reveal/copy, title/description semantics where appropriate, resilient wrapping for labels, and fixtures for long localized strings.

**P2.5 Global `saving` state is too coarse**
- **Source evidence:** Single `const [saving, setSaving]` drives `EditDrawer`.
- **Runtime hypothesis:** One pending save can obscure which product is saving, block unrelated actions, or misrepresent autosave status.
- **Fix:** Track save status by draft/product/request id. Ignore stale responses, prevent double-submit, and make autosave status specific: “Saving SKU-123,” “Saved 10:42,” “Retrying,” “Could not save.”

---

### P3 — Polish and consistency

**P3.1 Product rows need explicit interaction states**
- **Source evidence:** Row CSS only shows grid layout and broad transition.
- **Runtime hypothesis:** Hover/selected/disabled/error states may be inconsistent or absent.
- **Fix:** Standardize row states: default, hover, selected, focused, dirty, saving, saved, error, disabled/permission-restricted.

**P3.2 Ellipsis-only names reduce scan confidence**
- **Source evidence:** `.product-name` uses nowrap/ellipsis.
- **Runtime hypothesis:** Operators may confuse similar long product names.
- **Fix:** Keep dense table layout but provide accessible full-name inspection: secondary line at wider widths, details in drawer, or keyboard-reachable disclosure/tooltip.

---

## 3) Concrete production fixes by area

**Hostile data**
- Add fixtures for 1-char, 200-char, missing price, absent image, 8MB image, long translated labels.
- Define display fallbacks: “No price,” “No image,” “Unsupported image,” “Upload failed.”
- Reserve image dimensions and enforce client-side file limits before upload.

**Failures**
- Replace swallowed errors with visible, recoverable states.
- Represent 401/403 distinctly from 500/timeout/offline/429.
- Add retry with backoff for retryable failures; do not retry conflicts blindly.
- For bulk actions, report partial failure per product and preserve selection of failed rows.

**Responsive layout**
- Replace page-level hard minimum as the only tablet strategy.
- Use a horizontally scrollable table region if needed, not whole-page overflow.
- Keep important columns/actions sticky or reachable.
- Make drawer width responsive and avoid covering critical confirmation/error UI.

**Accessibility**
- Drawer: labelled dialog, focus trap, inert background, focus restore.
- Buttons: accessible names, visible focus-visible, larger hit area on tablet.
- Table/list: semantic structure, keyboard row navigation, selected state announcement.
- Status: autosave/error messages announced through polite/assertive live regions as appropriate.
- Motion: reduced-motion fallback.

**State recovery**
- Persist dirty draft locally while drawer is open and across transient failures.
- Guard close/navigation during dirty or saving states.
- Correlate save responses to the current draft version to avoid stale success overwriting newer edits.
- Show last saved time and unresolved error count.

**Performance**
- Window visible rows; avoid rendering 10,000 DOM rows.
- Memoize filtered results and expensive formatting.
- Defer filtering work so typing stays responsive.
- Lazy-load row images and reserve dimensions.
- Avoid `transition: all`; animate transform/opacity only.

---

## 4) Static detector-like signal reconciliation

**Decisive from static/source facts**
- `catch {}` with no surfaced error is a decisive silent-failure risk.
- Rendering `rows.map(...)` for 10,000 rows is a decisive unbounded-rendering risk.
- `transition: all` is a decisive broad-animation risk.
- `outline: none` on icon buttons is a decisive focus-visibility risk unless replaced elsewhere, which is not shown.
- `28px × 28px` icon buttons are decisively below common touch target guidance.
- `min-width: 1180px` plus tablet support is a decisive responsive risk.
- “No focus trap/background interaction lock” is decisive for drawer accessibility risk.

**Needs project/runtime context**
- Actual frame rate, INP, memory, and commit durations need profiling.
- Exact screen-reader output needs DOM/accessibility tree validation.
- Contrast cannot be concluded from the shown CSS alone.
- Whether `ProductRow` uses real table semantics is unknown from the snippet.
- Permission affordances require product authorization rules.
- Image upload failure modes require upload implementation and network behavior.
- Whether virtualization is safe depends on row height, selection model, sticky columns, and assistive-tech requirements.

---

## 5) Measurement-first validation plan

**Baseline before fixes**
- Measure initial render time, memory, row count in DOM, filter keystroke latency, and long tasks with 10,000 rows.
- Record save flows for success, timeout, offline, 409, 429, 500, and partial batch failure using controlled responses.
- Keyboard-pass the drawer: open, tab through, save, error, retry, Escape, close, focus restore.
- Test hostile fixtures: long names, missing prices, absent/large images, expanded translations.
- Check tablet widths around the minimum supported viewport.

**Acceptance conditions**
- No save failure is silent; every failed/conflicted save preserves the draft and gives a recovery path.
- Pending save cannot be accidentally discarded by Escape/close/navigation.
- Drawer traps focus, restores focus, blocks background interaction, and has named controls.
- Keyboard users can operate filters, table selection, drawer save/close, retry, and bulk failure review.
- Filter typing remains responsive at 10,000 rows; table renders a bounded row count rather than all rows.
- Images do not cause meaningful layout shift; large/invalid uploads fail early with clear recovery.
- Tablet layout has no whole-page unusable horizontal overflow; critical actions remain reachable.
- Reduced-motion mode removes large movement while retaining state feedback.

**Rollback conditions**
- Roll back table windowing if it breaks selection, keyboard navigation, sticky columns, or row announcements.
- Roll back save-flow changes if they block valid saves or create duplicate submissions.
- Roll back responsive drawer changes if they obscure errors/actions at supported tablet widths.
- Keep risky changes behind feature flags or narrow rollout where possible.

**Final release gate**
- Re-audit the same P0/P1 list after implementation.
- Ship only when data-loss paths, drawer accessibility, and 10,000-row interaction performance meet the acceptance conditions; treat visual polish as final-pass work, not a substitute for hardening.
