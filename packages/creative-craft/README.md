# creative-craft

An Agent Skill for distinctive campaign concepts, commercial copy, art
direction, production-ready image and video briefs, evidence-aware critique,
and traceable creative production when the work actually needs it.

```text
context -> routes -> direction -> production -> evaluation -> delivery -> learning
```

> 中文定位：面向真实创意任务的创意策略、创意导演、生成式图像与视频生产、评估迭代和交付治理系统。

Creative Craft is not a prompt collection or a paperwork generator. It turns a
vague idea, an incomplete brief, or an existing asset into usable creative work:

- what the work must achieve;
- who it is for and what tension it should unlock;
- which genuinely different creative routes are worth pursuing;
- how the selected route should look, move, sound, and communicate;
- how to produce image and video assets with provider-aware execution packs;
- what was observed, inferred, hypothesized, accepted, rejected, or left unknown;
- how variants are evaluated, refined, adapted, packaged, and learned from.

It has two operating depths:

- **Quick Craft is the default.** The Agent delivers the requested concept,
  copy, prompt, treatment, shot plan, or critique directly, using only the
  structure that improves the answer.
- **Traceable Project is opt-in.** Multi-asset or multi-agent campaigns can add
  schemas, immutable authority snapshots, execution receipts, inspections,
  approvals, provenance, and delivery verification.

The schemas and CLI support the creative work; they are not the product's
default response shape.

## Status

The working tree is an unreleased **`0.3.2` candidate**. It adds
direction-gated refinement and Grok discovery evidence without changing public
artifact contracts or adding a Provider adapter. Version **`0.3.0`** made Quick
Craft the default Agent path, moved the evidence-bound runtime behind an
explicit Traceable Project mode, narrowed automatic routing, and added a
repository-only text A/B evaluation harness. It also includes first-class
`creative-craft.copy-sheet.v1` authority, public-copy approval gates, a v2
copy-bound Project Manifest, modular portable runtime/test boundaries, safe
atomic writes, indexed `uniqueItems` validation, and evidence-backed Agent
creative-quality improvements. The latest published and installable GitHub
release is the immutable `v0.3.0` tag.

Company-specific Brand Packs and non-authoritative Reference Packs remain
private, portable, and separate from this public method. The fictional example
contains reviewed internal copy, not real Provider output or owner-approved
public copy.

The package deliberately does **not** make network calls or incur generation
costs. It prepares and validates production jobs. Direct provider adapters are
separate, opt-in roadmap items so the creative method remains portable and
provider changes do not destabilize the core.

## Product boundary

Use Creative Craft for:

- creative briefs, campaign territories, concepts, big ideas, hooks, and
  communication systems;
- art direction, visual worlds, copy hierarchy, narrative structures, motion
  language, sound direction, treatments, storyboards, and shot plans;
- generation and editing plans for images, especially OpenAI GPT Image 2;
- generation, reference, extension, and editing plans for video, especially
  ByteDance Seedance;
- analysis and critique of existing images, videos, campaigns, moodboards,
  scripts, storyboards, and prompt packs;
- controlled iteration, channel adaptation, delivery specifications, asset
  provenance, and creative learning.

Do not use Creative Craft as a replacement for:

- content calendars, KOL/KOC planning, full brand strategy, or media buying;
- `design-craft` when the target is product UI/UX, interaction design, design
  systems, frontend implementation, or product presentation quality;
- `review-craft` when the target is software engineering quality;
- media-buying attribution, legal advice, model safety bypassing, deepfake
  impersonation, or unlicensed use of third-party likeness, brands, music, or
  copyrighted material;
- a full nonlinear editor, compositing suite, color-grading tool, DAM, or
  production management system.

## What makes it different

Creative Craft requires:

1. **Authority before aesthetics.** `BRAND.md`, `CREATIVE.md`, source assets,
   rights, channel constraints, and live output evidence outrank generic taste.
2. **Strategy before style.** Objective, audience, tension, insight,
   proposition, and desired response are separated from execution.
3. **Copy is governed authority.** Strategy, proof, exact units, evidence,
   render method, and approval live in one Copy Sheet instead of drifting across
   prompts and layouts.
4. **Distinct routes, not cosmetic variants.** Concepts must differ in creative
   mechanism, not merely color, camera, or art style.
