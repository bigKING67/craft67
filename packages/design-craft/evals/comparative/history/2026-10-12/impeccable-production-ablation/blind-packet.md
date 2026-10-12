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

## 1. Sequence and verdict

**Sequence:** establish baseline and audit → harden correctness, recovery, accessibility, and responsive behavior → measure and optimize → polish within the existing design system → validate and stage rollout.

**Verdict:** the described surface is not ready for production sign-off: save failures are swallowed, recovery states are absent, and tablet/accessibility risks need hardening before visual polish.

This is a read-only assessment of the supplied snippets and notes. No files were changed; no detector, browser, build, profiler, accessibility-tree inspection, network throttle, or device test was run.

## 2–3. Prioritized findings and concrete repairs

**Priority:** P0 = release blocker; P1 = fix in this hardening cycle; P2 = schedule soon with explicit risk acceptance; P3 = polish backlog. Runtime consequences below remain hypotheses unless directly established by the supplied facts.

### F1 — P0: save failure has no observable recovery contract
- **Source evidence:** `catch {}` discards errors; `saving` returns to `false` after either success or failure. No failure state is represented.
- **Runtime unknown:** whether the drawer interprets resolution as success, dismisses itself, or clears drafts. Silent failure is established here; actual lost edits are not.
- **Repair:** represent dirty, saving, saved, failed, and conflict states explicitly. Show “Saved” only after acknowledgement of the current revision; retain edits on failure and offer a specific recovery action.
- Return an explicit outcome or propagate a typed error; record operational failures without logging product contents or credentials.
- **Acceptance:** reject a save and verify no success indication, no draft loss, an actionable error, and a successful retry of the intended revision.

### F2 — P1: pending saves, dismissal, and bulk updates lack safe ownership
- **Source evidence:** one page-level `saving` boolean; Escape closes the drawer while saving; conflict and partial-batch states are absent.
- **Runtime hypothesis:** if requests overlap, an earlier completion can clear the indicator while a later request is pending; out-of-order writes may overwrite newer edits. Concurrency is not established by this snippet.
- **Repair:** scope mutation state to product/request revision; serialize or coalesce same-product autosaves, and prevent stale responses from updating current UI. Use server version checks where supported.
- Keep drafts and mutation ownership outside the drawer’s mount lifetime. Closing must either safely preserve work and continue saving with visible status, or require an explicit decision; never silently discard it. Aborting a request does not prove the server canceled the write.
- Track bulk selection by stable IDs, not rendered row positions. Make “selected rows” versus “all filtered results” explicit; preserve or explicitly reconcile selection when filters change.
- **Acceptance:** test rapid edits, reversed response order, double activation, drawer close/reopen, route departure, and filter changes. Verify the latest revision and exact selected IDs; retry only failed batch items.

### F3 — P1: operational states are missing
- **Source evidence:** initial/filter loading produces a blank body; empty, authentication, authorization, conflict, rate-limit, server, timeout, offline, retry, and partial-failure states are not represented.
- **Runtime unknown:** API error shape, session recovery, idempotency support, and whether mutation outcomes can be queried.
- **Repair:** implement these states inside existing table/drawer patterns:

| Condition | Render and user action | Context/recovery |
|---|---|---|
| Initial/filter loading | Stable loading rows or progress text; mark results busy. During refiltering, retain prior results with an updating indication. | Preserve filters and selection; do not offer ambiguous bulk actions against stale results. |
| Empty results | Distinguish “No inventory” from “No matches”; offer reset filters where appropriate. | Keep entered filters until explicitly cleared. |
| 401 / 403 | Reauthentication / permission explanation; remove or disable unauthorized actions with a reason. | Preserve authorized draft context securely; recheck permissions after authentication. Server enforcement remains mandatory. |
| 409 | Conflict panel with local and current server values; reload or explicitly reconcile. | Retain local edits; never blindly overwrite. |
| 429 | Rate-limit message and next retry time; honor `Retry-After`. | Preserve work; prevent retry storms. |
| 500 / timeout / offline | Specific error or connection state, with retry/reconnect action. | Keep drafts. For uncertain writes, reconcile server state or use supported idempotency before retrying. |
| Partial batch failure | Success/failure counts and item-level reasons; retry failed items. | Preserve failed selection/drafts; do not resubmit successful items. |

- **Acceptance:** inject each condition and verify its rendered state, permitted action, preserved context, and successful recovery—not merely that an error branch exists.

