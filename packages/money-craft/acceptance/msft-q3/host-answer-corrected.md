**盈利效率有所改善，但现金回报未同步改善，资本投入压力尚未缓解。**

事实：单季收入、营业利润、净利润同比增长13.27%、16.02%、17.71%，营业利润率升1.08个百分点；累计营业利润率亦升0.71个百分点。不过累计净利率下降0.30个百分点，改善并不全面。[S01]

单季经营现金流（OCF）增16.06%，现金资本开支却增52.89%，简化FCF降3.18%；累计分别为增14.95%、增55.12%、降9.27%。OCF还包含折旧、摊销及其他调整、股份支付等非现金加回，其增长不能全归于回款改善。FCF仅指OCF减现金购置物业设备支出，不等于股东可分配现金。[S01]

管理层解释：云账单及回款支持OCF，税款增加形成抵消；费用低于预期也包含部分投入延至Q4。AI扩建令云毛利率同比降3个百分点至69%。含融资租赁资本投入214亿美元略低预期，被解释为租赁交付时点波动，不能据此认定投资收缩；此口径也不能全算作AI支出或直接扣入现金FCF。[S02]

待验证假设与下一窗口：AI效率提升能否抵消扩建与折旧负担，尚未证实。观察FY2025 Q4及全年：管理层预计Q4资本投入环比增加、云毛利率约67%，AI供给约束延续至六月之后；FY2026投入仍增长，仅增速放缓。届时以全年减九个月复算单季，跟踪现金及含租赁投入、FCF、云毛利率和AI变现。若投入继续快于OCF且FCF同比下降，“压力缓解”假设仍不获支持。[S02]

**计算附录**

对象为 Microsoft Corporation，`US-NASDAQ:MSFT` 普通股，交易及报告币种均为USD。研究截止 **2025-04-30**；实际回放日为 **2026-09-20**，使用事后捕获材料，不计预测成绩。

已核对S01原HTML表头：利润表、现金流表均列示 **Three Months Ended March 31** 与 **Nine Months Ended March 31**，各窗口列序均为2025、2024；单位为百万美元，未经审计。下表使用同份披露比较列，箭头为2024→2025。单季为1—3月，累计为上年7月至当年3月，均为直接披露值，无需反推。[S01]

| 指标 | 单季：2024 → 2025 | 同比变化 | 九个月累计：2024 → 2025 | 同比变化 |
|---|---:|---:|---:|---:|
| 收入 | 61,858 → 70,066 | +13.27% | 180,395 → 205,283 | +13.80% |
| 营业利润 | 27,581 → 32,000 | +16.02% | 81,508 → 94,205 | +15.58% |
| 净利润 | 21,939 → 25,824 | +17.71% | 66,100 → 74,599 | +12.86% |
| OCF | 31,917 → 37,044 | +16.06% | 81,353 → 93,515 | +14.95% |
| 现金资本开支（支出绝对值） | 10,952 → 16,745 | +52.89% | 30,604 → 47,472 | +55.12% |
| 简化FCF（计算值） | 20,965 → 20,299 | −3.18% | 50,749 → 46,043 | −9.27% |
| 营业利润率 | 44.59% → 45.67% | +1.08个百分点 | 45.18% → 45.89% | +0.71个百分点 |
| 净利率 | 35.47% → 36.86% | +1.39个百分点 | 36.64% → 36.34% | −0.30个百分点 |

计算口径：

- 同比＝`（本期−上年同期）÷上年同期×100%`；利润率＝`对应利润÷收入×100%`。
- 单季FCF：2025年 `37,044−16,745＝20,299`；2024年 `31,917−10,952＝20,965`。
- 累计FCF：2025年 `93,515−47,472＝46,043`；2024年 `81,353−30,604＝50,749`。

上述28项计算回执经 Decimal 计算及 `financial_rigor.audit_text` 校验通过；这只验证计算，不证明管理层解释的因果关系。

