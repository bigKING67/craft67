# Upstream adoption review — 2026-10-06

## Decision and scope

This is a bounded **adoption decision** for Design Craft, not a whole-upstream engineering, security or product-quality audit. No new upstream content, runtime, host integration or Skill behavior is imported. All compatibility pins and absorbed-behavior boundaries remain unchanged.

Taste changes only provenance. The three other ranges are explicitly deferred: useful candidates exist, but neither entrypoint expansion nor a new runtime dependency is justified by the current monorepo release-preparation task. `reviewed_through_commit` records the range considered for adoption; `latest_range_status=deferred` does not mean its implementation was validated or its behavior absorbed. It must not be cited as cross-host, native or release-certification evidence.

## Exact inventory

| Upstream | Compared range | Commits / changed paths | Adoption disposition |
| --- | --- | --- | --- |
| taste-skill | [e79ca9e…ce26fc2](https://github.com/Leonxlnx/taste-skill/compare/e79ca9ec7e071eb3a3b623c4fb752e853fc3ed58...ce26fc25c0e5e8cab638f883de62d9a86ee5e45b) | 10 / 2 | `provenance_only` |
| impeccable | [f2c7051…cf3d2fa](https://github.com/pbakaus/impeccable/compare/f2c7051853848826aac2f4646581d62a732155ad...cf3d2fa07d3ad1814ac5fbbbb5b2043b795eaef1) | 480 / 1288 | `deferred` |
| emilkowalski-skills | [85e8e23…e8a175d](https://github.com/emilkowalski/skills/compare/85e8e2363b713506e1d5b6e07a0eb2da66be1bc3...e8a175de22ae1e49370fc144c1f3bb9aeedf988d) | 3 / 3 | `deferred` |
| jakubkrehel-skills | [267330e…d574cc8](https://github.com/jakubkrehel/skills/compare/267330e1adfc66a718fb65fa6918c1f06d0a689e...d574cc8a576dc24256ad38268b8d03d86724a1b3) | 13 / 56 | `deferred` |

Taste, Emil and Jakub comparisons contained the complete commit and path inventories (10/2, 3/3 and 13/56); source patches were read for the selected surfaces below. Binary sponsor artwork was classified by its asset boundary, not visually evaluated.

Impeccable's GitHub comparison was incomplete: 300 files and a truncated commit list. A **repository-external bare filtered clone** recovered the exact 480-commit range and 1,288 paths using `git rev-list --count <base>..<head>` and `git diff --no-renames --name-only <base> <head>`. The sorted Git path output with its trailing newline has SHA-256 `5b5a26825512ca621c9408657706bc7bac8872f49f95e43ec76bc2882d49c578`. No tracked submodule was fetched, moved or edited.

The full Impeccable path inventory includes 631 test paths, 237 Rust crate paths, 29 UI paths and 17 paths under `skill/`; the rest includes generated provider surfaces, plugin/host integration, browser bundles and repository operations. Inventory completeness is not line-by-line source-review completeness.

## Source-specific decisions

### Taste

The two paths are `README.md` and `assets/sponsors/fluxion-ai-banner.png`: sponsor names, sponsor placement and promotional credit copy. The complete README patch contains no Skill instructions. Record `provenance_only`; do not advance the compatibility pin or copy sponsor material into Design.

### Emil

New `skills/break-ui/SKILL.md` and `CATALOG.md` add schema-backed realistic extremes, Unicode/grapheme cases, zero/one/large collections, locale-aware display, missing media and environment checks. README changes advertise that entrypoint and change promotional links.

Local `skills/design-craft/references/impeccable-workflow.md` already requires realistic hostile data, reachable cases, the real component, isolated data fixtures, preservation of server/client boundaries and actual-runtime evidence. `design-system-contract.md` already covers whole-message localization and plural/select rules.

Defer the new standalone Skill/catalog. Its detailed data examples remain possible future input, not newly absorbed behavior. Do not import an initial-response ritual, mandatory persistent bottom toggle, blanket report-then-stop behavior or automatic test loads beyond the product contract. Any later adoption needs a demonstrated local gap and an applicable evaluation; no new entrypoint or inventory change is claimed here.

### Jakub

The complete 56-path inventory includes writing and break updates, broad accessibility/layout/type/UI reference changes, and new `build-design` and `state-machine` entrypoints. Selected writing/break patches, writing patterns and the two new entrypoint workflows were inspected. Other domain references and every generated agent manifest were **not** reviewed line by line.

- Writing vocabulary, pluralization, meaningful errors and context-aware labels overlap the current local content contract. New partial-result/undo templates are candidates for a later focused review, not an imported policy.
- The new state workbench imports a real component and feeds state through the data boundary, which is useful but overlaps the local scenario-inspection boundary. Its blanket client-page requirement conflicts with preservation of server/client semantics; production isolation cannot be inferred from a throwaway route name.
- Design-source measurements and explicit comparison evidence are useful principles. Do not adopt automatic nearest-token rounding, a universal 2px decision threshold, omission of undrawn loading/error states, or restoration of an inaccessible design without the project's authority and applicable contract.
- The break workflow's browser-one-load budget and keep-the-server-running default do not replace local evidence and lifecycle requirements.

Defer the range and retain only the previously adopted writing/scenario boundary. The 11-entry compatibility inventory still describes the unchanged pinned source; the two new remote entrypoints are screened candidates, not installed products.

### Impeccable

Beyond the complete path inventory, selected canonical entrypoint/reference/agent deltas were inspected. They include Operate/Read/Persuade composition distinctions, comp/region mapping, asset openings and transparency, a human component-review receipt, build-phase sequencing and Gemini hook integration. The engine, browser bridge, generated providers, binary/runtime changes and all tests were **not** independently audited or executed.

- Local product clarity and visual-authority rules already constrain composition by task. Mode-specific composition guidance is a candidate for focused future evaluation; this review does not import universal art-direction rules.
- The component-review/region-map sequence depends on the upstream CLI, derived JSON, receipts and its phase protocol. Copying only the Markdown would create commands and evidence claims the local package does not implement.
- Hooks, generated provider files, live-browser/session code and the Rust engine remain outside the selected runtime boundary. No installation or hook approval flow was invoked.
- Asset opening/alpha guidance remains a scoped candidate; no pixel test or new image-generation contract was evaluated here.

Defer the range. This is deliberately not a claim that 480 commits or 1,288 paths are defect-free.

## Verification and follow-up

Verification completed after the metadata update: upstream absorption validators passed, all 25 portable gates passed, and `upstream_absorption_report.py --remote-details --fail-on-unreviewed` passed with all four `reviewed_remote_drift=false`. A live freshness pass only means the recorded **adoption decision** covers the sampled remote heads and metadata is internally valid; later remote movement requires a new check. It does not remove the independently failing host/comparative evidence gates.

No model calls, global installs, source hash rewriting, tag creation or Release publication are part of this review. Real evaluation remains subject to the model/budget choice recorded in the root certification checklist. Before expanding the Skill, choose a concrete deferred candidate and its acceptance test; do not copy the whole remote tree.
