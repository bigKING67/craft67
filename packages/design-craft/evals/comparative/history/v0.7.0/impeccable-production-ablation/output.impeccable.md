## 1. Sequencing and verdict

**Sequencing:** audit current behavior → harden save/error/state recovery paths → fix accessibility and drawer interaction safety → make hostile data/layout resilient → optimize 10,000-row rendering/filtering/images → validate with measurements and guarded rollout.

**Verdict:** Not production-ready for an operations-critical inventory editor as described; the main risks are silent data loss, unrecoverable/ambiguous save states, inaccessible drawer/actions, tablet breakage, and predictable performance failure at 10,000 rows.

---

## 2. Prioritized findings

### P0 — Data integrity, save recovery, and destructive interaction risks

1. **Save errors are swallowed**
   - **Source evidence:** `catch {}` in `saveProduct`.
   - **Impact:** Users may believe inventory edits were saved when the API rejected them.
   - **Runtime hypothesis:** Severity depends on API error rate and whether another layer surfaces errors, but the local code path shown provides no recovery.

2. **Single global `saving` flag is unsafe for row/product saves**
   - **Source evidence:** `const [saving, setSaving] = useState(false)` and `EditDrawer saving={saving}`.
   - **Impact:** Concurrent saves can race: one save can finish and set `saving=false` while another is still pending.
   - **Runtime hypothesis:** If the UI only permits one in-flight save, risk is lower; this must be enforced, not assumed.

3. **Drawer can close while save is pending**
   - **Source evidence:** additional note: Escape closes drawer even while save is pending.
   - **Impact:** User can lose context, interrupt recovery, or assume save completed.
   - **Fix priority:** Block close, require confirmation, or queue close until save resolves.

4. **Conflict and partial failure states are absent**
   - **Source evidence:** 409 conflict and partial batch failure states not represented.
   - **Impact:** Inventory edits can overwrite newer data or leave bulk edits partially applied without clear remediation.

---

### P1 — Scale/performance failure at expected data size

5. **All 10,000 rows render at once**
   - **Source evidence:** `{rows.map((row) => <ProductRow ... />)}`.
   - **Impact:** High initial render cost, slow updates, poor keyboard/mouse responsiveness, expensive reconciliation.
   - **Runtime hypothesis:** Exact latency requires measurement, but rendering 10,000 interactive product rows is a decisive static risk.

6. **Filtering recalculates synchronously on every keystroke**
   - **Source evidence:** additional note.
   - **Impact:** Typing in filters can block the main thread, especially with translated labels, long names, and derived fields.
   - **Runtime hypothesis:** Depends on filter complexity, but the described behavior is unsafe at 10,000 rows.

7. **Image dimensions are not reserved**
   - **Source evidence:** additional note.
   - **Impact:** Layout shifts while images load; absent/large images can destabilize row height and scrolling.
   - **Runtime hypothesis:** Actual CLS/visual jump depends on image component implementation, but absence of reserved dimensions is a known failure mode.

8. **`transition: all` on rows and drawer**
   - **Source evidence:** `.product-row, .drawer { transition: all 300ms ease-in; }`.
   - **Impact:** Accidental animation of layout-affecting properties can cause jank during filtering, drawer open/close, and row updates.

---

### P1 — Accessibility and keyboard-operability gaps

9. **Drawer does not trap focus or prevent background interaction**
   - **Source evidence:** additional note.
   - **Impact:** Keyboard and screen-reader users can interact with obscured page content; focus can escape modal context.
   - **Severity:** High because edit drawer likely performs critical inventory mutations.

10. **Icon-only save and close actions lack described accessible names**
   - **Source evidence:** additional note: save and close are icon-only.
   - **Impact:** Screen-reader users may not know what the controls do.

11. **Focus indicator removed**
   - **Source evidence:** `.icon-button { ... outline: none; }`.
   - **Impact:** Keyboard users can lose track of active control.
   - **Fix:** Restore visible `:focus-visible` styling using existing design tokens.

12. **Keyboard navigation and screen-reader labels are not described**
   - **Source evidence:** additional note.
   - **Impact:** 10,000-row table, bulk selection, filters, upload, and drawer are likely difficult or impossible to operate fully by keyboard.

---

### P1 — Failure states and permission-specific behavior missing

13. **Initial/filter loading renders blank table body**
   - **Source evidence:** additional note.
   - **Impact:** Users cannot distinguish loading from empty, broken, or unauthorized states.

14. **No empty, auth, rate-limit, server, timeout, offline, retry states**
   - **Source evidence:** additional note lists missing 401/403, 429, 500, timeout, offline, retry.
   - **Impact:** Operations users cannot recover confidently from common production failures.

15. **Permission-specific affordances are not described**
   - **Source evidence:** additional note.
   - **Impact:** Users may see controls they cannot use, or receive late failures after editing.

---

### P2 — Hostile data and layout resilience

