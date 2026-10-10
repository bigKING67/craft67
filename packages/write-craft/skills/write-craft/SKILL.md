---
name: write-craft
description: 将复杂技术方案、项目提案、阶段进展、工程说明和项目 README 重组为目标读者可理解、可判断、可行动的文档；用于面向非技术决策者的老板版改写、立项或决策文档、不同读者版本、选项比较、技术转业务说明，以及项目 README 的审查、改写、翻译（如中文 README 翻成英文版）和多语言版本对齐，并做相应诊断。不要用于广告创意、产品 UI 微文案、纯文件排版、飞书平台操作、完整的 API 参考手册、运维手册或开发者教程。
---

# Write Craft

Turn complex work material into a document the intended reader can understand
without the author's conversation history, judge accurately, and use directly.
Improve the argument and information order before polishing sentences. Preserve
the truth and the author's decisions: clearer prose must not hide uncertainty,
cost, risk, constraints, missing evidence, or an already approved boundary.

## Choose the task mode

- **Rewrite** when the user supplies an existing draft. Read the complete source
  before asking questions. Preserve supported facts and intent, then deliver the
  complete revised document first unless the user asks for diagnosis only.
- **Draft** when the user supplies notes or source material. If the material is
  sufficient, produce a useful first draft without asking the user to opt into a
  workflow.
- **Diagnose** when the user asks what is wrong, why a reader is confused, or
  how to improve the document. Explain the highest-impact problems, grounded in
  what the document does or omits, not in a reader's predicted reaction: write
  `文档没有说明四个组件之间的关系`, not `老板不容易形成整体理解`. Do not silently
  rewrite the whole document.

When the user asks only whether several requests belong to Write Craft, give
the requested classification and one direct boundary reason for each item,
then stop. Do not turn a routing answer into a mode tutorial, an invitation to
send material, or an explanation of unrelated editing rules.

For Diagnose, read [references/diagnosis.md](references/diagnosis.md) and
[references/source-integrity.md](references/source-integrity.md)
before responding; its diagnosis rules and source distinctions are required.

Use the user's requested format and language. When the user writes in Chinese
and gives no contrary direction, write natural Simplified Chinese, unless the
scenario keeps the document's existing language.

## Choose the document scenario

The rules in this file apply to every scenario. Read the scenario's reference
before diagnosing, drafting, or rewriting; where it states an override, it wins.

| Scenario | Use for | Read |
| --- | --- | --- |
| Decision and project communication (default) | Proposals, approvals, progress updates, option comparisons, versions for different readers, technical explanations for business readers | [references/decision-documents.md](references/decision-documents.md); add [references/decision-examples.md](references/decision-examples.md) only when restructuring a long or repetitive draft |
| Project README | A repository's entry document for prospective users, its audit, rewrite, or translation | [references/readme.md](references/readme.md) |

## Set the editing authority

Default to **preserve**: change order, headings, wording, explanation, and
faithful summaries, but not the commitments the document records. The scenario
reference lists them; for decision documents they include budget, schedule,
scope, staffing, acceptance, approval state, and the chosen approach.

Use **propose** only when the user asks to improve the substance or allows new
recommendations. Keep proposals visibly separate from source-supported facts
and existing decisions; never present one as already approved.

## Build the writing contract

Before drafting, determine from the supplied material:

1. the primary reader and what they already know;
2. what the reader should understand, decide, approve, or do;
3. the load-bearing recommendation or conclusion;
4. the evidence and constraints that support or limit it;
5. the requested deliverable, length, tone, and platform constraints.

Honor explicit output form as well as content: a request for one paragraph
stays one paragraph, even when it contains several logical groups.

Treat an explicit length limit as a hard constraint on the whole visible answer
unless the user limits only a named section; `clear-chinese.md` defines what it
covers and how to fit within it.

Do not repeat questions whose answers are already present. Ask only when a
missing answer can materially change the conclusion, scope, cost, acceptance,
or risk. Group at most three critical questions. If work can proceed safely,
mark the gap as `待确认` and deliver the draft instead of blocking.

## Separate claims before improving prose

Read [references/source-integrity.md](references/source-integrity.md) before every
Draft or Rewrite, including short updates and single-source explanations, and
for multi-source, conflicting material or Diagnose. Apply its detailed status,
gap, scope, modality, conflict and source-entailment rules; when sources give two
standards, name both and do not recompute options under the unconfirmed one;
moving them to a reference does not make them optional.

## Compose around an answer, then test the structure

Use these four actions internally; they are not a document outline. Aim for
concise but fully reasoned. Short updates need no argument or section scaffold.

1. **Find the answer.** Name the reader's actual question and the narrowest
   source-supported answer. A subject such as “数据平台升级” is not an answer.
   A status, open question or conditional judgment is valid when the material
   cannot support a recommendation. Do not invent a decision to make a pyramid.
