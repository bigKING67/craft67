# Upstream adoption review — 2026-10-11

## Decision and scope

This is a bounded **adoption decision** for Design Craft, not a whole-upstream engineering, security or product-quality audit. It covers the remote movement after [the 2026-10-06 review](upstream-adoption-review-2026-10-06.md). All compatibility pins stay unchanged; no upstream file, runtime, hook or host integration is imported.

Three small rules are adapted into local references. Taste changes only provenance and Emil has no new commits. The ranges deferred on 2026-10-06 stay deferred.

## Exact inventory

| Upstream | Compared range | Commits / changed paths | Adoption disposition |
| --- | --- | --- | --- |
| taste-skill | [ce26fc2…717446e](https://github.com/Leonxlnx/taste-skill/compare/ce26fc25c0e5e8cab638f883de62d9a86ee5e45b...717446e07a78d4e6d7918b1fde1a263378eebac9) | 8 / 9 | `provenance_only` |
| impeccable | [cf3d2fa…c63b8dd](https://github.com/pbakaus/impeccable/compare/cf3d2fa07d3ad1814ac5fbbbb5b2043b795eaef1...c63b8dd7dd5a5f3c32eaabe1af76d0694f863ed2) | 32 / 431 | `partial` |
| emilkowalski-skills | no movement after `e8a175d` | 0 / 0 | unchanged |
| jakubkrehel-skills | [d574cc8…c0588bb](https://github.com/jakubkrehel/skills/compare/d574cc8a576dc24256ad38268b8d03d86724a1b3...c0588bb6d654eb725046f0bf9deec338c34891ab) | 4 / 5 | `partial` |

The GitHub comparison for Impeccable truncated at 300 files. A repository-external bare filtered clone recovered the exact range with `git rev-list --count` (32) and `git diff --no-renames --name-only` (431 paths). The sorted path list with its trailing newline has SHA-256 `7564da3e69783d9926209025828c1e6010876a4d8818c8e77c3a62e161af116f`. It is dominated by tests (108 oracle and 35 fixture paths), Rust crates and generated provider copies. The canonical `skill/` tree was diffed in full: 8 files, 17 insertions and 16 deletions. Engine, URL-capture, CLI, browser-extension and generated provider paths were screened by path and commit subject only; they were not read line by line, built or executed.

## Source-specific decisions

### Taste

The changed paths are `README.md`, five removed README button images, a TasteCode announcement image and Sidrune sponsor assets. No Skill instruction changed. Record `provenance_only`; copy no sponsor material.

### Impeccable

Absorbed, adapted to local authority:

- **Operate and Read surfaces are not comp-first** (#990). Local comps were already request-only, so the surface-mode definitions in `surface-playbooks.md` now only stop proposing one as the default first step for working screens and documents.
- **Operate comps and dashboards carry real meaning** (`mode-operate.md`). Requested comps use real content, plausible data with units and one state worth seeing. The dashboard playbook in `surface-playbooks.md` now limits state colours to meaningful use and asks a time-varying headline number to show recent history with its onset marked.

Not adopted:

- The per-reference visual description in new-work concept seeding is `partial`: the local package has no cultural-world seeding step to attach it to.
- Decision-card dealing, the `buildPath` config and toggle, and HTML skeleton decision cards depend on the upstream CLI, decision page and persisted config.
- Audit dimension renumbering, version files, engine pins 0.1.12/0.1.14 and detector engine fixes stay behind the unchanged compatibility pin. A pin bump needs local executable fixtures first.

The selected behavior boundary advances to `c63b8dd` for these two rules only. As with the earlier `524fb8c` boundary, `cumulative_status=selective_absorbed` means selected behavior up to that commit; it does not claim the deferred `f2c7051..cf3d2fa` range (480 commits) is represented. The new `operate_code_led_and_dashboard_meaning` coverage terms in `scripts/design_craft_impeccable_absorption.py` fail the check if these rules are removed.

### Jakub

The four commits rework the `state-machine` and `variant` switchers: a row of tabs becomes a grouped vertical list, and a grouped `<select>` replaces it where space runs out. Local component scenario inspection in `impeccable-workflow.md` now names cases in product language and groups them under headings by what changes once there are more than about seven.

The switcher markup, fixed 232px layout, container-query recipe and `__state` search-param convention are not adopted. They are host-harness detail, and local evidence and runtime ownership rules already govern the harness. The pinned 11-entry inventory and entrypoint decisions are unchanged. The beyond-pin selection (`state-machine`: partial, `variant`: deferred), its local coverage and the reviewed `skills/state-machine/SKILL.md` digest are recorded under `skill_inventory.latest_range_*` and asserted by the Jakub contract test.

## Discovery source screened: Designeer

[Designeer](https://designeer.xyz/) is a human-curated directory of 422 tools and 132 people. It has no repository, no content license and no Skill instructions, so it is **not registered as an upstream**. It may be used as a discovery index for future candidates. Its DESIGN.md generators (Refero, getdesign.md, Hyperbrowser Design.md, Open Design, Aura) are the leads closest to Design Craft's authority model. They are unreviewed, and they overlap the existing `extract`/`document` absorption.

## Verification

Ancestry was checked against the remote history in repository-external filtered clones, because the pinned submodules do not contain the reviewed commits. For Impeccable, `cf3d2fa` and the `80e4dd0` pin are ancestors of `c63b8dd`. For Jakub, `267330e` is an ancestor of `c0588bb`.

After the metadata and reference updates:

- `make upstream-absorption-check` passed: the Taste, Impeccable, Emil and Jakub contracts, plus the detector and Jakub unit tests.
- `upstream_absorption_report.py --remote-details --fail-on-unreviewed` passed, with all four `reviewed_remote_drift=false`.
- `make validate-portable` passed all 25 gates; `lint`, `skill-quick-validate` and `package-check` passed.

A passing freshness check only means the recorded decision covers the sampled remote heads. No model calls, tag creation or Release publication are part of this review. The local install was refreshed separately through `make publish-local`.
