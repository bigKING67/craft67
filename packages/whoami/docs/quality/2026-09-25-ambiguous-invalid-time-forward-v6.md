# v6 歧义与非法日期时刻前向验收

日期：2026-09-25。结论：时间输入现在先检查自身是否合法且唯一，再检查命理 evidence 是否支持该粒度。`03/04`、`2027-02-29`、`24:30` 与 `09:30 CST` 分别触发月日顺序歧义、无效公历日、非法钟点和非唯一时区；这些输入不再被静默猜测、顺延或默认解释。

## 错误优先级

带年份的数字日期要求分隔符一致且构成真实公历日，否则返回 `INVALID_NUMERIC_DATE`。没有年份、用于事件判断且月/日与日/月两种顺序都成立时返回 `AMBIGUOUS_NUMERIC_DATE`，要求改成 `YYYY-MM-DD`；两种顺序都不成立仍返回 `INVALID_NUMERIC_DATE`。小时超过 23，或分、秒超过 59，返回 `INVALID_CLOCK_TIME`。`CST/EST/PST/MST/IST/BST` 与“北京时间、中国标准时间、美东时间、美西时间、中部时间”等缩写或口语标签不能唯一绑定可复算规则，返回 `AMBIGUOUS_TIME_ZONE`，要求提供 IANA 时区。

这四类错误在 `UNSUPPORTED_TIME_GRANULARITY` 与 `UNSUPPORTED_TIME_OF_DAY` 之前产生。用户把输入修正为有效、唯一的日期、钟点和 IANA 时区后，仍须具备对应日级或小时级 evidence；输入合法性不等于事件时点已有命理依据。

## 两阶段产物

第一 case 使用[同一 input](../../examples/acceptance/semantic-forward-017/input.json) 与 [2026—2027 context](../../examples/acceptance/semantic-forward-017/context.json)。[停机答复](../../examples/acceptance/semantic-forward-017/response-stop.md) 为 288 个非空白 Unicode 字符，在读取命理 evidence 前逐项说明四类错误，不生成 report，不推断加薪、升职、行动或签约结果，也不自行修正输入。

第二 case 假定用户撤回全部问题时点，只保留 2027 年度事业主题。[v6 报告](../../examples/acceptance/semantic-forward-017/report.json) 绑定同一 evidenceId，冻结 `2026-09-25 / Asia/Shanghai`，并保留合法的出生时间与周期边界。[年度答复](../../examples/acceptance/semantic-forward-017/response-annual.md) 为 381 个非空白字符，[sidecar](../../examples/acceptance/semantic-forward-017/response-claims.json)逐段绑定 timing、career 与 advice claim；现实岗位、考核、权限、组织机会、跨层作用、定位缺口和撤回条件仍未闭合。

## 复核结果

- 第一 case：responseSafety=pass，未提供 report 的三项检查为 not-applicable。
- 第二 case：responseSafety、reportValidation、responseReportPremise、responseClaimsValidation 全部 pass。
- reviewStatus=PASS，五项问题计数均为 0，artifactCount=11；最终 status=partial。
- 核心边界测试与固定前向回归各新增 1 项；`npm run check` 为 157/157 PASS，TypeScript strict 与 build PASS。
- 二十二份 semantic-forward manifest 均由当前构建版重放成功；Skill quick_validate PASS。AGENTS/README/SKILL/references/docs 共 77 个现行 Markdown、378 个本地链接无缺失；不读取 private，private 与 node_modules 之外 170 个 JSON 均可解析；`openspec/` 不存在。
- runtimeBound/runtimeAttested/runtimeVerified 均为 false；缺可信 runtime receipt，不能升级为 verified。

关键指纹：Skill 快照 `d43106438a6ff794ebfad895f75e5c586109ef9846560cd8032880a5c7649844`；任务 `6c6a19e337ccdce3aa08dac1968af8d9eaba1651375bdef708bdb679b340404b`；量表 `c20b02402c4efed29a644e2884095c5261bb05e834751cc02e6306558a177020`；context `5c6a9bf47472a1b285d6ae821926372901922cd49b6e3467d0a9dffdc66d6dbf`；报告 `77b5694169e83f6f76ed7bd63904d7a07c9ff09c1c4ad3d2ff39a49d06575458`；停机答复 `8b33282fa05279376580afa80189b46e23b47a383b671a771f0641605ce8f395`；年度答复 `4857030899503c628d34b2928cf86cd0b96955d53cc6e44c4fe664b4c56d78a1`；sidecar `0b42d3ca3db139de886a6d64bbbcbae549141ff9534f748dddc2677ff57acc18`；manifest `76645db945bfd0b0c7eb7ad0c413a69872c78a6f9b1b79460bf497c1ae147be5`。

这项 PASS 只说明固定样例遵守输入合法性与唯一性、错误优先级、年度改写、证据绑定与未决前提合同。它不证明模型真实运行、模型普遍表现、紫微传统规则或现实事件预测有效。