5. **Model-agnostic core, provider-specific execution.** Current capabilities
   live in dated provider profiles instead of leaking into timeless rules.
6. **Reference roles.** Every reference states what it controls: identity,
   geometry, composition, lighting, material, motion, sound, typography, or
   continuity.
7. **Change/preserve contracts.** Editing instructions explicitly separate what
   may change from what must remain invariant.
8. **Evidence-aware critique.** Observation, interpretation, performance
   hypothesis, decision, and remaining unknowns are never collapsed together.
9. **Controlled iteration.** A revision changes one primary variable unless a
   deliberate rebuild is authorized.
10. **Evidence-gated evaluation.** Scores are comparative aids, not objective
   truth, and are withheld when rights, brief, deliverable, or evidence coverage
   is inadequate.
11. **Provenance and delivery integrity.** Source rights, model/provider,
    prompt, input roles, output specifications, versions, and checksums remain
    traceable.

## The CRAFT operating loop

`CRAFT` is the compact operating model:

- **C — Context:** understand the objective, audience, product, evidence,
  constraints, source assets, rights, and distribution environment.
- **R — Routes:** develop genuinely different creative mechanisms, then select
  with an explicit rationale.
- **A — Art direction:** lock message hierarchy, visual world, narrative,
  performance, motion, sound, references, invariants, and deliverables.
- **F — Fabrication:** produce provider-aware image and video jobs, generate or
  edit assets, inspect actual outputs, and record receipts.
- **T — Testing:** critique, compare, refine, adapt, package, measure, and feed
  learning back into the next brief.

The full Traceable Project workflow is:

```text
frame -> inspect -> research -> brief -> diverge -> select -> direct
      -> produce -> inspect output -> refine -> adapt -> deliver -> learn
```

A task may enter at any stage. Quick Craft should not force a bounded request
through every stage. The Agent reconstructs only the upstream authority needed
to avoid false downstream claims.

## Modes

- `understand`: analyze an idea, brief, reference set, or existing asset.
- `brief`: create or repair creative authority.
- `concept`: generate, separate, compare, and select creative routes.
- `direct`: produce a treatment, art direction, storyboard, shot plan, copy
  hierarchy, motion language, or sound direction.
- `image`: prepare a GPT Image 2 generation or editing job.
- `video`: prepare a Seedance generation, reference, extension, or editing job.
- `campaign`: orchestrate a cross-format creative system and variant matrix.
- `critique`: perform a read-only creative review.
- `refine`: improve an authorized existing direction or output.
- `adapt`: resize, reframe, localize, version, or translate a locked direction.
- `deliver`: validate files, provenance, manifests, and handoff completeness.

Choose the smallest mode that covers the request. Combined production follows
one causal order: understand, lock authority, develop/select, direct, fabricate,
inspect actual output, refine, validate, then deliver.

## Optional Traceable Project authority files

A project may seed:

- `BRAND.md` — durable brand identity, audience, voice, visual codes, proof,
  claims boundaries, and non-negotiables;
- `CREATIVE.md` — current job objective, audience tension, proposition,
  selected concept, creative direction, invariants, and approval state;
- `DELIVERABLES.md` — channel slots, ratios, sizes, durations, languages,
  variants, copy, safe areas, naming, deadlines, and owners;
- `asset-ledger.json` — source identity, role, rights, consent, checksum, and
  allowed use.

These are not required for Quick Craft. In a Traceable Project, unresolved
authority must be named as an assumption rather than silently invented.

## Public core, private packs, immutable projects

Do not add company knowledge, claims, internal links, or proprietary assets to
this repository. Use three independent lifecycles:

```text
creative-craft/             public generic method, schemas, and tooling
acme-brand-pack/            private Primary Brand authority: who we are
acme-reference-library/     private reference intelligence: who we learn from
campaign-project/           private work: what we make now
```

A Brand Pack is deliberately thin. It contains only curated authority needed
for creative execution: brand, products, approved claims, visual and verbal
systems, channel rules, rights/approvals, and an asset ledger. Large binaries
stay in the team's DAM, drive, or object store; the ledger keeps stable URIs,
SHA-256 identity, rights, consent, and allowed use. Small approved assets may be
stored locally under the private Brand Skill.

