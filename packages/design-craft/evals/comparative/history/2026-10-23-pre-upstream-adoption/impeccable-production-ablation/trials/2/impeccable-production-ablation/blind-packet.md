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

**Sequence:** audit and baseline → harden correctness, recovery, accessibility, and tablet behavior → optimize measured bottlenecks → polish within the existing design system → regression validation. Measure performance before changing it; do not defer task-blocking accessibility to polish.

**Verdict:** Hold release for save/recovery and core interaction hardening; preserve the inventory workflow and visual system rather than redesigning them.

This is a read-only assessment of the supplied excerpts and notes. No execution, detector, browser, build, profiler, accessibility-tree, network-throttle, or device testing occurred. “Evidence” below means supplied source facts; “hypothesis” means impact requiring verification. There is insufficient evidence for a numerical health score or overall WCAG compliance determination.

## 2. Prioritized findings

### P0 — Release-blocking correctness

**1. Save failures have no reliable user-visible outcome.**
- **Evidence:** `saveProduct` catches and discards errors, then clears `saving`; no failure/retry states are represented.
- **Impact:** A failed operation becomes indistinguishable from an idle operation at this boundary. Staff cannot reliably know whether edits persisted.
- **Hypothesis:** A false “Saved” message or actual draft loss depends on drawer/status implementation; neither is established.
- **Fix:** Model dirty, saving, saved, and failed states explicitly. Report success only for an acknowledged revision; preserve failed drafts and provide actionable retry.

### P1 — Major production risks

**2. Pending saves and drawer dismissal are not coordinated.**
- **Evidence:** A single Boolean represents saving; Escape closes the drawer during a pending save.
- **Hypothesis:** If saves overlap, the first completion can clear `saving` while another remains pending. Out-of-order writes or discarded drafts depend on request and drawer behavior.
- **Fix:** Track product/revision-specific requests, serialize or coalesce autosaves, and ignore stale responses. Make all dismissal paths follow one draft-preservation policy.

**3. Drawer interaction is incomplete.**
- **Evidence:** No focus trap or background interaction restriction; save/close are icon-only; `.icon-button` removes outlines.
- **Hypothesis:** Missing accessible names or all visible focus styling cannot be inferred from icons and `outline: none` alone; alternatives are unspecified.
- **Fix:** Establish modal versus nonmodal behavior, accessible names, visible focus, appropriate initial focus, and focus restoration. For a modal drawer, contain focus and make the background inert.

**4. Operational states are missing.**
- **Evidence:** Blank initial/filter loading; no empty, auth, conflict, rate-limit, server, timeout, offline, retry, or partial-batch states.
- **Impact:** Staff cannot distinguish waiting, no matches, failed requests, or incomplete work.
- **Fix:** Use distinct states with retained context and recovery actions; see the failure matrix below.

**5. Rendering and filtering scale without bounds.**
- **Evidence:** All 10,000 rows mount; filtering recalculates synchronously on every keystroke.
- **Hypothesis:** Input lag, long tasks, costly commits, and excessive memory are likely, but no timings establish their magnitude.
- **Fix:** Measure filter computation separately from rendering; bound mounted rows and remove unnecessary work while preserving bulk selection and keyboard behavior.

**6. Tablet layout is constrained by desktop dimensions.**
- **Evidence:** `.page { min-width: 1180px; }`; fixed 520px drawer; fixed grid columns; no tablet behavior described.
- **Impact:** The supplied page rule cannot shrink below 1180px.
- **Hypothesis:** Exact clipping, obscured controls, and scroll behavior depend on the containing layout and viewport.
- **Fix:** Let the page shrink; contain necessary horizontal scrolling within the table; bound drawer width and height to the viewport.

**7. Bulk-selection and permission semantics require verification.**
- **Evidence:** Bulk selection exists, but permission-specific affordances and partial-failure states are unspecified.
- **Hypothesis:** Hidden selections, unauthorized actions, or ambiguous “select all” scope are risks—not demonstrated bugs.
- **Fix:** Explicitly distinguish selected visible rows from all matching rows, keep selection keyed by IDs, and revalidate permission and eligibility server-side.

### P2 — Resilience and accessibility refinements

**8. Hostile content and image loading lack defined handling.**
- **Evidence:** Names span 1–200 characters and are ellipsized; prices may be absent; labels can expand 60%; images may be absent or 8MB; dimensions are not reserved.
- **Hypothesis:** Lost identification, label clipping, layout shifts, and memory pressure depend on actual content and rendering.
- **Fix:** Provide accessible full-name disclosure, explicit missing-value treatment, flexible labels, stable image boxes, fallbacks, and upload validation.

