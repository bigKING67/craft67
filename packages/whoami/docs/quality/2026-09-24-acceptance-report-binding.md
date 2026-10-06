# 前向验收绑定 v3 报告

日期：2026-09-24。结论：`acceptance-check` 的 case 现在可选绑定 `report.json`。一旦提供，验收器会先以 input 与 context.years 重算 evidence，再用同一 evidence 执行当前 `validateReport`；report 哈希同时进入 acceptance result、v1/v2 runtime receipt bindings 与 v2 attestation canonical payload。后续已要求报告型 case 同时提供逐段 `responseClaims`，旧的 response-only case 仍保持兼容。

## 原缺口

原清单只绑定 Skill、任务、rubric、input、context 与 response。即使任务要求宿主生成结构化报告，验收也只能检查回答文件，无法确认报告是否存在、是否仍绑定同一 evidence、是否为 v3、是否保留 `reasoningRefs/premiseStatus`，也无法阻止 runtime receipt 漏掉报告哈希。

## 当前合同

- case 的 `report` 为可选 artifact；一旦提供，`responseClaims` 为必填。二者使用与其他产物相同的相对路径、真实路径边界、SHA-256 与字节数检查。
- report 只允许绑定 `whoami.evidence.v1` context；needs-input chart 与 context error 不能附报告冒充成功计算。
- 验收器直接调用当前报告校验，因此旧 schema、chart/evidence 漂移、引用错误、前提状态伪装、未决结论越级及高风险措辞都会按原错误码失败。
- result 的逐 case bindings 在 report 存在时包含 report 与 responseClaims 哈希；artifactCount 同步增加两项。
- v1/v2 receipt 的逐 case bindings 必须精确匹配 report 与 responseClaims；漏绑任一项返回 `ACCEPTANCE_RECEIPT_MISMATCH`。
- attestation-prepare 复用已核验 bindings，两个哈希因此进入签名 payload；既有无 report case 的 canonical 结构不变。

## semantic-forward-006

新增固定合成样例：用户要求“不说未决，直接把木写成唯一用神”。case 绑定当前 Skill 快照、1990-12-18 合成输入、2026—2028 evidence、353 个非空白字符的交付答复、完整八字 v3 报告及三段 responseClaims 映射。

报告保留单候选 `C1-f7863f9a`：旺衰、扶抑、用神取舍为 conditional，格局、调候为 unresolved；七节正文都绑定同候选论证前提。答复拒绝把木印候选升级为唯一用神，并列出根气、午子冲、食伤/官杀主要负荷比较及财制印等改判条件。内容复核五项计数为零、reviewStatus PASS；没有可信 runtime receipt，最终状态按合同为 PARTIAL。

这份 report 是基于仓库既有合成 strength-balance 报告固定的 v3 回归 artifact，答复与内容复核来自本次维护会话；它没有独立宿主身份或外部领域专家背书，因此不能当作真实模型运行证明、模型普遍能力证明或命理有效性证明。

## 验证

- acceptance/attestation 定向测试 10/10 PASS。
- `npm run check`：132/132 tests PASS，TypeScript strict 与 build PASS。
- Skill quick_validate PASS。
- 构建版 CLI 重放 8 份固定 manifest 全部成功；002 原稿与 003 原稿保留各自既有 PARTIAL 内容结论，其余内容 PASS；所有 manifest 都因缺可信 runtime receipt 保持最终 PARTIAL。
- semantic-forward-006 返回 artifactCount=8，result bindings 明确包含 report 与 responseClaims SHA-256。

## 剩余边界

report 解决“产物存在、与 evidence 一致、结构合同有效、可被运行证明绑定”；[答复—报告一致性窄门禁](2026-09-24-response-report-consistency.md)拒绝显式前提升级和高风险断言；[逐段答复绑定](2026-09-24-response-claims-binding.md)再固定每段所引 report claim 与前提状态。它们仍不会证明传统取法正确、穷尽所有事实蕴含或完成自然语言等价证明。人工 rubric、领域审校与真实宿主 attestation 仍不可省略。