16. **Fixed desktop minimum width conflicts with tablet support**
   - **Source evidence:** `.page { min-width: 1180px; }`.
   - **Impact:** Tablet users likely get horizontal overflow or clipped controls.
   - **Runtime hypothesis:** Actual breakpoint behavior depends on outer shell, but this static rule is a strong tablet-risk signal.

17. **Rigid grid columns may fail with translated labels and long names**
   - **Source evidence:** `grid-template-columns: 64px 280px 1fr 120px 96px`; names up to 200 chars; translations can expand labels 60%.
   - **Impact:** Truncation, crowding, hidden controls, or inaccessible content.

18. **Missing prices and absent images not represented**
   - **Source evidence:** additional notes.
   - **Impact:** Users may confuse missing data with zero price, failed load, or blank UI.

19. **8MB images can degrade upload and preview performance**
   - **Source evidence:** additional note.
   - **Impact:** Slow preview, memory spikes, timeout ambiguity, failed autosave/upload states.

---

### P2 — Motion and interaction polish

20. **Reduced motion is not described**
   - **Source evidence:** additional note; CSS transitions active.
   - **Impact:** Motion-sensitive users may be forced through drawer/row animation.

21. **`ease-in` for drawer can feel sluggish**
   - **Source evidence:** `300ms ease-in`.
   - **Impact:** Drawer starts slowly and may feel delayed. This is polish-level unless it blocks operation.

---

### P3 — Maintainability and observability gaps

22. **No visible autosave state model**
   - **Source evidence:** only `saving` boolean shown.
   - **Impact:** Cannot express “unsaved changes,” “saving,” “saved,” “failed,” “retrying,” “conflict,” or “offline queued.”

23. **No described telemetry hooks**
   - **Source evidence:** none shown.
   - **Impact:** Hard to monitor save failure rate, conflict rate, filter latency, upload failures, or drawer abandonment.

---

## 3. Concrete fixes

### Hostile data

- Render explicit placeholders:
  - Missing price: “No price” or “—” with tooltip/description, not `$0`.
  - Missing image: stable placeholder with reserved dimensions.
  - Failed image: retryable/error placeholder.
- Reserve image width/height or aspect ratio in rows and drawer previews.
- Constrain long product names with truncation plus accessible full text:
  - visible ellipsis remains acceptable,
  - full name available via title/description/popover according to existing design patterns.
- Audit all fixed column widths against 60% label expansion.
- Use `minmax(0, 1fr)` for flexible text columns to prevent overflow.
- Ensure numeric columns align consistently and handle null/unknown values distinctly.

### Failures and state recovery

- Replace `catch {}` with explicit error classification:
  - 401/403: permission/session state with clear next step.
  - 409: conflict resolution path: reload, compare, or overwrite if permitted.
  - 429: rate-limit message with retry-after handling where available.
  - 500/timeout/offline: retry affordance and local unsaved state preservation.
  - partial batch failure: per-row success/failure summary with retry failed only.
- Model save state as more than a boolean:
  - `idle`, `dirty`, `saving`, `saved`, `failed`, `conflict`, `offline`, `retrying`.
- Use request IDs or per-product save state so stale responses cannot overwrite newer state.
- Use `try/catch/finally`, but only clear pending state for the matching request.
- Preserve draft edits after failed save.
- Prevent drawer close during critical save, or show a confirmation:
  - “Save in progress. Close anyway and keep draft?” if drafts are retained.
- Add retry that does not require re-entering edits.
- For autosave, show last saved time and failure state, not only spinner/pending.

### Responsive layout

- Replace hard `min-width: 1180px` with responsive constraints:
  - desktop keeps current dense table,
  - tablet uses horizontal scroll inside the table region or adaptive columns,
  - critical actions remain reachable.
- Keep the existing desktop-first workflow, but define tablet breakpoints:
  - filters wrap predictably,
  - bulk actions remain sticky/visible,
  - drawer width becomes `min(520px, 100vw)` or similar,
  - table container handles overflow without breaking the whole page shell.
- Ensure drawer does not cover required confirmation/toast regions on tablet.
- Test translated labels at +60% length in filters, headers, drawer buttons, and error messages.

### Accessibility

- Treat the edit drawer as a modal or non-modal panel deliberately:
  - if modal: `role="dialog"`, accessible name, focus trap, background inert/disabled, restore focus on close.
  - if non-modal: no trap, but clear keyboard model and background interaction must be intentional.
- Save and close icon buttons need accessible names:
  - `aria-label="Save product"` / `aria-label="Close editor"` or visible text where possible.
- Restore visible keyboard focus:
  - remove `outline: none` or replace with `:focus-visible` tokenized ring.
- Define keyboard behavior:
  - Tab order through filters, table actions, bulk selection, drawer fields.
  - Escape behavior disabled or confirmed while save is pending.
  - Bulk selection reachable and announced.