**9. Motion and pointer affordances need tightening.**
- **Evidence:** Rows/drawer use `transition: all 300ms ease-in`; icon buttons are 28×28px; reduced-motion behavior is unspecified.
- **Hypothesis:** Layout animation or dropped frames occurs only if costly properties change. Effective target area and spacing need inspection.
- **Fix:** Transition only intentional properties, preserve immediate interaction feedback, supply reduced-motion alternatives, and enlarge touch hit areas without changing icon styling.

### P3 — Final polish

**10. Finish consistency after functional fixes.**
- **Evidence:** The supplied styles establish dimensions and timing, but not enough visual detail to prove alignment or token inconsistencies.
- **Verification candidates:** Existing-system spacing, numeric alignment, status wording, truncation affordances, and loading-to-content continuity.
- **Fix:** Apply only demonstrated corrections; do not invent visual defects or replace the design language.

## 3. Concrete hardening plan

### Save, recovery, and failures

Use explicit fetch, edit/save, upload, and batch states rather than one page-wide Boolean. Keep the last acknowledged revision distinct from the current draft.

| Situation | Required behavior |
|---|---|
| Initial loading | Stable table shell and loading status; never imply zero results. |
| Filter loading | Keep prior results if appropriate, mark them as updating, and prevent stale responses replacing newer results. |
| No inventory / no matches | Distinct explanations; offer permitted creation or clear-filters actions respectively. |
| 401 | Request reauthentication; retain drafts securely and restore context afterward. |
| 403 | Explain permission loss; preserve work where allowed, remove invalid actions, and avoid futile retries. |
| 409 | Preserve both local draft and latest server version; offer review/reapply rather than blind overwrite. |
| 429 | Respect `Retry-After`, bound retries, and show when another attempt is available. |
| 500 / timeout | Keep edits; offer retry. Treat timeout as an unknown write outcome, not proof of failure. |
| Offline | Show “Not saved—offline”; do not promise background delivery without a durable queue. |
| Partial batch failure | Report succeeded/failed/skipped counts and row-level reasons; retry only eligible failures. |

- Use server-supported version checks and idempotency where available; otherwise reconcile uncertain writes before retrying. Client-side cancellation does not prove a server write stopped.
- On close, Escape, backdrop click, and navigation, preserve the draft or offer a clear wait/discard/continue-editing choice. Do not trap users indefinitely behind a hung request.
- A response must not mark newer edits as saved. Keep failed values until explicit discard or successful acknowledgement.
- Scope any persisted drafts to user/product, consider sensitive inventory data, and prevent cross-account restoration.
- Define how selection survives filters and refreshes; show its scope and count before bulk mutation.

### Hostile data and uploads

- Keep compact table rows, but expose full product names through keyboard/touch-accessible detail or disclosure—not hover-only `title`.
- Use `min-width: 0` and flexible grid tracks; wrap long or unbroken names in the drawer. Render names as text, not injected HTML.
- Render missing prices as “Not set” or the established equivalent, never zero. Format real prices with locale/currency rules.
- Allow translated labels and validation messages to wrap; test 60% expansion without clipping actions.
- Reserve thumbnail space with dimensions/aspect ratio; provide absent/broken-image fallbacks. Use decorative alt text only when adjacent content already conveys the image’s meaning.
- Validate upload size, type, and decodeability client-side and enforce limits server-side. State the actual limit before selection; do not arbitrarily reject 8MB if supported.
- Track upload progress, cancellation, failure, and retry independently; do not mark an image saved before upload and attachment succeed.
- Use suitably sized thumbnails and offscreen lazy loading; release temporary object URLs. Avoid decoding full upload originals for every table row.

### Responsive layout and accessibility

- Remove the page-wide minimum width; preserve required column widths within a labeled, keyboard-scrollable table region. Do not hide essential editing fields just to fit.
- Bound the drawer to available width, use a dynamic viewport-height strategy with fallback, and give its content internal scrolling. Keep actions reachable with tablet keyboards open.
- Preserve filters, bulk controls, and save status at supported tablet sizes and zoom; wrap controls rather than force page-wide overflow.
- Use native table semantics where feasible. Adopt ARIA grid behavior only if the existing spreadsheet-like interaction requires it and its keyboard contract is implemented.
- Give row checkboxes product-specific names, expose mixed selection state, and label every icon action.
- For a modal drawer: use dialog semantics, an accessible title, initial focus, focus containment, inert background, and focus return. If its opener is unmounted, choose a stable logical fallback.
- Restore `:focus-visible` treatment using existing tokens; ensure sticky elements do not cover focused controls.
- Announce loading, result counts, save outcomes, and errors without announcing every keystroke. Associate field errors with inputs.
- Prefer roughly 44px touch hit areas where feasible. A 28px target is not automatically a WCAG 2.2 AA size failure; its minimum is generally 24px, subject to exceptions and spacing.
- Reduce drawer movement under reduced-motion preferences while preserving state feedback.

### Performance without changing the workflow

