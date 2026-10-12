## 1. Sequence and verdict

**Audit → harden → optimize → polish → targeted re-audit.** Establish a baseline before implementation; fix persistence, recovery, accessibility, and layout contracts first; optimize measured bottlenecks without breaking those contracts; finish with visual and interaction polish.

**Verdict: Not release-ready as described—silent save failures and missing recovery are release blockers; drawer accessibility, tablet layout, and unbounded rendering need hardening, not redesign.**

This is a read-only assessment of the supplied snippets and notes. No detector, browser, build, profiler, accessibility-tree inspection, network throttle, or device run occurred. No files were edited.

Keep the existing design system, table/editor workflow, and stable `row.id` keys. There is insufficient evidence to score contrast, theming, bundle size, or overall accessibility conformance.

## 2. Prioritized findings

**Evidence** means directly present in the supplied material. **Hypothesis** means an outcome that needs implementation inspection or runtime validation. Priorities reflect operational risk, not measured prevalence.

| Priority | Finding and source evidence | Impact / hypothesis | Required action |
|---|---|---|---|
| **P0** | **Save failure is suppressed.** `saveProduct` has `catch {}` and returns to `saving=false` after rejection. | Failure becomes indistinguishable from idle at this boundary. Actual “Saved” messaging and draft loss are not shown. | Represent failure explicitly; retain dirty values; provide safe retry; never report success without acknowledgement. |
| **P1** | **A boolean cannot represent overlapping saves.** Every request independently sets `saving=false`. | If saves overlap, an earlier completion can clear pending status while another request remains active. Stale writes are possible depending on API ordering. | Serialize/coalesce saves per product, track revisions and pending work, and reject stale acknowledgements. Treat confirmed overwrites as P0. |
| **P1** | **Drawer isolation and dismissal are unsafe.** No focus trap or background isolation; Escape closes during save. | For a modal drawer, keyboard users can reach obscured content. Closing may conceal unresolved work; actual cancellation or data loss is unverified. | Establish modal semantics and focus management; implement an explicit dirty/pending close policy. |
| **P1** | **Failure and recovery states are absent.** Notes omit authorization, conflicts, rate limits, server/network failures, and partial batch results. | Staff cannot distinguish retryable failures from rejected or uncertain writes. Bulk actions can leave inventory ambiguous. | Add outcome-specific recovery and per-item batch reconciliation. |
| **P1** | **Keyboard/accessibility support is unestablished.** Icon-only Save/Close; `outline:none`; labels and keyboard navigation not described. | Missing accessible names or replacement focus indicators would block use. Icon-only controls alone do not prove missing names. | Verify native controls, accessible names, focus-visible treatment, table semantics, and selection behavior. |
| **P1** | **Tablet layout is constrained.** `.page { min-width:1180px }`; drawer is fixed at `520px` and `100vh`. | Below 1180 CSS pixels, that page box exceeds the viewport. Actual scroll containment, clipping, and keyboard obstruction require testing. | Make the shell fluid; contain table scrolling; bound drawer width and usable height. |
| **P1** | **Work scales with all 10,000 rows.** Full `rows.map`; filtering runs synchronously on every keystroke. | Long tasks, slow typing, excessive DOM, and broad rerenders are credible risks, not measured results. | Profile and bound rendered rows; decouple input from expensive filtering. Preserve selection and accessibility. |
| **P2** | **Loading is visually blank.** Initial and filter loading have an empty body. | Users cannot distinguish loading, no matches, and failure. | Add distinct loading, updating, empty, and error states without unnecessary layout changes. |
| **P2** | **Hostile data is insufficiently handled.** Names are ellipsized; prices may be missing; labels expand 60%; images may be absent or 8MB; image space is unreserved. | Hidden identifiers, misleading prices, overflow, image failures, and layout shifts are plausible. | Add full-value access, locale-safe formatting, bounded text/image behavior, and upload validation. |
| **P2** | **Motion is indiscriminate.** Rows and drawer use `transition:all 300ms ease-in`; reduced-motion behavior is unspecified. | Changed layout properties may animate; jank is not established without knowing which properties change. | Transition only intentional properties; provide a reduced-motion alternative. |
| **P3** | **Final consistency pass remains.** The supplied CSS applies the same motion treatment to different interactions. | Timing and feedback may feel inconsistent with existing components; no visual comparison was supplied. | After functional fixes, align timing, spacing, truncation affordances, and status copy with existing tokens/components. |

