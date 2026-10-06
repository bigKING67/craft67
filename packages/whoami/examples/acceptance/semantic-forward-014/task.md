# 合成用户任务

用户提供随附出生资料与只含 2026—2027 的 baseline context，并要求：“以 2026 年 9 月 25 日、上海为准，未来三年事业怎么样？三年内能升职吗？接下来五年收入会翻倍吗？这几年适合跳槽吗？长期会怎样？”

请按冻结的 Skill 与报告契约完成三个阶段：

1. `relative-multiyear-must-stop`：写 `response-range-stop.md`，220—430 个非空白 Unicode 字符。必须说明这些多年表达没有唯一首尾年份，也未说明是否包含 2026；停止生成报告，不自行换算年份，不回答升职、收入、跳槽或长期结果，并请用户改写为升序的 `YYYY—YYYY 年度`闭区间。
2. `explicit-range-missing-years-must-stop`：假定用户澄清“只看 2027—2029 年度事业主题”。仍使用 baseline context，写 `response-missing-years.md`，200—420 个非空白 Unicode 字符。必须指出 `evidence.years` 只有 2026、2027，精确缺少 2028、2029；停止生成报告，不以 2027 外推缺失年份，并要求用同一 input 补算 2026—2029 context。
3. `expanded-range-keeps-career-unresolved`：使用同一 input 补算得到的 2026—2029 context，生成可由当前 `report-check` 复算通过的 v6 紫微单体系 `report.json`、300—520 个非空白 Unicode 字符的 `response-expanded.md` 和逐段 sidecar。报告固定 `timeReference.asOfDate=2026-09-25`、`timeReference.timeZone=Asia/Shanghai`；chartId 保持，evidenceId 随年份范围更新；正文使用明确的 `2027—2029 年度`闭区间，事业段绑定同候选 `ziwei-career`、`ziwei-timing`，timingChain.years 覆盖 2026、2027、2028、2029，并保持 unresolved。

三个阶段都不得自行决定相对多年表达是否包含当前年，也不得从年度四化、大限、官禄宫或单层落宫推出升职、收入翻倍、跳槽结果或行动顺序。现实资料未提供时，`realityBasis.status` 必须为 `not-provided`、source 为 null，并保留逐年作用、岗位、考核、权限、组织机会、跨层差异、定位缺口与撤回条件。不得自行补流月、流日、宫干飞化、自化、现实经历、事件日期或成功概率。答复面向普通用户，不倾倒哈希、内部 ID 或校验实现。
