# Third-party notices

This project is a personal fusion layer built on top of upstream open-source
design engineering and frontend quality skill projects. Upstream repositories
registered in the upstream lock are kept as pristine submodules under
`upstreams/`. Reviewed sources and their adoption boundaries are identified below.

## gustavo-fior/craft

- Repository: https://github.com/gustavo-fior/craft
- Fixed reference revision: `1758451bc13c15f7b0c04fc4f22b673852425bbc`
- License observation: the README declares MIT; no standalone license or
  notice file exists in the inspected revision. No copyright notice is inferred.
- Referenced concepts: document canvas backgrounds, nested corner geometry,
  image edge separation and per-glyph optical alignment.

The local design-system guidance and evaluation fixture are original work.
No upstream prose, code snippets, generated Skill, fonts, imagery, components
or runtime dependencies are distributed. This reference is not registered as a
managed submodule or automatic update source. Before any future substantial
copying, obtain and preserve the applicable license and copyright notice.
See `docs/gustavo-fior-craft-reference.md` in the source repository for the
review scope and source digests.

## jakubkrehel/skills

- Repository: https://github.com/jakubkrehel/skills
- Reviewed source revision: `267330e1adfc66a718fb65fa6918c1f06d0a689e`
- License: MIT; copyright 2026 Jakub Krehel.
- Selected sources: `skills/better-writing/SKILL.md`,
  `skills/break/SKILL.md`, and `skills/break/scenarios.md`.

Original local adaptations cover flow vocabulary, enabled-state toggle labels,
complete localized messages, persistent guidance outside empty states, and
component-input-driven scenario inspection. They live in the existing
design-system and hardening references. The installed package includes no
upstream plugin, host configuration, browser runtime or source snapshot. The
repository keeps pristine provenance at `upstreams/jakubkrehel-skills`.
Other entrypoints remain
screened candidates, not adopted behavior. This fixed selective reference is
registered in `upstreams.lock.json` and enrolled in upstream freshness checks.

The preserved distribution license is `LICENSES/MIT-upstreams.txt`.

## Leonxlnx/taste-skill

- Repository: https://github.com/Leonxlnx/taste-skill
- License: MIT
- Copyright: 2026 Leonxlnx
- Local path: `upstreams/taste-skill`
- Initial pinned commit:
  `06d6028b5c623016c59ce8536f578e5a1127b499`
- Current reviewed commit:
  `b17742737e796305d829b3ad39eda3add0d79060`

The fusion layer references and adapts ideas around anti-slop frontend design,
brief inference, design-system selection, visual hierarchy, redesign workflow,
motion discipline, and final preflight review.
The reviewed 2026-07-10 range changed sponsorship/readme assets only, so it is
retained as provenance and did not change design-craft behavior.

The preserved distribution license is available at:
`LICENSES/MIT-upstreams.txt`.

## pbakaus/impeccable

- Repository: https://github.com/pbakaus/impeccable
- License: Apache-2.0
- Local path: `upstreams/impeccable`
- Initial pinned commit:
  `d2ab4ddee6fa63002fae680652b5fbd31735e280`
- Current absorbed commit:
  `80e4dd0d581fcdb42be62252b7bc07dcd2238330`
- Current reviewed commit:
  `ae5e95101a6979e7f7973a4ff57680b3c7adc1ec`

The fusion layer references and adapts ideas around command taxonomy, context
setup, audit/polish/harden/optimize/live workflows, deterministic detector
checks, design-system-aware validation, and production-readiness review.
The 2026-07-10 review selectively absorbed platform routing, native audit/adapt
guidance, iOS/Android quality rules, and detector/design-system fixes. Generated
provider bundles, site output, dependencies, and store packaging remain
provenance only.
The 2026-08-05 selective update pins the canonical detector correctness
boundary for style carriers, comment-safe image checks, versioned local
stylesheets, `rounded-none`, retired single-font rules, YAML scalar escapes,
and Blade compound suffixes. It also adapts reference-first fidelity and
post-fix verdict ideas as original local contracts. Generated provider copies,
live/browser-session and hook runtime, forced delegation, and universal visual
bans remain outside the fusion layer. The upstream source detector remains an
optional runtime: selected behavior has function-level local coverage, while
full static HTML/CSS execution depends on upstream parser packages that Design
Craft neither vendors nor silently treats as installed.

The preserved distribution license and notice are available at:
`LICENSES/Apache-2.0.txt` and `LICENSES/NOTICE-impeccable.md`.

