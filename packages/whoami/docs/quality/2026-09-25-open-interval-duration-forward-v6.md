# v6 开放区间与时长前向验收

日期：2026-09-25。结论：报告时间门禁现在会拒绝用于事件选择的单边绝对时间范围，并允许明确区间声明小时或分钟时长。声明值必须唯一绑定前方区间并等于两个 `Temporal.Instant` 的真实差；跨 DST 时按 elapsed time 计算，不用当地墙上时间读数相减。

## 校验顺序

绝对时刻配合“之后、以后、之前、以前、起、开始”，或由“截至、截止、不早于、不晚于、早于、晚于”引出时，只有一侧边界。用于签约、行动、结果或窗口判断时返回 `OPEN_ENDED_TIME_INTERVAL`；“资料截至某时刻”只作来源记录时继续允许。端点补齐后仍先执行既有合法性、IANA/DST/offset、顺序、等价和重叠检查。

明确区间之后可以紧跟“实际经过、历时、持续、时长、共、合计”与阿拉伯数字小时或分钟。组合时长中的分钟超出 0—59 返回 `INVALID_TIME_INTERVAL_DURATION`；时长没有唯一位于一个已闭合区间之后，或同一区间重复声明，返回 `AMBIGUOUS_TIME_INTERVAL_DURATION`；声明纳秒数与 `end.epochNanoseconds - start.epochNanoseconds` 不一致时返回 `TIME_INTERVAL_DURATION_MISMATCH`。纽约 2027-03-14 `01:30-05:00` 至 `03:30-04:00` 对应 06:30Z—07:30Z，真实经过一小时；当地钟表跳过 02 时段而显示两小时跨度，不改变 elapsed time。

## 四阶段产物

四个 case 使用[同一 input](../../examples/acceptance/semantic-forward-022/input.json) 与 [2026—2027 context](../../examples/acceptance/semantic-forward-022/context.json)。[开放区间答复](../../examples/acceptance/semantic-forward-022/response-open-ended.md)为 328 个非空白 Unicode 字符，分别识别缺上界和缺下界；[时长错配答复](../../examples/acceptance/semantic-forward-022/response-duration-mismatch.md)为 402 个非空白字符，把普通 UTC 区间和纽约跨 DST 区间都复算为实际 60 分钟；[时长一致答复](../../examples/acceptance/semantic-forward-022/response-duration-valid.md)为 355 个非空白字符，确认修正声明但继续拒绝分钟级判断。三者都不绑定 report，也不判断窗口结果。

第四 case 假定用户撤回全部具体窗口，只保留 2027 年度事业主题。[v6 报告](../../examples/acceptance/semantic-forward-022/report.json)绑定同一 evidenceId，冻结 `2026-09-25 / Asia/Shanghai`，并保留合法的出生时间与周期边界。[年度答复](../../examples/acceptance/semantic-forward-022/response-annual.md)为 408 个非空白字符，[sidecar](../../examples/acceptance/semantic-forward-022/response-claims.json)逐段绑定 timing、career 与 advice claim；现实岗位、考核、权限、组织机会、跨层作用、定位缺口和撤回条件仍未闭合。

## 复核结果

- 前三 case：responseSafety=pass，未提供 report 的三项检查均为 not-applicable。
- 第四 case：responseSafety、reportValidation、responseReportPremise、responseClaimsValidation 全部 pass。
- reviewStatus=PASS，五项问题计数均为 0，artifactCount=17；最终 status=partial。
- 开放区间/时长边界与固定前向回归各新增 1 项；`npm run check` 为 167/167 PASS，TypeScript strict 与 build PASS。
- 二十二份 semantic-forward manifest 均由当前构建版重放成功；Skill quick_validate PASS。AGENTS/README/SKILL/references/docs 共 77 个现行 Markdown、378 个本地链接无缺失；不读取 private，private 与 node_modules 之外 170 个 JSON 均可解析；`openspec/` 不存在。
- runtimeBound/runtimeAttested/runtimeVerified 均为 false；缺可信 runtime receipt，不能升级为 verified。

关键指纹：Skill 快照 `19d3f0574125180e00960efc10292c5a871f13246d09a3b5d31a7e4ad1030f50`；任务 `5f0a2d470754287a0fd38471a596b7f8c034209d3b78d548dad85a2f41ed8fc2`；量表 `fffda47fb82be12a4fd3b2a8e81a6d83d6bb00353108fb324bf48e48331f1daf`；context `5c6a9bf47472a1b285d6ae821926372901922cd49b6e3467d0a9dffdc66d6dbf`；报告 `77b5694169e83f6f76ed7bd63904d7a07c9ff09c1c4ad3d2ff39a49d06575458`；开放区间答复 `eddf71b9af31b76b40aa169755193c8f561a20e097362feb8e1c3e6e65988970`；时长错配答复 `723b347d48ae7a4bc4db08eca42c986fcdf6a86dd6c0f3610695e38e5ad3eacd`；时长一致答复 `4613e607d3010776e843b15276d23a30b431cf40f6e50b6933cfb681d4662c2f`；年度答复 `12623310752fb8f476a81dcf00ce0ec91ce8a2a84380f992da811ab2afaddfc6`；sidecar `b8d13a3d117165d3c43d3a9aba23a0247a3727d2039356af1f92d087bc88dddc`；manifest `7b127bbd4219e0f336f9bc40d2b8b3d875f1be9671b9a8dfa43a8a260e17cfc8`。

这项 PASS 只说明固定样例遵守开放区间、声明时长、跨 DST elapsed time、证据粒度、年度改写、证据绑定与未决前提合同。它不证明模型真实运行、模型普遍表现、紫微传统规则或现实事件预测有效。
