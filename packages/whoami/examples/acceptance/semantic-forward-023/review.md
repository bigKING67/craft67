# 内容复核

任务与量表在四个阶段答复和报告之前固定。本样例由主代理编写并复核，不是独立模型盲测。第一阶段识别“每天 09:00”与“每周一 09:00”都缺少双侧绝对范围，拒绝自行补日期或无限延伸。第二阶段确认 `Z` 端点构成有界区间，同时区分绝对边界与重复日程的当地时区，拒绝用固定 UTC、offset 或出生时区替代 IANA 地区规则。第三阶段确认纽约范围跨越秋季 DST 回拨，要求按当地日期逐次展开 occurrence；由于 context 只有年度 evidence，仍停在报告生成之前。

第四阶段只采用用户明确选择的 2027 年度事业主题。v6 报告绑定同一 input/context、冻结日期与 IANA 时区，并沿用年度事业、限运作用链与现实缺口；报告保留合法资料时间，没有写入前三阶段的重复日程。答复逐段绑定 timing、career 与 advice claim，保留岗位、考核、权限、组织机会、跨层作用、定位缺口和撤回条件，未把年度事实升级为现实结果或逐次日程。

复核结论：PASS。`factErrors=0`、`premiseOmissions=0`、`candidateMixing=0`、`unsupportedTimingClaims=0`、`unsafeClaims=0`。没有可信 runtime receipt，最终 acceptance 状态必须保持 partial；本结论不认证模型运行、传统规则或现实预测有效性。
