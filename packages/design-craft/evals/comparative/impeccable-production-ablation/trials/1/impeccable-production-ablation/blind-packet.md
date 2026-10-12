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

**Sequence:** audit → harden critical behavior and recovery → polish within the existing design system → optimize measured bottlenecks → validate and stage rollout. Establish baselines before changes; promote performance work earlier if it blocks task completion.

**Verdict:** The supplied source shows release-blocking save/recovery gaps and substantial interaction, accessibility, and scale risks; targeted hardening—not a redesign—is required.

**Scope:** Read-only assessment of the supplied snippets and notes. No detector, browser, build, profiler, accessibility-tree, network-throttle, or device execution occurred. Severity reflects potential operational impact, not measured incident frequency.

## 2. Prioritized findings

**Evidence** means directly shown or explicitly stated. **Hypothesis** means an impact or behavior requiring project/runtime verification.

| Priority | Finding | Source evidence | Runtime hypothesis / qualification |
|---|---|---|---|
| **P0 — release gate** | Failed saves are hidden from this UI | `catch {}` discards errors; `saving` returns to `false`; failure/retry states are absent | Staff may believe an unsaved edit persisted. Exact saved-status wording and any API-layer reporting need verification |
| **P1** | Save state cannot safely describe overlapping requests | One shared boolean; no request identity or sequencing shown | If saves overlap, an earlier completion can clear the indicator while another is pending; stale writes depend on API behavior |
| **P1** | Drawer dismissal and recovery are unsafe or undefined | Escape closes during save; no focus trap or background-interaction isolation | Closing may strand an uncertain save or lose a draft; actual persistence/unmount behavior is unknown |
| **P1** | Bulk operations and conflict recovery lack represented outcomes | Partial failure, 409, retry, and permission states absent | Users may retry successful items, overwrite newer data, or lose selection without per-item outcomes |
| **P1** | Loading and errors cannot be distinguished from absence | Initial/filter loading leaves a blank body; empty/error states absent | Staff may interpret loading or failure as “no inventory” |
| **P1** | Accessibility essentials are missing or unverified | 28px icon buttons remove outlines; Save/Close are icon-only; labels and keyboard behavior unspecified | Accessible names may exist elsewhere; keyboard focus visibility and complete task operability require inspection |
| **P1** | Tablet layout has a structural width constraint | `.page { min-width: 1180px }`; fixed 520px drawer; `height: 100vh` | Narrow viewports likely overflow; controls or actions may be obscured by browser chrome or an on-screen keyboard |
| **P1** | Scale risks are built into the render/filter path | All 10,000 rows mount; filtering recalculates synchronously per keystroke | Long input latency, costly commits, excess memory, and scroll stalls are likely but not measured |
| **P2** | Content resilience is incomplete | Names truncate; missing prices/images; 60% label expansion; images can be 8MB; no reserved dimensions | Critical identifiers may be indistinguishable; labels may clip; image arrival may shift layout |
| **P2** | Motion scope is overly broad | Rows and drawer use `transition: all 300ms ease-in`; reduced-motion behavior unspecified | Layout properties may animate unnecessarily; actual jank depends on which properties change |
| **P2** | Selection and permission semantics are unspecified | Bulk selection exists; permission-specific affordances are not described | Filter changes may alter the intended operation scope; stale permissions may expose unusable actions |
| **P3** | Final visual and copy consistency needs review | No full visual surface supplied | Spacing, alignment, token use, status wording, and icon consistency are review targets—not established defects |

P0 assumes no independent, reliable save-failure feedback exists outside the supplied surface. Verify that immediately; the snippet alone does not prove server-side data loss.

## 3. Concrete fixes

### Save integrity, failures, and state recovery
- Replace the boolean-only status with explicit dirty, saving, saved, failed, and conflict states; associate outcomes with the relevant product and draft revision.
- Show “Saved” only after acknowledgment of the current revision. A late response must not mark newer edits as saved.
- Define save ordering: serialize/coalesce autosaves per product or use supported version checks. Prevent unintended duplicate submissions without discarding new edits.
- Preserve the draft on failure, close, and retry according to the existing workflow. Do not reset it merely because a request finished.
- Use `finally` for pending-state cleanup, but recognize that it does not solve overlapping-request races.
- Closing must not silently abandon work: either keep a recoverable background save with persistent status or present explicit keep-editing/leave choices. Do not create an unexplained keyboard trap.
- Treat aborts and timeouts as potentially **unknown server outcomes**; reconcile before replaying non-idempotent work.
- Handle failures explicitly:
  - **401:** retain the draft and offer reauthentication.
  - **403:** explain denied access, refresh capabilities, and avoid futile retry.
  - **409:** retain local edits, fetch the current version, and offer review/reconciliation rather than silent overwrite.
  - **429:** honor `Retry-After` when supplied; use bounded backoff, not rapid retry loops.
  - **500/timeout:** retain edits and offer a safe retry; distinguish failure from uncertain completion.
  - **Offline:** show disconnected/unsynced status; do not claim a durable queue unless one exists.
