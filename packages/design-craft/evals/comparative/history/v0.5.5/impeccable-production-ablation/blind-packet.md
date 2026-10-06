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

## 1. Sequencing + verdict

**Correct sequence:** audit evidence boundaries → harden save/error/state recovery → fix accessibility and permissions → optimize table/filter/image hot paths → tablet/responsive adjustments → motion/visual polish.

**One-line verdict:** This surface has enough static evidence of production risk that polish should wait until save failure handling, drawer accessibility, failure states, and 10,000-row rendering are hardened and measured.

---

## 2. Prioritized findings

### P0 — Silent save failure can create false confidence and unrecoverable edits

**Source evidence**
- `catch {}` swallows save errors.
- `saving` is reset without representing failure, retry, conflict, offline, timeout, or partial success.
- Additional notes explicitly say 401/403, 409, 429, 500, timeout, offline, retry, and partial batch failure states are not represented.

**Runtime hypothesis**
- Operators may believe a product was saved when it was not.
- Last-write-wins or conflict overwrites may happen if 409 handling is absent.
- Pending local edits may be lost if the drawer closes, route changes, or auth expires.

**Fix**
- Replace silent catch with explicit save state: `idle | saving | saved | failed | conflict | offline | unauthorized | rateLimited`.
- Preserve dirty draft after failure.
- Block destructive close while save is pending or require confirmation.
- Surface retry with stable error copy.
- For 409, show conflict resolution: keep mine, reload server value, or compare changed fields.
- For partial batch failure, report affected count and failed row IDs.

---

### P0 — Drawer interaction is unsafe and inaccessible

**Source evidence**
- Drawer traps neither focus nor background interaction.
- Escape closes it even while save is pending.
- Save and close are icon-only.
- `.icon-button { width: 28px; height: 28px; outline: none; }`

**Runtime hypothesis**
- Keyboard users can tab behind the drawer and activate background controls.
- Screen-reader users may not know the drawer opened or what icon-only controls do.
- Operators can accidentally dismiss the drawer during a pending save.

**Fix**
- Treat drawer as a modal or clearly non-modal panel; if modal, add focus trap, initial focus, return focus, inert/background blocking, and Escape behavior rules.
- Disable or confirm close while save is pending.
- Add accessible names to icon-only save/close controls.
- Restore visible focus using `:focus-visible`, not `outline: none`.
- Increase hit target to at least a comfortable operations size; 28px is too small for repeated desktop/tablet use.

---

### P0 — Blank loading and missing failure states obscure system status

**Source evidence**
- Initial and filter loading render a blank table body.
- Empty, auth, conflict, rate-limit, server error, timeout, offline, retry, and partial failure states are not represented.

**Runtime hypothesis**
- Operators cannot distinguish “loading,” “no results,” “not allowed,” “offline,” and “broken.”
- Filter changes may appear to delete rows temporarily.

**Fix**
- Add distinct table-body states:
  - initial loading skeleton or progress row,
  - filtering/loading state that preserves previous results when safe,
  - empty results with active filter summary,
  - unauthorized/forbidden state with permission-specific explanation,
  - retryable network/server state,
  - conflict state,
  - offline state,
  - partial batch result state.
- Keep table headers and layout stable while body state changes.

---

### P1 — Rendering all 10,000 rows and filtering on every keystroke is a hot-path risk

**Source evidence**
- `{rows.map(...)}`
- All 10,000 rows render at once.
- Filtering recalculates synchronously on every keystroke.
- Route includes bulk selection and edit drawer, which likely increase row interaction cost.

**Runtime hypothesis**
- Keystrokes may block the main thread.
- Bulk selection may trigger large re-renders.
- Drawer edits may cause unrelated rows to re-render if state is broad.
- Tablet support may be especially sensitive.

**Fix**
- Virtualize or window the table body while preserving keyboard navigation and selection semantics.
- Debounce or defer filter computation.
- Memoize derived filtered rows with correct dependencies.
- Keep selection state normalized by row ID.
- Memoize row components where useful.
- Avoid passing unstable object/function props into every row.
- Keep autosave state scoped to the edited product rather than global `saving` if multiple row/drawer states can coexist.