- First compare filter computation, React render/commit cost, DOM count, image decode, and memory.
- Use an existing table/windowing capability if available; otherwise choose a bounded rendering approach compatible with the current stack. No new dependency is assumed.
- Preserve ID-based selection across unmounted rows, row position/count semantics, focus continuity, and access to all matching results.
- Separate typed input from expensive result updates. Debouncing reduces frequency; deferred rendering does not itself make a heavy synchronous filter cheap.
- Cache or index filtering only when measurements justify it; consider existing server filtering for expensive queries, with stale-response protection.
- Stabilize row props and isolate unrelated updates; add memoization only where profiling shows benefit.
- Replace `transition: all` with explicit properties; avoid blanket `will-change`.

## 4. Static signals: decisive versus contextual

**Decisive about the supplied implementation:** errors are swallowed; save state is only Boolean; 10,000 rows mount; filtering runs per keystroke; the page has an 1180px minimum; transitions target all properties; image space is unreserved; the listed operational states and drawer protections are absent.

**Not decisive about runtime impact or compliance:**
- `outline: none` proves outline removal, not absence of a replacement focus ring.
- Icon-only buttons need accessible names; they do not prove names are absent.
- A 28px button is a touch-usability concern, not an automatic AA failure.
- Fixed column widths and horizontal table scrolling can be appropriate for dense inventory data; page-wide overflow is a separate issue.
- `transition: all` is an overbroad rule, not evidence that layout is actually animating.
- Unreserved images create shift risk, but measured CLS depends on when and how they appear.
- Ellipsis is acceptable if full values remain discoverable; it is not inherently inaccessible.
- No evidence supports claims about contrast, bundle size, dark mode, backend authorization, or actual data loss.

Preserve useful foundations: stable `row.id` keys, existing component boundaries, compact scanning, and the current design system.

## 5. Measurement-first validation and release gates

**Before implementation**
- Agree on supported desktop/tablet viewports, browsers, input modes, and representative hardware.
- Capture baseline input-to-result latency, filter duration, long tasks, React commit time, mounted rows, memory, image bytes/decode cost, layout shifts, and save outcomes.
- Create fixtures for 10,000 rows, long/unbroken names, missing prices/images, 8MB uploads, expanded translations, and mixed permissions.

**Acceptance tests**
- Exercise every failure in the matrix, rapid edits, overlapping responses, close/reopen, navigation, reconnect, and ambiguous timeout retries.
- Require no silently discarded drafts, false “Saved” states, stale-result replacement, or duplicate mutations in those scenarios.
- Test select-all scope, filter changes, row unmounting, partial batches, and retry-only-failed behavior.
- Verify keyboard-only operation and screen-reader announcements manually; automated checks supplement rather than replace these tests.
- Check tablet orientations, touch, on-screen keyboard, 200% zoom, reduced motion, full-name discovery, and reachable drawer actions.
- Set budgets before optimization. Proposed starting gates: p95 typing feedback ≤100ms, p95 filter-to-results ≤300ms, and no interaction long task over 200ms on agreed reference hardware; calibrate against the baseline before adopting them.
- Require bounded mounted rows, stable memory over repeated drawer/upload cycles, and no thumbnail-induced layout shifts in controlled fixtures.

**Rollout and rollback**
- Ship correctness, layout/accessibility, and rendering changes in separable increments using existing rollout controls.
- Block release on any P0 or unresolved major task-access failure; document ownership and timing for accepted lower-priority risks.
- Roll back the affected increment on lost edits, incorrect bulk scope, duplicate writes, focus/navigation regressions, or an agreed material performance regression.
- Keep error reporting and recovery protections when reverting optimization. Recheck the same fixtures and budgets before final polish sign-off.


## Output B

## 1. Sequence and verdict

**Sequence:** baseline and audit → correctness/hardening → measured optimization → visual polish → final regression validation. Measure before choosing performance techniques; do not polish over broken recovery paths.

**Verdict:** Preserve the existing editor, but block production sign-off on silent save failures; harden recovery, accessibility, and tablet behavior before accepting performance or polish improvements.

**Scope:** Static assessment of the supplied description only. No files edited; no detector, browser, build, profiler, accessibility-tree, network-throttle, or device execution occurred. Runtime outcomes below remain unverified.

## 2. Prioritized findings and concrete repairs

P0 = release-blocking correctness; P1 = high-priority hardening; P2 = scheduled resilience work; P3 = final polish. “Evidence” means supplied source facts, not observed runtime behavior.

### F1 — P0: Failed saves have no observable outcome
- **Evidence:** `catch {}` discards failures; `saving` returns to `false` after success or failure. No failure/retry state is represented.
- **Runtime unknown:** Whether the drawer interprets completion as success or discards drafts; actual lost edits are not established.
- **Repair:** Return a typed save result or propagate failure. Track per-product draft revision and `dirty / saving / saved / failed / conflict` state; show “Saved” only for an acknowledged revision. Retain failed drafts and expose Retry with an actionable error.
- **Repair:** Serialize writes per product or use version-aware concurrency. A shared boolean cannot accurately represent overlapping saves; use request ownership so an old completion cannot clear a newer pending state.
- **Acceptance:** Inject rejected and out-of-order requests, edit again during save, switch products, and reopen the drawer. No false success, stale overwrite, or lost draft; retry saves the intended revision exactly once.

