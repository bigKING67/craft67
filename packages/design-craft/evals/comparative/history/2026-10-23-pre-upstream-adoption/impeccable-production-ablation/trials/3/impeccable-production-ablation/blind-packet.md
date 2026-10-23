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

**Sequence:** audit the source and workflow → establish baseline measurements → harden data integrity, failure recovery, and accessibility → polish within existing components and tokens → optimize measured bottlenecks → validate and release incrementally.

**Verdict:** Not production-ready as described: silent save failures, ambiguous concurrent-save state, inaccessible drawer behavior, and unbounded rendering require hardening before cosmetic polish.

This is a read-only assessment of the supplied description. No files were edited and no detector, browser, build, profiler, accessibility-tree, network-throttle, or device run was performed. “Confirmed” below means evidenced by that description; runtime effects remain unverified.

## 2. Prioritized findings

Priorities: **P0** release-blocking integrity/security issue; **P1** core-workflow blocker; **P2** material usability/resilience issue; **P3** lower-risk refinement.

| Priority | Finding and source evidence | Runtime hypothesis / uncertainty |
|---|---|---|
| **P0** | **Save failure is hidden.** `catch {}` discards errors and `saving` becomes false after either outcome. Failure and retry states are absent. | Users may interpret completion as persistence. Actual data loss depends on whether drafts remain available; no false “Saved” text is shown in the excerpt. |
| **P1 → P0 if reproduced** | **Save ordering is unspecified.** A single Boolean tracks all calls, with no shown concurrency or version control. One completion can clear `saving` while another call remains pending. | Overlapping saves may overwrite newer edits if the API does not enforce ordering or revisions. Verify before asserting corruption. |
| **P1** | **Drawer interaction is incomplete.** No focus trap or background blocking; Escape closes during save; save/close are icon-only; labels and keyboard behavior are unspecified. | For a modal drawer, focus may escape and background actions may conflict. Draft loss on dismissal depends on state ownership. Icon-only controls are not inherently inaccessible if named. |
| **P1** | **Critical states are missing.** Loading has a blank body; authentication, permission, conflict, rate-limit, server, timeout, offline, retry, and partial-batch states are absent. | Users cannot reliably distinguish waiting, empty results, denied access, or failure. Backend handling is unknown. |
| **P1** | **Rendering and filtering are unbounded.** All 10,000 rows mount; filtering recalculates synchronously on each keystroke. | Long input latency, costly commits, memory pressure, and scroll stalls are likely, but timings are unmeasured. |
| **P1** | **Tablet layout is constrained.** `.page` has `min-width: 1180px`; the drawer is fixed at `520px` wide and `100vh` tall. | Page-level overflow, hidden actions, and keyboard/browser-chrome occlusion depend on viewport and surrounding CSS. |
| **P1** | **Focus and target usability are at risk.** `.icon-button` removes outlines and is `28px × 28px`; no replacement focus-visible treatment is described. | Lost keyboard focus visibility depends on other styles. A 28px target is not automatically below the 24px WCAG minimum, but is small for touch. |
| **P1 verification gate** | **Bulk selection scope and permission-specific affordances are unspecified.** Bulk actions exist, and partial failure has no representation. | Stale or ambiguous selection may affect unintended products. Server authorization and selection semantics cannot be inferred from this excerpt. |
| **P2** | **Hostile data and images lack explicit treatment.** Names span 1–200 characters, prices can be missing, labels can expand 60%, and images may be absent or 8MB. Dimensions are not reserved. | Truncation may hide identifying details; images may cause shifts or memory/network pressure. Currency formatting and upload checks are unknown. |
| **P2** | **Motion is overbroad.** Rows and drawer use `transition: all 300ms ease-in`; reduced motion is unspecified. | Layout-property animation is possible, not proven. Blanket transitions can also create unintended effects after future CSS changes. |
| **P3** | **Visual finish needs a consistency pass after hardening.** Fixed column sizes, truncation, icon-only actions, and autosave feedback warrant review against existing tokens. | Spacing, contrast, alignment, and perceived hierarchy cannot be judged from these snippets alone. |

## 3. Concrete hardening and polish

