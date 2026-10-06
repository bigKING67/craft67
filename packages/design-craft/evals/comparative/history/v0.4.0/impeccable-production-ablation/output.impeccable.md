## 1. Sequencing + verdict

**Correct sequence:**  
**Audit → harden failure/data/state paths → optimize table/filter/image performance → adapt tablet/responsive behavior → accessibility pass → final polish/QA.**

**Verdict:** Not production-ready as described; preserve the existing workflow, but block release on save failure visibility, drawer focus/safety, 10,000-row rendering, missing operational states, and keyboard/accessibility gaps.

---

## 2. Prioritized findings

### P0 — Blocking

**P0.1 Silent save failure can create false confidence**  
- **Source evidence:** `catch {}` swallows `api.save(product)` errors; missing 401/403, 409, 429, 500, timeout, offline, retry, and partial batch failure states.  
- **Impact:** Operations staff may believe edits were saved when they were rejected, conflicted, rate-limited, or lost.  
- **Runtime hypothesis:** Actual API layer may have global interceptors/toasts, but none are represented here.  
- **Fix:** Return structured save outcomes: success, validation error, permission error, conflict, retryable failure, offline queued, partial batch failure. Show inline drawer errors and autosave status with recovery actions.

**P0.2 Drawer can close during pending save**  
- **Source evidence:** Additional notes state Escape closes drawer while save is pending.  
- **Impact:** User can lose context or interrupt recovery while a write is unresolved.  
- **Runtime hypothesis:** Save may still complete server-side, but UI state recovery is not defined.  
- **Fix:** While saving, either block close with explicit “Saving…” state or require confirmation: “Save still in progress. Keep editing / discard local changes.” Always preserve draft state.

**P0.3 Drawer lacks modal interaction safety**  
- **Source evidence:** Drawer traps neither focus nor background interaction.  
- **Impact:** Keyboard and screen-reader users can tab behind the drawer, edit the wrong row, or lose orientation.  
- **Runtime hypothesis:** A design-system drawer may add this elsewhere, but not shown in the source facts.  
- **Fix:** Treat the edit drawer as a modal/panel with focus trap, inert background, labelled title, focus return to invoking row/action, and Escape behavior gated by dirty/saving state.

**P0.4 Rendering all 10,000 rows is a production performance risk**  
- **Source evidence:** `{rows.map(...ProductRow...)}` renders every row; all 10,000 rows render at once.  
- **Impact:** Initial load, filter changes, selection, and drawer edits can cause long main-thread stalls.  
- **Runtime hypothesis:** Actual row complexity and hardware determine severity, but the unbounded render pattern is decisive.  
- **Fix:** Use existing table/list patterns if available; otherwise add windowing/virtualization, stable row heights, memoized row rendering, and isolated selection state.

---

### P1 — Major

**P1.1 Filtering recalculates synchronously on every keystroke**  
- **Source evidence:** Source notes state synchronous recalculation on each keystroke.  
- **Impact:** Input lag and dropped characters on large inventories.  
- **Fix:** Debounce or defer filter updates, memoize derived rows, move expensive matching off the urgent render path, and keep input typing immediate.

**P1.2 Loading states are blank**  
- **Source evidence:** Initial and filter loading render a blank table body.  
- **Impact:** Users cannot distinguish loading from empty data, permissions failure, or broken UI.  
- **Fix:** Use table skeleton rows for initial load; during filtering, keep prior results visible with a subtle “Updating…” affordance or show deterministic skeleton/placeholder rows.

**P1.3 Critical operational states are absent**  
- **Source evidence:** Empty results, auth/permission, conflict, rate-limit, server error, timeout, offline, retry, and partial batch failure states not represented.  
- **Impact:** Staff cannot recover from common production conditions.  
- **Fix:** Add state-specific messages and actions: clear filters, request access, reload, retry, resolve conflict, retry failed batch items, continue offline/draft where supported.

**P1.4 Icon-only save/close controls are under-specified**  
- **Source evidence:** Save and close are icon-only; screen-reader labels are not described.  
- **Impact:** Non-visual users and many sighted users may not know what the controls do.  
- **Fix:** Add accessible names, visible tooltips/help text on hover/focus, disabled/loading labels, and confirmation copy for destructive close/discard states.

**P1.5 Focus indicator is explicitly removed**  
- **Source evidence:** `.icon-button { ... outline: none; }`; focus-visible behavior is not described.  
- **Impact:** Keyboard users may be unable to track focus.  
- **Fix:** Restore `:focus-visible` using existing focus-ring tokens; do not remove outline without an equivalent visible replacement.