## 3. Concrete production fixes

### Persistence, failures, and state recovery

- Replace the single status flag with explicit **clean, dirty, queued, saving, saved, failed, and conflict** states as needed; track uploads separately.
- Associate requests with product ID and revision. A response must not mark newer edits clean or update a different product’s drawer.
- Use per-product save serialization or latest-draft coalescing; use server version checks where supported. Client ordering alone does not prevent multi-user conflicts.
- Show “Saved” only for the acknowledged revision. Expose pending changes, failure, and last confirmed save without announcing every keystroke.
- Preserve draft values and validation errors after failure. Keep save state outside drawer lifetime if saving is allowed to continue after dismissal.
- On dirty or pending close, offer a clear policy: stay, explicitly discard unsent edits, or close while tracked work continues. Do not imply that closing or aborting a request reverses a server write.
- Prevent silent duplicate submission. After uncertain outcomes, reconcile with server state before repeating a write; use idempotency support where available.

| Condition | Recovery behavior |
|---|---|
| **401** | Preserve a draft within approved security/storage policy; request sign-in; reconcile before resubmission. |
| **403** | Explain the permission restriction; remove or disable unauthorized actions with an accessible reason. Keep server authorization authoritative. |
| **409** | Preserve local edits; fetch the current version; show conflicting fields and an explicit resolve/reapply path. Never silently overwrite. |
| **429** | Honor `Retry-After`; retain edits; show when retry becomes available. Avoid rapid automatic retries. |
| **500 / timeout** | Keep edits and show retry guidance. A timeout can mean “outcome unknown,” not “nothing saved.” |
| **Offline** | Mark edits unsynced. Do not promise durable offline queuing unless implemented; reconcile on reconnect. |
| **Partial batch failure** | Report succeeded, failed, and unknown items separately. Retain failed-item selection; retry only eligible unresolved items after reconciliation. |

- Define selection scope explicitly: visible rows, filtered results, or all products. Filtering and virtualization must not silently change that scope.
- Keep filters, sort, scroll position, selection, and drawer draft stable through recoverable failures.
- Separate “no inventory” from “no matching results”; offer the appropriate existing action, such as clearing filters.
- During filtering, retain existing results with an updating indicator when safe; prevent bulk actions from ambiguously targeting stale versus new results.

### Hostile data and images

- Test 1- and 200-character names, unbroken strings, non-Latin text, and bidirectional text. Render names as text, not injected HTML.
- Allow grid children to shrink with `min-width:0`; use bounded tracks such as `minmax(0,1fr)` where appropriate.
- Preserve compact table truncation, but expose full names through keyboard- and touch-accessible details—not hover-only tooltips. Wrap long text in the drawer.
- Distinguish missing prices from zero. Use a meaningful “Not set” state and locale-aware currency formatting; validate numeric ranges and precision.
- Allow translated labels to wrap and controls to grow. Test 60% expansion and text zoom without hiding critical actions.
- Reserve thumbnail dimensions/aspect ratio, including loading, missing, and failed-image placeholders.
- Serve suitably sized thumbnails rather than original uploads in rows. Lazy-load offscreen imagery while prioritizing visible content.
- Set and communicate upload byte, type, and pixel limits. Validate on the server as well as the client; provide progress, failure, retry, and cancellation.
- If 8MB files are allowed, use the existing image pipeline for bounded resize/compression where appropriate. If not, reject clearly before upload rather than silently failing.

### Responsive layout and accessibility

- Remove the page-level width floor; preserve dense columns inside a clearly bounded horizontal table scroller. Do not turn the entire page into a sideways viewport.
- Keep key identifiers and bulk controls discoverable. Do not hide operationally necessary columns merely to fit tablet widths.
- Bound drawer width to available space, for example `width:min(520px,100%)`; use an appropriate dynamic viewport height with fallback, internal scrolling, and reachable actions.
- Test tablet orientation, browser zoom, and the on-screen keyboard. Wrap filters and bulk controls without changing their workflow.
- If the drawer is modal, provide an accessible dialog name, initial focus, contained Tab navigation, inert background, and focus return to the trigger or a stable fallback.
- If it is intentionally non-modal, do not falsely use `aria-modal` or trap focus; instead provide clear navigation between drawer and table.
- Use named native buttons for Save and Close. Restore a visible keyboard focus treatment using existing tokens.
- A 28×28 control is below a useful **44×44 touch target**, but is not automatically below WCAG 2.2 AA’s 24×24 minimum. Enlarge effective hit areas for tablet use without overlapping neighbors.
- Use table/header semantics and labeled selection checkboxes with a mixed-state select-all control. If using an interactive grid, implement its full keyboard contract rather than adding a role alone.
- Associate field errors and help text programmatically. Announce save/loading outcomes through restrained live regions.
- For reduced motion, remove nonessential movement while preserving immediate state feedback.

