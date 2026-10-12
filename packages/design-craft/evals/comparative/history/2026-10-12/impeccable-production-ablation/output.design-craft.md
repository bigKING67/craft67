## 1. Sequence and verdict

**Sequence:** establish baseline and audit → harden correctness, recovery, accessibility, and responsive behavior → measure and optimize → polish within the existing design system → validate and stage rollout.

**Verdict:** the described surface is not ready for production sign-off: save failures are swallowed, recovery states are absent, and tablet/accessibility risks need hardening before visual polish.

This is a read-only assessment of the supplied snippets and notes. No files were changed; no detector, browser, build, profiler, accessibility-tree inspection, network throttle, or device test was run.

## 2–3. Prioritized findings and concrete repairs

**Priority:** P0 = release blocker; P1 = fix in this hardening cycle; P2 = schedule soon with explicit risk acceptance; P3 = polish backlog. Runtime consequences below remain hypotheses unless directly established by the supplied facts.

### F1 — P0: save failure has no observable recovery contract
- **Source evidence:** `catch {}` discards errors; `saving` returns to `false` after either success or failure. No failure state is represented.
- **Runtime unknown:** whether the drawer interprets resolution as success, dismisses itself, or clears drafts. Silent failure is established here; actual lost edits are not.
- **Repair:** represent dirty, saving, saved, failed, and conflict states explicitly. Show “Saved” only after acknowledgement of the current revision; retain edits on failure and offer a specific recovery action.
- Return an explicit outcome or propagate a typed error; record operational failures without logging product contents or credentials.
- **Acceptance:** reject a save and verify no success indication, no draft loss, an actionable error, and a successful retry of the intended revision.

### F2 — P1: pending saves, dismissal, and bulk updates lack safe ownership
- **Source evidence:** one page-level `saving` boolean; Escape closes the drawer while saving; conflict and partial-batch states are absent.
- **Runtime hypothesis:** if requests overlap, an earlier completion can clear the indicator while a later request is pending; out-of-order writes may overwrite newer edits. Concurrency is not established by this snippet.
- **Repair:** scope mutation state to product/request revision; serialize or coalesce same-product autosaves, and prevent stale responses from updating current UI. Use server version checks where supported.
- Keep drafts and mutation ownership outside the drawer’s mount lifetime. Closing must either safely preserve work and continue saving with visible status, or require an explicit decision; never silently discard it. Aborting a request does not prove the server canceled the write.
- Track bulk selection by stable IDs, not rendered row positions. Make “selected rows” versus “all filtered results” explicit; preserve or explicitly reconcile selection when filters change.
- **Acceptance:** test rapid edits, reversed response order, double activation, drawer close/reopen, route departure, and filter changes. Verify the latest revision and exact selected IDs; retry only failed batch items.

### F3 — P1: operational states are missing
- **Source evidence:** initial/filter loading produces a blank body; empty, authentication, authorization, conflict, rate-limit, server, timeout, offline, retry, and partial-failure states are not represented.
- **Runtime unknown:** API error shape, session recovery, idempotency support, and whether mutation outcomes can be queried.
- **Repair:** implement these states inside existing table/drawer patterns:

| Condition | Render and user action | Context/recovery |
|---|---|---|
| Initial/filter loading | Stable loading rows or progress text; mark results busy. During refiltering, retain prior results with an updating indication. | Preserve filters and selection; do not offer ambiguous bulk actions against stale results. |
| Empty results | Distinguish “No inventory” from “No matches”; offer reset filters where appropriate. | Keep entered filters until explicitly cleared. |
| 401 / 403 | Reauthentication / permission explanation; remove or disable unauthorized actions with a reason. | Preserve authorized draft context securely; recheck permissions after authentication. Server enforcement remains mandatory. |
| 409 | Conflict panel with local and current server values; reload or explicitly reconcile. | Retain local edits; never blindly overwrite. |
| 429 | Rate-limit message and next retry time; honor `Retry-After`. | Preserve work; prevent retry storms. |
| 500 / timeout / offline | Specific error or connection state, with retry/reconnect action. | Keep drafts. For uncertain writes, reconcile server state or use supported idempotency before retrying. |
| Partial batch failure | Success/failure counts and item-level reasons; retry failed items. | Preserve failed selection/drafts; do not resubmit successful items. |

- **Acceptance:** inject each condition and verify its rendered state, permitted action, preserved context, and successful recovery—not merely that an error branch exists.