### F4 — P1: drawer and controls need an accessible interaction contract
- **Source evidence:** no focus or background-interaction containment; Save/Close are icon-only; `.icon-button` is `28px × 28px` with `outline: none`. Labels and keyboard behavior are unspecified.
- **Runtime unknown:** accessible names, replacement focus styling, effective hit areas, table semantics, and whether the drawer is intended to be modal.
- **Repair:** for a modal edit drawer, use the existing dialog pattern: accessible title, initial focus, contained tab order, inert background, and focus return to the opener or a logical surviving row. Coordinate Escape with F2.
- If intentionally nonmodal, do not add modal semantics or a focus trap; instead provide clear keyboard movement between editor and table.
- Provide explicit accessible names for Save, Close, row actions, and checkboxes; retain icon visuals if established. Restore a visible `:focus-visible` indicator.
- Enlarge effective targets to **at least 44 × 44 CSS px provisionally for tablet comfort**, without overlapping targets; the icon itself can remain smaller.
- Preserve semantic table headers and cell associations. Use grid roles only if the corresponding keyboard model is implemented. Announce save/error and selection changes without announcing every keystroke.
- **Acceptance:** complete filtering, selection, editing, saving, and recovery by keyboard and screen reader; verify focus visibility, containment/return, names, and touch target geometry.

### F5 — P1: fixed geometry conflicts with tablet and expanded content
- **Source evidence:** page `min-width: 1180px`; columns `64px 280px 1fr 120px 96px`; drawer width `520px`, height `100vh`; translations may expand by 60%.
- **Runtime hypothesis:** narrower viewports or zoom may cause page-wide scrolling, clipped actions, or an inaccessible drawer footer. Exact breakage depends on surrounding layout and styles.
- **Repair:** remove the page-wide minimum; allow filters and bulk controls to wrap. Keep necessary wide-table overflow within a labeled, keyboard-accessible table scroller.
- Replace rigid content tracks with bounded flexible tracks, including `minmax(0, 1fr)` where appropriate and `min-width: 0` on shrinkable children. Preserve essential columns and workflow rather than switching to an unrelated card layout.
- Cap drawer width at the available viewport (`min(520px, 100%)`), use dynamic viewport height with a fallback, and provide internal scrolling with reachable Save/Close controls. Account for tablet browser chrome and the on-screen keyboard.
- **Acceptance:** supported desktop/tablet widths, portrait/landscape, 200% zoom, and 60%-expanded labels preserve all actions; horizontal overflow is confined to the data region.

### F6 — P2: hostile data and image uploads need explicit handling
- **Source evidence:** names span 1–200 characters and are ellipsized; prices may be missing; images may be absent or 8MB; dimensions are not reserved.
- **Runtime unknown:** full-name disclosure, price formatting, image transformation, upload limits, preview lifetime, and validation.
- **Repair:** retain compact ellipsis where useful, but expose the full name through keyboard/touch-accessible disclosure or the editor—not hover alone. Test unbroken strings, translated labels, and locale-specific number formats.
- Render missing prices as “Not set,” distinct from zero; validate currency and numeric inputs without silent coercion.
- Reserve image dimensions/aspect ratio; use an intentional missing/error placeholder and context-appropriate alternative text.
- Publish upload size/type limits, validate on client and server, and either accept 8MB originals with appropriately sized previews/thumbnails or reject them clearly before upload. Show progress, failure, retry, and cancellation; preserve other edits and retain the previous image until replacement succeeds.
- Release preview object URLs and temporary resources after replacement or teardown.
- **Acceptance:** exercise all stated bounds, missing versus zero prices, broken images, and failed/canceled/retried 8MB uploads; verify layout stability and no lost edits.

### F7 — P1: render/filter work is unbounded relative to the viewport
- **Source evidence:** all 10,000 rows render; filtering recalculates synchronously per keystroke.
- **Runtime hypothesis:** input delay, long commits, scrolling stalls, and excess memory. Their magnitude is unmeasured, so this is not automatically P0.
- **Repair:** baseline first, then introduce an explicit mounted-row/work bound using existing project capabilities. Windowing best preserves continuous scrolling if compatible; pagination requires workflow approval.
- Profile filtering separately: cache reusable normalized data; defer result rendering where useful; debounce remote queries only where appropriate. Deferral alone does not make synchronous filtering cheaper; chunking or worker execution requires measured need.
- Preserve selection, focused-row identity, scroll restoration, and accessible row counts across unmounts. Memoize only demonstrated repeat work; avoid a blanket dependency or memoization pitch.
- **Acceptance:** meet the provisional gates below and repeat F2/F4 workflow checks with rows leaving and re-entering the rendered window.

### F8 — P3: broad transitions need targeted polish
- **Source evidence:** rows and drawer use `transition: all 300ms ease-in`; reduced-motion behavior is unspecified.
- **Runtime unknown:** which properties actually change, whether transitions cause layout/paint work, and whether motion overrides exist.
- **Repair:** transition only intentional properties using existing motion tokens; prefer transform/opacity for drawer movement where suitable. Remove decorative motion under `prefers-reduced-motion`; preserve immediate status feedback.
- **Acceptance:** no unintended dimension/color transitions or delayed interaction; reduced-motion behavior remains complete. Promote priority if runtime evidence reveals a material access or performance problem.

