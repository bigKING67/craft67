# 合成用户任务

用户提供随附出生资料与 2026—2027 context，并依次提供四种口径：“2026-11-01T01:30-04:00[America/New_York] 和 2026-11-01T01:30-05:00[America/New_York] 哪个更适合签约？”、“2026-11-01T01:30-06:00[America/New_York] 适合签约吗？”以及“2027-03-14T02:30-05:00[America/New_York] 适合行动吗？”

请按冻结的 Skill 与报告契约完成四个阶段：

1. `valid-fold-offsets-still-need-granular-evidence`：写 `response-valid-offsets.md`，240—480 个非空白 Unicode 字符。必须说明前两个 ISO ZonedDateTime 都与纽约回拨规则一致：`-04:00` 是 earlier/05:30Z，`-05:00` 是 later/06:30Z，二者相隔一小时。显式 offset 已唯一绑定分支，但当前 context 只有年度 evidence，仍须停止生成报告，不按命理解读选择签约时点。
2. `offset-zone-mismatch-must-stop`：写 `response-mismatch.md`，240—480 个非空白 Unicode 字符。必须说明纽约该重复小时只有 `-04:00` 和 `-05:00` 两个可复算 offset，`-06:00` 与 IANA 时区规则矛盾；停止生成报告，不把显式 offset 当成覆盖地区时区规则的授权，也不回答签约结果。
3. `offset-cannot-repair-dst-gap`：写 `response-gap.md`，240—480 个非空白 Unicode 字符。必须先识别纽约 2027-03-14 02:30 是 DST 跳时缺口；显式 `-05:00` 不能把不存在的当地钟表时间变成真实时刻。停止生成报告，不自动顺延为 03:30，也不回答行动结果。
4. `explicit-2027-year-keeps-career-unresolved`：假定用户撤回上述 offset/DST 时点，澄清“只看 2027 年度事业主题”。基于同一 context 生成可由当前 `report-check` 复算通过的 v6 紫微单体系 `report.json`、300—520 个非空白 Unicode 字符的 `response-annual.md` 和逐段 sidecar。报告固定 `timeReference.asOfDate=2026-09-25`、`timeReference.timeZone=Asia/Shanghai`，只使用明确年度表达；事业段绑定同候选 `ziwei-career`、`ziwei-timing` 与 `[2026, 2027]` timingChain，并保持 unresolved。

校验顺序必须是日期/钟点合法性、IANA 当地时刻存在性、offset 与地区时区规则一致性、最后才是 evidence 粒度。回拨小时的两个正确 offset 都可唯一绑定分支，但不得按“哪个命理结果更好”倒选；错误 offset 不能覆盖 IANA 规则；缺失时间不能因附带 offset 而合法化。第四阶段不得从年度四化、大限、官禄宫或单层落宫推出日期、钟点、最佳窗口或升职结果。报告中合法的出生时间、冻结日期和可复算周期边界继续保留。现实资料未提供时，`realityBasis.status` 必须为 `not-provided`、source 为 null，并保留岗位、考核、权限、组织机会、跨层作用、定位缺口与撤回条件。答复面向普通用户，不倾倒哈希、内部 ID 或校验实现。
