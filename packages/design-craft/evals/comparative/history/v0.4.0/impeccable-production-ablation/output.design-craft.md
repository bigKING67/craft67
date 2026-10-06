Reading this as a dense desktop operations inventory editor, optimized for fast bulk review/editing with tablet support—not a redesign.

## 1. Sequencing + verdict

**Correct sequence:** **Audit → Harden → Optimize → Polish**  
1. **Audit:** separate source-proven defects from runtime risks.  
2. **Harden:** fix save/error/recovery/data/a11y failure modes before visual polish.  
3. **Optimize:** measure and reduce 10,000-row/filter/image hot paths.  
4. **Polish:** refine motion, responsive density, focus affordances, and empty/loading communication within the existing system.

**Verdict:** Not production-ready for an operations-critical inventory editor; the surface can be preserved, but failure handling, accessibility, state recovery, and large-list performance need hardening before polish.

---

## 2. Prioritized findings

### P0 — Must fix before production confidence

**P0.1 Save failures are swallowed and recovery is undefined**  
- **Source evidence:** `catch {}` ignores `api.save(product)` failures; additional notes say timeout/offline/retry/partial failure states are absent.  
- **Impact:** staff may believe inventory changes saved when they did not.  
- **Runtime hypothesis:** actual data loss depends on API semantics and whether other layers surface errors.

**P0.2 Global `saving` state is unsafe for row/product-level editing**  
- **Source evidence:** single `saving` boolean shared by `EditDrawer`; route has bulk selection and product rows.  
- **Impact:** concurrent saves can misrepresent status; one save finishing can clear the saving state while another is still pending.  
- **Runtime hypothesis:** if UI strictly serializes saves, severity drops, but source does not show that guarantee.

**P0.3 Drawer interaction is unsafe during pending save**  
- **Source evidence:** drawer does not trap focus/background interaction; Escape closes even while save is pending.  
- **Impact:** lost context, accidental dismissal, unsaved/unknown state, keyboard users can interact behind modal-like UI.  
- **Runtime hypothesis:** exact loss risk depends on whether drawer keeps draft state after close.

**P0.4 Required failure states are absent**  
- **Source evidence:** empty results, 401/403, 409, 429, 500, timeout, offline, retry, and partial batch failure states are not represented.  
- **Impact:** operators cannot distinguish “no products” from “broken filter/load/auth/rate-limit/server failure.”  
- **Runtime hypothesis:** some errors may be handled globally, but this route has no represented local contract.

---

### P1 — High-risk production hardening

**P1.1 10,000 rows render at once**  
- **Source evidence:** `{rows.map(...)}` renders every row; notes confirm all 10,000 rows render.  
- **Impact:** slow initial render, memory pressure, poor filter responsiveness, possible scroll jank.  
- **Runtime hypothesis:** actual latency requires profiling on target devices/data, but unbounded render is a decisive hot-path risk.

**P1.2 Filtering recalculates synchronously on every keystroke**  
- **Source evidence:** notes state synchronous recalculation on each keystroke.  
- **Impact:** input stalls on large datasets.  
- **Runtime hypothesis:** severity depends on filter complexity and device, but 10,000-row synchronous input work is a clear measurement target.

**P1.3 Initial/filter loading renders blank body**  
- **Source evidence:** notes say initial and filter loading render a blank table body.  
- **Impact:** users cannot tell loading from empty or broken state; encourages repeated actions.  
- **Runtime hypothesis:** perceived severity depends on latency, but the absence of state is source-proven.

**P1.4 Accessibility affordances are incomplete**  
- **Source evidence:** icon-only save/close; `.icon-button { outline: none; }`; no focus trap; keyboard navigation, labels, focus-visible, screen-reader labels not described.  
- **Impact:** keyboard and screen-reader users may be blocked from editing safely.  
- **Runtime hypothesis:** some labels may exist inside components not shown, but notes explicitly identify gaps.

**P1.5 Fixed desktop width conflicts with tablet support**  
- **Source evidence:** `.page { min-width: 1180px; }`; tablet behavior not described.  
- **Impact:** tablet users likely get clipping or page-level horizontal scroll.  
- **Runtime hypothesis:** actual behavior depends on outer shell and viewport handling.

---

### P2 — Important quality/performance polish

**P2.1 `transition: all` on rows and drawer is overbroad**  
- **Source evidence:** `.product-row, .drawer { transition: all 300ms ease-in; }`  
- **Impact:** accidental animation of layout/paint-heavy properties; harder reduced-motion compliance.  
- **Runtime hypothesis:** actual jank depends on changed properties.

