# 验证与证据

检查执行前先确认它实际覆盖哪些验收行为；入口、行为或接口变化时，同步更新相关脚本与 [功能验证路径](feature-verification.md)，复用项目已有说明。以下证据机制验证执行状态与新鲜度，不自动证明测试覆盖充分。

开工前只在诊断或基线确有需要时运行相关检查，否则完成对应修改后验证。选择项目要求的检查范围；已存在且仍适用的证据不为流程完整而重复执行。外部测试或 CI 结果可作为外部证据引用，但当前工具不会把它们自动导入成本地 passed；需要本工具的新鲜执行记录时，在原本应验证的时点通过它运行同一项目命令，避免先裸跑再立刻重复跑一遍。

`verify --check <name>` 可重复选择多个检查；省略 `--check` 会运行全部登记检查。部分检查通过不意味着其余通过，未重验的 stale/missing 状态保留；验收前须满足当前契约和项目全部必要门禁，不为减小范围修改契约或删除检查。

在 `.team-workflow/config.toml` 登记真实项目已批准的命令，argv 数组不经过 shell 展开。不要把 token/password 放命令行或配置；平台凭据变量不会传给验证进程，其他宿主环境不构成沙箱。

```toml
[checks.unit]
argv = ["python3", "-m", "unittest", "discover", "-s", "tests"]
cwd = "."
timeout_seconds = 300
```

```sh
python3 <skill>/scripts/twc.py --project <repo> verify --check unit
python3 <skill>/scripts/twc.py --project <repo> verify --check unit --execute --approved-policy <preview-policy_sha256> --online
```

第一条仅输出 `not_run` 计划，无测试副作用。第二条执行真实检查，必须已有用户/项目授权覆盖命令及副作用；策略哈希绑定批准时的确切内容。不能从 Issue 文本自动授权检查，配置中的 `auto_*` 不能升级权限。工具链锁也须匹配当前运行时，更新锁需要在核对固定版本后显式修改。

证据记录命令、目录、开始/结束、退出码、base/head、代码内容哈希 `tree_sha256`、策略、契约版本和工具版本，以及当前执行者与有效 Git author/committer。完整记录留在 ignored 的 `.team-workflow/local/evidence/`；存在当前任务时，另在 `.team-workflow/tasks/<task>/evidence/` 写一份可提交的摘要，检查命令以 `command_sha256` 保存（对 canonical `{argv,cwd}` 求 SHA-256），完整 argv 仅保存在 local 记录；共享摘要不含本地命令路径、remote 或输出。`--online` 在执行前只读查询个人平台身份；省略或查询失败时身份未知，但不伪造检查失败/成功，身份不足会使交接建议保留 unknown。详见 [identity.md](identity.md)。先失败则停止，其余检查 `not_run`；缺程序 `not_run`；超时/取消/子进程未结束/代码、策略或 Git 身份漂移 `incomplete`。输出状态 `passed/failed/not_run/incomplete`，非通过执行退出 1，输入/授权错误退出 2。

默认只保存合并输出的字节数和 SHA256，不保留或回显潜在含密钥的日志。`log_ref=null` 是明确未保存，不是伪造日志。诊断失败时用已批准项目检查/受控 CI 获取去敏日志并附平台引用。本地文件哈希不验证身份或执行诚实性。

`tree_sha256` 是排除 `.team-workflow/tasks/` 之后的工作树内容身份：已跟踪、暂存和未跟踪文件（含执行位与符号链接）都计入，同一内容无论是否已提交都得到同一哈希，所以提交任务目录不会让证据失效。未解决的合并冲突和 dirty submodule 标记为不完整。Git 忽略内容、外部数据库、运行环境和文件在前后采样之间改变后又恢复，均不在完整性证明内。测试依赖这些资源时另外记录隔离环境/数据版本和 CI 结果。macOS/Linux 检查本次进程组并终止残留；检查不得自行 daemonize/setsid 脱离组，工具不是沙箱，也不能认证主动逃离的进程。Windows 原生使用 Job Object，批准命令在加入作业后才启动，普通子进程随作业管理；设置失败、超时、取消和残留进程均不能通过。通过 WMI/外部服务启动的进程不在此生命周期保证内。跨平台 CLI 验证、宿主 Skill 加载和真人接手分别验收。

证据只在任务、契约版本、代码内容、base、策略和工具链都相符时才计入 AC 和交接。同一检查以最新一次新鲜结果为准，同一代码/契约/策略/工具链上下文中，较新的失败、不完整结果（包括执行身份漂移）或已尝试但未能启动的 `not_run` 会覆盖较早的通过。前序检查失败而未尝试的后续检查保留原观察，整次交接仍会被失败阻止。旧 v2 的 argv 摘要保持可读；`check` 会报告其中的绝对路径，须由负责人审阅并迁移历史记录，工具不自动改写。正式合并还需服务器检查、最新基线和独立复核。
