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


## Output B

## 1. Sequencing + verdict

**Correct sequence:** static audit → production hardening for save/error/state recovery → performance optimization for 10k-row workflows → responsive/accessibility fixes → visual/motion polish within the existing system → measured rollout with rollback gates.

**Verdict:** **Not production-ready for an operations-critical inventory editor**: the surface risks silent data loss, keyboard/a11y exclusion, tablet breakage, and severe interaction latency under the stated 10,000-row workload.

---

## 2. Prioritized findings: evidence vs runtime hypotheses

### P0 — Blocking

#### P0.1 Silent save failure can cause data loss
- **Source evidence:** `catch {}` swallows `api.save(product)` failures; `setSaving(false)` runs with no error, retry, rollback, or conflict state.
- **Runtime hypothesis:** severity depends on whether autosave/draft recovery exists elsewhere, but the shown save path is unsafe.
- **Impact:** operators may believe edits were saved when they were not.

#### P0.2 Drawer can close during pending save
- **Source evidence:** notes say Escape closes the drawer even while save is pending.
- **Runtime hypothesis:** data loss risk depends on whether pending edits are persisted elsewhere.
- **Impact:** easy accidental loss or ambiguous state during repeated keyboard use.

#### P0.3 No represented recovery paths for common production failures
- **Source evidence:** empty results, 401/403, 409, 429, 500, timeout, offline, retry, and partial batch failure states are not represented.
- **Runtime hypothesis:** backend may return these correctly, but the UI contract is missing.
- **Impact:** users cannot distinguish “no data,” “still loading,” “permission denied,” “conflict,” and “failed save.”

---

### P1 — Major before release

#### P1.1 10,000 rows render synchronously
- **Source evidence:** `{rows.map(...)}` renders all rows; notes confirm all 10,000 rows render at once.
- **Runtime hypothesis:** actual latency depends on row complexity, images, and browser/device, but this is a decisive hot-path risk.
- **Impact:** slow initial render, expensive updates, keyboard lag, poor tablet behavior.

#### P1.2 Filtering recalculates on every keystroke
- **Source evidence:** notes say filtering recalculates synchronously on every keystroke.
- **Runtime hypothesis:** exact cost depends on filter complexity, but 10,000 rows makes this a likely interaction blocker.
- **Impact:** users typing filters may experience jank, dropped input, or delayed results.

#### P1.3 Global `saving` state is too coarse
- **Source evidence:** single `const [saving, setSaving] = useState(false)` controls `EditDrawer`.
- **Runtime hypothesis:** if only one drawer save can happen at a time, global state may be acceptable for the drawer, but not for table autosave/bulk operations.
- **Impact:** one save can block or misrepresent unrelated product actions; partial batch failure is hard to model.

#### P1.4 Drawer lacks modal/dialog accessibility and background isolation
- **Source evidence:** notes say drawer traps neither focus nor background interaction.
- **Runtime hypothesis:** exact screen-reader behavior depends on markup not shown.
- **Impact:** keyboard and assistive-tech users can tab behind the drawer, lose context, or trigger background actions.

#### P1.5 Icon-only save/close controls are not described as labeled
- **Source evidence:** “Save and close are icon-only”; screen-reader labels are not described.
- **Runtime hypothesis:** `aria-label` may exist in omitted markup, but the note flags it as absent/undocumented.
- **Impact:** non-visual users cannot reliably identify destructive or committing actions.

#### P1.6 Focus visibility is explicitly suppressed
- **Source evidence:** `.icon-button { ... outline: none; }`
- **Runtime hypothesis:** if a replacement `:focus-visible` style exists elsewhere, this may be mitigated; none is shown.
- **Impact:** keyboard-heavy operators lose their position in a dense workflow.

#### P1.7 Touch targets are too small for tablet support
- **Source evidence:** `.icon-button { width: 28px; height: 28px; }`
- **Runtime hypothesis:** hit area could be enlarged by padding/wrapper elsewhere, but the class itself fails the expected target size.
- **Impact:** tablet users will mis-tap critical save/close controls.

#### P1.8 Fixed desktop width blocks tablet adaptation
- **Source evidence:** `.page { min-width: 1180px; }`; drawer fixed at `520px`.
- **Runtime hypothesis:** horizontal scrolling may be intentional for dense tables, but tablet behavior is undescribed.
- **Impact:** cramped or clipped controls, unusable drawer/table pairing on narrower viewports.

