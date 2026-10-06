# 双盘分歧专门验收：2026-09-23

结论：五个追问场景暴露了无依据的决策取舍和关系分类问题；已修订 Skill 分析指引、纠正两份已有报告的过度印证，并通过一次定向变体复测。有限场景语义验收通过，不代表真实命盘冲突已由专家裁定，也不代表现实预测有效。

## 样本与问题

出生资料为合成输入。A、B 使用未验证的转述，C 明确假设两份解读已经分别论证，不冒充实际命盘产生相反建议；D、E 另以本地库重算事实。

| 场景 | 初次独立答复 | 复核与修正 |
|---|---|---|
| A：不同年份、不同安排 | insufficient | 保留；不能仅凭可同时执行便认定互补 |
| B：财线索＋官禄压力是否共同支持升职 | insufficient | 保留；两个标签未分别论证晋升 |
| C：同条件接项目与不接项目，强制二选一 | conflicts，但擅自假定等权、选择不接且认为更易撤回 | 保留冲突，撤回无依据取舍；先明确成本、机会、退出条件及用户偏好 |
| D：2026-02-10 八字丙午、紫微乙巳 | complements | 改为年界口径说明；历法标签差异不是分析互补 |
| E：旧时间八字＋新时间紫微 | conflicts | 改为 insufficient；输入未对齐，应分别重算完整双盘 |

## 实际变更

- [分析指引](../../references/analysis.md#综合与追问)先对齐候选、问题、实际时间范围、现实前提和判断层级，再区分 supports/complements/conflicts/insufficient；禁止补造权重或把不行动默认为低成本。
- [报告契约](../../references/report.md)引用上述要求。本轮没有改变报告 schema、核心算法或依赖。
- [原示例](../../examples/report.md)与[普通样例](../../examples/acceptance/ordinary/report.md)分别将缺少充分依据的 supports/complements 降为 insufficient，并同步修正文案及追问。通用实践建议不能充当双盘共同证明。

## 独立性与复测

实际启用一个隔离代理 `/root/cross_system_acceptance`，只读 Skill、references 和本地 dist，不读既有质量记录或验收答案；无网络、浏览器、外部 API 或源码修改。初稿完成后，主代理逐项复核并修订指引。同一代理再按新指引回答变体：2027年5月培训报名与不报名，以及混用出生输入和年界标签。

复测保留真实冲突但没有凭空代选；混合输入判为 insufficient；年界说明不强行套用 complements。主代理核对三项行为通过。这是定向复测，不是盲测、跨模型评测或统计留出集。

## 可复现事实与检查

[verify-facts.mjs](../../examples/acceptance/cross-system/verify-facts.mjs) 使用锁定的 lunar-typescript 1.8.6、iztro 2.6.1 及本地构建，核对实际运限查询和出生输入变化：

- 固定 UTC+08 口径，库计算2026立春为2月4日04:02:08，农历新年为2月17日。2月3日两者乙巳；2月10日八字丙午、紫微乙巳；2月17日两者丙午。这验证当前配置的换年行为，没有对天文时刻作独立认证。
- 1993-11-08 女性、120°E、Asia/Shanghai、真太阳时，14:20→14:50：时柱己未→庚申，命宫卯→寅，身宫巳→午，chartId 改变；不能拼接两套输入的结果。
- 事实复算脚本、两份更新报告的 report-check/render、Skill quick_validate 通过。本轮没有修改 src 或单元测试；上一轮完整检查为69/69通过，本轮未重复运行全量套件。

从项目根目录执行 `node examples/acceptance/cross-system/verify-facts.mjs`；输出记录见 [computation.json](../../examples/acceptance/cross-system/computation.json)。

## 稳定交付与限制

[问题与输入](../../examples/acceptance/cross-system/requests.json)、[初次独立原稿（含已知错误）](../../examples/acceptance/cross-system/baseline-responses.md)、[经复核答复](../../examples/acceptance/cross-system/responses.md)、[定向复测原稿](../../examples/acceptance/cross-system/retest.md)均保存在项目内，临时目录不是唯一证据。

指引约束仍依赖宿主理解，report-check 不会自动识别所有自然语言推断错误。缺少独立领域专家审定的真实双盘冲突样本；旺衰、用神及制化有效性仍未完成自动裁定。本轮没有 Fatetell 在线实验、全题库模型跑分、全局安装或发布。
