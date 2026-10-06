# Jakub Krehel skills: candidate reference review

Decision: use `jakubkrehel/skills` as a **fixed selective reference** for the
writing and component-scenario instructions below. Remaining entrypoints stay
candidates. This is not a whole-upstream absorption-complete claim or a runtime
dependency. It is now registered as the fourth pristine submodule for automated
freshness checks; registration does not expand the reviewed or adopted scope.

## Source and evidence boundary

- Review date: 2026-09-05.
- Upstream: <https://github.com/jakubkrehel/skills>.
- Resolved revision: `267330e1adfc66a718fb65fa6918c1f06d0a689e`.
- Local comparison revision: `ab2b06b49062e221ead725516dc4e0e3410802e5`;
  worktree clean before this documentation change.
- Source inventory: 65 files, 274,820 bytes; 11 Skill entrypoints,
  35 supporting Markdown files, 11 `agents/openai.yaml` files and eight
  repository/plugin/configuration files.
- Acquisition: repository-external temporary snapshot fetched at the resolved
  revision. All 65 files matched the Git blob IDs in that revision's tree.
  No upstream scripts, plugin commands or installation instructions ran.
- Review depth: entrypoint-level suitability screening across all 11 Skills;
  detailed comparison of `better-writing/SKILL.md`, `break/SKILL.md` and
  `break/scenarios.md`. Other supporting references are not fully reviewed.
- License inspected: MIT, copyright 2026 Jakub Krehel. Future copied or
  substantially adapted material must preserve the applicable notice and
  license in the repository/package attribution boundary.

The snapshot is disposable working evidence. Durable provenance is the fixed
revision, source paths and hashes below; no local temporary path is required
to interpret this decision.

| Priority source | SHA-256 |
| --- | --- |
| `skills/better-writing/SKILL.md` | `d53163382a058f06e00ac0b36312189108b006aa0b05869c71a70f5c213c44ae` |
| `skills/break/SKILL.md` | `4b8a1d6b60c2d522432765ab90e9b794fa36dc54f08d1a734c5cb2a1baa69ff1` |
| `skills/break/scenarios.md` | `5aacf085d5eca87b7b5e4f1b0a7412bfd532c8eaa574f455a5b1ffb00cdf86e9` |
| `LICENSE` | `ed1dfe988fc40511b4845ccd9050a143a2002fee3bedc8064c47fa342b5d8d4f` |

Source links below remain bound to this revision. The matrix is a human
assessment, not a second machine-readable lock or validator input.

## Priority comparison: product writing