## 4. Static signals: decisive versus contextual

- **Decisive within this supplied description:** swallowed save errors (F1), explicitly missing recovery states (F3), absent drawer containment (F4), and full 10,000-row rendering with per-keystroke filtering (F7). These justify repairs without pretending latency or user harm was measured.
- **Decisive CSS declarations, contextual consequences:** `1180px`, `520px`, `100vh`, and rigid tracks identify constraints, but the cascade, viewport, and scroll ownership determine actual clipping (F5).
- **Strong accessibility signals, not standalone conformance verdicts:** icon-only controls can have accessible names; `outline: none` can have a replacement; a 28px visual box can have a larger effective target. Conversely, 28px alone does not establish failure of a 24px minimum criterion. Inspect actual names, focus, spacing, and hit areas (F4).
- **Conditional correctness risk:** a global boolean becomes unsafe with overlapping operations; it does not prove overlap occurs (F2).
- **Risk rather than measured outcome:** `transition: all` does not prove jank; missing reserved image space does not quantify CLS; an 8MB original does not prove an 8MB table download (F6–F8).
- Ellipsis, fixed dimensions, animation timing, and visual density are not grounds for redesign. Preserve established tokens/components unless concrete usability evidence requires a local exception.

## 5. Measurement-first validation and release gates

**All following checks are planned, not executed.**

1. **Establish a reproducible baseline.** Agree supported desktop/tablet browsers and minimum hardware; use identical 10,000-row fixtures, query sequences, uploads, cache conditions, and network profiles for before/after comparisons. Record device/browser versions and repeated-run distributions.
2. **Measure separate costs.** Capture initial render, typing-to-paint, query-to-settled-results, React commits, longest main-thread tasks, mounted rows, image transfer/decode cost, CLS, and retained memory after repeated drawer/upload cycles. Separate client filtering from network delay.
3. **Ratify provisional budgets before implementation:**
   - Input-to-next-paint p95 ≤ **100ms**; local filter-to-settled-results p95 ≤ **200ms**.
   - No interaction-attributable main-thread task > **100ms**; aim for tasks ≤ **50ms**.
   - Mounted product rows ≤ **200**, subject to measured viewport/overscan requirements.
   - CLS ≤ **0.1** over the defined loading/filter/image scenario.
   - Post-cleanup retained heap growth ≤ **10MB** after 20 drawer/upload cycles, with no sustained upward trend; ratify an absolute peak-memory budget from the baseline device.
   - No unrelated latency metric worsens by more than **10% or 20ms, whichever allowance is larger**; peak heap must not grow by more than **10%**.
4. **Verify correctness before claiming speed.** Exercise F1–F3 with controlled delayed, rejected, reordered, and uncertain responses. Check final server values, draft revision, selected IDs, permission handling, and batch outcomes.
5. **Verify interaction and presentation.** Run F4–F6/F8 across keyboard, screen reader, tablet touch, zoom, expanded translations, reduced motion, and supported themes. Compare against existing design-system exemplars; screenshots alone cannot prove interaction.
6. **Use existing project checks.** Run applicable type, lint, unit/integration, and production-build checks after implementation; do not treat passing compilation as usability or performance acceptance.
7. **Stage and retain rollback.** Ship narrowly scoped changes with a reversible render/filter path; monitor save failures/conflicts, recovery success, task completion, and performance without capturing sensitive content.
8. **Acceptance/rollback:** block release for silent save failure, lost drafts, wrong-item bulk updates, unauthorized mutation, or inaccessible core actions. Roll back an optimization that misses its agreed benefit or breaches regression gates; keep independent correctness repairs. Unverified tablet or recovery paths remain unsigned-off, not implicitly passed.


## Output B

## 1. Sequence and verdict

**Audit → harden → optimize → polish**, with baseline measurement before changes and targeted validation at every stage:
- **Audit:** map states, permissions, data extremes, accessibility requirements, and performance baselines.
- **Harden:** make saves, failures, recovery, drawer interaction, and tablet access safe.
- **Optimize:** address row rendering, filtering, and images without breaking selection or keyboard behavior.
- **Polish:** refine spacing, truncation, motion, and status feedback using existing design-system patterns.

**Verdict:** The supplied description is not ready for production sign-off: save outcomes are unreliable, recovery states are missing, and drawer accessibility is incomplete; runtime performance and tablet usability remain unverified.

This is a read-only assessment of the supplied source facts. No detector, browser, build, profiler, accessibility-tree, network-throttle, or device run was performed.

## 2. Prioritized findings: evidence versus hypotheses

