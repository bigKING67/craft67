## 1. Sequence and verdict

**Sequence:** audit and establish baselines → harden correctness, recovery, and accessibility → optimize measured bottlenecks → polish within the existing design system → validate and release incrementally. Address overlapping fixes together; cosmetic polish must not conceal broken states.

**Verdict:** The supplied source establishes production-blocking save/recovery gaps and significant accessibility and scale risks; preserve the workflow and components, but harden them before visual polish.

**Scope:** Read-only review of the supplied description and snippets. No detector, build, browser, profiler, accessibility-tree, network, or device run was performed. Runtime effects below are hypotheses unless directly established by the source.

## 2. Prioritized findings

Priority meaning: **P0** release blocker for data integrity or security; **P1** essential workflow/accessibility hardening; **P2** robustness and performance improvements; **P3** finishing polish.

| Priority | Finding and source evidence | Runtime hypothesis / uncertainty |
|---|---|---|
| **P0** | **Failed saves are indistinguishable from completed saves.** `catch {}` discards the error, then `saving` becomes false; no failure or recovery state is represented. | The UI may imply success or allow users to discard unsaved edits. Actual data loss and success messaging are not demonstrated. Block release until failure preserves edits and is explicit. |
| **P1 → P0 if reproduced** | **Save concurrency is not modeled.** A single boolean surrounds each `api.save(product)` call. | If saves overlap, one completion can clear `saving` while another is pending; responses may arrive out of order. Escalate to P0 if an older edit can overwrite a newer one. |
| **P1** | **Drawer interaction is incomplete.** No focus trap or background-interaction containment; Escape closes during a pending save; save/close are icon-only. | If this is a modal drawer, users can escape its interaction context. Closing may lose draft/status visibility. Icon-only controls are not inherently inaccessible; accessible names are unverified. |
| **P1** | **Loading, empty, failure, and partial-success states are missing.** Loading leaves the table body blank; listed HTTP/network outcomes have no representation. | Users may confuse loading with zero inventory, repeat mutations, or miss batch failures. |
| **P1** | **Rendering and filtering scale poorly by construction.** All 10,000 rows mount; filtering recalculates synchronously per keystroke. | Input delay, long tasks, memory pressure, and slow drawer interaction are likely, but magnitude requires measurement. |
| **P1** | **Tablet layout has a hard constraint.** `.page { min-width: 1180px; }`; drawer is fixed at `520px` with `100vh`. | Narrower viewports will need overflow handling. Unusable controls, drawer obstruction, or mobile-keyboard clipping require rendered checks. |
| **P1** | **Keyboard focus and permissions are unspecified.** `.icon-button` removes outlines; no focus-visible or permission affordances are described. | Focus may be invisible unless another rule restores it. Missing frontend permission cues are not proof of missing server authorization; verified unauthorized mutation would be P0. |
| **P2** | **Hostile data is insufficiently accommodated.** Names vary from 1–200 characters, prices can be missing, labels expand 60%, and images may be absent or 8MB. Names are ellipsized. | Important identifiers may become indistinguishable; labels may collide; large images may dominate loading. Truncation itself is not a defect if full values remain accessible. |
| **P2** | **Image layout stability is unprotected.** Image dimensions are not reserved. | Layout shifts depend on surrounding sizing and load timing; the snippet does not establish a measured shift score. |
| **P2** | **Transitions are broad and motion preferences unspecified.** Rows and drawer use `transition: all 300ms ease-in`. | Layout/paint properties may animate unnecessarily; actual cost depends on which properties change. Reduced-motion behavior needs verification. |
| **P3** | **Status and visual consistency need a final pass.** Multiple workflow states must be added to existing components. | Spacing, contrast, hierarchy, and status readability cannot be judged conclusively from these snippets. |

## 3. Concrete hardening and polish

