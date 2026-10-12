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