- Announce save status changes via a polite live region:
  - “Saving changes,” “Saved,” “Save failed,” “Conflict detected.”
- Respect reduced motion:
  - disable or shorten drawer/row transitions under `prefers-reduced-motion: reduce`.
- Ensure disabled controls expose reason where needed, especially permission-specific actions.

### Performance

- Do not render 10,000 full rows at once.
  - Prefer existing table/windowing/pagination primitives if already present.
  - If no primitive exists, implement minimal row windowing or server/client pagination within existing architecture.
- Keep selection state independent from rendered rows so bulk selection works across the full filtered set.
- Debounce or defer filter input work.
- Memoize filtered rows and derived display values with correct dependencies.
- Move expensive normalization/search token generation out of keystroke paths where possible.
- Use stable callbacks/row props for row rendering to avoid unnecessary row updates.
- Avoid `transition: all`; transition only safe properties:
  - drawer: `transform`, `opacity`;
  - row hover/selection: color/background only if needed.
- Reserve image dimensions and lazy-load non-visible images.
- Avoid previewing full 8MB files directly when a lower-memory preview path exists in the current stack.
- Add upload progress, size validation, retry/cancel, and clear failure messages.

---

## 4. Static signals: decisive vs needs project/runtime context

### Decisive from the provided source/facts

- `rows.map(...)` renders every row passed to the component.
- `catch {}` hides save failures in this code path.
- A single `saving` boolean cannot safely represent concurrent per-product saves.
- `.page { min-width: 1180px; }` is incompatible with robust tablet support unless contained by a deliberate scroll/adaptive shell.
- `transition: all` is unsafe for performance-sensitive rows/drawer.
- `.icon-button { outline: none; }` removes the default focus indicator unless replaced elsewhere.
- Blank loading, missing failure states, no focus trap, no reduced-motion behavior, and no keyboard/screen-reader description are production hardening gaps given the route’s responsibilities.

### Requires project/runtime context

- Whether another global error boundary, toast system, or API client already reports save failures.
- Whether `ProductRow` is memoized or expensive.
- Actual filter algorithm cost and keystroke latency.
- Whether the table uses semantic table roles or accessible grid patterns inside `ProductRow`.
- Whether CSS elsewhere restores focus-visible styling.
- Whether shell layout intentionally provides horizontal scrolling for `min-width: 1180px`.
- Actual image loading behavior, cache hit rate, decoding cost, and upload pipeline limits.
- API semantics for conflicts, retries, idempotency, and partial batch failure.
- Permission model and whether unavailable actions are hidden, disabled, or server-rejected.

---

## 5. Measurement-first validation plan

### Baseline before changes

- Capture current numbers for:
  - initial render time with 10,000 rows,
  - filter keystroke latency at p50/p95,
  - drawer open/close latency,
  - save success/failure/conflict handling,
  - upload behavior for absent, normal, and 8MB images,
  - layout stability during image loading,
  - keyboard completion of edit/save/close flow.
- Use representative datasets:
  - 10,000 rows,
  - 200-character names,
  - missing prices,
  - absent images,
  - 8MB images,
  - translated labels expanded by 60%,
  - mixed permissions,
  - partial batch failures.

### Acceptance conditions

- Save failures are visible, recoverable, and preserve draft edits.
- 409 conflicts cannot silently overwrite newer data.
- Pending save cannot be accidentally dismissed without clear protection or confirmation.
- Filter input remains responsive at 10,000 rows under agreed latency targets.
- Only visible or paged rows render, while bulk selection remains correct for the full result set.
- Loading, empty, unauthorized, forbidden, rate-limited, server error, timeout, offline, retry, and partial failure states are represented.
- Drawer is keyboard-operable, named, focus-safe, and restores focus on close.
- Icon-only controls have accessible names and visible focus.
- Tablet layout keeps filters, table actions, drawer controls, and bulk actions reachable.
- Reduced-motion users are not forced through nonessential animation.
- Image loading/upload does not cause major layout shift or ambiguous failure.

### Rollback conditions

- Save success rate drops or conflict handling becomes ambiguous.
- Bulk selection semantics change unexpectedly.
- Filter latency, initial load, or drawer interaction becomes worse than baseline.
- Tablet users lose access to existing controls.
- Accessibility fixes break existing keyboard workflows.
- Error handling increases duplicate saves or repeated uploads.
- Virtualization/pagination causes row identity, selection, or scroll-position bugs.

### Rollout approach

- Ship hardening in guarded slices:
  1. save/error state model and recovery,
  2. drawer accessibility and close safety,
  3. loading/empty/error states,
  4. responsive containment,
  5. row rendering/filter performance,
  6. image reservation/upload resilience.
- Keep visual changes token-based and consistent with the existing system.
- Avoid new dependencies unless measurement proves the existing stack cannot meet the row-count and interaction targets.