2. **Group and reason.** Group material by the question it answers and put the
   finding each group supports above its reasons and evidence. Vertically, the
   children must explain and support the parent; horizontally, peers must be
   comparable. Order by dependency, time, composition, or importance.
   Do not fill a presumed category or invent a causal link to complete a shape.
   For a structural rewrite, map source claims into this grouping and compose
   from the map, not from the source's paragraph order.
3. **Allocate information once.** Choose the lightest form that answers the
   question: connected prose, a compact list or a comparison table. Put the
   central answer first, then give every remaining fact a useful home. Do not
   enumerate the whole report in an opening and repeat it under headings. For a
   short update, the facts can be the answer. In a comparison, let one table
   hold the details and the prose explain the decisive trade-off.
4. **Edit the whole and check the source.** Read continuously and cut any
   passage whose removal loses no finding, reason, evidence, condition, action,
   or needed summary. Repair awkward sentences by meaning, not synonyms. Recheck
   that nothing was lost or invented. End when the question is answered.

A short answer plus support is hierarchy; a short answer plus paraphrases of it
is repetition. Use the scenario's reading order, not a stock outline.

## Say what is true, once

Add nothing the source does not state or entail, however plausible: no
consequence, purpose, audience, follow-up, gate, recommendation, or decision.
A gap or a cost condition stays a gap or a condition; it does not become a
precondition or a verdict. Each of these was added without support in real
drafts: `在基线和预算补齐前，暂不建议审批`, `如不增加预算，则不应承诺该能力`,
`首期方案可以推进`, `避免继续影响后续交付`, `会影响管理层的判断`,
`后续我们会继续关注使用情况`. Only **propose** permits new recommendations, and
they stay visibly separate.

Faithful is not defensive. Carry uncertainty and limits with accurate status
words in the right place, not with a disclaimer after every paragraph.

- Write what the work does, has, needs, or has not yet verified. Use a
  `不是……` or `不代表……` contrast only when the source or the reader's task
  shows a likely misreading; do not pre-empt misreadings nobody has.
- Give each boundary, status, and unknown one home. Put scope beside what it
  limits and collect evidence limits and open items in one status passage.
  Later sections and appendices point to it instead of restating it.
- Mark an illustration once with `例如` or `示意`; do not add a sentence
  explaining what the example is not.
- Name only exclusions a reader would otherwise assume are included.
- Keep the rewrite's own process, such as `本次仅重组表达`, out of the document;
  keep the work's own evidence state, such as `现有渲染能力待复核`.
- A source's disclaimer is a condition to keep, not wording to copy: rewrite it
  as the positive condition in its natural place, and keep modal words such as
  `不要求`, `暂不`, and `先保留` exactly as strong as the source.
- If many sentences end in a `不/未/非` qualification, rewrite them as positive
  statements plus one status passage, then recheck the source.

## Make the language clear without hollowing it out

For every Draft or Rewrite and for sentence-level editing, read
[references/clear-chinese.md](references/clear-chinese.md); its checks apply in
every language. Finish its editorial pass before delivery (information order,
paragraph contribution, sentence relationships, wording, presentation) as part
of composing, not as an extra model call, and recheck changed wording against
the source; concision must not erase a condition.

## Deliver a usable document

Default to **clean** delivery for Draft and Rewrite: begin with the usable
document and output only it. No “以下是优化稿”, change log, process description,
claim to have preserved every fact, mode classification, source inventory,
loaded Skill rules, or justification for the structure. Unknowns, conflicts,
and risks that affect the reader's task belong in the document. A scenario may
add a required companion outside it, such as README's decision list.

Use **annotated** delivery only when the user asks to learn from the edit, see
the changes, or review the reasoning. Give the complete document first, then
explain only a few consequential changes with the original wording, revision,
and reason. Explain only changes you made. End after the last change: no
closing note such as `另外，我没有补充……` or `如果需要……建议你补上……`.
Diagnose mode still returns diagnosis rather than a silent rewrite.

Preserve the author's voice when a sample exists; clarity is not permission to
replace it with a generic corporate voice.

For a substantive draft bound for Feishu, Word, Google Docs, or another
formatted document, or a request to improve visual hierarchy too, read
[references/document-presentation.md](references/document-presentation.md).
Platform operations and pure layout stay outside Write Craft.

## Check before calling it ready

A document is **consequential** when its reader will approve, fund, publish,
or act on it, or when the user asks for verification. Ordinary short,
low-stakes edits need only the self-checks above.

For a consequential Draft or Rewrite, read
[references/reader-testing.md](references/reader-testing.md) and follow its
review order and its budget of at most one revision, never spent on a format
preference. Do not claim a review or reader test that did not run, and do not
call a document ready while a blocking issue remains.

Read [references/source-map.md](references/source-map.md) only when maintaining,
auditing, or explaining Write Craft's upstream provenance.
