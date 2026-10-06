# 财报工具合同

财报 CLI 的输入合同与输出语义。阅读方法、最低输出与语义复核见 [earnings-review.md](earnings-review.md)；工具输出不能替代完整精读的披露面与历史比较要求。

## 可复算的财报更新入口

对已有、已审计论文，使用共享核心生成财报变化、模型输入变化、三情景估值桥及 tracking 建议：

```bash
python3 "$MONEY_CRAFT_SKILL_DIR/scripts/money_craft.py" earnings review \
  --input <earnings-update-input.json> --previous-thesis <audited-thesis.md> --json
```

输入合同为 `schemas/earnings-update-input.schema.json`。为每份来源登记证券身份、公开 URL、披露日期、文件 SHA-256 和本地路径；每个数字登记单位与页码/表格定位。文件路径相对输入 JSON 所在目录解析，也可使用绝对路径。完整文件留在私有证据目录；输出回执只含来源元数据、定位、输入值与计算结果。历史回放应另记实际获取时间和 post-hoc 性质，不将今天下载的文件冒充历史捕获。

当前计算层覆盖相邻年份的同一财政窗口（annual/quarter/ytd 不能混用），并要求营业收入、归母净利润、经营现金流、普通股股数四项归一化输入。`shares` 必须是核实后的股数，不能直接拿账面股本金额代替；确认股权类别、单位换算及稀释影响。`net_income` 必须与普通股权益口径相符。非标准 52/53 周或变更年结导致窗口不一致时，本版要求先另行建立可比口径，不自动平移日期。

`comparison_basis` 必须为 unchanged、restated 或 unverified；unverified 返回 `valid=false` 并阻断估值及交接。重述时提供同一旧期间的 `comparable_previous` 与原因，比较表显示重述调整；旧估值仍保留当时已知的原始输入，避免回写历史模型。非正基数不生成增长百分比。

预期是可选项。只有同时提供完整财政窗口、会计口径、单位、预期日期和来源定位，以及单独绑定来源的 `first_actual_disclosure`，才计算实际与预期的差异。先核查业绩快报/预告/公告等是否早于年报披露相同实际值，不能把后来年报发布日期当成首次披露。首次事件或可比口径不明时不提供预期比较；软件只核验登记日期与引用的一致性，事件识别仍由研究者负责。

估值首版仅支持正归母利润的 `earnings_multiple`：`net_income × earnings_factor × pe × fx / shares`，强制 bear/base/bull、显式假设理由和币种。按净利润、盈利因子、倍数、股数、汇率顺序逐项替换输入，贡献和舍入残差须与端点变化一致。桥的归因与替换顺序有关，数值是演示/研究情景，不是市场目标价；不将净现金重复加到权益利润倍数法上。DCF、亏损/周期正常化或金融企业的其他模型尚不由此命令计算。

输出 `valid` 只表示输入/计算合同通过；文件完整性、人工提取准确性、论文支持分别表达。`thesis_updates` 必须覆盖旧论文的全部假设与红线 ID，逐项提供建议状态、理由与来源，不能通过额外字段覆盖旧状态。`tracking_handoff` 保持 PROPOSED_REQUIRES_REVIEW；确认后按其绑定的旧论文和 as_of 执行 `track init`，完成 thesis/card/state，再执行 `track check` 和 `track verify`。保留旧更新行，不根据同比正负自动改变长期假设。

## 财报前瞻封存与催化剂兑现

复盘前先保存独立前瞻，使用共用核心：

```bash
python3 "$MONEY_CRAFT_SKILL_DIR/scripts/money_craft.py" earnings seal-preview --input preview.json --output baseline.json --json
python3 "$MONEY_CRAFT_SKILL_DIR/scripts/money_craft.py" earnings replay-preview --baseline baseline.json --input outcome.json --json
```

`preview.json` 的 schema 为 `money-craft.earnings-preview.v1`，包含 `security_id`、`currency`、`as_of`、`sources`、`expectations`、`catalysts`。sources 沿用 earnings review 的来源合同：证券绑定、HTTPS URL、发布日期、真实本地文件、SHA-256。基线保留绝对本地证据路径，不应直接对外发布；源文件需长期保留。

