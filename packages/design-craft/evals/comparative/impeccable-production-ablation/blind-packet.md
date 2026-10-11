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

**Sequence:** establish baseline and audit → harden correctness, recovery, accessibility, and layout → measure and optimize → polish within the existing design system → validate and stage rollout.

**Verdict:** Not ready for production sign-off: silent save failures are a release blocker; accessibility, recovery, tablet layout, and unbounded rendering require hardening before cosmetic polish.

This is a read-only assessment of the supplied description. No files were edited, and no detector, browser, build, profiler, accessibility-tree, network-throttle, or device validation occurred.

## 2–3. Prioritized finding ledger and concrete repairs

**Priority:** P0 = release blocker; P1 = fix before sign-off; P2 = schedule soon with explicit risk acceptance; P3 = final polish. “Unknown” identifies behavior not established by the supplied evidence.

### F1 — P0: Save failures have no actionable outcome
- **Evidence:** `catch {}` discards errors; `saving` returns to `false` after either success or failure. Failure and recovery states are explicitly absent.
- **Unknown:** Whether another layer retains drafts or reports errors; actual data loss and false “Saved” text are not demonstrated.
- **Repair:** Model dirty, saving, saved, failed, and conflict states per product/revision. Mark saved only after acknowledgement of the current revision; retain edits and expose a specific retry action on failure.
- **Repair:** Preserve the last confirmed value separately from the draft. Log sanitized failure categories and request IDs without product-sensitive payloads.
- **Recovery contract:**
  - **401:** Show session expiry and reauthentication; retain the draft through the supported secure recovery path.
  - **403:** Explain denied access; stop prohibited retries and offer permitted navigation without pretending the edit saved.
  - **409:** Keep the draft and show server-versus-local differences; offer review/merge or explicit reload, never automatic overwrite.
  - **429:** Show a retry delay, respect `Retry-After`, and prevent retry storms.
  - **500/timeout:** Show “Save not confirmed”; retain edits. Reconcile ambiguous outcomes before retrying, using idempotency/versioning where supported.
  - **Offline:** Show “Not saved—offline”; retain the draft, with explicit retry or a clearly disclosed supported queue.
- **Acceptance:** Inject each outcome; verify accurate status, preserved drafts, recoverable actions, and no duplicate or stale writes.

### F2 — P1: Save ownership, dismissal, and batch recovery are underspecified
- **Evidence:** One page-level `saving` boolean; Escape closes during a pending save; partial batch failures are absent.
- **Unknown:** Whether saves can overlap, drawer closure unmounts draft state, or the API prevents stale writes.
- **Repair:** Serialize or coalesce saves per product, track request/revision ownership, and reject stale completions. A pending counter alone does not prevent stale server writes; use server version checks where supported.
- **Repair:** Keep draft and pending work independent of drawer visibility. Escape must not silently discard work: either close safely while saving continues with persistent status, or present an accessible leave/discard confirmation when necessary.
- **Repair:** Store selection by stable product ID, not rendered row index. Make “selected visible rows” versus “all matching results” explicit; preserve or explicitly reset scope when filters change.
- **Repair:** For partial batches, show succeeded/failed counts and per-row reasons; retain failed selections and drafts, with retry for failed eligible items only.
- **Acceptance:** Exercise reversed response order, rapid edits, product switching, Escape, unmount/reopen, filter changes, and mixed-success batches; verify final server values and selection scope.

### F3 — P1: Drawer interaction and control accessibility are incomplete
- **Evidence:** No focus trap or background-interaction containment; save/close are icon-only; `.icon-button` is `28px × 28px` with `outline: none`.
- **Unknown:** Accessible names, alternate focus styling, effective hit areas, table semantics, and keyboard behavior are not described.
- **Repair:** Preserve the drawer pattern. If modal, provide dialog semantics and a name, move focus inside, contain Tab navigation, make the background inert, and restore focus to the opener or a stable fallback. Do not declare `aria-modal` without actual modality.
- **Repair:** Give save/close accessible names and discoverable tooltips; restore token-based `:focus-visible`. Expand effective targets to at least **44 × 44 CSS px** for tablet use, provisionally pending project standards, without overlapping adjacent targets.
- **Repair:** Use semantic table headers and labelled selection checkboxes; expose mixed bulk-selection state. Adopt grid-style arrow navigation only if the existing interaction model requires it.
- **Repair:** Label filters/uploads, associate validation errors with fields, and announce saving/results politely without per-keystroke chatter. Explain permission-disabled actions; server authorization remains authoritative.
- **Acceptance:** Complete filter → select → edit → upload → save → close using keyboard and screen reader; verify focus return, names, status announcements, and touch targets.

