# whoami Skill 离线端到端验收

日期：2026-09-23
执行范围：只读取项目的 `SKILL.md`、`references/` 与 `dist/` CLI；未读取 `src/`、`tests/`、`examples/`、`docs/` 或质量记录，未联网、未使用浏览器、未调用 API，未改动项目文件。所有本轮写入均在 `/tmp/whoami-full-report-20260923`。

## 合成请求与输入

请求：女性，阳历 1996-07-19 09:40，合成地点东经120度，`Asia/Shanghai`，真太阳时；需要 2026—2028 年的工作合作、资源安排和关系沟通，并要完整八字和紫微解释及不确定性边界。

输入见 `birth.json`。该地点和经度由请求直接给出，是合成样例，不将其陈述为外部地理核验结果。

## 实际执行与结果

| 阶段 | 实际命令/产物 | 结果 |
|---|---|---|
| CLI 入口 | `node dist/cli.js --help` | PASS：列出 validate、chart、context、rule-review、report-template、report-check、render。 |
| 输入校验 | `validate --input birth.json` | PASS：`status: valid`。 |
| 排盘 | `chart --years 2026,2027,2028` → `chart.json` | PASS：ready、单候选 `C1-0e85dde8`。 |
| 事实/规则包 | `context --years 2026,2027,2028` → `context.json` | PASS：绑定 chartId `219eea8317c53033a396ddb81dd1b5d380074f1e00b90737ee30e0c181397902` 与 evidenceId `7e155f3e7aee71553c39e8d36f113a517eb9d07eecde1d48a8fed9639cf5303d`。 |
| 财格规则复核 | `rule-review` → `rule-review.md` | PASS：入口 `outside-scope`，财印位置和财旺生官分支均 `not-applicable`；报告正文没有把它写成无财或成格。 |
| 报告模板 | `report-template --mode combined` → `report-template.json` | PASS：生成七节、一个候选的五项八字论证槽位。 |
| 自然语言报告 | `report.json` | PASS：七节均有完整 claim；每项都有事实/规则引用；每个候选都有旺衰、格局、调候、扶抑、取舍五项论证；包含跨体系关系。 |
| 结构检查 | `report-check` | PASS：`status: valid`；工具明确说明它不验证自然语言的语义正确性或预测能力。 |
| 渲染 | `render` → `report.md` | PASS：成功插入资料口径、自动财格规则复核、七节正文、五项论证、跨体系对照及可核对事实附录。 |

## 人工事实复核

报告中的核心盘面复述与 `context.json` 一致：真太阳时为 09:33:48.249；四柱为丙子、乙未、丁巳、乙巳；日主为丁；2026—2028 八字年度柱为丙午、丁未、戊申，八字大运为壬辰；紫微命宫在寅、身宫在子，2026—2027 为夫妻大限、2028 为子女大限。正文同时区分了八字立春与紫微农历新年的年度边界，并明确流年四化的本命落宫和流年宫职不是同一层。

## 追问验收与出生时间变更

`followups.md` 回答了三个追问。第三问实际以 10:10 重新校验并运行 chart/context/rule-review；结果保存为 `birth-1010.json`、`chart-1010.json`、`context-1010.json`、`rule-review-1010.md`，逐事实差异保存为 `diff-1010-facts.patch`。重排后四柱、紫微本命、2026—2028 年度事实和财格复核不变；真太阳时和起运日期改变，且 chart/evidence ID 改变，所以旧报告不能直接作为新输入的已校验报告沿用。

## 实际失败与修正

一次用于读取两个 `context` 事实差异的 `jq` 正则表达式括号不匹配，命令报 `Regex failure: end pattern with unmatched parenthesis`。该错误没有修改输入、命盘或报告，也不是 whoami CLI 的失败。随后改用精确事实 ID 选择和排序后的 `diff -u`，得到可复核的 `diff-1010-facts.patch`。其余实际运行的 whoami CLI 命令均退出 0。

## 未核验项与边界

- 这是合成资料的离线试用，不是盲测，也没有现实人生效果、预测准确度或用户体验的外部验证。
- 未验证任意外部地理来源、传统原典的影印校勘、其他流派取用规则、宫干飞化/自化、流月流日，或系统之外的实现细节。
- `report-check` 的 PASS 只说明 JSON 结构、引用和显式断言合格；自然语言仍由人工按现有 facts/rules 复核，不能由 PASS 推出术数理论正确或现实事件必然发生。
- 报告中未以命盘给出医疗诊断、投资指令、保证收益、死亡、疾病或必然婚变判断；资源与合作建议均为可被现实资料反驳的低风险流程建议。

## 交付文件

- 主输入与计算：`birth.json`、`chart.json`、`context.json`、`rule-review.md`。
- 报告：`report.json`、`report.md`。
- 验收与追问：`acceptance.md`、`followups.md`。
- 时间更正对照：`birth-1010.json`、`chart-1010.json`、`context-1010.json`、`rule-review-1010.md`、`diff-1010-facts.patch`。
