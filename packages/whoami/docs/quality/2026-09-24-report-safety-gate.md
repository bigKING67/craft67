# 报告高风险现实断言门禁

日期：2026-09-24。结论：修复前，`whoami.report.v2` 只要引用结构合法，即使正文写入“命主必死，并且投资稳赚，婚姻必然离婚”也能通过 `validateReport`。现在 `report-check` 与 `render` 会在全部用户可见自由文本入口上执行统一的高置信门禁，并返回 `UNSAFE_REPORT_CLAIM`。这关闭了一个确定性安全缺口，但不把模式匹配夸大为完整语义理解。

## 修复前复现

以当前 `examples/birth.json` 和 `examples/report.json` 重算 2024—2028 context，只替换第一条 claim.text，其余 chartId、evidenceId、factRefs 与 ruleRefs 保持合法。修复前命令正常结束并输出 `UNSAFE_REPORT_ACCEPTED`，证明合法引用此前能够掩盖明显的高风险现实断言。

## 当前行为

新增 `src/report-safety.ts`，将窄范围规则和否定语境处理从报告结构校验中分离。`src/report.ts` 对以下字段统一调用门禁：

- title、uncertainty；
- 每个 section 的 claim.text 与 claim.conditions；
- 每个 baziReasoning 的 conclusion、counterReview、conditions、alternatives；
- 每个 crossSystem.text。

当前拒绝死亡/寿命确定性预测、疾病诊断、保证收益/确定性盈亏和必然婚变/关系事件。错误只返回字段与类别，不回显整段报告。明确的“不能、不得、不宜、不代表、并非、没有”等否定语境允许通过；逗号、句号、分号、换行及“但是/然而/不过/可是”结束此前否定作用，避免“不能保证收益，但是稳赚不赔”逃过检查。

## 验证

- 修复后重放同一故障注入：返回 `UNSAFE_REPORT_CLAIM`，类别为死亡或寿命确定性预测。
- 构建版 CLI 实际执行同一故障输入：stderr 返回结构化 `UNSAFE_REPORT_CLAIM`，退出码 1；临时报告随后清理。
- 定向报告测试：29/29 PASS；新增三项合同覆盖四类断言、全部渲染自由文本入口、否定语境及转折逃逸。
- `npm run check`：126/126 tests PASS，TypeScript strict 与 build PASS。
- 现有 example report JSON 自由文本扫描：无非否定的高风险命中。
- Skill quick_validate 与本地 Markdown 链接检查 PASS。

## 边界

门禁有意保持高精度，不尝试推断所有委婉表达、隐喻、反讽、复杂双重否定或医学/投资建议的完整语义。自然语言前向验收的独立 Markdown response 仍由冻结 rubric 的 `unsafeClaims` 人工复核；本轮没有用模式扫描替代该评审，也没有修改历史原始回答。报告通过门禁只说明未命中当前高置信禁止表达，不能证明传统理论、现实预测或整篇建议安全有效。
