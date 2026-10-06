# Blind comparative judgment
Judge only the supplied outputs. Do not infer which skill produced a label. Apply the machine-readable scorecard exactly, recompute each total from criterion points, and return only JSON matching the supplied schema.

## Task prompt

# Inventory editor production audit

Perform a read-only production audit of this static React product-surface
description. Do not edit files or claim that a detector, browser, build,
profiler, accessibility tree, network throttle, or device run actually
occurred. Do not name, cite, or reveal any skill, repository, author, or
upstream source in the response; the output will be judged blind.

Product context:

- Desktop-first inventory editor used by operations staff, with tablet support.
- The route contains filters, a 10,000-row product table, bulk selection, an
  edit drawer, image uploads, and an autosave status.
- The existing design system and workflow must be preserved; this is a
  production hardening/polish task, not a redesign or new dependency pitch.

Observed source facts:

```tsx
function InventoryPage() {
  const [rows, setRows] = useState(allRows);
  const [saving, setSaving] = useState(false);

  async function saveProduct(product) {
    setSaving(true);
    try {
      await api.save(product);
    } catch {}
    setSaving(false);
  }

  return (
    <div className="page">
      <Filters />
      {rows.map((row) => <ProductRow key={row.id} row={row} />)}
      <EditDrawer onSave={saveProduct} saving={saving} />
    </div>
  );
}
```

```css
.page { min-width: 1180px; }
.product-row { display: grid; grid-template-columns: 64px 280px 1fr 120px 96px; }
.product-row, .drawer { transition: all 300ms ease-in; }
.product-name { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.drawer { position: fixed; right: 0; width: 520px; height: 100vh; }
.icon-button { width: 28px; height: 28px; outline: none; }
```

Additional source notes:

- Initial and filter loading render a blank table body.
- Empty results, 401/403, 409 conflict, 429, 500, timeout, offline, retry, and
  partial batch failure states are not represented.
- Product names may be 1-200 characters; prices may be missing; translations
  may expand labels by 60 percent; some images are absent or 8MB.
- The drawer traps neither focus nor background interaction. Escape closes it
  even while a save is pending. Save and close are icon-only.
- All 10,000 rows render at once; filtering recalculates synchronously on every
  keystroke. Image dimensions are not reserved.
- Tablet behavior, keyboard navigation, screen-reader labels, focus-visible,
  reduced motion, and permission-specific affordances are not described.

Return:

1. The correct audit/polish/harden/optimize sequencing and one-line verdict.
2. Prioritized P0-P3 findings with source evidence versus runtime hypotheses.
3. Concrete fixes for hostile data, failures, responsive layout,
   accessibility, state recovery, and performance.
4. Reconcile which static detector-like signals are decisive and which need
   project/runtime context.
5. A measurement-first validation plan with rollback/acceptance conditions.

Stay within 180 lines. Do not turn this into a ground-up redesign.


## Human-readable scorecard

# Comparative scorecard

Generated from `scorecard.json`; do not edit by hand.

| Criterion | Weight | Full credit |
|---|---:|---|
| Mode sequencing and prioritization | 10 | Chooses audit before targeted polish, hardening, and measured optimization with coherent P0-P3 severity. |
| Hostile data and failure hardening | 20 | Covers long and missing data, permissions, conflicts, limits, offline, retry, partial failures, uploads, and truthful save recovery. |
| Responsive and accessibility quality | 15 | Repairs fixed geometry, drawer interaction, keyboard, focus, labels, touch targets, translations, reduced motion, and tablet adaptation. |
| Measurement-first performance | 15 | Identifies render, filter, image, and layout hot paths and requires baselines, thresholds, and rollback conditions. |
| Detector and design-system reconciliation | 10 | Treats static anti-patterns as contextual signals under project authority instead of fabricated runtime proof. |
| Concrete production fixes | 20 | Provides implementation-ready state, error, layout, accessibility, scale, and recovery moves with acceptance conditions. |
| Evidence honesty and scope control | 10 | Separates static proof from hypotheses, claims no unrun tools, stays read-only, and avoids redesign or unjustified dependencies. |
| **Total** | **100** | |


## Machine-readable scorecard