**来源与范围：**[S01 原始业绩公告](https://www.microsoft.com/en-us/Investor/earnings/FY-2025-Q3/press-release-webcast)，定位为 Income Statements、Cash Flows；[S02 原始业绩电话会](https://www.microsoft.com/en-us/investor/events/fy-2025/earnings-fy-2025-q3)，定位为 Amy Hood 本季回顾、Q4展望及FY2026资本开支说明。两文件SHA-256均与指定值一致；均为发行人来源，**不构成独立双源核验**。缺少更长季度序列及独立验证，不能确认持续性经营质量或AI投资回报已经改善。未联网、未归档。

实际读取的Skill为 [money-craft/SKILL.md](~/.agents/skills/money-craft/SKILL.md)，及其 `routing.md`、`earnings-review.md`、`financial-data-and-evidence.md`、`research-semantic-review.md`；另读取宿主 `investment.md` 规则。路由为 `earnings / quick / chat`，主代理串行执行。

<!-- money-craft-calc: {"id":"C01","operation":"divide","inputs":["820800","61858"],"expected":"13.26910019722590449093084160","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C02","operation":"divide","inputs":["2488800","180395"],"expected":"13.79639125252917209457024862","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C03","operation":"divide","inputs":["441900","27581"],"expected":"16.02189913346144084695986367","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C04","operation":"divide","inputs":["1269700","81508"],"expected":"15.57761201354468273052951857","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C05","operation":"divide","inputs":["388500","21939"],"expected":"17.70819089293039792150964037","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C06","operation":"divide","inputs":["849900","66100"],"expected":"12.85779122541603630862329803","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C07","operation":"divide","inputs":["512700","31917"],"expected":"16.06353980637277939655982705","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C08","operation":"divide","inputs":["1216200","81353"],"expected":"14.94966381079984757783978464","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C09","operation":"divide","inputs":["579300","10952"],"expected":"52.89444850255661066471877283","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C10","operation":"divide","inputs":["1686800","30604"],"expected":"55.11697817278787086655339171","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C11","operation":"divide","inputs":["-66600","20965"],"expected":"-3.176723109945146673026472693","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C12","operation":"divide","inputs":["-470600","50749"],"expected":"-9.273089124908865199314272202","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C13","operation":"divide","inputs":["2758100","61858"],"expected":"44.58760386692101264185715671","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C14","operation":"divide","inputs":["3200000","70066"],"expected":"45.67122427425570176690548911","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C15","operation":"subtract","inputs":["45.67122427425570176690548911","44.58760386692101264185715671"],"expected":"1.08362040733468912504833240","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C16","operation":"divide","inputs":["8150800","180395"],"expected":"45.18307048421519443443554422","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C17","operation":"divide","inputs":["9420500","205283"],"expected":"45.89030752668267708480487912","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C18","operation":"subtract","inputs":["45.89030752668267708480487912","45.18307048421519443443554422"],"expected":"0.70723704246748265036933490","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C19","operation":"divide","inputs":["2193900","61858"],"expected":"35.46671408710271913091273562","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C20","operation":"divide","inputs":["2582400","70066"],"expected":"36.85667798932435132589272971","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C21","operation":"subtract","inputs":["36.85667798932435132589272971","35.46671408710271913091273562"],"expected":"1.38996390222163219497999409","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C22","operation":"divide","inputs":["6610000","180395"],"expected":"36.64181379749993070761384739","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C23","operation":"divide","inputs":["7459900","205283"],"expected":"36.33958973709464495355192588","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C24","operation":"subtract","inputs":["36.33958973709464495355192588","36.64181379749993070761384739"],"expected":"-0.30222406040528575406192151","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C25","operation":"subtract","inputs":["37044","16745"],"expected":"20299","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C26","operation":"subtract","inputs":["31917","10952"],"expected":"20965","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C27","operation":"subtract","inputs":["93515","47472"],"expected":"46043","tolerance":"0.000001"} -->
<!-- money-craft-calc: {"id":"C28","operation":"subtract","inputs":["81353","30604"],"expected":"50749","tolerance":"0.000001"} -->

交付修订说明：主代理仅将两处本机来源链接替换为案例绑定的官方URL，并将Skill本机路径归一为~；研究文字与计算未改动。原始宿主答案及失败记录保持不变。