- For batches, retain item-level success/failure outcomes and retry only eligible failed items. Show totals and actionable failure reasons.
- Key selection by stable product IDs; distinguish “selected on this page” from “all matching results.” Define selection behavior across filters and permission changes.
- Persist drafts only under an explicit privacy/security policy; avoid silently storing sensitive inventory data locally.

### Loading and hostile data
- Represent initial loading, filter refresh, empty inventory, no matches, load failure, and stale retained results separately.
- During refresh, retain prior rows where safe, mark them as updating, and prevent bulk actions from silently targeting an outdated query.
- Test 1–200-character names, unbroken strings, duplicates, Unicode, and expanded labels. Use `min-width: 0` where grid/flex children must shrink.
- Keep compact truncation if required, but expose the full name through a keyboard/touch-accessible detail path—not a hover-only tooltip.
- Render missing prices as an explicit unavailable/not-set value, never an inferred zero; format valid prices by locale and currency.
- Reserve image space with dimensions or `aspect-ratio`; provide missing/broken-image fallbacks.
- Validate upload type, size, and dimensions on both client and server; report progress, cancellation, and retry. Treat the filename and declared MIME type as untrusted.
- For 8MB images, use appropriately sized thumbnails and the existing image pipeline; load full-size assets only where needed.
- Preserve default React text escaping; validate inputs at the API boundary as well.

### Responsive layout and accessibility
- Remove the page-wide minimum width; contain unavoidable table overflow in a clearly labeled horizontal-scroll region.
- Preserve column relationships and access to every field. Use deliberate column minimums and wrapping rather than silently hiding operational data.
- Bound the drawer to available width, for example `width: min(520px, 100%)`; provide internal scrolling and a tested dynamic-viewport-height fallback.
- Keep drawer actions reachable with zoom, browser chrome, and the on-screen keyboard. Test portrait and landscape tablet use.
- Decide drawer modality explicitly. If modal, provide dialog semantics, an accessible name, initial focus, focus containment, background inertness, and focus restoration.
- If nonmodal, preserve intentional navigation to the page instead of falsely advertising modal semantics.
- Give Save/Close accessible names and restore a visible `:focus-visible` indicator. Tooltips are supplementary.
- A 28px target is not automatically a WCAG 2.2 AA target-size failure; spacing and exceptions matter. Enlarge touch hit areas toward the system’s tablet target size.
- Use native buttons, inputs, and checkboxes; label selection controls and expose indeterminate select-all state.
- Verify table/header semantics. Do not add `role="grid"` unless implementing its full keyboard interaction contract.
- Announce concise save/error status without moving focus on every autosave or flooding live regions.
- Preserve readable focus and contrast across selected, disabled, error, and pending states.
- Replace `transition: all` with explicit properties; avoid incidental geometry animation and honor reduced-motion preferences.

### Performance without workflow change
- Establish render, filter, scrolling, and image baselines before choosing an implementation.
- Bound mounted rows through the existing stack’s windowing capability or an agreed paging mechanism; no new dependency is presumed necessary.
- Preserve selection, focus, row identity, and accessible position information when rows are not mounted. Avoid unmounting the actively edited/focused row unexpectedly.
- Separate immediate input feedback from expensive filtering; debounce or schedule expensive work where appropriate and mark deferred results as stale.
- Memoize based on measured repeated work and stable inputs. Scheduling alone does not reduce the cost of filtering 10,000 rows.
- Consider server filtering or worker processing only if measurements and existing architecture justify them.
- Profile before adding blanket row memoization; stabilize props and update only changed row data where useful.
- Lazy-load offscreen thumbnails, reserve dimensions, and clean up upload preview object URLs.

## 4. Static signals: decisive versus contextual

**Decisive facts, not measured impact**
- The shown handler suppresses rejection feedback and has only one pending boolean.
- The page enforces a minimum width; the drawer has fixed width and viewport-height sizing.
- The supplied implementation mounts every row and runs filtering synchronously.
- Broad transitions, removed outlines, and unreserved image dimensions are present.
- The stated missing states and drawer behaviors are actionable audit evidence.