**P1.6 Tablet support conflicts with fixed desktop minimums**  
- **Source evidence:** `.page { min-width: 1180px; }`, fixed grid columns, `.drawer { width: 520px; }`; tablet behavior not described.  
- **Impact:** Tablet users may get forced horizontal scroll, clipped drawer/table content, or inaccessible controls.  
- **Runtime hypothesis:** A horizontal table scroller may exist outside the snippet, but tablet behavior is not established.  
- **Fix:** Define tablet breakpoints: persistent table scroller if necessary, compact columns, drawer width as `min(520px, 100vw)` or tablet-specific full-height panel, sticky actions, and touch-safe spacing.

**P1.7 Image sizing is not reserved**  
- **Source evidence:** Image dimensions are not reserved; some images absent or 8MB.  
- **Impact:** Layout shift, slow rendering, broken visual scanning, excessive bandwidth.  
- **Fix:** Reserve aspect-ratio boxes, show absent-image placeholders, lazy-load below viewport, use thumbnails/transforms, validate upload size/type, and show upload progress/errors.

---

### P2 — Minor but important

**P2.1 `transition: all 300ms ease-in` is too broad**  
- **Source evidence:** `.product-row, .drawer { transition: all 300ms ease-in; }`  
- **Impact:** Can animate layout, size, grid, color, shadow, and other unintended properties; `ease-in` makes exits/opens feel sluggish; reduced motion missing.  
- **Fix:** Restrict to `transform`, `opacity`, or specific color properties; use 150–250ms state-driven motion; add `prefers-reduced-motion`.

**P2.2 Long names are visually truncated without recovery path**  
- **Source evidence:** Product names may be 1–200 chars; `.product-name` uses nowrap/ellipsis.  
- **Impact:** Staff may not distinguish similarly named SKUs.  
- **Fix:** Preserve dense table behavior but expose full name via accessible title/details cell expansion, drawer header, or copyable secondary text. Avoid relying on hover-only disclosure.

**P2.3 Missing prices and hostile data are not represented**  
- **Source evidence:** Prices may be missing.  
- **Impact:** Blank cells can be confused with zero, loading, or display bug.  
- **Fix:** Use explicit em dash/“No price” state with semantic styling; prevent invalid bulk edits; validate save payloads.

**P2.4 Internationalization expansion not accounted for**  
- **Source evidence:** Translations may expand labels by 60 percent.  
- **Impact:** Buttons, filters, drawer labels, and status text may overflow or truncate critical actions.  
- **Fix:** Test label expansion budgets, avoid fixed-width labels where possible, allow wrapping in drawer/forms, and keep table cells intentionally truncated with recovery.

**P2.5 Single global `saving` flag may be too coarse**  
- **Source evidence:** `const [saving, setSaving] = useState(false)` passed to `EditDrawer`.  
- **Impact:** If multiple rows, batch actions, uploads, or autosaves overlap, one boolean cannot represent per-field/per-product status.  
- **Runtime hypothesis:** If only one drawer save can occur at a time, this may be acceptable.  
- **Fix:** Model save state by product/draft/batch operation: idle, dirty, saving, saved, failed, conflicted, retrying.

---

### P3 — Polish

**P3.1 Autosave status needs stable, non-noisy copy**  
- **Source evidence:** Autosave exists in product context; only `saving` is shown in source.  
- **Fix:** Use concise states: “Unsaved changes”, “Saving…”, “Saved 10:42”, “Couldn’t save — retry”, “Offline — changes kept locally.”

**P3.2 Permission-specific affordances are absent**  
- **Source evidence:** Permission-specific affordances are not described.  
- **Fix:** Hide or disable unavailable actions with explanations; distinguish read-only, limited edit, upload denied, and bulk action denied.

**P3.3 Empty results should teach recovery**  
- **Source evidence:** Empty results state not represented.  
- **Fix:** Show active filter summary and actions: clear filters, broaden search, check archived/unavailable items if applicable.

---

## 3. Concrete fixes by concern

### Hostile data
- Reserve table behavior for long product names: ellipsis plus full-name access through drawer/cell details.
- Use explicit placeholders for missing prices/images, not blank cells.
- Validate 8MB uploads before sending; show size/type errors and retry paths.
- Add image placeholders with reserved dimensions and thumbnail transforms.
- Support 60% label expansion in filters, drawer fields, buttons, and status text.

### Failures
- Replace `catch {}` with typed error handling.
- Map failures to user actions:
  - **401/403:** sign in/request access/read-only explanation.
  - **409:** show conflict resolution: reload, compare, overwrite only if allowed.
  - **429:** explain rate limit and retry timing.
  - **500/timeout/offline:** retry, keep draft, show last saved state.
  - **Partial batch failure:** summarize successes/failures and allow retry failed only.

