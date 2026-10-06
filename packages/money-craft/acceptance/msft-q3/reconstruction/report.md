# Microsoft FY2025 Q3：增长与资本投入的不同信号

执行日2026-09-20；历史研究截止2025-04-30；US-NASDAQ:MSFT普通股，交易及报告币种USD。所选业绩披露的季度截至2025-03-31；本案例是事后材料回放，不计预测成绩。以下金额为百万USD，现金资本开支按支出绝对值展示。[S01]

**有界判断：经营利润率改善有支持，但资本投入压力缓解尚无支持。** OCF增长与简化FCF下降并存；不能把盈利增长、管理层的资本开支时点解释或一季现金流表现升级为AI投资回报率已验证。

## 同期间现金比较

| 窗口 | 2025 OCF | 2024 OCF | 2025现金PP&E | 2024现金PP&E | 2025 FCF proxy | 2024 FCF proxy |
|---|---:|---:|---:|---:|---:|---:|
| 截至3月31日三个月 | 37044 | 31917 | 16745 | 10952 | 20299.00 | 20965.00 |
| 截至3月31日九个月 | 93515 | 81353 | 47472 | 30604 | 46043.00 | 50749.00 |

单季OCF同比16.06%，现金PP&E同比52.89%，FCF proxy同比-3.18%；累计对应14.95%、55.12%、-9.27%。proxy为同一窗口OCF减现金购建物业设备支出，两组分别比较，不将九个月值误称单季或直接年化。[S01]

季度现金桥：17482 + 37044 − 13036 − 12714 + 52 = 28828.00。累计现金桥：18315 + 93515 − 40855 − 42027 − 120 = 28828.00。两条桥的起点不同；汇率影响不能漏掉。[S01]

## 利润质量与资本投入口径

营业利润率由44.59%变为45.67%，变化1.08个百分点；净利润/收入由35.47%变为36.86%，变化1.39个百分点。集团毛利率则由70.08%变为68.72%，变化-1.37个百分点。营业利润率上升不能推出所有层次利润率均改善，也不能仅凭比率证明改善原因。[S01]

管理层披露含融资租赁资本投入约21.4十亿美元、现金PP&E约16.7十亿美元，后者与报表16745百万的舍入展示相符。含租赁投入不能直接替换现金FCF公式中的现金PP&E，也不能把两者差额称为本期融资租赁现金还本。proxy尚未桥接租赁偿付、债务和必要资金，不等于股东可自由分配现金；完整租赁附注未纳入本案例。[S01][S02]

管理层将资本投入略低于预期归于数据中心租赁交付时间，并预计Q4资本投入环比增加。这里记录其解释与展望，未独立认证因果或预测兑现。GAAP与固定汇率增速须分列；本表采用报告美元，不将固定汇率增速用于反算GAAP报表。未引入独立共识，不自行称“超市场预期”。[S02]

## 反方与下一窗口

反方是本季营业利润率与OCF确实改善，持续资本建设可能支持未来收入，因此FCF下降本身不能证明投资失败。反过来，现有增长不能证明新增AI资本具有足够回报；资料没有分离AI专属现金流、资本基数或可靠回报率。[S01][S02]

下一窗口是FY2025 Q4：检查现金PP&E、含租赁投入及租赁现金偿付各自口径，复核收入、毛利率/营业利润率及现金转换。需要从全年累计推导Q4时，必须与这份九个月累计同口径相减；若后续重述，另建可比基数。只有多期现金转换与可归属收益改善，才有依据上调“资本负担缓解”的判断；继续投入增长且转换走弱则削弱它。

两份来源均来自微软，不构成独立双源；仅阅读选定公告、现金表及电话会相关段落，未完成全量10-Q或四季度趋势审查。结论限这些披露支持的会计比较，不给完整经营质量认证、AI回报率、估值或交易建议。语义由主代理复核。

## 来源索引

[S01] https://www.microsoft.com/en-us/Investor/earnings/FY-2025-Q3/press-release-webcast
[S02] https://www.microsoft.com/en-us/investor/events/fy-2025/earnings-fy-2025-q3

## 复现

准备manifest绑定的私有原件后，运行 `python3 acceptance/msft-q3/reproduce.py --output-dir <新目录>`。它使用现有共享Decimal核心，只重现本案例公式，不自动核实摘录、来源独立性或经济含义。


