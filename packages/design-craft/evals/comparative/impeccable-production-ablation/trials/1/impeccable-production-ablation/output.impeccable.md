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
