# v6 offset 与 IANA 一致性前向验收

日期：2026-09-25。结论：报告时间门禁现在支持 `YYYY-MM-DDTHH:mm[:ss]±HH:mm[Area/Location]`，并要求显式 UTC offset 与 IANA 地区时区在该当地时刻的真实规则一致。纽约回拨小时的 `-04:00/-05:00` 两个分支都可复算，`-06:00` 被拒绝；春季缺失小时即使附带 offset 也不能合法化。

## 校验顺序

校验器先沿用 `inspectLocalDateTime` 判断当地钟表时间是否存在，再从 unique 或 ambiguous 结果取得可复算 offset 集合，最后比较输入的显式 offset。缺失时间优先返回 `NONEXISTENT_LOCAL_TIME`；地区时区无法识别返回 `INVALID_TIMEZONE`；当地时刻存在但 offset 不属于可复算集合时返回 `OFFSET_TIME_ZONE_MISMATCH`。只有全部一致，才继续进入日级、小时级 evidence 门禁。

纽约 `2026-11-01T01:30-04:00[America/New_York]` 对应 earlier/05:30Z，`-05:00` 对应 later/06:30Z；两者当地钟表读数相同但绝对时刻相隔一小时。`-06:00` 不会制造第三个分支。`2027-03-14T02:30-05:00[America/New_York]` 的核心问题仍是 02:30 不存在，不能让 offset 覆盖地区时区规则，也不能自动顺延为 03:30。

## 四阶段产物

前三 case 使用[同一 input](../../examples/acceptance/semantic-forward-019/input.json) 与 [2026—2027 context](../../examples/acceptance/semantic-forward-019/context.json)。[正确分支答复](../../examples/acceptance/semantic-forward-019/response-valid-offsets.md)为 425 个非空白 Unicode 字符，确认两个 offset 分支都真实但 evidence 粒度不足；[错配答复](../../examples/acceptance/semantic-forward-019/response-mismatch.md)为 383 个非空白字符，拒绝 `-06:00`；[缺失小时答复](../../examples/acceptance/semantic-forward-019/response-gap.md)为 341 个非空白字符，拒绝用 offset 修补 DST 缺口。三者都不绑定 report，也不判断签约或行动结果。

第四 case 假定用户撤回全部 offset/DST 问题时点，只保留 2027 年度事业主题。[v6 报告](../../examples/acceptance/semantic-forward-019/report.json)绑定同一 evidenceId，冻结 `2026-09-25 / Asia/Shanghai`，并保留合法的出生时间与周期边界。[年度答复](../../examples/acceptance/semantic-forward-019/response-annual.md)为 423 个非空白字符，[sidecar](../../examples/acceptance/semantic-forward-019/response-claims.json)逐段绑定 timing、career 与 advice claim；现实岗位、考核、权限、组织机会、跨层作用、定位缺口和撤回条件仍未闭合。

## 复核结果

- 前三 case：responseSafety=pass，未提供 report 的三项检查均为 not-applicable。
- 第四 case：responseSafety、reportValidation、responseReportPremise、responseClaimsValidation 全部 pass。
- reviewStatus=PASS，五项问题计数均为 0，artifactCount=17；最终 status=partial。
- offset/IANA 边界与固定前向回归各新增 1 项；`npm run check` 为 161/161 PASS，TypeScript strict 与 build PASS。
- 二十二份 semantic-forward manifest 均由当前构建版重放成功；Skill quick_validate PASS。AGENTS/README/SKILL/references/docs 共 77 个现行 Markdown、378 个本地链接无缺失；不读取 private，private 与 node_modules 之外 170 个 JSON 均可解析；`openspec/` 不存在。
- runtimeBound/runtimeAttested/runtimeVerified 均为 false；缺可信 runtime receipt，不能升级为 verified。

关键指纹：Skill 快照 `7d09cf63ed258f0ef492f701c9df9c43d4d1092ca935513b2b8417eb5e50d434`；任务 `f4ed8ffdeeb06a575d3269f2d52f88c5362576732d2a472947bda072238ab7d5`；量表 `2e24a1fe9d6417dae2ba46e0e018d5e6379fd90eedacd33ac470c423f817771b`；context `5c6a9bf47472a1b285d6ae821926372901922cd49b6e3467d0a9dffdc66d6dbf`；报告 `77b5694169e83f6f76ed7bd63904d7a07c9ff09c1c4ad3d2ff39a49d06575458`；正确分支答复 `f430ad377d3c060f3a7d227698297f83ea4bde0ca00a3b8173d378909cfc0c0b`；错配答复 `8d8dcef71ca93d7ef1372b2b081a3b54e458622baf7e76e4e0aded559f1efe8c`；缺失小时答复 `4996392f563c1763d49495b636836f3ea087aa4b98fac548984177ec0d7315ca`；年度答复 `3bca54f91a22cce1c3bd8951ecd9b13326f4b3cf085a6be3ff16954b8ba08fe2`；sidecar `54907d79f4d78ea61e093a9f74ff6be0ae9d3ee5fb85bc89b8d28bccdf5f2625`；manifest `f91b2d7db68ee095198484d3ff7cd364553d5f26d7055fc0e40e4d8003e0fe2a`。

这项 PASS 只说明固定样例遵守显式 offset/IANA 一致性、DST 优先级、证据粒度、年度改写、证据绑定与未决前提合同。它不证明模型真实运行、模型普遍表现、紫微传统规则或现实事件预测有效。