### F4 — P1: drawer and controls need an accessible interaction contract
- **Source evidence:** no focus or background-interaction containment; Save/Close are icon-only; `.icon-button` is `28px × 28px` with `outline: none`. Labels and keyboard behavior are unspecified.
- **Runtime unknown:** accessible names, replacement focus styling, effective hit areas, table semantics, and whether the drawer is intended to be modal.
- **Repair:** for a modal edit drawer, use the existing dialog pattern: accessible title, initial focus, contained tab order, inert background, and focus return to the opener or a logical surviving row. Coordinate Escape with F2.
- If intentionally nonmodal, do not add modal semantics or a focus trap; instead provide clear keyboard movement between editor and table.
- Provide explicit accessible names for Save, Close, row actions, and checkboxes; retain icon visuals if established. Restore a visible `:focus-visible` indicator.
- Enlarge effective targets to **at least 44 × 44 CSS px provisionally for tablet comfort**, without overlapping targets; the icon itself can remain smaller.
- Preserve semantic table headers and cell associations. Use grid roles only if the corresponding keyboard model is implemented. Announce save/error and selection changes without announcing every keystroke.
- **Acceptance:** complete filtering, selection, editing, saving, and recovery by keyboard and screen reader; verify focus visibility, containment/return, names, and touch target geometry.

### F5 — P1: fixed geometry conflicts with tablet and expanded content
- **Source evidence:** page `min-width: 1180px`; columns `64px 280px 1fr 120px 96px`; drawer width `520px`, height `100vh`; translations may expand by 60%.
- **Runtime hypothesis:** narrower viewports or zoom may cause page-wide scrolling, clipped actions, or an inaccessible drawer footer. Exact breakage depends on surrounding layout and styles.
- **Repair:** remove the page-wide minimum; allow filters and bulk controls to wrap. Keep necessary wide-table overflow within a labeled, keyboard-accessible table scroller.
- Replace rigid content tracks with bounded flexible tracks, including `minmax(0, 1fr)` where appropriate and `min-width: 0` on shrinkable children. Preserve essential columns and workflow rather than switching to an unrelated card layout.
- Cap drawer width at the available viewport (`min(520px, 100%)`), use dynamic viewport height with a fallback, and provide internal scrolling with reachable Save/Close controls. Account for tablet browser chrome and the on-screen keyboard.
- **Acceptance:** supported desktop/tablet widths, portrait/landscape, 200% zoom, and 60%-expanded labels preserve all actions; horizontal overflow is confined to the data region.

### F6 — P2: hostile data and image uploads need explicit handling
- **Source evidence:** names span 1–200 characters and are ellipsized; prices may be missing; images may be absent or 8MB; dimensions are not reserved.
- **Runtime unknown:** full-name disclosure, price formatting, image transformation, upload limits, preview lifetime, and validation.
- **Repair:** retain compact ellipsis where useful, but expose the full name through keyboard/touch-accessible disclosure or the editor—not hover alone. Test unbroken strings, translated labels, and locale-specific number formats.
- Render missing prices as “Not set,” distinct from zero; validate currency and numeric inputs without silent coercion.
- Reserve image dimensions/aspect ratio; use an intentional missing/error placeholder and context-appropriate alternative text.
- Publish upload size/type limits, validate on client and server, and either accept 8MB originals with appropriately sized previews/thumbnails or reject them clearly before upload. Show progress, failure, retry, and cancellation; preserve other edits and retain the previous image until replacement succeeds.
- Release preview object URLs and temporary resources after replacement or teardown.
- **Acceptance:** exercise all stated bounds, missing versus zero prices, broken images, and failed/canceled/retried 8MB uploads; verify layout stability and no lost edits.

### F7 — P1: render/filter work is unbounded relative to the viewport
- **Source evidence:** all 10,000 rows render; filtering recalculates synchronously per keystroke.
- **Runtime hypothesis:** input delay, long commits, scrolling stalls, and excess memory. Their magnitude is unmeasured, so this is not automatically P0.
- **Repair:** baseline first, then introduce an explicit mounted-row/work bound using existing project capabilities. Windowing best preserves continuous scrolling if compatible; pagination requires workflow approval.
- Profile filtering separately: cache reusable normalized data; defer result rendering where useful; debounce remote queries only where appropriate. Deferral alone does not make synchronous filtering cheaper; chunking or worker execution requires measured need.
- Preserve selection, focused-row identity, scroll restoration, and accessible row counts across unmounts. Memoize only demonstrated repeat work; avoid a blanket dependency or memoization pitch.
- **Acceptance:** meet the provisional gates below and repeat F2/F4 workflow checks with rows leaving and re-entering the rendered window.

