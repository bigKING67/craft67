# Decision documents

This is the scenario reference for decision and project communication: a draft
that must help a non-technical reader understand a complex proposal, follow
progress, compare options, approve a bounded next step, or decide not to
proceed. Read it for every Draft, Rewrite, or Diagnose in this scenario. It is
guidance, not a mandatory template. The two long example sections at the end
are needed only when restructuring a long or repetitive draft.

## Contents

- Scenario contract
- Start from the decision
- Find the load-bearing idea
- Build a pyramid of findings
- Design the first reading layer
- Separate the decision entry from the engineering source when needed
- Use a source-supported scenario
- Layer the body by reader need
- Use the lightest table that fits the reader's task
- Keep decision-changing constraints visible (includes appendix rules)
- Keep the evidence boundary explicit
- A worked decision structure
- Learn from complete synthetic examples
- Complete restructuring: each paragraph contributes something different

## Scenario contract

**Commitments under preserve.** Budget, schedule, scope, staffing, acceptance,
approval state, and the chosen approach. This includes approved plans: do not
redesign one into a pilot or reopen a decision merely because another option
reads better.

**Reading order.** Lead with the bottom line that the reader needs. A decision
document normally lets a scanning reader find the problem, recommendation,
strongest reason, material uncertainty, and requested decision before
implementation detail. Decision-ready does not mean every document needs a new
decision. If neither the request nor the source specifies an approval, owner,
pilot, or next-step process, do not manufacture one from the gaps; explain what
the supplied material supports and keep consequential unknowns visible. Do not
invent an approval request when the source is only a status update. Do not
impose a fixed number of reasons or a stock “背景—方案—收益—总结” outline.

**Versions for different readers.** Change emphasis, order, and explanation
depth. Do not turn a source activity into a new audit duty, ongoing
confirmation requirement, acceptance purpose, or control process merely because
the execution version needs more detail.

**Optional forms.** Apply the usage-scenario (使用场景), appendix, and separate-decision-entry
rules below when those forms are requested or useful; their source boundaries
remain mandatory. For a long draft that repeats itself, use the complete
restructuring example to distinguish a paragraph's contribution from its topic.

## Start from the decision

State the reader's task in one sentence. Distinguish these common outcomes:

- **Understand:** establish a shared model; do not invent an approval request.
- **Choose:** compare real alternatives using the same decision criteria.
- **Approve:** state the bounded resource, scope, risk, or next stage being
  authorized.
- **Act:** name the owner, next step, and trigger or deadline when supplied.

“Learn about the project” is not yet a decision. When no decision is required,
the document may end with a next step already supplied by the source; otherwise
it does not need to manufacture one.

## Find the load-bearing idea

Identify the one idea that makes the rest easier to understand. Express it in
plain language without losing its condition or uncertainty. Use it to organize
the explanation; do not give every implementation detail equal weight.

For a technical-to-business rewrite, translate this sequence:

`implementation mechanism -> changed workflow -> observable result -> decision value`

Use only the links the source states or clearly entails. A component list may
support a component-level explanation without supporting a changed workflow.
Do not skip directly from a mechanism to revenue, efficiency, quality, or
adoption unless evidence establishes that link, and do not fill an absent link
with a conventional process.

## Build a pyramid of findings

Work from the evidence upward; present from the answer downward. Start with the
question this reader needs answered, group relevant facts, and express the
finding each group supports. A finding must add a supported meaning, not just
name the group: “两方案都能按期交付，差别在费用与后续维护” says more than
“方案分析”. Do not derive that finding unless the source supports both parts.

Test the relationships before drafting:

- **Vertical support:** if the parent says “建议选甲”, its children must explain
  why that choice fits the stated criteria. Listing what 甲 contains is not
  enough. Evidence belongs under the reason it supports. If a premise is missing,
  narrow the judgment or expose the consequential uncertainty; do not supply it.
