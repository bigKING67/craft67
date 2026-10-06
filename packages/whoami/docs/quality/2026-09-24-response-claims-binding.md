# 前向答复逐段绑定报告 claim

日期：2026-09-24。结论：报告型 acceptance case 现在必须同时提供轻量 `whoami.response-claims.v1` sidecar。它不引入依赖或服务，只让 `acceptance-check` 能确定回答的每个非空段落绑定到哪条已验证 report claim，以及沿用了哪些八字论证前提。

## 原缺口

上一轮只能做两件事：验证 report 本身，并用窄关键词门禁阻止 response 显式宣布“唯一用神、结论已定、无需核对条件”。如果回答换一种措辞增加材料、漏掉限制或引用另一段报告，两个文件虽然都进入哈希绑定，验收器仍不知道回答每段自称依据哪条 report claim。

## 当前合同

- 有 report 的 case 必须有 responseClaims；没有 report 的既有 case 保持兼容，也不能单独附 sidecar。
- sidecar 的 `reportSha256` 必须等于当前 report artifact 的 SHA-256。
- response 按空行分段并去除文件与段落首尾空白；sidecar 必须按同一顺序、同一文字覆盖全部非空段落，漏段、加段或改字均拒绝。
- 每段至少引用一个存在的 `{section, claimIndex}`。重复或不存在的 report claim 引用拒绝。
- 每段 `reasoningRefs` 必须等于所引 report claims 的引用并集；`premiseStatus` 取所引 claims 中最保守状态：unresolved 优先于 conditional，均无八字绑定时为 not-applicable。
- 段落文字明确提到旺衰、格局、调候、扶抑或用神取舍时，所引 claims 必须含对应 reasoning topic。
- responseClaims 哈希进入 acceptance result、v1/v2 runtime receipt 与 v2 attestation payload；回执漏绑或错绑即失败。
- `caseChecks.responseClaimsValidation` 明示该检查为 pass 或 not-applicable。

## 故障注入与迁移

合成测试覆盖：无 report 却附 sidecar、报告型 case 缺 sidecar、sidecar 错绑 report 哈希、段落文字漂移、reasoningRefs 缺项，以及回执保留 report 却漏掉 responseClaims。它们分别由 `INVALID_ACCEPTANCE_RESPONSE_CLAIMS`、`RESPONSE_CLAIMS_MISMATCH` 或 `ACCEPTANCE_RECEIPT_MISMATCH` 拒绝。错误 context 附无效 report 时仍优先返回原本更具体的 `INVALID_ACCEPTANCE_REPORT`，不被缺 sidecar 掩盖。

`semantic-forward-006` 已增加三段映射；三段均引用报告 `summary[0]`，其 reasoningRefs 完整覆盖 strength、pattern、climate、balance、selection，premiseStatus 保持 unresolved。该 case 的 artifactCount 从 7 增至 8，result 与 attestation prepare bindings 同时包含 report 和 responseClaims 哈希。

最终验证：`npm run check` 为 132/132 PASS，TypeScript strict 与 build PASS；acceptance/attestation 定向测试 10/10 PASS；8 份固定 manifest、10 个 case 全部由构建版 CLI 重放成功；Skill quick_validate PASS；51 个 Markdown 文件中的 168 个本地链接无缺失。构建版 CLI 另以哈希同步后的篡改 sidecar 做故障注入，退出 1 并返回 `RESPONSE_CLAIMS_MISMATCH`，确认不是只被 artifact 哈希门禁提前拦下。

## 边界

sidecar 证明的是“提交者显式声明的段落—报告 claim 映射与前提状态在结构上自洽”。它不自动证明一段自然语言在所有细节上都由所引 claim 蕴含，也不验证传统理论或现实预测。事实级逐句蕴含、隐喻、反讽与遗漏仍由 rubric 和人工审校负责；真实生成身份仍需外部受信 attestation。
