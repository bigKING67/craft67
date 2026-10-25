# 架构与合同

Skill 负责组织与解释，标准库 Python 工具负责确定性事实。所有安装后需要的代码/引用/模板都位于 `skills/team-workflow-craft/`。外层 scripts 只构建、安装和验收；没有服务、模型客户端或任务数据库。

## 权威与边界

| 事实 | 权威 |
| --- | --- |
| 任务目标、验收、负责人 | 所配置平台的 Issue/分配及明确引用规格 |
| 公共接口、长期约定 | 仓库版本化文件/Schema |
| 代码、审批、合并 | Git 和协作 平台记录 |
| 验证 | 实际执行记录/受控 CI |
| 任务目录 `.team-workflow/tasks/<task>/` | 随任务分支提交的契约记录、证据摘要和最新交接；派生自上述来源，无权覆盖它们 |
| packet、binding、完整证据 | ignored local 可重建工作材料 |

`binding.json` 只表示这个工作区当前在处理哪件事，不表示认领、租约或任务完成；不同机器可同时绑定同任务，工具不伪造分布式排他性。多个进程不得同时共用同一工作区进行有副作用的验证；使用独立 worktree 及服务命名空间。

## 交换数据

版本为 `schema_version=2`（不读取 v1 产物），完整结构入口为 [contracts.schema.json](../skills/team-workflow-craft/assets/schemas/contracts.schema.json)。这是交换结构说明，不宣称提供通用 JSON Schema 执行器；运行时通过 `records.py` 在持久记录读取边界验证消费者使用的字段和状态不变量；CLI 与 CI 使用相同校验。旧 v2 argv 记录可读取，但 `check` 会报告绝对命令路径，需人工审阅迁移。

- TaskRef：provider/instance/repository/type/number，任务唯一身份。
- TaskRecord（`task.json`，提交）：TaskRef、revision、契约、编号的验收条件、来源哈希、`contract_sha256` 和修订历史。
- WorkPacket（local）：TaskRef、权威任务观察时间与快照、契约/来源哈希、Git 状态、策略哈希。缺契约/网络不可用保留未知。
- VerificationEvidence（local）：run_id、TaskRef、契约哈希、命令/时间/目录/退出码、before/after code、policy、toolchain、各检查状态和 drift。`local_execution_unattested` 明示本地证据不验证身份。
- VerificationRecord（`evidence/*.json`，提交）：上项的可提交摘要，命令用 `command_sha256` 绑定 canonical `{argv,cwd}`，完整 argv 留在 local；不含本地命令路径、remote 或输出。
- Handoff（`handoff.json/md`，提交）：TaskRef、契约版本、代码、done/remaining/next_steps、每条验收条件和每项检查的状态、blockers/unknowns/readiness；`merge_authorized=false`、`published=false`。

摘要状态固定为 `passed / failed / not_run / incomplete`；交接为 `not_ready / advisory_ready / unknown`。CNB 与 Gitea 是两个实际只读 provider；共用有界 GET 传输、失败分类和安全约束，分别实现端点、认证、分页及数据语义。不预留自动写入接口或任务引擎。

历史 v0.1.1 在快照、证据、交接中增加可选的 `actor` 观察字段，当时保持 schema v1 兼容。当前运行时只读 v2；兼容的旧 v2 记录缺身份时记未知。平台实例/账号 ID/login 与 Git 的有效 author/committer 分开保存，每次操作重新采集；交接另保留 `prepared_by`、每份证据的 actor 和契约 integrator。这些观察不创建成员目录、不改变任务分配，也不认证实际 push/merge 身份。具体使用见 [成员身份](../skills/team-workflow-craft/references/identity.md)。

## 代码身份与局限

代码身份 `tree_sha256` 是排除 `.team-workflow/tasks/` 后的工作树内容哈希：已跟踪、暂存、未跟踪文件及执行位、符号链接都计入，同一内容无论是否提交都相同，因此提交任务目录不会让证据失效。它不证明执行身份，不覆盖 ignored 文件/外部数据库/环境/瞬时改变后恢复。未解决冲突和 dirty submodule 无法完整绑定时不认证通过。代码内容、base、策略、契约版本或工具链改变都需要新证据。

工具链锁固定 `version/protocol_version/runtime_tree_sha256`，运行树哈希是相对路径→文件 SHA256 的排序 JSON（ASCII、紧凑分隔符）再 SHA256；排除 VERSION/LICENSE/安装标记/pyc。产物完整性另外使用安装器 ZIP 与全文件清单，二者不混用。运行时不自动更新锁或 latest。

验证默认不保留原始输出，仅哈希/字节数；不能用这一摘要诊断完整报错，必要时转受控 CI 的去敏日志。执行子进程仍有宿主权限，TWC 不是沙箱；审批哈希只是防止无意执行变更后的配置。