### F4 — P1: Initial loading, filter loading, and empty results are ambiguous
- **Evidence:** Loading produces a blank table body; empty-result and read-failure states are absent.
- **Unknown:** Fetch cancellation, stale-response handling, and whether existing rows survive filter requests.
- **Repair:** Initial load: reserve table geometry and show a labelled loading state. Filter refresh: retain previous results with an explicit updating indicator and prevent ambiguous bulk actions against stale results.
- **Repair:** Distinguish “No inventory” from “No matches”; provide the existing creation action only when permitted, or a clear-filters action. Keep filter values intact.
- **Repair:** Read failure: show an inline error and retry, retaining filters and any safely displayed prior results. Ignore superseded filter responses.
- **Acceptance:** Verify zero/one/many rows, delayed requests, request failure, and out-of-order filter responses; blank content must never be the only explanation.

### F5 — P1: Fixed geometry threatens tablet and zoom usability
- **Evidence:** Page minimum width is `1180px`; row columns contain `64px 280px 1fr 120px 96px`; drawer is `520px` wide and `100vh` tall.
- **Unknown:** Actual clipping, global overflow, surrounding containers, and browser-keyboard behavior.
- **Repair:** Remove the page-wide minimum; allow filters and bulk controls to wrap. Keep unavoidable horizontal scrolling inside a labelled, keyboard-accessible table region rather than the whole page.
- **Repair:** Replace inflexible text tracks with appropriate `minmax(0, …)` tracks and `min-width: 0`; retain useful numeric/action widths. Keep headers and rows aligned; do not hide critical actions to force a fit.
- **Repair:** Cap drawer width to available space, e.g. `min(520px, 100%)`; use dynamic viewport height with fallback, internal scrolling, and a reachable action area. Account for safe areas and the tablet keyboard.
- **Acceptance:** At supported desktop/tablet widths, portrait/landscape, and 200% zoom, filters and drawer actions remain reachable; only the table may intentionally scroll horizontally.

### F6 — P2: Hostile text, missing values, and uploads need explicit handling
- **Evidence:** Names range from 1–200 characters; names are ellipsized; prices/images may be missing; labels expand 60%; images may be 8MB; image space is not reserved.
- **Unknown:** Actual truncation severity, asset transfer/decode costs, upload limits, and whether original-sized images become thumbnails.
- **Repair:** Preserve compact rows but offer full names through a keyboard/touch-accessible disclosure or drawer—not hover-only tooltips. Test unbroken text and translated labels; allow wrapping where appropriate.
- **Repair:** Render missing prices as “Not set” or the established equivalent, never zero; retain valid zero prices and locale-aware currency formatting.
- **Repair:** Reserve thumbnail dimensions/aspect ratio; provide absent/broken-image fallbacks and purposeful alt text. Use correctly sized thumbnails and offscreen loading where appropriate.
- **Repair:** Validate upload type, byte size, and pixel dimensions on client and server. For 8MB files, either support them with progress/cancel/retry or reject before transfer with a clear limit; preserve the prior image until replacement succeeds and release preview URLs.
- **Acceptance:** Exercise name-length boundaries, +60% translations, missing/zero prices, absent/corrupt images, 8MB uploads, cancellation, and upload failure without losing other edits.

### F7 — P1: Rendering and filtering have no bounded-work strategy
- **Evidence:** All 10,000 rows mount; filtering recalculates synchronously on every keystroke.
- **Unknown:** Input latency, commit time, memory, long tasks, and device-specific task failure. These are not established P0 performance defects.
- **Repair:** Baseline first, then impose a mounted-row bound using existing capabilities. Windowing can preserve continuous-table workflow; pagination needs workflow approval. Preserve selection, logical row positions, and focused-row access across either strategy.
- **Repair:** Separate urgent input feedback from expensive results work. Choose caching, deferred scheduling, chunking, worker execution, or server filtering only against measured costs; debouncing alone does not bound expensive work.
- **Acceptance:** Meet the provisional gates below on 10,000 realistic rows; verify selection and assistive-technology behavior rather than accepting speed at the expense of correctness.

### F8 — P2 motion safety; P3 visual tuning
- **Evidence:** Rows and drawer use `transition: all 300ms ease-in`; reduced-motion support is not described.
- **Unknown:** Which properties change, whether layout work is animated, and perceived motion quality.
- **Repair:** Transition only intended properties; prefer transform/opacity for drawer movement and remove nonessential movement under `prefers-reduced-motion`. Then tune timing/easing using existing tokens and conventions.
- **Acceptance:** Verify interruption, close/reopen, focus visibility during transitions, and reduced motion; compare equivalent controls and states before approving polish.

## 4. Static signals: decisive versus contextual

