# Target：经营驱动与历史截止事件增量

执行日：2026-09-20；历史截止：2025-04-30；US-NYSE:TGT 普通股，USD。金额为百万美元，每股金额为美元。接续上一轮估值重建，旧报告与旧验收保留；本报告只改变研究判断，不把历史回放描述为当时实际预测。

**判断更新：三月管理层指引和署名分析师 EPS 可继续作为条件输入，但应标记 NEEDS_REUNDERWRITING，不能作为四月底已确认的可持续盈利。** 本次补充了成本改善是否已计入、现金缓冲与回购约束、后续政策冲击，以及 EPS 所需营业利润率。合理倍数仍未证实；本轮不扩大目标价区间，也不运行新的应用或交易功能。

## 事件与证据准入

| 事件时间 | 证据 | 对模型的影响 |
|---|---|---|
| 2025-03-04 | S02 业绩及全年指引 | 收入约增1%、税率23%–24%和EPS8.80–9.80是管理层预期；“约1%”不等于精确增长点 |
| 2025-03-04会议 | S10 逐字稿，文件页脚生成标记为3月6日 | 已实现的损耗改善与节约不可再次加回；资产负债表缓冲约束回购。网页原始上传时刻未保存 |
| 2025-04-09发布，4月10日起相关条款生效 | S11 官方行政令 | 三月预测之后的政策变化触发重估采购成本、定价与需求；不等于发行人正式撤回指引 |

S11 规定不同来源地适用的调整、暂停和例外，不能将某项名义税率乘 Target 全部成本，更不能声称本次已完整核验全部税目。原产地、进口完税价格、在途例外、其他税率层、供应商分担、转产、提价与需求弹性没有齐备。S01 明确中国是其进口商品最大的单一来源地，但未给足上述成本暴露明细；因此方向风险可记录，利润冲击不能伪精确量化。[S01][S11]

截至本次检索，事件表为**有界覆盖**，不声称检索穷尽或期间没有其他重大变化。May 2025及以后财报、后续政策变化、当前行情字段排除；搜索中出现的期后结果未作为模型参数。客流新闻只作为待核线索，未取得可复核的原始样本/方法和消费转化关系，不用其跌幅代替公司收入跌幅。

## 哪些改善已经在基线里

管理层称 FY2024 损耗改善已贡献约40bp营业利润率，前两年的节约目标已实现超过20亿美元；这些已经发生的改善不能再叠加到 FY2024 基线上。后续损耗、广告与平台业务、效率改善有方向性说明，缺乏能独立相加的新增金额。[S10 pp20–21]

管理层还计划保留高于通常水平的现金缓冲；回购时点和金额取决于经营及环境。故不自动用回购授权减少预测股数。全年“小幅提高利润率”不能擅自替换为分析师提问中的6%目标；答问没有提供相应年度承诺。[S10 pp21、24–25]

## 从 EPS 反推经营要求

历史勾稽为：营业利润5,566 − 净利息411 + 其他收益106 = 税前5,261；减所得税1,170 = 净利润4,091。[S01 Form10-K p42]

条件反推采用：

`所需营业利润 = EPS × 预测加权稀释股数 ÷ (1 − 税率) − 其他净税前损益`

`所需营业利润率 = 所需营业利润 ÷ 预测收入`

将收入约增1%取为一个分析点，收入为 107631.6600。预测加权稀释股数暂固定为 FY2024 的461.8百万股，净利息与其他收益净额暂固定为−305；这两项是研究者保持不变的假设，不是管理层指引。它们也不能替代上一报告计算市值时的实际在外股数。[S01][S02]

税率使用指引端点23%／24%和分析中点23.5%；EPS使用指引端点8.80／9.80及 S03 外部分析师9.15。九种组合只是条件门槛，不是九个预测或概率情景。[S02][S03]