### Performance without a dependency pitch

- Measure row render/commit cost and filter cost separately before choosing changes.
- Bound mounted rows using existing windowing capability or a minimal implementation. Preserve row identity, selected IDs, focus, scroll restoration, and access to offscreen results.
- Keep input updates immediate; defer or debounce expensive filtering as appropriate. Deferring rendering alone does not move CPU work off the main thread.
- Normalize searchable fields once when data changes. Consider chunking, a worker, or server filtering only if measurements and existing architecture justify it.
- Memoize rows only where profiling shows avoidable work and stable props make it effective; keep frequently changing save status from needlessly invalidating the table.
- Limit transitions to deliberate properties, usually transform/opacity for drawer movement. Do not add blanket `will-change`.

## 4. Static signals: decisive versus contextual

**Decisive from the supplied source**
- Rejected saves are swallowed at the shown boundary.
- Every row is mounted; filtering is synchronous on each keystroke.
- The page has a fixed minimum width; the drawer has fixed width/viewport-height rules.
- The shown rule removes the outline and transitions all animatable properties.
- Loading, failure, and image-space handling are absent as described.

**Require project or runtime context**
- Whether another style restores focus visibility; whether icon buttons have accessible names.
- Whether the drawer is intended to be modal and whether dismissal actually loses data.
- Whether overlapping requests occur and whether server safeguards prevent stale writes.
- Whether overflow is already contained by an ancestor.
- Actual typing latency, memory use, frame drops, image transfer sizes, and layout-shift magnitude.
- Whether ellipsis has an accessible full-value alternative.
- Contrast, dark-mode behavior, permissions enforcement, bundle waste, and complete semantic markup.

Static rules identify implementation patterns, not complete user outcomes. Fixed dimensions and ellipsis can be appropriate inside controlled layouts; missing memoization is not inherently a defect. Conversely, a clean static scan would not establish recoverable saves, correct batch semantics, or usable keyboard interaction.

## 5. Measurement-first validation and release gates

1. **Establish a baseline before changes.** Use representative 10,000-row data, worst-case names/translations, missing prices, image variants, and the supported permission matrix. Record environment and repeat runs.
2. **Measure core tasks:** initial usable table, filter input-to-results latency, long tasks, React render/commit time, mounted-row count, memory trend, image bytes, and layout shifts.
3. **Exercise write correctness:** rapid edits, overlapping/out-of-order responses, product switching, drawer dismissal, navigation, reconnect, every listed failure, and mixed batch outcomes.
4. **Check interaction access:** keyboard-only operation, screen-reader names/statuses, focus visibility/return, selection semantics, reduced motion, text enlargement, and tablet touch/keyboard behavior.
5. **Set acceptance budgets before implementation.** Proposed starting targets: field INP p75 ≤200ms, CLS ≤0.1, and representative lab filter results p95 ≤200ms on the agreed tablet. Calibrate these with the baseline; lab timing is not field INP.
6. **Correctness gates:** no false “Saved,” stale acknowledgement clearing newer edits, silent draft loss, unauthorized mutation, or duplicate successful batch application. Every tested failure has a recoverable, understandable outcome.
7. **Layout/accessibility gates:** no unreachable actions or page-level horizontal overflow at supported sizes; intentional table scrolling is acceptable. All core tasks work by keyboard, with visible focus and meaningful names.
8. **Performance gates:** mounted rows remain bounded if windowing is introduced; repeated filtering/open-close cycles show no unexplained memory growth; no agreed critical-task regression beyond a predefined tolerance.
9. **Stage independently:** persistence/recovery, accessibility/layout, rendering/filtering, then polish. Compare before/after under the same conditions and recheck invariants after each stage.
10. **Rollback:** halt rollout for correctness, permission, focus, selection, or scroll-restoration regressions, or a breached performance budget. Disable the offending optimization independently; do not roll back safety fixes into silent failure.
11. **Final acceptance:** review representative desktop/tablet states against the existing design system, confirm recovery tests and budgets, and document remaining risks with owners. Do not substitute visual polish for these gates.
