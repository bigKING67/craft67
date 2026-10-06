# Component primitive selection

Use this reference when a task selects, adopts, replaces, or materially adapts
a headless component primitive library such as Base UI, Radix UI, React Aria,
Ark UI, Headless UI, or a project-owned equivalent. Do not load it for ordinary
component styling when the project primitive authority is already clear and no
library-level limitation is in evidence.

This is a framework-neutral decision contract, not a library ranking.
Base UI is a supported project choice.
It is conditionally applicable when project authority selects Base UI.
The Base UI-only universal prescription remains intentionally rejected.

## Contents

- [Authority and default](#authority-and-default)
- [Decision record](#decision-record)
- [Decision matrix](#decision-matrix)
- [Candidate evaluation](#candidate-evaluation)
- [Base UI application](#base-ui-application)
- [Migration gate](#migration-gate)
- [Visual-system boundary](#visual-system-boundary)
- [Validation and delivery](#validation-and-delivery)
- [False-pass guards](#false-pass-guards)

## Authority and default

Resolve the effective primitive authority from current evidence in this order:

1. explicit user or project architecture decision;
2. current package manifest, lockfile, imports, wrappers, and runtime behavior;
3. scoped `AGENTS.md`, `PRODUCT.md`, `DESIGN.md`, and architecture records;
4. measured accessibility, compatibility, performance, and maintenance needs;
5. generic library guidance.

An existing healthy project library defaults to `keep`. A newer upstream
recommendation, library popularity, or a wording-only Radix-to-Base preference
does not justify ecosystem churn. When no authority exists, compare candidates
against the product and runtime rather than silently selecting a favorite.

## Decision record

For every applicable task, record this compact decision before implementation:

```yaml
component_primitive_decision:
  current_library: Base UI | Radix UI | React Aria | Ark UI | custom | none
  authority_source: package | source | architecture | explicit_user | none
  decision: keep | adopt | migrate | defer
  decision_reason: <project-specific reason>
  evidence:
    accessibility: verified | risk | unverified | not_applicable
    keyboard_focus: verified | risk | unverified | not_applicable
    overlay_portal: verified | risk | unverified | not_applicable
    forms: verified | risk | unverified | not_applicable
    ssr_hydration: verified | risk | unverified | not_applicable
    animation_hooks: verified | risk | unverified | not_applicable
    bundle_performance: verified | risk | unverified | not_applicable
    maintenance: verified | risk | unverified | not_applicable
  migration_cost: low | medium | high | not_applicable
  rollback: <required for migrate, otherwise not_applicable>
  visual_system_impact: none | localized | system_wide | unverified
```

Do not use `adopt` or `migrate` when decisive criteria remain unverified. Use
`defer`, name the missing evidence, and provide the smallest next verification.

## Decision matrix

| Situation | Default decision | Required reasoning |
| --- | --- | --- |
| Existing library is healthy and the issue is visual inconsistency | `keep` | Repair shared components, variants, tokens, states, themes, and interaction contracts first. |
| Existing library has a confirmed product or architecture blocker | `migrate` may be considered | Bind the blocker to a target capability, migration plan, validation, and rollback. |
| New project has no primitive authority | `adopt` or `defer` | Compare candidates against actual product, stack, accessibility, and maintenance needs. |
| Project already uses Base UI | normally `keep` | Use its real APIs, state attributes, focus/overlay contracts, and origin variables. |
| Evidence is incomplete or candidates are materially tied | `defer` | Preserve optionality and state which evidence would change the decision. |

The decision applies to the declared scope. A component-level adoption does not
silently authorize a product-wide migration.

## Candidate evaluation

Compare only criteria that affect the current product. At minimum consider:

- semantic and ARIA coverage for required components;
- keyboard behavior, focus movement, restoration, and input-mode parity;
- portal, overlay, modal/non-modal, dismissal, and positioning behavior;
- controlled/uncontrolled state and form integration;
- SSR, hydration, Electron/WebView, browser, and framework compatibility;
- state attributes, CSS variables, animation hooks, and Reduced Motion support;
- bundle and runtime performance measured in the target application;
- wrapper complexity, testability, release cadence, and maintenance risk;
- migration cost, coexistence period, rollback, and visual-system impact.

A checklist is not evidence. Cite package/source/runtime observations and mark
unknowns. Do not claim one library is more accessible or faster without a
relevant version, component scope, and verification source.

## Base UI application

When current package/source evidence establishes Base UI as authority:

- use the actual Base UI component and version contract rather than generic
  pseudo-attributes;
- map Base UI state attributes and CSS variables through project tokens and
  wrappers instead of styling isolated instances;
- use the library-equivalent transform-origin and positioning data for
  trigger-anchored motion;
- verify focus, keyboard, dismissal, portal, form, and Reduced Motion behavior
  in the applicable runtime;
- keep project `DESIGN.md`, semantic families, and interaction language above
  any upstream example styling.

This conditional support is positive capability coverage. It is not permission
to migrate a Radix or custom project merely because Base UI is supported.

## Migration gate

Treat a primitive-library migration as architecture work. Before `migrate`,
require:

1. a confirmed current blocker that cannot be resolved safely in the existing
   wrapper or component layer;
2. an inventory of affected primitives, wrappers, consumers, states, themes,
   tests, and platform surfaces;
3. a current-to-target behavior matrix for focus, keyboard, overlay, forms,
   state ownership, positioning, and animation hooks;
4. an incremental coexistence or cutover plan with explicit ownership;
5. rollback criteria and a reversible boundary;
6. targeted source, accessibility, integration, browser/native, and visual
   validation appropriate to the claimed scope.

Do not hide migration inside a polish, prototype promotion, or local visual
fix. If the primitive limitation is only a hypothesis, keep the current library
and verify the hypothesis first.

## Visual-system boundary

Primitive-library consistency cannot substitute for visual-system consistency.
A single primitive library can still ship inconsistent typography, density,
tokens, geometry, state styling, theme parity, icon treatment, feedback, and
motion. Multiple internal primitives can still form a coherent product system
when project wrappers and authority deliberately own their differences.

When a visual-language regression appears, first inspect:

- shared components and real consumers;
- variants and semantic component families;
- token roles and bypasses;
- default, hover, pressed, focus, selected, disabled, pending, and error states;
- light/dark or equivalent themes;
- interaction-pattern and motion contracts;
- the original `system-review` finding ledger.

Open a library migration only when evidence traces the unresolved problem to a
primitive limitation. Using Base UI, Radix UI, or any one library across the
scope is architecture evidence, not visual acceptance and not a `pass` signal.

## Validation and delivery

Report when applicable:

- the decision record and evidence source;
- candidates considered and why any were excluded;
- wrapper/component scope and architecture impact;
- coexistence, migration, and rollback status;
- targeted accessibility, integration, performance, browser/native, and visual
  evidence actually produced;
- unresolved compatibility or maintenance risk.

For `keep`, identify the shared component, variant, token, or interaction
contract that will own the repair. For `adopt` or `migrate`, do not claim
completion from dependency installation or source compilation alone.

## False-pass guards

None of these independently justifies `adopt`, `migrate`, or visual sign-off:

- an upstream author changed a preferred-library recommendation;
- Base UI, Radix UI, or another library appears in a curated list;
- the target package installs or type-checks;
- a primitive is described as accessible without task-specific verification;
- bundle size is quoted without comparable target-build measurement;
- one demo state looks correct while applicable states or themes are missing;
- every in-scope component imports the same primitive library;
- a visual inconsistency exists but no primitive-level blocker is confirmed.
