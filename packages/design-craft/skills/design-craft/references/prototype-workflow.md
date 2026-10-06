# Prototype divergence workflow

Use `prototype` to explore genuinely different implementations of one bounded
UI piece before any direction is promoted into production. This is an explicit
exploration mode, not an automatic detour for ordinary implementation.

Project product truth, `DESIGN.md`, tokens, accessibility, platform behavior,
and existing component conventions still bound the exploration. Divergence
tests different answers inside that world; it does not grant permission to
replace the product's visual language.

## Contents

- [Entry and scope](#entry-and-scope)
- [Recon and authority](#recon-and-authority)
- [Direction contract](#direction-contract)
- [Isolated prototype surface](#isolated-prototype-surface)
- [Runtime verification](#runtime-verification)
- [Selection and promotion](#selection-and-promotion)
- [Cleanup and delivery](#cleanup-and-delivery)
- [Failure guards](#failure-guards)

## Entry and scope

Run this mode only when the user explicitly asks to prototype, compare, explore,
or generate multiple UI directions, or when the user accepts a proposed
prototype step. Do not invoke it merely because a normal implementation has
more than one possible solution.

Explore one UI piece per run: a toast, result row, command palette, pricing
card, destructive confirmation, table control, or similarly bounded unit. If
the request names a page or product area, choose the highest-leverage piece,
state the narrower boundary, and leave the remaining pieces for separate runs.

Exploration and promotion are separate write scopes:

- exploration may add only an isolated prototype surface and its local harness;
- exploration must not edit production behavior, production routes, shared
  design-system primitives, or persistent product data;
- promotion begins only after the selection gate below.

## Recon and authority

Before naming directions, record:

- the UI piece, its user job, frequency, context, and success condition;
- stack, route conventions, styling system, motion runtime, and CSP/build
  constraints;
- `PRODUCT.md`, `DESIGN.md`, tokens, shared components, and the nearest verified
  runtime exemplars;
- realistic content ranges, states, neighboring UI, viewports, input modes,
  themes, and accessibility requirements;
- production files explicitly excluded from exploration.

If no product authority exists, state that the result is a standalone concept
and use a restrained, accessible baseline. Do not present that baseline as a
new project design system.

## Direction contract

Default to three variants. Use two when the design space is genuinely narrow;
use four or five only when the user asks or each additional direction adds a
defensible decision axis. Never pad the set to reach a count.

Before implementation, write one row per candidate:

| Direction | Primary divergence axis | Product hypothesis | What remains invariant | Cost / risk |
| --- | --- | --- | --- | --- |

Directions must differ on a named product-relevant axis such as layout,
information density, interaction model, disclosure strategy, motion model,
editing model, or personality within the approved brand range. Color swaps,
copy swaps, icon substitutions, minor spacing changes, or the same layout with
different decoration are not separate directions.

Every direction must preserve the brief, required content, product truth,
accessibility floor, project tokens unless intentionally under test, and the
same comparison context. A direction that cannot plausibly ship is not useful
divergence.

## Isolated prototype surface

Choose the smallest harness that fits the project:

- use an isolated framework route, story, preview target, or equivalent surface
  in an existing project;
- use a self-contained local document only when no project runtime exists;
- keep prototype modules out of production imports and bundles where the
  framework supports that boundary;
- do not write to real accounts, remote services, analytics, notifications, or
  production storage; use explicit local fixtures or mocked boundaries.

Render one variant at a time at usable size in realistic surrounding context.
Side-by-side postage-stamp thumbnails may be used only as navigation aids, not
as the evaluation view. Switching variants should be immediate and keyboard
operable; high-frequency comparison chrome should not add decorative motion.

The harness chrome is infrastructure, not a visual direction. Keep it minimal,
accessible, and compatible with the project/runtime. Do not copy a fixed
upstream picker, visual theme, route, query parameter, keyboard binding, or CSS
contract verbatim when it conflicts with the project, CSP, framework, or host.

Each variant must use realistic content and implement its decisive interaction,
states, focus behavior, and motion/reduced-motion behavior. Dead buttons,
`lorem ipsum`, screenshots standing in for interactive UI, or prose asking the
user to imagine behavior do not satisfy the contract.

## Runtime verification

When a runnable prototype was created, verify it in the applicable real browser
or native runtime before presenting it:

- each variant is reachable and only one evaluation view is full size;
- decisive interactions, keyboard/input behavior, focus, and recovery work;
- required themes, viewports, long content, empty/error/loading states, and
  reduced motion are covered according to the brief;
- console/runtime errors are absent or explicitly reported;
- screenshot artifacts are produced only when the route requires them.

Source, tests, a generated plan, or a static golden fixture cannot substitute
for required rendered verification. If the runtime is unavailable, finish
`incomplete`, name the exact missing evidence, and do not ask for a selection
as though the variants had been experienced.

## Selection and promotion

Present the verified comparison without preselecting a winner:

| Direction | Axis | When it wins | Cost / tradeoff | Evidence |
| --- | --- | --- | --- | --- |

Then stop at `ready_for_selection`. Promotion requires explicit user selection
or an explicit instruction made before exploration that delegates the selection
decision. Silence, a generated score, or the agent's preference is not approval.

After selection:

1. restate the chosen direction and promotion scope;
2. integrate it through existing production conventions and shared primitives;
3. remove prototype-only wiring from production imports;
4. run the normal implementation validation and the system-consistency closeout
   from `system-review.md` against project exemplars and applicable states;
5. report any deliberate authority evolution instead of silently changing the
   visual system.

## Cleanup and delivery

Delete the prototype surface after successful promotion unless the user asks to
retain it or the project has an established prototype archive. Retention must
be explicit, excluded from production bundles and navigation as appropriate,
and documented with its owner and purpose.

Before selection, report `ready_for_selection`, `blocked`, or `incomplete`.
After selection, report `promoted`, `blocked`, or `incomplete`, plus:

- isolated prototype files and production files changed in separate lists;
- direction axes and tradeoffs;
- runtime/browser/native evidence and artifacts actually observed;
- selected direction and approval source;
- cleanup status and retained prototype boundary;
- system-consistency closeout for the promoted UI.

## Failure guards

Do not claim a successful prototype round when:

- candidates differ only by color, copy, icon, or minor decoration;
- production code changed before selection;
- the harness makes the candidates look like a different product;
- variants use different content or context that prevents fair comparison;
- a variant omits the decisive interaction or accessibility state;
- all variants are shown only as reduced thumbnails;
- a picker or fixed route is copied without checking framework, CSP, or host
  constraints;
- the user has not selected or delegated a winner but production promotion
  already began;
- cleanup is asserted without inspecting the prototype boundary.
