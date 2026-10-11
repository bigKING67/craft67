## 1. Sequence and verdict

**Sequence:** Audit and establish baselines → harden correctness, recovery, accessibility, and tablet behavior → optimize measured bottlenecks → polish within the existing design system → regression validation and staged release. Performance measurement starts during audit, not after hardening.

**Verdict:** Not release-ready: silent save failures and missing recovery paths undermine editing trust; drawer accessibility and the unbounded table need remediation before visual polish.

This is a read-only assessment of the supplied description. No files were edited, and no detector, browser, build, profiler, accessibility-tree, network-throttle, or device run occurred. Runtime consequences below are hypotheses, not measured results.

Preserve the filters–table–drawer workflow, existing tokens/components, and stable `row.id` keys. There is insufficient evidence to grade contrast, theming, bundle size, or overall WCAG conformance.

## 2. Prioritized findings

**Evidence** means explicitly supplied code or notes. **Hypothesis** means a consequence requiring verification. Priorities reflect operational risk, not detector counts.

### P0 — Release blocker: save outcomes cannot be trusted

- **Evidence:** `saveProduct` swallows errors with `catch {}` and then clears `saving`; failure and conflict states are absent.
- **Impact:** A rejected save has no represented recovery path. **Hypothesis:** the drawer may appear saved or close with unsaved changes; its status rendering and draft lifecycle are not shown.
- **Fix:** Represent dirty, saving, saved, and failed states explicitly. Mark saved only after server acknowledgement of the current revision; preserve failed drafts and show an actionable error.
- **Concurrency risk:** One shared boolean cannot accurately represent overlapping requests. **Hypothesis:** if saves overlap, an earlier completion can clear the indicator while another request remains pending.
- **Fix:** Track status by product/revision; serialize or coalesce autosaves per product, ignore stale responses, and use server version checks to prevent stale writes. Merely moving `setSaving(false)` into `finally` does not solve this.

### P1 — Drawer interaction and pending-save exit

- **Evidence:** No focus trap or background interaction blocking; Escape closes even while saving. Save and close are icon-only.
- **Impact:** Users can leave the active editing context or interact behind it. Actual draft loss on close is **unverified**.
- **Fix:** If this is a modal drawer, use dialog semantics, an accessible title, initial focus, focus containment, inert background, and return focus to the opener. If intentionally nonmodal, do not falsely mark it modal; define usable focus movement between regions.
- Route Escape, close, navigation, and backdrop dismissal through one dirty/pending policy. Preserve the draft and clarify whether saving continues; offer a deliberate leave/discard decision rather than silently dropping work or trapping users indefinitely.
- Give save and close programmatic names; use existing labeled-action patterns where available.

### P1 — Failure, loading, and batch recovery are missing

- **Evidence:** Blank bodies during initial/filter loading; no empty, authorization, conflict, rate-limit, server, timeout, offline, retry, or partial-batch states.
- **Impact:** Users cannot distinguish waiting, no matches, or failure, nor know which bulk edits succeeded.
- **Fix:** Implement the state/recovery matrix below. Preserve filters, draft values, and appropriate selection during recoverable failures.

### P1 — Rendering and filtering scale poorly by construction

- **Evidence:** All 10,000 rows mount; filtering recalculates synchronously on every keystroke.
- **Impact:** Unbounded rendering and synchronous work are confirmed. Input lag, long tasks, memory pressure, and dropped frames are **runtime hypotheses**, not measured facts.
- **Fix:** Bound mounted rows using an existing windowing capability or an agreed incremental rendering strategy; retain the table workflow. Measure filtering separately before choosing scheduling, indexing, or computation changes.

### P1 — Tablet and keyboard access are at risk

- **Evidence:** `.page` has `min-width: 1180px`; drawer is fixed at `520px` with `100vh`; `.icon-button` removes outlines. Tablet behavior, focus-visible styling, and navigation are unspecified.
- **Impact:** The page cannot shrink below 1180 CSS pixels under the supplied rule. Exact viewport clipping and any replacement focus indicator require project context.
- **Fix:** Allow the page shell to shrink, constrain horizontal scrolling to the table, adapt the drawer to available width/height, and provide visible keyboard focus.
- Verify table semantics and keyboard operation; CSS grid styling alone proves neither their presence nor absence.

### P2 — Hostile content and upload handling

