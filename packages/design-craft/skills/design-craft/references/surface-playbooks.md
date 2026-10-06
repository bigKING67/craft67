# Surface playbooks

Use this to avoid applying the wrong aesthetic to the wrong surface.

## Contents

- [Choose the surface mode](#choose-the-surface-mode)
- [Landing or brand page](#landing-or-brand-page)
- [Dashboard or admin app](#dashboard-or-admin-app)
- [Persistent agent workspace](#persistent-agent-workspace)
- [Data visualization](#data-visualization)
- [Static or special report](#static-or-special-report)
- [Mobile flow](#mobile-flow)
- [Mobile Web platform behavior](#mobile-web-platform-behavior)
- [Native phone or tablet app](#native-phone-or-tablet-app)
- [Forms and settings](#forms-and-settings)
- [Existing redesign](#existing-redesign)

## Choose the surface mode

Choose the mode from the current surface, not the product's category or brand:

- `Persuade`: the visitor must understand, decide, and act. Landing, campaign,
  pricing, and marketing surfaces belong here.
- `Operate`: the user must complete or monitor a task. Apps, dashboards,
  editors, admin, settings, and tools belong here.
- `Read`: the reader must understand structured information. Documentation,
  articles, guides, help, changelogs, and evidence-heavy reports belong here.
- `Experience`: the work itself is the destination. Portfolios, galleries, and
  showcases belong here; the interface should recede behind the artifact.

A developer tool's landing page is still `Persuade`; a fashion brand's guide
is still `Read`. Persist the choice only for the surface being designed.

## Landing or brand page

Primary job: persuade, explain, convert, or establish taste.

- Strong design read is mandatory.
- Visual hierarchy can be expressive.
- Use proof, contrast, rhythm, and memorable sections.
- Avoid generic hero + three cards + testimonial grid.
- Browser verification should cover desktop and mobile.

## Dashboard or admin app

Primary job: monitor, compare, operate, decide.

- Information architecture beats visual drama.
- Density should be purposeful, not sparse by default.
- Tables need scanning, sorting/filtering, empty/loading/error states.
- Charts need correct scales, labels, legends, tooltips, and responsive behavior.
- Motion should be quiet and state-oriented.

## Persistent agent workspace

Primary job: delegate work, understand its progress, and retain control.

An AI marketing page or ordinary chat input alone does not trigger this
playbook.

Use for product surfaces where delegated work outlives a single response,
users supervise computer actions, or routines run later. Apply only supported
capabilities; this reference does not require adding agents, scheduling,
computer control, or a new execution architecture.

### Start from the user's responsibility

Identify what users return to manage: a project, task, workspace, conversation,
or durable agent role. Preserve established product authority and navigation
unless the task authorizes a change supported by user needs. A bot roster is
useful only when durable roles are the user's organizing concept; it does not
replace the product's session or workspace source of truth.

Reuse [product-design-principles.md](product-design-principles.md) for agency
and feedback, and [motion-quality.md](motion-quality.md) for motion behavior.
Apply the following decisions to the affected flow, not every product screen.

### Truthful progress

- Map user-facing status to actual execution events. Distinguish active work,
  waiting for input, waiting for authorization, a blocking condition, failure,
  cancellation, and completion where those states exist. Use product-native
  names; a new backend state enum is not required.
- A spinner is not evidence of activity. If observation is disconnected or
  stale, communicate that uncertainty rather than declaring the task running,
  failed, or complete without evidence. Separate the last observed action from
  the current connection state.
- Show a compact status and the next action needed from the user, if any.
  Offer current-action detail and expandable execution records when useful.
  Report observed actions and outcomes, not fabricated internal reasoning or
  invented percentage progress.
- Make essential detail reachable by keyboard and touch, not only hover.
  Motion may reinforce a state but cannot be its only indicator; reduced
  motion must preserve the same information.

### Observe, take control, return control

- When computer control exists, distinguish a status summary, an inspection
  preview, and interactive control as needed. Opening a preview must not
  silently transfer ownership or grant execution permission.
- Identify the affected environment and current controller. Make takeover and
  return explicit, and reflect acknowledged runtime transitions. Do not show
  control as transferred merely because the user clicked a button; pending,
  rejected, and interrupted transfers need honest feedback.
- Prevent the interface from implying simultaneous independent control when
  the runtime cannot support it. If ownership enforcement is missing, report
  that implementation gap; a visual label cannot prove safe handoff.
- Keep task scope and existing authorization boundaries visible where users
  decide. Returning control does not grant permission for a new operation.

### Results that fit the task

- Choose prose, a table, a review card, a visualization, or a document from the
  user's next decision. Avoid converting every response into a card.
- Separate a proposed action or draft from approval, execution, and confirmed
  outcome. A successful tool invocation alone does not prove the user's goal
  succeeded; show partial results and failures where they affect the decision.
- Let users reopen durable outputs and connect them to their producing task
  or run. Avoid making a long transcript the only way to find a deliverable.
- Preserve action context across retries: show which attempt a result belongs
  to and avoid presenting an earlier failure as the current result. Retrying
  must respect existing authorization and duplicate-effect constraints.

### Recurring work, when supported

Expose responsibility, schedule or event trigger, relevant timezone, next
scheduled run when applicable, latest result, pause state, and exceptions that
need attention. Distinguish pausing future runs from stopping a current run.
Do not infer shared memory, tool permissions, or autonomous coordination from
the presence of several agent identities.

### Acceptance in the affected product

Choose checks for the changed capabilities; use the existing
[validation-contract.md](validation-contract.md) evidence levels. For example:

- An authorization wait stops looking like active execution and exposes the
  relevant decision; a disconnected observer does not falsely mark completion.
- A control transfer shows its pending and acknowledged states; returning
  control restores the supported workflow without implying broader permission.
- A user can distinguish a draft from an executed result and reopen the output
  after leaving the conversation; a retry retains attempt-specific outcomes.
- Essential status is understandable with reduced motion and accessible without
  hover; a paused routine clearly explains what happens to an in-flight run.

Source review or a mockup can establish intended behavior, not prove live
execution, ownership enforcement, or usability. Mark unobserved behavior as
unverified rather than treating a checklist as runtime evidence.

### Design case source and limits

Informed by xAI's [Designing Grok Bot for a world of persistent agents](https://x.ai/news/designing-grok-bot)
(September 3, 2026; reviewed September 5, 2026), particularly its treatment of
persistent responsibility, layered supervision, and task-shaped information.
The operational checks above are Design Craft's own application of those
ideas. The article is a vendor design account, not independent usability or
runtime validation. It supplies no authority to copy brand assets, prescribe
bot counts or avatar styles, or replace local architecture and permissions.

## Data visualization

Primary job: reveal a comparison, trend, composition, distribution, or anomaly.

- Keep the requested deliverable honest: a chart request stays a chart request;
  analysis alone does not imply a complete report. Use the report mode only
  when the user asks for a structured narrative deliverable.
- Pick the chart from the analytical question and data shape, not decoration,
  a gallery category, or the chart library's most convenient example.
- Count charts by independent conclusions, not available columns or template
  slots. Remove repeated views that make the same point.
- Prefer the simplest familiar encoding that preserves magnitude, order, and
  uncertainty. For ambiguous or high-consequence choices, compare two or three
  candidates on encoding truth, label density, reading time, and interaction
  need; do not force this ceremony for an obvious simple choice.
- Preserve project `DESIGN.md`, existing component/library choices, and runtime
  constraints as authority over external chart galleries.
- Keep tables as supporting evidence when charts can carry the story.
- Use accessible color ramps and direct labels where possible; color must not
  be the only cue for series, state, direction, or selection.
- Verify tooltip overflow, legend wrapping, and small viewport readability.
- For report composition and encoding-integrity checks, also read
  `references/report-quality.md`.

## Static or special report

Primary job: guide reading and decision-making.

- Use formal report grammar: clear cover, executive summary, section hierarchy,
  chart-first evidence, quiet navigation, footnote-sized caveats.
- For dashboard exports, business-review pages, and evidence-heavy report
  surfaces, also read `references/report-quality.md`.
- Avoid dashboard hero treatments, heavy rounded cards, decorative section
  banners, and giant tables as the main narrative.
- Every chart should answer a question; every table should justify its weight.
- Caveats belong in footnotes or hover/title when they are secondary.

## Mobile flow

Primary job: complete one task under interruption.

- Resolve whether the surface is mobile web, iOS, Android, or adaptive before
  choosing controls. `surface=mobile` alone is not a native signal.
- Mobile web touch targets should normally be at least 44 CSS px. Native iOS
  uses at least `44pt`; Android uses at least `48dp`.
- Prefer simple flows, visible progress, and forgiving errors.
- Avoid hover-only behavior.
- Test long labels and keyboard viewport behavior.
- For iOS, Android, or adaptive targets, read the matching platform reference
  and verify system navigation, insets, text scaling, screen reader order, and
  runtime gesture behavior.

## Mobile Web platform behavior

Load for a Web/PWA flow with viewport, keyboard, safe-area, touch, scrolling or
browser-chrome symptoms. Keep `platform=web`; this does not select native iOS,
Android or React Native guidance. Ordinary responsive spacing alone does not
require this reference. Project components, browser support and observed
behavior govern each change; there is no global mobile reset to install.

### Viewport and keyboard

- Choose height behavior from the surface: `svh` provides a stable small-viewport
  baseline; `dvh` tracks dynamic browser UI and may resize content during scroll.
  Neither guarantees that long content fits. Prefer minimum height and reachable
  overflow for documents; constrain an app shell only when it owns scrolling.
  Retain fallbacks only for the project's supported browsers.
- Distinguish layout viewport from visual viewport before repairing a keyboard
  overlap. `dvh` alone does not prove keyboard avoidance. In supporting browsers,
  `interactive-widget=resizes-content` opts into layout-viewport resizing;
  it is not a cross-browser default or a guarantee for embedded WebViews.
  Use the existing framework's keyboard strategy; add VisualViewport handling
  only for a demonstrated gap, with listener cleanup and no double compensation.
- Keep focused inputs, validation messages and the submit action reachable when
  the keyboard opens, after dismissal and in landscape. A smaller emulated
  viewport tests reflow, not a real software keyboard.

### Safe areas and theme

- Use `viewport-fit=cover` only for an intended edge-to-edge layout. Apply
  `env(safe-area-inset-*, 0px)` to exposed controls and content, retaining the
  normal spacing token (add or take the maximum as the layout requires).
  Avoid counting the same inset in both a parent shell and its child bar.
  Safe-area padding is not keyboard avoidance; zero desktop insets do not prove
  notched-device correctness. Test browser and standalone modes when shipped.
- Root canvas and active theme follow `design-system-contract.md`. Browser
  chrome, manifest colors and platform-specific status-bar settings have
  different support and lifecycle behavior; inspect the supported target rather
  than promising that one `theme-color` changes all of them.

### Input and gesture ownership

- Keep content and actions reachable without hover. Gate optional hover effects
  by input capability, not viewport width or user-agent strings; do not assume
  mouse, pen and touch are mutually exclusive. `hover`/`pointer` describe the
  primary input and do not enumerate all attached devices.
- Separate immediate press feedback from activation. Native buttons and their
  `click` semantics preserve keyboard access and release/cancel behavior.
  Pointer-down feedback must not submit, purchase or navigate early; custom
  gestures must clear feedback on cancellation and lost capture.
- Diagnose latency before prescribing `touch-action: manipulation`. It permits
  panning and pinch zoom while restricting additional gestures such as double
  tap; it is not a general repair for slow handlers or expensive rendering.
- On a custom horizontal drag surface, consider `pan-y pinch-zoom` when the
  browser should retain vertical scroll and pinch zoom. Values name browser
  permissions, not the custom gesture's direction. Ancestor declarations also
  constrain the effective behavior, and changing it after a gesture starts
  does not change that gesture. Avoid broad `touch-action: none`; preserve
  keyboard alternatives and test cross-axis scrolling. Prefer existing native
  scrolling/scroll-snap when no custom drag behavior is needed.
- Apply `overscroll-behavior` to the scroll container that owns the conflict.
  `contain` suppresses chaining while retaining local boundary effects; `none`
  suppresses those effects too. Root pull-to-refresh/navigation changes require
  a product reason; do not disable them simply to make a document feel installed.
  Check short/non-scrollable content as well as a genuinely scrollable sheet.
- Keep browser tap/long-press feedback unless equivalent scoped feedback exists.
  Do not globally remove text selection, link previews, callouts or text-size
  adjustment as a cosmetic reset. Addresses, errors and other copyable content
  must remain usable.

### Forms and evidence

- Preserve zoom. Investigate computed input font size and actual target behavior
  when focus causes unwanted zoom. A 16 CSS px input size is a candidate for
  affected Safari cases, not a reason to overwrite all project typography;
  `1rem` is not necessarily 16px. Verify on the affected browser, including
  focus, typing, blur and user text scaling.
- Match native field semantics and keyboard hints to the data: `inputmode`,
  `autocomplete`, `enterkeyhint` and suitable input types. Numeric-looking
  identifiers may need leading zeros and are not automatically number inputs.
  Keyboard hints neither validate data nor guarantee a particular keyboard.
- Report source checks, browser/emulated observations and device observations
  separately. Emulation can verify layout and selected input conditions; it
  does not establish real browser-bar motion, keyboard, notch, latency or touch
  feel. For a device-specific symptom, retain an unverified-device status until
  the affected target is observed. Do not block unrelated desktop work on that
  missing device evidence or open a LAN server merely because a recipe says so.

### Technical references

Reviewed 2026-09-19; consult the target support matrix before changing behavior:

- [MDN viewport units](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/length#relative_length_units_based_on_viewport)
- [Chrome keyboard viewport policy](https://developer.chrome.com/blog/viewport-resize-behavior)
- [WebKit safe-area guidance](https://webkit.org/blog/7929/designing-websites-for-iphone-x/)
- [Pointer Events: touch-action](https://www.w3.org/TR/pointerevents3/#the-touch-action-css-property)
- [MDN viewport metadata](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/meta/name/viewport)
- [MDN overscroll behavior](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/overscroll-behavior)

Selected upstream provenance is in `source-map.md`; its recipes are not a
second platform or visual authority.

## Native phone or tablet app

Primary job: complete the product task while preserving platform trust.

- Read `product-context.md` and resolve the platform before implementation.
- iOS reads `ios-quality.md`; Android reads `android-quality.md`; adaptive reads
  both plus `adaptive-quality.md`.
- Translate brand through system tint/color roles, typography, content, and
  motion rather than replacing navigation and controls.
- Restructure for tablets, split-screen, multi-window, orientation, or fold
  posture; never stretch a phone canvas.
- Treat simulator/emulator breadth and real-device truth as separate evidence.

## Forms and settings

Primary job: configure or submit accurately.

- Group related fields.
- Labels must be explicit.
- Help text should be local and concise.
- Error messages should say what happened and how to recover.
- Destructive actions need separation and confirmation.

## Existing redesign

Primary job: improve without breaking learned behavior.

- Audit before changing.
- Preserve brand assets, information architecture, and successful interactions
  unless the user asked for a full overhaul.
- Change one visual language at a time.
- Verify affected routes in browser.