### Persistence, failures, and recovery
- Replace the Boolean-only model with explicit states: **clean, dirty, saving, saved, failed, conflict**; record the last server-confirmed revision.
- Preserve the current draft on every failure. Mark a revision saved only after its matching acknowledgement; retain dirty status when newer edits exist.
- Serialize/coalesce autosaves per product, or use request IDs plus server-side revision checks. Ignoring stale responses alone does not prevent stale server writes.
- Use `finally` for cleanup, but do not treat cleanup as success. Track pending operations per product or request rather than one shared flag.
- For a **409**, retain local edits and offer refresh/compare/reapply against the latest version; do not blindly retry an overwrite.
- For **401**, offer reauthentication without discarding the draft; for **403**, explain denied access and retain recoverable work where policy permits.
- For **429**, honor `Retry-After`; for **500/timeouts**, offer clear retry and use bounded automatic retries only when the operation is safely repeatable.
- Treat a timeout as an **unknown outcome**, not proof the write failed. Reconcile with the server or use supported idempotency keys before retrying.
- Show offline state explicitly; do not imply durable offline queuing unless it exists. Avoid storing sensitive inventory drafts persistently without policy approval.
- For batches, report succeeded/failed counts and per-item reasons. Retry only failed items and reconcile successful rows with server results.
- Define dismissal during dirty/pending states: either preserve drafts and saving independently of drawer visibility, or provide an accessible close confirmation. Closing must not silently discard work.
- Show stable loading placeholders initially; during filtering, keep previous results clearly marked as updating where appropriate. Separate empty inventory, no matches, and load failure.
- Define “select all” scope explicitly: visible page, filtered results, or entire inventory. Use stable IDs, disclose hidden selections, and reconcile selection after filters, deletes, and failures.
- Match edit/bulk affordances to permissions, while enforcing authorization on the server. Recover gracefully if permission changes mid-session.

### Hostile data and uploads
- Keep ellipsis where required, but make full names available through drawer details or an accessible focus/touch disclosure—not hover-only or `title` alone.
- Allow labels and validation messages to wrap. Use `min-width: 0` on shrinking grid children; test long unbroken strings and 60% label expansion.
- Distinguish missing price from zero; display a deliberate “Not set” state and format real values using the correct currency and locale.
- Reserve thumbnail dimensions/aspect ratio; provide consistent absent/broken-image fallbacks.
- Serve appropriately sized thumbnails rather than originals. Lazy-load offscreen images without delaying initially visible content.
- Enforce upload size, type, and decoded-dimension limits client-side for feedback and server-side for enforcement. An 8MB file is not automatically invalid: apply the product’s actual limits.
- Provide upload progress, cancel, retry, and clear rejection messages. Keep the prior image until replacement succeeds; clean up temporary preview resources.

### Responsive layout and accessibility
- Remove the page-wide minimum width. Keep any necessary table minimum width inside a labelled horizontal scroll region, not on the entire route.
- Preserve important identifying/action columns and existing column controls; do not silently hide operationally essential information on tablet.
- Constrain the drawer to the viewport, for example `width: min(520px, 100%)`; use a `100dvh` strategy with fallback and an internally scrolling body.
- Keep save/status controls reachable with touch, zoom, safe areas, and the on-screen keyboard. Let filters wrap without changing workflow.
- Decide whether the drawer is modal. If modal, provide a named dialog, meaningful initial focus, focus containment, inert background, and focus restoration.
- If intentionally nonmodal, do not add a focus trap; provide a clear keyboard route between drawer and table. Preserve the pending-save dismissal safeguards either way.
- Use real buttons with accessible names such as “Save product” and “Close editor.” Restore visible focus treatment using existing design tokens.
- Increase touch hit areas toward 44px where practical without unnecessarily enlarging icons; check spacing and overlap.
- Prefer native table semantics unless the established component intentionally implements a grid. Use labelled row-selection controls and a mixed-state select-all checkbox.
- Announce save progress/success politely and actionable failures promptly, without repeating announcements on every keystroke. Associate field errors with fields.
- Scope transitions to intentional properties, typically `transform`/`opacity` for the drawer. Respect reduced motion and avoid animating ordinary row layout updates.

### Performance without changing the product model
- Measure render, filter, layout, image decode, and memory costs separately before choosing the largest optimization.
- Bound mounted rows using the existing table’s virtualization or established pagination capability. Do not introduce a dependency merely for this audit.
- Preserve stable selection, focus, row position, and accessible row information when rows mount/unmount; focused controls must not disappear unexpectedly.
- Keep typed input immediate; debounce or defer result work as appropriate. React deferral does not make a monolithic synchronous filter cheaper.
- Cache normalized searchable fields and stable derived results. Consider chunking, a worker, or server filtering only if measurements justify it.
- Apply row memoization only where profiling shows avoidable rerenders; stabilize relevant props. Account for selection/header updates.
- Use bounded overscan and thumbnail loading, then verify scroll smoothness, screen-reader behavior, and memory together.

## 4. Static signals: decisive versus contextual

**Decisive evidence of implementation gaps**
- Empty error handling provides no local failure recovery.
- One Boolean cannot accurately represent multiple simultaneous saves.
- Loading/failure/partial-success representations are explicitly absent.
- All 10,000 rows mount, and filtering runs synchronously per keystroke.
- The CSS explicitly imposes the wide minimum, removes outlines, and transitions all properties.

