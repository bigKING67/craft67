# MingLi-Bench：用于评测，不作为现实预测证明

来源：[README_zh](https://github.com/DestinyLinker/MingLi-Bench/blob/main/README_zh.md)、LICENSE、data/data.json；commit/哈希见 manifest。当前读取到 questions 数组 160 题，含 id、case_id、birth_info、question、options、answer、category。仓库声明 MIT，原赛题资料来源与个人资料适用边界需分别看待，本项目不提交整份数据集。

OBSERVED：原项目以选择题答案匹配计分，可注入预排命盘以分离“计算”和“解读”。部分出生地点仅是国家字符串，如 usa，不能据此唯一确定历史时区与经度。

whoami 采纳：固定数据指纹；按 case_id 而非题目随机拆分；prompts/answer-key 分文件；被测输入字段白名单；预测绑定 datasetHash；未答题保留分母，单报覆盖率。

whoami 不将题集作为调参后的无偏验收。开发集用于检查提示与流程，留出集不根据答错情况调参；若已经看过留出答案，应另标污染。上游预排盘必须标 external-chart，不能冒充 whoami 计算通过。缺时区/经度不得补造。

三项验收分开：

1. 计算适配与口径回归：固定命盘/历法样例。
2. 传统事件选择题：本题集表现和覆盖率，附样本数与污染限制。
3. 报告质量：事实引用、矛盾、候选时辰、资料更正与追问一致性。

命理解释不是科学验证的预测机制；无论题集分数如何，不将其写成“人生预测准确率”。本次不运行批量付费 API。
