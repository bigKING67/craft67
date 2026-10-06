# 多候选起运范围渲染与前向验收

日期：2026-09-23。结论：八字与综合 Markdown 现在按候选自动展示出生时间采样与起运范围，减少自由文本隐藏或压平不确定性的空间；新增双候选独立前向验收，复核发现原回答遗漏一条直接相关的大限四化，内容状态修正为 PARTIAL。这里验证的是固定合成样例的事实忠实和表达合同，不证明传统理论或现实预测有效。

## 自动渲染

当任一 `bazi.cycles` 事实的 `uncertainty.status` 为 `range` 时，`render` 在正文前生成“出生时间与起运范围（自动生成）”，逐候选显示：

- 候选 ID；
- 采样数与不同起运结果数；
- 出生时间、真太阳时偏移范围；
- 起运民用时最早值与最晚值；
- 绑定该候选 `bazi.cycles` 事实的附录链接。

段落明确说明顶层大运起点仅为代表样本。相关事实进入报告附录。纯紫微报告不插入八字段落。该机制保证确定性数据可见，仍不能自动理解正文是否用另一种措辞作出矛盾判断。

边界完整报告已按当前构建重渲染。女性合成样例的两个候选分别显示 3 个和 2 个采样，起运范围为 1991-10-17 11:00—15:02 与 1991-10-17 06:58—08:59；两者引用各自候选事实，没有串线。

## 双候选独立前向验收

新增 [semantic-forward-002](../../examples/acceptance/semantic-forward-002/) 固定套件。输入为男性合成资料：1988-02-15 23:00±2 分钟、东经 120 度、Asia/Shanghai、民用时、子初换日，并明确缺少来源元数据。边界产生两个候选：

| 候选 | 四柱 | 起运范围 | 2026 运年 |
|---|---|---|---|
| `C1-c6a1740f` | 戊辰、甲寅、辛丑、戊子 | 1994-05-14 15:02—19:00 | 戊午大运、丙午流年 |
| `C2-2f8865eb` | 戊辰、甲寅、庚子、丁亥 | 1994-05-14 20:59—22:58 | 戊午大运、丙午流年 |

独立代理只读取冻结的 Skill 快照、任务和 context；未读取 rubric、源码、测试、其他示例或网络。原始回答保留两个候选 ID 和不同起运范围，分别使用各自八字与紫微事实解释 2026，并拒绝因某个候选更有利而替用户选择出生时辰；它也将来源元数据标为未核验。

独立最终复核发现一项 P2：C1 使用本命天同化权、2026 流年天同化禄支持岗位授权和项目推进，却没有并列同一星在 2019—2028 大限化忌；三层均落本命官禄宫。冻结 Skill 明确禁止只选一层支持叙述，因此原始回答保持不变，人工评审修正为 PARTIAL、`premiseOmissions=1`；其余四项为 0。详情保存在 [内容复核](../../examples/acceptance/semantic-forward-002/review.md)。

manifest 绑定 Skill 快照、任务、量表、输入、context 与原始回答的 SHA-256 和字节数。当前环境没有可核验的 provider、model、modelVersion、reasoningEffort 或 runtime receipt，因此运行字段保持 `UNVERIFIED`。当前 PARTIAL 同时反映已知内容遗漏和运行身份缺口。

## 修订验收

原始结果没有覆写。另行固定 `remediation-task.md` 与 `remediation-rubric.md` 后，原代理只读取冻结 Skill、修订任务、context 和原稿，生成 `response-remediated.md`。修订稿显式并列 C1 本命天同权、2019—2028 大限天同忌、2026 流年天同禄，说明三层同落本命官禄且不能互相抵消或单向断吉；财务段区分本命落宫与流年宫职，C2 继续使用自己的盘面与起运范围。

独立有界复核五项计数均为 0，内容状态 PASS；非空白字符数 778。`manifest-remediated.json` 单独绑定修订任务、量表和回答，因 runtime receipt 仍缺失，`acceptance-check` 最终状态依然为 PARTIAL。该 PASS 只说明已定位遗漏在修订稿中得到处理，不把原始前向结果改写为通过。

## 验证边界

新增报告回归覆盖自动段落的精确起止值、事实附录和纯紫微隔离。最终验证结果：

- 最终 `npm run check`：113/113 tests PASS，TypeScript strict 与 build PASS；新增真实双候选分段回归及纯八字正向分支；
- Skill `quick_validate.py`：PASS；
- `semantic-forward-001`：`reviewStatus=PASS`、五项计数为 0；`semantic-forward-002`：`reviewStatus=PARTIAL`、`premiseOmissions=1`；`semantic-forward-002-remediated`：`reviewStatus=PASS`、五项计数为 0；三者 `runtimeVerified=false`，最终状态均为 PARTIAL；
- 主报告与边界报告 `report-check`：PASS；边界报告绑定年份为 2026—2028；
- 实际 Markdown 抽查：两个候选的范围和附录锚点分别为 `fact-14` 与 `fact-43`，没有交叉引用。

第一次只以 `--years 2026` 检查边界报告时按设计返回 `STALE_REPORT`；读取报告内容确认固定范围后，使用原绑定的 `2026,2027,2028` 重跑通过。该失败是调用年份不完整，不是报告漂移。完整记录汇总在 [验收记录](../validation.md)。

本轮没有修改排盘算法、报告 schema 或 evidenceId，也没有调用远端模型 API、处理真人资料、全局安装、发布或 push。分钟枚举仍不是连续区间完备证明；自动段落也不构成自然语言全语义验证。
