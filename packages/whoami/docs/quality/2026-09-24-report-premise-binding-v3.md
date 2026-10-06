# 报告正文—八字论证前提绑定 v3

日期：2026-09-24。结论：报告升级为 `whoami.report.v3`。含八字事实的 claim 与 crossSystem 现在必须绑定同候选具体 baziReasoning 主题，`premiseStatus` 由所引论证状态决定；未决前提不能自行标成 conditional，也不能显式写成“已经成立、无需核对、唯一用神”。渲染结果会把未决或条件性前提直接显示在相关正文下。

## 原缺口

v2 已要求逐候选填写 strength、pattern、climate、balance、selection，但正文与这些论证之间只有人工核对约定。既有故障注入“财旺生官已经成立，不必理会其他条件”引用合法事实和规则，仍能通过结构校验；这使正文可以绕过本身标为 unresolved 的论证。

## v3 合同

每个 claim 与 crossSystem 新增：

```json
{
  "reasoningRefs": [
    {"candidate": "C1-...", "topic": "selection"}
  ],
  "premiseStatus": "unresolved"
}
```

校验器执行以下约束：

- 每个被 factRefs 引用的八字候选至少有一条 reasoningRef；另一候选、悬空主题、重复引用和无八字事实却绑定论证均拒绝。
- 正文明示旺衰、格局、调候、扶抑、用神/喜忌时，要求同候选对应主题。
- 任一所引 reasoning status 为 unresolved，premiseStatus 必须为 unresolved；全部 conditional 才能为 conditional；无八字事实时必须是 not-applicable。
- 未决项拒绝“已经成立、结论已定、唯一用神、无需核对条件”等窄而高置信的越级表述。否定语境允许，逗号、句号、分号和转折结束前一否定作用。
- render 在正文下显示如“八字论证前提：未决（C1/旺衰、C1/用神取舍）”。

## 迁移与验证

8 份现有 report JSON 已机械迁移为 v3：正文、factRefs、ruleRefs、baziReasoning 内容和 status 未改，只增加 reasoningRefs/premiseStatus。迁移后共有 77 条 claim：46 条 unresolved、13 条 conditional、18 条 not-applicable；7 条 crossSystem 均如实保留 unresolved。7 份现有 Markdown 已由构建版 CLI 重渲染。

- 修复前故障注入会放行；修复后返回 `UNRESOLVED_PREMISE_CLAIM`。
- 报告定向测试 33/33 PASS，新增四项合同覆盖缺失/跨候选/重复绑定、状态伪装、主题缺失、否定语境和渲染可见性。
- 8/8 report JSON 使用各自原始输入与年份，经构建版 `report-check` 全部 PASS。
- `npm run check`：130/130 tests PASS，TypeScript strict 与 build PASS。
- 构建版 CLI 反例：v2 schema 返回 `INVALID_REPORT`，未决正文写“用神已经确定，无需再核对其他条件”返回 `UNRESOLVED_PREMISE_CLAIM`；两者退出码均为 1、stdout 为空。
- Skill quick_validate PASS；48 个 Markdown 文件的 160 个本地链接全部可达。

## 仍有限的部分

reasoningRefs 由报告作者选择；校验器能验证候选、主题、状态与明显关键词，却不能证明作者列出的主题已经穷尽正文全部隐含前提。显式越级门禁保持高精度，不尝试理解所有同义改写、反讽或长距离语义矛盾。v3 显著收窄“未决在后文悄悄变确定”的空间，但仍不能替代逐段语义复核、传统来源审校或现实预测验证。