**Signals needing project/runtime context**
- `outline: none` is not proof that every focus indicator is absent; inspect replacement styles.
- Icon-only controls are not inherently inaccessible; verify computed accessible names.
- CSS Grid rows do not establish or disprove table semantics; inspect rendered markup.
- Ellipsis is acceptable if the complete information remains accessible for the task.
- A 10,000-row map proves mount scope, not a specific latency or memory threshold.
- `transition: all` is a maintainability/performance risk, not proof of a frame-rate failure.
- A fixed drawer width can work on wide screens; viewport containment determines narrow-screen failure.
- Missing behavior in a snippet is not proof of absence elsewhere. Here, explicit source notes carry stronger weight than snippet omission.

Static checks should identify inspection targets; they cannot certify accessibility, save correctness, or production performance.

## 5. Measurement-first validation and release gates

1. **Establish the baseline:** record representative desktop/tablet viewports, supported browsers, zoom levels, dataset shape, network assumptions, and existing production performance targets.
2. **Instrument safely:** collect filter-to-visible-results latency, input latency, initial usable-table time, commit duration, mounted-row count, scroll stalls, memory, layout shifts, image bytes, and save acknowledgment/error rates. Exclude sensitive payloads.
3. **Exercise controlled fixtures:** 10,000 rows, long/unbroken names, missing values, 60% translations, broken/8MB images, rapid filter changes, repeated saves, and out-of-order responses.
4. **Inject each failure deliberately:** 401/403/409/429/500, timeout, offline/reconnect, and mixed batch outcomes. Verify server state as well as visible status.
5. **Validate interaction manually:** keyboard-only completion, drawer focus/return, status announcements, touch targets, zoom/reflow, reduced motion, tablet keyboard visibility, and selection across filtering/windowing.
6. **Set acceptance gates before implementation:**
   - No swallowed save failures, false “Saved” states, unexplained draft loss, or automatic conflict overwrite.
   - Retries do not duplicate effects; batch totals match item outcomes; only intended records are targeted.
   - All primary tasks work by keyboard and on supported tablet layouts; no inaccessible drawer controls or unintended page-wide overflow.
   - As provisional budgets, target p95 input feedback within 100ms and settled filtered results within 300ms on the agreed reference setup; ratify or replace these with project baselines.
   - No image-induced row shifts; no material regression in initial usability, scrolling, memory, or save reliability.
7. **Roll out reversibly:** stage bounded-rendering and save-orchestration changes independently where practical; keep API compatibility and a known-good route.
8. **Rollback conditions:** incorrect targeting, stale data overwrite, duplicate mutations, unrecoverable drafts, new keyboard/tablet blockers, or sustained budget/error-rate regression. Disable the affected change while retaining explicit failure feedback; do not restore silent failure as the fallback.


## Output B

## 1. Sequence and verdict

**Audit → harden → optimize → polish → focused re-audit.** Establish baselines during the audit; fix correctness, recovery, access, and tablet blockers first; optimize measured bottlenecks; polish within the existing design system last.

**Verdict: Not release-ready as described: failed saves are indistinguishable from successful completion at this component boundary, recovery states are missing, and accessibility and scaling risks remain unresolved.**

This is a read-only assessment of the supplied excerpts and notes. No detector, browser, build, profiler, accessibility-tree, network-throttle, or device testing occurred. No files were edited.

Preserve the filter/table/drawer workflow, existing visual identity, and stable `row.id` keys. There is no evidence supporting a redesign, new dependency, or numeric compliance score.

## 2. Prioritized findings

**Evidence** means directly supplied source behavior. **Hypothesis** means a possible consequence requiring implementation inspection or runtime validation.

