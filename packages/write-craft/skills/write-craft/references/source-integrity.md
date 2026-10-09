# Source integrity

Read this reference for every Draft, Rewrite, and Diagnose in every scenario.
Its rules matter most when material has multiple sources, consequential facts,
ambiguous evidence, or an explanation that could be mistaken for a new claim.
The aim is faithful transformation, not literal copying.

Plausibility is not provenance. A cause, workflow step, baseline state, owner,
decision, boundary, or reader behavior remains unsupported when the source does
not state or entail it, even if it sounds normal and does not contradict the
source. Mark a user-authorized proposal as a proposal; otherwise omit it or
preserve the actual unknown.

Source-bounded writing does not need to look conventionally complete. Before
turning components into a process, identify source support for every actor,
input, action, review point, output, and boundary. If the source provides only
component or capability names, describe only those components or capabilities.
Do not create a workflow, baseline, owner, or `待确认` item to fill the missing
shape of a familiar proposal.

## Allow useful transformation

These changes are normally valid when they preserve meaning:

- explain a term through source-supported actions by a person or system;
- summarize several stated steps as one bounded workflow;
- group related facts and reorder them for the reader;
- state the supported topic or purpose more directly; and
- remove repetition that carries no additional condition or exception.

For example, if the source says the system retrieves clips, arranges them on a
timeline, and renders the result, “生成视频初稿” can be a faithful summary.
“每天自动生产一百条高转化视频” adds unsupported capacity, automation, and
outcome claims.

## Check the relationships introduced by grouping

Combining true facts can create an unsupported relationship. Check the modifiers
and grouping labels in headings, opening summaries and tables as carefully as
the individual facts: does the source assign this place, owner, cause, time or
status to this particular action or object? Nearby records do not establish
that link. Keep the facts separate if the relationship is not supported.

## Check in both directions

Before delivery, check both directions:

- **Draft to source:** every statement that changes understanding or a decision
  has support, is clearly marked as a proposal, or is explicitly unknown.
- **Source to draft:** every source fact, condition, exception, and decision that
  matters to this reader's task remains visible.

Apply the same check to an intermediate outline or fact-to-section map before
using it to draft. A generated map is an editing aid, not a new factual source:
reject unsupported status or causal links there rather than carry them into
polished prose.

Run this check across the title, summary, tables, captions, body, appendix, and
next-step language. A correct body does not repair a misleading title.

## Protect meaning, not just nouns and numbers

Reject transformations such as:

| Source meaning | Distorted rewrite |
| --- | --- |
| completed testing | testing passed |
| completed listed tasks | overall progress is normal or on schedule |
| production status not stated | never tested in production |
| requires additional budget | guaranteed if funded |
| aims to reduce manual time | has reduced manual time |
| some samples improved | all tasks improved |
| budget is proposed | budget is approved |
| a field is not required | collecting that field is forbidden |
| human review remains now | can never be automated |
| real-time use requires more investment | phase one excludes real-time use |
| two metrics changed together | one metric caused the other |

Also preserve modality and time: `cannot`, `not yet supported`, `not yet
verified`, `planned`, and `approved` are different states.

Do not turn a current, phase-specific, or approved boundary into a permanent
commitment. `当前/本期必须人工确认` does not support `永久如此`, `不是过渡做法`,
or `以后也不会自动化` unless the source states that time scope.

Keep the modality exact in the other direction too. `不要求`, `暂不`, and `先保留`
state what the phase does not require; they are not `不做`, `不涉及`, `由人工处理`,
or a promise that the item belongs to a later stage. `试点不要求建成完整平台` can
become `试点只需做好单一类目，不需要完整平台`. A target such as `每天 200 张是后续
目标，不是试点门槛` can move to the stage that pursues it only when the source
places it there; otherwise keep the non-requirement where the scope is stated.

## Status, scope and missing information