### F8 — P3: broad transitions need targeted polish
- **Source evidence:** rows and drawer use `transition: all 300ms ease-in`; reduced-motion behavior is unspecified.
- **Runtime unknown:** which properties actually change, whether transitions cause layout/paint work, and whether motion overrides exist.
- **Repair:** transition only intentional properties using existing motion tokens; prefer transform/opacity for drawer movement where suitable. Remove decorative motion under `prefers-reduced-motion`; preserve immediate status feedback.
- **Acceptance:** no unintended dimension/color transitions or delayed interaction; reduced-motion behavior remains complete. Promote priority if runtime evidence reveals a material access or performance problem.

## 4. Static signals: decisive versus contextual

- **Decisive within this supplied description:** swallowed save errors (F1), explicitly missing recovery states (F3), absent drawer containment (F4), and full 10,000-row rendering with per-keystroke filtering (F7). These justify repairs without pretending latency or user harm was measured.
- **Decisive CSS declarations, contextual consequences:** `1180px`, `520px`, `100vh`, and rigid tracks identify constraints, but the cascade, viewport, and scroll ownership determine actual clipping (F5).
- **Strong accessibility signals, not standalone conformance verdicts:** icon-only controls can have accessible names; `outline: none` can have a replacement; a 28px visual box can have a larger effective target. Conversely, 28px alone does not establish failure of a 24px minimum criterion. Inspect actual names, focus, spacing, and hit areas (F4).
- **Conditional correctness risk:** a global boolean becomes unsafe with overlapping operations; it does not prove overlap occurs (F2).
- **Risk rather than measured outcome:** `transition: all` does not prove jank; missing reserved image space does not quantify CLS; an 8MB original does not prove an 8MB table download (F6–F8).
- Ellipsis, fixed dimensions, animation timing, and visual density are not grounds for redesign. Preserve established tokens/components unless concrete usability evidence requires a local exception.

## 5. Measurement-first validation and release gates

**All following checks are planned, not executed.**

1. **Establish a reproducible baseline.** Agree supported desktop/tablet browsers and minimum hardware; use identical 10,000-row fixtures, query sequences, uploads, cache conditions, and network profiles for before/after comparisons. Record device/browser versions and repeated-run distributions.
2. **Measure separate costs.** Capture initial render, typing-to-paint, query-to-settled-results, React commits, longest main-thread tasks, mounted rows, image transfer/decode cost, CLS, and retained memory after repeated drawer/upload cycles. Separate client filtering from network delay.
3. **Ratify provisional budgets before implementation:**
   - Input-to-next-paint p95 ≤ **100ms**; local filter-to-settled-results p95 ≤ **200ms**.
   - No interaction-attributable main-thread task > **100ms**; aim for tasks ≤ **50ms**.
   - Mounted product rows ≤ **200**, subject to measured viewport/overscan requirements.
   - CLS ≤ **0.1** over the defined loading/filter/image scenario.
   - Post-cleanup retained heap growth ≤ **10MB** after 20 drawer/upload cycles, with no sustained upward trend; ratify an absolute peak-memory budget from the baseline device.
   - No unrelated latency metric worsens by more than **10% or 20ms, whichever allowance is larger**; peak heap must not grow by more than **10%**.
4. **Verify correctness before claiming speed.** Exercise F1–F3 with controlled delayed, rejected, reordered, and uncertain responses. Check final server values, draft revision, selected IDs, permission handling, and batch outcomes.
5. **Verify interaction and presentation.** Run F4–F6/F8 across keyboard, screen reader, tablet touch, zoom, expanded translations, reduced motion, and supported themes. Compare against existing design-system exemplars; screenshots alone cannot prove interaction.
6. **Use existing project checks.** Run applicable type, lint, unit/integration, and production-build checks after implementation; do not treat passing compilation as usability or performance acceptance.
7. **Stage and retain rollback.** Ship narrowly scoped changes with a reversible render/filter path; monitor save failures/conflicts, recovery success, task completion, and performance without capturing sensitive content.
8. **Acceptance/rollback:** block release for silent save failure, lost drafts, wrong-item bulk updates, unauthorized mutation, or inaccessible core actions. Roll back an optimization that misses its agreed benefit or breaches regression gates; keep independent correctness repairs. Unverified tablet or recovery paths remain unsigned-off, not implicitly passed.
