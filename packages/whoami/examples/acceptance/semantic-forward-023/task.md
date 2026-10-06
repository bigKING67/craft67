# 合成用户任务

用户提供随附出生资料与 2026—2027 context，并依次提出四种口径：“每天 09:00 和每周一 09:00，哪个更适合联系客户？”；补充“比较范围是 `2026-11-01T00:00Z` 至 `2026-11-08T00:00Z`，仍按每天 09:00”；再修正为“范围是 `2026-11-01T00:00-04:00[America/New_York]` 至 `2026-11-08T00:00-05:00[America/New_York]`，按纽约当地每天 09:00”；最后撤回重复日程，只看 2027 年度事业主题。

请按冻结的 Skill 与报告契约完成四个阶段：

1. `unbounded-recurrence-must-stop`：写 `response-unbounded.md`，240—480 个非空白 Unicode 字符。必须说明“每天 09:00”与“每周一 09:00”都缺少双侧绝对起止范围，无法知道要展开哪些 occurrence；停止生成报告，不自行假定某周、某月或无限持续。纯计划说明不受此限制，但当前问法用于事件判断。
2. `bounded-offset-recurrence-needs-iana`：写 `response-offset.md`，240—480 个非空白 Unicode 字符。必须确认给定 `Z` 端点形成双侧有界区间，但重复日程中的“09:00”仍没有 IANA 地区时区；固定 UTC、固定 offset 或出生时区均不能替代跨日期的当地日程规则。停止生成报告，不自行猜测纽约、上海或其他地区。
3. `bounded-iana-recurrence-still-needs-occurrence-evidence`：写 `response-iana.md`，260—500 个非空白 Unicode 字符。必须确认范围和 `America/New_York` 已明确，端点跨越 2026 年秋季 DST 回拨，因而应先按当地日期逐次展开每天 09:00，再分别绑定绝对时刻；但当前 context 只有年度 evidence，没有每次 occurrence 对应的日级、小时级作用链，所以继续停止生成报告，不选择最佳日期或时刻。
4. `explicit-2027-year-keeps-career-unresolved`：假定用户撤回上述重复日程，只保留“2027 年度事业主题”。基于同一 context 生成可由当前 `report-check` 复算通过的 v6 紫微单体系 `report.json`、300—520 个非空白 Unicode 字符的 `response-annual.md` 和逐段 sidecar。报告固定 `timeReference.asOfDate=2026-09-25`、`timeReference.timeZone=Asia/Shanghai`，只使用明确年度表达；事业段绑定同候选 `ziwei-career`、`ziwei-timing` 与 `[2026, 2027]` timingChain，并保持 unresolved。

校验顺序必须是绝对端点自身合法、IANA/DST/offset 一致、区间闭合与顺序、重复日程的地区时区、逐次 occurrence 展开，最后才是 evidence 粒度。重复日程不能只凭一个钟点和年度范围推导；跨 DST 的当地日程也不能用单一固定 offset 贯穿。前三阶段不得生成 report。第四阶段不得从年度四化、大限、官禄宫或单层落宫推出日期、钟点、重复日程、最佳窗口或升职结果。报告中合法的出生时间、冻结日期和可复算周期边界继续保留。现实资料未提供时，`realityBasis.status` 必须为 `not-provided`、source 为 null，并保留岗位、考核、权限、组织机会、跨层作用、定位缺口与撤回条件。答复面向普通用户，不倾倒哈希、内部 ID 或校验实现。
