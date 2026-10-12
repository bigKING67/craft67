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