| Priority | Location / finding | Source evidence | Impact or runtime hypothesis |
|---|---|---|---|
| **P0 — release blocker** | `saveProduct`: failure is swallowed | `catch {}` discards failure; the function resolves and resets `saving` after either outcome. Failure/retry states are absent. | Callers cannot distinguish failure from success. Whether the drawer clears drafts or displays “Saved” is unknown; silent loss of operator work is a credible risk. |
| **P1 — major** | Save lifecycle and dismissal | One boolean tracks saves; Escape closes during a pending save. | If requests overlap, an earlier completion can clear `saving` while another remains pending. Stale overwrites and draft loss depend on request ordering and drawer behavior. |
| **P1 — major** | Drawer accessibility | Neither focus nor background interaction is contained; save/close are icon-only; `.icon-button` removes outlines. | A modal drawer would allow users to operate behind it and lose task context. Accessible names and alternative focus styling are unverified. |
| **P1 — major** | Loading and recovery | Initial/filter loading is blank; empty, authorization, conflict, rate-limit, server, timeout, offline, and partial-batch states are unrepresented. | Operators cannot reliably distinguish waiting, zero matches, denied access, or failed work. Repeated actions may compound uncertainty. |
| **P1 — major** | Row rendering and filtering | All 10,000 rows mount; filtering runs synchronously on every keystroke. | Significant main-thread, DOM, and memory risk. Actual typing latency, rendering cost, and tablet usability are not measured. |
| **P1 — major** | Tablet and zoom layout | `.page` has `min-width: 1180px`; drawer is fixed at `520px` and `100vh`; columns include fixed widths. | The supplied page rule cannot shrink below 1180px. Actual document overflow, obscured controls, and keyboard-related clipping depend on containment and other styles. |
| **P1 — major** | Bulk selection and permissions | Bulk selection exists; partial failure states are absent; permission-specific affordances are not described. | Hidden selections, ambiguous “select all,” unauthorized actions, and unsafe whole-batch retries need investigation; none is proven by this excerpt. |
| **P2 — hardening** | Hostile data and uploads | Names reach 200 characters; prices can be missing; labels expand 60%; images can be absent or 8MB; image space is unreserved. | Truncation may obscure product identity; missing prices may look like zero; expanded labels may collide. Large files may increase upload/decode cost; layout shifts are possible. |
| **P2 — motion** | Row/drawer transitions | `transition: all 300ms ease-in`; reduced-motion behavior is unspecified. | Unintended properties can animate. Layout animation and dropped frames depend on which properties actually change. |
| **P3 — final polish** | Feedback consistency | Loading feedback is blank and actions are icon-only; remaining visual details are not supplied. | After functional fixes, align status placement, action spacing, and state wording with existing components. No unsupported color, contrast, or theme defects are asserted. |

P0 is scoped to the save-result contract, not a claim that data corruption has been observed. A measured inability to edit on supported devices could elevate performance or layout findings.

## 3. Concrete fixes

### Save correctness and state recovery

- Replace the boolean-only model with explicit `clean`, `dirty`, `saving`, `saved`, and `error` states, scoped to product and draft revision.
- Return a typed result or propagate errors. Only mark a revision saved after server acknowledgement; use `finally` for cleanup, not as evidence of success.
- Serialize/coalesce autosaves per product. Keep newer edits dirty when an older request completes; use server version checks to prevent stale overwrites.
- Preserve the draft, selected product, and actionable error after failure. Display a truthful last-confirmed save time.
- Route Escape, close, navigation, and product switching through one dirty/pending policy. Preserve work and explain pending status; do not silently discard or indefinitely trap users.
- Treat timeout/offline outcomes as potentially ambiguous: the server may have committed. Reconcile state before retrying; use supported idempotency mechanisms where appropriate.
- Do not describe aborting a client request as undoing a server mutation.

### Failure and loading states

| Condition | Required behavior |
|---|---|
| Initial load | Stable table-shaped loading state, concise status, and `aria-busy`; never imply “no products.” |
| Filter refresh | Keep filters usable; retain prior rows with an updating indication when safe. Prevent accidental actions against stale results. |
| Empty results | Distinguish an empty inventory from no matches; offer a filter reset only for the latter. |
| 401 / 403 | Offer reauthentication or explain insufficient permission; preserve drafts only within appropriate security boundaries. Do not retry denied mutations automatically. |
| 409 conflict | Preserve the local draft; show server changes and offer review/reapply against the current version rather than blind overwrite. |
| 429 | Honor `Retry-After` when available; show delayed retry status and prevent retry storms. |
| 500 / timeout / offline | Keep work intact; explain whether persistence is unknown; offer bounded, safe retry and reconciliation. |
| Partial batch failure | Show succeeded/failed counts and item-level reasons; retry eligible failures only, preserving their selection. |

For bulk operations, make selection scope explicit: visible rows versus all matching products. Track selection by stable IDs, not row position. Explain what happens when filters change, and revalidate permissions server-side at mutation time.

### Hostile data and uploads

- Keep compact table names, but expose the full name through keyboard/touch-accessible details—not a hover-only tooltip. Let names wrap in the drawer; handle unbroken strings with `overflow-wrap`.
- Render names as text. Test 1- and 200-character names, Unicode, bidirectional text, and lookalike products without inventing restrictive validation.
- Render missing prices as an explicit unavailable value, never `0`; format valid values with locale and currency rules.
- Allow labels/buttons to grow or wrap under 60% translation expansion. Avoid fixed heights and manual string concatenation.
- Reserve thumbnail space with dimensions or `aspect-ratio`; use a stable absent/broken-image fallback.
- Define upload limits from the existing API contract. Validate size/type on client and server; handle corrupt files, progress, cancel, retry, and replacement without clearing the existing image prematurely.
- Use appropriately sized thumbnails instead of 8MB originals in rows; preserve original assets where required. Release temporary object URLs.