### Save correctness, failures, and recovery
- Replace the boolean-only model with explicit dirty, queued, saving, saved, and failed states tied to the product and draft revision.
- Serialize/coalesce autosaves per product, or use revision-aware requests and responses. Only acknowledge the revision actually saved; retain edits made during an in-flight request.
- Use server-supported version checks for conflicts. An aborted client request does not prove the server canceled a mutation.
- Preserve the draft and show a persistent, actionable save error. Show “Saved” only after acknowledgment; distinguish it from “Saving” and “Unsaved changes.”
- Keep save status visible if drawer closure is allowed. Otherwise guard close, Escape, and navigation while edits are at risk, with a clear explanation and safe exit path.
- Avoid a permanent keyboard trap: let users return to editing or explicitly discard when safe. Do not silently treat closing as cancellation.
- Retry only eligible failures, with bounded backoff and jitter; respect `Retry-After`. Do not blindly replay non-idempotent mutations.
- Handle outcomes explicitly:
  - **401:** reauthentication flow that preserves the draft without exposing it across users.
  - **403:** explain denied action, retain recoverable work where appropriate, refresh permissions; enforce authorization server-side.
  - **409:** retain local edits and offer comparison/reload/merge appropriate to the existing workflow; never silently overwrite.
  - **429:** communicate the wait and defer retries.
  - **500 / timeout / offline:** keep edits, expose retry, and distinguish failure from an unknown commit outcome.
  - **Partial batch failure:** report succeeded/failed counts and row-level reasons; retry only eligible failed rows without repeating successful work.
- Define bulk-selection scope: current page/window, filtered result set, or explicit IDs. Filtering and virtualization must not silently change it.
- Keep selected IDs and drafts outside mounted row instances; validate stale/deleted/ineligible records at mutation time.

### Loading, hostile data, and uploads
- Use distinct initial loading, filter updating, empty inventory, no matches, and load-error states.
- For filter refreshes, preserve prior results when appropriate, mark them as updating, and prevent stale result responses from replacing newer ones.
- Render missing prices as an explicit unknown/not-set value, not zero; preserve legitimate zero prices and use locale-aware formatting.
- Keep visual name truncation where needed, but provide the full value through keyboard/touch-accessible detail or expansion—not hover-only tooltips.
- Test long unbroken names, punctuation, non-Latin text, and 60% label expansion. Allow wrapping and flexible control sizing without changing hierarchy.
- Reserve image aspect ratio/dimensions; provide consistent absent/broken-image fallbacks and context-appropriate alt text.
- Validate file type, size, and decoded dimensions on client and server. Explain limits before upload; an 8MB file is not automatically invalid.
- Show upload progress, cancellation/retry, and failure separately from product-save status; save image references only when upload completion is valid.
- Use existing thumbnail/delivery capabilities, responsive sources, and below-viewport lazy loading. Avoid fetching full originals for tiny row previews.

### Responsive layout and accessibility
- Remove the page-wide minimum-width dependency. Keep essential controls responsive and isolate necessary horizontal scrolling to the table region.
- Preserve row/header alignment and access to every field. Do not hide operationally important columns merely to make the page fit.
- Constrain drawer width to available space, retain the desktop width where it fits, and use viewport-aware height with internal scrolling and reachable actions.
- Verify tablet portrait/landscape, zoom, touch, and software-keyboard behavior; do not assume a desktop breakpoint solves them.
- Decide whether the drawer is modal. If modal: supply a labeled dialog, contain focus, make background content inert, set sensible initial focus, and restore focus to the opener or a logical fallback.
- If nonmodal: keep background interaction available intentionally and provide a clear keyboard route between the drawer and inventory; do not claim modal semantics.
- Give save/close explicit accessible names and preferably existing labeled-button variants where ambiguity matters.
- Restore visible keyboard focus. Increase touch hit areas using existing spacing tokens; a 28px target exceeds the basic 24px size threshold but may still be poor for frequent tablet use.
- Use appropriate table semantics and labeled selection controls; communicate checked, indeterminate, disabled, sort, and busy states.
- Adopt grid keyboard behavior only if implementing the full grid interaction model. Avoid creating thousands of unnecessary tab stops.
- Announce save/error changes without announcing every keystroke. Associate validation errors with fields and avoid color-only status.
- Replace `transition: all` with the properties actually needed; favor transform/opacity for drawer movement and honor reduced motion.