Preserve evidence-bearing status verbs exactly: completing a test is not the
same as passing it, and completing listed tasks does not prove that the overall
project is normal, on schedule, or proceeding as planned. Do not add those
stronger judgments unless the source states them. In a short progress update,
do not add `测试通过`, `功能正常`, `进展正常`, `顺利`, or `按计划推进` merely
because tasks were completed.
Preserve cost conditions as cost conditions: `实时生成需要额外 GPU 预算`
does not say the current version lacks real-time capability, that the phase
excludes it, that the current proposal excludes the budget, that a separate
application is required, or that no budget is needed when it is not enabled.
Before delivery, scan every evaluative or operational clause that was not in
the source. Remove new success labels (`通过`, `正常`, `顺利`, `符合计划`), missing-
field claims, obligations, purposes, or verification steps unless the source
states or necessarily entails them. Mentioning an activity does not authorize
inventing why it is done, how it will be checked, or what later decision it
supports.
Silence is not an explicitly named unknown and does not by itself authorize a
new gap. Surface an absent field only when the user asked for gap analysis or
when the absence directly prevents this reader from completing the current
decision or action; say `材料未说明` rather than upgrading it to `尚未决定`. For
example, if the source already gives a 10-minute acceptance threshold and a
total budget, do not add `材料未提供当前基线`, `费用构成待补`, or similar gaps merely
because those fields are common in project documents.
Plausible but unstated causes, workflows, baselines, owners, decisions, and
boundaries are still unsupported. Merely not contradicting the source is not
evidence; add them only as visibly separate suggestions when **propose** applies.
Completeness means covering the relevant supported material, not filling every
conventional section. A shorter source-bounded draft is more complete than a
polished document whose missing links were supplied by convention.

Keep unknowns at the source's granularity. If the source names budget, schedule,
baseline, and acceptance threshold as unknown, do not unpack them into cost
categories, milestone approvals, trial size, failure handling, owners, module
inputs or outputs, or other “missing information”. You may state the direct
decision dimension an unknown leaves unresolved, such as cost or timing, but do
not turn it into a new prerequisite, approval process, or future decision rule.
A trial and its measurement plan do not by themselves establish whether, when,
or how a later rollout decision will be made.

When the source explicitly names its unknowns, treat that list as closed for
the current draft. For example, `尚无响应基线、负责人和预算` supports marking
only those three gaps; it does not support adding system capability, usage
scope, delivery method, new owner roles, or a “must complete before proceeding”
gate.

Missing information can limit a decision without proving that approval is
impossible or that the gap must be filled before any action. Use the narrowest
supported consequence unless the request or source defines the approval gate.

## Diagnose what is actually present

In Diagnose, use `observed feature -> possible comprehension risk -> supported
revision direction`. For example: “原稿先列实现组件，最后才说明业务目的” is an
observed feature; “这种顺序可能让读者更难在接触组件时判断这些信息为何重要”
is a bounded comprehension risk; “把原稿已有的业务目的移到组件说明之前” is a
supported direction. Do not replace that chain with claims about how bosses
usually read, what they know, or when they stop reading.