- **Decisive source findings:** swallowed save errors, explicitly absent states, lack of drawer containment, the supplied dimensions, direct 10,000-row mounting, and synchronous filtering. These establish missing contracts or architectural risk—not measured user impact.
- **Conditional findings:** a global boolean becomes a concurrency defect when calls overlap; Escape becomes destructive if state is discarded; icon-only controls are not inherently inaccessible if properly named.
- **CSS requires context:** `outline: none` removes the outline but does not prove all focus indicators are absent. A 28px box may have a larger effective target; verify it rather than assuming one. Fixed widths and ellipsis can be appropriate inside a bounded table.
- **Performance requires measurement:** missing image dimensions create instability risk, not a measured CLS score. `transition: all` creates unintended-animation risk, not proof of jank. Row count proves work volume, not a specific delay.
- **Do not infer unrelated defects:** no evidence establishes contrast failure, bundle bloat, theme inconsistency, or need for a new component library.
- **Severity rule:** retain F7 at P1 unless representative runtime evidence demonstrates release-blocking task failure. Project conventions can justify visual choices, but not silent failure or inaccessible task completion.

## 5. Measurement-first validation and release conditions

All steps below are proposed, not executed.

1. **Lock the comparison conditions.** Agree supported browsers, desktop/tablet hardware, viewport/zoom matrix, permissions, data distribution, and existing design-system exemplars. Use the same fixtures and environment for baseline and candidate.
2. **Record the baseline before optimization.** Measure route readiness, input-to-paint, input-to-correct-results, render/commit duration, longest main-thread task, mounted rows, image transfer/decode cost, CLS, and memory across repeated edit/filter/drawer cycles.
3. **Validate correctness first.** Add targeted tests for F1–F4, including ambiguous timeouts, stale responses, permission changes, and batch recovery. Run the project’s established type, lint, test, and build checks when implementation is authorized.
4. **Exercise real interactions.** Test F3/F5/F6 with keyboard, screen reader, tablet touch and on-screen keyboard, long translations, supported locales, reduced motion, and failure injection. Capture before/after representative states for visual comparison.
5. **Ratify provisional performance gates before implementation:**

| Metric | Proposed acceptance gate—not measured |
|---|---|
| Input-to-next-paint | p95 ≤100ms during filtering |
| Local input-to-correct-results, 10,000 rows | p95 ≤200ms, including any debounce |
| Longest main-thread task during filter/edit/scroll | ≤100ms; investigate every task over 50ms |
| Mounted product rows | ≤200, or a ratified viewport-plus-overscan bound |
| CLS during load and image arrival | ≤0.1 |
| Memory after 20 repeated interaction cycles | Stabilizes; post-GC retained heap ≤10% above warmed baseline under a consistent measurement method |
| Candidate versus baseline | No untargeted latency regression exceeding both 10% and 20ms; peak memory increase ≤10% |

6. **Accept only demonstrated resolution.** F1 must pass all failure/recovery checks; P1 findings require evidence-backed closure or an explicit release decision. Pending changes must never be presented as saved. Preserve workflow, selection semantics, density, tokens, and critical-action reachability.
7. **Stage changes independently.** Separate save/recovery, accessibility/layout, bounded rendering, and polish so each can be reverted without losing draft compatibility.
8. **Rollback conditions:** any data-integrity failure, inaccessible critical action, selection-scope regression, breached ratified budget, or worsening production save-error/conflict rates. Revert optimization that neither improves its target metric nor simplifies implementation.
9. **Safety on rollback:** retain compatible draft/error handling; if reverting would restore silent save failure, disable the affected editing path rather than silently reintroducing it.

**Current acceptance status: unverified; production sign-off withheld on the supplied evidence.**


## Output B

## 1. Sequence and verdict

**Sequence:** Audit → harden correctness, recovery, and accessibility → polish within existing design tokens and workflow → optimize against measurements → validate and release incrementally. Establish performance baselines before changes; address obvious high-cost rendering during hardening if it prevents usable operation.

**Verdict:** Not ready for production sign-off: silent save failures, incomplete recovery states, and drawer interaction gaps are source-confirmed; performance and tablet usability carry substantial unmeasured risk.

This is a read-only assessment of the supplied description. No execution, browser inspection, build, detector, profiler, accessibility-tree inspection, network throttling, or device testing occurred.

## 2. Prioritized findings

Priorities: **P0** release blocker for trustworthy editing; **P1** required production hardening; **P2** robustness/polish; **P3** measured refinement. Runtime consequences below are hypotheses, not test results.

