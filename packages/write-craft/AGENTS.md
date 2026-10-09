# Write Craft repository guidance

This repository ships exactly one installable product: `skills/write-craft/`.
Root-level files exist for source governance, evaluation, validation, and
packaging; they must not become runtime requirements for the installed Skill.

## Current boundary

- Turn complex technical proposals and project material into decision-ready
  documents for non-technical readers, with Simplified Chinese as the default
  when the user writes in Chinese.
- Preserve evidence, uncertainty, constraints, trade-offs, and the difference
  between planned, implemented, and verified behavior.
- Project READMEs are a second scenario: help prospective users judge fit and
  start using the project. Their rules live in `references/readme.md`; the
  decision-document scenario stays the default.
- Do not absorb advertising copy, product UI microcopy, document-platform
  operations, complete API reference manuals, runbooks, or developer tutorials
  into the trigger surface.
- Prefer a useful complete draft when the supplied material is sufficient.
  Ask only for missing information that can change the decision, scope, cost,
  acceptance, or material risk.

## Adding a scenario

`SKILL.md` holds only rules that apply to every scenario, plus the scenario
routing table. Everything specific to one document type lives in that
scenario's reference under `skills/write-craft/references/` (flat; the
validator matches links to top-level files). A new scenario needs:

- a reference that states its reader, reading order, the commitments that
  **preserve** protects, any delivery companion, and every core rule it
  overrides, such as allowing labeled hypotheses in a postmortem;
- one row in the routing table and, when it widens triggering, a description
  update that keeps the existing routing phrases checked by `validate.py`;
- behavior cases for the scenario and a routing case that separates it from
  neighboring exclusions.

Do not put a scenario's exception into `SKILL.md`; put the override in the
scenario reference. Keep `SKILL.md` within 200 lines (`validate.py` enforces
it): Codex (GPT-5.5) through Pi often reads only the first 200 lines of the
entrypoint, and a rule moved out of the entrypoint loses salience for it.

## Source and change discipline

- Keep `upstreams/` pristine. Review pinned sources, then write independent
  behavior into the fusion layer under `skills/write-craft/`.
- Treat licenses per source path. Do not copy text from a source whose reuse
  terms are absent or unclear.
- Keep source validation, installation, commit, push, versioning, tagging, and
  release as separate authorization layers.
- Preserve unrelated work. Do not write to global Skill roots unless the user
  explicitly authorizes installation.