- **Evidence:** Names span 1–200 characters and truncate; prices may be missing; labels can expand 60%; images may be absent or 8MB; image space is not reserved.
- **Impact:** Hidden product distinctions, ambiguous prices, control overflow, and unstable loading geometry are risks. Actual layout shift and upload failures remain **unmeasured**.
- **Fix:** Apply the content and upload rules below. Escalate to P1 if truncation prevents reliable identification or upload failure blocks editing.

### P2 — Overbroad motion and small touch controls

- **Evidence:** Rows and drawer use `transition: all 300ms ease-in`; icon buttons measure `28px × 28px`; reduced-motion behavior is unspecified.
- **Impact:** Unintended property animation and touch errors are plausible; frame drops are not established.
- **Fix:** Transition only intended properties; use existing motion tokens and a reduced-motion alternative. Expand effective touch areas toward 44px without changing icon size or overlapping adjacent targets.
- A 28px target is not automatically a WCAG 2.2 AA target-size failure: the general minimum is 24px, subject to exceptions and actual geometry.

### P3 — Final consistency pass

- Once functional states exist, align table/drawer spacing, status placement, labels, tooltip behavior, and animation timing with incumbent patterns.
- These are bounded polish checks, not verified visual defects; no rendered surface was supplied.

## 3. Concrete remediation contract

### Hostile data and localization

- Keep dense row truncation where useful, but expose the complete product name in the drawer and a keyboard/touch-accessible reveal—not only a hover tooltip or `title`.
- Preserve a stable identifier beside ambiguous names. Test long unbroken strings; use shrinkable grid tracks such as `minmax(0, 1fr)` and `min-width: 0` where appropriate.
- Render missing prices as “Not set” or the existing equivalent; never convert absence to zero. Use locale-aware currency formatting and preserve numeric alignment.
- Allow filter labels, drawer actions, and error text to wrap under 60% expansion. Test localized plurals and 200% text sizing; avoid assembling translated sentences from fragments.
- Reserve thumbnail dimensions or aspect ratio. Provide absent/broken-image fallbacks and appropriate alt text; avoid repeating a nearby name for purely decorative thumbnails.
- Publish upload limits before selection. Validate size/type on client and server, handle decode failures, and support progress, retry, and cancellation.
- Use correctly sized thumbnails rather than 8MB originals in rows. Keep original-quality policy unchanged unless agreed; release temporary preview URLs.

### Failure and recovery matrix

| Situation | Required behavior |
|---|---|
| Initial loading | Stable loading structure, concise status, and no premature “no products” message. |
| Filter loading | Retain prior results where safe, mark them updating, and prevent bulk actions from targeting an ambiguous result set. |
| Empty results | Distinguish an empty inventory from no filter matches; offer the appropriate existing create or clear-filter action. |
| 401 | Request reauthentication; preserve drafts within the product’s security policy and do not replay writes blindly. |
| 403 | Explain insufficient permission; remove unavailable affordances or disable with a reason. Server authorization remains authoritative. |
| 409 | Preserve local edits, fetch the current version, and offer comparison/reconciliation; do not silently overwrite. |
| 429 | Respect `Retry-After`; show a useful wait state and avoid aggressive automatic retries. |
| 500 / timeout | Keep the draft and offer retry. A timeout may follow a successful write: reconcile status or use an idempotency mechanism before replaying. |
| Offline | Show unsaved/offline status; retain the draft. Only promise queued persistence if implemented and safe; reconcile versions on reconnect. |
| Partial batch failure | Report succeeded/failed counts and per-item reasons; preserve failed-item context and retry only failures. |

- Scope selections by stable IDs, not row positions or mounted DOM. Explicitly distinguish “selected rows” from “all matching results,” especially when filters change.
- Keep “Saved” tied to the last acknowledged revision and timestamp. New edits during an in-flight save remain dirty.
- Add appropriately scoped draft recovery if reload recovery is required; define retention, account boundaries, and clearing behavior. Never imply durable recovery from component state alone.

### Responsive layout and accessibility

- Keep desktop information density. Let filters wrap; keep primary actions reachable; allow table-only horizontal scrolling rather than forcing the entire page wide.
- Bound drawer width by the viewport and use dynamic viewport height with an appropriate fallback. Scroll its content internally; ensure action controls remain reachable with a tablet keyboard open.
- Prefer native table semantics for tabular data, labeled row checkboxes, a correctly represented mixed-state select-all control, and associated column headers.
- Do not add `role="grid"` without its expected keyboard model. With windowing, preserve focus and expose correct row counts/positions where applicable.
- Associate field errors with inputs; announce save success politely and actionable errors without announcing every keystroke.
- Restore focus sensibly if the original row is filtered out or unmounted. Provide a clear focus-visible treatment, meaningful button names, and accessible upload controls.
- Honor reduced motion without removing essential saving/error feedback.