- **Horizontal grouping:** peers answer the same question at the same level.
  Reasons for choosing, implementation steps and expected results have different
  jobs; do not mix them as three “advantages”. Compare alternatives against the
  same relevant criteria, preserving an unknown cell rather than guessing it.
- **Order:** arrange dependencies before dependent actions, steps by time, parts
  by their relationship, or reasons by decision importance. A list without a
  defensible order may need regrouping. Independent reasons need no invented
  causal bridge. Do not force a fixed number of groups or completeness beyond
  what this task and the sources support.

Use the reader's situation and the change or difficulty only to establish the
question when it is not already obvious. Do not prepend a background story to a
short update. The answer can be a current state or a conditional conclusion;
writing about a project does not itself authorize recommending another project.

After drafting, read only the opening and the section claims: do they form a
coherent answer? Then read the support under each claim: does it explain or
substantiate the claim, or merely repeat it? Revise the grouping before wording.
This checks the argument, not the number or style of headings.

## Design the first reading layer

Open with the answer this reader needs, including the condition without which
it would be misleading. Choose the relevant problem, recommendation or current
state, decisive reason, limitation and requested action from the source. These
are selection criteria, not five compulsory sentences or a miniature copy of
the whole body. Put each supporting detail where it serves the argument once.

A short update can be one paragraph or a small list of completed work, remaining
work and relevant dependency. A proposal explanation can state the supported
use and then its constraints. A comparison can use one common-criteria table and
a decision paragraph that interprets it. Choose by the task; no format or
paragraph count is mandatory. If the form already answers the question, stop.

Use a separate summary when requested or when it has a real independent reading
purpose, such as a decision entry paired with a full engineering source. Write
it after the body is sound and include the conclusion. Do not add a summary to
a short report merely to satisfy “conclusion first”. A heading and its paragraph
should contribute different information, just as prose and a table should.

## Separate the decision entry from the engineering source when needed

When one document must serve both decision-makers and implementers, a short
summary at the top may still leave the first reading path too long. If the
existing engineering plan must remain complete, preserve it as the detailed
source and create a shorter decision entry that can stand on its own. The short
entry should contain only the supported elements needed for the decision. These
may include the recommendation, a representative workflow when the source
provides one, a bounded first-stage deliverable and acceptance method, explicit
non-goals, material unknowns, and a real next decision or action. Omit an
inapplicable element instead of filling it from convention. Link to the detailed
source for architecture and implementation mechanics instead of copying them
all.

If the short entry and engineering source are separate files, or may be split
after delivery, put an explicit pointer inside the short entry itself. Name the
included file, attachment, or exact section, for example `完整工程方案见文件二`.
Showing the engineering source later in the same response is not enough: the
short entry must retain the path when copied or sent on its own.

Use the reader's present task to choose detail, not the source's section count.
When the task is to confirm a first-stage scope and inputs, explain the complete
goal but develop the first stage. Category examples, historical tables and
later-stage mechanics may remain in the linked detailed source when they do not
change that decision. Do not reproduce every category list and illustrative
case merely to prove that the source was read. This does not authorize deleting
material the user explicitly asks to preserve in full, narrowing the approved
plan, or hiding a condition that affects the current choice.

Do not use the split to hide a constraint. Any fact that changes feasibility,
cost, timing, risk, acceptance, or the requested authorization must still
appear in the decision entry.

## Use a source-supported scenario

When an architecture description is too abstract and the source supplies the
necessary relationships, show one representative flow:

1. who begins the task and with what input;
2. what the proposed system or process does;
3. where a human reviews, changes, or rejects the result;
4. what output is produced;
5. how success and failure will be observed.

For a product explanation to business readers, place a supported scenario near
the opening when it helps explain the use before the architecture. Start with
the user's task, supplied input, proposed action, and observable output; include
the human role and boundary where supported. Keep approval requests or urgent
decision-changing facts first when that is the reader's task. A scenario is not
a compulsory opening for short updates, diagnoses, or sparse component lists.

Distinguish the evidence behind a case:

- A real case names only supplied materials, events, and observed results. Real
  input material alone does not establish that a proposed output was produced.
- An illustrative scenario explains supported behavior and is visibly labeled
  as illustrative. It must not invent customer history, an old manual process,
  pain, measured savings, capabilities, or successful results. A plausible
  before/after table also needs source support on both sides.
  For example, `目标减少人工核对时间` supports that goal, not `现在靠人工逐项
  核对` as a description of the existing process. Explain the proposed task
  directly when the current process is unspecified.
- When the source says real materials are still being prepared, add a brief
  relevant note and continue with the supported explanation. If the user has
  deferred supplying them, do not repeatedly request them or make the otherwise
  usable document depend on them. Do not call materials unfinished merely
  because the source does not mention them.

Give each presentation form a distinct job. A case can explain the use; steps
can add actionable sequence; a table can compare choices or acceptance criteria.
If these forms only repeat the same actors, inputs, actions, and outputs, merge
or remove one. Preserve necessary emphasis on consequential boundaries and the
independence of a short entry from its engineering appendix.
This also applies to prose: after a complete scenario, omit a paragraph that
only restates its purpose, output, and human boundary. For a usable explanation,
do not append an inventory of facts you avoided inventing. Omit irrelevant
absences; if one matters, retain `材料未说明` rather than claiming the activity or
record does not exist.

Label the scenario as an example when it is illustrative. Do not let an example
silently become a promise that every case behaves the same way. Each actor,
input, action, review point, output, and boundary must come from the source or a
clear entailment. Module names alone do not establish who initiates work, where
humans intervene, what gets recorded, or what happens next. If those links are
absent, explain the components without constructing a scenario.

## Layer the body by reader need

Choose only the sections the decision requires and the source can support.
Useful candidates include:

- current problem and why it matters now;
- proposal and representative use case;
- first-stage scope and explicit non-goals;
- alternatives and trade-offs, including the status quo when relevant;
- deliverables, owners, dependencies, and sequence;
- acceptance method and evidence needed;
- people, time, budget, and operational load;
- risks, mitigations, stop conditions, and fallback;
- requested decision or next action;
- technical appendix.

Use consistent criteria when comparing options. Do not praise one option for
speed and reject another for cost without showing both criteria for both
options. Follow the reader's supplied priority order. If the primary criterion
has no comparable evidence, say what cannot be ranked; do not manufacture a
winner from a cheaper price, a different population, an analogy or an adjacent
metric. “Delivered” need not mean “understood”, just as “tested” need not mean
“passed”. Adding “probably” does not supply the missing relationship.

Preserve a source's tentative recommendation as tentative under **preserve**.
When **propose** is authorized, new recommendations may interpret supported
trade-offs but must not claim an unmeasured advantage. Explain any condition
under which the available evidence supports a choice. If it supports no such
choice, give the comparison and its decision limit rather than force a winner.

## Use the lightest table that fits the reader's task

For a small, static comparison such as scope, stages, responsibilities, or
acceptance criteria, use the destination document's native table when it makes
scanning easier. Introduce a spreadsheet or another embedded data artifact only
when the task actually needs formulas, live data, filtering, calculation, or
independent data collaboration. A more powerful container is not automatically
a clearer one; it can add navigation, access, and maintenance overhead without
helping the decision.

## Keep decision-changing constraints visible

A technical fact belongs in the main body when it changes any of these:

- feasibility or supported use cases;
- cost, staffing, or operational burden;
- delivery time or dependencies;
- security, privacy, compliance, or rights;
- failure recovery or business continuity;
- acceptance thresholds or quality risk.

Explain the consequence in reader language, then place implementation mechanics
in the appendix if further detail is useful. Move detail to an appendix only when
it does not change the decision.

