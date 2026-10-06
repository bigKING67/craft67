# Target 历史估值案例

范围：2025-04-30 截止的 US-NYSE:TGT 普通股；2026-09-20 执行历史材料回放。目标是验证估值输入、资本结构桥及假设的证据边界，不创建应用、正式 money 档案或交易建议。

- [研究报告](../acceptance/target-valuation/reconstruction/report.md)
- [手工提取输入与原文定位](../acceptance/target-valuation/input.json)
- [来源元数据与哈希](../acceptance/target-valuation/evidence-manifest.json)
- [计算结果与敏感性](../acceptance/target-valuation/reconstruction/result.json)
- [最终文本计算审计](../acceptance/target-valuation/reconstruction/financial-audit.json)
- [主代理语义复核](../acceptance/target-valuation/semantic-review.json)

## 复现

原始 PDF/HTML/JSON 保留在忽略的私有证据目录，不随仓库/Skill 分发。准备 manifest 指定的原件后运行：

```bash
python3 scripts/check_valuation_case.py --output-dir <新的输出目录>
```

脚本先检查 8 份来源的 SHA-256，再用共享 `financial_rigor` 计算 39 条回执并审计最终 Markdown。输出目录必须不存在；不会覆盖既有回执。网页会变化，重新下载的同 URL 文件不一定匹配旧哈希，不能更改 manifest 来伪装复现。

本次未新增通用估值引擎：实际算术由现有共享核心覆盖；新增脚本只固定本案例输入、公式和输出，不能自动认证原文提取、日期对齐或经济假设。

## 实际发现与修补

Skill 的历史价格规则补充分界：走势复权与历史时点市值/PE 使用场景不同。估值引用补充股数/余额/行情日期桥、融资租赁去重、现金内短投去重、权益倍数与 EV 转换、正常化调整及外部倍数归属。相对于上一安装基线仅这两份引用变化。

四个错误变体均能通过算术审计，但语义应拒绝：重复加融资租赁、重复扣短投、用加权平均股数计算市值、给 EPS×PE 再扣净债务。回执明确为主代理判断，不声称程序自动拒绝。

## 结论限制

有界重建通过不等于完整合理价值研究完成。精确当日资本结构、独立来源血缘、经营驱动下的可持续盈利、完整同行倍数及历史截止事件覆盖仍有缺口。三情景为有来源归属的条件计算；同一分析师的预测与倍数不能充当两项独立验证，不能把上行价差称安全边际。

## 宿主与安装验收

[完整源码案例](../acceptance/skill-tasks/target-valuation-host-20260920.json)的8份原件、41条回执及8项人工语义标准通过；[安装版收口](../acceptance/skill-tasks/target-valuation-installed-20260920.json)为更窄的新问题，2份原件、9条回执和4项人工语义标准通过。两次均独立宿主执行，语义由主代理复核；不是相同prompt复测或独立语义审查。

候选包7项检查通过，源码/候选/安装75文件一致，35项财务审计回归通过。源码门禁19项在隔离PyYAML验证环境通过；默认Python及现有报告环境的缺包失败没有当作源码成功。全局旧安装保留备份；本次无commit、push或Release。

## 后续经营驱动与事件复核

[增量报告](../acceptance/target-drivers/reconstruction/report.md)补充三月电话会和四月官方政策原件，建立有限事件表及 EPS 所需营业利润率的反推。它识别已实现节约/损耗改善不得重复加回、现金缓冲限制回购假设、政策变化要求重新核验较早预测；没有给政策冲击虚构成本系数。

5份原件绑定、124条计算和9组反推/正向回代通过；未来事件、来源哈希篡改、历史净利润不勾稽3种负向输入均拒绝。[主代理复核回执](../acceptance/target-drivers/review.json)另列语义判断与未决依赖，本轮没有新增独立宿主验收。

这是一份后续研究增量：原压力组合仅保留为压力参照，原外部基准及乐观组合标记 NEEDS_REUNDERWRITING；原报告及安装回执保持原样。脚本 `scripts/check_target_driver_case.py` 使用现有共享 Decimal 核心；保持其案例复现用途，不是新的通用预测 API。

## 首份后续季度披露回放

[Target Q1 增量报告](../acceptance/target-q1/reconstruction/report.md)将研究截止推进至2025-05-21，实际执行于2026-09-20。GAAP盈利增长包含诉讼和解收益，调整后盈利及年度销售/调整后EPS指引转弱；原修复基准需要重建。旧截止报告、驱动假设和来源哈希保持不变，新结果没有回填为事前预测。

[案例回执](../acceptance/target-q1/review.json)：3份来源绑定、46条计算通过，未来披露、未推进截止、来源哈希变化、现金桥与EPS桥错误5类输入均拒绝。库存与销售背离目前只验证一个季度，保留WATCH，不提前触发旧规则的连续两季条件。此复现器固定本案例，不能替代通用来源真实性或经济语义审查。

[安装版自然语言宿主验收](../acceptance/skill-tasks/target-q1-host-20260920.json)：隐式读取已安装Skill，路由READY，2份原件哈希和19条计算通过，5项语义标准经主代理复核通过。宿主仅收到所选原件与问题，未提供主代理答案；执行独立，语义审查不独立。宿主把指引中点明确作为过渡假设，未误称承诺或长期正常化盈利。本次未变更Skill或共享运行时代码，也未重新安装。

本次完成的是有界的业绩跟踪验收；同一发行人的公告不构成独立双源，未完成全量10-Q审读或合理价值重估，不代表预测能力评分。
