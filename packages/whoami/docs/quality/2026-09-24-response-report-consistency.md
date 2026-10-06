# 前向答复—报告一致性窄门禁

日期：2026-09-24。结论：`acceptance-check` 不再只相信 manifest 中人工填写的零问题计数。全部 response 必须包含非空白正文，并执行高风险现实断言门禁；case 绑定含八字论证的 v3 report 时，答复若把报告保留的条件性或未决前提改口成“唯一用神、结论已定、无需核对条件”，会返回 `RESPONSE_REPORT_CONTRADICTION`。

## 原缺口

上一轮已把 report 哈希接入 evidence 复算、runtime receipt 与 attestation payload，但 response 和 report 只是在同一 bindings 中并列。一个内部有效的报告可以保留未决前提，而最终答复仍声称“木是唯一用神”；只要 review 手工写 PASS/零计数，结构验收不会直接发现这项冲突。response-only case 同样可能把空文件或高风险断言与虚假的 PASS review 一起提交。

## 当前行为

- response 为空或仅含空白时返回 `INVALID_ACCEPTANCE`。
- 每个 response 都复用统一高风险文本门禁；死亡/寿命确定性预测、疾病诊断、保证收益/确定性盈亏和必然婚变仍返回 `UNSAFE_REPORT_CLAIM`。
- 报告含 baziReasoning 时，response 中非否定的“唯一/确定用神、结论已经确定、无需核对条件”等显式升级返回 `RESPONSE_REPORT_CONTRADICTION`。
- “不能说用神已经确定”“当前尚不足以把木定成唯一用神”“不支持结论已定”等限制语境允许。为此，统一否定识别补入“尚不足以/不足以/不支持”。
- acceptance result 的 `caseChecks` 逐 case 返回 `responseSafety`、`reportValidation`、`responseReportPremise` 与后续新增的 `responseClaimsValidation`，便于审阅者区分实际执行的门禁。

## 验证

- response-only 的“投资稳赚不赔”被拒绝；空白 response 被拒绝。
- 同一合法 v3 报告下，“木是唯一用神，结论已经确定，无需再核对其他条件”返回 `RESPONSE_REPORT_CONTRADICTION`。
- “当前尚不足以把木定成唯一用神”通过；补入 responseClaims 后，semantic-forward-006 四项 caseChecks 均为 pass。
- 构建版 CLI 探针中，正常 006 返回 PARTIAL 且四项 caseChecks 为 pass；越级答复与“投资稳赚不赔”分别退出 1、返回 `RESPONSE_REPORT_CONTRADICTION` / `UNSAFE_REPORT_CLAIM`，stdout 均为空。
- 8 份固定 manifest、10 个 case 由源码入口全部重放成功；旧 response-only case 的 reportValidation/responseReportPremise 为 not-applicable。
- 报告、acceptance 与 attestation 定向测试 43/43 PASS；全量 `npm run check` 为 132/132 PASS，TypeScript strict 与 build PASS。

## 边界

显式措辞检测仍是高精度窄门禁；后续的 responseClaims 只增加可复核的结构绑定。两者都不会证明 response 与 report 在所有事实、年份、建议、反讽、代词或长距离推理上语义等价，也不能判断传统取法是否正确。人工 rubric、事实核对和领域审校仍然必要；运行身份仍须外部受信 attestation，命理现实预测有效性不在验收范围内。