If the source supplies only decision-changing constraints and no implementation
mechanism, keep the constraints in the body and omit the appendix. Do not invent
placeholder mechanisms, new checks, owners, optionality, or `待补充` appendix
items merely to satisfy an appendix request, and do not pad the explanation with
hypothetical implementation examples. Omit the appendix cleanly: do not justify its absence by listing
conventional fields such as components, interfaces, or deployment methods that
the source did not mention, and do not add
`来源没有实现细节`, `没有可放入附录的内容`, or any other explanation for it.

## Keep the evidence boundary explicit

Use the strongest accurate verb:

- **observed / verified:** directly supported by current evidence;
- **estimated:** derived from stated inputs or a model;
- **expected:** a reasoned forecast, not yet observed;
- **targeted:** an intended outcome;
- **unknown / pending confirmation:** no adequate basis yet.

If the source explicitly leaves a relevant cost, duration, headcount, baseline,
or success threshold unknown, retain that uncertainty and its direct decision
impact. An absent field is not automatically an undecided project commitment:
surface it as `材料未说明` only for requested gap analysis or when it prevents
the current reader task. Omit unrelated absences. Keep the
gap at the source's granularity: do not expand “预算待确认” into conventional
cost categories, or “验收阈值待确认” into trial size, failure handling, owners,
and approval steps. Smooth prose must not conceal the gap or manufacture the
process for closing it.

## A worked decision structure

The following example is synthetic. It demonstrates grouping and information
gain, not a fixed heading template.

**Source material**

> 甲方案每年 6 万元，能在 3 周内交付并启用，后续由供应商维护。乙方案每年 4 万元，交付并启用要 7 周，后续由本部门维护。目前本部门没有可安排的维护人员。业务要求 4 周内启用，先满足上线时间，再比较费用。两方案都能导出所需报表。建议采用甲方案，请负责人决定是否批准每年 6 万元费用。

**Weak organization**

> 建议采用甲方案。理由有三点：支持报表导出、安排供应商对接、每年费用 6 万元。

This mixes a shared capability, an unstated action and a cost as though they
were comparable reasons for the choice. Leading with a recommendation has not
established support for it.

**Complete rewrite**

> 建议采用甲方案，请批准每年 6 万元费用。甲可在 3 周内交付并启用，满足 4 周内启用的要求；乙需要 7 周，无法满足这一时间要求。
>
> 甲比乙每年贵 2 万元，但后续由供应商维护。乙需要本部门维护，而目前没有可安排的维护人员。两方案都能导出所需报表，因此这项能力不构成选择差异。

The first paragraph answers the decision and supplies the decisive timing
comparison. The second adds the cost trade-off, maintenance constraint and
non-differentiating capability. It does not repeat the recommendation in an
extra conclusion, nor turn the document into an implementation plan.

## Learn from complete synthetic examples

Examples demonstrate decisions and information order, not mandatory wording or
headings. The following material is synthetic and does not describe a real
project state.

**Source material**

> 拟建设设备巡检辅助工具。现场人员提交传感器读数、巡检照片和设备编号；系统标记异常记录并生成检查清单。设备工程师复核清单后决定是否安排检修。本轮不自动停机，也不自动下发维修指令。目标是减少人工筛查巡检记录所需的时间，尚未用同批记录比较实际耗时。预算与验收阈值未确定。本文先解释方案，不申请审批。

**Request**

> 给不了解技术的业务负责人说明方案。只改表达，不改变范围，也不申请立项。

**Usable rewrite**

> ## 从巡检记录生成异常检查清单：设备巡检辅助方案说明
>
> 这套拟建设的工具用于辅助筛查巡检记录。现场人员提交传感器读数、巡检照片和设备编号，系统标记异常记录并生成检查清单；设备工程师复核后，决定是否安排检修。本轮不自动停机，也不自动下发维修指令。
>
> 方案希望减少人工筛查巡检记录的时间，但尚未开展同批记录的耗时对比，实际节省时间还未验证。预算和验收阈值也尚未确定。
>
> 本文用于说明方案，当前不提交审批请求。

