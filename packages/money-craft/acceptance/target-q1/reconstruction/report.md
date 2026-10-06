# Target Q1：盈利修复条件的后续复核

执行日2026-09-20；新研究截止2025-05-21；旧截止2025-04-30。对象US-NYSE:TGT普通股，USD。新材料为截至2025-05-03的13周业绩，对比截至2024-05-04的13周；金额为百万美元，每股值为美元。

**研究判断：原盈利修复基准受到削弱，需要重建；GAAP盈利上升不能单独支持旧估值逻辑。** 这是事后回放，不是盲测或预测成绩。旧报告及假设文件只读保留，新数据不回填旧截止日。

## 报告与调整口径

| 指标 | Q1 2025 | Q1 2024／对照 | 解释 |
|---|---:|---:|---|
| 收入 | 23,846 | 24,531 | 重算同比 -2.7924% |
| GAAP营业利润 | 1,472 | 1,296 | 重算同比 13.5802% |
| 剔除和解收益的营业利润 | 879.0000 | 1,296 | 重算同比 -32.1759% |
| 调整后营业利润率 | 3.6862% | 5.2831% | 变化 -1.5970 个百分点 |
| GAAP净利润 | 1,036 | 942 | 重算同比 9.9788% |
| 剔除和解收益的净利润 | 595.0000 | 942 | 重算同比 -36.8365% |

和解收益披露为税前593、税后441；税效为 152.0000，采用正式调整桥，不套全公司有效税率自行估算。稀释EPS按披露的舍入数桥接：2.27 − 0.97 = 1.3000，上年为2.03。表内百分比是按已披露整数金额重算，精度不高于输入。剔除此项不等于所有经济调整已完成，也不自动等于长期正常化盈利。[S12 pp1–3、5、10]

## 更新年度基线

三月同口径的调整后指引8.80–9.80，五月变为约7.00–9.00；端点变化为 -1.8000／-0.8000，算术中点由 9.3000 变为 8.0000，变化 -1.3000。中点不是公司承诺或市场共识。[S02][S12]

五月GAAP指引约8.00–10.00，含本季和解收益，不能将其上限高于旧上限解释为经营升级。公司给的是近似区间，不能把近似区间端点精确相减后，指责其与调整后指引存在矛盾。

| 旧研究项 | 后续状态 | 对使用的限制 |
|---|---|---|
| 三月管理层调整后8.80–9.80仍代表最新指引 | SUPERSEDED | 新截止日使用五月同口径披露，旧记录保留 |
| 外部分析师9.15作为基准 | CHALLENGED_REMODEL | 高于新的调整后指引上端；需要重新论证，不等于数学上不可能 |
| 9.80乐观情景代表当前管理层调整后上端 | SUPERSEDED | 不能用新的GAAP上端替它背书；仅可保留为明确的额外乐观假设 |
| 2022低谷EPS压力组合 | STRESS_ONLY | 本季数据不证明它是损失下限 |

销售指引从约增1%转为低个位数下降，利润率和同店表现使修复命题减弱；三月已经预告首季压力，因此不能把所有下降都称意外。[S02][S12]

## 现金与下一窗口

本季OCF275、资本开支790，FCF proxy为 -515.0000；上年对应proxy为 427.0000。现金桥为275 − 787 − 1,363 = -1875.0000；4,762 + -1875.0000 = 2887.0000，与期末余额勾稽。单季受营运资金和季节性影响，不能乘四作为全年现金预测，也不能把proxy直接称可分配现金。[S12 pp6–7]

资本配置说明中的回购金额251与现金流表的回购现金250分别保留：现金桥使用现金流表值，未确认差异原因，不强改成相同值。诉讼税后收益不等于其本期净现金流，不能机械再从OCF扣441。[S12 pp3、7、10]

库存同比 11.2361%，收入同比 -2.7924%；目前只验证了旧规则要求的两个连续季度中的一个，库存压力标记 WATCH，不能提前触发“两期均恶化”。数字业务增长也不能单独证明经营杠杆改善。下一份正式季度披露要核对调整后利润率、同口径库存/销售、全年指引和现金转换，再决定是否继续削弱或恢复原命题。

没有新截止日行情，本次不生成新的PE、目标价或上涨空间，也不沿用四月价格冒充五月市值。贸易政策、消费及其他因素的贡献尚未量化，不把同期发生当成单一因果证明。

## 证据边界与复现

S02与S12均为发行人材料，网页/PDF不是独立双源；本次只核验所选业绩公告，未冒充完整10-Q审读。全部原件为事后抓取，原始预测构造也发生在2026年，故不形成事前预期命中率。语义由主代理复核。

`python3 acceptance/target-q1/reproduce.py --output-dir <新目录>`：核验上一复核记录绑定的旧文件、来源SHA-256、新旧截止顺序和来源披露日，再复算并审计最终文本。工具不自动认证来源真实性或经济判断，不自动写正式tracking revision。

## 来源索引

[S01] https://corporate.target.com/getmedia/c23bca62-1790-47bd-ad0e-6971aee4f78d/2024-Annual-Report-Target-Corporation.pdf
[S02] https://corporate.target.com/press/release/2025/03/target-corporation-reports-fourth-quarter-and-full-year-2024-earnings
[S12] https://corporate.target.com/getmedia/06df3254-1476-4b4d-a968-d4ad5a19939e/Target-Corporation-Reports-First-Quarter-Earnings.pdf


