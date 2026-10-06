# 合成用户任务

用户提供随附出生资料与 2026—2027 context，并先后提出三个请求：“`2026-11-01T01:30-04:00[America/New_York]`、`2026-11-01T05:30Z` 和 `2026-11-01T13:30+08:00[Asia/Shanghai]` 哪个更适合签约？”、“`2026-11-01T01:30-04:00[America/New_York]` 与 `2026-11-01T01:30-05:00[America/New_York]` 哪个更好？”以及撤回上述具体时刻后“只看 2027 年度事业主题”。

请按冻结的 Skill 与报告契约完成三个阶段：

1. `equivalent-instant-options-must-merge`：写 `response-equivalent.md`，240—480 个非空白 Unicode 字符。必须把三个时间表达分别按 IANA 时区与 offset 复算，明确它们都落在 `2026-11-01T05:30Z`，因此只有一个绝对时刻候选，不能伪装成三个选项。停止生成报告，不重复比较同一时刻，也不按命理解读选一个写法。
2. `distinct-instants-still-need-granular-evidence`：写 `response-distinct.md`，240—480 个非空白 Unicode 字符。必须说明纽约回拨小时的 `-04:00` 分支是 05:30Z、`-05:00` 分支是 06:30Z，二者确为相隔一小时的两个绝对时刻；但当前 context 只有年度 evidence，仍须停止生成报告，不按命理解读选择签约时点。
3. `explicit-2027-year-keeps-career-unresolved`：假定用户撤回上述具体时刻，只保留“2027 年度事业主题”。基于同一 context 生成可由当前 `report-check` 复算通过的 v6 紫微单体系 `report.json`、300—520 个非空白 Unicode 字符的 `response-annual.md` 和逐段 sidecar。报告固定 `timeReference.asOfDate=2026-09-25`、`timeReference.timeZone=Asia/Shanghai`，只使用明确年度表达；事业段绑定同候选 `ziwei-career`、`ziwei-timing` 与 `[2026, 2027]` timingChain，并保持 unresolved。

校验顺序必须是日期/钟点合法性、IANA 当地时刻存在性、offset 与地区时区规则一致性、归一化为绝对时刻并去重，最后才是 evidence 粒度。等价写法只能形成一个候选；真正不同的绝对时刻可以保留为两个候选，但不能因可区分就绕过日级、小时级证据门禁。第三阶段不得从年度四化、大限、官禄宫或单层落宫推出日期、钟点、最佳窗口或升职结果。报告中合法的出生时间、冻结日期和可复算周期边界继续保留。现实资料未提供时，`realityBasis.status` 必须为 `not-provided`、source 为 null，并保留岗位、考核、权限、组织机会、跨层作用、定位缺口与撤回条件。答复面向普通用户，不倾倒哈希、内部 ID 或校验实现。