### Performance without changing the product

- Baseline row mounting, filter computation, React commits, image decoding, and network cost separately.
- Bound mounted rows with overscan; validate selection, keyboard focus, scroll position, variable text height, and assistive technology before rollout.
- Keep filter input responsive. Defer result updates or chunk expensive computation as supported; deferral alone does not make a single expensive computation cheap.
- Memoize derived results and rows only where profiling demonstrates avoidable work; maintain stable props and handlers where beneficial.
- Lazy-load below-fold thumbnails, not immediately needed imagery. Reserve image geometry and request appropriately sized assets.
- Remove broad transitions; animate drawer transform/opacity only when appropriate. Avoid speculative blanket `will-change` or dependency additions.

## 4. What static signals establish—and what they do not

| Signal | Decisive conclusion | Context still required |
|---|---|---|
| Empty `catch` | Save errors are discarded by this handler. | Whether another layer logs errors or misleadingly shows success. |
| Shared `saving` boolean | State cannot distinguish concurrent requests. | Whether callers permit overlap and how the server orders writes. |
| 10,000 mapped rows + synchronous filtering | Work is unbounded by the viewport and runs synchronously. | Actual latency, commit cost, memory, and benefit of each optimization. |
| `min-width: 1180px`, fixed drawer | Supplied rules constrain available shrinkage. | Cascade, containers, tablet viewport, zoom, and keyboard behavior. |
| `outline: none` | Native outline is suppressed by this rule. | Replacement focus styles elsewhere; actual focus contrast and visibility. |
| Icon-only controls / 28px size | Labels are not visible; declared box is small for touch comfort. | Accessible names, effective hit area, spacing, and conformance. |
| `transition: all` | Every changing animatable property is eligible. | Which properties change, motion sensitivity, and rendering cost. |
| Ellipsis / unreserved images | Names are visually truncated; image geometry is not reserved. | Full-name access, identification impact, actual layout shift. |

Static warnings are triage inputs, not severity scores. Fixed dimensions, ellipsis, and icon controls can be legitimate in a dense operations tool. No evidence supports claims about dark-mode failure, poor contrast, unnecessary packages, or a need to replace the design system.

## 5. Measurement-first validation and release gates

**Proposed work—not executed:**

1. **Baseline:** Use representative 10,000-row data, 200-character names, missing prices/images, 8MB uploads, expanded translations, and permission variants. Record agreed desktop/tablet devices and browser versions.
2. **Capture:** Measure input-to-next-paint latency, filter-to-settled-results time, long tasks, React render/commit duration, mounted row count, heap trend, image bytes, and layout shift. Measure save acknowledgement separately from client responsiveness.
3. **Exercise failures:** Inject each matrix state, reordered save responses, rapid edits, close-during-save, filter changes during selection, and partial batch outcomes.
4. **Manual access checks:** Keyboard-only editing, screen-reader table/drawer interaction, focus restoration, reduced motion, 200% text sizing, zoom, tablet portrait/landscape, and the on-screen keyboard.
5. **Set budgets before implementation:** Provisional targets include p75 interaction latency ≤200ms on agreed devices, no image-induced table jumps, and mounted row count bounded by viewport plus overscan. Use repeated traces; do not equate a lab interaction measurement with field INP.
6. **Correctness acceptance:** Zero silently discarded save errors, stale overwrites in race tests, lost recoverable drafts, duplicate retried writes, or selection mismatches. Every failure has a truthful state and recovery action.
7. **Usability acceptance:** All editing and batch tasks complete by keyboard and supported tablet input; no inaccessible actions, focus escapes from modal drawers, or page-level clipping. Localization must not hide required actions.
8. **Staged rollout:** Separate state/recovery, rendering, and polish changes where practical. Compare completion rates, save errors/conflicts, latency distributions, and support signals against baseline.
9. **Rollback:** Roll back a rendering optimization immediately for selection corruption, lost focus, inaccessible rows, or material latency/memory regression. Roll back affected releases for lost edits or false save success; retain truthful failure handling through a safe fallback rather than restoring silent errors.

Finish with a bounded consistency pass and regression check—not a new visual direction.