Priorities: **P0** confirmed release-blocking integrity/security issue; **P1** required hardening; **P2** important robustness/performance; **P3** polish. No P0 is conclusively established by the excerpts.

| Priority | Finding | Source evidence | Runtime hypothesis / escalation condition |
|---|---|---|---|
| P1; conditional P0 | Failed saves have no usable outcome | `catch {}` suppresses errors; `saving` returns to false regardless of success | Users may mistake an unsaved edit for a saved one. Escalate to P0 if failure clears drafts, falsely reports success, or causes irreversible loss. |
| P1 | Save status cannot represent overlapping requests | One boolean tracks every invocation | If saves overlap, the first completion can hide another pending save; request ordering could overwrite newer edits, depending on API semantics. |
| P1 | Recovery and batch outcomes are absent | No conflict, authorization, rate-limit, server, timeout, offline, retry, or partial-failure states | Staff may lose context, repeat successful operations, or be unable to recover safely. Backend behavior is not shown. |
| P1 | Drawer interaction is unsafe or ambiguous | No focus/background containment; Escape closes during a pending save; save/close are icon-only | Focus may escape a modal; closure may hide unresolved work. Actual draft persistence and accessible names are unknown. |
| P1 | Tablet fit is structurally constrained | Page minimum width is 1180px; fixed drawer is 520px wide and `100vh` tall | Narrower viewports may cause page-wide overflow or obscure controls, especially with the on-screen keyboard. |
| P1 | Accessible interaction is incomplete | 28px icon buttons, `outline: none`; keyboard behavior, labels, and focus-visible are undescribed | Controls may lack names or visible focus. Rendered semantics, overrides, spacing, and contrast require inspection. |
| P2; promote if task-blocking | Rendering and filtering have unbounded main-thread cost | All 10,000 rows render; filtering recalculates synchronously per keystroke | Input delay, slow drawer updates, and dropped frames are plausible, not measured. |
| P2 | Loading is indistinguishable from missing content | Initial and filter loading show a blank body; no empty-results state | Users may interpret loading as zero stock or a broken screen. |
| P2 | Data and media extremes are unsupported | Names up to 200 characters, missing prices/images, 60% label expansion, 8MB images, no reserved image dimensions | Ambiguous prices, inaccessible truncated names, layout shifts, and excessive transfer/decode cost are possible. |
| P3 | Motion is overly broad | Rows and drawer use `transition: all 300ms ease-in`; no reduced-motion behavior described | Layout properties may animate unintentionally. The affected properties and actual rendering cost need verification. |

## 3. Concrete fixes within the existing surface

### Save integrity, failures, and recovery
- Replace the boolean-only model with explicit **clean, dirty, saving, saved, and error/conflict** states, scoped to the relevant product and revision.
- Report “Saved” only after a confirmed response for that revision; retain edits made while an earlier revision is saving.
- Serialize/coalesce autosaves per product, or use the existing API’s revision/version checks. Ignoring stale responses alone does not prevent stale server writes.
- Preserve the draft on failure. Show a persistent inline error and a clear retry path; do not depend only on transient notifications.
- Define pending-save closure behavior: keep the save/draft alive outside the drawer, or explain why closure is temporarily unavailable. Never silently discard work.
- Confirm discard only when work would actually be lost; successful durable autosaves should not trigger unnecessary prompts.
- Handle failures by meaning:
  - **401:** retain the draft through the approved reauthentication flow.
  - **403:** explain the denied operation and offer an allowed exit; do not retry automatically.
  - **409:** preserve local input, retrieve the latest revision, and provide review/reapply using existing conflict conventions.
  - **429:** respect `Retry-After`, back off, and avoid retry storms.
  - **500/timeout/offline:** preserve work and explain the uncertain outcome; reconcile before retrying mutations that might already have committed.
- Use idempotency support where available; do not assume a client timeout means the server rejected the save.
- For partial batches, show per-item outcomes and counts. Retry only failed eligible items; never silently repeat successful ones.
- Keep selection keyed by stable IDs, not row positions. Clearly distinguish selected visible rows from all matching rows and retain understandable scope across filters.
- Reflect permissions in edit/upload/bulk affordances while retaining server-side authorization. No client-side permission defect proves a backend security flaw.
- If reload recovery is needed, use approved, scoped, expiring draft storage rather than indiscriminately persisting inventory data.