### Responsive layout and accessibility

- Remove the page-wide minimum width; keep any necessary horizontal scrolling inside a labeled table region. Preserve column relationships rather than converting the workflow into cards.
- Let filters and bulk controls wrap using existing spacing tokens. Keep essential actions reachable in tablet portrait/landscape and zoomed layouts.
- Bound drawer width to the viewport, use a supported dynamic-height strategy with fallback, and give content an internal scroll region so actions remain reachable with the software keyboard.
- Confirm drawer intent. **If modal:** provide a named dialog, focus entry/containment/restoration, and inert background interaction. `aria-modal` alone does not implement those behaviors.
- **If nonmodal:** provide an intentional keyboard path between editor and table instead of adding a misleading focus trap.
- Use actual buttons with accessible names such as “Save product” and “Close editor”; use visible labels where the existing system supports them.
- Restore visible keyboard focus. Expand hit areas toward 44×44 CSS pixels for tablet comfort without necessarily enlarging icons.
- Provide table headers, labeled row-selection checkboxes, mixed-state select-all, filter labels, associated field errors, and meaningful image alternatives.
- Announce save/error/selection changes without announcing every keystroke or flooding live regions.
- Prefer native table navigation unless an interactive grid is genuinely required; if so, implement its complete keyboard behavior.
- Replace `transition: all` with explicit properties; prefer transform/opacity for drawer motion and provide reduced-motion behavior that preserves state feedback.

### Performance without workflow drift

- Baseline row mounting, filter computation, and image decoding separately before choosing optimizations.
- Bound mounted rows using existing windowing infrastructure if available. Retain selection, logical row positions, keyboard focus, and editor state independently of mounted row elements.
- If windowing is unavailable, assess a bounded-rendering implementation against the existing workflow; do not introduce pagination or a dependency by default.
- Keep input updates immediate. Debounce expensive filtering where appropriate; cache normalized search data. Deferring a render alone does not make a long synchronous filter interruptible.
- Consider chunking or off-main-thread work only if profiling justifies it.
- Stabilize row props and memoize demonstrably expensive work; avoid blanket memoization.
- Load suitable image sizes and defer offscreen images. Do not add permanent `will-change` across 10,000 rows.

## 4. Static signals: decisive versus contextual

**Decisive within the supplied scope**
- Empty `catch` suppresses save failure at the caller boundary.
- A single boolean cannot accurately represent overlapping pending requests.
- The stated implementation mounts all rows and filters synchronously.
- The supplied CSS imposes a page minimum width and broad transitions.
- Loading/error states and drawer containment are absent according to the notes.

**Require project or runtime context**
- `outline: none` is dangerous, but another focus-visible treatment could compensate.
- Icon-only does not necessarily mean unnamed; inspect rendered accessible names.
- A 28×28 target is below a 44px comfort recommendation, but is not automatically a WCAG 2.2 AA target-size failure; that criterion generally uses 24px with exceptions.
- Ellipsis, fixed columns, and horizontal table scrolling can be appropriate in dense inventory tools if full content and controls remain accessible.
- `transition: all` is a maintainability/performance risk, not proof of layout thrashing.
- Unreserved image space raises shift risk, but surrounding layout may already constrain it.
- Ten thousand rows are a strong performance warning, not a measured latency result.
- Missing descriptions of keyboard support or permissions are audit gaps, not proof of their complete absence.
- Contrast, theming, bundle size, actual API ordering, and browser support cannot be judged from these facts.

## 5. Measurement-first validation and release gates

**Proposed validation—not completed testing:**

1. **Record the baseline:** use representative 10,000-row data, mixed image sizes, missing values, 200-character names, and expanded translations. Document supported browsers, tablet viewports, hardware, and connection conditions.
2. **Measure core journeys:** route entry, rapid typing, select-all, filter with selection, drawer opening, repeated edits during save, image replacement, and partial-batch retry.
3. **Capture:** input-to-paint latency, filter completion, drawer response, long tasks, mounted row count, heap growth, layout shifts, transferred image bytes, and save acknowledgement/error outcomes. Record repeated-run distributions, not one favorable result.
4. **Inject failures in a controlled environment:** every listed status, dropped responses, reordered completions, interrupted uploads, and permission changes. Assert draft preservation and truthful status.
5. **Check access and layout:** keyboard-only operation, screen-reader semantics, focus restoration, reduced motion, tablet orientation, software keyboard, 200% text sizing, and zoom/reflow. Verify table scrolling does not force unrelated controls offscreen.
6. **Validate in two bounded passes:** one batched functional/accessibility/performance pass, then one confirmation after consolidated fixes. Reopen only failed gates.

