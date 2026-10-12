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