---

### P1 — Global `saving` state is too coarse for product-level editing

**Source evidence**
- `const [saving, setSaving] = useState(false);`
- `EditDrawer onSave={saveProduct} saving={saving}`

**Runtime hypothesis**
- One product save can disable or misrepresent unrelated actions.
- Concurrent saves, autosave, or retry behavior may become ambiguous.
- Save status may not map to the edited product after selection changes.

**Fix**
- Track save status per draft/product ID.
- Bind drawer state to a stable selected product ID and draft version.
- Ignore stale save responses if the drawer has moved to another product.
- Use request IDs or abort signals for superseded saves.

---

### P1 — Permission-specific affordances are missing

**Source evidence**
- Permission-specific affordances are not described.
- 401/403 states are not represented.

**Runtime hypothesis**
- Users may see controls they cannot use.
- Failed save attempts may be mistaken for product errors instead of access limits.

**Fix**
- Disable or hide restricted actions according to product policy.
- Explain why an action is unavailable.
- Use 401 for session recovery and 403 for permission explanation.
- Prevent bulk actions from starting if selected rows include unauthorized items, or clearly split allowed/blocked results.

---

### P2 — Hostile product data can break layout and comprehension

**Source evidence**
- Product names may be 1–200 characters.
- Prices may be missing.
- Translations may expand labels by 60%.
- Some images are absent or 8MB.
- `.product-name { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }`
- Fixed row grid: `64px 280px 1fr 120px 96px`.

**Runtime hypothesis**
- Important product distinctions may be hidden by truncation.
- Missing prices may look like loading or zero.
- Expanded translations may collide with fixed columns.
- Large images may delay interaction or cause memory/network pressure.

**Fix**
- Keep truncation but provide accessible full-name disclosure where appropriate.
- Use stable missing-value treatments such as “Not set” or an em dash with accessible label.
- Reserve image dimensions and show absent-image placeholders.
- Validate/upload-compress 8MB images with progress and recoverable errors.
- Test long names, missing fields, long localized labels, and dense numeric values in the existing table layout.
- Allow critical columns to shrink/wrap according to priority instead of relying only on fixed widths.

---

### P2 — Tablet support is contradicted by fixed minimum width

**Source evidence**
- `.page { min-width: 1180px; }`
- Desktop-first with tablet support is required.

**Runtime hypothesis**
- Tablets may require horizontal scrolling or clipped drawer/table content.
- Fixed 520px drawer may dominate smaller tablet widths.

**Fix**
- Keep desktop layout intact, but define tablet behavior:
  - table horizontal scroll with sticky key columns, or
  - reduced column set with details in drawer, or
  - drawer width using `min()`, `max()`, and viewport constraints.
- Ensure filters, bulk actions, and drawer controls remain reachable at tablet widths.
- Do not introduce a new mobile workflow unless required; this is tablet accommodation, not redesign.

---

### P2 — Motion is broad, potentially expensive, and ignores reduced motion

**Source evidence**
- `.product-row, .drawer { transition: all 300ms ease-in; }`
- Reduced motion is not described.

**Runtime hypothesis**
- `transition: all` may animate layout-affecting properties.
- Row transitions across thousands of elements may add jank.
- Motion may be uncomfortable or misleading for users with reduced-motion preferences.

**Fix**
- Replace `transition: all` with explicit properties, preferably `transform` and `opacity` for drawer movement.
- Avoid transitions on every row by default.
- Add `prefers-reduced-motion` handling that preserves state feedback without unnecessary movement.
- Use faster, calmer easing for operations work; avoid sluggish ease-in on frequent interactions.

---

### P2 — Image dimensions are not reserved

**Source evidence**
- Image dimensions are not reserved.
- Some images are absent or 8MB.

**Runtime hypothesis**
- Rows may shift as images load.
- Large assets may harm initial render, scrolling, and memory.

**Fix**
- Reserve fixed image slots in the row grid.
- Add placeholders and broken-image fallback.
- Use thumbnail URLs for table rows.
- Lazy-load offscreen images if compatible with virtualization.
- Validate upload size/type and show upload progress/error states.

