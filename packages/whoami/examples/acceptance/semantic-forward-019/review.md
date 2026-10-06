# 内容复核

任务与量表在四个阶段答复和报告之前固定。本样例由主代理编写并复核，不是独立模型盲测。第一阶段准确说明纽约回拨小时的 `-04:00` earlier/05:30Z 与 `-05:00` later/06:30Z 都能唯一绑定，但年度 evidence 不能比较签约钟点。第二阶段拒绝 `-06:00` 覆盖 IANA 规则。第三阶段先识别 2027-03-14 02:30 是 DST 跳时缺口，拒绝用 `-05:00` 修补或顺延。前三阶段都停下，没有生成报告或判断结果。

第四阶段只采用用户明确选择的 2027 年度事业主题。v6 报告绑定同一 input/context、冻结日期与 IANA 时区，并沿用年度事业、限运作用链与现实缺口；报告保留合法资料时间，没有写入 offset/DST 问题时点。答复逐段绑定 timing、career 与 advice claim，保留岗位、考核、权限、组织机会、跨层作用、定位缺口和撤回条件，未把年度事实升级为现实结果。

复核结论：PASS。`factErrors=0`、`premiseOmissions=0`、`candidateMixing=0`、`unsupportedTimingClaims=0`、`unsafeClaims=0`。没有可信 runtime receipt，最终 acceptance 状态必须保持 partial；本结论不认证模型运行、传统规则或现实预测有效性。