| EPS 条件 | 税率 | 所需营业利润率 | 较 FY2024 变化（bp） |
|---:|---:|---:|---:|
| 8.80 | 23.0% | 5.1869% | -3.62 |
| 8.80 | 23.5% | 5.2189% | -0.41 |
| 8.80 | 24.0% | 5.2514% | 2.83 |
| 9.15 | 23.0% | 5.3819% | 15.88 |
| 9.15 | 23.5% | 5.4152% | 19.22 |
| 9.15 | 24.0% | 5.4490% | 22.59 |
| 9.80 | 23.0% | 5.7441% | 52.10 |
| 9.80 | 23.5% | 5.7798% | 55.67 |
| 9.80 | 24.0% | 5.8159% | 59.29 |

如果营业利润率维持 FY2024 不变，采用上述收入、税率中点、股数和非经营项目条件，EPS 为 8.8074。该结果用于检查“收入约增1%是否足以支持EPS修复”，不能称为新的实际预测。

在相同条件下，营业利润率每变化100bp，对应营业利润变化 1076.3166、EPS变化 1.7830。这是单位敏感性；没有证据说关税恰好造成100bp变化，不能把该敏感性反向包装成政策冲击预测。

每个反推门槛均重新代入正向利润公式，检查恢复原EPS。计算回执证明代数一致，不能证明该利润率能够实现。增长、费用、税率、股数等多个变量可能同时变化，单变量保持不变的结果不能作为因果归因。

## 对上一轮三情景的处置

| 原情景 | 新状态 | 原因 |
|---|---|---|
| 2022低谷EPS × 较早市场倍数 | RETAIN_AS_STRESS_ONLY | 历史组合可复算，但不是当下需求、成本及估值条件的配套观测，也不是损失下限 |
| 署名分析师9.15 × 15 | NEEDS_REUNDERWRITING | 现在可列出利润率门槛；四月政策及经营承接证据未验证，15倍仍是外部观点 |
| 管理层9.80 × 15 | NEEDS_REUNDERWRITING | 上端EPS要求更强经营改善；不得重复计入已实现节约或依赖未承诺回购 |

不改写旧报告中的数值和历史验收结果。旧工程 PASS 仍仅证明当时声明范围；本次新增证据不会自动将“可复算”提升为“合理价值成立”。

## 下一步可验证条件

1. 下一份正式季度业绩：检查全年指引是否维持；第一季利润压力已被三月提示，单季下降本身不等于额外负面惊喜。
2. 同口径收入／同店、毛利与库存：核实改善是否覆盖折价、履约、税率和新增投入，防止将数字渠道增长直接当利润增长。
3. 采购与政策影响：取得品类、原产地、成本分担、提价和需求反应证据后才填成本冲击数值。没有资料时保留未知。
4. 资本配置：新现金流、稀释股数和实际回购披露决定是否改变股数及现金桥；不以回购授权替代执行。

本轮完成了经营门槛的可复算表达和关键假设的重新分级；独立证实的可持续盈利、完整截止事件集及合理倍数仍未完成。S01/S02/S10是同一发行人相关材料，S03财务转录不构成独立审计；S11独立证明政策事件，不独立证明公司的利润影响。

## 来源索引

[S01] https://corporate.target.com/getmedia/c23bca62-1790-47bd-ad0e-6971aee4f78d/2024-Annual-Report-Target-Corporation.pdf
[S02] https://corporate.target.com/press/release/2025/03/target-corporation-reports-fourth-quarter-and-full-year-2024-earnings
[S03] https://www.suredividend.com/wp-content/uploads/2025/03/TGT-2025-03-12.pdf
[S10] https://corporate.target.com/getmedia/d29ff305-a470-477a-bf4b-585069cf8fc0/TGT-Transcript-2025-03-04.pdf
[S11] https://www.whitehouse.gov/presidential-actions/2025/04/modifying-reciprocal-tariff-rates-to-reflect-trading-partner-retaliation-and-alignment/

原件只保存在私有目录；元数据、SHA-256、输入和事件表位于同案例目录。来源事后抓取不能证明历史时点曾保存；输入为人工提取。复现：`python3 scripts/check_target_driver_case.py --output-dir <新目录>`。


## 计算回执