---

### P3 — Visual polish should focus on clarity, not redesign

**Source evidence**
- Existing design system and workflow must be preserved.
- Production hardening/polish task, not redesign or new dependency pitch.

**Runtime hypothesis**
- Adding decorative treatment before state/performance fixes could hide real production problems.

**Fix**
- Preserve current layout and component vocabulary.
- Improve hierarchy through spacing, labels, stable status placement, and clear disabled/error states.
- Keep autosave feedback close to the edited object.
- Avoid decorative gradients, new card systems, or broad visual resets.

---

## 3. Concrete fixes by area

### Hostile data
- Long names: stable truncation, accessible full value, no row-height explosions.
- Missing prices: explicit missing state, not blank or zero.
- Expanded translations: test 60% longer labels in filters, drawer actions, bulk toolbar, and table headers.
- Absent images: reserved placeholder.
- 8MB images: upload validation, compression/resizing path, progress, retry, and failure copy.
- Unknown/malformed fields: safe fallback rendering and logging hooks.

### Failures
- Represent 401, 403, 409, 429, 500, timeout, offline, and partial batch failure distinctly.
- Never swallow save errors.
- Preserve user edits after failed save.
- Provide retry where safe.
- Use conflict-specific recovery instead of generic “failed.”
- Keep previous table results visible during filter refetch unless stale visibility is unsafe.

### Responsive layout
- Replace fixed-only `min-width: 1180px` with a defined tablet strategy.
- Constrain drawer width to viewport.
- Ensure filters and bulk controls do not overflow.
- Preserve table readability with sticky identifiers or controlled horizontal scroll.
- Validate pointer target sizes for tablet use.

### Accessibility
- Drawer: role/name, focus trap if modal, initial focus, return focus, background inertness.
- Icon buttons: accessible names and visible focus.
- Keyboard: row navigation, selection, drawer open/close, save/cancel, filter traversal.
- Status: autosave and error messages announced without stealing focus.
- Motion: reduced-motion mode.
- Contrast and focus-visible states must be preserved by the design system.

### State recovery
- Draft state survives save failure, auth refresh, retry, and drawer accidental close attempts.
- Save requests are tied to product ID and draft version.
- Stale responses cannot overwrite newer edits.
- Pending uploads survive transient network failure where feasible.
- Bulk operations report exact successes/failures.

### Performance
- Window 10,000-row rendering.
- Defer/debounce filter work.
- Memoize derived rows.
- Normalize row and selection state.
- Reserve image dimensions and use thumbnails.
- Avoid broad state updates that re-render every row.
- Limit animation to the drawer and targeted state changes.

---

## 4. Static detector-like signals: decisive vs context-dependent

### Decisive from the provided source
- Empty `catch {}` is a production hardening failure.
- Blank table body for loading is an insufficient state model.
- Missing explicit error/empty/auth/conflict/rate-limit/offline states is a production gap.
- `outline: none` without replacement focus styling is an accessibility risk.
- Icon-only save/close without described labels is an accessibility risk.
- No drawer focus trap/background blocking is unsafe if the drawer functions as a modal editor.
- `transition: all` is too broad for predictable production motion.
- Rendering all 10,000 rows at once is a known performance risk.
- Synchronous filtering on each keystroke is a hot-path risk.
- Fixed `min-width: 1180px` conflicts with tablet support unless a separate tablet strategy exists.

### Needs project/runtime context
- Exact frame drops, input latency, memory use, and scroll performance.
- Whether `ProductRow` is lightweight enough to delay virtualization urgency.
- Whether the drawer is intended to be modal or non-modal.
- Whether accessible names exist deeper inside reusable components.
- Actual focus order and screen-reader announcements.
- Whether API already performs conflict detection, retries, or idempotency.
- Whether images are already served as thumbnails by infrastructure.
- Actual tablet breakpoints, supported devices, and operator hardware.
- Whether permissions are encoded in product data, session data, or route guards.

---

## 5. Measurement-first validation plan with rollback/acceptance

