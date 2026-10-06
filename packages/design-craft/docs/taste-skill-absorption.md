# Leonxlnx/taste-skill absorption matrix

This document records the deliberate baseline-fusion boundary for
`https://github.com/Leonxlnx/taste-skill` at commit
`ccbc15639c97057cbfcf32ecebc38ef716e4bb37`. The compatibility submodule stays
pinned at `b17742737e796305d829b3ad39eda3add0d79060`.

## Contents

- [Inventory truth](#inventory-truth)
- [Status vocabulary](#status-vocabulary)
- [Entrypoint matrix](#entrypoint-matrix)
- [Auxiliary-file matrix](#auxiliary-file-matrix)
- [Rules deliberately not promoted](#rules-deliberately-not-promoted)
- [Current conclusion](#current-conclusion)

## Inventory truth

The reviewed remote head contains the same thirteen Skill entrypoints, one
`llms.txt`, and one Stitch-oriented `DESIGN.md` as the pinned compatibility
snapshot. It contains no reusable component library, runtime package, test
harness, or implementation script under `skills/`.

`design-craft` absorbs durable judgment and workflow behavior into one design
entrypoint with conditional references. Optional image and style capabilities
do not become prerequisites for ordinary UI work. Host-output policy and
specialized brand/mobile generators remain outside this consolidation.

## Status vocabulary

- `absorbed`: the durable capability is represented in local instructions,
  references, scripts, templates, or validation.
- `partial`: a useful, generalizable subset is local; style- or host-specific
  behavior remains separate.
- `missing-high-value`: an important behavior is absent and must block an
  "absorption complete" claim.
- `intentionally-rejected`: promoting the rule into the baseline would reduce
  correctness, force a style/tool, or conflict with project authority.
- `provenance-only`: retained for history or compatibility, not active behavior.

## Entrypoint matrix

| Upstream entrypoint | Status | Local target or boundary | Decision |
| --- | --- | --- | --- |
| `taste-skill` | absorbed | `visual-judgment.md`, `foundational-visual-principles.md`, `product-ui-taste-review.md`, `design-move-library.md` | Brief inference, anti-slop judgment, hierarchy, product fit, responsive craft, and final preflight are baseline behavior. |
| `taste-skill-v1` | provenance-only | pristine upstream | The legacy v1 behavior is retained for traceability; the current fusion is the maintained baseline. |
| `redesign-skill` | absorbed | `product-ui-taste-review.md`, `design-move-library.md`, critique/polish passes | Scan, diagnose, preserve functionality, remove generic patterns, and apply concrete repair moves are local. |
| `minimalist-skill` | partial | `visual-judgment.md`, `design-system-contract.md` | Restraint, typography, low-noise surfaces, and meaningful elevation are useful; a fixed minimalist palette/font/icon prescription is not universal. |
| `brutalist-skill` | intentionally-rejected | separate style Skill | Industrial brutalism is a valid selected direction, not a safe default for every product surface. |
| `gpt-tasteskill` | partial | `visual-judgment.md`, motion references | Variance, typography width, composition, anti-repetition, and motion craft are useful. Simulated Python randomness, mandatory AIDA, GSAP, fixed fonts, and universal cinematic spacing are rejected. |
| `brandkit` | intentionally-rejected | separate `brandkit` Skill | Brand-board image generation is a specialized artifact workflow, not baseline UI implementation behavior. |
| `image-to-code-skill` | partial | `image-reference-implementation.md`, `comp-fidelity.md` | Selected-image extraction, faithful implementation, and bounded comparison are internal; forced generation and treating regenerated detail as source evidence remain rejected. |
| `imagegen-frontend-web` | partial | `web-image-direction.md` | Requested web comps, coherent image sets, actual-tool execution, and implementation handoff are internal and opt-in; fixed generation counts and compulsory per-section output remain rejected. |
| `imagegen-frontend-mobile` | intentionally-rejected | separate image-generation Skill | Mobile concept-image generation is not native implementation or general UI review. |
| `stitch-skill` | partial | `design-system-contract.md`, developer-product templates | Agent-readable `DESIGN.md`, semantic tokens, typography roles, and state contracts are local; Google Stitch-specific generation stays opt-in. |
| `soft-skill` | partial | `visual-judgment.md`, `product-ui-taste-review.md` | Premium specificity, rhythm, restrained surfaces, and anti-generic checks are local. Absolute font/icon/border bans and price/persona theater are rejected. |
| `output-skill` | intentionally-rejected | host delivery policy | Complete output is important, but overriding host truncation/context policy is not a design-engineering capability and must not live in this baseline. |

## Auxiliary-file matrix

| Upstream file | Status | Decision |
| --- | --- | --- |
| `skills/llms.txt` | provenance-only | Discovery metadata is not behavior. |
| `skills/stitch-skill/DESIGN.md` | partial | Its machine-readable design-system structure informed the local contract, while Stitch-specific style authority remains opt-in. |

## Rules deliberately not promoted

The baseline does not universally require or ban a named font, icon library,
layout archetype, color family, card shape, animation library, generated image,
or page-funnel formula. It also does not simulate tools that were not run.

Project `PRODUCT.md`, project `DESIGN.md`, real content, live runtime evidence,
accessibility, platform conventions, and measured performance always outrank a
generic aesthetic prescription. Optional style references do not silently
redefine default behavior. Actual image generation still follows the host's
available tool and its required instructions, not a bundled provider runtime.

## Local entrypoint consolidation

The 2026-09-07 local consolidation reuses the previously reviewed Taste source
and the locally simplified entrypoints; it makes no new remote-freshness claim
and does not advance upstream pins. It retires the independent `image-to-code`,
`imagegen-frontend-web`, `gpt-taste`, `high-end-visual-design`, and
`full-output-enforcement` installation entries after source, route, and install
validation. Preserve pristine upstream material and attribution for maintenance.
The first four contribute conditional capabilities inside design-craft;
complete output remains the host delivery policy, not a separate design mode.

## Current conclusion

Freshness review on 2026-09-19 extends the reviewed head to
`e79ca9ec7e071eb3a3b623c4fb752e853fc3ed58`: the three commits after `ccbc156`
change only `README.md` sponsor presentation and `assets/sponsors/fluxion-ai.png`.
The complete two-file comparison is provenance-only. The compatibility pin and
absorbed behavior do not advance; the earlier range description below is retained
as historical context.

`missing-high-value`: none for the reviewed snapshot.

The cumulative state is selective absorption: design judgment, redesign,
selected-image implementation, requested web comps, and useful expressive
style guidance are local. Specialized Stitch, brand-kit, mobile generation,
and host-output policy remain outside this five-entrypoint consolidation.
The latest reviewed range after
`dfb6f9f9e93a39f673b1827c0889cc28326d1800` through
`ccbc15639c97057cbfcf32ecebc38ef716e4bb37` contains seven commits that update
README and sponsor presentation only. It changes no Skill entrypoint, runtime,
or reusable design-engineering behavior. Its latest-range status is
`provenance-only`; the submodule does not need to advance for those
repository-presentation changes.

Historical independent blind evidence for its recorded source is retained in
`evals/comparative/taste-visual-critique-ablation/`: `design-craft` 98,
focused taste upstream 96, no-skill baseline 95. The first controlled run
exposed an incomplete move-budget rule; the Skill was repaired and the final
evidence was rerun rather than editing the judge result. Those scores do not
certify the changed 2026-09-07 Skill tree; current behavioral evidence must be
collected separately without rewriting historical hashes or judge results.