## 计算回执

<!-- money-craft-calc: {"id": "C01", "operation": "subtract", "inputs": ["1472", "593"], "expected": "879", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C02", "operation": "subtract", "inputs": ["1036", "441"], "expected": "595", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C03", "operation": "subtract", "inputs": ["593", "441"], "expected": "152", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C04", "operation": "subtract", "inputs": ["2.27", "0.97"], "expected": "1.30", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C05", "operation": "subtract", "inputs": ["23846", "24531"], "expected": "-685", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C06", "operation": "divide", "inputs": ["-685", "24531"], "expected": "-0.02792385145326321796910032204149851", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C07", "operation": "multiply", "inputs": ["-0.02792385145326321796910032204149851", "100"], "expected": "-2.792385145326321796910032204149851", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C08", "operation": "subtract", "inputs": ["1472", "1296"], "expected": "176", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C09", "operation": "divide", "inputs": ["176", "1296"], "expected": "0.1358024691358024691358024691358025", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C10", "operation": "multiply", "inputs": ["0.1358024691358024691358024691358025", "100"], "expected": "13.58024691358024691358024691358025", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C11", "operation": "subtract", "inputs": ["879", "1296"], "expected": "-417", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C12", "operation": "divide", "inputs": ["-417", "1296"], "expected": "-0.3217592592592592592592592592592593", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C13", "operation": "multiply", "inputs": ["-0.3217592592592592592592592592592593", "100"], "expected": "-32.17592592592592592592592592592593", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C14", "operation": "subtract", "inputs": ["1036", "942"], "expected": "94", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C15", "operation": "divide", "inputs": ["94", "942"], "expected": "0.09978768577494692144373673036093418", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C16", "operation": "multiply", "inputs": ["0.09978768577494692144373673036093418", "100"], "expected": "9.978768577494692144373673036093418", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C17", "operation": "subtract", "inputs": ["595", "942"], "expected": "-347", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C18", "operation": "divide", "inputs": ["-347", "942"], "expected": "-0.3683651804670912951167728237791932", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C19", "operation": "multiply", "inputs": ["-0.3683651804670912951167728237791932", "100"], "expected": "-36.83651804670912951167728237791932", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C20", "operation": "subtract", "inputs": ["13048", "11730"], "expected": "1318", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C21", "operation": "divide", "inputs": ["1318", "11730"], "expected": "0.1123614663256606990622335890878090", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C22", "operation": "multiply", "inputs": ["0.1123614663256606990622335890878090", "100"], "expected": "11.23614663256606990622335890878090", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C23", "operation": "subtract", "inputs": ["275", "1101"], "expected": "-826", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C24", "operation": "divide", "inputs": ["-826", "1101"], "expected": "-0.7502270663033605812897366030881017", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C25", "operation": "multiply", "inputs": ["-0.7502270663033605812897366030881017", "100"], "expected": "-75.02270663033605812897366030881017", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C26", "operation": "divide", "inputs": ["1472", "23846"], "expected": "0.06172943051245491906399396125136291", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C27", "operation": "multiply", "inputs": ["0.06172943051245491906399396125136291", "100"], "expected": "6.172943051245491906399396125136291", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C28", "operation": "divide", "inputs": ["879", "23846"], "expected": "0.03686152813889121865302356789398641", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C29", "operation": "multiply", "inputs": ["0.03686152813889121865302356789398641", "100"], "expected": "3.686152813889121865302356789398641", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C30", "operation": "divide", "inputs": ["1296", "24531"], "expected": "0.05283111165464106640577228812522930", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C31", "operation": "multiply", "inputs": ["0.05283111165464106640577228812522930", "100"], "expected": "5.283111165464106640577228812522930", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C32", "operation": "subtract", "inputs": ["0.03686152813889121865302356789398641", "0.05283111165464106640577228812522930"], "expected": "-0.01596958351574984775274872023124289", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C33", "operation": "multiply", "inputs": ["-0.01596958351574984775274872023124289", "100"], "expected": "-1.596958351574984775274872023124289", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C34", "operation": "subtract", "inputs": ["275", "790"], "expected": "-515", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C35", "operation": "subtract", "inputs": ["1101", "674"], "expected": "427", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C36", "operation": "add", "inputs": ["275", "-787", "-1363"], "expected": "-1875", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C37", "operation": "add", "inputs": ["4762", "-1875"], "expected": "2887", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C38", "operation": "add", "inputs": ["8.80", "9.80"], "expected": "18.60", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C39", "operation": "divide", "inputs": ["18.60", "2"], "expected": "9.30", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C40", "operation": "add", "inputs": ["7.00", "9.00"], "expected": "16.00", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C41", "operation": "divide", "inputs": ["16.00", "2"], "expected": "8.00", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C42", "operation": "add", "inputs": ["8.00", "10.00"], "expected": "18.00", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C43", "operation": "divide", "inputs": ["18.00", "2"], "expected": "9.00", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C44", "operation": "subtract", "inputs": ["8.00", "9.30"], "expected": "-1.30", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C45", "operation": "subtract", "inputs": ["7.00", "8.80"], "expected": "-1.80", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C46", "operation": "subtract", "inputs": ["9.00", "9.80"], "expected": "-0.80", "tolerance": "0.000001"} -->