| Priority | Finding and source evidence | Runtime hypothesis / uncertainty |
|---|---|---|
| **P0** | **Save failure is hidden.** `catch {}` discards errors; `saving` returns to `false` regardless of success. Failure and retry states are absent. | Operators may mistake completion for persistence and leave with unsaved work. Actual status wording is not shown. |
| **P1** | **Save lifecycle is not concurrency-safe.** One boolean represents every request; no sequencing, cancellation, or revision handling is shown. | If saves overlap, an earlier completion can clear pending status while another request remains active. Stale writes depend on API behavior. Escalate to P0 if lost updates are confirmed. |
| **P1** | **Recovery is incomplete.** Empty, authorization, conflict, rate-limit, server, timeout, offline, and partial-batch states are explicitly absent. | Users may repeat successful operations, lose drafts, or lack a safe path forward. Backend idempotency and authorization are unknown. |
| **P1** | **Drawer has incomplete interaction containment.** No focus or background-interaction trap; Escape closes during pending saves; save/close are icon-only. | For a modal drawer, focus can escape and background edits can occur. Closing may hide unresolved changes; icon-only controls are not necessarily unlabeled, but names require verification. |
| **P1** | **Keyboard focus protection is missing.** `.icon-button` removes outlines; focus-visible and keyboard behavior are undescribed. | Keyboard users may lose their location unless another focus indicator exists. Full keyboard operability cannot be inferred. |
| **P1** | **Tablet layout is constrained by desktop sizing.** Page minimum is `1180px`; drawer is fixed at `520px` and `100vh`. | Narrow viewports, zoom, and an on-screen keyboard may cause clipping, page-wide scrolling, or unreachable actions. Actual geometry needs testing. |
| **P1** | **Rendering and filtering scale poorly by construction.** All 10,000 rows render; filtering runs synchronously on each keystroke. | Input delay, long tasks, and excessive layout/memory are plausible, but their magnitude is unmeasured. |
| **P1** | **Loading is indistinguishable from missing content.** Initial/filter loading leaves the body blank. | Operators may interpret loading as zero inventory or repeat actions. Whether stale results remain elsewhere is unknown. |
| **P2** | **Hostile data handling is incomplete.** Names reach 200 characters; prices/images may be absent; labels expand 60%; images may be 8MB. Names use ellipsis. | Ambiguous product identification, distorted layouts, slow uploads, and placeholder shifts are likely boundary failures to test. |
| **P2** | **Image geometry is not reserved.** Source notes explicitly identify this. | Image arrival may shift rows and targets; actual layout shift depends on surrounding constraints. |
| **P2** | **Animation scope is overly broad.** Rows and drawer use `transition: all 300ms ease-in`; reduced motion is undescribed. | Layout properties may animate unnecessarily; discomfort and rendering cost depend on which properties change. |
| **P2** | **Bulk-selection scope and permission affordances are unspecified.** The workflow includes bulk selection; permission-specific behavior is not described. | Filtering, paging/windowing, or partial failure may make selection counts or allowed actions misleading. |
| **P3** | **Further render/motion tuning lacks measurements.** Component costs and changed-property traces are unavailable. | Blanket memoization or animation rewrites may add complexity without useful gains. |

## 3. Concrete hardening and polish

### Save integrity and recovery
- Replace the boolean-only model with explicit `dirty`, `saving`, `saved`, and `error` states; distinguish validation and conflict failures.
- Show “Saved” only after an acknowledged successful revision. Keep dirty values and error context on failure.
- Serialize saves per product or coalesce queued edits; track revisions/request identity so stale responses cannot overwrite newer state.
- Coordinate with the API for version checks and idempotency where supported. Client response guards alone cannot prevent stale server writes.
- Define pending-save close behavior: keep drafts and visible save status if closing is allowed, or warn/block dismissal with an accessible explanation.
- Use the same policy for Escape, close, route changes, and other dismissals; do not silently discard edits.
- Keep drafts through recoverable failures. Persist locally only if data sensitivity and retention rules permit; do not promise offline durability without it.
- For uncertain outcomes after timeout/disconnection, reconcile server state before replaying non-idempotent actions.

### Loading, failures, and bulk actions
- Distinguish initial loading, refreshing, no inventory, and no filter matches. Offer clear/reset filters for the latter.
- Use stable loading geometry and a named busy region. During refresh, retain results only with clear stale/busy treatment and safe action rules.
- **401:** preserve the draft while offering reauthentication; **403:** explain the restriction and prevent unavailable actions.
- **409:** retain local edits, retrieve the current server version, and offer review/reconciliation rather than silent overwrite.
- **429:** respect `Retry-After`; **500/timeout:** show a persistent contextual error and controlled retry.
- **Offline:** indicate unsaved status; bound any automatic retry with backoff and stop conditions. Connectivity indicators alone do not establish API reachability.
- For batch results, show succeeded/failed counts and row-level reasons. Retry only eligible failures; never silently replay successes.
- Store selection by stable product ID, not row position or mounted DOM. State whether “select all” means visible rows or all matching results.
- Define what happens to selection when filters change; show hidden-selection counts and revalidate permissions before bulk execution.
- Keep server-side authorization authoritative; UI permission affordances improve clarity but are not a security boundary.

