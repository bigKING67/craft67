## 1. Sequence and verdict

**Audit → harden → optimize → polish → focused re-audit.** Establish baselines before changes; fix save integrity, recovery, and access first; optimize measured bottlenecks without changing workflow; polish only after behavior is reliable.

**Verdict: Not release-ready as described—silent save failures are a release blocker; accessibility, recovery, tablet layout, and rendering need targeted hardening, not redesign.**

This is a read-only assessment of the supplied snippets and notes. No detector, browser, build, profiler, accessibility-tree inspection, network throttling, or device testing occurred. No files were edited.

**Evidence labels:** **Source** means explicit in the supplied material; **Hypothesis** means a consequence requiring implementation or runtime verification. Missing descriptions are not proof that functionality is absent. No numerical compliance or health score is justified by this partial surface description.

## 2. Prioritized findings

### P0 — Block release

**1. Save failures disappear; completion state cannot establish persistence**
- **Source:** `saveProduct` swallows exceptions with `catch {}` and clears `saving` after success or failure. Failure and recovery states are not represented.
- **Impact:** Operations staff cannot reliably distinguish persisted edits from rejected edits.
- **Hypothesis:** The drawer may display a false “saved” state or discard a failed draft; its internal implementation is not supplied.
- **Fix:** Represent dirty, queued, saving, saved, failed, and conflict states explicitly. Only acknowledge “saved” for the exact revision confirmed by the server. Preserve failed drafts and offer actionable recovery.

### P1 — Fix before release

**2. Concurrent saves and drawer closure have no demonstrated safety contract**
- **Source:** One boolean tracks saving; Escape closes during pending saves.
- **Hypothesis:** If requests overlap, the first completion can clear `saving` while another remains pending; responses may arrive out of order. Closing may lose draft access, though closing alone does not prove cancellation or data loss.
- **Fix:** Track per-product revisions and pending requests; serialize/coalesce saves per product or use version checks. Keep save ownership outside drawer lifetime. Define dirty/pending close behavior explicitly.

**3. Drawer keyboard and assistive-technology behavior is incomplete**
- **Source:** No focus containment or background-interaction restriction; save and close are icon-only; `.icon-button` removes outlines.
- **Hypothesis:** Modal users may reach background controls; accessible names and replacement focus indicators may be missing.
- **Fix:** Establish whether this is modal. If modal, provide a named dialog, initial focus, focus containment, inert background, and focus restoration. If intentionally nonmodal, preserve background access and provide clear keyboard movement between regions; do not falsely mark it modal.
- Add accessible button names and visible keyboard focus. Keep Escape useful, but do not let it silently discard work.

**4. Loading, failures, permissions, and batch recovery are missing**
- **Source:** Blank initial/filter loading; no empty-result, listed failure, retry, or partial-batch states. Permission affordances are unspecified.
- **Impact:** Users cannot distinguish waiting from zero results or choose a safe recovery action.
- **Fix:** Provide the state-specific responses below; preserve filters, drafts, selection, and confirmed outcomes through recoverable failures.

**5. Layout imposes desktop dimensions on tablet use**
- **Source:** `.page` has `min-width: 1180px`; drawer is fixed at `520px × 100vh`; table columns include fixed widths.
- **Hypothesis:** Narrow tablet viewports, zoom, or the software keyboard can produce page overflow or obscure drawer actions; exact behavior depends on surrounding layout.
- **Fix:** Allow the page shell to shrink, contain table overflow locally, and clamp drawer dimensions to available space. Preserve the table workflow rather than replacing it with a different interface.

**6. Rendering and filtering create substantial responsiveness risk**
- **Source:** All 10,000 rows render; filtering recalculates synchronously per keystroke; image space is unreserved.
- **Hypothesis:** Input delay, long render commits, excess memory, and image-driven layout shifts. Magnitudes are unmeasured.
- **Fix:** Measure first, then bound row rendering, separate urgent typing from result work, and reserve image dimensions. Maintain keyboard access and selection semantics.

### P2 — Correct in the hardening pass

**7. Hostile data has incomplete presentation and upload handling**
- **Source:** Names span 1–200 characters and are ellipsized; prices may be missing; labels may expand 60%; images may be absent or 8MB.
- **Hypothesis:** Ambiguous product identification, clipped actions, accidental zero-price display, upload delays, or memory pressure.
- **Fix:** Make full names available without hover dependence, distinguish missing prices from zero, accommodate wrapping, and validate/upload images through explicit states.

