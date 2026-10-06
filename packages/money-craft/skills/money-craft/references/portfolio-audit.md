# 证据绑定的组合审计

适用于已取得基金费用和持仓快照的、权重合计为 1 的多头组合。先按正常投资路由明确目标、期限和约束，再构造 [输入合同](../schemas/portfolio-input.schema.json)，运行：

```bash
python3 skills/money-craft/scripts/money_craft.py portfolio audit --input /absolute/path/portfolio.json --json
```

在安装目录使用时，以实际 Skill 路径替换命令前缀。命令只读输入与来源文件，不请求网络、不修改账户。返回 `money-craft.portfolio-audit.v1`；输入无效退出 2，计算有效退出 0。`valid: true` 表示合同与运算通过，风险约束仍可能是 `BREACHED`。

## 输入与证据

- 所有数值用普通十进制字符串，最多 34 位数字、18 位小数；不接受浮点 JSON 数字、指数或 NaN。比例用小数，例如 0.03% 为 `"0.0003"`。
- `as_of` 是此次研究截止日；`principal`、`base_currency`、`assumption_note` 明确本金、基础币种及用户事实/演示假设。`max_loss` 为情景损失上限，`max_issuer_weight` 为发行人权重上限，均在 0–1 内。
- `sources` 逐项提供 `id/fund_id/path/sha256/url/as_of`。文件路径相对输入文件，也可为绝对路径；URL 为无用户名密码的 HTTPS。日期指数据快照日，不是发布日期或抓取时间；历史可知性研究仍须另核验发布日期。最多 100 来源，单个文件最多 32 MiB，输入最多 2 MiB。
- `funds` 最多 50 项。每项包含唯一 `id`、`quote_currency`、正 `weight`、`fee`、`holdings`。全部基金权重必须精确合计 1。`fee` 包含 `rate/source_id/locator`；`holdings` 包含 `coverage/as_of/source_id/locator/positions`。来源的基金身份必须匹配引用基金。
- `positions` 每项为 `security_id/issuer_id/weight`；区分证券类别后再汇总发行人。一个证券不能重复或映射到不同发行人。最多 20,000 项/基金。`complete` 必须合计 1；部分披露使用 `partial`，没有转录的持仓用空数组，并在 locator 说明。所有基金持仓日期须相同且等于各自引用来源日期，不能合并不同期末的快照。
- `scenarios` 最多 100 项，每项包含唯一 `id`、`assumption_note`、`asset_returns` 和 `fx_returns`。前者键必须恰好覆盖所有基金；后者必须恰好覆盖所有非基础交易币种，基础币种隐含为 0。收益率不得低于 -1。

来源 SHA-256 通过只证明本地文件与输入摘要一致，不证明文件来自所列网站，也不证明转录、完整覆盖、发行人映射正确。因此结果始终保留 `claim_support: UNVERIFIED`，研究者仍须核对原文和定位。输出回显输入、输入哈希和 Decimal 计算回执，可交给既有计算审计器重算。

## 计算及判定

加权费率为 Σ(基金权重 × 年费率)，静态年费为本金 × 加权费率；不含交易、换汇、税费，不对已扣费用的净值收益再次扣费。

已知持仓覆盖率为 Σ(基金权重 × 已转录持仓权重之和)。发行人权重聚合同一发行人的所有证券。已知权重超过上限即 `BREACHED`；部分持仓低于上限仍是 `UNVERIFIED`，完整声明下才是 `WITHIN_SNAPSHOT`。

两基金证券重叠度为 Σ min(两边同一证券的基金内权重)。双方均完整时是 `EXACT_WITHIN_INPUT`；其他情况只能是 `LOWER_BOUND`。这不是发行人重叠度、相关系数或组合风险贡献；空持仓的下界 0 不代表没有重叠。

压力情景按 Σ[基金权重 × (1+资产净值收益) × (1+FX收益)]−1 计算基础币种收益。FX 方向是每单位交易币种可兑换的基础币种金额变化。情景期间不再平衡；美元交易基金也可能有其他经济货币敞口，本公式不替代底层敞口模型。损失严格超过上限才判 `BREACHED`，等于上限为 `WITHIN_SCENARIO`。

本核心不估计概率、历史最大回撤、相关性或最优配置。情景通过不保证未来风险合规；完整性声明也不是自动穿透认证。对数据选择、现金需求、适当性和研究结论的解释仍需人工语义复核。

计算回执编号为 `C` 加 2–7 位数字；大持仓输入超过 9,999 条计算时继续编号，财务审计与勾稽合同使用同一长度范围。
