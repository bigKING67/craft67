# Codex 运行时证据能力审计

日期：2026-09-24。结论：本机 `codex-cli 0.156.1` 暴露 upstream `x-oai-attestation` 客户端传输 token 和 internal/experimental raw response ID，但当前 schema 没有声明 token 与 whoami canonical payload/manifest 的绑定，本轮也没有执行认证 provider readback。两类信号都不能把自然语言验收升级为 `runtimeVerified`。

## 现场与实现

新增 `npm run audit:codex-runtime`。它只执行 `codex --version` 和 `codex app-server generate-json-schema --experimental --out <临时目录>`，解析五份相关 schema 后删除临时目录；不启动模型、不读取认证文件、不调用网络或 Responses API。输出 schema 为 `whoami.codex-runtime-evidence-audit.v1`。

本机审计观察到：

| 信号 | 当前声明 | 验收判定 |
|---|---|---|
| initialize capability | `requestAttestation` 指向 upstream `x-oai-attestation` | 仅说明客户端传输能力 |
| attestation request | params 是空 object，没有 payload/manifest/bindings 字段 | 未声明 whoami canonical payload 绑定 |
| attestation response | required string `token`，说明为 opaque client attestation token | token 本身不构成 v2 receipt |
| raw response event | internal-only，含 required responseId/threadId/turnId | ID 本身不证明响应内容与本次 artifact 相同 |
| raw event opt-in | `experimentalRawEvents`，说明为 internal use only | 不是稳定公开验收合同 |
| provider readback | 本轮未执行 | `liveProviderReadbackPerformed=false` |

核心判定函数对缺失 schema 失败封闭；schema 不可用时把能力记为未声明，并保持 `canUpgradeAcceptance=false`。即使未来观察到 manifest/payload 字段，当前实现也不会自动把接口声明升级为验证已发生；接入新的 trust path 仍需独立设计和验收。

## 为什么 response ID 仍不够

OpenAI 的 Responses API 支持按响应 ID 读取已存储响应，返回响应对象中的 id、model、output 与 status；响应默认是否存储及保留期由 API 合同决定。[Retrieve a model response](https://developers.openai.com/api/reference/cli/resources/responses/methods/retrieve) 与 [Conversation state](https://developers.openai.com/api/docs/guides/conversation-state) 说明了这条 provider readback 能力。Codex app-server 的 raw response 事件则明确是 internal/experimental 集成面；事件里出现 ID，只能提供后续核验的候选句柄。

要把 provider readback 发展成 whoami 的新 receipt，受信编排器至少还需证明它有权读取该响应、响应确已存储、返回内容与本次 response artifact 原始字节一致，并把模型身份、Skill、task、rubric、input/context、review 与逐 case 哈希纳入不可替换的绑定。本轮没有这些证据，所以没有改动 `acceptance-check` 的信任条件。

## 验证与限制

- 合成合同测试覆盖完整能力、schema 缺失以及非法 schema/版本三类路径：3/3 PASS。
- 当前 CLI 的实时本地审计 PASS，输出四个不足原因：未绑定的传输 attestation、internal/experimental raw event、只有 response ID、未执行 provider readback。
- `npm run check`：123/123 tests PASS，TypeScript strict 与 build PASS。
- Skill quick validation 与本地文档链接检查 PASS。

这是 2026-09-24 对本机 CLI 版本的能力快照，不是 OpenAI 服务长期合同，也没有证明任一固定前向回答由该版本真实生成。重新安装或升级 Codex 后应重跑审计；只有外部 Ed25519 签发链或未来经过独立验收的认证 provider readback 才能关闭当前 runtime blocker。