```json
{
  "schema": "design-craft.comparative-scorecard.v1",
  "total": 100,
  "criteria": [
    {
      "id": "mode_sequence",
      "label": "Mode sequencing and prioritization",
      "weight": 10,
      "full_credit": "Chooses audit before targeted polish, hardening, and measured optimization with coherent P0-P3 severity."
    },
    {
      "id": "hostile_data",
      "label": "Hostile data and failure hardening",
      "weight": 20,
      "full_credit": "Covers long and missing data, permissions, conflicts, limits, offline, retry, partial failures, uploads, and truthful save recovery."
    },
    {
      "id": "responsive_accessibility",
      "label": "Responsive and accessibility quality",
      "weight": 15,
      "full_credit": "Repairs fixed geometry, drawer interaction, keyboard, focus, labels, touch targets, translations, reduced motion, and tablet adaptation."
    },
    {
      "id": "measured_performance",
      "label": "Measurement-first performance",
      "weight": 15,
      "full_credit": "Identifies render, filter, image, and layout hot paths and requires baselines, thresholds, and rollback conditions."
    },
    {
      "id": "detector_reconciliation",
      "label": "Detector and design-system reconciliation",
      "weight": 10,
      "full_credit": "Treats static anti-patterns as contextual signals under project authority instead of fabricated runtime proof."
    },
    {
      "id": "production_fixes",
      "label": "Concrete production fixes",
      "weight": 20,
      "full_credit": "Provides implementation-ready state, error, layout, accessibility, scale, and recovery moves with acceptance conditions."
    },
    {
      "id": "evidence_scope",
      "label": "Evidence honesty and scope control",
      "weight": 10,
      "full_credit": "Separates static proof from hypotheses, claims no unrun tools, stays read-only, and avoids redesign or unjustified dependencies."
    }
  ]
}
```