### Hostile data and uploads
- Let grid children shrink with `min-width: 0`; use `minmax(0, 1fr)` for flexible tracks.
- Keep ellipsis where appropriate, but expose the full product name through keyboard-, pointer-, and touch-accessible detail—not a hover-only tooltip.
- Test long unbroken strings, one-character names, punctuation, and 60% label expansion; allow labels/actions to wrap without overlap.
- Render missing prices explicitly as unavailable, never as zero. Preserve locale-aware currency formatting and applicable validation rules.
- Supply a stable missing/broken-image placeholder and reserve image space using dimensions or aspect ratio.
- Define upload type, size, and pixel-dimension limits; validate client-side for feedback and server-side for enforcement.
- Provide upload progress, cancellation, failure, and retry. Preserve the existing image until replacement succeeds.
- Treat large uploads separately from row thumbnails; use appropriately sized delivery assets where the existing pipeline supports them.

### Responsive layout and accessibility
- Replace the global minimum-width constraint with a fluid page shell; contain necessary horizontal scrolling within the table region.
- Preserve column relationships and operationally important fields rather than converting the editor into a new card workflow.
- Bound drawer width by the viewport, for example `min(520px, 100%)`; provide internal scrolling, reachable actions, and dynamic-viewport sizing with fallback.
- Verify drawer behavior with tablet portrait/landscape, browser zoom, safe areas, and the on-screen keyboard.
- Establish whether the drawer is modal. If modal: name the dialog, set modal semantics, contain focus, make the background inert, and restore focus on close.
- If intentionally nonmodal, provide deliberate keyboard transitions and safe background interaction rather than adding a trap indiscriminately.
- Use native buttons with accessible names for icon controls; restore a clearly visible `:focus-visible` style.
- Check actual hit regions and spacing: `28px` is not automatically a WCAG target-size failure, but larger touch-friendly targets are preferable for tablet use.
- Use appropriate table headers and labeled selection controls. Adopt grid semantics only if the complete grid keyboard interaction is implemented.
- Announce saves/errors through a restrained status/live region; do not announce every keystroke or rely on color alone.
- Restrict transitions to intentional properties, favor transform/opacity where suitable, and honor reduced motion.

### Performance without a redesign
- Measure row-render and filter costs before choosing implementation details.
- Window the table or use workflow-compatible paging; prefer existing project capabilities rather than adding a dependency by default.
- Preserve selection, row identity, scroll position, keyboard focus, and meaningful row information when rows mount/unmount.
- Avoid expensive filtering on every character: precompute searchable fields, reduce redundant work, and use a measured debounce or scheduling strategy.
- Keep input feedback immediate. Scheduling updates does not by itself make a monolithic synchronous filter cheap.
- Memoize rows/calculations only when traces show avoidable work; keep props stable where this produces a measurable benefit.
- Reserve image dimensions, lazy-load offscreen thumbnails, and verify image decoding and upload preview cleanup.

## 4. Static signals: decisive versus contextual

**Decisive from the supplied source**
- Save errors are swallowed; required failure states are absent.
- All rows are rendered and filters run synchronously per keystroke.
- Page/drawer sizing is rigid; image space is not reserved.
- Outline removal and broad transitions are present.
- These facts justify corrective work or targeted validation, but not invented timing, accessibility, or data-loss measurements.

**Require project/runtime context**
- Icon-only controls can be accessible if correctly named; missing labels are not proven by appearance.
- Outline removal fails users if no equivalent focus treatment exists; inspect all applicable styles.
- A focus trap is required for modal behavior, not every drawer.
- A 28px target is a usability concern, not an automatic standards failure.
- Ellipsis is acceptable if essential information remains accessible.
- `transition: all` is a risk signal, not proof of layout thrashing.
- Ten thousand rows is a strong scaling warning, not a measured latency result.
- Fixed dimensions may be intentional within a supported viewport contract; they must still be reconciled with tablet and zoom requirements.
- Missing permission UI does not prove missing server authorization; lack of shown concurrency protection does not prove the API lacks version checks.

## 5. Measurement-first validation and release gates

