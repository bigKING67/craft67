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
