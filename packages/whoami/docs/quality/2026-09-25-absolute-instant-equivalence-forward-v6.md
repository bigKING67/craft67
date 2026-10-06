# v6 绝对时刻等价归并前向验收

日期：2026-09-25。结论：报告时间门禁现在会把合法的 IANA 当地时间、带地区时区的显式 offset 和独立 Z/offset 时间统一归一化为 `Temporal.Instant`。多个写法落到同一个绝对时刻时只保留一个候选，并拒绝把同一时刻包装成多个选项反复比较；归一化后确实不同的时刻继续保留，但仍须通过日级、小时级 evidence 门禁。

## 校验顺序

校验器先复用数字日期与钟点合法性检查，再验证 IANA 当地时刻存在性、DST 分支及显式 offset 一致性，之后才把合法表达转换为 canonical instant 并按其字符串分组。比较语境中，同一 canonical instant 出现多次会返回 `DUPLICATE_ABSOLUTE_TIME`；仅用于说明“同一绝对时刻”或“写法等价”的信息性陈述可以通过。归一化后不同的 instant 不会被误并，但用于签约、行动、结果或窗口判断时仍返回 `UNSUPPORTED_TIME_GRANULARITY`。

`2026-11-01T01:30-04:00[America/New_York]`、`2026-11-01T05:30Z` 与 `2026-11-01T13:30+08:00[Asia/Shanghai]` 均为 05:30Z，只能形成一个候选。纽约同日的 `01:30-05:00` 则是 later/06:30Z，与 earlier/05:30Z 相隔一小时，仍是两个不同候选。非法的绝对时间继续优先返回 `INVALID_NUMERIC_DATE` 或 `INVALID_CLOCK_TIME`；同时修复了 offset 片段 `01:30-04:00` 中 `30-04` 被年缺失数字日期规则误识别的假阳性。

## 三阶段产物

前三个 case 使用[同一 input](../../examples/acceptance/semantic-forward-020/input.json) 与 [2026—2027 context](../../examples/acceptance/semantic-forward-020/context.json)。[等价时刻答复](../../examples/acceptance/semantic-forward-020/response-equivalent.md)为 420 个非空白 Unicode 字符，把三个表达归并为一个 05:30Z 候选；[不同时刻答复](../../examples/acceptance/semantic-forward-020/response-distinct.md)为 423 个非空白字符，保留 05:30Z 与 06:30Z 的一小时时差。两者都不绑定 report，也不判断签约结果。

第三 case 假定用户撤回全部具体时刻，只保留 2027 年度事业主题。[v6 报告](../../examples/acceptance/semantic-forward-020/report.json)绑定同一 evidenceId，冻结 `2026-09-25 / Asia/Shanghai`，并保留合法的出生时间与周期边界。[年度答复](../../examples/acceptance/semantic-forward-020/response-annual.md)为 394 个非空白字符，[sidecar](../../examples/acceptance/semantic-forward-020/response-claims.json)逐段绑定 timing、career 与 advice claim；现实岗位、考核、权限、组织机会、跨层作用、定位缺口和撤回条件仍未闭合。

## 复核结果

- 前两 case：responseSafety=pass，未提供 report 的三项检查均为 not-applicable。
- 第三 case：responseSafety、reportValidation、responseReportPremise、responseClaimsValidation 全部 pass。
- reviewStatus=PASS，五项问题计数均为 0，artifactCount=14；最终 status=partial。
- 绝对时刻归一化边界与固定前向回归各新增 1 项；`npm run check` 为 163/163 PASS，TypeScript strict 与 build PASS。
- 二十二份 semantic-forward manifest 均由当前构建版重放成功；Skill quick_validate PASS。AGENTS/README/SKILL/references/docs 共 77 个现行 Markdown、378 个本地链接无缺失；不读取 private，private 与 node_modules 之外 170 个 JSON 均可解析；`openspec/` 不存在。
- runtimeBound/runtimeAttested/runtimeVerified 均为 false；缺可信 runtime receipt，不能升级为 verified。

关键指纹：Skill 快照 `51bd0fe9c84b63ac6daf0606c9a7a5d4db9430e2663df8fc185d7c28611a9f47`；任务 `7517b494118b1c67a93922bcd313c5f8b7c43a0a01a61273803f42888cbd4ee8`；量表 `21f5b24a0ad43995bccac67a3f2bef445077202eaceedc895c6e7755bf280bfb`；context `5c6a9bf47472a1b285d6ae821926372901922cd49b6e3467d0a9dffdc66d6dbf`；报告 `77b5694169e83f6f76ed7bd63904d7a07c9ff09c1c4ad3d2ff39a49d06575458`；等价时刻答复 `07e37f21a2d0b72ad70b5c2f2a48319a7a1c8fa4b635e31e1bd81309c0e12856`；不同时刻答复 `60f1c50079da9f9f38c10d7d2be662d65bd93d506f91a7cb5f9ebadcbd4982a7`；年度答复 `1402bd478f88df67b0b714321707ed4815ceee17efce3806d6f3d6872e2d839b`；sidecar `87fcee70d5f5fae2cb367163e7625ae46e52bc0252e705adbcc9e81c2e652025`；manifest `3c76a3c30fceeefc99b66e5be063eaaf10019b7d9447e38f1a9875cb9bdd44d9`。

这项 PASS 只说明固定样例遵守绝对时刻归一化、候选去重、证据粒度、年度改写、证据绑定与未决前提合同。它不证明模型真实运行、模型普遍表现、紫微传统规则或现实事件预测有效。