### F2 — P1: Loading, failures, permissions, and batch recovery are missing
- **Evidence:** Blank initial/filter loading; no empty, 401/403, 409, 429, 500, timeout, offline, retry, or partial-batch states. Permission-specific affordances are undescribed.
- **Runtime unknown:** API error payloads, idempotency support, server authorization, and current selection semantics.
- **Repair — loading/empty:** Show dimensionally stable loading rows and an accessible loading status. During filtering retain the last result with an “Updating” indicator, without implying it matches the new filter. Empty results show the active criteria and Clear filters; distinguish an empty inventory.
- **Repair — access:** For 401, offer reauthentication and preserve authorized draft context under the session policy. For 403, explain access restrictions and provide a safe exit; hide or disable unauthorized mutations consistently. Server authorization remains mandatory.
- **Repair — conflict:** For 409, retain local edits and show current server values for review/reapplication; never silently overwrite or auto-retry a conflict.
- **Repair — availability:** For 429, show retry timing and honor `Retry-After`. For 500, show a specific failure and Retry. For timeout, show “Save status unknown” and reconcile before repeating a mutation. Offline shows “Not saved—offline,” preserves the draft, and offers retry after reconnection; do not promise durable queuing without implementing it.
- **Repair — bulk:** Store selection by stable IDs, explicitly distinguish visible versus all-matching selection, and preserve that scope across filters. Show succeeded/failed/skipped counts and row-level reasons; retry failed items only, with duplicate-write protection.
- **Acceptance:** Fault-inject every branch; verify its rendered message, available action, retained filters/draft/selection, and eventual recovery. Never report full batch success for partial completion.

### F3 — P1: Drawer interaction and control accessibility are unsafe
- **Evidence:** No focus trap or background interaction isolation; Escape closes during save. Save/close are icon-only; `.icon-button` is 28×28px with `outline: none`. Keyboard and screen-reader behavior are undescribed.
- **Runtime unknown:** Whether labels, replacement focus styles, or larger effective hit areas exist elsewhere; whether dismissal actually loses work.
- **Repair:** Using the existing dialog primitive, give the modal drawer a name, appropriate dialog semantics, initial focus, contained Tab navigation, inert background, and focus restoration to a valid trigger.
- **Repair:** Make Escape and close follow the same explicit pending/dirty policy. Closing need not be prohibited if save ownership and drafts survive dismissal; otherwise explain the pending state and prevent destructive dismissal. A canceled client request does not prove the server canceled its write.
- **Repair:** Provide accessible “Save product” and “Close editor” names, visible focus indicators, labeled selection controls, and programmatic error associations. Announce autosave transitions politely without announcing every keystroke.
- **Repair:** Expand effective targets from 28×28px to at least **44×44 CSS px** as a provisional tablet comfort target, without overlapping adjacent controls; icons can remain visually compact.
- **Repair:** Preserve semantic table headers/cells and checkbox state. Do not add grid roles unless the full grid keyboard interaction is implemented.
- **Acceptance:** Complete filtering, selection, edit, upload, save failure/retry, and dismissal using keyboard and screen reader; no background activation, lost focus, unnamed action, or inaccessible status.

### F4 — P1: Fixed geometry threatens tablet task completion
- **Evidence:** `.page { min-width: 1180px }`; columns are `64px 280px 1fr 120px 96px`; drawer is fixed at 520px wide and `100vh`.
- **Runtime unknown:** Exact overflow, viewport clipping, virtual-keyboard behavior, and action reachability on supported tablets.
- **Repair:** Remove the page-wide minimum and allow filter controls to wrap. Use shrinkable grid tracks such as `minmax(0, 1fr)` and `min-width: 0` where appropriate.
- **Repair:** Preserve essential table columns and density. If a table minimum remains necessary, place horizontal scrolling inside a labeled, keyboard-accessible data region—not on the entire page.
- **Repair:** Cap drawer width to the viewport while retaining 520px on roomy screens; use dynamic viewport height with fallback, internal vertical scrolling, and reachable header/footer actions. Test keyboard occlusion rather than assuming viewport units solve it.
- **Acceptance:** At agreed desktop/tablet sizes, portrait/landscape, and 200% zoom, filters and actions remain reachable, no unintended page-wide overflow occurs, and necessary table overflow stays local.