### Responsive layout
- Keep desktop-first density, but define tablet behavior explicitly.
- Avoid global `min-width: 1180px` as the only strategy.
- Use a contained horizontal table scroller if the table must remain wide.
- Make drawer width responsive: `width: min(520px, 100vw)` with tablet-safe actions.
- Ensure touch targets are at least 44×44px on tablet, even if desktop icons remain compact.

### Accessibility
- Restore visible `:focus-visible`.
- Give icon buttons accessible names and state labels.
- Trap drawer focus, mark background inert, restore focus on close.
- Add keyboard navigation for row selection, bulk actions, drawer open/close/save.
- Announce save status and errors with appropriate live regions.
- Respect `prefers-reduced-motion`.
- Ensure image upload has labelled controls, progress, error text, and keyboard access.

### State recovery
- Preserve unsaved drafts on failed saves, close attempts, offline transitions, and conflicts.
- Track dirty state separately from saving state.
- Never clear local edits until server success is confirmed.
- Add explicit rollback/retry for failed bulk operations.
- Show last successful save timestamp where autosave is used.

### Performance
- Virtualize/window the 10,000-row table.
- Memoize row rendering and derived filtered rows.
- Defer/debounce filtering so typing remains responsive.
- Keep selection state normalized and avoid re-rendering every row on each toggle.
- Lazy-load images and reserve layout dimensions.
- Replace `transition: all` with targeted transform/opacity/color transitions.

---

## 4. Static detector-like signals: decisive vs context-dependent

### Decisive from the provided source facts
- `rows.map(...)` over 10,000 rows is an unbounded render pattern.
- `catch {}` makes save failures invisible at this layer.
- Blank loading body is an ambiguous state.
- Missing production error states are a hardening gap.
- Drawer without focus trap/background inertness is an accessibility and safety gap.
- Escape closing during pending save is unsafe.
- `.icon-button { outline: none; }` is a focus-risk unless a replacement exists.
- `transition: all` is an implementation anti-pattern.
- Fixed `min-width: 1180px` plus tablet support is a responsive risk.
- Unreserved image dimensions create layout-shift risk.

### Needs project/runtime context before final severity
- Whether a shared drawer/table component already supplies ARIA, focus trap, and inert behavior.
- Whether global API interceptors already surface errors.
- Whether server-side pagination exists outside this snippet.
- Actual row complexity, device fleet, and measured render/filter latency.
- Whether the table intentionally uses a horizontal scroller on tablet.
- Actual color contrast, semantic table markup, heading/landmark structure.
- Whether image CDN transforms, upload validation, or lazy-loading exist elsewhere.
- Whether permissions are handled upstream or must be represented in this route.
- Whether global focus-ring tokens replace the removed outline.

---

## 5. Measurement-first validation plan

**No runtime validation is claimed here; this is the plan before release.**

### Baseline before fixes
- Measure initial route render with 10,000 representative rows.
- Measure filter input latency on realistic hardware.
- Measure row selection, bulk selection, drawer open/close, save, upload, and conflict flows.
- Capture failure-state behavior with mocked/staged API responses.
- Check keyboard-only operation and screen-reader labels.
- Check tablet layouts at common widths, including 768, 834, 1024, and 1180px.

### Acceptance conditions
- Filtering remains responsive: no perceptible input lag; target p95 interaction response under 100ms, tighter if existing standards require.
- Initial table render does not block task start; virtualized rows keep DOM size bounded.
- No ambiguous blank table state during initial load or filtering.
- Save failures are visible, actionable, and preserve local edits.
- Drawer traps focus, blocks background interaction, restores focus, and handles pending save safely.
- All icon-only controls have accessible names and visible focus states.
- Tablet users can complete filtering, selection, editing, upload, save, and close flows without clipped controls.
- Reduced-motion users do not receive non-essential animation.
- Missing/large/absent images do not cause layout jumps or broken scanning.
- Permission, conflict, offline, timeout, 429, 500, and partial batch states have clear recovery paths.

### Rollback conditions
- Any fix increases data-loss risk or hides save failures.
- Virtualization breaks selection, keyboard navigation, row heights, or screen-reader access.
- Tablet changes degrade the desktop operations workflow.
- Error handling produces noisy duplicate messages or blocks successful saves.
- Performance worsens materially versus baseline, especially filter latency or drawer interaction.
- Accessibility fixes remove established design-system behavior instead of extending it.

### Release approach
- Ship hardening behind a narrow feature flag if available.
- Roll out to internal operations users first.
- Monitor save failures, retry rates, conflict rates, upload failures, time-to-save, and abandoned edits.
- Keep a fast rollback path to the previous table/drawer behavior while preserving safer error reporting where possible.
