# System consistency review

Use this reference to prevent a locally correct UI change from shipping with a
different visual or interaction language than the product around it. It defines
the lightweight completion gate for every visible UI change and the full
`system-review` mode for project-level consistency work.

This is a review and sign-off contract, not a new aesthetic. Project authority,
semantic roles, and live runtime evidence remain primary. Consistency does not
mean forcing unlike controls to look identical.

## Contents

- [When to use each gate](#when-to-use-each-gate)
- [Lightweight completion gate](#lightweight-completion-gate)
- [Full system review workflow](#full-system-review-workflow)
- [Component primitive boundary](#component-primitive-boundary)
- [Reference fidelity matrix](#reference-fidelity-matrix)
- [State and theme matrix](#state-and-theme-matrix)
- [Browser-native surface consistency](#browser-native-surface-consistency)
- [Finding ledger](#finding-ledger)
- [Post-fix verdict](#post-fix-verdict)
- [Sign-off status](#sign-off-status)
- [Route integration](#route-integration)
- [False-pass guards](#false-pass-guards)

## When to use each gate

Run the lightweight completion gate before delivering every visible UI change.
It applies to micro, component, section, page, and multi-page work whenever the
change affects rendered appearance or interaction feedback.

Run the full `system-review` mode when any of these conditions is true:

- the review covers a whole product, multiple pages, or multiple routes;
- the change evolves a design system, visual language, interaction system, or
  motion system;
- the change spans multiple semantic component families or shared primitives;
- a visual-language or interaction-language inconsistency has already escaped
  an earlier review;
- the user explicitly asks for an overall, project-level, or system-level
  review.

A component or section change normally uses only the lightweight gate. Escalate
it to a full review when an observed regression or shared-system impact makes a
local comparison insufficient.

## Lightweight completion gate

Before delivery, record the smallest evidence set that answers all applicable
questions:

1. **Authority:** Which `DESIGN.md`, token layer, shared component, or verified
   runtime pattern governs the changed control?
2. **Semantic family:** What job and family does the control belong to? Examples
   include primary action, compact utility action, selection control, field,
   tab, disclosure, menu trigger, or status indicator.
3. **Exemplar:** Which existing project instance is the correct comparison
   baseline? Do not use the newly changed instance as its own exemplar.
4. **Same-state comparison:** Compare sibling or equivalent instances in the
   same applicable state rather than comparing one hovered control with another
   idle control.
5. **State coverage:** Check the applicable default/idle, hover, pressed/active,
   focus-visible, open/selected, disabled, loading/pending, invalid, and
   destructive states.
6. **Theme coverage:** When the project supports multiple themes, compare the
   touched family and states in Light and Dark or the project's equivalent
   themes.
7. **Rendered review:** When the route requires browser/native or screenshot
   evidence, inspect that real rendered result. Attaching the artifact is not
   itself a critique.
8. **Reference fidelity:** When an approved comp, screenshot, or reference is
   authoritative, inventory its salient elements directly before reading a
   builder-authored summary. Classify every applicable element with the
   fidelity matrix below; preserving only palette or mood is not fidelity.
9. **Closeout:** Record unresolved findings and finish with `pass`, `blocked`,
   or `incomplete` using the status rules below.

Classify semantics before judging similarity. Controls in the same family and
priority should share the project's component grammar unless authority records
an intentional variant. Controls in different families may legitimately use
different fills or shapes, but shared toolbar alignment, density, focus
visibility, optical size, and interaction feedback should still form one
coherent system.

## Full system review workflow

### 1. Declare scope, authority, and evidence

State:

- the product, route, surface, or component boundary in scope;
- excluded or deferred surfaces;
- product and style authority, including any documented exceptions;
- runtime, screenshot, DOM/computed-style, source, and test evidence actually
  available;
- themes, viewports, input modes, and platforms covered or unverified.

Do not silently treat one representative route as whole-product coverage.

### 2. Inventory authoritative references directly

When the task has an approved comp, screenshot, design file, or other visual
reference, inspect it before reading the implementation summary. Record its
salient topology, reading order, focal scale, density, type relationships,
signature geometry, material/asset medium, icons, controls, overlaps, and
interaction implications in your own words. A builder-authored contract or
summary is useful context, but it is a lossy abstraction and cannot replace
direct reference inspection.

Classify the rendered result with the reference fidelity matrix below. An
adaptation is acceptable only when it cites accessibility, responsive
behavior, product truth, platform convention, technical safety, or explicit
user approval. An uncited deviation is a finding. If no authoritative visual
reference exists, mark this step `not_applicable`; do not manufacture one.

### 3. Build a surface inventory

List each in-scope route or major surface with its primary job, representative
state, theme coverage, and evidence source. Mark every entry as reviewed,
deferred, or unavailable. Select representative surfaces by real component and
interaction coverage, not visual convenience.

### 4. Build a semantic component-family inventory

For every repeated interactive or visual family, record:

- semantic role and user job;
- canonical project exemplar and authority source;
- shared primitive or owning component when known;
- sizes, variants, and priority levels;
- routes or surfaces where it appears;
- intentional exceptions and their rationale.

Compare like with like. A checkbox and a primary action do not need identical
appearance, but two compact utility actions should not drift into unrelated
shape, density, focus, and feedback grammars without an explicit reason.

### 5. Build an interaction-pattern inventory

Record repeated patterns such as navigation, selection, disclosure, menus,
dialogs, inline editing, drag/direct manipulation, submission, optimistic work,
loading, errors, and recovery. For each pattern, compare trigger, feedback,
keyboard or assistive behavior, pending state, cancellation, and recovery.

### 6. Review the four systems

Use one finding ledger across these dimensions:

- **Visual system:** tokens, typography roles, spacing rhythm, radii, borders,
  elevation, icon sizing, density, alignment, and responsive composition.
- **Visual language:** hierarchy, emphasis, restraint, brand character,
  semantic color, family resemblance, and intentional exceptions.
- **Interaction system:** affordance, trigger behavior, feedback, focus,
  keyboard/input parity, async ownership, errors, and recovery.
- **Motion system:** purpose, duration/easing, origin, interruption, reduced
  motion, and cohesion across equivalent transitions.

Do not duplicate one issue across dimensions. Record it once and reference its
finding ID from the other relevant sections.

### 7. Complete the state and theme matrix

Use the matrix contract below for each important component family. A source
branch proves that a state exists; rendered evidence is required to prove its
appearance and visual relationship when the route requires runtime review.

### 8. Reconcile findings and verify fixes

Assign P0/P1/P2/P3 using the existing review severity contract. Reconcile
scanner findings as confirmed, dismissed with evidence, or still unverified.
When fixes were applied, run the post-fix verdict below against the original
finding IDs rather than opening an unrelated new defect hunt. Then emit exactly
one final status.

## Component primitive boundary

Primitive-library consistency cannot substitute for visual-system consistency.
One shared library can still produce divergent semantic families, typography,
density, tokens, states, themes, focus treatment, icons, feedback, and motion.
Conversely, project-owned wrappers over more than one internal primitive can be
coherent when project authority deliberately owns the differences.

Do not treat a visual-language finding as evidence that the project must move
between Radix UI, Base UI, React Aria, Ark UI, or another primitive. First trace
the mismatch through the shared component, variant, token, semantic family,
state/theme matrix, interaction contract, and finding ledger. Load
`component-primitive-selection.md` only when the task explicitly selects or
migrates a library, or when evidence traces an unresolved blocker to the
primitive contract. Then record `keep | adopt | migrate | defer` and the
required architecture evidence.

Using one primitive library across every in-scope component is architecture
evidence, not visual acceptance and not a `pass` signal. Library adoption or
migration also does not close the original system-review findings; verify them
against the same exemplars, states, themes, surfaces, and finding IDs.

## Reference fidelity matrix

Use one row per salient reference element. Add project-specific evidence fields
when needed.

| Reference element | Observed result | Classification | Adaptation evidence | Finding ID |
| --- | --- | --- | --- | --- |

`Classification` must be exactly one of:

- `match`: the result preserves the reference commitment;
- `acceptable_adaptation`: the difference is required by cited accessibility,
  responsive, product, platform, safety, or user-approved evidence;
- `missing`: a salient reference element is absent;
- `contradicted`: the result replaces or reverses the reference commitment;
- `added_without_approval`: the result introduces a new compositional or
  interaction commitment without authority.

Fidelity is not pixel tracing. Semantic HTML, responsive reflow, accessible
controls, platform adaptation, and safe implementation may translate a
reference. They do not authorize silent recomposition, a different type
character, removal of signature material, or a second visual direction.

## State and theme matrix

Use one row per semantic family and variant. Add only project-relevant states,
themes, viewports, and input modes.

| Family / variant | Exemplar | Default | Hover | Pressed / active | Focus-visible | Open / selected | Disabled | Loading / pending | Light | Dark | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Each cell must be one of:

- `verified`: the required evidence was actually reviewed;
- `not_applicable`: the platform or semantic role does not expose that state;
- `unverified`: the state applies but the required evidence is missing;
- a finding ID such as `F-02`: reviewed and inconsistent.

For native targets, replace web-only hover/focus language with the applicable
pressed, selected, keyboard/D-pad focus, VoiceOver/TalkBack, Dynamic Type, and
font-scale states. Do not mark unsupported web states as failures.

## Browser-native surface consistency

When these surfaces are visible and project authority styles them, include
them in the relevant component/state matrix:

- keyboard focus ring or other visible focus treatment;
- text selection highlight;
- editable-text caret;
- link underline thickness and offset;
- numeric alignment such as tabular numerals in changing metrics;
- scrollbars when the product deliberately owns their appearance.

Visible focus is a required accessibility state for keyboard-operable web
controls. The other surfaces are conditional: inspect them when the product,
browser matrix, or changed component makes them relevant.
Browser defaults are not automatically defects.
This contract does not require universal custom selection, caret, underline,
numeral, or scrollbar styling.
Compare supported browsers and platforms only when the declared scope claims
that coverage.

## Finding ledger

Use one compact ledger for the entire review:

| ID | Severity | Scope | Family / pattern | State / theme | Authority and evidence | Finding | Required resolution | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

Each finding must distinguish:

- the authority or exemplar that establishes the expected system;
- the observed mismatch;
- whether it is confirmed in runtime, inferred from source, or still a
  hypothesis;
- the minimum system-level resolution and how it will be verified.

Do not create a second numeric score for this review. Product UI Taste Score,
source completeness, and release maturity retain their existing meanings.

## Post-fix verdict

After a fix batch, recapture or re-observe the same decisive routes, viewports,
states, themes, and reference elements used by the original findings. Score
each original finding exactly once:

| Finding ID | Verdict | Evidence | Regression IDs |
| --- | --- | --- | --- |

`Verdict` must be `resolved`, `partial`, or `unresolved`. Verification returns
to the original ledger; it does not restart an unbounded review or accept a
builder's assertion that the issue was fixed. Record only regressions caused by
the fix batch, assign them new finding IDs, and keep them in the same ledger.

Any P0/P1 finding with a `partial` or `unresolved` verdict remains blocking.
Missing required post-fix evidence makes the review `incomplete` unless a known
blocker already determines `blocked`.

## Sign-off status

Finish the lightweight gate and full review with exactly one status:

- `pass`: required scope, state, theme, and runtime evidence is complete enough
  for the claimed coverage, and no P0/P1 finding remains unresolved.
- `blocked`: a confirmed unresolved P0/P1 exists within the delivery scope. A
  known blocker remains blocking even if secondary evidence is also missing.
- `incomplete`: no confirmed blocker currently determines the outcome, but
  missing authority, surface, runtime, state, theme, or platform evidence makes
  a pass claim unsafe.

P2/P3 findings may accompany `pass` only when they are explicitly recorded as
accepted follow-up and do not contradict the project's release policy. Never
convert `incomplete` to `pass` because automation exited successfully.

## Route integration

Consume the host route contract rather than inventing a parallel trigger:

- `visual_review_mode=baseline_only`: run a baseline critique or shape pass;
- `visual_review_mode=before_after`: record the baseline before implementation,
  then run the lightweight completion gate on the final rendered result;
- `visual_review_mode=final_only`: run the lightweight completion gate after
  final capture and before delivery;
- `final_visual_review_required=true`: the final gate is mandatory;
- `visual_review_blocks_delivery=true`: unresolved route blocking severities
  prevent completion.

When a full-review trigger also applies, the full `system-review` satisfies the
final stage only if its declared scope includes the changed surface and its
required evidence. Route planning does not prove that either review stage ran.

## False-pass guards

The following evidence is useful but cannot independently produce `pass`:

- a screenshot was attached or a capture command succeeded;
- target size, panel height, overflow, or other geometry assertions passed;
- default-state border, background, or computed-style checks passed;
- CSS, focus, token, or detector scanners returned no findings;
- the changed component matches itself or only its source-level tokens;
- one theme, viewport, or idle state was reviewed while another applicable
  state remains unverified;
- automated tests passed without a required browser/native visual judgment;
- every in-scope component imports the same primitive library;
- a visual inconsistency exists but no primitive-level blocker is confirmed.

Stop at the earliest missing decisive evidence. Do not broaden into unrelated
personal data, routes, or projects merely to make the inventory look complete.