Keep the middle step explicitly conditional: use “可能让……更难定位” or
“读者可能需要先……再……”, not unqualified predictions such as “读者需要先……
之后才能……”, “读者无法理解”, or “只能读完全文才知道”. Describe a missing
relationship or reader task as a feature of the text, not as proof that a reader
must guess, cannot understand, or will not know how to respond. Diagnose only
what the supplied text or summary makes observable. A summary that says
components appear first does not establish that the source lacks role
descriptions, inputs, outputs, or relationships. If the available material is
enough for the requested diagnosis, deliver the bounded diagnosis without
ending with requests to paste more material, choose a communication purpose,
or ask for another rewrite.
Respect the source's stated completeness. If the user identifies the supplied
text as the complete draft, do not relabel it as a summary, claim that the
original wording was unavailable, or append a caveat about not having seen the
full document.
Distinguish information that is absent from information that appears too late
or is hard to find. If the source states the business purpose near the end,
diagnose its position; do not say that the document has no purpose or never
explains what the work is for.
When the source already states what each component does, acknowledge those
actions and diagnose only the relationship, order, or decision framing that is
actually absent. Treat an unstated reader task as an observed gap; do not turn
it into a question the user must answer before receiving the diagnosis.
A Diagnose response is incomplete if it stops at problems and risks. Give at
least one prioritized, source-supported revision direction. Moving an existing
business purpose before the component paragraphs is a revision direction, not
an unauthorized full rewrite.
Describe an absent reader task as `文档没有说明读者需要做什么`, not as the
predicted outcome `读者看完不知道如何回应`. If component relationships are
missing, recommend adding them only when another supplied source supports them;
otherwise keep the stated component actions parallel. Do not tell the writer to
infer each component's business contribution from the component description.

Keep predictions about reader cognition or document effects conditional too.
Phrases such as `老板读完仍然不知道`, `读者只会记住`, or `阅读成本会下降`
claim an outcome; use them only when evidence supports that outcome. Otherwise
describe the observable order or omission and the comprehension risk it may
create.

**Source excerpt**

> 识别服务读取质检照片并标记异常区域。索引库保存设备编号和照片位置。任务队列记录每条检查任务的处理状态。查询接口按设备编号返回检查结果。我们希望借此减少人工查找异常照片的时间。原稿没有说明需要负责人批准什么。

**Request**

> 只诊断为什么负责人可能难抓住重点，不要重写。

**Bounded diagnosis**

> 影响理解最大的不是四个组件“没有解释”，而是信息顺序和组件关系没有建立。
>
> - **业务目的出现得晚。** 原稿先连续说明四个组件各自做什么，最后才说明希望减少人工查找异常照片的时间。这种顺序可能让读者更难在接触组件时判断这些信息为何重要。可以把原稿已有的业务目的前移，再保留必要的组件说明。
> - **组件动作已有，但关系未说明。** 原稿已经说明识别服务、索引库、任务队列和查询接口分别做什么；没有说明的是它们之间的先后、依赖或数据流。若原材料能支持这些关系，可以补充；如果不能，就保持并列说明，不要补造流程。
> - **阅读任务没有交代。** 原稿明确没有说明负责人需要批准、选择或配合什么。诊断可以指出这一空缺，但不能替作者制造审批事项。

This diagnosis acknowledges the supplied actions, limits criticism to the late
purpose, missing relationships, and absent reader task, and ends without asking
for more material or offering a rewrite service.

## Handle multiple sources and conflicts

Keep source identity and version distinct. A later date or a filename such as
“最终版” does not by itself prove authority. Apply a correction only when the
user, approval record, or explicit version relationship supports it. Otherwise
state the conflict and its decision impact instead of choosing the more
optimistic, convenient, or detailed claim.

When traceability is required, cite the real supplied source location. Do not
invent line numbers, quotes, hashes, or provenance. A valid quote proves where
text came from; it does not by itself prove that the interpretation is correct.

## Classify claims before composing

Internally classify material as:

- confirmed fact or observed state;
- judgment or recommendation;
- goal or intended outcome;
- assumption or hypothesis to test;
- unknown or missing decision input.

Do not expose this ledger unless it helps the user. Never turn a goal into an
observed result, an expectation into a promise, a generated artifact into a
business outcome, or an unknown into a plausible-sounding number. Preserve
source attribution when the document depends on external evidence.

## Short status updates

Keep a short status update at the source's granularity. A source that says
`本周完成接口联调和本地测试；下周处理监控；当前没有需管理层协调的事项`
supports a complete update with exactly those three facts. It does not support
an added closing judgment such as `进展正常`, `团队按计划推进`, or `整体顺利`, or
an appended caveat such as `尚未给出测试结论`.
