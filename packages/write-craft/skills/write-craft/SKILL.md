---
name: write-craft
description: 将复杂技术方案、项目提案、阶段进展和工程说明重组为目标读者，尤其是非技术决策者，可理解、可判断、可行动的中文文档；用于老板版改写、立项或决策文档、不同读者版本、选项比较、技术转业务说明及相应诊断。不要用于广告创意、产品 UI 微文案、纯文件排版、飞书平台操作或面向开发者的 API 文档。
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
  how to improve the document. Explain the highest-impact structural,
  evidentiary, and language problems. Ground the diagnosis in observable
  features of the supplied document and its stated task, not an imagined
  reader's attention span, knowledge, or reaction. Do not silently rewrite the
  whole document.

When the user asks only whether several requests belong to Write Craft, give
the requested classification and one direct boundary reason for each item,
then stop. Do not turn a routing answer into a mode tutorial, an invitation to
send material, or an explanation of unrelated editing rules.

For Diagnose, read [references/source-integrity.md](references/source-integrity.md)
before responding; its diagnosis rules and source distinctions are required.

Use the user's requested format and language. When the user writes in Chinese
and gives no contrary direction, write natural Simplified Chinese.

## Set the editing authority

Default to **preserve** for rewrites and drafts based on an existing proposal.
You may change order, headings, wording, explanation, and faithful summaries,
but not budget, schedule, scope, staffing, acceptance, approval state, or the
chosen approach. This includes approved plans: do not redesign one into a pilot
or reopen a decision merely because another option reads better.

Use **propose** only when the user explicitly asks to improve the plan itself or
allows new recommendations. Keep proposed changes visibly separate from source-
supported facts and existing decisions; never write a new suggestion as though
it were already approved.

## Build the writing contract

Before drafting, determine from the supplied material:

1. the primary reader and what they already know;
2. what the reader should understand, decide, approve, or do;
3. the load-bearing recommendation or conclusion;
4. the evidence and constraints that support or limit it;
5. the requested deliverable, length, tone, and platform constraints.

Honor explicit output form as well as content: a request for one paragraph
stays one paragraph, even when it contains several logical groups.

Treat an explicit length limit as a hard deliverable constraint. Unless the
user limits only a named section, the limit applies to the entire user-visible
answer, including titles, headings, table text, appendices, notes, caveats,
change explanations, and unresolved items. Budget space across those parts;
do not exceed the limit and then label the overflow as outside the “main text”.
Compress structure and wording before dropping decision-changing evidence. If
the critical facts still cannot fit, surface that conflict instead of silently
omitting them or overrunning the limit.

Do not repeat questions whose answers are already present. Ask only when a
missing answer can materially change the conclusion, scope, cost, acceptance,
or risk. Group at most three critical questions. If work can proceed safely,
mark the gap as `待确认` and deliver the draft instead of blocking.

## Separate claims before improving prose

Read [references/source-integrity.md](references/source-integrity.md) before every
Draft or Rewrite, including short updates and single-source explanations, and
for multi-source, conflicting material or Diagnose. Apply its detailed status, gap, scope and
source-entailment rules; moving them to a reference does not make them optional.

## Compose around an answer, then test the structure

Use these four actions internally. They are not a mandatory document outline.
The default is concise but fully reasoned, not a fixed word count or a one-screen
summary. Short progress updates need no artificial argument or section scaffold.

1. **Find the answer.** Name the reader's actual question and the narrowest
   source-supported answer. A subject such as “数据平台升级” is not an answer.
   A status, open question or conditional judgment is valid when the material
   cannot support a recommendation. Do not invent a decision to make a pyramid.
2. **Group and reason.** Group related material by the question it answers;
   state the useful finding each group supports. Put that finding above its
   reasons and their evidence. Check vertically: do the children answer why,
   how or what specifically, and actually support the parent? Check horizontally:
   are these comparable reasons, options, parts or steps, rather than a mixture?
   Order by causal dependency, time, composition or importance as appropriate.
   Do not fill a presumed category or invent a causal link to complete a shape.
   For a structural rewrite, map source claims into this grouping before
   writing prose. Compose from that map instead of paraphrasing each source
   paragraph in its original order. Preserve the claims and constraints, not
   redundant sections or the original placement of a decisive reason.
3. **Allocate information once.** Choose the lightest form that answers the
   question: connected prose, a compact list or a comparison table. Put the
   central answer first, then give every remaining fact a useful home. Do not
   enumerate the whole report in an opening and repeat it under headings. For a
   short update, the facts can be the answer; no abstract, background or closing
   summary is needed. In a comparison, one table can hold the details while the
   surrounding prose explains the decisive trade-off instead of reading the
   table aloud. Add another form only for a different, necessary reading task.
4. **Edit the whole and check the source.** Read continuously, then test deletion:
   would removing this passage lose a relevant finding, reason, evidence,
   condition or action, or the independence of a separately used summary? If
   nothing is lost, cut or merge it. Repair awkward sentences or paragraphs by
   meaning, not synonym substitution. Recheck that nothing important was lost
   and no relationship was invented. End when the reader's question is answered.

A short answer plus its detailed support is useful hierarchy. A short answer
followed by paraphrases of the same answer is repetition. More headings do not
create a logical structure. Do not impose a fixed number of reasons or a stock
“背景—方案—收益—总结” outline.

When producing versions for different readers, change emphasis, order, and
explanation depth. Do not turn a source activity into a new audit duty, ongoing
confirmation requirement, acceptance purpose, or control process merely
because the execution version needs more detail.

