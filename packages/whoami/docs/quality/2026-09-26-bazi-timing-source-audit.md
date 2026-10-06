# 八字岁运来源审计

日期：2026-09-26。结论：已为 `R-bazi-timing` 补齐可定位的传统来源、版本限制、反例类别和运行检查顺序。改动只加强宿主解释合同，不修改确定性排盘、cycles、报告 schema、evidenceId 或现有验收产物。

## 发现与决策

现有规则只写“将具体运年与本命柱联系”“冲不等于灾、合不等于吉”，能阻止最明显的越级，却不能指导宿主处理同类干支不同作用、冲合失效、成格不喜、变格不忌，以及用户反馈的事后回填。

本轮读取《子平真诠》论行运、行运成格变格、支中喜忌逢运透清，《滴天髓》岁运论及《三命通会》卷十一相关段落。五个来源共同支持“岁运须回配本命、逐层看条件、保留反例”；它们没有提供统一数值权重、年度排序或现实事件映射。因此新增 [运行参考](../../references/bazi-timing.md) 和 [来源审计](../research/bazi-timing.md)，未把古文整理成自动吉凶表。

## 变更范围

- `SKILL.md` 在八字大运/流年问题与 `bazi-timing` 写作时强制加载运行参考。
- `references/analysis.md` 将原有年度段落收紧为本命前提、大运、流年、主题、反例、现实资料六层顺序。
- `docs/research/source-manifest.json` 记录五个页面的 2026-09-26 现场指纹、定位语和用途限制。
- 研究索引和分析路线标明来源审计已完成的范围，以及影印校勘与专家盲核仍未完成。

## 验证边界

本轮没有改 TypeScript 行为，现有 context/report/manifest 的哈希无需迁移。现场验证结果：

- 五个来源页面的 SHA-256 和字节数均与 `source-manifest.json` 新增条目一致，来源清单可解析。
- `full-1991` 以相同输入和 2026—2028 重算后，chartId/evidenceId 与收据完全一致；构建版 `report-check` 仍为 valid，四项 artifact 哈希逐项一致。
- `npm run check` 为 185/185 PASS，TypeScript strict 与 build PASS；24 份 semantic-forward manifest 全部重放成功并因无可信 runtime receipt 保持 partial。
- Skill quick_validate PASS；最终文档、JSON、目录状态见总验证记录。

即使这些检查通过，也只证明来源可定位、运行指令彼此一致且旧行为没有漂移。它不证明传统理论、古籍命例、用户反馈或未来预测有效，也不构成命理专家对文本版本和流派的独立审校。