### Hostile data and uploads
- Preserve column alignment while allowing bounded wrapping or truncation. Make full names available through keyboard and touch-accessible existing patterns, not hover alone.
- Show a localized “Not set” for absent prices, distinct from zero; format valid amounts with the correct currency and locale.
- Test long unbroken strings, 200-character names, expanded translations, and applicable bidirectional text. Let grid children shrink with `min-width: 0`.
- Reserve thumbnail space with explicit dimensions or aspect ratio; supply stable absent/broken-image placeholders.
- Use appropriately sized thumbnail assets rather than transferring full 8MB originals for table cells.
- Validate upload type, size, and decodeability on both appropriate client and server boundaries; show limits before selection.
- Represent upload progress, failure, retry, and cancellation. Distinguish uploaded media from media actually attached to a saved product.
- Render names as text; treat client validation as usability support, not a security boundary.

### Loading, empty states, and layout
- Differentiate initial loading, refreshing/filtering, no inventory, no matches, and load failure.
- During refresh, retain prior rows only with an explicit updating indicator; do not present old rows as current results.
- Keep skeletons/placeholders dimensionally stable and avoid announcing each placeholder to assistive technology.
- Replace page-wide fixed minimum sizing with a flexible shell and a deliberately bounded horizontal table-scroll region.
- Preserve the operational columns and table workflow; do not convert everything into cards or silently hide essential data.
- Cap drawer width to the viewport, use a dynamic viewport-height strategy with fallback, and provide internal scrolling with reachable actions.
- Verify tablet portrait/landscape, zoom, long translations, and the on-screen keyboard. Horizontal table scrolling must not force unrelated controls offscreen.

### Accessibility and motion
- Decide whether the existing drawer is modal. If modal, use a labelled dialog, appropriate initial focus, focus containment, inert background, and focus restoration.
- If intentionally nonmodal, do not trap focus or declare modality; provide predictable navigation between editor and table.
- Give save, close, selection, upload, and bulk controls accessible names. Use visible labels where ambiguity warrants them.
- Restore a clearly visible `:focus-visible` style using design tokens; do not remove outlines without an equivalent.
- Prefer approximately 44px touch hit areas for frequent tablet actions while preserving compact icon visuals.
- Preserve native table/header relationships where appropriate. An ARIA grid is not a shortcut: it requires a complete, documented keyboard interaction model.
- Label row checkboxes meaningfully; expose select-all’s mixed state and selection scope.
- Announce save progress/results politely without repeating on every keystroke; associate errors with their affected controls.
- Transition only intended properties. Prefer transform/opacity for drawer motion where suitable, and honor reduced-motion preferences.

### Performance
- Measure first, then bound rendered rows through existing windowing facilities or the least disruptive established paging pattern; do not add a dependency by default.
- Preserve logical row counts, headers, focus, selection, and assistive-technology navigation when windowing. Never recycle a focused row without a safe handoff.
- Separate urgent input updates from expensive filtering; debounce or defer as appropriate, and avoid stale filter results replacing newer ones.
- Cache expensive derivations by their actual inputs. Consider existing server filtering only if its semantics and API support fit the workflow.
- Profile row rerenders before memoizing. Stable props and state isolation may prevent save-status changes from rerendering the full list.
- Lazy-load offscreen thumbnails, request suitable sizes, and release temporary upload preview resources.

## 4. Static signals: decisive versus contextual

**Decisive in the supplied material**
- Save errors are swallowed; success and failure have no distinct representation in the shown state.
- Rendering work scales with the entire 10,000-row array; filtering is synchronous by the supplied note.
- Fixed page/drawer dimensions impose real constraints; image space is not reserved.
- Loading and failure-state coverage is explicitly incomplete.
- `outline: none` removes that outline; `transition: all` indiscriminately opts changed animatable properties into transitions.

**Require project or runtime context**
- A 28px target is not automatically a WCAG minimum-target failure: applicable criteria, spacing, and exceptions matter. It can still be poor tablet ergonomics.
- Icon-only controls are not inherently unnamed; accessible-name markup is not shown.
- Missing focus trapping is a modal-dialog defect, not a universal drawer defect.
- Ellipsis is not inherently inaccessible; full-text access and actual accessible names must be checked.
- `100vh` and fixed widths are risk signals, not proof that every supported viewport fails.
- Ten thousand rows do not establish a specific latency; virtualization is not automatically accessible or necessary in every implementation.
- Broad transitions do not prove layout thrashing; inspect what actually changes.
- Absent permission affordances do not demonstrate missing server authorization.

## 5. Measurement-first validation and rollout

