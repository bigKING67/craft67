---
name: money-craft
description: 面向全球市场的证据优先投资研究与理财决策支持，覆盖上市公司、行业主题、基金与组合分析、财报、估值和论文追踪；不执行自动交易或账户操作。
---

# Money Craft

以可核验事实、精确计算和反方证据支持全球投资研究与理财决策。A 股只是 Fuyao 适配器当前覆盖的一个市场，不是 Money Craft 的产品边界。不要把结构化数据平台、搜索摘要或模型记忆当作正式披露的替代品。

## 路由

宿主 AGENTS 或已声明的投资治理规则要求外部路由时，先读 [references/routing.md](references/routing.md) 并完成路由回执核对，再进入分析；用户显式指定本 Skill、quick/chat、合成演练、离线或仅用给定材料都不豁免该要求。宿主没有此要求时只用下表，不引入额外工具依赖。只加载当前模式需要的参考：

- 快速排雷或质量筛选：[references/screening.md](references/screening.md)；涉及数字时再读 [references/financial-data-and-evidence.md](references/financial-data-and-evidence.md)，不要读取完整公司研究运行合同。
- 完整公司研究：[references/company-research.md](references/company-research.md)；它包含确定性研究入口、可恢复运行和完成收据门禁。
- 全球市场、基金/债券/组合或跨币种理财问题：[references/global-investing.md](references/global-investing.md)；已有基金费用与持仓快照的组合审计：[references/portfolio-audit.md](references/portfolio-audit.md)
- 行业主题、时代主线、核心资产或高增长 α：[references/high-growth-alpha.md](references/high-growth-alpha.md)；研究具体公司时同时加载完整公司研究和估值规则
- 财报或业绩解读：[references/earnings-review.md](references/earnings-review.md)；运行 `earnings` 子命令（更新、前瞻封存/复盘、交叉核验、驱动模型）时再读 [references/earnings-tools.md](references/earnings-tools.md)
- 估值、建立或更新投资论文：[references/valuation-and-thesis.md](references/valuation-and-thesis.md)
- 完整研究、估值或论文交付前的语义验收：[references/research-semantic-review.md](references/research-semantic-review.md)
- 将论文更新封存为公司级跟踪历史：[references/tracking-workflow.md](references/tracking-workflow.md)
- 涉及任何财务、行情或估值数字：[references/financial-data-and-evidence.md](references/financial-data-and-evidence.md)
- 使用 Fuyao A 股客户端：[references/providers/fuyao.md](references/providers/fuyao.md)；可选 yfinance 港美股客户端：[references/providers/yfinance.md](references/providers/yfinance.md)；FRED/ALFRED 宏观、利率、通胀和历史 vintage 数据：[references/providers/fred.md](references/providers/fred.md)
- 生成或验收最终 HTML/PDF：[references/report-rendering.md](references/report-rendering.md)

`security_id` 使用 Money Craft 的开放 `MARKET:SYMBOL` 语法，例如 `CN-SZ:000333`、`HK:00700`、`US-NASDAQ:NVDA`；它不是对外部交易所代码标准的声明。`thscode` 和 Yahoo symbol 都只是 Provider identifier，不能替代证券身份。基金/ETF、债券和组合的身份字段见 [routing.md](references/routing.md#证券身份)。

## 不可省略的合同

1. 开始任何事实型研究前，记录当前日期、研究 `as_of`、数据截止时间和最新正式报告期。
2. 将对象解析为唯一 `security_id`，并记录市场、交易币种、报告币种、工具类型和 share class；同名、多地上市或存托凭证有歧义时列出候选并停止。
3. 当地监管机构、交易所、发行人/基金管理人正式披露和法定文件是主真源。Fuyao、yfinance 和 FRED 都只是适用范围内的结构化适配器或补充来源。
4. 关键财务数据必须绑定 `[S01]` 形式的来源；推算值同时写出公式、输入、单位和计算回执。
5. 区分 `OBSERVED`、`INFERRED`、`HYPOTHESIZED`、`UNVERIFIED`。资料不足时降低置信度，不补齐看似完整的数字。
6. 明确给出结论、反方证据、证伪条件和下一次需要验证的事实。筛选通过不等于建议买入。
7. 任何账户访问、下单、发布、消息或外部写操作都需要当前明确授权；本 Skill 本身不执行交易。
8. 外部路由只有命令成功退出且返回有效路由结果才算完成；最终回答前检查该回执。无法完成时明确标为路由未完成，不把已尝试的调用描述为成功，也不启动依赖该路由的后续阶段。

## 按需操作合同

把包含本文件的目录解析为绝对路径 `MONEY_CRAFT_SKILL_DIR`。完整公司研究的 `research plan/init/collect/import-official/import-public/status/finalize`、运行目录、Provider gap 与完成收据规则在 [company-research.md](references/company-research.md)。使用 Provider 时，先读 [financial-data-and-evidence.md](references/financial-data-and-evidence.md) 的共享运行、凭据和当前来源边界，再读实际 Provider 的 reference 获取其专用解释器、可选依赖和迁移兼容性；不得将 key 放进命令行、报告、Git 或运行回执。

报告 HTML/PDF 的受控运行时、渲染与验收命令在 [report-rendering.md](references/report-rendering.md)；它们只从已审计 Markdown 生成 repo 外派生物，不能改写 sealed revision 或研究结论。论文更新和公司级跟踪的 `track` 命令、离线验证及只读 revision 合同在 [tracking-workflow.md](references/tracking-workflow.md)。