1. **Establish a baseline before changes.** Use representative 10,000-row data plus boundary fixtures: long names, missing values, expanded labels, absent/large images, and mixed permissions.
2. **Agree budgets in advance.** Record route readiness, filter input-to-paint latency, commit/render duration, long tasks, DOM size, memory, layout shift, and save acknowledgement time.
3. **Separate client and network costs.** Proposed starting gates: filter response p95 ≤200ms on an agreed tablet profile, no filter-related task >50ms, and no image-induced target movement. Calibrate these against actual operational requirements.
4. **Exercise deterministic failure cases.** Test every listed response/state, delayed and out-of-order saves, rapid repeated edits, close/reopen, navigation, reconnect, session expiry, and mixed batch outcomes.
5. **Validate integrity as a hard gate.** No false “Saved,” lost newer edit, silent conflict overwrite, duplicated successful batch action, or discarded failed draft.
6. **Inspect keyboard and assistive behavior manually.** Verify names, headers, focus visibility/order/return, modal containment where applicable, status announcements, and virtualized navigation.
7. **Test the supported layout matrix.** Desktop/tablet orientations, 200%/400% zoom, touch, software keyboard, reduced motion, and expanded translations; no unreachable essential action or unintended page-wide overflow.
8. **Compare before/after traces.** Accept optimization only if it improves the agreed bottleneck without degrading selection, focus, recovery, or supported-device performance.
9. **Release in reversible slices.** Separate save/recovery, drawer/layout, and rendering changes; use existing rollout controls and privacy-safe telemetry for failures, retries, conflicts, and latency.
10. **Rollback triggers:** any integrity/accessibility hard-gate failure, broken bulk semantics, or budget breach. Roll back the responsible slice to a known-safe state; if none exists, pause affected editing rather than restoring silent failure.

**Acceptance:** all P0/P1 issues resolved and verified, measured budgets met on supported hardware, and remaining P2/P3 work explicitly owned and scheduled.


## Output C

## 1. Sequence and verdict

**Sequence:** Audit and establish baselines → harden correctness, recovery, accessibility, and tablet behavior → optimize measured bottlenecks → polish within the existing design system → regression validation and staged release. Performance measurement starts during audit, not after hardening.

**Verdict:** Not release-ready: silent save failures and missing recovery paths undermine editing trust; drawer accessibility and the unbounded table need remediation before visual polish.

This is a read-only assessment of the supplied description. No files were edited, and no detector, browser, build, profiler, accessibility-tree, network-throttle, or device run occurred. Runtime consequences below are hypotheses, not measured results.

Preserve the filters–table–drawer workflow, existing tokens/components, and stable `row.id` keys. There is insufficient evidence to grade contrast, theming, bundle size, or overall WCAG conformance.

## 2. Prioritized findings

**Evidence** means explicitly supplied code or notes. **Hypothesis** means a consequence requiring verification. Priorities reflect operational risk, not detector counts.

### P0 — Release blocker: save outcomes cannot be trusted

- **Evidence:** `saveProduct` swallows errors with `catch {}` and then clears `saving`; failure and conflict states are absent.
- **Impact:** A rejected save has no represented recovery path. **Hypothesis:** the drawer may appear saved or close with unsaved changes; its status rendering and draft lifecycle are not shown.
- **Fix:** Represent dirty, saving, saved, and failed states explicitly. Mark saved only after server acknowledgement of the current revision; preserve failed drafts and show an actionable error.
- **Concurrency risk:** One shared boolean cannot accurately represent overlapping requests. **Hypothesis:** if saves overlap, an earlier completion can clear the indicator while another request remains pending.
- **Fix:** Track status by product/revision; serialize or coalesce autosaves per product, ignore stale responses, and use server version checks to prevent stale writes. Merely moving `setSaving(false)` into `finally` does not solve this.

### P1 — Drawer interaction and pending-save exit

- **Evidence:** No focus trap or background interaction blocking; Escape closes even while saving. Save and close are icon-only.
- **Impact:** Users can leave the active editing context or interact behind it. Actual draft loss on close is **unverified**.
- **Fix:** If this is a modal drawer, use dialog semantics, an accessible title, initial focus, focus containment, inert background, and return focus to the opener. If intentionally nonmodal, do not falsely mark it modal; define usable focus movement between regions.
- Route Escape, close, navigation, and backdrop dismissal through one dirty/pending policy. Preserve the draft and clarify whether saving continues; offer a deliberate leave/discard decision rather than silently dropping work or trapping users indefinitely.
- Give save and close programmatic names; use existing labeled-action patterns where available.

### P1 — Failure, loading, and batch recovery are missing

- **Evidence:** Blank bodies during initial/filter loading; no empty, authorization, conflict, rate-limit, server, timeout, offline, retry, or partial-batch states.
- **Impact:** Users cannot distinguish waiting, no matches, or failure, nor know which bulk edits succeeded.
- **Fix:** Implement the state/recovery matrix below. Preserve filters, draft values, and appropriate selection during recoverable failures.

### P1 — Rendering and filtering scale poorly by construction

- **Evidence:** All 10,000 rows mount; filtering recalculates synchronously on every keystroke.
- **Impact:** Unbounded rendering and synchronous work are confirmed. Input lag, long tasks, memory pressure, and dropped frames are **runtime hypotheses**, not measured facts.
- **Fix:** Bound mounted rows using an existing windowing capability or an agreed incremental rendering strategy; retain the table workflow. Measure filtering separately before choosing scheduling, indexing, or computation changes.

### P1 — Tablet and keyboard access are at risk