## Required judgment schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["results", "winner", "rationale"],
  "properties": {
    "results": {
      "type": "array",
      "minItems": 3,
      "maxItems": 3,
      "items": {
        "type": "object",
        "required": ["label", "criteria", "total", "summary"],
        "properties": {
          "label": {"enum": ["A", "B", "C"]},
          "criteria": {
            "type": "object",
            "required": [
              "mode_sequence",
              "hostile_data",
              "responsive_accessibility",
              "measured_performance",
              "detector_reconciliation",
              "production_fixes",
              "evidence_scope"
            ],
            "additionalProperties": false,
            "properties": {
              "mode_sequence": {"type": "integer", "minimum": 0, "maximum": 10},
              "hostile_data": {"type": "integer", "minimum": 0, "maximum": 20},
              "responsive_accessibility": {"type": "integer", "minimum": 0, "maximum": 15},
              "measured_performance": {"type": "integer", "minimum": 0, "maximum": 15},
              "detector_reconciliation": {"type": "integer", "minimum": 0, "maximum": 10},
              "production_fixes": {"type": "integer", "minimum": 0, "maximum": 20},
              "evidence_scope": {"type": "integer", "minimum": 0, "maximum": 10}
            }
          },
          "total": {"type": "integer", "minimum": 0, "maximum": 100},
          "summary": {"type": "string", "minLength": 20}
        },
        "additionalProperties": false
      }
    },
    "winner": {"enum": ["A", "B", "C"]},
    "rationale": {"type": "string", "minLength": 40}
  },
  "additionalProperties": false
}
```

## Output A

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


## Output B

## 1) Sequencing + verdict

**Correct sequence:** static audit and baseline plan → P0 correctness/recovery hardening → accessibility/responsive/hostile-data hardening → measured performance optimization → small visual/motion polish → validation with rollback gates.

**Verdict:** Not production-ready for a 10,000-row operations workflow yet; preserve the existing design system, but fix save integrity, state coverage, accessibility, responsive constraints, and bounded rendering before polish.

---

## 2) Prioritized findings

### F1 — P0: Save failures are silent and recovery is undefined
- **Source evidence:** `catch {}` suppresses `api.save(product)` failures; `saving` is a single global boolean; Escape can close the drawer while save is pending.
- **Runtime hypothesis:** Users may believe inventory changes were saved when they failed, conflicted, timed out, or were interrupted.
- **Fix:** Represent save states explicitly: `idle / dirty / saving / saved / failed / conflict / retrying / offline`. Keep the draft open or confirm close while pending/failed. Surface actionable errors. Preserve local edits until acknowledged by the server.
- **Acceptance:** Failed save, timeout, offline, 409, and retry paths all leave the user with visible status, preserved edits, and a clear next action.

### F2 — P0: Required failure and recovery states are missing
- **Source evidence:** Initial/filter loading renders a blank table body; empty, 401/403, 409, 429, 500, timeout, offline, retry, and partial batch failure states are not represented.
- **Runtime hypothesis:** Operators may see a blank or stale surface and cannot distinguish “no data,” “loading,” “not allowed,” “rate limited,” or “failed.”
- **Fix:** Add state-specific table/body panels and bulk-action summaries: loading skeleton or progress, empty result copy, permission denial, auth expiry, conflict resolution, retry/backoff, offline queue notice, and partial batch result with row-level retry.
- **Acceptance:** Every listed state renders a distinct message, preserves filters/selection/drafts where appropriate, and offers the correct recovery path.

### F3 — P1: 10,000 rows render and filter work is unbounded
- **Source evidence:** `rows.map(...)` renders all rows; source notes say filtering recalculates synchronously on every keystroke.
- **Runtime hypothesis:** Input latency, memory, scroll jank, and long tasks are likely at 10,000 rows, but exact severity needs measurement.
- **Fix:** Bound visible rows via existing table virtualization/windowing, pagination, or server-side paging. Memoize filtered results. Defer or debounce keystroke filtering where acceptable. Avoid re-rendering unchanged rows.
- **Acceptance:** Mounted row count is bounded; filter input p95 and long-task budgets pass on target desktop/tablet hardware.

### F4 — P1: Tablet support conflicts with fixed layout
- **Source evidence:** `.page { min-width: 1180px; }`; fixed grid columns total substantial width; drawer is fixed `520px`.
- **Runtime hypothesis:** Tablet users may hit page-level horizontal overflow, obscured controls, or unreachable bulk/edit actions.
- **Fix:** Keep desktop density, but isolate unavoidable horizontal scroll to the table region, not the whole page. Use responsive column priorities, `minmax()`/`clamp()`, wrapping filters, and `max-width: min(520px, calc(100vw - gutter))` for the drawer.
- **Acceptance:** Critical filters, bulk actions, save/close controls, and drawer content remain reachable on supported tablet widths.

### F5 — P1: Drawer and icon controls are not accessible enough for production
- **Source evidence:** Drawer does not trap focus or block background interaction; icon-only save/close; `.icon-button` is `28px` square and `outline: none`; keyboard navigation, labels, focus-visible, and screen-reader behavior are not described.
- **Runtime hypothesis:** Keyboard and assistive-technology users can lose focus, activate background content, or encounter unnamed controls.
- **Fix:** Add dialog semantics, labelled title, focus trap, background inerting, restore focus on close, visible `:focus-visible`, accessible names for icon buttons, disabled/pending semantics, and effective tablet target size at least project standard or provisionally 44 CSS px.
- **Acceptance:** Full edit flow works by keyboard; screen-reader labels identify controls and status; focus never escapes behind an open drawer.

### F6 — P2: Hostile product data is under-specified
- **Source evidence:** Names can be 1–200 chars; prices may be missing; labels may expand 60%; images may be absent or 8MB; product name is single-line ellipsis.
- **Runtime hypothesis:** Long names, missing prices, translated labels, and absent/large images may cause ambiguity, clipping, layout shift, or upload failures.
- **Fix:** Provide full-name access in drawer/details, robust empty price display such as `—` not `0`, locale-aware formatting, flexible label widths, image placeholders, upload validation, compression guidance, and reserved image dimensions.
- **Acceptance:** 1/20/60/200-char names, missing prices, long translations, no-image rows, and 8MB uploads render predictably.

### F7 — P2: Motion may cause jank and ignores reduced motion
- **Source evidence:** `.product-row, .drawer { transition: all 300ms ease-in; }`.
- **Runtime hypothesis:** Animating `all` across many rows can accidentally animate layout/paint properties and worsen 10,000-row performance.
- **Fix:** Restrict transitions to intentional properties, preferably `transform` and `opacity`; avoid row-wide transitions unless state-specific; add `prefers-reduced-motion` handling.
- **Acceptance:** Drawer animation does not animate layout-heavy properties; reduced-motion users get a non-animated or minimal transition path.

### F8 — P3: Permission-specific affordances and autosave nuance need polish
- **Source evidence:** Permission-specific affordances are not described; autosave status exists in context but not in source behavior.
- **Runtime hypothesis:** Users may attempt unavailable edits or misunderstand whether changes are queued, saving, saved, failed, or blocked by role.
- **Fix:** Disable or hide unauthorized actions per project convention, explain why actions are unavailable, and make autosave status row/drawer-specific where possible.
- **Acceptance:** Users can tell what they may edit, what changed, what is saving, and what needs attention.

---

## 3) Concrete fix set by area

### Hostile data
- Reserve image aspect ratio and show deterministic placeholders.
- Validate large uploads before sending; show size/type errors and retry.
- Treat missing price as missing, not zero.
- Keep row density, but expose full product names in drawer/details and accessible text.
- Test translation expansion and long currency formats.

### Failures and state recovery
- Replace blank table bodies with explicit loading, empty, permission, and error states.
- Add retry semantics for timeout/500/offline; backoff messaging for 429.
- For 409, preserve local draft and show conflict resolution.
- For batch edits, summarize success/failure counts and allow row-level retry.
- Do not clear dirty state until server acknowledgement.

### Responsive layout
- Remove page-level fixed minimum as the primary tablet behavior.
- Let filters wrap and keep bulk action/status controls visible.
- Confine data overflow to the table viewport.
- Make drawer width adaptive and ensure close/save remain visible.
- Define column priority for tablet instead of shrinking every column equally.

### Accessibility
- Use real dialog behavior for the drawer.
- Add accessible names for save/close and all icon-only buttons.
- Restore visible focus styles; do not rely on `outline: none`.
- Add keyboard selection behavior for rows and bulk selection.
- Announce autosave changes through a polite live region.
- Respect reduced motion and maintain effective touch targets.

### Performance
- Establish baseline before choosing the implementation.
- Bound rows with existing project mechanisms first: virtualization, paging, or server pagination.
- Memoize derived filtered rows and avoid full recalculation on unrelated renders.
- Use deferred/debounced filtering only if it preserves the operations workflow.
- Lazy-load thumbnails and reserve dimensions.
- Replace `transition: all` with targeted transitions.

---

## 4) Static signal reconciliation

**Decisive from the provided source/facts:**
- `catch {}` hides save failures.
- Missing listed states are product-state gaps.
- `rows.map` over 10,000 rows is unbounded render work.
- Synchronous filtering on each keystroke is an input hot path.
- Fixed `min-width`, fixed columns, and fixed drawer width are responsive risks.
- Icon-only controls, no focus trap, no background inerting, and removed outline are accessibility risks.
- Missing image dimensions create layout-shift risk.
- `transition: all` is an unsafe motion/performance pattern.

**Needs project/runtime context before final severity or exact remedy:**
- Whether 10,000 rows causes release-blocking latency on target devices.
- Whether existing table primitives already provide virtualization/pagination elsewhere.
- Whether a global focus style replaces `.icon-button { outline: none; }`.
- Whether design tokens already define tablet breakpoints, target sizes, drawer widths, and motion durations.
- Whether backend APIs support conflict details, idempotency, retry-after, server filtering, or partial batch responses.
- Whether image handling is CDN-backed, preprocessed, or client-uploaded directly.

---

## 5) Measurement-first validation and rollback plan

### Baseline before changes
- Measure initial render, filter keystroke latency, scroll smoothness, drawer open/close, save failure paths, image load/layout shift, and mounted DOM row count using the real 10,000-row fixture.
- Cover desktop and supported tablet widths.
- Include normal, empty, long-name, missing-price, absent-image, 8MB-image, unauthorized, conflict, offline, timeout, 429, 500, and partial batch scenarios.

### Provisional acceptance gates, to be ratified by the project
- Filter input p95: ≤100–150 ms on target hardware.
- No individual long task over 50 ms during filtering, scrolling, or drawer open/close.
- Mounted rows bounded to visible rows plus overscan, or page size explicitly capped.
- CLS after image loading: <0.1.
- Drawer open/close must not block input or animate layout-heavy properties.
- Keyboard-only user can filter, select, edit, save, recover from failure, and close safely.
- Save failures must never be silent; edits remain recoverable.
- Tablet viewport keeps critical actions reachable without page-level unusable overflow.

### Rollback conditions
- Revert or feature-flag any table optimization that breaks selection, row identity, keyboard navigation, sticky bulk actions, or edit-drawer ownership.
- Revert any save-state change that drops drafts, duplicates saves, or hides conflicts.
- Revert motion changes that regress reduced-motion behavior or introduce layout jank.
- Do not ship visual polish if P0/P1 correctness, accessibility, and bounded-work gates remain unresolved.


## Output C

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
