# Project README

Use this reference when the user asks to audit, draft, rewrite, or translate a
project README or a comparable repository entry document. A complete API
reference manual, a runbook, or a changelog is a different document; a README
links to them instead of absorbing them.

The README is the reader's first view of the project and often the only one.
It also states the project's public contract: what the project does, how it is
used, and what it promises to keep stable. Its job is to let a prospective user
decide quickly whether the project fits, and leaving early after an accurate
"not for me" is a successful reading. Persuasion is not the goal.

## Contents

- Identify the reader and the project shape
- Order by the reader's decision
- Diagnose before rewriting
- Check the repository before editing files
- Rewrite rules
- Translated and bilingual READMEs
- Verify and deliver

## Identify the reader and the project shape

The primary reader is a prospective user or integrator, not a maintainer and
not the author. Maintainer content such as release steps, CI secret tables,
repository-structure tours, and debugging guides serves a different reader.

Decide what kind of project this is from the code and packaging, not from the
old README alone:

- a **library** whose value is its API: the reader judges the API before
  installing;
- an **application, CLI, service, or agent Skill** that is used without
  programming against it: setup comes right after a usage example, and an API
  section may not exist.

## Order by the reader's decision

Put the facts that decide fit earliest, and deeper detail only after a reader
has a reason to stay:

1. project name;
2. one sentence stating what it is and the need it serves;
3. short background only when the domain is unfamiliar to the expected reader;
4. a real usage example: command, code, or prompt with its observable result;
5. install or setup;
6. API overview, or a link to the full reference (for a library, this can come
   before install);
7. limits, caveats, supported platforms or versions;
8. pointer to contributing and maintainer documentation;
9. license.

Adapt the order to the project; do not add empty sections to complete it. A
license that restricts typical use, such as AGPL or SSPL, also needs a short
note near the top, because it can rule the project out before anything else.
Images that carry essential information belong in the repository, not only on
an external host.

## Diagnose before rewriting

Read the current README completely and compare it with the order above. Report
or fix the problems that actually appear, in order of reader impact:

- **Mixed audiences.** Maintainer procedures interleaved with user content.
  This is the most common and most damaging problem.
- **Deep detail first.** Internals, adapters, or architecture before the reader
  knows what the project is for.
- **Repeated facts.** The same requirement, version, or behavior stated in
  several places.
- **Outdated framing.** Text written when the project supported one tool,
  platform, or use case still leads after the scope grew. Check the code: the
  old text may be wrong, not only unbalanced.
- **Stale references.** Dead relative links, drifted version ranges, deleted
  files, commands that no longer exist.
- **Unlinked reference material.** Detailed docs exist in the repository but the
  README never points to them.

The rules in `diagnosis.md` still apply: ground each problem in
the supplied README and repository, not in an imagined reader's reaction.

## Check the repository before editing files

When editing README files in a repository rather than text pasted into the
conversation, do these checks first:

1. **Working tree state.** Rewrite the README as it exists in the current
   checkout, including uncommitted edits; they are usually the user's latest
   material. Never discard or revert them. Ask first only when uncommitted
   changes in the files you would touch look unrelated to the request.
2. **Pinned wording.** Search tests, CI configuration, and scripts for README,
   CONTRIBUTING, or exact headings. Know what is asserted before restructuring.
3. **Derived copies.** Package READMEs, website pages, or generated docs may
   duplicate the README. Update them deliberately or state that they are out of
   scope.

## Rewrite rules

- **Move maintainer content; do not delete it.** Put it in `CONTRIBUTING.md`
  or `docs/` and leave a link where it was. Reordering a README for its users
  is a structural rewrite: maintainer sections moved to the bottom are still a
  mixed audience. When the README was pasted rather than edited in a repository,
  deliver the moved content after the README as a block labeled only with its
  destination path; never drop it. When the user asked for a
  structural rewrite, moving content into an existing or new file of that kind
  is part of the task; for a wording-only request, leave structure alone and
  mention the mixed audience instead.
- **One home per fact.** If a detail lives in a reference document, link to it
  instead of restating it at length.
- **Usage shows the real interaction.** Use commands, code, and output that the
  code supports and a reader can copy. Never invent output; when it cannot be
  confirmed, show the command and omit or mark the result.
- **Re-verify every carried-forward claim against the code.** The old README is
  a source, not proof. Supported platforms, defaults, flags, and versions keep
  their actual status: implemented, experimental, planned, or unverified.
- **Prefer tables for scannable detail** such as options, compatibility, or
  environment variables. Keep explanatory prose for trade-offs.
- **Do not let pinned tests break silently.** When a test asserts exact
  headings or a file list that the rewrite changes, report it. Change the test
  only when the user asked for repository edits that include it; then assert
  the requirement, such as the presence of a link or the order of two install
  paths, and explain each changed assertion. Never weaken a test silently to
  make the docs pass.
- **The author's taste outranks this checklist.** Keep badges, wordmarks,
  charts, and other decorative elements unless the author agrees to remove
  them.

Editing authority still applies. Under **preserve**, restructure and clarify,
but do not change the project's stated scope, support promises, or license
terms. Recommending a new feature claim or support policy requires **propose**.

## Translated and bilingual READMEs

- Keep the README's existing language unless the user asks for a translation
  or a second version, even when the user writes to you in another language.
  Replies, diagnoses, and the decision list follow the user's language.
- Translate by meaning in the target language's technical-writing rhythm.
  Restructure sentences freely; sentence-by-sentence mapping produces
  translationese. For Chinese, apply `clear-chinese.md`.
- Keep a term in English when the target community actually uses the English
  term; translate it when a natural native term exists.
- Start every language version with a language-switch line, such as
  `[English](README.md) · 简体中文`, even when the original has none yet. It is
  the one allowed difference from the original and does not break parity. If
  you deliver only the translation, give the matching line for the original in
  your reply.
- Otherwise keep versions structurally parallel: same sections, tables, links,
  and code blocks, so parity can be checked mechanically.
- Deliver the translated file only. Do not append a translator's note about
  parity, choices, or differences; a choice the user must make goes in the
  reply, not in the file.
- Update in-page anchor links when translated headings change their anchors.

## Verify and deliver

Before reporting completion:

- check that every relative link and image path resolves;
- run every test or script that reads the README or CONTRIBUTING;
- read the final README from top to bottom as a newcomer and note where you
  would stop; if the stopping points arrive in the wrong order, revise the
  order.

Delivery depends on the input:

- **Pasted README text:** deliver the clean document as `SKILL.md` describes.
  When maintainer content moves out, deliver it as a separate block labeled
  only with its destination path, such as `CONTRIBUTING.md`; the label does
  not say where the content came from or why it moved.
- **Files edited in a repository:** the README itself stays free of process
  commentary, but the reply reports the changes as a short decision list: what
  moved where, what was removed and why, which test assertions changed, and
  which claims remain unverified. Reviewers can approve a list of decisions
  much faster than a prose diff.
