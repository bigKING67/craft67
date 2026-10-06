# Impeccable release-preparation adoption review

Date: 2026-09-19. Range: `695df68a5860da4d25cd629fc3727ec8f3c0991b`
through `f2c7051853848826aac2f4646581d62a732155ad`.
Decision: **defer this range; preserve existing selected behavior and pin**.

## Evidence completeness and review depth

GitHub compare returned 300 file records and 100 commits while reporting 110
commits ahead. That response was incomplete and was not used to advance review
metadata. Fetching the fixed head into the existing object database, without
changing the submodule checkout, enabled a complete local comparison:

```sh
git -C upstreams/impeccable diff --no-ext-diff --no-renames \
  --ignore-submodules=none --name-status -z \
  695df68a5860da4d25cd629fc3727ec8f3c0991b \
  f2c7051853848826aac2f4646581d62a732155ad
```

The range has 110 commits and 4,472 changed paths. Major groups include 1,238
test paths, 299 Rust crate paths, 121 canonical Skill paths, generated host and
plugin copies, workflows, CLI, extension and browser assets. Complete inventory
does not mean every changed implementation line was audited. Review depth is
adoption-boundary screening plus focused canonical workflow/reference reading;
the engine and live runtime were not built, executed or security-audited.

## Decisions

| Delta | Local decision and rationale |
| --- | --- |
| Rust binary/launcher replaces JS scripts and detector | Defer adoption. The package remains dependency-free and its optional detector uses the existing compatibility snapshot; a launcher migration is a separate implementation and compatibility project. |
| Generated host/plugin files, extension/marketplace packaging, hooks and installer changes | Outside the selected runtime boundary; do not import into the canonical Skill. |
| Live-generate entrypoint, overlay target resolution, lease/roll-call, variant bake and polling | Reject integration into this release. browser67 and existing isolated prototype/Shadow workflows own browser lifecycle and source promotion. No claims about the new upstream runtime's correctness. |
| Launcher-failure fallback and helper-path clarification | Keep existing local helper resolution and unavailable-tool fallback. Do not adopt a mandatory boot loader or exact fallback speech. |
| Preserve incumbent design files during ordinary extension; advice does not execute workflows | Consistent with existing project-authority and read-only task boundaries. No duplicate instruction needed. |
| Touch dragging versus page scrolling, pointer interruption and recovery | Defer the more detailed checklist for a dedicated interaction fixture. Existing interaction-physics and validation references already distinguish source/screenshots from gesture runtime; this review does not claim they contain every new upstream edge case. |
| Native-alpha cutouts, light/dark composites, explicit unscored assets | Defer instruction changes until exercised through the actual host image-generation workflow. Do not import provider/model defaults, fixed generation resolution or an upstream asset runtime. |
| Placeholder contrast detector change | Defer engine-specific adoption. Existing accessibility requirements do not establish detector coverage; the pinned detector is not claimed to include the new rule. |
| Mandatory craft floor, menu, generated sidecar, fixed comp count and delegation | Preserve project authority and local routing; no new universal workflow requirement. |

The latest-range status is `deferred`, not `provenance_only`: this range contains
real behavior changes. Cumulative selective absorption remains valid only for
the previously recorded boundary. No high-value-completeness claim is extended
to this range. Reviewed head means this explicit adoption decision was made,
not that new behavior was imported or that every source line passed review.

## Verification boundary

Submodule checkout stays `80e4dd0d581fcdb42be62252b7bc07dcd2238330`.
No runtime Skill, dependency, global route, installation, model choice or
release certification is changed. Existing comparative/host/native evidence
still needs its own current-source verification; upstream freshness alone
does not close those release gates.
