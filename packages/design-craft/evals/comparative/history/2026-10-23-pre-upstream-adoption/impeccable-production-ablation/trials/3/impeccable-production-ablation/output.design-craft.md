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
