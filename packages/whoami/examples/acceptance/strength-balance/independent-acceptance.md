# whoami 普通格旺衰—扶抑独立试用记录

日期：2026-09-23。项目只读范围为 `SKILL.md`、`references/*.md`，以及 `references/strength-balance.md` 直接引用的 `docs/research/strength-balance.md`；未读取项目其他 `docs`、`src`、`tests`、`examples` 或其他代理产物，未联网、未调用 API/浏览器。唯一写入目录：`/tmp/whoami-strength-balance-20260923`。

## 来源与本轮引用

- 运行契约：`SKILL.md`；要求使用 `dist/cli.js`，以同一输入和年份运行 `chart`、`context`、`report-template`、`report-check`、`render`，并为八字模式填写五项 `baziReasoning`。
- 结构、通根与正文契约：`references/analysis.md`、`references/input-and-cli.md`、`references/report.md`。报告使用 A 的实际 `chartId` `975f2f41c627e87ab9bd4649660481f3012dd3925ab6d71a69c60b3ff2daef7e` 与 `evidenceId` `3d63ac72c281c6a6366ab1f3b76667951fe4a1648c8baf3748dc450f48261040`；报告内引用的是该 context 的实际事实/规则 ID。
- 旺衰—扶抑方法：`references/strength-balance.md`，其研究记录 `docs/research/strength-balance.md` 记载本轮工作取法为《滴天髓阐微》“体用”任氏注的普通旺抑弱扶，并以《子平真诠·论十干得时不旺失时不弱》约束“月令不是唯一依据、根与透干不能简单计数”。研究记录列出的公开转录链接是：[子平真诠章节](https://donglishuzhai.net/chapter/3719.html)、[滴天髓阐微体用](https://zh.wikisource.org/zh-hans/%E6%BB%B4%E5%A4%A9%E9%AB%93%E9%97%A1%E5%BE%AE)。本轮未联网复核这些原文或影印本。

## 实际命令与结果

全部在仓库根目录执行，输入与结果均在临时目录 `/tmp/whoami-strength-balance-20260923`。

1. `node dist/cli.js --help`：成功；确认本地 CLI 的子命令。
2. A：`validate`、`chart --years 2026,2027,2028`、`context --years 2026,2027,2028`、`rule-review --years 2026,2027,2028`、`report-template --mode bazi --years 2026,2027,2028`：均成功。A 为唯一候选 `C1-f7863f9a`，四柱为庚午、戊子、丁巳、甲辰。
3. B：`validate`、`chart --years 2026,2027,2028`、`context --years 2026,2027,2028`：均成功。B 为唯一候选 `C1-2b3d9d47`，四柱为丁卯、甲辰、乙酉、乙酉。
4. A：`report-check --report report.json --years 2026,2027,2028`：成功，输出 `status: valid`；随后 `render --report report.json --years 2026,2027,2028`：成功，生成 `report.md`。

没有 CLI 失败。一次只读探索命令错误地将 `context` 视为含 `.candidates` 字段，`jq` 返回“Cannot iterate over null”；随后改按真实 schema 的 `.facts`、`.rules` 读取。最后的产物列举中，macOS `find` 不支持 GNU 风格 `-printf`，该列举命令失败后以 `rg --files` 成功列出目录。两项失败都未影响任何计算或产物。

## 独立论证自审

### A：扶抑中的“戊伤官为主要负荷”是否已充分比较子月癸杀得令？

**结论：不足以作强优先级结论。** 现有 `balance` 写作已保留条件（“若偏弱成立”“子、辰中癸杀未透，仍要另核验”），并没有声称癸杀不存在；但它仍把“当前更具体的主要负荷先看戊伤官透月”作为倾向，而允许来源没有提供子月癸杀的司权、得令权重、实际克力、杀印制化或与戊泄之间的比较规则。

可确认的盘面事实是：戊伤官透于月干；子中癸为七杀、未在年/月/时同干透出；辰中也藏癸。`references/strength-balance.md` 明确要求月令背景不能直接等同全局强弱，且如判断依赖司权日数应点明资料缺口；它也要求分别说明食伤泄和官杀克，不能合并，也不能因“未透”当作无作用。因此，透出的戊提供了可以讨论“食伤泄”的充分事实，但**不足以排除或降低得令癸杀为主要负荷的可能性**。对 A 更合格的扶抑表述应保持两个分支：若后续作用核验认定戊泄主导，则讨论印扶身/制泄；若子月癸杀的实际克力主导，则讨论印化杀扶身，并审印是否可用、是否受财制、杀印路径是否成立。

本次按任务要求保留 `report.json` 和 `report.md` 不改。故这是一项对现有论证的**实质性限制**，而不是以 `report-check` 通过替代学理复核。

### B：是否强行选了主要负荷或唯一方向？

没有。`analysis-b.md` 将双酉辛七杀及冲卯列为优先核验的压力线索，但明确其未透、未有实际强度/制化规则，故未坐实为主要负荷；扶抑保留“同类木确可任负荷时讨论食伤泄比并需财承接”与“若双酉杀主导则审印化杀”的两条路径。它没有用藏干顺序、五行个数或“有根”来强定身强。

## 未验证项与边界

- `report-check` 仅验证结构、引用和显式事实断言；其输出也明确不证明自然语言解释的语义正确性或预测能力。`valid` 不是本报告的学理、现实效果或用户决策认证。
- A 的月令司权、子中癸杀的实际作用、巳午火根等级、午子冲对根的影响、甲乙印是否受财制及实际扶身、合化/制化、特殊从势/专旺/化气均未验证。A 的格局与调候也未定。
- B 的月令司权、卯辰根的实际等级、卯酉冲和辰酉合对根/杀的影响、双酉辛杀的实克、印杀制化、特殊格与调候均未验证。
- 请求年份只计算年度柱和大运数据；未做流月/流日，也没有从年度柱推导现实升职、财富、健康或关系事件。
- 经度120与时区Asia/Shanghai为题设合成资料而非外部地理核验结果；真太阳时使用核心提示的 NOAA 近似均时差模型。
- 本轮只读取研究记录中列出的公开原文转录，不构成原典校勘、传统命理专业评审，也不证明传统理论或任何现实预测的有效性。

## 产物清单

- `birth.json`、`birth-b.json`：两份题设输入。
- `chart-a.json`、`context-a.json`、`rule-review-a.md`、`report-template-a.json`：A 的本地计算与报告模板证据。
- `report.json`：A 的八字模式七节报告与五项 `baziReasoning`。
- `report-check.json`：结构/引用检查结果。
- `report.md`：A 渲染后的最终 Markdown 报告。
- `chart-b.json`、`context-b.json`：B 的本地计算证据。
- `analysis-b.md`：B 的局部强弱—负荷—扶抑—改判条件回答。
- `followups.md`：两项追问回答。

以上文件均在 `/tmp/whoami-strength-balance-20260923/`。