1. **Record a baseline before changes:** use a fixed 10,000-row dataset with long names, missing prices/media, expanded labels, and upload extremes on agreed desktop and tablet profiles.
2. **Measure representative tasks:** initial usable table, filter-to-result latency, input responsiveness, drawer open/edit/save, bulk actions, scrolling, layout shift, image bytes, DOM size, and memory after repeated use.
3. **Inspect interaction paths:** keyboard-only traversal, visible focus, dialog entry/exit, selection semantics, accessible names, save announcements, zoom, reduced motion, and tablet touch/keyboard reachability.
4. **Exercise deterministic failure cases:** overlapping saves, out-of-order responses, timeout after server commit, offline/reconnect, every listed HTTP failure, partial batch success, and close/reopen while dirty or saving.
5. **Agree budgets before implementation:** suggested field targets are p75 INP ≤200ms, CLS ≤0.1, and LCP ≤2.5s where applicable; route-specific filter/save targets must distinguish client work from backend latency.
6. **Acceptance:** no false “Saved,” silent draft loss, duplicate mutation on retry, stale overwrite, or selection-scope error in the test matrix; all critical actions remain reachable and understandable.
7. **Performance acceptance:** demonstrate improvement against the same baseline without regressing correctness, accessibility, supported tablet behavior, or agreed latency/memory budgets.
8. **Roll out incrementally:** separate correctness/state fixes, rendering changes, and visual polish into reversible releases; use existing rollout controls and non-sensitive telemetry.
9. **Rollback triggers:** increased failed/duplicate saves, conflict-related loss, focus/selection regressions, inaccessible actions, or breached performance budgets. Disable the responsible change while retaining independently validated integrity fixes.
10. **Sign-off:** require recorded measurements and recovery-test results. Static cleanup alone is not proof of production readiness.


## Output C

## 1. Sequence and verdict

**Audit → harden → optimize → polish → focused re-audit.** Establish baselines before changes; fix save integrity, recovery, and access first; optimize measured bottlenecks without changing workflow; polish only after behavior is reliable.

**Verdict: Not release-ready as described—silent save failures are a release blocker; accessibility, recovery, tablet layout, and rendering need targeted hardening, not redesign.**

This is a read-only assessment of the supplied snippets and notes. No detector, browser, build, profiler, accessibility-tree inspection, network throttling, or device testing occurred. No files were edited.

**Evidence labels:** **Source** means explicit in the supplied material; **Hypothesis** means a consequence requiring implementation or runtime verification. Missing descriptions are not proof that functionality is absent. No numerical compliance or health score is justified by this partial surface description.

## 2. Prioritized findings

### P0 — Block release

**1. Save failures disappear; completion state cannot establish persistence**
- **Source:** `saveProduct` swallows exceptions with `catch {}` and clears `saving` after success or failure. Failure and recovery states are not represented.
- **Impact:** Operations staff cannot reliably distinguish persisted edits from rejected edits.
- **Hypothesis:** The drawer may display a false “saved” state or discard a failed draft; its internal implementation is not supplied.
- **Fix:** Represent dirty, queued, saving, saved, failed, and conflict states explicitly. Only acknowledge “saved” for the exact revision confirmed by the server. Preserve failed drafts and offer actionable recovery.

### P1 — Fix before release

**2. Concurrent saves and drawer closure have no demonstrated safety contract**
- **Source:** One boolean tracks saving; Escape closes during pending saves.
- **Hypothesis:** If requests overlap, the first completion can clear `saving` while another remains pending; responses may arrive out of order. Closing may lose draft access, though closing alone does not prove cancellation or data loss.
- **Fix:** Track per-product revisions and pending requests; serialize/coalesce saves per product or use version checks. Keep save ownership outside drawer lifetime. Define dirty/pending close behavior explicitly.

**3. Drawer keyboard and assistive-technology behavior is incomplete**
- **Source:** No focus containment or background-interaction restriction; save and close are icon-only; `.icon-button` removes outlines.
- **Hypothesis:** Modal users may reach background controls; accessible names and replacement focus indicators may be missing.
- **Fix:** Establish whether this is modal. If modal, provide a named dialog, initial focus, focus containment, inert background, and focus restoration. If intentionally nonmodal, preserve background access and provide clear keyboard movement between regions; do not falsely mark it modal.
- Add accessible button names and visible keyboard focus. Keep Escape useful, but do not let it silently discard work.

**4. Loading, failures, permissions, and batch recovery are missing**
- **Source:** Blank initial/filter loading; no empty-result, listed failure, retry, or partial-batch states. Permission affordances are unspecified.
- **Impact:** Users cannot distinguish waiting from zero results or choose a safe recovery action.
- **Fix:** Provide the state-specific responses below; preserve filters, drafts, selection, and confirmed outcomes through recoverable failures.

**5. Layout imposes desktop dimensions on tablet use**
- **Source:** `.page` has `min-width: 1180px`; drawer is fixed at `520px × 100vh`; table columns include fixed widths.
- **Hypothesis:** Narrow tablet viewports, zoom, or the software keyboard can produce page overflow or obscure drawer actions; exact behavior depends on surrounding layout.
- **Fix:** Allow the page shell to shrink, contain table overflow locally, and clamp drawer dimensions to available space. Preserve the table workflow rather than replacing it with a different interface.