- **Evidence:** `.page` has `min-width: 1180px`; drawer is fixed at `520px` with `100vh`; `.icon-button` removes outlines. Tablet behavior, focus-visible styling, and navigation are unspecified.
- **Impact:** The page cannot shrink below 1180 CSS pixels under the supplied rule. Exact viewport clipping and any replacement focus indicator require project context.
- **Fix:** Allow the page shell to shrink, constrain horizontal scrolling to the table, adapt the drawer to available width/height, and provide visible keyboard focus.
- Verify table semantics and keyboard operation; CSS grid styling alone proves neither their presence nor absence.

### P2 — Hostile content and upload handling

- **Evidence:** Names span 1–200 characters and truncate; prices may be missing; labels can expand 60%; images may be absent or 8MB; image space is not reserved.
- **Impact:** Hidden product distinctions, ambiguous prices, control overflow, and unstable loading geometry are risks. Actual layout shift and upload failures remain **unmeasured**.
- **Fix:** Apply the content and upload rules below. Escalate to P1 if truncation prevents reliable identification or upload failure blocks editing.

### P2 — Overbroad motion and small touch controls

- **Evidence:** Rows and drawer use `transition: all 300ms ease-in`; icon buttons measure `28px × 28px`; reduced-motion behavior is unspecified.
- **Impact:** Unintended property animation and touch errors are plausible; frame drops are not established.
- **Fix:** Transition only intended properties; use existing motion tokens and a reduced-motion alternative. Expand effective touch areas toward 44px without changing icon size or overlapping adjacent targets.
- A 28px target is not automatically a WCAG 2.2 AA target-size failure: the general minimum is 24px, subject to exceptions and actual geometry.

### P3 — Final consistency pass

- Once functional states exist, align table/drawer spacing, status placement, labels, tooltip behavior, and animation timing with incumbent patterns.
- These are bounded polish checks, not verified visual defects; no rendered surface was supplied.

## 3. Concrete remediation contract

### Hostile data and localization

- Keep dense row truncation where useful, but expose the complete product name in the drawer and a keyboard/touch-accessible reveal—not only a hover tooltip or `title`.
- Preserve a stable identifier beside ambiguous names. Test long unbroken strings; use shrinkable grid tracks such as `minmax(0, 1fr)` and `min-width: 0` where appropriate.
- Render missing prices as “Not set” or the existing equivalent; never convert absence to zero. Use locale-aware currency formatting and preserve numeric alignment.
- Allow filter labels, drawer actions, and error text to wrap under 60% expansion. Test localized plurals and 200% text sizing; avoid assembling translated sentences from fragments.
- Reserve thumbnail dimensions or aspect ratio. Provide absent/broken-image fallbacks and appropriate alt text; avoid repeating a nearby name for purely decorative thumbnails.
- Publish upload limits before selection. Validate size/type on client and server, handle decode failures, and support progress, retry, and cancellation.
- Use correctly sized thumbnails rather than 8MB originals in rows. Keep original-quality policy unchanged unless agreed; release temporary preview URLs.

### Failure and recovery matrix

| Situation | Required behavior |
|---|---|
| Initial loading | Stable loading structure, concise status, and no premature “no products” message. |
| Filter loading | Retain prior results where safe, mark them updating, and prevent bulk actions from targeting an ambiguous result set. |
| Empty results | Distinguish an empty inventory from no filter matches; offer the appropriate existing create or clear-filter action. |
| 401 | Request reauthentication; preserve drafts within the product’s security policy and do not replay writes blindly. |
| 403 | Explain insufficient permission; remove unavailable affordances or disable with a reason. Server authorization remains authoritative. |
| 409 | Preserve local edits, fetch the current version, and offer comparison/reconciliation; do not silently overwrite. |
| 429 | Respect `Retry-After`; show a useful wait state and avoid aggressive automatic retries. |
| 500 / timeout | Keep the draft and offer retry. A timeout may follow a successful write: reconcile status or use an idempotency mechanism before replaying. |
| Offline | Show unsaved/offline status; retain the draft. Only promise queued persistence if implemented and safe; reconcile versions on reconnect. |
| Partial batch failure | Report succeeded/failed counts and per-item reasons; preserve failed-item context and retry only failures. |

- Scope selections by stable IDs, not row positions or mounted DOM. Explicitly distinguish “selected rows” from “all matching results,” especially when filters change.
- Keep “Saved” tied to the last acknowledged revision and timestamp. New edits during an in-flight save remain dirty.
- Add appropriately scoped draft recovery if reload recovery is required; define retention, account boundaries, and clearing behavior. Never imply durable recovery from component state alone.

### Responsive layout and accessibility