### F5 — P1: Render and filter work scale directly with the full dataset
- **Evidence:** All 10,000 rows mount; filtering recalculates synchronously on every keystroke. The supplied render path has no row bound.
- **Runtime unknown:** Input latency, render/commit cost, row complexity, memory use, and whether staff encounter severe stalls. Static scale alone does **not** establish P0.
- **Repair:** Require bounded mounted rows. After baseline measurement, choose the smallest compatible existing approach: windowing if continuous scrolling must remain, or existing pagination if consistent with the workflow. Preserve selection, focus, row identity, and accessible navigation.
- **Repair:** Separate immediate input feedback from expensive result computation. Profile before choosing cached normalization, deferred updates, debounce, or worker execution; scheduling does not remove computational cost. Ignore stale filter results.
- **Acceptance:** Meet the provisional gates below on the same 10,000-row fixtures and target hardware without changing selection scope or dropping keyboard access.

### F6 — P2: Hostile text, missing values, and images lack explicit contracts
- **Evidence:** Names span 1–200 characters; ellipsis hides overflow. Prices may be missing, translations expand 60%, images may be absent or 8MB, and image dimensions are not reserved.
- **Runtime unknown:** Actual clipping, assistive access to full names, image transfer sizes, layout shift, and upload limits.
- **Repair:** Keep compact table truncation but expose full names through the existing detail flow and accessible keyboard/touch disclosure where needed—not hover-only. Allow long/unbroken names to wrap in the drawer.
- **Repair:** Distinguish missing price from zero using localized “Not set” copy; use locale-aware currency formatting. Allow label wrapping and test supported scripts and directionality.
- **Repair:** Reserve image width/height or aspect ratio; use a stable missing/broken-image placeholder and appropriate alt text. Serve size-appropriate thumbnails and lazily load offscreen images where compatible.
- **Repair:** Validate upload type, byte size, and decoded dimensions on client and server. If 8MB is allowed, show progress and recoverable failure; if disallowed, explain the limit before upload. Keep the previous image until replacement commits, support retry/cancel, and release preview object URLs.
- **Acceptance:** Exercise every specified data extreme, corrupt images, rejected uploads, and interrupted replacements; no silent coercion, unreachable content, unexpected layout movement, or lost previous image.

### F7 — P2: Broad transitions and missing reduced-motion behavior
- **Evidence:** Rows and drawer use `transition: all 300ms ease-in`; reduced-motion behavior is undescribed.
- **Runtime unknown:** Which properties change, whether layout is animated, and whether global reduced-motion rules compensate.
- **Repair:** Transition only intended properties using existing motion tokens; prefer transform/opacity where suitable and remove unnecessary row animation. Under reduced motion, remove nonessential movement while preserving status feedback.
- **Acceptance:** Inspect actual animated properties and exercise reduced motion; focus and save feedback must not depend on animation completion.

### F8 — P3: Final visual consistency needs a bounded polish pass
- **Evidence:** No rendered view or complete token/component context is supplied; a spacing, contrast, or aesthetic defect cannot be established.
- **Runtime unknown:** Alignment, density, state consistency, contrast, and truncation quality.
- **Repair:** After F1–F7, compare touched controls, statuses, and drawer states with existing equivalents; refine only demonstrated inconsistencies. Preserve typography, tokens, information architecture, and staff workflow.
- **Acceptance:** Before/after visual review approves the same states and viewports; no unrelated visual changes or new dependencies.

## 3. Static signals: decisive versus contextual

- **Decisive correctness evidence:** F1’s discarded error and indistinguishable completion state establish a missing failure contract. This justifies a release gate without claiming observed data loss.
- **Decisive coverage evidence:** Explicitly absent states in F2 and missing focus/background containment in F3 require repairs. Undescribed labels or keyboard behavior require investigation, not a claim that every component lacks them.
- **Decisive architecture risk, not measured latency:** F5 proves dataset-proportional mounting and synchronous filtering. Keep it P1 unless target-runtime evidence establishes release-blocking task failure.
- **Context-dependent CSS signals:** `outline: none` may have a valid replacement; 28px visual geometry may have a larger hit target; fixed widths may be intentional inside contained scrolling. Verify computed behavior and ownership before declaring a specific violation.
- **Context-dependent motion/data signals:** `transition: all` is a broad-risk declaration, not proof of jank. Ellipsis is reasonable in dense tables if full content remains available. Missing dimensions create shift risk, not a measured CLS result.
- **Not grounds for redesign:** Font count, stylistic preferences, or generic scanner taste rules cannot override the existing design system. Static checks cannot establish contrast, perceived smoothness, task success, or overall visual quality.

## 4. Measurement-first validation and release plan

**All steps below are proposed, not executed.**