**Require project or runtime context**
- Rendering 10,000 rows proves workload, not a specific latency or memory number.
- `outline: none` proves outline removal, not invisible focus if another visible treatment exists.
- Icon-only controls need accessible names; the icon presentation alone is not a failure.
- `transition: all` is fragile, but does not prove layout thrashing without changing properties and traces.
- `100vh` and fixed widths need viewport/keyboard checks; tablet breakage should not be claimed as observed.
- Missing dimensions create shift risk; actual shifts depend on other sizing constraints and load timing.
- Ellipsis, a 28px target, and an 8MB image are not universal failures; disclosure, spacing, policy, and resource delivery matter.
- Authorization flaws, XSS, actual data loss, contrast failures, and invalid table semantics are **not established** by the supplied source.

## 5. Measurement-first validation and release gates

1. **Define the matrix:** supported desktop/tablet browsers, viewport/zoom levels, touch and keyboard, representative permissions, 10,000 realistic rows, and hostile-data fixtures.
2. **Record a baseline:** initial usable-table time, input-to-result latency, render/commit cost, long tasks, mounted nodes, memory after repeated drawer cycles, image transfer/decode cost, and layout shift.
3. **Set budgets before implementation:** proposed targets include field p75 INP ≤200ms and CLS ≤0.1; separately measure filter-result latency because INP alone does not capture it. Agree a reference device and filter/render budgets.
4. **Exercise persistence deterministically:** delayed, reordered, failed, and ambiguously completed saves; rapid edits; switching products; close/reopen; reauthentication; conflicts; and partial batches.
5. **Verify invariants:** no stale write wins, no false saved state, drafts survive failures, only intended IDs are changed, successful batch items are not retried, and denied operations never reach unauthorized success.
6. **Check accessibility manually and with appropriate tooling:** names, table relationships, focus order/restoration, modal containment, error/status announcements, zoom, touch targets, reduced motion, and virtualized-row navigation.
7. **Check layout and loading:** no page-level overflow at supported widths, deliberate table scrolling, reachable drawer actions with keyboard open, stable image space, and distinguishable loading/empty/error states.
8. **Compare changes independently:** hardening first; then bounded rendering/filter changes and image/motion polish. Retain baseline traces and inspect regressions rather than accepting a single aggregate score.
9. **Release incrementally:** use existing rollout controls; monitor save/conflict/retry rates, pending-save duration, client errors, interaction latency, and support reports without logging sensitive drafts.
10. **Accept only when** integrity invariants and supported accessibility/device checks pass, agreed budgets are met, and core workflow has no material regression.
11. **Pause or roll back** on lost drafts, wrong-row/batch writes, false success, inaccessible primary actions, or breached regression thresholds. Revert risky optimizations independently; if persistence safety fails, disable affected editing rather than restoring silent failure.


## Output B

## 1. Sequence and verdict

**Sequence:** establish baseline and audit → harden correctness, recovery, accessibility, and responsive behavior → optimize measured bottlenecks → polish within the existing design system → validate and stage release.

**Verdict:** Not ready for production sign-off: save failures are suppressed, recovery states are absent, and drawer interaction is unsafe; the 10,000-row hot path is a serious P1 risk, not a measured performance failure.

This is a read-only assessment of the supplied description. No files were changed; no detector, browser, build, profiler, accessibility-tree, network-throttle, or device checks were performed.

## 2. Prioritized findings and concrete repairs

“Evidence” means supplied source or notes. “Unknown” identifies behavior requiring additional context or runtime verification. P0 blocks release; P1 belongs in this hardening effort; P2 needs scheduled remediation or explicit risk acceptance; P3 is polish.

### F1 — P0: Failed saves have no trustworthy outcome
- **Evidence:** `catch {}` suppresses rejection; `saving` becomes false after either success or failure. The callback resolves without exposing failure.
- **Unknown:** Whether another layer reports errors; whether the drawer interprets resolution as success, clears drafts, or closes. Actual data loss is not established.
- **Repair:** Return an explicit save result or propagate a handled error. Represent dirty, saving, saved, and failed states; only acknowledge saved after server confirmation. Preserve the draft on failure and provide Retry.
- **Repair:** If saves can overlap, serialize/coalesce per product and associate responses with product ID and revision. A single boolean cannot describe multiple requests; stale responses must not overwrite newer edits. Clear pending state through ownership-aware finalization.
- **Acceptance:** Rejected, delayed, reordered, and repeated requests never produce false success or erase edits; confirmed server values reconcile into the row and drawer.

