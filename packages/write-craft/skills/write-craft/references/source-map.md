# Source map

This file records method provenance for maintainers. Write Craft remains usable
without any upstream checkout.

| Upstream | Reviewed capability | Local decision | Local expression |
| --- | --- | --- | --- |
| Anthropic `doc-coauthoring` | Context gathering, iterative structure, fresh-reader testing | Partial, independently expressed | `SKILL.md`, `reader-testing.md` |
| Anthropic Skill authoring guidance | Concise instructions, progressive references, representative input/output examples | Selectively adopted | `SKILL.md`, `decision-documents.md` |
| Anthropic agent-evaluation guidance | Separate capability from regression evidence; calibrate model graders with people | Development guidance only | `reader-testing.md`, repository evals |
| Anthropic `internal-comms` | Internal communication formats | Reference only for a later release | Not in the current trigger surface |
| `writing-clearly-and-concisely` | Topic-focused paragraphs, concrete language, concision | Language-neutral principles only | `clear-chinese.md` |
| Composio `content-research-writer` | Research-assisted articles and section feedback | Reference only; outside current scope | Not in the current trigger surface |
| Arjun `plain-language` | Explain technical material without deleting precision or uncertainty | Selectively absorbed under MIT | `decision-documents.md`, `clear-chinese.md` |
| Pi Skill documentation | Progressive Skill loading and package integration boundaries | Packaging and validation guidance only | Repository tooling; no runtime dependency |
| tommy0103 `better-readme` (MIT) | Reader-order README audit, maintainer-content separation, repository pre-checks, translated-README parity | Independently expressed; behavior improvement not yet established | `readme.md`, scenario routing in `SKILL.md` |
| LifelongLazyLearner `qu-ai-wei` (MIT) and op7418 `Humanizer-zh` (MIT) | Protection order for edits, relation-preserving rewrites, hollow rhetorical frames, stacked adverbials, citation binding | Independently expressed; behavior improvement not yet established | `clear-chinese.md`, `source-integrity.md` |
| lijigang `ljg-writes` and selected `ljg-paper` guidance | Separate content review from Chinese editing; paragraph contribution, continuity, and reader-facing explanation | Independently expressed methods; behavior improvement not yet established | `SKILL.md`, `clear-chinese.md`, revised examples in `decision-documents.md` |

The pyramid-building method independently applies the grouping-to-insight
principle described at https://www.barbaraminto.com/concept (reviewed 2026-09-26).
No book text or course materials are reproduced; this is not a claim of having
read the complete book. Local application: `decision-documents.md` and the
entrypoint compose/group/edit workflow. Writing quality requires evaluation.

The project also consulted public Microsoft guidance on scannable content and
Google developer-documentation accessibility guidance. Public method guidance
in this table is not vendored and is not a runtime dependency.

See the repository-level `upstreams.lock.json`, `THIRD_PARTY_NOTICES.md`, and
`docs/upstream-absorption.md` for exact revisions and license handling.
The non-vendored ljg-skills review is pinned in `docs/upstream-absorption.md` at
`fdea0bea5133246de418d19015f65eeb18699623` (MIT); `ljg-plain` was reviewed only
as a supplementary reference, not adopted as a style or output contract.

## Reviewed candidates not admitted as upstreams

| Candidate | Reviewed revision | Decision | Reason |
| --- | --- | --- | --- |
| `aAAaqwq/AGI-Super-Team`, `feishu-doc-optimizer` | `b996aacc2987904c584316f91591f892ffdf5afd` (MIT) | Not admitted | Its useful hierarchy advice overlaps current guidance, while its tenant-specific reader and repeated whole-document browser deletion are outside Write Craft's runtime boundary. No source text, scripts, credentials, or destructive editing workflow were copied. The local presentation reference is an independent, platform-neutral response to live document evidence and the existing host document contract. |
