# Gustavo Fior Craft: fixed selective reference

Decision date: 2026-09-19. Source baseline: design-craft `8762cbe`.
Reference revision: `1758451bc13c15f7b0c04fc4f22b673852425bbc`
in <https://github.com/gustavo-fior/craft> (commit dated 2026-09-17).

## Decision and provenance

Register a fixed external reference in the existing source map and notices;
do not add a submodule, dependency, automatic update job or second Skill.
Review depth is the Skill entrypoint, launch filter and four concept articles
below, with candidate screening of chart, sound and novelty articles. It is
not a full source or interactive-demo audit.

The tree contains 34 MDX concepts, but `src/lib/concepts.ts` launches seven.
The generated Skill contains those seven concepts across four references.
Article presence or frontmatter dates do not prove production availability.

README declares MIT. The inspected tree has no standalone LICENSE/NOTICE and
no upstream copyright notice is inferred. This change distributes original
instructions and an original controlled fixture, not upstream prose, snippets,
images, fonts, components or generated Skill files. Substantial copying is
deferred until the applicable license and notice can be preserved.

The following digests identify the inspected raw bytes at the fixed revision.
This is a human review record, not a second machine-readable update lock.

| Source path | SHA-256 |
| --- | --- |
| `README.md` | `ac159fd073d546d3d64acaf75bdbd5941d655ade00da045575d6d9964c07466c` |
| `skills/craft-design-engineering/SKILL.md` | `630366c9c57ac16eda597286d791e157a0b0af312e45b3d79952e3cb050773d5` |
| `src/lib/concepts.ts` | `4fe4dbeffedcb8dfba33b1a3af4c299a2a4ed3c6d053d17d33348c072482124b` |
| `content/layout/html-background.mdx` | `0f6080dc4295e9d18dc23f05654517ed984ce40b9fc67333cafbd199bde97ca0` |
| `content/layout/nested-border-radius.mdx` | `90535adf40c0a0a4b96691381a804bcb4a2d89feb2162897ad3edffddaa197b5` |
| `content/color/image-outlines.mdx` | `b26617ae7c2598e71e6561bec5806c1d824fbb821e922455df4eb81b66f70808` |
| `content/typography/optical-alignment.mdx` | `07b0b07e40e58f9a9e1c224f2dbe9cb20b2588a66329b42b1afb2e0fea510e46` |

## Selected delta

All selected behavior lives in the already-routed
`references/design-system-contract.md`; the Skill entrypoint is unchanged.

| Concept | Existing coverage | Local decision |
| --- | --- | --- |
| Document canvas | Theme tokens and parity | Add conditional root-canvas checks, body propagation exception, theme switching and preservation of platform overscroll. |
| Nested corners | General inner/outer radius relationship | Clarify measured inset including borders, zero clamp and limits for unequal/noncircular geometry. |
| Image outlines | General image/theme quality | Add optional layout-neutral media edge, theme/image calibration and separation from keyboard focus. |
| Optical alignment | Optical font sizing and numeric roles | Add actual-glyph inspection and scoped correction; preserve target/focus geometry and check applicable sizes/directions. |
| Tabular numbers, hover restraint | Already explicit | No duplicate instructions. |
| Noise | Optional visual direction | No default texture requirement. |
| Sound, live charts, curve smoothing | Candidate articles outside launch filter | Deferred; no new audio or chart dependency or guidance in this change. |

The optical-alignment article says the play icon moves left, but its CSS uses
positive `translateX(1px)`. Adopt inspection, not its contradictory direction
or any universal offset. Upstream preferred exact values never override project
tokens. No universal table-shaped review, tooling or installation rule is adopted.

Technical calibration: [CSS Backgrounds and Borders](https://www.w3.org/TR/2024/CRD-css-backgrounds-3-20240311/)
sections 2.11, 4.2 and 6.1.3 distinguish canvas propagation, corner edges and
inset-shadow paint order. A transparent root alone is not a visible bug; an
inset shadow on an image is not proof of a visible overlay above its pixels.

## Validation boundary

The original fixture under `evals/fixtures/craft-details/` provides explicit
before/after states using the same controls, content, layout and theme tokens.
Its baseline issues are deliberately seeded, not discovered production defects.
Results are recorded in `evals/craft-details-2026-09-19.md` after execution.
It can establish feasibility and bounded rendered behavior; it cannot establish
independent-agent improvement, whole-product quality or Safari overscroll.

Future reference refreshes compare these exact selected paths and review any
changed behavior before updating the fixed revision. Current registration does
not enroll this repository in `upstreams.lock.json` or freshness automation.