### F2 — P1: Failure and recovery workflows are missing
- **Evidence:** Initial/filter loading is blank; empty, authorization, conflict, rate-limit, server, timeout, offline, retry, and partial-batch states are not represented.
- **Unknown:** API retry/idempotency contracts, draft persistence policy, and selection semantics across filters.
- **Repair — loading/empty:** Show a stable loading structure with a labeled busy state. During refiltering, retain explicitly marked previous results where safe; prevent bulk actions against ambiguous results. Distinguish “No products” from “No matches,” with an authorized creation action or Clear filters respectively.
- **Repair — 401/403:** Offer sign-in recovery for expired authentication; render read-only/denied affordances for insufficient permission. Retain drafts only within approved security boundaries. Server authorization remains mandatory.
- **Repair — 409:** Show a conflict explanation with server and draft values; offer review/merge or explicit reload, never silent overwrite.
- **Repair — 429/500:** Respect `Retry-After`, show when retry is available, and retain work. Offer bounded retry for transient server failures; do not retry mutations blindly.
- **Repair — timeout/offline:** Show “Save unconfirmed” or “Offline—changes not saved.” A timeout may follow a committed write: reconcile by operation ID/version before retrying, or use an agreed idempotency contract. Do not imply an offline queue exists.
- **Repair — partial batch:** Show succeeded/failed counts and per-item reasons; retry only failed IDs. Keep selection keyed by stable IDs, state whether selection covers visible or all matching rows, and preserve that scope explicitly.
- **Acceptance:** Inject each state and verify what renders, the recovery action, retained filters/drafts/selection, and the final server result. Filter responses must not replace newer results out of order.

### F3 — P1: Drawer lifecycle and controls lack safe accessible behavior
- **Evidence:** No focus trap or background-interaction containment; Escape closes during saves; Save/Close are icon-only; buttons are `28px × 28px` with `outline: none`. Labels and keyboard behavior are unspecified.
- **Unknown:** Whether the drawer is intended to be modal, accessible names exist elsewhere, effective hit areas are larger, or other CSS supplies focus indication.
- **Repair:** For a modal drawer, use the existing dialog primitive: accessible title, modal semantics, initial focus, contained Tab navigation, inert background, and focus restoration. For an intentionally nonmodal drawer, do not add a trap; provide deliberate focus navigation instead.
- **Repair:** Route Escape, Close, outside-click, and navigation through one dirty/pending-close policy. Keep drafts and save ownership alive if dismissal is allowed; otherwise explain the pending state and provide a recovery path. Closing the UI must not imply a server write was canceled.
- **Repair:** Name Save/Close accessibly; restore visible `:focus-visible`. Provide nonoverlapping effective targets of at least **44 × 44 CSS px** as a provisional tablet comfort floor, preserving icon size and existing styling.
- **Repair:** Use table/header semantics, labeled row-selection checkboxes, mixed-state select-all, and labeled filters/errors. Use a grid keyboard model only if the existing interaction warrants it. Announce save/batch summaries without announcing every keystroke.
- **Acceptance:** Complete filter → select → edit → save → recover → close by keyboard and assistive technology; verify focus order, announcements, background containment, and touch targets.

### F4 — P1: Fixed geometry conflicts with tablet support
- **Evidence:** Page minimum width is `1180px`; columns use `64px 280px 1fr 120px 96px`; drawer is fixed at `520px × 100vh`.
- **Unknown:** Actual clipping, scroll containers, enclosing layout, tablet viewport, zoom, and software-keyboard behavior.
- **Repair:** Remove the page-level width floor; give layout children `min-width: 0`. Keep any necessary table minimum width inside a labeled horizontal-scroll region, not on the entire route.
- **Repair:** Adapt the column template using bounded flexible tracks such as `minmax(0, 1fr)` and content-aware limits; preserve critical identity, selection, and actions. Wrap filter controls and translated labels.
- **Repair:** Cap drawer width at available viewport width, retaining 520px where space permits. Use dynamic viewport height with a fallback, independently scrollable content, and reachable header/footer actions above the software keyboard.
- **Acceptance:** Desktop and supported tablet orientations, 200% zoom, long translations, and keyboard-open editing retain every essential action without page-wide horizontal overflow.

### F5 — P1: Render/filter work has no scalable bound
- **Evidence:** All 10,000 rows mount; filtering recalculates synchronously on every keystroke. Parent `saving` changes also revisit the row-mapping path.
- **Unknown:** Actual input delay, render cost, row memoization, memory use, and device-specific task failure.
- **Repair:** Establish measurements first, then impose a mounted-row bound using the existing pagination/windowing capability. Preserve workflow, stable IDs, selection across unmounted rows, focus, and accessible row context.
- **Repair:** Measure filter computation separately from rendering. Choose the smallest effective remedy: cached normalized search data, deferred result updates, cancellation of stale requests, or a worker/server filter only if justified. Debouncing alone does not remove expensive work.
- **Repair:** Isolate drawer status updates from unrelated table work where profiling supports it; do not blanket-memoize or add a dependency by default.
- **Acceptance:** Meet the provisional performance gates below without altering results, keyboard navigation, or bulk-selection semantics. Escalate to P0 only if target-runtime evidence establishes task failure.

