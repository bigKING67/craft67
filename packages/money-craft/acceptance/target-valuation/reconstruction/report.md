# Target：历史估值重建与条件情景

研究执行日：2026-09-20；历史截止：2025-04-30 美股收盘；对象：Target Corporation，US-NYSE:TGT，普通股，USD。金额为百万美元，股数为百万股，每股金额为美元。本案例验收 Skill 与共享计算核心，不是当前买卖建议、完整公司研究或正式 money 档案。

结论：可以重建最近已披露余额下的市值/EV、报告盈利倍数和有署名依据的条件情景。可持续盈利、当日资本结构和估值倍数尚未独立证实，因此不能交付确定的合理价值、安全边际或买入评级。算术通过不解除这些限制。

## 数据日期和血缘

财报余额日 2025-02-01；10-K 审计日 2025-03-12；封面股数观测日 2025-03-05。价格为 2025-04-30。未取得三月股数及二月余额到四月底的完整回购/分红/融资滚动桥。所有原件为 2026-09-20 或此前案例的事后下载，不是 2025 年保存的快照。

S04 的当日 Close 为 96.70；S07 的 quote.close 为 96.69999694824219，按美元分位还原为 96.70，差异来自机器浮点表示。S07 同时另列 adjclose；S06 的抓取页面为 90.89，而搜索缓存曾显示 91.59。后两者未证明适用于原始历史报价，不能平均这些价格，也不能仅凭相近就确认 S06 的复权算法。Yahoo 与 ChartExchange 上游行情血缘未核实，数值一致不宣称独立双源。[S04][S06][S07]

S01 与 S02 同属发行人，不算独立来源。S03 对披露数值的转录可作复核，但仍依赖发行人原始财报；它的预测和倍数属于分析师观点。S08 为 Walmart 发行人材料，S09 只取得一个行情 Provider，相关倍数保留单源限制。

## 资本结构桥

以下都是 OBSERVED 输入下的 INFERRED 估算；不主张精确当日资本结构，也不认证全部现金可分配。[S01][S04][S07]

| 项目 | 数值 | 解释 |
|---|---:|---|
| 市值 | 44054.2441 | 96.70 × 455.576464；最近披露实际股数 |
| 债务账面合计 | 15940.0000 | 1,636 + 14,304；其中已含融资租赁 2,161 |
| 全部现金扣减口径的净债务 | 11178.0000 | 债务 − 4,762；只是账面口径 |
| 发行人净债务 | 12047.0000 | 债务 − 短期投资 3,893；不是同一现金定义 |
| 现金与短期投资差额 | 869.0000 | 不能自动视为闲置现金；短投已在现金等价物中 |
| 简化 EV，未资本化经营租赁 | 55232.2441 | 市值 + 账面净债务；账面桥，不是完整债权市价模型 |
| 仅扣短投的 EV 对照 | 56101.2441 | 不声称短投全部可调度，只展示发行人口径影响 |
| 另资本化经营租赁的 EV 对照 | 59167.2441 | 增加 3,935；未同步调整利润分母，不用于横比排名 |

融资租赁已包含在债务内，不能重复加。优先股在资产负债表注释明确为零；未列少数股东不等于所有潜在权益请求权都已核清。该桥不包含债券公允价值、养老金和所有或有请求权的逐项市价调整。FY2024 的 461.8 是加权稀释股数，适用于 EPS，不适用于市值；4,091 / 461.8 = 8.8588 与披露 EPS 的舍入一致。

## 报告盈利与正常化

FY2024 GAAP 与发行人 adjusted diluted EPS 都是 8.86；发行人当期调整桥净额为零。这不能证明全部盈利永久可持续。五年 GAAP EPS 依次为 8.64、14.10、5.98、8.94、8.86，机械平均 9.3040，但包含高峰/低谷、股数变化及一个 53 周年度，不能直接标成 normalized EPS。[S01]

报告 EPS 下 PE 为 10.9142 倍。管理层三月给出的 FY2025 指引 8.80–9.80 对应 9.8673–10.9886 倍，属于“指引若实现”的 forward 条件，不是已实现 TTM。[S02]

