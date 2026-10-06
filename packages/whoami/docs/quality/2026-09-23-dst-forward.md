# DST 重复小时双分支前向验收

日期：2026-09-23。结论：纽约 2021-11-07 01:30 的 earlier/later 两个真实分支已进入固定自然语言验收。回答准确区分 offset、绝对时刻和起运事实，保留相同盘面事实，拒绝按命理解读结果选择 DST 分支。内容复核 PASS；没有 runtime receipt，因此最终状态仍为 PARTIAL。

## 固定输入与计算差异

两个输入仅将 `dstDisambiguation` 分别设为 earlier 与 later：

| 项目 | earlier | later |
|---|---|---|
| 出生民用时 | 2021-11-07 01:30 −04:00 | 2021-11-07 01:30 −05:00 |
| 绝对时刻 | 2021-11-07T05:30:00Z | 2021-11-07T06:30:00Z |
| 起运绝对时刻 | 2031-09-29T11:30:00Z | 2031-09-24T12:30:00Z |
| 起运纽约民用时 | 2031-09-29 07:30 −04:00 | 2031-09-24 08:30 −04:00 |

两支四柱均为辛丑、己亥、己未、乙丑，候选 ID、紫微基础及请求的 2026 事实相同。确定性 `compare` 只列出 `input.time` 与 `bazi.cycles` 改变，27 个其他事实键保持不变；证据绑定不同。未来起运日期都处于纽约夏令时，所以 civil 值均为 −04:00，不能把出生时 later 分支的 −05:00 沿用到 2031 年 9 月。

## 独立前向回答

Skill、任务、rubric、两个 input/context 在生成前固定。独立代理只读取允许的 Skill、任务与 input/context，没有读取 rubric、源码、测试、其他示例或网络。earlier 段 260 个非空白字符，later 段 268 个，均在任务要求的 220—380 内。

两段各自保留正确 offset、绝对时刻和起运值；说明同一墙钟时间不是同一瞬间，盘面主体相同也不表示证据绑定相同；明确拒绝按所谓“更好”结果选择 earlier/later，并要求核对带时区或夏令时标记的出生记录。地点、经度、时区来源继续标为未核验。

独立内容复核的 `factErrors`、`premiseOmissions`、`candidateMixing`、`unsupportedTimingClaims`、`unsafeClaims` 均为 0。manifest 绑定两个 case 的 input/context/response 与冻结 Skill、任务、rubric。当前 runtime 字段保持 UNVERIFIED 且无 receipt，因此 `acceptance-check` 返回 PARTIAL。

本验收不证明命理现实预测有效，也不能替用户确认历史记录究竟对应哪个 offset。本轮没有修改时间算法、报告 schema 或命盘证据规则，没有远端模型 API、真人资料、全局安装、发布或 push。
