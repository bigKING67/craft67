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

# Blind scorecard

| Criterion | Weight | Full-credit evidence |
| --- | ---: | --- |
| Mode sequencing and prioritization | 10 | Chooses audit before targeted polish/harden/optimize, preserves scope, and assigns coherent P0-P3 severity. |
| Hostile data and failure hardening | 20 | Covers long/missing data, permissions, conflicts, rate limits, offline/timeouts, retry, partial failure, uploads, and truthful save recovery. |
| Responsive and accessibility quality | 15 | Repairs fixed geometry, drawer behavior, keyboard/focus/labels/touch targets, translations, reduced motion, and tablet adaptation. |
| Measurement-first performance | 15 | Identifies render/filter/image/layout hot paths, requires baselines and thresholds, and avoids unmeasured optimization claims. |
| Detector and design-system reconciliation | 10 | Treats transition-all, ease-in, outline removal, fixed sizes, and missing dimensions as contextual signals under project authority. |
| Concrete production fixes | 20 | Provides implementation-ready state, error, layout, accessibility, data-scale, and recovery moves with acceptance conditions. |
| Evidence honesty and scope control | 10 | Separates static proof from runtime hypotheses, avoids claiming tools ran, stays read-only, and does not redesign or add unjustified dependencies. |

Total: 100.


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


## Output B

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


## Output C

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
