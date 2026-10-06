# 流动性语义验收案例

本轮将美的研究暴露的四类问题转为虚构数值的正反例：法人范围、流动可转债、受限现金重复扣减、产品到期与解押。每一对只改变结论，事实与计算回执不变。具体规则补入 Skill 的 research-semantic-review.md，不修改计算核心，不将真实公司暂时缺项泛化成所有公司的必填清单。

四组八份报告实际经过 report_audit 与 financial_rigor；四条错误解释也通过了结构和算术审计。此结果记录现有机器审计的边界，不能声称自动拦截了经济解释错误。人工标签来自作者和主代理自审，不是独立、盲测、留出集或泛化成绩。

37项定向测试通过：新增2项测试与既有35项审计测试。新增测试覆盖正反例仅改变解释的隔离性、四个数值篡改对照，以及回执不冒称语义/宿主验收。未锁定错误解释未来必须通过；若后续审计增加语义能力，runner会记录新结果而非要求保留盲区。

复现命令：

```sh
python scripts/check_liquidity_semantics.py --output local/liquidity-replay.json
python -m unittest discover -s tests -p test_liquidity_semantics.py
python -m unittest discover -s tests -p test_audits.py
```

本轮使用 local/validation/disclosure-candidate/bin/python 执行上述命令。验收产物位于 acceptance/liquidity-semantics/；其中 replay-20260921.json 是机器实际结果，acceptance-20260921.json 绑定规则、runner、测试及案例哈希。

acceptance/skill-tasks/liquidity-cases-20260921.json 提供后续真实宿主任务与评审标准，状态为 READY_SYNTHETIC_NOT_EXECUTED。执行时只传 prompt/facts，不向被测宿主传 criteria、正反例或参考答案，再对实际工具轨迹与回答评审。本轮没有运行该宿主验收、没有同步全局安装、没有独立审查或完整仓库验收；不将源码规则补齐等同已安装 Skill 生效。原美的研究的PARTIAL不因工程案例通过而改变。