每条 expectation 包含 `metric`、`origin`（analyst/management/consensus）、`rationale`、`value`（十进制字符串）、`unit`、`as_of`、`period_start`、`period_end`、`kind`、`accounting_basis`、`source_refs`。同一指标可以按来源类型分别比较，不混称“一致预期”。分析师估计的 source_refs 绑定假设依据，不能声称来源直接披露了自算预测值。

每个 catalyst 包含唯一 `id`、`window_start`、`window_end`、`impact_path`、`confirmation_condition`、`invalidation_condition`、`next_evidence`、`decision_condition`、`source_refs`。即使窗口已过也不视为兑现。

`outcome.json` 的 schema 为 `money-craft.earnings-outcome.v1`，包含相同身份字段、复盘 `as_of`、本次 `sources`、`actual`（沿用 earnings review 的四项 reported 实际值快照）、`first_actual_disclosure`（date/source_refs）和 `catalyst_observations`。观察以催化剂 ID 为键，值包含 `state`（OCCURRED/CANCELLED）、`observed_on`、`rationale`、`source_refs`。没有观察时使用空对象。事实必须在复盘截止日前可用；首披日期需要当日来源，但是否真正为首次披露仍需人工核实。重述口径需另行明确调和，当前前瞻复盘入口拒绝直接混用。

封存不覆盖已有文件；修订预期另建版本并保留旧文件。复盘输出保留基线哈希、输入哈希、预期来源、差额、催化剂状态与开放研究任务。任务说明关注原因、所需证据、影响决策的条件，不能自动修改论文或执行账户操作。

`LOCAL_SEALED_BEFORE_DISCLOSURE` 只表示本地时钟早于披露日；同日或事后封存标为 `RECONSTRUCTED_AFTER_DISCLOSURE`，不得算作事前预测成绩。本地哈希可检出未同步修改哈希的内容变化，不提供外部可信时间戳或防管理员篡改证明。来源哈希通过仍不代表抽取和论点语义已核实。事件已发生也保持 `thesis_support=UNVERIFIED`，由研究者按保存的确认/证伪条件审核。

尚无实际结果时运行 `earnings inspect-preview --baseline baseline.json --json`：离线校验基线和引用文件，列出关注任务；返回 `UNVERIFIED_NO_OUTCOME_PROVIDED`，不会将“未提供结果”当成“尚未披露”。日期字段使用宿主本地日历日，封存时间保留 UTC offset，比较首披日时按该封存时区的日历日保守判断；使用者应使研究环境时区与所填披露日口径一致。同日封存不算披露前预测。

## 前瞻输入数字交叉核验

`earnings crosscheck-preview --baseline baseline.json --input checks.json --json` 离线读取独立保存的核验清单和 Fuyao `financials.income` capture，不重写基线。输入 schema 为 `money-craft.earnings-crosscheck-input.v1`，字段为 `security_id`、核验 `as_of`、可选 `provider_capture`（含 capture.json/response.json 的目录）、`provider_basis` 和 `checks`。当前仅支持上海/深圳 A 股收入和归母净利润；捕获方式沿用 Fuyao reference。

每个 check 包含 `metric`（revenue/net_income）、`year`、`quarter`（1–4）、`kind`（ytd/quarter）、`unit`、正式来源摘录的十进制字符串 `value` 和基线来源中的 `source_refs`。必须核对正式表格后才能写 `provider_basis=ytd_confirmed_against_filing`。接口 `quarterly` 只表示频率，不足以证明单季口径；此入口在明确累计口径后，以相邻累计差推导单季，并回显计算输入。不能把净利润字段替代归母净利润。

结果按正式值绝对值（零值分母下限 0.000001）计算差异率：≤1% 为 MATCHED，>1% 至 5% 为 REVIEW_REQUIRED，>5% 为 CONFLICT。缺捕获、缺期间或 null 为 MISSING，未明确口径为 UNVERIFIED_BASIS。除 MATCHED 外 CLI 返回非零；来源哈希错误、重复期间、单位错配、未来披露或业务失败直接拒绝。未匹配不以“已解释”自动放行，修订另存核验版本。

