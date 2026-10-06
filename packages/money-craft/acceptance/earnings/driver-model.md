# 业务驱动模型验收

使用已捕获的贵州茅台 2026 半年报：第 74 页产品收入，第 30–31 页合并利润表。历史输入为 2026H1，演示窗口为 2027H1；并非对已知结果的真实事前预测，也不构成可信投资预测。

收入按茅台酒、其他系列酒、其他业务三个互斥类别相加。未取得可靠量价假设，因此不拆销量/单价。费用率包括销售、管理和研发；税金及附加、金融子公司收支、财务费用及其他收益等明确留在 other_pretax 调整项。历史税前利润、所得税、少数股东损益对应正式报表；毛利和费用比率由金额精确推算，历史归母利润闭合误差小于 0.01 元。

情景采用演示区间：产品收入变化 −5%/0/+5%，毛利率变化 −1/0/+1 个百分点，其他比例和绝对调整额保持历史值。该区间用于验证计算行为，未经过行业/渠道研究证明；模型保留 HYPOTHESIZED、PARTIAL，不附目标价或买卖结论。

```bash
python3 scripts/check_driver_case.py --half-year <2026半年报PDF> --output-dir <全新目录>
python3 skills/money-craft/scripts/money_craft.py earnings drivers --input <全新目录>/model-input.json --json
python3 skills/money-craft/scripts/money_craft.py earnings inspect-preview --baseline <全新目录>/baseline.json --json
```

实际最终文件位于忽略的 `local/evidence/driver-20260915-r2/`。首次 `driver-20260915/` 的产品表 locator 写成第 77 页，属于定位错误的旧版本，保留但不作为验收版本；r2 改为已核对的第 74 页，重新封存，没有改写旧基线。原三季度前瞻仍独立保留。

测试覆盖历史闭合、维度混加、缺失证伪条件、越界敏感性、非有限值、未来来源、实际期间错配、利润桥与无法解释的残差，以及关联模型篡改。实际结果复盘分支使用合成测试；2027H1 实际结果尚未提供。更复杂模型是否优于原机械前瞻，仍需后续样本评价。