**6. Rendering and filtering create substantial responsiveness risk**
- **Source:** All 10,000 rows render; filtering recalculates synchronously per keystroke; image space is unreserved.
- **Hypothesis:** Input delay, long render commits, excess memory, and image-driven layout shifts. Magnitudes are unmeasured.
- **Fix:** Measure first, then bound row rendering, separate urgent typing from result work, and reserve image dimensions. Maintain keyboard access and selection semantics.

### P2 — Correct in the hardening pass

**7. Hostile data has incomplete presentation and upload handling**
- **Source:** Names span 1–200 characters and are ellipsized; prices may be missing; labels may expand 60%; images may be absent or 8MB.
- **Hypothesis:** Ambiguous product identification, clipped actions, accidental zero-price display, upload delays, or memory pressure.
- **Fix:** Make full names available without hover dependence, distinguish missing prices from zero, accommodate wrapping, and validate/upload images through explicit states.

**8. Motion and pointer targets need contextual correction**
- **Source:** `transition: all 300ms ease-in`; icon buttons are `28px × 28px`; reduced motion is unspecified.
- **Hypothesis:** Unintended layout animation, sluggish feedback, or difficult tablet activation.
- **Fix:** Transition only necessary properties, usually transform/opacity; remove nonessential travel under reduced motion while preserving status feedback. Aim for roughly 44px touch hit areas without forcing larger visual icons or overlapping targets.

### P3 — Final polish

**9. Refine presentation after state correctness**
- **Source:** The existing system and workflow must remain intact; detailed visual tokens are not supplied.
- **Validation task:** Check status wording, alignment of prices and row actions, focus treatment, truncation affordances, and drawer spacing against existing components.
- **Fix:** Reuse incumbent tokens and patterns; avoid new typography, palette, navigation, or decorative treatments.

**Preserve:** Stable `row.id` keys, recognizable row/drawer workflow, and the existing component system are useful foundations. None needs wholesale replacement.

## 3. Concrete hardening contract

### Hostile data and uploads
- Keep compact name truncation where useful, but expose the full name in the drawer and through a keyboard/touch-accessible disclosure if needed during scanning. Do not rely solely on a `title` tooltip.
- Use `minmax(0, 1fr)`/`min-width: 0` where appropriate; permit translated labels and validation messages to wrap. Test long unbroken strings and 60% label expansion.
- Render missing prices as an explicit unavailable state, never as zero; use locale-aware currency formatting and distinguish invalid input from missing data.
- Reserve thumbnail aspect ratios; show consistent absent/broken-image placeholders. Use meaningful alt text only when images add information beyond adjacent names.
- Enforce documented upload type, byte, and dimension limits client- and server-side. Handle 8MB files deliberately: accept with progress or reject before transfer with the exact limit.
- Provide upload cancellation/retry and preserve the previous image until replacement succeeds. Release temporary preview URLs and avoid loading full originals as list thumbnails.

### Failure and recovery behavior

| State | Required response |
|---|---|
| Initial loading | Labeled, stable loading structure; no misleading empty result. |
| Filter refresh | Keep prior results visibly marked as updating where safe; prevent bulk actions against an ambiguous result scope; ignore stale responses. |
| Empty results | Distinguish an empty inventory from no filter matches; offer clear-filter recovery. |
| 401 | Explain session expiry; preserve drafts under an approved sensitive-data policy and resume after authentication. |
| 403 | Explain the unavailable operation; reflect permissions in affordances, with server authorization authoritative. |
| 409 | Preserve local edits and compare against the current server version; allow deliberate resolution, not silent overwrite. |
| 429 | Honor `Retry-After`; use bounded backoff and show when retry is available. |
| 500 / timeout | Preserve draft and show retry. A timeout may follow a successful write: reconcile or use idempotency before repeating it. |
| Offline | Clearly say changes are not saved. Queue only if durable, authorized recovery semantics exist; otherwise retain the draft and offer retry. |
| Partial batch failure | Show succeeded/failed counts and per-item reasons; retry only failed items and retain their selection. |

- Distinguish “Saved at…” from “Saving…” and “Changes not saved.” Use a restrained live region; associate field errors with their inputs.
- Keep draft and server snapshots separate. Applying an older response must not erase newer typing.
- For dirty closure, offer a clear retain/discard decision where needed. For pending saves, either continue safely after closure with persistent status or explain why closure is temporarily deferred.
- Persist across reload only where explicitly supported and safe; otherwise warn before losing unsaved work. Aborting a client request is not proof the server canceled the write.
- Define bulk selection by stable IDs and explicit scope: visible page, filtered set, or entire inventory. Filtering and virtualization must not silently change that scope.