### F6 — P2: Hostile text, prices, and images need explicit treatment
- **Evidence:** Names span 1–200 characters and are ellipsized; prices may be missing; translations expand 60%; images may be absent or 8MB; image dimensions are not reserved.
- **Unknown:** Existing full-name disclosure, currency rules, upload limits, thumbnail delivery, and actual layout shift.
- **Repair:** Keep compact truncation if consistent with the system, but expose the full name through keyboard/touch-accessible detail or disclosure—not hover alone. Handle unbroken strings and supported text directions; retain the full accessible name.
- **Repair:** Render missing prices as a meaningful “Not set” state, distinct from zero; use locale-aware currency formatting and explicit validation.
- **Repair:** Reserve image width/height or aspect ratio for images and fallbacks. Serve appropriately sized thumbnails, load offscreen images lazily, and define suitable alternative text.
- **Repair:** State upload size/type limits before selection; validate both client and server. For 8MB files, support the approved processing path or reject clearly while retaining edits. Show upload progress/failure/retry/cancel and prevent save from falsely implying an incomplete upload is stored.
- **Acceptance:** Test 1/20/60/200-character and unbroken names, missing/zero prices, +60% labels, absent/broken images, and 8MB uploads; no inaccessible information, unstable image slots, or lost form state.

### F7 — P2: Motion is broad and reduced-motion behavior is unspecified
- **Evidence:** Rows and drawer use `transition: all 300ms ease-in`; reduced-motion handling is not described.
- **Unknown:** Which properties actually change and whether animation causes layout work or perceptible lag.
- **Repair:** Transition only intended properties, preferably drawer transform/opacity; remove unintended row transitions. Honor reduced motion while preserving immediate state feedback. Reuse existing motion tokens.
- **Acceptance:** Inspect actual transitions and reduced-motion behavior; no hidden controls, delayed feedback, or unnecessary layout animation.

### F8 — P3: Final visual consistency needs a bounded polish pass
- **Evidence:** The existing design system must remain authoritative; supplied snippets cannot establish visual alignment or contrast quality.
- **Unknown:** Rendered density, spacing, typography, theme parity, and state consistency.
- **Repair:** After F1–F7, reconcile control alignment, status copy, truncated-name disclosure, and loading/error states with existing components and tokens. Avoid changing information architecture or table density gratuitously.
- **Acceptance:** Compare equivalent controls and states at desktop/tablet sizes; approve only purposeful differences.

## 3. Static signal reconciliation

- **Decisive within scope:** Empty error handling and the declared missing states prove local recovery gaps. Direct rendering of 10,000 rows and per-keystroke synchronous filtering prove work scales with the dataset, not that latency exceeds a budget.
- **Decisive interaction evidence:** The notes explicitly establish absent drawer containment and pending-save dismissal. Whether dismissal loses data still depends on state ownership.
- **Context-dependent CSS:** Fixed widths are not inherently wrong for desktop data tables; route-level overflow versus contained table overflow matters. `520px` may fit some tablets but does not establish an adaptive drawer.
- **Context-dependent accessibility:** `outline: none` is a warning until all focus styling is inspected; icon-only does not necessarily mean unnamed. A 28px visual box does not prove the effective target is 28px, though the supplied CSS provides no enlargement.
- **Context-dependent presentation:** Ellipsis can be appropriate with accessible disclosure. `ease-in` and 300ms are not automatic defects; `transition: all` is a broad-risk signal, not proof of jank.
- **Unproven runtime effects:** Missing image reservations create layout-shift risk; 8MB images create transfer/decode risk. Neither proves measured CLS, network cost, or memory exhaustion.
- Generic static warnings should trigger focused checks, not override intentional design-system choices or be reported as completed tests.

## 4. Measurement-first validation and release plan

**All steps below are proposed, not executed.**

1. **Freeze the baseline:** Record current workflow, components/tokens, supported browsers/tablets, permissions, API contracts, and selection semantics. Use representative synthetic inventory, including all F6 extremes.
2. **Measure before performance changes:** On representative desktop and the lowest-supported tablet, capture repeated initial loads, typing/filter completion, scrolling, drawer opening, saves, uploads, and bulk actions. Separate cold/warm cases and CPU/network scenarios.
3. **Collect comparable metrics:** Input-to-paint and input-to-correct-results p95, filter compute time, React commits, long tasks, mounted row count, image transfer/decode cost, CLS, and peak/retained memory. Use identical fixtures and conditions before/after.
4. **Ratify provisional gates:** These are proposals, not measured results or universal guarantees:
   - Input-to-paint p95 ≤100ms; input-to-final-filter-results p95 ≤200ms at 10,000 rows, including any debounce delay.
   - Maximum attributable main-thread task ≤100ms during filtering, scrolling, and drawer interaction.
   - Mounted product rows ≤200, or a documented viewport-plus-overscan bound agreed before implementation.
   - CLS ≤0.1 for the tested route lifecycle.
   - Peak route heap ≤150MB on the reference browser; after 20 edit/filter/upload cycles and controlled cleanup, retained heap growth ≤10MB.
   - For unaffected timing metrics, base-to-head p95 regression ≤10% **and** ≤20ms; peak memory regression ≤10%.
