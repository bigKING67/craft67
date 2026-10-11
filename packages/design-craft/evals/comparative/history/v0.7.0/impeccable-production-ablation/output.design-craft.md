## 1) Sequencing + verdict

**Correct sequence:** static audit and baseline plan → P0 correctness/recovery hardening → accessibility/responsive/hostile-data hardening → measured performance optimization → small visual/motion polish → validation with rollback gates.

**Verdict:** Not production-ready for a 10,000-row operations workflow yet; preserve the existing design system, but fix save integrity, state coverage, accessibility, responsive constraints, and bounded rendering before polish.

---

## 2) Prioritized findings

### F1 — P0: Save failures are silent and recovery is undefined
- **Source evidence:** `catch {}` suppresses `api.save(product)` failures; `saving` is a single global boolean; Escape can close the drawer while save is pending.
- **Runtime hypothesis:** Users may believe inventory changes were saved when they failed, conflicted, timed out, or were interrupted.
- **Fix:** Represent save states explicitly: `idle / dirty / saving / saved / failed / conflict / retrying / offline`. Keep the draft open or confirm close while pending/failed. Surface actionable errors. Preserve local edits until acknowledged by the server.
- **Acceptance:** Failed save, timeout, offline, 409, and retry paths all leave the user with visible status, preserved edits, and a clear next action.

### F2 — P0: Required failure and recovery states are missing
- **Source evidence:** Initial/filter loading renders a blank table body; empty, 401/403, 409, 429, 500, timeout, offline, retry, and partial batch failure states are not represented.
- **Runtime hypothesis:** Operators may see a blank or stale surface and cannot distinguish “no data,” “loading,” “not allowed,” “rate limited,” or “failed.”
- **Fix:** Add state-specific table/body panels and bulk-action summaries: loading skeleton or progress, empty result copy, permission denial, auth expiry, conflict resolution, retry/backoff, offline queue notice, and partial batch result with row-level retry.
- **Acceptance:** Every listed state renders a distinct message, preserves filters/selection/drafts where appropriate, and offers the correct recovery path.

### F3 — P1: 10,000 rows render and filter work is unbounded
- **Source evidence:** `rows.map(...)` renders all rows; source notes say filtering recalculates synchronously on every keystroke.
- **Runtime hypothesis:** Input latency, memory, scroll jank, and long tasks are likely at 10,000 rows, but exact severity needs measurement.
- **Fix:** Bound visible rows via existing table virtualization/windowing, pagination, or server-side paging. Memoize filtered results. Defer or debounce keystroke filtering where acceptable. Avoid re-rendering unchanged rows.
- **Acceptance:** Mounted row count is bounded; filter input p95 and long-task budgets pass on target desktop/tablet hardware.

### F4 — P1: Tablet support conflicts with fixed layout
- **Source evidence:** `.page { min-width: 1180px; }`; fixed grid columns total substantial width; drawer is fixed `520px`.
- **Runtime hypothesis:** Tablet users may hit page-level horizontal overflow, obscured controls, or unreachable bulk/edit actions.
- **Fix:** Keep desktop density, but isolate unavoidable horizontal scroll to the table region, not the whole page. Use responsive column priorities, `minmax()`/`clamp()`, wrapping filters, and `max-width: min(520px, calc(100vw - gutter))` for the drawer.
- **Acceptance:** Critical filters, bulk actions, save/close controls, and drawer content remain reachable on supported tablet widths.

### F5 — P1: Drawer and icon controls are not accessible enough for production
- **Source evidence:** Drawer does not trap focus or block background interaction; icon-only save/close; `.icon-button` is `28px` square and `outline: none`; keyboard navigation, labels, focus-visible, and screen-reader behavior are not described.
- **Runtime hypothesis:** Keyboard and assistive-technology users can lose focus, activate background content, or encounter unnamed controls.
- **Fix:** Add dialog semantics, labelled title, focus trap, background inerting, restore focus on close, visible `:focus-visible`, accessible names for icon buttons, disabled/pending semantics, and effective tablet target size at least project standard or provisionally 44 CSS px.
- **Acceptance:** Full edit flow works by keyboard; screen-reader labels identify controls and status; focus never escapes behind an open drawer.

### F6 — P2: Hostile product data is under-specified
- **Source evidence:** Names can be 1–200 chars; prices may be missing; labels may expand 60%; images may be absent or 8MB; product name is single-line ellipsis.
- **Runtime hypothesis:** Long names, missing prices, translated labels, and absent/large images may cause ambiguity, clipping, layout shift, or upload failures.
- **Fix:** Provide full-name access in drawer/details, robust empty price display such as `—` not `0`, locale-aware formatting, flexible label widths, image placeholders, upload validation, compression guidance, and reserved image dimensions.
- **Acceptance:** 1/20/60/200-char names, missing prices, long translations, no-image rows, and 8MB uploads render predictably.