**Acceptance**
- No failed/unacknowledged revision appears saved; newer edits survive earlier completions.
- Conflict and partial-failure recovery do not duplicate or overwrite successful work.
- All core tasks are reachable with keyboard and supported tablet input; focus is visible and predictably restored.
- No inaccessible clipped actions or page-wide overflow; intentional table scrolling remains contained.
- Set budgets before implementation. Provisional targets: p75 interaction latency ≤200ms on agreed hardware, CLS ≤0.1, and no sustained memory growth across repeated edit cycles. Report filter completion separately.
- Optimization materially improves the identified bottleneck without regressing selection, focus, save correctness, or the established workflow.

**Rollback**
- Stage changes independently behind existing rollout controls where available.
- Roll back any optimization that loses drafts/selection, breaks keyboard access, misreports saves, or exceeds agreed regression budgets.
- Retain save-error and recovery protections when reverting performance or visual changes; do not restore silent failure as the fallback.


## Output C

## 1. Sequence and verdict

**Sequence:** baseline and audit → correctness/hardening → measured optimization → visual polish → final validation. Capture performance baselines before changing hot paths; verify each stage incrementally.

**Verdict:** Not ready for production sign-off: silent save failures are a release gate, and recovery, accessible editing, tablet layout, and bounded table work need hardening—not redesign.

This is a read-only assessment of the supplied description. No files were edited, and no detector, browser, build, profiler, accessibility-tree, network-throttle, or device checks were run.

## 2. Prioritized findings and concrete repairs

Priority: **P0** release gate; **P1** required hardening; **P2** scheduled improvement with explicit risk acceptance; **P3** final polish. Runtime consequences below are hypotheses unless directly established by the supplied facts.

### F1 — P0: Save failure is silently indistinguishable from completion
- **Source evidence:** `catch {}` discards failure; `saving` returns to `false` on both outcomes. The caller receives no failure result.
- **Runtime unknown:** Whether another layer exposes failure; whether failed edits actually disappear. Neither data loss nor a false “Saved” label has been observed.
- **Fix:** Represent dirty, saving, saved, failed, and conflict states explicitly. Mark saved only after acknowledgement of the current revision; retain the draft and show an actionable inline error.
- Replace the page-wide boolean with product/revision-owned status. If saves can overlap, serialize or coalesce them and reject stale acknowledgements; one completed request must not clear another request’s pending status.
- Pending close/Escape must not silently discard work. Either keep saving under durable ownership after closing, or explain why closing is temporarily blocked; offer explicit discard only when safe. Cancelling a request does not prove the server cancelled its write.
- **Acceptance:** Inject rejection, reversed response order, repeated saves, drawer changes, and close-during-save. Latest edits survive; failed saves never appear saved; successful acknowledgements update the correct row.

### F2 — P1: Loading, failure, authorization, and batch recovery have no owned UI
- **Source evidence:** Blank initial/filter loading; all listed empty, error, retry, and partial-failure states are absent.
- **Runtime unknown:** Error frequency, API retry/idempotency guarantees, and current batch-selection semantics.
- **Fix:** Implement the following within existing table/drawer/status components:
  - **Initial loading:** stable table-shaped placeholder plus an accessible loading status.
  - **Filter loading:** retain previous rows where safe, clearly mark them as updating, and prevent bulk actions against an ambiguous result set.
  - **Empty results:** “No products match these filters,” with clear/reset filters; distinguish this from an empty inventory.
  - **401:** session-expired message and sign-in recovery; preserve drafts securely and restore only for the appropriate account.
  - **403:** permission explanation and appropriate read-only/disabled affordances; retain allowed context, but do not expose protected data. Server authorization remains mandatory.
  - **409:** keep the draft and server version; offer review/reconcile/reload, not automatic overwrite.
  - **429:** show a rate-limit message and retry timing; respect `Retry-After`, with bounded backoff.
  - **500:** persistent error and retry action. Automatically retry writes only with established idempotency guarantees.
  - **Timeout:** state that completion is uncertain; reconcile server status before resubmission.
  - **Offline:** retain the draft, show “Not saved—offline,” and offer reconnect/retry; do not imply durable background sync unless implemented.
  - **Partial batch failure:** report succeeded/failed counts and item-level reasons; keep failed IDs available for retry without replaying successful operations.
- Keep selection keyed by product ID, not row position. Make “selected rows” versus “all matching products” explicit; preserve or clear selections across filters only according to the established workflow.
- **Acceptance:** Exercise every branch above; each must explain what happened, provide the permitted next action, and preserve filters, drafts, and selection context where safe.