**8. Motion and pointer targets need contextual correction**
- **Source:** `transition: all 300ms ease-in`; icon buttons are `28px × 28px`; reduced motion is unspecified.
- **Hypothesis:** Unintended layout animation, sluggish feedback, or difficult tablet activation.
- **Fix:** Transition only necessary properties, usually transform/opacity; remove nonessential travel under reduced motion while preserving status feedback. Aim for roughly 44px touch hit areas without forcing larger visual icons or overlapping targets.

### P3 — Final polish

**9. Refine presentation after state correctness**
- **Source:** The existing system and workflow must remain intact; detailed visual tokens are not supplied.
- **Validation task:** Check status wording, alignment of prices and row actions, focus treatment, truncation affordances, and drawer spacing against existing components.
- **Fix:** Reuse incumbent tokens and patterns; avoid new typography, palette, navigation, or decorative treatments.

**Preserve:** Stable `row.id` keys, recognizable row/drawer workflow, and the existing component system are useful foundations. None needs wholesale replacement.

## 3. Concrete hardening contract

### Hostile data and uploads
- Keep compact name truncation where useful, but expose the full name in the drawer and through a keyboard/touch-accessible disclosure if needed during scanning. Do not rely solely on a `title` tooltip.
- Use `minmax(0, 1fr)`/`min-width: 0` where appropriate; permit translated labels and validation messages to wrap. Test long unbroken strings and 60% label expansion.
- Render missing prices as an explicit unavailable state, never as zero; use locale-aware currency formatting and distinguish invalid input from missing data.
- Reserve thumbnail aspect ratios; show consistent absent/broken-image placeholders. Use meaningful alt text only when images add information beyond adjacent names.
- Enforce documented upload type, byte, and dimension limits client- and server-side. Handle 8MB files deliberately: accept with progress or reject before transfer with the exact limit.
- Provide upload cancellation/retry and preserve the previous image until replacement succeeds. Release temporary preview URLs and avoid loading full originals as list thumbnails.

### Failure and recovery behavior

| State | Required response |
|---|---|
| Initial loading | Labeled, stable loading structure; no misleading empty result. |
| Filter refresh | Keep prior results visibly marked as updating where safe; prevent bulk actions against an ambiguous result scope; ignore stale responses. |
| Empty results | Distinguish an empty inventory from no filter matches; offer clear-filter recovery. |
| 401 | Explain session expiry; preserve drafts under an approved sensitive-data policy and resume after authentication. |
| 403 | Explain the unavailable operation; reflect permissions in affordances, with server authorization authoritative. |
| 409 | Preserve local edits and compare against the current server version; allow deliberate resolution, not silent overwrite. |
| 429 | Honor `Retry-After`; use bounded backoff and show when retry is available. |
| 500 / timeout | Preserve draft and show retry. A timeout may follow a successful write: reconcile or use idempotency before repeating it. |
| Offline | Clearly say changes are not saved. Queue only if durable, authorized recovery semantics exist; otherwise retain the draft and offer retry. |
| Partial batch failure | Show succeeded/failed counts and per-item reasons; retry only failed items and retain their selection. |

- Distinguish “Saved at…” from “Saving…” and “Changes not saved.” Use a restrained live region; associate field errors with their inputs.
- Keep draft and server snapshots separate. Applying an older response must not erase newer typing.
- For dirty closure, offer a clear retain/discard decision where needed. For pending saves, either continue safely after closure with persistent status or explain why closure is temporarily deferred.
- Persist across reload only where explicitly supported and safe; otherwise warn before losing unsaved work. Aborting a client request is not proof the server canceled the write.
- Define bulk selection by stable IDs and explicit scope: visible page, filtered set, or entire inventory. Filtering and virtualization must not silently change that scope.

### Responsive layout and accessibility
- Remove the shell’s hard minimum width; keep necessary two-dimensional table scrolling inside a labeled region. Filters, status, and primary controls should reflow independently.
- Use a drawer width bounded by the viewport, dynamic viewport height with fallback, and an internal scroll area. Keep actions reachable with keyboard open and at zoom; avoid obscuring focused fields.
- Preserve essential columns and access to all data; do not silently hide operational fields to make tablet layouts fit.
- Prefer native table semantics for tabular data and native buttons/checkboxes. Use an ARIA grid only if its complete keyboard interaction is implemented.
- Give row checkboxes product-specific names; expose select-all’s mixed state and selection scope. Ensure keyboard focus survives filtering, row removal, and windowing.
- Test visible focus, accessible names, status announcements, error associations, contrast, and focus not obscured. Contrast cannot be assessed from these snippets.

