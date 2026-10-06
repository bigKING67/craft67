# 内容复核

状态：PASS。该结论只覆盖本固定合成样例，不认证模型运行身份或现实预测有效性。

| 案例 | 非空白字符 | factErrors | premiseOmissions | candidateMixing | unsupportedTimingClaims | unsafeClaims |
|---|---:|---:|---:|---:|---:|---:|
| dst-overlap-earlier | 260 | 0 | 0 | 0 | 0 | 0 |
| dst-overlap-later | 268 | 0 | 0 | 0 | 0 | 0 |

earlier 正确保留出生偏移 −04:00、绝对时刻 2021-11-07T05:30:00Z、起运 2031-09-29T11:30:00Z；later 正确保留出生偏移 −05:00、绝对时刻 2021-11-07T06:30:00Z、起运 2031-09-24T12:30:00Z。两个未来起运民用时间都按对应日期的纽约 −04:00 表示，没有把出生 offset 错套到未来日期。

两支四柱、紫微基础及 2026 事实相同。确定性 compare 仅识别 `input.time` 与 `bazi.cycles` 变化，输入变化为 `dstDisambiguation`；两段没有混用分支。回答拒绝按命理结果选择 earlier/later，要求核对带时区与夏令时标记的出生记录，并保留地点、经度、时区来源未核验。
