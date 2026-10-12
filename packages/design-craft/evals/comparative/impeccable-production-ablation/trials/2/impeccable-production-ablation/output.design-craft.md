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