Source: [better-writing](https://github.com/jakubkrehel/skills/blob/267330e1adfc66a718fb65fa6918c1f06d0a689e/skills/better-writing/SKILL.md).

Existing [voice and content rules](../skills/design-craft/references/design-system-contract.md#voice-and-content)
already require action/object labels, recovery instructions, useful empty
states and descriptive loading states. Repeating those would add little.

The useful candidate delta is more specific:

- Preserve one vocabulary across a flow and its menus, dialogs and toasts;
  adapt tone to consequences without inventing a new product voice.
- Describe a toggle's enabled behavior so its inverse remains understandable.
- Use complete localized message templates, including plural handling, rather
  than assembling sentences around variables.
- Keep persistent guidance outside empty states that disappear once populated;
  distinguish an empty collection from a filtered search with no matches.
- Make links understandable independently and keep placeholders subordinate
  to persistent labels.

Implemented destination: the existing voice/content section now carries the
selected missing behavior. No parallel writing authority or standalone
automatically loaded Skill was created.

Adaptation constraints: language-specific casing and English verb ordering
must remain conditional. Error recovery must describe the actual validation
or failure cause; examples such as restricting names to letters are not
general product requirements. Source inspection can verify terminology and
templates, but it cannot prove rendered truncation, announcement behavior or
translation fit. Those retain the applicable runtime checks.

## Priority comparison: component stress scenarios

Sources: [break](https://github.com/jakubkrehel/skills/blob/267330e1adfc66a718fb65fa6918c1f06d0a689e/skills/break/SKILL.md)
and [scenario axes](https://github.com/jakubkrehel/skills/blob/267330e1adfc66a718fb65fa6918c1f06d0a689e/skills/break/scenarios.md).

The existing [harden workflow](../skills/design-craft/references/impeccable-workflow.md)
already covers long content, localization, empty/error/loading states,
permissions, offline behavior and overflow. The useful delta is a small
inspection surface: import a real component, feed explicit local fixtures,
label each applicable case and place observed failures beside their cases.

Select cases from actual inputs and supported states. Record why an axis is
included or excluded. Relevant axes include text length and script, item
count, available container space, component states and supported environments.
Observed failures and untested cases must remain distinguishable.

Implemented destination: the conditional component scenario inspection
subsection owned by `harden`. It reuses existing stories or preview
infrastructure where available. No new CLI, browser manager, persistent fixture
database or default all-component sweep was added.

Adaptations included in the local instructions:

1. Keep real component code, tokens, fonts and relevant providers. Use isolated
   fixture data and prevent requests or writes to production services.
2. Preserve the framework's actual server/client boundary. Do not universally
   mark the page as a Client Component or assume that this fixes empty props.
3. Fixed container widths prove container behavior only. Media queries,
   viewport units, zoom and device input require their corresponding runtime
   conditions; a 320px container is not a 320px viewport receipt.
4. Replace the upstream one-look/no-browser-launch budget with existing
   browser67 ownership and evidence rules. Unobserved scenarios remain
   unverified; a URL handed to the user is not a passed inspection.
5. Test supported themes and interaction states through their real mechanisms.
   Keep follow-up verification proportional to failures or changed inputs.
6. Bound fixture scale by actual product limits; a tenfold item count is an
   input idea, not a performance benchmark or permission for costly traffic.
7. Use the project's isolated preview ownership and cleanup policy. A report
   does not require an indefinitely running process.

## Entrypoint suitability screening

All paths below are under `skills/` at the resolved upstream revision.
`selected instructions` means incorporated source guidance; runtime coverage
is reported separately in the bounded evaluation below. `candidate delta`
means proposed future work; `overlap` means the local capability predates this
review, not that Jakub's source was absorbed.

| Entrypoint | Disposition | Local destination / rationale |
| --- | --- | --- |
| `better-writing` | selected instructions | Existing voice/content contract; detailed comparison above. |
| `break` | selected instructions | Existing `harden` workflow; detailed comparison above. |
| `variant` | overlap; optional delta | `prototype-workflow.md` already has named axes, invariants, realistic context and selection/promotion gates. A single shared comparison axis can help a bounded experiment, but should not replace broader direction exploration. |
| `better-typography` | overlap; defer recipes | `design-system-contract.md` already covers role-based typography, optical sizing, tracking, leading and numeric alignment. Inspect specific auxiliary recipes before adding anything. |
| `better-colors` | overlap; defer recipes | Existing semantic tokens, theme parity and contrast requirements; no second palette authority or migration to a preferred color notation. |
| `better-layout` | overlap; defer recipes | Existing layout rhythm, adaptive behavior and edge-state checks; pseudo-localization is a possible targeted follow-up. |
| `better-accessibility` | overlap; defer recipes | Existing keyboard, focus, labels, motion and platform quality rules. Check applicable standards and exceptions before importing thresholds or form policies. |
| `better-ui` | selective reference only | Optical alignment and surface/motion details are useful examples. Fixed animation values cannot override project tokens or verified interaction needs. |
| `better-interface` | overlap; orchestration excluded | Existing audit/critique/system-review flows own coverage, severity and evidence. Do not require loading six external Skills or asking the user to invoke another entrypoint. |
| `interface-review` | candidate methodology; defer integration | Introduced/regression/pre-existing classification and removed-code inspection merit comparison with existing review ownership. Do not copy fixed consumer/finding caps or create a competing review engine. |
| `explain-interface` | overlap; runtime excluded | `reference-workflow.md` already separates source, rendered observations and transferable mechanisms. No upstream MCP installation or browser substitution. |

Entrypoints are available in the [fixed source tree](https://github.com/jakubkrehel/skills/tree/267330e1adfc66a718fb65fa6918c1f06d0a689e/skills).
Plugin metadata, host YAML, repository instructions and other supporting files
are inventoried only and excluded from behavioral adoption in this decision.

## Rules not to import as defaults

- Exact global motion recipes such as `scale(0.96)`, fixed icon blur/spring
  values, or unconditional root font smoothing.
- Fixed hue-distance, spacing-ratio or typography values as universal defects
  independent of the product, language, font or accessibility requirement.
- Global transition suppression or forced reflow without examining existing
  theme ownership and performance behavior.
- Upstream severity ladders, finding caps, user-invoked handoffs or installation
  commands as replacements for local authority and authorization.
- A real-page variant picker that changes production wiring before selection,
  or a fixed picker theme that overrides the project's preview conventions.
- A screenshot-derived color pair as proof of live accessibility compliance.

These are adaptation decisions, not claims that every upstream recipe is
incorrect in its original context.

## Admission and completion boundary

Assessment is complete at the stated depth. The selected writing and scenario
instructions are implemented in the canonical Skill references, with source
mapping and MIT attribution. Other supporting-reference audit and real-project
validation remain outstanding before any broader absorption-complete claim.

Examples for applying the new guidance (acceptance expectations, not runtime
test receipts):

- A localized receipt toggle should describe the enabled action consistently
  in its label and toast. A count message should use the project's complete
  plural-aware template rather than concatenated translated fragments.
- A filtered project list should offer a relevant filter/query exit. Persistent
  account instructions belong outside the empty-list branch.
- A card consuming user titles and optional metadata warrants long/unbreakable
  title and missing-metadata fixtures. It does not acquire a loading prop merely
  because loading appears in a generic scenario list.
- A component using viewport media queries needs an actual viewport check in
  addition to narrow-container fixtures. A server component keeps its server
  boundary and dependencies in the preview. Unavailable runtime evidence is
  recorded as unverified even if the preview compiles.

A [bounded real-component Shadow Lab observation](../evals/jakub-component-shadow-2026-09-05.md)
now records actual browser67 rendering and keyboard evidence on myblog's fixed
AnimeCard source. It found fixture clipping and Space activation failures while
preserving the original project. Coverage remains partial: this was main-agent
application, not independent Host testing or full writing-flow validation.
Older source-bound host/comparative/native receipts are not reused as proof.

## Formal tracking

Registered on 2026-09-05 at the same reviewed revision under
`upstreams/jakubkrehel-skills`, with `selective_absorbed` cumulative status.
The initial snapshot uses equal latest-range base/head; this records an initial
review, not a claim that an empty diff supplied the adopted behavior.
`upstreams.lock.json` owns the inventory, partial/deferred decisions, selected
source hashes, and local mappings; this document remains the human rationale.

`make jakub-absorption-check` verifies that contract and participates in
`make upstream-absorption-check`. The shared report and scheduled audit discover
the new lock entry automatically. Review future changes by relevant source
paths/content as well as revision; README or host metadata churn does not imply
changed design behavior. Synchronizing a pin never advances review or absorption
metadata automatically.

Global route-pack writes, installation, push and release remain separate actions.