When a project binds a Brand Pack, Creative Craft copies only the manifest,
registered authority files, Brand Pack ledger, and safe local assets into
`.creative-craft/brand-snapshot/`. It also projects the pack's `brand` authority
to the project `BRAND.md`, merges brand assets into the project ledger, and
records source ref/commit plus content digests in `brand-binding.json`. The
project never uses a live symlink, so later Brand Skill edits cannot rewrite
historical project authority. `update-brand-snapshot` is explicit, backed up,
lineage-recorded, validated, and rolled back on failure.

Draft packs remain useful for exploration, but a bound draft pack blocks a Job
from becoming `ready`. Only reviewed source material should be used to mark a
pack `approved`; the initializer never invents claims, facts, rights, or an
approval.

A Reference Pack is a separate, non-authoritative research layer for brands,
companies, teams, agencies, creators, campaigns, products, visual systems,
films, photography, packaging, editorial systems, social accounts, or other
useful entities. It records evidence-classed observations, transferable
principles, non-transferable expression, applicable contexts, source identity,
and asset-use policy. It must declare
`may_override_primary_brand: false`; reference intelligence can inform a route
or direction but can never redefine identity, product facts, claims, exact
copy, rights, product geometry, or primary visual/verbal authority.

A project can bind multiple Reference Packs. Each binding copies a complete
snapshot to `.creative-craft/reference-snapshots/<pack-id>/`, records selection
under `.creative-craft/reference-bindings/`, archives immutable predecessors
under `.creative-craft/reference-lineage/<pack-id>/`, and merges only assets
used by the selected reference entities. A `reviewed` Pack must copy every
registered source snapshot and verify its SHA-256; a URI or evidence label alone
is insufficient. `update-reference-snapshot` updates one pack without rewriting
the Primary Brand Pack or other Reference Packs. Draft references produce an
exploratory warning but do not block a Job from becoming `ready`; revoked packs
fail validation, and superseded packs remain readable in historical projects
but cannot be used for a new binding or update. Public visibility is never
treated as generation-input permission.

## Versioned artifacts

The current contracts are:

- `creative-craft.brief.v1`
- `creative-craft.asset-ledger.v1`
- `creative-craft.concept-routes.v1`
- `creative-craft.critique.v1`
- `creative-craft.project-manifest.v1`
- `creative-craft.project-manifest.v2`
- `creative-craft.creative-direction.v1`
- `creative-craft.copy-sheet.v1`
- `creative-craft.image-job.v2`
- `creative-craft.video-job.v2`
- `creative-craft.execution-receipt.v1`
- `creative-craft.output-inspection.v1`
- `creative-craft.revision-lineage.v1`
- `creative-craft.evaluation.v2`
- `creative-craft.delivery.v2`
- `creative-craft.brand-pack.v1`
- `creative-craft.brand-binding.v1`
- `creative-craft.reference-pack.v1`
- `creative-craft.reference-binding.v1`
- `creative-craft.reference-binding-history.v1`

The v1 Manifest, job, evaluation, and delivery contracts remain readable for
migration. They are never silently upgraded or approved. New projects seed
Project Manifest v2 with `copy_policy=required`; each image/video Job binds one
Copy Sheet and explicit copy-unit references. Draft Copy Sheets are limited to
exploration, reviewed Copy Sheets can support internal-ready Jobs, and public
delivery requires an approved public Copy Sheet with a named owner. Approved
public copy cannot rely on `HYPOTHESIZED` or `UNVERIFIED` evidence.

Job v2 can declare only `draft`, `ready`, or `superseded`; generated, inspected,
approved, and delivered states are derived from receipts, files, digests,
inspections, and delivery evidence.

Schemas live under `skills/creative-craft/schemas/`. Human-oriented templates
live under `skills/creative-craft/templates/`.

## Provider profiles

Provider facts are dated and isolated:

- `providers/openai-gpt-image-2.json`
- `providers/bytedance-seedance-2.5.json`
- `providers/surfaces/*.json`

The core skill may say “use a low-cost draft pass before a final pass.” Only a
provider profile may state current model names, size limits, reference counts,
background support, or API availability.

## Repository layout

```text
creative-craft/
├── .codex-plugin/
├── .github/workflows/
├── adapters/
├── docs/
├── examples/
├── scripts/
├── skills/creative-craft/
│   ├── SKILL.md
│   ├── providers/
│   ├── references/
│   ├── schemas/
│   ├── scripts/
│   └── templates/
├── tests/
├── package.json
├── sources.lock.json
└── VERSION
```