1. **Establish baseline and ownership:** Confirm supported browsers/tablets, lowest supported hardware, API/version/idempotency contracts, existing primitives, selection semantics, and performance budgets. Record the current route and its unchanged visual conventions.
2. **Create controlled scenarios:** Use 0, 1, typical, and 10,000 rows; all F6 extremes; every F2 response; rapid edits, concurrent products, filter races, dismissal mid-save, upload interruption, and repeated drawer open/close cycles.
3. **Measure before performance changes:** Record input-to-paint and input-to-current-results p95, long-task maximum, render/commit time, mounted rows/DOM count, CLS, image transfer/decoding, and retained/peak memory. Compare identical production-mode configurations, fixtures, hardware, and repeated runs.
4. **Validate correctness first:** Use existing type/lint/build and unit/integration checks. Assert request ownership, acknowledged revision tracking, draft survival, permissions, idempotent retry, conflict handling, and partial-batch accounting.
5. **Validate the surface:** Plan desktop plus actual supported tablets, portrait/landscape, zoom, keyboard, screen reader, touch, reduced motion, slow/interrupted connections, and supported themes. Capture relevant states and manually review them; screenshots alone do not prove behavior.

**Provisional performance gates—ratify against target hardware before implementation:**

| Metric | Proposed acceptance |
|---|---|
| Input-to-next-paint p95 | ≤100ms during filtering |
| Input-to-current-results p95 | ≤300ms at 10,000 rows, including any debounce |
| Maximum main-thread long task | ≤100ms during filter, scroll, and drawer interactions |
| Mounted product rows | ≤200 with viewport/overscan rationale; never all 10,000 |
| CLS | ≤0.1 during initial load and image completion |
| Memory recovery | Retained heap after 20 edit/upload/filter cycles ≤10% above warmed baseline after collection; no monotonic growth |
| Base-to-head regression | Timing regression ≤10% **and** ≤20ms; peak memory regression ≤10% **and** ≤20MB |

6. **Acceptance:** Resolve F1 and in-scope P1 findings with scenario evidence; explicitly approve any deferred P2 risk. Require accessible task completion, intact drafts/selection, target performance gates, and visual consistency—not merely successful compilation.
7. **Rollout/rollback:** Separate correctness, performance, and polish changes into reversible increments using existing rollout controls. Stop or roll back on false save success, stale writes, lost drafts, incorrect batch scope, accessibility/task regressions, or breached ratified budgets. Revert an optimization that neither improves its target metric nor simplifies the implementation.
8. **Safe fallback:** Do not restore silent failures to regain speed. If a safe save path cannot be maintained, pause affected mutations or use an established safe fallback while retaining recoverable drafts.

**Current disposition:** Audit complete at the static-evidence level; production readiness, visual acceptance, and runtime performance remain unverified.


## Output C

## 1. Sequence and verdict

**Sequence:** audit and establish baselines → harden correctness, recovery, and accessibility → optimize measured bottlenecks → polish within the existing design system → validate and release incrementally. Address overlapping fixes together; cosmetic polish must not conceal broken states.

**Verdict:** The supplied source establishes production-blocking save/recovery gaps and significant accessibility and scale risks; preserve the workflow and components, but harden them before visual polish.

**Scope:** Read-only review of the supplied description and snippets. No detector, build, browser, profiler, accessibility-tree, network, or device run was performed. Runtime effects below are hypotheses unless directly established by the source.

## 2. Prioritized findings

Priority meaning: **P0** release blocker for data integrity or security; **P1** essential workflow/accessibility hardening; **P2** robustness and performance improvements; **P3** finishing polish.

| Priority | Finding and source evidence | Runtime hypothesis / uncertainty |
|---|---|---|
| **P0** | **Failed saves are indistinguishable from completed saves.** `catch {}` discards the error, then `saving` becomes false; no failure or recovery state is represented. | The UI may imply success or allow users to discard unsaved edits. Actual data loss and success messaging are not demonstrated. Block release until failure preserves edits and is explicit. |
| **P1 → P0 if reproduced** | **Save concurrency is not modeled.** A single boolean surrounds each `api.save(product)` call. | If saves overlap, one completion can clear `saving` while another is pending; responses may arrive out of order. Escalate to P0 if an older edit can overwrite a newer one. |
| **P1** | **Drawer interaction is incomplete.** No focus trap or background-interaction containment; Escape closes during a pending save; save/close are icon-only. | If this is a modal drawer, users can escape its interaction context. Closing may lose draft/status visibility. Icon-only controls are not inherently inaccessible; accessible names are unverified. |
| **P1** | **Loading, empty, failure, and partial-success states are missing.** Loading leaves the table body blank; listed HTTP/network outcomes have no representation. | Users may confuse loading with zero inventory, repeat mutations, or miss batch failures. |
| **P1** | **Rendering and filtering scale poorly by construction.** All 10,000 rows mount; filtering recalculates synchronously per keystroke. | Input delay, long tasks, memory pressure, and slow drawer interaction are likely, but magnitude requires measurement. |
| **P1** | **Tablet layout has a hard constraint.** `.page { min-width: 1180px; }`; drawer is fixed at `520px` with `100vh`. | Narrower viewports will need overflow handling. Unusable controls, drawer obstruction, or mobile-keyboard clipping require rendered checks. |
| **P1** | **Keyboard focus and permissions are unspecified.** `.icon-button` removes outlines; no focus-visible or permission affordances are described. | Focus may be invisible unless another rule restores it. Missing frontend permission cues are not proof of missing server authorization; verified unauthorized mutation would be P0. |
| **P2** | **Hostile data is insufficiently accommodated.** Names vary from 1–200 characters, prices can be missing, labels expand 60%, and images may be absent or 8MB. Names are ellipsized. | Important identifiers may become indistinguishable; labels may collide; large images may dominate loading. Truncation itself is not a defect if full values remain accessible. |
| **P2** | **Image layout stability is unprotected.** Image dimensions are not reserved. | Layout shifts depend on surrounding sizing and load timing; the snippet does not establish a measured shift score. |
| **P2** | **Transitions are broad and motion preferences unspecified.** Rows and drawer use `transition: all 300ms ease-in`. | Layout/paint properties may animate unnecessarily; actual cost depends on which properties change. Reduced-motion behavior needs verification. |
| **P3** | **Status and visual consistency need a final pass.** Multiple workflow states must be added to existing components. | Spacing, contrast, hierarchy, and status readability cannot be judged conclusively from these snippets. |