### Baseline before changes
- Record current 10,000-row initial render time, filter keystroke latency, scroll smoothness, memory, and image load behavior.
- Record save flows for success, failure, timeout, offline, 401/403, 409, 429, and 500 using controlled responses.
- Record keyboard path through filters, table, bulk selection, drawer, save, cancel, and close.
- Record tablet-width layout behavior.
- Record reduced-motion behavior.

### Acceptance conditions
- Save failures are visible, recoverable, and never reported as success.
- Dirty edits are preserved across retryable failures.
- Conflict handling prevents silent overwrite.
- Drawer focus behavior is deterministic and keyboard-safe.
- Icon-only controls have accessible names and visible focus.
- Loading, empty, auth, offline, server error, rate-limit, timeout, conflict, and partial batch states are represented.
- 10,000-row table remains responsive during scroll and filtering within agreed product latency budgets.
- Image slots do not cause layout shift.
- Tablet layout keeps primary actions reachable.
- Reduced-motion mode removes nonessential movement while preserving status feedback.

### Rollback conditions
- Virtualization breaks selection, keyboard navigation, or screen-reader access.
- Save-state changes introduce duplicate saves or stale overwrites.
- Drawer focus management traps users or blocks required background workflow.
- Tablet changes degrade the primary desktop workflow.
- Image handling blocks valid uploads without clear recovery.
- Error-state handling hides actionable product data.

### Rollout approach
- Ship save/error-state hardening first behind the existing workflow.
- Then add drawer accessibility and close-pending safeguards.
- Then optimize rendering/filtering with measured before/after results.
- Then handle tablet and hostile-data polish.
- Keep changes reversible and avoid new dependencies unless measurement proves the existing stack cannot meet the target.


## Output B

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


## Output C

## 1) Sequence and verdict

**Correct sequence:** audit static evidence and define baseline → harden data/failure/accessibility/state recovery → measure hot paths → optimize only proven or source-obvious bottlenecks → polish motion/layout within the existing system.

**One-line verdict:** This surface is not production-ready for a 10,000-row, keyboard-heavy operations workflow because static evidence shows silent save failure, missing recovery states, unsafe drawer behavior, unbounded rendering, and unresolved accessibility/responsive contracts.

## 2) Prioritized findings

### P0 — Data integrity and recovery are unsafe
**Source evidence:**  
- `catch {}` swallows save failures.  
- `setSaving(false)` runs after failure without any error state.  
- 409 conflict, timeout, offline, retry, and partial batch failure states are explicitly absent.  
- Escape closes the drawer while save is pending.

**Runtime hypothesis:** Actual data loss depends on API semantics and whether unsaved edits are kept elsewhere, but the shown code cannot prove that failed saves are visible or recoverable.

**Fix:**  
- Replace silent catch with explicit save result state: `idle | saving | saved | failed | conflict | offline | retrying`.  
- Keep failed edits in the drawer; do not clear or close on failed save.  
- Block or confirm drawer close while saving or dirty.  
- Add conflict UI showing server value, local value, and user action: reload, overwrite if permitted, or merge.  
- For batch edits, report succeeded, failed, skipped, and retryable rows.

### P1 — Loading, empty, auth, rate-limit, server, and permission states are missing
**Source evidence:**  
- Initial and filter loading render a blank table body.  
- Empty results, 401/403, 429, 500, timeout, offline, retry, and permission-specific affordances are not represented.

**Runtime hypothesis:** Backend may return structured errors, but no UI contract is described for them.

**Fix:**  
- Initial loading: render table skeleton or stable rows shell, not blank disappearance.  
- Filter loading: keep previous results visible with “Updating…” status.  
- Empty results: show active filters, clear-filter action, and no-results explanation.  
- 401/403: show re-auth or permission explanation; hide/disable actions the user cannot perform.  
- 429: show retry-after messaging and disabled save until allowed.  
- 500/timeout/offline: show retry, preserved edits, and last successful autosave time.  
- Partial batch failure: keep selection and show per-row failure reasons.

### P1 — Drawer interaction is not safe or accessible
**Source evidence:**  
- Drawer traps neither focus nor background interaction.  
- Escape closes it while save is pending.  
- Save and close are icon-only.  
- `.icon-button { width: 28px; height: 28px; outline: none; }`.

