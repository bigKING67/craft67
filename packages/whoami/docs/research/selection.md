# 最终取舍状态：来源分层与工作约定

日期：2026-09-24。目标是解决一个报告层问题：什么时候可以把 selection 写成 `conditional`，什么时候即使其他四项都已有条件结论也必须保持 `unresolved`。

## 这不是新的古籍规则

现有研究分别采用：

- [旺衰与扶抑来源](strength-balance.md)：《滴天髓阐微》普通扶抑取法，并以《子平真诠》约束月令、根与透干不能简单计数；
- [财格条件来源](wealth-review.md)：《子平真诠》财格入口、成败与救应条件；
- [丙火申月调候来源](climate.md)：1926 年《穷通宝鉴》所选条目的壬水候选及壬、戊条件。

三类文本回答的问题、作者层次和“用神”语境不同。本轮没有找到、也不宣称存在一套古籍统一算法，可以把它们按票数或权重合成唯一元素。selection 状态门槛是 whoami 为防止报告越级而制定的工作约定，不冒充传统原文。

## 两种机械规则都不成立

“只要任一前置 topic unresolved，selection 就必须 unresolved”过严。已有合成报告能在明确限定为普通格扶抑、列全前提与撤回条件时，提出印星木这一限定候选；格局和调候仍未决，不妨碍说明该候选只在哪个范围成立。

“只要四个前置 topic 都 conditional，selection 就自动 conditional”则过松。当前主样例的四项条件结论分别只确认支持基础、财格入口、调候候选和优先比较分支，没有完成同一层级的方向选择；其中扶抑潜在比劫方向与调候壬水候选也不能合并。

因此状态依据不是前置状态计数，而是 selection 自己是否给出：具体方向、限定语境、完整前提、反证、撤回条件，以及未决口径如何影响最终答案。

## 三份固定样例

| 样例 | 前置状态 | selection | 裁决 |
|---|---|---|---|
| `strength-balance/report.json` | strength、balance conditional；pattern、climate unresolved | conditional | 允许：结论明确只提出普通格扶抑中的印星木候选，两条待核负荷路径在该前提下均指向印；同时保留财制印、强弱转向、格局与调候会撤回或改变最终答案 |
| 主 `examples/report.json` | strength、pattern、climate、balance 均 conditional | unresolved | 必须保留：四项只是最低结论，尚无已成立的具体取用方向；不能按 conditional 数量升级 |
| `full-1991/report.json` | balance conditional；strength、pattern、climate unresolved | unresolved | 必须保留：财、杀、食伤等不同分支会导向不同方向，尚无主分支或共同方向 |

这些样例验证报告状态和文字边界，不验证传统理论、现实预测或某种五行干预有效。

## 实现边界

本轮只增加 Skill 运行参考、报告合同说明和固定样例复核，没有给 `report-check` 增加自然语言分类器。当前结构校验能保证主题、引用和 premiseStatus 绑定，但不能判断“限定方向”是否真的满足全部传统前提。只有后续出现可重复的宿主错误样本，才考虑把稳定、低误报的部分升级为程序门禁；不能为自动化而发明关键词评分。

执行规则见[最终取舍的状态门槛](../../references/selection.md)。
