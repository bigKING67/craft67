# 丙火申月调候候选的正例与双反例

日期：2026-09-24。结论：当前调候参考只覆盖 `dayMaster=丙` 与 `month.branch=申` 的合取入口。两项同时满足时，可以条件性确认“在所选 1926 年《穷通宝鉴》版本下，壬水进入调候优先复核候选”；任一项不满足都不能套用该条目。

## 固定口径

- 条件 A：同一候选的日主为丙。
- 条件 B：同一候选的月支为申。
- `PASS+PASS` 只确认来源条目和壬水候选身份，不确认壬有效、唯一喜水或最终用神。
- `PASS+FAIL`、`FAIL+PASS` 均表示当前窄条目不适用；它们不证明没有其他调候取法，也不反向证明壬水有害。
- 入口满足后还要核对壬、戊的透藏与多寡。藏壬不能改写成壬透，癸水不能因同属水就替代壬水。

## 当前核心重算

三例均使用仓库内合成出生资料，经当前构建版 `context` 重算。历史消融目录中的旧 context 快照未改写；本轮只复用其出生输入形成入口反例。

| 对照 | 输入与年份 | 可复算事实 | A | B | 当前条目结果 |
|---|---|---|---|---|---|
| 正例 | [`examples/birth.json`](../../examples/birth.json)，2024—2028 | 庚辰、甲申、丙午、庚寅；日主丙、月支申；申藏壬、戊，二者均未同干透于年/月/时 | PASS | PASS | 可条件性确认壬水为来源特定的调候复核候选；不可确认唯一喜水 |
| 近失配 A | [`case-03-birth.json`](../../examples/acceptance/strength-ablation/case-03-birth.json)，2026—2028 | 日主丙，月柱丁巳、月支巳 | PASS | FAIL | 同日主但月份不符，不能套用“七月丙火”条目 |
| 近失配 B | [`case-02-birth.json`](../../examples/acceptance/strength-ablation/case-02-birth.json)，2026—2028 | 月柱壬申、月支申，日主甲 | FAIL | PASS | 同月支但日主不符，不能把壬透干借成丙火条目的结论 |

正例重算得到 `chartId=a3fee7834bc85e84bff82e9ad80e72c9678383d5948ea7ae4d76e2094cb97789`、`evidenceId=3d0b34bd617494d53f269cc99fa79edf01647a9ebb72b0fc6a806970d096ea9e`。`monthExposure` 明确列出申藏壬七杀、戊食神的 `exposedAt=[]`，因此“有壬候选”和“壬已经透出或调候完成”是两种不同判断。

近失配 A 重算得到 `chartId=557a8dc94ee48ca5e7c1365c34ecbaeb5343ca9986e0190ea147c335a4ba895b`、`evidenceId=9add0f179098b9cd918664b526e83e777b9175c3dc2f2fcff0d7b313d2b0b2a5`。近失配 B 重算得到 `chartId=ddbbd8bb361b916e2c328aea10f14e779e308bb87762beaee42e5e6ad3cc61dd`、`evidenceId=9b5af8ebc18f73fbf97b16ff6d17b13387b4f5f77953f9a0ff16ca74b7069d0d`。后者虽月、时两壬透出，但它是甲日主的偏印事实，不能跨日主套入丙火调候条目。

## 主报告边界

主报告的 climate 从“未找到具体候选”收窄为 `conditional`，只确认所选版本下的壬水复核候选；selection 继续 `unresolved`。正文同时写明壬、戊只藏未透，以及调候、扶抑、格局必须分别核验。引用 climate 但同时依赖 selection 的用户段落仍保持 unresolved，不因单个前提收窄而越级。

本轮没有新增自动调候引擎、十天干十二月令表、评分阈值、报告 schema 或依赖。结构校验通过只证明引用与前提状态一致，不证明古籍理论、现实预测或“补某五行”的干预有效。

主报告 `report-check` 返回 valid，重新 `render` 与 [`examples/report.md`](../../examples/report.md) 字节一致。更新后的结构化报告为 28,589 字节、SHA-256 `a92d530ebd2161970562c69f8bfe09ad3e84338dea59f98e6d9f89fce1a3443a`；Markdown 为 67,067 字节、SHA-256 `21253175017d4157f3f5f105c1eff2cb47e9f46ae9524dbb7c9fb304c401165f`。`npm run check` 132/132 PASS，TypeScript strict 与 build PASS，Skill quick_validate PASS；54 个现行 Markdown 的 179 个本地链接无缺失。
