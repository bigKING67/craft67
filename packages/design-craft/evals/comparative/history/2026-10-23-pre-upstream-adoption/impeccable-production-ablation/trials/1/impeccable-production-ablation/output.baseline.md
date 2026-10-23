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
