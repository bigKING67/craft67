# 五类论证主题依据门禁

日期：2026-09-25。结论：报告校验不再只要求“存在事实、规则与五个主题”。每项八字或紫微论证现在还必须引用当前 evidence 中与该主题稳定对应的事实锚点和规则作用域；只挂一个无关事实或把四化规则复用到事业、财运、关系等全部主题，会分别返回 `MISSING_TOPIC_EVIDENCE` 或 `MISSING_TOPIC_RULE`。

## 可证明范围

八字沿用现有总规则，不强迫五项使用互不相同的规则。旺衰检查月柱与 rootDetails；格局检查 monthExposure；调候检查月柱；扶抑检查 rootDetails 或 relations；最终取舍检查 monthExposure、wealthReview、rootDetails 至少一项。每项还要引用其允许的 structure、root-review、wealth-review 或 month-exposure 规则，运年规则不能单独冒充本命主题规则。

紫微本命结构检查 base、命宫事实及至少一条联宫规则；事业、财运、关系分别检查官禄、财帛、夫妻宫及对应联宫规则；限运继续检查 transformations 规则，并沿用既有 timingChain 对四化、运限、主题宫和年份的更严格约束。规则与事实仍须属于同一候选，原有候选隔离、规则—事实关联及重复引用门禁保持有效。

这组映射只使用当前 evidence 的稳定 ID 后缀和宫位结构值，不扫描自由文本关键词，也不按文字相似度判断相关性。审计的 22 份 `report.json` 共包含 35 项八字论证、100 项紫微论证，全部满足新锚点；因此没有改写冻结报告、context、manifest 或历史 Skill 快照。

附加重放六份当前主报告时，发现三份报告仍含此前时间门禁已经拒绝的旧措辞：`当月令财透` 被分词为“当月”，`从元旦持续到年底`、`公历年初`、`未来五年`、`每季度`及两处“何时”混合了年度边界与细分计划。逐项核对后只做语义等价澄清：改成“视作月令财透”“完整公历年区间”“同一公历年的起算边界”，并把现实建议改为无固定日程的目标、职责和复盘触发条件。主报告、full-1996 与 ordinary 的 JSON 随后由当前构建版重新渲染；其余三份保持原字节。

## 验证边界

- 新增三项直接回归：八字错挂运年规则、调候缺月柱；紫微事业错挂财运规则、缺官禄宫；本命结构缺 base 或只挂四化规则。
- `npm run check`：178/178 PASS；TypeScript strict 与 build PASS。
- 构建版 CLI 对八字错规则、八字缺锚点、紫微错规则、紫微缺主题宫四个故障样例均退出 1，并分别返回预期的 `MISSING_TOPIC_RULE` 或 `MISSING_TOPIC_EVIDENCE`。
- 主样例、boundary、full-1991、full-1996、ordinary、strength-balance 六份当前报告均由构建版 `report-check` 返回 valid；三份文字澄清报告的 Markdown 已重新渲染。
- 23 份 semantic-forward manifest 由当前构建版逐份重放成功，仍因缺可信 runtime receipt 保持 partial；没有新增第 24 份，因为本轮是确定性 report JSON 合同，不以复制自然语言回答代替直接门禁测试。
- Skill quick_validate PASS；AGENTS/README/SKILL/references/docs 共 82 个现行 Markdown、404 个本地链接无缺失；不读取 private，private 与 node_modules 之外 175 个 JSON 均可解析；`openspec/` 与 `.git/` 均不存在。

完整检查第一次运行时，重构后的 acceptance 测试夹具遗漏了跨体系断言仍使用的 `ziweiFact` 局部变量，导致 177/178；恢复夹具变量后同一完整命令为 178/178。没有为变绿放宽主题规则、事实锚点或时间门禁。

这些 PASS 只证明报告至少引用了主题需要的结构化入口，不能证明引用文字正确解释了事实、传统规则成立、各证据权重合理，或现实预测有效。