5. **Validate correctness first:** Exercise every F1/F2 failure and concurrency path, including close/unmount during saves, late filter responses, partial batches, permission changes, and upload cancellation. Assert both UI state and server outcome.
6. **Validate access and layout:** Perform F3/F4 keyboard, assistive-technology, touch, zoom, orientation, and software-keyboard checks; inspect contrast, focus visibility, and reduced motion. Capture representative states for visual review, not as proof of hidden behavior.
7. **Run existing checks when implementation is authorized:** Relevant unit/integration tests, type checks, lint, and build; no new test framework or UI dependency is required by this audit.
8. **Release in small reversible changes:** Separate save/recovery work, layout/accessibility, render bounding, and polish. Canary performance changes with error, conflict, retry, latency, and task-completion monitoring.

**Acceptance:** F1 resolved; P1 items pass their stated checks; remaining P2 risks have explicit owners and approval; the existing workflow and visual system remain intact. An optimization must materially improve its target metric or demonstrably reduce complexity without violating gates.

**Rollback/hold:** Stop rollout for false success, lost drafts, wrong bulk targets, duplicate writes, focus/selection regressions, or agreed budget violations. Revert the implicated change independently; if reverting would restore unsafe save behavior, disable the affected mutation path rather than knowingly reintroducing it.

**Current status:** Static audit complete; implementation, runtime behavior, performance, accessibility, and release acceptance remain unverified.


## Output C

## 1. Sequence and verdict

**Audit → harden → optimize → polish → targeted re-audit.** Establish a baseline before implementation; fix persistence, recovery, accessibility, and layout contracts first; optimize measured bottlenecks without breaking those contracts; finish with visual and interaction polish.

**Verdict: Not release-ready as described—silent save failures and missing recovery are release blockers; drawer accessibility, tablet layout, and unbounded rendering need hardening, not redesign.**

This is a read-only assessment of the supplied snippets and notes. No detector, browser, build, profiler, accessibility-tree inspection, network throttle, or device run occurred. No files were edited.

Keep the existing design system, table/editor workflow, and stable `row.id` keys. There is insufficient evidence to score contrast, theming, bundle size, or overall accessibility conformance.

## 2. Prioritized findings

**Evidence** means directly present in the supplied material. **Hypothesis** means an outcome that needs implementation inspection or runtime validation. Priorities reflect operational risk, not measured prevalence.

| Priority | Finding and source evidence | Impact / hypothesis | Required action |
|---|---|---|---|
| **P0** | **Save failure is suppressed.** `saveProduct` has `catch {}` and returns to `saving=false` after rejection. | Failure becomes indistinguishable from idle at this boundary. Actual “Saved” messaging and draft loss are not shown. | Represent failure explicitly; retain dirty values; provide safe retry; never report success without acknowledgement. |
| **P1** | **A boolean cannot represent overlapping saves.** Every request independently sets `saving=false`. | If saves overlap, an earlier completion can clear pending status while another request remains active. Stale writes are possible depending on API ordering. | Serialize/coalesce saves per product, track revisions and pending work, and reject stale acknowledgements. Treat confirmed overwrites as P0. |
| **P1** | **Drawer isolation and dismissal are unsafe.** No focus trap or background isolation; Escape closes during save. | For a modal drawer, keyboard users can reach obscured content. Closing may conceal unresolved work; actual cancellation or data loss is unverified. | Establish modal semantics and focus management; implement an explicit dirty/pending close policy. |
| **P1** | **Failure and recovery states are absent.** Notes omit authorization, conflicts, rate limits, server/network failures, and partial batch results. | Staff cannot distinguish retryable failures from rejected or uncertain writes. Bulk actions can leave inventory ambiguous. | Add outcome-specific recovery and per-item batch reconciliation. |
| **P1** | **Keyboard/accessibility support is unestablished.** Icon-only Save/Close; `outline:none`; labels and keyboard navigation not described. | Missing accessible names or replacement focus indicators would block use. Icon-only controls alone do not prove missing names. | Verify native controls, accessible names, focus-visible treatment, table semantics, and selection behavior. |
| **P1** | **Tablet layout is constrained.** `.page { min-width:1180px }`; drawer is fixed at `520px` and `100vh`. | Below 1180 CSS pixels, that page box exceeds the viewport. Actual scroll containment, clipping, and keyboard obstruction require testing. | Make the shell fluid; contain table scrolling; bound drawer width and usable height. |
| **P1** | **Work scales with all 10,000 rows.** Full `rows.map`; filtering runs synchronously on every keystroke. | Long tasks, slow typing, excessive DOM, and broad rerenders are credible risks, not measured results. | Profile and bound rendered rows; decouple input from expensive filtering. Preserve selection and accessibility. |
| **P2** | **Loading is visually blank.** Initial and filter loading have an empty body. | Users cannot distinguish loading, no matches, and failure. | Add distinct loading, updating, empty, and error states without unnecessary layout changes. |
| **P2** | **Hostile data is insufficiently handled.** Names are ellipsized; prices may be missing; labels expand 60%; images may be absent or 8MB; image space is unreserved. | Hidden identifiers, misleading prices, overflow, image failures, and layout shifts are plausible. | Add full-value access, locale-safe formatting, bounded text/image behavior, and upload validation. |
| **P2** | **Motion is indiscriminate.** Rows and drawer use `transition:all 300ms ease-in`; reduced-motion behavior is unspecified. | Changed layout properties may animate; jank is not established without knowing which properties change. | Transition only intentional properties; provide a reduced-motion alternative. |
| **P3** | **Final consistency pass remains.** The supplied CSS applies the same motion treatment to different interactions. | Timing and feedback may feel inconsistent with existing components; no visual comparison was supplied. | After functional fixes, align timing, spacing, truncation affordances, and status copy with existing tokens/components. |