#### P1.9 `transition: all` on rows and drawer is unsafe
- **Source evidence:** `.product-row, .drawer { transition: all 300ms ease-in; }`
- **Runtime hypothesis:** actual animated properties depend on state classes, but the declaration permits layout/paint-heavy animation.
- **Impact:** jank on row updates, slow drawer motion, inaccessible motion without reduced-motion handling.

---

### P2 — Important hardening

#### P2.1 Blank table body during loading
- **Source evidence:** initial and filter loading render a blank table body.
- **Runtime hypothesis:** if surrounding chrome has status text, impact is reduced; not described.
- **Impact:** users cannot tell whether data is loading, filtered out, or broken.

#### P2.2 Hostile product data is under-modeled
- **Source evidence:** names can be 1–200 chars; prices may be missing; labels may expand 60%; images may be absent or 8MB.
- **Runtime hypothesis:** row components may already format some fields, but CSS suggests only single-line truncation for names.
- **Impact:** broken layout, hidden critical identifiers, misleading price display, image shift or slow loads.

#### P2.3 Image dimensions are not reserved
- **Source evidence:** notes say image dimensions are not reserved.
- **Runtime hypothesis:** actual CLS depends on image placement and table row height.
- **Impact:** table rows can jump during image load; repeated operations become error-prone.

#### P2.4 Permission-specific affordances are not described
- **Source evidence:** permission-specific affordances are absent from notes.
- **Runtime hypothesis:** route guards may exist elsewhere.
- **Impact:** users may see actions they cannot perform, or receive late 403 failures after effort.

---

### P3 — Polish once blockers are fixed

#### P3.1 Product names rely only on ellipsis
- **Source evidence:** `.product-name { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }`
- **Runtime hypothesis:** there may be a detail drawer or title attribute elsewhere.
- **Impact:** operators may lose distinguishing SKU/name details in dense rows.

#### P3.2 Motion timing/easing should be tuned for task UI
- **Source evidence:** `300ms ease-in` on rows/drawer.
- **Runtime hypothesis:** perceived speed depends on actual distance and hardware.
- **Impact:** state changes can feel sluggish; ease-in delays feedback at the start.

---

## 3. Concrete fixes

### Hostile data
- Preserve the existing table system, but make row cells resilient:
  - Use grid columns with `minmax()` and defined overflow behavior instead of brittle fixed widths everywhere.
  - Keep product names single-line by default, but expose full names through an accessible detail affordance, tooltip/popover, or drawer field.
  - Render missing prices as an explicit neutral state: `—`, “No price,” or permission-aware copy, not blank.
  - Support 60% label expansion by avoiding fixed-label buttons where text is expected.
  - Reserve image slots with fixed width/height or aspect ratio.
  - Use placeholders for absent images.
  - Reject or pre-process 8MB uploads with visible size/type guidance, upload progress, retry, and failure copy.

### Failure states
- Replace boolean-only loading/saving with explicit states:
  - `idle`, `initialLoading`, `filtering`, `saving`, `saved`, `error`, `offline`, `conflict`, `unauthorized`, `rateLimited`.
- Add distinct UI for:
  - empty inventory,
  - empty filter results,
  - 401/403 permission failure,
  - 409 conflict with reload/merge/discard choices,
  - 429 backoff message,
  - 500/timeout retry,
  - offline queued draft,
  - partial bulk failure with per-row outcomes.
- Never swallow errors. Surface a durable inline/banner/toast status and preserve unsaved edits.

### Responsive layout
- Remove or conditionally scope `min-width: 1180px`.
- For desktop, keep the dense table; for tablet:
  - allow horizontal table scroll inside a labeled region if density must remain,
  - keep key identifiers sticky,
  - make the drawer width responsive: `min(520px, 100vw)` or a tablet-specific full-width sheet,
  - ensure the drawer does not cover required table actions without an obvious close/back path.
- Define breakpoint behavior for filters, bulk bar, table, and drawer together; do not only shrink columns.

### Accessibility
- Use real buttons for icon actions with accessible names: “Save product,” “Close editor,” “Remove image,” etc.
- Restore visible keyboard focus with `:focus-visible`; do not rely on browser outline removal.
- Increase interactive hit areas to at least 44×44 CSS px for tablet/touch.
- Treat the drawer as a dialog-like surface:
  - focus moves into it on open,
  - focus is contained while open,
  - background is inert or otherwise non-interactive,
  - focus returns to the invoking row/control on close.
- Disable or confirm close/Escape while save is pending.
- Announce autosave status changes through a polite live region.
- Provide keyboard paths for filters, table rows, bulk selection, drawer save/cancel, and image upload.
- Add reduced-motion handling for drawer/row transitions.

