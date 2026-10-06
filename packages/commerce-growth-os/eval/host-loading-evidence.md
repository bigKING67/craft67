# 宿主加载证据能力核查

核查日期：2026-09-07。现场版本：`codex-cli 0.153.4`。仅运行版本、帮助及协议 schema 导出，无模型调用、安装或用户配置变更。

## 已确认的边界

- 本机 `codex exec --help` 提供 `--json`。官方[非交互模式文档](https://developers.openai.com/codex/noninteractive/)描述 thread、turn、item 和 error 事件；这些是执行遥测，不能直接证明 Skill 注入。
- 本机 `codex app-server generate-json-schema --experimental` 导出的 `TurnStartParams` 包含 `UserInput` 的 `skill` 分支，必需字段为 `type`、`name`、`path`。官方 [App Server 文档](https://developers.openai.com/codex/app-server/)也说明，显式 Skill 输入可让服务端注入完整指令。
- 同版本 `ServerNotification` 中名称含 skill 的通知只有 `skills/changed`。它表达目录变化，不是某次 turn 成功加载某个摘要的收据。此结论只覆盖本次导出的协议，不能推出所有内部通道均不支持加载证据。
- 默认执行路径仍为 `codex exec`。新增可选 App Server 适配器通过显式 Skill 输入记录合同接受状态，但不能把接受请求冒充所注入字节的独立收据。

本机导出文件的 SHA-256：

| Schema | SHA-256 |
|---|---|
| `v2/TurnStartParams.json` | `b36fb37326b1cf69f75c8b306f1f886d53a57c4b1b985e08e298e2407ea2ad02` |
| `ServerNotification.json` | `1a59e2cecb8e7930c4358f7a92245d9d52c96adb0e02b210fc39772ed10610fc` |

## 本次接入

执行器开启 `--json`，显式执行结果携带 `execution_events`：完整指令和 stdout 的摘要、已知事件计数、异常行数、未知事件数、有效非负整数 Token 用量。事件摘要不保存消息文本、工具参数、线程标识或未知事件 payload。stdout 摘要用于绑定本次捕获内容，原始流不持久保存，因此不能仅靠摘要重建或独立验证原始事件。

此摘要是诊断信息，不是成功门禁或加载证明。未知事件即使名为 `skill.loaded` 也不会将 `runtime_skill_loading_verified` 改为 true。模型自述也不提升证明等级。超时分支目前不保留部分事件摘要，继续返回超时错误；不能据缺失摘要断言调用未发生。

下一步如需关闭加载证据缺口，应明确选择并验收宿主侧注入证据通道。当前保持 `UNSUPPORTED_BY_CURRENT_ADAPTER`，不发起付费调用来猜测接口，也不修改全局配置或安装额外 hook。

## 可选 App Server 适配器

`run_execution_eval.py --backend app-server --model MODEL` 可选择新路径；质量编排对应 `--execution-backend app-server`，只影响 execution 层。默认 exec 路径保留。App Server 要求显式模型，不静默使用默认值。

每次调用创建私有临时工作目录与 `CODEX_HOME`，不复制用户 config、auth、MCP 或 hook 配置；继承进程环境，按 allowlist 接受非秘密 provider transport 配置。用户已登录的 Codex 认证文件不会自动复用，认证能力必须另外验证，不能通过复制个人配置绕过隔离。本路径不是无 Skill 对照环境，也不能证明默认发现目录只包含一个 Skill。

初始化后显式请求 ephemeral、read-only、approvalPolicy=never，并核对服务端返回的模型、cwd、审批与 sandbox 类型。服务端请求交互审批时拒绝并终止。请求负载限制为 4 KiB；事件按有界队列读取，超时与成功结束均回收本次进程组。新 App Server 适配器当前只支持 POSIX，Windows 在启动前明确拒绝；原 exec 的 Windows 分支不受此平台限制影响。

`skill_input_receipt` 绑定名称、路径、指令摘要、Skill 与 Bundle 摘要、thread/turn ID、服务端接受状态、完成状态及执行前后 Bundle 一致性。字段 `input_accepted=true` 只证明请求已被服务端接受；`runtime_skill_loading_verified` 仍为 false，`loading_evidence_status=INPUT_CONTRACT_ONLY`。文件前后摘要也不能证明执行中没有短暂变化，不能代替宿主注入字节收据。

本机 initialize-only 握手已通过，未发送 thread/start 或 turn/start。完整 turn 使用本地模拟 stdio 子进程验证，覆盖 SIGTERM 取消及忽略 TERM 的后代回收，不作为真实模型输出或认证通过的证明。

## 首次真实 smoke

已用 `gpt-5.6-sol` / `high` 完成 1 次商业案例，耗时 197.167 秒。服务端返回同名模型和 `observed_reasoning_effort=high`，API-key 登录、显式输入接受、轮次完成及 Bundle 前后一致性通过。只证明当前本机代理和该次调用，不扩展为所有 provider 或模型均可用。

入口新增 `--reasoning-effort`；默认 medium 保持兼容。App Server 将环境中的 `CODEX_API_KEY`（优先）或 `OPENAI_API_KEY` 经 stdin 的 `account/login/start` 提供给隔离服务，并从服务进程的继承环境移除这两个变量；不把凭据写入 argv 或结果。宿主可能将登录信息存于临时 CODEX_HOME，目录随调用清理。本次由操作进程只读取得已授权的现有 API key，不复制整份 auth/config。

生成答案核心算术通过，但漏列两项验收要求的比值；词法 linter 也出现现状词与标题词匹配误判，均保留为待处理项。没有运行额外 Judge 或无 Skill 对照。`runtime_skill_loading_verified=false` 仍保留，不将真实完成一次调用改写为注入字节已验证。