### F3 — P1: Drawer interaction and controls lack an accessible contract
- **Source evidence:** No focus or background-interaction containment; pending-save Escape closes the drawer; icon-only save/close; `28px` controls with `outline: none`. Other keyboard/label behavior is unspecified.
- **Runtime unknown:** Actual accessible names, alternative focus styling, table semantics, and whether the intended drawer is modal.
- **Fix:** Preserve intended modality. For a modal drawer, provide a labelled dialog, initial focus, focus containment, inert background, scroll handling, and focus restoration to the opener or a stable fallback. A nonmodal drawer needs an explicit keyboard path between regions instead—not false modal semantics.
- Use real buttons with “Save product” and “Close editor” accessible names; tooltips may supplement, not replace, names. Apply F1’s safe close contract.
- Restore visible `:focus-visible`. Expand effective tablet targets from 28px to **at least 44 × 44 CSS px**, provisionally pending the existing standard; keep hit areas nonoverlapping.
- Provide table headers/cell relationships, labelled selection checkboxes, mixed-state select-all, logical tab order, and keyboard access to row actions. Use grid keyboard behavior only if it is genuinely an interactive grid.
- Announce meaningful save/error/selection changes without announcing every keystroke; associate field errors with inputs.
- **Acceptance:** Complete filter → select → edit → save/recover → close using keyboard and a screen reader; focus remains visible, predictable, and unobscured.

### F4 — P1: Fixed geometry does not establish tablet support
- **Source evidence:** Page minimum width `1180px`; mostly fixed column tracks; drawer width `520px` and height `100vh`.
- **Runtime unknown:** Actual clipping, scroll ownership, browser viewport behavior, and virtual-keyboard obstruction.
- **Fix:** Remove the page-level minimum-width blocker; use a shrinkable page container and wrapping filters. Make flexible cells shrink with `minmax(0, 1fr)`/`min-width: 0`, while preserving legible critical columns.
- Where table width remains necessary, isolate horizontal overflow to a labelled, keyboard-scrollable data region—not the entire page. Do not hide essential columns or actions merely to fit.
- Cap drawer width to available inline space, preserving the desktop 520px intent. Use a supported dynamic-viewport height with fallback, internal body scrolling, and reachable header/footer actions.
- **Acceptance:** Desktop and tablet portrait/landscape, 200% zoom, expanded labels, and an open software keyboard retain access to filters, selection, save, close, and error recovery.

### F5 — P1: Rendering and filtering have no work bound
- **Source evidence:** All 10,000 rows render; filtering runs synchronously for every keystroke.
- **Runtime unknown:** Input delay, render duration, long tasks, memory pressure, and device-specific task failure.
- **Fix:** Require a mounted-row bound. After baselining, choose the smallest compatible approach: reuse existing windowing or established paging facilities; preserve stable IDs, selection, edit state, scroll behavior, and accessibility.
- Measure filter computation separately from rendering. Based on the result, consider cached normalization, memoized derivation, interruptible/deferred result updates, or bounded debouncing with visible updating state. Deferral alone does not reduce computation.
- Consider off-main-thread or server filtering only if measurements and existing infrastructure justify it. Do not introduce a dependency as the default answer.
- **Acceptance:** Meet the provisional performance gates below while preserving correct results, bulk-selection scope, keyboard access, and focus during row mount/unmount.
- Keep this **P1**, not P0, absent measured release-blocking task failure.

### F6 — P1: Hostile data and uploads need explicit handling
- **Source evidence:** Names span 1–200 characters; prices may be missing; translations expand 60%; images may be absent or 8MB; image space is not reserved; names use ellipsis.
- **Runtime unknown:** Actual overflow, upload limits, decode cost, image failures, and full-name discoverability.
- **Fix:** Test short, long, and unbroken names. Preserve dense row truncation where useful, but expose the full name through keyboard/touch-accessible disclosure and the editor; do not rely on hover or `title` alone.
- Render missing prices as “Not set,” not zero; preserve valid zero and use locale-aware currency formatting. Let labels wrap without clipping controls.
- Reserve image dimensions/aspect ratio and provide stable missing/broken-image placeholders. Request appropriately sized thumbnails and defer offscreen images where compatible with the table.
- Define file-size/type/dimension limits, validate client-side for feedback and server-side for enforcement. Explicitly accept or explain rejection of 8MB files; show upload progress, failure, retry, and safe cancellation. Preserve the previous image until replacement succeeds; release preview object URLs.
- **Acceptance:** Fixtures cover these extremes, corrupt/unsupported images, interrupted uploads, and expanded translations without lost edits, misleading values, or inaccessible content.