### Performance without workflow regression
- Baseline row mount cost, typing-to-results latency, commit duration, DOM size, image transfer/decode cost, and memory.
- Bound mounted rows through existing windowing infrastructure or a small scoped implementation; consider pagination only if the current workflow permits it. No new dependency is assumed.
- Preserve logical row counts/positions, focused rows, select-all semantics, and assistive-technology access when windowing.
- Cache normalized search data and avoid unrelated row rerenders where measurements justify it. Deferred rendering alone does not make a synchronous expensive filter cheap; chunk or move computation off-thread if measured cost requires it.
- Load suitably sized thumbnails; lazy-load offscreen images while prioritizing visible ones. Use explicit dimensions and avoid blanket `will-change`.

## 4. Static signals: decisive versus contextual

**Decisive from the supplied source**
- Save rejection is swallowed; the shown state has no error outcome.
- All rows render and filtering is synchronous per keystroke.
- The listed loading/error states are absent.
- Fixed layout constraints, broad transitions, outline removal, and unreserved image dimensions exist.

**Require project or runtime context**
- `outline: none` is not proof of invisible focus if another visible treatment exists; absence of any replacement would be a failure.
- Icon-only is not inherently inaccessible; an icon-only button without an accessible name is.
- A 28px target is below a useful tablet comfort goal, but not automatically below WCAG 2.2 AA’s 24px minimum; actual target size, spacing, and exceptions matter.
- `transition: all` is risky, not proof of dropped frames. The properties that change determine cost.
- `100vh`, fixed widths, ellipsis, and table scrolling are not categorically wrong; containment, viewport behavior, full-text access, and task needs determine impact.
- Missing memoization is not itself a defect; 10,000 rendered rows do not establish a measured latency.
- Missing descriptions of labels, permissions, or reduced motion warrant verification, not invented compliance failures.
- No supplied evidence supports judgments about contrast, bundle size, theming quality, or decorative design-system drift.

## 5. Measurement-first validation and release gates

1. **Record a baseline before intervention:** representative desktop and lower-powered supported tablet; agreed viewport/zoom matrix; 10,000 realistic rows plus long names, missing prices/images, expanded translations, and 8MB uploads.
2. **Instrument task outcomes:** filter latency, save acknowledgment latency, overlapping requests, failure/retry outcomes, mounted rows, render/interaction timing, layout shifts, memory, and transferred image bytes. Exclude sensitive draft content from telemetry.
3. **Exercise deterministic failures:** every listed status, offline/reconnect, out-of-order saves, double activation, close/reopen during save, timeout-after-server-commit, permission change, and mixed batch results.
4. **Validate access manually as well as automatically:** keyboard-only filter/select/edit/save/recover flow; supported screen readers; tablet touch; reduced motion; zoom and expanded text. Automation alone cannot certify these workflows.
5. **Agree numerical budgets before optimizing:** provisional targets might include p75 interaction latency ≤200ms, filter feedback/results within 300ms on the reference dataset/device, and CLS ≤0.1. Separate input responsiveness from result completion and server latency; report tail behavior, not averages alone.
6. **Correctness acceptance:** no silent failures, false saved acknowledgments, stale overwrites, duplicate retry effects, or lost drafts in the test matrix; batch retry affects only failures; selection and permissions remain correct.
7. **Usability acceptance:** all essential tasks work by keyboard and tablet; focus is visible and restored; drawer actions remain reachable; full product identity is accessible; no unintended page-level overflow at supported widths.
8. **Stage changes independently:** save/recovery hardening, layout/accessibility, rendering optimization, then polish. Compare each against the baseline and preserve the current design system.
9. **Rollback gates:** revert a change that introduces data loss, duplicate writes, selection mismatch, inaccessible rows, focus loss, or performance beyond agreed budgets. If a save-integrity fix cannot safely ship, disable the affected write path rather than restoring silent failure.
10. **Final acceptance:** focused regression audit plus monitored staged rollout with explicit ownership of error-rate and latency thresholds; do not treat visual polish or a clean static scan as release evidence.