The first paragraph explains the supported workflow once, with its proposed
state and human boundary. The second places the target beside the evidence gap.
The last sentence preserves the communication purpose. Editing explanations
stay outside the usable draft.

### A scenario-led explanation with real materials pending

**Source material (synthetic)**

> 拟建设客服回复辅助工具。客服提交客户的问题和已批准的产品说明，系统据此起草回复。客服核对后自行发送；系统不直接联系客户。目标是减少起草时间，尚未做耗时对比。真实客户问题样例仍在整理，整理后由作者补进文档。本文向业务解释方案，不申请审批。材料未说明当前人工起草流程。

**Request**

> 写成老板和业务能理解的具体场景说明。先用示意场景，真实样例以后再补，不要再追问；不要重复堆案例、流程和表格。

**Usable rewrite**

> ## 客服回复辅助方案：先起草，由客服核对后发送
>
> **使用场景示意：**客服需要回复客户提出的产品问题时，将问题和已批准的产品说明交给拟建设的工具。系统据此起草回复，客服核对后自行发送。工具承担回复起草环节，不直接联系客户。
>
> 方案希望减少起草时间，实际节省多少尚未做耗时对比。本文用于说明方案，不申请审批。
>
> **真实样例待补：**客户问题样例仍在整理，准备完成后由作者补入文档。

The scenario explains the whole supported use once. The following paragraphs
add evidence state and the deferred input, rather than retelling it as steps
and a table. It does not invent a customer's question, product facts, the old
manual process, or savings to make the example vivid.

### When the source contains components but no workflow

**Source material**

> 这是一套库存盘点辅助方案。现有材料只列出图像识别、货品匹配、规则调度和报表生成四个组成部分，没有说明具体输入、输出、先后关系、人工节点、投产状态或报表形态。预算、工期、现状基线和验收阈值尚未确定。本文只说明方案，不申请审批。

**Request**

> 写成业务负责人能直接理解的方案说明，不改变范围。

**Usable rewrite**

> ## 库存盘点辅助方案说明
>
> 现有材料把方案分为图像识别、货品匹配、规则调度和报表生成四个部分。当前只能确认这四项构成，不能据此判断它们怎样衔接、哪里需要人工确认，或最终会形成什么报表。
>
> 预算、工期、现状基线和验收阈值尚未确定，因此目前还不能判断成本、交付时间和实际效果。本文只说明方案，不申请审批。

This version does not convert the four names into a guessed process or unpack
the stated unknowns into a longer diligence list. Sparse source material calls
for a short, bounded explanation, not a conventionally complete proposal.

### When the source is already sufficient for approval

**Source material**

> 当前首次审阅时长中位数为 28 分钟，采购专员需要在多个条款库之间查找内容。建议用六周为 30 名采购专员试运行合同条款提示功能。系统只提示可能需要关注的条款，由采购专员确认后处理，不自动修改或提交合同。投入为法务 1 人、采购主管 1 人、工程师 2 人，预算上限 20 万元。试运行前后比较首次审阅时长、人工修改率和漏检数；通过条件为首次审阅时长中位数不高于 15 分钟、没有未经采购专员确认的合同提交。主要风险是条款库过期和权限配置错误，分别由法务每周复核、工程师上线前检查。请管理层批准六周范围和 20 万元预算。

**Request**

> 按材料直接改写成审批稿，已有信息不要再问。

**Usable rewrite**

> ## 合同条款提示功能试运行申请
>
> **申请批准：**用六周时间面向 30 名采购专员试运行合同条款提示功能，预算上限 20 万元。
>
> 目前，首次审阅时长中位数为 28 分钟，采购专员需要在多个条款库之间查找内容。
>
> 系统只提示可能需要关注的条款，由采购专员确认后处理，不自动修改或提交合同。参与人员为法务 1 人、采购主管 1 人、工程师 2 人。
>
> 试运行前后比较首次审阅时长、人工修改率和漏检数。通过条件有两项：首次审阅时长中位数不高于 15 分钟；没有未经采购专员确认的合同提交。
>
> 主要风险是条款库过期和权限配置错误，分别由法务每周复核、工程师上线前检查。

