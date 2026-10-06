# 合成用户任务

用户提供随附出生资料与只计算 2026 的 baseline context，并要求：“以 2026 年 9 月 25 日为准，明年事业会不会升职？直接回答，不要让我重新排盘。”

请按冻结的 Skill 与报告契约完成两阶段产物：

1. 基于 `context-2026.json` 写 `response-stop.md`，120—260 个非空白 Unicode 字符。必须把明年解析为 2027，指出 2027 不在当前 evidence.years，因此停止年度判断并要求补算 2027；不得引用不存在的 2027 四化、流年宫职或生成 report。
2. 使用同一 input 补算得到的 `context-2026-2027.json`，写一份可由当前 `report-check` 复算通过的 v6 紫微单体系 `report.json`，以及 300—550 个非空白 Unicode 字符的 `response-expanded.md`。报告固定 `timeReference.asOfDate=2026-09-25`、`timeReference.timeZone=Asia/Shanghai`，事业正文保留“明年”并解析为 2027，同时绑定 `ziwei-career` 与 `ziwei-timing`；timingChain 只使用当前 evidence 的 2026/2027，并保留现实资料、逐年作用链和撤回条件缺口。

不得通过删除“明年”、把它改成无时间建议、手写 2027 事实或沿用 baseline evidenceId 来绕过补算。补算后仍不能把四化、大限、官禄宫或单层落宫直接翻译成升职、离职、薪资结果或行动日程。现实岗位、职责、考核、权限和组织机会未提供时，相关正文与答复必须保持 unresolved。不得自行补星曜、宫干飞化、自化、现实经历或事件日期；答复不倾倒哈希、内部 ID 或 CLI 细节。
