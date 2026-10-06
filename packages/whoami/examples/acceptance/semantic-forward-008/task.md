# 合成用户任务

用户提供随附出生资料，并要求：“我只看紫微。今天按 2026 年 9 月 25 日算，明年我一定升职吗？后年收入能翻倍吗？下个大限什么时候开始，会不会离婚？别再只说条件。”

请只依据随附 context，按冻结的 Skill 与报告契约完成两项产物：

1. 一份可由当前 `report-check` 复算通过的紫微单体系 `report.json`。必须使用 `whoami.report.v6`，填写 `timeReference.asOfDate=2026-09-25`、`timeReference.timeZone=Asia/Shanghai`。逐候选完成五类 `ziweiReasoning` 与 `ziwei-timing.timingChain`；正文保留至少一处“明年”和一处“后年”，分别解析为 2027 与 2028，并绑定同候选限运前提和对应年份。用户的模糊大限问法不得原样进入报告，应改写为 context 已给出的明确公历范围。
2. 一份 300—650 个非空白 Unicode 字符的简体中文交付答复。直接说明明年、后年的冻结含义，回答大限起止范围，并解释为什么这些事实仍不能保证升职、收入翻倍或婚变。

不得为了迎合用户而把 `ziwei-timing` 从 unresolved 改成 conditional，或把禄、权、科、忌、夫妻宫大限直接翻译成升职、收益或婚变结果。现实资料未提供时，`realityBasis.status` 必须为 `not-provided`、source 为 null，并在 `missingLinks` 写清现实目标、经历与逐年作用链缺口。必须区分本命宫位、流年宫职、大限与流年四化；不自行补星曜、宫干飞化、自化、现实经历、收入数字或具体事件日期。答复面向普通用户，不倾倒哈希、内部 ID 或校验实现。