The rewrite uses the supplied approval facts without reopening whether the
budget contains particular cost categories, inventing thresholds for the other
comparison metrics, or adding a later rollout decision. It also prevents two
adjacent observations from becoming an unsupported causal claim. When the
source is sufficient, completeness means organizing what is there and stopping.

For an approved plan, the same method improves explanation without reopening
scope. For a request that explicitly permits plan changes, put new suggestions
in a separate proposal section and label their effect on the approved baseline.

## Complete restructuring: each paragraph contributes something different

This source and edit are entirely synthetic. Use the editing choices, not the
headings, number of paragraphs or project sequence. The example does not require
a separate outline, an extra model call or a pilot for another user's plan.

**Repetitive source draft**

> 共享设备预约项目拟提供会议投影仪和便携音箱的预约。预约涉及设备、日期和借用人。前台确认后才能借出，不自动批准。
>
> 首期安排东区前台试用两周，只做投影仪。借用人填写日期、设备和姓名，系统显示是否有冲突，前台核对后决定是否借出。前台仍需确认，系统不能直接批准借用。音箱在后续扩展。
>
> 验收时查看投影仪预约记录有没有漏记、有没有同一时段重复借出，记录前台处理用时。首期试用两周，只在东区前台进行。
>
> 先做投影仪是因为它已经有统一资产编号，音箱的编号仍在核对，无法直接使用同一份设备清单。试用尚未开始，不能确认是否节省时间。
>
> 业务要提供投影仪编号清单与可借时段。前台负责人安排回看人。预算与上线日期待确认，最终验收门槛也未确定。
>
> 本项目保持人工确认，不会自动批准借用。完整工程附录另列预约表字段、冲突接口、操作日志与部署步骤；已知这些实现细节不改变本次范围、成本或验收条件。本文只供确认试用安排，不申请扩大范围。

**Reader request**

> 给业务负责人一份可以独立发送的方案说明，精炼但不要丢失理由、限制和待确认项；工程附录继续保留。

**Complete edit**

> # 设备预约：先在东区前台试用投影仪登记
>
> 设备预约项目拟覆盖投影仪和便携音箱，首期在东区前台试用投影仪登记两周。投影仪已有统一资产编号，音箱编号仍在核对，因此先验证投影仪这一类。本文用于确认试用安排，不申请扩大范围。
>
> 借用人填写设备、日期和姓名，系统提示冲突，由前台核对后决定是否借出；系统不自动批准。试用期间检查预约有无漏记、同一时段有无重复借出，并记录前台处理用时。试用尚未开始，能否节省时间仍待验证，最终验收门槛也未确定。
>
> 业务需提供投影仪编号清单与可借时段，前台负责人安排回看人。预算与上线日期待确认。预约字段、接口、操作日志和部署步骤见随附的《完整工程附录》。

**What changed and why**

| Source passage | Editing choice | Information preserved |
| --- | --- | --- |
| Scope in paragraphs 1–2; reason in paragraph 4 | Put the bounded proposal beside its actual reason | Both device types, first scope, duration, location and different identifier states |
| Human approval stated three times | Keep it with the action it governs | Who decides, what the system does and what it cannot do |
| Trial duration and place repeated in acceptance | Keep the scope once; acceptance contributes observations | Missing bookings, duplicate loans and handling time remain separate checks |
| Intended time savings and not-yet-started status | Put them together to limit the outcome claim | No measured improvement is implied; no target is invented |
| Preparation and implementation mechanics | Keep actionable inputs in the body; name the attached appendix | Owner, inputs, unknowns and the standalone document's route to detail |

The compression comes from assigning each fact a useful place, not deleting
conditions or replacing full sentences with terse labels. A repeated noun can
serve different actions: the trial's human approval and the acceptance check
are both needed. A different source may need a different structure or retain
technical detail in the main text when it changes the decision.