FY2024 OCF 7,367 − capex 2,891 = FCF proxy 4476.0000。若只将 capex 改为当时 FY2025 指引的 4,000／4,500／5,000，保持 OCF 不变，则 proxy 为 3367.0000／2867.0000／2367.0000。这揭示低资本支出基线的敏感性；OCF 保持不变是 HYPOTHESIZED，不能当作未来现金流预测或股东可得现金。[S01]

## 同行与情景

Walmart FY2025 截至 2025-01-31，已披露 GAAP diluted EPS 2.41；其当日价格 97.25 对应 40.3527 倍。它和 Target 的窗口接近但并不同步，国际业务、会员制分部、食品结构、增长与资本需求不同。只作有限经营及倍数参照，不将 Walmart 的 PE 直接赋给 Target；也不偷用四月底结束但之后才披露的 Q1。原案例里的 Costco 年报窗口更早，本次未补齐当时最新中报，不纳入倍数样本。此处不是完整可比公司估值组。[S08][S09]

以下均为条件敏感性，**不是合理价值区间、目标价、安全边际或收益预测**。外部分析师 S03 在三月采用 9.15 EPS 和 15 倍估值；其当时市场 forward PE 为约 12.3 倍。这里只重建假设，不采纳评级或将一位分析师改称共识。[S03]

| 情景 | EPS × PE | 条件每股值 | 来源与经济限制 |
|---|---|---:|---|
| 悲观压力 | 5.98 × 12.3 | 73.5540 | 历史低谷 EPS 与较早市场倍数的研究组合；不代表损失下限 |
| 外部基准 | 9.15 × 15 | 137.2500 | 复算单一署名分析师模型；盈利兑现和倍数回归都未验证 |
| 乐观条件 | 9.80 × 15 | 147.0000 | 管理层指引高端 × 外部倍数；不是共同发布的预测 |

EPS × PE 已是权益每股值，不再扣净债务或加全部现金。完整九格 EPS/PE 敏感性及各情景相对参考价差值见 result.json；这些价差不等于预期收益。DCF 所需可靠现金流路径、资本成本和终值依据不足，本案例不另造折现率。

## 反方、可证伪条件与未决项

- 若未来首份季度披露显示同店销售转弱、库存压力及促销侵蚀利润，不能继续将三月全年指引作为可持续盈利；状态转 REVIEW_REQUIRED，重建销量/毛利与库存假设。
- 若实际资本支出恢复而经营现金流不能覆盖新增支出，重算现金转换，不能把 FY2024 proxy 外推为可分配现金。下一份季度现金流仅作进度验证，季节性下不能简单乘四。
- 若后续融资、回购或现金调度材料改变股数/净债务，重做日期桥；在取得之前维持滞后余额估算。
- 独立来源、业务驱动下的正常化盈利、可比倍数经济依据与截止日事件覆盖仍欠缺。下一验证窗口为截止日后首份正式季度业绩；本次没有用后来实际结果选择情景，也不宣称预测成功。

## 来源索引

[S01] https://corporate.target.com/getmedia/c23bca62-1790-47bd-ad0e-6971aee4f78d/2024-Annual-Report-Target-Corporation.pdf
[S02] https://corporate.target.com/press/release/2025/03/target-corporation-reports-fourth-quarter-and-full-year-2024-earnings
[S03] https://www.suredividend.com/wp-content/uploads/2025/03/TGT-2025-03-12.pdf
[S04] https://chartexchange.com/symbol/nyse-tgt/historical/
[S06] https://www.statmuse.com/money/ask/what-was-the-price-of-target-in-april-2025
[S07] https://query1.finance.yahoo.com/v8/finance/chart/TGT?period1=1745971200&period2=1746057600&interval=1d&events=div%2Csplits
[S08] https://stock.walmart.com/sec-filings/all-sec-filings/content/0000104169-25-000021/wmt-20250131.htm
[S09] https://query1.finance.yahoo.com/v8/finance/chart/WMT?period1=1745971200&period2=1746057600&interval=1d&events=div%2Csplits

各原件 SHA-256、补抓时间和本地路径见 evidence-manifest.json；手工提取的输入与定位见 input.json。重算命令：`python3 scripts/check_valuation_case.py --output-dir <新的目录>`。源码与脚本输出不替代人工语义审查。


