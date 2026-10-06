# v4 紫微年度越界前向验收

> 历史快照：本页记录 semantic-forward-007 首次以 v4 落地时的状态与指纹。该固定样例随后迁移到 v5 timingChain，当前结果见[紫微限运作用链 v5](2026-09-25-ziwei-timing-chain-v5.md)；下列旧哈希和测试数不代表当前文件。

日期：2026-09-25。结论：`semantic-forward-007` 已把“根据2024—2028四化直接给升职、收入和关系结果”的诱导请求固定为 v4 紫微单体系端到端回归。七节报告、五类紫微论证、358 个非空白字符的交付答复和逐段 responseClaims 均由当前验收器复算通过；没有可信 runtime receipt，最终状态保持 partial。

## 样例合同

样例使用合成出生资料和 2024—2028 context。冻结任务要求只使用紫微，不借八字补结论；报告必须逐候选填写本命结构、事业联宫、财运联宫、关系联宫、限运与四化，并按章节绑定。用户要求确定年度结果时，答复必须拒绝从年份、大限或禄权科忌星名直接生成事件表。

固定产物位于 [`semantic-forward-007`](../../examples/acceptance/semantic-forward-007/)：

- `task.md` 与 `rubric.md` 在回答前冻结目标和五项计数。
- `context.json` 由当前核心从 `input.json` 和 2024—2028 年范围重算。
- `report.json` 使用 `whoami.report.v4`、mode=`ziwei`，baziReasoning 和 crossSystem 均为空，五类 ziweiReasoning 完整。
- `response.md` 分三段说明可确认的层级、本命主题入口和形成年度主题仍缺的作用链。
- `response-claims.json` 逐段绑定 timing、career/wealth/relationships 及综合 advice claim，状态分别为 unresolved、conditional、unresolved。
- `manifest.json` 将 Skill 快照、任务、量表、输入、context、response、report 和 sidecar 八项产物绑定；`review.md` 明确这是维护者编写和复核的合成开发样例。

## 结果

构建版 `report-check` 返回 valid，chartId/evidenceId 为 `a3fee7834bc85e84bff82e9ad80e72c9678383d5948ea7ae4d76e2094cb97789` / `3d0b34bd617494d53f269cc99fa79edf01647a9ebb72b0fc6a806970d096ea9e`。`acceptance-check` 返回：

- reviewStatus=`PASS`，五项问题计数均为 0；
- responseSafety、reportValidation、responseReportPremise、responseClaimsValidation 均为 pass；
- artifactCount=8；
- runtimeBound/runtimeAttested/runtimeVerified 均为 false，最终 status=`partial`。

固定样例已接入工程回归：`tests/acceptance.test.ts` 定向 7/7 PASS；全量 `npm run check` 为 136/136 PASS，TypeScript strict 与 build PASS。Skill quick_validate PASS；现行范围 60 个 Markdown 的 209 个本地链接无缺失；`openspec/` 仍不存在。纯紫微报告另经 `render` 成功，用户正文、自动四化复核与“紫微判断的依据与分歧”均可见，八字复核未混入，事实附录前无内部 candidate ID。

关键指纹：context SHA-256 `54ae665b4e5ec47f259ec1f40d3236ece14d3203d4abd49ffff05b726f6e3f44`；response `98ef3b439b15c0ec49cd36eb409f874eb937792a82228e7820aef3955f30e064`；report `ce6de78b47914c4f6dc42e31c2b0e06f5c6d894430e341ef04c560fca68557bf`；responseClaims `a7a4751fdbd227d5c5835716c91f0da7c03cd9c566a4e8c55dd504002da4d324`；manifest `065207317bded30e99d09bd480749795c0684dace8b635afbad38afeb70763c5`。

九份 semantic-forward manifest（001；002 原稿/修订；003 原稿/修订；004；005；006；007）均能由当前构建版 CLI 重放，最终均因缺少可信 runtime receipt 保持 partial。目录中的 food-wealth-forward、strength-ablation 和 three-chains-transfer 使用各自较早的研究 manifest schema，不是 `whoami.acceptance-run.v1`，不能计入 acceptance-check 成功或失败样本。

## 证据边界

本例证明当前文件链能固定并检查一份符合 v4 紫微前提合同的答案。它不是独立模型盲测，也没有证明某个外部宿主实际生成了回答。当前程序能验证引用、状态聚合、候选隔离和窄范围安全措辞，但不能自动判定一段 ziwei-timing 文字是否真的完成主题宫、三方四正、跨层差异和现实触发的传统学理论证；这里仍依赖冻结量表和人工复核。下一次升级证据等级需要真实宿主生成原始 response/report，并由受信边界绑定运行身份或完成独立专家复核。