`skills/creative-craft/` is the canonical installable runtime. Repository-root
files provide governance, CI, examples, and release support.

See the repository-only [video/image upstream register](docs/upstream-absorption.md)
for pins, licenses and maintenance, and [image tools](integrations/image-production/README.md)
for local editable posters and acceptance.

## Install as an Agent Skill

Distribution is **GitHub-only**. The npm package name is reserved for package
metadata and Pi discovery, but this project is private-to-npm and is not
published to the npm registry.

Pi is a Tier 1 host. Check out a verified craft67 commit, then install its
package subdirectory globally or for one project:

```bash
pi install /path/to/craft67/packages/creative-craft
pi install -l /path/to/craft67/packages/creative-craft
```

Codex is a Tier 1 host. Ask the built-in `skill-installer` to install
`bigKING67/craft67`, path `packages/creative-craft/skills/creative-craft`,
pinned to a verified craft67 commit, or run:

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo bigKING67/craft67 \
  --ref <verified-craft67-commit> \
  --path packages/creative-craft/skills/creative-craft
```

The skill becomes available to Codex on the next turn/session. A generic Agent
host can clone the repository and use the atomic installer:

```bash
python3 scripts/install_skill.py --target /path/to/host/skills
```

For a local Codex/Grok setup where both hosts discover the shared Agents Skill
root, install one canonical copy:

```bash
python3 scripts/install_skill.py --target ~/.agents/skills
```

Grok Build discovery is documented under `adapters/grok/`. The `0.3.2`
candidate verifies Skill discovery without a model call, but does not yet claim
Grok Tier 1 runtime behavior.

The installer stages on the target filesystem, validates the copy, writes
`INSTALL_PROVENANCE.json`, atomically swaps it into place, and preserves the
previous installation as a backup when `--force` is used. Claude and Cursor
directories currently document thin-adapter expectations; they are not Tier 1
runtime claims.

## Quick start

Creative Craft declares **Python `>=3.10`** for the portable runtime. The CI
matrix covers the minimum plus Python 3.11 and 3.13; no third-party dependency
is required for the installed leaf CLI. Repository Schema parity and lint gates
use `requirements-dev.txt`.

Run the portable repository checks:

```bash
python3 scripts/validate.py
```

Run the full JSON Schema gate used by CI:

```bash
python3 -m pip install -r requirements-dev.txt
python3 scripts/validate_schemas.py
```

Run the repository package self-test from a checkout:

```bash
python3 skills/creative-craft/scripts/creative_craft.py self-test
```

The same command automatically selects installed-runtime scope when invoked
from a leaf Pi, Codex, or generic Skill installation. Use `--json` to record the
selected `scope` and separate repository/runtime validity. Release verification
uses `self-test --scope runtime --json` to test the exact leaf inside the `.tgz`
even though the surrounding archive also contains repository metadata.

Inspect the CLI:

```bash
python3 skills/creative-craft/scripts/creative_craft.py --help
```

For Traceable Project work, seed planning scaffolds without overwriting
existing files:

```bash
python3 skills/creative-craft/scripts/creative_craft.py seed \
  --target /path/to/project
```

A seed contains planning-authority scaffolds, Critique, draft Jobs, Evaluation,
and a planned Delivery manifest. Placeholder scaffolds are not approved or
locked authority. The seed does not create an Execution Receipt, Output
Inspection, or Revision Lineage: those lifecycle artifacts must be created only
after the corresponding real attempt, output inspection, or revision exists.
Quick Craft does not require `seed` or any JSON artifact.

Initialize and validate a separate private Brand Skill using placeholder-only
authority:

```bash
python3 skills/creative-craft/scripts/creative_craft.py init-brand-pack \
  --target /path/to/acme-brand-pack/skills/acme-brand \
  --brand-id acme \
  --brand-name "Acme" \
  --owner brand-operations

python3 skills/creative-craft/scripts/creative_craft.py validate-brand-pack \
  --root /path/to/acme-brand-pack/skills/acme-brand