`valid=true` 仅覆盖清单列出的数字。来源摘录的准确性和所有预测输入是否列全仍需人工复核。结果保留基线/输入/Provider 响应哈希、抓取时间及是否晚于原封存；当前快照始终不冒充 point-in-time 数据。独立 Provider 渠道的数据仍可能源于同一发行人，因此保留来源同源限制，不自动提升整体研究准备度或确认投资论文。

## 业务驱动模型

`earnings drivers --input model-input.json --json` 读取 `money-craft.earnings-drivers-input.v1`。身份、币种、as_of、sources 沿用财报合同；`historical_period`、`forecast_period` 包含 start/end/kind/accounting_basis，当前限相邻年度的相同财政窗口。选择一个 `dimension=product|channel|consolidated`；`segments` 按唯一 ID 保存同维度的历史 revenue 和 source_refs，不能将产品和渠道两套收入相加。

`historical` 保存总 revenue、归母 net_income、gross_margin、expense_rate、tax_rate、other_pretax、minority_profit 和 source_refs。金额使用报告币种，比例为 0–1 的十进制字符串。expense_rate 的费用范围须在输入解释中固定；other_pretax 明确容纳尚未单独建模的税金及附加、利息或其他损益，不等于这些项目不存在。少数股东损益用绝对金额。

每个情景的 driver 集合必须为全部 `growth:<segment_id>` 加上述五个利润驱动。每项包括 value、rationale、confirmation_condition、invalidation_condition、next_evidence、source_refs；bear/base/bull 必须齐全。来源支持假设依据，不代表正式来源披露了预测值。无可靠量价证据时只使用分部收入变化，不能补造销量/单价。

计算链为：各分部历史收入 × (1+增长率) → 合计收入 → 收入 × 毛利率 − 收入 × 费用率 + other_pretax → 税前利润 × (1−所得税率) − 少数股东损益。历史收入/归母利润须在 0.01 报告币种单位内闭合；亏损税务情形当前拒绝，需要另建明确税务模型。情景收入和归母利润须悲观≤基准≤乐观。

`sensitivity` 数组的 driver/delta 对基准单项加减：增长率和费率 delta=0.01 表示加 1 个百分点，不是相对增加 1%；其余为金额变化。结果是其他条件不变的敏感性，不是预测概率。

可选 `actual` 包含完全相同的 period、实际 drivers（数值字符串）、实际 revenue/net_income 和 source_refs。实际分部收入须闭合；利润桥按固定顺序替换驱动，保留无法解释的残差。残差未闭合时输出 REQUIRES_RESEARCH；已闭合也只证明条件计算成立，不证明因果。未给实际结果时输出 null，不能伪造已兑现记录。

案例脚本 `scripts/check_driver_case.py` 在新目录保存模型并生成单独前瞻基线。基线内 linked_model_hashes 可绑定同目录 model-input.json/model-result.json；检查基线同时检查关联文件。修订须另建版本，旧模型及已有三季度前瞻不得覆盖。当前演示模型不自动升级为完整研究或替代旧预测。

实际复盘应分别读取 `bridge_status` 与 `residual_status`：即使基准和实际端点盈利，固定替换顺序仍可能经过亏损中间状态。此时保留实际端点与残差，返回 bridge_status=UNAVAILABLE、空 bridge 和原因；不得把残差闭合解释为归因已完成。真实亏损端点仍要求另建税务模型。

封存前必须校验关联模型；发布使用完整临时文件的原子不覆盖操作，失败不能留下看似已封存的半份基线。平台不支持所需文件操作时直接失败，不降低为覆盖写。

### 日期与期间准入

财报更新的研究 `as_of` 不得晚于运行主机的本地自然日；前瞻可研究未来报告期间，但研究日期本身不能来自未来。前瞻预期的期间与实际值共用期间合同：annual 为 330–380 天、quarter 为 60–110 天、ytd 为 1–380 天，日期须有序且 accounting_basis 非空。这里检查的是声明的基本一致性，不证明特定发行人的财政日历或累计口径正确。旧基线若违反期间合同，检查/回放会拒绝，不自动改写历史文件。

业绩前瞻的 baseline、crosscheck、drivers 与 reconciliation 扩展输入以对应 CLI 的运行时校验为准；当前不是每类输入都有独立公开 JSON Schema，不应把通用 earnings-update schema 当作这些输入的完整预校验合同。