<!-- money-craft-calc: {"id": "C01", "operation": "subtract", "inputs": ["37044", "16745"], "expected": "20299", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C02", "operation": "subtract", "inputs": ["31917", "10952"], "expected": "20965", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C03", "operation": "subtract", "inputs": ["93515", "47472"], "expected": "46043", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C04", "operation": "subtract", "inputs": ["81353", "30604"], "expected": "50749", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C05", "operation": "subtract", "inputs": ["37044", "31917"], "expected": "5127", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C06", "operation": "divide", "inputs": ["5127", "31917"], "expected": "0.1606353980637277939655982705141461", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C07", "operation": "multiply", "inputs": ["0.1606353980637277939655982705141461", "100"], "expected": "16.06353980637277939655982705141461", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C08", "operation": "subtract", "inputs": ["93515", "81353"], "expected": "12162", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C09", "operation": "divide", "inputs": ["12162", "81353"], "expected": "0.1494966381079984757783978464223815", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C10", "operation": "multiply", "inputs": ["0.1494966381079984757783978464223815", "100"], "expected": "14.94966381079984757783978464223815", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C11", "operation": "subtract", "inputs": ["16745", "10952"], "expected": "5793", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C12", "operation": "divide", "inputs": ["5793", "10952"], "expected": "0.5289444850255661066471877282688093", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C13", "operation": "multiply", "inputs": ["0.5289444850255661066471877282688093", "100"], "expected": "52.89444850255661066471877282688093", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C14", "operation": "subtract", "inputs": ["47472", "30604"], "expected": "16868", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C15", "operation": "divide", "inputs": ["16868", "30604"], "expected": "0.5511697817278787086655339171350150", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C16", "operation": "multiply", "inputs": ["0.5511697817278787086655339171350150", "100"], "expected": "55.11697817278787086655339171350150", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C17", "operation": "subtract", "inputs": ["20299", "20965"], "expected": "-666", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C18", "operation": "divide", "inputs": ["-666", "20965"], "expected": "-0.03176723109945146673026472692582876", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C19", "operation": "multiply", "inputs": ["-0.03176723109945146673026472692582876", "100"], "expected": "-3.176723109945146673026472692582876", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C20", "operation": "subtract", "inputs": ["46043", "50749"], "expected": "-4706", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C21", "operation": "divide", "inputs": ["-4706", "50749"], "expected": "-0.09273089124908865199314272202407929", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C22", "operation": "multiply", "inputs": ["-0.09273089124908865199314272202407929", "100"], "expected": "-9.273089124908865199314272202407929", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C23", "operation": "divide", "inputs": ["32000", "70066"], "expected": "0.4567122427425570176690548911026746", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C24", "operation": "multiply", "inputs": ["0.4567122427425570176690548911026746", "100"], "expected": "45.67122427425570176690548911026746", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C25", "operation": "divide", "inputs": ["27581", "61858"], "expected": "0.4458760386692101264185715671376378", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C26", "operation": "multiply", "inputs": ["0.4458760386692101264185715671376378", "100"], "expected": "44.58760386692101264185715671376378", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C27", "operation": "subtract", "inputs": ["45.67122427425570176690548911026746", "44.58760386692101264185715671376378"], "expected": "1.08362040733468912504833239650368", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C28", "operation": "divide", "inputs": ["25824", "70066"], "expected": "0.3685667798932435132589272971198584", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C29", "operation": "multiply", "inputs": ["0.3685667798932435132589272971198584", "100"], "expected": "36.85667798932435132589272971198584", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C30", "operation": "divide", "inputs": ["21939", "61858"], "expected": "0.3546671408710271913091273562029164", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C31", "operation": "multiply", "inputs": ["0.3546671408710271913091273562029164", "100"], "expected": "35.46671408710271913091273562029164", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C32", "operation": "subtract", "inputs": ["36.85667798932435132589272971198584", "35.46671408710271913091273562029164"], "expected": "1.38996390222163219497999409169420", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C33", "operation": "divide", "inputs": ["48147", "70066"], "expected": "0.6871663859789341478034995575600148", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C34", "operation": "multiply", "inputs": ["0.6871663859789341478034995575600148", "100"], "expected": "68.71663859789341478034995575600148", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C35", "operation": "divide", "inputs": ["43353", "61858"], "expected": "0.7008471014258462931229590352096738", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C36", "operation": "multiply", "inputs": ["0.7008471014258462931229590352096738", "100"], "expected": "70.08471014258462931229590352096738", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C37", "operation": "subtract", "inputs": ["68.71663859789341478034995575600148", "70.08471014258462931229590352096738"], "expected": "-1.36807154469121453194594776496590", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C38", "operation": "add", "inputs": ["17482", "37044", "-13036", "-12714", "52"], "expected": "28828", "tolerance": "0.000001"} -->
<!-- money-craft-calc: {"id": "C39", "operation": "add", "inputs": ["18315", "93515", "-40855", "-42027", "-120"], "expected": "28828", "tolerance": "0.000001"} -->
