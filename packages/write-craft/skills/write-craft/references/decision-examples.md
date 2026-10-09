# Decision examples

Complete synthetic examples for the decision scenario. Read this file when
restructuring a long or repetitive draft, or when a draft keeps restating the
same point under different headings: the examples show how to tell a
paragraph's contribution from its topic. The rules they illustrate live in
`decision-documents.md` and remain authoritative.

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