**P2.2 Image dimensions are not reserved**  
- **Source evidence:** notes say dimensions are not reserved; images may be absent or 8MB.  
- **Impact:** layout shift, slow decode/upload, broken visual rhythm.  
- **Runtime hypothesis:** measured CLS/decode cost requires runtime data.

**P2.3 Hostile data is under-specified**  
- **Source evidence:** names 1–200 chars; missing prices; labels can expand 60%; absent/large images.  
- **Impact:** truncation without accessible full value, broken columns, ambiguous missing values, upload stalls.  
- **Runtime hypothesis:** current `ProductRow` may provide tooltips/titles, but not shown.

**P2.4 Permission-specific affordances are absent**  
- **Source evidence:** permission-specific affordances not described; 401/403 not represented.  
- **Impact:** unauthorized users may see controls they cannot use or receive late failures.  
- **Runtime hypothesis:** route guard may exist elsewhere, but local UI affordances are not evidenced.

---

### P3 — Non-blocking but worthwhile polish

**P3.1 Product name truncation needs accessible disclosure**  
- **Source evidence:** `.product-name` uses nowrap/ellipsis.  
- **Impact:** acceptable for dense tables only if full value is available through accessible name, title, drawer, or expansion.  
- **Runtime hypothesis:** not inherently wrong; depends on surrounding markup.

**P3.2 Drawer sizing is rigid**  
- **Source evidence:** `.drawer { width: 520px; height: 100vh; }`  
- **Impact:** may be acceptable on desktop, cramped or overflowing on tablet.  
- **Runtime hypothesis:** depends on viewport and content density.

**P3.3 Motion easing/duration may feel heavy for operational workflows**  
- **Source evidence:** 300ms ease-in on rows/drawer.  
- **Impact:** dense ops tools usually benefit from fast, interruptible, property-specific motion.  
- **Runtime hypothesis:** perceived feel needs runtime observation.

---

## 3. Concrete fixes

### Hostile data
- Preserve dense table workflow, but make each cell resilient:
  - Product name: keep ellipsis, add accessible full name path via `aria-label`, `title`, row detail, or drawer field.
  - Missing price: render explicit placeholder such as `—` plus semantic “price missing” state if actionable.
  - Long translated labels: avoid fixed label-only assumptions; use `minmax(0, 1fr)`, wrapping where safe, and tokenized spacing.
  - Missing image: reserve same thumbnail box and show existing-system placeholder.
  - 8MB images: validate size/type before upload, show progress/error, support retry/cancel, and avoid decoding full-size images in table cells.

### Failures
- Add route-level states:
  - Initial loading skeleton/body state.
  - Filter loading/processing state that does not blank the table without explanation.
  - Empty results state with current filter summary and clear-filter action.
  - Auth states: 401 sign-in/session-expired; 403 read-only/no-permission explanation.
  - Conflict `409`: show stale data warning, compare current/server values where feasible, reload/merge/discard options.
  - `429`: rate-limit message with backoff/retry timing.
  - `500`, timeout, offline: retry affordance and non-destructive message.
  - Partial batch failure: per-row success/failure summary with retry failed only.

### Responsive layout
- Replace page-level hard minimum with constrained table behavior:
  - Keep desktop density, but put horizontal overflow on the table region, not the whole page.
  - Use column `minmax()` rules so name/description columns absorb compression first.
  - Keep selection/actions visible if current system supports sticky columns.
  - Drawer: `width: clamp(360px, 42vw, 520px)` on desktop; tablet can become a wider sheet or near-full-width panel while preserving workflow.
  - Reserve room for translated labels and validation messages.

### Accessibility
- Drawer:
  - Treat as modal/dialog if it blocks editing context: role, labelled title, focus trap, restore focus on close, inert/background lock.
  - Disable or confirm Escape/close while save is pending or dirty.
- Buttons:
  - Save/close icon buttons need accessible names and visible tooltips/help text where appropriate.
  - Restore focus styling: use `:focus-visible`, not `outline: none` without replacement.
  - Increase hit target or padding while preserving visual density.
- Table:
  - Use semantic table when possible; if virtualized grid is used, ensure row/column counts, selection state, and keyboard navigation are coherent.
  - Bulk selection needs labelled checkbox state: none/some/all selected.
- Motion:
  - Add reduced-motion path and restrict transitions to `transform`, `opacity`, or specific safe properties.