## 3. Concrete production fixes

### Persistence, failures, and state recovery

- Replace the single status flag with explicit **clean, dirty, queued, saving, saved, failed, and conflict** states as needed; track uploads separately.
- Associate requests with product ID and revision. A response must not mark newer edits clean or update a different product’s drawer.
- Use per-product save serialization or latest-draft coalescing; use server version checks where supported. Client ordering alone does not prevent multi-user conflicts.
- Show “Saved” only for the acknowledged revision. Expose pending changes, failure, and last confirmed save without announcing every keystroke.
- Preserve draft values and validation errors after failure. Keep save state outside drawer lifetime if saving is allowed to continue after dismissal.
- On dirty or pending close, offer a clear policy: stay, explicitly discard unsent edits, or close while tracked work continues. Do not imply that closing or aborting a request reverses a server write.
- Prevent silent duplicate submission. After uncertain outcomes, reconcile with server state before repeating a write; use idempotency support where available.

| Condition | Recovery behavior |
|---|---|
| **401** | Preserve a draft within approved security/storage policy; request sign-in; reconcile before resubmission. |
| **403** | Explain the permission restriction; remove or disable unauthorized actions with an accessible reason. Keep server authorization authoritative. |
| **409** | Preserve local edits; fetch the current version; show conflicting fields and an explicit resolve/reapply path. Never silently overwrite. |
| **429** | Honor `Retry-After`; retain edits; show when retry becomes available. Avoid rapid automatic retries. |
| **500 / timeout** | Keep edits and show retry guidance. A timeout can mean “outcome unknown,” not “nothing saved.” |
| **Offline** | Mark edits unsynced. Do not promise durable offline queuing unless implemented; reconcile on reconnect. |
| **Partial batch failure** | Report succeeded, failed, and unknown items separately. Retain failed-item selection; retry only eligible unresolved items after reconciliation. |

- Define selection scope explicitly: visible rows, filtered results, or all products. Filtering and virtualization must not silently change that scope.
- Keep filters, sort, scroll position, selection, and drawer draft stable through recoverable failures.
- Separate “no inventory” from “no matching results”; offer the appropriate existing action, such as clearing filters.
- During filtering, retain existing results with an updating indicator when safe; prevent bulk actions from ambiguously targeting stale versus new results.

### Hostile data and images

- Test 1- and 200-character names, unbroken strings, non-Latin text, and bidirectional text. Render names as text, not injected HTML.
- Allow grid children to shrink with `min-width:0`; use bounded tracks such as `minmax(0,1fr)` where appropriate.
- Preserve compact table truncation, but expose full names through keyboard- and touch-accessible details—not hover-only tooltips. Wrap long text in the drawer.
- Distinguish missing prices from zero. Use a meaningful “Not set” state and locale-aware currency formatting; validate numeric ranges and precision.
- Allow translated labels to wrap and controls to grow. Test 60% expansion and text zoom without hiding critical actions.
- Reserve thumbnail dimensions/aspect ratio, including loading, missing, and failed-image placeholders.
- Serve suitably sized thumbnails rather than original uploads in rows. Lazy-load offscreen imagery while prioritizing visible content.
- Set and communicate upload byte, type, and pixel limits. Validate on the server as well as the client; provide progress, failure, retry, and cancellation.
- If 8MB files are allowed, use the existing image pipeline for bounded resize/compression where appropriate. If not, reject clearly before upload rather than silently failing.

### Responsive layout and accessibility