## 3. Concrete hardening and polish

### Save correctness, failures, and recovery
- Replace the boolean-only model with explicit dirty, queued, saving, saved, and failed states tied to the product and draft revision.
- Serialize/coalesce autosaves per product, or use revision-aware requests and responses. Only acknowledge the revision actually saved; retain edits made during an in-flight request.
- Use server-supported version checks for conflicts. An aborted client request does not prove the server canceled a mutation.
- Preserve the draft and show a persistent, actionable save error. Show “Saved” only after acknowledgment; distinguish it from “Saving” and “Unsaved changes.”
- Keep save status visible if drawer closure is allowed. Otherwise guard close, Escape, and navigation while edits are at risk, with a clear explanation and safe exit path.
- Avoid a permanent keyboard trap: let users return to editing or explicitly discard when safe. Do not silently treat closing as cancellation.
- Retry only eligible failures, with bounded backoff and jitter; respect `Retry-After`. Do not blindly replay non-idempotent mutations.
- Handle outcomes explicitly:
  - **401:** reauthentication flow that preserves the draft without exposing it across users.
  - **403:** explain denied action, retain recoverable work where appropriate, refresh permissions; enforce authorization server-side.
  - **409:** retain local edits and offer comparison/reload/merge appropriate to the existing workflow; never silently overwrite.
  - **429:** communicate the wait and defer retries.
  - **500 / timeout / offline:** keep edits, expose retry, and distinguish failure from an unknown commit outcome.
  - **Partial batch failure:** report succeeded/failed counts and row-level reasons; retry only eligible failed rows without repeating successful work.
- Define bulk-selection scope: current page/window, filtered result set, or explicit IDs. Filtering and virtualization must not silently change it.
- Keep selected IDs and drafts outside mounted row instances; validate stale/deleted/ineligible records at mutation time.

### Loading, hostile data, and uploads
- Use distinct initial loading, filter updating, empty inventory, no matches, and load-error states.
- For filter refreshes, preserve prior results when appropriate, mark them as updating, and prevent stale result responses from replacing newer ones.
- Render missing prices as an explicit unknown/not-set value, not zero; preserve legitimate zero prices and use locale-aware formatting.
- Keep visual name truncation where needed, but provide the full value through keyboard/touch-accessible detail or expansion—not hover-only tooltips.
- Test long unbroken names, punctuation, non-Latin text, and 60% label expansion. Allow wrapping and flexible control sizing without changing hierarchy.
- Reserve image aspect ratio/dimensions; provide consistent absent/broken-image fallbacks and context-appropriate alt text.
- Validate file type, size, and decoded dimensions on client and server. Explain limits before upload; an 8MB file is not automatically invalid.
- Show upload progress, cancellation/retry, and failure separately from product-save status; save image references only when upload completion is valid.
- Use existing thumbnail/delivery capabilities, responsive sources, and below-viewport lazy loading. Avoid fetching full originals for tiny row previews.