### Responsive layout and accessibility
- Remove the shell’s hard minimum width; keep necessary two-dimensional table scrolling inside a labeled region. Filters, status, and primary controls should reflow independently.
- Use a drawer width bounded by the viewport, dynamic viewport height with fallback, and an internal scroll area. Keep actions reachable with keyboard open and at zoom; avoid obscuring focused fields.
- Preserve essential columns and access to all data; do not silently hide operational fields to make tablet layouts fit.
- Prefer native table semantics for tabular data and native buttons/checkboxes. Use an ARIA grid only if its complete keyboard interaction is implemented.
- Give row checkboxes product-specific names; expose select-all’s mixed state and selection scope. Ensure keyboard focus survives filtering, row removal, and windowing.
- Test visible focus, accessible names, status announcements, error associations, contrast, and focus not obscured. Contrast cannot be assessed from these snippets.

### Performance without workflow regression
- Baseline row mount cost, typing-to-results latency, commit duration, DOM size, image transfer/decode cost, and memory.
- Bound mounted rows through existing windowing infrastructure or a small scoped implementation; consider pagination only if the current workflow permits it. No new dependency is assumed.
- Preserve logical row counts/positions, focused rows, select-all semantics, and assistive-technology access when windowing.
- Cache normalized search data and avoid unrelated row rerenders where measurements justify it. Deferred rendering alone does not make a synchronous expensive filter cheap; chunk or move computation off-thread if measured cost requires it.
- Load suitably sized thumbnails; lazy-load offscreen images while prioritizing visible ones. Use explicit dimensions and avoid blanket `will-change`.

## 4. Static signals: decisive versus contextual

**Decisive from the supplied source**
- Save rejection is swallowed; the shown state has no error outcome.
- All rows render and filtering is synchronous per keystroke.
- The listed loading/error states are absent.
- Fixed layout constraints, broad transitions, outline removal, and unreserved image dimensions exist.

**Require project or runtime context**
- `outline: none` is not proof of invisible focus if another visible treatment exists; absence of any replacement would be a failure.
- Icon-only is not inherently inaccessible; an icon-only button without an accessible name is.
- A 28px target is below a useful tablet comfort goal, but not automatically below WCAG 2.2 AA’s 24px minimum; actual target size, spacing, and exceptions matter.
- `transition: all` is risky, not proof of dropped frames. The properties that change determine cost.
- `100vh`, fixed widths, ellipsis, and table scrolling are not categorically wrong; containment, viewport behavior, full-text access, and task needs determine impact.
- Missing memoization is not itself a defect; 10,000 rendered rows do not establish a measured latency.
- Missing descriptions of labels, permissions, or reduced motion warrant verification, not invented compliance failures.
- No supplied evidence supports judgments about contrast, bundle size, theming quality, or decorative design-system drift.

## 5. Measurement-first validation and release gates

1. **Record a baseline before intervention:** representative desktop and lower-powered supported tablet; agreed viewport/zoom matrix; 10,000 realistic rows plus long names, missing prices/images, expanded translations, and 8MB uploads.
2. **Instrument task outcomes:** filter latency, save acknowledgment latency, overlapping requests, failure/retry outcomes, mounted rows, render/interaction timing, layout shifts, memory, and transferred image bytes. Exclude sensitive draft content from telemetry.
3. **Exercise deterministic failures:** every listed status, offline/reconnect, out-of-order saves, double activation, close/reopen during save, timeout-after-server-commit, permission change, and mixed batch results.
4. **Validate access manually as well as automatically:** keyboard-only filter/select/edit/save/recover flow; supported screen readers; tablet touch; reduced motion; zoom and expanded text. Automation alone cannot certify these workflows.
5. **Agree numerical budgets before optimizing:** provisional targets might include p75 interaction latency ≤200ms, filter feedback/results within 300ms on the reference dataset/device, and CLS ≤0.1. Separate input responsiveness from result completion and server latency; report tail behavior, not averages alone.
6. **Correctness acceptance:** no silent failures, false saved acknowledgments, stale overwrites, duplicate retry effects, or lost drafts in the test matrix; batch retry affects only failures; selection and permissions remain correct.
7. **Usability acceptance:** all essential tasks work by keyboard and tablet; focus is visible and restored; drawer actions remain reachable; full product identity is accessible; no unintended page-level overflow at supported widths.
8. **Stage changes independently:** save/recovery hardening, layout/accessibility, rendering optimization, then polish. Compare each against the baseline and preserve the current design system.
9. **Rollback gates:** revert a change that introduces data loss, duplicate writes, selection mismatch, inaccessible rows, focus loss, or performance beyond agreed budgets. If a save-integrity fix cannot safely ship, disable the affected write path rather than restoring silent failure.
10. **Final acceptance:** focused regression audit plus monitored staged rollout with explicit ownership of error-rate and latency thresholds; do not treat visual polish or a clean static scan as release evidence.