- Remove the page-level width floor; preserve dense columns inside a clearly bounded horizontal table scroller. Do not turn the entire page into a sideways viewport.
- Keep key identifiers and bulk controls discoverable. Do not hide operationally necessary columns merely to fit tablet widths.
- Bound drawer width to available space, for example `width:min(520px,100%)`; use an appropriate dynamic viewport height with fallback, internal scrolling, and reachable actions.
- Test tablet orientation, browser zoom, and the on-screen keyboard. Wrap filters and bulk controls without changing their workflow.
- If the drawer is modal, provide an accessible dialog name, initial focus, contained Tab navigation, inert background, and focus return to the trigger or a stable fallback.
- If it is intentionally non-modal, do not falsely use `aria-modal` or trap focus; instead provide clear navigation between drawer and table.
- Use named native buttons for Save and Close. Restore a visible keyboard focus treatment using existing tokens.
- A 28×28 control is below a useful **44×44 touch target**, but is not automatically below WCAG 2.2 AA’s 24×24 minimum. Enlarge effective hit areas for tablet use without overlapping neighbors.
- Use table/header semantics and labeled selection checkboxes with a mixed-state select-all control. If using an interactive grid, implement its full keyboard contract rather than adding a role alone.
- Associate field errors and help text programmatically. Announce save/loading outcomes through restrained live regions.
- For reduced motion, remove nonessential movement while preserving immediate state feedback.

### Performance without a dependency pitch

- Measure row render/commit cost and filter cost separately before choosing changes.
- Bound mounted rows using existing windowing capability or a minimal implementation. Preserve row identity, selected IDs, focus, scroll restoration, and access to offscreen results.
- Keep input updates immediate; defer or debounce expensive filtering as appropriate. Deferring rendering alone does not move CPU work off the main thread.
- Normalize searchable fields once when data changes. Consider chunking, a worker, or server filtering only if measurements and existing architecture justify it.
- Memoize rows only where profiling shows avoidable work and stable props make it effective; keep frequently changing save status from needlessly invalidating the table.
- Limit transitions to deliberate properties, usually transform/opacity for drawer movement. Do not add blanket `will-change`.

## 4. Static signals: decisive versus contextual

**Decisive from the supplied source**
- Rejected saves are swallowed at the shown boundary.
- Every row is mounted; filtering is synchronous on each keystroke.
- The page has a fixed minimum width; the drawer has fixed width/viewport-height rules.
- The shown rule removes the outline and transitions all animatable properties.
- Loading, failure, and image-space handling are absent as described.

**Require project or runtime context**
- Whether another style restores focus visibility; whether icon buttons have accessible names.
- Whether the drawer is intended to be modal and whether dismissal actually loses data.
- Whether overlapping requests occur and whether server safeguards prevent stale writes.
- Whether overflow is already contained by an ancestor.
- Actual typing latency, memory use, frame drops, image transfer sizes, and layout-shift magnitude.
- Whether ellipsis has an accessible full-value alternative.
- Contrast, dark-mode behavior, permissions enforcement, bundle waste, and complete semantic markup.

Static rules identify implementation patterns, not complete user outcomes. Fixed dimensions and ellipsis can be appropriate inside controlled layouts; missing memoization is not inherently a defect. Conversely, a clean static scan would not establish recoverable saves, correct batch semantics, or usable keyboard interaction.

## 5. Measurement-first validation and release gates

1. **Establish a baseline before changes.** Use representative 10,000-row data, worst-case names/translations, missing prices, image variants, and the supported permission matrix. Record environment and repeat runs.
2. **Measure core tasks:** initial usable table, filter input-to-results latency, long tasks, React render/commit time, mounted-row count, memory trend, image bytes, and layout shifts.
3. **Exercise write correctness:** rapid edits, overlapping/out-of-order responses, product switching, drawer dismissal, navigation, reconnect, every listed failure, and mixed batch outcomes.
4. **Check interaction access:** keyboard-only operation, screen-reader names/statuses, focus visibility/return, selection semantics, reduced motion, text enlargement, and tablet touch/keyboard behavior.
5. **Set acceptance budgets before implementation.** Proposed starting targets: field INP p75 ≤200ms, CLS ≤0.1, and representative lab filter results p95 ≤200ms on the agreed tablet. Calibrate these with the baseline; lab timing is not field INP.
6. **Correctness gates:** no false “Saved,” stale acknowledgement clearing newer edits, silent draft loss, unauthorized mutation, or duplicate successful batch application. Every tested failure has a recoverable, understandable outcome.
7. **Layout/accessibility gates:** no unreachable actions or page-level horizontal overflow at supported sizes; intentional table scrolling is acceptable. All core tasks work by keyboard, with visible focus and meaningful names.
8. **Performance gates:** mounted rows remain bounded if windowing is introduced; repeated filtering/open-close cycles show no unexplained memory growth; no agreed critical-task regression beyond a predefined tolerance.
9. **Stage independently:** persistence/recovery, accessibility/layout, rendering/filtering, then polish. Compare before/after under the same conditions and recheck invariants after each stage.
10. **Rollback:** halt rollout for correctness, permission, focus, selection, or scroll-restoration regressions, or a breached performance budget. Disable the offending optimization independently; do not roll back safety fixes into silent failure.
11. **Final acceptance:** review representative desktop/tablet states against the existing design system, confirm recovery tests and budgets, and document remaining risks with owners. Do not substitute visual polish for these gates.