### Responsive layout and accessibility
- Remove the page-wide minimum-width dependency. Keep essential controls responsive and isolate necessary horizontal scrolling to the table region.
- Preserve row/header alignment and access to every field. Do not hide operationally important columns merely to make the page fit.
- Constrain drawer width to available space, retain the desktop width where it fits, and use viewport-aware height with internal scrolling and reachable actions.
- Verify tablet portrait/landscape, zoom, touch, and software-keyboard behavior; do not assume a desktop breakpoint solves them.
- Decide whether the drawer is modal. If modal: supply a labeled dialog, contain focus, make background content inert, set sensible initial focus, and restore focus to the opener or a logical fallback.
- If nonmodal: keep background interaction available intentionally and provide a clear keyboard route between the drawer and inventory; do not claim modal semantics.
- Give save/close explicit accessible names and preferably existing labeled-button variants where ambiguity matters.
- Restore visible keyboard focus. Increase touch hit areas using existing spacing tokens; a 28px target exceeds the basic 24px size threshold but may still be poor for frequent tablet use.
- Use appropriate table semantics and labeled selection controls; communicate checked, indeterminate, disabled, sort, and busy states.
- Adopt grid keyboard behavior only if implementing the full grid interaction model. Avoid creating thousands of unnecessary tab stops.
- Announce save/error changes without announcing every keystroke. Associate validation errors with fields and avoid color-only status.
- Replace `transition: all` with the properties actually needed; favor transform/opacity for drawer movement and honor reduced motion.

### Performance without a redesign
- Profile representative 10,000-row data first, then use existing infrastructure for row virtualization or established pagination.
- Preserve selection, focused-row behavior, row identity, scroll restoration, and screen-reader context across unmounted rows.
- Separate input responsiveness from expensive filtering; defer/debounce computation where appropriate and avoid recomputing unchanged normalized data.
- Consider a worker or server-side filtering only if measurements and the current architecture justify it—not as an automatic dependency addition.
- Isolate drawer/save state from unnecessary table rerenders. Apply memoization only where traces show useful work avoidance.
- Keep image loading and row rendering fixes independently releasable so regressions can be isolated.

## 4. Static signals: decisive versus contextual

**Decisive from supplied source**
- Errors are swallowed; listed recovery states are absent.
- The shown render path maps every row without windowing.
- The supplied loading state is blank.
- Fixed minimum/page/drawer dimensions and unrestricted transitions exist.
- Modal safeguards, image dimension reservation, and several accessibility behaviors are absent or unspecified as noted.

**Require project or runtime context**
- `outline: none` proves outline removal, not absence of every possible focus indicator.
- Icon-only controls require accessible names; icons alone do not establish whether names exist.
- `28px` does not by itself establish a minimum-target-size violation; spacing, exceptions, and usability matter.
- `transition: all` is a risk signal, not proof of layout thrashing or a frame-rate failure.
- Ten thousand rendered rows establish workload, not a specific latency or memory figure.
- Ellipsis, fixed columns, `100vh`, and horizontal scrolling require viewport/content checks before declaring a particular failure.
- Missing permission descriptions do not prove an authorization vulnerability.
- Contrast, DOM semantics, announcements, actual request ordering, and draft persistence cannot be inferred from the excerpts.

Use static findings to target investigation, not to manufacture scores or runtime results.

## 5. Measurement-first validation and release gates

1. **Record a reproducible baseline:** current production-equivalent configuration, representative and worst-case data, supported desktop/tablet viewports, and agreed device/network profiles.
2. **Measure the critical journeys:** initial inventory display, rapid filtering, bulk selection, opening/editing/closing the drawer, image upload, save, and recovery after interruption.
3. **Capture:** input-to-result latency, interaction latency, long tasks, render/commit time, mounted-row count, peak memory, image bytes, layout shifts, and save acknowledgment time.
4. **Set budgets before implementation:** define per-journey limits with product/engineering. Candidate guardrails include p75 interaction latency ≤200ms and CLS ≤0.1; these are targets, not observed results, and do not replace workflow-specific limits.
5. **Exercise deterministic failures:** every listed HTTP state, slow/out-of-order saves, timeout after server commit, offline/reconnect, expired sessions, denied actions, upload failure, and mixed batch outcomes.
6. **Validate data invariants:** no stale overwrite; no false “Saved”; no lost draft on recoverable failure; retry cannot duplicate successful work; selections remain correct through filtering/windowing.
7. **Validate access manually and automatically:** keyboard-only journeys, focus visibility/order/restoration, labels and announcements with supported screen readers, reduced motion, zoom, and touch targets.
8. **Run a content/layout matrix:** 1- and 200-character names, unbroken strings, missing/zero prices, expanded translations, absent/large images, and narrow tablet orientations.
9. **Compare equivalent runs:** use repeated measurements and distributions, not one favorable sample. Investigate regressions in correctness, accessibility, latency, memory, and request volume.

**Acceptance:** all P0 issues resolved; essential P1 journeys pass; agreed budgets are met without losing workflow or design-system consistency. Document any remaining lower-priority limitations with owners.

**Release:** stage changes in small, reversible increments, with separate controls for rendering/filtering optimizations. Monitor save failures, conflicts, retries, abandoned edits, and interaction performance without logging sensitive product contents.

**Rollback:** halt or revert an increment on stale writes, draft loss, duplicate mutations, selection corruption, blocked keyboard workflows, or agreed performance/error-budget breaches. Preserve queued edits during rollback; disable an unsafe mutation path rather than reverting to known silent failure.
