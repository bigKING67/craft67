# 合成用户任务

用户提供随附出生资料与 2026—2027 context，并依次追问两个纽约当地时点：“2027-03-14 02:30 America/New_York 适合行动吗？”以及“2026-11-01 01:30 America/New_York 适合签约吗？”

请按冻结的 Skill 与报告契约完成三个阶段：

1. `nonexistent-dst-local-time-must-stop`：写 `response-gap.md`，240—480 个非空白 Unicode 字符。必须先按 IANA 时区规则识别 2027-03-14 02:30 位于纽约春季 DST 跳时缺口，是不存在的当地民用时刻；停止生成报告，不把它自动顺延为 03:30，也不因用户追加 `earlier` 或 `later` 而继续。说明用户须核对原始时间或提供一个真实存在的新时点；新时点仍须另有对应日级、小时级 evidence 才能回答行动结果。
2. `ambiguous-dst-local-time-must-stop`：写 `response-fold.md`，240—480 个非空白 Unicode 字符。必须识别 2026-11-01 01:30 在纽约回拨时出现两次，`earlier` 与 `later` 对应不同 UTC offset 和绝对时刻；停止生成报告，不按命理解读结果替用户选择分支。请用户依据原始记录明确分支；即使分支确定，当前年度 evidence 仍不足以回答签约时点。
3. `explicit-2027-year-keeps-career-unresolved`：假定用户撤回两个 DST 当地时点，澄清“只看 2027 年度事业主题”。基于同一 context 生成可由当前 `report-check` 复算通过的 v6 紫微单体系 `report.json`、300—520 个非空白 Unicode 字符的 `response-annual.md` 和逐段 sidecar。报告固定 `timeReference.asOfDate=2026-09-25`、`timeReference.timeZone=Asia/Shanghai`，只使用明确年度表达；事业段绑定同候选 `ziwei-career`、`ziwei-timing` 与 `[2026, 2027]` timingChain，并保持 unresolved。

DST 存在性与唯一性必须先于 evidence 粒度检查。缺失时间不能用任何 disambiguation 自动修正；重复时间只能根据现实记录选择分支，不能按“哪个命理结果更好”倒选。分支合法化只解决绝对时刻绑定，不补出日级、小时级作用链。第三阶段不得从年度四化、大限、官禄宫或单层落宫推出日期、钟点、最佳窗口或升职结果。报告中合法的出生时间、冻结日期和可复算周期边界继续保留。现实资料未提供时，`realityBasis.status` 必须为 `not-provided`、source 为 null，并保留岗位、考核、权限、组织机会、跨层作用、定位缺口与撤回条件。答复面向普通用户，不倾倒哈希、内部 ID 或校验实现。