Lead with the bottom line that the reader needs. A decision document normally
lets a scanning reader find the problem, recommendation, strongest reason,
material uncertainty, and requested decision before implementation detail.
Decision-ready does not mean every document needs a new decision. If neither
the request nor the source specifies an approval, owner, pilot, or next-step
process, do not manufacture one from the gaps; explain what the supplied
material supports and keep consequential unknowns visible.

For substantial decision writing or restructuring, read
[references/decision-documents.md](references/decision-documents.md) before
outlining. For a long draft that repeats itself, use its complete restructuring
example to distinguish a paragraph's contribution from its topic. Apply its
scenario, appendix and separate-decision-entry rules when
those forms are requested or useful; their source boundaries remain mandatory.

## Say what is true, once

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
- Keep the rewrite's own process out of the document. `本次仅重组表达` or
  `本文未修改代码` describes an edit; drop it rather than turning it into a
  claim about the work such as `代码尚未调整`. Keep the work's own evidence
  state when the source gives it, such as `现有渲染能力待复核`.

A source's disclaimer is a condition to keep, not wording to copy. Rewrite it
as the positive condition in its natural place; never delete it to reduce
negations. For example, `格式相同只是初筛条件，不代表都能直接录入` becomes
`格式相同的报名表还要核对姓名、日期和签字，再决定能否录入`.

Keep the modality exact. `不要求`, `暂不`, and `先保留` state what the phase
does not require; they are not `不做`, `不涉及`, `由人工处理`, or a promise that
the item belongs to a later stage. `试点不要求建成完整平台` can become
`试点只需做好单一类目，不需要完整平台`. A target such as `每天 200 张是后续目
标，不是试点门槛` can move to the stage that pursues it only when the source
places it there; otherwise keep the non-requirement where the scope is stated.

If many sentences end in a `不/未/非` qualification, rewrite them as positive
statements plus one status passage, then recheck the source in both directions.
[references/clear-chinese.md](references/clear-chinese.md) has a worked example.

## Make the language clear without hollowing it out

For every Draft or Rewrite and for sentence-level editing, read
[references/clear-chinese.md](references/clear-chinese.md). Its general clarity,
precision and final reader checks apply in every language; Chinese examples do
not override the user's requested language.

## Deliver a usable document

Default to **clean** delivery for Draft and Rewrite: output only the usable
document. Do not prepend “以下是优化稿”, append a change log, describe your
process, or assert that you preserved every fact. Material unknowns, conflicts,
risks, and missing decisions belong in the document when they affect the
reader's task; they are not process commentary.
Do not expose the mode classification, source inventory, internal decision
analysis, loaded Skill rules, or a justification for the structure. Begin with
the document the user can use.

Use **annotated** delivery only when the user asks to learn from the edit, see
the changes, or review the reasoning. Give the complete document first, then
explain only a few consequential changes with the original wording, revision,
and reason. Diagnose mode still returns diagnosis rather than a silent rewrite.

Do not invent an approval request when the source is only a status update.
Preserve the author's voice when a sample exists; clarity is not permission to
replace it with a generic corporate voice.

When the user asks for a substantive draft that will be delivered in Feishu,
Word, Google Docs, or another formatted document, or asks to improve both the
content and its visual hierarchy, read
[references/document-presentation.md](references/document-presentation.md).
It defines semantic presentation, not platform operations. Keep pure layout or
document-platform requests outside Write Craft, and use the destination
platform's document capability to apply and verify actual styles.

## Verify the draft, then test the reader

For every Chinese Draft or Rewrite, finish the editorial pass in
`clear-chinese.md` before delivery: check information order, paragraph
contribution, sentence relationships, wording, and useful presentation. This
is part of composing the draft, not a mandatory extra model call. Check changed
wording against the source again; concision must not erase a condition.

For a consequential Draft or Rewrite, treat drafting, source review, and any
reader test as one bounded quality workflow. After the first draft, apply the
two-way check in `source-integrity.md` before asking a blind reader to interpret
the document. Use a genuinely independent context for review only when the
capability is available and authorized; otherwise self-check and do not claim
independence. When independent review is used to assess writing quality, give
the editor the request and complete draft as a separate reading task. A long
source checklist is not a substitute for reading the prose continuously; the
source reviewer must confirm or reject the editor's proposed issues against
the request and sources before revision. Keep preferences distinct from located
problems and preserve necessary actors, conditions and checks.

If a fact or reader check finds a blocking issue, or an editorial check locates
an actual problem such as duplicated meaning or an unsupported argument, use at
most one additional revision. Remove, narrow, or correctly label unsupported
claims; repair the located editorial problem without dropping necessary
conditions. Do not revise merely to satisfy a reviewer's format preference.
Then rerun the affected checks, including source fidelity after an editorial
change. All three kinds of feedback share this one revision budget; a later
reader test does not reset it. If a blocking conflict, unsupported claim or
located editorial problem remains, do not call the document ready; surface the
unresolved limitation. Ordinary short, low-stakes edits do not require an
independent review.

For a consequential final document, read
[references/reader-testing.md](references/reader-testing.md). If no independent
reader context is available or authorized, do not claim that a test ran. Provide
the fallback prompt only when the user requests a testing aid. Keep clean copy
free of testing instructions; if validation status is requested or required for
acceptance, report the missing check separately and concisely. Report first-draft
and revised results separately when the extra revision is used.

Read [references/source-map.md](references/source-map.md) only when maintaining,
auditing, or explaining Write Craft's upstream provenance.