### Performance without a redesign
- Profile representative 10,000-row data first, then use existing infrastructure for row virtualization or established pagination.
- Preserve selection, focused-row behavior, row identity, scroll restoration, and screen-reader context across unmounted rows.
- Separate input responsiveness from expensive filtering; defer/debounce computation where appropriate and avoid recomputing unchanged normalized data.
- Consider a worker or server-side filtering only if measurements and the current architecture justify it—not as an automatic dependency addition.
- Isolate drawer/save state from unnecessary table rerenders. Apply memoization only where traces show useful work avoidance.
- Keep image loading and row rendering fixes independently releasable so regressions can be isolated.

## 4. Static signals: decisive versus contextual

**Decisive from supplied source**
- Errors are swallowed; listed recovery states are absent.
- The shown render path maps every row without windowing.
- The supplied loading state is blank.
- Fixed minimum/page/drawer dimensions and unrestricted transitions exist.
- Modal safeguards, image dimension reservation, and several accessibility behaviors are absent or unspecified as noted.

**Require project or runtime context**
- `outline: none` proves outline removal, not absence of every possible focus indicator.
- Icon-only controls require accessible names; icons alone do not establish whether names exist.
- `28px` does not by itself establish a minimum-target-size violation; spacing, exceptions, and usability matter.
- `transition: all` is a risk signal, not proof of layout thrashing or a frame-rate failure.
- Ten thousand rendered rows establish workload, not a specific latency or memory figure.
- Ellipsis, fixed columns, `100vh`, and horizontal scrolling require viewport/content checks before declaring a particular failure.
- Missing permission descriptions do not prove an authorization vulnerability.
- Contrast, DOM semantics, announcements, actual request ordering, and draft persistence cannot be inferred from the excerpts.

Use static findings to target investigation, not to manufacture scores or runtime results.

## 5. Measurement-first validation and release gates

1. **Record a reproducible baseline:** current production-equivalent configuration, representative and worst-case data, supported desktop/tablet viewports, and agreed device/network profiles.
2. **Measure the critical journeys:** initial inventory display, rapid filtering, bulk selection, opening/editing/closing the drawer, image upload, save, and recovery after interruption.
3. **Capture:** input-to-result latency, interaction latency, long tasks, render/commit time, mounted-row count, peak memory, image bytes, layout shifts, and save acknowledgment time.
4. **Set budgets before implementation:** define per-journey limits with product/engineering. Candidate guardrails include p75 interaction latency ≤200ms and CLS ≤0.1; these are targets, not observed results, and do not replace workflow-specific limits.
5. **Exercise deterministic failures:** every listed HTTP state, slow/out-of-order saves, timeout after server commit, offline/reconnect, expired sessions, denied actions, upload failure, and mixed batch outcomes.
6. **Validate data invariants:** no stale overwrite; no false “Saved”; no lost draft on recoverable failure; retry cannot duplicate successful work; selections remain correct through filtering/windowing.
7. **Validate access manually and automatically:** keyboard-only journeys, focus visibility/order/restoration, labels and announcements with supported screen readers, reduced motion, zoom, and touch targets.
8. **Run a content/layout matrix:** 1- and 200-character names, unbroken strings, missing/zero prices, expanded translations, absent/large images, and narrow tablet orientations.
9. **Compare equivalent runs:** use repeated measurements and distributions, not one favorable sample. Investigate regressions in correctness, accessibility, latency, memory, and request volume.

**Acceptance:** all P0 issues resolved; essential P1 journeys pass; agreed budgets are met without losing workflow or design-system consistency. Document any remaining lower-priority limitations with owners.

**Release:** stage changes in small, reversible increments, with separate controls for rendering/filtering optimizations. Monitor save failures, conflicts, retries, abandoned edits, and interaction performance without logging sensitive product contents.

**Rollback:** halt or revert an increment on stale writes, draft loss, duplicate mutations, selection corruption, blocked keyboard workflows, or agreed performance/error-budget breaches. Preserve queued edits during rollback; disable an unsafe mutation path rather than reverting to known silent failure.