**Runtime hypothesis:** Component internals could add ARIA labels or focus styles elsewhere, but the supplied notes say labels/focus-visible are not described.

**Fix:**  
- Treat drawer as a modal or explicitly non-modal panel; for editing, modal behavior is safer.  
- On open: move focus to drawer heading or first editable field.  
- Trap focus inside while open; restore focus to invoking row on close.  
- Prevent background row interaction while modal drawer is open.  
- Add accessible names to icon-only save/close controls.  
- Replace `outline: none` with visible `:focus-visible` styling.  
- Disable close or require confirmation during pending save/dirty state.

### P1 — 10,000-row rendering and synchronous filtering are hot-path risks
**Source evidence:**  
- `{rows.map(...)}` renders all rows.  
- Product context says 10,000-row product table.  
- Filtering recalculates synchronously on every keystroke.

**Runtime hypothesis:** Actual frame drops, input latency, and memory cost require measurement, but the source shape is a decisive scalability smell.

**Fix:**  
- Virtualize visible rows while preserving keyboard navigation and selection semantics.  
- Debounce or defer filter input work; keep typing responsive.  
- Memoize filtered/sorted row derivations with correct dependencies.  
- Avoid recreating row props and handlers unnecessarily.  
- Move expensive normalization/search indexing out of the keystroke path.  
- Keep bulk selection state independent from rendered row count.

### P1 — Tablet support conflicts with fixed desktop geometry
**Source evidence:**  
- `.page { min-width: 1180px; }`.  
- Drawer fixed at `width: 520px; height: 100vh`.  
- Grid columns are fixed-heavy: `64px 280px 1fr 120px 96px`.  
- Tablet behavior is not described.

**Runtime hypothesis:** Horizontal scrolling may be acceptable for dense tables, but critical controls must remain reachable and drawer must fit.

**Fix:**  
- Keep desktop density, but isolate horizontal overflow to the table region, not the whole page.  
- Make filters, autosave status, and primary actions remain visible above/around the scroll container.  
- Bound drawer width: `min(520px, 100vw)` or use full-screen drawer on narrower tablet widths.  
- Preserve row identity/action columns when horizontally scrolling.  
- Define tablet breakpoints for filters, drawer, and bulk-action bar.

### P2 — Hostile data is not contained
**Source evidence:**  
- Product names can be 1–200 characters.  
- Prices may be missing.  
- Translations may expand labels by 60%.  
- Some images are absent or 8MB.  
- Product names use nowrap ellipsis only.  
- Image dimensions are not reserved.

**Runtime hypothesis:** Some row components may handle fallback rendering internally, but it is not represented here.

**Fix:**  
- Product names: keep one-line table truncation with tooltip/details in drawer; never let names push action columns away.  
- Prices: render explicit “Missing price” or em dash with validation state, not blank.  
- Translations: test labels at +60%; avoid fixed-width action text where labels expand.  
- Images: reserve dimensions/aspect ratio; lazy-load thumbnails; show absent-image fallback.  
- Reject or process 8MB uploads with visible compression/progress/error state.

### P2 — Motion choices are broad and may harm performance/accessibility
**Source evidence:**  
- `.product-row, .drawer { transition: all 300ms ease-in; }`.  
- Reduced motion is not described.

**Runtime hypothesis:** Actual animation smoothness needs runtime inspection, but `transition: all` is a strong static risk.

**Fix:**  
- Transition only intended properties, preferably `transform` and `opacity` for drawer entrance.  
- Do not animate layout-affecting table properties.  
- Use shorter, clearer easing for operational feedback; avoid slow ease-in delays on exits.  
- Add reduced-motion path that removes large movement while preserving state feedback.

### P2 — Autosave status is too coarse
**Source evidence:**  
- Single `saving` boolean is passed to `EditDrawer`.  
- Save failures are swallowed.  
- Autosave status exists in product context but not represented as durable state.

**Runtime hypothesis:** The single boolean proves coarse ownership, not necessarily all concurrency behavior; overlapping saves need project context.