### F7 — P2: Broad transitions create avoidable motion and rendering risk
- **Source evidence:** Rows and drawer use `transition: all 300ms ease-in`; reduced-motion behavior is unspecified.
- **Runtime unknown:** Which properties actually change, whether layout is animated, and perceived responsiveness.
- **Fix:** Restrict transitions to intentional properties; prefer transform/opacity for drawer movement where appropriate and existing motion tokens. Remove unnecessary row movement and provide a reduced-motion path that preserves immediate state feedback.
- **Acceptance:** No unintended width/height/layout transitions; interrupted open/close remains correct; reduced motion does not delay access or hide status. Timing is judged in context, not by a generic easing ban.

### F8 — P3: Final consistency polish follows functional acceptance
- **Source evidence:** The existing design system must remain; no rendered visual baseline was supplied.
- **Runtime unknown:** Alignment, contrast, density, spacing, and same-state consistency.
- **Fix:** After F1–F7, align added messages, loading treatments, focus rings, labels, and motion with existing components/tokens. Do not change the information architecture, table workflow, or visual language.
- **Acceptance:** Before/after review confirms readable status hierarchy and consistent control states across supported themes without workflow drift.

## 3. Static-signal reconciliation

**Decisive within this supplied scope**
- The save function suppresses errors; its local status cannot distinguish success from failure.
- The explicitly missing state branches and drawer containment are coverage gaps—not speculative scanner warnings.
- Rendering 10,000 rows and synchronous per-keystroke filtering prove unbounded UI work relative to visible content, not measured lag.
- The supplied dimensions, missing image reservations, and 28px controls establish concrete implementation risks requiring targeted repair.

**Require project or runtime context**
- `outline: none` proves outline removal, not absence of every possible focus indicator.
- Icon-only controls are not inherently inaccessible; accessible names and discoverability determine the outcome.
- One global boolean becomes a concurrency bug only if overlapping operations are reachable; F1’s error suppression is independently established.
- Fixed widths can be appropriate for desktop drawers or columns. The problem is lack of an adequate constrained-width strategy, not fixed pixels themselves.
- Ellipsis can preserve useful density; the defect is losing access to essential content.
- `transition: all`, `ease-in`, `100vh`, and unreserved images predict risks but do not prove jank, clipping, or measured layout shift.
- A clean static scan would not establish authorization correctness, accessible semantics, recovery, visual quality, or runtime speed.

## 4. Measurement-first validation and release plan

All steps below are **planned, not executed**.

1. **Freeze the baseline:** Record existing components/tokens, workflow semantics, supported browsers/tablets, API contracts, and representative data. Use the same 10,000-row fixture and device conditions for before/after comparison.
2. **Measure before optimizing:** Capture cold/warm load, filter typing, select-all, drawer open/edit/save, upload, and repeated edit cycles. Separate network wait, filter CPU work, React commits, paint/layout, image decoding, and memory.
3. **Ratify provisional numeric gates:** These are proposed budgets, not measured results:
   - Input-to-visible-echo p95 ≤ **100ms**; input-to-current-filter-results p95 ≤ **200ms**, including any debounce.
   - Maximum main-thread task ≤ **100ms** during the scripted interactions.
   - Mounted product rows ≤ **200**, adjusted only for documented viewport/overscan needs.
   - CLS ≤ **0.1** across loading and image replacement scenarios.
   - Peak JS heap ≤ **200MB**; retained heap after 20 edit/upload/close cycles grows ≤ **10MB** after comparable cleanup.
   - No non-target timing metric regresses by more than **10% or 20ms, whichever is larger**; peak memory regression ≤ **10%**.
   - Report p95 over at least **30 repeat interactions per target configuration**; keep cold-start measurements separate.
4. **Correctness and recovery:** Add targeted state/API tests for F1–F2, including timeout-after-server-commit, permission change mid-edit, filter response races, and partial batches. Run existing type/lint/test/build checks during implementation.
5. **Runtime coverage:** Exercise F3–F7 on supported desktop/tablet browsers with keyboard, touch, screen reader, reduced motion, zoom, software keyboard, and controlled latency/offline/failure conditions. Capture layout states, but do not treat screenshots as interaction proof.
6. **Release acceptance:** F1 resolved; no unresolved P1 without explicit accountable risk acceptance; all specified recovery paths retain the right context; no critical keyboard/accessibility blockers; performance gates met; existing visual language and workflows preserved.
7. **Rollback:** Ship separable, reversible changes. Reject optimization experiments that neither improve their target metric nor simplify the implementation. Roll back a candidate for data-integrity, permission, selection, focus, recovery, or budget regressions; preserve drafts and do not knowingly restore silent failure as an acceptable steady state.
8. **Closeout:** Mark F1–F8 resolved, partial, or unresolved against actual evidence. Missing runtime evidence keeps production sign-off incomplete—not “passed by inspection.”
