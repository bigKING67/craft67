# Upstream adoption review — 2026-10-23

## Decision and scope

Selectively absorb three instruction refinements into existing references:
business-aware KPI comparisons, mobile task priority after reflow, and
phrase-aware typography. All four compatibility pins stay unchanged. This is a
bounded adoption review, not an engineering or security audit of entire
upstream runtimes.

| Upstream | Compared range | Commits / changed paths | Disposition |
| --- | --- | --- | --- |
| taste-skill | [d237dd3…6010f91](https://github.com/Leonxlnx/taste-skill/compare/d237dd399d57524945c0c81327da5da19f7a468d...6010f91a9935f1c167dfc500fb1a475681892e6b) | 41 / 105 | `partial` |
| impeccable | [c63b8dd…5cb95ee](https://github.com/pbakaus/impeccable/compare/c63b8dd7dd5a5f3c32eaabe1af76d0694f863ed2...5cb95eea9c96479f57afe0732a45470d30183326) | 114 / 1,250 | `partial` |
| jakubkrehel-skills | [c0588bb…4c66b1f](https://github.com/jakubkrehel/skills/compare/c0588bb6d654eb725046f0bf9deec338c34891ab...4c66b1fa86e9ab70187b43d7da9b6fdb29f2ef63) | 11 / 25 | `deferred` |
| emilkowalski-skills | `2d228630ba1446365f614a108cb8252f1feda202` unchanged | 0 / 0 | Prior decision retained |

## Inventory completeness and reading depth

Taste and Impeccable were compared in repository-external bare filtered clones.
Ancestry, `git rev-list --count`, and NUL-delimited `git diff --no-renames`
recovered complete commit and path inventories without fetching into, editing,
or changing the pinned submodules. Impeccable's API comparison returned only
100 commits and 300 files; that response alone was incomplete. Jakub's API
comparison returned all eleven commits and twenty-five paths.

The SHA-256 of each sorted path list, one path per line with a final newline:

| Upstream | Path-list SHA-256 |
| --- | --- |
| Taste | `2f2c9e3d042022469b1ac07ae7a52dc81f5e9dc9cdee1c2d070f5fd3eef8e416` |
| Impeccable | `ca0414ae84c038ed27850b112caa12f422c4a0f42bd3a8837e16b2c49f4e7ad8` |

Complete inventory does not mean complete source review. Taste reading covered
the main entrypoint, app-screen data/KPI/state/mobile guidance, copy proof
structure, and scene fallback/intermediate-progress checks. Other large style,
asset, recipe, and script surfaces were structure-screened and remain outside
the selected behavior. Impeccable's canonical Markdown deltas were screened,
with detailed patch reading of `critique`, `harden`, `typeset`, `distill`, and
`extract`, plus targeted main/native/host boundary inspection. Its 1,250 paths
include 588 host/plugin paths, 390 tests, 171 crate paths, 26 canonical `skill/`
paths, and 75 others. Engines, installers, and browser code were not built,
executed, or fully reviewed. Jakub's new tool is inventory-screened only.

## Selected behavior

| Fixed source | Adaptation and local destination |
| --- | --- |
| [Taste app screens](https://github.com/Leonxlnx/taste-skill/blob/6010f91a9935f1c167dfc500fb1a475681892e6b/skills/taste-skill/references/app-screens.md), KPI guidance | `surface-playbooks.md` and `validation-contract.md`: interpret improvement from the metric definition, retain sign/window and a cue beyond color, and avoid fabricated percentage change from zero or missing baselines. The actual source data and declared formula govern |
| Same source, phone adaptation | Dashboard playbook: keep relevant urgent/primary actions and summaries ahead of long lists after column collapse, preserving detail and coherent reading/keyboard order |
| [Impeccable typeset](https://github.com/pbakaus/impeccable/blob/5cb95eea9c96479f57afe0732a45470d30183326/skill/reference/typeset.md), line breaks | `design-system-contract.md`: manual breaks follow meaningful phrases and are rechecked at target widths, text sizes, and locales. `balance` is conditional; `pretty` stays an optional progressive enhancement, with layout-cost and editing-stability checks. Intentional uneven final lines are not automatic defects |

The typography adaptation is narrower than the upstream default. The
[CSS wrapping reference](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/text-wrap-style)
describes the layout/performance tradeoff and editable-content stability; it
does not justify globally forcing `pretty` across long or updating content.
Existing project authority and supported-target verification still govern.

The Taste coverage map now includes dashboard/data checks; Impeccable adds a
`typographic_line_breaks` coverage group. These checks preserve discoverable
instruction coverage. They do not prove improved rendering or model behavior.

## Deferred and rejected scope

- Taste's [reorganization](https://github.com/Leonxlnx/taste-skill/blob/6010f91a9935f1c167dfc500fb1a475681892e6b/CHANGELOG.md)
  leaves one main entrypoint and moves classic/image Skills to other
  repositories. The pinned thirteen-Skill/two-auxiliary inventory stays valid;
  destination repositories are neither registered nor reviewed here.
- Complex scroll-scene checks remain candidates for an actual requested scene.
  Do not add motion to ordinary pages, a second browser runtime, or a fixed
  frame quota. Unreviewed style/asset/reference recipes remain deferred.
- Universal palette, icon, type-size, viewport, or animation quotas, mandatory
  drawing/seeding/inspection, and upstream installation/host orchestration are
  rejected as baseline rules. Actual business aggregation and rounding win over
  a universal requirement to sum already-rounded display values.
- Arabic/Persian joining, numeral/calendar, and mixed-script hardening are
  conditional candidates for a real target locale, not a universal normalization
  or nationality-based calendar policy.
- The newer Impeccable head lacks `skill/scripts/detect.mjs` and supplies a Rust
  launcher. Keep the local JS detector pin. JSON/exit/degraded behavior,
  distribution trust, platform behavior, and rollback need a separate migration.
  New engine, CDP, hook, provider, and browser-session compatibility is unverified.
- Weakened prohibition wording and open-ended polish are not adopted. Existing
  requirement strength, bounded verification, and completion conditions remain.
- Jakub adds twenty-two `technical-drawing` paths plus three repository/plugin
  paths. Defer the viewer/geometry/projection/export/build/test scope as a whole;
  no script or viewer was run. Its behavior boundary remains `c0588bb6d654eb725046f0bf9deec338c34891ab`.

Earlier deferred ranges retain their decisions, including Impeccable's
`695df68…f2c7051` and `f2c7051…cf3d2fa` ranges, Emil's `break-ui` range, and
Jakub's `267330e…d574cc8` range. A newer selected-behavior boundary describes
selective local representation, not full absorption of intervening history.

## Evidence boundary

The edits touch `skill-core` and typography in the existing Evidence Graph v2,
so prior comparative/cross-agent projections that inherit those paths cannot
certify this change. Native observations bound to the earlier full Skill tree
also cannot certify the changed tree. Preserve original hashes, commits,
outputs, and judgments; source validation is separate from current-source
evidence admission.

The four comparative cases and three observed cross-agent tasks are archived
under their domain's `history/2026-10-23-pre-upstream-adoption/`. All 286
original files match their pre-archive SHA-256 byte for byte. The cross-agent
archive also derives a Markdown scorecard from its unchanged JSON and records
the missing Cursor observation for compatibility with the historical validator;
no original receipt is rewritten. Active case definitions remain, and affected
host statuses are now pending. The native active directory had no observed
receipts to archive. Recapture affected evidence against the final clean release
candidate before using it for release certification.

This maintenance change does not collect model comparisons, real-product
browser/native observations, installed-host parity, or newer-engine evidence.
Source checks cannot establish those outcomes. It does not install, commit,
push, tag, or release the package, and does not change its version.

## Source validation

- `make upstream-absorption-check`: four upstream contracts passed, including
  fourteen detector tests and six Jakub tracking tests.
- Skill Creator `quick_validate.py`: passed in an isolated PyYAML environment.
- Root `python3 scripts/check.py --package design-craft`: passed all twenty-five
  portable gates, including lint, package boundary, workflow/source contracts,
  the source test suite, and development maturity.
- New comparative/cross-agent archive validators and active definition
  validators passed. These are archival integrity and source checks, not new
  observed model or native evidence.
- `upstream_absorption_report.py --remote --fail-on-unreviewed`: passed against
  the four registered heads on the review date; the compatibility pins remain
  older and pristine by design.