## 计算回执

<!-- money-craft-calc: {"id": "C01", "operation": "multiply", "inputs": ["96.70", "455.576464"], "expected": "44054.24406880", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C02", "operation": "add", "inputs": ["1636", "14304"], "expected": "15940", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C03", "operation": "subtract", "inputs": ["15940", "4762"], "expected": "11178", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C04", "operation": "subtract", "inputs": ["15940", "3893"], "expected": "12047", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C05", "operation": "subtract", "inputs": ["4762", "3893"], "expected": "869", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C06", "operation": "add", "inputs": ["44054.24406880", "11178"], "expected": "55232.24406880", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C07", "operation": "add", "inputs": ["44054.24406880", "12047"], "expected": "56101.24406880", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C08", "operation": "add", "inputs": ["55232.24406880", "3935"], "expected": "59167.24406880", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C09", "operation": "divide", "inputs": ["96.70", "8.86"], "expected": "10.91422121896162528216704288939052", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C10", "operation": "divide", "inputs": ["96.70", "9.80"], "expected": "9.867346938775510204081632653061224", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C11", "operation": "divide", "inputs": ["96.70", "8.80"], "expected": "10.98863636363636363636363636363636", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C12", "operation": "divide", "inputs": ["97.25", "2.41"], "expected": "40.35269709543568464730290456431535", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C13", "operation": "subtract", "inputs": ["7367", "2891"], "expected": "4476", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C14", "operation": "add", "inputs": ["4000", "5000"], "expected": "9000", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C15", "operation": "divide", "inputs": ["9000", "2"], "expected": "4500", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C16", "operation": "subtract", "inputs": ["7367", "4000"], "expected": "3367", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C17", "operation": "subtract", "inputs": ["7367", "4500"], "expected": "2867", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C18", "operation": "subtract", "inputs": ["7367", "5000"], "expected": "2367", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C19", "operation": "add", "inputs": ["8.86", "8.94", "5.98", "14.10", "8.64"], "expected": "46.52", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C20", "operation": "divide", "inputs": ["46.52", "5"], "expected": "9.304", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C21", "operation": "divide", "inputs": ["4091", "461.8"], "expected": "8.858813339107838891294932871372889", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C22", "operation": "multiply", "inputs": ["5.98", "12.3"], "expected": "73.554", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C23", "operation": "subtract", "inputs": ["73.554", "96.70"], "expected": "-23.146", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C24", "operation": "divide", "inputs": ["-23.146", "96.70"], "expected": "-0.2393588417786970010341261633919338", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C25", "operation": "multiply", "inputs": ["9.15", "15"], "expected": "137.25", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C26", "operation": "subtract", "inputs": ["137.25", "96.70"], "expected": "40.55", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C27", "operation": "divide", "inputs": ["40.55", "96.70"], "expected": "0.4193381592554291623578076525336091", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C28", "operation": "multiply", "inputs": ["9.80", "15"], "expected": "147.00", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C29", "operation": "subtract", "inputs": ["147.00", "96.70"], "expected": "50.30", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C30", "operation": "divide", "inputs": ["50.30", "96.70"], "expected": "0.5201654601861427094105480868665977", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C31", "operation": "multiply", "inputs": ["5.98", "10.91422121896162528216704288939052"], "expected": "65.26704288939051918735891647855531", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C32", "operation": "multiply", "inputs": ["5.98", "12.3"], "expected": "73.554", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C33", "operation": "multiply", "inputs": ["5.98", "15"], "expected": "89.70", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C34", "operation": "multiply", "inputs": ["8.86", "10.91422121896162528216704288939052"], "expected": "96.70000000000000000000000000000001", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C35", "operation": "multiply", "inputs": ["8.86", "12.3"], "expected": "108.978", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C36", "operation": "multiply", "inputs": ["8.86", "15"], "expected": "132.90", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C37", "operation": "multiply", "inputs": ["9.80", "10.91422121896162528216704288939052"], "expected": "106.9593679458239277652370203160271", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C38", "operation": "multiply", "inputs": ["9.80", "12.3"], "expected": "120.540", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C39", "operation": "multiply", "inputs": ["9.80", "15"], "expected": "147.00", "tolerance": "0.000001"} -->