**Fix:**  
- Track per-product save status and last saved timestamp.  
- Distinguish saving, saved, failed, offline queued, and conflict.  
- Prevent stale responses from overwriting newer edits.  
- If autosave batches, expose queue depth and partial failures.

### P3 — Visual polish should follow hardening, not mask it
**Source evidence:**  
- Existing design system/workflow must be preserved.  
- Several missing states and data contracts precede visual refinement.

**Runtime hypothesis:** Actual visual hierarchy cannot be fully judged from the snippet alone.

**Fix:**  
- After state/performance fixes, polish density, row scanning, focus rings, status placement, and drawer transitions using existing tokens.  
- Do not introduce decorative layouts, new component paradigms, or new dependencies as the first move.

## 3) Concrete fix coverage by area

- **Hostile data:** bounded text, explicit missing values, i18n expansion checks, reserved image boxes, upload size/progress/error handling.  
- **Failures:** typed error states for auth, permission, conflict, rate limit, server, timeout, offline, retry, and partial batch failure.  
- **Responsive layout:** table-contained overflow, reachable controls, bounded drawer, tablet-specific drawer/filter behavior.  
- **Accessibility:** focus trap/restoration, labeled icon buttons, visible focus, keyboard row navigation, reduced motion, permission-aware disabled states.  
- **State recovery:** dirty-state guard, pending-save close protection, preserved failed edits, retry queue, conflict resolution.  
- **Performance:** virtualization, deferred filtering, memoized derived data, stable row props, reserved image dimensions, measured render/input budgets.

## 4) Static detector-like signal reconciliation

**Decisive from supplied static evidence:**  
- Empty `catch {}` means save errors are swallowed in the shown save path.  
- Missing represented states are decisive because the prompt explicitly says they are absent.  
- Rendering `rows.map` for all rows is decisive for unvirtualized rendering in the shown component.  
- `min-width: 1180px`, fixed drawer width, fixed grid columns, `transition: all`, and `outline: none` are real static CSS risks.  
- Notes that focus trap, background interaction blocking, tablet behavior, screen-reader labels, focus-visible, and reduced motion are not described are decisive gaps in the supplied scope.

**Needs project/runtime context before final severity or implementation choice:**  
- Actual input latency, scroll FPS, memory pressure, layout shift, and animation smoothness.  
- Whether row internals already provide ARIA labels, fallbacks, or keyboard shortcuts.  
- Whether horizontal scrolling is an accepted table pattern for this product.  
- Whether API provides retry-after, conflict payloads, idempotency keys, or offline queue support.  
- Whether the drawer is intended to be modal or a persistent side panel.  
- Whether the single `saving` boolean creates real concurrency bugs across multiple save paths.

## 5) Measurement-first validation plan

**Baseline before changes:**  
- Record render time, input latency while filtering, scroll responsiveness, memory, and image layout shift with 10,000 representative rows.  
- Capture state matrix coverage: loading, empty, 401/403, 409, 429, 500, timeout, offline, retry, partial batch failure.  
- Audit keyboard path: filters → table rows → bulk actions → drawer → save/close → focus restore.  
- Verify tablet viewport behavior for table overflow, drawer width, and action reachability.

**Acceptance conditions:**  
- Failed save is visible, recoverable, and does not falsely appear saved.  
- Dirty or saving drawer cannot be accidentally dismissed without protection.  
- All named failure states render actionable UI while preserving user context.  
- 10,000-row filtering remains responsive under representative data.  
- Only visible rows render, without breaking selection or keyboard navigation.  
- Icon-only controls have accessible names and visible focus.  
- Drawer focus behavior is deterministic.  
- Reduced-motion users still receive status feedback without large motion.  
- Tablet users can reach filters, rows, bulk actions, drawer actions, and autosave status.

**Rollback conditions:**  
- Virtualization breaks selection, row focus, screen-reader navigation, or bulk actions.  
- Error-state handling hides recoverable edits or causes duplicate saves.  
- Drawer focus trap blocks legitimate background workflow if the product requires non-modal editing.  
- Responsive changes make dense desktop scanning materially worse.  
- Motion changes obscure state transitions or violate reduced-motion behavior.
