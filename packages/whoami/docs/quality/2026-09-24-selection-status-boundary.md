# 最终取舍 conditional / unresolved 边界验收

日期：2026-09-24。结论：selection 的状态不能由其他四个 topic 的状态投票决定。`conditional` 要求在明确语境中真正提出具体方向，并写全前提、反证与撤回条件；只有候选入口、支持基础或待比较分支时，必须保持 `unresolved`。

## 验收矩阵

三份报告均为仓库内合成样例，使用各自固定输入和年份。判断对象是报告语义合同，不是命理准确率。

| 样例 | strength | pattern | climate | balance | selection | 关键原因 |
|---|---|---|---|---|---|---|
| [`strength-balance/report.json`](../../examples/acceptance/strength-balance/report.json) | conditional | unresolved | unresolved | conditional | conditional | 在普通格且暂偏弱这一限定语境中，食伤制泄与官杀化生两条待核路径都明确落到印星木候选；报告同时写明印是否可用、财制印、强弱转向、格局与调候仍会改判 |
| [`examples/report.json`](../../examples/report.json) | conditional | conditional | conditional | conditional | unresolved | 四项只是支持基础、偏财格入口、壬水调候候选和财荷优先比较；没有已经成立的具体取用方向，扶抑潜在比劫与调候壬水也不可合并 |
| [`full-1991/report.json`](../../examples/acceptance/full-1991/report.json) | unresolved | unresolved | unresolved | conditional | unresolved | 财、杀、食伤分支分别依赖尚未裁定的强弱和主要负荷，方向没有收敛 |

该矩阵同时阻止两种错误：一是看到任一 unresolved 就拒绝范围明确的扶抑候选；二是看到四个 conditional 就机械宣布最终喜用已选。

## 主报告更新

主报告 selection 继续为 `unresolved`，但不再只写“条件未完成”。结论明确列出：扶抑只有在偏弱且财为主要负荷时才讨论比劫；调候只有所选版本下的壬水复核候选；偏财格入口没有给出格局用神。三者没有形成同一范围内的具体方向，因此不选统一喜用。

正文仍可给低风险、与五行无关的现实建议；不得把学习、颜色、方位、职业、投资或用户事后反馈倒填为 selection 的证据。

## 验证边界

本轮没有修改报告 schema、核心计算、依赖或自动语义门禁。三份 `report-check` 只能证明结构、引用和显式前提状态有效；人工复核负责确认限定范围、条件和撤回路径确实写入。测试与样例均不证明传统理论或现实预测有效。

## 验证结果

- 主样例、`strength-balance` 正例与 `full-1991` 反例分别按各自固定输入和年份执行构建版 `report-check`，三份均返回 `status: valid`。对应 chartId / evidenceId 为：
  - 主样例：`a3fee7834bc85e84bff82e9ad80e72c9678383d5948ea7ae4d76e2094cb97789` / `3d0b34bd617494d53f269cc99fa79edf01647a9ebb72b0fc6a806970d096ea9e`；
  - `strength-balance`：`4b6a66ef698209a07964e294019e8ad54923b3fc74eccaa1786dc7aeaa20f62a` / `8412f9eadc80551ea35b44533fafb97fe6dad691f990827416b521d2e1aeb410`；
  - `full-1991`：`3f46b10f2f63940f5b589531a6cd9a4866c904062a8580dc1ae843cd59c7786a` / `eaf468fb8c1a63f9440e51743c82d658fc71a2021293243a2082393f734c0bce`。
- 本项 selection 验收完成时，主样例重新 `render` 后与 `examples/report.md` 字节一致；当时的 `examples/report.json` 为 28,901 字节、SHA-256 `404cd7584a2258984e35dbc80a0bdeecf9c5e88a748ef3209af2a1088b874b50`，`examples/report.md` 为 67,379 字节、SHA-256 `f0607f656424cba05bcc392437da07bc1fdd0b74ba4c7dc801ce87ec325caa1e`。后续年度行动日程边界收紧改变了两份文件的当前指纹，但没有改变本项五个 topic 的状态矩阵；当前指纹记录在 `docs/quality/2026-09-24-yearly-timing-boundary.md`。
- Skill `quick_validate.py` 返回 `Skill is valid!`。`openspec/` 仍不存在。
- README、SKILL、`docs/`、`references/` 与当前主样例正文共 57 个 Markdown、192 个本地链接，缺失目标为 0。
- 本轮 selection 收口只改运行参考、研究说明、质量记录及主样例文字，没有改 `src/`、`tests/`、报告 schema、依赖或自动校验器。最近一次全量代码门禁仍是此前已记录的 `npm run check` 132/132 PASS；本轮没有将它重复执行并冒充新的验证结果。