### State recovery
- Track dirty state per product, not only global saving.
- Maintain local draft state until save confirmation.
- Add retry with idempotency where backend supports it.
- For conflicts, show what changed and let the user reload, overwrite, or merge.
- For batch operations, report successful, failed, skipped, and pending rows separately.
- Preserve filter, selection, scroll position, and open drawer context across recoverable failures.

### Performance
- Virtualize/window the 10,000-row table using existing project patterns where available.
- Memoize filtered/sorted rows with correct dependencies.
- Debounce or defer filter input work so typing remains responsive.
- Avoid re-rendering every row when `saving` changes; scope save state to the edited product/drawer.
- Keep row components stable with memoized props/callbacks where appropriate.
- Lazy-load thumbnails and reserve dimensions.
- Replace `transition: all` with specific properties, typically `transform`, `opacity`, or color only.
- Add reduced-motion CSS:
  - disable drawer slide/row transitions or shorten to near-instant,
  - preserve state feedback through copy/icon/status changes.

---

## 4. Static detector-like signals: decisive vs context-dependent

### Decisive from the provided source
- `catch {}` with no user-visible error path is unsafe.
- Rendering `{rows.map(...)}` for 10,000 rows is a decisive scalability smell.
- Synchronous filtering on every keystroke is a hot-path risk.
- `outline: none` on icon buttons is an accessibility failure unless replaced elsewhere.
- 28×28 icon buttons are too small for tablet touch targets.
- `transition: all` on rows/drawer is an unsafe motion/performance pattern.
- Fixed `min-width: 1180px` conflicts with stated tablet support.
- Blank loading, absent error states, absent conflict/offline/retry/partial failure states are production hardening gaps.
- Missing drawer focus trap/background isolation is a major modal interaction gap.

### Needs project/runtime context before final severity
- Whether `ProductRow` is memoized or internally expensive.
- Whether the real table has semantic roles, headers, row selection labels, and keyboard behavior.
- Whether design tokens already provide focus rings, motion durations, z-index, and responsive primitives.
- Whether route-level auth/permissions already prevent some 401/403 paths.
- Whether upload processing compresses/rejects 8MB images before rendering.
- Whether autosave has draft persistence outside the shown snippet.
- Exact latency, memory, layout shift, and interaction delay numbers.

---

## 5. Measurement-first validation plan with rollback and acceptance

### Baseline before changes
- Create representative fixtures:
  - 10,000 rows,
  - 200-character names,
  - missing prices,
  - 60% longer labels,
  - absent images,
  - 8MB image cases,
  - 401/403/409/429/500/timeout/offline responses,
  - partial bulk failure.
- Measure initial render, filter keystroke latency, drawer open/close latency, save feedback timing, image layout shift, and row count in the DOM.
- Record keyboard-only task completion for: filter, select bulk rows, open drawer, edit, save, upload image, recover from failed save.

### Acceptance conditions
- No failed save can appear as successful.
- Pending save cannot be lost through Escape/close without an explicit safe outcome.
- 10,000-row route remains responsive during filtering and selection.
- DOM row count is bounded by windowing rather than all 10,000 visible rows.
- Filtering does not block typing perceptibly under the target dataset.
- Drawer focus is contained, background is non-interactive, and focus returns correctly.
- All icon-only controls have accessible names and visible focus.
- Touch targets meet tablet requirements.
- Loading, empty, forbidden, conflict, rate-limit, timeout, offline, retry, and partial failure states are visible and actionable.
- Images reserve space; table layout does not jump during thumbnail loading.
- Reduced-motion users still receive clear state feedback.

### Rollback conditions
- Filter latency or drawer latency regresses beyond agreed baseline.
- Virtualization breaks row selection, keyboard navigation, or scroll restoration.
- Autosave changes increase failed/duplicate saves.
- Conflict handling blocks normal saves or loses drafts.
- Responsive drawer/table changes hide critical bulk or save actions.
- Accessibility fixes trap users, lose focus return, or block assistive-tech navigation.

### Rollout approach
- Ship hardening behind narrow flags where practical: save-state recovery, virtualization, responsive drawer behavior.
- Roll out first to internal/staff accounts with production-like data volume.
- Monitor save failures, retry counts, conflict rates, upload failures, and client-side error reports.
- Keep a one-step fallback for table virtualization and drawer behavior until metrics and support feedback are stable.


## Output C

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