```

After the Brand Pack has been populated and reviewed, bind its current content
to a new project. Source provenance is optional but strongly recommended for a
team repository:

```bash
python3 skills/creative-craft/scripts/creative_craft.py seed \
  --target /path/to/campaign-project \
  --brand-pack /path/to/acme-brand-pack/skills/acme-brand \
  --brand-source-uri https://git.example/acme-brand-pack.git \
  --brand-source-ref v1.0.0 \
  --brand-source-commit <full-commit-sha> \
  --imported-by <identity>

python3 skills/creative-craft/scripts/creative_craft.py update-brand-snapshot \
  --target /path/to/campaign-project \
  --brand-pack /path/to/acme-brand-pack/skills/acme-brand \
  --reason "Adopt reviewed brand authority v1.1.0" \
  --brand-source-uri https://git.example/acme-brand-pack.git \
  --brand-source-ref v1.1.0 \
  --brand-source-commit <full-commit-sha> \
  --imported-by <identity>
```

Initialize a separate private Reference Skill, add evidence and entities under
review, save every reviewed source under the private Skill, set its
`snapshot_path` and SHA-256 in `source_references`, then bind any number of
Reference Packs to an existing project:

```bash
python3 skills/creative-craft/scripts/creative_craft.py init-reference-pack \
  --target /path/to/acme-reference-library/skills/acme-creative-references \
  --pack-id acme-creative-references \
  --name "Acme Creative References" \
  --owner creative-operations
```

Before setting the Pack to `reviewed`, capture each source inside the private
Reference Skill and register its real digest:

```json
{
  "source_id": "source-example",
  "authority": "official",
  "uri": "<original-source-uri>",
  "captured_at": "2026-08-04T00:00:00Z",
  "snapshot_path": "sources/source-example.md",
  "sha256": "<sha256-of-sources/source-example.md>",
  "notes": "Reviewed source snapshot."
}
```

Then validate and bind:

```bash

python3 skills/creative-craft/scripts/creative_craft.py validate-reference-pack \
  --root /path/to/acme-reference-library/skills/acme-creative-references

python3 skills/creative-craft/scripts/creative_craft.py bind-reference-pack \
  --target /path/to/campaign-project \
  --reference-pack /path/to/acme-reference-library/skills/acme-creative-references \
  --select reference-entity-a \
  --reference-source-uri https://git.example/acme-reference-library.git \
  --reference-source-ref v0.1.0 \
  --reference-source-commit <full-commit-sha> \
  --imported-by <identity>

python3 skills/creative-craft/scripts/creative_craft.py update-reference-snapshot \
  --target /path/to/campaign-project \
  --reference-pack /path/to/acme-reference-library/skills/acme-creative-references \
  --select reference-entity-a \
  --select reference-entity-b \
  --reason "Adopt reviewed reference revision"
```

Omit `--select` to select all entities in a non-empty pack. A newly initialized
empty draft library validates but cannot be bound until at least one reference
entity exists.

Validate and compile an image job:

```bash
python3 skills/creative-craft/scripts/creative_craft.py validate \
  --file examples/premium-haircare-launch/image-job.json

python3 skills/creative-craft/scripts/creative_craft.py compile-image \
  --file examples/premium-haircare-launch/image-job.json \
  --output /tmp/image-prompt.md
```

Validate and compile a video job:

```bash
python3 skills/creative-craft/scripts/creative_craft.py compile-video \
  --file examples/premium-haircare-launch/video-job.json \
  --output /tmp/video-prompt.md
```

Evaluate a route or output:

```bash
python3 skills/creative-craft/scripts/creative_craft.py score \
  --file examples/premium-haircare-launch/evaluation.json \
  --root examples/premium-haircare-launch
```

Validate the content-bound project graph and inspect derived state:

```bash
python3 skills/creative-craft/scripts/creative_craft.py doctor-project \
  --root examples/premium-haircare-launch --json

python3 skills/creative-craft/scripts/creative_craft.py validate-project \
  --root examples/premium-haircare-launch

python3 skills/creative-craft/scripts/creative_craft.py project-status \
  --root examples/premium-haircare-launch --json
```

`doctor-project` is read-only. It reports invalid project graphs and known
Creative Craft JSON artifacts that exist beside the manifest but are not
registered in it. A byte-identical bundled template is classified as
`seed_template_residue`; the command never registers or deletes a file because
file presence alone does not prove that the corresponding lifecycle event
happened.

Hash a source or output for the asset ledger:

```bash
python3 skills/creative-craft/scripts/creative_craft.py hash \
  --file path/to/asset.png