<!-- money-craft-calc: {"id": "C01", "operation": "subtract", "inputs": ["106", "411"], "expected": "-305", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C02", "operation": "add", "inputs": ["5566", "-305"], "expected": "5261", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C03", "operation": "subtract", "inputs": ["5261", "1170"], "expected": "4091", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C04", "operation": "divide", "inputs": ["5566", "106566"], "expected": "0.05223054257455473603213032299232401", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C05", "operation": "multiply", "inputs": ["0.05223054257455473603213032299232401", "100"], "expected": "5.223054257455473603213032299232401", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C06", "operation": "add", "inputs": ["1", "0.01"], "expected": "1.01", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C07", "operation": "multiply", "inputs": ["106566", "1.01"], "expected": "107631.66", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C08", "operation": "subtract", "inputs": ["1", "0.23"], "expected": "0.77", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C09", "operation": "multiply", "inputs": ["8.80", "461.8"], "expected": "4063.840", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C10", "operation": "divide", "inputs": ["4063.840", "0.77"], "expected": "5277.714285714285714285714285714286", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C11", "operation": "subtract", "inputs": ["5277.714285714285714285714285714286", "-305"], "expected": "5582.714285714285714285714285714286", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C12", "operation": "divide", "inputs": ["5582.714285714285714285714285714286", "107631.66"], "expected": "0.05186870002482806373408822539496544", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C13", "operation": "multiply", "inputs": ["0.05186870002482806373408822539496544", "100"], "expected": "5.186870002482806373408822539496544", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C14", "operation": "subtract", "inputs": ["0.05186870002482806373408822539496544", "0.05223054257455473603213032299232401"], "expected": "-0.00036184254972667229804209759735857", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C15", "operation": "multiply", "inputs": ["-0.00036184254972667229804209759735857", "10000"], "expected": "-3.618425497266722980420975973585700", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C16", "operation": "multiply", "inputs": ["107631.66", "0.05186870002482806373408822539496544"], "expected": "5582.714285714285714285714285714286", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C17", "operation": "add", "inputs": ["5582.714285714285714285714285714286", "-305"], "expected": "5277.714285714285714285714285714286", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C18", "operation": "multiply", "inputs": ["5277.714285714285714285714285714286", "0.77"], "expected": "4063.840000000000000000000000000000", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C19", "operation": "divide", "inputs": ["4063.840000000000000000000000000000", "461.8"], "expected": "8.80000000000000000000000000000", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C20", "operation": "subtract", "inputs": ["1", "0.235"], "expected": "0.765", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C21", "operation": "multiply", "inputs": ["8.80", "461.8"], "expected": "4063.840", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C22", "operation": "divide", "inputs": ["4063.840", "0.765"], "expected": "5312.209150326797385620915032679739", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C23", "operation": "subtract", "inputs": ["5312.209150326797385620915032679739", "-305"], "expected": "5617.209150326797385620915032679739", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C24", "operation": "divide", "inputs": ["5617.209150326797385620915032679739", "107631.66"], "expected": "0.05218918996814503637332096367072420", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C25", "operation": "multiply", "inputs": ["0.05218918996814503637332096367072420", "100"], "expected": "5.218918996814503637332096367072420", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C26", "operation": "subtract", "inputs": ["0.05218918996814503637332096367072420", "0.05223054257455473603213032299232401"], "expected": "-0.00004135260640969965880935932159981", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C27", "operation": "multiply", "inputs": ["-0.00004135260640969965880935932159981", "10000"], "expected": "-0.4135260640969965880935932159981000", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C28", "operation": "multiply", "inputs": ["107631.66", "0.05218918996814503637332096367072420"], "expected": "5617.209150326797385620915032679739", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C29", "operation": "add", "inputs": ["5617.209150326797385620915032679739", "-305"], "expected": "5312.209150326797385620915032679739", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C30", "operation": "multiply", "inputs": ["5312.209150326797385620915032679739", "0.765"], "expected": "4063.840000000000000000000000000000", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C31", "operation": "divide", "inputs": ["4063.840000000000000000000000000000", "461.8"], "expected": "8.80000000000000000000000000000", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C32", "operation": "subtract", "inputs": ["1", "0.24"], "expected": "0.76", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C33", "operation": "multiply", "inputs": ["8.80", "461.8"], "expected": "4063.840", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C34", "operation": "divide", "inputs": ["4063.840", "0.76"], "expected": "5347.157894736842105263157894736842", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C35", "operation": "subtract", "inputs": ["5347.157894736842105263157894736842", "-305"], "expected": "5652.157894736842105263157894736842", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C36", "operation": "divide", "inputs": ["5652.157894736842105263157894736842", "107631.66"], "expected": "0.05251389688440039023149097481853241", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C37", "operation": "multiply", "inputs": ["0.05251389688440039023149097481853241", "100"], "expected": "5.251389688440039023149097481853241", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C38", "operation": "subtract", "inputs": ["0.05251389688440039023149097481853241", "0.05223054257455473603213032299232401"], "expected": "0.00028335430984565419936065182620840", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C39", "operation": "multiply", "inputs": ["0.00028335430984565419936065182620840", "10000"], "expected": "2.833543098456541993606518262084000", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C40", "operation": "multiply", "inputs": ["107631.66", "0.05251389688440039023149097481853241"], "expected": "5652.157894736842105263157894736842", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C41", "operation": "add", "inputs": ["5652.157894736842105263157894736842", "-305"], "expected": "5347.157894736842105263157894736842", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C42", "operation": "multiply", "inputs": ["5347.157894736842105263157894736842", "0.76"], "expected": "4063.840000000000000000000000000000", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C43", "operation": "divide", "inputs": ["4063.840000000000000000000000000000", "461.8"], "expected": "8.80000000000000000000000000000", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C44", "operation": "subtract", "inputs": ["1", "0.23"], "expected": "0.77", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C45", "operation": "multiply", "inputs": ["9.15", "461.8"], "expected": "4225.470", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C46", "operation": "divide", "inputs": ["4225.470", "0.77"], "expected": "5487.623376623376623376623376623377", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C47", "operation": "subtract", "inputs": ["5487.623376623376623376623376623377", "-305"], "expected": "5792.623376623376623376623376623377", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C48", "operation": "divide", "inputs": ["5792.623376623376623376623376623377", "107631.66"], "expected": "0.05381895416853532337396471797074743", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C49", "operation": "multiply", "inputs": ["0.05381895416853532337396471797074743", "100"], "expected": "5.381895416853532337396471797074743", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C50", "operation": "subtract", "inputs": ["0.05381895416853532337396471797074743", "0.05223054257455473603213032299232401"], "expected": "0.00158841159398058734183439497842342", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C51", "operation": "multiply", "inputs": ["0.00158841159398058734183439497842342", "10000"], "expected": "15.88411593980587341834394978423420", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C52", "operation": "multiply", "inputs": ["107631.66", "0.05381895416853532337396471797074743"], "expected": "5792.623376623376623376623376623377", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C53", "operation": "add", "inputs": ["5792.623376623376623376623376623377", "-305"], "expected": "5487.623376623376623376623376623377", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C54", "operation": "multiply", "inputs": ["5487.623376623376623376623376623377", "0.77"], "expected": "4225.470000000000000000000000000000", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C55", "operation": "divide", "inputs": ["4225.470000000000000000000000000000", "461.8"], "expected": "9.15000000000000000000000000000", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C56", "operation": "subtract", "inputs": ["1", "0.235"], "expected": "0.765", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C57", "operation": "multiply", "inputs": ["9.15", "461.8"], "expected": "4225.470", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C58", "operation": "divide", "inputs": ["4225.470", "0.765"], "expected": "5523.490196078431372549019607843137", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C59", "operation": "subtract", "inputs": ["5523.490196078431372549019607843137", "-305"], "expected": "5828.490196078431372549019607843137", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C60", "operation": "divide", "inputs": ["5828.490196078431372549019607843137", "107631.66"], "expected": "0.05415219087096149378862148560974658", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C61", "operation": "multiply", "inputs": ["0.05415219087096149378862148560974658", "100"], "expected": "5.415219087096149378862148560974658", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C62", "operation": "subtract", "inputs": ["0.05415219087096149378862148560974658", "0.05223054257455473603213032299232401"], "expected": "0.00192164829640675775649116261742257", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C63", "operation": "multiply", "inputs": ["0.00192164829640675775649116261742257", "10000"], "expected": "19.21648296406757756491162617422570", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C64", "operation": "multiply", "inputs": ["107631.66", "0.05415219087096149378862148560974658"], "expected": "5828.490196078431372549019607843137", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C65", "operation": "add", "inputs": ["5828.490196078431372549019607843137", "-305"], "expected": "5523.490196078431372549019607843137", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C66", "operation": "multiply", "inputs": ["5523.490196078431372549019607843137", "0.765"], "expected": "4225.470000000000000000000000000000", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C67", "operation": "divide", "inputs": ["4225.470000000000000000000000000000", "461.8"], "expected": "9.15000000000000000000000000000", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C68", "operation": "subtract", "inputs": ["1", "0.24"], "expected": "0.76", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C69", "operation": "multiply", "inputs": ["9.15", "461.8"], "expected": "4225.470", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C70", "operation": "divide", "inputs": ["4225.470", "0.76"], "expected": "5559.828947368421052631578947368421", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C71", "operation": "subtract", "inputs": ["5559.828947368421052631578947368421", "-305"], "expected": "5864.828947368421052631578947368421", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C72", "operation": "divide", "inputs": ["5864.828947368421052631578947368421", "107631.66"], "expected": "0.05448981226684064012978689492820626", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C73", "operation": "multiply", "inputs": ["0.05448981226684064012978689492820626", "100"], "expected": "5.448981226684064012978689492820626", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C74", "operation": "subtract", "inputs": ["0.05448981226684064012978689492820626", "0.05223054257455473603213032299232401"], "expected": "0.00225926969228590409765657193588225", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C75", "operation": "multiply", "inputs": ["0.00225926969228590409765657193588225", "10000"], "expected": "22.59269692285904097656571935882250", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C76", "operation": "multiply", "inputs": ["107631.66", "0.05448981226684064012978689492820626"], "expected": "5864.828947368421052631578947368421", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C77", "operation": "add", "inputs": ["5864.828947368421052631578947368421", "-305"], "expected": "5559.828947368421052631578947368421", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C78", "operation": "multiply", "inputs": ["5559.828947368421052631578947368421", "0.76"], "expected": "4225.470000000000000000000000000000", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C79", "operation": "divide", "inputs": ["4225.470000000000000000000000000000", "461.8"], "expected": "9.15000000000000000000000000000", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C80", "operation": "subtract", "inputs": ["1", "0.23"], "expected": "0.77", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C81", "operation": "multiply", "inputs": ["9.80", "461.8"], "expected": "4525.640", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C82", "operation": "divide", "inputs": ["4525.640", "0.77"], "expected": "5877.454545454545454545454545454545", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C83", "operation": "subtract", "inputs": ["5877.454545454545454545454545454545", "-305"], "expected": "6182.454545454545454545454545454545", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C84", "operation": "divide", "inputs": ["6182.454545454545454545454545454545", "107631.66"], "expected": "0.05744085472113451984802106132577111", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C85", "operation": "multiply", "inputs": ["0.05744085472113451984802106132577111", "100"], "expected": "5.744085472113451984802106132577111", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C86", "operation": "subtract", "inputs": ["0.05744085472113451984802106132577111", "0.05223054257455473603213032299232401"], "expected": "0.00521031214657978381589073833344710", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C87", "operation": "multiply", "inputs": ["0.00521031214657978381589073833344710", "10000"], "expected": "52.10312146579783815890738333447100", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C88", "operation": "multiply", "inputs": ["107631.66", "0.05744085472113451984802106132577111"], "expected": "6182.454545454545454545454545454545", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C89", "operation": "add", "inputs": ["6182.454545454545454545454545454545", "-305"], "expected": "5877.454545454545454545454545454545", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C90", "operation": "multiply", "inputs": ["5877.454545454545454545454545454545", "0.77"], "expected": "4525.640000000000000000000000000000", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C91", "operation": "divide", "inputs": ["4525.640000000000000000000000000000", "461.8"], "expected": "9.80000000000000000000000000000", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C92", "operation": "subtract", "inputs": ["1", "0.235"], "expected": "0.765", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C93", "operation": "multiply", "inputs": ["9.80", "461.8"], "expected": "4525.640", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C94", "operation": "divide", "inputs": ["4525.640", "0.765"], "expected": "5915.869281045751633986928104575163", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C95", "operation": "subtract", "inputs": ["5915.869281045751633986928104575163", "-305"], "expected": "6220.869281045751633986928104575163", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C96", "operation": "divide", "inputs": ["6220.869281045751633986928104575163", "107631.66"], "expected": "0.05779776397619205755989388349650245", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C97", "operation": "multiply", "inputs": ["0.05779776397619205755989388349650245", "100"], "expected": "5.779776397619205755989388349650245", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C98", "operation": "subtract", "inputs": ["0.05779776397619205755989388349650245", "0.05223054257455473603213032299232401"], "expected": "0.00556722140163732152776356050417844", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C99", "operation": "multiply", "inputs": ["0.00556722140163732152776356050417844", "10000"], "expected": "55.67221401637321527763560504178440", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C100", "operation": "multiply", "inputs": ["107631.66", "0.05779776397619205755989388349650245"], "expected": "6220.869281045751633986928104575163", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C101", "operation": "add", "inputs": ["6220.869281045751633986928104575163", "-305"], "expected": "5915.869281045751633986928104575163", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C102", "operation": "multiply", "inputs": ["5915.869281045751633986928104575163", "0.765"], "expected": "4525.640000000000000000000000000000", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C103", "operation": "divide", "inputs": ["4525.640000000000000000000000000000", "461.8"], "expected": "9.80000000000000000000000000000", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C104", "operation": "subtract", "inputs": ["1", "0.24"], "expected": "0.76", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C105", "operation": "multiply", "inputs": ["9.80", "461.8"], "expected": "4525.640", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C106", "operation": "divide", "inputs": ["4525.640", "0.76"], "expected": "5954.789473684210526315789473684211", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C107", "operation": "subtract", "inputs": ["5954.789473684210526315789473684211", "-305"], "expected": "6259.789473684210526315789473684211", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C108", "operation": "divide", "inputs": ["6259.789473684210526315789473684211", "107631.66"], "expected": "0.05815936940565824708376503227474343", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C109", "operation": "multiply", "inputs": ["0.05815936940565824708376503227474343", "100"], "expected": "5.815936940565824708376503227474343", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C110", "operation": "subtract", "inputs": ["0.05815936940565824708376503227474343", "0.05223054257455473603213032299232401"], "expected": "0.00592882683110351105163470928241942", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C111", "operation": "multiply", "inputs": ["0.00592882683110351105163470928241942", "10000"], "expected": "59.28826831103511051634709282419420", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C112", "operation": "multiply", "inputs": ["107631.66", "0.05815936940565824708376503227474343"], "expected": "6259.789473684210526315789473684211", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C113", "operation": "add", "inputs": ["6259.789473684210526315789473684211", "-305"], "expected": "5954.789473684210526315789473684211", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C114", "operation": "multiply", "inputs": ["5954.789473684210526315789473684211", "0.76"], "expected": "4525.640000000000000000000000000000", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C115", "operation": "divide", "inputs": ["4525.640000000000000000000000000000", "461.8"], "expected": "9.80000000000000000000000000000", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C116", "operation": "subtract", "inputs": ["1", "0.235"], "expected": "0.765", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C117", "operation": "multiply", "inputs": ["107631.66", "0.01"], "expected": "1076.3166", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C118", "operation": "multiply", "inputs": ["1076.3166", "0.765"], "expected": "823.3821990", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C119", "operation": "divide", "inputs": ["823.3821990", "461.8"], "expected": "1.782984406669553919445647466435686", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C120", "operation": "divide", "inputs": ["1170", "5261"], "expected": "0.2223911803839574225432427295191028", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C121", "operation": "multiply", "inputs": ["107631.66", "0.05223054257455473603213032299232401"], "expected": "5621.660000000000000000000000000000", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C122", "operation": "add", "inputs": ["5621.660000000000000000000000000000", "-305"], "expected": "5316.660000000000000000000000000000", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C123", "operation": "multiply", "inputs": ["5316.660000000000000000000000000000", "0.765"], "expected": "4067.244900000000000000000000000000", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C124", "operation": "divide", "inputs": ["4067.244900000000000000000000000000", "461.8"], "expected": "8.807373105240363793850151580770896", "tolerance": "0.000001"} -->
