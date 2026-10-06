# Write Craft repository guidance

This repository ships exactly one installable product: `skills/write-craft/`.
Root-level files exist for source governance, evaluation, validation, and
packaging; they must not become runtime requirements for the installed Skill.

## V0.2 boundary

- Turn complex technical proposals and project material into decision-ready
  documents for non-technical readers, with Simplified Chinese as the default
  when the user writes in Chinese.
- Preserve evidence, uncertainty, constraints, trade-offs, and the difference
  between planned, implemented, and verified behavior.
- Do not absorb advertising copy, product UI microcopy, document-platform
  operations, or developer/API documentation into the V0.2 trigger surface.
- Prefer a useful complete draft when the supplied material is sufficient.
  Ask only for missing information that can change the decision, scope, cost,
  acceptance, or material risk.

## Source and change discipline

- Keep `upstreams/` pristine. Review pinned sources, then write independent
  behavior into the fusion layer under `skills/write-craft/`.
- Treat licenses per source path. Do not copy text from a source whose reuse
  terms are absent or unclear.
- Keep source validation, installation, commit, push, versioning, tagging, and
  release as separate authorization layers.
- Preserve unrelated work. Do not write to global Skill roots unless the user
  explicitly authorizes installation.