- Keep desktop information density. Let filters wrap; keep primary actions reachable; allow table-only horizontal scrolling rather than forcing the entire page wide.
- Bound drawer width by the viewport and use dynamic viewport height with an appropriate fallback. Scroll its content internally; ensure action controls remain reachable with a tablet keyboard open.
- Prefer native table semantics for tabular data, labeled row checkboxes, a correctly represented mixed-state select-all control, and associated column headers.
- Do not add `role="grid"` without its expected keyboard model. With windowing, preserve focus and expose correct row counts/positions where applicable.
- Associate field errors with inputs; announce save success politely and actionable errors without announcing every keystroke.
- Restore focus sensibly if the original row is filtered out or unmounted. Provide a clear focus-visible treatment, meaningful button names, and accessible upload controls.
- Honor reduced motion without removing essential saving/error feedback.

### Performance without changing the product

- Baseline row mounting, filter computation, React commits, image decoding, and network cost separately.
- Bound mounted rows with overscan; validate selection, keyboard focus, scroll position, variable text height, and assistive technology before rollout.
- Keep filter input responsive. Defer result updates or chunk expensive computation as supported; deferral alone does not make a single expensive computation cheap.
- Memoize derived results and rows only where profiling demonstrates avoidable work; maintain stable props and handlers where beneficial.
- Lazy-load below-fold thumbnails, not immediately needed imagery. Reserve image geometry and request appropriately sized assets.
- Remove broad transitions; animate drawer transform/opacity only when appropriate. Avoid speculative blanket `will-change` or dependency additions.

## 4. What static signals establish—and what they do not

| Signal | Decisive conclusion | Context still required |
|---|---|---|
| Empty `catch` | Save errors are discarded by this handler. | Whether another layer logs errors or misleadingly shows success. |
| Shared `saving` boolean | State cannot distinguish concurrent requests. | Whether callers permit overlap and how the server orders writes. |
| 10,000 mapped rows + synchronous filtering | Work is unbounded by the viewport and runs synchronously. | Actual latency, commit cost, memory, and benefit of each optimization. |
| `min-width: 1180px`, fixed drawer | Supplied rules constrain available shrinkage. | Cascade, containers, tablet viewport, zoom, and keyboard behavior. |
| `outline: none` | Native outline is suppressed by this rule. | Replacement focus styles elsewhere; actual focus contrast and visibility. |
| Icon-only controls / 28px size | Labels are not visible; declared box is small for touch comfort. | Accessible names, effective hit area, spacing, and conformance. |
| `transition: all` | Every changing animatable property is eligible. | Which properties change, motion sensitivity, and rendering cost. |
| Ellipsis / unreserved images | Names are visually truncated; image geometry is not reserved. | Full-name access, identification impact, actual layout shift. |

Static warnings are triage inputs, not severity scores. Fixed dimensions, ellipsis, and icon controls can be legitimate in a dense operations tool. No evidence supports claims about dark-mode failure, poor contrast, unnecessary packages, or a need to replace the design system.

## 5. Measurement-first validation and release gates

**Proposed work—not executed:**

1. **Baseline:** Use representative 10,000-row data, 200-character names, missing prices/images, 8MB uploads, expanded translations, and permission variants. Record agreed desktop/tablet devices and browser versions.
2. **Capture:** Measure input-to-next-paint latency, filter-to-settled-results time, long tasks, React render/commit duration, mounted row count, heap trend, image bytes, and layout shift. Measure save acknowledgement separately from client responsiveness.
3. **Exercise failures:** Inject each matrix state, reordered save responses, rapid edits, close-during-save, filter changes during selection, and partial batch outcomes.
4. **Manual access checks:** Keyboard-only editing, screen-reader table/drawer interaction, focus restoration, reduced motion, 200% text sizing, zoom, tablet portrait/landscape, and the on-screen keyboard.
5. **Set budgets before implementation:** Provisional targets include p75 interaction latency ≤200ms on agreed devices, no image-induced table jumps, and mounted row count bounded by viewport plus overscan. Use repeated traces; do not equate a lab interaction measurement with field INP.
6. **Correctness acceptance:** Zero silently discarded save errors, stale overwrites in race tests, lost recoverable drafts, duplicate retried writes, or selection mismatches. Every failure has a truthful state and recovery action.
7. **Usability acceptance:** All editing and batch tasks complete by keyboard and supported tablet input; no inaccessible actions, focus escapes from modal drawers, or page-level clipping. Localization must not hide required actions.
8. **Staged rollout:** Separate state/recovery, rendering, and polish changes where practical. Compare completion rates, save errors/conflicts, latency distributions, and support signals against baseline.
9. **Rollback:** Roll back a rendering optimization immediately for selection corruption, lost focus, inaccessible rows, or material latency/memory regression. Roll back affected releases for lost edits or false save success; retain truthful failure handling through a safe fallback rather than restoring silent errors.

Finish with a bounded consistency pass and regression check—not a new visual direction.