## Vercel design reference history

- Source: https://vercel.com/design.md
- Source: https://vercel.com/design.dark.md
- Local path: `skills/design-craft/templates/vercel-geist/`
- Retrieved: 2026-06-24

Historical commits used these public design-system references as seed inputs.
Because no separate redistribution license was identified, the current package
replaces the snapshots with original design-craft templates under
`skills/design-craft/templates/developer-product/`. The compatibility paths no
longer contain Vercel-authored snapshot text. See
`LICENSES/VERCEL-DESIGN-NOTICE.md` for provenance and scope.

## emilkowalski/skills

- Repository: https://github.com/emilkowalski/skills
- License: MIT
- Copyright: 2026 Emil Kowalski
- Local path: `upstreams/emilkowalski-skills`
- Initial pinned commit:
  `a47903a06a05d2e24c483bd8961c85969a51a494`
- Current absorbed commit:
  `85e8e2363b713506e1d5b6e07a0eb2da66be1bc3`
- Current reviewed commit:
  `85e8e2363b713506e1d5b6e07a0eb2da66be1bc3`

The 2026-09-19 update selectively adapts Mobile Web viewport, keyboard,
safe-area and gesture-ownership concepts into original conditional guidance,
calibrated against browser/standards documentation. No global CSS reset,
initial-response block, component code or native-platform reclassification is
imported. The compatibility submodule remains at `7bb7061`.

The fusion layer references and adapts ideas around motion purpose, animation
frequency, easing and duration standards, physicality, gesture handling,
animation performance, reduced-motion behavior, strict animation review, and
animation vocabulary.
The 2026-07-10 review also absorbed product-design principles, direct
manipulation, presentation-value interruption, spring response/damping,
velocity handoff, momentum projection, rubber-banding, and optical typography
into original design-craft references.
The later 2026-07-11 range added `improve-animations`; design-craft selectively
adapted its codebase recon, prioritized audit, self-contained plan, and plan
reconciliation workflow while retaining project-authority and runtime-evidence
calibration instead of copying absolute heuristics.
The following `b024c8b` update changes README newsletter copy only and remains
provenance-only.
The subsequent `4691d39` and `7bb7061` range corrects two README typos only and
also remains provenance-only.
The 2026-07-12 five-Skill deep audit maps every upstream Skill entrypoint and
auxiliary Markdown file. The local fusion adds original calibrated rules and
implementation recipes rather than redistributing an upstream component
library; the reviewed upstream Skill tree contains no non-Markdown runtime
source. Substantial adapted text and code snippets remain covered by the
preserved MIT notice below.
The 2026-08-05 review selectively adapts the new prototype workflow into an
original framework-neutral exploration/selection/promotion contract. The fixed
picker markup, dark-glass CSS, route/query wiring, and host-specific runtime are
not copied.

The preserved distribution license is available at:
`LICENSES/MIT-upstreams.txt`.

## cameroncooke/AXe

- Repository: https://github.com/cameroncooke/AXe
- License: MIT
- CI tool version: `v1.7.1`
- Pinned release asset SHA-256:
  `26a64009c09a3ae980b1f1b4b377bd2a2dd96cbbde24821935e47352cb71cc69`

The native-runtime workflow downloads this pinned tool only on the ephemeral
macOS runner when a current iOS Simulator presents its system URL-opening
confirmation. AXe taps the real `Open` control by accessibility label; the
fixture must still receive the URL callback and write the interaction marker.
The AXe binary is not stored in this repository, included in the npm package,
or redistributed in release assets.

## Peekpaper discovery metadata

- Source: https://peekpaper.com/
- Structured issue endpoint: https://peekpaper.com/content/editions/YYYY/MM/DD.json
- Source policy: https://peekpaper.com/robots.txt
- Pilot observations: 2026-08-10 and 2026-08-11 issues, observed 2026-08-17

Peekpaper is used only as a mutable, reference-only discovery source. The
repository stores bounded metadata fixtures and original review annotations;
it does not store or redistribute Peekpaper screenshots, origin-site assets,
internal ranking fields, capture identifiers, or CDN keys. The adapter is
original design-craft code, network access is opt-in, and source material does
not become product authority or a training corpus.

## Fusion-layer policy

- Keep upstream directories pristine.
- Do not automatically overwrite local fusion rules from upstream updates.
- Preserve license notices for copied or derived code and substantial text.
- Prefer original integration rules that cite upstream ideas rather than blind
  copy-paste.
