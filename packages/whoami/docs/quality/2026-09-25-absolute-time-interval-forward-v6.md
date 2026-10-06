# v6 绝对时间区间前向验收

日期：2026-09-25。结论：报告时间门禁现在会用两个已归一化的 `Temporal.Instant` 组成明确时间区间，先拒绝零长度、逆序和连续三端点，再归并等价区间并识别正时长交集。只在边界相接的区间不算重叠；结构合法且互不重叠的窗口仍须通过日级、小时级 evidence 门禁。

## 校验顺序

端点继续先经过数字日期、钟点、IANA 当地时刻、DST 分支与显式 offset 一致性检查。两个合法端点以“到、至、—、–、-、~、～”直接连接后才进入区间层：起止 instant 相同返回 `ZERO_LENGTH_TIME_INTERVAL`；起点晚于终点返回 `REVERSED_TIME_INTERVAL`；连续三个端点返回 `AMBIGUOUS_TIME_INTERVAL`。这三类错误不会被静默延长、交换或猜成两段区间。

多个区间用于比较时，起止均相同的不同写法返回 `DUPLICATE_TIME_INTERVAL`；非等价区间只要满足 `startA < endB && startB < endA`，就存在正时长交集，未明确说明重叠时返回 `OVERLAPPING_TIME_INTERVAL`。若一个区间恰在另一区间起点结束，没有正时长交集，不会被误判为重叠。明确说明“区间相同”或“存在重叠”的资料性换算可以保留；用于签约、行动或结果选择时仍返回 `UNSUPPORTED_TIME_GRANULARITY`。

## 四阶段产物

四个 case 使用[同一 input](../../examples/acceptance/semantic-forward-021/input.json) 与 [2026—2027 context](../../examples/acceptance/semantic-forward-021/context.json)。[无效区间答复](../../examples/acceptance/semantic-forward-021/response-invalid.md)为 335 个非空白 Unicode 字符，分别拒绝零长度与逆序；[等价和重叠答复](../../examples/acceptance/semantic-forward-021/response-overlap.md)为 383 个非空白字符，把 A/B 归并为 05:30Z—06:30Z，并定位其与 C 在 06:00Z—06:30Z 的正时长交集；[互不重叠答复](../../examples/acceptance/semantic-forward-021/response-disjoint.md)为 378 个非空白字符，确认两个窗口结构合法但年度 evidence 不足。三者都不绑定 report，也不判断签约结果。

第四 case 假定用户撤回全部具体区间，只保留 2027 年度事业主题。[v6 报告](../../examples/acceptance/semantic-forward-021/report.json)绑定同一 evidenceId，冻结 `2026-09-25 / Asia/Shanghai`，并保留合法的出生时间与周期边界。[年度答复](../../examples/acceptance/semantic-forward-021/response-annual.md)为 393 个非空白字符，[sidecar](../../examples/acceptance/semantic-forward-021/response-claims.json)逐段绑定 timing、career 与 advice claim；现实岗位、考核、权限、组织机会、跨层作用、定位缺口和撤回条件仍未闭合。

## 复核结果

- 前三 case：responseSafety=pass，未提供 report 的三项检查均为 not-applicable。
- 第四 case：responseSafety、reportValidation、responseReportPremise、responseClaimsValidation 全部 pass。
- reviewStatus=PASS，五项问题计数均为 0，artifactCount=17；最终 status=partial。
- 绝对时间区间边界与固定前向回归各新增 1 项；`npm run check` 为 165/165 PASS，TypeScript strict 与 build PASS。
- 二十二份 semantic-forward manifest 均由当前构建版重放成功；Skill quick_validate PASS。AGENTS/README/SKILL/references/docs 共 77 个现行 Markdown、378 个本地链接无缺失；不读取 private，private 与 node_modules 之外 170 个 JSON 均可解析；`openspec/` 不存在。
- runtimeBound/runtimeAttested/runtimeVerified 均为 false；缺可信 runtime receipt，不能升级为 verified。

关键指纹：Skill 快照 `8999e6210dfe260264a8ec645b68735ff94ca41245eb7e9ce1ec9637e749eed1`；任务 `70ea7a4326541f3727a8eb411dcb61166a21b5512bdd67de46fd8446d92da991`；量表 `c2be61ad190809b378e10bd5d62e04cd9ded07f3b454f4e8c1775178ef1e194b`；context `5c6a9bf47472a1b285d6ae821926372901922cd49b6e3467d0a9dffdc66d6dbf`；报告 `77b5694169e83f6f76ed7bd63904d7a07c9ff09c1c4ad3d2ff39a49d06575458`；无效区间答复 `6e80b0ee4a1a535ebb5ebb201295d755edcfe714c7a3d324ddacae448f7ca3c4`；等价和重叠答复 `13673acd8496dff4b2ff74ddf247ca94abf182788a2b29a1a8413be3e658de9e`；互不重叠答复 `e22d12cdac2641b3379ca392c98c040f3726a528c5d5da4e4f37a37b79952839`；年度答复 `6609894015e9bc63342500f571b67f00f6c3a89e6ceba14a454a1e4a08963374`；sidecar `11a581ef65c0090b0bcb055a273e79d2cead1cce2d1f454c569cd82daef2a2fa`；manifest `ddeb64d3a0b144812a8ae220d1783896dba85032e02c0356fd8142ff0ba9c9d2`。

这项 PASS 只说明固定样例遵守区间顺序、等价归并、正时长重叠、证据粒度、年度改写、证据绑定与未决前提合同。它不证明模型真实运行、模型普遍表现、紫微传统规则或现实事件预测有效。