```

## Agent quality evaluation

The repository includes a maintainer-only text evaluation harness. It compares
a no-Skill baseline, a selected committed comparison revision, and the worktree
candidate across nine creative cases, then uses blind scoring and four routing
cases. The internal `baseline` and `current` evidence keys remain stable for old
report readability; they do not identify installed Skill copies:

```bash
python3 scripts/evaluate_agent_quality.py check --json
python3 scripts/evaluate_agent_quality.py run
python3 scripts/evaluate_agent_quality.py judge --run-dir dist/evals/agent-quality/<run>
python3 scripts/evaluate_agent_quality.py route --run-dir dist/evals/agent-quality/<run>
python3 scripts/evaluate_agent_quality.py report --run-dir dist/evals/agent-quality/<run>
```

Runs use temporary `0700` Codex and user homes, isolate `CODEX_HOME`,
`HOME`/`USERPROFILE`, XDG, shell-profile, and platform application-data roots,
symlink only the existing Codex auth file without reading or copying it, install
no global Skill, use an empty workspace, and invoke Codex with
ephemeral/read-only/ignore-config flags. Event evidence must prove that the
no-Skill baseline read no Creative Craft entrypoint and that comparison and
candidate calls read only their digest-bound isolated copies; otherwise the run
fails before more judging or routing calls are spent. When the local Codex uses
a custom model provider, the harness extracts only an
allowlist of non-secret transport fields (`name`, `base_url`, `wire_api`, auth
mode, and WebSocket support) and passes them as explicit CLI overrides; it never
copies the user config.

The committed comparison is exported into a temporary directory and removed at
the end of generation. Generated evidence stays under ignored
`dist/evals/agent-quality/` and is bound to the model, reasoning level,
comparison revision, and candidate Skill digest.

This live evaluation is intentionally outside CI because it incurs model cost.
It is text-only: no image or video Provider is called, and a blind model judge
is not a substitute for real output inspection or human creative approval. Each
variant has one generated sample and one blind judgment per case, so repeated
runs may vary. A selected-case canary can be reported without routing evidence,
but it remains `PARTIAL`; only the complete quality and routing suites can pass
the release-oriented acceptance gate.

## Relationship to the Craft family

- `design-craft` asks: **Is this product surface right, usable, coherent,
  tasteful, accessible, and well implemented?**
- `review-craft` asks: **Is this codebase correct, maintainable, performant,
  testable, and supported by reproducible evidence?**
- `creative-craft` asks: **Is this communication idea strategically right,
  creatively distinctive, executable in image/video, faithful to its
  references, and ready to learn from?**

The packages may cooperate, but none should become a catch-all. Creative Craft
can hand a campaign landing-page direction to Design Craft; Design Craft can
hand implementation quality to Review Craft.

## Release philosophy

A repository score is not shipped. Release readiness is represented by
independent gates:

- source and schema integrity;
- provider-profile freshness;
- example and test validity;
- rights and provenance coverage;
- current generation-output evidence;
- host portability;
- delivery completeness.

Released version `0.3.0` proves copy-bound contract validation, named-owner
public-delivery gating, legacy v1 readability, modular installed runtime, safe
write boundaries, measured near-linear `uniqueItems` scaling, and improved
Agent creative output through synthetic fixtures, package gates, and an
isolated text evaluation. It still does not claim that
unobserved image or video output is production quality, that real Golden Evals
are complete, that owner approval exists for the fictional example, or that
Provider network adapters exist.

The unreleased `0.3.2` candidate adds direction-gated refinement and Grok
discovery evidence. It does not change those Provider-output limitations.

Maintainers build one release candidate from a clean commit after installing
`requirements-dev.txt`:

```bash
python3 scripts/build_release.py
```

After `npm pack`, the builder validates every archive member before extraction,
rejects path escapes and links, then runs the leaf self-test plus Reference
bind/update/validation/rollback E2E against the exact generated `.tgz`. The
ignored `dist/release/` directory contains that `.tgz`, its SHA-256 file, and a
command-bound validation summary for the GitHub Release. It is not an npm
publication workflow.