### State recovery
- Change from global `saving` to scoped state:
  - Track save status by product id and batch id.
  - Use `try/catch/finally`; never silently discard errors.
  - Keep dirty draft state separate from persisted row state.
  - Prevent close/navigation during pending save, or show a clear pending/unsaved confirmation.
  - Autosave status should show: idle, saving, saved timestamp, failed, offline queued, retrying, conflict.
  - Make retries idempotent where the API supports it.
  - For bulk updates, retain failed row ids and allow retry/export of failures.

### Performance
- Table:
  - Virtualize visible rows with overscan while preserving selection, keyboard navigation, sticky header/actions, and screen-reader strategy.
  - Memoize row rendering and expensive cell formatting.
  - Keep row keys stable, avoid recreating large objects/functions per row where possible.
- Filtering:
  - Debounce or defer keystroke filtering.
  - Memoize derived filtered rows with correct dependencies.
  - Consider chunked filtering or worker/server filtering only if measurement shows main-thread pressure.
- Images:
  - Reserve dimensions/aspect ratio.
  - Lazy-load thumbnails below the fold.
  - Use appropriately sized thumbnail URLs rather than full originals.
- CSS:
  - Replace `transition: all` with property-specific transitions.
  - Avoid animating grid/layout dimensions on thousands of rows.

---

## 4. Static signals: decisive vs context-dependent

### Decisive from provided source/notes
- `rows.map(...)` plus 10,000-row note proves unbounded row rendering.
- `catch {}` proves local save errors are swallowed.
- Single `saving` boolean proves no visible per-row/per-request save state in this snippet.
- Blank loading body and missing error states are explicitly stated.
- Drawer lacks focus trap/background lock and closes on Escape during save.
- Icon-only save/close and missing screen-reader/focus-visible descriptions are accessibility gaps.
- `outline: none` without replacement is unsafe.
- `transition: all` is an implementation smell.
- Image dimensions not reserved is a layout stability risk.

### Needs project/runtime context before final severity
- Actual filter latency, scroll FPS, memory use, and input delay.
- Whether global auth/error boundaries already handle some 401/500 cases.
- Whether `ProductRow` has accessible labels, titles, memoization, or image fallbacks not shown.
- Whether product workflow truly permits concurrent saves.
- Whether tablet support means full editing parity or limited review mode.
- Whether design-system components already provide focus rings, dialog behavior, and button labels.
- Whether horizontal scrolling is accepted in this operations workflow.
- Actual accessibility tree, contrast, reading order, and keyboard behavior.
- Actual upload transport limits, server resizing, and retry semantics.

---

## 5. Measurement-first validation plan

No validation is claimed here; this is the plan to run before accepting changes.

### Baseline fixtures
- 10,000 products.
- Names at 1, 80, 120, and 200 chars.
- Missing prices.
- Translated labels expanded by 60%.
- Missing images and large image uploads.
- Auth denied, conflict, rate-limit, server error, timeout, offline, and partial batch failure responses.

### Measure first
- Initial render time and main-thread long tasks.
- Filter keystroke latency at p50/p95.
- Scroll smoothness and memory with 10,000 rows.
- React commit duration for table/filter/edit drawer interactions.
- Layout shift around image loading.
- Upload time, failure recovery, retry behavior.
- Save-state accuracy with overlapping saves.
- Keyboard-only completion of: filter → select rows → open drawer → edit → save → close.

### Acceptance conditions
- No silent save failure; every failed save has visible recovery.
- Pending/dirty drawer cannot be accidentally dismissed without protection.
- 10,000-row table remains usable under agreed latency targets.
- Filtering does not block typing perceptibly on target desktop and tablet devices.
- Loading, empty, auth, conflict, rate-limit, server, timeout, offline, retry, and partial failure states are represented.
- Icon buttons have accessible names and visible focus states.
- Drawer focus is contained and restored correctly.
- Reduced motion preference is honored.
- Tablet layout preserves core workflow without unusable clipping.
- Images do not cause disruptive layout shifts.

### Rollback conditions
- Virtualization breaks selection, keyboard navigation, sticky headers, or row edit targeting.
- Save recovery introduces duplicate writes or stale overwrites.
- Drawer hardening blocks legitimate bulk workflow.
- Responsive changes reduce desktop operator throughput.
- Upload handling regresses successful large-image workflows without a fallback.

### Safe rollout
- Gate high-risk table virtualization and autosave changes behind a reversible flag.
- Log save failure categories and retry outcomes.
- Compare before/after latency and error metrics.
- Keep API contracts unchanged unless separately versioned.

Applied evidence-bound frontend, accessibility, and performance review guardrails; this audit is static-only and does not assert any browser, build, profiler, detector, network, or device run.
