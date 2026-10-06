# 外部宿主签发交接

日期：2026-09-24。结论：仓库新增 `attestation-prepare` 与 `attestation-finalize`，把已验证的 v2 协议接到外部签名器，同时保持私钥和回执文件写入完全在仓库工具之外。此能力解决 canonical payload 交付、请求漂移检测与外置公钥验签；finalize 只在 stdout 返回结构化 receipt 和唯一序列化字节，不替宿主生成或托管身份密钥，也不承担文件持久化。

## 合同

- `whoami.runtime-run.v1` 固定 runId、绝对 startedAt 与 provider/model/modelVersion/reasoningEffort/temperature/seed；必须与 draft manifest 的 runtime 完全一致。
- prepare 要求 `manifest.runtime.receipt=null`，先执行现有验收重算与 artifact/review 校验，再输出 `whoami.runtime-attestation-request.v1`。请求含受签 claims、canonical payload base64、字节数和 SHA-256。
- 外部签发方只签署 payload base64 解码后的原始字节。仓库 CLI 没有 private-key 参数，不读取或写入私钥。
- finalize 以当前 draft 和 request 内 run 重新生成完整请求，要求逐字段一致；随后使用清单目录树外的 Ed25519 SPKI PEM 公钥验签。
- finalize 返回 `whoami.runtime-attestation-finalization.v1`：`receipt` 是结构化 v2 回执，`serializedReceipt` 是唯一应持久化的 UTF-8 JSON bytes，并同时给出 base64、SHA-256 与长度。命令没有 output 参数，不创建、覆盖或探测 receipt 目标路径。
- 受信宿主编排器解码并核对 `serializedReceipt` 后，须用自身具备的目录句柄或事务边界安全持久化；再把实际相对 path、SHA-256 和 bytes 填入最终 manifest。文件写入竞态、权限和回滚属于该编排器的明确责任。
- 最终仍须运行 `acceptance-check --trusted-runtime-key`。prepare/finalize 成功本身不替代最终验收。

## 已验证边界

合成定向测试覆盖：请求 payload 的 schema、rubric 与 review 绑定；runtime run 错绑；draft 带旧 receipt；合法外部签名；篡改请求；错误签名；清单内公钥；CLI 拒绝遗留 output 参数；finalize 前后 manifest 目录条目完全不变；返回字节的 base64、长度、SHA-256 和结构化 receipt 一致。测试夹具再以外部编排器身份持久化这些精确字节，完成函数与 CLI 的 prepare → 外部签名 → finalize → acceptance-check=verified 链路。测试私钥只存在于测试进程内，用于模拟仓库外签名器。

本地 `npm run check` 为 120/120 PASS，TypeScript strict 与 build PASS；Skill quick_validate PASS；文档与规格范围 45 个文件、152 个本地链接无缺失。当时的 `openspec/` requirement 只作 Markdown 同步；后续审计确认它不参与运行或验收并已删除，现行合同以 `references/` 与自动测试为准。

独立审查首先复现两项已废弃写入实现的缺陷：父目录符号链接可在 realpath 检查后切向目录外；模拟 ENOSPC 在创建目标并写入 12 字节后失败时，旧实现误报 OUTPUT_EXISTS 并留下截断目标。第一轮修复用真实父目录、同目录临时文件和 hard link 关闭了这两项复现，但复审继续证明：攻击者仍可重命名已核验真实父目录，再在相同路径放置指向目录外的符号链接；字符串形式的 canonical 路径会重新解析到新对象。

本机 Node/macOS 探针确认无法用 `/dev/fd/<dirfd>/...` 相对已打开目录句柄创建文件（返回 ENOENT），Node 也没有可移植的 `openat` 接口。继续用路径字符串包装写入无法证明竞态安全，因此最终设计删除 finalize 的 output 参数和全部文件写入能力。先前路径、符号链接、部分写入与 no-clobber 回归只记录已否决方案的发现，不再被描述为现行实现能力。

纯 stdout 版本的最终独立复审为 PASS，未发现 High/P1/P2/P3。源码定向测试 8/8 PASS；独立用 dist 构建产物执行的 3 项工作流探针全部 PASS。复审逐文件比较 finalize 前后的 manifest 与信任公钥目录名称和内容哈希，确认零变化；源码和构建版 CLI 均拒绝 `--output`。`serializedReceipt` 的 base64、SHA-256、bytes 与结构化 receipt 一致，由外部测试夹具持久化后 `acceptance-check` 返回 verified。该结论只关闭当前仓库工具的写入竞态，不替外部编排器证明其持久化实现安全。

## 限制

当前没有选定或接入真实宿主签名器，也没有 provider readback。签发方必须在仓库外建立私钥保护、调用鉴权和“只对真实运行及其产物签名”的策略；若宿主无条件签署任意请求，密码学签名只能证明该密钥签过文件，不能证明声明的模型实际生成了回答。固定前向套件没有因此获得真实回执，状态仍为 PARTIAL。