### F7 — P2: Motion may cause jank and ignores reduced motion
- **Source evidence:** `.product-row, .drawer { transition: all 300ms ease-in; }`.
- **Runtime hypothesis:** Animating `all` across many rows can accidentally animate layout/paint properties and worsen 10,000-row performance.
- **Fix:** Restrict transitions to intentional properties, preferably `transform` and `opacity`; avoid row-wide transitions unless state-specific; add `prefers-reduced-motion` handling.
- **Acceptance:** Drawer animation does not animate layout-heavy properties; reduced-motion users get a non-animated or minimal transition path.

### F8 — P3: Permission-specific affordances and autosave nuance need polish
- **Source evidence:** Permission-specific affordances are not described; autosave status exists in context but not in source behavior.
- **Runtime hypothesis:** Users may attempt unavailable edits or misunderstand whether changes are queued, saving, saved, failed, or blocked by role.
- **Fix:** Disable or hide unauthorized actions per project convention, explain why actions are unavailable, and make autosave status row/drawer-specific where possible.
- **Acceptance:** Users can tell what they may edit, what changed, what is saving, and what needs attention.

---

## 3) Concrete fix set by area

### Hostile data
- Reserve image aspect ratio and show deterministic placeholders.
- Validate large uploads before sending; show size/type errors and retry.
- Treat missing price as missing, not zero.
- Keep row density, but expose full product names in drawer/details and accessible text.
- Test translation expansion and long currency formats.

### Failures and state recovery
- Replace blank table bodies with explicit loading, empty, permission, and error states.
- Add retry semantics for timeout/500/offline; backoff messaging for 429.
- For 409, preserve local draft and show conflict resolution.
- For batch edits, summarize success/failure counts and allow row-level retry.
- Do not clear dirty state until server acknowledgement.

### Responsive layout
- Remove page-level fixed minimum as the primary tablet behavior.
- Let filters wrap and keep bulk action/status controls visible.
- Confine data overflow to the table viewport.
- Make drawer width adaptive and ensure close/save remain visible.
- Define column priority for tablet instead of shrinking every column equally.

### Accessibility
- Use real dialog behavior for the drawer.
- Add accessible names for save/close and all icon-only buttons.
- Restore visible focus styles; do not rely on `outline: none`.
- Add keyboard selection behavior for rows and bulk selection.
- Announce autosave changes through a polite live region.
- Respect reduced motion and maintain effective touch targets.

### Performance
- Establish baseline before choosing the implementation.
- Bound rows with existing project mechanisms first: virtualization, paging, or server pagination.
- Memoize derived filtered rows and avoid full recalculation on unrelated renders.
- Use deferred/debounced filtering only if it preserves the operations workflow.
- Lazy-load thumbnails and reserve dimensions.
- Replace `transition: all` with targeted transitions.

---

## 4) Static signal reconciliation

**Decisive from the provided source/facts:**
- `catch {}` hides save failures.
- Missing listed states are product-state gaps.
- `rows.map` over 10,000 rows is unbounded render work.
- Synchronous filtering on each keystroke is an input hot path.
- Fixed `min-width`, fixed columns, and fixed drawer width are responsive risks.
- Icon-only controls, no focus trap, no background inerting, and removed outline are accessibility risks.
- Missing image dimensions create layout-shift risk.
- `transition: all` is an unsafe motion/performance pattern.

**Needs project/runtime context before final severity or exact remedy:**
- Whether 10,000 rows causes release-blocking latency on target devices.
- Whether existing table primitives already provide virtualization/pagination elsewhere.
- Whether a global focus style replaces `.icon-button { outline: none; }`.
- Whether design tokens already define tablet breakpoints, target sizes, drawer widths, and motion durations.
- Whether backend APIs support conflict details, idempotency, retry-after, server filtering, or partial batch responses.
- Whether image handling is CDN-backed, preprocessed, or client-uploaded directly.

---

## 5) Measurement-first validation and rollback plan

### Baseline before changes
- Measure initial render, filter keystroke latency, scroll smoothness, drawer open/close, save failure paths, image load/layout shift, and mounted DOM row count using the real 10,000-row fixture.
- Cover desktop and supported tablet widths.
- Include normal, empty, long-name, missing-price, absent-image, 8MB-image, unauthorized, conflict, offline, timeout, 429, 500, and partial batch scenarios.

### Provisional acceptance gates, to be ratified by the project
- Filter input p95: ≤100–150 ms on target hardware.
- No individual long task over 50 ms during filtering, scrolling, or drawer open/close.
- Mounted rows bounded to visible rows plus overscan, or page size explicitly capped.
- CLS after image loading: <0.1.
- Drawer open/close must not block input or animate layout-heavy properties.
- Keyboard-only user can filter, select, edit, save, recover from failure, and close safely.
- Save failures must never be silent; edits remain recoverable.
- Tablet viewport keeps critical actions reachable without page-level unusable overflow.

### Rollback conditions
- Revert or feature-flag any table optimization that breaks selection, row identity, keyboard navigation, sticky bulk actions, or edit-drawer ownership.
- Revert any save-state change that drops drafts, duplicates saves, or hides conflicts.
- Revert motion changes that regress reduced-motion behavior or introduce layout jank.
- Do not ship visual polish if P0/P1 correctness, accessibility, and bounded-work gates remain unresolved.
